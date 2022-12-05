import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.models import Query
from app.config import settings
from app.dependencies import db_session, mq_channel


LOG = logging.getLogger(__name__)
router = APIRouter()


class CreateRequest(BaseModel):
    query: dict


@router.get('/{guid}')
async def get_task(guid: str, session:AsyncSession = Depends(db_session)):
    item = await session.execute(select(Query).where(Query.guid == guid))
    item = item.scalars().first()
    return {
        'guid': item.guid,
        'compiled_query': item.compiled_query,
        'run_id': item.last_run_id,
        'status': item.status
    }


@router.post('/')
async def send_query(create: CreateRequest, session:AsyncSession = Depends(db_session), mq = Depends(mq_channel)):
    query_json = json.dumps(create.query)
    query = Query(
        query=query_json
    )
    session.add(query)
    await session.commit()
    LOG.info(f'Creating send query request with guid {query.guid}')

    await mq.basic_publish(settings.exchange_compile, 'task', json.dumps({
        'guid': query.guid,
        'query': query_json
    }))
    LOG.info(f'Qreating send query request {query.guid} sent to compiler')

    return {
        'query_id': query.guid,
    }
