"""
* @author        yasir <yasiramunandar@gmail.com>
* @date          2022-12-01 09:12:27
* @projectName   MissKatyPyro
* Copyright @YasirPedia All rights reserved
"""

import ast
import asyncio
import contextlib
import html
import json
import os
import re
import sys
import traceback
from logging import getLogger
from urllib.parse import quote

import aiohttp
import httpx
from bs4 import BeautifulSoup
from gtts import gTTS
from PIL import Image
from pyrogram import Client, filters
from pyrogram.errors import (
    ChatAdminRequired,
    MessageTooLong,
    QueryIdInvalid,
    UserNotParticipant,
)
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from misskaty import BOT_USERNAME, app
from misskaty.core.decorator.errors import capture_err
from misskaty.helper import fetch, gtranslate, gen_trans_image, rentry
from misskaty.vars import COMMAND_HANDLER
from utils import extract_user, get_file_id

LOGGER = getLogger("MissKaty")

__MODULE__ = "Misc"
__HELP__ = """
/carbon [text or reply to text or caption] - Make beautiful snippet code on carbon from text.
/removebg [Reply to image] - Remove background from image.
/calc - Simple math calculator using inline buttons.
/kbbi [keyword] - Search definition on KBBI (For Indonesian People)
/sof [query] - Search your problem in StackOverflow.
/google [query] - Search using Google Search.
(/tr, /trans, /translate) [lang code] - Translate text using Google Translate.
/tts - Convert Text to Voice.
/imdb [query] - Find Movie Details From IMDB.com (Available in English and Indonesia version).
/readqr [reply to photo] - Read QR Code From Photo.
/createqr [text] - Convert Text to QR Code.
/anime [query] - Search title in myanimelist.
/info - Get info user with Pic and full description if user set profile picture.
/id - Get simple user ID.
"""


def remove_html_tags(text):
    """Remove html tags from a string"""

    clean = re.compile("<.*?>")
    return re.sub(clean, "", text)


def calcExpression(text):
    try:
        return float(ast.literal_eval(text))
    except (SyntaxError, ZeroDivisionError):
        return ""
    except TypeError:
        return float(ast.literal_eval(text.replace("(", "*(")))
    except Exception as e:
        LOGGER.error(e, exc_info=True)
        return ""


def calc_btn(uid):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("DEL", callback_data=f"calc|{uid}|DEL"),
                InlineKeyboardButton("AC", callback_data=f"calc|{uid}|AC"),
                InlineKeyboardButton("(", callback_data=f"calc|{uid}|("),
                InlineKeyboardButton(")", callback_data=f"calc|{uid}|)"),
            ],
            [
                InlineKeyboardButton("7", callback_data=f"calc|{uid}|7"),
                InlineKeyboardButton("8", callback_data=f"calc|{uid}|8"),
                InlineKeyboardButton("9", callback_data=f"calc|{uid}|9"),
                InlineKeyboardButton("÷", callback_data=f"calc|{uid}|/"),
            ],
            [
                InlineKeyboardButton("4", callback_data=f"calc|{uid}|4"),
                InlineKeyboardButton("5", callback_data=f"calc|{uid}|5"),
                InlineKeyboardButton("6", callback_data=f"calc|{uid}|6"),
                InlineKeyboardButton("×", callback_data=f"calc|{uid}|*"),
            ],
            [
                InlineKeyboardButton("1", callback_data=f"calc|{uid}|1"),
                InlineKeyboardButton("2", callback_data=f"calc|{uid}|2"),
                InlineKeyboardButton("3", callback_data=f"calc|{uid}|3"),
                InlineKeyboardButton("-", callback_data=f"calc|{uid}|-"),
            ],
            [
                InlineKeyboardButton(".", callback_data=f"calc|{uid}|."),
                InlineKeyboardButton("0", callback_data=f"calc|{uid}|0"),
                InlineKeyboardButton("=", callback_data=f"calc|{uid}|="),
                InlineKeyboardButton("+", callback_data=f"calc|{uid}|+"),
            ],
        ]
    )


@app.on_message(filters.command(["calc", "calculate", "calculator"]))
async def calculate_handler(self, ctx):
    if not ctx.from_user:
        return
    await ctx.reply_text(
        text=f"Made by @{self.me.username}",
        reply_markup=calc_btn(ctx.from_user.id),
        disable_web_page_preview=True,
        quote=True,
    )


