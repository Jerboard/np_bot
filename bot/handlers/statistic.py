from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command as CommandFilter, StateFilter
from aiogram.fsm.context import FSMContext

import db
import keyboards as kb
from init import dp
import utils as ut
from . import base
from enums import CB, Command, UserState, Action, Role


# # Обработка команды /start_statistics
# @dp.message(CommandFilter(Command.STATS.value))
# async def start_stats(msg: Message, state: FSMContext):
#     active_creatives = await db.get_statistics(msg.from_user.id)
#
#     # Получаем первый доступный campaign_id для пользователя
#     if active_creatives:
#         await state.set_state(UserState.SEND_STATISTIC)
#         await state.update_data(data={'page': 0, 'active_creatives': active_creatives, 'sending_list': []})
#
#         await msg.answer("<b>❕ Выберите креатив для подачи статистики</b>")
#         await base.start_statistic(
#             active_creatives=active_creatives,
#             user_id=msg.from_user.id,
#             sending_list=[],
#             state=state
#         )
#     else:
#         await msg.answer("❗️ У вас нет активных креативов.")


# Выбор страницы
@dp.callback_query(lambda cb: cb.data.startswith(CB.STATISTIC_SELECT_PAGE.value))
async def statistic_select_page(cb: CallbackQuery, state: FSMContext):
    _, page_str, action = cb.data.split(':')
    page = int(page_str)

    data = await state.get_data()
    active_creatives = data.get('active_creatives')
    await state.update_data(data={'page': page, 'message_id': cb.message.message_id})
    if not active_creatives:
        active_creatives = await db.get_statistics(cb.from_user.id)
        await state.update_data(data={'active_creatives': active_creatives})

    await base.start_statistic(
        active_creatives=active_creatives,
        page=page,
        user_id=cb.from_user.id,
        message_id=cb.message.message_id,
        sending_list=data.get('sending_list', []),
        state=state
    )


# Сохраняет статистику по креативу
@dp.message(StateFilter(UserState.SEND_STATISTIC))
async def save_target_link(msg: Message, state: FSMContext):
    await msg.delete()

    if not msg.text.isdigit():
        await msg.answer('❌ Некорректный формат\n\nОтправьте числом количество просмотров')
        return

    data = await state.get_data()
    page = data['page']
    sending_list: list = data.get('sending_list', [])
    active_creatives = data.get('active_creatives')

    statistic: db.StatisticRow = active_creatives[page]
    creative = await db.get_creative(creative_id=statistic.creative_id)
    platform = await db.get_platform(platform_id=statistic.platform_id)

    statistic_ord_id = await ut.send_statistic_to_ord(
        creative_ord_id=creative.ord_id,
        platform_ord_id=platform.ord_id,
        views=msg.text,
        creative_date=creative.created_at
    )

    if statistic_ord_id:
        await db.update_statistic(statistic_id=creative.id, views=int(msg.text), ord_id=statistic_ord_id)

        sending_list.append(page)
        await state.update_data(data={'active_creatives': active_creatives})

    else:
        await msg.answer('❌ Данные не были отправлены')

    await base.start_statistic(
        active_creatives=active_creatives,
        page=page,
        user_id=msg.from_user.id,
        message_id=data['message_id'],
        sending_list=sending_list,
        state=state
    )

