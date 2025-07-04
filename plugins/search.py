from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import *
from utils import get_group, save_last_query, get_last_query, force_sub
from plugins.generate import database
from pyrogram.errors import FloodWait
import asyncio

# Auto delete utility
async def delete_after(message, delay=40):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

@Client.on_message(filters.text & filters.group)
async def search(bot, message):
    query = message.text.strip()
    if not query:
        return

    # Save user query for Try Again feature
    await save_last_query(message.from_user.id, message.chat.id, query)

    # Check Force Subscribe
    fsub_ok = await force_sub(bot, message)
    if not fsub_ok:
        return

    group = await get_group(message.chat.id)
    channels = group.get("channels", [])
    if not channels:
        return await message.reply("⚠️ No channels connected to this group.")

    vj = database.find_one({"chat_id": ADMIN})
    if not vj:
        return await message.reply("❌ Admin not logged in.")

    results = ""
    unique_ids = set()

    from pyrogram import Client as UserClient
    User = UserClient("post_search", session_string=vj["session"], api_id=API_ID, api_hash=API_HASH)
    await User.start()

    for ch in channels[:3]:  # Search only top 3 channels
        async for msg in User.search_messages(chat_id=ch, query=query, limit=5):
            content = (msg.text or msg.caption or "").split("\n")[0]
            if not content:
                continue
            uid = f"{content[:40]}{msg.link}"
            if uid in unique_ids:
                continue
            unique_ids.add(uid)
            results += f"🔹 <b>{content}</b>\n🔗 {msg.link}\n\n"
            if len(unique_ids) >= 5:
                break
        if len(unique_ids) >= 5:
            break

    await User.stop()

    if results:
        reply = await message.reply(
            f"<u>🔍 Search results for:</u> <b>{query}</b>\n\n{results}",
            disable_web_page_preview=True
        )
        asyncio.create_task(delete_after(reply, 40))
    else:
        reply = await message.reply("❌ No results found. Try something else.")
        asyncio.create_task(delete_after(reply, 40))

@Client.on_callback_query(filters.regex("^checksub_"))
async def retry_query(bot, update):
    user_id = int(update.data.split("_")[-1])
    chat_id = update.message.chat.id

    class DummyMessage:
        def __init__(self, user, chat):
            self.from_user = user
            self.chat = chat
            self.chat.id = chat

    dummy = DummyMessage(update.from_user, update.message.chat)

    is_member = await force_sub(bot, dummy)
    if not is_member:
        return await update.answer("❌ Still not subscribed!", show_alert=True)

    query = await get_last_query(user_id, chat_id)
    if not query:
        return await update.answer("⚠️ No recent query found.", show_alert=True)

    await update.message.delete()

    fake_message = update.message
    fake_message.text = query
    fake_message.from_user = update.from_user
    await search(bot, fake_message)
