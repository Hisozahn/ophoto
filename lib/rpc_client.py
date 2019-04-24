#!/usr/bin/env python3

import asyncio
import uuid
import aioamqp
import sys
import json

class RPCClient(object):
    def __init__(self):
        self.transport = None
        self.protocol = None
        self.channel = None
        self.callback_queue = None
        self.exchange_name = None
        self.events = {}

    async def connect(self):
        self.transport, self.protocol = await aioamqp.connect()
        self.channel = await self.protocol.channel()
        self.exchange_name = 'request_routing'

        await self.channel.exchange(self.exchange_name, 'direct')
        result = await self.channel.queue_declare()
        self.callback_queue = result['queue']

        await self.channel.basic_consume(
            self.on_response,
            no_ack=True,
            queue_name=self.callback_queue,
        )

    async def on_response(self, channel, body, envelope, properties):
        if properties.correlation_id in self.events:
            self.events[properties.correlation_id]['response'] = body
            self.events[properties.correlation_id]['event'].set()

    async def call(self, routing_key, msg):
        response = None
        corr_id = str(uuid.uuid4())
        await self.channel.basic_publish(
            payload=json.dumps(msg),
            exchange_name=self.exchange_name,
            routing_key=routing_key,
            properties={
                'reply_to': self.callback_queue,
                'correlation_id': corr_id,
            },
        )
        event = asyncio.Event();
        self.events[corr_id] = {'event': event, 'response': None}
        await event.wait()
        response = self.events[corr_id]['response']
        del(self.events[corr_id])

#        await self.protocol.close()

        return json.loads(response)
