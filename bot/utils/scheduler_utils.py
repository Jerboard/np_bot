from aiogram.types import Message
from aiogram.enums.content_type import ContentType
from aiogram.fsm.context import FSMContext
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
    scheduler.add_job()


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


# отправляет статистику
async def send_statistic():
    now = datetime.now()

    if now.day != 3:
        statistics = await db.get_statistics()
        items = []
        for statistic in statistics:
            items = []
            creative = await db.get_creative(creative_id=statistic.creative_id)
            platform = await db.get_platform(platform_id=statistic.platform_id)
            # campaign = await db.get_campaign(campaign_id=creative.campaign_id)
            # contract = await db.get_contract(contract_id=campaign.contract_id)

            items.append(
                {
                    "creative_external_id": creative.ord_id,
                    "pad_external_id": platform.ord_id,
                    "shows_count": statistic.views,
                    "date_start_actual": creative.created_at.strftime(Config.ord_date_form),
                    "date_end_actual": now.strftime(Config.ord_date_form)
                }
            )

            print(datetime.now() - now)

            # await db.update_statistic(statistic_id=statistic.id, in_ord=True)

            statistic_ord_id = await send_statistic_to_ord(
                creative_ord_id=creative.ord_id,
                platform_ord_id=platform.ord_id,
                views=str(statistic.views),
                creative_date=creative.created_at
            )

