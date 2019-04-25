#!/usr/bin/env python3

from ophoto.lib.db import Database
import json

class Post(object):
    def __init__(self, _id, user, image_id, description, likes):
        self.id = _id
        self.user = user
        self.image_id = image_id
        self.description = description
        self.likes = likes

class PostDatabase(Database):
    def __init__(self, host, port, name):
        super().__init__(host, port, name)

    async def get_post(self, _id):
        post = await self.db.posts.find_one({'_id' : _id})
        if post is None:
            return None
        return Post(post["_id"], post["user"], post["image_id"], post["description"], post["likes"])

    async def create_post(self, user, image_id, description):
        result = await self.db.posts.insert_one({'user': user, 'image_id': image_id, 'description': description, 'likes': []})
        return str(result.inserted_id)

    async def post_set_like(self, _id, user, value):
        if value == '1':
            result = await self.db.posts.update_one({'_id': _id}, { '$addToSet': { 'likes': user } })
        else:
            result = await self.db.posts.update_one({'_id': _id}, { '$pull': { 'likes': user } })


    async def find_posts(self, users):
        print(users)
        cursor = self.db.posts.find({"user": {"$in": users}})
        posts = await cursor.to_list(None)
        return posts
