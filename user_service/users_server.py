#!/usr/bin/env python3

import asyncio
import bcrypt
import json

from .users_db import UserDatabase
from ophoto.lib.rpc_server import RPCServer

import tornado.options
from tornado.options import define, options

define("port", default=8890, help="run on the given port", type=int)
define("db_host", default="127.0.0.1", help="user database host")
define("db_port", default=27017, help="user database port")
define("db_database", default="users", help="user database name")

class UserServer(RPCServer):
    def __init__(self, routing_key, db):
        super().__init__(routing_key, db)
        self.scheme = [{'op': 'user.create', 'handler': self.user_create, 'args': ['_id', 'user']}]


    async def user_create(self, _id, user):
        try:
            user_id = await self.db.create_user(_id, user)
        except Exception as err:
            return({"code": 999, "message": err.args[0]})
        return ({"code": 1000, "message": "User is created", "user_id": user_id})



async def user_rpc_server():
    db = UserDatabase(options.db_host, options.db_port, options.db_database)
    server = UserServer('user', db)
    await server.connect()


tornado.options.parse_command_line()
event_loop = asyncio.get_event_loop()
event_loop.run_until_complete(user_rpc_server())
event_loop.run_forever()