@app.on_callback_query(filters.regex("^calc"))
async def calc_cb(self, query):
    _, uid, data = query.data.split("|")
    if query.from_user.id != int(uid):
        return await query.answer("Who are you??", show_alert=True, cache_time=5)
    try:
        text = query.message.text.split("\n")[0].strip().split("=")[0].strip()
        text = "" if f"Made by @{self.me.username}" in text else text
        inpt = text + query.data
        result = ""
        if data == "=":
            result = calcExpression(text)
            text = ""
        elif data == "DEL":
            text = text[:-1]
        elif data == "AC":
            text = ""
        else:
            dot_dot_check = re.findall(r"(\d*\.\.|\d*\.\d+\.)", inpt)
            opcheck = re.findall(r"([*/\+-]{2,})", inpt)
            if not dot_dot_check and not opcheck:
                if strOperands := re.findall(r"(\.\d+|\d+\.\d+|\d+)", inpt):
                    text += data
                    result = calcExpression(text)

        text = f"{text:<50}"
        if result:
            if text:
                text += f"\n{result:>50}"
            else:
                text = result
        text += f"\n\nMade by @{self.me.username}"
        await query.message.edit_msg(
            text=text,
            disable_web_page_preview=True,
            reply_markup=calc_btn(query.from_user.id),
        )
    except Exception as error:
        LOGGER.error(error)


@app.on_cmd("removebg")
async def removebg(_, ctx: Client):
    if not ctx.reply_to_message:
        return await ctx.reply_msg("Please reply image.")
    if not ctx.reply_to_message.photo:
        return await ctx.reply_msg("Only support photo for remove background.")
    prg = await ctx.reply("Processing...")
    source = await ctx.reply_to_message.download()
    await gen_trans_image(source, f"transp_bckgrnd-{ctx.from_user.id}.png")
    await ctx.reply_document(f"transp_bckgrnd-{ctx.from_user.id}.png")
    await prg.delete_msg()
    os.remove(source)
    os.remove(f"transp_bckgrnd-{ctx.from_user.id}.png")


@app.on_cmd("kbbi")
async def kbbi_search(_, ctx: Client):
    if len(ctx.command) == 1:
        return await ctx.reply_msg("Please add keyword to search definition in kbbi")
    try:
        r = await fetch.get(f"https://yasirapi.eu.org/kbbi?kata={ctx.input}")
    except httpx.HTTPError as e:
        return await ctx.reply_msg(f"HTTP error occured: {e}")
    if r.status_code != 200:
        return await ctx.reply("Maaf, makna kata tersebut tidak ditemukan.")
    parse = r.json()
    if nomsg := parse.get("detail"):
        return await ctx.reply_msg(nomsg)
    kbbi_btn = InlineKeyboardMarkup(
        [[InlineKeyboardButton(text="Open in Web", url=parse.get("link"))]]
    )
    res = "<b>Definisi:</b>\n"
    for _, a in enumerate(parse.get("result"), start=1):
        submakna = "".join(f"{a}, " for a in a["makna"][0]["submakna"])[:-2]
        contoh = "".join(f"{a}, " for a in a["makna"][0]["contoh"])[:-2]
        kt_dasar = "".join(f"{a}, " for a in a["kata_dasar"])[:-2]
        bt_takbaku = "".join(f"{a}, " for a in a["bentuk_tidak_baku"])[:-2]
        res += f"<b>{a['nama']} ({a['makna'][0]['kelas'][0]['nama']}: {a['makna'][0]['kelas'][0]['deskripsi']})</b>\n<b>Kata Dasar:</b> {kt_dasar if kt_dasar else '-'}\n<b>Bentuk Tidak Baku:</b> {bt_takbaku if bt_takbaku else '-'}\n<b>Submakna:</b> {submakna}\n<b>Contoh:</b> {contoh if contoh else '-'}\n\n"
    await ctx.reply(f"{res}<b>By YasirPedia API</b>", reply_markup=kbbi_btn)


