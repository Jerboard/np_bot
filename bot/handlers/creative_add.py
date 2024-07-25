from telebot.types import CallbackQuery

import logging
import sqlite3

import db
import keyboards as kb
from init import bot
from . import common as cf
from .base import ask_amount


####  Добавление креативов ####
# Настройка логирования
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


# # Функция для выполнения запросов к базе данных с логированием
# def query_db(query, args=(), one=False):
#     logging.debug(f"Выполнение запроса: {query} с аргументами {args}")
#     with sqlite3.connect('bot_database2.db', check_same_thread=False) as conn:
#         cursor = conn.cursor()
#         cursor.execute(query, args)
#         conn.commit()
#         r = cursor.fetchall()
#         cursor.close()
#         logging.debug(f"Результат запроса: {r}")
#         return (r[0] if r else None) if one else r


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
    campaigns = db.query_db('SELECT campaign_id, brand, service FROM ad_campaigns WHERE chat_id = ?', (chat_id,))
    logging.debug(f"Рекламные кампании для пользователя {chat_id}: {campaigns}")
    if not campaigns:
        bot.send_message(
            chat_id,
            "У вас нет активных рекламных кампаний. Пожалуйста, создайте кампанию перед добавлением креатива."
        )
        return

    bot.send_message(chat_id, "Выберите рекламную кампанию для этого креатива:", reply_markup=kb.get_add_creative_kb(campaigns))


# Обработчик выбора рекламной кампании
@bot.callback_query_handler(func=lambda call: call.data.startswith('choose_campaign_'))
def choose_campaign_callback(call: CallbackQuery):
    chat_id = call.message.chat.id
    campaign_id = call.data.split('_')[2]
    logging.debug(f"Выбранная рекламная кампания: {campaign_id}")
    cf.add_creative_start(chat_id, campaign_id)


# Обработчик кнопки "Добавить файл или текст"
@bot.callback_query_handler(func=lambda call: call.data.startswith('add_more_'))
def add_more_creative(call: CallbackQuery):
    campaign_id = call.data.split('_')[2]
    cf.add_creative_start(call.message.chat.id, campaign_id)


# Обработчик кнопки "Продолжить"
@bot.callback_query_handler(func=lambda call: call.data.startswith('continue_creative_'))
def choose_campaign(call: CallbackQuery):
    chat_id = call.message.chat.id
    campaign_id = call.data.split('_')[2]
    cf.finalize_creative(chat_id, campaign_id)


# Добавление ссылки на креатив
@bot.callback_query_handler(func=lambda call: call.data.startswith('add_link_'))
def add_link(call: CallbackQuery):
    ord_id = call.data.split('_')[2]
    msg = bot.send_message(call.message.chat.id,
                           "Опубликуйте ваш креатив и пришлите ссылку на него. Если вы публикуете один креатив на разных площадках - пришлите ссылку на каждую площадку.")
    bot.register_next_step_handler(msg, lambda message: cf.handle_creative_link(message, ord_id))


@bot.callback_query_handler(func=lambda call: call.data.startswith('link_done_'))
def link_done(call: CallbackQuery):
    chat_id = call.message.chat.id
    bot.send_message(
        chat_id,
        "Вы успешно добавили все ссылки на креатив. "
        "Подать отчетность по показам нужно будет в конце месяца или при завершении публикации. "
        "В конце месяца мы вам напомним о подаче отчетности.")
