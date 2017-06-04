import json
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from urllib.request import urlopen
from webbrowser import open_new

PORT = 1234


class HTTPServerHandler(BaseHTTPRequestHandler):
    @staticmethod
    def build_token_request():
        base = 'https://oauth.vk.com/access_token?'
        id = 'client_id={}'.format('6030058')
        secret = '&client_secret={}'.format('4I4fJIYihlYd4UO7Truz')
        uri = '&redirect_uri={}'.format('http://localhost:{}/'.format(PORT))
        code = '&code='
        return base + id + secret + uri + code

    @staticmethod
    def get_access_token(auth_code):
        url = HTTPServerHandler.build_token_request() + auth_code
        response = urlopen(url).read()
        return json.loads(response.decode())['access_token']

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        auth_code = self.path.split('=')[1]
        self.server.access_token = self.get_access_token(auth_code)

    def log_message(self, format, *args):
        return


def build_auth_request():
    base = 'https://oauth.vk.com/authorize?'
    app_id = 'client_id=6030058'
    redirect_uri = 'redirect_uri=http://localhost:{}/'.format(PORT)
    display = 'display=page'
    version = 'v=5.52'
    response_type = 'response_type=code'
    return '{}{}&{}&{}&{}&{}'.format(base, app_id, redirect_uri, display, version, response_type)


def get_access_token():
    request = build_auth_request()

    open_new(request)

    address = ('localhost', PORT)
    http_server = HTTPServer(address, HTTPServerHandler)

    http_server.socket.settimeout(40)
    http_server.handle_request()

    return http_server.access_token


def get_response(post_id, access_token):
    request = build_request(post_id, access_token)
    response = urlopen(request).read().decode('utf-8')
    return response


def build_request(post_id, access_token):
    method_name = 'wall.getById'
    parameters = 'posts={}'.format(post_id)
    return 'https://api.vk.com/method/{}?{}&{}'.format(method_name, parameters, access_token)
