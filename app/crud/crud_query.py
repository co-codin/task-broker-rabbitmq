import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import db_session
from app.models import Query, QUERY_STATUS
from app.errors import NoTaskFound

LOG = logging.getLogger(__name__)


async def update_compile_query_status(guid: str, query: str, status: QUERY_STATUS):
    async with db_session() as session:
        await session.execute(
            update(Query)
            .where(Query.guid == guid)
            .values(compiled_query=query, status=status)
        )


async def update_compile_query_last_run_id(guid: str, last_run_id: str):
    async with db_session() as session:
        await session.execute(
            update(Query).where(Query.guid == guid).values(
                last_run_id=last_run_id)
        )


async def update_execute_query_status(guid: str, result: str):
    async with db_session() as session:
        status_ = QUERY_STATUS.DONE.value
        if result != 'done':
            status_ = QUERY_STATUS.ERROR_EXECUTION_ERROR.value

        await session.execute(
            update(Query)
            .where(Query.guid == guid)
            .values(status=status_)
        )


async def select_task(session: AsyncSession, guid: str) -> Query:
    item = await session.execute(select(Query).where(Query.guid == guid))
    item = item.scalars().first()
    if item is None:
        raise NoTaskFound(guid)
    return item


async def create_query(session: AsyncSession, query_json: str, identity_id: str) -> Query:
    query = Query(
        query=query_json,
        identity_id=identity_id
    )
    session.add(query)
    await session.commit()
    LOG.info(f'Creating send query request with guid {query.guid}')
    return query
