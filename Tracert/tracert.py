import argparse
import ipaddress
import socket
import string
import struct
import whois

MAX_HOPS = 30
PORT = 33434
BUFFER_SIZE = 1024
PACKET_FORMAT = '!BBHHH'
SOCKET_TIMEOUT = 1


def print_report(ttl, ip_info, additional_info):
    report = '{0}. {1}\r\n{2}'.format(ttl, ip_info, additional_info)
    print(report)


def get_node_info(address):
    if ipaddress.ip_address(address).is_private:
        return address, 'local\r\n'
    return address, whois.get_info(address)


def form_icmp_packet():
    message_type = 8
    code = 0
    checksum = 26980  # suggested by WireShark
    identifier = 0
    sequence_number = 0
    payload = string.ascii_lowercase.encode()
    return struct.pack(PACKET_FORMAT, message_type, code, checksum, identifier, sequence_number) + payload


def trace_address(address):
    if ipaddress.ip_address(address).is_private:
        yield 1, address, 'local'
        return
    with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
        sock.settimeout(SOCKET_TIMEOUT)
        for ttl in range(1, MAX_HOPS + 1):
            sock.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
            sock.sendto(form_icmp_packet(), (address, PORT))

            try:
                reply, addr = sock.recvfrom(BUFFER_SIZE)
                ip_info, additional_info = get_node_info(addr[0])
            except socket.timeout:
                ip_info, additional_info = '*', ''
                addr = None, None

            yield ttl, ip_info, additional_info
            if addr[0] == address:
                break


def get_destination_by_address(address):
    try:
        destination = socket.gethostbyname(address)
        return destination
    except socket.gaierror:
        destination = socket.gethostbyaddr(address)
        return destination


def start_tracing(arguments):
    for address in arguments.addresses:
        try:
            destination = get_destination_by_address(address)
        except socket.gaierror:
            print("{} is invalid".format(str(address)))
            continue
        for report in trace_address(socket.gethostbyname(address)):
            print_report(*report)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("addresses", nargs='+')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        start_tracing(args)
    except OSError:
        print('Application need administrator rights')
    except KeyboardInterrupt:
        pass
