from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command as CommandFilter, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.enums.message_entity_type import MessageEntityType
from datetime import datetime
from yookassa import Payment
from asyncio import sleep

import db
import keyboards as kb
from config import Config
from init import dp, log_error, bot
import utils as ut
from .base import start_campaign_base, register_creative, start_bot
from enums import CB, Command, UserState, Action, Role, Delimiter


# Обработчик для команды /add_creative
@dp.message(CommandFilter(Command.ADD_CREATIVE.value), StateFilter('*'))
async def add_creative(msg: Message, state: FSMContext):
    await state.set_state(UserState.ADD_CREATIVE)

    # creative_ord_id = ut.get_ord_id(msg.from_user.id, delimiter=Delimiter.CR.value)
    #
    # response = await ut.send_creative_to_ord(
    #     creative_id=creative_ord_id,
    #     brand='Тестовый бренд',
    #     creative_name=f'Тестовый бренд',
    #     creative_text=['Тут описания чё чего почём'],
    #     description='Да прост всякая фигня',
    #     media_ids=['524275902-m-4566922434', '524275902-m-6830202514', '524275902-m-4360940154'],
    #     contract_ord_id='524275902-c-1146478275'
    # )
    # log_error(f'response: {response}', wt=False)
    # erid = response.get('erid') if response else None

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
        text = (f'Загрузите файл своего рекламного креатива или введите текст.\n'
                f'Вы можете загрузить несколько файлов для одного креатива. '
                f'Например, несколько идущих подряд видео в сторис.')
        await msg.answer(text)


# Обработчик загрузки креатива
@dp.message(StateFilter(UserState.ADD_CREATIVE_LINK))
async def handle_creative_upload(msg: Message, state: FSMContext):
    if msg.entities and msg.entities[0].type == MessageEntityType.URL:
        data = await state.get_data()
        await db.update_creative(creative_id=data['creative_id'], link=msg.text)
        await msg.answer(
            text='Вы успешно добавили ссылку на ваш рекламный креатив\n\n'
                 'Добавьте ещё ссылки или нажмите "Готово"',
            reply_markup=kb.get_end_creative_kb(data['creative_id'], with_add=False))

    else:
        await msg.answer('❌ Некорректный формат ссылки')


# media_ord_id: 524275902-m-8688379168, 524275902-m-8258534790, 524275902-m-4984138183
# Обработчик загрузки креатива
@dp.message(StateFilter(UserState.ADD_CREATIVE))
@dp.message()
async def handle_creative_upload(msg: Message, state: FSMContext):
    # Попробовать с медиагруппой
    if msg.content_type in ['text', 'photo', 'video', 'audio', 'document']:
        if msg.video and msg.video.file_size >= 50000000:
            await msg.answer(f'❌ Слишком большое видео. Размер видео не должен быть больше 50 МВ ')
            return

        current_state = await state.get_state()
        if not current_state:
            campaigns = await db.get_user_campaigns(msg.from_user.id)
            if not campaigns:
                await msg.answer(
                    "❌ У вас нет активных рекламных кампаний. Пожалуйста, создайте кампанию перед добавлением креатива."
                )
                await state.clear()
                await start_campaign_base(msg=msg, state=state)
                return

            await state.set_state(UserState.ADD_CREATIVE)
            await state.update_data(data={'campaigns': campaigns})

        data = await state.get_data()

        creative = {
            'content_type': msg.content_type,
            'file_id': ut.get_file_id(msg),
            'video_name': msg.video.file_name if msg.video else None
        }

        # сохраняем текст, если есть
        creative_text = msg.text or msg.caption
        if creative_text:
            tests = data.get('text', [])
            tests.append(creative_text)
            await state.update_data(data={'text': tests})

        creatives = data.get('creatives', [])
        creatives.append(creative)
        await state.update_data(data={'creatives': creatives})

        message_id = data.get('message_id')
        if message_id:
            try:
                await bot.delete_message(chat_id=msg.chat.id, message_id=message_id)
            except:
                pass

        sent = await msg.answer(
            '✅ Креатив успешно добавлен\n\n'
            'Чтобы добавить еще файл или текст для этого креатива просто отправьте его сообщением или '
            'нажмите "Продолжить", чтобы получить токен.',
            reply_markup=kb.get_select_campaigns_kb()
        )
        await state.update_data(data={'message_id': sent.message_id})
    else:
        sent = await msg.answer("❌ Ошибка. Пожалуйста, попробуйте еще раз и пришлите креатив.")
        await sleep(3)
        await sent.delete()


