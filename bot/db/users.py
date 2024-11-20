from datetime import datetime
from random import choice

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
    inn: str
    role: str
    phone: str
    email: str
    j_type: str
    fio: str
    ref_code: str
    referrer: int
    in_ord: bool


UserTable: sa.Table = sa.Table(
    "users",
    METADATA,

    sa.Column('first_visit', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('last_visit', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('user_id', sa.BigInteger,  primary_key=True,),
    sa.Column('full_name', sa.String(255)),
    sa.Column('username', sa.String(255)),
    sa.Column('role', sa.String(255)),
    sa.Column('inn', sa.String(255)),
    sa.Column('name', sa.String(255)),
    sa.Column('phone', sa.String(255)),
    sa.Column('email', sa.String(255)),
    sa.Column('j_type', sa.String(255)),
    sa.Column('fio', sa.String(255)),
    sa.Column('referrer', sa.BigInteger()),
    sa.Column('ref_code', sa.String(255)),
    sa.Column('in_ord', sa.Boolean(), default=False),
)


# даёт случайную сроку для реферальной ссылки
def get_ref_code() -> str:
    return ''.join([choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(10)])


# Добавляет пользователя
async def add_user(
        user_id: int,
        full_name: str,
        username: str,
        referrer: int = None,
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
            ref_code=get_ref_code(),
            referrer=referrer,
            # inn=inn,
            # name=name,
            # phone=phone,
            # email=email,
            # j_type=j_type
        )
        .on_conflict_do_update(
            index_elements=[UserTable.c.user_id],
            set_={"full_name": full_name, 'username': username, 'last_visit': now}
        )
    )
    async with begin_connection() as conn:
        await conn.execute(query)
        
        
# возвращает данные пользователя
async def get_user_info(user_id: int = None, ref_code: str = None) -> UserRow:
    query = UserTable.select()

    if user_id:
        query = query.where(UserTable.c.user_id == user_id)
    elif ref_code:
        query = query.where(UserTable.c.ref_code == ref_code)
    else:
        return None

    async with begin_connection() as conn:
        result = await conn.execute(query)

    return result.first()


# обновляет данные пользователя
async def update_user(
        user_id: int,
        role: str = None,
        j_type: str = None,
        in_ord: bool = None,
        inn: str = None,
        name: str = None,
        phone: str = None,
        email: str = None,
        fio: str = None,
) -> None:
    query = UserTable.update().where(UserTable.c.user_id == user_id).values(last_visit=datetime.now())

    if role:
        query = query.values(role=role)
    if j_type:
        query = query.values(j_type=j_type)
    if in_ord is not None:
        query = query.values(in_ord=in_ord)
    if inn:
        query = query.values(inn=inn)
    if name:
        query = query.values(name=name)
    if phone:
        query = query.values(phone=phone)
    if email:
        query = query.values(email=email)
    if fio:
        query = query.values(fio=fio)

    async with begin_connection() as conn:
        await conn.execute(query)
