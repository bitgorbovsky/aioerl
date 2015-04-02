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
        if ptype == 121:
            success = buf.read('uint:8')
            creation = buf.read('bytes:2')
            return Alive2Response(data, success == 0, creation)


class UnknownEPMDResponse(EPMDresponse):
    pass
