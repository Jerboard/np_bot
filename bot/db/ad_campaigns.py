from datetime import datetime
import typing as t
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

from .base_db import METADATA, begin_connection
from enums import Status


class CampaignRow(t.Protocol):
    id: int
    created_at: datetime
    user_id: int
    contract_id: int
    brand: str
    service: str
    links: list[str]


CampaignTable: sa.Table = sa.Table(
    "ad_campaigns",
    METADATA,

    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('updated_at', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('user_id', sa.BigInteger),
    sa.Column('contract_id', sa.Integer),
    sa.Column('brand', sa.String(255)),
    sa.Column('service', sa.String(255)),
    sa.Column('status', sa.String(255), default=Status.ACTIVE.value),
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
async def get_user_campaigns(user_id: int = None, contract_id: int = None) -> list[CampaignRow]:
    query = CampaignTable.select().where(CampaignTable.c.status == Status.ACTIVE)

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


# возвращает рекламную компанию
async def update_campaign(contract_id: int, status: str = None) -> None:
    query = CampaignTable.update().where(CampaignTable.c.contract_id == contract_id).values(updated_at=datetime.now())

    if status:
        query = query.values(status=status)

    async with begin_connection() as conn:
        await conn.execute(query)
