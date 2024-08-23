from aiogram import types
from aiogram.types import CallbackQuery

import db
import keyboards as kb
from init import dp
from . import common as cf
from .base import preloader_advertiser_entity


#### Добавление контрагента ####
@dp.message(commands=['preloader_advertiser_entity'])
async def preloader_advertiser_entity_base(message: Message):
    preloader_advertiser_entity(message)


@dp.callback_query(lambda cb: cb.data in ['no_advertiser'])
async def handle_no_advertiser(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    await message.answer(chat_id,
                     "Вы можете в любой момент продолжить добавление контрагента нажав на соответствующий пункт в меню")


@dp.callback_query(lambda cb: cb.data in ['register_advertiser_entity'])
async def register_advertiser_entity(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    await message.answer(
        chat_id,
        "Укажите правовой статус вашего контрагента",
        reply_markup=kb.get_register_advertiser_entity_kb()
    )


# Обработчик для сбора информации о контрагентах
@dp.callback_query(lambda cb: cb.data in ['ip_advertiser', 'ur_advertiser', 'fiz_advertiser'])
async def collect_advertiser_info(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    juridical_type_map = {
        'ip_advertiser': 'ip',
        'ur_advertiser': 'juridical',
        'fiz_advertiser': 'physical'
    }
    juridical_type = juridical_type_map[cb.data]
    user_role = db.query_db('SELECT role FROM users WHERE chat_id = ?', (chat_id,), one=True)[0]

    # Определение роли контрагента
    contractor_role = 'advertiser' if user_role == 'publisher' else 'publisher'
    if juridical_type == 'juridical' and user_role == 'publisher':
        contractor_role = 'ors'

    contractor_id = db.query_db('SELECT COUNT(*) FROM contractors WHERE chat_id = ?', (chat_id,), one=True)[0] + 1
    ord_id = f"{chat_id}.{contractor_id}"

    # сменил запрос под постгрес
    db.insert_contractors_data(chat_id, contractor_id, contractor_role, juridical_type, ord_id)

    #  старый запрос
    # db.query_db('INSERT OR REPLACE INTO contractors (chat_id, contractor_id, role, juridical_type, ord_id) VALUES (?, ?, ?, ?, ?)',
    #             (chat_id, contractor_id, contractor_role, juridical_type, ord_id))

    if cb.data == 'ip_advertiser':
        await message.answer(chat_id,
                         "Укажите фамилию, имя и отчество вашего контрагента. \nНапример, Иванов Иван Иванович.")
        dp.register_next_step(cb.message, lambda m: cf.fio_i_collector_advertiser(m, contractor_id))
    elif cb.data == 'ur_advertiser':
        await message.answer(chat_id, "Укажите название организации вашего контрагента. \nНапример, ООО ЮКЦ Партнер.")
        dp.register_next_step(cb.message, lambda m: cf.title_collector_advertiser(m, contractor_id))
    elif cb.data == 'fiz_advertiser':
        await message.answer(chat_id,
                         "Укажите фамилию, имя и отчество вашего контрагента. \nНапример, Иванов Иван Иванович.")
        dp.register_next_step(cb.message, lambda m: cf.fio_collector_advertiser(m, contractor_id))


# Обработчик для кнопок после успешного добавления контрагента
@dp.callback_query(lambda cb: cb.data in ['add_another_distributor', 'continue'])
async def handle_success_add_distributor(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    role = db.query_db('SELECT role FROM users WHERE chat_id = ?', (chat_id,), one=True)[0]
    if cb.data == 'add_another_distributor':
        register_advertiser_entity(call)
    elif cb.data == 'continue':
        if role == 'advertiser':
            # перенёс preloader_choose_platform
            # preloader_choose_platform(cb.message)
            await message.answer(
                chat_id,
                "Перейти к созданию рекламной площадки?",
                reply_markup=kb.get_preloader_choose_platform_kb()
            )
        elif role == 'publisher':
            await message.answer(chat_id, "Теперь укажите информацию о договоре.")
            # перенёс start_contract
            # start_contract(cb.message)
            selected_contractor = db.query_db(
                'SELECT contractor_id FROM selected_contractors WHERE chat_id = ?', (chat_id,),
                one=True
            )
