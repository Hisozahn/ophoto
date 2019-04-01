#!/usr/bin/env python3

import aiopg
import bcrypt
import markdown
import os.path
import motor.motor_tornado
import re
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.locks
import tornado.options
import tornado.web
import unicodedata
import json
from tornado_json.requesthandlers import APIHandler
from tornado_json import schema
from tornado_json.gen import coroutine
from enum import Enum

from tornado.options import define, options

class User(object):
    def __init__(self, _id, name, hashed_password, bio, follows):
        self._id = _id
        self.name = name
        self.hashed_password = hashed_password
        self.bio = bio
        self.follows = follows

class Search_type(Enum):
    ALL = 1
    FOLLOWERS = 2
    FOLLOWING = 3

class Database(object):
    db = None

    def __init__(self, host, port, name):
        print('{0} {1} {2}'.format(host, port, name))
        self.db = motor.motor_tornado.MotorClient(host, port)[name]
        self.db.users.create_index('name', unique=True)

    async def get_user(self, name):
        user = await self.db.users.find_one({'name' : name})
        if user is None:
            return None
        print(user)
        return User(user["_id"], user["name"], user["hashed_password"], user["bio"], user["follows"])

    async def create_user(self, name, hashed_password):
        if await self.get_user(name) is not None:
            raise Exception('User already exists')
        result = await self.db.users.insert_one({
            'name': name,
            'hashed_password': hashed_password,
            'bio': '',
            'follows': [],
            })
        return result.inserted_id

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


'''
    async def create_collections(self):
        await

    async def maybe_create_collections(self):
        db = self.db
        try:
            await db.users.find_one()
        except:
            with open('schema.sql') as f:
                schema = f.read()
            with (await db.cursor()) as cur:
                await cur.execute(schema)
'''

'''
    def get_db(self):
        if __db is None:
            raise Exception('Database is not connected')
        return __db
'''
