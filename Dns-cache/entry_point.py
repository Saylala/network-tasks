import argparse
import socket
from dns_server import Server

BUFFER_SIZE = 4096


def prepare_socket(arguments):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(('127.0.0.1', arguments.port))
    except Exception as e:
        return None
    return sock


def start_server(arguments):
    sock = prepare_socket(arguments)

    if sock is None:
        print('Server start failed. There is something wrong with PORT: {}'.format(arguments.port))
        return

    print('Server started at PORT: {}'.format(arguments.port))
    with sock:
        forwarder = (arguments.forwarder, arguments.port)
        server = Server(forwarder, sock)
        while True:
            data, address = sock.recvfrom(BUFFER_SIZE)  # TODO: make killable
            # print('{} connected'.format(address[0]))
            server.handle_request(data, address)


def parse_args():
    parser = argparse.ArgumentParser('DNS server')
    parser.add_argument('-p', '--port', type=int, default=53)
    parser.add_argument('-f', '--forwarder', type=str, default='8.8.8.8')
    # parser.add_argument('-h', '--help')  # TODO: implement help
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    start_server(args)
