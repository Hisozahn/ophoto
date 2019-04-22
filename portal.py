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
            (r"/post", PostCreateHandler),
            (r"/get_posts", GetPostsHandler),
            (r"/get_post", GetPostHandler),
        ]
        settings = dict(
            xsrf_cookies=False,
            cookie_secret="JIPe32fieoHF(Eb32o98fe]32[e3[2u*(FQhue2dsqnjodehiw&*Te2yvdbiew",
            debug=True,
        )
        super(Application, self).__init__(handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):
    def prepare(self):
        self.args = json.loads(self.request.body)

    def get_current_user(self):
        return self.get_secure_cookie(SECURE_COOKIE_NAME)

class HomeHandler(BaseHandler):
    async def get(self):
        self.write( {"code": 1000, "message": "OK"})


class AuthCreateHandler(BaseHandler):
    async def post(self):
        _id = str(uuid.uuid4())
        user = self.args["user"]
        password = self.args["password"]
        auth_response = await self.application.rpc_client.call('auth', {'op': 'auth.create',
                                                                        '_id': _id,
                                                                        'user': user,
                                                                        'password': password})
        user_response = await self.application.rpc_client.call('user', {'op': 'user.create',
                                                                        '_id': _id,
                                                                        'user': user})
        if auth_response['code'] != 1000:
            self.write(auth_response)
            return
        if user_response['code'] != 1000:
            self.write(user_response)
            return
            #TODO

        self.write( {"code": 1000, "message": "Authenticated"})


class AuthLoginHandler(BaseHandler):
    async def post(self):
        user = self.args["user"]
        password = self.args["password"]
        response = await self.application.rpc_client.call('auth', {'op': 'auth.login',
                                                                   'user': user,
                                                                   'password': password})
        self.write(response)


class AuthLogoutHandler(BaseHandler):
    async def post(self):
        token = self.args["token"]
        response = await self.application.rpc_client.call('auth', {'op': 'auth.logout', 'token': token})
        self.write(response)

class PostCreateHandler(BaseHandler):
    async def post(self):
        response = await self.application.rpc_client.call('auth', {'op': 'auth.check', 'token': self.args["token"]})
        if response['code'] != 1000:
            self.write(response)
            return
        user = response['user']
        response = await self.application.rpc_client.call('image', {'op': 'image.create', 'image': self.args["image"]})
        if response['code'] != 1000:
            self.write(response)
            return
        response = await self.application.rpc_client.call('post', {'op': 'post.create', 'user': user, 'image_id': response['image_id'], 'description': self.args["description"]})
        self.write(response)

class GetPostsHandler(BaseHandler):
    async def post(self):
        search_type = self.args["search_type"]
        response = await self.application.rpc_client.call('auth', {'op': 'auth.check', 'token': self.args["token"]})
        if response['code'] != 1000:
            self.write(response)
            return
        user = response['user']
        response = await self.application.rpc_client.call('user', {'op': 'user.find', 'user': user, 'search_type': search_type})
        if response['code'] != 1000:
            self.write(response)
            return
        response = await self.application.rpc_client.call('post', {'op': 'post.find', 'users': response['users']})
        self.write(response)

class GetPostHandler(BaseHandler):
    async def post(self):
        response = await self.application.rpc_client.call('auth', {'op': 'auth.check', 'token': self.args["token"]})
        if response['code'] != 1000:
            self.write(response)
            return
        post_response = await self.application.rpc_client.call('post', {'op': 'post.get', 'post_id': self.args["post_id"]})
        if post_response['code'] != 1000:
            self.write(post_response)
            return
        image_response = await self.application.rpc_client.call('image', {'op': 'image.get', 'image_id': post_response['image_id']})
        if image_response['code'] != 1000:
            self.write(image_response)
            return
        self.write( {"code": 1000, "message": "Got post", "description": post_response["description"], "image": image_response["image"]})

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
