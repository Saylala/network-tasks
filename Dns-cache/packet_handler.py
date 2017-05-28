import struct
import time


def parse_question(data):
    buffer = ''
    offset = 0
    while True:
        next_length = data[offset]
        offset += 1
        if next_length & 0xC0 == 0 and next_length > 0:
            next_part = data[offset: offset + next_length].decode('utf-8')
            buffer += next_part + '.'
            offset += next_length
        else:
            return buffer


class Record:
    def __init__(self, data):
        self.data = data
        self.creation_time = time.time()
        self.ttl = struct.unpack('!I', self.data[6:10])[0]

    def is_obsolete(self):
        time_since_creation = time.time() - self.creation_time
        return time_since_creation > self.ttl

    @staticmethod
    def get_records(parts, offset, count):
        records = []
        for i in range(count):
            try:
                if len(parts[offset + i]) == 0:
                    continue
                records.append(Record(b'\xc0\x0c' + parts[offset + i]))
            except IndexError:
                break
        return records

    @staticmethod
    def parse_records(data, ANCount, NSCount, ARCount):
        parts = data.split(b'\xc0\x0c')
        ANRecords = Record.get_records(parts, 0, ANCount)
        NSRecords = Record.get_records(parts, ANCount, NSCount)
        ARRecords = Record.get_records(parts, ANCount + NSCount, ARCount)
        return ANRecords, NSRecords, ARRecords


class Packet:
    _query_types = {1: 'A', 2: 'NS', 3: 'MD', 4: 'MF', 5: 'CNAME',
                    6: 'SOA', 7: 'MB', 8: 'MG', 9: 'MR', 10: 'NULL',
                    11: 'WKS', 12: 'PTR', 13: 'HINFO', 14: 'MINFO',
                    15: 'MX', 16: 'TXT', 28: 'AAAA', 255: '*'}

    def __init__(self, data):
        self.data = data
        self.query_name = self.get_query_name()
        self.query_type = self.get_query_type()
        self.records = self.get_records()

    def get_query_name(self):
        position = self.data[12:].find(b'\x00') + 1
        name = self.data[12:12 + position]
        return struct.unpack(str(position) + 's', name)[0]

    def get_query_type(self):
        position = 12 + len(self.query_name) + 1
        raw_type = self.data[position]
        return self._query_types[raw_type]

    def get_records(self):
        raw_records = self.data[12 + len(self.query_name) + 6:]
        ANCount, NSCount, ARCount = struct.unpack('!HHH', self.data[6:12])
        return Record.parse_records(raw_records, ANCount, NSCount, ARCount)


class CacheInstance:
    def __init__(self, records):
        self.records = records

    def pack_records(self):
        records = []
        for record_group in self.records:
            for record in record_group:
                records.append(record.data)
        packed = b''.join(records)
        return packed

    def pack_header(self, request):
        QDCount = 1
        ANCount, NSCount, ARCount = len(self.records[0]), len(self.records[1]), len(self.records[2])
        id = request[:2]
        flags = b'\x81\x80'
        return id + flags + struct.pack('!HHHH', QDCount, ANCount, NSCount, ARCount)

    def pack(self, request):
        index = 12 + request[12:].find(b'\x00') + 5
        question = request[12:index]
        return self.pack_header(request) + question + self.pack_records()
