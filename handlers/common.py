from telebot import types
from telebot.types import CallbackQuery
from datetime import datetime, timedelta
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
import hashlib
from urllib import parse
from urllib.parse import urlparse

import db
import config
import keyboards as kb
from init import bot
import utils


# Обработчик для сбора ФИО ИП контрагента
def fio_i_collector_advertiser(message, contractor_id):
    chat_id = message.chat.id
    fio_i_advertiser = message.text
    db.query_db('UPDATE contractors SET fio = ? WHERE chat_id = ? AND contractor_id = ?',
             (fio_i_advertiser, chat_id, contractor_id))
    bot.send_message(message.chat.id,
                     "Введите ИНН вашего контрагента. Например, 563565286576. ИНН индивидуального предпринимателя совпадает с ИНН физического лица.")
    bot.register_next_step_handler(message, lambda m: inn_collector_advertiser(m, contractor_id))


# Обработчик для сбора ФИО физ. лица контрагента
def fio_collector_advertiser(message, contractor_id):
    chat_id = message.chat.id
    fio_advertiser = message.text
    db.query_db('UPDATE contractors SET fio = ? WHERE chat_id = ? AND contractor_id = ?',
             (fio_advertiser, chat_id, contractor_id))
    bot.send_message(message.chat.id, "Введите ИНН вашего контрагента. Например, 563565286576.")
    bot.register_next_step_handler(message, lambda m: inn_collector_advertiser(m, contractor_id))


# Обработчик для сбора названия организации контрагента
def title_collector_advertiser(message, contractor_id):
    chat_id = message.chat.id
    title_advertiser = message.text
    db.query_db('UPDATE contractors SET title = ? WHERE chat_id = ? AND contractor_id = ?',
             (title_advertiser, chat_id, contractor_id))
    bot.send_message(message.chat.id, "Введите ИНН вашего контрагента. Например, 6141027912.")
    bot.register_next_step_handler(message, lambda m: inn_collector_advertiser(m, contractor_id))


# Валидатор ИНН
def validate_inn1(inn, juridical_type):
    inn = str(inn)

    if juridical_type in ['ip', 'physical']:
        if len(inn) != 12:
            return False
    elif juridical_type == 'juridical':
        if len(inn) != 10:
            return False

    if not re.match(r'^\d{10}$|^\d{12}$', inn):
        return False

    def check_control_digit(inn, coefficients):
        n = sum([int(a) * b for a, b in zip(inn, coefficients)]) % 11
        return n if n < 10 else n % 10

    if len(inn) == 10:
        coefficients = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        return check_control_digit(inn[:-1], coefficients) == int(inn[-1])
    elif len(inn) == 12:
        coefficients1 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        coefficients2 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        return (check_control_digit(inn[:-1], coefficients1) == int(inn[-1]) and
                check_control_digit(inn[:-2], coefficients2) == int(inn[-2]))

    return False


# Обработчик для сбора ИНН контрагента
def inn_collector_advertiser(message, contractor_id):
    chat_id = message.chat.id
    inn_advertiser = message.text.strip()
    juridical_type = db.query_db(
        'SELECT juridical_type FROM contractors WHERE chat_id = ? AND contractor_id = ?',
        (chat_id, contractor_id),
        one=True
    )[0]
    if not validate_inn1(inn_advertiser, juridical_type):
        bot.send_message(chat_id, "Неверный формат ИНН. Пожалуйста, введите корректный ИНН:")
        bot.register_next_step_handler(message, lambda m: inn_collector_advertiser(m, contractor_id))
        return
    db.query_db('UPDATE contractors SET inn = ? WHERE chat_id = ? AND contractor_id = ?',
             (inn_advertiser, chat_id, contractor_id))
    contractor_data = db.query_db(
        'SELECT fio, role, juridical_type, inn, title, ord_id FROM contractors WHERE chat_id = ? AND contractor_id = ?',
        (chat_id, contractor_id), one=True)
    fio, role, juridical_type, inn, title, ord_id = contractor_data
    phone = "+7(922)744-93-08"  # Используем заглушку для номера телефона
    rs_url = "https://example.com" if juridical_type != 'physical' else None  # Используем заглушку для rs_url только для юр. лиц и ИП
    name = title if juridical_type == 'juridical' else fio  # Устанавливаем правильное значение для name
    response = utils.send_contractor_to_ord(ord_id, name, role, juridical_type, inn, phone, rs_url)
    handle_contractor_ord_response(response, message, success_add_distributor, contractor_id, message)


