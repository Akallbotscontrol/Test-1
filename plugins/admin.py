from pyrogram import Client, filters
from info import ADMIN
from utils import get_users, get_groups, delete_user, delete_group
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
from pyrogram.types import Message
import asyncio

# /userc - List users with @username
@Client.on_message(filters.command("userc") & filters.user(ADMIN))
async def user_counter(bot, message: Message):
    total, users = await get_users()

    if total == 0:
        return await message.reply("😕 No users found in database.")

    text = f"📊 Total Users: <b>{total}</b>\n\n"
    for user in users:
        name = user.get('name', None)
        username = f"@{name}" if name else "Unknown"
        text += f"{username}\n"

    await message.reply(text)


# /groupc - List groups with link
@Client.on_message(filters.command("groupc") & filters.user(ADMIN))
async def group_counter(bot, message: Message):
    total, groups = await get_groups()

    if total == 0:
        return await message.reply("📭 No groups found in database.")

    text = f"👥 Total Groups: <b>{total}</b>\n\n"
    count = 1
    for group in groups:
        name = group.get('name', 'Unknown Group')
        group_id = group['_id']
        try:
            invite_link = (await bot.get_chat(group_id)).invite_link or "No invite link"
        except:
            invite_link = "Unavailable or Bot not in group"
        text += f"{count}. <b>{name}</b>\n{invite_link}\n\n"
        count += 1

    await message.reply(text, disable_web_page_preview=True)


# /broadcast - Send to all users
@Client.on_message(filters.command("broadcast") & filters.user(ADMIN))
async def broadcast_message(bot, message: Message):
    if not message.reply_to_message:
        return await message.reply("📌 Use this command as a reply to a message you want to broadcast.")

    reply_msg = message.reply_to_message
    users_count, users = await get_users()

    sent = await message.reply("⚡ Broadcasting started...")
    total = users_count
    success = 0
    failed = 0

    for user in users:
        user_id = user["_id"]
        try:
            await reply_msg.copy(chat_id=user_id)
            success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            continue
        except (InputUserDeactivated, UserIsBlocked, PeerIdInvalid):
            await delete_user(user_id)
            failed += 1
        except Exception as e:
            failed += 1
            print(f"❌ Failed to send to {user_id}: {e}")

        await sent.edit(f"📤 Broadcasting...\n\n✅ Sent: {success}\n❌ Failed: {failed}\n🕐 Remaining: {total - (success + failed)}")

    await sent.edit(f"✅ Broadcast Completed!\n\n📬 Total: {total}\n✅ Success: {success}\n❌ Failed: {failed}")


# /broadcast_groups - Send to all groups
@Client.on_message(filters.command("broadcast_groups") & filters.user(ADMIN))
async def broadcast_groups(bot, message: Message):
    if not message.reply_to_message:
        return await message.reply("📌 Use this command as a reply to a message you want to broadcast.")

    reply_msg = message.reply_to_message
    group_count, groups = await get_groups()

    sent = await message.reply("⚡ Group broadcast started...")
    total = group_count
    success = 0
    failed = 0

    for group in groups:
        group_id = group["_id"]
        try:
            msg = await reply_msg.copy(chat_id=group_id)
            try:
                await msg.pin(disable_notification=True)
            except:
                pass
            success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            continue
        except Exception as e:
            await delete_group(group_id)
            failed += 1
            print(f"❌ Failed to send to group {group_id}: {e}")

        await sent.edit(f"📢 Broadcasting to Groups...\n\n✅ Sent: {success}\n❌ Failed: {failed}\n🕐 Remaining: {total - (success + failed)}")

    await sent.edit(f"✅ Group Broadcast Completed!\n\n📬 Total: {total}\n✅ Success: {success}\n❌ Failed: {failed}")