#!/usr/bin/env python3

import asyncio
import json

async def route(scheme, msg):
    print(msg)
    if 'op' not in msg:
        return({"code": 999, "message": "Operation is not present in the message %s" % msg})

    for operation in scheme:
        print(operation)
        if operation['op'] == msg['op']:
            op = operation

    if op is None:
        return({"code": 999, "message": "Operation is not present in the scheme"})

    for key in op['args']:
        if key not in msg:
            return({"code": 999, "message": "Key %s is not present in the message %s" % (key, msg)})

    args = []
    for arg in op['args']:
        args.append(msg[arg])

    return await op['handler'](*args)
