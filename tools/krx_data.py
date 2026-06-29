#!/usr/bin/env python3
"""한국 주식 데이터 도구 — 네이버금융 기반, 외부 의존성 0 (stdlib만 사용).

AI Berkshire Skills에 한국(KOSPI/KOSDAQ) 실시간 시세·재무·밸류에이션 데이터를 제공한다.
설계 원칙: 독립 모듈, 기존 도구(ashare_data.py 등)에 영향 없음. urllib 사용으로
Windows/macOS/Linux 모두에서 동작(외부 curl 바이너리 불필요).

사용법(Skill이 자동 호출):
    python3 tools/krx_data.py quote 005930          # 실시간 시세 (삼성전자)
    python3 tools/krx_data.py valuation 005930      # 밸류에이션 지표 (PER/PBR/시총)
    python3 tools/krx_data.py financials 005930     # 핵심 재무 데이터 (최근 연도)
    python3 tools/krx_data.py search 삼성전자        # 종목 코드 검색

종목 코드는 6자리 숫자(예: 005930=삼성전자, 000660=SK하이닉스, 035420=NAVER).
Python >= 3.8 필요, 외부 의존성 0.
"""

import argparse
import json
import sys
from decimal import Decimal
from urllib.parse import quote as _urlquote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Windows 콘솔(cp949 등)에서도 한글이 깨지지 않도록 UTF-8 출력 고정
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

_TIMEOUT = 15
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def _get(url: str) -> str:
    """urllib로 직접 요청(시스템 curl 불필요). UTF-8 디코딩."""
    req = Request(url, headers={
        "User-Agent": _UA,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://m.stock.naver.com/",
    })
    try:
        with urlopen(req, timeout=_TIMEOUT) as resp:
            raw = resp.read()
    except (URLError, HTTPError) as e:
        raise ConnectionError(f"요청 실패: {url} ({e})")
    if not raw:
        raise ConnectionError(f"빈 응답: {url}")
    return raw.decode("utf-8", errors="replace")


def _get_json(url: str):
    return json.loads(_get(url))


def _clean_code(code: str) -> str:
    """'005930.KS', '005930.KQ', 'KRX:005930' 등을 6자리 코드로 정규화."""
    code = code.strip().upper()
    for sep in (":", "."):
        if sep in code:
            parts = code.split(sep)
            # 'KRX:005930' -> '005930' / '005930.KS' -> '005930'
            code = parts[-1] if parts[0] in ("KRX", "KOSPI", "KOSDAQ") else parts[0]
    return code.zfill(6) if code.isdigit() else code


def _won(raw) -> str:
    """원 단위 정수를 조/억 단위 한국어 표기로."""
    if raw is None or raw == "" or raw == "-":
        return "-"
    try:
        v = Decimal(str(raw).replace(",", ""))
    except Exception:
        return str(raw)
    jo = Decimal("1000000000000")   # 조
    eok = Decimal("100000000")      # 억
    if abs(v) >= jo:
        jo_part = int(v / jo)
        eok_part = int((v % jo) / eok)
        return f"{jo_part}조 {eok_part:,}억원" if eok_part else f"{jo_part}조원"
    if abs(v) >= eok:
        return f"{(v / eok):.2f}억원"
    return f"{v:,.0f}원"


# ---------------------------------------------------------------------------
# 1) 실시간 시세 — polling.finance.naver.com
# ---------------------------------------------------------------------------

def _fetch_quote(code: str) -> dict:
    url = f"https://polling.finance.naver.com/api/realtime/domestic/stock/{code}"
    data = _get_json(url)
    rows = data.get("datas", [])
    return rows[0] if rows else {}


def cmd_quote(code: str):
    code = _clean_code(code)
    d = _fetch_quote(code)
    if not d:
        print(f"❌ 종목을 찾을 수 없음: {code}")
        return

    ex = d.get("stockExchangeType", {})
    cur = d.get("currencyType", {}).get("code", "KRW")
    print("=" * 60)
    print(f"실시간 시세: {d.get('stockName')} ({code}) · {ex.get('nameKor', '')}")
    print("=" * 60)
    print(f"  현재가:      {d.get('closePrice')} {cur}")
    print(f"  전일대비:    {d.get('compareToPreviousClosePrice')} ({d.get('fluctuationsRatio')}%)")
    print(f"  시가:        {d.get('openPrice')}")
    print(f"  고가:        {d.get('highPrice')}")
    print(f"  저가:        {d.get('lowPrice')}")
    print(f"  거래량:      {d.get('accumulatedTradingVolume')} 주")
    print(f"  거래대금:    {d.get('accumulatedTradingValue')}")
    print(f"  시가총액:    {_won(d.get('marketValueFullRaw'))}")
    print(f"  ISIN:        {d.get('isinCode')}")
    print(f"  체결시각:    {d.get('localTradedAt')}")


# ---------------------------------------------------------------------------
# 2) 밸류에이션 — m.stock.naver.com/api/stock/{code}/integration (totalInfos)
# ---------------------------------------------------------------------------

def _fetch_integration(code: str) -> dict:
    return _get_json(f"https://m.stock.naver.com/api/stock/{code}/integration")


