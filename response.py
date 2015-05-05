# coding: utf-8

import re
from collections import namedtuple
from struct import pack, unpack, unpack_from, calcsize


ALIVE2_RESP = 121
PORT2_RESP = 119


match_node_info = re.compile('^name (\w+) at port (\d+)$')


NodeInfo = namedtuple('NodeInfo', ['name', 'port'])


def parse_node_info(info):
    name, port = match_node_info.match(info.decode('utf-8')).groups()
    return NodeInfo(name, int(port))


class EPMDresponse:

    def __init__(self, data):
        self._raw_data = data


class Alive2Response(EPMDresponse):

    def __init__(self, data, success, creation):
        super(Alive2Response, self).__init__(data)
        self.success = success
        self.creation = creation

    @classmethod
    def decode(cls, data):
        RES_TYPE, = unpack('>B', data[:1])
        if RES_TYPE != ALIVE2_RESP:
            return

        success, creation = unpack('>B2s', data[1:])
        return Alive2Response(data, success == 0, creation)


class PortResponse(EPMDresponse):

    def __init__(self, port_no,
                       node_type,
                       protocol,
                       high_ver,
                       low_ver,
                       node_name, 
                       extra):
        self.port_no = port_no
        self.node_type = node_type
        self.high_ver = high_ver
        self.low_ver = low_ver
        self.node_name = node_name
        self.extra = extra
        self.protocol = protocol

    @classmethod
    def decode(cls, data):
        RES_TYPE, status = unpack('>BB', data[:2])
        if RES_TYPE != PORT2_RESP or status > 0:
            return

        pack_fmt = '>HBBHHH'

        port_no, node_type, protocol, high_ver, low_ver, nlen = unpack_from(
            pack_fmt,
            data,
            2
        )

        node_name, elen = unpack_from(
            '>{nlen}sH'.format(nlen=nlen),
            data,
            calcsize(pack_fmt) + 2
        )

        node_name = node_name.decode('utf-8')
        if elen:
            extra = unpack_from(
                '>{elen}s'.format(elen=elen),
                data,
                calcsize(pack_fmt) + 2 + nlen
            )
        else:
            extra = None

        return cls(
            port_no=port_no,
            node_type=node_type,
            protocol=protocol,
            high_ver=high_ver,
            low_ver=low_ver,
            node_name=node_name,
            extra=extra
        )

    def __repr__(self):
        return '{node} on {port}'.format(
            node=self.node_name,
            port=self.port_no
        )


class NamesResponse(EPMDresponse):

    def __init__(self, nodes):
        self.nodes = nodes

    @classmethod
    def decode(cls, data):
        port_non = unpack_from('>H', data, 0)
        nodes = []
        for nodeinfo in data[4:].split(b'\n'):
            if nodeinfo:
                nodes.append(parse_node_info(nodeinfo))
        return cls(nodes)


class UnknownEPMDResponse(EPMDresponse):
    pass
