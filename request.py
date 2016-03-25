# coding: utf-8

from struct import pack, pack_into


__all__ = [
    "TCP_PROTOCOL",
    "IP_V4",
    "NORMAL_ERL_NODE",
    "HIDDEN_NODE",
    "HIGHEST_VERSION",
    "LOWEST_VERSION",
    "EPMDRequest",
    "Alive2Request",
    "NamesRequest",
    "PortRequest"
]


ALIVE2_REQ = 120
NAMES_REQ = 110
PORT_PLEASE_REQ = 122


TCP_PROTOCOL = 0
IP_V4 = 1

NORMAL_ERL_NODE = 77
HIDDEN_NODE = 72


HIGHEST_VERSION = 5
LOWEST_VERSION = 5


class EPMDRequest:

    def encode(self):
        raw_packet = self.get_raw_data()
        packet_len = len(raw_packet)
        return pack('>H{pack_len}s'.format(pack_len=packet_len),
                    packet_len, raw_packet)

    def get_raw_data(self):
        raise NotImplementedError("protected method _get_raw_data should be "
                                  "implemented!")


class EmptyEPMDRequest(EPMDRequest):

    def get_raw_data(self):
        return b'\x00'

    def encode(self):
        return b'\x00'


class Alive2Request(EPMDRequest):

    expected_response_len = 4

    def __init__(self, port_no,
                       node_type=NORMAL_ERL_NODE,
                       protocol=TCP_PROTOCOL,
                       high_ver=HIGHEST_VERSION,
                       low_ver=LOWEST_VERSION,
                       node_name='pynode',
                       extra=None):
        self.port_no = port_no
        self.node_type = node_type
        self.protocol = protocol
        self.high_ver = high_ver
        self.low_ver = low_ver
        self.node_name = node_name
        self.extra = extra

    def get_raw_data(self):

        node_name_encoded = self.node_name.encode()
        nlen = len(node_name_encoded)

        if self.extra is not None:
            extra_encoded = self.extra.encode()
            elen = len(extra_encoded)
        else:
            elen = 0

        packet = pack(
            '>BHBBHHH{nlen}sH'.format(nlen=nlen),
            ALIVE2_REQ,         # B, ALIVE2_REQ
            self.port_no,       # H, PORT_NO
            self.node_type,     # B, NODE_TYPE
            self.protocol,      # B, PROTOCOL
            self.high_ver,      # H, HIGHEST_VERSION
            self.low_ver,       # H, LOWEST_VERSION
            nlen,               # H, NLEN
            node_name_encoded,  # {nlen}s, NODENAME
            elen                # H, EXTRA_LEN
        )

        if elen:
            packet = pack_into('{elen}s'.format(elen=elen),
                               packet, len(packet))

        return packet


class NamesRequest(EPMDRequest):
    ''' NAMES_REQ packet coder '''

    def get_raw_data(self):
        return pack('B', NAMES_REQ)


class PortRequest(EPMDRequest):
    ''' PORT_PLEASE_REQ packet coder '''

    def __init__(self, nodename):
        self._nodename = nodename

    def get_raw_data(self):
        node_name_encoded = self._nodename.encode()
        nlen = len(node_name_encoded)
        return pack('>B{nlen}s'.format(nlen=nlen), PORT_PLEASE_REQ,
                    node_name_encoded)
