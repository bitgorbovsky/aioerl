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


class UnknownEPMDResponse(EPMDresponse):
    pass
