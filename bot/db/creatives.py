from datetime import datetime
import typing as t
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

from .base_db import METADATA, begin_connection
from enums import Status


class CreativeRow(t.Protocol):
    id: int
    created_at: datetime
    user_id: int
    campaign_id: int
    content_type: str
    file_id: str
    file_path: str
    token: str
    status: str


CreativeTable: sa.Table = sa.Table(
    "creatives",
    METADATA,

    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.now()),
    sa.Column('user_id', sa.BigInteger),
    sa.Column('campaign_id', sa.Integer),
    sa.Column('content_type', sa.String(255)),
    sa.Column('text', sa.Text),
    sa.Column('file_id', sa.String(255)),
    sa.Column('file_path', sa.String(255)),
    sa.Column('token', sa.String(255)),
    sa.Column('status', sa.String(255), default=Status.ACTIVE.value),
)


# добавляет оплату
async def add_creative(
        user_id: int,
        campaign_id: int,
        content_type: str,
        token: str,
        text: str = None,
        file_path: str = None,
        file_id: str = None,
) -> int:
    now = datetime.now()
    query = CreativeTable.insert().values(
            created_at=now,
            user_id=user_id,
            campaign_id=campaign_id,
            content_type=content_type,
            text=text,
            file_id=file_id,
            file_path=file_path,
            token=token,
        )

    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.inserted_primary_key


# обновляет креатив
async def update_creative(
        creative_id: int,
        token: str,
        status: str,
) -> None:
    query = CreativeTable.update().where(creative_id=creative_id)

    if token:
        query = query.values(token=token)

    if status:
        query = query.values(status=status)

    async with begin_connection() as conn:
        await conn.execute(query)
