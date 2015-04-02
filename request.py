# coding: utf-8


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

    def _get_raw_data(self):
        raise NotImplementedError("protected method _get_raw_data should be "
                                  "implemented!")


class EmptyEPMDRequest(EPMDRequest):

    def _get_raw_data(self):
        pass

    def encode(self):
        return b'\x00'


class Alive2Request(EPMDRequest):

    expected_response_len = 4

    def __init__(self, port_no,
                       node_type=NORMAL_ERL_NODE,
                       protocol=TCP_PROTOCOL,
                       high_ver=HIGHEST_VERSION,
                       low_ver=LOWEST_VERSION,
                       node_name='bit',
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


class PortRequest(EPMDRequest):

    def __init__(self, nodename):
        self._nodename = nodename

    def _get_raw_data(self):
        pass
