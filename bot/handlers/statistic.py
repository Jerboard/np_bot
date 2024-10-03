from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command as CommandFilter, StateFilter
from aiogram.fsm.context import FSMContext

import db
import keyboards as kb
from init import dp
import utils as ut
from .base import preloader_advertiser_entity
from enums import CB, Command, UserState, JStatus, Role


### Блок подачи статистики ###


# Обработка команды /start_statistics
@dp.message(CommandFilter(Command.STATS.value))
async def send_welcome(message: Message):
    user_id = message.from_user.id
    user_state = {}
    # Получаем первый доступный campaign_id для пользователя
    campaign_ids = db.query_db('SELECT campaign_id FROM ad_campaigns WHERE chat_id = ?', (user_id,))
    if campaign_ids:
        user_state[user_id] = [cid[0] for cid in campaign_ids]  # Сохраняем все доступные campaign_id для пользователя
        user_state[str(user_id) + "_current"] = 0  # Текущий индекс campaign_id
        message_text, markup = cf.create_message_text(user_state[user_id][0])
        await message.answer(message.chat.id, message_text, reply_markup=markup, parse_mode='HTML')

    #     добавляем данные в редис
        ut.save_user_data(message.chat.id, user_state)
    else:
        await message.answer(message.chat.id, "У вас нет активных кампаний.")


# Обработка нажатий на кнопки
@dp.callback_query(lambda cb: cb.data in ['back', 'forward'] or cb.data.startswith('select_'))
async def callback_query(cb: CallbackQuery):
    user_id = cb.from_user.id

    # получаем данные из редиса
    user_state = ut.get_user_data(user_id)
    current_index = user_state.get(str(user_id) + "_current", 0)  # Получаем текущий индекс креатива для пользователя
    total_creatives = cf.get_total_creatives(user_id)

    logging.debug(
        f"callback_query: cb.data = {cb.data}, current_index = {current_index}, total_creatives = {total_creatives}")

    if cb.data == 'back':
        current_index = (current_index - 1) % total_creatives
    elif cb.data == 'forward':
        current_index = (current_index + 1) % total_creatives
    elif cb.data.startswith('select_'):
        selected_campaign_id = cb.data.split('_')[1]
        user_state[str(user_id) + "_selected"] = selected_campaign_id
        await message.answer(cb.message.chat.id, "Укажите количество показов по данному креативу:")
        dp.register_next_step(cb.message, cf.handle_statistics_input)
        return

    user_state[str(user_id) + "_current"] = current_index
    current_campaign_id = user_state[user_id][current_index]
    message_text, markup = cf.create_message_text(current_campaign_id)
    dp.edit_message_text(chat_id=cb.message.chat.id, message_id=cb.message.message_id,
                         text=message_text, reply_markup=markup, parse_mode='HTML')

#     обновляем данные в редис
#     ut.save_user_data(user_id, user_state)


# Обработка подтверждения
@dp.callback_query(lambda cb: cb.data in ['confirm_yes', 'confirm_no'])
async def handle_confirm(call):
    chat_id = cb.message.chat.id
    logging.debug(f"handle_confirm: cb.data = {cb.data}")
    if cb.data == 'confirm_yes':
        logging.debug("Обработка подтверждения: cb.data = confirm_yes")
        cf.send_statistics_to_ord(chat_id)
    elif cb.data == 'confirm_no':
        await message.answer("Введите корректное количество показов:")
        dp.register_next_step(cb.message, cf.handle_statistics_input)
