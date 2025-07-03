import asyncio
from info import *
from pyrogram import enums, filters  # Add filters import
from imdb import Cinemagoer
from pymongo.errors import DuplicateKeyError
from pyrogram.errors import UserNotParticipant, FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton

dbclient = AsyncIOMotorClient(DATABASE_URI)
db = dbclient["Channel-Filter"]
grp_col = db["GROUPS"]
user_col = db["USERS"]
dlt_col = db["Auto-Delete"]

ia = Cinemagoer()

# ... (keep existing functions: add_group, get_group, update_group, etc) ...

async def force_sub(bot, message):
    # ... (existing force_sub function) ...

# Callback handler for "Try Again" button
@bot.on_callback_query(filters.regex(r"^checksub_(\d+)$"))
async def checksub_callback(client, callback_query):
    user_id = int(callback_query.matches[0].group(1))
    chat_id = callback_query.message.chat.id
    group = await get_group(chat_id)
    
    if not group or not group.get("f_sub"):
        await callback_query.answer("Force subscription is disabled!", show_alert=True)
        return

    f_sub = group["f_sub"]
    try:
        # Get updated channel invite link
        f_link = (await client.get_chat(f_sub)).invite_link
        
        # Check user's status in channel
        member = await client.get_chat_member(f_sub, user_id)
        
        if member.status == enums.ChatMemberStatus.BANNED:
            await callback_query.answer("You're banned in our channel!", show_alert=True)
            await asyncio.sleep(10)
            await client.ban_chat_member(chat_id, user_id)
            await callback_query.message.edit_text("🚫 User banned for being banned in channel")
            return
            
        if member.status in (enums.ChatMemberStatus.OWNER, 
                            enums.ChatMemberStatus.ADMINISTRATOR, 
                            enums.ChatMemberStatus.MEMBER):
            # Unrestrict user
            await client.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True
                )
            )
            # Update success message
            await callback_query.message.edit_text(
                f"✅ Thanks for joining! You can now send messages.",
                reply_markup=None
            )
        else:
            await callback_query.answer("❌ Still not joined! Join first.", show_alert=True)
            
    except UserNotParticipant:
        await callback_query.answer("❌ Still not joined! Join first.", show_alert=True)
    except Exception as e:
        await callback_query.answer("⚠️ Error checking status. Try again.", show_alert=True)
        admin_id = group["user_id"]
        await client.send_message(admin_id, f"❌ Checksub error:\n`{str(e)}`")

# ... (keep existing broadcast_messages function) ...
