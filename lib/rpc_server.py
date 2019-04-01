#!/usr/bin/env python3

import asyncio
import aioamqp
import json

from ophoto.lib.route import *

class RPCServer(object):
    def __init__(self, routing_key, db):
        self.transport = None
        self.protocol = None
        self.channel = None
        self.exchange_name = 'request_routing'
        self.routing_key = routing_key
        self.db = db
        self.scheme = None

    async def connect(self):
        """ an `__init__` method can't be a coroutine"""
        print("CONNECT")
        self.transport, self.protocol = await aioamqp.connect()

        self.channel = await self.protocol.channel()

        await self.channel.exchange(self.exchange_name, 'direct')

        result = await self.channel.queue_declare(exclusive=True)
        queue_name = result['queue']

        await self.channel.queue_bind(
            exchange_name=self.exchange_name,
            queue_name=queue_name,
            routing_key=self.routing_key,
        )

        await self.channel.basic_consume(self.on_request, queue_name=queue_name)
        print(" [x] Awaiting RPC requests")


    async def on_request(self, channel, body, envelope, properties):
        msg = json.loads(body)
        response = await route(self.scheme, msg)
        await channel.basic_publish(
            payload=json.dumps(response),
            exchange_name='',
            routing_key=properties.reply_to,
            properties={
                'correlation_id': properties.correlation_id,
            },
        )
        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)
