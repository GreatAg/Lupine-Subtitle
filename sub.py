from __future__ import with_statement

import contextlib

try:
    from urllib.parse import urlencode

except ImportError:
    from urllib import urlencode
try:
    from urllib.request import urlopen

except ImportError:
    from urllib2 import urlopen

from tenacity import retry, wait_fixed, stop_after_attempt

import sys
import requests
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = '1112353414:AAHtywLOJ5qC5KKwekC1jVjk5aZ4FK68tc4'

bot = telebot.TeleBot(TOKEN, num_threads=10)


def make_tiny(url):
    request_url = ('http://tinyurl.com/api-create.php?' + urlencode({'url': url}))
    with contextlib.closing(urlopen(request_url)) as response:
        return response.read().decode('utf-8 ')


def search(name):
    data = find_movie(name)
    if data is None:
        return
    final = []
    j = 0
    try:
        for i in data:
            if j < 8:
                final.append(i)
                j += 1
            else:
                break
    except TypeError:
        pass
    return final


def find_movie(name):
    name = name.replace(" ", "%20")
    link = f"https://api.codebazan.ir/subtitle/?type=search&text={name}"
    try:
        data = requests.get(link)
        data = data.json()
    except:
        pass
    return data['Result']


def find_download_link(data):
    try:
        download = requests.get(f"https://api.codebazan.ir/subtitle/?type=download&id={data}")
        download = download.json()
        return download['links']
    except:
        pass


def build_markup(links):
    markup = types.InlineKeyboardMarkup()
    for i, obj in enumerate(links):
        links[i]['name'] = obj['name'].replace("دانلود زیرنویس فارسی سریال ", "")
        links[i]['name'] = obj['name'].replace("دانلود زیرنویس فارسی فیلم ", "")

    for i in links:
        id = i['id']
        id = id.replace('https://esubtitle.com/subtitles/', '')
        if len(id) >= 64:
            id = 'https://esubtitle.com/subtitles/' + id
            id = make_tiny(id)
        try:
            markup.add(InlineKeyboardButton('🎞'+i['name']+'🎞', callback_data=id))
        except:
            pass
    markup.add(InlineKeyboardButton('🔆بستن پنل🔆', callback_data='close'))
    return markup


def build_markup2(links):
    markup = InlineKeyboardMarkup()
    if links is None:
        return
    for i in links:
        i['namelink'] =i['namelink'].replace(' رایگان ',' ')
        x ='دریافت فایل ' + i['namelink']
        param = i['link']
        #param = param.replace('http://esubtitle.com/wp-content/uploads/', '')
        #param = param.replace('https://esubtitle.com/wp-content/uploads/', '')
        param = make_tiny(param)
        param = param.replace('http://tinyurl.com/', '')
        param = param.replace('https://tinyurl.com/', '')
        param = param.replace('/', 'SLH')
        param = param.replace('.', 'DT')
        url = f'https://t.me/LupSub_bot?start={param}'
        if 'دانلود قسمت 1' == i['namelink']:
            markup.add(InlineKeyboardButton('🔻لینک های دانلود فصل بعد🔻', callback_data='next'))
        markup.add(InlineKeyboardButton(i['namelink'], url=i['link']),
                   InlineKeyboardButton(x, url=url))
    markup.add(InlineKeyboardButton('🔆بستن پنل🔆', callback_data='close'))
    return markup


def build_markup3():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('⚜️کانال لوپین گایز⚜️', url='t.me/lupine_guys'))
    return markup


@bot.inline_handler(lambda query: len(query.query) == 0)
def default_query(inline_query):
    try:
        r = types.InlineQueryResultArticle('1', '❕راهنمایی و نحوه استفاده از بات❕', types.InputTextMessageContent('''❕ابتدا ایدی بات را نوشته و سپس یک فاصله میگذارید🔅

❕اسم فیلم را کامل و بدون سال تولید تایپ میکنید🔅

❕سپس اندکی صبر میکنید تا جستجو انجام شود سپس رو نمایش نتایج میزنید و پنل فیلم‌ ها برای شما باز میشود و با انتخاب هر فیلم لیست زیرنویس ها نمایش داده میشود🔅

❗️درصورت ایراد میتوانید با ایدی زیر در تماس باشید:
ID : @Ee_Alie ⚜️
Channel: @lupine_guys ⚜️'''))
        bot.answer_inline_query(inline_query.id, [r])
    except Exception as e:
        print(e)


