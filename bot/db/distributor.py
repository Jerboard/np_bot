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
    inn: str
    j_type: str
    role: str
    ord_id: str


DistributorTable: sa.Table = sa.Table(
    "distributors",
    METADATA,

    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('user_id', sa.BigInteger),
    sa.Column('name', sa.String(255)),
    sa.Column('inn', sa.String(255)),
    sa.Column('j_type', sa.String(255)),
    sa.Column('role', sa.String(255)),
    sa.Column('ord_id', sa.String(255), unique=True),
)


# добавляет контрагента
async def add_contractor(user_id: int, name: str, inn: str, j_type: str, ord_id: str, role: str) -> int:
    now = datetime.now()
    query = (
        psql.insert(DistributorTable)
        .values(
            created_at=now,
            user_id=user_id,
            name=name,
            inn=inn,
            j_type=j_type,
            role=role,
            ord_id=ord_id
        )
        .on_conflict_do_update(
            index_elements=[DistributorTable.c.ord_id],
            set_={"created_at": now, 'user_id': user_id, 'name': name, "inn": inn, 'j_type': j_type, 'role': role}
        )
    )
    async with begin_connection() as conn:
        result = await conn.execute(query)

    return result.inserted_primary_key[0]


'''
[SQL: INSERT INTO distributors 
(created_at, user_id, name, inn, j_type, ord_id) 
VALUES (
$1::TIMESTAMP WITH TIME ZONE, 
$2::BIGINT, 
$3::VARCHAR, 
$4::VARCHAR, 
$5::VARCHAR, 
$6::VARCHAR) 
ON CONFLICT (ord_id) 
DO UPDATE SET created_at = $7::TIMESTAMP WITH TIME ZONE, user_id = $8::BIGINT, name = $9::VARCHAR, inn = $10::VARCHAR, j_type = $11::VARCHAR RETURNING distributors.id]
[parameters: (datetime.datetime(2024, 9, 23, 17, 24, 19, 431492), 524275902, 'ООО ЮКЦ Партнер', '7727563778', 'juridical', '524275902-u-283548423', datetime.datetime(2024, 9, 23, 17, 24, 19, 431492), 524275902, 'ООО ЮКЦ Партнер', '7727563778', 524275902)]
(Background on this error at: https://sqlalche.me/e/20/dbapi)
'''

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