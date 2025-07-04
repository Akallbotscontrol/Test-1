from pyrogram import Client, filters
from info import ADMIN
from utils import get_groups
from pyrogram.types import Message

@Client.on_message(filters.command("groupc") & filters.user(ADMIN))
async def group_counter(bot, message: Message):
    total, groups = await get_groups()

    if total == 0:
        return await message.reply("📭 No groups found in database.")

    text = f"👥 Total Groups: <b>{total}</b>\n\n"
    for group in groups:
        name = group.get('name', 'Unknown Group')
        text += f"• <code>{name}</code>\n"

    await message.reply(text)