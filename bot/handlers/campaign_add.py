from aiogram.types import CallbackQuery

import logging

import db
import keyboards as kb
from init import dp
from . import common as cf


####  Добавление рекламной кампании ####
# Конфигурация логгирования
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


# Обработчик для команды /start_campaign
@dp.message(commands=['start_campaign'])
async def start_campaign(message):
    chat_id = message.chat.id
    await message.answer("Введите название бренда, который вы планируете рекламировать.")
    cf.ask_for_brand(chat_id)


@dp.callback_query(
    lambda cb: cb.data.startswith('add_another_link') or cb.data.startswith('continue_campaign'))
async def handle_additional_link(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    campaign_id = cb.data.split(':')[1]
    if cb.data.startswith('add_another_link'):
        cf.ask_for_target_link(chat_id, campaign_id)
    elif cb.data.startswith('continue_campaign'):
        confirm_ad_campaign(chat_id, campaign_id)


# Подтверждение рекламной кампании
async def confirm_ad_campaign(chat_id, campaign_id):
    ad_campaign = db.query_db(
        'SELECT brand, service FROM ad_campaigns WHERE campaign_id = ?', (campaign_id,),
        one=True
    )
    target_links = db.query_db('SELECT link FROM target_links WHERE campaign_id = ?', (campaign_id,))
    links_str = "\n".join([f"Целевая ссылка {i + 1}: {link[0]}" for i, link in enumerate(target_links)])
    await message.answer(
        chat_id,
        f"Проверьте, правильно ли указана информация о рекламной кампании:\n"
        f"Бренд: {ad_campaign[0]}\n"
        f"Услуга: {ad_campaign[1]}\n{links_str}",
        reply_markup=kb.get_confirm_ad_campaign_kb(campaign_id)
    )


# Обработка выбора подтверждения, изменения или удаления рекламной кампании
@dp.callback_query(lambda cb: cb.data.startswith("confirm_ad_campaign") or cb.data.startswith(
    "change_ad_campaign") or cb.data.startswith("delete_ad_campaign"))
async def handle_ad_campaign_callback(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    campaign_id = cb.data.split(':')[1]
    if cb.data.startswith("confirm_ad_campaign"):
        await message.answer(
            chat_id,
            f"Рекламная кампания с брендом "
            f"{db.query_db('SELECT brand FROM ad_campaigns WHERE campaign_id = ?', (campaign_id,), one=True)[0]} "
            f"успешно создана!"
        )
        cf.add_creative_start(chat_id, campaign_id)
    elif cb.data.startswith("change_ad_campaign"):
        cf.ask_for_brand(chat_id)
    elif cb.data.startswith("delete_ad_campaign"):
        db.query_db('DELETE FROM ad_campaigns WHERE campaign_id = ?', (campaign_id,))
        db.query_db('DELETE FROM target_links WHERE campaign_id = ?', (campaign_id,))
        dp.answer_callback_query(cb.id, "Рекламная кампания удалена")
        logging.debug(f"Deleted campaign_id: {campaign_id} and associated links")
