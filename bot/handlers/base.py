from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from asyncio import sleep
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta

import db
import data as dt
import keyboards as kb
import utils as ut
from config import Config
from init import dp, log_error, bot, scheduler
from utils import ord_api
from enums import CB, JStatus, UserState, Step, Delimiter, Role


# стартовый экран
async def start_bot(
        msg: Message,
        state: FSMContext,
        user: db.UserRow = None,
        referrer: int = None,
        edit_text: bool = False
):
    await state.clear()
    if not user:
        user = await db.get_user_info(msg.from_user.id)

    # обновляем данные пользователя
    await db.add_user(
        user_id=msg.from_user.id,
        full_name=msg.from_user.full_name,
        username=msg.from_user.username,
        referrer=referrer,
    )

    if user and user.in_ord:
        saved_cards = await db.get_user_card(user_id=user.user_id)

        # Если пользователь найден в базе данных, выводим информацию о нем
        if user.j_type == JStatus.JURIDICAL:
            name_label = f'Название организации: {user.name}\nОтветственный: {user.fio}\n'
        else:
            name_label = f'ФИО: <b>{user.name}</b>\n'

        text = (f"Информация о вас:\n\n"
                f"{name_label}"
                f"ИНН: <b>{user.inn}</b>\n"
                f"Правовой статус: <b>{dt.juridical_type_map.get(user.j_type, user.j_type)}</b>\n"
                f"Текущая роль: <b>{dt.role_map.get(user.role, user.role)}</b>\n\n"
                f"Вы можете изменить свои данные и роль.\n\n"
                f"Реферальная ссылка:\n"
                f"<code>{Config.bot_link}?start={user.ref_code}</code>\n\n"
                f"Чтобы воспользоваться функционалом бота - нажмите на синюю кнопку меню и выберите действие.\n\n")

        if edit_text:
            await msg.edit_text(text, reply_markup=kb.get_start_kb(with_card=len(saved_cards) > 0))
        else:
            await msg.answer(text, reply_markup=kb.get_start_kb(with_card=len(saved_cards) > 0))

    else:
        # Если пользователь не найден в базе данных, предлагаем согласиться с офертой
        await msg.answer(dt.start_text, reply_markup=kb.get_agree_button(), disable_web_page_preview=True)


async def preloader_advertiser_entity(message: Message):
    await message.answer("Перейти к созданию контрагента?", reply_markup=kb.get_preloader_advertiser_entity_kb())


async def start_contract(
        msg: Message,
        user_id: int = None,
        selected_contractor: int = None,
        state: FSMContext = None
):
    if selected_contractor:
        await msg.answer(f"Выбранный ранее контрагент будет использован: № {selected_contractor}")
        await msg.answer("Введите дату начала договора (дд.мм.гггг):")
        if state:
            await state.set_state(UserState.ADD_CONTRACT)
            await state.update_data(data={
                'step': Step.START_DATE.value,
                'dist_id': selected_contractor
            })

    else:
        if not user_id:
            user_id = msg.from_user.id

        contractors = await db.get_all_contractors(user_id)
        await msg.answer("Контрагент не был выбран. Пожалуйста, выберите контрагента.")
        if contractors:
            await msg.answer("Выберите контрагента\n"
                             "(Контрагент - это другая сторона вашего договора)",
                             reply_markup=kb.get_select_distributor_kb(contractors))

        else:
            await msg.answer(text=f"❗️У вас нет контрагентов.")
            await preloader_advertiser_entity(msg)


async def end_contract(state: FSMContext, chat_id: int):
    data = await state.get_data()

    contractor = await db.get_contractor(contractor_id=data['dist_id'])
    await state.update_data(data={'contractor_ord_id': contractor.ord_id})

    amount = f'{data["sum"]:.2f} руб' if data.get('sum') else 'нет'
    text = (
        f'❕ Проверьте, правильно ли указана информация по вашему договору с рекламодателем:\n\n'
        f'<b>Контрагент:</b> {contractor.name}\n'
        f'<b>Дата заключения договора:</b> {data["input_start_date"]}\n'
        f'<b>Номер договора:</b> {data.get("num", "нет")}\n'
        f'<b>Сумма договора:</b> {amount}\n'
        f'<b>Дата завершения договора:</b> {data.get("input_end_date", "нет")}'
    )
    await bot.send_message(chat_id=chat_id, text=text, reply_markup=kb.get_contract_end_kb(data['dist_id']))


