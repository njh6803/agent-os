# 2026-10-23 (22) `.env` 읽기 훅의 Grep 도구 glob 판정을 실제 rg와 맞댄다

> 사용자: 대기열 422를 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md로 쓰고 한다

## 한 일

- harness 티켓 007을 쓰고 워크트리 `chore/007-env-read-glob-matches-rg`에서 시작했다.
- Grep 도구가 glob을 rg에 넘기는 모양을 손으로 봤다(claude 2.1.302, 세션 스크래치패드의 가짜 폴더. `.ignore`에 든 `secret.txt`·`.hid`와 무시하지 않은 `.vis`, `a.md`). glob 없이는 `.vis`·`a.md`만 냈다. `*.md,secret.txt`와 `*.md .hid`는 무시된 파일까지 냈고, `{secret.txt}`는 그 파일을, `{*.md},secret.txt`는 아무것도 내지 않았다. 공백으로 나누고, 중괄호가 없으면 쉼표로도 나누며, 중괄호가 있으면 쉼표로 나누지 않는다고 읽었다.
- 그 자리에서 훅의 판정을 스크래치 스크립트로 찍었다. `*.md,.env`와 `*.md .env`를 지나보냈다(거짓 음성).
- PATH에 rg가 없다. Claude Code 실행 파일(`~/.local/bin/claude.exe`)을 실행 이름 `rg`로 띄우면 `ripgrep 14.1.1 (rev 0049fd75eb)`로 답했다(손으로 봤다). PyPI의 `ripgrep` 15.1.0은 macOS arm64와 manylinux x86_64 휠뿐이라 이 PC에서는 소스 빌드가 실패했다. CI 러너 이미지(ubuntu-24.04 20261012.334.1)의 README 원문에 ripgrep이 없다(받아서 grep했다).

## 결정

시험이 실제 rg를 띄울 길을 물었다.

> 사용자: CI에도 rg를 깔고 실제로 맞댄다 (Recommended) — "시험이 매번 실제 rg를 띄워, 임시 폴더의 가짜 `.env`를 rg가 내는지와 훅의 판정이 같은지 봅니다. CI는 ci.yml에서 apt로 ripgrep을 깔고, 로컬은 Claude Code 실행 파일을 씁니다(PATH에 rg가 없고 그 실행 파일이 ripgrep 14.1.1로 답한 것은 손으로 봤습니다. Grep 도구가 그것을 쓴다는 것은 그로부터 미룬 어림입니다). rg를 찾지 못하면 건너뛰지 않고 실패합니다. 잡아 주는 것: rg 판이나 glob 규칙이 바뀌어도 시험이 바로 빨개집니다. 치르는 값: 시험 전제가 하나 늘어서 ADR을 쓰고 승인을 받아야 하며(pwsh 때의 ADR 0030과 같은 모양), CI 잡이 apt 설치 시간을 더 씁니다(재지 않았고 수 초~수십 초로 어림합니다)."

## 구현(커밋 전)

- 실제 rg(Claude Code 실행 파일, 14.1.1)로 `git init`한 임시 폴더의 gitignore 된 가짜 `.env`를 두고 손으로 더 봤다. rg의 `-g`는 `--hidden`·`--no-ignore` 없이도 `.env`를 읽었고(무시·숨김 규칙을 이긴다), `-t py`가 있어도 읽었으며, 뒤에 온 glob이 이겼고(`-g '!.env*' -g .env`는 읽고 거꾸로는 읽지 않았다), 붙여 쓴 `-g.env`도 읽었다. 훅의 Bash 길은 이것을 모두 지나보냈다(거짓 음성). 하위 폴더 경로 `sub`를 주면 그 아래 `.env`를 읽는다(독스트링이 이미 적은 못 보는 것의 rg 꼴).
- rg는 모든 파일을 걸렀을 때(`No files were searched`)와 glob을 풀지 못할 때(`{.env`, 겹친 묶음 `{{.env}}`) 종료 코드 2로 끝나고 아무것도 읽지 않는다.
- 새 시험 `tests/tools/test_hook_env_read_rg.py`를 먼저 썼다. 껍데기 `grep_tool_globs`(통째로 돌려줌)로 28개가 빨갰다. 그 뒤 `tools/hook_env_read.py`에 `grep_tool_globs`(공백·쉼표 나누기), `_rg_globs_include_env`(마지막으로 `.env`를 말한 glob이 고르는 것이면 막는다), `_option_values`의 붙여 쓴 짧은 옵션을 더해 244개가 초록이다(`tests/tools/test_hook_env_read.py`와 함께).
- 훅이 rg보다 넓게 막는 자리(거짓 양성) 넷을 시험에 고정했다: `.ENV`, `{{.env}}`, `.env !.env`, `src/** tests/**`.
- ADR 0038 초안(`proposed`)과 색인 행, `ci.yml`의 apt 설치 줄, rg 전제를 `tech.md`·`operations.md`·`README.md`·`.pre-commit-config.yaml`에 적었고 헌법 판을 3.0.52로 올렸다.
- 일지 번호는 형제(008)와 두 번 겹쳐 옮겼고, main이 앞서 다시 22로 옮겼다(`sibling_overlap.py --move`).
- ADR 0038은 아직 사용자에게 보이지 않았다. 셀프 리뷰를 반영한 뒤 보이고 승인받는다(`CLAUDE.md` 작업 규약 5).

