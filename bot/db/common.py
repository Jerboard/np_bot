import sqlalchemy as sa
from datetime import date, datetime, timedelta

import typing as t

from .base_db import METADATA, begin_connection
from .distributor import DistributorTable
from .contracts import ContractTable
from .creatives import CreativeTable
from .statistic import StatisticTable
from enums import Status


class ContractDistRow(t.Protocol):
    contract_id: int
    contract_user_id: int
    contractor_id: int
    contract_date: date
    end_date: date
    serial: str
    amount: float
    contract_ord_id: str
    name: str


class CreativeFullRow(t.Protocol):
    creative_id: int
    created_at: datetime
    user_id: int
    campaign_id: int
    token: str
    # texts: list[str]
    creative_ord_id: str
    statistic_id: int
    url: str
    views: int
    platform_id: int


# возвращает контракты с контрагентами
async def get_all_user_contracts(user_id: int = None) -> list[ContractDistRow]:
    query = (
        sa.select (
            ContractTable.c.id.label('contract_id'),
            ContractTable.c.contract_date,
            ContractTable.c.user_id.label('contract_user_id'),
            ContractTable.c.contractor_id,
            ContractTable.c.end_date,
            ContractTable.c.serial,
            ContractTable.c.amount,
            ContractTable.c.ord_id.label('contract_ord_id'),
            DistributorTable.c.name,
        )
        .select_from (ContractTable.join (
            DistributorTable, ContractTable.c.contractor_id == DistributorTable.c.id, isouter=True), )
    ).where(
        ContractTable.c.user_id == user_id,
        ContractTable.c.status == Status.ACTIVE,
        ContractTable.c.contractor_id != 0,
    )

    async with begin_connection () as conn:
        result = await conn.execute (query)

    return result.all ()


# возвращает контракт с контрагентом
async def get_contract_full_data(contract_id: int = None) -> ContractDistRow:
    query = (
        sa.select (
            ContractTable.c.id.label('contract_id'),
            ContractTable.c.user_id.label('contract_user_id'),
            ContractTable.c.contractor_id,
            ContractTable.c.contract_date,
            ContractTable.c.end_date,
            ContractTable.c.serial,
            ContractTable.c.amount,
            ContractTable.c.ord_id.label('contract_ord_id'),
            DistributorTable.c.name,
        )
        .select_from (ContractTable.join (
            DistributorTable, ContractTable.c.contractor_id == DistributorTable.c.id, isouter=True), )
    ).where(
        ContractTable.c.status == Status.ACTIVE,
        ContractTable.c.id == contract_id
    )

    async with begin_connection () as conn:
        result = await conn.execute (query)

    return result.first ()


# возвращает кампании с креативом
async def get_creative_full_data(
        campaign_id: int = None,
        user_id: int = None,
        user_id_statistic: int = None,
        for_monthly_report: bool = False
) -> list[CreativeFullRow]:
    query = (
        sa.select (
            CreativeTable.c.id.label('creative_id'),
            CreativeTable.c.created_at,
            CreativeTable.c.user_id,
            CreativeTable.c.campaign_id,
            CreativeTable.c.token,
            CreativeTable.c.ord_id.label('creative_ord_id'),
            StatisticTable.c.id.label('statistic_id'),
            StatisticTable.c.url,
            StatisticTable.c.views,
            StatisticTable.c.platform_id,

        )
        .select_from (
            CreativeTable.join (
                StatisticTable, CreativeTable.c.id == StatisticTable.c.creative_id,
                isouter=True
            )
        )
    ).where(
        CreativeTable.c.status == Status.ACTIVE
    )

    if campaign_id:
        query = query.where(CreativeTable.c.campaign_id == campaign_id)

    if user_id:
        query = query.where(CreativeTable.c.user_id == user_id)

    if user_id_statistic:
        query = query.where(StatisticTable.c.user_id == user_id_statistic)

    if for_monthly_report:
        now = datetime.now()
        if now.day <= 3:
            now = datetime.now() - timedelta(days=4)

        query = query.where(
            sa.and_(
                StatisticTable.c.ord_id.is_(None),
                sa.extract('year', StatisticTable.c.created_at) == now.year,
                sa.extract('month', StatisticTable.c.created_at) == now.month
            ))

    async with begin_connection () as conn:
        result = await conn.execute (query)

    return result.all()
