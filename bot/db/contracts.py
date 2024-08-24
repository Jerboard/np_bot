from datetime import datetime, date
import typing as t
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as sa_postgresql

from .base_db import METADATA, begin_connection


class ContractRow(t.Protocol):
    id: int
    created_at: datetime
    user_id: int
    contractor_id: int
    contract_date: date
    end_date: date
    serial: str
    amount: float
    vat_included: int
    ord_id: str


ContractTable: sa.Table = sa.Table(
    "contracts",
    METADATA,

    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('user_id', sa.BigInteger),
    sa.Column('contractor_id', sa.Integer),
    sa.Column('contract_date', sa.Date()),
    sa.Column('end_date', sa.Date()),
    sa.Column('serial', sa.String(255)),
    sa.Column('amount', sa.Float),
    sa.Column('vat_included', sa.Integer),
    sa.Column('ord_id', sa.String(255)),

)


# Добавляет пользователя
async def add_contract(
        user_id: int,
        contractor_id: int,
        contract_date: date,
        vat_included: int,
        ord_id: str,
        end_date: date = None,
        serial: str = None,
        amount: float = None,
) -> None:
    now = datetime.now()
    query = ContractTable.insert(ContractTable).values(
        user_id=user_id,
        contractor_id=contractor_id,
        contract_date=contract_date,
        vat_included=vat_included,
        ord_id=ord_id,
        end_date=end_date,
        serial=serial,
        amount=amount
    )

    async with begin_connection() as conn:
        await conn.execute(query)
