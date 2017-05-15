import argparse
import json
import os
import re
import urllib.parse
import urllib.request
from http_handler import HTTPServerHandler
from http.server import HTTPServer
from webbrowser import open_new


def save_pictures(pictures):
    for picture in pictures:
        filename = picture.split('/')[-1]
        directory = 'Images'
        if not os.path.exists(directory):
            os.makedirs(directory)
        urllib.request.urlretrieve(picture, '{}/{}'.format(directory, filename))


def get_pictures_paths(picture_params):
    paths = []
    for param in picture_params:
        if param.startswith('photo') or param.startswith('src'):
            paths.append(picture_params[param])
    return paths


def get_pictures(json_data):
    attachments = json_data['response'][0]['attachments']
    pictures = []
    for attachment in attachments:
        if attachment['type'] == 'photo':
            pictures += get_pictures_paths(attachment['photo'])
    return pictures


def build_request(post_id, access_token):
    method_name = 'wall.getById'
    parameters = 'posts={}'.format(post_id)
    return 'https://api.vk.com/method/{}?{}&{}'.format(method_name, parameters, access_token)


def parse_post_id(url):
    pattern = 'w=wall(-?[0-9]+_[0-9]+)'
    regex = re.compile(pattern)
    result = regex.search(url)
    if result is None:
        return result
    return result.groups()[0]


def get_access_token(request):
    open_new(request)

    address = ('localhost', 456)
    http_server = HTTPServer(address, HTTPServerHandler)

    http_server.socket.settimeout(40)
    http_server.handle_request()

    return http_server.access_token


def build_auth_request():
    base = 'https://oauth.vk.com/authorize?'
    app_id = 'client_id=6030058'
    redirect_uri = 'redirect_uri=http://localhost:456/'
    display = 'display=page'
    version = 'v=5.52'
    response_type = 'response_type=code'
    return '{}{}&scope=friends&{}&{}&{}&{}'.format(base, app_id, redirect_uri, display, version, response_type)


def main(arguments):
    auth_request = build_auth_request()
    access_token = get_access_token(auth_request)
    post_id = parse_post_id(arguments.url)

    request = build_request(post_id, access_token)
    response = urllib.request.urlopen(request).read().decode('utf-8')
    json_data = json.loads(response)
    pictures = get_pictures(json_data)
    save_pictures(pictures)


def parse_arguments():
    parser = argparse.ArgumentParser('Fetch images from vk publication')
    parser.add_argument('url', help='publication url')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_arguments()
    main(args)
