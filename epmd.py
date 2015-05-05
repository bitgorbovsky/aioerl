# coding: utf-8

import asyncio

from request import (
    Alive2Request,
    NamesRequest,
    EmptyEPMDRequest,
    PortRequest
    )
from response import (
    UnknownEPMDResponse,
    Alive2Response,
    PortResponse,
    NamesResponse,
    NodeInfo
    )


__all__ = ["EPMDClient", "NodeInfo"]


class EPMDClient:

    def __init__(self, epmd_host, epmd_port, loop):
        self._epmd_host = epmd_host
        self._epmd_port = epmd_port
        self._loop = loop

        self._alive2_connect = None

    @asyncio.coroutine
    def __make_conn(self, host=None, port=None):
        reader, writer = yield from asyncio.open_connection(
            host or self._epmd_host,
            port or self._epmd_port,
            loop=self._loop
        )
        return reader, writer

    @asyncio.coroutine
    def __recv(self, reader, chunk_size=100):
        data = b''
        while not reader.at_eof():
            data += (yield from reader.read(chunk_size))

        return data

    @asyncio.coroutine
    def register(self, nodeinfo):
        # don't close connetion in this method because EPMD daemon
        # tracks this connection for leep alive status.
        reader, writer = yield from self.__make_conn()

        writer.write(Alive2Request(
            port_no=nodeinfo.port,
            node_name=nodeinfo.name
        ).encode())

        data = yield from reader.read(Alive2Request.expected_response_len)
        result = Alive2Response.decode(data)
        if result and result.success:
            self._alive2_connect = (reader, writer)
            return True
        return False

    @asyncio.coroutine
    def names(self, host=None, port=None):
        reader, writer = yield from self.__make_conn(host, port)
        writer.write(NamesRequest().encode())

        data = yield from self.__recv(reader)
        writer.close()

        if not data:
            return False

        return NamesResponse.decode(data)


    @asyncio.coroutine
    def distribution_port(self, node_name, host=None, port=None):
        reader, writer = yield from self.__make_conn(host, port)
        writer.write(PortRequest(node_name).encode())

        data = yield from self.__recv(reader)
        writer.close()

        return PortResponse.decode(data)

    @asyncio.coroutine
    def kill(self):
        return

    @asyncio.coroutine
    def stop(self):
        return

    @asyncio.coroutine
    def dump(self):
        return
