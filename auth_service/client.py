#!/usr/bin/env python3

import asyncio
import uuid
import aioamqp
import sys

class FibonacciRpcClient(object):
    def __init__(self):
        self.transport = None
        self.protocol = None
        self.channel = None
        self.callback_queue = None
        self.exchange_name = None
        self.routing_key = None
        self.waiter = asyncio.Event()

    async def connect(self):
        """ an `__init__` method can't be a coroutine"""
        self.transport, self.protocol = await aioamqp.connect()
        self.channel = await self.protocol.channel()
        self.exchange_name = 'request_routing'
        self.routing_key = sys.argv[1]

        await self.channel.exchange(self.exchange_name, 'direct')
        result = await self.channel.queue_declare(exclusive=True)
        self.callback_queue = result['queue']

        await self.channel.basic_consume(
            self.on_response,
            no_ack=True,
            queue_name=self.callback_queue,
        )

    async def on_response(self, channel, body, envelope, properties):
        if self.corr_id == properties.correlation_id:
            self.response = body

        self.waiter.set()

    async def call(self, n):
        if not self.protocol:
            await self.connect()
        self.response = None
        self.corr_id = str(uuid.uuid4())
        await self.channel.basic_publish(
            payload=str(n),
            exchange_name=self.exchange_name,
            routing_key=self.routing_key,
            properties={
                'reply_to': self.callback_queue,
                'correlation_id': self.corr_id,
            },
        )
        await self.waiter.wait()

        await self.protocol.close()
        return int(self.response)


async def rpc_client():
    fibonacci_rpc = FibonacciRpcClient()
    print(" [x] Requesting fib(30)")
    response = await fibonacci_rpc.call(30)
    print(" [.] Got %r" % response)


asyncio.get_event_loop().run_until_complete(rpc_client())
