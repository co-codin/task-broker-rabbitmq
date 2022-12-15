import logging

import asyncio
from fastapi import FastAPI

from app.routers import queries
from app.mq import create_channel
from app.config import settings
from app.services.query_lifecycle import process_compile_update, process_execution_update
from app.logger_config import config_logger
from app.auth import load_jwks


config_logger()
LOG = logging.getLogger(__name__)

app = FastAPI()
app.include_router(queries.router, prefix='/query')


@app.on_event('startup')
async def on_startup():
    await load_jwks()

    async with create_channel() as channel:
        await channel.exchange_declare(settings.exchange_compile, 'direct')
        await channel.queue_declare(settings.query_compile)
        await channel.queue_declare(settings.query_compile_result)
        await channel.queue_bind(settings.query_compile, settings.exchange_compile, 'task')
        await channel.queue_bind(settings.query_compile_result, settings.exchange_compile, 'result')

        await channel.exchange_declare(settings.exchange_execute, 'direct')
        await channel.queue_declare(settings.query_execute_result)
        await channel.queue_bind(settings.query_execute_result, settings.exchange_execute, 'result')

        asyncio.create_task(consume(settings.query_compile_result, process_compile_update))
        asyncio.create_task(consume(settings.query_execute_result, process_execution_update))


async def consume(query, func):
    while True:
        try:
            LOG.info(f'Starting {query} worker')
            async with create_channel() as channel:
                async for body in channel.consume(query):
                    try:
                        await func(body)
                    except Exception as e:
                        LOG.exception(f'Failed to process message {body}: {e}')
        except Exception as e:
            LOG.exception(f'Worker {query} failed: {e}')

        await asyncio.sleep(0.5)


@app.get('/ping')
def ping():
    return {'status': 'ok'}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
