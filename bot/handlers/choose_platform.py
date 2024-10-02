from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command as CommandFilter, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.enums.message_entity_type import MessageEntityType
from datetime import datetime
from asyncio import sleep

import db
import keyboards as kb
from config import Config
from init import dp
import utils as ut
from .base import preloader_choose_platform, finalize_platform_data, start_contract, start_bot
from enums import CB, Command, UserState, platform_dict, Role, Action


# выбора платформы старт
@dp.message(CommandFilter(Command.PRELOADER_CHOOSE_PLATFORM.value))
async def preloader_choose_platform_base(msg: Message, state: FSMContext):
    user = await db.get_user_info(msg.from_user.id)
    if user:
        await preloader_choose_platform(msg)
    else:
        await start_bot(msg, state)


# если не хочет выбирать платформу
@dp.callback_query(lambda cb: cb.data.startswith(CB.NO_CHOOSE_PLATFORM.value))
async def no_choose_platform(cb: CallbackQuery):
    await cb.message.answer("Вы можете в любой момент продолжить добавление рекламной площадки "
                            "нажав на соответствующий пункт в меню")


# выбор платформы
@dp.callback_query(lambda cb: cb.data.startswith(CB.PLATFORM_START.value))
async def choose_platform(cb: CallbackQuery):
    await cb.message.answer("Выберите площадку:", reply_markup=kb.get_choose_platform_kb())


# сохраняем платформу просим ссылку
@dp.callback_query(lambda cb: cb.data.startswith(CB.PLATFORM_SELECT.value))
async def collect_platform(cb: CallbackQuery, state: FSMContext):
    _, platform = cb.data.split(':')

    await state.set_state(UserState.ADD_PLATFORM_NAME)
    await state.update_data(data={'platform_name': platform})

    await cb.message.answer("Пришлите ссылку на аккаунт рекламораспространителя.")


    # elif cb.data == 'other':
    #     platform_name = 'Другое'
    #     await message.answer("Пришлите ссылку на площадку рекламораспространителя.")
    #     dp.register_next_step(cb.message, cf.platform_url_collector)
    #
    # else:
    #     # добавил чтоб не было предупреждения
    #     platform_name = 'error'


# принимаем ссылку
@dp.message(StateFilter(UserState.ADD_PLATFORM_NAME))
async def collect_advertiser_link(msg: Message, state: FSMContext):
    entity = msg.entities[0].type if msg.entities else None
    if entity != MessageEntityType.URL:
        await msg.answer('❗️ Некорректная ссылка\n\nПришлите ссылку на аккаунт рекламораспространителя.')
        return

    advertiser_link = f'https://{msg.text}' if not msg.text.startswith("https://") else msg.text

    await state.update_data(data={'platform_url': advertiser_link})
    data = await state.get_data()

    text = (f"Проверьте, правильно ли указана ссылка на площадку рекламораспространителя:\n\n"
            f"{platform_dict.get(data['platform_name'], 'нд')} - {advertiser_link}"
            )
    await msg.answer(text, reply_markup=kb.get_platform_url_collector_kb(), disable_web_page_preview=True)


# подтверждение ссылки
@dp.callback_query(lambda cb: cb.data.startswith(CB.PLATFORM_CORRECT.value))
async def handle_platform_verification(cb: CallbackQuery, state: FSMContext):
    _, action = cb.data.split(':')
    if action == Action.YES:
        await state.set_state(UserState.ADD_PLATFORM_VIEW)
        await cb.message.answer("Укажите среднее количество просмотров поста за месяц:")
    else:
        await preloader_choose_platform(cb.message)


# Функция для проверки введенных данных и перехода к следующему шагу
@dp.message(StateFilter(UserState.ADD_PLATFORM_VIEW))
async def process_average_views(msg: Message, state: FSMContext):
    if msg.text.isdigit():
        await state.update_data(data={'view': int(msg.text)})

        # Получение person_external_id для РР
        user = await db.get_user_info(msg.from_user.id)
        if user.role == Role.ADVERTISER:
            contractors = await db.get_all_contractors(msg.from_user.id)
            if contractors:
                await msg.answer("Выберите контрагента\n"
                                 "(Контрагент - это другая сторона вашего договора)",
                                 reply_markup=kb.get_process_average_views_kb(contractors))
            else:
                await msg.answer("Не найдено контрагентов. Пожалуйста, добавьте контрагентов и повторите попытку.")

        else:
            await state.update_data(data={'dist_id': str(msg.from_user.id)})
            await finalize_platform_data(msg, state)
    else:
        sent = await msg.answer(
            "❌ Неверный формат. "
            "Пожалуйста, укажите среднее количество просмотров вашего поста за месяц, используя только цифры:"
        )
        await sleep(3)
        await sent.delete()


# выбор контрагента
@dp.callback_query(lambda cb: cb.data.startswith(CB.PLATFORM_DIST.value))
async def handle_contractor_selection(cb: CallbackQuery, state: FSMContext):
    _, dist_ord_id_str = cb.data.split(':')

    await state.update_data(data={'dist_id': dist_ord_id_str})
    await finalize_platform_data(cb.message, state)


# завершение создания платформы. Следующий шаг
@dp.callback_query(lambda cb: cb.data.startswith(CB.PLATFORM_FIN.value))
async def handle_success_add_platform(cb: CallbackQuery):
    _, action = cb.data.split(':')

    if action == Action.ADD:
        await choose_platform(cb)

    else:
        user = await db.get_user_info(cb.from_user.id)
        if user.role == Role.ADVERTISER:
            await cb.message.answer("Теперь укажите информацию о договоре.")
            await start_contract(cb.message, user_id=cb.from_user.id, )
        else:
            await cb.message.answer(
                "Перейти к созданию контрагента?",
                reply_markup=kb.get_preloader_advertiser_entity_kb()
            )
