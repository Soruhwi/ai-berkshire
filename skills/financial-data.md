# 재무 데이터 취득과 교차검증 규범

본 규범은 기업 재무 데이터가 관련된 모든 연구에 적용된다. **모든 핵심 데이터는 독립된 두 출처에서 와야 하며, 오차 >1%는 표시해야 한다.**

---

## 데이터 출처 우선순위

### 미국주 (PDD, 텐센트 ADR, 네이스 ADR 등)

| 우선순위 | 출처 | URL | 취득 방식 |
|--------|------|-----|---------|
| 1(주) | **macrotrends** | macrotrends.net/stocks/charts/{ticker} | 직접 접속, 가입 불필요 |
| 2(부) | **stockanalysis** | stockanalysis.com/stocks/{ticker}/financials | 직접 접속, 가입 불필요 |
| 원천 일차 | SEC EDGAR | sec.gov/cgi-bin/browse-edgar | 10-K / 10-Q 원문 |

### 홍콩주 (텐센트 0700, 네이스 9999, 메이투안 3690 등)

| 우선순위 | 출처 | URL | 취득 방식 |
|--------|------|-----|---------|
| 1(주) | **aastocks** | aastocks.com/tc/stocks/analysis/company-fundamental | 직접 접속 |
| 2(부) | **macrotrends**(ADR 코드) | 텐센트는 TCEHY, 네이스는 NTES | 직접 접속 |
| 원천 일차 | HKEX 披露易 | hkexnews.hk | 연차보고서 PDF |

### 중국 A주 (三七互娱, 吉比特 등)

| 우선순위 | 출처 | URL | 취득 방식 |
|--------|------|-----|---------|
| 1(주) | **东方财富** | eastmoney.com → 종목 코드 검색 → 재무제표 | 직접 접속 |
| 2(부) | **巨潮资讯** | cninfo.com.cn | 원천 연차/분기보고서 PDF |

### 한국주 (KOSPI/KOSDAQ, 삼성전자·SK하이닉스 등)

| 우선순위 | 출처 | 취득 방식 |
|--------|------|---------|
| 1(주) | **tools/krx_data.py** (네이버금융 기반) | `quote` / `valuation` / `financials` / `search` 서브커맨드로 조회, 통화는 원(KRW) 기준 |
| 2(부) | **네이버금융 / KIND(전자공시)** | 원천 사업보고서/분기보고서 |

---

## 실행 규범

### 1단계: 데이터 취득

각 재무 지표(매출, 순이익, 매출총이익률, 영업현금흐름, 부채비율 등)에 대해, **출처 1**과 **출처 2**에서 각각 수치를 취한다.

### 2단계: 오차 계산과 표시

```
오차율 = |출처1 수치 - 출처2 수치| / 출처1 수치 × 100%
```

| 오차 | 처리 방식 |
|------|---------|
| ≤ 1% | ✅ 일치, 출처1 수치 채택, 두 출처 표기 |
| 1% ~ 5% | ⚠️ "데이터 차이 존재" 표시, 두 수치 명기, 가능한 원인 설명(환율/회계 기준) |
| > 5% | ❌ "데이터 중대 차이 존재" 표시, 반드시 원천 실적을 확인하여 검증, 그대로 사용 불가 |

### 3단계: 데이터 제시 형식

각 핵심 데이터는 반드시 다음 형식으로 표기한다:

```
매출: 1,239억 위안 ✅
  - macrotrends: 1,241억 위안
  - stockanalysis: 1,237억 위안
  - 오차: 0.3%
```

차이 예시:
```
순이익: 245억 위안 ⚠️ 데이터 차이 존재
  - macrotrends: 245억 위안(GAAP)
  - stockanalysis: 278억 위안(Non-GAAP)
  - 오차: 13.5% — 원인: 회계 기준 상이(GAAP vs Non-GAAP)
```

---

## 흔한 차이 원인 (반드시 데이터 오류인 것은 아님)

| 원인 | 설명 |
|------|------|
| GAAP vs Non-GAAP | 가장 흔함, 특히 이익류 데이터 |
| 환율 환산 | 홍콩달러/위안/달러 환산 시점이 다름 |
| 회계연도 정의 | 자연년 vs 회계연도(예: 애플 회계연도는 10월 종료) |
| 연결 기준 | 소수주주지분 포함 여부 |
| 데이터 갱신 지연 | 어느 플랫폼이 아직 최신 분기 실적을 갱신하지 않음 |

---

## 특별 규칙

1. **비상장 기업**(미호요, 릴리스 등): 일차 데이터 출처가 하나뿐일 때는, 데이터 앞에 `[추정]`을 표시하고 교차검증을 하지 않는다
2. **분기 데이터 vs 연간 데이터**: 교차검증은 연간 데이터를 우선 사용하며, 분기 데이터는 일부 출처에 지연이 있을 수 있다
3. **원천 실적 우선**: 두 출처가 모두 원천 실적(10-K/연차보고서 PDF)과 불일치하면, 원천 실적을 기준으로 하고 출처 오류로 표시한다

---

## 빠른 색인

| 상황 | 주요 출처 | 보조 출처 |
|------|---------|---------|
| PDD / 핀둬둬 | macrotrends.net/stocks/charts/PDD | stockanalysis.com/stocks/pdd |
| 텐센트 | macrotrends.net/stocks/charts/TCEHY | aastocks(0700.HK) |
| 네이스 | macrotrends.net/stocks/charts/NTES | aastocks(9999.HK) |
| 三七互娱 | eastmoney.com(002555) | cninfo.com.cn |
| 吉比特 | eastmoney.com(603444) | cninfo.com.cn |
| Nintendo | macrotrends.net/stocks/charts/NTDOY | stockanalysis.com/stocks/ntdoy |
| Capcom | macrotrends(CCOEY) | stockanalysis(CCOEY) |
| 한국주(예: 삼성전자 005930) | tools/krx_data.py quote/financials | 네이버금융 / KIND 전자공시 |
