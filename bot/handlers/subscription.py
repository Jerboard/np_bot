import inspect
import re
from datetime import datetime, timedelta

from aiogram.filters import StateFilter, Command as CommandFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from yookassa import Payment

import db
import keyboards as kb
import utils as ut
from config import Config
from db.subscriptions import get_subscription
from enums import UserState, CB
from enums.subscriptions import Subscription
from handlers.base import register_creative
from init import dp, bot

SUBSCRIPTION_DESCRIPTIONS = {
    Subscription.TESTER.name: 'Пробная версия – 1 рубль, 7 дней, 1 токен.',
    Subscription.BASED.name: 'Базовая подписка – 3000 рублей/месяц, 20 токенов.',
    Subscription.PRO.name: 'Премиум подписка – 10000 рублей/месяц, 200 токенов.',
}

SUBSCRIPTION_PRICES = {
    Subscription.TESTER.name: 1,
    Subscription.BASED.name: 3000,
    Subscription.PRO.name: 10000,
}

SUBSCRIPTION_TOKENS = {
    Subscription.TESTER.name: 1,
    Subscription.BASED.name: 20,
    Subscription.PRO.name: 200,
}


async def subscription_main(user: int | db.UserRow):
    if isinstance(user, int):
        user = await db.get_user_info(user)
    subscription = await get_subscription(user.user_id)

    subscription_text = ''
    sub_data = await db.get_subscription(user.user_id)
    tokens_left = sub_data.tokens_additional + sub_data.tokens_subscription
    if sub_data.end_date:
        subscription_text += f"Подписка до: {sub_data.end_date.strftime(Config.date_form)}"
        if sub_data.is_cancelled:
            subscription_text += ' (отменена)'
    else:
        subscription_text += f"У вас нет подписки."
    subscription_text += f"\nОсталось токенов: <b>{tokens_left}</b>"

    await bot.send_message(
        user.user_id,
        f"Управление подпиской.\n\n{subscription_text}\n\nМожете выбрать тариф.",
        reply_markup=kb.get_subscription_main_kb(
            subscription.plan if not subscription.is_cancelled else None,
            was_subscribed_at_least_once=bool(sub_data.start_date),
        ),
    )


# BUY SUBSCRIPTION PLAN:


@dp.callback_query(lambda cb: cb.data.startswith(f"{CB.SUBSCRIPTION_BUY_PLAN.value}:"))
async def subscription_confirm(cb: CallbackQuery, state: FSMContext):
    print(f"[{inspect.stack()[0][3]}]")  # print func name
    requested_plan = cb.data.split(':')[1]
    await state.update_data(data={'requested_plan': requested_plan})
    await state.update_data({
        'requested_plan': requested_plan,
        'amount_rub': SUBSCRIPTION_PRICES[requested_plan],
        'payment_type': 'buy_subscription',
    })
    await cb.message.edit_text(
        text=SUBSCRIPTION_DESCRIPTIONS[requested_plan],
        reply_markup=kb.get_subscription_buy_plan_confirm_kb(),
    )


@dp.callback_query(lambda cb: cb.data == CB.SUBSCRIPTION_CANCEL.value)
async def cancel_subscription(cb: CallbackQuery, state: FSMContext):
    print(f"[{inspect.stack()[0][3]}]")  # print func name
    sub = await db.get_subscription(cb.from_user.id)
    await cb.message.edit_text(
        text=f"Действующая подписка: {getattr(Subscription, sub.plan).value}."
             f"\n\nТокены останутся доступными до окончания срока действия подписки."
             f"\n\nОтменить подписку?",
        reply_markup=kb.get_subscription_cancel_kb(),
    )


@dp.callback_query(lambda cb: cb.data == CB.SUBSCRIPTION_CANCEL_CONFIRMED.value)
async def cancel_subscription_confirmed(cb: CallbackQuery, state: FSMContext):
    print(f"[{inspect.stack()[0][3]}]")  # print func name
    await db.update_subscription(cb.from_user.id, is_cancelled=True)
    await cb.message.edit_text(text='Подписка отменена. На главную: /start')


# BUY TOKENS:


@dp.callback_query(lambda cb: cb.data.startswith(f"{CB.SUBSCRIPTION_BUY_TOKENS.value}"))
async def subscription_buy_tokens(cb: CallbackQuery, state: FSMContext):
    print(f"[{inspect.stack()[0][3]}]")  # print func name
    
    await state.set_state(UserState.SUBSCRIPTION_INPUT_TOKENS_AMOUNT)
    await cb.message.edit_text(
        text=f'Стоимость дополнительных токенов - {Config.token_price} руб. / токен. Введите количество токенов для покупки.',
    )


