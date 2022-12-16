from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

from app.db.session import db_session as _db_session
from app.config import settings
from app.errors import NoAMQPConnection

from app.mq import create_channel, PikaChannel
from app.auth import decode_jwt


bearer = HTTPBearer()


async def db_session() -> AsyncSession:
    async with _db_session() as session:
        yield session


async def mq_channel() -> PikaChannel:
    if PikaChannel.pika_connection:
        async with create_channel() as channel:
            yield channel
    else:
        raise NoAMQPConnection(settings.mq_connection_string)


async def get_user(token = Depends(bearer)) -> dict:
    try:
        return await decode_jwt(token.credentials)
    except:
        raise HTTPException(status_code=401)
