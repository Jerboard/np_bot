from telebot.types import CallbackQuery

import logging

import db
import keyboards as kb
import utils as ut
from init import bot, log_error
from . import common as cf
from .base import ask_amount


####  Добавление креативов ####

# Команда /creative для Telegram бота
# @bot.message_handler(commands=['creative'])
# def start_creative_process(message):
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
@bot.message_handler(commands=['add_creative'])
def add_creative(message):
    chat_id = message.chat.id
    campaigns = db.query_db('SELECT campaign_id, brand, service FROM ad_campaigns WHERE chat_id = ?', (chat_id,))
    logging.debug(f"Рекламные кампании для пользователя {chat_id}: {campaigns}")
    if not campaigns:
        bot.send_message(
            chat_id,
            "У вас нет активных рекламных кампаний. Пожалуйста, создайте кампанию перед добавлением креатива."
        )
        return

    bot.send_message(chat_id, "Выберите рекламную кампанию для этого креатива:", reply_markup=kb.get_add_creative_kb(campaigns))


# Обработчик выбора рекламной кампании
@bot.callback_query_handler(func=lambda call: call.data.startswith('choose_campaign_'))
def choose_campaign_callback(call: CallbackQuery):
    chat_id = call.message.chat.id
    campaign_id = call.data.split('_')[2]
    logging.debug(f"Выбранная рекламная кампания: {campaign_id}")
    cf.add_creative_start(chat_id, campaign_id)


# Обработчик кнопки "Добавить файл или текст"
@bot.callback_query_handler(func=lambda call: call.data.startswith('add_more_'))
def add_more_creative(call: CallbackQuery):
    campaign_id = call.data.split('_')[2]
    cf.add_creative_start(call.message.chat.id, campaign_id)


# создаёт ссылку на оплату
@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_yk'))
def pay_yk(call: CallbackQuery):
    _, campaign_id = call.data.split(':')
    # ищем карточки для быстрой оплаты
    sent = bot.send_message(call.message.chat.id, '⏳')
    save_cards = db.query_db(
        'SELECT DISTINCT card FROM payment_yk WHERE user_id = %s', (call.from_user.id,)
    )
    pay_id = ut.create_pay_link(campaign_id)
    bot.delete_message(chat_id=sent.chat.id, message_id=sent.message_id)
    bot.send_message(
        call.from_user.id,
        'Для получения маркировки необходимо осуществить оплату',
        reply_markup=kb.get_yk_pay_kb(pay_id, save_cards)
    )


# Обработчик кнопки "Продолжить"
@bot.callback_query_handler(func=lambda call: call.data.startswith('continue_creative_'))
def choose_campaign(call: CallbackQuery):
    _, pay_id = call.data.split(':')

    sent = bot.send_message(call.message.chat.id, '⏳')
    pay_data = ut.check_pay_yoo(pay_id)
    bot.delete_message(chat_id=sent.chat.id, message_id=sent.message_id)

    log_error(pay_data, wt=False)
    if pay_data:
        card_info, campaign_id = pay_data
        # сохраняем данные платежа
        db.query_db(
            'INSERT INTO payment_yk (user_id, pay_id, card) VALUES (%s, %s, %s)',
            (call.from_user.id, pay_id, card_info)
                    )
        chat_id = call.message.chat.id
        cf.finalize_creative(chat_id, campaign_id)

    else:
        bot.answer_callback_query(call.id, '❗️  Оплата не прошла нажмите оплатить и совершите платёж', show_alert=True)


# Добавление ссылки на креатив
@bot.callback_query_handler(func=lambda call: call.data.startswith('add_link_'))
def add_link(call: CallbackQuery):
    ord_id = call.data.split('_')[2]
    msg = bot.send_message(
        call.message.chat.id,
        "Опубликуйте ваш креатив и пришлите ссылку на него. Если вы публикуете один креатив на разных площадках - "
        "пришлите ссылку на каждую площадку.")
    bot.register_next_step_handler(msg, lambda message: cf.handle_creative_link(message, ord_id))


@bot.callback_query_handler(func=lambda call: call.data.startswith('link_done_'))
def link_done(call: CallbackQuery):
    chat_id = call.message.chat.id
    bot.send_message(
        chat_id,
        "Вы успешно добавили все ссылки на креатив. "
        "Подать отчетность по показам нужно будет в конце месяца или при завершении публикации. "
        "В конце месяца мы вам напомним о подаче отчетности.")
