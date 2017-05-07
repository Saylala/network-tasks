import argparse
import socket
import struct
from concurrent.futures import ThreadPoolExecutor

THREADS = 256
CONNECTION_TIMEOUT = 1


def is_http(sock):
    # sock.send(b'OPTIONS * HTTP/1.1\r\n')
    sock.send(b'GET TEST HTTP/1.1\r\n\r\n')
    data = sock.recv(1024)
    return data[:4] == b'HTTP' or b'<html>' in data


def is_smtp(sock):
    data = sock.recv(1024)
    return data[:3] == b'220'


def is_pop3(sock):
    data = sock.recv(1024)
    return data[:3] == b'+OK'


def is_imap(sock):
    data = sock.recv(1024)
    return data[:4] == b'* OK'


def is_dns(host, port):
    packet = struct.pack(">HHHHHH", 12049, 256, 1, 0, 0, 0)
    split_url = "www.google.com".split(".")
    for part in split_url:
        packet += struct.pack("B", len(part))
        for byte in bytes(part, encoding='utf-8'):
            packet += struct.pack("b", byte)
    packet += struct.pack("BHH", 0, 1, 1)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(bytes(packet), (host, port))
    data, address = sock.recvfrom(1024)
    sock.close()
    return True


def is_sntp(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = '\x1b' + 47 * '\0'
    sock.sendto(data.encode(), (host, port))
    data, address = sock.recvfrom(1024)
    sock.close()
    return True


def detect_protocol_type(host, port, is_tcp_socket=True):
    protocols_with_tcp = {'HTTP': is_http, 'SMTP': is_smtp, 'POP3': is_pop3, 'IMAP': is_imap}
    protocols_with_udp = {'SNTP': is_sntp, 'DNS': is_dns}

    if is_tcp_socket:
        for protocol in protocols_with_tcp:
            try:
                with socket.create_connection((host, port), CONNECTION_TIMEOUT) as sock:
                    if protocols_with_tcp[protocol](sock):
                        return protocol
            except socket.timeout:
                continue
    else:
        for protocol in protocols_with_udp:
            try:
                if protocols_with_udp[protocol](host, port):
                    return protocol
            except socket.timeout:
                continue
    return ''


def scan_tcp(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if sock.connect_ex((host, port)) == 0:
        sock.close()
        port_type = detect_protocol_type(host, port)
        print('TCP {} {}'.format(port, port_type))


def scan_udp(host, port):
    port_type = detect_protocol_type(host, port, is_tcp_socket=False)
    if port_type != '':
        print('UDP {} {}'.format(port, port_type))
        return
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(b'', (host, port))
    try:
        data = sock.recvfrom(1024)
        print('UDP {}'.format(port))
    except:
        pass
    finally:
        sock.close()


def scan(scan_func, host, ports_range):
    socket.setdefaulttimeout(CONNECTION_TIMEOUT)
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        for port in ports_range:
            executor.submit(scan_func, host, port)


def scan_ports(args):
    host = args.host
    ports = range(args.ports[0], args.ports[1])
    if args.u:
        scan(scan_udp, host, ports)
    if args.t:
        scan(scan_tcp, host, ports)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('host')
    parser.add_argument('-p', '--ports', nargs=2, type=int)
    parser.add_argument('-t', action="store_true")
    parser.add_argument('-u', action="store_true")
    return parser.parse_args()

if __name__ == '__main__':
    arguments = parse_args()
    scan_ports(arguments)
