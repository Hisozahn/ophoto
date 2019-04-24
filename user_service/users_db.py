#!/usr/bin/env python3

from ophoto.lib.db import Database
from enum import Enum
import json

class User(object):
    def __init__(self, _id, name, bio, follows, image_id):
        self.id = _id
        self.name = name
        self.bio = bio
        self.follows = follows
        self.image_id = image_id

SearchType = {
    "ALL": 1,
    "FOLLOWERS": 2,
    "FOLLOWING": 3,
}

class UserDatabase(Database):
    def __init__(self, host, port, name):
        super().__init__(host, port, name)
        self.db.users.create_index('name', unique=True)

    async def get_user(self, name):
        user = await self.db.users.find_one({'name' : name})
        if user is None:
            return None
        return User(user["_id"], user["name"], user["bio"], user["follows"], user["image_id"])

    async def create_user(self, _id, name):
        if await self.get_user(name) is not None:
            raise Exception('User already exists')
        result = await self.db.users.insert_one({'_id': _id, 'name': name, 'bio': '', 'follows': [], 'image_id': ''})
        return result.inserted_id

    async def update_user_info(self, name, image_id, bio):
        result = await self.db.users.update_one({'name': name}, {'$set': {"image_id": image_id, "bio": bio}})

    async def user_set_follow(self, name, follow_name, value):
        if value == '1':
            result = await self.db.users.update_one({'name': name}, { '$addToSet': { 'follows': [ follow_name ] } })
        else:
            result = await self.db.users.update_one({'name': name}, { '$pull': { 'follows': [ follow_name ] } })
            

    async def find_related(self, user, search_type):
        user_obj = await self.get_user(user)
        if user_obj is None:
            return []
        match = {}
        if SearchType[search_type] == 3:
            match['name'] = {'$in': user_obj.follows}
        elif SearchType[search_type] == 2:
            match['follows'] = user_obj.name
        elif SearchType[search_type] != 1:
            raise Exception('Invalid search type')
        cursor = self.db.users.find(match)
        people = await cursor.to_list(None)
        return people

    async def find_people(self, user, query, search_type):
        user_obj = await self.get_user(user)
        if user_obj is None:
            return []
        match = {"$and": []}
        if SearchType[search_type] == 3:
            match["$and"].append({ "name": {'$in': user_obj.follows}})
        elif SearchType[search_type] == 2:
            match["$and"].append({'follows': user_obj.name})
        elif SearchType[search_type] != 1:
            raise Exception('Invalid search type')
        match["$and"].append({"name": '/{0}/'.format(query)})
        cursor = self.db.users.find(match)
        people = await cursor.to_list(None)
        return people