# Функция для обработки ответа от ОРД и дальнейшего выполнения кода для контрагента
def handle_contractor_ord_response(response, message, next_step_function, contractor_id, *args):
    if response and response.status_code in [200, 201]:
        next_step_function(message, *args)  # Передаем аргумент message
    else:
        chat_id = message.chat.id
        delete_contractor(chat_id, contractor_id)
        bot.send_message(
            chat_id,
            f"Произошла ошибка при добавлении контрагента в ОРД: "
            f"{response.status_code if response else 'Нет ответа'}. "
            f"Попробуйте снова.")

        # перенёс
        # register_advertiser_entity(message)
        bot.send_message(
            chat_id,
            "Укажите правовой статус вашего контрагента",
            reply_markup=kb.get_register_advertiser_entity_kb()
        )


# Функция для удаления контрагента из базы данных
def delete_contractor(chat_id, contractor_id):
    db.query_db('DELETE FROM contractors WHERE chat_id = ? AND contractor_id = ?', (chat_id, contractor_id))


# Функция для обработки успешного добавления контрагента
def success_add_distributor(message, *args):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    add_another_button = types.InlineKeyboardButton('Добавить еще контрагента',
                                                    callback_data='add_another_distributor')
    continue_button = types.InlineKeyboardButton('Продолжить', callback_data='continue')
    markup.row(add_another_button, continue_button)
    bot.send_message(chat_id, "Контрагент успешно добавлен!\nВы всегда можете добавить новых контрагентов позже.",
                     reply_markup=markup)


# Функция для запроса бренда
def ask_for_brand(chat_id):
    msg = bot.send_message(chat_id, "Укажите бренд.")
    bot.register_next_step_handler(msg, save_brand)


# Обработчик для сохранения бренда
def save_brand(message):
    chat_id = message.chat.id
    brand = message.text
    campaign_id = db.query_db('SELECT ord_id FROM platforms WHERE chat_id = ? ORDER BY ord_id DESC LIMIT 1', (chat_id,),
                           one=True)

    if campaign_id:
        campaign_id = campaign_id[0]  # Извлекаем значение из результата запроса
        ord_id = utils.get_ord_id(chat_id, campaign_id)
        db.query_db('INSERT INTO ad_campaigns (chat_id, campaign_id, brand, ord_id) VALUES (?, ?, ?, ?)',
                 (chat_id, campaign_id, brand, ord_id))
        logging.debug(f"Inserted campaign record for chat_id: {chat_id}, campaign_id: {campaign_id}, ord_id: {ord_id}")
        bot.send_message(chat_id, "Бренд сохранен.")
        ask_for_service(chat_id, campaign_id)
    else:
        logging.error(f"No campaign_id found for chat_id: {chat_id}")
        bot.send_message(chat_id, "Ошибка: не удалось сохранить бренд.")


# Функция для запроса услуги
def ask_for_service(chat_id, campaign_id):
    msg = bot.send_message(
        chat_id,
        "Кратко опишите товар или услугу, которые вы планируете рекламировать (не более 60 символов)."
    )
    bot.register_next_step_handler(msg, lambda msg: save_service(msg, campaign_id))


# Обработчик для сохранения услуги
def save_service(message, campaign_id):
    chat_id = message.chat.id
    service = message.text[:60]  # Ограничение на 60 символов
    db.query_db('UPDATE ad_campaigns SET service = ? WHERE campaign_id = ?', (service, campaign_id))
    logging.debug(f"Updated service for campaign_id: {campaign_id}")
    bot.send_message(chat_id, "Услуга сохранена.")
    ask_for_target_link(chat_id, campaign_id)


