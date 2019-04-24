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
            (r"/get_posts_of", GetPostsOfHandler),
            (r"/get_image", GetImageHandler),
            (r"/get_post", GetPostHandler),
            (r"/get_user", GetUserHandler),
            (r"/set_user_image", SetUserImageHandler),
            (r"/set_user_bio", SetUserBioHandler),
            (r"/user_follow", UserFollowHandler),
            (r"/find_users", UserFindHandler),
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

class GetPostsOfHandler(BaseHandler):
    async def post(self):
        search_type = self.args["search_type"]
        response = await self.application.rpc_client.call('auth', {'op': 'auth.check', 'token': self.args["token"]})
        if response['code'] != 1000:
            self.write(response)
            return
        response = await self.application.rpc_client.call('post', {'op': 'post.find', 'users': [self.args["user"]]})
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

class GetImageHandler(BaseHandler):
    async def post(self):
        response = await self.application.rpc_client.call('auth', {'op': 'auth.check', 'token': self.args["token"]})
        if response['code'] != 1000:
            self.write(response)
            return
        image_response = await self.application.rpc_client.call('image', {'op': 'image.get', 'image_id': self.args['image_id']})
        if image_response['code'] != 1000:
            self.write(image_response)
            return
        self.write( {"code": 1000, "message": "Got image", "image": image_response["image"]})

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
        self.write( {"code": 1000, "message": "Got post", "user": post_response["user"], "description": post_response["description"], "image": image_response["image"]})

class GetUserHandler(BaseHandler):
    async def post(self):
        response = await self.application.rpc_client.call('auth', {'op': 'auth.check', 'token': self.args["token"]})
        if response['code'] != 1000:
            self.write(response)
            return
        response = await self.application.rpc_client.call('user', {'op': 'user.get', 'name': self.args["name"]})
        if response['code'] != 1000:
            self.write(response)
            return
        image = ''
        if response["image_id"]:
            image_response = await self.application.rpc_client.call('image', {'op': 'image.get', 'image_id': response['image_id']})
            if image_response['code'] != 1000:
                self.write(image_response)
                return
            image = image_response["image"]
        self.write( {"code": 1000, "message": "Got user", "bio": response["bio"], "follows": response["follows"], "image": image})

class SetUserImageHandler(BaseHandler):
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
        response = await self.application.rpc_client.call('user', {'op': 'user.set_image', 'name': user, "image_id": response["image_id"]})
        self.write(response)

class SetUserBioHandler(BaseHandler):
    async def post(self):
        response = await self.application.rpc_client.call('auth', {'op': 'auth.check', 'token': self.args["token"]})
        if response['code'] != 1000:
            self.write(response)
            return
        user = response['user']
        response = await self.application.rpc_client.call('user', {'op': 'user.set_bio', 'name': user, "bio": self.args["bio"]})
        self.write(response)

class UserFollowHandler(BaseHandler):
    async def post(self):
        response = await self.application.rpc_client.call('auth', {'op': 'auth.check', 'token': self.args["token"]})
        if response['code'] != 1000:
            self.write(response)
            return
        user = response['user']
        response = await self.application.rpc_client.call('user', {'op': 'user.follow', 'name': user, "follow_name": self.args["follow_name"], "value": self.args["value"]})
        self.write(response)

class UserFindHandler(BaseHandler):
    async def post(self):
        response = await self.application.rpc_client.call('auth', {'op': 'auth.check', 'token': self.args["token"]})
        if response['code'] != 1000:
            self.write(response)
            return
        user = response['user']
        response = await self.application.rpc_client.call('user', {'op': 'user.find_people', 'name': user, "query": self.args["query"], "search_type": self.args["search_type"]})
        self.write(response)

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
