from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import *
from utils import *
from plugins.generate import database
from pyrogram.errors import FloodWait
import asyncio

# Commands to exclude from search
IGNORED_COMMANDS = [
    "start", "id", "verify", "connect", "disconnect",
    "fsub", "nofsub", "connections", "stats", "userc",
    "login", "logout"
]

# Auto-delete message
async def delete_after_delay(message, delay=40):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

@Client.on_message(filters.text & filters.group & ~filters.command(IGNORED_COMMANDS))
async def search(bot, message):
    query = message.text
    if not query:
        return

    # Save last query for Try Again
    await save_last_query(message.from_user.id, message.chat.id, query)

    # Force Subscribe check
    if not await force_sub(bot, message):
        return

    vj = database.find_one({"chat_id": ADMIN})
    if not vj:
        return

    group = await get_group(message.chat.id)
    verified = group.get("verified")
    channels = group.get("channels", [])

    if not verified or not channels:
        return

    from pyrogram import Client as UserClient
    User = UserClient("post_search", session_string=vj["session"], api_id=API_ID, api_hash=API_HASH)
    await User.start()

    results = ""
    unique = []

    try:
        for ch in channels:
            async for msg in User.search_messages(chat_id=ch, query=query):
                line = (msg.text or msg.caption or "").split("\n")[0]
                if not line:
                    continue
                uid = f"{line[:50]}{msg.link}"
                if uid in unique:
                    continue
                unique.append(uid)
                results += f"<b>• {line}</b>\n🔗 {msg.link}\n\n"
                if len(unique) >= 10:
                    break
            if len(unique) >= 10:
                break
        await User.stop()
    except Exception as e:
        print("Search error:", e)

    if results:
        sent = await message.reply(
            f"<u>Here are your results {message.from_user.mention} 👇</u>\n\n🔎 Powered By {CHANNEL}\n\n{results}",

            disable_web_page_preview=True
        )
        asyncio.create_task(delete_after_delay(sent))
    else:
        clean = query.replace(" ", "+")
        btn = [[
            InlineKeyboardButton("🔍 Google", url=f"https://www.google.com/search?q={clean}"),
            InlineKeyboardButton("📬 Request Admin", callback_data=f"req_{message.id}")
        ]]
        sent = await message.reply_photo(
            photo="https://www.imghippo.com/i/CrF9619b.jpg",
            caption=f"❌ No results found for: <code>{query}</code>\nTry different keywords or ask admin.",
            reply_markup=InlineKeyboardMarkup(btn)
        )
        asyncio.create_task(delete_after_delay(sent))

@Client.on_callback_query(filters.regex("^checksub_"))
async def retry(bot, update):
    user_id = int(update.data.split("_")[-1])
    chat_id = update.message.chat.id

    class DummyMessage:
        def __init__(self, from_user, chat):
            self.from_user = from_user
            self.chat = chat
            self.chat.id = chat_id

    dummy = DummyMessage(update.from_user, update.message.chat)

    if not await force_sub(bot, dummy):
        return await update.answer("❌ You still haven’t joined!", show_alert=True)

    query = await get_last_query(user_id, chat_id)
    if not query:
        return await update.answer("⚠️ No previous query found.", show_alert=True)

    await update.message.delete()

    fake = update.message
    fake.text = query
    fake.from_user = update.from_user
    await search(bot, fake)
