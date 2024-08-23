from aiogram import types
from aiogram.types import CallbackQuery

import logging

import db
import utils as ut
import keyboards as kb
from init import dp, log_error
from . import common as cf
from .base import start_contract
from enums import AddContractStep


### Добавление договоров ####

# Конфигурация логгирования
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


# Функция для получения ord_id
# async def get_ord_id(chat_id, contractor_id):
#     return f"{chat_id}.{contractor_id}"


# Обработчик для команды /start_contract
# перенёс функцию в base поменял название, чтоб не совпадали
@dp.message(commands=['start_contract'])
async def start_contract_hnd(message: Message):
    start_contract(message)


# следующий шаг
@dp.callback_query(lambda cb: cb.data.startswith('add_contract_next_step_check'))
async def add_contract_next_step_check(cb: CallbackQuery):
    _, step, answer_str = cb.data.split(':')
    answer = bool(int(answer_str))

    if answer:
        data = ut.get_user_data(cb.message.chat.id)
        if step == AddContractStep.END_DATE:
            await message.answer(cb.message.chat.id, "Введите дату завершения договора (дд.мм.гггг):")
            dp.register_next_step(cb.message, cf.process_contract_end_date, data['contractor_id'])

        elif step == AddContractStep.NUM:
            await message.answer(cb.message.chat.id, "Введите номер договора:")
            dp.register_next_step(cb.message, cf.process_contract_serial, data['contractor_id'])

        elif step == AddContractStep.SUM:
            await message.answer(cb.message.chat.id, "Введите сумму договора:")
            dp.register_next_step(cb.message, cf.process_contract_amount, data['contractor_id'])

        else:
            await message.answer(cb.message.chat.id, "❗️Что-то сломалось. Перезапустите бот \n\n/start")

    else:
        if step == AddContractStep.END_DATE:
            await message.answer(
                cb.message.chat.id,
                "Есть ли номер у вашего договора?",
                reply_markup=kb.get_check_next_step_contract_kb(AddContractStep.NUM.value)
            )

        elif step == AddContractStep.NUM:
            await message.answer(
                cb.message.chat.id,
                "Указана ли в договоре сумма?",
                reply_markup=kb.get_check_next_step_contract_kb(AddContractStep.SUM.value)
            )

        elif step == AddContractStep.SUM:
            data = ut.get_user_data(cb.message.chat.id)
            await message.answer(
                cb.message.chat.id,
                "Сумма по договору указана с НДС?",
                reply_markup=kb.get_nds_kb(data['contractor_id'])
            )

        else:
            await message.answer(cb.message.chat.id, "❗️Что-то сломалось. Перезапустите бот \n\n/start")


# Обработчик для выбора контрагента
@dp.callback_query(lambda cb: cb.data.startswith('contractor_'))
async def handle_contract_contractor_selection(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    contractor_id = cb.data.split('_')[1]
    ord_id = ut.get_ord_id(chat_id, contractor_id)
    db.query_db(
        'INSERT OR IGNORE INTO contracts (chat_id, contractor_id, ord_id) VALUES (?, ?, ?)',
        (chat_id, contractor_id, ord_id)
    )
    logging.debug(
        f"Inserted initial contract record for chat_id: {chat_id}, contractor_id: {contractor_id}, ord_id: {ord_id}")
    await message.answer(chat_id, "Введите дату начала договора (дд.мм.гггг):")
    dp.register_next_step(cb.message, cf.process_contract_start_date, contractor_id)


# Обработчик для выбора НДС
@dp.callback_query(lambda cb: cb.data.startswith("vat_yes_") or cb.data.startswith("vat_no_"))
async def handle_vat_selection(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    contractor_id = cb.data.split('_')[2]
    vat_included = cb.data.startswith("vat_yes")
    ord_id = ut.get_ord_id(chat_id, contractor_id)
    db.query_db(
        'UPDATE contracts SET vat_included = ? WHERE chat_id = ? AND contractor_id = ? AND ord_id = ?',
        (int(vat_included), chat_id, contractor_id, ord_id)
    )
    logging.debug(f"Updated VAT included for ord_id: {ord_id}")
    user_role = db.query_db('SELECT role FROM users WHERE chat_id = ?', (chat_id,), one=True)[0]
    cf.finalize_contract_data(cb.message, user_role, contractor_id)
