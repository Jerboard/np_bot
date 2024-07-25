from telebot import types

import re

import db
from init import bot


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
    juridical_type = \
    db.query_db('SELECT juridical_type FROM contractors WHERE chat_id = ? AND contractor_id = ?', (chat_id, contractor_id),
             one=True)[0]
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
    response = send_contractor_to_ord(ord_id, name, role, juridical_type, inn, phone, rs_url)
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
        register_advertiser_entity(message)


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
        ord_id = get_ord_id(chat_id, campaign_id)
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