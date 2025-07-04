from pyrogram import Client, filters
from info import *
from utils import *
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
import asyncio

# 📤 Broadcast to Users
@Client.on_message(filters.command("broadcast") & filters.user(ADMIN))
async def broadcast_message(bot, message):
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


# 📤 Broadcast to Groups
@Client.on_message(filters.command("broadcast_groups") & filters.user(ADMIN))
async def broadcast_groups(bot, message):
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