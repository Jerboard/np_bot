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
from .base import start_contract, start_bot, end_contract, start_campaign_base
from enums import CB, Command, UserState, JStatus, Role, AddContractStep, Delimiter


# Обработчик для команды /start_contract
# перенёс функцию в base поменял название, чтоб не совпадали
@dp.message(CommandFilter(Command.START_CONTRACT.value))
async def start_contract_hnd(msg: Message, state: FSMContext):
    user = await db.get_user_info(msg.from_user.id)
    if user:
        await start_contract(msg)
    else:
        await start_bot(msg, state)


# возвращает к старту контракта
@dp.callback_query(lambda cb: cb.data.startswith(CB.CONTRACT_BACK))
async def start_contract_hnd(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await start_contract(cb.message, user_id=cb.from_user.id)


# Обработчик выбора контрагента
@dp.callback_query(lambda cb: cb.data.startswith(CB.CONTRACT_DIST_SELECT))
async def process_contract_start_date(cb: CallbackQuery, state: FSMContext):
    _, dist_id_str = cb.data.split(':')

    await state.clear()
    await state.set_state(UserState.ADD_CONTRACT)
    await state.update_data(data={
        'step': AddContractStep.START_DATE.value,
        'dist_id': int(dist_id_str)
    })
    await cb.message.answer(
        text="Введите дату начала договора (дд.мм.гггг или гггг-мм-дд):",
        reply_markup=kb.get_close_kb()
    )


# Обработчик для обработки даты начала договора
@dp.message(StateFilter(UserState.ADD_CONTRACT))
async def process_contract_start_date(msg: Message, state: FSMContext):
    data = await state.get_data()
    error_text = ''

    if data['step'] == AddContractStep.START_DATE.value:
        date_str = ut.convert_date(msg.text)
        if date_str:
            await state.update_data(data={
                'step': AddContractStep.END_DATE.value,
                'start_date': date_str,
                'input_start_date': msg.text,
            })
            await msg.answer(
                "Указана ли в договоре дата завершения?",
                reply_markup=kb.get_check_next_step_contract_kb(AddContractStep.END_DATE.value)
            )
        else:
            error_text = '❌ Неверный формат даты. Пожалуйста, введите дату в формате дд.мм.гггг:'

    elif data['step'] == AddContractStep.END_DATE.value:
        date_str = ut.convert_date(msg.text)
        if date_str:
            await state.update_data(data={
                'step': AddContractStep.NUM.value,
                'end_date': date_str,
                'input_end_date': msg.text
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
                'step': AddContractStep.SUM.value,
                'sum': float(msg.text)
            })
            await end_contract(state=state, chat_id=msg.chat.id)
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
            await end_contract(state=state, chat_id=cb.message.chat.id)

        else:
            await state.clear()
            await cb.message.answer("❗️Что-то сломалось. Перезапустите бот \n\n/start")


# Обработчик для выбора НДС
@dp.callback_query(lambda cb: cb.data.startswith(CB.CONTRACT_END.value))
async def handle_vat_selection(cb: CallbackQuery, state: FSMContext):

    user = await db.get_user_info(cb.from_user.id)
    data = await state.get_data()
    await state.clear()

    # for k, v in data.items():
    #     print(f'{k}: {v}')

    ord_id = ut.get_ord_id(cb.from_user.id, delimiter=Delimiter.C.value)

    contractor = await db.get_contractor(contractor_id=data['dist_id'])
    if user.role == Role.ADVERTISER:
        client_external_id = f"{cb.from_user.id}"
        contractor_external_id = contractor.ord_id
    else:
        client_external_id = contractor.ord_id
        contractor_external_id = f"{cb.from_user.id}"

    response = await ut.send_contract_to_ord(
        ord_id=ord_id,
        client_external_id=client_external_id,
        contractor_external_id=contractor_external_id,
        contract_date=data.get('start_date'),
        serial=data.get('num'),
        # vat_flag=vat_flag,
        amount=data.get('sum')
    )

    if response:
        start_date = datetime.strptime(data['start_date'], Config.ord_date_form) if data.get('start_date') else None
        end_date = datetime.strptime(data['end_date'], Config.ord_date_form) if data.get('end_date') else None
        contract_id = await db.add_contract(
            user_id=cb.from_user.id,
            contractor_id=data['dist_id'],
            start_date=start_date,
            # vat_code=vat,
            ord_id=ord_id,
            end_date=end_date,
            serial=data.get('num'),
            amount=data.get('sum'),
        )
        await cb.message.answer("Договор успешно зарегистрирован в ОРД.")
        await start_campaign_base(msg=cb.message, state=state, user_id=cb.from_user.id, contract_id=contract_id)

        #     добавил чтоб не было кругового импорта
        # await cb.message.answer("Введите название бренда, который вы планируете рекламировать.")
        # ask_for_brand(chat_id)
    else:
        await cb.message.answer("Произошла ошибка при регистрации договора в ОРД.")
        # logging.error(f"Error registering contract in ORD: {response}")






# else:
#     await message.answer("Произошла ошибка. Данные о договоре не найдены.")
#     logging.error(
#         f"Contract data not found for chat_id: {chat_id}, contractor_id: {contractor_id}, ord_id: {ord_id}")
