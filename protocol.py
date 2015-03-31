# coding: utf-8

import re
import asyncio

from bitstring import ConstBitStream

from request import Alive2Request, NamesRequest, EmptyEPMDRequest
from response import UnknownEPMDResponse, Alive2Response

match_node_info = re.compile('^name (\w+) at port (\d+)$')


def parse_node_info(info):
    name, port = match_node_info.match(info.decode('utf-8')).groups()
    return (name, int(port))


class EPMDProtocol(asyncio.Protocol):

    ERROR = -1
    INIT = 1
    SENT_REG = 2
    WAIT_FOR_NAMES = 3

    def __init__(self, node_port, loop):
        self.loop = loop
        self.state = self.INIT
        self.node_port = node_port

    def connection_made(self, transport):
        self._transport = transport
        self.register()

    def data_received(self, data):
        response = self._unpack_epmd_resp(data)

    def eof_received(self):
        return True

    def connection_lost(self, exc):
        self.loop.stop()

    def register(self):
        self.state = self.SENT_REG
        self.send_epmd_request(Alive2Request(port_no=self.node_port))

    def get_names(self):
        self.state = self.WAIT_FOR_NAMES
        self.send_epmd_request(NamesRequest())

    def _unpack_epmd_resp(self, data):
        buf = ConstBitStream(data)
        if self.state == self.WAIT_FOR_NAMES:
            portno = buf.read('uint:32')
            nodes = []
            for nodeinfo in buf.bytes[4:].split(b'\n'):
                if nodeinfo:
                    nodes.append(parse_node_info(nodeinfo))
            print(nodes)
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
