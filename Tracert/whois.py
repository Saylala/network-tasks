import socket
import re
import select
from collections import namedtuple

Info = namedtuple("Info", "name, as_value, country")

BUFFER_SIZE = 1024
PORT = 43
SOCKET_TIMEOUT = 1
SOCKET_POLLING_PERIOD = 0.25
REGEXES = None


def get_info(address):
    if REGEXES is None:
        cache_regexes()
    info = find_info(address)
    return format_info(*info)


def cache_regexes():
    global REGEXES
    values = ['whois', 'netname', 'NetName', 'origin', 'OriginAS', 'country', 'Country']
    pattern = '{}:(.+)'
    REGEXES = dict()
    for value in values:
        REGEXES[value] = re.compile(pattern.format(value))


def find_info(address):
    server = get_correct_server(address)
    if server is None:
        return None, None, None

    server_response = get_info_from_server(address, server)
    info = get_info_to_find(server)
    name = find_pattern(server_response, info.name)
    as_value = find_pattern(server_response, info.as_value)
    country = find_pattern(server_response, info.country)
    return name, as_value, country


def get_correct_server(address):
    server_response = get_info_from_server(address, 'whois.iana.org')
    pattern = 'whois'
    server = find_pattern(server_response, pattern)
    return server


def get_info_from_server(ip, server):
    with socket.create_connection((server, PORT)) as sock:
        sock.settimeout(SOCKET_TIMEOUT)
        sock.sendall((ip + '\r\n').encode())
        return receive_all(sock).decode('utf-8')


def receive_all(sock):
    result = b''
    while select.select([sock], [], [], SOCKET_POLLING_PERIOD)[0]:
        data = sock.recv(BUFFER_SIZE)
        if len(data) == 0:
            break
        result += data
    return result


def get_info_to_find(server):
    for pattern in ['lacnic', 'arin']:
        if pattern in server:
            return Info('NetName', 'OriginAS', 'Country')
    return Info('netname', 'origin', 'country')


def find_pattern(string, pattern):
    regex = REGEXES[pattern]
    result = regex.search(string)
    if result is None:
        return result
    return result.groups()[0].strip()


def format_info(name, as_value, country):
    info = ''
    if name:
        info += '{0} '.format(name)
    if as_value:
        info += '{0} '.format(as_value)
    if country:
        info += country
    return info
