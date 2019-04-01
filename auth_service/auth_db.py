#!/usr/bin/env python3

from ophoto.lib.db import Database
import json

class AuthUser(object):
    def __init__(self, _id, name, hashed_password):
        self.id = _id
        self.name = name
        self.hashed_password = hashed_password

class AuthDatabase(Database):
    def __init__(self, host, port, name):
        super().__init__(host, port, name)
        self.db.users.create_index('name', unique=True)

    async def get_user(self, name):
        user = await self.db.users.find_one({'name' : name})
        if user is None:
            return None
        return AuthUser(user["_id"], user["name"], user["hashed_password"])

    async def create_user(self, _id, name, hashed_password):
        if await self.get_user(name) is not None:
            raise Exception('User already exists')
        result = await self.db.users.insert_one({
            '_id': _id,
            'name': name,
            'hashed_password': hashed_password,
            })
        return result.inserted_id
