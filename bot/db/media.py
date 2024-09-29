from datetime import datetime
import typing as t
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

from .base_db import METADATA, begin_connection
from enums import Status


class MediaRow(t.Protocol):
    id: int
    created_at: datetime
    user_id: int
    creative_ord_id: str
    ord_id: str
    content_type: str
    text: str
    file_id: str
    file_path: str
    file_size: int


MediaTable: sa.Table = sa.Table(
    "media",
    METADATA,

    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('user_id', sa.BigInteger),
    sa.Column('creative_ord_id', sa.String(255)),
    sa.Column('ord_id', sa.String(255)),
    sa.Column('file_id', sa.String(255)),
    sa.Column('content_type', sa.String(255)),
)


# добавляет оплату
async def add_media(
        user_id: int,
        creative_ord_id: str,
        content_type: str,
        file_id: str,
        ord_id: str,
) -> int:
    now = datetime.now()
    query = MediaTable.insert().values(
            created_at=now,
            user_id=user_id,
            creative_ord_id=creative_ord_id,
            ord_id=ord_id,
            content_type=content_type,
            file_id=file_id
        )

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.inserted_primary_key
