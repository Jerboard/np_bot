from aiogram.types import Message, CallbackQuery

import logging

import db
import keyboards as kb
from init import dp
from utils import get_ord_id
from . import common as cf


async def start_contract(message: Message):
    chat_id = message.chat.id
    selected_contractor = db.query_db(
        'SELECT contractor_id FROM selected_contractors WHERE chat_id = ?', (chat_id,),
        one=True
    )

    if selected_contractor:
        contractor_id = selected_contractor[0]
        ord_id = get_ord_id(chat_id, contractor_id)

        # поменял на постгре
        db.insert_contracts_data(chat_id, contractor_id, ord_id)
        # старый код
        # db.query_db(
        #     # 'INSERT OR IGNORE INTO contracts (chat_id, contractor_id, ord_id) VALUES (?, ?, ?)',
        #     'INSERT contracts (chat_id, contractor_id, ord_id) VALUES (?, ?, ?)',
        #     (chat_id, contractor_id, ord_id)
        # )
        logging.debug(f"Selected contractor: {contractor_id} for chat_id: {chat_id}")
        await message.answer(chat_id, f"Выбранный ранее контрагент будет использован: № {contractor_id}")
        await message.answer(chat_id, "Введите дату начала договора (дд.мм.гггг):")
        dp.register_next_step(message, cf.process_contract_start_date, contractor_id)
    else:
        await message.answer(chat_id, "Контрагент не был выбран. Пожалуйста, выберите контрагента.")
        contractors = db.query_db('SELECT contractor_id, fio, title FROM contractors WHERE chat_id = ?', (chat_id,))
        if contractors:
            kb = InlineKeyboardBuilder()
            for contractor in contractors:
                contractor_name = contractor[2] if contractor[2] else contractor[1]  # Используем title или fio
                contractor_button = kb.button(text=contractor_name,
                                                               callback_data=f"contractor_{contractor[0]}")
                contractor_button)
            await message.answer(chat_id, "Выберите контрагента:", reply_markup=markup)


# старт оплаты
def ask_amount(message: Message):
    chat_id = message.chat.id
    balance = db.query_db('SELECT balance FROM users WHERE chat_id = ?', (chat_id,), one=True)
    if balance:
        balance_amount = balance[0]
        logging.debug(f"Баланс пользователя {chat_id}: {balance_amount}")
        msg = await message.answer(
            message.chat.id,
            f"На вашем балансе {balance_amount} рублей. \n\n "
            f"Введите сумму, на которую хотите пополнить баланс. \n\n "
            f"Стоимость маркировки одного креатива составляет 400 рублей."
        )
        dp.register_next_step(msg, cf.process_amount)
    else:
        logging.error(f"Не удалось получить баланс для пользователя {chat_id}")
        await message.answer(message.chat.id, "Ошибка: не удалось получить ваш баланс. Пожалуйста, попробуйте позже.")


async def preloader_choose_platform(message: Message):
    chat_id = message.chat.id
    await message.answer(
        chat_id,
        "Перейти к созданию рекламной площадки?",
        reply_markup=kb.get_preloader_choose_platform_kb()
    )


async def preloader_advertiser_entity(message: Message):
    chat_id = message.chat.id
    await message.answer(chat_id, "Перейти к созданию контрагента?", reply_markup=kb.get_preloader_advertiser_entity_kb())