# Функция для запроса целевой ссылки
def ask_for_target_link(chat_id, campaign_id):
    msg = bot.send_message(chat_id, "Пришлите ссылку на товар или услугу, которые вы планируете рекламировать.")
    bot.register_next_step_handler(msg, lambda msg: save_target_link(msg, campaign_id))


# Обработчик для сохранения целевой ссылки
def save_target_link(message, campaign_id):
    chat_id = message.chat.id
    target_link = message.text.strip()
    if not target_link.startswith("http://") and not target_link.startswith("https://"):
        target_link = "https://" + target_link
    db.query_db('INSERT INTO target_links (chat_id, campaign_id, link) VALUES (?, ?, ?)',
             (chat_id, campaign_id, target_link))
    logging.debug(f"Inserted target link for campaign_id: {campaign_id}")
    bot.send_message(chat_id, "Целевая ссылка сохранена.")
    ask_for_additional_link(chat_id, campaign_id)


# Функция для запроса дополнительной ссылки
def ask_for_additional_link(chat_id, campaign_id):
    bot.send_message(chat_id,
                     "Есть ли дополнительная ссылка на товар или услугу, которые вы планируете рекламировать?",
                     reply_markup=kb.get_ask_for_additional_link_kb(campaign_id))


#### Функция для выбора платформы ####
# Функция для сбора ссылки на аккаунт рекламораспространителя
def collect_advertiser_link(message, platform_url):
    print(platform_url)
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
    verification_message = (f"Проверьте, правильно ли указана ссылка на площадку рекламораспространителя:\n"
                            f"{platform_name} - {advertiser_link}")
    bot.send_message(chat_id, verification_message, reply_markup=kb.get_platform_url_collector_kb())


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

        # перенёс
        # preloader_choose_platform(call.message)
        bot.send_message(
            chat_id,
            "Перейти к созданию рекламной площадки?",
            reply_markup=kb.get_preloader_choose_platform_kb()
        )
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
                bot.send_message(
                    chat_id,
                    "Выберите контрагента:",
                    reply_markup=kb.get_process_average_views_kb(contractors)
                )
            else:
                bot.send_message(chat_id,
                                 "Не найдено контрагентов. Пожалуйста, добавьте контрагентов и повторите попытку.")
        else:
            finalize_platform_data(chat_id, str(chat_id))
    else:
        msg = bot.send_message(chat_id,
                               "Неверный формат. Пожалуйста, укажите среднее количество просмотров вашего поста за месяц, используя только цифры:")
        bot.register_next_step_handler(msg, process_average_views)



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


# Функция для отправки данных о платформе в ОРД API
def send_platform_to_ord(ord_id, platform_name, platform_url, average_views, person_external_id, chat_id):
    # чтоб не было ошибки при возврате False
    text_error = 'Response error'
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
        text_error = response.text
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
        logging.error(f"Response text: {text_error}")
        return False


### Добавление договоров ####
# Обработчик для обработки даты начала договора
def process_contract_start_date(message, contractor_id):
    chat_id = message.chat.id
    contract_date = message.text.strip()
    try:
        date_obj = datetime.strptime(contract_date, "%d.%m.%Y")
        formatted_date = date_obj.strftime("%Y-%m-%d")
        ord_id = utils.get_ord_id(chat_id, contractor_id)
        db.query_db('UPDATE contracts SET contract_date = ? WHERE chat_id = ? AND contractor_id = ? AND ord_id = ?',
                 (formatted_date, chat_id, contractor_id, ord_id))
        logging.debug(f"Updated contract start date for ord_id: {ord_id}")
        bot.send_message(chat_id, "Введите дату завершения договора (дд.мм.гггг):")
        bot.register_next_step_handler(message, process_contract_end_date, contractor_id)
    except ValueError:
        logging.error(f"Invalid date format for start date: {contract_date}")
        bot.send_message(chat_id, "Неверный формат даты. Пожалуйста, введите дату в формате дд.мм.гггг:")
        bot.register_next_step_handler(message, process_contract_start_date, contractor_id)


# Обработчик для конпок даты завершения договора

