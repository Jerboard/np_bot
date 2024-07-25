from telebot import types
from telebot.types import CallbackQuery

import logging
import requests

import db
import keyboards as kb
from init import bot
from .statistic import ask_amount


#### Функция для выбора платформы ####
@bot.message_handler(commands=['preloader_choose_platform'])
def preloader_choose_platform(message):
    chat_id = message.chat.id

    bot.send_message(
        chat_id,
        "Перейти к созданию рекламной площадки?",
        reply_markup=kb.get_preloader_choose_platform_kb()
    )


@bot.callback_query_handler(func=lambda call: call.data == 'no_choose_platform')
def no_choose_platform(call: CallbackQuery):
    chat_id = call.message.chat.id
    bot.send_message(
        chat_id,
        "Вы можете в любой момент продолжить добавление рекламной площадки нажав на соответствующий пункт в меню"
    )


@bot.callback_query_handler(func=lambda call: call.data == 'choose_platform')
def choose_platform(call: CallbackQuery):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Выберите площадку:", reply_markup=kb.get_choose_platform_kb())


# Функция для сбора ссылки на аккаунт рекламораспространителя
def collect_advertiser_link(message, platform_url):
    chat_id = message.chat.id
    global advertiser_link
    advertiser_link = message.text.strip()  # Получаем введенную ссылку и убираем лишние пробелы
    if not advertiser_link.startswith("https://"):
        advertiser_link = platform_url + advertiser_link  # Если ссылка не начинается с "https://", добавляем префикс
    platform_url_collector(message)


# Функция для сбора ссылки на площадку рекламораспространителя
def platform_url_collector(message):
    global platform_url, platform_name, advertiser_link
    platform_url = advertiser_link  # Используем advertiser_link вместо message.text.strip()
    chat_id = message.chat.id
    verification_message = f"Проверьте, правильно ли указана ссылка на площадку рекламораспространителя:\n{platform_name} - {advertiser_link}"
    bot.send_message(chat_id, verification_message, reply_markup=kb.get_platform_url_collector_kb())


@bot.callback_query_handler(
    func=lambda call: call.data in ['vk', 'instagram', 'youtube', 'telegram_channel', 'personal_telegram', 'other'])
def collect_platform(call: CallbackQuery):
    chat_id = call.message.chat.id
    global platform_name
    if call.data == 'vk':
        platform_name = 'ВКонтакте'
        bot.send_message(chat_id, "Пришлите ссылку на аккаунт рекламораспространителя.")
        bot.register_next_step_handler(call.message,
                                       lambda message: collect_advertiser_link(message, "https://vk.com/"))
    elif call.data == 'instagram':
        platform_name = 'Instagram'
        bot.send_message(chat_id, "Пришлите ссылку на аккаунт рекламораспространителя.")
        bot.register_next_step_handler(call.message,
                                       lambda message: collect_advertiser_link(message, "https://instagram.com/"))
    elif call.data == 'youtube':
        platform_name = 'YouTube'
        bot.send_message(chat_id, "Пришлите ссылку на аккаунт рекламораспространителя.")
        bot.register_next_step_handler(call.message,
                                       lambda message: collect_advertiser_link(message, "https://youtube.com/"))
    elif call.data == 'telegram_channel':
        platform_name = 'Telegram-канал'
        bot.send_message(chat_id, "Пришлите ссылку на аккаунт рекламораспространителя.")
        bot.register_next_step_handler(call.message,
                                       lambda message: collect_advertiser_link(message, "https://t.me/"))
    elif call.data == 'personal_telegram':
        platform_name = 'Личный профиль Telegram'
        bot.send_message(chat_id, "Пришлите ссылку на аккаунт рекламораспространителя.")
        bot.register_next_step_handler(call.message,
                                       lambda message: collect_advertiser_link(message, "https://t.me/"))
    elif call.data == 'other':
        platform_name = 'Другое'
        bot.send_message(chat_id, "Пришлите ссылку на площадку рекламораспространителя.")
        bot.register_next_step_handler(call.message, platform_url_collector)


@bot.callback_query_handler(
    func=lambda call: call.data in ['correct_platform', 'change_platform', 'delete_platform'])
def handle_platform_verification(call: CallbackQuery):
    chat_id = call.message.chat.id
    if call.data == 'correct_platform':
        request_average_views(chat_id)
    elif call.data == 'change_platform':
        choose_platform(call)
    elif call.data == 'delete_platform':
        del_platform(call)


# Функция для удаления платформы
def del_platform(call: CallbackQuery):
    chat_id = call.message.chat.id
    platform_name = db.query_db(
        'SELECT platform_name FROM platforms WHERE chat_id = ? AND ord_id = (SELECT MAX(ord_id) FROM platforms WHERE chat_id = ?)',
        (chat_id, chat_id), one=True)
    if platform_name:
        platform_name = platform_name[0]
        db.query_db('DELETE FROM platforms WHERE chat_id = ? AND platform_name = ?', (chat_id, platform_name))
        bot.send_message(chat_id, f"Платформа '{platform_name}' успешно удалена.")
        preloader_choose_platform(call.message)
    else:
        bot.send_message(chat_id, "Ошибка при удалении платформы. Пожалуйста, попробуйте снова.")


