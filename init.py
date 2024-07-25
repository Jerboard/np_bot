from telebot.types import BotCommand
from datetime import datetime

import os
import re
import traceback
import logging
import telebot

from cachetools import cached, TTLCache
from flask import Flask, request, redirect

import config

app = Flask(__name__)
bot = telebot.TeleBot(config.TOKEN)


# Настройка логирования
logging.basicConfig(filename='bot_errors.log', level=logging.WARNING,
                    format='%(asctime)s %(levelname)s:%(message)s')

# Настройка кэша
cache = TTLCache(maxsize=100, ttl=300)


def set_main_menu():
    main_menu_commands = [
        BotCommand(command='/start', description='Главный экран'),
        BotCommand(command='/preloader_advertiser_entity', description='Рекламодатель'),
        BotCommand(command='/preloader_choose_platform', description='Выбор платформы'),
        BotCommand(command='/start_contract', description='Контракт'),
        BotCommand(command='/start_campaign', description='Начать компанию'),
        BotCommand(command='/creative', description='Креатив'),
        BotCommand(command='/add_creative', description='Добавить креатив'),
        BotCommand(command='/start_statistics', description='Статистика'),
        BotCommand(command='/pay', description='Оплата'),
    ]

    bot.set_my_commands(main_menu_commands)


# запись ошибок
def log_error(message, with_traceback: bool = True):
    now = datetime.now()
    log_folder = now.strftime ('%m-%Y')
    log_path = os.path.join('logs', log_folder)

    if not os.path.exists(log_path):
        os.makedirs(log_path)

    log_file_path = os.path.join(log_path, f'{now.day}.log')
    logging.basicConfig (level=logging.WARNING, filename=log_file_path, encoding='utf-8')

    if with_traceback:
        ex_traceback = traceback.format_exc()
        tb = ''
        msg = ''
        start_row = '  File'
        tb_split = ex_traceback.split('\n')
        for row in tb_split:
            if row.startswith(start_row) and not re.search ('venv', row):
                tb += f'{row}\n'

            if not row.startswith(' '):
                msg += f'{row}\n'

        logging.warning(f'{now}\n{tb}\n\n{msg}\n---------------------------------\n')
        return msg
    else:
        logging.warning(f'{now}\n{message}\n\n---------------------------------\n')
