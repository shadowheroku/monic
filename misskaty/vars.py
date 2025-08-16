# * @author        Yasir Aris M <yasiramunandar@gmail.com>
# * @date          2023-06-21 22:12:27
# * @projectName   MissKatyPyro
# * Copyright ©YasirPedia All rights reserved
import requests
import sys
from logging import getLogger
from os import environ

import dotenv

LOGGER = getLogger("Monic")

dotenv.load_dotenv("config.env", override=True)

if YT_COOKIES := environ.get("YT_COOKIES"):
    response = requests.get(YT_COOKIES)
    if response.status_code == 200:
        with open('cookies.txt', 'w') as file:
            file.write(response.text)
            LOGGER.info("Success download YT Cookies")
    else:
        LOGGER.info("Failed download YT Cookies")

if API_ID := environ.get("API_ID", "23212132"):
    API_ID = int(API_ID)
else:
    LOGGER.error("API_ID variable is missing! Exiting now")
    sys.exit(1)
API_HASH = environ.get("API_HASH", "1c17efa86bdef8f806ed70e81b473c20")
if not API_HASH:
    LOGGER.error("API_HASH variable is missing! Exiting now")
    sys.exit(1)
BOT_TOKEN = environ.get("BOT_TOKEN", "8013665655:AAEdJiyyXhVtgBBUoCFTbs3kA5xX6EYjKjc")
if not BOT_TOKEN:
    LOGGER.error("BOT_TOKEN variable is missing! Exiting now")
    sys.exit(1)
DATABASE_URI = environ.get("DATABASE_URI", "mongodb+srv://ryumasgod:ryumasgod@cluster0.ojfkovp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
if not DATABASE_URI:
    LOGGER.error("DATABASE_URI variable is missing! Exiting now")
    sys.exit(1)
if LOG_CHANNEL := environ.get("LOG_CHANNEL", "-1003035600604"):
    LOG_CHANNEL = int(LOG_CHANNEL)

else:
    LOGGER.error("LOG_CHANNEL variable is missing! Exiting now")
    sys.exit(1)
# Optional ENV
LOG_GROUP_ID = environ.get("LOG_GROUP_ID" , "-1002800777153")
USER_SESSION = environ.get("USER_SESSION" , "BQGvJ_0Adt6lmVaTljo96G9YV0xaOi0O26V2utMXtqO1d9cySnNMh1KCQh2oqT2rxMwDjTj274JF5QDUOF1wO21nH52TvrOuqDvnuZbiOsKM7o4XeTS5CLmwJFAP0IKDvAvEgCnfVGLBGuaOJEijZNaP4nhFvtMP_sMLYjLATOsJHZLEkdz4PkJyfQZCMTV6MSR1D7BFnythV1VTBRA7qIjqYenmEZzGVHXGy4DaetN-BbDwJZmf2QIIZx90Q2-zvFl_z7-2srBWXcOYYDT5pZ1UkwtX71c1hChhmuFJHhLejZz0PWoTUyVr35GRto9J5QU4D0xGvdTaw8qi7m7qe5Gk4IZkjQAAAAHdw02OAA")
DATABASE_NAME = environ.get("DATABASE_NAME", "MONICDB")
TZ = environ.get("TZ", "Asia/Jakarta")
PORT = environ.get("PORT", 80)
COMMAND_HANDLER = environ.get("COMMAND_HANDLER", "! . /").split()
SUDO = list(
    {
        int(x)
        for x in environ.get(
            "SUDO",
            "8473262774 7732844436 8315739587",
        ).split()
    }
)
OWNER_ID = int(environ.get("OWNER_ID", 8429156335))
SUPPORT_CHAT = environ.get("SUPPORT_CHAT", "ShadowAdda")
AUTO_RESTART = environ.get("AUTO_RESTART", False)
OPENAI_KEY = environ.get("OPENAI_KEY" , "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")
GOOGLEAI_KEY = environ.get("GOOGLEAI_KEY" ,"AIzaSyDwe8fkycs07N9ki9cdrHS96J_YYUS4K1Y")
PAYDISINI_KEY = environ.get("PAYDISINI_KEY")
PAYDISINI_CHANNEL_ID = environ.get("PAYDISINI_CHANNEL_ID", "17")

## Config For AUtoForwarder
# Forward From Chat ID
FORWARD_FROM_CHAT_ID = list(
    {
        int(x)
        for x in environ.get(
            "FORWARD_FROM_CHAT_ID",
            "-1002664606508",
        ).split()
    }
)
# Forward To Chat ID
FORWARD_TO_CHAT_ID = list(
    {int(x) for x in environ.get("FORWARD_TO_CHAT_ID", "-1002800777153").split()}
)
FORWARD_FILTERS = list(set(environ.get("FORWARD_FILTERS", "video document").split()))
BLOCK_FILES_WITHOUT_EXTENSIONS = bool(
    environ.get("BLOCK_FILES_WITHOUT_EXTENSIONS", True)
)
BLOCKED_EXTENSIONS = list(
    set(
        environ.get(
            "BLOCKED_EXTENSIONS",
            "html htm json txt php gif png ink torrent url nfo xml xhtml jpg",
        ).split()
    )
)
MINIMUM_FILE_SIZE = environ.get("MINIMUM_FILE_SIZE")
CURRENCY_API = environ.get("CURRENCY_API")
