import base64
import socket
import ssl
import argparse
import sys
import os
import glob
import time
import string
import random
from getpass import getpass


class Client:
    def __init__(self, ssl, auth, verbose):
        self.buffer_size = 4096
        self.version = "MIME-Version: 1.0"

        self.ssl = ssl
        self.auth = auth
        self.verbose = verbose

        self.socket = None
        self.boundary = self.generate_boundary()

    @staticmethod
    def generate_boundary():
        symbols = string.ascii_letters + string.digits
        boundary = ''
        for x in range(0, 20):
            boundary += random.choice(symbols)
        return boundary

    def send_mail(self, connection, sender, receiver, subject, files):
        self.connect(*connection)
        self.greet()
        if self.auth:
            self.login()
        self.set_sender(sender)
        self.set_receiver(receiver)
        self.send_message(sender, receiver, subject, files)

    def connect(self, server, port):
        timeout = 3
        socket.setdefaulttimeout(timeout)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((server, port))
        if self.ssl:
            self.greet()
            self.send('STARTTLS\r\n')
            self.receive()
            self.socket = ssl.wrap_socket(self.socket)

    def greet(self):
        self.send('EHLO Test\r\n')
        time.sleep(0.5)
        self.receive()

    def send(self, message, base=False, show=True):
        if self.verbose and show:
            print(message)
        if not base:
            encoded = message.encode()
        else:
            encoded = base64.b64encode(message)
        self.socket.sendall(encoded)

    def receive(self):
        message = self.socket.recv(self.buffer_size).decode()
        self.check_response(message)
        if self.verbose:
            print("Server response: {}".format(message))
        time.sleep(0.1)

    @staticmethod
    def check_response(message):
        if len(message) < 3:
            return True
        code = message[:3]
        if code[0] != '2' and code[0] != '3':
            print('Error: {}'.format(message))
            sys.exit()
        return True

    def login(self):
        self.send('AUTH LOGIN\r\n')
        self.receive()

        login = input('Login:')
        self.send(login.encode('ascii'), True, show=False)
        self.send('\r\n')
        self.receive()

        password = getpass()
        self.send(password.encode('ascii'), True, show=False)
        self.send('\r\n')
        self.receive()

    def set_sender(self, email):
        self.send('MAIL FROM: <{0}>\r\n'.format(email))
        self.receive()

    def set_receiver(self, email):
        self.send('RCPT TO: <{0}>\r\n'.format(email))
        self.receive()

    def send_message(self, sender, receiver, subject, files):
        self.send('DATA\r\n')
        self.receive()

        message = self.form_message(sender, receiver, subject)
        self.send(message, show=False)
        self.send_files(files)

        self.send('\r\n.\r\n')
        self.receive()

        self.send('QUIT')
        self.receive()

    def form_message(self, sender, receiver, subject):
        header = ('From: <{0}>\r\n'.format(sender) +
                  'To: <{0}>\r\n'.format(receiver) +
                  'Subject: {0}\r\n'.format(subject) +
                  '{0}\r\n'.format(self.version))
        message = ('Content-Type: multipart/mixed; boundary={}'.format(self.boundary) +
                   '\r\n--{}\r\n'.format(self.boundary) +
                   'Content-type: text/plain;\r\nContent-Disposition: inline;' +
                   '\r\n\r\n\r\n\r\n\r\n')
        return header + message

    def send_files(self, files):
        for count, file in enumerate(files):
            parts = file.split('/')
            name = parts[len(parts) - 1]
            text = ('--{}\r\n'.format(self.boundary) +
                    'Content-Type: text/plain\r\n' +
                    'Content-Disposition: attachment; ' +
                    'filename={}\r\n'.format(name) +
                    'Content-Transfer-Encoding: base64\r\n\r\n')
            self.send(text, show=False)
            self.receive()

            with open(file, "rb") as opened_file:
                file_contents = opened_file.read()

            self.send(file_contents, True, show=False)
            self.socket.sendall('\r\n'.encode())
            if count == len(files) - 1:
                self.send('--{}--\r\n'.format(self.boundary), show=False)


def get_files_paths(directory):
    os.chdir(directory)
    extensions = ["jpg", "png", "gif", "bmp", "jpeg"]
    files = []
    for extension in extensions:
        for file in glob.glob('*.{}'.format(extension)):
            files.append(file)
    return files


def parse_server(server):
    default_port = 25
    chunks = server.split(':')
    return chunks[0], int(chunks[1]) if len(chunks) > 1 else default_port


def main(arguments):
    client = Client(arguments.ssl, arguments.auth, arguments.verbose)

    connection = parse_server(arguments.server)
    sender = arguments.f
    receiver = arguments.to
    subject = arguments.subject
    files = get_files_paths(arguments.directory)

    client.send_mail(connection, sender, receiver, subject, files)


def parse_args():
    parser = argparse.ArgumentParser('Program to send mail with pictures using SMTP protocol')
    parser.add_argument('--ssl', action="store_true", default=False, help='Use ssl')
    parser.add_argument('-s', '--server', help='SMTP server address')
    parser.add_argument('-t', '--to', help='Receiver mail address')
    parser.add_argument('-f', default='', help='Sender mail address')
    parser.add_argument('--subject', default='Happy Pictures', help='Mail subject')
    parser.add_argument('--auth', action="store_true", default=False, help='Mail subject')
    parser.add_argument('-v', '--verbose', action="store_true", default=False, help='Show work of protocol')
    parser.add_argument('-d', '--directory', default='.', help='Path of directory with pictures')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    try:
        main(args)
    except socket.timeout:
        print('Server took too long to respond')