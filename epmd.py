# coding: utf-8

import asyncio
import functools

from bitstring import Bits, BitArray, ConstBitStream


TCP_PROTOCOL = 0
IP_V4 = 1

NORMAL_ERL_NODE = 77
HIDDEN_NODE = 72


HIGHEST_VERSION = 5
LOWEST_VERSION = 5


class EPMDRequest:

    def encode(self):
        raw_packet = self._get_raw_data()
        packet_len = len(raw_packet) // 8
        fullbuf = BitArray()
        fullbuf.append(Bits(uint=packet_len, length=16))
        fullbuf.append(raw_packet)
        return fullbuf.bytes


class Alive2Request(EPMDRequest):

    def __init__(self, port_no,
                       node_type=NORMAL_ERL_NODE,
                       protocol=TCP_PROTOCOL,
                       high_ver=HIGHEST_VERSION,
                       low_ver=LOWEST_VERSION,
                       node_name='pynode@localhost',
                       extra=None):
        self.port_no = port_no
        self.node_type = node_type
        self.protocol = protocol
        self.high_ver = high_ver
        self.low_ver = low_ver
        self.node_name = node_name
        self.extra = extra

    def _get_raw_data(self):
        buf = BitArray()

        # ALIVE2_REQ
        buf.append(Bits(uint=120, length=8))

        # PORT_NO
        buf.append(Bits(uint=self.port_no, length=16))

        # NODE_TYPE
        buf.append(Bits(uint=self.node_type, length=8))

        # PROTOCOL
        buf.append(Bits(uint=self.protocol, length=8))

        # HGHEST VERSION
        buf.append(Bits(uint=self.high_ver, length=16))

        # LOWEST VERSION
        buf.append(Bits(uint=self.low_ver, length=16))

        node_name_encoded = self.node_name.encode()
        nlen = len(node_name_encoded)

        # NLEN
        buf.append(Bits(uint=nlen, length=16))

        # NODENAME
        buf.append(Bits(bytes=node_name_encoded, length=nlen * 8))

        # EXTRA
        if self.extra is not None:
            extra_encoded = self.extra.encode()
            elen = len(extra_encoded)
            buf.append(Bits(uint=elen, length=16))
            buf.append(Bits(bytes=extra_encoded, length=elen * 8))
        else:
            buf.append(Bits(uint=0, length=16))
        return buf


class NamesRequest(EPMDRequest):

    def _get_raw_data(self):
        return BitArray(Bits(uint=110, length=8))


class EPMDresponse:

    def __init__(self, data):
        self._raw_data = data


class Alive2Response(EPMDresponse):

    def __init__(self, data, success, creation):
        super(Alive2Response, self).__init__(data)
        self.success = success
        self.creation = creation


class UnknownEPMDResponse(EPMDresponse):
    pass


class EPMDProtocol(asyncio.Protocol):

    ERROR = -1
    INIT = 1
    SENT_REG = 2
    WAIT_FOR_NAMES = 3

    def __init__(self, loop):
        self.loop = loop
        self.state = self.INIT

    def connection_made(self, transport):
        self._transport = transport
        self.send_epmd_request(Alive2Request(port_no=7170))

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
        self._transport.write(request.encode())


loop = asyncio.get_event_loop()

epmd = EPMDProtocol(loop)
coro = loop.create_connection(lambda : epmd, '127.0.0.1', 4369)

loop.run_until_complete(coro)
loop.run_forever()
loop.close()
