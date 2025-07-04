from pyrogram import Client, filters
from info import ADMIN
from utils import get_users
from pyrogram.types import Message

@Client.on_message(filters.command("userc") & filters.user(ADMIN))
async def user_counter(bot, message: Message):
    total, users = await get_users()

    if total == 0:
        return await message.reply("😕 No users found in database.")

    text = f"📊 Total Users: <b>{total}</b>\n\n"
    for user in users:
        uid = user['_id']
        name = user.get('name', 'Unknown')
        text += f"• <code>{name}</code> | <code>{uid}</code>\n"

    if len(text) > 4096:
        with open("/mnt/data/users.txt", "w", encoding="utf-8") as f:
            for user in users:
                uid = user['_id']
                name = user.get('name', 'Unknown')
                f.write(f"{name} - {uid}\n")
        await message.reply_document("/mnt/data/users.txt", caption=f"📦 Total Users: {total}")
    else:
        await message.reply(text)