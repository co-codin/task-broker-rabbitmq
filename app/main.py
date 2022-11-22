import json
import logging
import httpx
import asyncio

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers import queries
from app.mq import create_channel
from app.crud.crud_query import (
    update_compile_query_status, update_execute_query_status
)
from app.utils.parse_utils import parse_mq_query
from app.config import settings
from app.errors import (
    APIError, NoDBConnection, DBError, DeserializeJSONQueryError, DictKeyError,
    QueryExecutorTimeoutError
)

app = FastAPI()
app.include_router(queries.router, prefix='/query')

logger = logging.getLogger(__name__)


@app.on_event('startup')
async def declare_queues():
    async with create_channel() as channel:
        await channel.exchange_declare(settings.exchange_compile, 'direct')
        await channel.queue_declare(settings.query_compile)
        await channel.queue_declare(settings.query_compile_result)
        await channel.queue_bind(settings.query_compile, settings.exchange_compile, 'task')
        await channel.queue_bind(settings.query_compile_result, settings.exchange_compile, 'result')

        await channel.exchange_declare(settings.exchange_execute, 'direct')
        await channel.queue_declare(settings.query_execute_result)
        await channel.queue_bind(settings.query_execute_result, settings.exchange_execute, 'result')

        asyncio.create_task(update_compile_status())
        asyncio.create_task(update_execute_status())


async def update_compile_status():
    async with create_channel() as channel:
        try:
            async for delivery_tag, body in channel.consume(settings.query_compile_result):
                guid, query = parse_mq_query(body, key='query')
                await update_compile_query_status(guid, query)
                await post_query_to_executor(guid, query)
        except (NoDBConnection, DBError) as db_err:
            logger.error(db_err)
        except (DeserializeJSONQueryError, DictKeyError) as parse_err:
            await channel.basic_reject(delivery_tag)
            logger.error(parse_err)
        except QueryExecutorTimeoutError as query_executor_api_err:
            logger.error(query_executor_api_err)
    asyncio.create_task(update_compile_status())


async def update_execute_status():
    async with create_channel() as channel:
        try:
            async for delivery_tag, body in channel.consume(settings.query_execute_result):
                guid, result = parse_mq_query(body, key='result')
                await update_execute_query_status(guid, result)
        except (NoDBConnection, DBError) as db_err:
            logger.error(db_err)
        except (DeserializeJSONQueryError, DictKeyError) as parse_err:
            await channel.basic_reject(delivery_tag)
            logger.error(parse_err)
    asyncio.create_task(update_execute_status())


async def post_query_to_executor(guid: str, query: str):
    async with httpx.AsyncClient() as requests:
        try:
            r = await requests.post(
                f'{settings.api_query_executor}/queries/',
                content=json.dumps({
                    'guid': guid,
                    'query': query,
                    'db': 'raw',
                }))
        except (httpx.ConnectTimeout, httpx.ConnectError):
            raise QueryExecutorTimeoutError(f'{settings.api_query_executor}/queries/')


@app.exception_handler(APIError)
def api_exception_handler(request_: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": str(exc)},
    )


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
