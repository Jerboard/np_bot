from aiogram.types import Message
from aiogram.types import CallbackQuery
from aiogram.filters import CommandStart, StateFilter, Command as CommandFilter
from aiogram.fsm.context import FSMContext

import db
import data as dt
import keyboards as kb
import utils as ut
from config import Config
from init import dp, log_error, bot
from . import base
from utils import ord_api
from enums import CB, Command, UserState, Role


# 781602290203
# Обработчик команды /start
@dp.message(CommandStart())
async def start(msg: Message, state: FSMContext):
    check_referrer = msg.text.split(' ')
    ref_code = check_referrer[1] if len(check_referrer) == 2 else None

    # определяем реферала
    if ref_code:
        referrer = await db.get_user_info(ref_code=ref_code)
        referrer_id = referrer.user_id
    else:
        referrer_id = None

    await base.start_bot(msg=msg, state=state, referrer=referrer_id)


# Добавление контрагента начало
@dp.message(CommandFilter(Command.COUNTERAGENT.value))
async def preloader_advertiser_entity_command(msg: Message, state: FSMContext):
    user = await db.get_user_info(msg.from_user.id)
    if user and user.in_ord:
        await base.preloader_advertiser_entity(msg)
    else:
        await base.start_bot(msg, state, user=user)


# Обработчик для команды /start_campaign
@dp.message(CommandFilter(Command.CAMPAIGN.value))
async def start_campaign(msg: Message, state: FSMContext):
    await state.clear()

    user = await db.get_user_info(msg.from_user.id)
    if user and user.in_ord:
        await base.start_campaign_base(msg, state)
    else:
        await base.start_bot(msg, state, user=user)


# выбора платформы старт
@dp.message(CommandFilter(Command.PLATFORM.value))
async def preloader_choose_platform_base(msg: Message, state: FSMContext):
    await state.clear()

    user = await db.get_user_info(msg.from_user.id)
    if user and user.in_ord:
        await base.preloader_choose_platform(msg)
    else:
        await base.start_bot(msg, state, user=user)


# Обработчик для команды /start_contract
# перенёс функцию в base поменял название, чтоб не совпадали
@dp.message(CommandFilter(Command.CONTRACT.value))
async def start_contract_hnd(msg: Message, state: FSMContext):
    await state.clear()

    user = await db.get_user_info(msg.from_user.id)
    if user and user.in_ord:
        await base.start_contract(msg)
    else:
        await base.start_bot(msg, state, user=user)


# Обработчик для команды /add_creative
@dp.message(CommandFilter(Command.TOKEN.value))
async def add_creative(msg: Message, state: FSMContext):
    await state.clear()
    await state.set_state(UserState.ADD_CREATIVE)

    user = await db.get_user_info(msg.from_user.id)
    if not user or not user.in_ord:
        await base.start_bot(msg, state)

    campaigns = await db.get_user_campaigns(msg.from_user.id)
    if not campaigns:
        await msg.answer(
            "У вас нет активных рекламных кампаний. Пожалуйста, создайте кампанию перед добавлением креатива."
        )
        await base.start_campaign_base(msg, state)

    else:
        text = (f'Загрузите файл своего рекламного креатива или введите текст.\n'
                f'Вы можете загрузить несколько файлов для одного креатива. '
                f'Например, несколько идущих подряд видео в сторис.')
        await msg.answer(text)


# Обработка команды /start_statistics
@dp.message(CommandFilter(Command.STATS.value))
async def start_stats(msg: Message, state: FSMContext):
    await state.clear()

    active_creatives = await db.get_statistics(msg.from_user.id)

    # Получаем первый доступный campaign_id для пользователя
    if active_creatives:
        await state.set_state(UserState.SEND_STATISTIC)
        await state.update_data(data={'page': 0, 'active_creatives': active_creatives, 'sending_list': []})

        await msg.answer("<b>❕ Выберите креатив для подачи статистики</b>")
        await base.start_statistic(
            active_creatives=active_creatives,
            user_id=msg.from_user.id,
            sending_list=[],
            state=state
        )
    else:
        await msg.answer("❗️ У вас нет активных креативов.")


# Обработка команды /acts
@dp.message(CommandFilter(Command.ACTS.value))
async def start_stats(msg: Message, state: FSMContext):
    await state.clear()
    active_contracts = await db.get_all_user_contracts(msg.from_user.id)

    # Получаем первый доступный campaign_id для пользователя
    if active_contracts:
        await state.set_state(UserState.SEND_STATISTIC)
        await state.update_data(data={'page': 0, 'active_contracts': active_contracts})

        await msg.answer("<b>❕ Выберите контракт для подачи акта</b>")
        await base.start_acts(
            active_contracts=active_contracts,
            user_id=msg.from_user.id,
            state=state
        )
    else:
        await msg.answer("❗️ У вас нет активных контрактов.")


# Обработчик команды /help
@dp.message(CommandFilter(Command.HELP))
async def command_help(msg: Message, state: FSMContext):
    await state.clear()

    await msg.answer(
        'Напишите свой вопрос или пожелание по улучшению сервиса @id_np61',
        reply_markup=kb.get_help_button()
    )


# пишет что функция в разработке
@dp.callback_query(lambda cb: cb.data == 'in_dev')
async def in_dev(cb: CallbackQuery):
    dp.answer_callback_query(cb.id, '🛠 Функция в разработке 🛠', show_alert=True)


# пишет что функция в разработке
@dp.callback_query(lambda cb: cb.data == CB.CLOSE.value)
async def close(cb: CallbackQuery, state: FSMContext):
    await cb.message.delete()

    await state.clear()
    await cb.message.answer('В начало /start')
    # user = await db.get_user_info(cb.from_user.id)
    # await start_bot(cb.message, state, user=user)
