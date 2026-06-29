#!/usr/bin/env python3
"""AI Berkshire 로컬 대시보드 서버 — Python stdlib만 사용(외부 의존성 0).

리서치 리포트 브라우징 + 한국(KOSPI/KOSDAQ) 종목 실시간 데이터를 한 화면에서.

실행:
    python dashboard/server.py            # http://localhost:8765 자동 오픈
    python dashboard/server.py --port 9000 --no-open

설계:
- 정적 파일(dashboard/static/*)과 JSON API를 같은 서버에서 제공.
- 리포트 콘텐츠 루트: reports/, 종목선별/, 실전매매기록/ (저장소 루트 기준).
- 한국 종목 데이터는 tools/krx_data.py의 api_* 함수를 재사용.
"""

import argparse
import json
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(DASHBOARD_DIR)
STATIC_DIR = os.path.join(DASHBOARD_DIR, "static")

# 브라우징 허용 콘텐츠 루트(저장소 루트 기준 상대경로)
CONTENT_ROOTS = ["reports", "종목선별", "실전매매기록"]

# tools/krx_data.py 임포트
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))
try:
    import krx_data
except Exception as e:  # pragma: no cover
    krx_data = None
    _KRX_ERR = str(e)

_MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
}


def _abs_roots():
    return [os.path.realpath(os.path.join(REPO_ROOT, r)) for r in CONTENT_ROOTS]


def _safe_md_path(relpath: str):
    """relpath가 허용 콘텐츠 루트 안의 .md 파일인지 검증하고 절대경로 반환(아니면 None)."""
    target = os.path.realpath(os.path.join(REPO_ROOT, relpath))
    if not target.lower().endswith(".md") or not os.path.isfile(target):
        return None
    for root in _abs_roots():
        if target == root or target.startswith(root + os.sep):
            return target
    return None


def _build_tree(abs_dir: str):
    """디렉토리를 {name, path, type, children} 트리로. .md 파일과 하위 디렉토리만."""
    children = []
    try:
        entries = sorted(os.scandir(abs_dir), key=lambda e: (not e.is_dir(), e.name.lower()))
    except OSError:
        return children
    for e in entries:
        if e.name.startswith("."):
            continue
        rel = os.path.relpath(e.path, REPO_ROOT).replace(os.sep, "/")
        if e.is_dir():
            sub = _build_tree(e.path)
            if sub:  # .md를 품은 디렉토리만 노출
                children.append({"name": e.name, "path": rel, "type": "dir", "children": sub})
        elif e.name.lower().endswith(".md"):
            children.append({"name": e.name, "path": rel, "type": "file"})
    return children


def _content_tree():
    roots = []
    for r in CONTENT_ROOTS:
        abs_r = os.path.join(REPO_ROOT, r)
        if os.path.isdir(abs_r):
            roots.append({"name": r, "path": r, "type": "dir", "children": _build_tree(abs_r)})
    return roots


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # 조용히

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _krx(self, fn_name, **kw):
        if krx_data is None:
            return self._send(500, {"error": f"krx_data 임포트 실패: {_KRX_ERR}"})
        try:
            result = getattr(krx_data, fn_name)(**kw)
            self._send(200, result)
        except Exception as e:
            self._send(502, {"error": f"{fn_name} 실패: {e}"})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        # ---- API ----
        if path == "/api/tree":
            return self._send(200, _content_tree())

        if path == "/api/file":
            rel = (qs.get("path") or [""])[0]
            target = _safe_md_path(rel)
            if not target:
                return self._send(404, {"error": "파일을 찾을 수 없거나 허용되지 않은 경로"})
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                return self._send(200, {"path": rel, "markdown": f.read()})

        if path == "/api/krx/search":
            return self._krx("api_search", keyword=(qs.get("q") or [""])[0])
        if path == "/api/krx/quote":
            return self._krx("api_quote", code=(qs.get("code") or [""])[0])
        if path == "/api/krx/valuation":
            return self._krx("api_valuation", code=(qs.get("code") or [""])[0])
        if path == "/api/krx/financials":
            return self._krx("api_financials", code=(qs.get("code") or [""])[0])

        # ---- 정적 파일 ----
        if path == "/" or path == "":
            path = "/index.html"
        # /static/ 접두는 선택적으로 허용
        rel = path[len("/static/"):] if path.startswith("/static/") else path.lstrip("/")
        target = os.path.realpath(os.path.join(STATIC_DIR, rel))
        if (target == STATIC_DIR or target.startswith(STATIC_DIR + os.sep)) and os.path.isfile(target):
            ext = os.path.splitext(target)[1].lower()
            with open(target, "rb") as f:
                data = f.read()
            return self._send(200, data, _MIME.get(ext, "application/octet-stream"))

        self._send(404, {"error": "not found"})


def main():
    ap = argparse.ArgumentParser(description="AI Berkshire 로컬 대시보드")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-open", action="store_true", help="브라우저 자동 오픈 끄기")
    args = ap.parse_args()

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}/"
    print(f"AI Berkshire 대시보드 실행 중 → {url}")
    print(f"  콘텐츠 루트: {', '.join(CONTENT_ROOTS)}")
    print(f"  종료: Ctrl+C")
    if not args.no_open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n종료합니다.")
        httpd.shutdown()


if __name__ == "__main__":
    main()
