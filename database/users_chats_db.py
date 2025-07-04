import pymongo
from info import DATABASE_NAME, DATABASE_URI

client = pymongo.MongoClient(DATABASE_URI)
db = client[DATABASE_NAME]

async def get_chat(chat_id):
    return await db.chats.find_one({"chat_id": chat_id})

async def total_chat_count():
    return await db.chats.count_documents({})
