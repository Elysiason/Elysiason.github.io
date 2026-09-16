"""Serve dist with consistent MIME types on Windows and Linux."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
                      '.svg': 'image/svg+xml', '.css': 'text/css',
                      '.js': 'application/javascript', '.json': 'application/json',
                      '.woff2': 'font/woff2', '.woff': 'font/woff'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / 'dist'
    if not (root / 'index.html').exists():
        parser.error('请先运行 python scripts/build.py')
    print(f'Preview: http://localhost:{args.port}', flush=True)
    with ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(root))) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
