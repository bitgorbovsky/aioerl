''' epmd client module '''


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

from protocols import HandshakeProtocol


__all__ = ["EPMDClient", "NodeInfo", "NodeProtocol"]


class EPMDClient:

    def __init__(self, host, port, loop):
        self._host = host
        self._port = port
        self._loop = loop

        self._alive2_connect = None

    @asyncio.coroutine
    def __make_conn(self, host=None, port=None):
        reader, writer = yield from asyncio.open_connection(
            host or self._host,
            port or self._port,
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
        # don't close connection in this method because EPMD daemon
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


class NodeProtocol(asyncio.Protocol):

    def __init__(self, node_name, cookie):
        self.node_name = node_name
        self.cookie = cookie
        self.protocol = None

    def connection_made(self, transport):
        self.protocol = HandshakeProtocol(
            transport,
            self.node_name,
            self.cookie
        )
        self.transport = transport

    def data_received(self, packet):
        result = self.protocol.accept_packet(packet)
        if result:
            self.protocol = result
