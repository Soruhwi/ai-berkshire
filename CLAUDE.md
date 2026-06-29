# AI Berkshire — 프로젝트 지침

## 프로젝트 개요

Claude Code 기반의 가치투자 리서치 Skill 모음. 4대가 프레임워크: 버핏, 멍거, 돤융핑(段永平), 리루(李录).
GitHub: xbtlin/ai-berkshire

## 프로젝트 구조

```
skills/          — 투자 리서치 Skill 정의(.md). ~/.claude/commands/ 로 복사해 사용
tools/           — 보조 도구(financial_rigor.py 정밀 계산, ashare_data.py A주, krx_data.py 한국)
reports/         — 투자 리서치 리포트 출력
assets/          — 이미지 등 정적 리소스
```

## 리포트 디렉토리 구조

모든 리포트는 **회사명**으로 폴더를 만들고, 해당 회사 관련 리포트는 모두 그 폴더 안에 둔다:

```
reports/
├── AI산업연구/              — AI 산업체인 전경 연구(상단 고정)
│   ├── AI5층케이크-산업전경연구-20260605.md
│   └── AI5층케이크-블로그-20260605.md
├── 텐센트/                  — 텐센트 모든 리서치 리포트
│   ├── 텐센트-research-20260408.md
│   ├── 텐센트-earnings-2025Q4.md
│   ├── 텐센트-management-20260409.md
│   └── 텐센트-thesis.md
├── 삼성전자/                — 삼성전자 모든 리서치 리포트(한국 종목 예시)
├── 핀둬둬/                  — 핀둬둬 모든 리서치 리포트
├── 원전-industry-20260409.md — 산업 리포트는 루트에
├── AI컴퓨팅-funnel-20260509.md — 깔때기 스크리닝 리포트는 루트에
├── AI-로테이션판단-20260509.md — 테마급 종합판단 리포트는 루트에
├── portfolio-latest.md       — 포트폴리오 리포트는 루트에
└── 다회사비교-checklist-20260408.md — 멀티 회사 리포트는 루트에
```

## 리포트 명명 규칙

| Skill | 파일명 형식 | 예시 |
|------|---------|------|
| /investment-team | `{회사명}/` 디렉토리 안에 4개 시점 + 최종 리포트 | `reports/핀둬둬/최종리포트.md` |
| /investment-research | `{회사명}-research-{YYYYMMDD}.md` | `reports/텐센트/텐센트-research-20260408.md` |
| /investment-checklist | `{회사명}-checklist-{YYYYMMDD}.md` | `reports/텐센트/텐센트-checklist-20260408.md` |
| /industry-research | `{산업명}-industry-{YYYYMMDD}.md`(루트) | `reports/원전-industry-20260409.md` |
| /industry-funnel | `{산업명}-funnel-{YYYYMMDD}.md`(루트) | `reports/AI컴퓨팅-funnel-20260509.md` |
| /private-company-research | `{회사명}-private-{YYYYMMDD}.md` | `reports/바이트댄스/바이트댄스-private-20260408.md` |
| /earnings-review | `{회사명}-earnings-{기간}.md` | `reports/텐센트/텐센트-earnings-2025Q4.md` |
| /earnings-team | `{회사명}/` 디렉토리 안에 4대가 시점 + 리서치 원고 + 블로그 글 + 독자 리뷰 | `reports/텐센트/텐센트-earnings-2025Q4.md`(블로그 확정본) |
| /thesis-tracker | `{회사명}-thesis.md`(장기 유지) | `reports/텐센트/텐센트-thesis.md` |
| /portfolio-review | `portfolio-latest.md`(루트, 지속 갱신) | `reports/portfolio-latest.md` |
| /management-deep-dive | `{회사명}-management-{YYYYMMDD}.md` | `reports/텐센트/텐센트-management-20260409.md` |

## /investment-team 파일 구조

```
reports/{회사명}/
├── README.md                         — 리서치 프레임워크 개요 + 핵심 결론
├── 01-비즈니스모델분석-돤융핑시점.md
├── 02-재무밸류에이션분석-버핏시점.md
├── 03-산업경쟁분석-멍거시점.md
├── 04-리스크경영진평가-리루시점.md
└── 최종리포트.md                       — Team Lead 종합 리포트
```

