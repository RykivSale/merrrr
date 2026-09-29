"""Принимает ответы гостей и дописывает их в rsvp.json.

Запуск: python3 tools/rsvp_server.py [порт] [файл]
На VPS его запускает systemd (см. tools/deploy.sh), nginx проксирует на него /api/.
Локально ещё отдаёт сайт из site/ — можно открыть http://127.0.0.1:8787.
"""
import json, os, sys, tempfile, threading
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
DATA = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rsvp.json")
SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site")
lock = threading.Lock()


def save(name, ip):
    with lock:
        try:
            with open(DATA, encoding="utf-8") as f:
                rows = json.load(f)
        except FileNotFoundError:
            rows = []
        rows.append({"name": name, "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "ip": ip})
        # Пишем во временный файл и переименовываем, чтобы json не побился
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(DATA)))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=SITE, **kw)

    def reply(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/rsvp":
            return self.reply(404, {"ok": False})
        try:
            size = int(self.headers.get("Content-Length", 0))
            if size > 2000:
                raise ValueError
            name = " ".join(str(json.loads(self.rfile.read(size))["name"]).split())
            if not 1 <= len(name) <= 100:
                raise ValueError
        except Exception:
            return self.reply(400, {"ok": False})
        ip = self.headers.get("X-Real-IP") or self.client_address[0]
        save(name, ip)
        self.reply(200, {"ok": True})


if __name__ == "__main__":
    ThreadingHTTPServer((os.environ.get("HOST", "127.0.0.1"), PORT), Handler).serve_forever()
