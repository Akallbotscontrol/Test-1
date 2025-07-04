import os
import logging
from pyrogram import Client, filters, enums
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified, UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.ia_filterdb import Media, get_file_details
from database.users_chats_db import db
from info import ADMINS, LOG_CHANNEL, FILE_STORE_CHANNEL, PUBLIC_FILE_STORE, CUSTOM_CAPTION
from utils import get_settings, is_subscribed, save_group_settings, temp

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BUTTONS = {}
BOT = {}

@Client.on_message(filters.command('leave') & filters.user(ADMINS))
async def leave_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat id')
    chat = message.command[1]
    try:
        chat = int(chat)
    except:
        chat = chat
    try:
        buttons = [[
            InlineKeyboardButton('𝚂𝚄𝙿𝙿𝙾𝚁𝚃', url=f'https://t.me/{SUPPORT_CHAT}')
        ]]
        reply_markup=InlineKeyboardMarkup(buttons)
        await bot.send_message(
            chat_id=chat,
            text='<b>Hello Friends, \nMy admin has told me to leave from group so i go! If you wanna add me again contact my support group.</b>',
            reply_markup=reply_markup,
        )

        await bot.leave_chat(chat)
    except Exception as e:
        await message.reply(f'Error - {e}')

@Client.on_message(filters.command('disable') & filters.user(ADMINS))
async def disable_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat id')
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "No reason Provided"
    try:
        chat_ = int(chat)
    except:
        return await message.reply('Give Me A Valid Chat ID')
    cha_t = await db.get_chat(int(chat_))
    if not cha_t:
        return await message.reply("Chat Not Found In DB")
    if cha_t['is_disabled']:
        return await message.reply(f"This chat is already disabled:\nReason-<code> {cha_t['reason']} </code>")
    await db.disable_chat(int(chat_), reason)
    temp.BANNED_CHATS.append(int(chat_))
    await message.reply('Chat Successfully Disabled')
    try:
        buttons = [[
            InlineKeyboardButton('𝚂𝚄𝙿𝙿𝙾𝚁𝚃', url=f'https://t.me/{SUPPORT_CHAT}')
        ]]
        reply_markup=InlineKeyboardMarkup(buttons)
        await bot.send_message(
            chat_id=chat_, 
            text=f'<b>Hello Friends, \nMy admin has told me to leave from group so i go! If you wanna add me again contact my support group.</b> \nReason : <code>{reason}</code>',
            reply_markup=reply_markup)
        await bot.leave_chat(chat_)
    except Exception as e:
        await message.reply(f"Error - {e}")


@Client.on_message(filters.command('enable') & filters.user(ADMINS))
async def re_enable_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat id')
    chat = message.command[1]
    try:
        chat_ = int(chat)
    except:
        return await message.reply('Give Me A Valid Chat ID')
    sts = await db.get_chat(int(chat))
    if not sts:
        return await message.reply("Chat Not Found In DB !")
    if not sts.get('is_disabled'):
        return await message.reply('This chat is not yet disabled.')
    await db.re_enable_chat(int(chat_))
    temp.BANNED_CHATS.remove(int(chat_))
    await message.reply("Chat Successfully re-enabled")


@Client.on_message(filters.command('stats') & filters.incoming))
async def get_ststs(bot, message):
    rju = await message.reply('Fetching stats..')
    total_users = await db.total_users_count()
    totl_chats = await db.total_chat_count()
    files = await Media.count_documents()
    size = await db.get_db_size()
    free = 536870912 - size
    size = get_size(size)
    free = get_size(free)
    await rju.edit(script.STATUS_TXT.format(files, total_users, totl_chats, size, free))


@Client.on_message(filters.command('invite') & filters.user(ADMINS))
async def gen_invite(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat id')
    chat = message.command[1]
    try:
        chat = int(chat)
    except:
        return await message.reply('Give Me A Valid Chat ID')
    try:
        link = await bot.create_chat_invite_link(chat)
    except ChatAdminRequired:
        return await message.reply("Invite Link Generation Failed, Iam Not Having Sufficient Rights")
    except Exception as e:
        return await message.reply(f'Error {e}')
    await message.reply(f'Here is your Invite Link {link.invite_link}')

async def get_subscribed_users(bot):
    # ... (rest of the function remains)
    pass

async def get_poster(movie, auto=False):
    # ... (rest of the function remains)
    pass

async def get_shortlink(link):
    # ... (rest of the function remains)
    pass

async def get_verify_status(user_id):
    # ... (rest of the function remains)
    pass

async def update_verify_status(user_id, date, time, plan):
    # ... (rest of the function remains)
    pass

def get_size(size):
    # ... (rest of the function remains)
    pass

def split_list(l, n):
    # ... (rest of the function remains)
    pass

def get_settings(group_id):
    # ... (rest of the function remains)
    pass

async def save_group_settings(group_id, key, value):
    # ... (rest of the function remains)
    pass

async def is_check_admin(bot, chat_id, user_id):
    # ... (rest of the function remains)
    pass

async def allow_user(bot, user_id, file_id, chat_id):
    # ... (rest of the function remains)
    pass

async def get_shortlink(shortner, link):
    # ... (rest of the function remains)
    pass

async def get_tutorial(chat_id):
    # ... (rest of the function remains)
    pass

# Changed: Removed @bot.on_callback_query decorator
async def checksub_callback(client, callback_query):
    query = callback_query
    user_id = int(query.data.split("_")[1])
    if not await is_subscribed(client, query):
        try:
            invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL))
        except ChatAdminRequired:
            await query.answer("I am not admin in the channel", show_alert=True)
            return
        await client.send_message(
            chat_id=user_id,
            text=f"**Please Join My Updates Channel to use this Bot!**\n\n"
                 f"Due to Overload, Only Channel Subscribers can use the Bot!",
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("❣️ 𝙹𝙾𝙸𝙽 𝚄𝙿𝙳𝙰𝚃𝙴𝚂 𝙲𝙷𝙰𝙽𝙽𝙴𝙻 ❣️", url=invite_link.invite_link)
                ]]
            )
        )
        await query.answer("Please check your DM and join channel!", show_alert=True)
        return
    await query.answer()
    await client.send_message(
        chat_id=user_id,
        text=f"Thank you for joining! Now you can start using the bot."
    )

# Changed: Removed @bot.on_message decorator
async def button(client, msg):
    if msg.text.startswith('/'):
        return
    data = msg.data
    if data == "close":
        await msg.message.delete()

# Changed: Removed @bot.on_message decorator
async def auto_filter(client, msg, spoll=False):
    # ... (rest of the function remains unchanged)
    pass

# Changed: Removed @bot.on_message decorator
async def global_filters(client, message, text=False):
    # ... (rest of the function remains unchanged)
    pass
