# coding: utf-8

import asyncio
from protocol import EPMDProtocol

loop = asyncio.get_event_loop()

epmd = EPMDProtocol(7170, loop)
coro = loop.create_connection(lambda : epmd, '127.0.0.1', 4369)

loop.run_until_complete(coro)
loop.run_forever()
loop.close()