@dp.message(StateFilter(UserState.SUBSCRIPTION_INPUT_TOKENS_AMOUNT), ~CommandFilter(re.compile(r'.*')))
async def subscription_buy_tokens_amount(msg: Message, state: FSMContext):
    print(f"[{inspect.stack()[0][3]}]")  # print func name

    try:
        amount = int(msg.text)
    except (ValueError, TypeError):
        await msg.answer('Введите количество токенов для покупки. Например: 5')
        return
    if amount > 100:
        await msg.answer('Максимальное количество токенов на покупку - 100. Введите количество токенов для покупки.')
        return
    await state.clear()
    await state.update_data({
        'amount': amount,
        'amount_rub': amount * Config.token_price,
        'payment_type': 'buy_tokens',
    })
    await msg.answer(
        text=f"Стоимость дополнительных токенов - {Config.token_price * amount} руб.",
        reply_markup=kb.get_subscription_buy_tokens_confirm_kb(),
    )


@dp.callback_query(lambda cb: cb.data == CB.SUBSCRIPTION_BUY_BACK.value)
async def subscription_buy_no(cb: CallbackQuery, state: FSMContext):
    print(f"[{inspect.stack()[0][3]}]")  # print func name
    await state.clear()
    await subscription_main(cb.from_user.id)


# PAYMENTS:


# создаёт ссылку на оплату
@dp.callback_query(lambda cb: cb.data.startswith(CB.PAY_YK_NEW.value))
async def pay_yk(cb: CallbackQuery, state: FSMContext):
    print(f"[{inspect.stack()[0][3]}]")  # print func name
    
    data = await state.get_data()
    pay_id = data.get('pay_id')
    if not pay_id:
        user = await db.get_user_info(cb.from_user.id)
        pay_id = ut.create_simple_pay_link(
            email=user.email,
            amount_rub=data['amount_rub'],
            metadata={'payment_type': data['payment_type'], 'requested_plan': data.get('requested_plan')},
        )
        await state.update_data(data={'pay_id': pay_id})

    text = 'Перейдите по ссылке и произведите оплату, затем нажмите "Продолжить"\n\n'
    await cb.message.edit_text(text=text, reply_markup=kb.get_yk_pay_kb(pay_id, data['amount_rub']))


# Обработчик кнопки "Продолжить". Обычная оплата
@dp.callback_query(lambda cb: cb.data.startswith(CB.PAY_YK_CHECK.value))
async def continue_after_payment(cb: CallbackQuery, state: FSMContext):
    print(f"[{inspect.stack()[0][3]}]")  # print func name

    sandclock = await cb.message.answer('⏳')

    _, pay_id = cb.data.split(':')
    data = await state.get_data()
    pay_data = Payment.find_one(pay_id)
    amount_rub = int(pay_data.amount.value)
    paid = pay_data.paid
    if paid:
        # сохраняем данные платежа
        await db.add_payment(
            user_id=cb.from_user.id,
            pay_id=pay_data.id,
            amount=amount_rub,
        )
        await apply_payment(
            cb.from_user.id,
            amount_rub=amount_rub,
            payment_type=pay_data.metadata.get('payment_type'),
            requested_plan=pay_data.metadata.get('requested_plan'),
        )
        if data.get('payment_type') in ['buy_tokens', 'buy_subscription']:
            await state.clear()
            await cb.message.answer('Оплата прошла успешно!\n\nВернуться на главную: /start\n\nК маркировке креатива: /token')
        else:
            await sandclock.edit_text('Оплата прошла успешно!')
            sandclock = await cb.message.answer('⏳')
            await register_creative(data=data, user_id=cb.from_user.id, del_msg_id=sandclock.message_id, state=state)
    else:
        await sandclock.delete()
        await cb.answer('❗️  Оплата не найдена. Нажмите "Оплатить" и совершите платёж', show_alert=True)


async def apply_payment(user_id, amount_rub: int, payment_type: str = None, requested_plan: str = None):
    sub = await db.get_subscription(user_id)
    if payment_type == 'buy_subscription':
        today = datetime.now().date()
        await db.update_subscription(
            user_id=user_id,
            start_date=sub.start_date or today,
            end_date=today + timedelta(days=28),
            is_recurrent=False,
            is_cancelled=False,
            plan=requested_plan,
            tokens_subscription=SUBSCRIPTION_TOKENS[requested_plan],
        )
    else:
        await db.update_subscription(
            user_id=user_id,
            tokens_additional=sub.tokens_additional + (amount_rub // Config.token_price),
        )
