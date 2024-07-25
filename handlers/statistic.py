from telebot import types
from datetime import datetime, timedelta

import logging
import json
import hashlib
import sqlite3
import requests
import threading
from urllib import parse
from urllib.parse import urlparse

import db
from init import bot
from utils import get_next_inv_id


### Блок подачи статистики ###

# Глобальная переменная для хранения состояния пользователей
user_state = {}


# Функция для отправки напоминания о подаче статистики
def send_statistics_reminder(chat_id):
    bot.send_message(chat_id,
                     "Сегодня завершается отчетный период и вам необходимо подать статистику по вашим креативам. Пожалуйста, подайте статистику.")


# Функция для получения данных из базы данных
def get_data_from_db(campaign_id):
    data = db.db.query_db('''
          SELECT a.brand, a.service, t.link 
          FROM ad_campaigns a
          JOIN target_links t ON a.campaign_id = t.campaign_id
          WHERE a.campaign_id = ?
          ''', (campaign_id,))
    logging.debug(f"Запрос данных из БД для campaign_id {campaign_id}: {data}")
    return data


# Функция для создания сообщения с данными и кнопками
def create_message_text(campaign_id):
    data = db.db.query_db(
        'SELECT a.brand, a.service, t.link '
        'FROM ad_campaigns a '
        'JOIN target_links t ON a.campaign_id = t.campaign_id '
        'WHERE a.campaign_id = ?',
        (campaign_id,),
        one=True
    )

    if not data:
        logging.debug(f"Данные не найдены для campaign_id {campaign_id}")
        return "Данные не найдены.", None

    brand, service, link = data
    message_text = (f"Выберите креатив для подачи:\n"
                    f"Бренд - {brand}\n"
                    f"Описание услуги - {service}\n"
                    f"<a href='{link}'>Ссылка на креатив</a>")

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("◀", callback_data='back'),
        types.InlineKeyboardButton("▶", callback_data='forward')
    )
    markup.row(
        types.InlineKeyboardButton("Выбрать креатив", callback_data=f'select_{campaign_id}')
    )

    return message_text, markup


# Обработка команды /start_statistics
@bot.message_handler(commands=['start_statistics'])
def send_welcome(message):
    user_id = message.from_user.id
    # Получаем первый доступный campaign_id для пользователя
    campaign_ids = db.query_db('SELECT campaign_id FROM ad_campaigns WHERE chat_id = ?', (user_id,))
    if campaign_ids:
        user_state[user_id] = [cid[0] for cid in campaign_ids]  # Сохраняем все доступные campaign_id для пользователя
        user_state[str(user_id) + "_current"] = 0  # Текущий индекс campaign_id
        message_text, markup = create_message_text(user_state[user_id][0])
        bot.send_message(message.chat.id, message_text, reply_markup=markup, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "У вас нет активных кампаний.")


# Функция для получения общего количества креативов для пользователя
def get_total_creatives(user_id):
    count = db.query_db('SELECT COUNT(*) FROM ad_campaigns WHERE chat_id = ?', (user_id,), one=True)
    logging.debug(f"Общее количество креативов для user_id {user_id}: {count}")
    return count[0] if count else 0


# Обработка нажатий на кнопки
@bot.callback_query_handler(func=lambda call: call.data in ['back', 'forward'] or call.data.startswith('select_'))
def callback_query(call):
    user_id = call.from_user.id
    current_index = user_state.get(str(user_id) + "_current", 0)  # Получаем текущий индекс креатива для пользователя
    total_creatives = get_total_creatives(user_id)

    logging.debug(
        f"callback_query: call.data = {call.data}, current_index = {current_index}, total_creatives = {total_creatives}")

    if call.data == 'back':
        current_index = (current_index - 1) % total_creatives
    elif call.data == 'forward':
        current_index = (current_index + 1) % total_creatives
    elif call.data.startswith('select_'):
        selected_campaign_id = call.data.split('_')[1]
        user_state[str(user_id) + "_selected"] = selected_campaign_id
        bot.send_message(call.message.chat.id, "Укажите количество показов по данному креативу:")
        bot.register_next_step_handler(call.message, handle_statistics_input)
        return

    user_state[str(user_id) + "_current"] = current_index
    current_campaign_id = user_state[user_id][current_index]
    message_text, markup = create_message_text(current_campaign_id)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=message_text, reply_markup=markup, parse_mode='HTML')


