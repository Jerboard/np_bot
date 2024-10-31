from datetime import datetime, date
import typing as t
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql

from .base_db import METADATA, begin_connection
from enums import Status, ContractType


class ContractRow(t.Protocol):
    id: int
    created_at: datetime
    updated_at: datetime
    user_id: int
    contractor_id: int
    contract_date: date
    end_date: date
    serial: str
    amount: float
    status: str
    ord_id: str


ContractTable: sa.Table = sa.Table(
    "contracts",
    METADATA,

    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('updated_at', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('contract_type', sa.String(255), default=ContractType.BASE.value),
    sa.Column('user_id', sa.BigInteger),
    sa.Column('contractor_id', sa.Integer),
    sa.Column('contract_date', sa.Date()),
    sa.Column('end_date', sa.Date()),
    sa.Column('serial', sa.String(255)),
    sa.Column('amount', sa.Float, default=0),
    sa.Column('status', sa.String(255), default=Status.ACTIVE.value),
    sa.Column('ord_id', sa.String(255), unique=True),
    sa.Column('act_ord_id', sa.String(255)),

)


# Добавляет договор
async def add_contract(
        user_id: int,
        contractor_id: int,
        start_date: date,
        ord_id: str,
        end_date: date = None,
        serial: str = None,
        amount: float = 0,
        contract_type: str = None,
) -> int:
    now = datetime.now()
    # query = ContractTable.insert().values(
    # )

    query = psql.insert(ContractTable).values(
        user_id=user_id,
        created_at=now,
        contractor_id=contractor_id,
        contract_date=start_date,
        contract_type=contract_type,
        ord_id=ord_id,
        end_date=end_date,
        serial=serial,
        amount=amount
    ).on_conflict_do_update(
        index_elements=[ContractTable.c.ord_id],
        set_={
            'contract_type': contract_type,
            'updated_at': now
        }
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
async def get_agency_contract(user_id: int) -> ContractRow:
    query = ContractTable.select().where(
        ContractTable.c.user_id == user_id,
        ContractTable.c.contract_type == ContractType.AGENCY
    )
    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.first()


# возвращает договор
async def get_user_contracts(user_id: int) -> list[ContractRow]:
    query = ContractTable.select().where(
        sa.and_(
            ContractTable.c.user_id == user_id,
            ContractTable.c.status == Status.ACTIVE.value,
        )
    )

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.all()


# обновляет договор
async def update_contract(contract_id: int, status: str = None, act_ord_id: str = None) -> None:
    query = ContractTable.update().where(ContractTable.c.id == contract_id).values(updated_at=datetime.now())

    if status:
        query = query.values(status=status)

    if status:
        query = query.values(act_ord_id=act_ord_id)

    async with begin_connection() as conn:
        await conn.execute(query)
