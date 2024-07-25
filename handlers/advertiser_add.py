from telebot import types
from telebot.types import CallbackQuery
from datetime import datetime
from moviepy.editor import VideoFileClip
from PIL import Image

import logging
import re
import os
import json
import uuid
import sqlite3
import requests
import threading

import db
import keyboards as kb
from init import bot
from . import common as cf
from .base import preloader_advertiser_entity
from utils import send_contractor_to_ord


#### Добавление контрагента ####
@bot.message_handler(commands=['preloader_advertiser_entity'])
def preloader_advertiser_entity_base(message: types.Message):
    preloader_advertiser_entity(message)


@bot.callback_query_handler(func=lambda call: call.data in ['no_advertiser'])
def handle_no_advertiser(call: CallbackQuery):
    chat_id = call.message.chat.id
    bot.send_message(chat_id,
                     "Вы можете в любой момент продолжить добавление контрагента нажав на соответствующий пункт в меню")


@bot.callback_query_handler(func=lambda call: call.data in ['register_advertiser_entity'])
def register_advertiser_entity(call: CallbackQuery):
    chat_id = call.message.chat.id
    bot.send_message(
        chat_id,
        "Укажите правовой статус вашего контрагента",
        reply_markup=kb.get_register_advertiser_entity_kb()
    )


# Обработчик для сбора информации о контрагентах
@bot.callback_query_handler(func=lambda call: call.data in ['ip_advertiser', 'ur_advertiser', 'fiz_advertiser'])
def collect_advertiser_info(call: CallbackQuery):
    chat_id = call.message.chat.id
    juridical_type_map = {
        'ip_advertiser': 'ip',
        'ur_advertiser': 'juridical',
        'fiz_advertiser': 'physical'
    }
    juridical_type = juridical_type_map[call.data]
    user_role = db.query_db('SELECT role FROM users WHERE chat_id = ?', (chat_id,), one=True)[0]

    # Определение роли контрагента
    contractor_role = 'advertiser' if user_role == 'publisher' else 'publisher'
    if juridical_type == 'juridical' and user_role == 'publisher':
        contractor_role = 'ors'

    contractor_id = db.query_db('SELECT COUNT(*) FROM contractors WHERE chat_id = ?', (chat_id,), one=True)[0] + 1
    ord_id = f"{chat_id}.{contractor_id}"

    db.query_db(
        'INSERT OR REPLACE INTO contractors (chat_id, contractor_id, role, juridical_type, ord_id) VALUES (?, ?, ?, ?, ?)',
        (chat_id, contractor_id, contractor_role, juridical_type, ord_id))

    if call.data == 'ip_advertiser':
        bot.send_message(chat_id,
                         "Укажите фамилию, имя и отчество вашего контрагента. \nНапример, Иванов Иван Иванович.")
        bot.register_next_step_handler(call.message, lambda m: cf.fio_i_collector_advertiser(m, contractor_id))
    elif call.data == 'ur_advertiser':
        bot.send_message(chat_id, "Укажите название организации вашего контрагента. \nНапример, ООО ЮКЦ Партнер.")
        bot.register_next_step_handler(call.message, lambda m: cf.title_collector_advertiser(m, contractor_id))
    elif call.data == 'fiz_advertiser':
        bot.send_message(chat_id,
                         "Укажите фамилию, имя и отчество вашего контрагента. \nНапример, Иванов Иван Иванович.")
        bot.register_next_step_handler(call.message, lambda m: cf.fio_collector_advertiser(m, contractor_id))



# Обработчик для кнопок после успешного добавления контрагента
@bot.callback_query_handler(func=lambda call: call.data in ['add_another_distributor', 'continue'])
def handle_success_add_distributor(call: CallbackQuery):
    chat_id = call.message.chat.id
    role = db.query_db('SELECT role FROM users WHERE chat_id = ?', (chat_id,), one=True)[0]
    if call.data == 'add_another_distributor':
        register_advertiser_entity(call)
    elif call.data == 'continue':
        if role == 'advertiser':
            # перенёс preloader_choose_platform
            # preloader_choose_platform(call.message)
            bot.send_message(
                chat_id,
                "Перейти к созданию рекламной площадки?",
                reply_markup=kb.get_preloader_choose_platform_kb()
            )
        elif role == 'publisher':
            bot.send_message(chat_id, "Теперь укажите информацию о договоре.")
            # перенёс start_contract
            # start_contract(call.message)
            selected_contractor = db.query_db(
                'SELECT contractor_id FROM selected_contractors WHERE chat_id = ?', (chat_id,),
                one=True
            )