# Обработчик для обработки даты завершения договора
def process_contract_end_date(message, contractor_id):
    chat_id = message.chat.id
    end_date = message.text.strip()
    try:
        date_obj = datetime.strptime(end_date, "%d.%m.%Y")
        formatted_date = date_obj.strftime("%Y-%m-%d")
        ord_id = utils.get_ord_id(chat_id, contractor_id)
        db.query_db('UPDATE contracts SET end_date = ? WHERE chat_id = ? AND contractor_id = ? AND ord_id = ?',
                 (formatted_date, chat_id, contractor_id, ord_id))
        logging.debug(f"Updated contract end date for ord_id: {ord_id}")
        bot.send_message(chat_id, "Введите номер договора:")
        bot.register_next_step_handler(message, process_contract_serial, contractor_id)
    except ValueError:
        logging.error(f"Invalid date format for end date: {end_date}")
        bot.send_message(chat_id, "Неверный формат даты. Пожалуйста, введите дату в формате дд.мм.гггг:")
        bot.register_next_step_handler(message, process_contract_end_date, contractor_id)


# Обработчик для обработки номера договора
def process_contract_serial(message, contractor_id):
    chat_id = message.chat.id
    serial = message.text.strip()
    ord_id = utils.get_ord_id(chat_id, contractor_id)
    db.query_db('UPDATE contracts SET serial = ? WHERE chat_id = ? AND contractor_id = ? AND ord_id = ?',
             (serial, chat_id, contractor_id, ord_id))
    logging.debug(f"Updated contract serial for ord_id: {ord_id}")
    bot.send_message(chat_id, "Введите сумму договора:")
    bot.register_next_step_handler(message, process_contract_amount, contractor_id)


# Обработчик для обработки суммы договора
def process_contract_amount(message, contractor_id):
    chat_id = message.chat.id
    amount = message.text.strip()
    try:
        amount = float(amount)
        ord_id = utils.get_ord_id(chat_id, contractor_id)
        db.query_db('UPDATE contracts SET amount = ? WHERE chat_id = ? AND contractor_id = ? AND ord_id = ?',
                 (amount, chat_id, contractor_id, ord_id))
        logging.debug(f"Updated contract amount for ord_id: {ord_id}")

        # Спросить про НДС
        markup = types.InlineKeyboardMarkup()
        vat_yes_button = types.InlineKeyboardButton("Да", callback_data=f"vat_yes_{contractor_id}")
        vat_no_button = types.InlineKeyboardButton("Нет", callback_data=f"vat_no_{contractor_id}")
        markup.add(vat_yes_button, vat_no_button)
        bot.send_message(chat_id, "Сумма по договору указана с НДС?", reply_markup=markup)
    except ValueError:
        logging.error(f"Invalid amount format: {amount}")
        bot.send_message(chat_id, "Неверный формат суммы. Пожалуйста, введите сумму договора:")
        bot.register_next_step_handler(message, process_contract_amount, contractor_id)


# Функция для завершения процесса добавления данных договора
def finalize_contract_data(message, user_role, contractor_id):
    chat_id = message.chat.id
    ord_id = utils.get_ord_id(chat_id, contractor_id)
    contract_data = db.query_db(
        'SELECT contract_date, end_date, serial, amount, vat_included FROM contracts WHERE chat_id = ? AND contractor_id = ? AND ord_id = ?',
        (chat_id, contractor_id, ord_id), one=True)
    if contract_data:
        contract_date, end_date, serial, amount, vat_included = contract_data
        vat_flag = ["vat_included"] if vat_included else []
        if user_role == "advertiser":
            client_external_id = f"{chat_id}"
            contractor_external_id = f"{chat_id}.{contractor_id}"
        else:
            client_external_id = f"{chat_id}.{contractor_id}"
            contractor_external_id = f"{chat_id}"

        data = {
            "type": "service",
            "client_external_id": str(client_external_id),
            "contractor_external_id": str(contractor_external_id),
            "date": contract_date,
            "serial": str(serial),
            "subject_type": "org_distribution",
            "flags": vat_flag,
            "amount": str(amount)
        }
        response = send_contract_to_ord(ord_id, chat_id, data)
        if response in [200, 201]:
            bot.send_message(chat_id, "Договор успешно зарегистрирован в ОРД.")
            # start_campaign(message)

        #     добавил чтоб не было кругового импорта
            bot.send_message(chat_id, "Введите название бренда, который вы планируете рекламировать.")
            ask_for_brand(chat_id)
        else:
            bot.send_message(chat_id, "Произошла ошибка при регистрации договора в ОРД.")
            logging.error(f"Error registering contract in ORD: {response}")
    else:
        bot.send_message(chat_id, "Произошла ошибка. Данные о договоре не найдены.")
        logging.error(
            f"Contract data not found for chat_id: {chat_id}, contractor_id: {contractor_id}, ord_id: {ord_id}")


