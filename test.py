# coding: utf-8

import asyncio
from epmd import *

loop = asyncio.get_event_loop()

client = EPMDClient('localhost', 4369, loop)

print(loop.run_until_complete(client.register(NodeInfo('bit', 7171))))

print(loop.run_until_complete(client.names()).nodes)
print(loop.run_until_complete(client.distribution_port("kit")))
print(loop.run_until_complete(client.distribution_port("bit")))

loop.run_forever()
loop.close()
