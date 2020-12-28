# -*- coding: utf-8 -*-

import logging
import os
import random
import re
from datetime import datetime
from pathlib import Path

import asyncio
import ujson
from sanic import Sanic
from sanic.log import logger
from sanic.response import json, text
from sanic_jinja2 import SanicJinja2
from telebot import TeleBot
from telebot import apihelper as bothelper
from telebot import logger as botlogger
from telebot import types as bottypes
from tinydb import Query, TinyDB

from lang import Language

# Get working directory
workdir = Path(__file__).parent.absolute()
if Path.exists(Path(workdir, "imgs")):
    imgdir = Path(workdir, "imgs")
else:
    os.mkdir(Path(workdir, "imgs"))
    imgdir = Path(workdir, "imgs")

# Set webserver params
# WEB_HOST = '<external ip or domain>'
# WEB_PORT = 8443  # 443, 80, 88 or 8443 (port need to be 'open')
# WEB_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr

# Uncomment if custom certs needed
# WEB_SSL_CERT = Path(workdir, "webhook_cert.pem") # Path to the ssl certificate
# WEB_SSL_PRIV = Path(workdir, "webhook_pkey.pem") # Path to the ssl private key

# Init webserver
app = Sanic()
jinja = SanicJinja2(app)
# Set static
app.static("/memes", "/memer/imgs/")
# Init DBs
if Path.exists(Path(workdir, "data")) is False:
    os.mkdir(Path(workdir, "data"))
config = TinyDB(Path(workdir, "data", "config.json"))
db = TinyDB(Path(workdir, "data", "db.json"))

# Work with config
def get_from_config(pid):
    result = config.get(Query().param == pid)
    if result:
        return result["value"]
    else:
        return False


def set_to_config(pid, value):
    result = config.get(Query().param == pid)
    if result:
        try:
            config.update({"value": value}, Query().param == pid)
            return get_from_config(pid)
        except Exception as e:
            raise e
    else:
        try:
            config.insert({"param": pid, "value": value})
            return get_from_config(pid)
        except Exception as e:
            raise e


# Take params from config
api_token = get_from_config("bot_api_key")
if api_token is False:
    api_token = set_to_config(
        "bot_api_key", "<telegram API TOKEN here>"
    )  # Set your API TOKEN here

config_host = get_from_config("web_host")
if config_host is False:
    config_host = set_to_config("web_host", "<external ip or domain>")
config_port = get_from_config("web_port")
if config_port is False:
    config_port = set_to_config("web_port", "80")
config_listen = get_from_config("web_listen")
if config_listen is False:
    config_listen = set_to_config("web_listen", "0.0.0.0")

config_lang = get_from_config("app_language")
if config_lang is False:
    config_lang = set_to_config(
        "app_language", "en"
    )  # "en" for english, "ru" for russian

web_header = get_from_config("app_site_header")
if web_header is False:
    web_header = set_to_config("app_site_header", "Memer - shiny meme rotator")
web_title = get_from_config("app_site_title")
if web_title is False:
    web_title = set_to_config("app_site_title", "MEMER")
web_botname = get_from_config("app_site_botname")
if web_botname is False:
    web_botname = set_to_config("app_site_botname", "@memer_bot")
web_refresh_interval = get_from_config("app_site_refresh")
if web_refresh_interval is False:
    web_refresh_interval = set_to_config("app_site_refresh", 15)
webconfig = {
    "header": web_header,
    "title": web_title,
    "botname": web_botname,
    "refresh": web_refresh_interval,
}

img_refresh = get_from_config("img_refresh")
if img_refresh is False:
    img_refresh = set_to_config("img_refresh", 30)
img_removed = get_from_config("img_removed")
if img_removed is False:
    img_removed = set_to_config("img_removed", list())