# Функция для отправки данных о договоре в ОРД API
def send_contract_to_ord(ord_id, chat_id, data):
    # чтоб не было ошибки при возврате False
    text_error = 'Response error'
    try:
        contract_id = f"{ord_id}"
        url = f"https://api-sandbox.ord.vk.com/v1/contract/{contract_id}"

        headers = {
            "Authorization": "Bearer 633962f71ade453f997d179af22e2532",
            "Content-Type": "application/json"
        }

        logging.debug(f"URL: {url}")
        logging.debug(f"Headers: {headers}")
        logging.debug(f"Data: {data}")

        response = requests.put(url, headers=headers, json=data)
        text_error = response.text
        response.raise_for_status()

        logging.debug(f"Response status code: {response.status_code}")
        logging.debug(f"Response content: {response.content}")

        if response.status_code in [200, 201]:
            return response.status_code
        else:
            logging.error(f"Unexpected status code: {response.status_code}")
            bot.send_message(chat_id, "Договор добавлен, но сервер вернул неожиданный статус.")
            return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"RequestException: {e}")
        bot.send_message(chat_id, "Произошла ошибка при регистрации договора в ОРД.")
        return str(e)
    except ValueError as e:
        logging.error(f"ValueError: {e}")
        logging.error(f"Response text: {text_error}")
        bot.send_message(chat_id, "Произошла ошибка при обработке ответа от сервера ОРД.")
        return str(e)
    
    
####  Добавление креативов ####
# Функция для получения ord_id
def get_creative_ord_id(campaign_ord_id, creative_count):
    return f"{campaign_ord_id}.{creative_count + 1}"


# Начало процесса добавления креатива
def add_creative_start(chat_id, campaign_id):
    logging.debug(f"Начало процесса добавления креатива для кампании: {campaign_id}")
    msg = bot.send_message(
        chat_id,
        "Загрузите файл своего рекламного креатива или введите текст. "
        "Вы можете загрузить несколько файлов для одного креатива."
    )
    bot.register_next_step_handler(msg, lambda message: handle_creative_upload(message, campaign_id))


