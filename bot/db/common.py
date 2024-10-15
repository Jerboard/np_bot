import sqlalchemy as sa
from datetime import date

import typing as t

from .base_db import METADATA, begin_connection
from .distributor import DistributorTable
from .contracts import ContractTable
from .ad_campaigns import CampaignTable
from .creatives import CreativeTable
from enums import Status


class ContractDistRow(t.Protocol):
    contract_id: int
    user_id: int
    contract_date: date
    end_date: date
    serial: str
    amount: float
    name: str


class CampaignCreativeRow(t.Protocol):
    creative_id: int
    creative_ord_id: str
    token: str
    created_at: str



# возвращает контракты с контрагентами
async def get_all_user_contracts(user_id: int = None) -> tuple[ContractDistRow]:
    query = (
        sa.select (
            ContractTable.c.id.label('contract_id'),
            ContractTable.c.contract_date,
            ContractTable.c.end_date,
            ContractTable.c.serial,
            ContractTable.c.amount,
            DistributorTable.c.name,
        )
        .select_from (ContractTable.join (
            DistributorTable, ContractTable.c.contractor_id == DistributorTable.c.id, isouter=True), )
    ).where(
        ContractTable.c.user_id == user_id,
        ContractTable.c.status == Status.ACTIVE
    )

    async with begin_connection () as conn:
        result = await conn.execute (query)

    return result.all ()


# возвращает контракт с контрагентом
async def get_contract_full_data(contract_id: int = None) -> ContractDistRow:
    query = (
        sa.select (
            ContractTable.c.id.label('contract_id'),
            ContractTable.c.contract_date,
            ContractTable.c.end_date,
            ContractTable.c.serial,
            ContractTable.c.amount,
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
async def get_campaigns_with_creative(user_id: int = None) -> tuple[ContractDistRow]:
    query = (
        sa.select (
            ContractTable.c.id.label('contract_id'),
            ContractTable.c.contract_date,
            ContractTable.c.end_date,
            ContractTable.c.serial,
            ContractTable.c.amount,
            DistributorTable.c.name,
        )
        .select_from (ContractTable.join (
            DistributorTable, ContractTable.c.contractor_id == DistributorTable.c.id, isouter=True), )
    ).where(
        ContractTable.c.user_id == user_id,
        ContractTable.c.status == Status.ACTIVE
    )

    async with begin_connection () as conn:
        result = await conn.execute (query)

    return result.all ()