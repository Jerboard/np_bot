from datetime import datetime
import typing as t
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

from .base_db import METADATA, begin_connection


class PaymentRow(t.Protocol):
    id: int
    created_at: datetime
    user_id: int
    pay_id: str
    card: str
    save_card: bool


PaymentTable: sa.Table = sa.Table(
    "payment_yk",
    METADATA,

    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('user_id', sa.BigInteger),
    sa.Column('pay_id', sa.String(255)),
    sa.Column('card', sa.String(255)),
    sa.Column('save_card', sa.Boolean, default=False)
)


# добавляет оплату
async def add_payment(user_id: int, pay_id: str, card: str, save_card: bool) -> None:
    now = datetime.now()
    query = PaymentTable.insert().values(
            created_at=now,
            user_id=user_id,
            pay_id=pay_id,
            card=card,
            save_card=save_card,
        )

    async with begin_connection() as conn:
        await conn.execute(query)


# возвращает все карточки пользователя
async def get_user_save_cards(user_id: int) -> tuple[str]:
    query = PaymentTable.select().with_only_columns(PaymentTable.c.card).where(
        PaymentTable.c.user_id == user_id,
        # PaymentTable.c.save_card == True,
    )
    async with begin_connection() as conn:
        result = await conn.execute(query)

    return result.all()