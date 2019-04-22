#!/usr/bin/env python3

from ophoto.lib.db import Database
import json

class Post(object):
    def __init__(self, _id, user, image_id, description):
        self.id = _id
        self.user = user
        self.image_id = image_id
        self.description = description

class PostDatabase(Database):
    def __init__(self, host, port, name):
        super().__init__(host, port, name)

    async def get_post(self, _id):
        post = await self.db.posts.find_one({'_id' : _id})
        if post is None:
            return None
        return Post(post["_id"], post["user"], post["image_id"], post["description"])

    async def create_post(self, user, image_id, description):
        result = await self.db.posts.insert_one({'user': user, 'image_id': image_id, 'description': description})
        return str(result.inserted_id)

    async def find_posts(self, users):
        print(users)
        cursor = self.db.posts.find({"user": {"$in": users}})
        posts = await cursor.to_list(None)
        return posts