def cmd_valuation(code: str):
    code = _clean_code(code)
    d = _fetch_integration(code)
    infos = {i.get("code"): i.get("value") for i in d.get("totalInfos", [])}
    name = d.get("stockName", code)

    print("=" * 60)
    print(f"밸류에이션 지표: {name} ({code})")
    print("=" * 60)
    label = [
        ("marketValue", "시가총액"),
        ("per", "PER(실적)"),
        ("cnsPer", "PER(추정)"),
        ("eps", "EPS"),
        ("cnsEps", "EPS(추정)"),
        ("pbr", "PBR"),
        ("bps", "BPS"),
        ("dividendYieldRatio", "배당수익률"),
        ("dividend", "주당배당금"),
        ("foreignRate", "외국인소진율"),
        ("highPriceOf52Weeks", "52주 최고"),
        ("lowPriceOf52Weeks", "52주 최저"),
    ]
    for key, kor in label:
        if key in infos:
            print(f"  {kor:<12} {infos[key]}")

    # 시가총액 교차검증: 현재가 × 추정 주식수가 없으므로, PER×EPS≈주가로 정합성 점검
    try:
        per = Decimal(str(infos.get("per", "0")).replace("배", "").replace(",", ""))
        eps = Decimal(str(infos.get("eps", "0")).replace("원", "").replace(",", ""))
        implied = per * eps
        q = _fetch_quote(code)
        price = Decimal(str(q.get("closePriceRaw", "0")).replace(",", ""))
        if price > 0 and implied > 0:
            diff = abs(implied - price) / price * 100
            flag = "✅" if diff < 5 else "⚠️"
            print(f"\n  정합성 점검: PER×EPS={implied:,.0f} vs 현재가={price:,.0f} ({flag} 편차 {diff:.1f}%)")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 3) 핵심 재무 — m.stock.naver.com/api/stock/{code}/finance/annual
# ---------------------------------------------------------------------------

def cmd_financials(code: str):
    code = _clean_code(code)
    try:
        d = _get_json(f"https://m.stock.naver.com/api/stock/{code}/finance/annual")
    except ConnectionError:
        print(f"❌ 재무 데이터를 가져오지 못함: {code}")
        return

    fin = d.get("financeInfo", {})
    rows = fin.get("rowList", [])
    periods = [t.get("title", "") for t in fin.get("trTitleList", [])]
    # 컬럼 키(예: 202312)와 표시용 기간(예: 2023.12.)을 정렬해 매핑
    col_keys = sorted({k for r in rows for k in (r.get("columns") or {})})
    name = d.get("corporationSummary", {}).get("corpName")
    if not name:
        try:
            name = _fetch_quote(code).get("stockName") or code
        except Exception:
            name = code

    print("=" * 60)
    print(f"핵심 재무 데이터(연간): {name} ({code})")
    print(f"단위: 억원 / % (출처: 네이버금융)")
    print("=" * 60)

    if not rows:
        print("  ⚠️ 재무 데이터 없음 — WebSearch로 보완 권장")
        return

    want = ["매출액", "영업이익", "당기순이익", "영업이익률", "순이익률",
            "ROE", "부채비율", "EPS", "PER", "BPS", "PBR", "주당배당금"]
    by_title = {r.get("title"): (r.get("columns") or {}) for r in rows}

    header = "  " + f"{'항목':<10}" + "".join(f"{k:>14}" for k in col_keys)
    print(header)
    print("  " + "-" * (10 + 14 * len(col_keys)))
    for title in want:
        cols = by_title.get(title)
        if not cols:
            continue
        line = f"  {title:<10}"
        for k in col_keys:
            v = (cols.get(k) or {}).get("value", "-")
            line += f"{v:>14}"
        print(line)


# ---------------------------------------------------------------------------
# 4) 종목 검색 — m.stock.naver.com/front-api/search/autoComplete
# ---------------------------------------------------------------------------

def cmd_search(keyword: str):
    q = _urlquote(keyword)
    url = f"https://m.stock.naver.com/front-api/search/autoComplete?query={q}&target=stock"
    data = _get_json(url)
    items = data.get("result", {}).get("items", [])

    print("=" * 60)
    print(f"검색 결과: '{keyword}'")
    print("=" * 60)
    if not items:
        print(f"  ❌ '{keyword}'에 해당하는 종목 없음")
        return
    for it in items[:10]:
        nation = it.get("nationName", "")
        print(f"  {it.get('code'):<8} {it.get('name')}  [{it.get('typeName')}·{nation}]")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="한국 주식 데이터 도구 — 네이버금융 기반(시세/밸류에이션/재무/검색)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    p_q = sub.add_parser("quote", help="실시간 시세")
    p_q.add_argument("code", help="종목코드 6자리, 예: 005930")
    p_f = sub.add_parser("financials", help="핵심 재무 데이터(연간)")
    p_f.add_argument("code", help="종목코드")
    p_v = sub.add_parser("valuation", help="밸류에이션 지표")
    p_v.add_argument("code", help="종목코드")
    p_s = sub.add_parser("search", help="종목 코드 검색")
    p_s.add_argument("keyword", help="회사명 또는 키워드")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    {
        "quote": lambda: cmd_quote(args.code),
        "financials": lambda: cmd_financials(args.code),
        "valuation": lambda: cmd_valuation(args.code),
        "search": lambda: cmd_search(args.keyword),
    }[args.command]()


if __name__ == "__main__":
    main()
