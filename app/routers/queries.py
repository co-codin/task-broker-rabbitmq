import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.dependencies import db_session, mq_channel, get_user
from app.crud.crud_query import select_task, create_query

LOG = logging.getLogger(__name__)
router = APIRouter()


class CreateRequest(BaseModel):
    query: dict


@router.get('/{guid}')
async def get_task(guid: str, session:AsyncSession = Depends(db_session), user: dict = Depends(get_user)):
    item = await select_task(session, guid)
    if item.identity_id != user['identity_id']:
        raise HTTPException(status_code=404)

    return {
        'guid': item.guid,
        'compiled_query': item.compiled_query,
        'run_id': item.last_run_id,
        'error': item.error_description,
        'status': item.status
    }


@router.post('/')
async def send_query(create: CreateRequest,
                     session: AsyncSession = Depends(db_session),
                     mq=Depends(mq_channel),
                     user: dict = Depends(get_user)):
    query_json = json.dumps(create.query)
    query = await create_query(session, query_json, identity_id=user['identity_id'])

    await mq.basic_publish(settings.exchange_compile, 'task', json.dumps({
        'guid': query.guid,
        'query': query_json,
        'identity_id': user['identity_id']
    }))
    LOG.info(f'Send query request {query.guid} sent to compiler')

    return {
        'query_id': query.guid,
    }
