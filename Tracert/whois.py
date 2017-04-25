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
    values = ['netname', 'NetName', 'origin', 'OriginAS', 'country', 'Country']
    pattern = '{}:(.+)'
    REGEXES = dict()
    for value in values:
        REGEXES[value] = re.compile(pattern.format(value))


def find_info(address):
    servers = ['arin', 'ripe', 'afrinic', 'lacnic', 'apnic']
    for server in servers:
        server_response = get_info_from_server(address, server)
        info = get_info_to_find(server)
        name = find_pattern(server_response, info.name)
        if not is_acceptable_response(name, servers):
            continue
        as_value = find_pattern(server_response, info.as_value)
        country = find_pattern(server_response, info.country)
        return name, as_value, country
    return None, None, None


def get_info_from_server(ip, server):
    address = "whois.{name}.net".format(name=server)
    with socket.create_connection((address, PORT)) as sock:
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
    if server in ['lacnic', 'arin']:
        return Info('NetName', 'OriginAS', 'Country')
    return Info('netname', 'origin', 'country')


def find_pattern(string, pattern):
    regex = REGEXES[pattern]
    result = regex.search(string)
    if result is None:
        return result
    return result.groups()[0].strip()


def is_acceptable_response(name_response, servers):
    for server_name in servers:
        if name_response is None or server_name.upper() in name_response:
            return False
    return True


def format_info(name, as_value, country):
    info = ''
    if name:
        info += '{0} '.format(name)
    if as_value:
        info += '{0} '.format(name)
    if country:
        info += country
    return info
