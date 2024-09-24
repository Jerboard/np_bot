from aiogram.types import Message
from aiogram.types import CallbackQuery
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext

import db
import data as dt
import keyboards as kb
import utils as ut
from config import Config
from init import dp, log_error, bot
from .base import preloader_choose_platform, start_bot, preloader_advertiser_entity
from utils import ord_api
from enums import CB, JStatus, UserState, Role


# 781602290203
# Обработчик команды /start
@dp.message(CommandStart())
async def start(msg: Message, state: FSMContext):
    await start_bot(msg, state)


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
    await cb.message.answer('❓❓❓ Тут нужно поставить универсальную заглушку. '
                            'Куда отправляем пользователя после отмены действия\n\n'
                            'Пример\n\n'
                            'В начало /start')
    # user = await db.get_user_info(cb.from_user.id)
    # await start_bot(cb.message, state, user=user)
