import logging
import os
import random
import re
import string
import time
from http.cookies import SimpleCookie
from re import match as re_match
from googletrans import Translator
from typing import Union
from urllib.parse import urlparse

import cv2
import numpy as np
import psutil

from misskaty import BOT_NAME, UBOT_NAME, botStartTime
from misskaty.core.decorator import asyncify
from misskaty.helper.http import fetch
from misskaty.helper.human_read import get_readable_time
from misskaty.plugins import ALL_MODULES

LOGGER = logging.getLogger("MissKaty")
URL_REGEX = r"(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])"
GENRES_EMOJI = {
    "Action": "👊",
    "Adventure": random.choice(["🪂", "🧗‍♀", "🌋"]),
    "Family": "👨‍",
    "Musical": "🎸",
    "Comedy": "🤣",
    "Drama": " 🎭",
    "Ecchi": random.choice(["💋", "🥵"]),
    "Fantasy": random.choice(["🧞", "🧞‍♂", "🧞‍♀", "🌗"]),
    "Hentai": "🔞",
    "History": "📜",
    "Horror": "☠",
    "Mahou Shoujo": "☯",
    "Mecha": "🤖",
    "Music": "🎸",
    "Mystery": "🔮",
    "Psychological": "♟",
    "Romance": "💞",
    "Sci-Fi": "🛸",
    "Slice of Life": random.choice(["☘", "🍁"]),
    "Sports": "⚽️",
    "Supernatural": "🫧",
    "Thriller": random.choice(["🥶", "🔪", "🤯"]),
}


async def gtranslate(text, source="auto", target="id"):
    async with Translator() as translator:
         result = await translator.translate(text, src=source, dest=target)
         return result
        

def is_url(url):
    url = re_match(URL_REGEX, url)
    return bool(url)


async def bot_sys_stats():
    bot_uptime = int(time.time() - botStartTime)
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    process = psutil.Process(os.getpid())
    return f"""
{UBOT_NAME}@{BOT_NAME}
------------------
UPTIME: {get_readable_time(bot_uptime)}
BOT: {round(process.memory_info()[0] / 1024**2)} MB
CPU: {cpu}%
RAM: {mem}%
DISK: {disk}%

TOTAL PLUGINS: {len(ALL_MODULES)}
"""


def remove_N(seq):
    i = 1
    while i < len(seq):
        if seq[i] == seq[i - 1]:
            del seq[i]
            i -= 1
        else:
            i += 1


def get_random_string(length: int = 5):
    text_str = "".join(
        random.SystemRandom().choice(string.ascii_letters + string.digits)
        for _ in range(length)
    )
    return text_str.upper()


async def rentry(teks):
    # buat dapetin cookie
    cookie = SimpleCookie()
    kuki = (await fetch.get("https://rentry.co")).cookies
    cookie.load(kuki)
    kukidict = {key: value.value for key, value in cookie.items()}
    # headernya
    header = {"Referer": "https://rentry.co"}
    payload = {"csrfmiddlewaretoken": kukidict["csrftoken"], "text": teks}
    return (
        (
            await fetch.post(
                "https://rentry.co/api/new",
                data=payload,
                headers=header,
                cookies=kukidict,
            )
        )
        .json()
        .get("url")
    )


def get_provider(url):
    def pretty(names):
        name = names[1]
        if names[0] == "play":
            name = "Google Play Movies"
        elif names[0] == "hbogoasia":
            name = "HBO Go Asia"
        elif names[0] == "maxstream":
            name = "Max Stream"
        elif names[0] == "klikfilm":
            name = "Klik Film"
        return name.title()

    netloc = urlparse(url).netloc
    return pretty(netloc.split("."))


async def search_jw(movie_name: str, locale: Union[str, None] = "ID"):
    m_t_ = ""
    try:
        response = (
            await fetch.get(
                f"https://yasirapi.eu.org/justwatch?q={movie_name}&locale={locale}"
            )
        ).json()
    except:
        return m_t_
    if not response.get("results"):
        LOGGER.error("JustWatch API Error or got Rate Limited.")
        return m_t_
    for item in response["results"]["data"]["popularTitles"]["edges"]:
        if item["node"]["content"]["title"] == movie_name:
            t_m_ = []
            for offer in item["node"].get("offers", []):
                url = offer["standardWebURL"]
                if url not in t_m_:
                    p_o = get_provider(url)
                    m_t_ += f"<a href='{url}'>{p_o}</a> | "
                t_m_.append(url)
        if m_t_ != "":
            m_t_ = m_t_[:-2].strip()
        break
    return m_t_


def isValidURL(str):
    # Regex to check valid URL
    regex = (
        "((http|https)://)(www.)?"
        + "[a-zA-Z0-9@:%._\\+~#?&//=]"
        + "{2,256}\\.[a-z]"
        + "{2,6}\\b([-a-zA-Z0-9@:%"
        + "._\\+~#?&//=]*)"
    )

    # Compile the ReGex
    p = re.compile(regex)

    # If the string is empty
    # return false
    return False if str is None else bool((re.search(p, str)))


@asyncify
def gen_trans_image(source, path):
    # load image
    img = cv2.imread(source)

    # convert to graky
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # threshold input image as mask
    mask = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)[1]

    # negate mask
    mask = 255 - mask

    # apply morphology to remove isolated extraneous noise
    # use borderconstant of black since foreground touches the edges
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # anti-alias the mask -- blur then stretch
    # blur alpha channel
    mask = cv2.GaussianBlur(
        mask, (0, 0), sigmaX=2, sigmaY=2, borderType=cv2.BORDER_DEFAULT
    )

    # linear stretch so that 127.5 goes to 0, but 255 stays 255
    mask = (2 * (mask.astype(np.float32)) - 255.0).clip(0, 255).astype(np.uint8)

    # put mask into alpha channel
    result = img.copy()
    result = cv2.cvtColor(result, cv2.COLOR_BGR2BGRA)
    result[:, :, 3] = mask

    # save resulting masked image
    cv2.imwrite(path, result)
    return path
