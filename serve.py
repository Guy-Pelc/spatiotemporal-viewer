#!/usr/bin/env python3
"""Cross-platform launcher for the Coronal Aging spatial viewer.

Works the same on macOS, Linux, and Windows (only Python 3 is required).

    python serve.py                # serve on :8777 and open the browser
    python serve.py 9000           # pick a port
    python serve.py --no-open      # don't auto-open a browser
    python serve.py --port 9000 --no-open

If the data bundle (data/manifest.json) is missing it is regenerated first by
running export_data.py, which needs `anndata` and the source .h5ad.
"""
import argparse
import os
import socket
import subprocess
import sys
import threading
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))


def lan_ip():
    """Best-effort LAN IP of this machine (no packets are actually sent)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def ensure_data():
    if os.path.exists(os.path.join(HERE, "data", "manifest.json")):
        return
    print("Data bundle missing - running export_data.py ...")
    # sys.executable => the same interpreter, so this works whether the platform
    # calls it `python`, `python3`, py -3, etc.
    subprocess.run([sys.executable, os.path.join(HERE, "export_data.py")],
                   cwd=HERE, check=True)


def main():
    ap = argparse.ArgumentParser(description="Serve the spatial viewer.")
    ap.add_argument("port", nargs="?", type=int, default=8777,
                    help="port to serve on (default 8777)")
    ap.add_argument("--port", dest="port_opt", type=int, default=None,
                    help="alternative way to set the port")
    ap.add_argument("--no-open", action="store_true",
                    help="do not open a browser automatically")
    ap.add_argument("--lan", action="store_true",
                    help="serve on your local network so phones/other devices "
                         "on the same WiFi can connect")
    ap.add_argument("--host", default=None,
                    help="interface to bind (default 127.0.0.1; --lan uses 0.0.0.0)")
    args = ap.parse_args()
    port = args.port_opt if args.port_opt is not None else args.port
    host = args.host or ("0.0.0.0" if args.lan else "127.0.0.1")

    ensure_data()

    # Serve files relative to this script's directory, regardless of cwd.
    handler = partial(SimpleHTTPRequestHandler, directory=HERE)
    try:
        httpd = ThreadingHTTPServer((host, port), handler)
    except OSError as e:
        sys.exit(f"Could not bind to {host}:{port}: {e}\n"
                 f"Try another port, e.g. python serve.py {port + 1}")

    url = f"http://localhost:{port}/index.html"
    print(f"Viewer at -> {url}   (Ctrl-C to stop)")
    if host in ("0.0.0.0", "::"):
        print(f"On your network (phone, same WiFi) -> "
              f"http://{lan_ip()}:{port}/index.html")
    if not args.no_open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
        httpd.shutdown()


if __name__ == "__main__":
    main()
