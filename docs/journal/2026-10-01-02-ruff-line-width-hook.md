# 2026-10-01 (02) 편집 직후 ruff E501 계기 훅 — 대기열 53

web-admin 뒤 하네스 chore 배치의 다음 항목이다. 지시문은 일지 2026-10-01-01의 "다음"이 가리킨 next-session 지시문에서
왔다. 브랜치는 `chore/korean-line-width`, 워크트리(`.claude/worktrees/korean-line-width`, base `ff00407`)다. 주 체크아웃은
#110 병합 전(`d1afa7d`)에 머물러 있어 시작 전에 `git pull --ff-only`로 당겼다(지시문의 선행 조건).

> 사용자: ".scratch/retro-queue.md의 53(한국어 줄은 폭 2로 센다)을 chore PR로 반영한다"

## 자리를 정한 것

행이 연 셋(지침 한 줄, 감기 도구, 편집 직후 ruff 되먹임) 중 편집 직후 계기 훅을 골랐다.

- **지침은 이미 있었다.** `docs/constitution/operations.md` 가드레일에 "ruff E501은 표시 폭 기준이라 한글 한 글자가 2로
  세어진다"가 2026-09-20(`d751ccf`)부터 있었는데 회차가 쌓였다(표준 축이 찾았다). 지침이 어겨졌으니 훅이다(교정 루프).
  처음 판의 독스트링은 이것을 모르고 지침 한 줄 대신 두는 훅이라 적었다.
- **감기 도구는 짓지 않았다.** 일지 01의 감기 도우미가 흐트린 두 자리(줄 하나로 선 `사용:` 줄을 다음 문장에 붙였다, 코드
  스팬을 줄에서 갈랐다)는 수십 줄을 한꺼번에 감을 때의 모양이다. 판정을 편집 순간으로 당기면 다시 감을 줄이 방금 쓴 몇
  줄이라 손으로 감는다.
- **막지 않는다.** PostToolUse는 이미 쓴 뒤라 막을 것이 없고, 막는 것은 커밋 전 게이트가 한다.
- **E501만 남긴다.** import를 먼저 쓰고 쓰는 자리를 다음 Edit로 붙이는 동안의 F401처럼 편집 순서가 잠깐 만드는 위반을
  편집마다 울리면 헛계기다. ruff는 설정을 그대로 따르게 부르고(셀프 리뷰 뒤) 결과에서 E501만 남긴다.

## 한 것

- `tools/hook_ruff_line_width.py`(PostToolUse Write|Edit). `.py`·`.pyi`이고 조상에 ruff 설정이 있으면
  `python -m ruff check --no-cache --force-exclude --output-format json <파일>`을 돌려 E501만 행과 폭(`2행 102 > 100`)으로
  알린다. 열 줄까지 적고 나머지는 센다.
- 등록은 `hook_journal_retro`와 같은 Write|Edit 그룹. 테스트 13, 페이로드 표 셋(발동 하나, 짧은 파이썬 Edit 침묵, 설정 밖
  스크래치 스크립트 침묵)과 러너의 자리표시자 둘(`${RUFF_PROJECT}`, `${LOOSE_PY}`).
- 변이 파일 `.scratch/harness/probes/ruff_line_width_mutations.toml`과 프로브 README 행, `tools.md`의 비용 줄, KICKOFF(훅
  아홉, 계기 넷), 대기열 53 닫기.

## 잰 것

- **Windows 탐침.** anthropics/claude-code #80039는 exit 2와 stderr의 길이다 — 본문이 PreToolUse의 exit 2가 막지 않고
  PostToolUse의 stderr가 모델에 닿지 않는다고 보고하고, JSON 출력을 우회로로 든다. 이 훅은 exit 0과 JSON
  `additionalContext`의 길이라 같은 길의 `hook_journal_retro`로 쟀다. 스크래치패드의 `docs/journal/probe.md` 모양 경로에
  `## 다음`을 Write로, 이어서 Edit로 쓰자 둘 다 문구가 이 세션에 닿았다(저장소는 건드리지 않았다).
- **비용.** 등록 모양(`uv run --project … --no-sync python`, `PYTHONUTF8` 없이)으로 세 번씩: 파이썬 323~325ms, 마크다운
  197~206ms. ruff 몫이 약 0.12초다. 처음 판(`--select E501`)은 339~368ms였다.
