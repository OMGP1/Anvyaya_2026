"""WSGI transport for the same tested handlers, served with Waitress.

One process owns sessions and the write lock. Restarting invalidates sessions.
Use HTTPS at the reverse proxy; never expose the internal listener directly.
"""
from email.message import Message
from http import HTTPStatus
from urllib.parse import quote
import server


class Request(server.Handler):
    """Adapt the handler's request/response boundary without a second router."""

    def __init__(self, environ, start_response):
        self.headers = Message()
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                self.headers[key[5:].replace('_', '-')] = value
        self.headers['Content-Length'] = environ.get('CONTENT_LENGTH') or '0'
        self.headers['Content-Type'] = environ.get('CONTENT_TYPE', '')
        self.path = quote(environ.get('PATH_INFO', '/'), safe='/')
        if environ.get('QUERY_STRING'):
            self.path += '?' + environ['QUERY_STRING']
        self.client_address = (environ.get('REMOTE_ADDR', 'unknown'), 0)
        self.rfile = environ['wsgi.input']
        self.start_response = start_response
        self.result = b''

    def send(self, status, value, content_type='application/json', headers=None):
        self.result, values = server.response_data(value, content_type, headers)
        self.start_response(f'{status} {HTTPStatus(status).phrase}', list(values.items()))


def application(environ, start_response):
    request = Request(environ, start_response)
    method = environ.get('REQUEST_METHOD', 'GET')
    if method == 'GET':
        request.do_GET()
    elif method == 'POST':
        request.do_POST()
    else:
        request.send(405, {'error': 'Method not allowed.'}, headers={'Allow': 'GET, POST'})
    return [request.result]


def create_app():
    server.initialize()
    return application
