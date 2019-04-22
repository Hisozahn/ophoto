#!/usr/bin/env python3

from ophoto.lib.db import Database
from enum import Enum
import json

class User(object):
    def __init__(self, _id, name, bio, follows):
        self.id = _id
        self.name = name
        self.bio = bio
        self.follows = follows

class Search_type(Enum):
    ALL = 1
    FOLLOWERS = 2
    FOLLOWING = 3

class UserDatabase(Database):
    def __init__(self, host, port, name):
        super().__init__(host, port, name)
        self.db.users.create_index('name', unique=True)

    async def get_user(self, name):
        user = await self.db.users.find_one({'name' : name})
        if user is None:
            return None
        return User(user["_id"], user["name"], user["bio"], user["follows"])

    async def create_user(self, _id, name):
        if await self.get_user(name) is not None:
            raise Exception('User already exists')
        result = await self.db.users.insert_one({'_id': _id, 'name': name, 'bio': '', 'follows': []})
        return result.inserted_id

    async def find_related(self, user, search_type):
        cursor = self.db.users.find()
        people = await cursor.to_list(None)
        return people

    async def find_people(self, user, query, search_type):
        if search_type == Search_type.FOLLOWING:
            match['_id'] = {'$in': user.follows}
        elif search_type == Search_type.FOLLOWERS:
            match['follows'] = user._id
        elif search_type != Search_type.ALL:
            raise Exception('Invalid search type')
        match['name'] = '/{0}/'.format(query)
        cursor = self.db.users.find(match)
        people = await cursor.to_list(None)
        return people
