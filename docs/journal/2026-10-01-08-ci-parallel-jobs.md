# 2026-10-01 (08) CI를 잡 셋으로 나누고 필수 검사 `verify`가 결과를 모은다

지시문 없이 사용자의 질문에서 시작했다. 데스크톱 앱 세션이 주 체크아웃에서 시작해 `EnterWorktree`로 만든 워크트리에서
일했고, 브랜치는 `chore/ci-parallel-jobs`다.

> 사용자: "CI가 쫌 느린거 같은데 CI 병렬로는 안되나?"

앞 PR의 끝을 여기 남긴다(일지 07의 "다음"). PR #116은 `3325e9a`로 병합됐고, 그 main 푸시의 CI(`36865901921`)는
초록이었다. `verify` 잡 하나가 3분 8초 걸렸다.

## 자리를 정한 것

먼저 최근 실행 셋의 단계 시각을 `gh run view --json jobs`로 손으로 봤다. 한 잡이 파이썬(약 70초, pytest 47초), web(약
70초, `pnpm -C web verify` 55초), e2e(약 45초)를 차례로 돌았고, 셋은 서로의 산출물을 쓰지 않았다. 나누면 가장 긴 잡
하나만큼 걸릴 것이라고 어림했다. 걸리는 것은 셋이었다. 보호 설정의 필수 검사 이름(`verify`), 건너뛴 잡이 성공으로
보고되는 GitHub의 동작, ADR 0021의 2026-09-28 이력("e2e는 CI `verify` 잡의 한 단계다")이다.

> 사용자: "잡 분리 진행"

- **집계 잡.** `python`, `web`, `e2e`를 함께 돌리고 `verify`가 `needs`로 셋을 기다린다. 이름이 그대로라
  `tools/protection.json`은 바꾸지 않았다. `if: always()`로 돌고 `toJSON(needs)`를 `jq -e`로 보아, 모두 `success`일
  때만 초록이다. `e2e` 잡은 준비(`e2e/stack.ts`)가 `uv run`으로 가상 환경의 인터프리터를 찾으므로 uv와 pnpm을 둘 다
  준비한다.
- **ADR 0021의 2026-10-01 이력.** 초안을 보여주고 받았다. 거부한 안은 잡 셋을 각각 필수 검사로 거는 것과
  pytest-xdist다.

> 사용자: "승인"

- **살아 있는 문구.** `tech.md`의 원격·CI 행, `operations.md`의 가드레일, `CLAUDE.md`의 검증 명령 절,
  `playwright.config.ts` 주석, `plan.md`의 web-admin 행에서 "`verify` 잡의 한 단계"를 고쳤다. 헌법은 3.0.4(patch)다. 일지,
  `.scratch/web-admin/`의 명세·티켓, ADR의 옛 이력과 Consequences는 당시의 기록이라 두었다. 잡을 더할 계획인 대기열 34에는
  `needs`에 넣으라는 한 줄을 받는 쪽으로 적었다.

## 잰 것

- **나누기 전과 뒤(손으로 봤다).** 나누기 전은 위의 3분 8초다. 나눈 뒤 첫 실행(`6ccd491`, `36870392735`)은 1분 34초였다.
  `python` 84초, `e2e` 77초, `web` 67초가 함께 돌았고, `verify`는 `python`이 끝난 3초 뒤에 시작해 3초 돌았다. 이제 가장
  긴 잡은 `python`이고 그 안의 pytest다.
- **건너뛴 잡(실험 A, `1b2652c`, `36871174692`).** `web` 잡에 `if: false`를 걸었다. `python`·`e2e`는 성공, `web`은
  `skipped`였고 `verify`는 로그에 `web: skipped`를 찍고 종료 코드 1로 빨갰다. `gh pr checks`에서도 `verify`가 `fail`이고
  `web`은 `skipping`이었다. 조건 없이 이었다면 이 초록 착시가 났을 자리다.