@app.on_cmd("carbon")
async def carbon_make(self: Client, ctx: Message):
    if ctx.reply_to_message and ctx.reply_to_message.text:
        text = ctx.reply_to_message.text
    elif ctx.reply_to_message and ctx.reply_to_message.caption:
        text = ctx.reply_to_message.caption
    elif len(ctx.command) > 1:
        text = ctx.input
    else:
        return await ctx.reply(
            "Please reply text to make carbon or add text after command."
        )
    json_data = {
        "code": text,
        "backgroundColor": "#1F816D",
    }
    with contextlib.redirect_stdout(sys.stderr):
        try:
            response = await fetch.post(
                "https://carbon.yasirapi.eu.org/api/cook", json=json_data, timeout=20
            )
        except httpx.HTTPError as exc:
            return await ctx.reply_msg(f"HTTP Exception for {exc.request.url} - {exc}")
    if response.status_code != 200:
        return await ctx.reply_photo(
            f"https://http.cat/{response.status_code}",
            caption="<b>🤧 Carbon API ERROR</b>",
        )
    fname = (
        f"carbonBY_{ctx.from_user.id if ctx.from_user else ctx.sender_chat.title}.png"
    )
    with open(fname, "wb") as e:
        e.write(response.content)
    await ctx.reply_photo(fname, caption=f"Generated by @{self.me.username}")
    os.remove(fname)


@app.on_message(filters.command("readqr", COMMAND_HANDLER))
async def readqr(c, m):
    if not m.reply_to_message:
        return await m.reply("Please reply photo that contain valid QR Code.")
    if not m.reply_to_message.photo:
        return await m.reply("Please reply photo that contain valid QR Code.")
    foto = await m.reply_to_message.download()
    myfile = {"file": (foto, open(foto, "rb"), "application/octet-stream")}
    url = "http://api.qrserver.com/v1/read-qr-code/"
    r = await fetch.post(url, files=myfile)
    os.remove(foto)
    if res := r.json()[0]["symbol"][0]["data"] is None:
        return await m.reply_msg(res)
    await m.reply_msg(
        f"<b>QR Code Reader by @{c.me.username}:</b> <code>{r.json()[0]['symbol'][0]['data']}</code>",
        quote=True,
    )


@app.on_message(filters.command("createqr", COMMAND_HANDLER))
async def makeqr(c, m):
    if m.reply_to_message and m.reply_to_message.text:
        teks = m.reply_to_message.text
    elif len(m.command) > 1:
        teks = m.text.split(None, 1)[1]
    else:
        return await m.reply(
            "Please add text after command to convert text -> QR Code."
        )
    url = f"https://api.qrserver.com/v1/create-qr-code/?data={quote(teks)}&size=300x300"
    await m.reply_photo(
        url, caption=f"<b>QR Code Maker by @{c.me.username}</b>", quote=True
    )


@app.on_message(filters.command(["sof"], COMMAND_HANDLER))
@capture_err
async def stackoverflow(_, message):
    if len(message.command) == 1:
        return await message.reply("Give a query to search in StackOverflow!")
    r = (
        await fetch.get(
            f"https://api.stackexchange.com/2.3/search/excerpts?order=asc&sort=relevance&q={message.command[1]}&accepted=True&migrated=False¬ice=False&wiki=False&site=stackoverflow"
        )
    ).json()
    msg = await message.reply("Getting data..")
    hasil = ""
    for count, data in enumerate(r["items"], start=1):
        question = data["question_id"]
        title = data["title"]
        snippet = (
            remove_html_tags(data["excerpt"])[:80].replace("\n", "").replace("    ", "")
            if len(remove_html_tags(data["excerpt"])) > 80
            else remove_html_tags(data["excerpt"]).replace("\n", "").replace("    ", "")
        )
        hasil += f"{count}. <a href='https://stackoverflow.com/questions/{question}'>{title}</a>\n<code>{snippet}</code>\n"
    try:
        await msg.edit(hasil)
    except MessageTooLong:
        url = await rentry(hasil)
        await msg.edit(f"Your text pasted to rentry because has long text:\n{url}")
    except Exception as e:
        await msg.edit(e)


