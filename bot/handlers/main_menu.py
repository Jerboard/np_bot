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
from .base import preloader_choose_platform, start_bot, preloader_advertiser_entity
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

    await start_bot(msg=msg, state=state, referrer=referrer_id)


# Обработчик команды /help
@dp.message(CommandFilter(Command.HELP))
async def start(msg: Message, state: FSMContext):
    await msg.answer(
        'Напишите свой вопрос или пожелание по улучшению сервиса @id_np61',
        reply_markup=kb.get_help_button()
    )


# Обработчик команды /help
@dp.message(CommandFilter(Command.ACTS))
async def start(msg: Message, state: FSMContext):
    pass


# универсальный ответ на кнопку "нет"
@dp.callback_query(lambda cb: cb.data == 'in_dev')
async def in_dev(cb: CallbackQuery):
    dp.answer_callback_query(cb.id, '🛠 Функция в разработке 🛠', show_alert=True)


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
