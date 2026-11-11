#!/usr/bin/env python3
"""Render a .drawio file so you can LOOK at it (the diagram stays on this machine).

Usage: python preview.py diagram.drawio [--port 8765] [--width 2000] [--png out.png] [--no-serve]

Default: writes a tiny HTML page that embeds the diagram and loads draw.io's viewer script
(viewer.diagrams.net, needs internet for the script and AWS shape library only), then serves
it on http://127.0.0.1:<port>/ until you stop it (Ctrl+C, or kill the process).
--png uses the draw.io desktop CLI if installed (needs no browser).
"""
import functools
import html
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    flag = lambda f, d=None: argv[argv.index(f) + 1] if f in argv else d  # noqa: E731
    if not args:
        print(__doc__)
        return 2
    path = args[0]
    if "--png" in argv:
        out = flag("--png")
        cli = shutil.which("drawio") or "/Applications/draw.io.app/Contents/MacOS/draw.io"
        if not os.path.exists(cli):
            print("draw.io desktop CLI not found; use the browser preview instead (omit --png).")
            return 1
        return subprocess.call([cli, "-x", "-f", "png", "-s", "2", "-o", out, path])
    xml = open(path, encoding="utf-8").read()
    cfg = json.dumps({"highlight": "#0000ff", "nav": False, "resize": False, "toolbar": "", "xml": xml})
    width = int(flag("--width", "2000"))
    port = int(flag("--port", "8765"))
    d = os.path.join(tempfile.gettempdir(), f"drawio-preview-{port}")  # one fixed folder per port, so a re-run just refreshes the page
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(
        '<!doctype html><meta charset="utf-8"><body style="margin:0;background:#fff">'
        f'<div class="mxgraph" style="width:{width}px" data-mxgraph="{html.escape(cfg, quote=True)}"></div>'
        '<script src="https://viewer.diagrams.net/js/viewer-static.min.js"></script></body>')
    if "--no-serve" in argv:
        print(os.path.join(d, "index.html"))
        return 0
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=d)
    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError:  # already running from an earlier call: the page was just rewritten, so reload it
        print(f"Preview already running; refreshed. Reload http://127.0.0.1:{port}/", flush=True)
        return 0
    print(f"Preview at http://127.0.0.1:{port}/  (stop it with: pkill -f 'preview.py')", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
