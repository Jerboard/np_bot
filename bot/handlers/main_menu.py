from telebot import types
from telebot.types import CallbackQuery

import logging
import re
import requests

import db
import keyboards as kb
from init import bot
from .base import preloader_choose_platform, preloader_advertiser_entity


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_data = db.query_db(
        'SELECT fio, title, inn, juridical_type, balance, role FROM users WHERE chat_id = ?',
        (chat_id,),
        one=True
    )

    if user_data:
        # Если пользователь найден в базе данных, выводим информацию о нем
        fio, title, inn, juridical_type, balance, role = user_data
        juridical_type_map = {
            'ip': 'Индивидуальный предприниматель',
            'juridical': 'Юридическое лицо',
            'physical': 'Физическое лицо'
        }
        role_map = {
            'publisher': 'Рекламораспространитель',
            'advertiser': 'Рекламодатель'
        }

        display_name = fio if juridical_type != 'juridical' else title
        name_label = "ФИО" if juridical_type != 'juridical' else "Название организации"

        bot.send_message(chat_id,
                         f"Информация о вас:\n\n"
                         f"{name_label}: <b>{display_name}</b>\n"
                         f"ИНН: <b>{inn}</b>\n"
                         f"Правовой статус: <b>{juridical_type_map.get(juridical_type, juridical_type)}</b>\n"
                         f"Баланс: <b>{balance} рублей</b>\n"
                         f"Текущая роль: <b>{role_map.get(role, role)}</b>\n\n"
                         "Вы можете изменить свои данные и роль.\n\n"
                         "Чтобы воспользоваться функционалом бота - нажмите на синюю кнопку меню и выберите действие.\n\n",
                         reply_markup=kb.get_start_kb(), parse_mode="HTML")
    else:
        # Если пользователь не найден в базе данных, предлагаем согласиться с офертой
        markup = types.InlineKeyboardMarkup()
        agree_button = types.InlineKeyboardButton('Я согласен', callback_data='agree')
        markup.row(agree_button)
        bot.send_message(
            chat_id,
            'Для начала работы вам необходимо согласиться с офертой и дать согласие на обработку персональных данных: \n\n'
            '<a href="https://docs.google.com/document/d/1QnOmySz1lrFzrRQs6HBXuJqDAZA3DoSCRGC-KE6EMKg/edit?usp=sharing">Согласие на обработку персональных данных</a> \n'
            '<a href="https://docs.google.com/document/d/1_P9lq4CffvU3lIhNZ6TbyUIGPcl0n9St5pAdtVjFgBE/edit?usp=sharing">Согласие на рекламную рассылку</a> \n'
            '<a href="https://docs.google.com/document/d/1WvSRMMoC0OwAoRJKbuS0bi1DJOUvhsp9M_MwNTC11HU/edit?usp=sharing">Политика конфиденциальности</a> \n'
            '<a href="https://docs.google.com/document/d/1nWeP61-18S_4QfS4XloXSvyTLJKRbOfMe8rEZPSVJVI/edit?usp=sharing">Публичная оферта</a> \n',
            reply_markup=markup,
            parse_mode="HTML",
            disable_web_page_preview=True
        )


# Обработка смены роли пользователя
def process_role_change(message):
    chat_id = message.chat.id
    bot.send_message(
        chat_id,
        text=("Выберите свою роль:\n"
              "Рекламодатель - тот, кто заказывает и оплачивает рекламу.\n"
              "Рекламораспространитель - тот, кто распространяет рекламу на площадках, чтобы привлечь внимание "
              "к товару или услуге.")
    )
    bot.send_message(chat_id, "Выберите свою роль:", reply_markup=kb.get_process_role_change_kb())


# Обработчик нажатий на кнопки подтверждения или смены роли
@bot.callback_query_handler(func=lambda call: call.data in ['confirm_user', 'change_role'])
def handle_user_confirmation(call: CallbackQuery):
    chat_id = call.message.chat.id

    if call.data == 'confirm_user':
        bot.send_message(chat_id, "Данные подтверждены. Вы можете продолжить работу с ботом.")
    elif call.data == 'change_role':
        # Добавьте логику для смены роли пользователя здесь
        process_role_change(call.message)


