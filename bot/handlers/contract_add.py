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
from .base import start_contract
from enums import CB, Command, UserState, JStatus, Role, AddContractStep


### Добавление договоров ####
# Обработчик для команды /start_contract
# перенёс функцию в base поменял название, чтоб не совпадали
@dp.message(CommandFilter(Command.START_CONTRACT.value))
async def start_contract_hnd(message: Message):
    await start_contract(message)


# Обработчик выбора контрагента
@dp.callback_query(lambda cb: cb.data.startswith(CB.CONTRACT_DIST_SELECT))
async def process_contract_start_date(cb: CallbackQuery, state: FSMContext):
    _, dist_id_str = cb.data.split(':')

    await state.set_state(UserState.ADD_CONTRACT)
    await state.update_data(data={
        'step': AddContractStep.START_DATE.value,
        'dist_id': int(dist_id_str)
    })
    await cb.message.answer("Введите дату начала договора (дд.мм.гггг):", reply_markup=kb.get_close_kb())


# Обработчик для обработки даты начала договора
@dp.message(StateFilter(UserState.ADD_CONTRACT))
async def process_contract_start_date(msg: Message, state: FSMContext):
    data = await state.get_data()
    error_text = ''

    if data['step'] == AddContractStep.START_DATE.value:
        if ut.is_valid_date(msg.text):
            await state.update_data(data={
                'step': AddContractStep.END_DATE.value,
                'start_date': msg.text
            })
            await msg.answer(
                "Указана ли в договоре дата завершения?",
                reply_markup=kb.get_check_next_step_contract_kb(AddContractStep.END_DATE.value)
            )
        else:
            error_text = '❌ Неверный формат даты. Пожалуйста, введите дату в формате дд.мм.гггг:'

    elif data['step'] == AddContractStep.END_DATE.value:
        if ut.is_valid_date(msg.text):
            await state.update_data(data={
                'step': AddContractStep.NUM.value,
                'end_date': msg.text
            })

            await msg.answer(
                "Есть ли номер у вашего договора?",
                reply_markup=kb.get_check_next_step_contract_kb(AddContractStep.NUM.value)
            )

        else:
            error_text = '❌ Неверный формат даты. Пожалуйста, введите дату в формате дд.мм.гггг:'

    elif data['step'] == AddContractStep.NUM.value:
        await state.update_data(data={
            'step': AddContractStep.SUM.value,
            'num': msg.text
        })
        await msg.answer(
            "Указана ли в договоре сумма?",
            reply_markup=kb.get_check_next_step_contract_kb(AddContractStep.SUM.value)
        )

    elif data['step'] == AddContractStep.SUM.value:
        if ut.is_float(msg.text):
            await state.update_data(data={
                'sum': float(msg.text)
            })
            await msg.answer(
                "Сумма по договору указана с НДС?",
                reply_markup=kb.get_nds_kb()
            )
        else:
            error_text = '❌ Неверный формат сумму. Пожалуйста, отправьте сумму числом'
    else:
        await state.clear()
        await msg.answer("❗️Что-то сломалось. Перезапустите бот \n\n/start")
        return 
    
    if error_text:
        sent = await msg.answer(error_text)
        await sleep(3)
        await sent.delete()


# следующий шаг
@dp.callback_query(lambda cb: cb.data.startswith('add_contract_next_step_check'))
async def add_contract_next_step_check(cb: CallbackQuery, state: FSMContext):
    _, step, answer_str = cb.data.split(':')
    answer = bool(int(answer_str))

    if answer:
        if step == AddContractStep.END_DATE:
            await cb.message.answer("Введите дату завершения договора (дд.мм.гггг):")

        elif step == AddContractStep.NUM:
            await cb.message.answer("Введите номер договора:")

        elif step == AddContractStep.SUM:
            await cb.message.answer("Введите сумму договора:")

        else:
            await cb.message.answer("❗️Что-то сломалось. Перезапустите бот \n\n/start")

    else:
        if step == AddContractStep.END_DATE:
            await state.update_data(data={'step': AddContractStep.NUM.value})
            await cb.message.answer(
                "Есть ли номер у вашего договора?",
                reply_markup=kb.get_check_next_step_contract_kb(AddContractStep.NUM.value)
            )

        elif step == AddContractStep.NUM:
            await state.update_data(data={'step': AddContractStep.SUM.value})
            await cb.message.answer(
                "Указана ли в договоре сумма?",
                reply_markup=kb.get_check_next_step_contract_kb(AddContractStep.SUM.value)
            )

        elif step == AddContractStep.SUM:
            await cb.message.answer(
                "Сумма по договору указана с НДС?",
                reply_markup=kb.get_nds_kb()
            )

        else:
            await state.clear()
            await cb.message.answer("❗️Что-то сломалось. Перезапустите бот \n\n/start")


# Обработчик для выбора НДС
@dp.callback_query(lambda cb: cb.data.startswith(CB.CONTRACT_VAT.value))
async def handle_vat_selection(cb: CallbackQuery, state: FSMContext):
    _, vat_str = cb.data.split(':')
    vat = int(vat_str)

    user = await db.get_user_info(cb.from_user.id)
    
    data = await state.get_data()
    await state.clear()

    ord_id = ut.get_ord_id(cb.from_user.id)
   
    vat_flag = ["vat_included"] if vat == 4 else []
    if user.role == Role.ADVERTISER:
        client_external_id = f"{cb.from_user.id}"
        contractor_external_id = f"{cb.from_user.id}.{data['dist_id']}"
    else:
        client_external_id = f"{cb.from_user.id}.{data['dist_id']}"
        contractor_external_id = f"{cb.from_user.id}"

    response = ut.send_contract_to_ord(
        ord_id=ord_id,
        client_external_id=client_external_id,
        contractor_external_id=contractor_external_id,
        contract_date=data.get('start_date'),
        serial=data.get('num'),
        vat_flag=vat_flag,
        amount=data.get('sum', 0)
    )
    if response:
        await db.add_contract(
            user_id=cb.from_user.id,
            contractor_id=data['dist_id'],
            contract_date=data['start_date'],
            vat_code=vat,
            ord_id=ord_id,
            end_date=data.get('end_date'),
            serial=data.get('num'),
            amount=data.get('sum'),
        )
        await cb.message.answer("Договор успешно зарегистрирован в ОРД.")
        # start_campaign(message)

        #     добавил чтоб не было кругового импорта
        await cb.message.answer("Введите название бренда, который вы планируете рекламировать.")
        # ask_for_brand(chat_id)
    else:
        await cb.message.answer("Произошла ошибка при регистрации договора в ОРД.")
        # logging.error(f"Error registering contract in ORD: {response}")

# else:
#     await message.answer("Произошла ошибка. Данные о договоре не найдены.")
#     logging.error(
#         f"Contract data not found for chat_id: {chat_id}, contractor_id: {contractor_id}, ord_id: {ord_id}")
