from telebot import types

import db
import keyboards as kb
from init import bot
from .base import ask_amount


# Команда /pay для Telegram бота
@bot.message_handler(commands=['pay'])
def ask_amount_base(message: types.Message):
    ask_amount(message)