- **ruff 0.16.8의 모양.** 조상에 설정이 없으면 실행 위치의 설정으로 떨어진다(저장소에서 100, 그 자리에서 기본 88). 조상
  설정이 실행 위치보다 먼저다(120으로 바꾸자 114가 통과). `.md`를 넘기면 "No Python files found"에 `[]`. 깨진 설정은
  종료 2에 빈 stdout. 없는 파일은 stderr 경고에 `[]`·종료 0이다 — E902가 아니다(첫 테스트 독스트링이 틀렸다). 문법 오류는
  `--select E501` 아래서도 `invalid-syntax`로 온다. 캐시를 쓰면 설정 자리에 `.ruff_cache`가 생긴다. `--select`를 빼면 기본
  선택(E501 없음)과 `ignore`를 따르고, `extend-exclude`는 `--force-exclude`와 함께일 때만 듣는다. `--force-exclude`는
  워크트리 파일을 어느 실행 위치에서도 건너뛰지 않았다(주 저장소의 `.gitignore`에 걸리지 않는다).
- **변이.** 열셋 빨강, 확장자 검사 하나 초록(판정이 아니라 비용이라). 처음 판으로 되돌린 변이(`--select E501`)가 빨갛다.
  러너의 침묵 사례 note("설정을 보지 않으면 발동한다")는 스크래치 변이 파일로 한 번 쟀다(러너 어긋남 1건).
- **이 세션의 E501.** 워크트리 세션의 훅은 주 체크아웃의 파일로 돌아 이 세션에는 새 훅이 없었다. 그래서 이 세션도 커밋 전
  `ruff check`에서야 알았다 — 넷, 하나, 다섯. 모두 한글 독스트링·주석 줄이다.

## 셀프 리뷰

`/code-review`, base `ff00407`, 추적 파일 10(새 파일 3, 스테이지됨), 커밋 0. 두 축 모두 기본 모델.

- **명세 축.** 판정이 게이트와 어긋난다 — `--select E501`이 설정의 선택과 `ignore`를 덮고, `--force-exclude`가 없어 제외한
  파일도 본다. 픽스처(`line-length`만 둔 설정)는 게이트가 통과시키는 프로젝트였다. 회차 수가 대기열과 맞지 않는다. 대기열
  닫기에 감기 도구를 두지 않은 이유가 없다.
- **표준 축.** 하드: 헬퍼 `_project`가 영문이다(`tools.md`). 주장 오류: 회차가 넷이고 모두 커밋 직전에 알았고 수십 줄을
  한꺼번에 감았다는 서술(회차는 넷보다 많고, 리뷰가 잡은 회차가 있고, 수십 줄은 일지 01에만 맞다), ruff 몫이 훅 기동에
  견주어 작다는 서술(기동의 57~70%), 지침 한 줄 대신이라는 서술(`operations.md`에 이미 있었다). 판단: 대기열 행이
  독스트링의 논거를 되풀이한다, 픽스처 상수 중복, `create_fixtures`가 훅별로 자란다, ruff 출력의 지식이 두 함수로 갈렸다,
  `RUFF_FILES`의 이름, 테스트 이름과 둘째 단언, 점 키 설정을 못 보는 것, KICKOFF 붙여쓰기.
- **고친 것.** `--select`를 빼고 `--force-exclude`를 더했다. 픽스처를 E·F 선택으로 바꾸고 설정을 따르는 테스트 둘(선택과
  `ignore`, `extend-exclude`)을 더했다. 회차와 지침의 서술을 원문대로, 비용은 `tools.md`의 실측으로 돌렸다. 헬퍼
  `_ruff_설정_아래에_쓴다`, `RUFF_CONFIG_FILES`, 폭 떼기를 `long_lines`로, 테스트 이름, 점 키를 못 보는 것에, 대기열 행을 두
  문장으로, KICKOFF.
- **남긴 것.** 픽스처 상수 중복 — 러너는 테스트를 import하지 않고, 테스트가 러너의 픽스처를 끌어 쓰면 경계가 거꾸로다.
  `create_fixtures`가 훅별로 자라는 것은 이 러너의 기존 모양이다. `operations.md`의 그 줄은 고치지 않았다(ADR 뒤에 쓰는
  문서이고, 사실은 그대로 맞다).

## 검사

- `uv run pytest -q` 1114 passed(`tests/tools/test_hook_ruff_line_width.py` 13). `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run pyright`(0 errors), `uv run lint-imports` 초록. `pnpm -C web verify` 초록(테스트
  263, web은 바꾸지 않았다). 지침·타입 우회·마크다운 표·줄 구분 검사 초록, 훅 러너 37건에 어긋남 0, 인용 대조는 바뀐
  파일에 경고 0. `src/`를 바꾸지 않아 `-m llm`은 돌리지 않았다.
- 변이 14 모두 기대대로.