- **실패한 잡(실험 B, `52de1e0`, `36872184767`).** 실험 A를 되돌리고 `python` 잡의 첫 단계를 `exit 1`로 했다.
  `python`은 5초 만에 `failure`, `web`·`e2e`는 성공이었다. `verify`는 셋이 모두 끝난 뒤 `if: always()`로 돌아 로그에
  `python: failure`를 찍고 종료 코드 1로 빨갰다. 실험 커밋 둘은 `ci.yml`을 `6ccd491`의 것으로 되돌려 지웠다(`git diff
  6ccd491 -- .github/workflows/ci.yml`이 비었다).

## 셀프 리뷰

`/code-review`, base `3325e9a`, 수정 파일 7, 커밋 0, 미추적 0. 소스 파이썬이 바뀌지 않아 표준 축은 sonnet이다. 명세는
ADR 0021의 2026-10-01 이력과 `CLAUDE.md` 작업 규약 4다. 두 축 모두 Critical·Major는 없었다.

- **표준 축.** Minor 넷: ADR Consequences 28행의 잔존, ADR의 기동 서술("`serve`를 `uv run`으로 띄운다")이 부정확함, 근거에
  실행 ID·문서 주소·"코드를 읽었다"가 없음, `needs` 규칙이 문서로만 있음. Nit 둘: 같은 사실이 일곱 파일에 퍼짐(`CLAUDE.md`
  줄을 줄이라), ADR 0005에 포인터가 없음. 판단 사항으로 준비 단계의 중복을 들었고 지금은 두어도 된다고 했다.
- **명세 축.** 단계 대조, 종료 코드(`bash -e`, `jq -e`), 보호 설정, 수치 재확인이 모두 맞다고 했다. Minor 둘: `plan.md`의
  잔존, ADR에 없는 `needs` 규칙이 ADR을 근거로 적힘. Nit 둘: 대기열 34에 `needs`가 없음, ADR의 기동 서술.
- **고친 것.** ADR의 기동 서술과 근거 표기(커밋 셋과 실행 ID, 문서 주소, 읽은 파일), ADR에 `needs` 규칙과 그 대가를 한
  항목으로 더함, `CLAUDE.md`·`playwright.config.ts` 문구 줄임, `operations.md`의 "이것"을 풂, `plan.md`, 대기열 34.
- **남긴 것.** ADR Consequences 28행은 두었다. 개정은 이력에 쌓는 것이 관례이고, 같은 ADR의 `--immutable` 개정도
  Consequences를 고치지 않았다. 모든 잡이 `needs`에 드는지 보는 자동 검사는 두지 않았다. YAML을 읽으려면 새 의존성이
  든다(ADR 이력에 적었다). ADR 0005에는 포인터를 두지 않았다. `ci.yml` 머리가 두 ADR을 함께 가리킨다.

## 검사

- 리뷰 반영 뒤: `uv run pytest -q` 1155 passed, `uv run ruff check .`·`uv run ruff format --check .` 통과, `uv run pyright`
  0 errors, `uv run lint-imports` 5 kept, `pnpm -C web verify` 통과, `tools/check_instructions.py`·`tools/check_type_escapes.py`
  통과, `tools/run_hooks.py` 45건 어긋남 0. `src/`를 바꾸지 않아 `-m llm`은 돌리지 않았다.
- 처음 돌린 `pnpm -C web verify`는 Prettier가 `playwright.config.ts`를 빨갛게 봤다. 문구를 Python의 `write_text`로 바꿨더니
  Windows에서 CRLF로 쓰였다. `.gitattributes`가 `eol=lf`라 작업 트리도 LF가 맞아, 다섯 파일을 LF로 되돌렸다.

## PR 리뷰

PR #117을 draft로 열었다. PR 직전 CodeRabbit CLI는 돌리지 않았다. 열기 전 `coderabbit auth status`가 `Plan: Free`,
`Seat: not assigned`였다.