## 셀프 리뷰(새 세션, 기점 975bf04c, 커밋 0·바뀐 파일 8·미추적 4)

> 사용자: 대기열 422를 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md로 쓰고 한다

표준 축(sonnet·high)은 Major 1, Minor 5, Nit 3을, 명세 축은 Major 2, Minor 4, Nit 1을 냈다. 두 축이 같은 Major(묶은 짧은 옵션 속의 `-g`)를 따로 찾았다.

고친 것:
- Major(두 축). `rg -ig.env`·`-ug .env`·`-sg .env`·`-Ig .env`를 지나보냈다. `_rg_glob_values`가 짧은 옵션 묶음을 rg처럼 앞에서 읽어 값을 먹는 옵션에서 멈추게 했다. `_option_values`에 더했던 붙여 쓴 짧은 옵션 갈래는 되돌렸다(이제 grep의 긴 옵션만 쓴다).
- Major(명세). 빼는 glob을 대소문자 없이 견줘 `-g .env -g '!.ENV'`와 `-uu -g '!.ENV'`를 지나보냈다(뒤의 것은 옛 판의 구멍). `_rg_excludes_env`가 `fnmatchcase`로 가려 본다.
- Minor(명세·표준). 거짓 양성(`-g .ENV`, `-g ./.env`, `-g .env -g '!{.env}'`, `--iglob '!.ENV'`, Grep 도구의 `./.env`·`.env !.env`·`src/** tests/**`, 표에 없는 값 옵션 뒤의 `-rg .env`)을 모듈 독스트링에 적고 막는다고 단언하는 시험으로 고정했다.
- Minor(표준). 시험의 rg 호출에 `stdin=subprocess.DEVNULL`을 줬다. `sub/` 항목의 모순된 서술을 `_is_root`의 실제 동작(`..` 없는 상대 경로는 루트가 아니다)으로 고쳤다.
- Minor(명세). ADR 0038의 `{.env}` 서술을 고쳤다. Grep 도구의 `{.env}`는 PR #349가 이미 고쳤고(일지 2026-10-22-11의 명세 Minor 3), 이번에 닫은 것은 Grep 도구의 나누기와 rg `-g`가 무시 규칙을 이기는 길이다.
- Minor(명세). 수용 기준의 "28개가 빨갰다"를 다시 셌다. 고치기 전 판(975bf04c)에 통째로 돌려주는 `grep_tool_globs` 껍데기를 붙인 스크래치 사본에 반영 뒤의 시험을 대니 80개 가운데 29개가 빨갰다(스크래치 스크립트로 손으로 봤다). 반영에서 더한 14개를 빼면 15개로, 명세 축이 센 수와 같다. 28은 다시 셀 수 없어 지웠다.
- Minor·Nit(표준). ADR의 빈 `## 이력` 제목을 지웠고, "사용자가 거부했다"를 "두 안을 견주어 이 결정을 골랐다"로, 러너를 `ubuntu-latest`가 가리키는 24.04로 적었다. Grep 도구의 중괄호·쉼표가 섞인 꼴은 미루어 본 것이라고 ADR Consequences에 적었다. 시험의 Grep 도구 인자 만들기를 `_grep_tool_args`로 뽑았다.

남긴 것:
- Nit(표준). `_rg_sweeps_root`의 `_paths_reach_root` 반환 두 번. 두 갈래의 조건이 달라 합치면 읽기가 어려워진다.
- Nit(명세). 대기열 422는 표를 `tests/tools/test_hook_env_read.py`에 두라고 했는데 새 파일에 뒀다. 실제 rg를 띄우는 시험을 순수 함수 시험과 가르려는 것이고 뜻은 같다.
- Minor(표준). 헌법 판 3.0.52가 `proposed` ADR을 가리킨다. 승인 전에 병합하지 않는 순서로 닫는다.

ADR 0038을 셀프 리뷰를 반영한 뒤 보이고 승인을 물었다.

> 사용자: 승인 (Recommended) — "상태를 accepted로 바꾸고 커밋·PR·병합까지 진행합니다. 앞으로 pytest는 PATH에 rg도 claude도 없는 기계에서 그 시험이 실패합니다(_rg_command 의 pytest.fail 갈래)."

