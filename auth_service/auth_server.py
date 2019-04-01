#!/usr/bin/env python3

import asyncio
import aioamqp
import sys


def fib(n):
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fib(n-1) + fib(n-2)


class FibonacciRpcServer(object):
    def __init__(self):
        self.transport = None
        self.protocol = None
        self.channel = None

    async def connect(self):
        """ an `__init__` method can't be a coroutine"""
        self.transport, self.protocol = await aioamqp.connect()

        self.channel = await self.protocol.channel()
        exchange_name = 'request_routing'

        await self.channel.exchange(exchange_name, 'direct')

        result = await self.channel.queue_declare(exclusive=True)
        queue_name = result['queue']

        await self.channel.queue_bind(
            exchange_name=exchange_name,
            queue_name=queue_name,
            routing_key= sys.argv[1]
        )

        await self.channel.basic_consume(self.on_request, queue_name=queue_name)
        print(" [x] Awaiting RPC requests")


    async def on_request(self, channel, body, envelope, properties):
        n = int(body)

        print(" [.] fib(%s)" % n)
        response = fib(n)

        await channel.basic_publish(
            payload=str(response),
            exchange_name='',
            routing_key=properties.reply_to,
            properties={
                'correlation_id': properties.correlation_id,
            },
        )

        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)


async def rpc_server():
    server = FibonacciRpcServer()
    await server.connect()


event_loop = asyncio.get_event_loop()
event_loop.run_until_complete(rpc_server())
event_loop.run_forever()
