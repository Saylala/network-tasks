import argparse
import sys
from dns_server import Server


def parse_args():
    parser = argparse.ArgumentParser('Forwarding DNS server')
    parser.add_argument('-p', '--port', type=int, default=53, help='port to work on')
    parser.add_argument('-f', '--forwarder', type=str, default='8.8.8.8', help='forwarder to ask')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    try:
        server = Server(args)
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit()
