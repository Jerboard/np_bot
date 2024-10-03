from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command as CommandFilter, StateFilter
from aiogram.fsm.context import FSMContext

import db
import keyboards as kb
from init import dp
import utils as ut
from .base import preloader_advertiser_entity, start_bot
from enums import CB, Command, UserState, JStatus, Role, Delimiter


# Добавление контрагента начало
@dp.message(CommandFilter(Command.COUNTERAGENT.value))
async def preloader_advertiser_entity_command(msg: Message, state: FSMContext):
    user = await db.get_user_info(msg.from_user.id)
    if user:
        await preloader_advertiser_entity(msg)
    else:
        await start_bot(msg, state)


@dp.callback_query(lambda cb: cb.data == CB.NO_ADVERTISER.value)
async def handle_no_advertiser(cb: CallbackQuery):
    await cb.message.answer(
        "Вы можете в любой момент продолжить добавление контрагента нажав на соответствующий пункт в меню"
    )


# создаём контрагента первый этап
@dp.callback_query(lambda cb: cb.data.startswith(CB.REGISTER_ADVERTISER_ENTITY.value))
async def register_advertiser_entity(cb: CallbackQuery):
    await cb.message.answer(
        "Укажите правовой статус вашего контрагента",
        reply_markup=kb.get_register_advertiser_entity_kb()
    )


# Обработчик для сбора информации о контрагентах
@dp.callback_query(lambda cb: cb.data.startswith(CB.ADD_ADVERTISER.value))
async def collect_advertiser_info(cb: CallbackQuery, state: FSMContext):
    _, j_type = cb.data.split(':')

    await state.set_state(UserState.ADD_ADVERTISER_NAME)
    await state.update_data(data={'j_type': j_type})

    if j_type == JStatus.IP:
        await cb.message.answer("Укажите фамилию, имя и отчество вашего контрагента. \nНапример, Иванов Иван Иванович.")
    elif j_type == JStatus.JURIDICAL:
        await cb.message.answer("Укажите название организации вашего контрагента. \nНапример, ООО ЮКЦ Партнер.")
    elif j_type == JStatus.PHYSICAL:
        await cb.message.answer("Укажите фамилию, имя и отчество вашего контрагента. \nНапример, Иванов Иван Иванович.")


# принимает имя контрагента
@dp.message(StateFilter(UserState.ADD_ADVERTISER_NAME))
async def add_advisor_name(msg: Message, state: FSMContext):
    await state.set_state(UserState.ADD_ADVERTISER_INN)
    await state.update_data(data={'name': msg.text})
    data = await state.get_data()

    if data['j_type'] == JStatus.IP:
        await msg.answer(
            "Введите ИНН вашего контрагента. Например, 563565286576. "
            "ИНН индивидуального предпринимателя совпадает с ИНН физического лица."
        )

    elif data['j_type'] == JStatus.PHYSICAL:
        await msg.answer("Введите ИНН вашего контрагента. Например, 563565286576.")

    elif data['j_type'] == JStatus.JURIDICAL:
        await msg.answer("Введите ИНН вашего контрагента. Например, 6141027912.")


# Обработчик для сбора ИНН контрагента
@dp.message(StateFilter(UserState.ADD_ADVERTISER_INN))
async def inn_collector_advertiser(msg: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    if not ut.validate_inn(msg.text, j_type=data['j_type']):
        await msg.answer(
            text="❌ Неверный формат ИНН. Пожалуйста, введите корректный ИНН:",
            reply_markup=kb.get_close_kb()
        )
        return

    user = await db.get_user_info(user_id=msg.from_user.id)
    if user.inn == msg.text:
        await msg.answer(
            text="❌ ИНН контрагента не должен совпадать с вашим",
            reply_markup=kb.get_close_kb()
        )
        return

    # Определение роли контрагента
    contractor_role = Role.ADVERTISER.value if user.role == Role.PUBLISHER.value else Role.PUBLISHER.value

    # if data['j_type'] == JStatus.JURIDICAL and user.role == Role.PUBLISHER:
    #     contractor_role = Role.ORS.value

    ord_id = ut.get_ord_id(msg.from_user.id, delimiter=Delimiter.U.value)

    response = await ut.send_user_to_ord(
        ord_id=ord_id,
        name=data['name'],
        role=contractor_role,
        j_type=data['j_type'],
        inn=msg.text
    )

    # Функция для обработки ответа от ОРД и дальнейшего выполнения кода для контрагента
    if response and response in [200, 201]:
        # async def add_campaign(user_id: int, contract_id: int, brand: str, service: str, links: list) -> int:
        await db.add_contractor(
            user_id=msg.from_user.id,
            name=data['name'],
            inn=msg.text,
            j_type=data['j_type'],
            ord_id=ord_id
        )
        await msg.answer(
            text="✅ Контрагент успешно добавлен!\nВы всегда можете добавить новых контрагентов позже.",
            reply_markup=kb.get_add_distributor_finish_kb()
        )
    else:
        await msg.answer(f"Сообщение при ошибки регистрации в орд")

        # перенёс
        # register_advertiser_entity(message)
        await msg.answer(
            "Укажите правовой статус вашего контрагента",
            reply_markup=kb.get_register_advertiser_entity_kb()
        )


# про
# Обработчик для кнопок после успешного добавления контрагента
@dp.callback_query(lambda cb: cb.data.startswith(CB.ADD_ANOTHER_DISTRIBUTOR.value))
async def handle_success_add_distributor(cb: CallbackQuery):
    await register_advertiser_entity(cb)


# Обработчик для кнопок после успешного добавления контрагента
@dp.callback_query(lambda cb: cb.data.startswith(CB.CONTINUE.value))
async def handle_success_add_distributor(cb: CallbackQuery):
    user = await db.get_user_info(cb.from_user.id)
    if user.role == Role.ADVERTISER:
        await cb.message.answer(
            "Перейти к созданию рекламной площадки?",
            reply_markup=kb.get_preloader_choose_platform_kb()
        )
    elif user.role == Role.PUBLISHER:
        await cb.message.answer("Теперь укажите информацию о договоре.")

