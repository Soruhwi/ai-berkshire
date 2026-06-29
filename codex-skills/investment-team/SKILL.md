---
name: investment-team
description: "AI Berkshire skill: 투자 리서치 팀: 4-역할 병렬 분석 프레임워크. Source: skills/investment-team.md."
---

## Codex adapter note

This skill is generated from `skills/investment-team.md` so Claude Code and Codex users share one canonical workflow.

- Treat `$ARGUMENTS` as the user's request in the current Codex thread.
- When the source mentions Claude-only surfaces such as Task, Agent, WebSearch, Bash, Read, or Write, use the closest Codex capability available in this session: subagents when available, web search when needed, shell commands for local tools, and normal file edits for workspace files.
- Use shared project tools from `tools/` in this repository. Commands that reference `~/ai-berkshire/tools/...` assume the repo is checked out at `~/ai-berkshire`; if needed, prefer the current workspace path.
- Preserve the research quality rules from `AGENTS.md`: cross-check financial data, use exact arithmetic tools for valuation/math, and clearly label uncertainty and source gaps.

# 투자 리서치 팀: 4-역할 병렬 분석 프레임워크

$ARGUMENTS 에 대해 팀 기반 투자 리서치 분석을 수행한다. Team 도구를 사용해 진짜 멀티-Agent 병렬 리서치 팀을 만든다.

## 실행 흐름

### 첫 번째: 팀 프레임워크 제시

사용자에게 다음 팀 구조를 제시하고, 확인을 받은 뒤 시작한다:

| 역할 | 책임 | 분석 프레임워크 |
|------|------|----------|
| **team-lead**(당신 자신) | 총괄 조율, 종합 판단, 최종 보고서 산출 | 4대 대가 종합 프레임워크 |
| **business-analyst** | 비즈니스 모델 & 해자 분석 | 돤융핑 관점 |
| **financial-analyst** | 재무제표 & 밸류에이션 분석 | 버핏 관점 |
| **industry-researcher** | 산업 구도 & 경쟁 태세 | 멍거 관점 |
| **risk-assessor** | 리스크 평가 & 경영진 판단 | 리루 관점 |

### 1.5단계: AI 리서치 편향 평가

팀을 만들기 전에, 사용자에게 해당 회사의 "AI 리서치 가능성" 평가를 먼저 제시한다:

**정보 풍부도 등급**(리서치 전략을 결정):
| 등급 | 특징 | 리서치 전략 조정 |
|------|------|------------|
| A급(정보 풍부) | 상장 다년, 증권사 커버리지 광범위 | 팀은 **반증 검증**과 **비(非)컨센서스 관점**에 집중, 시장과 일치하는 "맞는 헛소리" 산출 회피 |
| B급(정보 보통) | 상장한 지 얼마 안 됨, 커버리지 제한적 | 각 Agent의 추산 데이터는 반드시 신뢰도를 표기, team-lead 종합 시 "데이터 충분도" 표기 |
| C급(정보 희소) | 비인기/신규 상장/신흥 시장 | 팀은 "제1원리 모드"로 전환: 보고서의 완결성을 추구하지 않고, 비즈니스 본질의 핵심 질문 몇 가지에 집중 |

**핵심 유의사항**: 자료가 많다 ≠ 확실성이 높다, 자료가 적다 ≠ 확실성이 낮다. AI가 산출할 수 있는 신뢰도 ≠ 투자의 실제 확실성. 확실성은 비즈니스 모델 그 자체에서 오지, 자료의 양에서 오지 않는다.

등급 평가 결과를 각 Agent에게 알려 리서치 방식에 반영한다.

### 두 번째: 팀 생성

TeamCreate로 팀을 생성한다:
- team_name: `{회사명}-research`(영문 소문자, 예: `meituan-research`)
- agent_type: `team-lead`

### 세 번째: 4개 태스크 생성

TaskCreate로 다음 4개 태스크를 생성한다(각각 subject, description, activeForm 필요):

#### 태스크1: 비즈니스 모델 분석
- subject: `{회사명}의 비즈니스 모델, 해자, 사용자 가치 분석`
- description 포함 사항:
  1. 비즈니스 모델 본질: 핵심 사업 정의, 매출 구조 분해
  2. 플랫폼/제품 플라이휠 효과가 어떻게 작동하는가
  3. 해자 분석: 브랜드/전환비용/네트워크 효과/규모의 경제/기술 장벽을 하나씩 검증
  4. 사용자/고객 가치: 각 주체에게 어떤 독특한 가치를 창출했는가
  5. 사업 매트릭스와 시너지 효과
  6. 돤융핑의 "좋은 사업" 기준 평가: 차별화, 가격결정력, 지속가능한 경쟁우위
  7. 최신 실적, 산업 보고서 등 공개 정보 검색 요구