## 투자 리서치 분석 핵심 원칙(최우선)

- **객관, 객관, 객관** — 모든 투자 분석은 사실과 데이터에 기반해야 하며, 주관적 억측을 엄격히 금지
- "사실"과 "관점"을 엄격히 구분: 사실은 데이터로 뒷받침하고, 관점은 반드시 "관점" 또는 "추측"으로 명확히 표기
- **입장을 미리 정하지 않기**: 강세/약세를 전제하지 말고, 먼저 데이터를 제시하고 → 논리를 전개하고 → 마지막에 결론. 결론은 데이터에서 자연스럽게 도출되어야 함
- "내 생각엔", "내가 보기엔", "분명히" 같은 주관적 표현 금지. "데이터에 따르면", "증거가 보여주듯", "○○ 출처에 근거하면"으로 대체
- **양면을 함께 제시**: 모든 핵심 판단에는 반대 논거("하지만 다른 한편…")를 첨부해 독자가 스스로 저울질하게 함
- 불확실한 것은 솔직히 "불확실" 또는 "데이터 부족"이라 말하고, 추측으로 확실성을 채우지 않기
- 모든 skill(investment-team, investment-research, earnings-review 등)은 실행 시 위 원칙을 반드시 준수

## 리포트 언어와 스타일

- 모든 리포트는 **한국어** 사용
- 스타일: 직설적, 날카롭게, 군더더기 없이
- 데이터는 반드시 출처를 표기하고, 핵심 데이터는 최소 2개 출처로 교차검증
- 추정치는 반드시 "추정"이라고 명기
- 평점은 ★ 기호 사용(★1~5), 반쪽 별 없음
- 버핏/멍거/돤융핑/리루의 어록을 중간중간 삽입

## 한국 시장 지원

- 한국(KOSPI/KOSDAQ) 종목 시세·재무·밸류에이션은 `tools/krx_data.py`로 조회(네이버금융 기반, 외부 의존성 0)

  ```bash
  python3 tools/krx_data.py quote 005930          # 실시간 시세(삼성전자)
  python3 tools/krx_data.py valuation 005930      # PER/PBR/시총/배당
  python3 tools/krx_data.py financials 005930     # 최근 연도 핵심 재무
  python3 tools/krx_data.py search 삼성전자        # 종목 코드 검색
  ```

- 시장별 데이터 도구 선택: 한국=`krx_data.py`, 중국 A주=`ashare_data.py`, 글로벌=`morningstar_fair_value.py` + WebSearch
- 한국 종목 코드는 6자리 숫자(예: 005930=삼성전자, 000660=SK하이닉스, 035420=NAVER)

## 주의사항

- 시가총액은 반드시 수동 검산: 주가 × 총발행주식수, 리포트 시총과 대조
- 통화 단위를 명확히(한국 원화 KRW/홍콩달러 HKD/위안 CNY/달러 USD), 혼동 방지
  - 특히 한국 종목은 **원(KRW)** 기준. 시총은 조/억원 단위로 명기(혼동 시 주가×주식수로 재검산)
- PE/ROE 등 지표는 tools/financial_rigor.py로 정밀 계산
- 리포트 작성 후 GitHub 푸시 여부를 능동적으로 질문

## GitHub 작업

- 로컬 클론 경로: `~/ai-berkshire/`
- 원격 저장소: `https://github.com/xbtlin/ai-berkshire.git`
- 푸시 전 `git pull --rebase origin main`(원격에 새 커밋이 자주 있음)
- commit message는 한국어로, 무엇을 바꿨는지 명확히 기술
- 중간 과정 파일(예: data_collection.md)은 푸시하지 말고 최종 리포트만 푸시

## 자주 쓰는 명령

```bash
# 리포트를 GitHub에 푸시
cd ~/ai-berkshire
git add reports/xxx.md
git commit -m "xxx 리포트 추가"
git pull --rebase origin main
git push origin main
```
