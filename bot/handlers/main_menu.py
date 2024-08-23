from aiogram.types import Message
from aiogram.types import CallbackQuery
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext

import db
import data as dt
import keyboards as kb
import utils as ut
from config import Config
from init import dp, log_error, bot
from .base import preloader_choose_platform, preloader_advertiser_entity
from utils import ord_api
from enums import CB, JStatus, UserState


# Обработчик команды /start
@dp.message(CommandStart)
async def start(msg: Message, state: FSMContext):
    user = await db.get_user_info(msg.from_user.id)
    if user:
        # Если пользователь найден в базе данных, выводим информацию о нем
        display_name = user.fio if user.j_type != 'juridical' else user.title
        name_label = "ФИО" if user.j_type != 'juridical' else "Название организации"

        text = (f"Информация о вас:\n\n"
                f"{name_label}: <b>{display_name}</b>\n"
                f"ИНН: <b>{user.inn}</b>\n"
                f"Правовой статус: <b>{dt.juridical_type_map.get(user.j_type, user.j_type)}</b>\n"
                f"Баланс: <b>{user.balance} рублей</b>\n"
                f"Текущая роль: <b>{dt.role_map.get(user.role, user.role)}</b>\n\n"
                "Вы можете изменить свои данные и роль.\n\n"
                "Чтобы воспользоваться функционалом бота - нажмите на синюю кнопку меню и выберите действие.\n\n")
        await msg.answer(text, reply_markup=kb.get_start_kb())

    else:
        # Если пользователь не найден в базе данных, предлагаем согласиться с офертой
        await msg.answer(dt.start_text, reply_markup=kb.get_agree_button())


# типа конец регистрации пользователя вроде
# Обработчик нажатия на кнопку "Я согласен"
@dp.callback_query(lambda cb: cb.data == CB.AGREE.value)
async def agree(cb: CallbackQuery):
    user = await db.get_user_info(cb.from_user.id)
    if not user:
        await cb.answer('Спасибо за согласие!')
    else:
        await cb.answer('Вы уже согласились.')

    await cb.message.answer("Укажите свой правовой статус", reply_markup=kb.get_register_kb())
        
        
# Обработчик нажатий на кнопки подтверждения
@dp.callback_query(lambda cb: cb.data.startswith(CB.CONFIRM_USER.value))
async def confirmation(cb: CallbackQuery):
    if cb.data.startswith(CB.CONFIRM_USER.value) == CB.CONFIRM_USER:
        await cb.message.answer("✅ Данные подтверждены. Вы можете продолжить работу с ботом.")


# Обработчик нажатий на кнопки подтверждения или смены роли
@dp.callback_query(lambda cb: cb.data.startswith(CB.CHANGE_ROLE.value))
async def select_role(cb: CallbackQuery):
    # Добавьте логику для смены роли пользователя здесь
    await cb.message.answer(
        text=("Выберите свою роль:\n"
              "Рекламодатель - тот, кто заказывает и оплачивает рекламу.\n"
              "Рекламораспространитель - тот, кто распространяет рекламу на площадках, чтобы привлечь внимание "
              "к товару или услуге.")
    )
    await cb.message.answer("Выберите свою роль:", reply_markup=kb.get_process_role_change_kb())


# Обработчик для сбора информации о пользователе
@dp.callback_query(lambda cb: cb.data in [CB.IP.value, CB.JURIDICAL.value, CB.PHYSICAL.value])
async def collect_info(cb: CallbackQuery, state: FSMContext):
    juridical_type = cb.data

    await db.update_user(user_id=cb.from_user.id, j_type=juridical_type)

    if juridical_type == JStatus.IP:
        await cb.message.answer("Укажите ваши фамилию, имя и отчество. \nНапример, Иванов Иван Иванович.")

    elif juridical_type == JStatus.JURIDICAL:
        await cb.message.answer("Укажите название вашей организации. \nНапример, ООО ЮКЦ Партнер.")

    elif juridical_type == JStatus.PHYSICAL:
        await cb.message.answer("Укажите ваши фамилию, имя и отчество. \nНапример, Иванов Иван Иванович.")

    await state.set_state(UserState.USER_ADD_NAME)
    await state.update_data(data={'j_type': juridical_type})


# принимает имя
@dp.message(StateFilter(UserState.USER_ADD_NAME))
async def add_fio(msg: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(UserState.USER_ADD_INN)
    await state.update_data(data={'name': msg.text})

    if data['j_type'] == JStatus.IP:
        await msg.answer("Введите ваш ИНН. \n"
                         "Например, 563565286576. ИНН индивидуального предпринимателя совпадает с ИНН физического лица.")
    elif data['j_type'] == JStatus.JURIDICAL:
        await msg.answer("Введите ваш ИНН. Например, 563565286576.")

    elif data['j_type'] == JStatus.PHYSICAL:
        await msg.answer("Введите ИНН вашей организации. Например, 6141027912.")


# принимает ИНН
@dp.message(StateFilter(UserState.USER_ADD_INN))
async def add_inn(msg: Message, state: FSMContext):
    data = await state.get_data()

    if not ut.is_valid_inn(msg.text, data['j_type']):
        await msg.answer("Неверный формат ИНН. Пожалуйста, введите корректный ИНН:")
        return

    await state.set_state(UserState.USER_ADD_INN)
    await state.update_data(data={'role': int(msg.text)})

    await msg.answer(
        text="Выберите свою роль:\n"
             "Рекламодатель - тот, кто заказывает и оплачивает рекламу.\n"
             "Рекламораспространитель - тот, кто распространяет рекламу на площадках, "
             "чтобы привлечь внимание к товару или услуге.\n\n"
             "Выберите свою роль",
        reply_markup=kb.get_select_role_kb()
    )


# Обработчик для выбора роли
@dp.callback_query(lambda cb: cb.data in ['advertiser', 'publisher'])
async def collect_role(cb: CallbackQuery, state: FSMContext):
    _, role = cb.data.split(':')

    data = await state.get_data()
    await state.clear()

    # Определяем rs_url только для юридических лиц и ИП
    rs_url = "https://example.com" if data['j_type'] == JStatus.JURIDICAL else None

    # Отправляем данные в ОРД
    response = await ord_api.send_to_ord(
        user_id=cb.from_user.id,
        name=data['name'],
        role=role,
        j_type=data['j_type'],
        inn=data['inn'],
        rs_url=rs_url
    )

    if response in [200, 201]:
        await cb.message.answer("Спасибо за регистрацию😉")
        await db.add_user(
            user_id=cb.from_user.id,
            full_name=cb.from_user.full_name,
            username=cb.from_user.username,
            role=role,
            inn=data['inn'],
            name=data['name'],
            j_type=data['j_type']
        )

        # handle_ord_response пока закомментил, используется только тут. Взял отправку сообщений
        if role == 'advertiser':
            # следующий шаг preloader_advertiser_entity
            pass
        elif role == 'publisher':
            # следующий шаг preloader_choose_platform
            pass
    else:
        await cb.message.answer("Произошла ошибка при регистрации в ОРД\n\n"
                                "Написать что произошла ошибка вывести данные. Мол попробуйте снова")


# пишет что функция в разработке
@dp.callback_query(lambda cb: cb.data == 'in_dev')
async def in_dev(cb: CallbackQuery):
    dp.answer_callback_query(cb.id, '🛠 Функция в разработке 🛠', show_alert=True)


# пишет что функция в разработке
@dp.callback_query(lambda cb: cb.data == CB.CLOSE.value)
async def close(cb: CallbackQuery, state: FSMContext):
    await state.clear()
#     тут команда старт
