#!/usr/bin/env python3

from ophoto.lib.db import Database
import json

class Image(object):
    def __init__(self, _id, data):
        self.id = _id
        self.data = data

class ImageDatabase(Database):
    def __init__(self, host, port, name):
        super().__init__(host, port, name)

    async def get_image(self, _id):
        image = await self.db.images.find_one({'_id' : _id})
        if image is None:
            return None
        return Image(image["_id"], image["data"])

    async def create_image(self, data):
        result = await self.db.images.insert_one({'data': data})
        return str(result.inserted_id)
