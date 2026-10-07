# 2026-10-07 (19) LLM 토큰 합계와 봇 리뷰 회차

next-session 지시문으로 연 새 세션의 하네스 chore다. 대기열 113·137을 한 PR로 닫는다. 세션은 주 체크아웃에서 열렸고,
지시문대로 `tidy-checkouts`를 먼저 돈 뒤 `EnterWorktree(name=llm-tokens-and-bot-review-rounds)`로 들어가
`origin/main`(`eda296e`, #167)에서 `chore/llm-tokens-and-bot-review-rounds`를 땄다. 이 일지는 처음에 17번이었는데, 커밋
직전의 `tools/sibling_overlap.py`가 열린 PR #169도 17번을 썼다고 알려 그 출력의 "옮길 번호"대로 19번으로 비켜 갔다.

> 사용자: "대기열 113·137을 한 PR로 반영한다(LLM 테스트 토큰 합계 세는 법, PR 봇 리뷰 둘째 회차부터의 기준)"

## 첫 턴의 tidy-checkouts

- **루트.** main이고 깨끗했다. `5c069d4`에서 `eda296e`로 당겼다. 스킬 파일은 바뀌지 않아 실린 사본 그대로 3을 돌았다.
- **지운 것.** 워크트리 여섯과 그 브랜치(`mutation-check-and-launch-notice`, `open-session-quitting-app`,
  `parallel-open-session`, `pre-commit-fetch-and-empty-scope`, `probe-conventions`, `retro-hook-and-mutation-files`),
  로컬 브랜치 둘(`chore/checkout-persist-credentials`, `chore/pin-review-action`).
- **종료 1로 남은 것.** `silly-carson-627e95`는 `.venv`의 `.pyd`가 잠겨 앞지우기가 막혔고(등록과 `.git`은 남았다),
  `tidy-before-worktree`는 다른 프로세스가 폴더를 쥐어 이름 바꾸기가 막혔다.
- **사람에게 넘긴 것.** prunable `05-admin-hides-decision-for-end-user`, PR 머리가 다른 `skill-check-and-retro-section`,
  분리 HEAD `unruffled-lalande-9017fa`, 등록 없는 폴더 여섯(대기열 148). 지시문대로 답을 기다리지 않았다.

## 어떻게 했나

- **113은 층을 사용자가 골랐다.** 승인된 처방은 `operations.md`의 한 줄이었다. 그런데 4회차(일지 2026-10-06-06)가 그 한 줄의
  방식대로 세고도 스크래치 스크립트를 또 지었고, 일지 2026-10-05-01은 "후보 2가 들면 토큰 합계 스크립트를 `tools/`에 둘지
  본다"고 남겼다. 셋을 보였다. pytest가 끝에 찍기, `tools/` 도구와 한 줄, 승인 문구대로 한 줄만.

  > 사용자: (고른 것) "pytest가 끝에 찍기 (Recommended)"

  세는 함수는 `tools/llm_tokens.py`에 두고 `tests/conftest.py`가 부른다. 토큰 이벤트는 종류 이름이 아니라 모양(최상위의 정수
  `input_tokens`·`output_tokens`)으로 고른다. 지금은 `llm_called`와 `conversation_summarized`뿐이고, sdk에 토큰을 든 종류가
  늘어도 목록이 낡지 않는다. 테스트마다의 `tmp_path`를 세므로 `--basetemp`도 `pytest-current`도 쓰지 않는다(5회차의 함정).
- **처음에는 autouse 픽스처로 짰다.** pyright strict가 `FixtureRequest.node`를 unknown으로 보아(pytest에 형 주석이 없다)
  `@pytest.hookimpl(tryfirst=True) pytest_runtest_teardown(item)`으로 옮겼다. pytest 9.1.1 소스에서 둘을 읽었다.
  `_fillfixtures`가 `item.fixturenames`(폐포)로 `funcargs`를 채우고, 기본 teardown 훅이 `teardown_exact`로 픽스처를 정리한다.
  그래서 tryfirst 구현은 테스트 본문 뒤, 픽스처 정리 전에 돈다. 모든 테스트에 붙던 자동 픽스처도 사라졌다.
- **137은 승인 문구에 회차의 정의를 더했다.** 셀프 리뷰 두 축이 함께 짚었다. 봇 둘(claude-review는 푸시마다,
  CodeRabbit은 요청마다)이 따로 돌아 "회차"가 갈렸다. 회차는 봇마다 세고 그 봇의 첫 리뷰가 첫 회차다. 그래서 첫 회차에 한도에
  걸린 CodeRabbit의 첫 리뷰는 둘째 푸시에 와도 첫 회차로 본다.

## 바꾼 것

- `tools/llm_tokens.py`(새 도구), `tests/conftest.py`(teardown 훅과 끝의 합계 줄), 시험 `tests/tools/test_llm_tokens.py`와
  `tests/test_conftest.py`의 두 사례.
- `docs/constitution/operations.md` LLM 테스트 절과 리뷰 파이프라인 4, `docs/constitution/README.md` 3.0.21.
- `.claude/skills/next-session/SKILL.md` 1단계(137의 기준과 회차의 정의), `.claude/rules/tests.md`의 llm 마커 항목, PR 템플릿의
  pytest 줄.
- 프로브: `.scratch/harness/probes/llm_tokens_mutations.toml`, 카나리아 명세 둘(`next_session_bot_rounds.toml`,
  `tests_rule_llm_tokens.toml`), 그 README의 두 행.
- `.scratch/retro-queue.md`: 113·137 닫힘.

## 잔존 grep

`basetemp`, `토큰 합계`, `봇 리뷰`, `둘째 회차`, `회차마다`를 살아 있는 문서(`*.md`, `.claude/`, `.github/`, `docs/constitution/`,
`docs/agents/`, `tools/`, `tests/`)에서 찾았다. `--basetemp`는 `tools/llm_tokens.py` 독스트링의 경위 문장에만 남았다. 옛 처방을
지시하는 문장은 없다. 리뷰 파이프라인 4의 "보류한 지적은 별도 티켓"은 셀프 리뷰 명세 축이 새 기준과 갈린다고 짚어 단서를
붙였다. PR 템플릿 48행, `code-review` 6단계 4, `CODING_STANDARDS.md`의 심각도 줄은 셀프 리뷰의 것이라 그대로다.

## 검사

- 변이: `llm_tokens_mutations.toml` 열둘 모두 기대대로. 변이마다 `-k`로 빨개질 테스트 하나를 좁혔고, 그 하나만 빨갛다. 처음 여섯은
  셀프 리뷰가, 마지막 셋은 PR 직전 버그·성능 리뷰가 더하게 했다.
- 카나리아(claude 2.1.292, 이 PC): `next_session_bot_rounds.toml` 통과 4(실험군 셋이 스킬을 불러 새 문장을 옮겼고, 대조군인
  주 체크아웃의 옛 판은 "없음"), `tests_rule_llm_tokens.toml` 통과 4(실험군 셋 모두 Read가 대상 하나, 대조군 "없음"). 셀프 리뷰
  반영으로 두 파일의 문장이 바뀌어 다시 돌렸고 둘 다 다시 통과 4였다.
- `uv run --env-file ../../../.env pytest -m llm`을 두 번 돌렸다. 셀프 리뷰 전 픽스처 판은 7 passed, "LLM 토큰 합계
  38,466(입력 37,475, 출력 991). 트레이스 9개, 모델 호출 20건." 셀프 리뷰를 반영한 최종 판(teardown 훅, 바이트 가르기)도 7 passed,
  "LLM 토큰 합계 38,461(입력 37,430, 출력 1,031). 트레이스 9개, 모델 호출 20건."이고 그 줄이 통과 수 줄 바로 위였다. 일지
  2026-10-06-06이 스크래치 스크립트로 센 규모(트레이스 9개, 호출 20회와 요약 1회, 41,343)와 같다. PR 직전 리뷰 반영으로 세지 못한
  테스트의 수가 줄에 붙은 뒤에는 그 길만 `pytest -m llm tests/core/test_model.py`로 돌렸다(1 passed, "LLM 토큰 합계 0(입력 0,
  출력 0). 트레이스 0개, 모델 호출 0건. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다."). 전체 `-m llm`을 세 번째로 돌리지
  않은 것은 트레이스를 세는 길이 읽기 오류를 건너뛰는 것 밖에 바뀌지 않아서다.
- 검증 명령: 셀프 리뷰 전에 `uv run pytest -q` 1854 passed(7 deselected, 끝에 토큰 줄 없음), `ruff check`·`ruff format --check`,
  `pyright` 0 errors, `lint-imports` 5 kept, `pnpm -C web verify`(25파일 338개), 지침 검사, 타입 우회 검사가 초록이었다. 셀프
  리뷰를 반영한 뒤 모두 다시 돌렸고 pytest만 1855 passed(시험 둘을 더하고 하나를 지웠다)로 바뀌었다. 판정 명령은 파이프 없이
  돌리고 로그 파일로 봤다.

## 셀프 리뷰

`/code-review`(기준 `eda296e`, 수정 9·미추적 5, 커밋 0). 표준 축 Major 1·Minor 2·Nit 5, 명세 축 Minor 2·Nit 1이었다. 명세 축은
빠진 요구가 없다고 했다.

- **고친 것.**
  - 표준 Major: 줄을 문자열 `splitlines`로 갈라, pydantic이 이스케이프하지 않는 U+2028이 든 응답의 호출이 합계에서 빠지고
    깨진 UTF-8은 teardown 훅에서 예외를 냈다(리뷰어가 스크래치 스크립트로 손으로 봤다). 독스트링이 인용한 ADR 0012 이력과
    어댑터는 디코딩 전에 바이트의 개행으로 가른다. 바이트로 가르고 두 사례의 시험과 변이를 더했다.
  - 명세 Minor: 합계 줄은 실행의 "끝 줄"이 아니라 통과 수 줄 바로 위다(`TerminalReporter`가 `pytest_terminal_summary`를 감싸고
    통계 줄은 그 뒤에 찍는다). 여섯 자리의 문구를 고치고 테스트가 그 위치를 `consecutive=True`로 단언한다.
  - 두 축: 리뷰 파이프라인 4의 "보류한 지적은 별도 티켓"과 새 기준이 갈렸고, 회차의 정의가 봇 둘에서 두 가지로 읽혔다(위
    "어떻게 했나").
  - 표준 Minor: 변이가 파일 전체를 돌아 빨강의 까닭을 좁히지 않았다(`docs/agents/issue-tracker.md` 프로브와 근거 절).
  - 표준 Nit: `tmp_path`를 "그 실행만의 번호 디렉터리"로 적은 것(번호는 basetemp의 것이다), 못 보는 것에 `tmp_path_factory`가
    빠진 것과 그 주장을 재지 않은 것(conftest 시험에 사례를 더했다), `LLM_INI`의 중복, `_used`의 튜플과 이름, 구현을 베낀 더하기
    시험(지웠다. `count` 시험이 트레이스 둘을 더하며 잰다), rules와 operations.md의 같은 문장.
- **남긴 것.** 없다. 일지가 아직 없다는 Nit은 이 파일이다.

## PR 직전 보안·버그·성능 축

`coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 대체 둘을 돌렸다. 주 체크아웃이 당겨져 `bug-perf-review`가 이
세션의 에이전트 목록에 실렸다.

- **버그·성능(`bug-perf-review`).** 범위 15개 파일, 유효 4(Major 1·Minor 3)·오탐 8이었고 넷 모두 고쳤다.
  - Major: 테스트 소스에 날것 U+2028·U+2029가 들었다. Edit 도구에 넘긴 U+2028의 역슬래시 이스케이프가 날것 문자로 저장된 것이고(대기열
    22와 같은 사고), 그 사이 첫 커밋 시도를 pre-commit의 줄 구분 문자 검사와 저장소 상태 테스트가 막았다. 그 줄은 sed로
    `chr(0x2028)`을 쓰게 바꿨다.
  - Minor: teardown 훅 안의 `OSError`(`.jsonl` 이름의 디렉터리, 다른 프로세스가 쥔 파일)가 pluggy의 나머지 구현, 곧 픽스처
    정리를 건너뛰게 해 다음 테스트의 setup까지 깨졌다(리뷰어가 스크래치로 재현했다). 읽기 오류를 건너뛴다. 디렉터리도
    `OSError`라 `is_file()` 확인은 두지 않았다.
  - Minor: 실패가 있으면 합계 줄과 통과 수 줄 사이에 `short test summary info`가 든다. 문구를 "결과 요약 바로 위"로 고쳤다.
  - Minor: 트레이스를 남기지 않는 LLM 테스트만 돌면 0만 찍혀 모델을 부르지 않았다고 읽힌다. 세지 못한 테스트의 수를 줄에 붙였다.
  - 오탐으로 둔 것: 트레이스를 통째로 읽는 비용(가장 큰 것이 20KB 밑), `rglob`의 범위, 기본 실행에 더하는 비용(합성 테스트
    2000개에서 잡음 안), tryfirst의 시점, CRLF.
  - 반영 뒤 검증 명령을 다시 돌렸다. `uv run pytest -q` 1857 passed(7 deselected), `ruff`·`pyright`·`lint-imports`·지침
    검사·타입 우회 검사가 초록이었다. `pnpm -C web verify`는 커밋 `5612bc5`의 pre-commit이 돌았고 훅 열다섯이 모두 지났다.
- **보안(`/security-review`).** 커밋한 뒤에 불렀고 그 명령이 이 브랜치의 파일 15개와 diff를 모았다. 발견이 없었다. 새 코드는
  표준 `json.loads`만 쓰고, 합계 줄에는 정수 집계만 실려 트레이스 내용(프롬프트, 응답, 키)이 나가지 않는다(원칙 V). 프로브
  TOML의 값이 셸 명령으로 조립되는 길도 없다.

## PR 리뷰 반영

PR [njh6803/agent-os#170](https://github.com/njh6803/agent-os/pull/170). CI 여섯이 `5d4e7be`에서 초록이었다. CodeRabbit은 요청
뒤 OSS 한도에 걸렸다("Review rate limited"). 그래서 이 PR의 보안·버그 축은 PR 본문 체크리스트에 적은 대체 둘의 결과가 맡는다.

claude-review 1회차는 Critical·Major 없이 Minor 둘·Nit 셋이었다. 이 PR이 세운 기준(대기열 137)을 처음으로 적용했다. 이 봇의
첫 리뷰라 첫 회차이고, 지적마다 판단했다.

- 고친 것: `Tokens`가 `count()`가 채우지 않는 `untraced_tests`를 들어 두 이유로 바뀌었다(Minor, 리뷰 관점 3). conftest가 따로
  세어 `summary()`의 인자로 넘긴다. `operations.md` LLM 테스트 절이 세지 못한 수까지 되풀이했다(Minor, 같은 사실은 한 곳에만).
  "그 줄을 옮긴다"와 원천 포인터만 남겼다. 독스트링의 어색한 줄바꿈과 합계 줄 끝 문장의 마침표(Nit 둘).
- 보류한 것: `next-session` 1단계가 길어 기준을 `operations.md`로 옮기고 스킬은 가리키기만 하자는 Nit. 대기열 137이 승인한
  자리가 행동이 일어나는 1단계이고, `operations.md` 리뷰 파이프라인 4가 그 자리를 가리킨다. 이유는 PR 코멘트에 남겼다.
- 변이 열둘이 다시 모두 기대대로였다(원문이 바뀐 셋을 고쳤다).