@bot.callback_query_handler(func=lambda call: True)
def ok(call):
    if call.data == 'next':
        bot.answer_callback_query(call.id, '❕قسمت مورد نظر را انتخاب کنید❕')
    elif call.data == 'close':
        bot.answer_callback_query(call.id, '❕پنل بسته شد❕')
        bot.edit_message_text('پنل بسته شد✅', inline_message_id=call.inline_message_id,
                              reply_markup=build_markup3())
    else:
        if 'http://tinyurl.com/' in call.data:
            searching = call.data
        else:
            searching = 'https://esubtitle.com/subtitles/' + call.data
        bot.answer_callback_query(call.id, '🔍در حال جستجوی زیرنویس🔍')
        links = find_download_link(searching)
        if links is None:
            bot.edit_message_text('❕خطا در پردازش اطلاعات از سایت❕',inline_message_id=call.inline_message_id)
        else:
            bot.edit_message_text('''جستجو انجام شد✅

❕لطفا از طریق پنل زیر زیرنویس مورد نظر خود را انتخاب کنید🔅

Channel: @lupine_guys ⚜️''', inline_message_id=call.inline_message_id,
                                  reply_markup=build_markup2(links))


@bot.inline_handler(lambda query: True)
def query_text(inline_query):
    try:
        name = inline_query.query
        data = search(name)
        if data is None:
            r = types.InlineQueryResultArticle('1', '❕فیلم مورد نظر پیدا نشد❕', types.InputTextMessageContent('❕لطفا اسم فیلم را کامل و بدون سال تولید وارد کنید🔅'))
            bot.answer_inline_query(inline_query.id, [r])
        r = types.InlineQueryResultArticle(1, '🔅نمایش نتایج جستجو🔅',
                                           types.InputTextMessageContent('''جستجو انجام شد✅

❕لطفا از طریق پنل زیر فیلم مورد نظر خود را انتخاب کنید🔅

Channel: @lupine_guys ⚜️'''),
                                           reply_markup=build_markup(data))
        bot.answer_inline_query(inline_query.id, [r])

    except Exception as e:
        bot.send_message(chat_id=638994540, text=e)


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    try:
        text = message.text
        text = text.split(' ')
        bot.send_chat_action(chat_id, 'upload_document')
        #url = 'http://esubtitle.com/wp-content/uploads/'
        url = 'https://tinyurl.com/' + text[1]
        url = url.replace('SLH', '/')
        url = url.replace('DT', '.')
        bot.send_document(chat_id, url, caption='Channel : @lupine_guys ⚜️')
    except IndexError:
        bot.reply_to(message, '''⚜️به ربات لوپین ساب خوش آمدید⚜️

❗️نحوه استفاده از بات🔻

❕ابتدا ایدی بات را نوشته و سپس یک فاصله میگذارید🔅

❕اسم فیلم را کامل و بدون سال تولید تایپ میکنید🔅

❕سپس اندکی صبر میکنید تا جستجو انجام شود سپس رو نمایش نتایج میزنید و پنل فیلم‌ ها برای شما باز میشود و با انتخاب هر فیلم لیست زیرنویس ها نمایش داده میشود🔅

❗️درصورت ایراد میتوانید با ایدی زیر در تماس باشید:
ID : @Ee_Alie ⚜️
Channel: @lupine_guys ⚜️

Developed by ✵αℓi αg''')


print('Sub Bot is Up!')


@retry(wait=wait_fixed(2), stop=stop_after_attempt(10))
def poll():
    if __name__ == "__main__":
        try:
            bot.polling(none_stop=True, timeout=234)
        except Exception as e:
            bot.send_message(chat_id=638994540, text=e)
            raise e


poll()
while True:
    pass
