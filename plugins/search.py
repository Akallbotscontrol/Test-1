from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import *
from utils import *
from time import time
from plugins.generate import database
from pyrogram.errors import FloodWait
import asyncio

# Auto delete message after delay
async def delete_after_delay(message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

@Client.on_message(filters.text & filters.group)
async def search(bot, message):
    query = message.text
    if not query:
        return

    vj = database.find_one({"chat_id": ADMIN})
    if not vj:
        return

    group = await get_group(message.chat.id)
    user_id = group.get("user_id")
    user_name = group.get("user_name")
    verified = group.get("verified")
    channels = group.get("channels", [])

    if not verified:
        return

    # Save query for Try Again
    await save_last_query(message.from_user.id, message.chat.id, query)

    # Force Subscribe check
    if not await force_sub(bot, message):
        return

    # Start user client
    User = Client("post_search", session_string=vj['session'], api_hash=API_HASH, api_id=API_ID)
    await User.start()

    results = ""
    unique = []
    head = f"<u>Here are your results {message.from_user.mention} 👇</u>\n\n🔎 Powered By {CHANNEL}\n\n"

    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                line = (msg.text or msg.caption or "").split("\n")[0]
                if not line:
                    continue
                if f"{line[:50]}{msg.link}" in unique:
                    continue
                unique.append(f"{line[:50]}{msg.link}")
                results += f"<b>• {line}</b>\n🔗 {msg.link}\n\n"
                if len(unique) >= 10:
                    break
            if len(unique) >= 10:
                break
        await User.stop()
    except Exception as e:
        print("search error:", e)

    if results:
        sent = await message.reply(head + results)
        asyncio.create_task(delete_after_delay(sent, 40))
    else:
        clean_q = query.replace(" ", "+")
        button = [[
            InlineKeyboardButton("🔍 Google", url=f"https://www.google.com/search?q={clean_q}"),
            InlineKeyboardButton("📬 Request Admin", callback_data=f"req_{message.id}")
        ]]
        sent = await message.reply_photo(
            photo="https://graph.org/file/c361a803c7b70fc50d435.jpg",
            caption=(
                f"❌ No results found for: <code>{query}</code>\n\n"
                "Try different keywords or ask the admin."
            ),
            reply_markup=InlineKeyboardMarkup(button)
        )
        asyncio.create_task(delete_after_delay(sent, 40))

@Client.on_callback_query(filters.regex("^checksub_"))
async def retry_check(bot, update):
    user_id = int(update.data.split("_")[-1])
    chat_id = update.message.chat.id

    class DummyMessage:
        def __init__(self, from_user, chat):
            self.from_user = from_user
            self.chat = chat
            self.chat.id = chat_id

    dummy = DummyMessage(update.from_user, update.message.chat)

    # Re-check FSub
    if not await force_sub(bot, dummy):
        return await update.answer("❌ You still haven’t joined!", show_alert=True)

    query = await get_last_query(user_id, chat_id)
    if not query:
        return await update.answer("⚠️ No previous query found.", show_alert=True)

    await update.message.delete()

    fake_message = update.message
    fake_message.text = query
    fake_message.from_user = update.from_user
    await search(bot, fake_message)
