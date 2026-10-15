# 2026-10-15 (11) PR 템플릿에 계약 영향 칸을 더한다

## 계기

사용자가 다른 저장소의 Git·PR 규약을 붙이고 이 저장소의 것과 견주어 물었다.

> 사용자: 위 내용이랑 비교했을 때 우리꺼랑 많이 달라? 우리보다 나은게 있어?

뼈대(짧은 기능 브랜치, PR, squash 병합, 한국어 컨벤셔널 커밋)는 같고, 이쪽은 같은 규칙을 훅·CI·보호 브랜치가 막는다고
답했다. 저쪽이 나은 것으로 PR 본문의 계약 영향 칸을 첫째로 들었다. `CLAUDE.md` 작업 규약 2는 계약을 `sdk/`,
`openapi.json`, 헌법 셋으로 정의하는데, PR 템플릿의 변경된 영역에서 계약이라 적힌 줄은 `sdk/` 하나이고 `openapi.json`,
`server.py`, `http/`는 줄이 없었다. `openapi.json`을 바꾼 PR 열하나(#44부터 #137까지, `git log -- openapi.json`)가
체크할 칸 없이 병합됐다.

> 사용자: PR 템플릿에 계약 영향 칸을 더하고, 변경된 영역에 openapi.json, http/, server.py를 계약으로 넣어 줘. chore 브랜치에서 규약대로 진행해.

작업 도중에 설계 질문이 하나 더 왔다.

> 사용자: 티켓마다 읽어야할 파일들 목록을 넣는건 어떻게 생각해?

(코드 파일 목록은 권하지 않는다고 답했다. 원본 to-tickets 템플릿이 파일 경로는 빨리 낡는다며 피하고, 낡은 목록은
"이것만 읽으면 된다"는 믿음을 만들어 작업 규약 1의 "추측으로 대신하지 않는다"와 부딪친다. 근거 문서 목록은 이미 관례로
있다. 티켓 56개 가운데 39개에 "근거는 …" 문단이, 50개에 명세나 ADR의 인용이 있고, next-session 지시문에는 `읽을 것:` 줄이
있다. 경로별 규칙은 `.claude/rules/*.md`의 `paths`가 싣는다. 대기열에 읽을 것을 놓쳐 틀린 사건은 없었다. 넣는다면 to-tickets
템플릿에 명세 절과 ADR 번호만 드는 `**근거:**` 줄 하나이고, 이 PR과 목적이 달라 따로 한다고 답했다.)

## 한 일

- `.github/PULL_REQUEST_TEMPLATE.md`: 변경사항 아래에 `### 계약 영향`을 더했다. 계약의 정의는 작업 규약 2를 가리키기만
  하고, 닿지 않았으면 "없음", 닿았으면 바뀐 것과 함께 바꾼 것(ADR, `schema_version`, 다시 뽑은 `openapi.json`과 생성
  클라이언트, 헌법 판)과 기다리는 티켓을 적게 했다.
- 같은 파일의 변경된 영역에 `openapi.json`, `src/agent_os/server.py`, `src/agent_os/http/`의 줄을 더했다. 꼬리표는
  "계약(`openapi.json`)과 그것을 만드는 HTTP 표면"이다. 괄호는 diff가 의도한 변경뿐인지(모델 독스트링과 `operation_id`가
  계약에 실린다)와, 이 줄 밖의 `admin/`·`channel/http/` 라우트나 `sdk/`의 이벤트 모델도 `openapi.json`을 바꾼다는 것을 묻고
  `.claude/rules/http.md`를 가리킨다.
- `.claude/skills/next-session/SKILL.md` 1단계: PR을 연 뒤 범위를 넓히는 커밋 전에 고칠 PR 본문 칸에 "계약 영향"을 더했다.
- `KICKOFF.md`의 PR 템플릿 항목: 절 목록(계약 영향, 그리고 전부터 빠져 있던 리뷰어 참고), 칸을 둔 까닭, 바꿀 곳(77행 중
  약 20행)을 맞췄다. 옛 행 수 67은 이 변경 전에도 71로 어긋나 있었다.
- 카나리아 명세 `.scratch/harness/probes/canary/next_session_pr_body_contract_impact.toml`.

## 셀프 리뷰

범위는 기준 `0c12284`, 수정 2개와 미추적 1개(일지), 커밋 0개. 문서만이라 표준 축은 sonnet이었다. 두 축 모두
Critical·Major가 없었다.

- 고친 것(Minor, 두 축): 템플릿 안에서 계약의 정의가 갈렸다. 계약 영향 칸은 "계약은 셋"이라 하면서 `openapi.json`이
  그대로여도 인증·CORS가 바뀌면 적게 했고, 영역 줄은 `server.py`·`http/`에 맨 "계약" 꼬리표를 달았다. 인증은
  `openapi.json`에 없어(`security` 키 0개, 명세 축) 사실상 작업 규약 2를 넓히는 셈이었다. 인증·CORS 문장을 빼고, 꼬리표를
  "계약(`openapi.json`)과 그것을 만드는 HTTP 표면"으로 좁혔다. 규약 2는 바꾸지 않았다.
- 고친 것(Minor, 두 축): next-session 1단계가 PR 본문 칸을 셋으로 못 박아 "계약 영향"이 빠졌다(작업 규약 4). 더했다.
- 고친 것(Minor·Nit): KICKOFF 절 목록의 "리뷰어 참고" 누락, 일지의 옛 행 수(72가 아니라 71, base 커밋의 파일을 셌다),
  영역 줄의 모호한 "이 파일", 자동 검사가 이미 보는 최신성을 "같이 확인할 것"에 다시 적은 문장(뺐다), `sdk/`의 이벤트
  모델도 계약에 실린다는 것(`tests/sdk/test_events.py:307`의 주석을 읽었다), 계약 셋을 템플릿에 다섯째로 다시 적은 것
  (작업 규약 2를 가리키게 했다), KICKOFF의 근거 문장이 사건처럼 읽힌 것(찾은 경위와 PR 수로 고쳤다).
- 남긴 것: 영역 표의 `docs/` 줄에 헌법이 계약이라는 표시를 달지 않았다. 계약 영향 칸이 셋을 모두 부르고, 헌법 파일을
  고치고 판을 올리지 않은 커밋은 `tools/sibling_overlap.py`가 1로 막는다. `claude-code-review.yml`의 경계 축이 `sdk` 계약의
  동반 수정만 보고 HTTP 계약은 보지 않는다는 것(두 축)은 그 워크플로 파일을 별도 PR로 먼저 병합해야 해서 이 PR에 넣지
  않았다.

## PR 직전

CodeRabbit CLI는 좌석이 없어(`Seat: not assigned`, Plan: Free) 돌지 못했다. origin/main이 기준 `0c12284`에서 움직이지 않아
합칠 것 없이 대체 둘을 돌렸다.

- `/security-review`: 발견 0건. 실행되는 코드 변경이 없고, 새 카나리아 명세를 읽는 `tools/canary.py`는 strict 모델로
  검증하며 `shell=True` 없이 인자 리스트로 `claude`를 띄운다.
- `bug-perf-review`: Nit 1건 유효, 오탐 4건. 카나리아 명세 머리에 병합 뒤 다시 돌리는 길(옛 판을
  `git worktree add --detach`로 꺼내 대조군으로 준다)이 없었다. 같은 디렉터리의 다른 명세처럼 한 문장을 더했다. 칸이 아니라
  머리 주석이라 카나리아는 다시 돌리지 않았다. 오탐은 계약 영향 칸이 없는 옛 PR에서 1단계를 따를 때의 어긋남(절을 파싱하는
  곳이 없다), "약 20행"의 어림, 셀프 리뷰 절의 범위가 최종 diff와 다른 것(그 시점의 스냅숏이다), HTML 주석의 깨짐이다.

## 검사

- 카나리아 `next_session_pr_body_contract_impact.toml`: 통과 4(claude 2.1.300). 실험군(커밋 전 워크트리) 셋은 칸 넷을,
  대조군(주 체크아웃, `0c12284`)은 옛 칸 셋을 옮겼다. 사전 확인(`--preflight`)도 통과했다.
- 첫 커밋 `4e343e72`의 pre-commit: 지침 검사, zizmor, `lint-imports`, 타입 우회 검사, `pyright`, `run-hooks`, `web-verify`,
  `pytest`, 표 검사, 줄 구분 문자 검사, 인용 대조(경고 없음), 커밋 메시지 검사 통과. `ruff` 둘과 변이 표 검사는 대상 파일이
  없어 Skipped였고, `ruff` 둘은 손으로 쳐서 통과했다(`All checks passed!`, `639 files already formatted`).
