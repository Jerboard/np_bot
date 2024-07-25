from telebot import types
from telebot.types import CallbackQuery
from datetime import datetime
from moviepy.editor import VideoFileClip
from PIL import Image

import logging
import re
import os
import json
import uuid
import sqlite3
import requests
import threading

import db
import keyboards as kb
from init import bot
from .statistic import ask_amount


####  Добавление креативов ####
# Настройка логирования
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


# Функция для выполнения запросов к базе данных с логированием
def query_db(query, args=(), one=False):
    logging.debug(f"Выполнение запроса: {query} с аргументами {args}")
    with sqlite3.connect('bot_database2.db', check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute(query, args)
        conn.commit()
        r = cursor.fetchall()
        cursor.close()
        logging.debug(f"Результат запроса: {r}")
        return (r[0] if r else None) if one else r


# Функция для получения ord_id
def get_creative_ord_id(campaign_ord_id, creative_count):
    return f"{campaign_ord_id}.{creative_count + 1}"


# Команда /creative для Telegram бота
@bot.message_handler(commands=['creative'])
def start_creative_process(message):
    chat_id = message.chat.id
    conn = sqlite3.connect('bot_database2.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchone()
    if result is None or result[0] < 400:
        bot.send_message(chat_id, "Недостаточно средств на балансе. Пожалуйста, пополните баланс.")
        ask_amount(message)
    else:
        balance = result[0]
        cursor.execute('UPDATE users SET balance = ? WHERE chat_id = ?', (balance - 400, chat_id))
        conn.commit()
        conn.close()
        # Продолжение процесса добавления креатива
        add_creative(message)


# Обработчик для команды /add_creative
@bot.message_handler(commands=['add_creative'])
def add_creative(message):
    chat_id = message.chat.id
    campaigns = query_db('SELECT campaign_id, brand, service FROM ad_campaigns WHERE chat_id = ?', (chat_id,))
    logging.debug(f"Рекламные кампании для пользователя {chat_id}: {campaigns}")
    if not campaigns:
        bot.send_message(chat_id,
                         "У вас нет активных рекламных кампаний. Пожалуйста, создайте кампанию перед добавлением креатива.")
        return

    bot.send_message(chat_id, "Выберите рекламную кампанию для этого креатива:", reply_markup=kb.get_add_creative_kb(campaigns))


# Обработчик выбора рекламной кампании
@bot.callback_query_handler(func=lambda call: call.data.startswith('choose_campaign_'))
def choose_campaign_callback(call: CallbackQuery):
    chat_id = call.message.chat.id
    campaign_id = call.data.split('_')[2]
    logging.debug(f"Выбранная рекламная кампания: {campaign_id}")
    add_creative_start(chat_id, campaign_id)


# Начало процесса добавления креатива
def add_creative_start(chat_id, campaign_id):
    logging.debug(f"Начало процесса добавления креатива для кампании: {campaign_id}")
    msg = bot.send_message(chat_id,
                           "Загрузите файл своего рекламного креатива или введите текст. Вы можете загрузить несколько файлов для одного креатива.")
    bot.register_next_step_handler(msg, lambda message: handle_creative_upload(message, campaign_id))


# Обработчик загрузки креатива
def handle_creative_upload(message, campaign_id):
    chat_id = message.chat.id
    if message.content_type in ['text', 'photo', 'video', 'audio', 'document']:
        creative_content = save_creative(message)
        creative_count = query_db('SELECT COUNT(*) FROM creatives WHERE chat_id = ? AND campaign_id = ?',
                                  (chat_id, campaign_id), one=True)
        if creative_count is None:
            creative_count = [0]
        ord_id_data = query_db('SELECT ord_id FROM ad_campaigns WHERE campaign_id = ?', (campaign_id,), one=True)
        logging.debug(f"ord_id для кампании {campaign_id}: {ord_id_data}")
        if ord_id_data is None:
            logging.error(f"Не удалось найти ord_id для кампании с campaign_id: {campaign_id}")
            bot.send_message(chat_id, "Ошибка: Не удалось найти ord_id для указанной кампании.")
            return
        ord_id = get_creative_ord_id(ord_id_data[0], creative_count[0])
        query_db(
            'INSERT INTO creatives (chat_id, campaign_id, creative_id, content_type, content, ord_id, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (chat_id, campaign_id, str(uuid.uuid4()), message.content_type, creative_content, ord_id, 'pending'))
        logging.debug(f"Inserted creative for chat_id: {chat_id}, campaign_id: {campaign_id}, ord_id: {ord_id}")

        bot.send_message(chat_id, "Креатив успешно добавлен. Добавить еще файл или текст для этого креатива?",
                         reply_markup=kb.get_handle_creative_upload_kb(campaign_id))
    else:
        bot.send_message(chat_id, "Ошибка. Пожалуйста, попробуйте еще раз и пришлите креатив.")
        add_creative_start(chat_id, campaign_id)


# Обработчик кнопки "Добавить файл или текст"
@bot.callback_query_handler(func=lambda call: call.data.startswith('add_more_'))
def add_more_creative(call: CallbackQuery):
    campaign_id = call.data.split('_')[2]
    add_creative_start(call.message.chat.id, campaign_id)


# Обработчик кнопки "Продолжить"
@bot.callback_query_handler(func=lambda call: call.data.startswith('continue_creative_'))
def choose_campaign(call: CallbackQuery):
    chat_id = call.message.chat.id
    campaign_id = call.data.split('_')[2]
    finalize_creative(chat_id, campaign_id)


def save_creative(message):
    chat_id = message.chat.id
    creative_type = message.content_type
    creative_content = None

    if creative_type == 'text':
        creative_content = message.text

    elif creative_type == 'photo':
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        creative_content = download_and_save_file(file_info, "photo", chat_id)

    elif creative_type == 'video':
        file_id = message.video.file_id
        file_info = bot.get_file(file_id)
        creative_content = download_and_save_file(file_info, "video", chat_id)

    elif creative_type == 'audio':
        file_id = message.audio.file_id
        file_info = bot.get_file(file_id)
        creative_content = download_and_save_file(file_info, "audio", chat_id)

    elif creative_type == 'document':
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        creative_content = download_and_save_file(file_info, "document", chat_id)

    return creative_content


def download_and_save_file(file_info, file_type, chat_id):
    downloaded_file = bot.download_file(file_info.file_path)
    file_extension = file_info.file_path.split('.')[-1]
    file_name = f"{file_type}_{chat_id}_{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join("creatives", file_name)
    db.create_directory("creatives")
    with open(file_path, "wb") as new_file:
        new_file.write(downloaded_file)

    if file_type == 'video':
        clip = VideoFileClip(file_path)
        resized_clip = clip.resize(newsize=(640, 360))
        resized_file_name = f"resized_{file_name}"
        resized_file_path = os.path.join("creatives", resized_file_name)
        resized_clip.write_videofile(resized_file_path, codec='libx264')
        file_path = resized_file_path

    elif file_type == 'photo':
        img = Image.open(file_path)
        img = img.resize((640, 360), Image.LANCZOS)
        resized_file_name = f"resized_{file_name}"
        resized_file_path = os.path.join("creatives", resized_file_name)
        img.save(resized_file_path)
        file_path = resized_file_path

    return file_path


# Завершение процесса добавления креатива
def finalize_creative(chat_id, campaign_id):
    creatives = query_db(
        'SELECT creative_id, content_type, content FROM creatives WHERE chat_id = ? AND campaign_id = ?',
        (chat_id, campaign_id))
    media_ids = []
    creative_data = []

    for creative in creatives:
        if creative[1] != 'text':
            media_id = register_media_file(creative[2], campaign_id, creative[1])
            media_ids.append(media_id)
        creative_data.append((creative[0], creative[2], media_id))

    description = query_db('SELECT service FROM ad_campaigns WHERE campaign_id = ?', (campaign_id,), one=True)[0]

    contract = query_db('SELECT ord_id, contractor_id FROM contracts WHERE chat_id = ? ORDER BY ROWID DESC LIMIT 1',
                        (chat_id,), one=True)
    if contract is None:
        bot.send_message(chat_id, "Ошибка: Не найден договор для данного пользователя.")
        return

    contract_ord_id, contractor_id_part = contract

    # Использование правильного ord_id для контракта
    contract_external_id = contract_ord_id

    user_inn = query_db('SELECT inn FROM users WHERE chat_id = ?', (chat_id,), one=True)
    if user_inn is None:
        bot.send_message(chat_id, "Ошибка: Не найден ИНН для данного пользователя.")
        return
    user_inn = user_inn[0]

    user_role = query_db('SELECT role FROM users WHERE chat_id = ?', (chat_id,), one=True)[0]

    if user_role == "advertiser":
        user_info = query_db('SELECT fio, inn FROM users WHERE chat_id = ?', (chat_id,), one=True)
        fio_or_title = user_info[0]
        user_inn = user_info[1]
    else:
        contractor_info = query_db('SELECT fio, title, inn FROM contractors WHERE contractor_id = ?',
                                   (contractor_id_part,), one=True)
        fio_or_title = contractor_info[0] if contractor_info[0] else contractor_info[1]
        user_inn = contractor_info[2]

    for creative_id, _, _ in creative_data:
        response = send_creative_to_ord(chat_id, campaign_id, creatives, description, media_ids, contract_external_id,
                                        user_inn)
        if response is None or 'marker' not in response:
            bot.send_message(chat_id, "Ошибка при отправке креатива в ОРД.")
            return

        marker = response['marker']
        query_db('UPDATE creatives SET token = ?, status = ? WHERE creative_id = ?', (marker, 'active', creative_id))
        query_db('INSERT OR REPLACE INTO creative_links (chat_id, ord_id, creative_id, token) VALUES (?, ?, ?, ?)',
                 (chat_id, contract_external_id, creative_id, marker))

    bot.send_message(chat_id,
                     f"Креативы успешно промаркированы. Ваш токен - {marker}.\n"
                     f"Для копирования нажмите на текст ниже👇\n\n"
                     f"`Реклама. {fio_or_title}. ИНН: {user_inn}. erid: {marker}`",
                     parse_mode="MARKDOWN")
    # Сохранение данных в таблицу statistics
    date_start_actual = datetime.now().strftime('%Y-%m-%d')
    query_db('INSERT INTO statistics (chat_id, campaign_id, creative_id, date_start_actual) VALUES (?, ?, ?, ?)',
             (chat_id, campaign_id, creative_id, date_start_actual))

    # Запрос ссылки на креатив
    ask_for_creative_link(chat_id, contract_external_id)


def register_media_file(file_path, campaign_id, creative_type):
    media_id = f"{campaign_id}_media_{uuid.uuid4()}"
    url = f'https://api-sandbox.ord.vk.com/v1/media/{media_id}'
    headers = {
        'Authorization': 'Bearer 633962f71ade453f997d179af22e2532'
    }
    files = {
        'media_file': open(file_path, 'rb')
    }
    description = query_db('SELECT service FROM ad_campaigns WHERE campaign_id = ?', (campaign_id,), one=True)[0]
    data = {
        'description': description
    }
    response = requests.put(url, headers=headers, files=files, data=data)
    response.raise_for_status()
    return media_id


def send_creative_to_ord(chat_id, campaign_id, creatives, description, media_ids, contract_external_id, user_inn):
    creative_id = query_db(
        'SELECT creative_id FROM creatives WHERE chat_id = ? AND campaign_id = ? ORDER BY rowid DESC LIMIT 1',
        (chat_id, campaign_id), one=True)
    if creative_id is None:
        bot.send_message(chat_id, "Ошибка: Не найден creative_id для указанной кампании.")
        return
    creative_id = creative_id[0]

    url = f"https://api-sandbox.ord.vk.com/v1/creative/{creative_id}"
    headers = {
        "Authorization": "Bearer 633962f71ade453f997d179af22e2532",
        "Content-Type": "application/json"
    }
    data = {
        "contract_external_id": contract_external_id,
        "okveds": ["73.11"],
        "name": creatives[0][1] if creatives else "Creative",
        "brand": query_db('SELECT brand FROM ad_campaigns WHERE campaign_id = ?', (campaign_id,), one=True)[0],
        "category": description,
        "description": description,
        "pay_type": "cpc",
        "form": "text_graphic_block",
        "targeting": "Школьники",
        "url": "https://www.msu.ru",
        "texts": [creative[1] for creative in creatives if creative[0] == 'text'],
        "media_external_ids": media_ids
    }

    logging.debug("Отправка запроса на регистрацию креатива:")
    logging.debug(json.dumps(data, indent=4))

    response = requests.put(url, headers=headers, json=data)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Ошибка при отправке запроса: {e}")
        logging.error(f"Ответ сервера: {response.text}")
        raise
    return response.json()


# Функция для запроса ссылки на креатив
def ask_for_creative_link(chat_id, ord_id):
    msg = bot.send_message(chat_id,
                           "Теперь прикрепите маркировку к вашему креативу, опубликуйте и пришлите ссылку на него. Прикрепить к публикации маркировку может как рекламодатель, так и рекламораспространитель. Если вы публикуете один креатив на разных площадках - пришлите ссылку на каждую площадку.")
    bot.register_next_step_handler(msg, lambda message: handle_creative_link(message, ord_id))

    # Установка таймера для напоминания через час, если ссылка не будет предоставлена
    threading.Timer(3600, check_and_remind_link, [chat_id, ord_id]).start()


# Обработчик ссылки на креатив
def handle_creative_link(message, ord_id):
    chat_id = message.chat.id
    link = message.text
    creative_id = query_db(
        'SELECT creative_id FROM creative_links WHERE chat_id = ? AND ord_id = ? ORDER BY ROWID DESC LIMIT 1',
        (chat_id, ord_id), one=True)
    if creative_id is None:
        bot.send_message(chat_id, "Ошибка: Не найден creative_id для указанной кампании.")
        return
    creative_id = creative_id[0]
    query_db('UPDATE creative_links SET link = ? WHERE chat_id = ? AND ord_id = ? AND creative_id = ?',
             (link, chat_id, ord_id, creative_id))
    bot.send_message(chat_id, "Вы успешно добавили ссылку на ваш рекламный креатив.")

    bot.send_message(
        chat_id,
        "Хотите добавить еще одну ссылку или закончить?",
        reply_markup=kb.get_handle_creative_link_kb(ord_id)
    )


# Добавление ссылки на креатив
@bot.callback_query_handler(func=lambda call: call.data.startswith('add_link_'))
def add_link(call: CallbackQuery):
    ord_id = call.data.split('_')[2]
    msg = bot.send_message(call.message.chat.id,
                           "Опубликуйте ваш креатив и пришлите ссылку на него. Если вы публикуете один креатив на разных площадках - пришлите ссылку на каждую площадку.")
    bot.register_next_step_handler(msg, lambda message: handle_creative_link(message, ord_id))


@bot.callback_query_handler(func=lambda call: call.data.startswith('link_done_'))
def link_done(call: CallbackQuery):
    chat_id = call.message.chat.id
    bot.send_message(chat_id,
                     "Вы успешно добавили все ссылки на креатив. Подать отчетность по показам нужно будет в конце месяца или при завершении публикации. В конце месяца мы вам напомним о подаче отчетности.")


# Функция для проверки и напоминания о ссылке на креатив
def check_and_remind_link(chat_id, ord_id):
    if not query_db('SELECT * FROM creative_links WHERE chat_id = ? AND ord_id = ? AND link IS NOT NULL',
                    (chat_id, ord_id)):
        remind_link(chat_id)


def remind_link(chat_id):
    bot.send_message(chat_id,
                     "Вы получили токен, но не прислали ссылку на ваш креатив. Пришлите, пожалуйста, ссылку. Это нужно для подачи статистики в ОРД.",
                     reply_markup=kb.generate_link_markup())
