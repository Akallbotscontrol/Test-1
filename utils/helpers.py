import asyncio
from info import *
from pyrogram import enums
from pymongo.errors import DuplicateKeyError
from pyrogram.errors import UserNotParticipant
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# MongoDB Setup
dbclient = AsyncIOMotorClient(DATABASE_URI)
db       = dbclient["Channel-Filter"]
grp_col  = db["GROUPS"]
user_col = db["USERS"]
query_col = db["LAST_QUERY"]

# ➤ Group Functions
async def add_group(group_id, group_name, user_name, user_id, channels, f_sub, verified):
    data = {
        "_id": group_id,
        "name": group_name,
        "user_id": user_id,
        "user_name": user_name,
        "channels": channels,
        "f_sub": f_sub,
        "verified": verified
    }
    try:
        await grp_col.insert_one(data)
    except DuplicateKeyError:
        pass

async def get_group(id):
    group = await grp_col.find_one({'_id': id})
    return dict(group) if group else None

async def update_group(id, new_data):
    await grp_col.update_one({"_id": id}, {"$set": new_data})

async def delete_group(id):
    await grp_col.delete_one({"_id": id})

# ➤ User Functions
async def add_user(id, name):
    try:
        await user_col.insert_one({"_id": id, "name": name})
    except DuplicateKeyError:
        pass

async def get_users():
    count = await user_col.count_documents({})
    users = await user_col.find({}).to_list(length=count)
    return count, users

async def get_groups():
    count = await grp_col.count_documents({})
    groups = await grp_col.find({}).to_list(length=count)
    return count, groups

# ➤ Last Search Query Save (For Try Again Feature)
async def save_last_query(user_id, chat_id, query):
    await query_col.update_one(
        {"_id": f"{chat_id}_{user_id}"},
        {"$set": {"query": query}},
        upsert=True
    )

async def get_last_query(user_id, chat_id):
    record = await query_col.find_one({"_id": f"{chat_id}_{user_id}"})
    return record["query"] if record else None

# ➤ Force Subscribe Check
async def force_sub(bot, message):
    group = await get_group(message.chat.id)
    f_sub = group.get("f_sub", False)
    admin = group.get("user_id")

    if not f_sub or not message.from_user:
        return True

    try:
        f_link = (await bot.get_chat(f_sub)).invite_link
        member = await bot.get_chat_member(f_sub, message.from_user.id)

        # User joined? Then allow.
        if member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return True

    except UserNotParticipant:
        pass  # User not joined

    except Exception as e:
        await bot.send_message(admin, f"❌ Error in force_sub:\n`{str(e)}`")
        return False

    # User not in channel — ask to join
    try:
        await message.reply(
            f"🔐 Hello {message.from_user.mention}, to use this bot you must join our channel first!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=f_link)],
                [InlineKeyboardButton("🔄 Try Again", callback_data=f"checksub_{message.from_user.id}")]
            ])
        )
    except:
        pass

    return False
