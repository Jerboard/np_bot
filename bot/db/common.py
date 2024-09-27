import sqlalchemy as sa
from datetime import date

import typing as t

from .base_db import METADATA, begin_connection
from .distributor import DistributorTable
from .contracts import ContractTable


class ContractDistRow(t.Protocol):
    contract_id: int
    user_id: int
    contract_date: date
    end_date: date
    serial: str
    amount: float
    name: str


# возвращает текущую задачу
async def get_all_user_contracts(user_id: int) -> tuple[ContractDistRow]:
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
    ).where(ContractTable.c.user_id == user_id)
    async with begin_connection () as conn:
        result = await conn.execute (query)

    return result.all ()