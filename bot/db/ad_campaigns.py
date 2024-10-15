from datetime import datetime
import typing as t
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

from .base_db import METADATA, begin_connection


class CampaignRow(t.Protocol):
    id: int
    created_at: datetime
    user_id: int
    contract_id: int
    brand: str
    service: str
    link: list


CampaignTable: sa.Table = sa.Table(
    "ad_campaigns",
    METADATA,

    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('user_id', sa.BigInteger),
    sa.Column('contract_id', sa.Integer),
    sa.Column('brand', sa.String(255)),
    sa.Column('service', sa.String(255)),
    sa.Column('links', psql.ARRAY(sa.String(255))),
)


# добавляет рекламную компанию
async def add_campaign(user_id: int, contract_id: int, brand: str, service: str, links: list) -> int:
    now = datetime.now()
    query = CampaignTable.insert().values(
            created_at=now,
            user_id=user_id,
            contract_id=contract_id,
            brand=brand,
            service=service,
            links=links,
        )

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.inserted_primary_key


# возвращает все рекламные компании пользователя
async def get_user_campaigns(user_id: int = None, contract_id: int = None) -> tuple[CampaignRow]:
    query = CampaignTable.select()

    if user_id:
        query = query.where(CampaignTable.c.user_id == user_id)

    if contract_id:
        query = query.where(CampaignTable.c.contract_id == contract_id)

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.all()


# возвращает рекламную компанию
async def get_campaign(campaign_id: int) -> CampaignRow:
    query = CampaignTable.select().where(CampaignTable.c.id == campaign_id)

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.first()
