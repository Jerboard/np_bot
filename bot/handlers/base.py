from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import logging

import db
import keyboards as kb
from init import dp
import utils as ut
from . import common as cf
from enums import UserState


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
    await message.answer(
        text="Перейти к созданию рекламной площадки?",
        reply_markup=kb.get_preloader_choose_platform_kb()
    )


async def preloader_advertiser_entity(message: Message):
    await message.answer("Перейти к созданию контрагента?", reply_markup=kb.get_preloader_advertiser_entity_kb())


# Функция для завершения процесса добавления данных платформы
async def finalize_platform_data(msg: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    ord_id = ut.get_ord_id(msg.from_user.id, delimiter='-p-')
    response = await ut.send_platform_to_ord(
        ord_id=ord_id,
        platform_name=data['platform_name'],
        platform_url=data['platform_url'],
        person_external_id=f"{msg.from_user.id}.{data['dist_id']}"

    )
    if response:
        await db.add_platform(
            user_id=msg.from_user.id,
            name=data['platform_name'],
            url=data['platform_url'],
            average_views=data['view'],
            ord_id=ord_id,
        )

        await msg.answer("Площадка успешно зарегистрирована в ОРД.")
        await msg.answer("Добавить новую площадку или продолжить?", reply_markup=kb.get_finalize_platform_data_kb())

    else:
        await msg.answer("Площадка добавлена, но сервер вернул неожиданный статус.")


async def start_campaign_base(msg: Message, state: FSMContext):
    await state.clear()
    await state.set_state(UserState.ADD_CAMPAIGN_BRAND)
    await msg.answer("Введите название бренда, который вы планируете рекламировать.\n\nУкажите бренд.")


# Начало процесса добавления креатива
async def add_creative_start(msg: Message, state: FSMContext, campaign_id: int):
    await state.set_state(UserState.ADD_CREATIVE)
    await state.update_data(data={'campaign_id': campaign_id})

    msg = await msg.answer(
        "Загрузите файл своего рекламного креатива или введите текст. "
        "Вы можете загрузить несколько файлов для одного креатива."
    )
    # dp.register_next_step(msg, lambda message: handle_creative_upload(message, campaign_id))