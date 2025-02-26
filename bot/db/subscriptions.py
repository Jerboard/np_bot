import typing as t
from datetime import date

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

from .base_db import METADATA, begin_connection


class SubscriptionRow(t.Protocol):
    user_id: int
    start_date: date
    end_date: date
    plan: str
    is_recurrent: bool = False
    is_cancelled: bool = False
    tokens_subscription: int = 0
    tokens_additional: int = 0


SubscriptionTable: sa.Table = sa.Table(
    "subscriptions",
    METADATA,

    sa.Column('user_id', sa.BigInteger, primary_key=True),
    sa.Column('start_date', sa.Date),
    sa.Column('end_date', sa.Date),
    sa.Column('plan', sa.String(32)),
    sa.Column('is_recurrent', sa.Boolean, default=False),
    sa.Column('is_cancelled', sa.Boolean, default=False),
    sa.Column('tokens_subscription', sa.SmallInteger, default=0),
    sa.Column('tokens_additional', sa.SmallInteger, default=0),
)


async def add_subscription(
        user_id: int,
        start_date: date = None,
        end_date: date = None,
        plan: str = None,
        is_recurrent: bool = False,
        is_cancelled: bool = False,
        tokens_subscription: int = 0,
        tokens_additional: int = 0,
) -> int:
    query = (
        psql.insert(
            SubscriptionTable,
        ).values(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            plan=plan,
            is_recurrent=is_recurrent,
            is_cancelled=is_cancelled,
            tokens_subscription=tokens_subscription,
            tokens_additional=tokens_additional,
        ).on_conflict_do_nothing()
    )
    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.inserted_primary_key[0]


async def get_subscription(user_id: int) -> SubscriptionRow:
    query = SubscriptionTable.select().where(SubscriptionTable.c.user_id == user_id)

    async with begin_connection() as conn:
        result = await conn.execute(query)
        subscription = result.first()
    if subscription is None:
        await add_subscription(user_id=user_id)
        query = SubscriptionTable.select().where(SubscriptionTable.c.user_id == user_id)
        async with begin_connection() as conn:
            result = await conn.execute(query)
            subscription = result.first()
    return subscription



async def get_subscriptions(campaign_id: int) -> list[SubscriptionRow]:
    query = SubscriptionTable.select()

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.all()


async def update_subscription(
        user_id: int,
        start_date: date = None,
        end_date: date =  None,
        is_recurrent: bool =  None,
        is_cancelled: bool =  None,
        plan: str =  None,
        tokens_subscription: int =  None,
        tokens_additional: int =  None,
) -> None:
    query = SubscriptionTable.update().where(SubscriptionTable.c.user_id == user_id)

    if start_date is not None:
        query = query.values(start_date=start_date)
    if end_date is not None:
        query = query.values(end_date=end_date)
    if is_recurrent is not None:
        query = query.values(is_recurrent=is_recurrent)
    if is_cancelled is not None:
        query = query.values(is_cancelled=is_cancelled)
    if plan is not None:
        query = query.values(plan=plan)
    if tokens_subscription is not None:
        query = query.values(tokens_subscription=tokens_subscription)
    if tokens_additional is not None:
        query = query.values(tokens_additional=tokens_additional)

    async with begin_connection() as conn:
        await conn.execute(query)
