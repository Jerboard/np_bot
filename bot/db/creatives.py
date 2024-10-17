from datetime import datetime
import typing as t
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

from .base_db import METADATA, begin_connection
from enums import Status


class CreativeRow(t.Protocol):
    id: int
    created_at: datetime
    updated_at: datetime
    user_id: int
    campaign_id: int
    token: str
    status: str
    ord_id: str
    texts: list[str]


CreativeTable: sa.Table = sa.Table(
    "creatives",
    METADATA,

    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('updated_at', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('user_id', sa.BigInteger),
    sa.Column('campaign_id', sa.Integer),
    sa.Column('texts', psql.ARRAY(sa.Text)),
    sa.Column('ord_id', sa.String(255)),
    sa.Column('token', sa.String(255)),
    sa.Column('status', sa.String(255), default=Status.ACTIVE.value),
)


# добавляет оплату
async def add_creative(
        user_id: int,
        campaign_id: int,
        ord_id: str,
        token: str,
        texts: list[str] = None,
) -> int:
    now = datetime.now()
    query = CreativeTable.insert().values(
            created_at=now,
            updated_at=now,
            user_id=user_id,
            campaign_id=campaign_id,
            texts=texts,
            ord_id=ord_id,
            token=token,
        )

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.inserted_primary_key[0]


# возвращает креатив
async def get_creative(creative_id: int) -> CreativeRow:
    query = CreativeTable.select().where(CreativeTable.c.id == creative_id)

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.first()


# возвращает креатив
async def get_creatives(campaign_id: int) -> list[CreativeRow]:
    query = CreativeTable.select().where(CreativeTable.c.campaign_id == campaign_id)

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.all()


# обновляет креатив
async def update_creative(
        creative_id: int = None,
        campaign_id: int = None,
        token: str = None,
        status: str = None
) -> None:
    query = CreativeTable.update().values(updated_at=datetime.now())

    if creative_id:
        query = query.values(token=token).where(CreativeTable.c.id == creative_id)

    elif campaign_id:
        query = query.values(token=token).where(CreativeTable.c.campaign_id == creative_id)

    if token:
        query = query.values(token=token)

    if status:
        query = query.values(status=status)

    async with begin_connection() as conn:
        await conn.execute(query)
