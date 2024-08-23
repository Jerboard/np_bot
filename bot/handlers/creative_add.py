from aiogram.types import CallbackQuery

import logging

import db
import keyboards as kb
import utils as ut
from init import dp, log_error
from . import common as cf
from .base import ask_amount


####  Добавление креативов ####

# Команда /creative для Telegram бота
# @bot.message(commands=['creative'])
# async def start_creative_process(message):
#     chat_id = message.chat.id
#
#     # сменил запрос на query_db
#     # conn = sqlite3.connect('bot_database2.db')
#     # cursor = conn.cursor()
#     # cursor.execute('SELECT balance FROM users WHERE chat_id = ?', (chat_id,))
#     # result = cursor.fetchone()
#     result = db.query_db('SELECT balance FROM users WHERE chat_id = ?', (chat_id,), one=True)
#
#     if result is None or result[0] < 400:
#         bot.send_message(chat_id, "Недостаточно средств на балансе. Пожалуйста, пополните баланс.")
#         ask_amount(message)
#     else:
#         balance = result[0]
#
#         # сменил запрос на query_db
#         # cursor.execute('UPDATE users SET balance = ? WHERE chat_id = ?', (balance - 400, chat_id))
#         # conn.commit()
#         # conn.close()
#         db.query_db('UPDATE users SET balance = ? WHERE chat_id = ?', (balance - 400, chat_id))
#
#         # Продолжение процесса добавления креатива
#         add_creative(message)


# Обработчик для команды /add_creative
@dp.message(commands=['add_creative'])
async def add_creative(message):
    chat_id = message.chat.id
    campaigns = db.query_db('SELECT campaign_id, brand, service FROM ad_campaigns WHERE chat_id = ?', (chat_id,))
    logging.debug(f"Рекламные кампании для пользователя {chat_id}: {campaigns}")
    if not campaigns:
        await message.answer(
            chat_id,
            "У вас нет активных рекламных кампаний. Пожалуйста, создайте кампанию перед добавлением креатива."
        )
        return

    await message.answer(chat_id, "Выберите рекламную кампанию для этого креатива:", reply_markup=kb.get_add_creative_kb(campaigns))


# Обработчик выбора рекламной кампании
@dp.callback_query(lambda cb: cb.data.startswith('choose_campaign_'))
async def choose_campaign_callback(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    campaign_id = cb.data.split('_')[2]
    logging.debug(f"Выбранная рекламная кампания: {campaign_id}")
    cf.add_creative_start(chat_id, campaign_id)


# Обработчик кнопки "Добавить файл или текст"
@dp.callback_query(lambda cb: cb.data.startswith('add_more_'))
async def add_more_creative(cb: CallbackQuery):
    campaign_id = cb.data.split('_')[2]
    cf.add_creative_start(cb.message.chat.id, campaign_id)


# создаёт ссылку на оплату
@dp.callback_query(lambda cb: cb.data.startswith('pay_yk'))
async def pay_yk(cb: CallbackQuery):
    _, campaign_id = cb.data.split(':')
    # ищем карточки для быстрой оплаты
    sent = await message.answer(cb.message.chat.id, '⏳')
    save_cards = db.query_db(
        'SELECT DISTINCT card FROM payment_yk WHERE user_id = %s', (cb.from_user.id,)
    )
    pay_id = ut.create_pay_link(campaign_id)
    dp.delete_message(chat_id=sent.chat.id, message_id=sent.message_id)
    await message.answer(
        cb.from_user.id,
        'Для получения маркировки необходимо осуществить оплату',
        reply_markup=kb.get_yk_pay_kb(pay_id, save_cards)
    )


# Обработчик кнопки "Продолжить"
@dp.callback_query(lambda cb: cb.data.startswith('continue_creative_'))
async def choose_campaign(cb: CallbackQuery):
    _, pay_id = cb.data.split(':')

    sent = await message.answer(cb.message.chat.id, '⏳')
    pay_data = ut.check_pay_yoo(pay_id)
    dp.delete_message(chat_id=sent.chat.id, message_id=sent.message_id)

    log_error(pay_data, wt=False)
    if pay_data:
        card_info, campaign_id = pay_data
        # сохраняем данные платежа
        db.query_db(
            'INSERT INTO payment_yk (user_id, pay_id, card) VALUES (%s, %s, %s)',
            (cb.from_user.id, pay_id, card_info)
                    )
        chat_id = cb.message.chat.id
        cf.finalize_creative(chat_id, campaign_id)

    else:
        dp.answer_callback_query(cb.id, '❗️  Оплата не прошла нажмите оплатить и совершите платёж', show_alert=True)


# Добавление ссылки на креатив
@dp.callback_query(lambda cb: cb.data.startswith('add_link_'))
async def add_link(cb: CallbackQuery):
    ord_id = cb.data.split('_')[2]
    msg = await message.answer(
        cb.message.chat.id,
        "Опубликуйте ваш креатив и пришлите ссылку на него. Если вы публикуете один креатив на разных площадках - "
        "пришлите ссылку на каждую площадку.")
    dp.register_next_step(msg, lambda message: cf.handle_creative_link(message, ord_id))


@dp.callback_query(lambda cb: cb.data.startswith('link_done_'))
async def link_done(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    await message.answer(
        chat_id,
        "Вы успешно добавили все ссылки на креатив. "
        "Подать отчетность по показам нужно будет в конце месяца или при завершении публикации. "
        "В конце месяца мы вам напомним о подаче отчетности.")