#### 태스크2: 재무 및 밸류에이션 분석
- subject: `{회사명}의 재무 데이터, 수익성, 밸류에이션 분석`
- description 포함 사항:
  1. 최근 3-5년 매출, 순이익, 영업이익 추세
  2. 수익성 지표: ROE, ROA, 매출총이익률, 영업이익률
  3. 현금흐름 분석: 영업현금흐름, 잉여현금흐름(FCF), 자본적지출(CAPEX)
  4. 재무상태표 건전성: 현금 보유고, 부채비율, 유동성
  5. 밸류에이션 분석: PE/PS/PB/EV 등, 과거 및 동종업계와 비교
  6. 안전마진 평가: 내재가치 vs 현재 주가
  7. **금융 엄밀성 검증(반드시 Bash로 도구를 호출, 암산 금지)**:
     - 시가총액 검산: `python3 ~/ai-berkshire/tools/financial_rigor.py verify-market-cap --price {가격} --shares {주식 수} --reported {보고 시총} --currency {통화}`
     - 밸류에이션 검산: `python3 ~/ai-berkshire/tools/financial_rigor.py verify-valuation --price {가격} --eps {EPS} --bvps {주당순자산}`
     - 핵심 데이터 교차 검증: `python3 ~/ai-berkshire/tools/financial_rigor.py cross-validate --field {필드} --values '{JSON}' --unit {단위}`
     - 3-시나리오 밸류에이션: `python3 ~/ai-berkshire/tools/financial_rigor.py three-scenario --price {가격} --eps {EPS} --shares {주식 수 억} --growth {낙관} {중립} {비관} --pe {낙관PE} {중립PE} {비관PE}`
     - 도구 출력 결과를 보고서에 검증 기록으로 직접 삽입

#### 태스크3: 산업 및 경쟁 분석
- subject: `{산업} 산업 구도와 {회사명}의 경쟁 태세 분석`
- description 포함 사항:
  1. 산업 규모와 성장: 시장 규모, 성장률, 침투율
  2. 경쟁 구도: 주요 경쟁자 시장 점유율, 경쟁 전략 비교
  3. 핵심 경쟁자 위협 평가: 주요 경쟁자를 하나씩 분석
  4. 각 세부 트랙(segment) 구도
  5. 산업 추세: 기술 변혁, 정책 영향, 신규 진입자
  6. 밸류체인 분석: 상·중·하류 가치 배분
  7. 최신 산업 데이터와 경쟁 동향 검색 요구

#### 태스크4: 리스크 및 경영진 평가
- subject: `{회사명}의 투자 리스크와 경영진 품질 평가`
- description 포함 사항:
  1. 경영진 평가: CEO 능력범위, 정직성, 전략적 안목, 자본배분 능력, 과거 의사결정 품질
  2. 규제 리스크: 현재 및 잠재적 규제 영향
  3. 경쟁 리스크: 각 경쟁자의 위협 정도 평가
  4. 사업 리스크: 신사업 적자, 확장 불확실성
  5. 거시 리스크: 경기 사이클, 산업 사이클 영향
  6. 지배구조: 지분 구조, 특수관계자 거래, 주주환원 정책
  7. 장기 확실성: 10년 후 회사는 어떻게 될까? 무엇이 비즈니스 모델을 뒤엎을 수 있는가?
  8. 최신 규제 동향, 경영진 발언 등 검색 요구

### 네 번째: 4개 병렬 Agent 실행

Task 도구로 4개 Agent를 동시에 띄운다(**반드시 같은 메시지 안에서 병렬 호출**):

각 Agent의 설정:
- `subagent_type`: `general-purpose`
- `run_in_background`: `true`
- `team_name`: 해당 팀명
- `name`: 해당 역할명(business-analyst / financial-analyst / industry-researcher / risk-assessor)

각 Agent의 prompt 템플릿:

```
당신은 {회사명} 투자 리서치 팀의 "{역할 한국어명}"이며, {대가명} 투자 관점에서 {회사명}을 분석한다.

태스크 #{태스크 번호}를 완수하라: {태스크 subject}

구체적 요구사항:
{태스크 description의 내용}

**리서치 방법**:
- WebSearch로 최신 공개 정보(실적, 산업 보고서, 뉴스) 검색
- **재무 데이터는 반드시 독립적인 두 출처에서**, `skills/financial-data.md` 규범에 따라 실행(미국주: macrotrends+stockanalysis; 홍콩주: aastocks+macrotrends; 중국 A주: 동방재부+거조자신; 한국 KOSPI/KOSDAQ 종목: tools/krx_data.py로 조회, 통화는 원(KRW)), 두 출처 오차 >1%면 표시
- 데이터 정확성 확보, 핵심 데이터는 출처 표기
- 분석은 깊이 있게, 표면에 그치지 말 것

**출력 요구사항**:
- 보고서는 상세하게, 핵심 데이터는 Markdown 표로 제시
- 각 분석 차원마다 명확한 결론과 평점 제시
- 보고서 말미에 해당 차원의 종합 결론 제시

**완료 후**:
1. TaskUpdate로 태스크 #{태스크 번호}를 completed로 표시
2. SendMessage로 전체 분석 보고서를 team-lead에게 전송(type: "message", recipient: "team-lead")
```

