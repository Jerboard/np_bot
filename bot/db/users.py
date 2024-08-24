from datetime import datetime
import typing as t
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

from .base_db import METADATA, begin_connection


class UserRow(t.Protocol):
    first_visit: datetime
    last_visit: datetime
    user_id: int
    full_name: str
    username: str
    name: str
    inn: int
    role: str
    phone: str
    j_type: str
    balance: float
    total_balance: float


UserTable: sa.Table = sa.Table(
    "users",
    METADATA,

    sa.Column('first_visit', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('last_visit', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('user_id', sa.BigInteger,  primary_key=True,),
    sa.Column('full_name', sa.String(255)),
    sa.Column('username', sa.String(255)),
    sa.Column('role', sa.String(255)),
    sa.Column('inn', sa.BigInteger),
    sa.Column('name', sa.String(255)),
    sa.Column('phone', sa.String(255)),
    sa.Column('j_type', sa.String(255)),
    sa.Column('balance', sa.Float(), default=0),
    sa.Column('total_balance', sa.Float(), default=0),
)


# Добавляет пользователя
async def add_user(
        user_id: int,
        full_name: str,
        username: str,
        role: str = None,
        inn: int = None,
        name: str = None,
        j_type: str = None,
) -> None:
    now = datetime.now()
    query = (
        psql.insert(UserTable)
        .values(
            user_id=user_id,
            full_name=full_name,
            username=username,
            first_visit=now,
            last_visit=now,
            role=role,
            inn=inn,
            name=name,
            j_type=j_type
        )
        .on_conflict_do_update(
            index_elements=[UserTable.c.user_id],
            set_={"full_name": full_name, 'username': username, 'last_visit': now}
        )
    )
    async with begin_connection() as conn:
        await conn.execute(query)
        
        
# возвращает данные пользователя
async def get_user_info(user_id: int) -> UserRow:
    query = UserTable.select().where(UserTable.c.user_id == user_id)
    async with begin_connection() as conn:
        result = await conn.execute(query)

    return result.first()


# обновляет данные пользователя
async def update_user(user_id: int, role: str = None, j_type: str = None) -> None:
    query = UserTable.update().where(UserTable.c.user_id == user_id)
    if role:
        query = query.values(role=role)
    if role:
        query = query.values(j_type=j_type)

    async with begin_connection() as conn:
        await conn.execute(query)
