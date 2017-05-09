import socket
import time
from packet_handler import DNSPacket
from packet_handler import pack_packet

SOCKET_TIMEOUT = 1
BUFFER_SIZE = 4096


class Server:
    def __init__(self, forwarder, sock):
        self.cache = {}
        self.forwarder = forwarder
        self.sock = sock

    def handle_request(self, request, client):
        request_type = ''  # TODO: implement type

        packet = DNSPacket(request)
        key = packet.query_name

        data = self.search_cache(key, request)
        source = 'cache'
        if data is None:
            data = self.ask_forwarder(key, request)
            source = 'forwarder'

        if data is None:
            self.print_forwarder_error(client, request_type, request)
        else:
            self.sock.sendto(data, client)
            self.print_report(client[0], request_type, request_type, source)

    def search_cache(self, key, request):
        if key not in self.cache:
            return None

        cache_data = self.cache[key]
        if self.is_obsolete(cache_data):
            return None

        return pack_packet(cache_data, request)

    @staticmethod
    def is_obsolete(cache_data):
        for records in cache_data:
            for record in records:
                if not time.time() - record.time <= record.ttl:
                    return True
        return False

    def ask_forwarder(self, key, request):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(SOCKET_TIMEOUT)
        with sock:
            try:
                sock.sendto(request, self.forwarder)
                data = sock.recv(BUFFER_SIZE)
                reply = DNSPacket(data)
            except socket.error:
                return None

        self.cache[key] = reply.records
        return reply.pack()

    @staticmethod
    def print_forwarder_error(client, request_type, request):
        report = 'Forwarder does not respond. Can not resolve {}, {}, {}'
        print(report.format(client, request_type, request))

    @staticmethod
    def print_report(client, request_type, request, source):
        report = '{}, {}, {}, {}'.format(client, request_type, request, source)
        print(report)

