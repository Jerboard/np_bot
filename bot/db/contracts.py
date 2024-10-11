from datetime import datetime, date
import typing as t
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql

from .base_db import METADATA, begin_connection
from enums import Status


class ContractRow(t.Protocol):
    id: int
    created_at: datetime
    user_id: int
    contractor_id: int
    contract_date: date
    end_date: date
    serial: str
    amount: float
    # vat_included: int
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
    sa.Column('status', sa.String(255), default=Status.ACTIVE.value),
    sa.Column('ord_id', sa.String(255)),

)


# Добавляет договор
async def add_contract(
        user_id: int,
        contractor_id: int,
        start_date: date,
        # vat_code: int,
        ord_id: str,
        end_date: date = None,
        serial: str = None,
        amount: float = None,
) -> int:
    now = datetime.now()
    query = ContractTable.insert().values(
        user_id=user_id,
        created_at=now,
        contractor_id=contractor_id,
        contract_date=start_date,
        # vat_code=vat_code,
        ord_id=ord_id,
        end_date=end_date,
        serial=serial,
        amount=amount
    )

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.inserted_primary_key[0]


# возвращает договор
async def get_contract(contract_id: int) -> ContractRow:
    query = ContractTable.select().where(ContractTable.c.id == contract_id)

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.first()


# возвращает договор
async def get_user_contracts(user_id: int) -> tuple[ContractRow]:
    query = ContractTable.select().where(
        ContractTable.c.user_id == user_id
    )

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.all()

