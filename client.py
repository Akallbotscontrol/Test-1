from info import *
from pyrogram import Client, filters
from pyrogram.handlers import CallbackQueryHandler
from utils.helpers import checksub_callback

class Bot(Client):   
    def __init__(self):
        super().__init__(   
           "vj-post-search-bot",
            api_id=API_ID,
            api_hash=API_HASH,           
            bot_token=BOT_TOKEN,
            plugins={"root": "plugins"})
            
    async def start(self):                        
        await super().start()
        
        # नया कोड: कॉलबैक हैंडलर रजिस्टर करें
        self.add_handler(CallbackQueryHandler(
            checksub_callback,
            filters.regex(r"^checksub_(\d+)$")
        ))
        
        print("Bot Started 🔧 Powered By @VJ_Botz")   
        
    async def stop(self, *args):
        await super().stop()
