import socket
import time
import select
import struct
import threading
import argparse
from concurrent.futures import ThreadPoolExecutor


SECONDS_OF_70_YEARS = 2208988800
PACKET_FORMAT = '!4B11I'
BUFFER_SIZE = 1024
THREADS_COUNT = 512


def build_package(time_with_delta, reference_seconds, reference_fraction):
    leap_indicator = 0
    ntp_version = 4
    mode = 4
    flags_b = (leap_indicator << 6) | (ntp_version << 3) | mode
    stratum_b = 2

    polling_interval_b = 0
    clock_precision_b = 0
    root_delay_i = 0
    root_dispersion_i = 0
    reference_id_i = 0

    origin_seconds = reference_seconds
    origin_fraction = reference_fraction
    receive_seconds = time_with_delta
    receive_fraction = reference_fraction
    transmit_seconds = time_with_delta
    transmit_fraction = reference_fraction

    return struct.pack(PACKET_FORMAT, flags_b, stratum_b, polling_interval_b, clock_precision_b,
                       root_delay_i, root_dispersion_i, reference_id_i,
                       reference_seconds, reference_fraction,
                       origin_seconds, origin_fraction,
                       receive_seconds, receive_fraction,
                       transmit_seconds, transmit_fraction)


def get_time_with_delta(delta_seconds):
    return int(time.time()) + SECONDS_OF_70_YEARS + delta_seconds


def handle_request(sock, delta):
    data, address = sock.recvfrom(BUFFER_SIZE)
    print(address[0])
    wrong_time = get_time_with_delta(delta)
    reference_seconds, reference_fraction = struct.unpack(PACKET_FORMAT, data)[13:15]
    sock.sendto(build_package(wrong_time, reference_seconds, reference_fraction), address)


def start_server(args):
    port = args.port
    delta = args.d
    timeout = 0.1

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', port))
    print('Server started')

    while True:
        ready_to_read, _, _ = select.select([sock], [], [], timeout)
        with ThreadPoolExecutor(max_workers=THREADS_COUNT) as executor:
            for x in ready_to_read:
                executor.submit(handle_request, x, delta)
            #     threading.Thread(target=handle_request, args=(x, delta)).start()
            # for port in ports_range:
            #         executor.submit(try_connect, host, port)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', nargs='?', default=0, type=int)
    parser.add_argument('-p', '--port', nargs='?', default=123, type=int)
    return parser.parse_args()

if __name__ == '__main__':
    arguments = parse_args()
    start_server(arguments)
