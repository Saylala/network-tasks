import json
from http.server import BaseHTTPRequestHandler
from urllib.request import urlopen


class HTTPServerHandler(BaseHTTPRequestHandler):
    @staticmethod
    def build_token_request():
        base = 'https://oauth.vk.com/access_token?'
        id = 'client_id={}'.format('6030058')
        secret = '&client_secret={}'.format('4I4fJIYihlYd4UO7Truz')
        uri = '&redirect_uri={}'.format('http://localhost:456/')
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
