from datetime import datetime
import typing as t
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

from .base_db import METADATA, begin_connection


class DistributorRow(t.Protocol):
    id: int
    created_at: datetime
    user_id: int
    name: str
    inn: int
    j_type: str
    ord_id: str


DistributorTable: sa.Table = sa.Table(
    "distributors",
    METADATA,

    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('user_id', sa.BigInteger),
    sa.Column('name', sa.String(255)),
    sa.Column('inn', sa.BigInteger),
    sa.Column('j_type', sa.String(255)),
    sa.Column('ord_id', sa.String(255), unique=True),
)


# добавляет контрагента
async def add_contractor(user_id: int, name: str, inn: int, j_type: str, ord_id: str) -> None:
    now = datetime.now()
    query = (
        psql.insert(DistributorTable)
        .values(
            created_at=now,
            user_id=user_id,
            name=name,
            inn=inn,
            j_type=j_type,
            ord_id=ord_id
        )
        .on_conflict_do_update(
            index_elements=[DistributorTable.c.ord_id],
            set_={"created_at": now, 'user_id': user_id, 'name': name, "inn": inn, 'j_type': user_id}
        )
    )
    async with begin_connection() as conn:
        await conn.execute(query)


# возвращает количество контрагентов
async def get_contractor_count(user_id: int) -> int:
    # query = DistributorTable.select().where(DistributorTable.c.user_id == user_id)

    query = DistributorTable.select().with_only_columns([sa.func.count()]).where(DistributorTable.c.user_id == user_id)
    async with begin_connection() as conn:
        result = await conn.execute(query)
        count = await result.scalar()

    return count

    # async with begin_connection() as conn:
    #     result = await conn.execute(query)
    #
    # return len(result.all())


# возвращает всех контрагентов
async def get_all_contractors(user_id: int) -> tuple[DistributorRow]:
    query = DistributorTable.select().where(DistributorTable.c.user_id == user_id)
    async with begin_connection() as conn:
        result = await conn.execute(query)

    return result.all()


# возвращает всех контрагентов
async def get_contractor(contractor_id: int) -> DistributorRow:
    query = DistributorTable.select().where(DistributorTable.c.id == contractor_id)
    async with begin_connection() as conn:
        result = await conn.execute(query)

    return result.first()