# Обработчик загрузки креатива
def handle_creative_upload(message, campaign_id):
    chat_id = message.chat.id
    if message.content_type in ['text', 'photo', 'video', 'audio', 'document']:
        creative_content = save_creative(message)
        creative_count = db.query_db('SELECT COUNT(*) FROM creatives WHERE chat_id = ? AND campaign_id = ?',
                                  (chat_id, campaign_id), one=True)
        if creative_count is None:
            creative_count = [0]
        ord_id_data = db.query_db(
            'SELECT ord_id FROM ad_campaigns WHERE campaign_id = ?',
            (campaign_id,),
            one=True
        )
        logging.debug(f"ord_id для кампании {campaign_id}: {ord_id_data}")
        if ord_id_data is None:
            logging.error(f"Не удалось найти ord_id для кампании с campaign_id: {campaign_id}")
            bot.send_message(chat_id, "Ошибка: Не удалось найти ord_id для указанной кампании.")
            return
        ord_id = get_creative_ord_id(ord_id_data[0], creative_count[0])
        db.query_db(
            'INSERT INTO creatives (chat_id, campaign_id, creative_id, content_type, content, ord_id, status) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (chat_id, campaign_id, str(uuid.uuid4()), message.content_type, creative_content, ord_id, 'pending'))
        logging.debug(f"Inserted creative for chat_id: {chat_id}, campaign_id: {campaign_id}, ord_id: {ord_id}")

        bot.send_message(chat_id, "Креатив успешно добавлен. Добавить еще файл или текст для этого креатива?",
                         reply_markup=kb.get_handle_creative_upload_kb(campaign_id))
    else:
        bot.send_message(chat_id, "Ошибка. Пожалуйста, попробуйте еще раз и пришлите креатив.")
        add_creative_start(chat_id, campaign_id)
        
    
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
        # неизвестный атрибут проверить
        resized_clip = clip.resize(newsize=(640, 360))
        resized_file_name = f"resized_{file_name}"
        resized_file_path = os.path.join("creatives", resized_file_name)
        resized_clip.write_videofile(resized_file_path, codec='libx264')
        file_path = resized_file_path

    elif file_type == 'photo':
        img = Image.open(file_path)
        # неизвестный атрибут проверить
        img = img.resize((640, 360), Image.LANCZOS)
        resized_file_name = f"resized_{file_name}"
        resized_file_path = os.path.join("creatives", resized_file_name)
        img.save(resized_file_path)
        file_path = resized_file_path

    return file_path


# Завершение процесса добавления креатива
def finalize_creative(chat_id, campaign_id):
    creatives = db.query_db(
        'SELECT creative_id, content_type, content FROM creatives WHERE chat_id = ? AND campaign_id = ?',
        (chat_id, campaign_id))
    media_ids = []
    creative_data = []

    for creative in creatives:
        if creative[1] != 'text':
            media_id = register_media_file(creative[2], campaign_id, creative[1])
            media_ids.append(media_id)
        else:
            media_id = None
        creative_data.append((creative[0], creative[2], media_id))

    description = db.query_db('SELECT service FROM ad_campaigns WHERE campaign_id = ?', (campaign_id,), one=True)[0]

    contract = db.query_db('SELECT ord_id, contractor_id FROM contracts WHERE chat_id = ? ORDER BY ROWID DESC LIMIT 1',
                        (chat_id,), one=True)
    if contract is None:
        bot.send_message(chat_id, "Ошибка: Не найден договор для данного пользователя.")
        return

    contract_ord_id, contractor_id_part = contract

    # Использование правильного ord_id для контракта
    contract_external_id = contract_ord_id

    user_inn = db.query_db('SELECT inn FROM users WHERE chat_id = ?', (chat_id,), one=True)
    if user_inn is None:
        bot.send_message(chat_id, "Ошибка: Не найден ИНН для данного пользователя.")
        return
    user_inn = user_inn[0]

    user_role = db.query_db('SELECT role FROM users WHERE chat_id = ?', (chat_id,), one=True)[0]

    if user_role == "advertiser":
        user_info = db.query_db('SELECT fio, inn FROM users WHERE chat_id = ?', (chat_id,), one=True)
        fio_or_title = user_info[0]
        user_inn = user_info[1]
    else:
        contractor_info = db.query_db('SELECT fio, title, inn FROM contractors WHERE contractor_id = ?',
                                   (contractor_id_part,), one=True)
        fio_or_title = contractor_info[0] if contractor_info[0] else contractor_info[1]
        user_inn = contractor_info[2]

    # для строки 707. Если creative_data пустая, то в INSERT INTO statistics добавляем None
    creative_id = None
    # для строки 700. Тоже самое, чтоб отправлялось сообщение, если marker не определён
    marker = 'Не найден'
    for creative_id, _, _ in creative_data:
        response = send_creative_to_ord(chat_id, campaign_id, creatives, description, media_ids, contract_external_id,
                                        user_inn)
        if response is None or 'marker' not in response:
            bot.send_message(chat_id, "Ошибка при отправке креатива в ОРД.")
            return

        marker = response['marker']
        db.query_db('UPDATE creatives SET token = ?, status = ? WHERE creative_id = ?', (marker, 'active', creative_id))
        db.query_db('INSERT OR REPLACE INTO creative_links (chat_id, ord_id, creative_id, token) VALUES (?, ?, ?, ?)',
                 (chat_id, contract_external_id, creative_id, marker))

    bot.send_message(chat_id,
                     f"Креативы успешно промаркированы. Ваш токен - {marker}.\n"
                     f"Для копирования нажмите на текст ниже👇\n\n"
                     f"`Реклама. {fio_or_title}. ИНН: {user_inn}. erid: {marker}`",
                     parse_mode="MARKDOWN")
    # Сохранение данных в таблицу statistics
    date_start_actual = datetime.now().strftime('%Y-%m-%d')
    db.query_db('INSERT INTO statistics (chat_id, campaign_id, creative_id, date_start_actual) VALUES (?, ?, ?, ?)',
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
    description = db.query_db('SELECT service FROM ad_campaigns WHERE campaign_id = ?', (campaign_id,), one=True)[0]
    data = {
        'description': description
    }
    response = requests.put(url, headers=headers, files=files, data=data)
    response.raise_for_status()
    return media_id


def send_creative_to_ord(chat_id, campaign_id, creatives, description, media_ids, contract_external_id, user_inn):
    creative_id = db.query_db(
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
        "brand": db.query_db('SELECT brand FROM ad_campaigns WHERE campaign_id = ?', (campaign_id,), one=True)[0],
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
    creative_id = db.query_db(
        'SELECT creative_id FROM creative_links WHERE chat_id = ? AND ord_id = ? ORDER BY ROWID DESC LIMIT 1',
        (chat_id, ord_id), one=True)
    if creative_id is None:
        bot.send_message(chat_id, "Ошибка: Не найден creative_id для указанной кампании.")
        return
    creative_id = creative_id[0]
    db.query_db('UPDATE creative_links SET link = ? WHERE chat_id = ? AND ord_id = ? AND creative_id = ?',
             (link, chat_id, ord_id, creative_id))
    bot.send_message(chat_id, "Вы успешно добавили ссылку на ваш рекламный креатив.")

    bot.send_message(
        chat_id,
        "Хотите добавить еще одну ссылку или закончить?",
        reply_markup=kb.get_handle_creative_link_kb(ord_id)
    )


# Функция для проверки и напоминания о ссылке на креатив
def check_and_remind_link(chat_id, ord_id):
    if not db.query_db('SELECT * FROM creative_links WHERE chat_id = ? AND ord_id = ? AND link IS NOT NULL',
                    (chat_id, ord_id)):
        remind_link(chat_id)


def remind_link(chat_id):
    bot.send_message(
        chat_id,
        "Вы получили токен, но не прислали ссылку на ваш креатив. Пришлите, пожалуйста, ссылку. "
        "Это нужно для подачи статистики в ОРД.",
        reply_markup=kb.generate_link_markup()
    )


### Блок подачи статистики ###
# Глобальная переменная для хранения состояния пользователей
user_state = {}


# Функция для отправки напоминания о подаче статистики
def send_statistics_reminder(chat_id):
    bot.send_message(
        chat_id,
        "Сегодня завершается отчетный период и вам необходимо подать статистику по вашим креативам. "
        "Пожалуйста, подайте статистику."
    )


# Функция для получения данных из базы данных
def get_data_from_db(campaign_id):
    data = db.query_db('''
          SELECT a.brand, a.service, t.link 
          FROM ad_campaigns a
          JOIN target_links t ON a.campaign_id = t.campaign_id
          WHERE a.campaign_id = ?
          ''', (campaign_id,))
    logging.debug(f"Запрос данных из БД для campaign_id {campaign_id}: {data}")
    return data


# Функция для создания сообщения с данными и кнопками
def create_message_text(campaign_id):
    data = db.query_db(
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


# Функция для получения общего количества креативов для пользователя
def get_total_creatives(user_id):
    count = db.query_db('SELECT COUNT(*) FROM ad_campaigns WHERE chat_id = ?', (user_id,), one=True)
    logging.debug(f"Общее количество креативов для user_id {user_id}: {count}")
    return count[0] if count else 0


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


### Оплата ###

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


def process_amount(message):
    try:
        amount = int(message.text)
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        chat_id = message.chat.id
        inv_id = utils.get_next_inv_id(chat_id)  # Получение следующего уникального inv_id
        description = "Пополнение баланса бота для маркировки рекламы || NP"

        payment_link = generate_payment_link(config.mrh_login, config.mrh_pass1, amount, inv_id, description)

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
