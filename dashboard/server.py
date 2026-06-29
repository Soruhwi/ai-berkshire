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
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import uuid
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


# ---------------------------------------------------------------------------
# AI 리포트 생성 — claude CLI를 헤드리스(-p)로 호출해 실제 워크플로 가동
# ---------------------------------------------------------------------------

# 리포트 종류 → (skill 파일, 파일명 suffix, 타임아웃 초, 라벨, 비용상한 USD)
# 비용상한은 환경변수 AIB_REPORT_BUDGET_USD 로 일괄 덮어쓸 수 있음.
REPORT_KINDS = {
    "checklist": ("investment-checklist.md", "checklist", 900, "빠른 체크리스트", 6),
    "research": ("investment-research.md", "research", 1800, "종합 리서치", 20),
    "team": ("investment-team.md", "team", 2700, "멀티에이전트 팀", 30),
}


def _budget_for(kind: str) -> str:
    env = os.environ.get("AIB_REPORT_BUDGET_USD")
    if env:
        try:
            return str(float(env))
        except ValueError:
            pass
    return str(REPORT_KINDS[kind][4])

JOBS = {}            # id -> dict(status, kind, code, name, started, path, error)
JOBS_LOCK = threading.Lock()


def _find_claude():
    for cand in ("claude.cmd", "claude.exe", "claude"):
        p = shutil.which(cand)
        if p:
            return p
    return None


CLAUDE_BIN = _find_claude()


def _safe_name(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "", (name or "").strip()) or "회사"


def _build_prompt(kind: str, code: str, name: str) -> str:
    skill_file = REPORT_KINDS[kind][0]
    skill_path = os.path.join(REPO_ROOT, "skills", skill_file)
    with open(skill_path, "r", encoding="utf-8") as f:
        skill = f.read()
    target = f"{name}({code})" if code else name
    skill = skill.replace("$ARGUMENTS", target)
    return (
        f"너는 AI Berkshire 투자 리서치 애널리스트다. 분석 대상: {name}"
        f"{f'(한국 KOSPI/KOSDAQ, 종목코드 {code})' if code else ''}.\n"
        f"아래 워크플로 지침을 충실히 수행하라.\n\n"
        f"=== 워크플로 지침 시작 ===\n{skill}\n=== 워크플로 지침 끝 ===\n\n"
        f"[실행 규칙 — 매우 중요]\n"
        f"- **이것은 비대화형(헤드리스) 1회 실행이다. 사용자에게 어떤 확인도 묻지 마라.**"
        f" 지침에 '확인 후 시작', '진행할까요?', '团队框架确认' 같은 확인·승인 단계가 있어도"
        f" 전부 건너뛰고, 워크플로 전체를 처음부터 끝까지 자율적으로 완수하라."
        f" 절대로 질문으로 끝내지 말 것.\n"
        f"- 지침에 팀 생성(TeamCreate/TaskCreate)·서브에이전트·Task·백그라운드 작업이 있어도"
        f" **그런 도구를 절대 쓰지 마라.** 네가 직접 4대가(돤융핑·버핏·멍거·리루) 관점 분석을 모두 작성하고"
        f" 최종 종합까지 한 번에 완성하라. (WebSearch·Bash/krx_data 같은 데이터 조회 도구는 사용 가능)\n"
        f"- **리포트 전문을 단 하나의 최종 응답 메시지에 담아 출력하라.** 여러 메시지로 나누지 말고,"
        f" '위 리포트', '앞서 작성한' 같은 이전 메시지 참조 금지. 마지막 메시지만으로 완결된 리포트가 되어야 한다.\n"
        f"- 모든 출력은 한국어로 작성한다.\n"
        f"- 실제 수치가 필요하면 `python tools/krx_data.py quote|valuation|financials {code}`"
        f" 와 WebSearch로 데이터를 확보하고 출처를 표기한다.\n"
        f"- 객관성 원칙(사실/관점 구분, 양면 제시, 추정은 '추정' 명기)을 지킨다.\n"
        f"- 파일을 직접 생성하지 말고, 진행 설명·확인 질문·도구 로그 없이"
        f" **완성된 리서치 리포트의 마크다운 본문만** 최종 출력으로 반환하라. (저장은 외부에서 처리한다.)\n"
    )