# Обработка ввода количества показов
# @bot.message_handler(func=lambda message: True)
def handle_statistics_input(message):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное число.")
        bot.register_next_step_handler(message, handle_statistics_input)
        return

    user_id = message.from_user.id
    campaign_id = user_state.get(str(user_id) + "_selected")
    if not campaign_id:
        bot.send_message(message.chat.id, "Ошибка: не удалось получить выбранную кампанию.")
        return

    views = int(message.text)

    data = get_data_from_db(campaign_id)
    if data:
        brand, description, link = data[0]  # так как get_data_from_db возвращает список кортежей
        platform_url = link  # заменим platform_url на link

        # Сохраняем данные в user_state для последующего подтверждения
        user_state[str(user_id) + "_data"] = {
            'views': views,
            'brand': brand,
            'description': description,
            'platform_url': platform_url
        }

        bot.send_message(message.chat.id, "Вы подали статистику по креативу:\n"
                                          f"Бренд - {brand}\n"
                                          f"Описание услуги - {description}\n"
                                          f"Название площадки - {platform_url}\n"
                                          f"Количество просмотров: {views}\n"
                                          "Всё верно?",
                         reply_markup=confirm_markup())
    else:
        bot.send_message(message.chat.id, "Ошибка: не удалось получить данные для креатива.")


# Кнопки подтверждения
def confirm_markup():
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("Да, продолжить", callback_data='confirm_yes'),
        types.InlineKeyboardButton("Изменить количество", callback_data='confirm_no')
    )
    return markup


# Обработка подтверждения
@bot.callback_query_handler(func=lambda call: call.data in ['confirm_yes', 'confirm_no'])
def handle_confirm(call):
    chat_id = call.message.chat.id
    logging.debug(f"handle_confirm: call.data = {call.data}")
    if call.data == 'confirm_yes':
        logging.debug("Обработка подтверждения: call.data = confirm_yes")
        send_statistics_to_ord(chat_id)
    elif call.data == 'confirm_no':
        bot.send_message(chat_id, "Введите корректное количество показов:")
        bot.register_next_step_handler(call.message, handle_statistics_input)