다시 돌린 명령: 두 시험 파일 259개 초록, `uv run ruff check .`·`uv run ruff format --check .` 초록, `uv run python tools/run_checks.py` 종료 0(pytest 394.2초, web-verify 357.4초를 포함해 모두 Passed). 커밋의 pre-commit 결과는 PR 본문에 적는다.

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 문장):
- "rg 의 `-g` 는 대소문자를 가려, Windows 에서도 `-g .env -g '!.ENV'` 가 `.env` 를 읽었다"(`_rg_excludes_env`)
- "rg 는 묶음을 앞에서부터 읽어 값을 먹는 옵션을 만나면 그 뒤를 값으로 읽는다(`-tg` 의 `g` 는 `-t` 의 값이다)"(`_rg_glob_values`)
- "`..` 가 없는 상대 경로는 루트로 보지 않는다"(모듈 독스트링)
- "다른 일로 그 함수를 고치던 PR #349의 셀프 리뷰가 잡아 그 PR에서 고쳤다"(ADR 0038)
- "손으로 본 꼴은 넷이고 … 중괄호와 쉼표가 섞인 다른 꼴(`a,{.env}`)도 쉼표로 나누지 않는다고 미루어 본다"(ADR 0038)

## 인계

이 세션의 제목은 `chore/007-env-read-glob-matches-rg`였다. 셀프 리뷰 직전에 컨텍스트 문턱을 넘어 인계 계기가 왔고, 곁 세션이 아니어서(`get_session`에 `parentSessionId` 없음) 넘긴다.

지시문:

```
다음 작업: harness 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md 를 잇는다. 구현을 마친 커밋 전 변경을 셀프 리뷰하고 ADR 0038 승인을 받은 뒤 커밋·PR·병합한다
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리다. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 422를 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md로 쓰고 한다
브랜치: chore/007-env-read-glob-matches-rg
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: .scratch/harness/issues/007-env-read-glob-matches-rg.md, docs/adr/0038-env-read-hook-is-tested-against-real-ripgrep.md, docs/journal/2026-10-23-22-env-read-glob-rg.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 기점 origin/main 의 merge-base)부터 한다. 리뷰를 반영한 뒤 ADR 0038 초안(status proposed)을 사용자에게 보이고 승인받는다. origin/main 이 앞서 있어 커밋 전에 sibling_overlap 으로 일지 번호를 다시 본다. docs/journal/2026-10-23-22-env-read-glob-rg.md
확인할 선행 조건: 주 체크아웃은 main이다. 형제 세션(003~006, 008)이 같은 날 나란히 돈다
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-22T23:16:42Z

## 인계 2(커밋 뒤)

이 세션의 제목은 `chore/007-env-read-glob-matches-rg`였다. 인계로 열려 셀프 리뷰를 반영하고 ADR 0038을 승인받았으며, 티켓을 done으로 닫고 커밋했다(pre-commit 통과, 이 일지의 인계 2 절은 그 커밋 뒤에 쓴 것이라 커밋하지 않았다). 커밋 뒤에 컨텍스트 문턱을 넘어 인계 계기가 왔고, 곁 세션이 아니며(`get_session`에 `parentSessionId` 없음), 넘겨받은 경계(셀프 리뷰 직전)와 지금 경계가 달라 넘긴다. 커밋 통계에서 `docs/constitution/README.md`가 `rewrite (96%)`로 찍혔는데, 한 줄이 1만5천 자가 넘는 파일의 그 한 줄만 바뀐 것이었다(`git diff --stat`은 1줄 더함·1줄 지움).

지시문:

```
다음 작업: harness 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md 를 잇는다. 셀프 리뷰를 반영하고 ADR 0038 승인을 받아 커밋했다. origin/main 을 합치고 PR 직전 리뷰, PR, 봇 회차, 병합을 한다
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리다. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 422를 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md로 쓰고 한다
브랜치: chore/007-env-read-glob-matches-rg
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: .scratch/harness/issues/007-env-read-glob-matches-rg.md, docs/adr/0038-env-read-hook-is-tested-against-real-ripgrep.md, docs/journal/2026-10-23-22-env-read-glob-rg.md
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰 반영, ADR 0038 승인(accepted), 티켓 done 까지 담은 커밋이 있고 푸시하지 않았다. 이 일지의 "인계 2" 절은 커밋하지 않았으니 다음 커밋에 싣는다. 남은 단계는 origin/main 합치기(커밋 전 sibling_overlap 으로 일지·ADR·헌법 판 번호 다시 보기), PR 직전 리뷰(CodeRabbit CLI 가 돌지 못하면 /security-review 와 bug-perf-review. 밀 주장은 일지 셀프 리뷰 절의 "PR 직전 리뷰에 밀 주장" 목록), PR(본문의 검사 결과는 일지의 다시 돌린 명령 줄), 봇 회차, 워크트리에서 병합. docs/journal/2026-10-23-22-env-read-glob-rg.md
확인할 선행 조건: 주 체크아웃은 main이다. 형제 세션(003~006, 008)이 같은 날 나란히 돈다
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-22T23:54:59Z