# Обработчик нажатия на кнопку "Я согласен"
@bot.callback_query_handler(func=lambda call: call.data == 'agree')
def agree(call: CallbackQuery):
    chat_id = call.message.chat.id
    if not db.get_user(chat_id):
        db.insert_user_data(chat_id, True, None, None, None, None, None)
        bot.answer_callback_query(callback_query_id=call.id, text='Спасибо за согласие!')
        register(call)
    else:
        bot.answer_callback_query(callback_query_id=call.id, text='Вы уже согласились.')
        register(call)


# Обработчик для регистрации
def register(call: CallbackQuery):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Укажите свой правовой статус", reply_markup=kb.get_register_kb())


# Обработчик для сбора информации о пользователе
@bot.callback_query_handler(func=lambda call: call.data in ['ip', 'juridical', 'physical'])
def collect_info(call: CallbackQuery):
    chat_id = call.message.chat.id
    juridical_type = call.data

    # постгре
    db.insert_users_juridical_type_data(chat_id, juridical_type)
    # старый код
    # db.query_db('INSERT OR REPLACE INTO users (chat_id, juridical_type) VALUES (?, ?)', (chat_id, juridical_type))

    logging.debug(f"Saved juridical_type: {juridical_type} for chat_id: {chat_id}")
    if juridical_type == 'ip':
        bot.send_message(chat_id, "Укажите ваши фамилию, имя и отчество. \nНапример, Иванов Иван Иванович.")
        bot.register_next_step_handler(call.message, fio_i_collector)
    elif juridical_type == 'juridical':
        bot.send_message(chat_id, "Укажите название вашей организации. \nНапример, ООО ЮКЦ Партнер.")
        bot.register_next_step_handler(call.message, title_collector)
    elif juridical_type == 'physical':
        bot.send_message(chat_id, "Укажите ваши фамилию, имя и отчество. \nНапример, Иванов Иван Иванович.")
        bot.register_next_step_handler(call.message, fio_collector)


# Обработчик для сбора ФИО ИП
def fio_i_collector(message):
    chat_id = message.chat.id
    fio_i = message.text
    db.query_db('UPDATE users SET fio = ? WHERE chat_id = ?', (fio_i, chat_id))
    logging.debug(f"Saved fio_i: {fio_i} for chat_id: {chat_id}")
    bot.send_message(message.chat.id,
                     "Введите ваш ИНН. \nНапример, 563565286576. ИНН индивидуального предпринимателя совпадает с ИНН физического лица.")
    bot.register_next_step_handler(message, inn_collector)


# Обработчик для сбора ФИО физ. лица
def fio_collector(message):
    chat_id = message.chat.id
    fio = message.text
    db.query_db('UPDATE users SET fio = ? WHERE chat_id = ?', (fio, chat_id))
    logging.debug(f"Saved fio: {fio} for chat_id: {chat_id}")
    bot.send_message(message.chat.id, "Введите ваш ИНН. Например, 563565286576.")
    bot.register_next_step_handler(message, inn_collector)


# Обработчик для сбора названия организации
def title_collector(message):
    chat_id = message.chat.id
    title = message.text
    db.query_db('UPDATE users SET title = ? WHERE chat_id = ?', (title, chat_id))
    logging.debug(f"Saved title: {title} for chat_id: {chat_id}")
    bot.send_message(message.chat.id, "Введите ИНН вашей организации. Например, 6141027912.")
    bot.register_next_step_handler(message, inn_collector)


# Валидатор ИНН
def validate_inn(inn, juridical_type):
    inn = str(inn)

    if juridical_type in ['ip', 'physical']:
        if len(inn) != 12:
            return False
    elif juridical_type == 'juridical':
        if len(inn) != 10:
            return False

    if not re.match(r'^\d{10}$|^\d{12}$', inn):
        return False

    # переименовал inn в inn_check и coefficients в coefficients_check, чтоб не дублировалось название переменной
    def check_control_digit(inn_check, coefficients_check):
        n = sum([int(a) * b for a, b in zip(inn_check, coefficients_check)]) % 11
        return n if n < 10 else n % 10

    if len(inn) == 10:
        coefficients = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        return check_control_digit(inn[:-1], coefficients) == int(inn[-1])
    elif len(inn) == 12:
        coefficients1 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        coefficients2 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        return (check_control_digit(inn[:-1], coefficients1) == int(inn[-1]) and
                check_control_digit(inn[:-2], coefficients2) == int(inn[-2]))

    return False