# старт оплаты
# async def ask_amount(message: Message):
#     chat_id = message.chat.id
#     balance = db.query_db('SELECT balance FROM users WHERE chat_id = ?', (chat_id,), one=True)
#     if balance:
#         balance_amount = balance[0]
#         msg = message.answer(
#             f"На вашем балансе {balance_amount} рублей. \n\n "
#             f"Введите сумму, на которую хотите пополнить баланс. \n\n "
#             f"Стоимость маркировки одного креатива составляет 400 рублей."
#         )
#         # dp.register_next_step(msg, cf.process_amount)
#     else:
#         await message.answer("Ошибка: не удалось получить ваш баланс. Пожалуйста, попробуйте позже.")


async def preloader_choose_platform(message: Message):
    await message.answer(
        text="Перейти к созданию рекламной площадки?",
        reply_markup=kb.get_preloader_choose_platform_kb()
    )


# Функция для завершения процесса добавления данных платформы
async def finalize_platform_data(msg: Message, state: FSMContext, user_id: int = None):
    if not user_id:
        user_id = msg.from_user.id

    data = await state.get_data()
    await state.clear()

    ord_id = ut.get_ord_id(user_id, delimiter='-p-')
    response = await ut.send_platform_to_ord(
        ord_id=ord_id,
        platform_name=data['platform_name'],
        platform_url=data['platform_url'],
        dist_ord_id=data['dist_id']
    )
    if response in [200, 201]:
        await db.add_platform(
            user_id=user_id,
            name=data['platform_name'],
            url=data['platform_url'],
            average_views=data['view'],
            ord_id=ord_id,
        )

        await msg.answer(
            text="Площадка успешно зарегистрирована в ОРД.\n\nДобавить новую площадку или продолжить?",
            reply_markup=kb.get_finalize_platform_data_kb()
        )

    else:
        await msg.answer(f"Сообщение при ошибки регистрации в орд", reply_markup=kb.get_help_button())


async def select_contract(
        contracts: list[db.ContractDistRow],
        current: int,
        chat_id: int,
        message_id: int = None,
):
    contract = contracts[current]

    text = (
        f'{current + 1}/{len(contracts)}:\n\n'
        f'Контрагент: {contract.name}\n'
        f'Дата заключения договора: {contract.contract_date}\n'
        f'Номер договора: {contract.serial}\n'
        f'Сумма договора: {contract.amount} руб\n'
        f'Дата завершения договора: {contract.end_date}'
    ).replace('None', 'нет')

    keyboard = kb.get_select_page_kb(
        end_page=(current + 1) == len(contracts),
        select_id=contract.contract_id,
        page=current
    )

    if message_id:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=keyboard)
    else:
        await bot.send_message(chat_id, text, reply_markup=keyboard)


async def start_campaign_base(msg: Message, state: FSMContext, contract_id: int = None, user_id: int = None):
    await state.clear()

    if contract_id:
        await state.set_state(UserState.ADD_CAMPAIGN_BRAND)
        await state.update_data(data={'contract_id': contract_id})
        await msg.answer("Введите название бренда, который вы планируете рекламировать.\n\nУкажите бренд.")

    else:
        if not user_id:
            user_id = msg.from_user.id
        contracts = await db.get_all_user_contracts(user_id)
        await state.update_data(data={'contracts': contracts, 'current': 0})

        if contracts:
            await select_contract(
                contracts=contracts,
                current=0,
                chat_id=user_id,
            )
        else:
            await msg.answer('У вас нет контрактов')
            await start_contract(msg=msg, user_id=user_id)


# Начало процесса добавления креатива
async def add_creative_start(msg: Message, state: FSMContext, campaign_id: int):
    await state.set_state(UserState.ADD_CREATIVE)
    await state.update_data(data={'campaign_id': campaign_id})

    await msg.answer(
        "Загрузите файл своего рекламного креатива или введите текст. "
        "Вы можете загрузить несколько файлов для одного креатива."
    )


