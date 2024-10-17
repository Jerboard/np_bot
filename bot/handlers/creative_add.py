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
from . import base
from enums import CB, Command, UserState, Action, Role, Delimiter


# media_ord_id: 524275902-m-8688379168, 524275902-m-8258534790, 524275902-m-4984138183
# Обработчик загрузки креатива
@dp.message(StateFilter(UserState.ADD_CREATIVE))
async def handle_creative_upload_st(msg: Message, state: FSMContext):
    await base.creative_upload(msg, state)


# Обработчик выбора рекламной кампании CREATIVE_SELECT_CAMPAIGN
@dp.callback_query(lambda cb: cb.data.startswith(CB.CREATIVE_SELECT_CAMPAIGN.value))
async def creative_select_campaign(cb: CallbackQuery, state: FSMContext):
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
        # data = await state.get_data()

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

    # text += 'Мы не храним данные о картах и пользователя все данные хранит сервис Юкасса...❓❓❓'

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

        await base.register_creative(data=data, user_id=cb.from_user.id, del_msg_id=sent.message_id, state=state)

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

    else:
        sent = await cb.message.answer('⏳')
        data = await state.get_data()
        await base.register_creative(data=data, user_id=cb.from_user.id, del_msg_id=sent.message_id, state=state)

    # sent = await cb.message.answer('⏳')
    # card_info = await db.get_card(card_id=card_id)
    # user_info = await db.get_user_info(user_id=cb.from_user.id)
    #
    # pay_data = ut.fast_pay(last_pay_id=card_info.last_pay_id, email=user_info.email)
    #
    # if pay_data.paid:
    #     # сохраняем данные платежа
    #     await db.add_payment(user_id=cb.from_user.id, pay_id=pay_data.id)
    #     # обновляем пей айди
    #     await db.update_card(card_id=card_id, pay_id=pay_data.id)
    #
    #     data = await state.get_data()
    #     await register_creative(data=data, user_id=cb.from_user.id, del_msg_id=sent.message_id)

    # else:
    #     await sent.delete()
    #     await cb.answer('❗️ Ошибка оплаты. Выберите другую карту или добавьте новую ❓❓❓', show_alert=True)


# Добавление ссылки на креатив
@dp.callback_query(lambda cb: cb.data.startswith(CB.CREATIVE_ADD_LINK.value))
async def add_link(cb: CallbackQuery, state: FSMContext):
    _, creative_id = cb.data.split(':')

    await state.set_state(UserState.ADD_CREATIVE_LINK)
    await state.update_data(data={'creative_id': int(creative_id)})
    await cb.message.answer(
        text="Опубликуйте ваш креатив и пришлите ссылку на него. Если вы публикуете один креатив на разных "
             "площадках - пришлите ссылку на каждую площадку.")


# Обработчик загрузки ссылки на креатив
@dp.message(StateFilter(UserState.ADD_CREATIVE_LINK))
async def handle_creative_upload(msg: Message, state: FSMContext):
    if msg.entities and msg.entities[0].type == MessageEntityType.URL:
        data = await state.get_data()

        # проверяем зарегистрирована ли платформа
        platform_url = msg.text.rsplit('/', 1)[0]
        # print(f'platform_url: {platform_url}')
        platform = await db.get_platform(url=platform_url)

        if platform:
            await db.add_statistic(
                user_id=msg.from_user.id,
                creative_id=data['creative_id'],
                url=msg.text,
                platform_id=platform.id
            )
            text = 'Вы успешно добавили ссылку на ваш рекламный креатив\n\nДобавьте ещё ссылки или нажмите "Готово"'
            await msg.answer(
                text=text,
                reply_markup=kb.get_end_creative_kb(data['creative_id'], with_add=False))

        else:
            platforms = await db.get_user_platforms(msg.from_user.id)
            text = f'Укажите платформу размещения <a href="{msg.text}">креатива</a>'
            await msg.answer(text=text, reply_markup=kb.get_select_creative_platform_kb(platforms))

    else:
        await msg.answer('❌ Некорректный формат ссылки')


@dp.callback_query(lambda cb: cb.data.startswith(CB.CREATIVE_SELECT_PLATFORM.value))
async def link_done(cb: CallbackQuery, state: FSMContext):
    _, platform_id = cb.data.split(':')
    data = await state.get_data()

    url = cb.message.entities[0].url
    # print(f'cb.message.entities[0].url: {url}')

    await db.add_statistic(
        user_id=cb.from_user.id,
        creative_id=data['creative_id'],
        url=url,
        platform_id=int(platform_id)
    )
    text = 'Вы успешно добавили ссылку на ваш рекламный креатив\n\nДобавьте ещё ссылки или нажмите "Готово"'
    await cb.message.edit_text(
        text=text,
        reply_markup=kb.get_end_creative_kb(data['creative_id'], with_add=False)
    )


@dp.callback_query(lambda cb: cb.data.startswith(CB.CREATIVE_DONE.value))
async def link_done(cb: CallbackQuery, state: FSMContext):
    _, creative_id = cb.data.split(':')

    published_creative = await db.get_statistics(creative_id=int(creative_id))
    if published_creative:
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


@dp.message()
async def handle_creative_upload(msg: Message, state: FSMContext):
    await base.creative_upload(msg, state)
