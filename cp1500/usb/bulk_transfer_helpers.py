"""Static-derived DBGmon RAM bulk transport; import performs no USB operations.

Use BulkTransfer(existing_open_TestSession).write/read with OWNED allocation.
Aw/o: file0x2a2160/0x2a2180; Mr/r: file0x2a25b8/0x2a25f4.
Run this file for offline packet/response tests only.
"""
import struct

PREFIX = b'\x1bD'
MAX_CHUNK = 1024  # 14+1024 == negotiated 0x040e submessage size


def address_command(operation, address):
    if operation not in (b'Aw', b'Mr') or not 0 <= address <= 0xffffffff:
        raise ValueError('invalid operation/address')
    return PREFIX + operation + struct.pack('<I', address)


def length_command(operation, length):
    if operation not in (b'o', b'r') or not 1 <= length <= MAX_CHUNK:
        raise ValueError('invalid operation/chunk length')
    return PREFIX + operation + struct.pack('<H', length) + b'\0' * 3


def validate_submessage(sub):
    if len(sub) < 6 or sub[1] != 1 or struct.unpack_from('<H', sub, 2)[0] != len(sub):
        raise RuntimeError(f'invalid channel1 reply: {sub.hex()}')


def check_ack(sub):
    validate_submessage(sub)
    if len(sub) != 6:
        raise RuntimeError(f'expected bare6-byte ACK: {sub.hex()}')


class BulkTransfer:
    """Wrap an open session implementing exchange(list[8B-command+body]).

    Commands share per-channel pointer state: do not interleave other users.
    No automatic retry after transport errors (write progress may be ambiguous).
    Default1024-byte chunks; batch8 conservatively stays below16KiB mux buffer.
    ACK confirms protocol completion; readback validates actual content.
    """
    def __init__(self, session, chunk_size=MAX_CHUNK, batch_size=8):
        if not 1 <= chunk_size <= MAX_CHUNK or not 1 <= batch_size <= 8:
            raise ValueError('chunk_size1..1024, batch_size1..8 required')
        self.session = session
        self.chunk_size = chunk_size
        self.batch_size = batch_size

    def _exchange(self, commands):
        replies = self.session.exchange(commands)
        if len(replies) != len(commands):
            raise RuntimeError('unexpected command reply count')
        return replies

    @staticmethod
    def _range(address, length):
        if not 0 <= address <= 0xffffffff or length < 0 or address + length > 0x100000000:
            raise ValueError('32-bit address range overflow')

    def write(self, address, data, verify=False, progress=None):
        data = bytes(data)
        self._range(address, len(data))
        if not data:
            return
        check_ack(self._exchange([address_command(b'Aw', address)])[0])
        offset = 0
        while offset < len(data):
            chunks = [data[o:o + self.chunk_size] for o in
                      range(offset, min(len(data), offset + self.chunk_size * self.batch_size), self.chunk_size)]
            commands = [length_command(b'o', len(chunk)) + chunk for chunk in chunks]
            for reply in self._exchange(commands):
                check_ack(reply)
            offset += sum(map(len, chunks))
            if progress:
                progress(offset, len(data))
        if verify and self.read(address, len(data)) != data:
            raise RuntimeError('bulk write readback mismatch')

    def read(self, address, length, progress=None):
        self._range(address, length)
        if not length:
            return b''
        check_ack(self._exchange([address_command(b'Mr', address)])[0])
        result = bytearray()
        while len(result) < length:
            sizes = [min(self.chunk_size, length - o) for o in
                     range(len(result), min(length, len(result) + self.chunk_size * self.batch_size), self.chunk_size)]
            commands = [length_command(b'r', n) for n in sizes]
            for command, n, reply in zip(commands, sizes, self._exchange(commands)):
                validate_submessage(reply)
                # Receiver rewrites D->d for lowercase r, output adds data after8B header.
                expected = command[:1] + b'd' + command[2:]
                if len(reply) != 14 + n or reply[6:14] != expected:
                    raise RuntimeError(f'invalid bulk-read reply ({len(reply)}B): {reply[:20].hex()}')
                result.extend(reply[14:])
            if progress:
                progress(len(result), length)
        return bytes(result)


def _offline_test():
    class FakeSession:
        def __init__(self):
            self.memory = bytearray(30000)
            self.wptr = self.rptr = 0
            self.commands = []
        def exchange(self, commands):
            self.commands.extend(commands)
            replies = []
            assert sum(6 + len(c) for c in commands) < 0x4000
            for c in commands:
                body = b''
                if c[:4] == b'\x1bDAw':
                    self.wptr = struct.unpack('<I', c[4:])[0]
                elif c[:4] == b'\x1bDMr':
                    self.rptr = struct.unpack('<I', c[4:])[0]
                elif c[:3] == b'\x1bDo':
                    n = struct.unpack_from('<H', c, 3)[0]
                    assert n == len(c) - 8
                    self.memory[self.wptr:self.wptr+n] = c[8:]
                    self.wptr += n
                elif c[:3] == b'\x1bDr':
                    n = struct.unpack_from('<H', c, 3)[0]
                    body = b'\x1bdr' + c[3:] + self.memory[self.rptr:self.rptr+n]
                    self.rptr += n
                else:
                    raise AssertionError(c)
                replies.append(struct.pack('<BBHBB', 1, 1, 6+len(body), 1, 0) + body)
            return replies
    assert address_command(b'Aw', 0x41234560).hex() == '1b44417760452341'
    assert address_command(b'Mr', 0x41234560).hex() == '1b444d7260452341'
    assert length_command(b'o', 1024).hex() == '1b446f0004000000'
    for size in (0, 1, 2, 3, 4, 1023, 1024, 1025, 8192, 17643):
        s = FakeSession()
        helper = BulkTransfer(s)
        data = bytes((i * 37 + 11) & 255 for i in range(size))
        helper.write(3, data, verify=True)
        assert helper.read(3, size) == data
        assert s.memory[:3] == b'\0'*3 and s.memory[3+size:4+size] == b'\0'
    for bad in (b'', b'\0'*6, struct.pack('<BBHBB',0,1,14,1,0)):
        try:
            check_ack(bad)
        except RuntimeError:
            pass
        else:
            raise AssertionError('malformed ACK accepted')
    print('offline bulk packet, chunking, readback and malformed-reply checks passed; no USB accessed')


if __name__ == '__main__':
    _offline_test()
