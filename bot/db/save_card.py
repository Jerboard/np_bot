from datetime import datetime
import typing as t
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

from .base_db import METADATA, begin_connection
from enums import Status


class SaveCardRow(t.Protocol):
    id: int
    created_at: datetime
    user_id: int
    last_pay_id: str
    card_info: str


SaveCardTable: sa.Table = sa.Table(
    "save_cards",
    METADATA,

    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('user_id', sa.BigInteger),
    sa.Column('last_pay_id', sa.String(255)),
    sa.Column('card_info', sa.String(255))
)


# добавляет карту
async def add_card(
        user_id: int,
        pay_id: str,
        card_info: str
) -> int:
    now = datetime.now()
    query = SaveCardTable.insert().values(
            created_at=now,
            user_id=user_id,
            last_pay_id=pay_id,
            card_info=card_info
        )

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.inserted_primary_key


# Обновляет карту
async def update_card(
        card_id: int,
        pay_id: str,
) -> None:
    query = SaveCardTable.update().where(SaveCardTable.c.id == card_id)

    if pay_id:
        query = query.values(last_pay_id=pay_id)

    async with begin_connection() as conn:
        await conn.execute(query)


# Возвращает все карты пользователя
async def get_user_card(user_id: int) -> list[SaveCardRow]:
    query = SaveCardTable.select().where(SaveCardTable.c.user_id == user_id)

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.all()


# Возвращает карту
async def get_card(card_id: int) -> SaveCardRow:
    query = SaveCardTable.select().where(SaveCardTable.c.id == card_id)

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.first()


# Удаляет карту
async def del_card(card_id: int) -> None:
    query = SaveCardTable.delete().where(SaveCardTable.c.id == card_id)

    async with begin_connection() as conn:
        await conn.execute(query)
