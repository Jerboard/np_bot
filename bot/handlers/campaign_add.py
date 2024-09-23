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
from .base import add_creative_start, start_campaign_base, start_bot
from enums import CB, Command, UserState, JStatus, Role, AddContractStep


# Обработчик для команды /start_campaign
@dp.message(CommandFilter(Command.START_CAMPAIGN.value))
async def start_campaign(msg: Message, state: FSMContext):
    user = await db.get_user_info(msg.from_user.id)
    if user:
        await start_campaign_base(msg, state)
    else:
        await start_bot(msg, state)


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

    await msg.answer("Пришлите ссылку на товар или услугу, которые вы планируете рекламировать.")


# Обработчик для сохранения целевой ссылки
@dp.message(StateFilter(UserState.ADD_CAMPAIGN_LINK))
async def save_target_link(msg: Message, state: FSMContext):
    target_link = msg.text
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
        links_str = "\n".join([f"Целевая ссылка {i + 1}: {link}" for i, link in data['links']])

        await cb.message.answer(
            f"Проверьте, правильно ли указана информация о рекламной кампании:\n"
            f"Бренд: {data['brand']}\n"
            f"Услуга: {data['service']}\n"
            f"{links_str}",
            reply_markup=kb.get_confirm_ad_campaign_kb()
        )


# Обработка выбора подтверждения, изменения или удаления рекламной кампании CAMPAIGN_ADD_CONFIRM
@dp.callback_query(lambda cb: cb.data.startswith(CB.CAMPAIGN_ADD_CONFIRM.value))
async def handle_ad_campaign_callback(cb: CallbackQuery, state: FSMContext):
    _, action = cb.data.split(':')
    if action == '1':
        data = await state.get_data()
        await state.clear()
        campaign_id = await db.add_campaign(
            user_id=cb.from_user.id,
            brand=data['brand'],
            service=data['service'],
            links=data['links'],
        )

        await cb.message.answer(
            f"Рекламная кампания с брендом "
            f"{data['brand']}"
            f"успешно создана!"
        )
        await add_creative_start(cb.message, state, campaign_id)

    elif cb.data.startswith("change_ad_campaign"):
        await state.clear()
        await start_campaign(cb.message, state)
