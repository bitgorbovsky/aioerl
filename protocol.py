# coding: utf-8

import asyncio

from bitstring import ConstBitStream

from request import Alive2Request, NamesRequest
from response import UnknownEPMDResponse, Alive2Response


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
        self.send_epmd_request(Alive2Request(port_no=self.node_port))

    def data_received(self, data):
        if self.state == self.INIT:
            response = self._unpack_epmd_resp(data)
            if response.success:
                print('Registering in EPMD success!')
                #self.send_epmd_request(NamesRequest())
                #self.state = self.WAIT_FOR_NAMES
        elif self.state == self.WAIT_FOR_NAMES:
            print(data)

    def connection_lost(self, exc):
        print('Connection to EPMD closed')
        self.loop.stop()

    def _unpack_epmd_resp(self, data):
        buf = ConstBitStream(data)
        ptype = buf.read('uint:8')
        if ptype == 121:
            success = buf.read('uint:8')
            creation = buf.read('bytes:2')
            return Alive2Response(data, success == 0, creation)
        else:
            return UnknownEPMDResponse(data)

    def send_epmd_request(self, request):
        print('sending request...')
        self._transport.write(request.encode())
