#!/usr/bin/env python3

import asyncio
import bcrypt
import json

from .image_db import ImageDatabase
from ophoto.lib.rpc_server import RPCServer

import tornado.options
from tornado.options import define, options
from bson import ObjectId

define("port", default=8892, help="run on the given port", type=int)
define("db_host", default="127.0.0.1", help="image database host")
define("db_port", default=27017, help="image database port")
define("db_database", default="images", help="image database name")

class ImageServer(RPCServer):
    def __init__(self, routing_key, db):
        super().__init__(routing_key, db)
        self.scheme = [
            {'op': 'image.create', 'handler': self.image_create, 'args': ['image']},
            {'op': 'image.get', 'handler': self.image_get, 'args': ['image_id']},
        ]

    async def image_get(self, image_id):
        image = await self.db.get_image(ObjectId(image_id))
        if image is None:
            return({"code": 999, "message": "No such image"})
        return({"code": 1000, "message": "Got image", "image": image.data})



    async def image_create(self, image):
        try:
            image_id = await self.db.create_image(image)
        except Exception as err:
            return({"code": 999, "message": err.args[0]})
        return ({"code": 1000, "message": "Image is created", "image_id": image_id})



async def image_rpc_server():
    db = ImageDatabase(options.db_host, options.db_port, options.db_database)
    server = ImageServer('image', db)
    await server.connect()


tornado.options.parse_command_line()
event_loop = asyncio.get_event_loop()
event_loop.run_until_complete(image_rpc_server())
event_loop.run_forever()
