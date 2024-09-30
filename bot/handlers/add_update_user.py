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
from .base import preloader_choose_platform, start_bot, preloader_advertiser_entity
from utils import ord_api
from enums import CB, JStatus, UserState, Role, Step


# Согласие с обработкой данных
@dp.callback_query(lambda cb: cb.data == CB.AGREE.value)
async def agree(cb: CallbackQuery):
    await cb.answer('Спасибо за согласие!')

    await cb.message.answer("Укажите свой правовой статус", reply_markup=kb.get_register_kb())


# Обработчик нажатий на кнопки подтверждения
@dp.callback_query(lambda cb: cb.data.startswith(CB.CONFIRM_USER.value))
async def confirmation(cb: CallbackQuery):
    await cb.message.answer("✅ Данные подтверждены. Вы можете продолжить работу с ботом.")


# Обработчик нажатий на кнопки подтверждения или смены роли
@dp.callback_query(lambda cb: cb.data.startswith(CB.CHANGE_ROLE.value))
async def select_role(cb: CallbackQuery):
    await cb.message.answer(
        text="Выберите свою роль:\n\n"
             "<b>Рекламодатель</b> - тот, кто заказывает и оплачивает рекламу.\n"
             "<b>Рекламораспространитель</b> - тот, кто распространяет рекламу на площадках, "
             "чтобы привлечь внимание к товару или услуге.\n\n"
             "Выберите свою роль",
        reply_markup=kb.get_select_role_kb()
    )


# Обработчик для сбора информации о пользователе
@dp.callback_query(lambda cb: cb.data.startswith(CB.RED_J_TYPE.value))
async def collect_info(cb: CallbackQuery, state: FSMContext):
    _, juridical_type = cb.data.split(':')

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
    await state.update_data(data={'name': msg.text, 'step': Step.INN.value})

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

    if data['step'] == Step.INN:
        if not ut.validate_inn(msg.text, j_type=data['j_type']):
            await msg.answer("❌ Неверный формат ИНН. Пожалуйста, введите корректный ИНН:")
            return

        # await state.set_state(UserState.USER_ADD_INN)
        await state.update_data(data={'inn': msg.text, 'step': Step.PHONE.value})
        await msg.answer('Введите ваш контактный номер телефона', reply_markup=kb.get_continue_btn_kb())

    elif data['step'] == Step.PHONE:
        await state.update_data(data={'phone': msg.text, 'step': Step.EMAIL.value})
        await msg.answer(
            text='Введите ваш адрес электронной почты\n\n'
                 'Адрес почты нужен для отправки чеков при оплате маркировки',
            reply_markup=kb.get_continue_btn_kb()
        )

    else:
        await state.update_data(data={'email': msg.text})

        await msg.answer(
            text="Выберите свою роль:\n\n"
                 "<b>Рекламодатель</b> - тот, кто заказывает и оплачивает рекламу.\n"
                 "<b>Рекламораспространитель</b> - тот, кто распространяет рекламу на площадках, "
                 "чтобы привлечь внимание к товару или услуге.\n\n"
                 "Выберите свою роль",
            reply_markup=kb.get_select_role_kb()
        )


# Пропускает ввод данных
@dp.callback_query(lambda cb: cb.data.startswith(CB.USER_CONTINUE.value))
async def collect_role(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if data['step'] == Step.PHONE:
        await state.update_data(data={'step': Step.EMAIL.value})
        await cb.message.answer(
            text='Введите ваш адрес электронной почты\n\n'
                 'Адрес почты нужен для отправки чеков при оплате маркировки',
            reply_markup=kb.get_continue_btn_kb()
        )

    else:
        await cb.message.answer(
            text="Выберите свою роль:\n\n"
                 "<b>Рекламодатель</b> - тот, кто заказывает и оплачивает рекламу.\n"
                 "<b>Рекламораспространитель</b> - тот, кто распространяет рекламу на площадках, "
                 "чтобы привлечь внимание к товару или услуге.\n\n"
                 "Выберите свою роль",
            reply_markup=kb.get_select_role_kb()
        )


# Обработчик для выбора роли CB.USER_SELECT_ROLE.value
@dp.callback_query(lambda cb: cb.data.startswith(CB.USER_SELECT_ROLE.value))
async def collect_role(cb: CallbackQuery, state: FSMContext):
    _, role = cb.data.split(':')

    data = await state.get_data()
    await state.clear()

    # for k, v in data.items():
    #     print(f'{k}: {v}')

    if not data:
        is_update = True

        text = f"✅ Роль успешно изменена на {dt.role_map.get(role)}"
        user_info = await db.get_user_info(cb.from_user.id)
        name = user_info.name
        j_type = user_info.j_type
        inn = user_info.inn
    else:
        is_update = False

        text = "Спасибо за регистрацию 😉"
        name = data['name']
        j_type = data['j_type']
        inn = data['inn']

    # Отправляем данные в ОРД
    response = await ord_api.send_user_to_ord(
        ord_id=cb.from_user.id,
        name=name,
        role=role,
        j_type=j_type,
        inn=inn,
        # rs_url=rs_url
    )

    if response in [200, 201]:
        await cb.message.answer(text)
        if is_update:
            await db.update_user(user_id=cb.from_user.id, role=role)

        else:
            await db.add_user(
                user_id=cb.from_user.id,
                full_name=cb.from_user.full_name,
                username=cb.from_user.username,
                role=role,
                inn=data['inn'],
                name=data['name'],
                j_type=data['j_type']
            )

        if role == Role.ADVERTISER:
            await preloader_advertiser_entity(cb.message)

        elif role == Role.PUBLISHER:
            await preloader_choose_platform(cb.message)

    else:
        await cb.message.answer("❗️ Произошла ошибка при регистрации в ОРД")
