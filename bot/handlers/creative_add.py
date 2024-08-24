from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command as CommandFilter, StateFilter
from aiogram.fsm.context import FSMContext
from datetime import datetime
from asyncio import sleep

import db
import keyboards as kb
from config import Config
from init import dp
import utils as ut
from .base import start_campaign_base, add_creative_start
from enums import CB, Command, UserState, JStatus, Role, AddContractStep


# Обработчик для команды /add_creative
@dp.message(CommandFilter(Command.ADD_CREATIVE.value))
async def add_creative(msg: Message, state: FSMContext):
    campaigns = await db.get_campaign(msg.from_user.id)
    if not campaigns:
        await msg.answer(
            "У вас нет активных рекламных кампаний. Пожалуйста, создайте кампанию перед добавлением креатива."
        )
        await start_campaign_base(msg, state)

    else:
        await msg.answer(
            text="Выберите рекламную кампанию для этого креатива:",
            reply_markup=kb.get_add_creative_kb(campaigns)
        )


# Обработчик выбора рекламной кампании CREATIVE_SELECT_CAMPAIGN
@dp.callback_query(lambda cb: cb.data.startswith(CB.CREATIVE_SELECT_CAMPAIGN.value))
async def choose_campaign_callback(cb: CallbackQuery, state: FSMContext):
    _, campaign_id = cb.data.split(':')
    await add_creative_start(msg=cb.message, campaign_id=campaign_id, state=state)


# Обработчик загрузки креатива
@dp.message(StateFilter(UserState.ADD_CREATIVE))
async def handle_creative_upload(msg: Message, state: FSMContext):
    if msg.content_type in ['text', 'photo', 'video', 'audio', 'document']:
        creative_content = save_creative(msg)
        creative_count = db.query_db('SELECT COUNT(*) FROM creatives WHERE chat_id = ? AND campaign_id = ?',
                                     (chat_id, campaign_id), one=True)
        if creative_count is None:
            creative_count = [0]

        ord_id_data = db.query_db(
            'SELECT ord_id FROM ad_campaigns WHERE campaign_id = ?',
            (campaign_id,),
            one=True
        )
        logging.debug(f"ord_id для кампании {campaign_id}: {ord_id_data}")

        if ord_id_data is None:
            logging.error(f"Не удалось найти ord_id для кампании с campaign_id: {campaign_id}")
            await msg.answer("Ошибка: Не удалось найти ord_id для указанной кампании.")
            return

        ord_id = get_creative_ord_id(ord_id_data[0], creative_count[0])
        db.query_db(
            'INSERT INTO creatives (chat_id, campaign_id, creative_id, content_type, content, ord_id, status) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (chat_id, campaign_id, str(uuid.uuid4()), msg.content_type, creative_content, ord_id, 'pending'))
        logging.debug(f"Inserted creative for chat_id: {chat_id}, campaign_id: {campaign_id}, ord_id: {ord_id}")

        await msg.answer(
            chat_id,
            "Креатив успешно добавлен. Добавить еще файл или текст для этого креатива?",
            reply_markup=kb.get_handle_creative_upload_kb(campaign_id)
        )
    else:
        await msg.answer("Ошибка. Пожалуйста, попробуйте еще раз и пришлите креатив.")
        add_creative_start(chat_id, campaign_id)


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
