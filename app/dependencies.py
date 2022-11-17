from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import db_session as _db_session
from app.mq import create_channel, PikaChannel
from app.config import settings
from app.errors import NoAMQPConnection


async def db_session() -> AsyncSession:
    async with _db_session() as session:
        yield session


async def mq_channel() -> PikaChannel:
    if PikaChannel.pika_connection:
        async with create_channel() as channel:
            yield channel
    else:
        raise NoAMQPConnection(settings.mq_connection_string)
