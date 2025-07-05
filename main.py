from client import Bot
from session import start_userbot
import asyncio

async def run_all():
    await start_userbot()
    Bot().run()

print("Bot Starting... 🔥")
asyncio.run(run_all())
