#!/usr/bin/env python3

import motor.motor_tornado

class Database(object):
    db = None
    def __init__(self, host, port, name):
        self.db = motor.motor_tornado.MotorClient(host, port)[name]
