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
        self.scheme = [
            {'op': 'user.create', 'handler': self.user_create, 'args': ['_id', 'user']},
            {'op': 'user.find', 'handler': self.user_find, 'args': ['user', 'search_type']},
            {'op': 'user.find_people', 'handler': self.find_people, 'args': ['user', 'query', 'search_type']},
            {'op': 'user.get', 'handler': self.user_get, 'args': ['name']},
            {'op': 'user.get_follow', 'handler': self.user_get_follow, 'args': ['name', 'follow']},
            {'op': 'user.set_image', 'handler': self.user_set_image, 'args': ['name', 'image_id']},
            {'op': 'user.set_bio', 'handler': self.user_set_bio, 'args': ['name', 'bio']},
            {'op': 'user.follow', 'handler': self.user_follow, 'args': ['name', 'follow_name', 'value']},
        ]


    async def user_create(self, _id, user):
        try:
            user_id = await self.db.create_user(_id, user)
        except Exception as err:
            return({"code": 999, "message": err.args[0]})
        return ({"code": 1000, "message": "User is created", "user_id": user_id})

    async def user_find(self, user, search_type):
        users = await self.db.find_related(user, search_type)
        user_names = []
        for user in users:
            user_names.append(user["name"])
        print(user_names)
        return({"code": 1000, "message": "Query succeeded", "users": user_names})

    async def find_people(self, user, query, search_type):
        users = await self.db.find_people(user, query, search_type)
        user_names = []
        for user in users:
            user_names.append(user["name"])
        print(user_names)
        return({"code": 1000, "message": "Query succeeded", "users": user_names})

    async def user_get(self, name):
        user = await self.db.get_user(name)
        if user is None:
            return({"code": 999, "message": "No such user"})
        return({"code": 1000, "message": "Got user", "bio": user.bio, "follows": user.follows, "image_id": user.image_id})

    async def user_get_follow(self, name, follow):
        user = await self.db.get_user(name)
        if user is None:
            return({"code": 999, "message": "No such user"})
        follows = 0
        if follow in user.follows:
            follows = 1
        return({"code": 1000, "message": "Got follow", "follows": follows})

    async def user_set_image(self, name, image_id):
        user = await self.db.get_user(name)
        if user is None:
            return({"code": 999, "message": "No such user"})
        await self.db.update_user_info(name, image_id, user.bio)
        return({"code": 1000, "message": "User updated"})

    async def user_set_bio(self, name, bio):
        user = await self.db.get_user(name)
        if user is None:
            return({"code": 999, "message": "No such user"})
        await self.db.update_user_info(name, user.image_id, bio)
        return({"code": 1000, "message": "User updated"})

    async def user_follow(self, name, follow_name, value):
        user = await self.db.get_user(name)
        follow_user = await self.db.get_user(follow_name)
        if user is None or follow_user is None:
            return({"code": 999, "message": "No such user"})
        await self.db.user_set_follow(name, follow_name, value)
        return({"code": 1000, "message": "User updated"})

async def user_rpc_server():
    db = UserDatabase(options.db_host, options.db_port, options.db_database)
    server = UserServer('user', db)
    await server.connect()


tornado.options.parse_command_line()
event_loop = asyncio.get_event_loop()
event_loop.run_until_complete(user_rpc_server())
event_loop.run_forever()