## PR 직전 리뷰(새 세션)

> 사용자: 대기열 422를 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md로 쓰고 한다

origin/main(d0e696c9)을 충돌 없이 합쳤고 `sibling_overlap.py`는 번호 겹침 없음이었다. CodeRabbit CLI는 `coderabbit auth status`가 `Seat: not assigned`라 돌지 못해 대체 둘을 나란히 돌렸다.

- `/security-review`: 후보 하나(MEDIUM). `_RG_VALUE_OPTIONS`에 `-r`(바꿀 글)이 없어 `-rg` 의 `g` 를 `-g` 로 읽고, 뒤의 `^` 를 `.env` 가 아닌 고르는 glob 으로 보아 `rg -uu -rg ^ .` 를 지나보냈다. main 은 막던 명령이라 이 브랜치가 연 구멍이다. 오탐 거르기 서브태스크가 두 판을 불러 보고 실제 rg 로 숨김 파일의 줄이 찍히는 것을 재현했지만 확신도를 7로 매겨, 명령의 기준(8 미만은 뺀다)으로는 보고에서 빠졌다. 같은 구멍을 bug-perf-review 도 Major 로 냈으므로 고쳤다.
- bug-perf-review: 유효 4(Major 2, Minor 2), 보류 1(Nit). 밀 주장 다섯은 모두 맞다고 봤다(1·2·5는 실제 rg 14.1.1 로, 3은 코드로, 4는 일지 2026-10-22-11 로).

고친 것:
- Major(두 리뷰). `_RG_VALUE_OPTIONS` 를 `rg --help` 의 값 옵션 전부로 채웠다(`-r`·`-d`·`--replace`·`--max-filesize`·`--ignore-file`·`--pre-glob` 등, `--maxdepth` 별칭은 rg 가 받는 것을 손으로 봤다). ag·ack 의 `-r` 는 값을 먹지 않는 재귀라 그 둘은 옛 표(`_AG_VALUE_OPTIONS`)를 쓴다. `-rg .env` 를 거짓 양성으로 적은 독스트링 항목과 시험은 뜻을 잃어 지우고, `rg -uu -rg <패턴> .` 과 `-r X -g .env`·`-d 3 -g .env`·`--replace`·`--max-filesize` 꼴을 실제 rg 와 맞대는 표에 더했다.
- Major(bug-perf-review). `_rg_excludes_env` 가 마지막 `/` 앞을 떼고 보아 `-g .env -g '!sub/.env'`(루트의 `.env` 를 읽는다)와 `-uu -g '!/.env'`(`sub/.env` 를 읽는다)를 지나보냈다. 앞의 `**/` 를 뗀 뒤 `/` 가 남으면 빼지 않는다고 본다. 그 거짓 양성(`!/.env* !sub/.env*`)을 넓게 막는 표에 더했다.
- Minor(bug-perf-review). `_is_root` 가 `./.`·`.//`·`././` 를 루트로 보지 않았다. 정규화해 `.` 이면 루트로 본다. 시험이 rg 출력 경로를 `posixpath.normpath` 로 펴게 고쳤다(경로를 준 rg 는 `./.\.env` 처럼 그 경로를 머리에 붙인다).
- Minor(bug-perf-review). 시험의 rg 호출에 `--no-config` 를 줘 `RIPGREP_CONFIG_PATH` 에 흔들리지 않게 했다.

새 시험 열하나는 커밋된 판(71cfefd0)의 훅으로 되돌려 돌리니 빨갰다(`sub/..` 는 옛 판도 `..` 로 막아 초록). 스크래치패드에 고친 훅을 옮겨 두고 되돌렸다가 복원했다.

남긴 것:
- Nit·보류(bug-perf-review). Grep 도구가 `a,{.env}` 를 쪼개지 않는다는 규칙은 손으로 본 넷에서 미룬 것이다. ADR 0038 Consequences 가 이미 어림이라고 적었다. 닫으려면 Claude Code 의 Grep 도구로 `a,{.hid}` 를 불러 봐야 한다.
- 보안 서브태스크가 확신도 미달로 뺀 `{.env, x}`(main 은 막고 이 브랜치는 `{.env,`·`x}` 로 나눠 지나보낸다). 나눈 조각을 받은 rg 가 `.env` 를 읽지 않는 것은 `_GREP_TOOL_SAME` 에 더해 실제 rg 로 봤다(초록). Grep 도구가 그렇게 나눈다는 쪽은 위 Nit 과 같은 어림이다.
