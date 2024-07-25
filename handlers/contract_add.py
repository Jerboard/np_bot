from telebot import types
from telebot.types import CallbackQuery
from datetime import datetime

import logging
import requests

import db
import keyboards as kb
from init import bot


### Добавление договоров ####

# Конфигурация логгирования
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


# Функция для получения ord_id
def get_ord_id(chat_id, contractor_id):
    return f"{chat_id}.{contractor_id}"


# Обработчик для команды /start_contract
@bot.message_handler(commands=['start_contract'])
def start_contract(message):
    chat_id = message.chat.id
    selected_contractor = db.query_db('SELECT contractor_id FROM selected_contractors WHERE chat_id = ?', (chat_id,),
                                   one=True)

    if selected_contractor:
        contractor_id = selected_contractor[0]
        ord_id = get_ord_id(chat_id, contractor_id)
        db.query_db('INSERT OR IGNORE INTO contracts (chat_id, contractor_id, ord_id) VALUES (?, ?, ?)',
                 (chat_id, contractor_id, ord_id))
        logging.debug(f"Selected contractor: {contractor_id} for chat_id: {chat_id}")
        bot.send_message(chat_id, f"Выбранный ранее контрагент будет использован: № {contractor_id}")
        bot.send_message(chat_id, "Введите дату начала договора (дд.мм.гггг):")
        bot.register_next_step_handler(message, process_contract_start_date, contractor_id)
    else:
        bot.send_message(chat_id, "Контрагент не был выбран. Пожалуйста, выберите контрагента.")
        contractors = db.query_db('SELECT contractor_id, fio, title FROM contractors WHERE chat_id = ?', (chat_id,))
        if contractors:
            markup = types.InlineKeyboardMarkup()
            for contractor in contractors:
                contractor_name = contractor[2] if contractor[2] else contractor[1]  # Используем title или fio
                contractor_button = types.InlineKeyboardButton(contractor_name,
                                                               callback_data=f"contractor_{contractor[0]}")
                markup.add(contractor_button)
            bot.send_message(chat_id, "Выберите контрагента:", reply_markup=markup)


# Обработчик для выбора контрагента
@bot.callback_query_handler(func=lambda call: call.data.startswith('contractor_'))
def handle_contract_contractor_selection(call: CallbackQuery):
    chat_id = call.message.chat.id
    contractor_id = call.data.split('_')[1]
    ord_id = get_ord_id(chat_id, contractor_id)
    db.query_db('INSERT OR IGNORE INTO contracts (chat_id, contractor_id, ord_id) VALUES (?, ?, ?)',
             (chat_id, contractor_id, ord_id))
    logging.debug(
        f"Inserted initial contract record for chat_id: {chat_id}, contractor_id: {contractor_id}, ord_id: {ord_id}")
    bot.send_message(chat_id, "Введите дату начала договора (дд.мм.гггг):")
    bot.register_next_step_handler(call.message, process_contract_start_date, contractor_id)


# Обработчик для обработки даты начала договора
def process_contract_start_date(message, contractor_id):
    chat_id = message.chat.id
    contract_date = message.text.strip()
    try:
        date_obj = datetime.strptime(contract_date, "%d.%m.%Y")
        formatted_date = date_obj.strftime("%Y-%m-%d")
        ord_id = get_ord_id(chat_id, contractor_id)
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
        ord_id = get_ord_id(chat_id, contractor_id)
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
    ord_id = get_ord_id(chat_id, contractor_id)
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
        ord_id = get_ord_id(chat_id, contractor_id)
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


# Обработчик для выбора НДС
@bot.callback_query_handler(func=lambda call: call.data.startswith("vat_yes_") or call.data.startswith("vat_no_"))
def handle_vat_selection(call: CallbackQuery):
    chat_id = call.message.chat.id
    contractor_id = call.data.split('_')[2]
    vat_included = call.data.startswith("vat_yes")
    ord_id = get_ord_id(chat_id, contractor_id)
    db.query_db('UPDATE contracts SET vat_included = ? WHERE chat_id = ? AND contractor_id = ? AND ord_id = ?',
             (vat_included, chat_id, contractor_id, ord_id))
    logging.debug(f"Updated VAT included for ord_id: {ord_id}")
    user_role = db.query_db('SELECT role FROM users WHERE chat_id = ?', (chat_id,), one=True)[0]
    finalize_contract_data(call.message, user_role, contractor_id)


# Функция для завершения процесса добавления данных договора
def finalize_contract_data(message, user_role, contractor_id):
    chat_id = message.chat.id
    ord_id = get_ord_id(chat_id, contractor_id)
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
            start_campaign(message)
        else:
            bot.send_message(chat_id, "Произошла ошибка при регистрации договора в ОРД.")
            logging.error(f"Error registering contract in ORD: {response}")
    else:
        bot.send_message(chat_id, "Произошла ошибка. Данные о договоре не найдены.")
        logging.error(
            f"Contract data not found for chat_id: {chat_id}, contractor_id: {contractor_id}, ord_id: {ord_id}")


# Функция для отправки данных о договоре в ОРД API
def send_contract_to_ord(ord_id, chat_id, data):
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
        logging.error(f"Response text: {response.text}")
        bot.send_message(chat_id, "Произошла ошибка при обработке ответа от сервера ОРД.")
        return str(e)