# Функция для запроса среднего количества просмотров
def request_average_views(chat_id):
    msg = bot.send_message(chat_id, "Укажите среднее количество просмотров поста за месяц:")
    bot.register_next_step_handler(msg, process_average_views)


# Функция для проверки введенных данных и перехода к следующему шагу
def process_average_views(message):
    chat_id = message.chat.id
    average_views = message.text
    if average_views.isdigit():
        ord_id = f"{chat_id}-p-{len(db.query_db('SELECT * FROM platforms WHERE chat_id = ?', (chat_id,))) + 1}"
        db.query_db(
            'INSERT OR REPLACE INTO platforms (chat_id, platform_name, platform_url, average_views, ord_id) VALUES (?, ?, ?, ?, ?)',
            (chat_id, platform_name, platform_url, average_views, ord_id))

        # Получение person_external_id для РР
        user_role = db.query_db('SELECT role FROM users WHERE chat_id = ?', (chat_id,), one=True)[0]
        if user_role == 'advertiser':
            contractors = db.query_db('SELECT contractor_id, fio, title FROM contractors WHERE chat_id = ?',
                                   (chat_id,))
            if contractors:
                bot.send_message(chat_id, "Выберите контрагента:", reply_markup=kb.get_process_average_views_kb())
            else:
                bot.send_message(chat_id,
                                 "Не найдено контрагентов. Пожалуйста, добавьте контрагентов и повторите попытку.")
        else:
            finalize_platform_data(chat_id, str(chat_id))
    else:
        msg = bot.send_message(chat_id,
                               "Неверный формат. Пожалуйста, укажите среднее количество просмотров вашего поста за месяц, используя только цифры:")
        bot.register_next_step_handler(msg, process_average_views)


@bot.callback_query_handler(func=lambda call: call.data.startswith('contractor1_'))
def handle_contractor_selection(call: CallbackQuery):
    chat_id = call.message.chat.id
    contractor_id = call.data.split('_')[1]
    finalize_platform_data(chat_id, contractor_id)


# Функция для завершения процесса добавления данных платформы
def finalize_platform_data(chat_id, contractor_id):
    platform_data = db.query_db(
        'SELECT platform_name, platform_url, average_views, ord_id FROM platforms WHERE chat_id = ? AND ord_id = (SELECT MAX(ord_id) FROM platforms WHERE chat_id = ?)',
        (chat_id, chat_id), one=True)
    if platform_data:
        platform_name, platform_url, average_views, ord_id = platform_data
        person_external_id = f"{chat_id}.{contractor_id}"
        response = send_platform_to_ord(ord_id, platform_name, platform_url, average_views, person_external_id, chat_id)
        bot.send_message(chat_id, "Площадка успешно зарегистрирована в ОРД.")
        db.query_db('INSERT OR REPLACE INTO selected_contractors (chat_id, contractor_id) VALUES (?, ?)',
                 (chat_id, contractor_id))

        bot.send_message(chat_id, "Добавить новую площадку или продолжить?", reply_markup=kb.get_finalize_platform_data_kb())


@bot.callback_query_handler(func=lambda call: call.data in ['add_another_platform', 'continue_to_entity'])
def handle_success_add_platform(call: CallbackQuery):
    chat_id = call.message.chat.id
    role = db.query_db('SELECT role FROM users WHERE chat_id = ?', (chat_id,), one=True)[0]
    if call.data == 'add_another_platform':
        choose_platform(call)
    elif call.data == 'continue_to_entity':
        if role == 'advertiser':
            bot.send_message(chat_id, "Теперь укажите информацию о договоре.")
            start_contract(call.message)
        elif role == 'publisher':
            preloader_advertiser_entity(call.message)
            # bot.send_message(chat_id, "Теперь укажите информацию о контрагенте.")
            # register_advertiser_entity(call.message)


# Функция для отправки данных о платформе в ОРД API
def send_platform_to_ord(ord_id, platform_name, platform_url, average_views, person_external_id, chat_id):
    try:
        url = f"https://api-sandbox.ord.vk.com/v1/pad/{ord_id}"

        headers = {
            "Authorization": "Bearer 633962f71ade453f997d179af22e2532",
            "Content-Type": "application/json"
        }

        data = {
            "person_external_id": person_external_id,
            "is_owner": True,
            "type": "web",
            "name": platform_name,
            "url": platform_url
        }

        logging.debug(f"URL: {url}")
        logging.debug(f"Headers: {headers}")
        logging.debug(f"Data: {data}")

        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()

        logging.debug(f"Response status code: {response.status_code}")
        logging.debug(f"Response content: {response.content}")

        if response.status_code in [200, 201]:
            return True
        else:
            bot.send_message(chat_id, "Площадка добавлена, но сервер вернул неожиданный статус.")
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"RequestException: {e}")
        return False
    except ValueError as e:
        logging.error(f"ValueError: {e}")
        logging.error(f"Response text: {response.text}")
        return False