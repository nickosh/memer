#import asyncio
import logging
import os
import random
import re
from datetime import datetime
from pathlib import Path

#import uvloop
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

#from signal import SIGINT, signal


#Ger working directory
workdir = Path(__file__).parent.absolute()
if Path.exists(Path(workdir, "imgs")):
    imgdir = Path(workdir, "imgs")
else:
    os.mkdir(Path(workdir, "imgs"))
    imgdir = Path(workdir, "imgs")

#Set webserver params
WEB_HOST = '<external ip or domain>'
WEB_PORT = 8443  # 443, 80, 88 or 8443 (port need to be 'open')
WEB_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr

#Uncomment if custom certs needed
#WEB_SSL_CERT = Path(workdir, "webhook_cert.pem") # Path to the ssl certificate
#WEB_SSL_PRIV = Path(workdir, "webhook_pkey.pem") # Path to the ssl private key

#Init webserver
app = Sanic()
jinja = SanicJinja2(app)
#Init DBs
config = TinyDB(Path(workdir, "config.json"))
db = TinyDB(Path(workdir, "db.json"))

#Work with config
def get_from_config(pid):
    result = config.get(Query().param == pid)
    if result:
        return result['value']
    else:
        return False

def set_to_config(pid, value):
    result = config.get(Query().param == pid)
    if result:
        try:
            config.update({'value': value}, Query().param == pid)
            return get_from_config(pid)
        except Exception as e:
            raise e
    else:
        try:
            config.insert({'param': pid, 'value': value})
            return get_from_config(pid)
        except Exception as e:
            raise e

#Take params from config
api_token = get_from_config('bot_api_key')
if api_token == False:
    api_token = set_to_config('bot_api_key', '<YOUR_API_KEY_HERE>') #Set your API TOKEN here
rotator_title = get_from_config('app_site_title')
if rotator_title == False:
    rotator_title = set_to_config('app_site_title', 'Memer - your shinny meme rotator')
img_cur = get_from_config('img_current')
if img_cur == False:
    img_cur = set_to_config('img_current', '0')

#Init bot
bot = TeleBot(api_token)
botlogger.setLevel(logging.DEBUG)

#Inner dicts
memes_shown = []
memes_removed = []
#Here what bot answer when save user's meme. Choosed randomly.
save_answers = ['Орно! Схоронил.', 'Кек! Хорошо так.', 'Лул! Годненько.']

#Bot
@bot.message_handler(commands=["start", "help"])
def bot_send_welcome(message):
    #Welcome message for user and descriptions for commands /show /up /down /report
    bot.send_message(message.chat.id, "Кукусь! Мы тут делимся мемами, а потом дружно над ними орём. Айда с нами!\n\n Просто кидай свою картинку прямо в этот чат и очень скоро увидешь её в общей ленте.\n\n Если хочешь больше, есть пара полезных комманд:\n /start или /help - увидешь данное сообщение;\n /show <id> или /покаж <id> - увидешь понравившийся мемасик ещё раз;\n /up <id> или /ор <id> - оценить мемасик как годный;\n /down <id> или /фу <id> - оценить мемасик как отстойный;\n /report <id> или /удоли <id> - проголосовать за удаление мемасика, три голоса и он отправится в корзину;\n\n ЗЫ: Все команды кроме /start и /help можно вводить без слэша (/). Только ID картинки после пробела не забудь. \n\n Наслаждайся!")

@bot.message_handler(content_types=['photo'])
def bot_upload_photo(message):
    bot.send_chat_action(message.chat.id, 'typing')
    fileID = message.photo[-1].file_id
    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)

    with open(Path(imgdir, '{}.jpg'.format(len(db)+1)), 'wb') as new_file:
        new_file.write(downloaded_file)
        new_file.flush()
    random.seed(datetime.now())
    bot.send_message(message.chat.id, random.choice(save_answers))

    db.insert({'id': len(db)+1, 'vote_up': 0, 'vote_down': 0, 'report': 0, 'users_voted': [], 'users_reported': [], 'date': datetime.now()})

