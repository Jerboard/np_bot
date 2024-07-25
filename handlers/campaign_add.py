from telebot import types
from telebot.types import CallbackQuery

import logging
import db
import keyboards as kb
from init import bot
from utils import get_ord_id


####  Добавление рекламной кампании ####
# Конфигурация логгирования
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


# Обработчик для команды /start_campaign
@bot.message_handler(commands=['start_campaign'])
def start_campaign(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Введите название бренда, который вы планируете рекламировать.")
    ask_for_brand(chat_id)


@bot.callback_query_handler(
    func=lambda call: call.data.startswith('add_another_link') or call.data.startswith('continue_campaign'))
def handle_additional_link(call: CallbackQuery):
    chat_id = call.message.chat.id
    campaign_id = call.data.split(':')[1]
    if call.data.startswith('add_another_link'):
        ask_for_target_link(chat_id, campaign_id)
    elif call.data.startswith('continue_campaign'):
        confirm_ad_campaign(chat_id, campaign_id)


# Подтверждение рекламной кампании
def confirm_ad_campaign(chat_id, campaign_id):
    ad_campaign = db.query_db(
        'SELECT brand, service FROM ad_campaigns WHERE campaign_id = ?', (campaign_id,),
        one=True
    )
    target_links = db.query_db('SELECT link FROM target_links WHERE campaign_id = ?', (campaign_id,))
    links_str = "\n".join([f"Целевая ссылка {i + 1}: {link[0]}" for i, link in enumerate(target_links)])
    bot.send_message(
        chat_id,
        f"Проверьте, правильно ли указана информация о рекламной кампании:\n"
        f"Бренд: {ad_campaign[0]}\n"
        f"Услуга: {ad_campaign[1]}\n{links_str}",
        reply_markup=kb.get_confirm_ad_campaign_kb(campaign_id)
    )


# Обработка выбора подтверждения, изменения или удаления рекламной кампании
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_ad_campaign") or call.data.startswith(
    "change_ad_campaign") or call.data.startswith("delete_ad_campaign"))
def handle_ad_campaign_callback(call: CallbackQuery):
    chat_id = call.message.chat.id
    campaign_id = call.data.split(':')[1]
    if call.data.startswith("confirm_ad_campaign"):
        bot.send_message(chat_id,
                         f"Рекламная кампания с брендом {db.query_db('SELECT brand FROM ad_campaigns WHERE campaign_id = ?', (campaign_id,), one=True)[0]} успешно создана!")
        add_creative_start(chat_id, campaign_id)
    elif call.data.startswith("change_ad_campaign"):
        ask_for_brand(chat_id)
    elif call.data.startswith("delete_ad_campaign"):
        db.query_db('DELETE FROM ad_campaigns WHERE campaign_id = ?', (campaign_id,))
        db.query_db('DELETE FROM target_links WHERE campaign_id = ?', (campaign_id,))
        bot.answer_callback_query(call.id, "Рекламная кампания удалена")
        logging.debug(f"Deleted campaign_id: {campaign_id} and associated links")