# Init logging
logging.basicConfig(
    filename=Path(workdir, "data", "memer.log"),
    level=logging.DEBUG,
    format=" %(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger("memer")

# Init language
lang = Language(config_lang)

# Init bot
bot = TeleBot(api_token)
botlogger.setLevel(logging.DEBUG)

# Inner dicts
memes_shown = list()
memes_removed = list()
memes_new = list()

# Bot
@bot.message_handler(commands=["start", "help"])
def bot_send_welcome(message):
    bot.send_message(message.chat.id, lang.welcome_message)


@bot.message_handler(content_types=["photo"])
def bot_upload_photo(message):
    bot.send_chat_action(message.chat.id, "typing")
    if len(db.all()) > 0:
        db_last_id = db.all()[-1]["id"]
    else:
        db_last_id = 0

    db.insert(
        {
            "id": int(db_last_id) + 1,
            "vote_up": 0,
            "vote_down": 0,
            "report": 0,
            "users_voted": [],
            "users_reported": [],
            "date": datetime.now(),
        }
    )
    log.debug("DB insert: ID {}, date: {}".format(int(db_last_id) + 1, datetime.now))

    fileID = message.photo[-1].file_id
    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)

    with open(Path(imgdir, "{}.jpg".format(int(db_last_id) + 1)), "wb") as new_file:
        new_file.write(downloaded_file)
        new_file.flush()

    memes_new.append(int(db_last_id) + 1)
    random.seed(datetime.now())
    bot.send_message(message.chat.id, random.choice(lang.img_save_answers))


@bot.message_handler(content_types=["text"])
def bot_commands(message):
    log.debug(message.text)
    match_show = re.search("(?:show|покаж)\s(\d+)$", message.text)
    match_voteup = re.search("(?:up|ор)\s(\d+)$", message.text)
    match_votedown = re.search("(?:down|фу)\s(\d+)$", message.text)
    match_report = re.search("(?:report|удоли)\s(\d+)$", message.text)
    if match_show:
        img_id = int(match_show.group(1))
        if Path.exists(Path(imgdir, "{}.jpg".format(img_id))):
            photo = open(Path(imgdir, "{}.jpg".format(img_id)), "rb")
            bot.send_photo(message.chat.id, photo)
        else:
            bot.send_message(message.chat.id, lang.error_no_id.format(img_id))
    elif match_voteup:
        img_id = int(match_voteup.group(1))
        dbitem = db.get(Query().id == img_id)
        if dbitem:
            if message.chat.id in dbitem["users_voted"]:
                bot.send_message(message.chat.id, lang.error_voted)
            else:
                try:
                    users_voted = dbitem["users_voted"]
                    users_voted.append(message.chat.id)
                    db.update(
                        {
                            "vote_up": int(dbitem["vote_up"]) + 1,
                            "users_voted": users_voted,
                        },
                        Query().id == img_id,
                    )
                    bot.send_message(
                        message.chat.id,
                        lang.vote_up_accepted.format(img_id),
                    )
                except Exception as e:
                    raise e
        else:
            bot.send_message(message.chat.id, lang.error_no_id.format(img_id))
    elif match_votedown:
        img_id = int(match_votedown.group(1))
        dbitem = db.get(Query().id == img_id)
        if dbitem:
            if message.chat.id in dbitem["users_voted"]:
                bot.send_message(message.chat.id, lang.error_voted)
            else:
                try:
                    users_voted = dbitem["users_voted"]
                    users_voted.append(message.chat.id)
                    db.update(
                        {
                            "vote_down": int(dbitem["vote_down"]) + 1,
                            "users_voted": users_voted,
                        },
                        Query().id == img_id,
                    )
                    bot.send_message(
                        message.chat.id,
                        lang.vote_down_accepted.format(img_id),
                    )
                except Exception as e:
                    raise e
        else:
            bot.send_message(message.chat.id, lang.error_no_id.format(img_id))
    elif match_report:
        img_id = int(match_report.group(1))
        dbitem = db.get(Query().id == img_id)
        if dbitem:
            if message.chat.id in dbitem["users_reported"]:
                bot.send_message(message.chat.id, lang.error_reported)
            else:
                try:
                    users_reported = dbitem["users_reported"]
                    users_reported.append(message.chat.id)
                    db.update(
                        {
                            "report": int(dbitem["report"]) + 1,
                            "users_reported": users_reported,
                        },
                        Query().id == img_id,
                    )
                    bot.send_message(
                        message.chat.id,
                        lang.img_reported.format(img_id),
                    )
                except Exception as e:
                    raise e
        else:
            bot.send_message(message.chat.id, lang.error_no_id.format(img_id))
    else:
        bot.send_message(message.chat.id, lang.error_unknown_command)


