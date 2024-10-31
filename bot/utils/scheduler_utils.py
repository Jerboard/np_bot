from aiogram.types import Message
from aiogram.enums.content_type import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from random import randint

import typing as t
import os

import db
import keyboards as kb
from init import bot, log_error, scheduler
from config import Config
from .ord_api import send_statistic_to_ord
from .media_utils import compress_video
from handlers import base
from enums import UserState, Delimiter, MediaType


# запуск основных планировщиков
async def start_schedulers():
    # запуск напоминалок о стате
    scheduler.add_job(request_monthly_statistic, trigger='cron', day='last', hour=11)
    scheduler.add_job(request_monthly_statistic, trigger='cron', day=1, hour=11)
    scheduler.add_job(request_monthly_statistic, trigger='cron', day=2, hour=11)

    # месячный отчёт по стате
    scheduler.add_job(send_monthly_statistic, trigger='cron', day=3, hour=4)

    scheduler.start()


# проверяем отправил ли пользователь ссылку на пост
async def check_post_link(creative_id: int, user_id: int):
    urls = await db.get_statistics(creative_id=creative_id)
    if not urls:
        await bot.send_message(
            chat_id=user_id,
            text="Вы получили токен, но не прислали ссылку на ваш креатив.\n"
                 "Пришлите, пожалуйста, ссылку. Это нужно для подачи статистики в ОРД.",
            reply_markup=kb.get_end_creative_kb(creative_id)
        )


# запрашивает неотправленную стату в конце месяца
async def request_monthly_statistic() -> None:
    statistics = await db.get_creative_full_data(for_monthly_report=True)
    # statistics = await db.get_creative_full_data(user_id_statistic=524275902, for_monthly_report=True)
    users = set([statistic.user_id for statistic in statistics])

    for user_id in users:
        active_creatives = [statistic for statistic in statistics if statistic.user_id == user_id]

        await bot.send_message(
            chat_id=user_id,
            text=f"<b>❗️ Сегодня завершается отчетный период и вам необходимо подать "
                 f"статистику по {len(active_creatives)} креативам. </b>",
            reply_markup=kb.get_send_monthly_statistic_kb(user_id)
        )


# отправляет статистику по нулевым креативам
async def send_monthly_statistic() -> None:
    statistics = await db.get_creative_full_data(for_monthly_report=True)

    for statistic in statistics:
        try:
            platform = await db.get_platform(platform_id=statistic.platform_id)

            statistic_ord_id = await send_statistic_to_ord(
                creative_ord_id=statistic.creative_ord_id,
                platform_ord_id=platform.ord_id,
                views=platform.average_views,
                creative_date=statistic.created_at
            )

            if statistic_ord_id:
                await db.update_statistic(
                    statistic_id=statistic.creative_id,
                    views=platform.average_views,
                    ord_id=statistic_ord_id
                )
        except Exception as ex:
            log_error(ex)
