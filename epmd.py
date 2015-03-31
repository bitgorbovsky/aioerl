# coding: utf-8

import asyncio
from protocol import EPMDProtocol, connect, NodeInfo

loop = asyncio.get_event_loop()

#epmd = EPMDProtocol(7170, loop)
#coro = loop.create_connection(lambda : epmd, '127.0.0.1', 4369)

conn = loop.run_until_complete(connect(
    loop,
    '127.0.0.1',
    4369,
    NodeInfo('bit', 7170)
))

res = loop.run_until_complete(conn.register())
print(res)

res = loop.run_until_complete(conn.get_names())
#print(res)



loop.run_forever()
loop.close()
