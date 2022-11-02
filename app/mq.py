import logging
import asyncio
import pika
from contextlib import asynccontextmanager
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.exceptions import ChannelClosedByClient

from app.config import settings


LOG = logging.getLogger(__name__)
PIKA_CONNECTION = None


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
    def __init__(self, channel):
        self._channel = channel
        self._close_callbacks = []
        self._channel.add_on_close_callback(self._close_callback)

    def _close_callback(self, *args, **kwargs):
        for cbk in self._close_callbacks:
            cbk(*args, **kwargs)

    async def queue_declare(self, queue: str):
        async with wait_for_callback('Queue.DeclareOk') as callback:
            self._channel.queue_declare(queue, callback=callback)

    async def exchange_declare(self, exchange: str, exchange_type: str):
        async with wait_for_callback('Exchange.DeclareOk') as callback:
            self._channel.exchange_declare(exchange, exchange_type, callback=callback)

    async def queue_bind(self, queue, exchange, routing_key=None):
        async with wait_for_callback('Queue.BindOk') as callback:
            self._channel.queue_bind(queue, exchange, routing_key, callback=callback)

    async def basic_ack(self, delivery_tag):
        self._channel.basic_ack(delivery_tag)

    async def basic_publish(self, exchange: str, routing_key: str, body: str):
        self._channel.basic_publish(exchange, routing_key, body)

    async def consume(self, queue):
        loop = asyncio.get_running_loop()
        messages = asyncio.Queue()
        self._channel.basic_consume(
            queue,
            on_message_callback=lambda _channel, method, _props, body: messages.put_nowait((method.delivery_tag, body)),
            auto_ack=False
        )

        fut = loop.create_future()

        def on_close_callback(ch, reason):
            try:
                raise reason
            except ChannelClosedByClient:
                fut.cancel()
            except:
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
                yield body

                await self.basic_ack(delivery_tag)
        finally:
            self._close_callbacks.remove(on_close_callback)


async def create_connection():
    global PIKA_CONNECTION
    if PIKA_CONNECTION:
        return PIKA_CONNECTION

    loop = asyncio.get_running_loop()

    fut = loop.create_future()
    AsyncioConnection(
        pika.URLParameters(settings.mq_connection_string),
        on_open_callback=lambda c: fut.set_result(c),
        on_open_error_callback=lambda c, exc: fut.set_exception(exc),
        on_close_callback=lambda c, exc: fut.set_exception(exc)
    )
    conn = await fut
    PIKA_CONNECTION = conn
    return conn


@asynccontextmanager
async def create_channel() -> PikaChannel:
    loop = asyncio.get_running_loop()
    conn = await create_connection()

    fut = loop.create_future()
    conn.channel(on_open_callback=lambda ch: fut.set_result(ch))
    channel = await fut

    try:
        yield PikaChannel(channel)
    finally:
        channel.close()
