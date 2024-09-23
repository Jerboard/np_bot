from aiogram import types
from aiogram.types import CallbackQuery
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
import utils as ut
import config
import keyboards as kb
from init import dp, log_error
from enums import AddContractStep


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






# Функция для удаления контрагента из базы данных
async def delete_contractor(chat_id, contractor_id):
    db.query_db('DELETE FROM contractors WHERE chat_id = ? AND contractor_id = ?', (chat_id, contractor_id))






# Функция для запроса услуги


# Обработчик для сохранения услуги






# Функция для запроса дополнительной ссылки



#### Функция для выбора платформы ####
# Функция для сбора ссылки на аккаунт рекламораспространителя



# Функция для сбора ссылки на площадку рекламораспространителя



# Функция для удаления платформы
async def del_platform(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    platform_name = db.query_db(
        'SELECT platform_name FROM platforms WHERE chat_id = ? AND ord_id = (SELECT MAX(ord_id) FROM platforms WHERE chat_id = ?)',
        (chat_id, chat_id), one=True)
    if platform_name:
        platform_name = platform_name[0]
        db.query_db('DELETE FROM platforms WHERE chat_id = ? AND platform_name = ?', (chat_id, platform_name))
        await message.answer(f"Платформа '{platform_name}' успешно удалена.")

        # перенёс
        # preloader_choose_platform(cb.message)
        await message.answer(
            chat_id,
            "Перейти к созданию рекламной площадки?",
            reply_markup=kb.get_preloader_choose_platform_kb()
        )
    else:
        await message.answer("Ошибка при удалении платформы. Пожалуйста, попробуйте снова.")











### Добавление договоров ####



# Обработчик для конпок даты завершения договора




# Функция для завершения процесса добавления данных договора




    
    
####  Добавление креативов ####
# Функция для получения ord_id
# async def get_creative_ord_id(campaign_ord_id, creative_count):
#     return f"{campaign_ord_id}.{creative_count + 1}"


# # Начало процесса добавления креатива
# async def add_creative_start(chat_id, campaign_id):
#     logging.debug(f"Начало процесса добавления креатива для кампании: {campaign_id}")
#     msg = await message.answer(
#         chat_id,
#         "Загрузите файл своего рекламного креатива или введите текст. "
#         "Вы можете загрузить несколько файлов для одного креатива."
#     )
#     dp.register_next_step(msg, lambda message: handle_creative_upload(message, campaign_id))



        
    



async def download_and_save_file(file_info, file_type, chat_id):
    downloaded_file = dp.download_file(file_info.file_path)
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
# async def finalize_creative(chat_id, campaign_id):
    # creatives = db.query_db(
    #     'SELECT creative_id, content_type, content FROM creatives WHERE chat_id = ? AND campaign_id = ?',
    #     (chat_id, campaign_id))
    # media_ids = []
    # creative_data = []
    #
    # for creative in creatives:
    #     if creative[1] != 'text':
    #         media_id = register_media_file(creative[2], campaign_id, creative[1])
    #         media_ids.append(media_id)
    #     else:
    #         media_id = None
    #
    #     creative_data.append((creative[0], creative[2], media_id))
    #
    # description = db.query_db('SELECT service FROM ad_campaigns WHERE campaign_id = ?', (campaign_id,), one=True)[0]
    # contract = db.query_db('SELECT ord_id, contractor_id FROM contracts WHERE chat_id = ? ORDER BY ID DESC LIMIT 1',
    #                        (chat_id,), one=True)
    # if contract is None:
    #     await message.answer("Ошибка: Не найден договор для данного пользователя.")
    #     return
    #
    # contract_ord_id, contractor_id_part = contract
    #
    # # Использование правильного ord_id для контракта
    # contract_external_id = contract_ord_id
    #
    # user_inn = db.query_db('SELECT inn FROM users WHERE chat_id = ?', (chat_id,), one=True)
    # if user_inn is None:
    #     await message.answer("Ошибка: Не найден ИНН для данного пользователя.")
    #     return
    # user_inn = user_inn[0]
    #
    # user_role = db.query_db('SELECT role FROM users WHERE chat_id = ?', (chat_id,), one=True)[0]
    #
    # if user_role == "advertiser":
    #     user_info = db.query_db('SELECT fio, inn FROM users WHERE chat_id = ?', (chat_id,), one=True)
    #     fio_or_title = user_info[0]
    #     user_inn = user_info[1]
    # else:
    #     contractor_info = db.query_db('SELECT fio, title, inn FROM contractors WHERE contractor_id = ?',
    #                                   (int(contractor_id_part),), one=True)
    #     # Чтоб не вис если не найден contractor_info
    #     fio_or_title = 'н.д.'
    #     if contractor_info:
    #         fio_or_title = contractor_info[0] if contractor_info[0] else contractor_info[1]
    #     user_inn = contractor_info[2] if contractor_info else 'н.д.'
    #
    # # для строки 707. Если creative_data пустая, то в INSERT INTO statistics добавляем None
    # creative_id = None
    # # для строки 700. Тоже самое, чтоб отправлялось сообщение, если marker не определён
    # marker = 'Не найден'
    # for creative_id, _, _ in creative_data:
    #     response = send_creative_to_ord(chat_id, campaign_id, creatives, description, media_ids, contract_external_id,
    #                                     user_inn)
    #     if response is None or 'marker' not in response:
    #         await message.answer("Ошибка при отправке креатива в ОРД.")
    #         return
    #
    #     marker = response['marker']
    #     db.query_db('UPDATE creatives SET token = ?, status = ? WHERE creative_id = ?', (marker, 'active', creative_id))
    #
    #     # постгре
    #     db.insert_creative_links_data(chat_id, contract_external_id, creative_id, marker)
    #     # старый код
    #     # db.query_db('INSERT OR REPLACE INTO creative_links (chat_id, ord_id, creative_id, token) VALUES (?, ?, ?, ?)',
    #     #             (chat_id, contract_external_id, creative_id, marker))
    #
    # await message.answer(chat_id,
    #                  f"Креативы успешно промаркированы. Ваш токен - {marker}.\n"
    #                  f"Для копирования нажмите на текст ниже👇\n\n"
    #                  f"`Реклама. {fio_or_title}. ИНН: {user_inn}. erid: {marker}`",
    #                 parse_mode="MARKDOWN")
    # # Сохранение данных в таблицу statistics
    # date_start_actual = datetime.now().strftime('%Y-%m-%d')
    # db.query_db('INSERT INTO statistics (chat_id, campaign_id, creative_id, date_start_actual) VALUES (?, ?, ?, ?)',
    #             (chat_id, campaign_id, creative_id, date_start_actual))
    #
    # # Запрос ссылки на креатив
    # ask_for_creative_link(chat_id, contract_external_id)




# Функция для запроса ссылки на креатив
async def ask_for_creative_link(chat_id, ord_id):
    msg = await message.answer(
        text="Теперь прикрепите маркировку к вашему креативу, опубликуйте и пришлите ссылку на него. "
             "Прикрепить к публикации маркировку может как рекламодатель, так и рекламораспространитель. "
             "Если вы публикуете один креатив на разных площадках - пришлите ссылку на каждую площадку."
    )
    dp.register_next_step(msg, lambda message: handle_creative_link(message, ord_id))

    # Установка таймера для напоминания через час, если ссылка не будет предоставлена
    # threading.Timer(3600, check_and_remind_link, [chat_id, ord_id]).start()


# Обработчик ссылки на креатив
async def handle_creative_link(message, ord_id):
    chat_id = message.chat.id
    link = message.text
    creative_id = db.query_db(
        'SELECT creative_id FROM creative_links WHERE chat_id = ? AND ord_id = ? ORDER BY ID DESC LIMIT 1',
        (chat_id, ord_id), one=True)
    if creative_id is None:
        await message.answer("Ошибка: Не найден creative_id для указанной кампании.")
        return
    creative_id = creative_id[0]
    db.query_db('UPDATE creative_links SET link = ? WHERE chat_id = ? AND ord_id = ? AND creative_id = ?',
                (link, chat_id, ord_id, creative_id))
    await message.answer("Вы успешно добавили ссылку на ваш рекламный креатив.")

    await message.answer(
        chat_id,
        "Хотите добавить еще одну ссылку или закончить?",
        reply_markup=kb.get_handle_creative_link_kb(ord_id)
    )


# Функция для проверки и напоминания о ссылке на креатив
async def check_and_remind_link(chat_id, ord_id):
    if not db.query_db('SELECT * FROM creative_links WHERE chat_id = ? AND ord_id = ? AND link IS NOT NULL',
                       (chat_id, ord_id)):
        remind_link(chat_id)


async def remind_link(chat_id):
    await message.answer(
        chat_id,
        "Вы получили токен, но не прислали ссылку на ваш креатив. Пришлите, пожалуйста, ссылку. "
        "Это нужно для подачи статистики в ОРД.",
        reply_markup=kb.generate_link_markup()
    )


### Блок подачи статистики ###
# Глобальная переменная для хранения состояния пользователей
user_state = {}


# Функция для отправки напоминания о подаче статистики
async def send_statistics_reminder(chat_id):
    await message.answer(
        chat_id,
        "Сегодня завершается отчетный период и вам необходимо подать статистику по вашим креативам. "
        "Пожалуйста, подайте статистику."
    )


# Функция для получения данных из базы данных
async def get_data_from_db(campaign_id):
    data = db.query_db('''
          SELECT a.brand, a.service, t.link 
          FROM ad_campaigns a
          JOIN target_links t ON a.campaign_id = t.campaign_id
          WHERE a.campaign_id = ?
          ''', (campaign_id,))
    logging.debug(f"Запрос данных из БД для campaign_id {campaign_id}: {data}")
    return data


# Функция для создания сообщения с данными и кнопками
async def create_message_text(campaign_id):
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

    kb = InlineKeyboardBuilder()
    kb.row(
        kb.button(text="◀", callback_data='back'),
        kb.button(text="▶", callback_data='forward')
    )
    kb.row(
        kb.button(text="Выбрать креатив", callback_data=f'select_{campaign_id}')
    )

    return message_text, markup


# Функция для получения общего количества креативов для пользователя
async def get_total_creatives(user_id):
    count = db.query_db('SELECT COUNT(*) FROM ad_campaigns WHERE chat_id = ?', (user_id,), one=True)
    logging.debug(f"Общее количество креативов для user_id {user_id}: {count}")
    return count[0] if count else 0


# Обработка ввода количества показов
# @bot.message(lambda message: True)
async def handle_statistics_input(message):
    if not message.text.isdigit():
        await message.answer(message.chat.id, "Пожалуйста, введите корректное число.")
        dp.register_next_step(message, handle_statistics_input)
        return

    user_id = message.from_user.id
    campaign_id = user_state.get(str(user_id) + "_selected")
    if not campaign_id:
        await message.answer(message.chat.id, "Ошибка: не удалось получить выбранную кампанию.")
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

        await message.answer(message.chat.id, "Вы подали статистику по креативу:\n"
                                          f"Бренд - {brand}\n"
                                          f"Описание услуги - {description}\n"
                                          f"Название площадки - {platform_url}\n"
                                          f"Количество просмотров: {views}\n"
                                          "Всё верно?",
                        reply_markup=confirm_markup())
    else:
        await message.answer(message.chat.id, "Ошибка: не удалось получить данные для креатива.")


# Кнопки подтверждения
async def confirm_markup():
    kb = InlineKeyboardBuilder()
    kb.row(
        kb.button(text="Да, продолжить", callback_data='confirm_yes'),
        kb.button(text="Изменить количество", callback_data='confirm_no')
    )
    return kb.adjust(1).as_markup()


# Функция для отправки статистики в ОРД
async def send_statistics_to_ord(chat_id):
    logging.debug(f"Начало send_statistics_to_ord для chat_id: {chat_id}")
    user_data = user_state.get(str(chat_id) + "_data")
    logging.debug(f"user_data: {user_data}")
    if not user_data:
        await message.answer("Ошибка: не удалось получить данные для отправки в ОРД.")
        return

    campaign_id = user_state.get(str(chat_id) + "_selected")
    logging.debug(f"campaign_id: {campaign_id}")
    views = user_data['views']
    platform_url = user_data['platform_url']
    date_submitted = datetime.now()

    creative_id = db.query_db('SELECT creative_id FROM creatives WHERE campaign_id = ?', (campaign_id,), one=True)
    logging.debug(f"creative_id: {creative_id}")
    if not creative_id:
        await message.answer(f"Ошибка: не удалось получить creative_id для креатива {campaign_id}.")
        return

    creative_id = creative_id[0]

    # Проверка существования pad_external_id
    pad_check_response = requests.get(f'https://api-sandbox.ord.vk.com/v1/pads/{campaign_id}', headers={
        "Authorization": "Bearer 633962f71ade453f997d179af22e2532"
    })

    if pad_check_response.status_code != 200:
        await message.answer(f"Ошибка: pad_external_id {campaign_id} не зарегистрирован в системе ОРД.")
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
        await message.answer("Статистика успешно отправлена в ОРД.")
        logging.debug(f"Статистика успешно отправлена в ОРД для chat_id: {chat_id}")
        # Обновляем состояние пользователя для перехода к следующему креативу
        current_index = user_state.get(str(chat_id) + "_current", 0)
        user_state[str(chat_id) + "_current"] = current_index + 1
        total_creatives = get_total_creatives(chat_id)
        logging.debug(f"Текущий индекс: {current_index}, Общее количество креативов: {total_creatives}")
        if user_state[str(chat_id) + "_current"] < total_creatives:
            current_campaign_id = user_state[chat_id][user_state[str(chat_id) + "_current"]]
            message_text, markup = create_message_text(current_campaign_id)
            await message.answer(message_text, reply_markup=markup, parse_mode='HTML')
        else:
            await message.answer("Вы успешно подали статистику по всем вашим креативам.")
    else:
        await message.answer(f"Ошибка при отправке статистики в ОРД: {response.text}")


# Функция для автоматической подачи статистики за день до конца месяца
async def auto_submit_statistics():
    now = datetime.now()
    next_month = now.month + 1 if now.month < 12 else 1
    next_year = now.year + 1 if next_month == 1 else now.year
    end_of_month = datetime(next_year, next_month, 1) - timedelta(days=1)
    auto_submit_time = end_of_month - timedelta(days=1)

    threading.Timer((auto_submit_time - now).total_seconds(), auto_submit_statistics_for_all).start()


async def auto_submit_statistics_for_all():
    users = db.query_db('SELECT DISTINCT chat_id FROM creatives')
    for user in users:
        chat_id = user[0]
        statistics = db.query_db('SELECT * FROM statistics WHERE chat_id = ?', (chat_id,))
        if not statistics:
            send_statistics_reminder(chat_id)
            submit_statistics_auto(chat_id)


async def submit_statistics_auto(chat_id):
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
async def calculate_signature(*args) -> str:
    return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()


# Парсинг ответа
async def parse_response(request: str) -> dict:
    params = {}
    for item in urlparse(request).query.split('&'):
        key, value = item.split('=')
        params[key] = value
    return params


# Проверка контрольной суммы результата
async def check_signature_result(order_number: int, received_sum: float, received_signature: str, password: str) -> bool:
    signature = calculate_signature(received_sum, order_number, password)
    return signature.lower() == received_signature.lower()


# Генерация ссылки для оплаты
async def generate_payment_link(merchant_login: str, merchant_password_1: str, cost: float, number: int, description: str,
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
async def result_payment(merchant_password_2: str, request: str) -> str:
    param_request = parse_response(request)
    cost = float(param_request['OutSum'])
    number = int(param_request['InvoiceID'])
    signature = param_request['SignatureValue']

    if check_signature_result(number, cost, signature, merchant_password_2):
        return f'OK{param_request["InvoiceID"]}'
    return "bad sign"


# Проверка параметров в скрипте завершения операции (SuccessURL)
async def check_success_payment(merchant_password_1: str, request: str) -> str:
    param_request = parse_response(request)
    cost = float(param_request['OutSum'])
    number = int(param_request['InvoiceID'])
    signature = param_request['SignatureValue']

    if check_signature_result(number, cost, signature, merchant_password_1):
        return "Thank you for using our service"
    return "bad sign"


async def process_amount(message):
    try:
        amount = int(message.text)
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        chat_id = message.chat.id
        inv_id = ut.get_next_inv_id(chat_id)  # Получение следующего уникального inv_id
        description = "Пополнение баланса бота для маркировки рекламы || NP"

        payment_link = generate_payment_link(config.mrh_login, config.mrh_pass1, amount, inv_id, description)

        # сменил запрос на query_db
        # Вставка данных в базу данных
        # conn = sqlite3.connect('bot_database2.db')
        # cursor = conn.cursor()
        # cursor.execute('INSERT INTO payments (chat_id, inv_id, amount, status) VALUES (?, ?, ?, ?)',
        #                (chat_id, inv_id, amount, 'pending'))
        # conn.commit()
        # conn.close()
        db.query_db('INSERT INTO payments (chat_id, inv_id, amount, status) VALUES (?, ?, ?, ?)',
                             (chat_id, inv_id, amount, 'pending'))

        # kb = InlineKeyboardBuilder()
        # button = kb.button(text=text="Оплатить", url=payment_link)
        # # button)
        # await message.answer("Нажмите кнопку ниже, чтобы перейти к оплате:", reply_markup=markup)

    except ValueError as e:
        await message.answer(message.chat.id, "Ошибка: введите корректную сумму (целое число).")