@bot.message_handler(content_types=['text'])
def bot_commands(message):
    print(message.text)
    match_show = re.search('(?:show|покаж)\s(\d+)$', message.text)
    match_voteup = re.search('(?:up|ор)\s(\d+)$', message.text)
    match_votedown = re.search('(?:down|фу)\s(\d+)$', message.text)
    match_report = re.search('(?:report|удоли)\s(\d+)$', message.text)
    if match_show:
        img_id = int(match_show.group(1))
        if Path.exists(Path(imgdir, '{}.jpg'.format(img_id))):
            photo = open(Path(imgdir, '{}.jpg'.format(img_id)), 'rb')
            bot.send_photo(message.chat.id, photo)
        else:
            #Send 'Can't find ID' message to user
            bot.send_message(message.chat.id, 'Упс, не могу найти ID {}. :('.format(img_id))
    elif match_voteup:
        img_id = int(match_voteup.group(1))
        dbitem = db.get(Query().id == img_id)
        if dbitem:
            if message.chat.id in dbitem['users_voted']:
                #Send 'Already voted' message to user
                bot.send_message(message.chat.id, 'Голос уже учтён! ;)')
            else:
                try:
                    users_voted = dbitem['users_voted']
                    users_voted.append(message.chat.id)
                    db.update({'vote_up': int(dbitem['vote_up'])+1, 'users_voted': users_voted}, Query().id == img_id)
                    #Send 'Thumb up accepted' message to user
                    bot.send_message(message.chat.id, 'Мемасик с ID {} успешно пооран!'.format(img_id))
                except Exception as e:
                    raise e
        else:
            #Send 'Can't find ID' message to user
            bot.send_message(message.chat.id, 'Упс, не могу найти ID {}. :('.format(img_id))
    elif match_votedown:
        img_id = int(match_votedown.group(1))
        dbitem = db.get(Query().id == img_id)
        if dbitem:
            if message.chat.id in dbitem['users_voted']:
                #Send 'Already voted' message to user
                bot.send_message(message.chat.id, 'Голос уже учтён! ;)')
            else:
                try:
                    users_voted = dbitem['users_voted']
                    users_voted.append(message.chat.id)
                    db.update({'vote_down': int(dbitem['vote_down'])+1, 'users_voted': users_voted}, Query().id == img_id)
                    #Send 'Thumb down accepted' message to user
                    bot.send_message(message.chat.id, 'Мемасик с ID {} успешно зафукан!'.format(img_id))
                except Exception as e:
                    raise e
        else:
            #Send 'Can't find ID' message to user
            bot.send_message(message.chat.id, 'Упс, не могу найти ID {}. :('.format(img_id))
    elif match_report:
        img_id = int(match_report.group(1))
        dbitem = db.get(Query().id == img_id)
        if dbitem:
            if message.chat.id in dbitem['users_reported']:
                #Send 'Already reported' message to user
                bot.send_message(message.chat.id, 'Уже донесено! :/')
            else:
                try:
                    users_reported = dbitem['users_reported']
                    users_reported.append(message.chat.id)
                    db.update({'report': int(dbitem['report'])+1, 'users_reported': users_reported}, Query().id == img_id)
                    #Send 'Meme reported' message to user
                    bot.send_message(message.chat.id, 'Мемасик с ID {} отРосКомНадзорен!'.format(img_id))
                except Exception as e:
                    raise e
        else:
            #Send 'Can't find ID' message to user
            bot.send_message(message.chat.id, 'Упс, не могу найти ID {}. :('.format(img_id))
    else:
        #Send 'Unknown command' message to user
        bot.send_message(message.chat.id, 'Моя нипанимать...')

#Webserv
@app.route("/")
async def test(request):
    return json({"hello": "world"})

@app.route("/wh", methods=['POST'])
async def webhook(request):
    if request.body is None:
        return json({'status': 'broken request'}, 403)
    body = request.body.decode("utf-8")
    body = ujson.loads(body)
    update = bottypes.Update.de_json(body)
    bot.process_new_updates([update])
    return json({'status': 'ok'}, 200)

#Webserver stuff
@app.listener('before_server_start')
async def before_start(app, loop):
    bot.remove_webhook()

@app.listener('after_server_start')
async def after_start(app, loop):
    bot.set_webhook(url="https://{}/wh".format(WEB_HOST))

# todo: before server stop save all removed memes ids in config (for history)

if __name__ == "__main__":
    #ssl = {'cert': WEB_SSL_CERT, 'key': WEB_SSL_PRIV} #if needed add ssl=ssl to app.run params
    app.run(host=WEB_LISTEN, port=WEB_PORT, debug=True, access_log=True)

# Quick'n'dirty SSL certificate generation:
#
# openssl genrsa -out webhook_pkey.pem 2048
# openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
#
# When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply
# with the same value in you put in WEBHOOK_HOST

'''if __name__ == "__main__":
    ssl = {'cert': WEB_SSL_CERT, 'key': WEB_SSL_PRIV}

    asyncio.set_event_loop(uvloop.new_event_loop())
    serv_coro = app.create_server(host=WEB_LISTEN, port=WEB_PORT, debug=True, access_log=True, return_asyncio_server=True)
    loop = asyncio.get_event_loop()
    serv_task = asyncio.ensure_future(serv_coro, loop=loop)
    signal(SIGINT, lambda s, f: loop.stop())
    server = loop.run_until_complete(serv_task)
    server.after_start()
    try:
        loop.run_forever()
    except KeyboardInterrupt as e:
        loop.stop()
    finally:
        server.before_stop()

        # Wait for server to close
        close_task = server.close()
        loop.run_until_complete(close_task)

        # Complete all tasks on the loop
        for connection in server.connections:
            connection.close_if_idle()
        server.after_stop()'''
