# AI Berkshire 로컬 대시보드

리서치 리포트 브라우징 + 한국(KOSPI/KOSDAQ) 종목 실시간 데이터를 한 화면에서 보는 로컬 웹앱.
**외부 의존성 0** — Python 표준 라이브러리(`http.server`)와 벤더링된 `marked.min.js`만 사용한다.

## 실행

```bash
# 저장소 루트에서
python dashboard/server.py
# → http://localhost:8765 가 자동으로 열림
```

옵션:

```bash
python dashboard/server.py --port 9000      # 포트 변경
python dashboard/server.py --no-open        # 브라우저 자동 오픈 끄기
python dashboard/server.py --host 0.0.0.0   # 같은 네트워크의 다른 기기에서 접속 허용
```

종료: 터미널에서 `Ctrl+C`.

> Windows에서 한글이 깨지면 터미널에서 `chcp 65001` 후 실행하거나, 환경변수 `PYTHONUTF8=1`을 설정한다.

## 기능

- **📈 관심종목 실시간**: 기본 화면. 삼성전자·SK하이닉스·현대차·NAVER 등 카드로 시세·등락·시총 표시(상승=빨강/하락=파랑, 한국 관습). 카드 클릭 → 상세.
- **종목 상세**: 시세 + 밸류에이션(PER/PBR/EPS/BPS/배당/외국인소진율) + 최근 4개년 핵심 재무(매출·영업이익·ROE 등).
- **🔎 종목 검색**: 상단 검색창에 회사명/코드 입력 → 자동완성 → 클릭 시 상세. "+ 관심종목"으로 추가(브라우저 localStorage에 저장).
- **📄 리포트 브라우저**: 좌측 트리에서 `reports/`, `종목선별/`, `실전매매기록/` 의 모든 `.md` 리포트를 회사·카테고리별로 탐색하고 마크다운을 렌더링해 열람. 이름 필터 제공.
- **🤖 AI 리포트 생성**: 종목 상세에서 종류(빠른 체크리스트 / 종합 리서치 / 멀티에이전트 팀)를 골라 "생성 시작"을 누르면, **`claude` CLI를 헤드리스로 호출해 실제 4대가 워크플로를 가동**한다. 생성된 리포트는 `reports/{회사명}/{회사명}-{종류}-{날짜}.md` 로 저장되고, 완료 시 "리포트 열기"로 바로 열람할 수 있다. 진행 상황은 자동 폴링으로 표시된다.
  - 전제: 로컬에 [Claude Code](https://claude.com/claude-code)(`claude` CLI)가 설치·로그인되어 있어야 한다. 없으면 패널이 자동 비활성화된다.
  - 동작: 서버가 `skills/{스킬}.md` 지침에 회사명·종목코드를 주입해 `claude -p --permission-mode bypassPermissions` 로 실행(데이터는 `krx_data.py`·WebSearch로 수집). 종류별로 수 분~십수 분 소요, 비용 상한 `--max-budget-usd 4`.
  - 종류별 소요(대략): 체크리스트 ~5–9분, 종합 리서치 ~10–20분, 팀 ~20–40분.

## 구조

```
dashboard/
├── server.py             — stdlib HTTP 서버(정적 파일 + JSON API)
└── static/
    ├── index.html        — 대시보드 셸
    ├── app.js            — 프론트엔드 로직
    ├── style.css         — 스타일(다크 테마)
    └── vendor/
        └── marked.min.js — 마크다운 렌더러(벤더링, 오프라인)
```

## API (서버가 제공)

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /api/tree` | 콘텐츠 루트의 디렉토리/`.md` 트리(JSON) |
| `GET /api/file?path=<상대경로>` | 리포트 마크다운 원문. 콘텐츠 루트 밖·비`.md`는 404로 차단 |
| `GET /api/krx/search?q=` | 종목 검색 |
| `GET /api/krx/quote?code=` | 실시간 시세 |
| `GET /api/krx/valuation?code=` | 밸류에이션 지표 |
| `GET /api/krx/financials?code=` | 연간 핵심 재무 |

한국 종목 데이터는 `tools/krx_data.py`(네이버금융 기반)를 그대로 재사용한다. 실시간 시세를 위해 인터넷 연결이 필요하다.

## 보안 메모

- 파일 API는 `reports/`, `종목선별/`, `실전매매기록/` 안의 `.md`만 제공하며 경로 탈출(`..`)을 차단한다.
- 기본 바인딩은 `127.0.0.1`(로컬 전용). `--host 0.0.0.0`은 신뢰된 네트워크에서만 사용할 것.
