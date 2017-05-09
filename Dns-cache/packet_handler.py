import time
import struct


def parse_records(name, data, counts):
    records = []
    pointer = 0
    packets = data[2:].split(b'\xc0\x0c')
    for count in counts:
        rrs = []
        for i in range(count):
            try:
                rrs.append(ResourceRecord(b'\xc0\x0c' + packets[pointer + i], time.time()))
            except IndexError:
                break
        records.append(rrs)
        pointer += count
    return records


def pack_packet(cache_data, request):
    ind = 12 + request[12:].find(b'\x00') + 5
    question = request[12:ind]
    counts = struct.pack('!HHHH', 1, len(cache_data[0]), len(cache_data[1]), len(cache_data[2]))
    records = b''.join([r.data for rrs in cache_data for r in rrs])
    packet = request[:2] + b'\x81\x80' + counts + question + records
    return packet


class DNSPacket:
    def __init__(self, data):
        self.data = data

        self.header = list(struct.unpack('!HHHHHH', self.data[0:12]))
        self.query_name = None
        self.parse_header()

        oth = data[12 + len(self.query_name) + 5:]
        self.records = parse_records(self.query_name, oth, self.header[3:])

    def parse_header(self):
        self.header = list(struct.unpack('!HHHHHH', self.data[0:12]))

        ln = self.data[12:].find(b'\x00')
        name = self.data[12:12 + ln]
        self.query_name = struct.unpack(str(ln) + 's', name)[0]

    def pack(self):
        ln = len(self.query_name)
        b_header = struct.pack('!HHHHHH', *self.header)
        off = 13 + ln
        b_name = struct.pack(str(ln) + 's', self.query_name) + b'\x00'
        b_rrs = b''.join([r.data for rrs in self.records for r in rrs])
        return b_header + b_name + self.data[off:off + 4] + b_rrs


class ResourceRecord:
    def __init__(self, record_data, record_time):
        self.data = record_data
        self._ttl = int.from_bytes(self.data[6:10] or '\x00', byteorder='big')
        self.time = record_time

    @property
    def ttl(self):
        self._ttl = int(self._ttl - time.time() + self.time)
        return self._ttl
