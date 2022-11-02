from app.database import db_session as _db_session
from app.mq import create_channel, PikaChannel


async def db_session():
    async with _db_session() as session:
        yield session


async def mq_channel() -> PikaChannel:
    async with create_channel() as channel:
        yield channel
