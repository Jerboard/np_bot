from aiogram import types
from aiogram.types import CallbackQuery

import db
import utils as ut
import keyboards as kb
from init import dp
from . import common as cf
from .base import start_contract, preloader_choose_platform


#### Функция для выбора платформы ####
@dp.message(commands=['preloader_choose_platform'])
async def preloader_choose_platform_base(message: Message):
    preloader_choose_platform(message)


@dp.callback_query(lambda cb: cb.data == 'no_choose_platform')
async def no_choose_platform(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    await message.answer(
        chat_id,
        "Вы можете в любой момент продолжить добавление рекламной площадки нажав на соответствующий пункт в меню"
    )


@dp.callback_query(lambda cb: cb.data == 'choose_platform')
async def choose_platform(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    await message.answer("Выберите площадку:", reply_markup=kb.get_choose_platform_kb())


@dp.callback_query(
    lambda cb: cb.data in ['vk', 'instagram', 'youtube', 'telegram_channel', 'personal_telegram', 'other'])
async def collect_platform(cb: CallbackQuery):
    chat_id = cb.message.chat.id

    user_data = {'platform_name': cb.data}
    ut.save_user_data(chat_id=chat_id, data=user_data)

    # убрать глобальную переменную, использовать машину состояний
    # global platform_name

    if cb.data == 'vk':
        platform_name = 'ВКонтакте'
        await message.answer("Пришлите ссылку на аккаунт рекламораспространителя.")
        dp.register_next_step(
            cb.message,
            lambda message: cf.collect_advertiser_link(message, "https://vk.com/")
        )
    elif cb.data == 'instagram':
        platform_name = 'Instagram'
        await message.answer("Пришлите ссылку на аккаунт рекламораспространителя.")
        dp.register_next_step(cb.message,
                              lambda message: cf.collect_advertiser_link(message, "https://instagram.com/"))
    elif cb.data == 'youtube':
        platform_name = 'YouTube'
        await message.answer("Пришлите ссылку на аккаунт рекламораспространителя.")
        dp.register_next_step(cb.message,
                              lambda message: cf.collect_advertiser_link(message, "https://youtube.com/"))
    elif cb.data == 'telegram_channel':
        platform_name = 'Telegram-канал'
        await message.answer("Пришлите ссылку на аккаунт рекламораспространителя.")
        dp.register_next_step(cb.message,
                              lambda message: cf.collect_advertiser_link(message, "https://t.me/"))
    elif cb.data == 'personal_telegram':
        platform_name = 'Личный профиль Telegram'
        await message.answer("Пришлите ссылку на аккаунт рекламораспространителя.")
        dp.register_next_step(cb.message,
                              lambda message: cf.collect_advertiser_link(message, "https://t.me/"))
    elif cb.data == 'other':
        platform_name = 'Другое'
        await message.answer("Пришлите ссылку на площадку рекламораспространителя.")
        dp.register_next_step(cb.message, cf.platform_url_collector)

    else:
        # добавил чтоб не было предупреждения
        platform_name = 'error'

    user_data = {'platform_name': platform_name}
    ut.save_user_data(chat_id=chat_id, data=user_data)


@dp.callback_query(
    lambda cb: cb.data in ['correct_platform', 'change_platform', 'delete_platform'])
async def handle_platform_verification(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    if cb.data == 'correct_platform':
        cf.request_average_views(chat_id)
    elif cb.data == 'change_platform':
        choose_platform(call)
    elif cb.data == 'delete_platform':
        cf.del_platform(call)


@dp.callback_query(lambda cb: cb.data.startswith('contractor1_'))
async def handle_contractor_selection(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    contractor_id = cb.data.split('_')[1]
    cf.finalize_platform_data(chat_id, contractor_id)


@dp.callback_query(lambda cb: cb.data in ['add_another_platform', 'continue_to_entity'])
async def handle_success_add_platform(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    role = db.query_db('SELECT role FROM users WHERE chat_id = ?', (chat_id,), one=True)[0]
    if cb.data == 'add_another_platform':
        choose_platform(call)
    elif cb.data == 'continue_to_entity':
        if role == 'advertiser':
            await message.answer("Теперь укажите информацию о договоре.")
            start_contract(cb.message)
        elif role == 'publisher':
            # перенёс preloader_advertiser_entity
            # preloader_advertiser_entity(cb.message)
            await message.answer("Перейти к созданию контрагента?",
                            reply_markup=kb.get_preloader_advertiser_entity_kb())
            # bot.send_message(chat_id, "Теперь укажите информацию о контрагенте.")
            # register_advertiser_entity(cb.message)
