import select
import socket
import sys
from packet_handler import CacheInstance
from packet_handler import Packet
from packet_handler import parse_question


class Server:
    def __init__(self, arguments):
        self.port = arguments.port
        self.cache = {}
        self.forwarder = self.get_forwarder(arguments.forwarder)
        self.sock = self.get_socket(self.port)

        self.socket_timeout = 1
        self.socket_polling_period = 0.25
        self.buffer_size = 4096

    @staticmethod
    def get_forwarder(raw_forwarder):
        port = 53
        chunks = raw_forwarder.split(':')
        return chunks[0], int(chunks[1]) if len(chunks) > 1 else port

    @staticmethod
    def get_socket(port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind(('', port))
        except Exception as e:
            print('Server start failed. There is something wrong with PORT: {}'.format(port))
            return sys.exit()
        return sock

    def serve_forever(self):
        print('Server started at PORT: {}'.format(self.port))
        with self.sock:
            while True:
                ready_read, _, _ = select.select([self.sock], [], [], self.socket_polling_period)
                if ready_read:
                    data, address = self.sock.recvfrom(self.buffer_size)
                    self.handle_request(data, address)

    def handle_request(self, request, client):
        packet = Packet(request)
        data = self.search_cache(packet.query_name, request)
        source = 'cache'
        if data is None:
            data = self.ask_forwarder(packet.query_name, request)
            source = 'forwarder'

        if data is None:
            self.print_forwarder_error(client, packet.query_type, packet.query_name)
        else:
            self.sock.sendto(data, client)
            self.print_report(client[0], packet.query_type, packet.query_name, source)

    def search_cache(self, key, request):
        if key not in self.cache:
            return None

        cache_data = self.cache[key]
        if self.is_expired(cache_data):
            return None

        return cache_data.pack(request)

    @staticmethod
    def is_expired(cache_data):
        for records in cache_data.records:
            for record in records:
                if record.is_obsolete():
                    return True
        return False

    def ask_forwarder(self, key, request):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.socket_timeout)
        with sock:
            try:
                sock.sendto(request, self.forwarder)
                data = sock.recv(self.buffer_size)
                reply = Packet(data)
            except socket.error:
                return None

        self.cache[key] = CacheInstance(reply.records)
        return data

    @staticmethod
    def print_forwarder_error(client, request_type, name):
        question = parse_question(name)
        report = 'Forwarder does not respond. Can not resolve {}, {}, {}'
        print(report.format(client, request_type, question))

    @staticmethod
    def print_report(client, request_type, name, source):
        question = parse_question(name)
        report = '{}, {}, {}, {}'.format(client, request_type, question, source)
        print(report)

