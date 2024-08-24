from aiogram.types import Message, CallbackQuery

import logging

import db
import keyboards as kb
from init import dp
from utils import get_ord_id
from . import common as cf


async def start_contract(msg: Message):
    # тут выбирать последнего контрагента из сделок
    selected_contractor = False

    if selected_contractor:
        await msg.answer(f"Выбранный ранее контрагент будет использован: № {selected_contractor}")
        await msg.answer("Введите дату начала договора (дд.мм.гггг):")
        # dp.register_next_step(msg, cf.process_contract_start_date, contractor_id)
    else:
        contractors = await db.get_all_contractors(msg.from_user.id)
        await msg.answer("Контрагент не был выбран. Пожалуйста, выберите контрагента.")
        if contractors:
            await msg.answer("Выберите контрагента:", reply_markup=kb.get_select_distributor_kb(contractors))

        else:
            await msg.answer(
                text=f"❗️У вас нет контрагентов.\n\n"
                     f"Чтобы добавить контрагента воспользуйтесь командой /{Command.PRELOADER_ADVERTISER_ENTITY.value}")




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
    await message.answer("Перейти к созданию контрагента?", reply_markup=kb.get_preloader_advertiser_entity_kb())
