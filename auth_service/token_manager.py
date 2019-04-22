#!/usr/bin/env python3

import uuid

class TokenManager(object):
    def __init__(self):
        self.tokens = {}

    def generate(self, user):
        new_token = str(uuid.uuid4())
        self.tokens[new_token] = user
        return new_token

    def check(self, token):
        if token in self.tokens:
            return self.tokens[token]
        return None

    def clear(self, token):
        if token in self.tokens:
            del(self.tokens[token])
            return True
        return False
