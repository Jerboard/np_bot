from telebot import types

import logging

import db
import keyboards as kb
from init import bot
from utils import get_ord_id
from . import common as cf


def start_contract(message: types.Message):
    chat_id = message.chat.id
    selected_contractor = db.query_db(
        'SELECT contractor_id FROM selected_contractors WHERE chat_id = ?', (chat_id,),
        one=True
    )

    if selected_contractor:
        contractor_id = selected_contractor[0]
        ord_id = get_ord_id(chat_id, contractor_id)
        db.query_db(
            'INSERT OR IGNORE INTO contracts (chat_id, contractor_id, ord_id) VALUES (?, ?, ?)',
            (chat_id, contractor_id, ord_id)
        )
        logging.debug(f"Selected contractor: {contractor_id} for chat_id: {chat_id}")
        bot.send_message(chat_id, f"Выбранный ранее контрагент будет использован: № {contractor_id}")
        bot.send_message(chat_id, "Введите дату начала договора (дд.мм.гггг):")
        bot.register_next_step_handler(message, cf.process_contract_start_date, contractor_id)
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


# старт оплаты
def ask_amount(message: types.Message):
    chat_id = message.chat.id
    balance = db.query_db('SELECT balance FROM users WHERE chat_id = ?', (chat_id,), one=True)
    if balance:
        balance_amount = balance[0]
        logging.debug(f"Баланс пользователя {chat_id}: {balance_amount}")
        msg = bot.send_message(
            message.chat.id,
            f"На вашем балансе {balance_amount} рублей. \n\n "
            f"Введите сумму, на которую хотите пополнить баланс. \n\n "
            f"Стоимость маркировки одного креатива составляет 400 рублей."
        )
        bot.register_next_step_handler(msg, cf.process_amount)
    else:
        logging.error(f"Не удалось получить баланс для пользователя {chat_id}")
        bot.send_message(message.chat.id, "Ошибка: не удалось получить ваш баланс. Пожалуйста, попробуйте позже.")


def preloader_choose_platform(message: types.Message):
    chat_id = message.chat.id
    bot.send_message(
        chat_id,
        "Перейти к созданию рекламной площадки?",
        reply_markup=kb.get_preloader_choose_platform_kb()
    )


def preloader_advertiser_entity(message: types.Message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Перейти к созданию контрагента?", reply_markup=kb.get_preloader_advertiser_entity_kb())