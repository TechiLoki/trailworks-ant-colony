"""Exercise real HTTP request parsing without binding a network socket."""
import io
import json
import unittest
from server import Handler
from simulation import Colony


class Socket:
    def __init__(self, request):
        self.input = io.BytesIO(request)
        self.output = bytearray()
    def makefile(self, *args, **kwargs): return self.input
    def sendall(self, data): self.output.extend(data)


class QuietHandler(Handler):
    def log_message(self, *args): pass


class APITests(unittest.TestCase):
    def setUp(self): QuietHandler.colony = Colony(population=10)

    def request(self, path, data=None, origin=None):
        body = json.dumps(data).encode() if data is not None else b''
        method = 'POST' if data is not None else 'GET'
        headers = f'{method} {path} HTTP/1.0\r\nHost: localhost\r\nContent-Length: {len(body)}\r\n'
        if origin: headers += f'Origin: {origin}\r\n'
        sock = Socket(headers.encode() + b'\r\n' + body)
        QuietHandler(sock, ('127.0.0.1', 1234), None)
        head, payload = bytes(sock.output).split(b'\r\n\r\n', 1)
        return int(head.split()[1]), payload

    def test_state_step_reset_and_food(self):
        code, payload = self.request('/api/state')
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(payload)['tick'], 0)
        code, payload = self.request('/api/step', {'steps': 3})
        self.assertEqual(json.loads(payload)['tick'], 3)
        code, payload = self.request('/api/food', {'x': 30, 'y': 30})
        self.assertEqual(json.loads(payload)['initial_food'], 1000)
        code, payload = self.request('/api/reset', {'population': 5})
        self.assertEqual(len(json.loads(payload)['ants']), 5)
        self.assertEqual(json.loads(payload)['tick'], 0)

    def test_reject_invalid_requests(self):
        for path, data in [('/api/step', {'steps': 21}), ('/api/reset', {'population': 0}), ('/api/reset', {'evaporation': 'bad'}), ('/api/food', {'x': -1, 'y': 0})]:
            self.assertEqual(self.request(path, data)[0], 400)
        self.assertEqual(self.request('/api/step', {}, 'https://example.com')[0], 403)
        self.assertEqual(self.request('/missing')[0], 404)

    def test_static_files(self):
        for path in ['/', '/app.js', '/style.css']:
            code, payload = self.request(path)
            self.assertEqual(code, 200)
            self.assertTrue(payload)
