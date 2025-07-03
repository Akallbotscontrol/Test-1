import asyncio
from imdb import IMDb
from info import *
from utils import *
from time import time
from plugins.generate import database
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

ia = IMDb()

# Function to send long messages in chunks
async def send_message_in_chunks(client, chat_id, text):
    max_length = 4096  # Maximum length of a message
    for i in range(0, len(text), max_length):
        msg = await client.send_message(chat_id=chat_id, text=text[i:i+max_length], disable_web_page_preview=True)
        asyncio.create_task(delete_after_delay(msg, 1800))

# Function to delete a message after a certain delay
async def delete_after_delay(message: Message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

# IMDb Search (optimized)
async def search_imdb(query):
    search_results = ia.search_movie(query)
    movies = []
    
    for result in search_results[:5]:  # Get top 5 search results
        movie_id = result.movieID
        title = result.get('title', 'Unknown')
        year = result.get('year', 'Unknown')
        movie_url = f"https://www.imdb.com/title/tt{movie_id}"
        
        movies.append({'title': f"{title} ({year})", 'id': movie_id, 'url': movie_url})
    
    return movies

# Search handler
@Client.on_message(filters.text & filters.group & filters.incoming & ~filters.command(["verify", "connect", "id"]))
async def search(bot, message):
    try:
        vj = database.find_one({"chat_id": ADMIN})
        if vj is None:
            return await message.reply("**Contact Admin Then Say To Login In Bot.**")

        async with Client("post_search", session_string=vj['session'], api_hash=API_HASH, api_id=API_ID) as User:
            f_sub = await force_sub(bot, message)
            if f_sub is False:
                return

            channels = (await get_group(message.chat.id))["channels"]
            if not channels:
                return

            if message.text.startswith("/"):
                return

            query = message.text
            head = f"<u>⭕ Here are the results for {message.from_user.mention} 👇\n\n💢 Powered By </u> <b><I>@RMCBACKUP ❗</I></b>\n\n"
            results = ""

            reply_message = message.reply_to_message if message.reply_to_message else None

            # Search in channels
            for channel in channels:
                async for msg in User.search_messages(chat_id=channel, query=query):
                    name = (msg.text or msg.caption).split("\n")[0]
                    if name in results:
                        continue
                    results += f"<b><I>♻️ {name}\n🔗 {msg.link}</I></b>\n\n"

            if not results:
                movies = await search_imdb(query)

                if not movies:
                    return await message.reply(
                        "🔺 No results found on IMDb either.\n\nPlease request the admin to add the content.",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Request To Admin 🎯", callback_data=f"request_{query}")]])
                    )

                buttons = [[InlineKeyboardButton(movie['title'], callback_data=f"recheck_{movie['id']}")] for movie in movies]

                await message.reply_photo(
                    photo="https://graph.org/file/c361a803c7b70fc50d435.jpg",
                    caption="<b><I>🔻 I Couldn't find anything related to Your Query😕.\n🔺 Did you mean any of these?</I></b>",
                    reply_markup=InlineKeyboardMarkup(buttons),
                    disable_web_page_preview=False
                )
            else:
                if reply_message:
                    await reply_message.reply_text(head + results)
                else:
                    await send_message_in_chunks(bot, message.chat.id, head + results)
    except Exception as e:
        print(f"Error in search function: {e}")
        await message.reply("❗Might be spelling mistake. Please try again with correct spelling.")

# Recheck handler
@Client.on_callback_query(filters.regex(r"^recheck"))
async def recheck(bot, update):
    try:
        vj = database.find_one({"chat_id": ADMIN})
        if vj is None:
            return await update.message.edit_text("**Contact Admin Then Say To Login In Bot.**")

        async with Client("post_search", session_string=vj['session'], api_hash=API_HASH, api_id=API_ID) as User:
            clicked = update.from_user.id

            try:
                typed = update.message.reply_to_message.from_user.id
            except AttributeError:
                return await update.message.delete()

            if clicked != typed:
                return await update.answer("That's not for you! 👀", show_alert=True)

            await update.message.edit_text("**Searching..💥**")
            movie_id = update.data.split("_")[-1]
            movie = ia.get_movie(movie_id)  # Fetch IMDb movie details
            query = movie.get('title', '')

            channels = (await get_group(update.message.chat.id))["channels"]
            head = "<u>⭕ I Have Searched Again But Take Care Next Time 👇\n\n💢 Powered By </u> <b><I>@RMCBACKUP ❗</I></b>\n\n"
            results = ""

            reply_message = update.message.reply_to_message if update.message.reply_to_message else None

            # Search in channels
            for channel in channels:
                async for msg in User.search_messages(chat_id=channel, query=query):
                    name = (msg.text or msg.caption).split("\n")[0]
                    if name in results:
                        continue
                    results += f"<b><I>♻️🍿 {name}</I></b>\n\n🔗 {msg.link}</I></b>\n\n"

            if not results:
                return await update.message.edit_text(
                    "🔺 Still no results found! Please Request To Group Admin 🔻",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Request To Admin 🎯", callback_data=f"request_{movie_id}")]])
                )

            if reply_message:
                await reply_message.reply_text(head + results)
            else:
                await send_message_in_chunks(bot, update.message.chat.id, head + results)

    except Exception as e:
        await update.message.edit_text(f"❌ Error: `{e}`")

# Request handler
@Client.on_callback_query(filters.regex(r"^request"))
async def request(bot, update):
    try:
        clicked = update.from_user.id

        try:
            typed = update.message.reply_to_message.from_user.id
        except AttributeError:
            return await update.message.delete()

        if clicked != typed:
            return await update.answer("That's not for you! 👀", show_alert=True)

        admin = (await get_group(update.message.chat.id))["user_id"]
        movie_id = update.data.split("_")[1]
        movie = ia.get_movie(movie_id)
        name = movie.get('title', 'Unknown')
        url = f"https://www.imdb.com/title/tt{movie_id}"

        text = f"#RequestFromYourGroup\n\nName: {name}\nIMDb: {url}"

        if update.message.reply_to_message:
            quoted_message = update.message.reply_to_message
            text += f"\n\n<quote>{quoted_message.text or quoted_message.caption}</quote>"

        await bot.send_message(chat_id=admin, text=text, disable_web_page_preview=True)
        await update.answer("✅ Request Sent To Admin", show_alert=True)
        await update.message.delete(60)

    except Exception as e:
        await update.message.edit_text(f"❌ Error: `{e}`")