# Webserv
async def app_rotator(app):
    while True:
        await asyncio.sleep(img_refresh)
        if len(memes_new) > 0:
            random.seed(datetime.now())
            img_current = random.choice(memes_new)
            set_to_config("img_current", img_current)
            memes_new.remove(img_current)
        else:
            memes_db = list()
            for meme in db.all():
                memes_db.append(meme["id"])
            img_current = get_from_config("img_current")
            memes_shown.append(img_current)
            memes_ready = list(set(memes_db).difference(set(memes_shown)))
            if len(memes_ready) == 0:
                memes_shown.clear()
                memes_shown.append(img_current)
                memes_ready = list(set(memes_db).difference(set(memes_shown)))
                random.seed(datetime.now())
                img_current = random.choice(memes_ready)
                set_to_config("img_current", img_current)
                log.debug(
                    "FROM START! All: {}, Shown: {}, Ready: {}, Current: {}".format(
                        memes_db, memes_shown, memes_ready, img_current
                    )
                )
            else:
                random.seed(datetime.now())
                img_current = random.choice(memes_ready)
                set_to_config("img_current", img_current)
                log.debug(
                    "NEXT! All: {}, Shown: {}, Ready: {}, Current: {}".format(
                        memes_db, memes_shown, memes_ready, img_current
                    )
                )


async def app_deleter(app):
    while True:
        await asyncio.sleep(3600)
        for meme in db.all():
            if meme["report"] > 2:
                if Path.exists(Path(imgdir, "{}.jpg".format(meme["id"]))):
                    os.remove(Path(imgdir, "{}.jpg".format(meme["id"])))
                    log.debug("Meme File {} deleted".format(meme["id"]))
                memes_shown.remove(meme["id"])
                memes_removed.append(meme["id"])
                log.debug("Meme {} deleted from DB".format(meme["id"]))
                db.remove(Query().id == meme["id"])


@app.route("/", methods=["GET"])
async def app_slideshow(request):
    img_current = get_from_config("img_current")
    if request.query_string:
        try:
            query_meme = int(request.query_string)
        except Exception as e:
            return json({"status": "input error", "data": e}, 500)
        imgdata = db.get(Query().id == query_meme)
        if imgdata:
            return jinja.render("index.html", request, cfg=webconfig, data=imgdata)
        else:
            return json({"status": "DB item not found", "data": imgdata}, 500)
    elif Path.exists(Path(imgdir, "{}.jpg".format(img_current))):
        imgdata = db.get(Query().id == img_current)
        if imgdata:
            return jinja.render("index.html", request, cfg=webconfig, data=imgdata)
        else:
            return json({"status": "DB item not found", "data": imgdata}, 500)
    else:
        return json({"status": "Img not found", "img": img_current}, 500)


@app.route("/wh", methods=["POST"])
async def app_webhook(request):
    if request.body is None:
        return json({"status": "broken request"}, 403)
    body = request.body.decode("utf-8")
    body = ujson.loads(body)
    log.debug("WH body incoming: {}".format(body))
    update = bottypes.Update.de_json(body)
    bot.process_new_updates([update])
    return json({"status": "ok"}, 200)


# Webserver stuff
@app.listener("before_server_start")
async def before_start(app, loop):
    bot.remove_webhook()
    img_current = get_from_config("img_current")
    if img_current is False:
        img_current = set_to_config("img_current", 1)


@app.listener("after_server_start")
async def after_start(app, loop):
    bot.set_webhook(url="https://{}/wh".format(config_host))
    app.add_task(app_rotator)
    app.add_task(app_deleter)


@app.listener("before_server_stop")
async def before_stop(app, loop):
    log.debug("Memer removed during session: {}".format(memes_removed))
    img_removed = get_from_config("img_removed")
    img_removed += memes_removed
    set_to_config("img_removed", img_removed)


if __name__ == "__main__":
    # ssl = {'cert': WEB_SSL_CERT, 'key': WEB_SSL_PRIV} #if needed add ssl=ssl to app.run params
    app.run(host=config_listen, port=config_port)
