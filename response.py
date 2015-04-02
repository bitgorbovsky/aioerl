# coding: utf-8


from bitstring import Bits, BitArray, ConstBitStream


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
        buf = ConstBitStream(data)
        ptype = buf.read('uint:8')
        if ptype != 121:
            return

        success = buf.read('uint:8')
        creation = buf.read('bytes:2')
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

    @classmethod
    def decode(cls, data):
        buf = ConstBitStream(data)
        ptype = buf.read('uint:8')
        if ptype != 119:
            return

        status = buf.read('uint:8')
        if status > 0:
            return

        port_no = buf.read('uint:16')
        node_type = buf.read('uint:8')
        protocol = buf.read('uint:8')
        high_ver = buf.read('uint:16')
        low_ver = buf.read('uint:16')
        nlen = buf.read('uint:16')
        node_name = buf.read('bytes:%d' % nlen).decode('utf-8')
        elen = buf.read('uint:16')
        extra = buf.read('bytes:%d' % elen)
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


class UnknownEPMDResponse(EPMDresponse):
    pass
