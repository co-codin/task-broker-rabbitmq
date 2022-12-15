from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from app.database import db_session as _db_session
from app.mq import create_channel, PikaChannel
from app.auth import decode_jwt


bearer = HTTPBearer()


async def db_session():
    async with _db_session() as session:
        yield session


async def mq_channel() -> PikaChannel:
    async with create_channel() as channel:
        yield channel


async def get_user(token = Depends(bearer)) -> dict:
    try:
        return await decode_jwt(token.credentials)
    except:
        raise HTTPException(status_code=401)