@app.on_message(filters.command(["google"], COMMAND_HANDLER))
@capture_err
async def gsearch(self, message):
    if len(message.command) == 1:
        return await message.reply("Give a query to search in Google!")
    def shorten_text(text):
        if len(text) > 150:
            return text[:150] + "..."
        return text
    query = message.text.split(maxsplit=1)[1]
    msg = await message.reply_text(f"**Googling** for `{query}` ...")
    try:
        gs = await fetch.get(
            f"https://www.google.com/search?q={query}&gl=id&hl=id&num=16",
        )
        soup = BeautifulSoup(gs.text, "lxml")

        # collect data
        data = []

        for result in soup.select(".tF2Cxc"):
            link = result.select_one(".yuRUbf a")["href"]
            title = result.select_one(".DKV0Md").text
            if snippet := result.find(class_="VwiC3b yXK7lf p4wth r025kc hJNv6b"):
                snippet = snippet.get_text()
            elif snippet := result.find(class_="VwiC3b yXK7lf p4wth r025kc hJNv6b Hdw6tb"):
                snippet = snippet.get_text()
            else:
                snippet = "-"
            data.append(
                {
                    "title": html.escape(title),
                    "link": link,
                    "snippet": shorten_text(html.escape(snippet)),
                }
            )
        arr = json.dumps(data, indent=2, ensure_ascii=False)
        parse = json.loads(arr)
        total = len(parse)
        res = "".join(
            f"<a href='{i['link']}'>{i['title']}</a>\n{i['snippet']}\n\n" for i in parse
        )
    except Exception:
        exc = traceback.format_exc()
        return await msg.edit(exc)
    await msg.edit_msg(
        text=f"<b>Ada {total} Hasil Pencarian dari {query}:</b>\n{res}<b>GoogleSearch by @{BOT_USERNAME}</b>",
        disable_web_page_preview=True,
    )


@app.on_message(filters.command(["tr", "trans", "translate"], COMMAND_HANDLER))
@capture_err
async def translate(_, message):
    if message.reply_to_message and (
        message.reply_to_message.text or message.reply_to_message.caption
    ):
        target_lang = "id" if len(message.command) == 1 else message.text.split()[1]
        text = message.reply_to_message.text or message.reply_to_message.caption
    else:
        if len(message.command) < 3:
            return await message.reply_msg(
                "Berikan Kode bahasa yang valid.\n[Available options](https://tgraph.yasirweb.eu.org/Lang-Codes-11-08).\n<b>Usage:</b> <code>/tr en</code>",
            )
        target_lang = message.text.split(None, 2)[1]
        text = message.text.split(None, 2)[2]
    msg = await message.reply_msg("Menerjemahkan...")
    try:
        my_translator = await gtranslate(text, source="auto", target=target_lang)
        result = my_translator.text
        await msg.edit_msg(
            f"Translation using source = {my_translator.src} and target = {my_translator.dest}\n\n-> {result}"
        )
    except MessageTooLong:
        url = await rentry(result)
        await msg.edit_msg(
            f"Your translated text pasted to rentry because has long text:\n{url}"
        )
    except Exception as err:
        await msg.edit_msg(f"Oppss, Error: <code>{str(err)}</code>")


@app.on_message(filters.command(["tts"], COMMAND_HANDLER))
@capture_err
async def tts_convert(_, message):
    if message.reply_to_message and (
        message.reply_to_message.text or message.reply_to_message.caption
    ):
        if len(message.text.split()) == 1:
            target_lang = "id"
        else:
            target_lang = message.text.split()[1]
        text = message.reply_to_message.text or message.reply_to_message.caption
    else:
        if len(message.text.split()) <= 2:
            await message.reply_text(
                "Berikan Kode bahasa yang valid.\n[Available options](https://telegra.ph/Lang-Codes-11-08).\n*Usage:* /tts en [text]",
            )
            return
        target_lang = message.text.split(None, 2)[1]
        text = message.text.split(None, 2)[2]
    msg = await message.reply("Converting to voice...")
    fname = f"tts_BY_{message.from_user.id if message.from_user else message.sender_chat.title}.mp3"
    try:
        tts = gTTS(text, lang=target_lang)
        tts.save(fname)
    except ValueError as err:
        await msg.edit(f"Error: <code>{str(err)}</code>")
        return
    await msg.delete()
    await msg.reply_audio(fname)
    if os.path.exists(fname):
        os.remove(fname)


@app.on_message(filters.command(["tosticker"], COMMAND_HANDLER))
@capture_err
async def tostick(client, message):
    try:
        if not message.reply_to_message or not message.reply_to_message.photo:
            return await message.reply_text("Reply ke foto untuk mengubah ke sticker")
        sticker = await client.download_media(
            message.reply_to_message.photo.file_id,
            f"tostick_{message.from_user.id}.webp",
        )
        await message.reply_sticker(sticker)
        os.remove(sticker)
    except Exception as e:
        await message.reply_text(str(e))


