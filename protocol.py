# coding: utf-8

import re
import asyncio
from collections import namedtuple

from bitstring import ConstBitStream

from request import Alive2Request, NamesRequest, EmptyEPMDRequest
from response import UnknownEPMDResponse, Alive2Response

match_node_info = re.compile('^name (\w+) at port (\d+)$')


NodeInfo = namedtuple('NodeInfo', ['name', 'port'])


class EPMDConnectionLost(Exception):
    pass


def parse_node_info(info):
    name, port = match_node_info.match(info.decode('utf-8')).groups()
    return NodeInfo(name, int(port))


class EPMDClient(asyncio.Protocol):

    ERROR = -1
    INIT = 1
    SENT_REG = 2
    WAIT_FOR_NAMES = 3

    def __init__(self, nodeinfo, loop):
        self._loop = loop
        self._state = self.INIT
        self._node_port = node_port
        self._waiter = None
        self._transport = None
        self._timeout = 500
        self._is_closed = False

    def connection_made(self, transport):
        self._transport = transport

    def data_received(self, data):
        response = self._unpack_epmd_resp(data)
        self._waiter.set_result(response)
        self._waiter = None

    def eof_received(self):
        self._is_closed = True
        if self._waiter:
            self._waiter.set_exception(EPMDConnectionLost(
                'Failed connection to EPMD'
            ))
            self._waiter.exception()
        return True

    def connection_lost(self, exc):
        self._loop.stop()

    def _get_waiter(self):
        return asyncio.Future(loop=self._loop)

    @asyncio.coroutine
    def register(self):
        if self._is_closed:
            raise EPMDConnectionLost('Failed connection to EPMD')
        self.state = self.SENT_REG
        self._waiter = self._get_waiter()
        self.send_epmd_request(Alive2Request(port_no=self._node_port))
        result = yield from asyncio.wait_for(
            self._waiter,
            self._timeout,
            loop=self._loop
        )
        return result

    @asyncio.coroutine
    def get_names(self):
        if self._is_closed:
            raise EPMDConnectionLost('Failed connection to EPMD')
        self.state = self.WAIT_FOR_NAMES
        self._waiter = self._get_waiter()
        self.send_epmd_request(NamesRequest())
        result = yield from asyncio.wait_for(
            self._waiter,
            self._timeout,
            loop=self._loop
        )
        return result

    def _unpack_epmd_resp(self, data):
        buf = ConstBitStream(data)
        if self.state == self.WAIT_FOR_NAMES:
            portno = buf.read('uint:32')
            nodes = []
            for nodeinfo in buf.bytes[4:].split(b'\n'):
                if nodeinfo:
                    nodes.append(parse_node_info(nodeinfo))
            return nodes
        ptype = buf.read('uint:8')
        if ptype == 121:
            success = buf.read('uint:8')
            creation = buf.read('bytes:2')
            return Alive2Response(data, success == 0, creation)
        else:
            return UnknownEPMDResponse(data)

    def send_epmd_request(self, request):
        data = request.encode()
        self._transport.write(data)


@asyncio.coroutine
def connect(loop, epmd_host, epmd_port, nodeinfo):
    epmd = EPMDClient(nodeinfo, loop)
    yield from loop.create_connection(lambda: epmd, epmd_host, epmd_port)
    return epmd


####


class EPMDClient:

    def __init__(self, epmd_host, epmd_port, loop):
        self._epmd_host = epmd_host
        self._epmd_port = epmd_port
        self._loop = loop

        self._alive2_connect = None

    @asyncio.coroutine
    def __make_conn(self):
        reader, writer = yield from asyncio.open_connection(
            self._epmd_host, self._epmd_port, loop=self._loop
        )
        return reader, writer

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
    def names(self):
        reader, writer = yield from self.__make_conn()
        writer.write(NamesRequest().encode())

        data = b''
        while reader.at_eof():
            data += (yield from reader.read(100))

        writer.close()

        if not data:
            return False

        buff = ConstBitStream(data)
        port_no = buf.read('uint:32')
        nodes = []
        for nodeinfo in buf.bytes[4:].split(b'\n'):
            if nodeinfo:
                nodes.append(parse_node_info(nodeinfo))
        return nodes

    @asyncio.coroutine
    def distribution_port(self, node_name):
        return

    @asyncio.coroutine
    def kill(self):
        return

    @asyncio.coroutine
    def stop(self):
        return

    @asyncio.coroutine
    def dump(self):
        return
