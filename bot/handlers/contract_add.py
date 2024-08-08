from telebot import types
from telebot.types import CallbackQuery

import logging

import db
import utils as ut
import keyboards as kb
from init import bot, log_error
from . import common as cf
from .base import start_contract
from enums import AddContractStep


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


# следующий шаг
@bot.callback_query_handler(func=lambda call: call.data.startswith('add_contract_next_step_check'))
def add_contract_next_step_check(call: CallbackQuery):
    _, step, answer_str = call.data.split(':')
    answer = bool(int(answer_str))

    if answer:
        data = ut.get_user_data(call.message.chat.id)
        if step == AddContractStep.END_DATE:
            bot.send_message(call.message.chat.id, "Введите дату завершения договора (дд.мм.гггг):")
            bot.register_next_step_handler(call.message, cf.process_contract_end_date, data['contractor_id'])

        elif step == AddContractStep.NUM:
            bot.send_message(call.message.chat.id, "Введите номер договора:")
            bot.register_next_step_handler(call.message, cf.process_contract_serial, data['contractor_id'])

        elif step == AddContractStep.SUM:
            bot.send_message(call.message.chat.id, "Введите сумму договора:")
            bot.register_next_step_handler(call.message, cf.process_contract_amount, data['contractor_id'])

        else:
            bot.send_message(call.message.chat.id, "❗️Что-то сломалось. Перезапустите бот \n\n/start")

    else:
        if step == AddContractStep.END_DATE:
            bot.send_message(
                call.message.chat.id,
                "Есть ли номер у вашего договора?",
                reply_markup=kb.get_check_next_step_contract_kb(AddContractStep.NUM.value)
            )

        elif step == AddContractStep.NUM:
            bot.send_message(
                call.message.chat.id,
                "Указана ли в договоре сумма?",
                reply_markup=kb.get_check_next_step_contract_kb(AddContractStep.SUM.value)
            )

        elif step == AddContractStep.SUM:
            data = ut.get_user_data(call.message.chat.id)
            bot.send_message(
                call.message.chat.id,
                "Сумма по договору указана с НДС?",
                reply_markup=kb.get_nds_kb(data['contractor_id'])
            )

        else:
            bot.send_message(call.message.chat.id, "❗️Что-то сломалось. Перезапустите бот \n\n/start")


# Обработчик для выбора контрагента
@bot.callback_query_handler(func=lambda call: call.data.startswith('contractor_'))
def handle_contract_contractor_selection(call: CallbackQuery):
    chat_id = call.message.chat.id
    contractor_id = call.data.split('_')[1]
    ord_id = ut.get_ord_id(chat_id, contractor_id)
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
    ord_id = ut.get_ord_id(chat_id, contractor_id)
    db.query_db(
        'UPDATE contracts SET vat_included = ? WHERE chat_id = ? AND contractor_id = ? AND ord_id = ?',
        (int(vat_included), chat_id, contractor_id, ord_id)
    )
    logging.debug(f"Updated VAT included for ord_id: {ord_id}")
    user_role = db.query_db('SELECT role FROM users WHERE chat_id = ?', (chat_id,), one=True)[0]
    cf.finalize_contract_data(call.message, user_role, contractor_id)