@app.on_message(filters.command(["id"], COMMAND_HANDLER))
async def showid(_, message):
    chat_type = message.chat.type.value
    if chat_type == "private":
        user_id = message.chat.id
        first = message.from_user.first_name
        last = message.from_user.last_name or ""
        username = message.from_user.username
        dc_id = message.from_user.dc_id or ""
        await message.reply_text(
            f"<b>➲ First Name:</b> {first}\n<b>➲ Last Name:</b> {last}\n<b>➲ Username:</b> {username}\n<b>➲ Telegram ID:</b> <code>{user_id}</code>\n<b>➲ Data Centre:</b> <code>{dc_id}</code>",
            quote=True,
        )

    elif chat_type in ["group", "supergroup"]:
        _id = ""
        _id += "<b>➲ Chat ID</b>: " f"<code>{message.chat.id}</code>\n"
        if message.reply_to_message:
            _id += (
                "<b>➲ User ID</b>: "
                f"<code>{message.from_user.id if message.from_user else 'Anonymous'}</code>\n"
                "<b>➲ Replied User ID</b>: "
                f"<code>{message.reply_to_message.from_user.id if message.reply_to_message.from_user else 'Anonymous'}</code>\n"
            )
            file_info = get_file_id(message.reply_to_message)
        else:
            _id += (
                "<b>➲ User ID</b>: "
                f"<code>{message.from_user.id if message.from_user else 'Anonymous'}</code>\n"
            )
            file_info = get_file_id(message)
        if file_info:
            _id += (
                f"<b>{file_info.message_type}</b>: "
                f"<code>{file_info.file_id}</code>\n"
            )
        await message.reply_text(_id, quote=True)


