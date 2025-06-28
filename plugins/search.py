# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import asyncio
import re
from info import *
from utils import *
from time import time 
from plugins.generate import database
from pyrogram import Client, filters 
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message 

# Global cache for force sub status to avoid repeated checks
fsub_cache = {}

async def send_message_in_chunks(client, chat_id, text):
    max_length = 4096
    for i in range(0, len(text), max_length):
        msg = await client.send_message(
            chat_id=chat_id,
            text=text[i:i+max_length],
            disable_web_page_preview=True
        )
        asyncio.create_task(delete_after_delay(msg, 40))

async def delete_after_delay(message: Message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

def clean_query(query):
    """Remove special characters from query for URL formatting"""
    return re.sub(r"[^\w\s]", "", query).strip().replace(" ", "+")

async def check_fsub_status(bot, chat_id, user_id):
    """Check if user is in force sub channel with caching"""
    cache_key = f"{chat_id}_{user_id}"
    
    if cache_key in fsub_cache:
        return fsub_cache[cache_key]
    
    group_data = await get_group(chat_id)
    fsub_channel = group_data.get("fsub")
    
    # If no force sub channel set, allow access
    if not fsub_channel:
        fsub_cache[cache_key] = True
        return True
    
    try:
        # Check if user is in channel
        member = await bot.get_chat_member(fsub_channel, user_id)
        status = member.status in ("member", "administrator", "creator")
        fsub_cache[cache_key] = status
        return status
    except:
        # If any error occurs, assume not member
        fsub_cache[cache_key] = False
        return False

@Client.on_message(filters.text & filters.group & filters.incoming & ~filters.command(["verify", "connect", "id"]))
async def search(bot, message):
    vj = database.find_one({"chat_id": ADMIN})
    if not vj:
        return
    
    # Skip processing if message is empty after cleanup
    if not message.text.strip():
        return
    
    # Check force subscription status
    fsub_status = await check_fsub_status(bot, message.chat.id, message.from_user.id)
    
    if not fsub_status:
        group_data = await get_group(message.chat.id)
        fsub_channel = group_data.get("fsub")
        
        if not fsub_channel:
            return
        
        try:
            channel = await bot.get_chat(fsub_channel)
            buttons = [[
                InlineKeyboardButton("Join Channel", url=channel.invite_link),
                InlineKeyboardButton("Refresh ♻️", callback_data=f"fsub_refresh_{message.id}")
            ]]
            
            msg = await message.reply_photo(
                photo="https://graph.org/file/2b2f4a0f3e7d3a3f0f3e7.jpg",
                caption=(
                    f"👋 Hello {message.from_user.mention}!\n\n"
                    "🔒 **Access Restricted**\n"
                    "You need to join our channel to use this bot.\n\n"
                    f"👉 Please join: {channel.title}\n"
                    "After joining, click the Refresh button below!"
                ),
                reply_markup=InlineKeyboardMarkup(buttons),
                quote=True
            )
            asyncio.create_task(delete_after_delay(msg, 120))
            return
        except Exception as e:
            print(f"FSub error: {e}")
            return
    
    channels = (await get_group(message.chat.id)).get("channels", [])
    if not channels:
        return
    
    query = message.text.strip()
    head = f"<u>⭕ Here are the results {message.from_user.mention} 👇</u>\n\n💢 Powered By <b><I>@RMCBACKUP ❗</I></b>\n\n"
    results = ""
    unique_results = set()
    
    try:
        User = Client("post_search", session_string=vj['session'], api_hash=API_HASH, api_id=API_ID)
        await User.start()
        
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name_line = (msg.text or msg.caption or "").split("\n")[0]
                if not name_line:
                    continue
                    
                # Use first line + link as unique identifier
                result_id = f"{name_line[:50]}{msg.link}"
                if result_id in unique_results:
                    continue
                    
                unique_results.add(result_id)
                results += f"<b><I>♻️ {name_line}</I></b>\n🔗 {msg.link}\n\n"
                
        await User.stop()
        
        if results:
            await send_message_in_chunks(bot, message.chat.id, head + results)
        else:
            clean_q = clean_query(query)
            buttons = [
                [
                    InlineKeyboardButton("🔍 Google Search", url=f"https://www.google.com/search?q={clean_q}"),
                    InlineKeyboardButton("📬 Request Admin", callback_data=f"req_{message.id}")
                ]
            ]
            msg = await message.reply_photo(
                photo="https://graph.org/file/c361a803c7b70fc50d435.jpg",
                caption=(
                    f"<b>❌ No results found for:</b> <code>{query}</code>\n\n"
                    "<i>• Try searching with different keywords\n"
                    "• Check spelling\n"
                    "• Request admin if content should be available</i>"
                ),
                reply_markup=InlineKeyboardMarkup(buttons),
                quote=True
            )
            asyncio.create_task(delete_after_delay(msg, 40))
            
    except Exception as e:
        print(f"Search error: {e}")

@Client.on_callback_query(filters.regex(r"^req_"))
async def request_admin(bot, update):
    message_id = int(update.data.split("_")[1])
    try:
        message = await bot.get_messages(update.message.chat.id, message_id)
        query = message.text.strip()
    except:
        return await update.answer("Original message not found", show_alert=True)
    
    admin_id = (await get_group(update.message.chat.id)).get("user_id")
    if not admin_id:
        return await update.answer("Admin not configured", show_alert=True)
    
    try:
        await bot.send_message(
            chat_id=admin_id,
            text=(
                f"#ContentRequest\nFrom: {update.from_user.mention}\n"
                f"Group: {update.message.chat.title}\n"
                f"Query: <code>{query}</code>"
            ),
            disable_web_page_preview=True
        )
        await update.answer("✅ Request sent to admin", show_alert=True)
        await update.message.edit_caption(
            caption=f"<b>📬 Request sent for:</b> <code>{query}</code>",
            reply_markup=None
        )
        asyncio.create_task(delete_after_delay(update.message, 10))
    except Exception as e:
        await update.answer("❌ Failed to send request", show_alert=True)

@Client.on_callback_query(filters.regex(r"^fsub_refresh_"))
async def refresh_fsub_status(bot, update):
    message_id = int(update.data.split("_")[-1])
    user_id = update.from_user.id
    
    try:
        # Clear cache for this user
        cache_key = f"{update.message.chat.id}_{user_id}"
        if cache_key in fsub_cache:
            del fsub_cache[cache_key]
        
        # Re-check status
        fsub_status = await check_fsub_status(bot, update.message.chat.id, user_id)
        
        if fsub_status:
            await update.answer("✅ Access granted! You can now use the bot", show_alert=True)
            await update.message.delete()
        else:
            await update.answer("❌ You haven't joined the channel yet", show_alert=True)
    except Exception as e:
        await update.answer("❌ Refresh failed, please try again", show_alert=True)