def _run_report_job(job_id: str, kind: str, code: str, name: str):
    info = JOBS[job_id]
    try:
        prompt = _build_prompt(kind, code, name)
        timeout = REPORT_KINDS[kind][2]
        comspec = os.environ.get("COMSPEC", "cmd.exe")
        # claude.cmd 는 cmd /c 로 실행, 프롬프트는 stdin(마크다운 메타문자 안전)
        budget = _budget_for(kind)
        cmd = [comspec, "/c", CLAUDE_BIN, "-p",
               "--output-format", "text",
               "--permission-mode", "bypassPermissions",
               "--max-budget-usd", budget,
               "--no-session-persistence"]
        proc = subprocess.run(
            cmd, input=prompt, capture_output=True, text=True, encoding="utf-8",
            cwd=REPO_ROOT, timeout=timeout,
        )
        out = (proc.stdout or "").strip()
        if proc.returncode != 0 and not out:
            raise RuntimeError((proc.stderr or "claude 실행 실패").strip()[:500])
        if not out:
            raise RuntimeError("빈 결과(리포트 생성 실패)")
        # 예산 초과/오류 출력을 리포트로 저장하지 않음
        if "Exceeded USD budget" in out:
            raise RuntimeError(f"비용 상한(${budget}) 초과로 미완료. 서버를 "
                               f"`AIB_REPORT_BUDGET_USD=<더 큰 값>` 으로 재시작하거나 더 가벼운 종류로 시도하세요.")
        if len(out) < 300 and out.lower().startswith("error"):
            raise RuntimeError(out[:300])
        # 비정상적으로 짧으면 워크플로 미완결(부분 캡처) 가능성 → 저장하지 않음
        if len(out) < 1500:
            raise RuntimeError(f"출력이 너무 짧습니다({len(out)}자). 워크플로가 끝까지 완결되지 "
                               f"않았을 수 있습니다. 다시 시도하거나 더 가벼운 종류를 선택하세요.")

        suffix = REPORT_KINDS[kind][1]
        today = datetime.date.today().strftime("%Y%m%d")
        safe = _safe_name(name)
        out_dir = os.path.join(REPO_ROOT, "reports", safe)
        os.makedirs(out_dir, exist_ok=True)
        fname = f"{suffix}-{today}.md"
        fname = f"{safe}-{fname}"
        # 모델이 생성한 리포트 본문을 그대로 저장(스킬이 자체 제목 포함). 없으면 최소 헤더만.
        body = out if "#" in out.split("\n", 1)[0] or out.lstrip().startswith("#") \
            else f"# {name} {REPORT_KINDS[kind][3]} ({today})\n\n{out}"
        with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as f:
            f.write(body)
        rel = f"reports/{safe}/{fname}"
        with JOBS_LOCK:
            info.update(status="done", path=rel, chars=len(out))
    except subprocess.TimeoutExpired:
        with JOBS_LOCK:
            info.update(status="error", error=f"시간 초과({REPORT_KINDS[kind][2]}초). 더 짧은 종류로 시도하세요.")
    except Exception as e:
        with JOBS_LOCK:
            info.update(status="error", error=str(e)[:500])


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

        if path == "/api/report/status":
            jid = (qs.get("id") or [""])[0]
            with JOBS_LOCK:
                job = JOBS.get(jid)
            return self._send(200 if job else 404, job or {"error": "작업 없음"})

        if path == "/api/report/jobs":
            with JOBS_LOCK:
                jobs = sorted(JOBS.values(), key=lambda j: j["started"], reverse=True)
            return self._send(200, jobs[:20])

        if path == "/api/report/available":
            # claude CLI 사용 가능 여부 + 지원 종류
            return self._send(200, {
                "available": bool(CLAUDE_BIN),
                "bin": CLAUDE_BIN,
                "kinds": [{"id": k, "label": v[3], "budget": _budget_for(k),
                           "minutes": round(v[2] / 60)} for k, v in REPORT_KINDS.items()],
            })

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

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/report/generate":
            return self._send(404, {"error": "not found"})
        if not CLAUDE_BIN:
            return self._send(503, {"error": "claude CLI를 찾을 수 없습니다. Claude Code 설치 후 PATH 확인."})
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            return self._send(400, {"error": "잘못된 요청 본문"})

        kind = body.get("kind", "research")
        code = (body.get("code") or "").strip()
        name = (body.get("name") or "").strip()
        if kind not in REPORT_KINDS:
            return self._send(400, {"error": f"지원하지 않는 종류: {kind}"})
        if not name:
            return self._send(400, {"error": "회사명(name)이 필요합니다."})

        job_id = uuid.uuid4().hex[:12]
        job = {
            "id": job_id, "status": "running", "kind": kind,
            "kindLabel": REPORT_KINDS[kind][3], "code": code, "name": name,
            "started": datetime.datetime.now().isoformat(timespec="seconds"),
            "path": None, "error": None,
        }
        with JOBS_LOCK:
            JOBS[job_id] = job
        threading.Thread(target=_run_report_job, args=(job_id, kind, code, name), daemon=True).start()
        self._send(202, job)


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
