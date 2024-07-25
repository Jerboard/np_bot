from telebot import types
from telebot.types import CallbackQuery

import logging
import requests

import db
import keyboards as kb
from init import bot
from . import common as cf
from .base import start_contract, preloader_choose_platform


#### Функция для выбора платформы ####
@bot.message_handler(commands=['preloader_choose_platform'])
def preloader_choose_platform_base(message: types.Message):
    preloader_choose_platform(message)


@bot.callback_query_handler(func=lambda call: call.data == 'no_choose_platform')
def no_choose_platform(call: CallbackQuery):
    chat_id = call.message.chat.id
    bot.send_message(
        chat_id,
        "Вы можете в любой момент продолжить добавление рекламной площадки нажав на соответствующий пункт в меню"
    )


@bot.callback_query_handler(func=lambda call: call.data == 'choose_platform')
def choose_platform(call: CallbackQuery):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Выберите площадку:", reply_markup=kb.get_choose_platform_kb())


@bot.callback_query_handler(
    func=lambda call: call.data in ['vk', 'instagram', 'youtube', 'telegram_channel', 'personal_telegram', 'other'])
def collect_platform(call: CallbackQuery):
    chat_id = call.message.chat.id

    # убрать глобальную переменную, использовать машину состояний
    global platform_name
    if call.data == 'vk':
        platform_name = 'ВКонтакте'
        bot.send_message(chat_id, "Пришлите ссылку на аккаунт рекламораспространителя.")
        bot.register_next_step_handler(call.message,
                                       lambda message: cf.collect_advertiser_link(message, "https://vk.com/"))
    elif call.data == 'instagram':
        platform_name = 'Instagram'
        bot.send_message(chat_id, "Пришлите ссылку на аккаунт рекламораспространителя.")
        bot.register_next_step_handler(call.message,
                                       lambda message: cf.collect_advertiser_link(message, "https://instagram.com/"))
    elif call.data == 'youtube':
        platform_name = 'YouTube'
        bot.send_message(chat_id, "Пришлите ссылку на аккаунт рекламораспространителя.")
        bot.register_next_step_handler(call.message,
                                       lambda message: cf.collect_advertiser_link(message, "https://youtube.com/"))
    elif call.data == 'telegram_channel':
        platform_name = 'Telegram-канал'
        bot.send_message(chat_id, "Пришлите ссылку на аккаунт рекламораспространителя.")
        bot.register_next_step_handler(call.message,
                                       lambda message: cf.collect_advertiser_link(message, "https://t.me/"))
    elif call.data == 'personal_telegram':
        platform_name = 'Личный профиль Telegram'
        bot.send_message(chat_id, "Пришлите ссылку на аккаунт рекламораспространителя.")
        bot.register_next_step_handler(call.message,
                                       lambda message: cf.collect_advertiser_link(message, "https://t.me/"))
    elif call.data == 'other':
        platform_name = 'Другое'
        bot.send_message(chat_id, "Пришлите ссылку на площадку рекламораспространителя.")
        bot.register_next_step_handler(call.message, cf.platform_url_collector)


@bot.callback_query_handler(
    func=lambda call: call.data in ['correct_platform', 'change_platform', 'delete_platform'])
def handle_platform_verification(call: CallbackQuery):
    chat_id = call.message.chat.id
    if call.data == 'correct_platform':
        cf.request_average_views(chat_id)
    elif call.data == 'change_platform':
        choose_platform(call)
    elif call.data == 'delete_platform':
        cf.del_platform(call)


@bot.callback_query_handler(func=lambda call: call.data.startswith('contractor1_'))
def handle_contractor_selection(call: CallbackQuery):
    chat_id = call.message.chat.id
    contractor_id = call.data.split('_')[1]
    cf.finalize_platform_data(chat_id, contractor_id)


@bot.callback_query_handler(func=lambda call: call.data in ['add_another_platform', 'continue_to_entity'])
def handle_success_add_platform(call: CallbackQuery):
    chat_id = call.message.chat.id
    role = db.query_db('SELECT role FROM users WHERE chat_id = ?', (chat_id,), one=True)[0]
    if call.data == 'add_another_platform':
        choose_platform(call)
    elif call.data == 'continue_to_entity':
        if role == 'advertiser':
            bot.send_message(chat_id, "Теперь укажите информацию о договоре.")
            start_contract(call.message)
        elif role == 'publisher':
            # перенёс preloader_advertiser_entity
            # preloader_advertiser_entity(call.message)
            bot.send_message(chat_id, "Перейти к созданию контрагента?",
                             reply_markup=kb.get_preloader_advertiser_entity_kb())
            # bot.send_message(chat_id, "Теперь укажите информацию о контрагенте.")
            # register_advertiser_entity(call.message)
