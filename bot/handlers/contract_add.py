from telebot import types
from telebot.types import CallbackQuery

import logging

import db
from init import bot, log_error
from utils import get_ord_id
from . import common as cf
from .base import start_contract


### Добавление договоров ####

# Конфигурация логгирования
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


# Функция для получения ord_id
# def get_ord_id(chat_id, contractor_id):
#     return f"{chat_id}.{contractor_id}"


# Обработчик для команды /start_contract
# перенёс функцию в base поменял название, чтоб не совпадали
@bot.message_handler(commands=['start_contract'])
def start_contract_hnd(message: types.Message):
    start_contract(message)


# Обработчик для выбора контрагента
@bot.callback_query_handler(func=lambda call: call.data.startswith('contractor_'))
def handle_contract_contractor_selection(call: CallbackQuery):
    chat_id = call.message.chat.id
    contractor_id = call.data.split('_')[1]
    ord_id = get_ord_id(chat_id, contractor_id)
    db.query_db(
        'INSERT OR IGNORE INTO contracts (chat_id, contractor_id, ord_id) VALUES (?, ?, ?)',
        (chat_id, contractor_id, ord_id)
    )
    logging.debug(
        f"Inserted initial contract record for chat_id: {chat_id}, contractor_id: {contractor_id}, ord_id: {ord_id}")
    bot.send_message(chat_id, "Введите дату начала договора (дд.мм.гггг):")
    bot.register_next_step_handler(call.message, cf.process_contract_start_date, contractor_id)


# Обработчик для выбора НДС
@bot.callback_query_handler(func=lambda call: call.data.startswith("vat_yes_") or call.data.startswith("vat_no_"))
def handle_vat_selection(call: CallbackQuery):
    chat_id = call.message.chat.id
    contractor_id = call.data.split('_')[2]
    vat_included = call.data.startswith("vat_yes")
    ord_id = get_ord_id(chat_id, contractor_id)
    db.query_db(
        'UPDATE contracts SET vat_included = ? WHERE chat_id = ? AND contractor_id = ? AND ord_id = ?',
        (int(vat_included), chat_id, contractor_id, ord_id)
    )
    logging.debug(f"Updated VAT included for ord_id: {ord_id}")
    user_role = db.query_db('SELECT role FROM users WHERE chat_id = ?', (chat_id,), one=True)[0]
    cf.finalize_contract_data(call.message, user_role, contractor_id)
