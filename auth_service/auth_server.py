#!/usr/bin/env python3

import asyncio
import bcrypt
import json

from .auth_db import AuthDatabase
from .token_manager import TokenManager
from ophoto.lib.rpc_server import RPCServer

import tornado.escape
import tornado.options
from tornado.options import define, options

define("port", default=8889, help="run on the given port", type=int)
define("db_host", default="127.0.0.1", help="user database host")
define("db_port", default=27017, help="user database port")
define("db_database", default="auth", help="user database name")

class AuthServer(RPCServer):
    def __init__(self, routing_key, db):
        super().__init__(routing_key, db)
        self.tok_man = TokenManager()
        self.scheme = [
            {'op': 'auth.create', 'handler': self.auth_create, 'args': ['_id', 'user', 'password']},
            {'op': 'auth.login', 'handler': self.auth_login, 'args': ['user', 'password']},
            {'op': 'auth.logout', 'handler': self.auth_logout, 'args': ['token']},
            {'op': 'auth.check', 'handler': self.auth_check, 'args': ['token']},
        ]


    async def auth_create(self, _id, user, password):
        loop = asyncio.get_event_loop()
        # NOTE: Original logic used some kind of to_unicode() functions for password
        hashed_password = await loop.run_in_executor(None, bcrypt.hashpw,
                                                     tornado.escape.utf8(password), bcrypt.gensalt())
        try:
            user_id = await self.db.create_user(_id, user, tornado.escape.to_unicode(hashed_password))
        except Exception as err:
            return({"code": 999, "message": err.args[0]})
        return ({"code": 1000, "message": "User is created", "user_id": str(user_id)})

    async def auth_login(self, user, password):
        user_obj = await self.db.get_user(user)
        if user_obj is None:
            return ({"code": 999, "message": "Invalid user/password pair"})
        loop = asyncio.get_event_loop()
        hashed_password = await loop.run_in_executor(
            None,
            bcrypt.hashpw,
            tornado.escape.utf8(password),
            tornado.escape.utf8(user_obj.hashed_password),
        )
        hashed_password = tornado.escape.to_unicode(hashed_password)
        if hashed_password == user_obj.hashed_password:
            token = self.tok_man.generate(user)
            return ({"code": 1000, "token": token, "message": "Authenticated"})
        return ({"code": 999, "message": "Invalid user/password pair"})

    async def auth_logout(self, token):
        if (self.tok_man.clear(token)):
            return ({"code": 1000, "message": "Token cleared"})
        return ({"code": 999, "message": "Invalid token"})

    async def auth_check(self, token):
        user = self.tok_man.check(token)
        if (user is None):
            return ({"code": 999, "message": "Invalid token"})
        return ({"code": 1000, "user": user, "message": "Token accepted"})

async def auth_rpc_server():
    db = AuthDatabase(options.db_host, options.db_port, options.db_database)
    server = AuthServer('auth', db)
    await server.connect()


tornado.options.parse_command_line()
event_loop = asyncio.get_event_loop()
event_loop.run_until_complete(auth_rpc_server())
event_loop.run_forever()
