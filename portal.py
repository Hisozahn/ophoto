#!/usr/bin/env python3

import aiopg
import bcrypt
import markdown
import os.path
import psycopg2
import re
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.locks
import tornado.options
import tornado.web
import unicodedata
import json
import uuid

from ophoto.lib.rpc_client import RPCClient

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)

SECURE_COOKIE_NAME="ophoto_user"

class Application(tornado.web.Application):
    def __init__(self, rpc_client):
        self.rpc_client = rpc_client
        handlers = [
            (r"/", HomeHandler),
            (r"/auth/create", AuthCreateHandler),
            (r"/auth/login", AuthLoginHandler),
            (r"/auth/logout", AuthLogoutHandler),
            (r"/secret", SecretHandler),
        ]
        settings = dict(
            xsrf_cookies=False,
            cookie_secret="JIPe32fieoHF(Eb32o98fe]32[e3[2u*(FQhue2dsqnjodehiw&*Te2yvdbiew",
            debug=True,
        )
        super(Application, self).__init__(handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie(SECURE_COOKIE_NAME)

class HomeHandler(BaseHandler):
    async def get(self):
        self.write( {"code": 1000, "message": "OK"})


class AuthCreateHandler(BaseHandler):
    async def post(self):
        _id = str(uuid.uuid4())
        user = self.get_argument("user")
        password = self.get_argument("password")
        auth_responce = await self.application.rpc_client.call('auth', {'op': 'auth.create',
                                                                        '_id': _id,
                                                                        'user': user,
                                                                        'password': password})
        user_responce = await self.application.rpc_client.call('user', {'op': 'user.create',
                                                                        '_id': _id,
                                                                        'user': user})
        if auth_responce['code'] != 1000:
            self.write(auth_responce)
            return
        if user_responce['code'] != 1000:
            self.write(user_responce)
            return
            #TODO

        self.set_secure_cookie(SECURE_COOKIE_NAME, str(auth_responce['user_id']))
        self.write( {"code": 1000, "message": "Authenticated"})


class AuthLoginHandler(BaseHandler):
    async def post(self):
        '''
        user = await self.application.db.get_user(self.get_argument("user"))
        if user is None:
            self.write( {"code": 999, "message": "User is not found" })
            return
        hashed_password = await tornado.ioloop.IOLoop.current().run_in_executor(
            None,
            bcrypt.hashpw,
            tornado.escape.utf8(self.get_argument("password")),
            tornado.escape.utf8(user.hashed_password),
        )
        hashed_password = tornado.escape.to_unicode(hashed_password)
        if hashed_password == user.hashed_password:
            self.set_secure_cookie(SECURE_COOKIE_NAME, str(user._id))
            self.write( {"code": 1000, "message": "Authenticated"})
        else:
            self.write( {"code": 999, "message": "Invalid user/password pair"})
        '''


class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie(SECURE_COOKIE_NAME)
        self.write( {"code": 1000, "message": "OK"})

class SecretHandler(BaseHandler):
    async def get(self):
        if not self.current_user:
            self.write({"code": 999, "message": "No secret for you"})
            return
        self.write({"code": 1000, "message": "Secret is secret"})


async def main():
    tornado.options.parse_command_line()

    rpc_client = RPCClient()
    await rpc_client.connect()
    app = Application(rpc_client)
    app.listen(options.port)
    shutdown_event = tornado.locks.Event()
    await shutdown_event.wait()

if __name__ == "__main__":
    tornado.ioloop.IOLoop.current().run_sync(main)
