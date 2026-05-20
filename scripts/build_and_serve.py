"""Local static preview helper for Aegis-IR.

Production deployment is still zero-backend: publish the docs/ directory with
GitHub Pages. This helper only starts a standard static file server for local
review while developing.
"""

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import functools
import webbrowser


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
HOST = "127.0.0.1"
PORT = 8000


def main():
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(DOCS_DIR))
    server = ThreadingHTTPServer((HOST, PORT), handler)
    url = f"http://{HOST}:{PORT}/"

    print("Aegis-IR static preview")
    print(f"Serving: {DOCS_DIR}")
    print(f"URL:     {url}")
    print("Press Ctrl+C to stop.")

    webbrowser.open(url)
    server.serve_forever()


if __name__ == "__main__":
    main()
