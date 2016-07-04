''' epmd client module '''


import asyncio
import random
import sys
from struct import unpack_from, pack, calcsize
import hashlib


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


__all__ = ["EPMDClient", "NodeInfo", "ErlServerProtocol"]


random.seed()


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


class ErlServerProtocol(asyncio.Protocol):

    class STATE:
        INIT = 0
        READY = 1
        WAIT_CHALLENGE = 2
        WAIT_STATUS = 3

    class DISTRIBUTION_FLAGS:
        PUBLISHED = 1
        ATOM_CACHE = 2
        EXTENDED_REFERENCES = 4
        DIST_MONITOR = 8
        FUN_TAGS = 0x10
        DIST_MONITOR_NAME = 0x20
        HIDDEN_ATOM_CACHE = 0x40
        NEW_FUN_TAGS = 0x80
        EXTENDED_PIDS_PORTS = 0x100
        EXPORT_PTR_TAG = 0x200
        BIT_BINARIES = 0x400
        NEW_FLOATS = 0x800
        UNICODE_IO = 0x1000
        DIST_HDR_ATOM_CACHE = 0x2000
        SMALL_ATOM_TAGS = 0x4000
        UTF8_ATOMS = 0x10000
        MAP_TAG = 0x20000

    def connection_made(self, transport):
        self.transport = transport
        self.state = self.STATE.INIT

    def data_received(self, packet):
        if self.state == self.STATE.INIT:
            header_format = '>HcHI'
            size, tag, version, flags = unpack_from(header_format, packet)

            node_name = packet[calcsize(header_format):].decode()

            self.challenge = random.randint(0, 4294967295)

            node_name = 'bit@localhost'
            challenge_packet_fmt = '>cHII{nlen}s'.format(nlen=len(node_name))
            packet_length = calcsize(challenge_packet_fmt)

            challenge = pack(
                '>H{nlen}s'.format(nlen=packet_length),
                packet_length,
                pack(
                    challenge_packet_fmt,
                    b'n',                 # message tag 'n'
                    version,              # distribution version
                    flags,                # distribution flags
                    self.challenge,       # challenge
                    node_name.encode()    # node name
                )
            )

            status = b'ok'
            status = pack(
                '>Hc{nlen}s'.format(nlen=len(status)),
                len(status) + 1,
                b's',
                status
            )
            self.transport.write(status)
            self.transport.write(challenge)

            self.state = self.STATE.WAIT_CHALLENGE
        elif self.state == self.STATE.WAIT_CHALLENGE:
            header_fmt = '>HcI'
            size, tag, challenge = unpack_from(
                header_fmt,
                packet
            )
            digest = packet[calcsize(header_fmt):]

            hash_fn = hashlib.md5()
            hash_fn.update(b'%s%s' % ('DMAHGNQKBFRQXOMHNSEB', challenge))
            my_digest = hash_fn.digest()




class ErlClient:
    pass
