# ClipStream Bot - Troubleshooting & Disaster Recovery

So, things went wrong? Here is how to fix them.

## 1. The "Quota Exceeded" Crash (Most Common)
**Symptoms:**
- Nightbot says "Error: Failed to fetch stream details."
- Logs show `403 Forbidden` or `quotaExceeded` from YouTube.

**The Fix (Hot Switching):**
1.  **Manual Way:**
    - Open `.env` file: `nano .env`
    - Change `YOUTUBE_API_KEY` to a new one.
    - Restart server: `systemctl restart clipstream` (takes 1 second).

2.  **Automatic Way (Recommended):**
    - We can update the code to accept **multiple keys** (e.g., `KEY1,KEY2,KEY3`).
    - If Key 1 fails, it automatically tries Key 2.
    - *I can implement this for you now.*

## 2. The "Zombie Process" Crash
**Symptoms:**
- You try to start the server and it says `Address already in use`.
- The site refuses to load.

**The Fix:**
- Run this command to kill the zombie:
  ```bash
  lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
  ```
- Then start the server again.

## 3. The "Database Timeout"
**Symptoms:**
- Nightbot takes 10+ seconds to reply.
- Logs show `Firestore timeout`.

**The Fix:**
- This usually happens if your internet (Home Server) is unstable.
- **Solution:** Check your server's internet connection. The bot will auto-recover when internet comes back.

## 4. The "Stream Not Found" Error
**Symptoms:**
- Streamer is live, but bot says "Stream is offline".

**The Fix:**
- YouTube sometimes changes their HTML layout, breaking our "Zero-Quota" trick.
- **Solution:** You might need to update the `regex` in `main.py` if YouTube changes their site.
- *Temporary Fix:* Disable the Zero-Quota check in code (forces API use, costs more quota but is reliable).

## 5. Server Out of Memory
**Symptoms:**
- The server freezes completely. SSH doesn't work.

**The Fix:**
- **Hard Reboot:** Unplug your PC / Restart VPS.
- **Prevention:** Ensure you are using `Gunicorn` (as per the guide), which manages memory better than just `python main.py`.
