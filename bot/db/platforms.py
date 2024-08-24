from datetime import datetime
import typing as t
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sa_postgresql

from .base_db import METADATA, begin_connection


class DistributorRow(t.Protocol):
    id: int
    created_at: datetime
    user_id: int
    name: str
    url: str
    advertiser_link: str
    average_views: int
    link: str
    ord_id: str
    vat_included: str


PlatformTable: sa.Table = sa.Table(
    "platforms",
    METADATA,

    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('user_id', sa.BigInteger),
    sa.Column('name', sa.String(255)),
    sa.Column('url', sa.String(255)),
    sa.Column('advertiser_link', sa.String(255)),
    sa.Column('average_views', sa.Integer),
    sa.Column('link', sa.String(255)),
    sa.Column('ord_id', sa.String(255), unique=True),
    sa.Column('vat_included', sa.String(255)),
)


# Добавляет пользователя
async def add_platform(
        user_id: int,
        name: str,
        url: str,
        average_views: int,
        ord_id: str,
) -> None:
    now = datetime.now()
    query = (
        sa_postgresql.insert(PlatformTable)
        .values(
            created_at=now,
            user_id=user_id,
            name=name,
            url=url,
            average_views=average_views,
            ord_id=ord_id,
        )
        .on_conflict_do_update(
            index_elements=[PlatformTable.c.ord_id],
            set_={"user_id": user_id, "name": name, 'url': url, 'average_views': average_views}
        )
    )
    async with begin_connection() as conn:
        await conn.execute(query)