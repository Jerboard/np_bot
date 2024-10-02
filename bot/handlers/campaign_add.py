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
from . import base
from enums import CB, Command, UserState, Action, Role, Step


# Обработчик для команды /start_campaign
@dp.message(CommandFilter(Command.START_CAMPAIGN.value))
async def start_campaign(msg: Message, state: FSMContext):
    user = await db.get_user_info(msg.from_user.id)
    if user:
        await base.start_campaign_base(msg, state)
    else:
        await base.start_bot(msg, state)


# Смена страницы контрактов
@dp.callback_query(lambda cb: cb.data.startswith(CB.CONTRACT_PAGE.value))
async def save_brand(cb: CallbackQuery, state: FSMContext):
    _, page_str, action = cb.data.split(':')
    page = int(page_str)

    if action == Action.CONT:
        data = await state.get_data()
        contracts = data.get('contracts')
        if not contracts:
            contracts = await db.get_all_user_contracts(cb.from_user.id)
            await state.update_data(data={'contracts': contracts, 'current': page})
        await base.select_contract(
            contracts=contracts,
            current=page,
            chat_id=cb.message.chat.id,
            message_id=cb.message.message_id,
        )
    else:
        await state.update_data(data={'contract_id': page})
        await base.start_campaign_base(
            msg=cb.message,
            state=state,
            contract_id=page,
            user_id=cb.from_user.id
        )


# Обработчик для сохранения бренда
@dp.message(StateFilter(UserState.ADD_CAMPAIGN_BRAND))
async def save_brand(msg: Message, state: FSMContext):
    await state.set_state(UserState.ADD_CAMPAIGN_SERVICE)
    await state.update_data(data={'brand': msg.text})
    # await msg.answer("Бренд сохранен.")
    msg = await msg.answer(
        text="Кратко опишите товар или услугу, которые вы планируете рекламировать (не более 60 символов)."
    )


# Обработчик для сохранения услуги
@dp.message(StateFilter(UserState.ADD_CAMPAIGN_SERVICE))
async def save_service(msg: Message, state: FSMContext):
    await state.set_state(UserState.ADD_CAMPAIGN_LINK)
    await state.update_data(data={'service': msg.text[:60]})

    await msg.answer(
        text="Пришлите ссылку на товар или услугу, которые вы планируете рекламировать.",
        reply_markup=kb.get_continue_add_link_kb()
    )


# Обработчик для сохранения целевой ссылки
@dp.message(StateFilter(UserState.ADD_CAMPAIGN_LINK))
async def save_target_link(msg: Message, state: FSMContext):
    target_link = msg.text
    if not target_link:
        await msg.answer('❌ Неверный формат. Отправьте ссылку сообщением')
        return

    if not target_link.startswith("http://") and not target_link.startswith("https://"):
        target_link = f"https://{target_link}"

    data = await state.get_data()
    links: list = data.get('links', [])
    links.append(target_link)
    await state.update_data(data={'links': links})

    await msg.answer(
        text="Есть ли дополнительная ссылка на товар или услугу, которые вы планируете рекламировать?",
        reply_markup=kb.get_ask_for_additional_link_kb()
    )


@dp.callback_query(lambda cb: cb.data.startswith(CB.CAMPAIGN_ADD_ANOTHER_LINK.value))
async def handle_additional_link(cb: CallbackQuery, state: FSMContext):
    _, action = cb.data.split(':')
    if action == '1':
        await state.set_state(UserState.ADD_CAMPAIGN_LINK)
        await cb.message.answer("Пришлите ссылку на товар или услугу, которые вы планируете рекламировать.")

    else:
        data = await state.get_data()
        if data.get('links'):
            links_str = "\n".join([f"Целевая ссылка: {link}" for link in data['links']])
        else:
            links_str = ''

        await cb.message.answer(
            f"❕ Проверьте, правильно ли указана информация о рекламной кампании:\n\n"
            f"<b>Бренд:</b> {data['brand']}\n"
            f"<b>Услуга:</b> {data['service']}\n"
            f"{links_str}",
            reply_markup=kb.get_confirm_ad_campaign_kb(),
            disable_web_page_preview=True
        )


# Обработка выбора подтверждения, изменения или удаления рекламной кампании CAMPAIGN_ADD_CONFIRM
@dp.callback_query(lambda cb: cb.data.startswith(CB.CAMPAIGN_ADD_CONFIRM.value))
async def handle_ad_campaign_callback(cb: CallbackQuery, state: FSMContext):
    _, action = cb.data.split(':')
    if action == Action.ADD:
        data = await state.get_data()
        await state.clear()
        campaign_id = await db.add_campaign(
            user_id=cb.from_user.id,
            contract_id=data['contract_id'],
            brand=data['brand'],
            service=data['service'],
            links=data.get('links', []),
        )

        await cb.message.answer(
            f"Рекламная кампания с брендом {data['brand']} успешно создана!"
        )
        await base.add_creative_start(cb.message, state, campaign_id)

    elif action == Action.EDIT:
        data = await state.get_data()
        await base.start_campaign_base(
            msg=cb.message,
            state=state,
            contract_id=data['contract_id'],
            user_id=cb.from_user.id
        )

    else:
        await state.clear()
        await base.start_campaign_base(msg=cb.message, state=state, user_id=cb.from_user.id)




