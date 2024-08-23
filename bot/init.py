from aiogram import Dispatcher, Bot
from aiogram.bot_command import BotCommand
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from yookassa import Configuration
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import create_async_engine
from datetime import datetime

import logging
import traceback
import os
import asyncio
import re
import redis

from config import Config


try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except:
    pass


loop = asyncio.get_event_loop()
dp = Dispatcher()
bot = Bot(Config.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

scheduler = AsyncIOScheduler()
ENGINE = create_async_engine(url=Config.db_url)

redis_db = redis.Redis(host=Config.redis_host, port=Config.redis_port, db=Config.redis_db)

Configuration.account_id = Config.yoo_account_id
Configuration.secret_key = Config.yoo_secret_key


async def set_main_menu():
    main_menu_commands = [
        BotCommand(command='/start', description='Главный экран'),
        BotCommand(command='/preloader_advertiser_entity', description='Контрагент'),
        BotCommand(command='/preloader_choose_platform', description='Выбор платформы'),
        BotCommand(command='/start_contract', description='Контракт'),
        BotCommand(command='/start_campaign', description='Начать компанию'),
        BotCommand(command='/add_creative', description='Добавить креатив'),
        BotCommand(command='/start_statistics', description='Статистика'),
        # BotCommand(command='/pay', description='Оплата'),
    ]

    await bot.set_my_commands(main_menu_commands)


# запись ошибок
def log_error(message, wt: bool = True):
    now = datetime.now()
    log_folder = now.strftime ('%m-%Y')
    log_path = os.path.join('logs', log_folder)

    if not os.path.exists(log_path):
        os.makedirs(log_path)

    log_file_path = os.path.join(log_path, f'{now.day}.log')
    logging.basicConfig (level=logging.WARNING, filename=log_file_path, encoding='utf-8')

    if wt:
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
