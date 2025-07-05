from pyrogram import Client
from plugins.generate import database
from info import API_ID, API_HASH, ADMIN

User = None

async def start_userbot():
    global User
    vj = database.find_one({"chat_id": ADMIN})
    if not vj:
        print("⚠️ No session found in DB for ADMIN")
        return
    User = Client("post_search", session_string=vj["session"], api_id=API_ID, api_hash=API_HASH)
    await User.start()
    print("✅ Userbot session started")
