import logging
import asyncio
import pika

from typing import Union
from contextlib import asynccontextmanager

from pika.channel import Channel
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.adapters.utils.connection_workflow import AMQPConnectionWorkflowFailed
from pika.exceptions import (
    ChannelClosedByClient,
    AMQPConnectionError,
    ChannelWrongStateError,
    AMQPError
)

from app.config import settings

LOG = logging.getLogger(__name__)
CONNECTION_FUT: Union[asyncio.Future, None] = None


@asynccontextmanager
async def wait_for_callback(wait_for: str):
    loop = asyncio.get_running_loop()
    fut = loop.create_future()

    def callback(method):
        try:
            if method.method.NAME == wait_for:
                fut.set_result(wait_for)
                return
        except Exception as e:
            fut.set_exception(e)
            return
        fut.set_exception(Exception(method.method.NAME))

    yield callback
    await fut


class PikaChannel:
    pika_connection: Union[AsyncioConnection, None] = None

    def __init__(self, channel: Channel):
        self._channel = channel
        self._close_callbacks = []
        self._channel.add_on_close_callback(self._close_callback)

    def _close_callback(self, *args, **kwargs):
        for cbk in self._close_callbacks:
            cbk(*args, **kwargs)

    async def queue_declare(self, queue: str):
        async with wait_for_callback('Queue.DeclareOk') as callback:
            self._channel.queue_declare(queue, callback=callback, durable=True)

    async def exchange_declare(self, exchange: str, exchange_type: str):
        async with wait_for_callback('Exchange.DeclareOk') as callback:
            self._channel.exchange_declare(exchange, exchange_type, callback=callback, durable=True)

    async def queue_bind(self, queue: str, exchange: str, routing_key: str = None):
        async with wait_for_callback('Queue.BindOk') as callback:
            self._channel.queue_bind(queue, exchange, routing_key, callback=callback)

    async def basic_ack(self, delivery_tag: int):
        self._channel.basic_ack(delivery_tag)

    async def basic_reject(self, delivery_tag: int):
        self._channel.basic_reject(delivery_tag)

    async def basic_publish(self, exchange: str, routing_key: str, body: bytes):
        self._channel.basic_publish(exchange, routing_key, body)

    async def consume(self, queue: str) -> bytes:
        loop = asyncio.get_running_loop()
        messages = asyncio.Queue()
        self._channel.basic_consume(
            queue,
            on_message_callback=lambda _channel, method, _props, body: messages.put_nowait((method.delivery_tag, body)),
            auto_ack=False
        )

        fut = loop.create_future()

        def on_close_callback(ch: Channel, reason: AMQPError):
            try:
                raise reason
            except ChannelClosedByClient:
                fut.cancel()
            except AMQPError:
                fut.set_exception(reason)

        self._close_callbacks.append(on_close_callback)
        try:
            while True:
                msg = asyncio.ensure_future(messages.get())
                await asyncio.wait([msg, fut], return_when=asyncio.FIRST_COMPLETED)

                if fut.done():
                    if fut.cancelled():
                        LOG.debug('Chanel gracefully closed, exiting loop')
                        break
                    raise fut.exception()

                delivery_tag, body = msg.result()
                yield delivery_tag, body

                await self.basic_ack(delivery_tag)
        except AMQPError as amqp_err:
            LOG.error(amqp_err)
        finally:
            self._close_callbacks.remove(on_close_callback)


async def _get_connection() -> AsyncioConnection:
    if PikaChannel.pika_connection:
        return PikaChannel.pika_connection

    while True:
        try:
            conn = await _set_connection()
            break
        except (AMQPConnectionError, AMQPConnectionWorkflowFailed):
            await _handle_failed_attempt_to_connect()

    if PikaChannel.pika_connection is None:
        PikaChannel.pika_connection = conn
    return conn


async def _set_connection() -> AsyncioConnection:
    global CONNECTION_FUT
    loop = asyncio.get_running_loop()

    if CONNECTION_FUT is None:
        CONNECTION_FUT = loop.create_future()
        AsyncioConnection(
            pika.URLParameters(
                settings.mq_connection_string +
                f"?heartbeat={settings.heartbeat}&"
                f"connection_attempts={settings.connection_attempts}&"
                f"retry_delay={settings.retry_delay}"
            ),
            on_open_callback=lambda c: CONNECTION_FUT.set_result(c),
            on_open_error_callback=lambda c, exc: CONNECTION_FUT.set_exception(
                exc),
            on_close_callback=lambda c, exc: _drop_conn(c, exc)
        )
    conn = await CONNECTION_FUT
    return conn


async def _handle_failed_attempt_to_connect():
    global CONNECTION_FUT
    if CONNECTION_FUT:
        LOG.error(
            f"Couldn't connect to RabbitMQ server "
            f"{settings.mq_connection_string}"
        )
        LOG.error(f"Waiting for {settings.timeout} seconds timeout...")
        CONNECTION_FUT = None
    await asyncio.sleep(settings.timeout)


@asynccontextmanager
async def create_channel() -> PikaChannel:
    loop = asyncio.get_running_loop()
    conn = await _get_connection()
    channel_fut = loop.create_future()
    conn.channel(on_open_callback=lambda ch: channel_fut.set_result(ch))
    channel = await channel_fut
    try:
        yield PikaChannel(channel)
    finally:
        _close_channel(channel)


def _close_channel(channel: Channel):
    try:
        channel.close()
    except ChannelWrongStateError as pika_err:
        LOG.error(pika_err)


def _drop_conn(conn: AsyncioConnection, exc: AMQPError):
    LOG.error(f"Connection with RabbitMQ server was closed")
    global CONNECTION_FUT
    PikaChannel.pika_connection = None
    CONNECTION_FUT = None
