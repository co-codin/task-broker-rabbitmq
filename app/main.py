import json

import asyncio
from fastapi import FastAPI
from sqlalchemy import update

from app.routers import queries
from app.mq import create_channel
from app.database import db_session
from app.models import Query, QUERY_STATUS
from app.config import settings


app = FastAPI()
app.include_router(queries.router, prefix='/query')


@app.on_event('startup')
async def declare_queues():
    async with create_channel() as channel:
        await channel.exchange_declare(settings.exchange_compile, 'direct')
        await channel.queue_declare(settings.query_compile)
        await channel.queue_declare(settings.query_compile_result)
        await channel.queue_bind(settings.query_compile, settings.exchange_compile, 'task')
        await channel.queue_bind(settings.query_compile_result, settings.exchange_compile, 'result')

        asyncio.create_task(update_compile_status())


async def update_compile_status():
    async with create_channel() as channel:
        async for body in channel.consume(settings.query_compile_result):
            payload = json.loads(body)
            guid = payload['guid']
            query = payload['query']

            async with db_session() as session:
                await session.execute(
                    update(Query)
                        .where(Query.guid == guid)
                        .values(compiled_query=query, status=QUERY_STATUS.COMPILED.value)
                )

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
