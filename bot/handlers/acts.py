from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command as CommandFilter, StateFilter
from aiogram.fsm.context import FSMContext

import db
import keyboards as kb
from init import dp
import utils as ut
from . import base
from enums import CB, Command, UserState, Action, Role


# Обработка команды /acts
@dp.message(CommandFilter(Command.ACTS.value))
async def start_stats(msg: Message, state: FSMContext):
    active_contracts = await db.get_all_user_contracts(msg.from_user.id)

    # Получаем первый доступный campaign_id для пользователя
    if active_contracts:
        await state.set_state(UserState.SEND_STATISTIC)
        await state.update_data(data={'page': 0, 'active_contracts': active_contracts})

        await msg.answer("<b>❕ Выберите креатив для подачи статистики</b>")
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
        await state.update_data(data={'contract_id': page})
        await base.start_campaign_base(
            msg=cb.message,
            state=state,
            contract_id=page,
            user_id=cb.from_user.id
        )