async def creative_upload(msg: Message, state: FSMContext):
    # Попробовать с медиагруппой
    if msg.content_type in ['text', 'photo', 'video', 'audio', 'voice']:
        if msg.video and msg.video.file_size >= 50000000:
            await msg.answer(f'❌ Слишком большое видео. Размер видео не должен быть больше 50 МВ ')
            return

        current_state = await state.get_state()
        if not current_state:
            campaigns = await db.get_user_campaigns(user_id=msg.from_user.id)
            if not campaigns:
                await msg.answer(
                    "❌ У вас нет активных рекламных кампаний. Пожалуйста, создайте кампанию перед добавлением креатива."
                )
                await state.clear()
                await start_campaign_base(msg=msg, state=state)
                return

            await state.set_state(UserState.ADD_CREATIVE)
            await state.update_data(data={'campaigns': campaigns})

        data = await state.get_data()

        creative = {
            'content_type': msg.content_type,
            'file_id': ut.get_file_id(msg)
        }

        # сохраняем текст, если есть
        creative_text = msg.text or msg.caption
        if creative_text:
            tests = data.get('text', [])
            tests.append(creative_text)
            await state.update_data(data={'text': tests})

        creatives = data.get('creatives', [])
        creatives.append(creative)
        await state.update_data(data={'creatives': creatives})

        message_id = data.get('message_id')
        if message_id:
            try:
                await bot.delete_message(chat_id=msg.chat.id, message_id=message_id)
            except:
                pass

        sent = await msg.answer(
            '✅ Креатив успешно добавлен\n\n'
            'Чтобы добавить еще файл или текст для этого креатива просто отправьте его сообщением или '
            'нажмите "Продолжить", чтобы получить токен.',
            reply_markup=kb.get_select_campaigns_kb()
        )
        await state.update_data(data={'message_id': sent.message_id})
    else:
        sent = await msg.answer("❌ Ошибка. Пожалуйста, попробуйте еще раз и пришлите креатив.")
        await sleep(3)
        await sent.delete()


async def register_creative(data: dict, user_id: int, del_msg_id: int, state: FSMContext):
    creatives: list[dict] = data.get('creatives', [])
    creative_texts: list[str] = data.get('text', [])

    # ut.print_dict(data, '>>creative data')

    creative_ord_id = ut.get_ord_id(user_id, delimiter=Delimiter.CR.value)

    campaign = await db.get_campaign(data['campaign_id'])
    contract = await db.get_contract(campaign.contract_id)
    user = await db.get_user_info(user_id)

    # определяем тип рекламы
    creative_form = ut.ident_creative_form(creatives)
    # print(f'creative_form: {creative_form} {creative_form[:4]} {not creative_texts} {creative_texts}')
    if creative_form[:4] == 'text' and not creative_texts:
        creative_texts.append(campaign.service)

    if user.role == Role.ADVERTISER:
        contractor_name = user.name
        contractor_inn = user.inn
    else:
        contractor_info = await db.get_contractor(contract.contractor_id)
        contractor_name = contractor_info.name
        contractor_inn = contractor_info.inn

    media_ord_ids = await ut.save_media_ord(
        creatives=creatives,
        creative_ord_id=creative_ord_id,
        user_id=user_id,
        descriptions=campaign.service
    )

    response = await ut.send_creative_to_ord(
        creative_id=creative_ord_id,
        brand=campaign.brand,
        creative_name=f'{contractor_name}',
        creative_text=creative_texts,
        description=campaign.service,
        media_ids=media_ord_ids,
        contract_ord_id=contract.ord_id,
        creative_form=creative_form,
        target_urls=campaign.links,
    )
    # log_error(f'response: {response}', wt=False)
    erid = response.get('erid') if response else None
    if not erid:
        await bot.send_message(chat_id=user_id, text="Сообщение при ошибки регистрации в орд", reply_markup=kb.get_help_button())
        # тут ещё возврат денег
        ut.refund_payment(data['pay_id'])
        return

    creative_id = await db.add_creative(
        user_id=user_id,
        campaign_id=campaign.id,
        texts=data.get('text', []),
        token=erid,
        ord_id=creative_ord_id,
    )

    text = (f'Креатив успешно промаркирован.\n'
            f'Ваш токен - <code>{erid}</code>.\n'
            f'<code>Реклама. {contractor_name}. ИНН: {contractor_inn}. erid: {erid}</code>. \n'
            f'<i>(нажмите на текст, чтобы скопировать)</i>\n\n'
            f'Теперь прикрепите маркировку к вашему креативу, опубликуйте и пришлите ссылку на него. \n'
            f'Если вы публикуете один креатив на разных площадках - пришлите ссылку на каждую площадку. \n'
            )

    # Создаем задание с триггером на определённую дату
    trigger_time = datetime.now() + timedelta(hours=1)
    # trigger_time = datetime.now() + timedelta(minutes=1)
    scheduler.add_job(ut.check_post_link, DateTrigger(run_date=trigger_time), args=[creative_id, user_id])

    await bot.delete_message(chat_id=user_id, message_id=del_msg_id)
    await bot.send_message(chat_id=user_id, text=text, reply_markup=kb.get_end_creative_kb(creative_id))

    # подача акта

    '''
    В акте указываем:
- номер акта: [последовательные числа, можно как [Номер договора / 1]]
- роль заказчика: [зависит от роли клиента - рекламодатель или рекламораспространитель]
- роль исполнителя: [агентство]
- дата выставления: [дата оплаты]
- дата начала периода: [дата оплаты]
- дата окончания периода: [дата оплаты]
- сумма: [400 рублей]
    '''

    agency_contract = await db.get_agency_contract(user_id=user_id)
    user_info = await db.get_user_info(user_id=user_id)
    data_str = datetime.now().strftime(Config.ord_date_form)
    act_data = {
        "contract_external_id": agency_contract.ord_id,
        "date": data_str,
        # "serial": ut.get_ord_id(creative_ord_id),
        "date_start": data_str,
        "date_end": data_str,
        "amount": f'{Config.service_price:.2f}',
        "flags": [
            "vat_included"
        ],
        "client_role": user_info.role,
        "contractor_role": Role.AGENCY.value,
        "items": [
            {
                "contract_external_id": agency_contract.ord_id,
                "amount": f'{Config.service_price:.2f}',
                "flags": [
                    "vat_included"
                ],
                # "creatives": []
            }
        ]
    }

    is_suc = await ut.send_acts_to_ord(
        ord_id=ut.get_ord_id(Config.partner_data['inn'], Delimiter.I.value),
        act_data=act_data
    )
    print(f'act: {is_suc}')


