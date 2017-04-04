import socket
import time
import select
import struct
import argparse

SECONDS_OF_70_YEARS = 2208988800
PACKET_FORMAT = '!4B11I'


def build_package(wrong_time, reference_seconds, reference_fraction):
    leap_indicator = 0
    ntp_version = 4
    mode = 4
    flags_b = (leap_indicator << 6) | (ntp_version << 3) | mode
    stratum_b = 2
    polling_interval_b = 0
    clock_precision_b = 250

    root_delay_i = 2 ** 11
    root_dispersion_i = 2804
    reference_id_i = 0

    origin_seconds = 0
    origin_fraction = 0
    receive_seconds = wrong_time
    receive_fraction = 0
    transmit_seconds = wrong_time
    transmit_fraction = 0

    return struct.pack(PACKET_FORMAT, flags_b, stratum_b, polling_interval_b, clock_precision_b,
                       root_delay_i, root_dispersion_i, reference_id_i,
                       reference_seconds, reference_fraction,
                       origin_seconds, origin_fraction,
                       receive_seconds, receive_fraction,
                       transmit_seconds, transmit_fraction)


def get_time(delta_seconds):
    return int(time.time()) + SECONDS_OF_70_YEARS + delta_seconds


def start_server(args):
    port = int(args.port)
    delta = int(args.d)
    timeout = 0.1
    buffer = 1024

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', port))
    print('Server started')

    while True:
        ready_to_read, _, _ = select.select([sock], [], [], timeout)
        for x in ready_to_read:
            data, address = x.recvfrom(buffer)
            print(address)
            wrong_time = get_time(delta)
            reference_seconds, reference_fraction = struct.unpack(PACKET_FORMAT, data)[13:14]
            sock.sendto(build_package(wrong_time, reference_seconds, reference_fraction), address)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', nargs='?', default=0)
    parser.add_argument('-p', '--port', nargs='?', default=123)
    return parser.parse_args()

if __name__ == '__main__':
    arguments = parse_args()
    start_server(arguments)
