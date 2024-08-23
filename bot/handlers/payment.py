from aiogram import types

import db
import keyboards as kb
from init import dp
from .base import ask_amount


# Команда /pay для Telegram бота
@dp.message(commands=['pay'])
async def ask_amount_base(message: Message):
    pass
    # ask_amount(message)

