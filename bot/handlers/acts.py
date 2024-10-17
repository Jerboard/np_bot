from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command as CommandFilter, StateFilter
from aiogram.fsm.context import FSMContext
from datetime import datetime

import db
import keyboards as kb
from config import Config
from init import dp, bot
import utils as ut
from . import base
from enums import CB, Delimiter, UserState, Action, Step, Status


# Выбор страницы
@dp.callback_query(lambda cb: cb.data.startswith(CB.ACTS_SELECT_PAGE.value))
async def acts_select_page(cb: CallbackQuery, state: FSMContext):
    _, page_str, action = cb.data.split(':')
    page = int(page_str)

    data = await state.get_data()
    if action == Action.CONT:
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
        await state.set_state(UserState.ACTS)
        contract = await db.get_contract_full_data(page)

        serial = contract.serial if contract.serial else contract.contract_id
        await state.update_data(data={
            'contract_id': page,
            'step': Step.END_DATE,
            'serial': serial,
            'amount': contract.amount or 0,
            'end_date_str': datetime.now().date().strftime(Config.ord_date_form),
        })
        text = f'Вы завершаете работу по договору №{serial} сегодня?'
        await cb.message.answer(text=text, reply_markup=kb.get_check_next_step_act_kb())


async def ask_amount(user_id: int, serial: str, amount: int):
    text = (f'Сумма работ по договору №{serial} указана верно?\n'
            f'Сумма по договору: {amount:.2f} руб')
    await bot.send_message(chat_id=user_id, text=text, reply_markup=kb.get_check_next_step_act_kb())


# выбор шага
@dp.callback_query(lambda cb: cb.data.startswith(CB.ACT_NEXT_STEP_CHECK.value))
async def act_next_step_check(cb: CallbackQuery, state: FSMContext):
    _, action = cb.data.split(':')

    data = await state.get_data()

    if action == Action.NO:
        if data['step'] == Step.END_DATE:
            # await state.update_data(data={'step': Step.END_DATE})
            # text = f'Введите дату'
            # await bot.send_message(chat_id=user_id, text=text)
            await cb.message.answer(f'Введите дату')

        elif data['step'] == Step.SUM:
            # text = f'Введите сумму'
            # await bot.send_message(chat_id=user_id, text=text)
            await cb.message.answer(f'Введите сумму')

    else:
        if data['step'] == Step.END_DATE:
            await state.update_data(data={'step': Step.SUM})
            await ask_amount(user_id=cb.from_user.id, serial=data["serial"], amount=data["amount"] or 0)
            # text = (f'Сумма работ по договору №{data["serial"]} указана верно?\n'
            #         f'Сумма по договору: {data["amount"] or 0}')
            # await cb.message.answer(text=text, reply_markup=kb.get_check_next_step_act_kb())

        else:
            await base.end_act(user_id=cb.from_user.id, data=data)


# Обработка команды /acts
@dp.message(StateFilter(UserState.ACTS))
async def start_save_data(msg: Message, state: FSMContext):
    data = await state.get_data()

    if data['step'] == Step.END_DATE:
        date_str = ut.convert_date(msg.text)
        if not date_str:
            await msg.answer("❌ Неверный формат даты. Пожалуйста, введите дату в формате дд.мм.гггг:")
            return

        start_date = datetime.strptime(date_str, Config.ord_date_form).date()
        today = datetime.now().date()
        if start_date > today:
            await msg.answer("❌ Неверный формат даты.\n\n Дата окончания договора не должна быть больше сегодняшней")
            return

        await state.update_data(data={'end_date_str': date_str, 'end_date_input': msg.text, 'step': Step.SUM})
        await ask_amount(user_id=msg.from_user.id, serial=data["serial"], amount=data["amount"] or 0)
        # text = (f'Сумма работ по договору №{data["serial"]} указана верно?\n'
        #         f'Сумма по договору: {data["amount"] or 0}')
        # await msg.answer(text=text, reply_markup=kb.get_check_next_step_act_kb())

    # elif data['step'] == Step.SUM:
    else:
        if not ut.is_float(msg.text):
            await msg.answer("❌ Неверный формат суммы.\n\n Введите сумму цифрами")
            return

        await state.update_data(data={'amount': float(msg.text)})
        data = await state.get_data()
        await base.end_act(user_id=msg.from_user.id, data=data)


