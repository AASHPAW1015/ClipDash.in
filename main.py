import os
import logging
import asyncio
import datetime
import re
from typing import Optional

import httpx
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Configuration ---
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
    datefmt="%Y-%m-%dT%H:%M:%S%z"
)
logger = logging.getLogger(__name__)

# --- Firebase Initialization ---
if not firebase_admin._apps:
    if FIREBASE_CREDENTIALS_PATH and os.path.exists(FIREBASE_CREDENTIALS_PATH):
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase initialized successfully.")
    else:
        logger.warning("Firebase credentials not found. Firestore operations will fail.")
        # For development without creds, you might want to mock this or handle gracefully
        # firebase_admin.initialize_app() # Implicit default creds if on GCP

try:
    db = firestore.client()
except Exception as e:
    logger.error(f"Failed to initialize Firestore client: {e}")
    db = None

# --- FastAPI App Setup ---
app = FastAPI(title="ClipStream Bot Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files (Serve CSS, JS, Assets)
app.mount("/css", StaticFiles(directory="public/css"), name="css")
app.mount("/js", StaticFiles(directory="public/js"), name="js")
app.mount("/assets", StaticFiles(directory="public/assets"), name="assets")

# --- Models ---
class SignupRequest(BaseModel):
    email: str
    youtubeChannelUrl: str
    discordWebhookUrl: str

    @validator('youtubeChannelUrl')
    def validate_channel_url(cls, v):
        # Basic check to ensure it looks like a channel URL or ID
        # We need to extract the ID starting with UC
        if 'youtube.com/channel/UC' not in v and not v.startswith('UC'):
             # It might be a custom URL, but the prompt specifically asks to validate Channel ID starts with UC
             # We'll assume the user provides the full URL or we extract it.
             # Let's be lenient here and extract in the logic, but strict on the ID format if possible.
             pass
        return v

# --- Helper Functions ---

def extract_channel_id(url_or_id: str) -> Optional[str]:
    """Extracts the channel ID (starting with UC) from a URL or string."""
    # Regex to find UC... followed by alphanumeric, -, _
    match = re.search(r'(UC[\w-]{22})', url_or_id)
    if match:
        return match.group(1)
    return None

async def send_discord_notification(webhook_url: str, message: str):
    """Sends a message to Discord webhook (Fire-and-Forget)."""
    async with httpx.AsyncClient() as client:
        try:
            await client.post(webhook_url, json={"content": message})
            logger.info(f"Sent Discord notification to {webhook_url}")
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")

# --- Routes ---


# ... (existing imports)

@app.get("/")
async def read_root():
    return FileResponse("public/index.html")

@app.post("/webhook/signup")
async def signup(request: SignupRequest):
    channel_id = extract_channel_id(request.youtubeChannelUrl)
    if not channel_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube Channel ID. Must start with 'UC'.")

    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized.")

    try:
        # Save to Firestore
        doc_ref = db.collection("clipper_integrations").document(channel_id)
        doc_ref.set({
            "email": request.email,
            "youtubeChannelUrl": request.youtubeChannelUrl,
            "discordWebhookUrl": request.discordWebhookUrl,
            "createdAt": firestore.SERVER_TIMESTAMP
        })
        logger.info(f"Registered user: {request.email} with Channel ID: {channel_id}")
        return {"message": "Signup successful", "channel_id": channel_id}
    except Exception as e:
        logger.error(f"Firestore error during signup: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- Cache ---
# Simple in-memory cache: {video_id: actual_start_time (datetime)}
# In production, use Redis or similar for multi-worker setups.
stream_start_cache = {}

@app.get("/webhook/clip")
async def create_clip(
    background_tasks: BackgroundTasks,
    channel_id: str = Query(..., description="YouTube Channel ID (UC...)"),
    user: str = Query("User", description="Username requesting the clip"),
    message: str = Query(None, description="Optional message/title for the clip")
):
    if not channel_id.startswith("UC"):
        raise HTTPException(status_code=400, detail="Invalid Channel ID")

    # 1. DB Lookup (Async Wrapper)
    # The firebase-admin SDK is synchronous, so we run it in a thread pool
    # to avoid blocking the entire server while waiting for the database.
    if not db:
         raise HTTPException(status_code=500, detail="Database error")

    try:
        loop = asyncio.get_running_loop()
        # Run the blocking DB call in a separate thread
        doc = await loop.run_in_executor(
            None, 
            lambda: db.collection("clipper_integrations").document(channel_id).get()
        )
        
        if not doc.exists:
            logger.warning(f"Channel ID {channel_id} not found in database.")
            return "Error: Channel not registered."
        
        data = doc.to_dict()
        discord_webhook_url = data.get("discordWebhookUrl")
    except Exception as e:
        logger.error(f"Database lookup failed: {e}")
        return "Error: Database lookup failed."

    # 2. The "Zero-Quota" Trick
    video_id = None
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient() as client:
            # Do NOT follow redirects to get the Location header
            response = await client.get(f"https://www.youtube.com/channel/{channel_id}/live", follow_redirects=False, headers=headers)
            
            # Check for 3xx redirect
            if response.status_code in (301, 302, 303, 307):
                location = response.headers.get("Location")
                if location:
                    vid_match = re.search(r'v=([\w-]+)', location)
                    if vid_match:
                        video_id = vid_match.group(1)
            
            # Fallback: If it returns 200 OK (YouTube sometimes does this instead of redirecting)
            elif response.status_code == 200:
                html_content = response.text
                # Look for <link rel="canonical" href="https://www.youtube.com/watch?v=VIDEO_ID">
                # or <meta property="og:url" content="https://www.youtube.com/watch?v=VIDEO_ID">
                
                # Regex to find video ID in canonical URL or og:url
                # Matches: youtube.com/watch?v=VIDEO_ID
                vid_match = re.search(r'youtube\.com/watch\?v=([\w-]+)', html_content)
                if vid_match:
                    video_id = vid_match.group(1)
                else:
                    # Try finding "isLive":true which implies we are on a live page, then look for videoId
                    if '"isLive":true' in html_content:
                         vid_match_json = re.search(r'"videoId":"([\w-]+)"', html_content)
                         if vid_match_json:
                             video_id = vid_match_json.group(1)

            if not video_id:
                logger.info(f"No live stream found for {channel_id} (Status: {response.status_code}).")
                return "Error: Stream is offline or not found."

    except Exception as e:
        logger.error(f"Zero-Quota check failed: {e}")
        return "Error: Failed to check stream status."

    # 3. YouTube API Call for Start Time (With Caching)
    if not YOUTUBE_API_KEY:
        logger.error("YouTube API Key is missing.")
        return "Error: Server misconfiguration."

    actual_start_time = None
    
    # Check Cache First
    if video_id in stream_start_cache:
        actual_start_time = stream_start_cache[video_id]
        logger.info(f"Cache hit for video {video_id}")
    else:
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "part": "liveStreamingDetails",
                    "id": video_id,
                    "key": YOUTUBE_API_KEY
                }
                yt_response = await client.get("https://www.googleapis.com/youtube/v3/videos", params=params)
                yt_data = yt_response.json()

                if "items" in yt_data and len(yt_data["items"]) > 0:
                    live_details = yt_data["items"][0].get("liveStreamingDetails", {})
                    actual_start_time_str = live_details.get("actualStartTime")
                    if actual_start_time_str:
                        # Parse ISO 8601 format: 2023-10-27T10:00:00Z
                        actual_start_time = datetime.datetime.fromisoformat(actual_start_time_str.replace('Z', '+00:00'))
                        
                        # Update Cache
                        stream_start_cache[video_id] = actual_start_time
                        logger.info(f"Cache miss for video {video_id}. Fetched from API.")
                
                if not actual_start_time:
                     logger.info(f"Could not get actualStartTime for video {video_id}. Stream might not be live.")
                     return "Error: Stream details not available."

        except Exception as e:
            logger.error(f"YouTube API call failed: {e}")
            return "Error: Failed to fetch stream details."

    # 4. Calculation
    now = datetime.datetime.now(datetime.timezone.utc)
    time_diff = now - actual_start_time
    total_seconds = int(time_diff.total_seconds())
    
    # Format timestamp like 1h23m44s
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    timestamp_str = ""
    if hours > 0:
        timestamp_str += f"{hours}h"
    if minutes > 0 or hours > 0:
        timestamp_str += f"{minutes}m"
    timestamp_str += f"{seconds}s"

    # Construct URL
    clip_url = f"https://youtu.be/{video_id}?t={timestamp_str}"
    
    # 5. Discord Notification (Fire-and-Forget)
    # Using BackgroundTasks to ensure the response returns immediately to Nightbot
    discord_content = f"**Clip Created by {user}!**\n{clip_url}"
    if message:
        discord_content += f"\n**Note:** {message}"
    
    background_tasks.add_task(send_discord_notification, discord_webhook_url, discord_content)

    # 6. Response
    return f"Clip created! {clip_url}"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
