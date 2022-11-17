import json

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import settings
from app.dependencies import db_session, mq_channel
from app.crud.crud_query import select_task, create_query


router = APIRouter()


class CreateRequest(BaseModel):
    query: dict


@router.get('/{guid}')
async def get_task(guid: str, session: AsyncSession = Depends(db_session)):
    item = await select_task(session, guid)
    return {
        'guid': item.guid,
        'compiled_query': item.compiled_query,
        'status': item.status
    }


@router.post('/')
async def send_query(create: CreateRequest, session: AsyncSession = Depends(db_session), mq=Depends(mq_channel)):
    query_json = json.dumps(create.query)
    query = await create_query(session, query_json)

    await mq.basic_publish(settings.exchange_compile, 'task', json.dumps({
        'guid': query.guid,
        'query': query_json
    }))

    return {
        'query_id': query.guid,
    }