'''
page: 0
active_contracts: [(1, datetime.date(2024, 9, 11), datetime.date(2024, 11, 24), 'fg596', 100500.0, 'Закатный Василий Кузьмич'), (2, datetime.date(2024, 9, 10), None, '945532665', 150000.0, 'Закатный Василий Кузьмич')]
message_id: 6545
contract_id: 2
step: Step.SUM
serial: 945532665
amount: 2000000.0
end_date_str: 2024-10-12
'''


# отправка данных в орд
@dp.callback_query(lambda cb: cb.data.startswith(CB.ACT_SEND.value))
async def acts_send(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    # ut.print_dict(data, 'act_data')

    ord_id = ut.get_ord_id(cb.from_user.id, Delimiter.I.value)

    contract = await db.get_contract_full_data(data['contract_id'])

    user_info = await db.get_user_info(user_id=cb.from_user.id)
    contractor = await db.get_contractor(contractor_id=contract.contractor_id)

    campaigns = await db.get_user_campaigns(contract_id=data['contract_id'])
    creatives = []
    for campaign in campaigns:
        # campaign_creatives = await db.get_creative_full_data(campaign_id=campaign.id)
        campaign_creatives = await db.get_creatives(campaign_id=campaign.id)
        # print(f'campaign_creatives: {len(campaign_creatives)} campaign.id: {campaign.id}')
        creatives = creatives + campaign_creatives

    cash_platforms = {}
    creative_data = []
    for creative in creatives:
        creative: db.CreativeRow

        creative_platforms = []
        statistics = await db.get_statistics(creative_id=creative.id)
        for statistic in statistics:
            platform: db.PlatformRow = cash_platforms.get(statistic.platform_id)
            if not platform:
                platform: db.PlatformRow = await db.get_platform(platform_id=statistic.platform_id)
                cash_platforms[statistic.platform_id] = platform

            creative_platforms.append(
                {
                    "pad_external_id": platform.ord_id,
                    "shows_count": statistic.views,
                    "invoice_shows_count": 0,
                    "amount": "0",
                    "amount_per_event": "0",
                    "date_start_planned": creative.created_at.date().strftime(Config.ord_date_form),
                    "date_start_actual": creative.created_at.date().strftime(Config.ord_date_form),
                    "date_end_planned": data['end_date_str'],
                    "date_end_actual": data['end_date_str'],
                    "pay_type": "other"
                }
            )

        creative_data.append({
              "creative_external_id": creative.ord_id,
              "platforms": creative_platforms,
            }
        )

    act_data = {
      "contract_external_id": contract.contract_ord_id,
      "date": data['end_date_str'],
      "serial": str(data['serial']),
      "date_start": contract.contract_date.strftime(Config.ord_date_form),
      "date_end": data['end_date_str'],
      "amount": f'{data["amount"]:.2f}',
      "flags": [
        "vat_included"
      ],
      "client_role": user_info.role,
      "contractor_role": contractor.role,
      "items": [
        {
          "contract_external_id": contract.contract_ord_id,
          "amount": f'{data["amount"]:.2f}',
          "flags": [
            "vat_included"
          ],
          "creatives": creative_data
        }
      ]
    }

    is_suc = await ut.send_acts_to_ord(ord_id=ord_id, act_data=act_data)

    if not is_suc:
        await cb.message.answer("❌ Акт не был отправлен\n\n"
                                "Проверьте данные. При повторении ошибки обратитесь в поддержку")
        return

    await cb.message.answer("✅ Данные об акте успешно отправлены в ОРД")

    # переводим в статус неактивно
    await db.update_contract(contract_id=data['contract_id'], status=Status.INACTIVE.value, act_ord_id=ord_id)
    await db.update_campaign(contract_id=contract.contract_id, status=Status.INACTIVE.value)
    for campaign in campaigns:
        await db.update_creative(campaign_id=campaign.id, status=Status.INACTIVE.value)



