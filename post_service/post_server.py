#!/usr/bin/env python3

import asyncio
import bcrypt
import json

from .post_db import PostDatabase
from ophoto.lib.rpc_server import RPCServer

import tornado.options
from tornado.options import define, options
from bson import ObjectId

define("port", default=8891, help="run on the given port", type=int)
define("db_host", default="127.0.0.1", help="post database host")
define("db_port", default=27017, help="post database port")
define("db_database", default="posts", help="post database name")

class PostServer(RPCServer):
    def __init__(self, routing_key, db):
        super().__init__(routing_key, db)
        self.scheme = [
            {'op': 'post.create', 'handler': self.post_create, 'args': ['user', 'image_id', 'description']},
            {'op': 'post.find', 'handler': self.post_find, 'args': ['users']},
            {'op': 'post.get', 'handler': self.post_get, 'args': ['post_id']},
            {'op': 'post.get_likes', 'handler': self.post_get_likes, 'args': ['post_id']},
            {'op': 'post.like', 'handler': self.post_like, 'args': ['post_id', 'user', 'value']},
        ]


    async def post_create(self, user, image_id, description):
        try:
            post_id = await self.db.create_post(user, image_id, description)
        except Exception as err:
            return({"code": 999, "message": err.args[0]})
        return ({"code": 1000, "message": "Post is created", "post_id": post_id})

    async def post_find(self, users):
        posts = await self.db.find_posts(users)
        post_ids = []
        for post in posts:
            post_ids.append(str(post["_id"]))
        print("users: ", users, "posts_id: ", post_ids)
        return({"code": 1000, "message": "Query succeeded", "posts": post_ids})

    async def post_get(self, post_id):
        post = await self.db.get_post(ObjectId(post_id))
        if post is None:
            return({"code": 999, "message": "No such post"})
        return({"code": 1000, "message": "Got post", "user": post.user, "description": post.description, "image_id": post.image_id})

    async def post_get_likes(self, post_id):
        post = await self.db.get_post(ObjectId(post_id))
        if post is None:
            return({"code": 999, "message": "No such post"})
        return({"code": 1000, "message": "Got post likes", "likes": post.likes})

    async def post_like(self, post_id, user, value):
        post = await self.db.get_post(ObjectId(post_id))
        if post is None:
            return({"code": 999, "message": "No such post"})
        await self.db.post_set_like(ObjectId(post_id), user, value)
        return({"code": 1000, "message": "Like succeeded"})


async def post_rpc_server():
    db = PostDatabase(options.db_host, options.db_port, options.db_database)
    server = PostServer('post', db)
    await server.connect()


tornado.options.parse_command_line()
event_loop = asyncio.get_event_loop()
event_loop.run_until_complete(post_rpc_server())
event_loop.run_forever()
