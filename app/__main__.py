import json
import logging
import httpx
import asyncio

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers import queries
from app.mq import create_channel
from app.crud.crud_query import (
    update_compile_query_status, update_execute_query_status,
    update_compile_query_last_run_id
)
from app.models import QUERY_STATUS
from app.utils.parse_utils import get_payload_value, deserialize_json_query
from app.config import settings
from app.logger_config import config_logger
from app.errors import (
    APIError, NoDBConnection, DBError, DeserializeJSONQueryError, DictKeyError,
    QueryExecutorTimeoutError
)

config_logger()
LOG = logging.getLogger(__name__)

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

        await channel.exchange_declare(settings.exchange_execute, 'direct')
        await channel.queue_declare(settings.query_execute_result)
        await channel.queue_bind(settings.query_execute_result, settings.exchange_execute, 'result')

        asyncio.create_task(update_compile_status())
        asyncio.create_task(update_execute_status())


async def update_compile_status():
    async with create_channel() as channel:
        try:
            async for delivery_tag, body in channel.consume(settings.query_compile_result):
                payload = deserialize_json_query(body)
                guid, query = get_payload_value(payload, 'guid'), get_payload_value(payload, 'query')
                LOG.info(
                    f'Received compile update for {guid}, result is {query}'
                )
                await update_compile_query_status(guid, query, QUERY_STATUS.COMPILED.value)
                await post_query_to_executor(guid, query)
        except (NoDBConnection, DBError) as db_err:
            LOG.error(db_err)
        except (DeserializeJSONQueryError, DictKeyError) as parse_err:
            await channel.basic_reject(delivery_tag)
            LOG.error(parse_err)
        except QueryExecutorTimeoutError as query_executor_api_err:
            LOG.error(query_executor_api_err)
    asyncio.create_task(update_compile_status())


async def update_execute_status():
    async with create_channel() as channel:
        try:
            async for delivery_tag, body in channel.consume(settings.query_execute_result):
                payload = deserialize_json_query(body)
                guid, result = get_payload_value(payload, 'guid'), get_payload_value(payload, 'status')
                LOG.info(
                    f'Received execute update for {guid}, result is {payload}'
                )
                await update_execute_query_status(guid, result)
        except (NoDBConnection, DBError) as db_err:
            LOG.error(db_err)
        except (DeserializeJSONQueryError, DictKeyError) as parse_err:
            await channel.basic_reject(delivery_tag)
            LOG.error(parse_err)
    asyncio.create_task(update_execute_status())


async def post_query_to_executor(guid: str, query: str):
    async with httpx.AsyncClient() as requests:
        try:
            r = await requests.post(f'{settings.api_query_executor}/queries/',
                                    content=json.dumps({
                                        'guid': guid,
                                        'query': query,
                                        'db': 'raw',
                                        'result_destinations': ['table',
                                                                'file']
                                    }))
            if r.status_code != 200:
                raise Exception(
                    f'Task {guid} failed to sent to execution: {r.text}')
            data = r.json()
            LOG.info(f'Task {guid} sent for execution: {data}')
            await update_compile_query_last_run_id(guid=guid, last_run_id=data['id'])
        except (httpx.ConnectTimeout, httpx.ConnectError):
            raise QueryExecutorTimeoutError(f'{settings.api_query_executor}/queries/')
        except Exception as e:
            LOG.info(f'Task {guid} failed to send to execution: {e}')
            await update_compile_query_status(guid, query, QUERY_STATUS.ERROR_EXECUTION_ERROR.value)
        else:
            LOG.info(f'Task {guid} sent for db execution')


@app.exception_handler(APIError)
def api_exception_handler(request_: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": str(exc)},
    )


@app.get('/ping')
def ping():
    return {'status': 'ok'}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
