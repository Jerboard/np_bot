from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command as CommandFilter, StateFilter
from aiogram.fsm.context import FSMContext
from datetime import datetime
from asyncio import sleep

import db
import keyboards as kb
from config import Config
from init import dp, log_error
import utils as ut
from .base import start_campaign_base, add_creative_start, start_bot
from enums import CB, Command, UserState, JStatus, Role, Delimiter


# Обработчик для команды /add_creative
@dp.message(CommandFilter(Command.ADD_CREATIVE.value), StateFilter('*'))
async def add_creative(msg: Message, state: FSMContext):
    user = await db.get_user_info(msg.from_user.id)
    if not user:
        await start_bot(msg, state)

    campaigns = await db.get_user_campaigns(msg.from_user.id)
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
    # Попробовать с медиагруппой
    if msg.content_type in ['text', 'photo', 'video', 'audio', 'document']:
        data = await state.get_data()

        creative = {
            'content_type': msg.content_type,
            'file_id': ut.get_file_id(msg),
            'text': msg.text
        }

        creatives = data.get('creatives', [])
        creatives.append(creative)
        await state.update_data(data={'creatives': creatives})

        # creative_content = save_creative(msg)
        # creative_count = db.query_db('SELECT COUNT(*) FROM creatives WHERE chat_id = ? AND campaign_id = ?',
        #                              (chat_id, campaign_id), one=True)
        # if creative_count is None:
        #     creative_count = [0]

        # campaign_data = await db.get_campaign(data['campaign_id'])

        # if ord_id_data is None:
        #     await msg.answer("Ошибка: Не удалось найти ord_id для указанной кампании.")
        #     return

        # ord_id = ut.get_ord_id(msg.from_user.id, delimiter=Delimiter.C.value)

        await msg.answer(
            "Креатив успешно добавлен. Добавить еще файл или текст для этого креатива?",
            reply_markup=kb.get_handle_creative_upload_kb(campaign_id)
        )
    else:
        sent = await msg.answer("❌ Ошибка. Пожалуйста, попробуйте еще раз и пришлите креатив.")
        await sleep(3)
        await sent.delete()


# Обработчик кнопки "Добавить файл или текст"
@dp.callback_query(lambda cb: cb.data.startswith(CB.CREATIVE_ADD_CREATIVE.value))
async def add_more_creative(cb: CallbackQuery):
    await cb.answer('📲 Отправьте ещё контент для вашего креатива', show_alert=True)


# создаёт ссылку на оплату
@dp.callback_query(lambda cb: cb.data.startswith('pay_yk'))
async def pay_yk(cb: CallbackQuery, state: FSMContext):
    _, campaign_id = cb.data.split(':')
    # ищем карточки для быстрой оплаты
    sent = await cb.message.answer('⏳')
    save_cards = await db.get_user_save_cards(cb.from_user.id)

    pay_id = ut.create_pay_link(campaign_id)
    await sent.delete()
    await cb.message.answer(
        'Для получения маркировки необходимо осуществить оплату',
        reply_markup=kb.get_yk_pay_kb(pay_id, save_cards)
    )


