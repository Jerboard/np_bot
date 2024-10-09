from datetime import datetime
import typing as t
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

from .base_db import METADATA, begin_connection
from enums import Status


class StatisticRow(t.Protocol):
    id: int
    created_at: datetime
    user_id: int
    last_pay_id: str
    card_info: str


StatisticTable: sa.Table = sa.Table(
    "statistic",
    METADATA,

    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('updated_at', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('user_id', sa.BigInteger),
    sa.Column('creative_id', sa.Integer),
    sa.Column('url', sa.String(255)),
    sa.Column('status', sa.String(255), default=Status.ACTIVE.value),
    sa.Column('views', sa.Integer(), default=0),
    sa.Column('platform_id', sa.Integer()),
    sa.Column('in_ord', sa.Boolean(), default=False)
)


# добавляет карту
async def add_statistic(
        user_id: int,
        creative_id: int,
        url: str,
        platform_id: int
) -> int:
    now = datetime.now()
    query = StatisticTable.insert().values(
            created_at=now,
            updated_at=now,
            user_id=user_id,
            creative_id=creative_id,
            url=url,
            platform_id=platform_id,
        )

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.inserted_primary_key


# Обновляет карту
async def update_statistic(
        statistic_id: int,
        views: int = None,
) -> None:
    now = datetime.now()
    query = StatisticTable.update().where(StatisticTable.c.id == statistic_id).values(updated_at=now)

    if views is not None:
        query = query.values(views=views)

    async with begin_connection() as conn:
        await conn.execute(query)


# Возвращает всю статистику пользователя
async def get_statistics(user_id: int = None, creative_id: int = None) -> tuple[StatisticRow]:
    query = StatisticTable.select()

    if user_id:
        query = query.where(StatisticTable.c.user_id == user_id)

    if creative_id:
        query = query.where(StatisticTable.c.creative_id == creative_id)

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.all()


# Возвращает статистику
async def get_statistic(statistic_id: int) -> StatisticTable:
    query = StatisticTable.select().where(StatisticTable.c.id == statistic_id)

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.first()
