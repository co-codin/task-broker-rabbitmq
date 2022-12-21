import json
import logging

import httpx
from sqlalchemy import update, select

from app.db.session import db_session
from app.models import Query, QUERY_STATUS
from app.config import settings


LOG = logging.getLogger(__name__)


async def process_execution_update(body: str):
    payload = json.loads(body)
    guid = payload['guid']
    result = payload['status']

    LOG.info(f'Received execute update for {guid}, result is {payload}')

    async with db_session() as session:
        status = QUERY_STATUS.DONE.value
        if result != 'done':
            status = QUERY_STATUS.ERROR_EXECUTION_ERROR.value

        await session.execute(
            update(Query)
            .where(Query.guid == guid)
            .values(status=status)
        )


async def process_compile_update(body: str):
    payload = json.loads(body)
    guid = payload['guid']
    status = payload['status']
    error = payload.get('error')
    query = payload.get('query')

    LOG.info(f'Received compile update for {guid}, result is {status}: {query or error}')

    status = {
        'compiled': QUERY_STATUS.COMPILED,
    }.get(status, QUERY_STATUS.ERROR_COMPILATION_ERROR)
    async with db_session() as session:
        await session.execute(
            update(Query)
                .where(Query.guid == guid)
                .values(
                    compiled_query=query,
                    status=status.value,
                    error_description=error
                )
        )

    await send_for_execution(guid)


async def send_for_execution(guid: str):
    async with db_session() as session:
        query = await session.execute(select(Query).where(Query.guid == guid))
        query = query.scalars().first()

    if query.status != QUERY_STATUS.COMPILED.value:
        return

    try:
        async with httpx.AsyncClient() as requests:
            r = await requests.post(f'{settings.api_query_executor}/queries/', content=json.dumps({
                'guid': query.guid,
                'query': query.compiled_query,
                'db': 'raw',
                'result_destinations': ['table', 'file'],
                'identity_id': query.identity_id,
            }))
            if r.status_code != 200:
                raise Exception(f'Rask {query.guid} failed to sent to execution: {r.text}')
            data = r.json()
            LOG.info(f'Task {query.guid} is going to be send for execution: {data}')

            async with db_session() as session:
                await session.execute(
                    update(Query).where(Query.guid == query.guid).values(last_run_id=data['id'])
                )
    except Exception as e:
        LOG.info(f'Task {query.guid} failed to send to execution: {e}')

        async with db_session() as session:
            await session.execute(
                update(Query)
                    .where(Query.guid == query.guid)
                    .values(compiled_query=query, status=QUERY_STATUS.ERROR_EXECUTION_ERROR.value)
            )

    LOG.info(f'Task {query.guid} sent for db execution')
