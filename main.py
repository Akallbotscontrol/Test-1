from client import Bot
from session import start_userbot
import asyncio

print("Bot Starting... 🔥")

loop = asyncio.get_event_loop()
loop.create_task(start_userbot())  # Background task without blocking
Bot().run()
