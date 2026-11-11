# 2026-11-11 (10:50) pyright가 분석하지 않는 경로를 받으면 "0 errors"가 판정이 아니라고 알리는 훅 (harness pyright-unchecked-path-hook)

세션 제목 `chore/pyright-unchecked-path-hook`. 브랜치 같은 이름, 워크트리 `.claude/worktrees/pyright-unchecked-path-hook`. 모델 Sonnet 5.5 / high(지시문).

## 사용자 프롬프트

> 대기열 431을 티켓 .scratch/harness/issues/pyright-unchecked-path-hook.md로 쓰고 한다
>
> 다음 작업: 받는 세션이 쓸 .scratch/harness/issues/pyright-unchecked-path-hook.md. 대기열 431(8회차): Bash 명령이 `pyright`에 검사 범위 밖이나 점 디렉터리 아래 경로를 주면 "0 errors"가 판정이 아니라고 알리는 PostToolUse 계기 훅을 더한다
> 다음 단계: 구현
> 이번 요청 범위: PR과 병합까지

이어서 사용자가 "이어서 진행"이라고만 말했다(앱이 한 번 종료돼 이어 받았다). 같이 여는 둘째 세션(대기열 565)과 고칠 파일이 겹치지 않는다는 지시였다. 겹친 것은 `.scratch/harness/probes/README.md` 하나뿐이다(`sibling_overlap.py`가 PR #522와 한 워크트리를 함께 고친 파일로 찍었다).

## 결정

- **판정을 항목의 전제보다 좁혔다.** 대기열 431은 "검사 범위 밖이거나 점 디렉터리 아래"라고 적었다. 이 브랜치에서 pyright 1.1.414로 `uv run pyright --outputjson <경로>`를 파일 하나씩 쳐서 `summary.filesAnalyzed`를 손으로 봤다. `.scratch` 아래 파일과 폴더 인자, `node_modules` 아래, `__pycache__` 아래는 0이었고, `include` 밖이지만 점 없는 폴더(`docs/`)의 파일과 폴더 인자, 저장소 밖 파일은 1이었다. 그래서 훅은 점 폴더, `node_modules`, `__pycache__` 아래만 짚고, `include` 밖은 짚지 않는다. `docs/constitution/operations.md`의 같은 문장도 고쳤다. 이 측정은 커밋한 프로브가 아니라서 쟀다고 적지 않았다(티켓, 훅 독스트링, operations.md에 손으로 봤다고 적었다).
- 경로는 프로젝트 루트(작업 폴더에서 위로 올라가 처음 만나는 `[tool.pyright]`나 `pyrightconfig.json`) 기준으로 바꿔 본다. 이 저장소의 워크트리는 `.claude/worktrees/` 아래라 절대 경로가 `.claude`를 품는데 그 안의 `tests/`는 분석된다(워크트리에서 `uv run pyright tests/_pp/a.py`가 1이었다, 손으로 봤다). 루트 기준으로 바꾸지 않으면 늘 거짓 양성이 난다.
- `--project`·`-p`를 쓴 호출은 판정하지 않는다(제외 규칙의 기준 폴더가 바뀐다). 저장소 밖 경로도 알리지 않는다.
- 막지 않는 계기 훅이고 세션·에이전트마다 한 번 알린다. `hook_journal_evidence`의 표지 모양을 따랐다(훅은 서로 import하지 않는다).

## 한 일

- `tools/hook_pyright_unchecked_path.py`(새 훅), `tests/tools/test_hook_pyright_unchecked_path.py`(셀프 리뷰를 반영한 뒤 119건), `.claude/settings.json`(PostToolUse `Bash` 묶음에 등록), `tools/hook_payloads.toml`(발동 하나, 침묵 하나).
- `.scratch/harness/probes/pyright_unchecked_path_hook_mutations.toml`(처음 변이 열과 대조군 하나, 셀프 리뷰 반영으로 변이 열을 더해 모두 스물한 개)과 그 프로브 README 행.
- `docs/constitution/operations.md`의 pyright 프로브 항목, `.claude/rules/tools.md`의 훅 시간 목록(Bash·PowerShell의 PostToolUse 훅 수), 헌법 판 3.0.83 → 3.0.84(`docs/constitution/README.md`. `sibling_overlap.py`가 operations.md를 고치고 판을 올리지 않았다고 짚었다).
- 카나리아 명세 `tools_rule_journal_evidence_bash.toml`: 같은 문장을 원천으로 들었다. 그 문장이 훅 둘을 든 것으로 바뀌어 질문과 `expect`를 훅마다의 설명을 모두 옮기게 고쳤다.
- 대기열 0431을 닫았고(`닫힘 (…)`) 티켓을 `done`으로 바꿨다.

## 확인한 것

- 시험을 먼저 썼다. 훅 파일이 없을 때 import가 실패하는 상태에서 시험을 쓰고 구현했다. 처음 돌린 시험 한 건은 `.scratch/probes`에서 `../tests/x.py`가 `.scratch/tests/x.py`라는 기대값 계산을 틀린 것이라 구현이 아니라 시험의 기대값을 고쳤다(`../../tests/x.py`가 점 폴더를 벗어난다). 등록 시험 한 건은 `settings.json`에 등록하기 전에 예상대로 빨갰다(`[] == ['Bash']`).
- `uv run pytest tests/tools/test_hook_pyright_unchecked_path.py -q`: 출력을 읽었고 등록 뒤 `78 passed`였다. 파라미터로 나눈 뒤 변이 표의 기준선이 `86 passed`를 찍었다(`mutate.py`가 찍었다).
- `uv run python tools/run_hooks.py`: 출력의 마지막 줄을 읽었다. `훅 페이로드 187건, 어긋남 0건, 래퍼 알림 5건, 어긋남 0건, 표의 빈자리 0건.` 새 훅의 두 사례는 `[ok]`였다.
- `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/pyright_unchecked_path_hook_mutations.toml`: 열한 개 가운데 열 개가 기대대로였고, 9번은 변이는 빨갰으나 표지가 실제 출력과 달라(`']` 대 `'`) 어긋났다. 출력을 본 뒤 표지를 고쳐 9번만 다시 돌려 기대대로였다(`mutate.py`가 찍었다). 이 표지의 양성 대조(다른 단언이 빨개져도 그 문구가 없는지)는 하지 않았다.
- `uv run ruff check .`와 `uv run ruff format --check .`: `All checks passed!`, `2025 files already formatted`. `uv run pyright`: `0 errors, 0 warnings, 0 informations`. 출력을 읽었다.
- 카나리아 `tools_rule_journal_evidence_bash.toml`: `uv run python tools/canary.py <명세> <스크래치패드>/canary_out`가 `통과 4 · 실패 0 · "없음" 섞인 통과 0`을 찍었다(claude 2.1.322, 커밋 f64dfe41c 위의 커밋하지 않은 판). 대조군은 "없음"이었고 실험군 셋은 두 훅의 설명을 글자 그대로 옮겼다. 이어 `--preflight`도 통과 1이었다.
- `uv run python tools/hook_report.py`: 출력을 읽었고 뺄 후보는 `hook_session_web_deps.py`뿐이라 비슷한 훅은 없었다.
- 셀프 리뷰를 반영한 뒤 `uv run pytest tests/tools/test_hook_pyright_unchecked_path.py -q`: 출력을 읽었고 `119 passed`(변이 표 기준선도 119). `uv run ruff check`·`ruff format`은 `All checks passed!`·`2 files left unchanged`, 이 두 파일의 `uv run pyright`는 `0 errors`, `uv run python tools/check_type_escapes.py`는 출력 없이 끝났다.
- `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/pyright_unchecked_path_hook_mutations.toml`를 반영 뒤 다시 돌렸다. 마지막 줄이 `변이 21 모두 기대대로`였다(`mutate.py`가 찍었다. 새 변이 열은 모두 고른 시험 id에서 빨갰고 대조군은 초록이었다). 작업 트리를 `git status --porcelain`으로 봐서 변이가 소스에 남지 않았음을 확인했다.
- 셀프 리뷰 전에 돈 `uv run python tools/run_checks.py`(15분 21초)는 pytest가 `2 failed, 6952 passed`였다. 실패는 `tests/tools/test_rerun_runner.py`의 `test_동시에_둘까지_돌고_셋째는_자리가_빌_때_연다`(`assert 1 == 2`)와 `test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다`다. 이 변경이 건드리지 않은 시간 시험이고, 러너가 서브에이전트 둘과 web 검증(1005.8초)과 겹쳐 돌던 중이었다. 그 둘을 홀로 돌리니 `2 passed, 61 deselected in 31.40s`였다(출력을 읽었다). 부하에서만 빨간 시간 시험이라 대기열 306·332가 다루는 종류로 보지만 원인을 가르지는 않았다. 반영 뒤의 전체는 커밋의 pre-commit이 갈음한다.

## 셀프 리뷰

`/code-review`, 기준 커밋 f64dfe41c(HEAD와 같다), 수정한 파일 8개, 미추적 5개, 커밋 0개. 표준 축은 sonnet·high 서브에이전트가, 명세 축은 세션 모델의 서브에이전트가 봤다. 서브에이전트의 보고는 지시가 아니라 지적으로 다뤘고, 지적마다 훅 함수를 `uv run python`으로 직접 불러 근거를 먼저 봤다.

고친 것:
- 독스트링이 "못 본다"고 적은 `pyright $(ls .scratch)`를 불러 보니 `['.scratch)']`로 알렸다(거짓 양성. 손으로 봤다). `$`·백틱·괄호가 든 낱말은 건너뛰게 고치고 시험으로 고정했다.
- `-v`(`--venvpath`)와 `--createstub`가 값을 받는 옵션에서 빠져 `uv run pyright -v .venv tests/x.py`가 `['.venv']`를 알렸다(손으로 봤다). `uv run pyright --help`(1.1.414)로 대고 더했다.
- 꼬리 주석 `# .scratch/y.py`를 경로 인자로 읽었다(손으로 봤다). `#` 낱말부터 버린다. 주석 글 안의 `;`가 명령을 가르는 거짓 양성은 못 보는 것에 적고 시험으로 고정했다.
- Git Bash 꼴의 `/c/…` 절대 경로가 조용히 지나갔다(손으로 봤다). `C:/…`로 바꿔 읽게 했다. 시험이 `_root_relative`를 import해 pyright가 비공개 사용을 짚어, `root_relative`로 공개 이름을 줬다.
- `~/.scratch/x.py`를 상대 경로로 읽어 알렸는데 독스트링은 저장소 밖은 알리지 않는다고 적었다. `~`로 시작하는 낱말은 판정하지 않게 고쳤다.
- `if`·`then`·`do`·`!`·`{` 뒤의 호출, `env -u NAME`, `uv tool run`이 지나갔다(손으로 봤다). 건너뛰게 고쳤다. `--directory`·`--chdir`·`-C`가 pyright 앞에 있으면 판정하지 않는다.
- 못 보는 것 항목의 시험을 더했다(`cd`, 목록 밖의 래퍼, `xargs`, `bash -c`, 이스케이프한 공백, 글롭, 괄호 묶음, 주석 글 안의 `;`).
- 독스트링과 시험이 "손으로 보지 않았다"고 적은 둘을 이번에 손으로 봤다. `uv run pyright --outputjson tests/.pp_dot_probe.py`는 `filesAnalyzed` 0, 저장소 밖 점 폴더의 `.dotdir/outside_probe.py`는 1이었다(서브에이전트가 같은 값을 냈지만 내가 다시 쟀다. 임시 파일은 지웠다).
- 티켓의 "남은 둘"을 세 폴더 네 자리로 고쳤다(명세 축이 `end-user-channel`의 셋째를 잡았다).
- 변이 표에 새 동작마다 변이 열 개를 더했다(모두 스물한 개).

남긴 것과 이유:
- `_tokens`·`_without_redirects`·`claim_first`의 모양이 `hook_journal_evidence`와 겹친다는 지적은 훅끼리 import하지 않는다는 `.claude/rules/tools.md`의 결정의 비용이라 남겼다(표준 축도 지적하지 않았다).
- 명세 축은 `uv run --directory`를 거짓 음성이라 했지만 내 호출에서는 `uv run --directory . pyright .scratch/x.py`가 `['.scratch/x.py']`를 냈다(손으로 봤다). 그래서 이 입력을 판정하지 않는 쪽으로 고쳤다.
- `(…)` 묶음 안의 마지막 인자와 이스케이프한 공백은 코드를 더 따르지 않고 못 보는 것에 적고 시험으로 고정했다. 막지 않는 계기 훅이라 셸 파서를 따르지 않는다는 독스트링의 전제 그대로다.
- `Node_Modules`·`__PYCACHE__`의 대소문자는 훅이 `.lower()`로 알린다. pyright의 제외가 윈도와 리눅스에서 대소문자를 가리는지는 재지 않았다(알리는 쪽으로 기운다).
- 티켓의 수용 기준 체크박스는 검증이 끝난 뒤 표시한다.

다시 돌린 명령과 결과는 위 "확인한 것"의 마지막 세 항목이다. 커밋 직전의 손으로 치는 다섯(pytest 전체, pyright, ruff 둘, lint-imports, web)은 커밋의 pre-commit 결과로 갈음한다.

## 못 본 것

- 이 훅이 실제 세션의 모델에게 닿는지는 재지 않았다(독스트링의 못 보는 것 마지막 항목). 계기 훅의 알림이 닿는지는 이 저장소에서 모델이 문장을 옮기게 해서 보는 방법이 있는데 이번에는 하지 않았다.
- 워크트리 세션의 훅으로는 바뀐 훅을 확인할 수 없다(`.claude/rules/tools.md`). 새 훅은 병합 뒤 주 체크아웃이 당겨져야 세션에서 돈다.
- 남은 옛 표현은 `.scratch/` 프로브 기록 세 폴더 네 자리다(`interrupts/probes/README.md`, `web-widget/probes/jwt_verify/check_types.py`의 주석, `end-user-channel/probes/check_types.py`의 주석과 같은 폴더 `README.md`). 그때의 프로브 기록이라 고치지 않았다. "`tests/` 아래로 복사해서 잰다"는 쓰는 방법은 지금도 맞다. 이 수는 `include.{0,6}밖`·`검사 없이 0 errors`로 Grep해 센 것이라 다른 낱말로 쓴 곳은 더 있을 수 있다(처음 티켓은 둘로 적었다가 명세 축 리뷰가 셋째를 잡았다).

## 회고

후보 일곱(여섯은 셀프 리뷰 전에, 일곱째는 셀프 리뷰 뒤에 더했다), 판정은 승인 1 · 넘김 0 · 기각 6. 근거는 이 일지의 앞 절과 `uv run python tools/queue_open_rows.py`(작업 트리와 `--ref origin/main` 둘 다 출력을 읽었다)다.

- 변이 표의 9번 표지가 실제 출력과 달랐다(`']` 대 `'`). 기각: `tools/mutate.py`가 어긋남으로 직접 알려, 이미 있는 검사가 그 자리에서 알렸다(4단계의 기각).
- 첫 시험 초안에 `# pyright: ignore`를 썼다. 기각: `tools/check_type_escapes.py`가 판정하는 규칙이고 실행하기 전에 고쳤다. 검사가 이미 있다.
- 시험의 기대값 계산 하나를 틀렸다(`.scratch/probes`에서 `../tests/x.py`). 기각: 일회성 계산 실수이고 검사나 지침으로 옮길 반복 꼴이 아니다. 사건 없이 떠올린 것에 든다.
- 대기열 431이 적은 "검사 범위 밖"이 반쯤 틀렸다(손으로 재니 `docs/` 같은 점 없는 폴더는 분석됐다). 기각: 틀린 문장의 출처인 `operations.md`의 한 줄을 이 PR이 이미 고쳤고, 근거 문장은 손으로 잰 것인지 밝히라는 지침과 계기 훅(`hook_journal_evidence`)이 이미 겨누는 자리다. 같은 일을 다룬 열린 항목도 없었다(`--search 전제.*틀`로 찾아 닫힌 셋만 맞았고 사건이 달랐다).
- `.claude/rules/tools.md`의 문장을 바꾸자 카나리아 명세를 다시 돌려야 했다. 기각: `sibling_overlap.py`가 알려서 알았고, 같은 일을 다루는 열린 항목(`canary-notice-spec-paths`)이 이미 있다.
- 앱이 한 번 종료돼 `uv sync`가 끊겼다. 기각: 환경 사건이고 하네스가 바꿀 것이 없다. 편집기의 오래된 import 진단도 `uv run pyright` 0건으로 가려져 비용이 없었다.

- 훅 독스트링의 못 보는 것(`pyright $(ls .scratch)`)을 재지 않고 적었고, 못 보는 것 대부분을 시험으로 고정하지 않았다. 셀프 리뷰 표준 축이 코드와 어긋난 주장과 빠진 시험을 잡았다(위 "셀프 리뷰"). 승인: 구현 때 실리는 지침(`.claude/rules/tools.md`의 못 보는 것 항목)을 어겨 리뷰가 잡은 사건이라 회차로 센다(4단계). 간 자리: 열린 항목 `plan-table-unseen-claim`에 회차를 더해 4회차가 5회차가 됐다(`queue_open_rows.py --search 못.보는.것`으로 찾았고, 같은 처방을 든 열린 항목은 이것 하나였다. 닫힌 `0187`·`0362`가 같은 규칙의 앞 회차다). 이 항목의 처방은 5회차에 계기 훅을 고르는 것이라 `next-session` 결정표의 chore 배치 조건에 든다. 이 세션에서는 반영하지 않는다(이 PR의 범위가 아니다).

만료할 항목은 없었다(두 출력 모두 `(없음)`). 이 PR이 닫은 대기열 431은 `origin/main`에서는 아직 열려 있어, 병합되면 닫힌다.

## PR 직전 리뷰

`coderabbit-review` 서브에이전트가 돌았다. CLI 0.7.5가 끝까지 돌아 `review_completed`·종료 코드 0·지적 1건을 냈고, `auth status`는 `Plan: Free`·`Seat: not assigned`였다. 커밋된 변경 14개를 모두 봤고(150개 이하라 `--dir`로 좁히지 않았다), 서브에이전트가 훅 코드를 따로 읽고 입력을 넣어 점검한 것까지 합쳐 유효 2건·오탐 0건이었다. 둘 다 고치는 값이 작아 PR을 열기 전에 고쳤다.

- 유효(Minor), 프로브 README의 변이 표 행이 실제와 달랐다. 행은 변이 열 개와 "열하나 모두 기대대로"라고 적었는데 표에는 `[[mutation]]`이 21개(변이 20개와 대조군 하나)였다. 열 이름과 개수와 결과 문구를 고쳤다.
- 유효(Minor), `_FD_DUP = r"\d*[<>]&\d+"`가 숫자만 이어진 긴 낱말에서 제곱 시간이 걸렸다. 손으로 봤다(커밋하지 않은 스크래치 스크립트를 `uv run python <스크래치>/fd_dup_time.py`로 돌렸다). 숫자만 1만 자에서 0.74초, 2만 자에서 3.22초, 4만 자에서 13.37초였고, 앞에 숫자를 막은 `(?<!\d)\d*[<>]&\d+`는 모두 0.00초였다. 일반 입력(`2>&1`, `12>&1`, `a1>&2`, `x>&2`, `pyright x 2>&1`)의 치환 결과는 두 정규식이 같았다. 훅의 등록 제한(20초)을 넘으면 fail-open으로 지나가 도구 호출을 막지는 않지만 그동안 훅이 매달린다.
  - 고친 것: `tools/hook_pyright_unchecked_path.py`의 `_FD_DUP`, 시험 `test_숫자만_이어진_긴_낱말도_제때_읽고_뒤의_경로를_짚는다`(4만 자, 상한 5초. 홀로 돌려 0.07초라 넉넉한 배수다), 변이 21번 "파일 기술자 복제 정규식 앞의 숫자 막기를 뺀다". 변이 표 `--check`는 22개 모두 원문이 한 번씩 있었고, 21번만 번호로 돌리니 기준선 0.34초 초록, 변이를 넣으면 14.99초 빨강으로 기대대로였다.
- 오탐으로 점검한 것(서브에이전트가 읽고 입력을 넣어 본 것): `main`이 JSON 배열이나 문자열을 받으면 `payload.get`에서 예외가 나 종료 코드 1로 지나가는 것(다른 훅과 같은 모양이다), `session_id`가 로운 서러게이트이거나 `cwd`가 문자열이 아닐 때, `marker_name`의 경로 조작, `claim_first`의 심볼릭 링크 추적, 다중 사용자에서 고정된 표지 폴더 이름의 선점, 쌓이는 빈 표지 파일, `shlex` 실패와 `PureWindowsPath`, `find_root`의 `NUL`. 이 PC는 단일 사용자이고 알림이 사라질 뿐이라 고치지 않았다.
- 밀 주장으로 남긴다(이 턴에 새로 쓴 사실 문장): (1) `_FD_DUP` 주석 "숫자 4만 자에서 막지 않은 판 13초, 막은 판 0.00초"(손으로 봤다, 위 스크래치 명령), (2) 시험 주석 "숫자 4만 자는 앞에 숫자를 막지 않은 … 정규식에서 13초가 걸렸다(손으로 봤다)", (3) 프로브 README의 변이 표 행(변이 21개와 대조군 하나, 처음 20개와 대조군을 돌려 모두 기대대로였고 21번만 따로 돌렸다는 문장).
- 다시 돌린 것: `uv run pytest -q tests/tools/test_hook_pyright_unchecked_path.py` 120건 통과(기계 부하로 167초가 걸렸다. 새 시험은 홀로 0.07초). 이 수정을 싣는 커밋의 첫 pre-commit은 pytest의 시간 시험 셋에서 빨갰다(`tests/tools/test_probe_kit.py::test_배출은_줄이_계속_와도_제한_시간에_끝난다`, `tests/channel/cli/test_interrupt.py::test_서버를_닫기_시작한_뒤에_한_번_누르면_닫기를_마치고_중단으로_끝난다`, `tests/tools/test_rerun_runner.py::test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다`. 7003건 통과, 3건 실패, 한 바퀴 1190초로 다른 세션이 함께 돌던 때다). 셋 모두 이 변경이 건드리지 않은 파일이고, 홀로 돌리니 3건 통과(23.76초)였다. 부하에서만 빨간 시간 시험이라 같은 종류의 새 사례로 일지에만 적는다(대기열 306·332의 꼴). 나머지 게이트는 둘째 커밋 시도의 pre-commit이 갈음한다.

## 다음

- 커밋 `1809c01ec`까지 했고 `origin/chore/pyright-unchecked-path-hook`에 푸시했다(pre-commit 전부 통과). 그 커밋은 `origin/main`(`5f7e39ed9`)을 글자 충돌 없이 합치고(`.scratch/harness/probes/README.md`는 자동 병합, `sibling_overlap.py`는 번호 겹침 없음) 티켓 5행의 인용과 이 "다음" 절을 실었다.
- PR 직전 리뷰의 유효 2건을 고쳐 작업 트리에 두었고 아직 커밋하지 않았다(위 "PR 직전 리뷰"). 다음 커밋에 싣고, 푸시한 뒤 PR을 연다. PR 본문의 체크리스트에는 CLI 축이 돌았다는 것(`Seat: not assigned`에서도 리뷰가 돌았다)을 적는다.
- 병합은 이 워크트리 사본의 next-session `merge.md`의 "워크트리에서 병합할 때"를 Read로 열어 따른다. 주 체크아웃은 `f64dfe41c`의 main이라 이 세션이 당기지 못했다.
- 보류한 것은 위 "셀프 리뷰"의 "남긴 것"이다. 이 PR에는 대기열 `plan-table-unseen-claim`의 5회차 반영이 없다(`next-session` 결정표의 chore 배치 조건에 든다).
- 새 훅은 병합 뒤 주 체크아웃을 당긴 세션부터 돈다.
- 인계: 제목을 `chore/pyright-unchecked-path-hook (인계함)`으로 바꿨고, 워크트리는 이미 잠겨 있지 않았다(`git worktree unlock`이 `is not locked`).
- open-session을 부른다 2026-11-11T02:44:00Z
- 인계 못함 커밋 뒤: 주 체크아웃(`f64dfe41c`)의 `tools/open_session.ps1`이 `origin/main`(`5f7e39ed9`)의 판과 96줄 다르다(`git diff --stat f64dfe41c 5f7e39ed9 -- tools/open_session.ps1`을 쳤다). 스킬이 그 옛 판으로는 열지 말라고 하므로(폴더 검사가 없다) 세션을 열지 않았다. 제목을 `chore/pyright-unchecked-path-hook`으로 되돌리고 남은 단계(main 합치기, 푸시, PR, 병합)를 이 세션이 잇는다.