# Обработчик кнопки "Продолжить"
@dp.callback_query(lambda cb: cb.data.startswith('continue_creative_'))
async def choose_campaign(cb: CallbackQuery, state: FSMContext):
    _, pay_id = cb.data.split(':')

    sent = await cb.message.answer('⏳')
    pay_data = ut.check_pay_yoo(pay_id)

    log_error(pay_data, wt=False)
    if pay_data:
        card_info, campaign_id = pay_data

        # сохраняем данные платежа
        await db.add_payment(
            user_id=cb.from_user.id,
            pay_id=pay_id,
            card=card_info,
            save_card=False
        )

        data = await state.get_data()
        creatives = data.get('creatives', [])

        campaign = await db.get_campaign(data['campaign_id'])
        contract = await db.get_contract(campaign.contract_id)
        user = await db.get_user_info(cb.from_user.id)

        contract_ord_id = contract.ord_id
        contractor_id_part = contract.contractor_id

        # contract_ord_id, contractor_id_part = contract

        # Использование правильного ord_id для контракта
        contract_external_id = contract_ord_id

        if user.role == Role.ADVERTISER:
            fio_or_title = user.name
            user_inn = user.inn
        else:
            contractor_info = await db.get_contractor(contract.contractor_id)

            fio_or_title = contractor_info.name
            user_inn = contractor_info.inn

        media_ids = []
        creative_data = []
        creative_text = ''
        for creative in creatives:
            # {'content_type': msg.content_type, 'file_id': ut.get_file_id(msg), 'text': msg.text}

            file_id = creative.get('file_id')
            if file_id:
                # тут медиа регистрируются в ОРД
                file_path = await ut.save_media(file_id=file_id, user_id=cb.from_user.id)
                media_id = await ut.register_media_file(file_path, campaign_id, campaign.service)
                media_ids.append(media_id)
            else:
                creative_text += f'{creative.text}\n\n'
                file_path = None
                media_id = None

            # await db.add_creative(
            #     user_id=cb.from_user.id,
            #     campaign_id=campaign.id,
            #     content_type=creative['content_type'],
            #     text=creative.get('text'),
            #     file_id=file_id,
            #     file_path=file_path
            # )
            # creative_data.append((creative[0], creative[2], creative))

        # for creative_id, _, _ in creative_data:
        # тут регистрируется весь весь креатив со списком медиа
            response = await ut.send_creative_to_ord(
                creative_id='',
                brand=campaign.brand,
                creative_name=f'{fio_or_title}',
                creative_text=creative_text.strip(),
                description=campaign.service,
                media_ids=media_id,
                contract_ord_id=contract.ord_id
            )
            log_error(f'response: {response}')
            if response is None or 'marker' not in response:
                await cb.message.answer("Ошибка при отправке креатива в ОРД.")
                # тут ещё возврат денег
                return

            marker = response['marker']
            await db.add_creative(
                user_id=cb.from_user.id,
                campaign_id=campaign.id,
                content_type=creative['content_type'],
                text=creative.get('text'),
                file_id=file_id,
                file_path=file_path,
                token=marker
            )

        await cb.message.answer(
            text=f"Креативы успешно промаркированы. Ваш токен - {marker}.\n"
                 f"Для копирования нажмите на текст ниже👇\n\n"
                 f"Реклама. {fio_or_title}. ИНН: {user_inn}. erid: {marker}`")
        # Сохранение данных в таблицу statistics
        # date_start_actual = datetime.now().strftime('%Y-%m-%d')
        # db.query_db('INSERT INTO statistics (chat_id, campaign_id, creative_id, date_start_actual) VALUES (?, ?, ?, ?)',
        #             (chat_id, campaign_id, creative_id, date_start_actual))

        # Запрос ссылки на креатив
        # ask_for_creative_link(chat_id, contract_external_id)

    else:
        await cb.answer('❗️  Оплата не прошла нажмите оплатить и совершите платёж', show_alert=True)


# Добавление ссылки на креатив
@dp.callback_query(lambda cb: cb.data.startswith('add_link_'))
async def add_link(cb: CallbackQuery):
    ord_id = cb.data.split('_')[2]
    msg = await cb.message.answer(
        "Опубликуйте ваш креатив и пришлите ссылку на него. Если вы публикуете один креатив на разных площадках - "
        "пришлите ссылку на каждую площадку.")
    # dp.register_next_step(msg, lambda message: cf.handle_creative_link(message, ord_id))


@dp.callback_query(lambda cb: cb.data.startswith('link_done_'))
async def link_done(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    await cb.message.answer(
        "Вы успешно добавили все ссылки на креатив. "
        "Подать отчетность по показам нужно будет в конце месяца или при завершении публикации. "
        "В конце месяца мы вам напомним о подаче отчетности.")
