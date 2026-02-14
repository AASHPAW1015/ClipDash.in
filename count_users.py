"""Quick script to count registered users in Firestore."""
import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()
docs = db.collection("clipper_integrations").stream()

print("\n🔍 ClipDash Registered Users")
print("=" * 40)

count = 0
for doc in docs:
    count += 1
    data = doc.to_dict()
    email = data.get("email", "N/A")
    channel = doc.id
    created = data.get("createdAt", "N/A")
    print(f"  {count}. {email} | Channel: {channel} | Joined: {created}")

print("=" * 40)
print(f"📊 Total Users: {count}")