# Функция для отправки статистики в ОРД
def send_statistics_to_ord(chat_id):
    logging.debug(f"Начало send_statistics_to_ord для chat_id: {chat_id}")
    user_data = user_state.get(str(chat_id) + "_data")
    logging.debug(f"user_data: {user_data}")
    if not user_data:
        bot.send_message(chat_id, "Ошибка: не удалось получить данные для отправки в ОРД.")
        return

    campaign_id = user_state.get(str(chat_id) + "_selected")
    logging.debug(f"campaign_id: {campaign_id}")
    views = user_data['views']
    platform_url = user_data['platform_url']
    date_submitted = datetime.now()

    creative_id = db.query_db('SELECT creative_id FROM creatives WHERE campaign_id = ?', (campaign_id,), one=True)
    logging.debug(f"creative_id: {creative_id}")
    if not creative_id:
        bot.send_message(chat_id, f"Ошибка: не удалось получить creative_id для креатива {campaign_id}.")
        return

    creative_id = creative_id[0]

    # Проверка существования pad_external_id
    pad_check_response = requests.get(f'https://api-sandbox.ord.vk.com/v1/pads/{campaign_id}', headers={
        "Authorization": "Bearer 633962f71ade453f997d179af22e2532"
    })

    if pad_check_response.status_code != 200:
        bot.send_message(chat_id, f"Ошибка: pad_external_id {campaign_id} не зарегистрирован в системе ОРД.")
        return

    date_start_actual = db.query_db(
        'SELECT date_start_actual FROM statistics WHERE campaign_id = ? AND creative_id = ? ORDER BY date_start_actual LIMIT 1',
        (campaign_id, creative_id), one=True)[0]

    items = [{
        "creative_external_id": creative_id,
        "pad_external_id": campaign_id,
        "shows_count": views,
        "date_start_actual": date_start_actual,
        "date_end_actual": datetime.now().strftime('%Y-%m-%d')
    }]

    data = {
        "items": items
    }

    headers = {
        "Authorization": "Bearer 633962f71ade453f997d179af22e2532",
        "Content-Type": "application/json"
    }

    logging.debug("Отправка статистики в ОРД: %s", json.dumps(data, indent=4))

    response = requests.post('https://api-sandbox.ord.vk.com/v1/statistics', headers=headers, json=data)

    logging.debug("Ответ ОРД: %s", response.text)

    if response.status_code in [200, 201]:
        bot.send_message(chat_id, "Статистика успешно отправлена в ОРД.")
        logging.debug(f"Статистика успешно отправлена в ОРД для chat_id: {chat_id}")
        # Обновляем состояние пользователя для перехода к следующему креативу
        current_index = user_state.get(str(chat_id) + "_current", 0)
        user_state[str(chat_id) + "_current"] = current_index + 1
        total_creatives = get_total_creatives(chat_id)
        logging.debug(f"Текущий индекс: {current_index}, Общее количество креативов: {total_creatives}")
        if user_state[str(chat_id) + "_current"] < total_creatives:
            current_campaign_id = user_state[chat_id][user_state[str(chat_id) + "_current"]]
            message_text, markup = create_message_text(current_campaign_id)
            bot.send_message(chat_id, message_text, reply_markup=markup, parse_mode='HTML')
        else:
            bot.send_message(chat_id, "Вы успешно подали статистику по всем вашим креативам.")
    else:
        bot.send_message(chat_id, f"Ошибка при отправке статистики в ОРД: {response.text}")


# Функция для автоматической подачи статистики за день до конца месяца
def auto_submit_statistics():
    now = datetime.now()
    next_month = now.month + 1 if now.month < 12 else 1
    next_year = now.year + 1 if next_month == 1 else now.year
    end_of_month = datetime(next_year, next_month, 1) - timedelta(days=1)
    auto_submit_time = end_of_month - timedelta(days=1)

    threading.Timer((auto_submit_time - now).total_seconds(), auto_submit_statistics_for_all).start()


def auto_submit_statistics_for_all():
    users = db.query_db('SELECT DISTINCT chat_id FROM creatives')
    for user in users:
        chat_id = user[0]
        statistics = db.query_db('SELECT * FROM statistics WHERE chat_id = ?', (chat_id,))
        if not statistics:
            send_statistics_reminder(chat_id)
            submit_statistics_auto(chat_id)


def submit_statistics_auto(chat_id):
    active_creatives = db.query_db('SELECT campaign_id, creative_id FROM creatives WHERE chat_id = ?', (chat_id,))
    for campaign_id, creative_id in active_creatives:
        platform_url = db.query_db('SELECT link FROM creative_links WHERE chat_id = ? AND creative_id = ?',
                                (chat_id, creative_id), one=True)
        if not platform_url:
            continue

        platform_url = platform_url[0]
        average_views = db.query_db('SELECT average_views FROM platforms WHERE chat_id = ?', (chat_id,), one=True)
        if not average_views:
            continue

        average_views = average_views[0]
        db.query_db(
            'INSERT INTO statistics (chat_id, campaign_id, creative_id, platform_url, views, date_submitted) VALUES (?, ?, ?, ?, ?, ?)',
            (chat_id, campaign_id, creative_id, platform_url, average_views, datetime.now()))
    send_statistics_to_ord(chat_id)


# Вызов функции для автоматической подачи статистики
auto_submit_statistics()

### Оплата ###

