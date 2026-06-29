# AI Berkshire Codex 가이드

이 저장소는 투자 리서치 워크플로, 리포트, 공용 검증 도구를 담고 있다.
Claude Code 사용자와 Codex 사용자 양쪽 모두와의 호환성을 유지한다.

## 프로젝트 구성

- `skills/*.md`: Claude Code 슬래시 커맨드 소스 파일.
- `codex-skills/*/SKILL.md`: Codex skill 패키지. 대부분 `skills/*.md`에서 생성됨.
  동일 이름의 `skills/*.md` 소스가 없고 명확히 표기된 경우에 한해 Codex 전용 수기 패키지 허용.
- `codex-prompts/*.md`: 슬래시 커맨드 스타일 진입점을 위해 생성된 Codex 커스텀 프롬프트.
  호환 레이어이며, skill이 우선.
- `tools/*.py`: 두 시스템이 공용으로 쓰는 금융 검증·데이터 도구.
- `reports/`: 리서치 산출물. 도구나 skill을 바꾸는 작업 중에 무관한 리포트를 다시 쓰지 말 것.
- `scripts/sync-codex-skills.py`: `skills/*.md`로부터 Codex skill 재생성.
- `scripts/install-codex-skills.sh`: Codex skill 로컬 설치.
- `scripts/install-codex-prompts.sh`: 생성된 Codex 슬래시 프롬프트 로컬 설치.
- `scripts/install-claude-commands.sh`: Claude Code 커맨드 로컬 설치.

## 호환성 규칙

- `skills/*.md`를 정본(canonical) 워크플로 소스로 취급.
- `skills/`의 파일을 변경한 뒤에는 다음을 실행:
  `python3 scripts/sync-codex-skills.py`
- 슬래시 프롬프트 호환이 필요하면 추가로 실행:
  `python3 scripts/sync-codex-prompts.py`
- 대응되는 `skills/`의 소스를 함께 갱신하지 않는 한, 생성된 `codex-skills/*/SKILL.md`를 수동 편집하지 말 것.
- `codex-skills/` 하위의 Codex 전용 수기 패키지는 Codex 전용임을 명확히 표기하고,
  의도적으로 Claude Code에도 워크플로를 채택하는 경우가 아니라면 같은 이름의 `skills/*.md`를 만들지 말 것.
- 도구 경로는 문서화된 체크아웃 경로와 호환되게 유지: `~/ai-berkshire/tools/...`
- Claude Code 동작은 `CLAUDE.md`, Codex 동작은 이 `AGENTS.md`로 관리.

## 리서치 품질 규칙

- skill이 검증을 요구할 때, 금융 데이터는 최소 2개의 독립 출처에서 가져와야 함.
- 시가총액, 밸류에이션, 다중 출처 교차검증, 시나리오 분석에는 정밀 산술 도구를 사용:
  `python3 tools/financial_rigor.py ...`
- 한국(KOSPI/KOSDAQ) 종목 시세·재무·밸류에이션 데이터는 한국 전용 도구 사용(네이버금융 기반, 외부 의존성 0):
  `python3 tools/krx_data.py quote|valuation|financials|search ...`
- 중국 A주 데이터는 `python3 tools/ashare_data.py ...`, 글로벌 공정가치는 `python3 tools/morningstar_fair_value.py ...` 사용.
- 통화 단위(KRW/HKD/CNY/USD)를 명확히 표기. 한국 종목은 원(KRW) 기준이며 시총은 조/억원 단위로 명기.
- 생성된 리서치를 발행 가능 상태로 취급하기 전 리포트 검수 도구 사용:
  `python3 tools/report_audit.py ...`
- 신뢰도 낮은 결론, 불완전한 데이터, 출처 공백을 명확히 표기.
- 본 프로젝트는 학습·연구 목적이며 투자 자문이 아님.

## 편집 규칙

- 작업이 명시적으로 요구하지 않는 한 기존 리포트 파일을 보존.
- 변경 범위는 요청된 skill, 도구, 스크립트, 문서로 한정.
- skill/도구 변경을 마치기 전에 관련 문법 또는 생성 점검을 실행. 호환성 변경 시:
  `python3 scripts/sync-codex-skills.py`
- 파일을 다시 쓰지 않고 생성된 Codex 산출물이 최신인지 검증하려면:
  `python3 scripts/sync-codex-skills.py --check`
  슬래시 프롬프트가 관련된 경우:
  `python3 scripts/sync-codex-prompts.py --check`