### 다섯 번째: 보고서 수신 및 진행 추적

- 사용자에게 진행 현황표를 실시간 제시(어느 Agent가 완료했고, 어느 Agent가 아직 리서치 중인지)
- 보고서를 하나 받을 때마다 진행 상황을 갱신하고 해당 보고서의 핵심 포인트(3-5개)를 제시
- 4개 보고서가 모두 도착할 때까지 대기

### 여섯 번째: 팀원 종료

모든 보고서 수신 후, 4개 Agent에게 shutdown_request를 보낸다(SendMessage 사용, type: "shutdown_request").

### 일곱 번째: 최종 보고서 종합

4개 분석 보고서를 종합하여 다음 구조의 최종 보고서를 산출한다:

---

#### 1. 한 문장 결론
> 투자 가치 여부와 핵심 논리를 한 단락(50-100자)으로 요약

#### 2. 4차원 평점 종합표
| 차원 | 프레임워크 | 평점(1-5성) | 핵심 판단 |
|------|------|------------|----------|

종합 평점: X / 5

#### 3. 핵심 데이터 한눈에 보기
주요 재무·경영 지표 표(최근 2년 비교)

#### 4. 각 차원 분석 요약
각 차원에서 가장 중요한 발견 3-5개 발췌

#### 5. 투자 논점(Bull vs Bear)
- 🟢 강세 논리(5-7개)
- 🔴 약세 논리(5-7개)

#### 6. 버핏 매수 전 Checklist
| # | 점검 항목 | 통과? | 설명 |
핵심 점검 항목 10개를 하나씩 평가

#### 7. 최종 투자 권고
- 정성 판단표(사업 품질/경영진/밸류에이션/타이밍)
- 계층별 운용 권고표(공격형/안정형/보수형 → 권고+가격대)
- 핵심 촉매(매수 신호/매도 신호 각 3-5개)

#### 8. 총괄 단락
100-200자의 최종 총괄

---

### 여덟 번째: 보고서 저장

완성된 최종 보고서를 `~/{회사명}투자연구보고서_{날짜}.md`에 작성한다(날짜 형식 YYYYMMDD).

### 아홉 번째: 데이터 표본 검사(발행 승인 절차)

```bash
# Step 1 — 표본 검사 목록 추출(15% 무작위 표본 추출)
python3 ~/ai-berkshire/tools/report_audit.py extract \
  --report <보고서 파일 경로>

# Step 2 — 목록의 각 항목을 신뢰할 수 있는 출처에서 취득(skills/financial-data.md 참조)

# Step 3 — 승인/반려 판정 출력
python3 ~/ai-berkshire/tools/report_audit.py verdict \
  --results '<작성된 JSON>' \
  --report <보고서 파일명>
```

**【승인】** 전부 통과 → 보고서 발행 가능; **【반려】** 미통과 항목 있음 → 수정 후 재심사.

### 열 번째: 팀 정리

TeamDelete로 팀 리소스를 정리한다.

## 중요 유의사항

1. **4개 Agent는 반드시 병렬로 실행**——같은 메시지 안에서 Task 도구를 4번 호출
2. **Agent는 SendMessage로 보고**——파일 협업이 아니라 메시지 통신
3. **데이터 정확성**——Agent에게 WebSearch로 최신 데이터 검색, 핵심 데이터 교차 검증 요구
4. **결론은 명확하게**——매수/관망/회피 권고와 구체적 가격대 제시를 회피하지 말 것
5. **모든 분석은 데이터로 뒷받침**——데이터 출처 첨부
6. **인내심을 갖고 대기**——4개 Agent 리서치에 수 분 소요, 사용자에게 실시간으로 진행 상황 갱신
7. **반편향 의식**——team-lead는 종합 시 반드시 평가할 것: 각 Agent의 분석이 자료 풍부도에 제약받았는가? 시장 컨센서스와 과도하게 수렴했는가? 최종 보고서에는 "정보 풍부도 등급"과 "AI 리서치 한계 선언"을 포함해야 함
8. **정보 희소 시의 정직 원칙**——추측으로 프레임워크를 채워 확실성을 위장하느니, 보고서에 "데이터 부족"이라고 공백으로 표기하는 편이 낫다