# Обработчик выбора рекламной кампании CREATIVE_SELECT_CAMPAIGN
@dp.callback_query(lambda cb: cb.data.startswith(CB.CREATIVE_SELECT_CAMPAIGN.value))
async def choose_campaign(cb: CallbackQuery, state: FSMContext):
    _, page_str, action = cb.data.split(':')
    page = int(page_str)

    if action == Action.CONT:
        data = await state.get_data()

        campaigns = data.get('campaigns')
        if not campaigns:
            campaigns = await db.get_user_campaigns(cb.from_user.id)
            await state.update_data(data={'campaigns': campaigns})

        text = (
            f'Выберите рекламную кампанию для этого креатива:\n'
            f'{page + 1}/{len(campaigns)}:\n\n'
            f'{campaigns[page].brand}\n'
            f'{campaigns[page].service}'
        ).replace('None', '')

        await cb.message.edit_text(text=text, reply_markup=kb.get_select_page_kb(
            end_page=(page + 1) == len(campaigns),
            select_id=campaigns[page].id,
            page=page,
            cb=CB.CREATIVE_SELECT_CAMPAIGN.value
        ))

    else:
        await state.update_data(data={'campaign_id': page})
        data = await state.get_data()

        # ищем карточки для быстрой оплаты
        # sent = await cb.message.answer('⏳')
        save_cards = await db.get_user_card(cb.from_user.id)

        # pay_id = ut.create_pay_link(data['campaign_id'])
        # await sent.delete()
        await cb.message.answer(
            text='Для получения токена (маркировки) произведите оплату.\n\n'
                 'Выберите карту для оплаты или добавьте новую.',
            reply_markup=kb.get_select_card_kb(save_cards)
        )


# создаёт ссылку на оплату
@dp.callback_query(lambda cb: cb.data.startswith(CB.PAY_YK_NEW.value))
async def pay_yk(cb: CallbackQuery, state: FSMContext):
    _, save_card = cb.data.split(':')
    save_card = bool(int(save_card))
    await state.update_data(data={'save_card': save_card})

    data = await state.get_data()
    pay_id = data.get('pay_id')
    if not pay_id:
        user = await db.get_user_info(cb.from_user.id)
        pay_id = ut.create_simple_pay_link(user.email)
        await state.update_data(data={'pay_id': pay_id})

    text = 'Перейдите по ссылке и оплатите маркировку креатива, затем нажмите "Продолжить"\n\n'

    if save_card:
        text += '✔️ Карта сохранена для быстрой оплаты\n\n'
    else:
        text += '❕ Поставьте галочку "Сохранить карту", чтоб сохранить данные для быстрой оплаты\n\n'

    text += 'Мы не храним данные о картах и пользователя все данные хранит сервис Юкасса...❓❓❓'

    await cb.message.edit_text(text=text, reply_markup=kb.get_yk_pay_kb(pay_id, save_card))


# Обработчик кнопки "Продолжить". Обычная оплата
@dp.callback_query(lambda cb: cb.data.startswith(CB.PAY_YK_CHECK.value))
async def choose_campaign(cb: CallbackQuery, state: FSMContext):
    _, pay_id = cb.data.split(':')

    sent = await cb.message.answer('⏳')
    pay_data = Payment.find_one(pay_id)
    if pay_data.paid:
        # сохраняем данные платежа
        await db.add_payment(
            user_id=cb.from_user.id,
            pay_id=pay_data.id,
        )
        data = await state.get_data()
        if data.get('save_card'):
            await db.add_card(
                user_id=cb.from_user.id,
                pay_id=pay_id,
                card_info=ut.get_payment_card_info(pay_data)
            )

        await register_creative(data=data, user_id=cb.from_user.id, del_msg_id=sent.message_id)

    else:
        await sent.delete()
        await cb.answer('❗️  Оплата не прошла нажмите "Оплатить" и совершите платёж', show_alert=True)


