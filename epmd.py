# coding: utf-8

import asyncio
import functools

import bitstring


class EPMDProtocol(asyncio.Protocol):

    def __init__(self, loop):
        self.loop = loop

    def connection_made(self, transport):
        print('Connecting to EPMD...')


    def data_received(self, data):
        print('Reived data: {!r}'.format(data.decode()))

    def connection_lost(self, exc):
        print('Connection to EPMD closed')
        self.loop.stop()


loop = asyncio.get_event_loop()

coro = loop.create_connection(
    functools.partial(EPMDProtocol, loop),
    '127.0.0.1',
    4369
)

loop.run_until_complete(coro)
loop.close()