@app.on_message(filters.command(["info"], COMMAND_HANDLER))
async def who_is(client, message):
    # https://github.com/SpEcHiDe/PyroGramBot/blob/master/pyrobot/plugins/admemes/whois.py#L19
    if message.sender_chat:
        return await message.reply_msg("Not supported channel..")
    status_message = await message.reply_text("`Fetching user info...`")
    await status_message.edit("`Processing user info...`")
    from_user = None
    from_user_id, _ = extract_user(message)
    try:
        from_user = await client.get_users(from_user_id)
    except Exception as error:
        return await status_message.edit(str(error))
    if from_user is None:
        return await status_message.edit("No valid user_id / message specified")
    message_out_str = ""
    username = f"@{from_user.username}" or "<b>No Username</b>"
    dc_id = from_user.dc_id or "<i>[User Doesn't Have Profile Pic]</i>"
    bio = (await client.get_chat(from_user.id)).bio
    count_pic = await client.get_chat_photos_count(from_user.id)
    message_out_str += f"<b>🔸 First Name:</b> {from_user.first_name}\n"
    if last_name := from_user.last_name:
        message_out_str += f"<b>🔹 Last Name:</b> {last_name}\n"
    message_out_str += f"<b>🆔 User ID:</b> <code>{from_user.id}</code>\n"
    message_out_str += f"<b>✴️ User Name:</b> {username}\n"
    message_out_str += f"<b>💠 Data Centre:</b> <code>{dc_id}</code>\n"
    if bio:
        message_out_str += f"<b>👨🏿‍💻 Bio:</b> <code>{bio}</code>\n"
    message_out_str += f"<b>📸 Pictures:</b> {count_pic}\n"
    message_out_str += f"<b>🧐 Restricted:</b> {from_user.is_restricted}\n"
    message_out_str += f"<b>✅ Verified:</b> {from_user.is_verified}\n"
    message_out_str += f"<b>🌐 Profile Link:</b> <a href='tg://user?id={from_user.id}'><b>Click Here</b></a>\n"
    if message.chat.type.value in (("supergroup", "channel")):
        with contextlib.suppress(UserNotParticipant, ChatAdminRequired):
            chat_member_p = await message.chat.get_member(from_user.id)
            joined_date = chat_member_p.joined_date
            message_out_str += (
                "<b>➲Joined this Chat on:</b> <code>" f"{joined_date}" "</code>\n"
            )
    if chat_photo := from_user.photo:
        local_user_photo = await client.download_media(message=chat_photo.big_file_id)
        buttons = [
            [
                InlineKeyboardButton(
                    "🔐 Close", callback_data=f"close#{message.from_user.id}"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_photo(
            photo=local_user_photo,
            quote=True,
            reply_markup=reply_markup,
            caption=message_out_str,
            disable_notification=True,
        )
        os.remove(local_user_photo)
    else:
        buttons = [
            [
                InlineKeyboardButton(
                    "🔐 Close", callback_data=f"close#{message.from_user.id}"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(
            text=message_out_str,
            reply_markup=reply_markup,
            quote=True,
            disable_notification=True,
        )
    await status_message.delete_msg()


@app.on_callback_query(filters.regex("^close"))
async def close_callback(_, query: CallbackQuery):
    _, userid = query.data.split("#")
    if query.from_user.id != int(userid):
        with contextlib.suppress(QueryIdInvalid):
            return await query.answer("⚠️ Access Denied!", True)
    with contextlib.suppress(Exception):
        await query.answer("Deleting this message in 5 seconds.")
        await asyncio.sleep(5)
        await query.message.delete_msg()
        await query.message.reply_to_message.delete_msg()


async def mdlapi(title):
    link = f"https://kuryana.vercel.app/search/q/{title}"
    async with aiohttp.ClientSession() as ses, ses.get(link) as result:
        return await result.json()


@app.on_message(filters.command(["mdl"], COMMAND_HANDLER))
@capture_err
async def mdlsearch(_, message):
    if " " in message.text:
        _, title = message.text.split(None, 1)
        k = await message.reply("Sedang mencari di Database MyDramaList.. 😴")
        movies = await mdlapi(title)
        res = movies["results"]["dramas"]
        if not movies:
            return await k.edit("Tidak ada hasil ditemukan.. 😕")
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{movie.get('title')} ({movie.get('year')})",
                    callback_data=f"mdls#{message.from_user.id}#{message.id}#{movie['slug']}",
                )
            ]
            for movie in res
        ]
        await k.edit(
            f"Ditemukan {len(movies)} query dari <code>{title}</code>",
            reply_markup=InlineKeyboardMarkup(btn),
        )
    else:
        await message.reply("Berikan aku nama drama yang ingin dicari. 🤷🏻‍♂️")


@app.on_callback_query(filters.regex("^mdls"))
async def mdl_callback(_, query: CallbackQuery):
    _, user, _, slug = query.data.split("#")
    if user == f"{query.from_user.id}":
        await query.message.edit_text("Permintaan kamu sedang diproses.. ")
        result = ""
        try:
            res = (await fetch.get(f"https://kuryana.vercel.app/id/{slug}")).json()
            result += f"<b>Title:</b> <a href='{res['data']['link']}'>{res['data']['title']}</a>\n"
            result += (
                f"<b>AKA:</b> <code>{res['data']['others']['also_known_as']}</code>\n\n"
            )
            result += f"<b>Rating:</b> <code>{res['data']['details']['score']}</code>\n"
            result += f"<b>Content Rating:</b> <code>{res['data']['details']['content_rating']}</code>\n"
            result += f"<b>Type:</b> <code>{res['data']['details']['type']}</code>\n"
            result += (
                f"<b>Country:</b> <code>{res['data']['details']['country']}</code>\n"
            )
            if res["data"]["details"]["type"] == "Movie":
                result += f"<b>Release Date:</b> <code>{res['data']['details']['release_date']}</code>\n"
            elif res["data"]["details"]["type"] == "Drama":
                result += f"<b>Episode:</b> {res['data']['details']['episodes']}\n"
                result += (
                    f"<b>Aired:</b> <code>{res['data']['details']['aired']}</code>\n"
                )
                try:
                    result += f"<b>Aired on:</b> <code>{res['data']['details']['aired_on']}</code>\n"
                except:
                    pass
                try:
                    result += f"<b>Original Network:</b> <code>{res['data']['details']['original_network']}</code>\n"
                except:
                    pass
            result += (
                f"<b>Duration:</b> <code>{res['data']['details']['duration']}</code>\n"
            )
            result += (
                f"<b>Genre:</b> <code>{res['data']['others']['genres']}</code>\n\n"
            )
            result += f"<b>Synopsis:</b> <code>{res['data']['synopsis']}</code>\n"
            result += f"<b>Tags:</b> <code>{res['data']['others']['tags']}</code>\n"
            btn = InlineKeyboardMarkup(
                [[InlineKeyboardButton("🎬 Open MyDramaList", url=res["data"]["link"])]]
            )
            await query.message.edit_text(result, reply_markup=btn)
        except Exception as e:
            await query.message.edit_text(f"<b>ERROR:</b>\n<code>{e}</code>")
    else:
        await query.answer("Tombol ini bukan untukmu", show_alert=True)