# Обработчик для сбора ИНН
def inn_collector(message):
    chat_id = message.chat.id
    inn = message.text.strip()
    juridical_type = db.query_db('SELECT juridical_type FROM users WHERE chat_id = ?', (chat_id,), one=True)[0]
    if not validate_inn(inn, juridical_type):
        bot.send_message(chat_id, "Неверный формат ИНН. Пожалуйста, введите корректный ИНН:")
        bot.register_next_step_handler(message, inn_collector)
        return
    db.query_db('UPDATE users SET inn = ? WHERE chat_id = ?', (inn, chat_id))
    logging.debug(f"Saved inn: {inn} for chat_id: {chat_id}")
    bot.send_message(chat_id,
                     "Выберите свою роль:\nРекламодатель - тот, кто заказывает и оплачивает рекламу.\nРекламораспространитель - тот, кто распространяет рекламу на площадках, чтобы привлечь внимание к товару или услуге.")

    bot.send_message(chat_id, "Выберите свою роль:", reply_markup=kb.get_inn_collector_kb())


# Обработчик для выбора роли
@bot.callback_query_handler(func=lambda call: call.data in ['advertiser', 'publisher'])
def collect_role(call: CallbackQuery):
    chat_id = call.message.chat.id
    role = call.data
    db.query_db('UPDATE users SET role = ? WHERE chat_id = ?', (role, chat_id))
    user_data = db.query_db(
        'SELECT fio, title, inn, juridical_type FROM users WHERE chat_id = ?',
        (chat_id,),
        one=True
    )
    fio, title, inn, juridical_type = user_data

    logging.debug(f"User data: fio={fio}, title={title}, inn={inn}, juridical_type={juridical_type}")

    assert juridical_type in ['physical', 'juridical', 'ip'], f"Invalid juridical_type: {juridical_type}"

    if juridical_type == 'juridical':
        fio = title  # если это юридическое лицо, то используем название организации как ФИО

    # Определяем rs_url только для юридических лиц и ИП
    rs_url = "https://example.com" if juridical_type != 'physical' else None

    # Отправляем данные в ОРД
    response = send_to_ord(chat_id, fio, role, juridical_type, inn, "", rs_url)

    # handle_ord_response пока закомментил, используется только тут. Взял отправку сообщений
    if role == 'advertiser':
        handle_ord_response(response, call.message, preloader_advertiser_entity, call.message)
    elif role == 'publisher':
        handle_ord_response(response, call.message, preloader_choose_platform, call.message)


# Функция для отправки данных в ОРД API
def send_to_ord(chat_id, fio, role, juridical_type, inn, phone, rs_url=None):
    try:
        assert juridical_type in ['physical', 'juridical', 'ip'], f"Invalid juridical_type: {juridical_type}"

        url = f"https://api-sandbox.ord.vk.com/v1/person/{chat_id}"
        headers = {
            "Authorization": f"Bearer 633962f71ade453f997d179af22e2532",
            "Content-Type": "application/json"
        }
        data = {
            "name": fio,
            "roles": [role],
            "juridical_details": {
                "type": juridical_type,
                "inn": inn,
                "phone": phone or "+7(495)709-56-39"  # Используем заглушку, если номер телефона пуст
            }
        }

        if rs_url:
            data["rs_url"] = rs_url

        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()  # Принудительно вызовет исключение для кода состояния HTTP 4xx или 5xx
        return response
    except AssertionError as e:
        logging.error(f"AssertionError: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"RequestException: {e}")
        return None


# Функция для обработки ответа от ОРД и дальнейшего выполнения кода
def handle_ord_response(response, message, next_step_function, *args):
    if response and response.status_code in [200, 201]:
        bot.send_message(message.chat.id, "Спасибо за регистрацию😉")
        next_step_function(*args)
    else:
        bot.send_message(message.chat.id, "Произошла ошибка при регистрации в ОРД")