# Параметры магазина
mrh_login = "markirovkaNP"
mrh_pass1 = "shNcJ5nQpyx9821eemKM"
mrh_pass2 = "LGb9k7QMZ5c3lzuqM2pI"


# Функция для расчета контрольной суммы
def calculate_signature(*args) -> str:
    return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()


# Парсинг ответа
def parse_response(request: str) -> dict:
    params = {}
    for item in urlparse(request).query.split('&'):
        key, value = item.split('=')
        params[key] = value
    return params


# Проверка контрольной суммы результата
def check_signature_result(order_number: int, received_sum: float, received_signature: str, password: str) -> bool:
    signature = calculate_signature(received_sum, order_number, password)
    return signature.lower() == received_signature.lower()


# Генерация ссылки для оплаты
def generate_payment_link(merchant_login: str, merchant_password_1: str, cost: float, number: int, description: str,
                          robokassa_payment_url='https://auth.robokassa.ru/Merchant/Index.aspx') -> str:
    signature = calculate_signature(merchant_login, cost, number, merchant_password_1)
    data = {
        'MerchantLogin': merchant_login,
        'OutSum': cost,
        'InvoiceID': number,
        'Description': description,
        'SignatureValue': signature
    }
    return f'{robokassa_payment_url}?{parse.urlencode(data)}'


# Получение уведомления об исполнении операции (ResultURL)
def result_payment(merchant_password_2: str, request: str) -> str:
    param_request = parse_response(request)
    cost = float(param_request['OutSum'])
    number = int(param_request['InvoiceID'])
    signature = param_request['SignatureValue']

    if check_signature_result(number, cost, signature, merchant_password_2):
        return f'OK{param_request["InvoiceID"]}'
    return "bad sign"


# Проверка параметров в скрипте завершения операции (SuccessURL)
def check_success_payment(merchant_password_1: str, request: str) -> str:
    param_request = parse_response(request)
    cost = float(param_request['OutSum'])
    number = int(param_request['InvoiceID'])
    signature = param_request['SignatureValue']

    if check_signature_result(number, cost, signature, merchant_password_1):
        return "Thank you for using our service"
    return "bad sign"


# Команда /pay для Telegram бота
@bot.message_handler(commands=['pay'])
def ask_amount(message):
    chat_id = message.chat.id
    balance = db.query_db('SELECT balance FROM users WHERE chat_id = ?', (chat_id,), one=True)
    if balance:
        balance_amount = balance[0]
        logging.debug(f"Баланс пользователя {chat_id}: {balance_amount}")
        msg = bot.send_message(message.chat.id,
                               f"На вашем балансе {balance_amount} рублей. \n\n Введите сумму, на которую хотите пополнить баланс. \n\n Стоимость маркировки одного креатива составляет 400 рублей.")
        bot.register_next_step_handler(msg, process_amount)
    else:
        logging.error(f"Не удалось получить баланс для пользователя {chat_id}")
        bot.send_message(message.chat.id, "Ошибка: не удалось получить ваш баланс. Пожалуйста, попробуйте позже.")


def process_amount(message):
    try:
        amount = int(message.text)
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        chat_id = message.chat.id
        inv_id = get_next_inv_id(chat_id)  # Получение следующего уникального inv_id
        description = "Пополнение баланса бота для маркировки рекламы || NP"

        payment_link = generate_payment_link(mrh_login, mrh_pass1, amount, inv_id, description)

        # Вставка данных в базу данных
        conn = sqlite3.connect('bot_database2.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO payments (chat_id, inv_id, amount, status) VALUES (?, ?, ?, ?)',
                       (chat_id, inv_id, amount, 'pending'))
        conn.commit()
        conn.close()

        markup = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton(text="Оплатить", url=payment_link)
        markup.add(button)
        bot.send_message(chat_id, "Нажмите кнопку ниже, чтобы перейти к оплате:", reply_markup=markup)

    except ValueError as e:
        bot.send_message(message.chat.id, "Ошибка: введите корректную сумму (целое число).")