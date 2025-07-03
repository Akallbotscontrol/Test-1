import asyncio
from info import *
from pyrogram import enums, filters
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

async def add_group(group_id, group_name, user_name, user_id, channels, f_sub, verified):
    data = {"_id": group_id, "name":group_name, 
            "user_id":user_id, "user_name":user_name,
            "channels":channels, "f_sub":f_sub, "verified":verified}
    try:
       await grp_col.insert_one(data)
    except DuplicateKeyError:
       pass

async def get_group(id):
    data = {'_id':id}
    group = await grp_col.find_one(data)
    return dict(group) if group else None

async def update_group(id, new_data):
    data = {"_id":id}
    new_value = {"$set": new_data}
    await grp_col.update_one(data, new_value)

async def delete_group(id):
    data = {"_id":id}
    await grp_col.delete_one(data)
    
async def delete_user(id):
    data = {"_id":id}
    await user_col.delete_one(data)

async def get_groups():
    count  = await grp_col.count_documents({})
    cursor = grp_col.find({})
    list   = await cursor.to_list(length=int(count))
    return count, list

async def add_user(id, name):
    data = {"_id":id, "name":name}
    try:
       await user_col.insert_one(data)
    except DuplicateKeyError:
       pass

async def get_users():
    count  = await user_col.count_documents({})
    cursor = user_col.find({})
    list   = await cursor.to_list(length=int(count))
    return count, list

async def search_imdb(query):
    try:
       int(query)
       movie = ia.get_movie(query)
       return movie["title"]
    except:
       movies = ia.search_movie(query, results=10)
       list = []
       for movie in movies:
           title = movie["title"]
           try: year = f" - {movie['year']}"
           except: year = ""
           list.append({"title":title, "year":year, "id":movie.movieID})
       return list

async def force_sub(bot, message):
    """Check if user has joined the channel without banning/restricting"""
    group = await get_group(message.chat.id)
    if not group:
        return True  # No group config found, allow message
    
    f_sub = group["f_sub"]
    if not f_sub:
        return True  # Force sub not enabled
    
    try:
        # Check user's status in channel
        member = await bot.get_chat_member(f_sub, message.from_user.id)
        
        # Allowed statuses: OWNER, ADMINISTRATOR, MEMBER
        allowed_statuses = [
            enums.ChatMemberStatus.OWNER,
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.MEMBER
        ]
        
        if member.status in allowed_statuses:
            return True
            
    except UserNotParticipant:
        # User hasn't joined the channel
        pass
    except Exception as e:
        # Log error but allow the message to avoid disruption
        admin = group["user_id"]
        await bot.send_message(admin, f"❌ Error in Fsub:\n`{str(e)}`")
        return True
    
    # User hasn't joined the channel - show join prompt
    try:
        f_link = (await bot.get_chat(f_sub)).invite_link
        await message.reply(
            f"<b>🚫 Hi {message.from_user.mention}!</b>\n\n"
            "📌 To use this bot, please join our channel first\n\n"
            "👉 After joining, click the 'Try Again' button below",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Join Channel", url=f_link)],
                [InlineKeyboardButton("🔄 Try Again", callback_data=f"checksub_{message.from_user.id}")]
            ]),
            quote=True
        )
    except Exception as e:
        admin = group["user_id"]
        await bot.send_message(admin, f"❌ Error sending Fsub message:\n`{str(e)}`")
    
    return False

@bot.on_callback_query(filters.regex(r"^checksub_(\d+)$"))
async def checksub_callback(client, callback_query):
    """Handle 'Try Again' button clicks"""
    user_id = int(callback_query.matches[0].group(1))
    
    # Verify the clicker is the same user
    if callback_query.from_user.id != user_id:
        await callback_query.answer("This button is not for you!", show_alert=True)
        return
    
    chat_id = callback_query.message.chat.id
    group = await get_group(chat_id)
    
    if not group or not group.get("f_sub"):
        await callback_query.answer("Force subscription is disabled now!", show_alert=True)
        await callback_query.message.delete()
        return
    
    f_sub = group["f_sub"]
    
    try:
        # Check user's current status
        member = await client.get_chat_member(f_sub, user_id)
        
        # Allowed statuses
        allowed_statuses = [
            enums.ChatMemberStatus.OWNER,
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.MEMBER
        ]
        
        if member.status in allowed_statuses:
            # User has joined - update message
            await callback_query.message.edit_text(
                f"✅ Thanks for joining {callback_query.from_user.mention}!\n"
                "You can now use the bot normally",
                reply_markup=None
            )
            await callback_query.answer("Verification successful!", show_alert=False)
            
            # Delete the message after 5 seconds
            await asyncio.sleep(5)
            await callback_query.message.delete()
            return
    except Exception as e:
        # Log error but proceed to show join prompt
        admin = group["user_id"]
        await client.send_message(admin, f"❌ Checksub error:\n`{str(e)}`")
    
    # User still hasn't joined - show updated prompt
    try:
        f_link = (await client.get_chat(f_sub)).invite_link
        await callback_query.message.edit_text(
            f"<b>🚫 Hi {callback_query.from_user.mention}!</b>\n\n"
            "📌 You still haven't joined our channel\n\n"
            "👉 Please join using the button below, then click 'Try Again'",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Join Channel", url=f_link)],
                [InlineKeyboardButton("🔄 Try Again", callback_data=f"checksub_{user_id}")]
            ])
        )
        await callback_query.answer("Please join the channel first!", show_alert=True)
    except Exception as e:
        await callback_query.answer("Error updating message. Please try again.", show_alert=True)

async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await delete_user(int(user_id))
        logging.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        logging.info(f"{user_id} -Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await delete_user(int(user_id))
        logging.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        return False, "Error"
