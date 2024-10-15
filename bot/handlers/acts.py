from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command as CommandFilter, StateFilter
from aiogram.fsm.context import FSMContext
from datetime import datetime

import db
import keyboards as kb
from config import Config
from init import dp, bot
import utils as ut
from . import base
from enums import CB, Command, UserState, Action, Step


# Обработка команды /acts
@dp.message(CommandFilter(Command.ACTS.value))
async def start_stats(msg: Message, state: FSMContext):
    await state.clear()
    active_contracts = await db.get_all_user_contracts(msg.from_user.id)

    # Получаем первый доступный campaign_id для пользователя
    if active_contracts:
        await state.set_state(UserState.SEND_STATISTIC)
        await state.update_data(data={'page': 0, 'active_contracts': active_contracts})

        await msg.answer("<b>❕ Выберите контракт для подачи акта</b>")
        await base.start_acts(
            active_contracts=active_contracts,
            user_id=msg.from_user.id,
            state=state
        )
    else:
        await msg.answer("❗️ У вас нет активных контрактов.")


# Выбор страницы
@dp.callback_query(lambda cb: cb.data.startswith(CB.ACTS_SELECT_PAGE.value))
async def acts_select_page(cb: CallbackQuery, state: FSMContext):
    _, page_str, action = cb.data.split(':')
    page = int(page_str)

    if action == Action.CONT:
        data = await state.get_data()
        active_contracts = data.get('active_contracts')
        if not active_contracts:
            active_contracts = await db.get_all_user_contracts(cb.from_user.id)
            await state.update_data(data={'active_contracts': active_contracts, 'current': page})
        await base.start_acts(
            active_contracts=active_contracts,
            page=page,
            user_id=cb.from_user.id,
            message_id=cb.message.message_id,
            state=state
        )
    else:
        await state.set_state(UserState.ACTS)
        await state.update_data(data={'contract_id': page, 'step': Step.END_DATE})
        text = f'Вы завершаете работу по [Договору №1] сегодня?'
        await cb.message.answer(text=text, reply_markup=kb.get_check_next_step_act_kb())


# проводит по шагам подачи акта
async def get_act_steps(user_id: int, step: str, state: FSMContext):
    if step == Step.END_DATE:
        # await state.update_data(data={'step': Step.END_DATE})
        text = f'Введите дату'
        await bot.send_message(chat_id=user_id, text=text)

    elif step == Step.SUM:
        text = f'Введите сумму'
        await bot.send_message(chat_id=user_id, text=text)


# выбор шага
@dp.callback_query(lambda cb: cb.data.startswith(CB.ACT_NEXT_STEP_CHECK.value))
async def act_next_step_check(cb: CallbackQuery, state: FSMContext):
    _, action = cb.data.split(':')

    data = await state.get_data()

    if action == Action.NO:
        await get_act_steps(user_id=cb.from_user.id, step=data['step'], state=state)

    else:
        if data['step'] == Step.END_DATE:
            await state.update_data(data={'step': Step.SUM})
            text = (f'Сумма работ по [Договору №1] указана верно?\n'
                    f'[Сумма по договору №1]')
            await cb.message.answer(text=text, reply_markup=kb.get_check_next_step_act_kb())

        else:
            await base.end_act(user_id=cb.from_user.id, data=data)


# Обработка команды /acts
@dp.message(StateFilter(UserState.ACTS))
async def start_save_data(msg: Message, state: FSMContext):
    data = await state.get_data()

    if data['step'] == Step.END_DATE:
        date_str = ut.convert_date(msg.text)
        if not date_str:
            await msg.answer("❌ Неверный формат даты. Пожалуйста, введите дату в формате дд.мм.гггг:")
            return

        start_date = datetime.strptime(date_str, Config.ord_date_form).date()
        today = datetime.now().date()
        if start_date > today:
            await msg.answer("❌ Неверный формат даты.\n\n Дата окончания договора не должна быть больше сегодняшней")
            return

        await state.update_data(data={'end_date_str': date_str, 'step': Step.SUM})
        await get_act_steps(user_id=msg.from_user.id, step=Step.SUM, state=state)

    # elif data['step'] == Step.SUM:
    else:
        if not ut.is_float(msg.text):
            await msg.answer("❌ Неверный формат суммы.\n\n Введите сумму цифрами")
            return

        await state.update_data(data={'amount': msg.text})
        data = await state.get_data()
        await base.end_act(user_id=msg.from_user.id, data=data)


# отправка данных в орд
@dp.callback_query(lambda cb: cb.data.startswith(CB.ACT_SEND.value))
async def acts_send(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    # contract = await db.get_contract_full_data(data['contract_id'])

    campaigns = await db.get_user_campaigns(contract_id=data['contract_id'])
