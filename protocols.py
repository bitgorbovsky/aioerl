''' protocols module '''

from struct import unpack_from, pack, calcsize
import random
import hashlib

random.seed()


def gen_digest(*args, **kwargs):
    hashfn = hashlib.md5()
    hashfn.update(b''.join(
        s if isinstance(s, bytes) else bytes(str(s), 'utf-8')
        for s in args
    ))
    if kwargs.get('hex', False):
        return hashfn.hexdigest()

    return hashfn.digest()


class UnexpectedTag(Exception):
    pass


def expect(expected_tag, format_spec=None):
    def wrapper(f):
        def method(self, message):
            tag, *message = message
            message = bytes(message)

            if expected_tag != chr(tag):
                raise UnexpectedTag(chr(tag))

            if format_spec:
                offset = calcsize(format_spec)
                unpacked = unpack_from(format_spec, message)
                tail = message[offset:]

                return f(self, *(unpacked + (tail, )))

            return f(self, message)
        return method
    return wrapper


DF_PUBLISHED = 1
DF_ATOM_CACHE = 2
DF_EXTENDED_REFERENCES = 4
DF_DIST_MONITOR = 8
DF_FUN_TAGS = 0x10
DF_DIST_MONITOR_NAME = 0x20
DF_HIDDEN_ATOM_CACHE = 0x40
DF_NEW_FUN_TAGS = 0x80
DF_EXTENDED_PIDS_PORTS = 0x100
DF_EXPORT_PTR_TAG = 0x200
DF_BIT_BINARIES = 0x400
DF_NEW_FLOATS = 0x800
DF_UNICODE_IO = 0x1000
DF_DIST_HDR_ATOM_CACHE = 0x2000
DF_SMALL_ATOM_TAGS = 0x4000
DF_UTF8_ATOMS = 0x10000
DF_MAP_TAG = 0x20000


class IProtocol:
    pass


class HandshakeProtocol(IProtocol):
    ''' Challenge Handshake Authentication Protocol Scheme '''

    def __init__(self, connection, name, cookie):
        self.connection = connection
        self.node_name = name
        self.cookie = cookie
        self.__expectation = self.__recv_name

    def accept_packet(self, packet):
        message = packet[calcsize('>H'):]

        data, expectation = self.__expectation(message)
        for chunk in data:
            self.send(chunk)

        if isinstance(expectation, IProtocol):
            return expectation

        self.__expectation = expectation

    def send(self, message):
        packet = b''.join([pack('>H', len(message)), message])
        self.connection.write(packet)

    @expect('s')
    def __recv_status(self, message):
        status = message.decode()

        if status in ['ok', 'ok_simultaneous']:
            challenge = gen_challenge()
            return [challenge], self.__recv_challenge_reply

        if status == 'nok':
            self.connection.close()
            return

        if status == 'not_allowed':
            self.connection.close()
            return

        if status == 'alive':
            return [], MessageProtocol()

    @expect('n', '>HI')
    def __recv_name(self, version, flags, node_name):
        node_name = node_name.decode()
        challenge = random.randint(0, 4294967295)
        self.digest = gen_digest(self.cookie, challenge)

        challenge = b''.join([
            pack(
                '>cHII',    # message byte structure
                b'n',       # c: message tag 'n', 1 byte
                version,    # H: distribution version, 2 bytes
                flags,      # I: distribution flags, 4 bytes
                challenge   # I: challenge, 4 bytes
            ),
            self.node_name.encode()
        ])

        return [b'sok', challenge], self.__recv_challenge

    @expect('r', '>I')
    def __recv_challenge(self, challenge, digest):
        ack = b''.join([
            b'a',
            gen_digest(self.cookie, challenge)
        ])

        if self.digest == digest:
            return [ack], MessageProtocol()

        self.connection.close()

    def __wait_ack(self, message):
        return [], self.__wait_ack


class MessageProtocol(IProtocol):

    def accept_packet(self, packet):
        offset = calcsize('>I')
        message = packet[offset:]
        dist_header_prefix = message[0:2]

        if dist_header_prefix != bytes([131, 68]):
            raise UnexpectedTag()

        message = message[2:]
        atom_cache_refs = message[0]
        print('atom cache refs:', atom_cache_refs)

        flags_len = (atom_cache_refs // 2) + 1
        flags = message[1:flags_len]
        message = message[(1 + flags_len):]
        print(message)
