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
from utils import ord_api
from enums import CB, JStatus, UserState, Command, Delimiter, Role


# стартовый экран
async def start_bot(msg: Message, state: FSMContext, user: db.UserRow = None):
    await state.clear()
    if not user:
        user = await db.get_user_info(msg.from_user.id)

    if user:
        # Если пользователь найден в базе данных, выводим информацию о нем
        name_label = "ФИО" if user.j_type != JStatus.JURIDICAL else "Название организации"

        text = (f"Информация о вас:\n\n"
                f"{name_label}: <b>{msg.from_user.first_name}</b>\n"
                f"ИНН: <b>{user.inn}</b>\n"
                f"Правовой статус: <b>{dt.juridical_type_map.get(user.j_type, user.j_type)}</b>\n"
                f"Баланс: <b>{user.balance} рублей</b>\n"
                f"Текущая роль: <b>{dt.role_map.get(user.role, user.role)}</b>\n\n"
                "Вы можете изменить свои данные и роль.\n\n"
                "Чтобы воспользоваться функционалом бота - нажмите на синюю кнопку меню и выберите действие.\n\n")
        await msg.answer(text, reply_markup=kb.get_start_kb())

        # обновляем данные пользователя
        if msg.from_user.full_name != user.full_name or msg.from_user.username != user.username:
            await db.add_user(user_id=msg.from_user.id, full_name=msg.from_user.full_name, username=msg.from_user.username)

    else:
        # Если пользователь не найден в базе данных, предлагаем согласиться с офертой
        await msg.answer(dt.start_text, reply_markup=kb.get_agree_button(), disable_web_page_preview=True)


async def start_contract(msg: Message, user_id: int = None, selected_contractor: int = None):
    if selected_contractor:
        await msg.answer(f"Выбранный ранее контрагент будет использован: № {selected_contractor}")
        await msg.answer("Введите дату начала договора (дд.мм.гггг):")
        # dp.register_next_step(msg, cf.process_contract_start_date, contractor_id)
    else:
        if not user_id:
            user_id = msg.from_user.id
        contractors = await db.get_all_contractors(user_id)
        await msg.answer("Контрагент не был выбран. Пожалуйста, выберите контрагента.")
        if contractors:
            await msg.answer("Выберите контрагента:", reply_markup=kb.get_select_distributor_kb(contractors))

        else:
            await msg.answer(
                text=f"❗️У вас нет контрагентов.\n\n"
                     f"Чтобы добавить контрагента воспользуйтесь командой /{Command.PRELOADER_ADVERTISER_ENTITY.value}")


async def end_contract(state: FSMContext, chat_id: int):
    data = await state.get_data()

    contractor = await db.get_contractor(contractor_id=data['dist_id'])
    await state.update_data(data={'contractor_ord_id': contractor.ord_id})
    text = (
        f'❕ Проверьте, правильно ли указана информация по вашему договору с рекламодателем:\n\n'
        f'Контрагент: {contractor.name}\n'
        f'Дата заключения договора: {data["input_start_date"]}\n'
        f'Дата завершения договора: {data.get("input_end_date", "нет")}\n'
        f'Номер договора: {data.get("num", "нет")}\n'
        f'Сумма договора: {data.get("sum", "нет")} руб\n'
        f'Дата завершения договора: {data.get("input_end_date", "нет")}'
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


async def preloader_advertiser_entity(message: Message):
    await message.answer("Перейти к созданию контрагента?", reply_markup=kb.get_preloader_advertiser_entity_kb())


# Функция для завершения процесса добавления данных платформы
async def finalize_platform_data(msg: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    ord_id = ut.get_ord_id(msg.from_user.id, delimiter='-p-')
    response = await ut.send_platform_to_ord(
        ord_id=ord_id,
        platform_name=data['platform_name'],
        platform_url=data['platform_url'],
        dist_ord_id=data['dist_id']
    )
    if response in [200, 201]:
        await db.add_platform(
            user_id=msg.from_user.id,
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
        await msg.answer(
            f"❌ Произошла ошибка при добавлении платформы в ОРД: "
            f"{response if response else 'Нет ответа'}. "
            f"Попробуйте снова.")


async def select_contract(
        contracts: tuple[db.ContractDistRow],
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

        await select_contract(
            contracts=contracts,
            current=0,
            chat_id=user_id,
        )


# Начало процесса добавления креатива
async def add_creative_start(msg: Message, state: FSMContext, campaign_id: int):
    await state.set_state(UserState.ADD_CREATIVE)
    await state.update_data(data={'campaign_id': campaign_id})

    await msg.answer(
        "Загрузите файл своего рекламного креатива или введите текст. "
        "Вы можете загрузить несколько файлов для одного креатива."
    )


async def register_creative(data: dict, user_id: int, del_msg_id: int):
    creatives = data.get('creatives', [])

    # ut.print_dict(data, '>>creative data')

    creative_ord_id = ut.get_ord_id(user_id, delimiter=Delimiter.CR.value)

    campaign = await db.get_campaign(data['campaign_id'])
    contract = await db.get_contract(campaign.contract_id)
    user = await db.get_user_info(user_id)

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
        creative_text=data.get('text', []),
        description=campaign.service,
        media_ids=media_ord_ids,
        contract_ord_id=contract.ord_id
    )
    log_error(f'response: {response}', wt=False)
    erid = response.get('erid') if response else None
    if not erid:
        await bot.send_message(chat_id=user_id, text="Ошибка при отправке креатива в ОРД.❓❓❓")
        # тут ещё возврат денег
        return

    await db.add_creative(
        user_id=user_id,
        campaign_id=campaign.id,
        text=data.get('text'),
        token=erid,
        ord_id=creative_ord_id,
    )

    text = (f'Креатив успешно промаркирован.\n'
            f'Ваш токен - <code>{erid}</code>.\n'
            f'<code>Реклама. {contractor_name}. ИНН: {contractor_inn}. erid: {erid}</code>. \n'
            f'Теперь прикрепите маркировку к вашему креативу, опубликуйте и пришлите ссылку на него. \n'
            f'Если вы публикуете один креатив на разных площадках - пришлите ссылку на каждую площадку. \n'
            f'❓❓❓'
            )

    await bot.delete_message(chat_id=user_id, message_id=del_msg_id)
    await bot.send_message(chat_id=user_id, text=text, reply_markup=kb.get_end_creative_kb())

# Кнопка:
# 1. Добавить ссылку на другую площадку (переход к п.58)
# 2. Готово (переход к п.60)
# Важно:
# "Реклама..." должны копироваться при клике.
# Если не прислали ссылку в течение 1 часа - (переход к п.57)'
