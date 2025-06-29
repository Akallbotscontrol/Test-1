import os
from os import environ

API_ID       = int(environ.get("API_ID", "22289037"))
API_HASH     = environ.get("API_HASH", "ced5a994db436661f9af63c4b5247ac6")
BOT_TOKEN    = environ.get("BOT_TOKEN", "")
DATABASE_URI = environ.get("DATABASE_URI", "")
LOG_CHANNEL  = int(environ.get("LOG_CHANNEL", "-1002273915928"))
ADMIN        = int(environ.get("ADMIN", "7037505654"))
CHANNEL      = environ.get("CHANNEL", "@RMCBACKUP")
