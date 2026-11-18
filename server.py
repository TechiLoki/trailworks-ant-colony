"""Local-only HTTP UI. Python standard library; no third-party dependencies."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
from simulation import Colony

STATIC = Path(__file__).parent / 'static'


class Handler(BaseHTTPRequestHandler):
    colony = Colony()

    def respond(self, status, body, content_type='application/json'):
        data = body.encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/api/state':
            self.respond(200, json.dumps(self.colony.snapshot()))
        elif path in ('/', '/app.js', '/style.css'):
            filename = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}[path]
            mime = {'/': 'text/html', '/app.js': 'text/javascript', '/style.css': 'text/css'}[path]
            self.respond(200, (STATIC / filename).read_text(), mime + '; charset=utf-8')
        else:
            self.respond(404, json.dumps({'error': 'not found'}))

    def do_POST(self):
        try:
            # Reject cross-origin browser requests to this local control API.
            origin = self.headers.get('Origin')
            if origin and origin != 'http://' + self.headers.get('Host', ''):
                self.respond(403, json.dumps({'error': 'origin rejected'}))
                return
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 <= length <= 4096:
                raise ValueError('invalid request length')
            data = json.loads(self.rfile.read(length) or b'{}')
            if not isinstance(data, dict):
                raise ValueError('expected an object')
            if self.path == '/api/reset':
                seed = data.get('seed', 7)
                population = data.get('population', 150)
                evaporation = data.get('evaporation', 0.025)
                if type(seed) is not int or type(population) is not int or type(evaporation) not in (int, float):
                    raise ValueError('invalid configuration types')
                type(self).colony = Colony(seed, population, evaporation)
            elif self.path == '/api/step':
                steps = data.get('steps', 1)
                if type(steps) is not int or not 1 <= steps <= 20:
                    raise ValueError('steps must be an integer between 1 and 20')
                self.colony.step(steps)
            elif self.path == '/api/food':
                x, y = data.get('x'), data.get('y')
                if type(x) is not int or type(y) is not int:
                    raise ValueError('coordinates must be integers')
                self.colony.add_food(x, y)
            else:
                self.respond(404, json.dumps({'error': 'not found'}))
                return
            self.respond(200, json.dumps(self.colony.snapshot()))
        except (ValueError, TypeError) as error:
            self.respond(400, json.dumps({'error': str(error)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    print(f'Ant colony: http://127.0.0.1:{args.port}', flush=True)
    try:
        HTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
    except KeyboardInterrupt:
        pass