# выбор креатива для подачи статистики
async def start_statistic(
        user_id: int,
        active_creatives: list[db.CreativeFullRow],
        sending_list: list[int],
        state: FSMContext,
        page: int = 0,
        message_id: int = 0,
):
    # if not state:
    #     state = FSMContext
    #     await state.set_state(UserState.SEND_STATISTIC)
    #     await state.update_data(data={'page': 0, 'active_creatives': active_creatives, 'sending_list': []})

    text = (f'Отправьте количество просмотров по креативу:\n\n'
            f'{active_creatives[page].url}')

    if page in sending_list:
        text += '\n\n✅ Вы уже отправили статистику по этому креативу'

    keyboard = kb.get_select_page_kb(
        end_page=(page + 1) == len(active_creatives),
        select_id=active_creatives[page].statistic_id,
        page=page,
        cb=CB.STATISTIC_SELECT_PAGE.value,
        with_select_btn=False
    )

    if message_id:
        try:
            await bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=text,
                reply_markup=keyboard
            )
        except Exception as ex:
            pass
    else:
        sent = await bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard)
        await state.update_data(data={'message_id': sent.message_id})


# выбор контракта для отправки акта
async def start_acts(
        user_id: int,
        active_contracts: list[db.ContractDistRow],
        state: FSMContext,
        page: int = 0,
        message_id: int = 0,
):
    contract: db.ContractDistRow = active_contracts[page]
    serial = contract.serial if contract.serial else contract.contract_id
    amount = f'{contract.amount:.2f} руб' if contract.amount else 'нет'
    text = (f'Выберите договор, чтобы подать информацию об акте выполненных работ.\n\n'
            f'{serial}\n'
            f'{contract.name}\n'
            f'{contract.contract_date.strftime(Config.date_form)}\n'
            f'{amount}\n')

    keyboard = kb.get_select_page_kb(
        end_page=(page + 1) == len(active_contracts),
        select_id=contract.contract_id,
        page=page,
        cb=CB.ACTS_SELECT_PAGE.value
    )

    if message_id:
        try:
            await bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=text,
                reply_markup=keyboard
            )
        except Exception as ex:
            pass
    else:
        sent = await bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard)
        await state.update_data(data={'message_id': sent.message_id})


# завершение акта
async def end_act(user_id: int, data: dict):
    contract = await db.get_contract_full_data(data['contract_id'])

    serial = contract.serial if contract.serial else contract.contract_id
    amount = f'{contract.amount:.2f} руб' if contract.amount else data.get('amount', 0)
    act_date = data.get('end_date_input') or datetime.now().date().strftime(Config.date_form)
    text = (f'Проверьте правильно ли указана информация:\n\n'
            f'Договор №{serial}\n'
            f'Контрагент: {contract.name}\n'
            f'Дата договора {contract.contract_date.strftime(Config.date_form)}\n'
            f'Сумма по договору: {contract.amount or "нет"}\n'
            f'Дата акта: {act_date}\n'
            f'Сумма акта: {amount}\n')

    await bot.send_message(chat_id=user_id, text=text, reply_markup=kb.get_end_act_kb(data['contract_id']))