# Быстрая оплата
@dp.callback_query(lambda cb: cb.data.startswith(CB.PAY_YK_FAST.value))
async def choose_campaign(cb: CallbackQuery, state: FSMContext):
    _, card_id_str = cb.data.split(':')
    card_id = int(card_id_str)

    if not Config.debug:
        await cb.answer('Быстрая оплата временно невозможна', show_alert=True)
        return

    sent = await cb.message.answer('⏳')
    card_info = await db.get_card(card_id=card_id)
    user_info = await db.get_user_info(user_id=cb.from_user.id)

    pay_data = ut.fast_pay(last_pay_id=card_info.last_pay_id, email=user_info.email)

    if pay_data.paid:
        # сохраняем данные платежа
        await db.add_payment(user_id=cb.from_user.id, pay_id=pay_data.id)
        # обновляем пей айди
        await db.update_card(card_id=card_id, pay_id=pay_data.id)

        data = await state.get_data()
        await register_creative(data=data, user_id=cb.from_user.id, del_msg_id=sent.message_id)

    else:
        await sent.delete()
        await cb.answer('❗️ Ошибка оплаты. Выберите другую карту или добавьте новую ❓❓❓', show_alert=True)


# Добавление ссылки на креатив
@dp.callback_query(lambda cb: cb.data.startswith(CB.CREATIVE_ADD_LINK.value))
async def add_link(cb: CallbackQuery, state: FSMContext):
    _, creative_id = cb.data.split(':')

    await state.set_state(UserState.ADD_CREATIVE_LINK)
    await state.update_data(data={'creative_id': int(creative_id)})
    await cb.message.answer(
        "Опубликуйте ваш креатив и пришлите ссылку на него. Если вы публикуете один креатив на разных площадках - "
        "пришлите ссылку на каждую площадку.")


# # Обработчик загрузки креатива
# @dp.message(StateFilter(UserState.ADD_CREATIVE_LINK))
# async def handle_creative_upload(msg: Message, state: FSMContext):
#     if msg.entities and msg.entities[0].type == MessageEntityType.URL:
#         data = await state.get_data()
#         await db.update_creative(creative_id=data['creative_id'], link=msg.text)
#         await msg.answer(
#             text='Вы успешно добавили ссылку на ваш рекламный креатив\n\n'
#                  'Добавьте ещё ссылки или нажмите "Готово"',
#             reply_markup=kb.get_end_creative_kb(data['creative_id'], with_add=False))
#
#     else:
#         await msg.answer('❌ Некорректный формат ссылки')


@dp.callback_query(lambda cb: cb.data.startswith(CB.CREATIVE_DONE.value))
async def link_done(cb: CallbackQuery, state: FSMContext):
    _, creative_id = cb.data.split(':')

    creative = await db.get_creative(int(creative_id))
    if creative.links:
        await state.clear()
        await cb.message.answer(
            "Вы успешно добавили все ссылки на креатив. "
            "Подать отчетность по показам нужно будет в конце месяца или при завершении публикации. "
            "В конце месяца мы вам напомним о подаче отчетности.")

    else:
        await cb.message.answer(
            "❌ Вы не добавили ссылки на креатив\n\n"
            "Опубликуйте ваш креатив и пришлите ссылку на него. Если вы публикуете один креатив на разных площадках - "
            "пришлите ссылку на каждую площадку.",
            reply_markup=kb.get_end_creative_kb(int(creative_id))
        )


# Обработчик кнопки "Добавить файл или текст"
# @dp.callback_query(lambda cb: cb.data.startswith(CB.CREATIVE_ADD_CREATIVE.value))
# async def add_more_creative(cb: CallbackQuery):
#     await cb.answer('📲 Отправьте ещё контент для вашего креатива', show_alert=True)