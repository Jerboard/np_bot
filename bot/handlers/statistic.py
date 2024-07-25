import logging

import db
import keyboards as kb
from init import bot
from . import common as cf


### Блок подачи статистики ###


# Обработка команды /start_statistics
@bot.message_handler(commands=['start_statistics'])
def send_welcome(message):
    user_id = message.from_user.id
    # Получаем первый доступный campaign_id для пользователя
    campaign_ids = db.query_db('SELECT campaign_id FROM ad_campaigns WHERE chat_id = ?', (user_id,))
    if campaign_ids:
        user_state[user_id] = [cid[0] for cid in campaign_ids]  # Сохраняем все доступные campaign_id для пользователя
        user_state[str(user_id) + "_current"] = 0  # Текущий индекс campaign_id
        message_text, markup = cf.create_message_text(user_state[user_id][0])
        bot.send_message(message.chat.id, message_text, reply_markup=markup, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "У вас нет активных кампаний.")


# Обработка нажатий на кнопки
@bot.callback_query_handler(func=lambda call: call.data in ['back', 'forward'] or call.data.startswith('select_'))
def callback_query(call):
    user_id = call.from_user.id
    current_index = user_state.get(str(user_id) + "_current", 0)  # Получаем текущий индекс креатива для пользователя
    total_creatives = cf.get_total_creatives(user_id)

    logging.debug(
        f"callback_query: call.data = {call.data}, current_index = {current_index}, total_creatives = {total_creatives}")

    if call.data == 'back':
        current_index = (current_index - 1) % total_creatives
    elif call.data == 'forward':
        current_index = (current_index + 1) % total_creatives
    elif call.data.startswith('select_'):
        selected_campaign_id = call.data.split('_')[1]
        user_state[str(user_id) + "_selected"] = selected_campaign_id
        bot.send_message(call.message.chat.id, "Укажите количество показов по данному креативу:")
        bot.register_next_step_handler(call.message, cf.handle_statistics_input)
        return

    user_state[str(user_id) + "_current"] = current_index
    current_campaign_id = user_state[user_id][current_index]
    message_text, markup = cf.create_message_text(current_campaign_id)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=message_text, reply_markup=markup, parse_mode='HTML')


# Обработка подтверждения
@bot.callback_query_handler(func=lambda call: call.data in ['confirm_yes', 'confirm_no'])
def handle_confirm(call):
    chat_id = call.message.chat.id
    logging.debug(f"handle_confirm: call.data = {call.data}")
    if call.data == 'confirm_yes':
        logging.debug("Обработка подтверждения: call.data = confirm_yes")
        cf.send_statistics_to_ord(chat_id)
    elif call.data == 'confirm_no':
        bot.send_message(chat_id, "Введите корректное количество показов:")
        bot.register_next_step_handler(call.message, cf.handle_statistics_input)
