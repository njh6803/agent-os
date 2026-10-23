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

## 인계 3(PR 연 뒤)

이 세션의 제목은 `chore/007-env-read-glob-matches-rg`였다. 인계 2 로 열려 origin/main 을 합치고 PR 직전 리뷰를 반영해 커밋했다(`f2058cdd`, pre-commit 통과: pytest 727.4초, web-verify 539.7초). 커밋 뒤에 온 인계 계기는 넘겨받은 경계(`커밋 뒤`)와 같아 넘기지 않았다. 푸시하고 PR [#366](https://github.com/njh6803/agent-os/pull/366)을 열었고, 그 직후 `PR 연 뒤` 경계에서 인계 계기가 왔다. 곁 세션이 아니다(`get_session` 에 `parentSessionId` 없음). `@coderabbitai review` 코멘트는 아직 남기지 않았다. 이 절은 커밋하지 않았다.

푸시 뒤 자동 보안 리뷰(security-guidance 플러그인)가 `tools/hook_env_read.py` 에 둘을 냈다. 코드로 읽어 둘 다 거짓 음성으로 본다(실제 rg 로는 재지 않았다).
- HIGH. 경로 없는 묶은 옵션. `rg -ig .env KEY` 는 `_positionals` 가 `-ig` 의 값을 몰라 `.env` 를 패턴, `KEY` 를 경로로 읽어 루트가 아니라고 지나보낸다. rg 는 `-i -g .env` 로 읽고 루트를 훑는다. `_rg_glob_values` 와 같은 묶음 읽기로 위치 인자를 고르게 하고, 경로 없는 `rg -ig .env {m}`·`rg -ug .env {m}` 를 `_BASH_RG_SAME` 에 더한다. 316행 근처의 파일 인자 판정도 같은 위치 인자를 쓴다.
- MEDIUM. 일부만 빼는 빼기. `-g '.env*' -g '!.env'` 는 `.env.local` 을 읽는데 `_rg_excludes_env` 가 견본 둘 가운데 하나만 맞아도(`any`) 뺀다고 본다. 견본 모두(`all`, `.env`·`.env.local`·`.env.production`)를 빼야 뺀 것으로 본다. `_rg_sweeps_root` 의 `!` 판정도 같은 함수다. `rg -g '.env*' -g '!.env' {m} .` 와 `rg -uu -g '!.env' {m} .` 를 표에 더한다.

지시문:

```
다음 작업: harness 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md 를 잇는다. PR #366 을 열었다. 봇 회차(CodeRabbit 요청부터), 반영, 워크트리에서 병합을 한다
다음 단계: PR 반영·병합
어디서: 새 세션. 같은 브랜치·워크트리다. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 422를 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md로 쓰고 한다
브랜치: chore/007-env-read-glob-matches-rg
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: .scratch/harness/issues/007-env-read-glob-matches-rg.md, docs/adr/0038-env-read-hook-is-tested-against-real-ripgrep.md, docs/journal/2026-10-23-22-env-read-glob-rg.md
이어받을 상태: 인계: PR 연 뒤. PR #366(https://github.com/njh6803/agent-os/pull/366)을 열었고 푸시까지 했다(머리 f2058cdd). PR 직전 리뷰(/security-review, bug-perf-review)는 반영했고 결과는 PR 체크리스트에 있다. 푸시 뒤 자동 보안 리뷰(security-guidance 플러그인)의 지적 둘을 아직 고치지 않았으니 먼저 고쳐 커밋·푸시한다(일지 "인계 3" 절의 푸시 뒤 보안 리뷰). 첫 `@coderabbitai review` 코멘트를 아직 남기지 않았으니 그 푸시 뒤에 남기고, 순서 1의 2(봇 회차)대로 대기를 띄운다. 이 일지의 "인계 3" 절은 커밋하지 않았으니 다음 커밋에 싣는다. docs/journal/2026-10-23-22-env-read-glob-rg.md
확인할 선행 조건: 주 체크아웃은 main이다. 형제 세션(003~006, 008)이 같은 날 나란히 돈다
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-23T00:29:17Z

## 푸시 뒤 보안 리뷰 반영(새 세션, 커밋 전)

> 사용자: 대기열 422를 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md로 쓰고 한다

인계 3 으로 열려 워크트리에 들어왔다. 지적 둘을 시험부터 고쳤다(새 시험 일곱이 빨갰다가 초록, 두 시험 파일 284개 초록).

- HIGH(묶은 짧은 옵션). `_positionals` 를 `_option_width` 로 getopt 처럼 읽게 했고(`_short_value_option` 을 뽑아 래퍼와 함께 쓴다), `_pattern_given_by_option` 도 묶음 속의 `-e`·`-f`(`-ie KEY`)를 같이 읽는다. 위치 인자만 바꾸면 `grep -ie KEY .env` 의 `.env` 를 패턴으로 버리게 되어 둘을 함께 바꿨다. `rg -ig .env {m}`·`rg -ug .env {m}`·`rg -ig.env {m}` 을 실제 rg 표에, `grep -ie`·`rg -ie`·`sed -ne`·`rg -ig '*' … .env` 를 막는 표에 더했다.
- MEDIUM(일부만 빼는 빼기). 지적이 제안한 `all` 로만 바꾸면 `-g .env -g '!.env'` 가 거짓 양성이 된다고 코드로 읽었다. 그래서 rg 는 견본(`_ENV_SAMPLES`: `.env`·`.env.local`·`.env.production`)마다 맞는 마지막 glob 으로 가르게 `_rg_sweeps_root` 를 `_rg_reads`·`_rg_selects`·`_rg_excludes` 로 다시 지었다(`_rg_globs_include_env`·`_rg_excludes_env` 는 없어졌다). 같은 견줌인 grep 의 `--exclude` 도 `_excludes_every_env`(견본 모두)로 바꿨고, 그래서 `grep -rn --exclude .env KEY .` 는 이제 막는다(옛 시험의 막지 않는 표에서 막는 표로 옮겼다). 견본을 하나씩 모두 뺀 뒤 남은 꼴(`.env.staging`)은 못 보는 것에 적고 시험으로 고정했다.

반영으로 새로 쓴 문장(셀프 리뷰와 PR 봇 회차에 밀 주장): `_excludes_every_env` 독스트링의 "`grep -r --exclude .env` 를 지나보냈다"(GNU grep 으로 재지 않았고 코드로 읽었다), `_rg_reads` 독스트링의 "맞는 glob 이 없으면 고르는 glob 이 하나도 없고 무시·숨김 규칙을 모두 끈 때만 읽는다".

`/code-review` 를 부른 직후 컨텍스트 문턱을 넘어 `셀프 리뷰 직전` 경계에서 인계 계기가 왔다. 곁 세션이 아니다(`get_session` 에 `parentSessionId` 없음). 띄웠던 `tools/run_checks.py` 는 멈췄다(결과 없음).

## 인계 4(셀프 리뷰 직전)

이 세션의 제목은 `chore/007-env-read-glob-matches-rg`였다.

지시문:

```
다음 작업: harness 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md 를 잇는다. PR #366 의 푸시 뒤 보안 리뷰 지적 둘을 고친 미커밋 변경을 셀프 리뷰하고 커밋·푸시한 뒤 봇 회차, 반영, 워크트리에서 병합을 한다
다음 단계: PR 반영·병합
어디서: 새 세션. 같은 브랜치·워크트리다. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 422를 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md로 쓰고 한다
브랜치: chore/007-env-read-glob-matches-rg
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: .scratch/harness/issues/007-env-read-glob-matches-rg.md, docs/adr/0038-env-read-hook-is-tested-against-real-ripgrep.md, docs/journal/2026-10-23-22-env-read-glob-rg.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 기점 HEAD f2058cdd, 범위 tools/hook_env_read.py 와 tests/tools/test_hook_env_read.py·test_hook_env_read_rg.py)부터 한다. 반영 뒤 검증 명령을 돌리고 커밋(이 일지의 인계 3, 푸시 뒤 보안 리뷰 반영, 인계 4 절도 싣는다)한다. grep `--exclude .env` 를 막게 바꾼 것은 PR 본문이 말하지 않은 결정이라 순서 1의 1대로 푸시 전에 PR 본문을 고친 뒤 푸시하고, 첫 `@coderabbitai review` 코멘트를 남겨 순서 1의 2(봇 회차)대로 대기를 띄운다. docs/journal/2026-10-23-22-env-read-glob-rg.md
확인할 선행 조건: 주 체크아웃은 main이다. 형제 세션(003~006, 008)이 같은 날 나란히 돈다
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-23T00:45:36Z

## 셀프 리뷰(새 세션, 기점 f2058cdd, 커밋 0·바뀐 파일 4·미추적 0)

> 사용자: 대기열 422를 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md로 쓰고 한다

표준 축(sonnet·high)은 Major 0, Minor 3, Nit 2를, 명세 축은 Major 1, Minor 1, Nit 2를 냈다. 두 축이 같은 거짓 양성(grep `--exclude` 여럿을 합쳐야 모두 빼는 꼴)을 따로 찾았고, 둘 다 GNU grep 3.1 로 손으로 봤다.

고친 것:
- Major(명세)·Minor(표준). `_excludes_every_env` 가 값마다 견본 모두를 요구해 `grep -rn --exclude .env --exclude '.env.*' KEY .` 를 새로 막았다(옛 판은 지나보냈고 grep 도 `.env` 꼴을 읽지 않는다). 값들을 받아 견본마다 빼는 값이 하나라도 있는지 보게 했다. rg 는 이미 견본마다 봐 같은 꼴을 지나보내므로 두 판정이 같은 모양이 됐다. 그 둘을 막지 않는 표에, rg 의 `-uu -g '!.env' -g '!.env.*'` 를 실제 rg 표에 더했다.
- Minor(두 축). 못 보는 것의 견본 항목을 견본 밖의 `.env` 꼴만 고르거나 남기는 glob 으로 넓히고 예 셋(견본을 하나씩 뺀 빼기, `--exclude '.en*[!g]'`, `rg -g .env.staging`)을 들었다. `grep -rn --exclude '.en*[!g]' KEY .`·`rg -uu -g '!.en*[!g]' KEY .`·`rg -g .env.staging KEY` 를 못 보는 것 시험에 고정했다.
- Minor(표준, Duplicated Code). `_rg_glob_values` 의 묶음 읽기가 `_short_value_option` 을 부르게 했다.
- Nit(명세 둘). `_rg_reads` 독스트링에 `-t` 조건을 더했고, `_ENV_SAMPLES` 주석이 grep·rg 의 빼기를 각자의 함수로 가리키게 고쳤다.

남긴 것:
- Nit(표준). `_matches_env` 를 Middle Man 으로 봤지만 부르는 자리가 둘(`_glob_reaching_env` 의 갈래, `_reaches_env`)이라 둔다.
- 명세 축이 범위 밖으로 낸 옛 결함 셋(`rg -uueKEY_X` 는 붙은 값에 `_` 가 들어 `_SHORT_CLUSTER` 가 맞지 않아 `-uu` 로 세지 않음, `grep -- -KEY .env` 의 `--` 뒤, `grep -f .env x` 의 패턴 파일). 이 세션이 훅 함수를 불러 셋 다 지나가는 것을 봤다(`rg -uueKEY` 는 막는다). 명세 축은 옛 판도 지나보낸다고 했고, 이 PR 이 연 구멍이 아니다. 회고 후보로 넘긴다.

반영으로 새로 쓴 문장(PR 봇 회차에 밀 주장): `_excludes_every_env` 독스트링의 "GNU grep 3.1 로 `--exclude .env` 가 `.env.local` 을 읽고 둘을 합치면 읽지 않는 것을 손으로 봤다"(두 축의 서브에이전트가 봤다), 모듈 독스트링의 "셋 다 `.env.staging` 을 읽는다"(첫째는 명세 축이 실제 rg 로, 둘째·셋째는 두 축이 grep·rg 로 봤다).

다시 돌린 명령: 두 시험 파일 291개 초록, 바뀐 파일의 `ruff check`·`ruff format --check` 초록. 나머지 손으로 치는 검증은 커밋의 pre-commit 으로 갈음한다.

첫 커밋 시도의 pre-commit 이 셋을 냈다. 변이 표 `.scratch/harness/probes/env_read_wrappers_mutations.toml` 의 두 변이(짧은 옵션 묶음, 긴 옵션의 값)가 고친 `_option_width` 의 옛 원문을 가리켜 그 원문을 새 코드로 옮겼고 `tools/mutate.py` 로 다시 돌렸다. pytest 의 `test_probe_kit.py` 배출 시험과 `test_interrupt.py` 의 닫기 시험이 빨갰는데 두 시험만 홀로 돌리니 초록이었다(이 변경이 닿지 않는 시험이고, 다른 세션과 겹친 부하로 본다). 인용 대조 경고는 이 절의 인용 하나를 따옴표를 떼어 고쳤다. 앞 절(푸시 뒤 보안 리뷰 반영)의 인용 둘은 그때의 독스트링 원문이라 두었다.

## 인계 5(커밋 뒤)

이 세션의 제목은 `chore/007-env-read-glob-matches-rg`였다. 인계 4 로 열려 셀프 리뷰를 반영하고 커밋했다(`e1550a0b`, pre-commit 통과: pytest 583.3초, web-verify 455.4초). 커밋 뒤에 인계 계기가 왔고, 넘겨받은 경계(`셀프 리뷰 직전`)와 달라 넘긴다. 곁 세션이 아니다(`get_session` 에 `parentSessionId` 없음). PR 본문은 푸시 전에 `gh pr edit` 으로 고쳤다(견본마다 가르기, 푸시 뒤 보안 리뷰 반영, grep `--exclude .env` 를 이제 막는다는 결정, 남긴 위험 둘, 체크리스트의 셀프 리뷰와 pre-commit 수치). 아직 푸시하지 않았다. 이 절은 커밋하지 않았다.

변이 표를 돌리는 동안 백그라운드 보안 리뷰(security-guidance)가 `_option_width` 를 `index += 1` 로 바꾼 diff 를 MEDIUM 으로 냈다. `tools/mutate.py` 가 시험 도중 넣은 변이를 본 것이다. 끝난 뒤 `git diff` 에 남은 변이가 없었고 `_positionals` 는 `_option_width` 를 쓴다. 고칠 것이 없다.

지시문:

```
다음 작업: harness 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md 를 잇는다. PR #366 의 푸시 뒤 보안 리뷰 반영과 그 셀프 리뷰를 커밋했다(e1550a0b). 푸시하고 봇 회차, 반영, 워크트리에서 병합을 한다
다음 단계: PR 반영·병합
어디서: 새 세션. 같은 브랜치·워크트리다. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 422를 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md로 쓰고 한다
브랜치: chore/007-env-read-glob-matches-rg
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: .scratch/harness/issues/007-env-read-glob-matches-rg.md, docs/adr/0038-env-read-hook-is-tested-against-real-ripgrep.md, docs/journal/2026-10-23-22-env-read-glob-rg.md
이어받을 상태: 인계: 커밋 뒤. 커밋 e1550a0b 까지 했고 푸시하지 않았다. PR #366(https://github.com/njh6803/agent-os/pull/366) 본문은 이 커밋의 범위로 이미 고쳤으니 바로 푸시하고, 첫 `@coderabbitai review` 코멘트를 남겨 순서 1의 2(봇 회차)대로 대기를 띄운다. 이 일지의 "인계 5" 절은 커밋하지 않았으니 다음 커밋(봇 회차 반영이나 회고를 실은 일지)에 싣는다. 셀프 리뷰가 범위 밖으로 넘긴 옛 거짓 음성 셋(`grep -f .env x` 등)은 일지 셀프 리뷰 절의 남긴 것에 있고 회고 후보다. docs/journal/2026-10-23-22-env-read-glob-rg.md
확인할 선행 조건: 주 체크아웃은 main이다. 형제 세션(003~006, 008)이 같은 날 나란히 돈다
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-23T01:38:57Z

## 푸시와 둘째 푸시 뒤 보안 리뷰 반영(새 세션, 커밋 전)

> 사용자: 대기열 422를 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md로 쓰고 한다

인계 5 로 열려 워크트리에 들어왔다. 푸시가 `hook_push_behind_main` 에 막혀(origin/main 이 2커밋 앞) origin/main(750761b9, harness 005 와 model-rerun 02)을 충돌 없이 합쳤고 `sibling_overlap.py` 는 번호 겹침 없음이었다. `tools/run_checks.py` 는 pytest 하나를 뺀 아홉이 Passed 였고, pytest 는 4725 가운데 `test_probe_kit.py` 의 배출 시험 하나가 빨갰다. 그 파일만 홀로 돌리니 15개 초록이었다(인계 4 절의 첫 커밋 시도와 같은 시험, 다른 세션과 겹친 부하로 본다). 린트 둘 초록. 푸시(b471dc75)하고 `@coderabbitai review` 를 남겼다. `wait_ci.py` 는 `끝: 모두 통과. CodeRabbit: Review rate limited` 로 끝났다(CodeRabbit 회차는 세지 않는다).

푸시 뒤 자동 보안 리뷰(security-guidance)가 `tools/hook_env_read.py` 에 MEDIUM 셋을 냈다. 훅 함수로 셋 다 지나가는 것을 봤고, 둘은 실제 도구로 봤다(스크래치 스크립트, git init 한 임시 폴더의 gitignore 된 가짜 `.env`).
- rg 고르는 glob 의 역슬래시. Windows 의 rg 14.1.1(Claude Code 실행 파일)이 `-g '\.env'` 로 `.env` 를 읽었고 실제 rg 표에 더한 `-g '\.e\nv'` 도 읽었다. `_rg_selects` 가 이스케이프를 지운 글과 `\` 를 `/` 로 바꾼 글도 본다(`_ESCAPE`). 빼는 쪽의 `!\.env*` 는 풀지 않아 막는다(거짓 양성, 모듈 독스트링과 `_BASH_RG_STRICTER`).
- grep `--exclude` 의 대소문자. GNU grep 3.1 이 `--exclude='.ENV*'` 로 `.env` 를 읽었다. `_excludes_every_env` 가 대소문자를 가리는 `_env_samples_excluded` 를 쓴다.
- ag·ack 의 값 옵션 표. 이 PC 에 둘 다 없어 재지 않았다. ag 의 `-t`(--all-text)·`-f`(--follow)를 값 옵션으로 읽어 `ag -t KEY .env` 를 지나보냈다(훅 함수로 봤다). 문서가 값을 꼭 받는다고 적은 것만 든 `_AG_VALUE_OPTIONS`·`_ACK_VALUE_OPTIONS` 로 갈랐고, rg 표는 홀로 섰다. 모르면 빼는 쪽이 막는 쪽이라는 판단을 표 위 주석에 적었다.
새 시험 일곱(`ag -it`·`ag -t`·`ag -ft`·`ack -t` 막기, `grep --exclude='.ENV*'` 막기, 실제 rg 표의 `\.env`·`\.e\nv`)과 거짓 양성 하나. 여섯이 빨갰다가(`ag -ft` 는 원래 막혔다) 두 시험 파일 299개 초록, 바뀐 세 파일의 ruff 둘 초록.

claude-review 둘째 회차(02:01, Minor 3·Nit 2)와, 처리 기록이 없던 첫 회차(00:29, Minor 2·Nit 2)를 읽었다. 둘째 회차라 Minor·Nit 은 PR 코멘트에 보류 이유를 남기고 병합한다(아직 남기지 않았다). 첫 회차는 지적마다 판단했다.
- 고친 것: 첫 회차 Minor(불리언 플래그). 그 함수는 이미 없었지만 이번 반영이 `_env_samples_matched(…, case_sensitive=…)` 로 같은 꼴을 다시 지어, 함수 둘로 나눴다. 첫 회차 Nit(ag·ack 표 주석의 방향)은 표를 가르며 풀렸다.
- 남길 것: 첫 회차 Minor(짧은 옵션 파서가 `_SHORT_CLUSTER` 와 `_short_value_option` 둘)와 둘째 회차 Minor(`_rg_glob_values` 와 `_positionals` 의 getopt 읽기 중복), 둘째 회차 Minor(`_rg_reads` 의 `unrestricted` 불리언), 두 회차의 독스트링 나누기·이력 덜기, 둘째 회차 Nit(시험의 `args` 거르기 헬퍼). 보안 훅의 판정 경로 전체를 다시 짜는 리팩터링이라 이 PR 에서 새 어긋남을 낼 위험이 크다고 봤다. 뒤로 넘기면 일지 "다음"이나 회고 후보에 적는다.

반영으로 새로 쓴 문장(셀프 리뷰에 밀 주장): `_rg_selects` 독스트링의 "rg 14.1.1 이 Windows 에서도 `-g '\.env'` 와 `-g '\.e\nv'` 로 `.env` 를 읽었는데"(첫째는 스크래치 스크립트로, 둘째는 실제 rg 시험으로 봤다), `_excludes_every_env` 독스트링의 "GNU grep 3.1 이 `--exclude='.ENV*'` 로 `.env` 를 읽었는데", `_AG_VALUE_OPTIONS` 위 주석의 "값을 꼭 받는다고 문서(ag 와 ack 의 man 페이지)가 적은 것만 둔다"(man 페이지를 이 세션에서 열지 않았고 기억에 기댄 것이다. 셀프 리뷰가 원문으로 잰다), 모듈 독스트링의 "빼는 glob 의 역슬래시(`!\.env*` 는 rg 가 이스케이프로 읽어 `.env` 꼴을 빼지만 풀어 보지 않는다)".

`/code-review` 를 부른 직후 컨텍스트 문턱을 넘어 `셀프 리뷰 직전` 경계에서 인계 계기가 왔다. 곁 세션이 아니다(`get_session` 에 `parentSessionId` 없음). 띄운 대기는 끝났다.

## 인계 6(셀프 리뷰 직전)

이 세션의 제목은 `chore/007-env-read-glob-matches-rg`였다.

지시문:

```
다음 작업: harness 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md 를 잇는다. PR #366 의 둘째 푸시 뒤 보안 리뷰 지적 셋과 claude-review 첫 회차 Minor 를 고친 미커밋 변경을 셀프 리뷰하고 커밋·푸시한 뒤 봇 회차, 반영, 워크트리에서 병합을 한다
다음 단계: PR 반영·병합
어디서: 새 세션. 같은 브랜치·워크트리다. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 422를 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md로 쓰고 한다
브랜치: chore/007-env-read-glob-matches-rg
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: .scratch/harness/issues/007-env-read-glob-matches-rg.md, docs/adr/0038-env-read-hook-is-tested-against-real-ripgrep.md, docs/journal/2026-10-23-22-env-read-glob-rg.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 기점 HEAD b471dc75, 범위 tools/hook_env_read.py 와 tests/tools/test_hook_env_read.py·test_hook_env_read_rg.py)부터 한다. 밀 주장은 일지 "푸시와 둘째 푸시 뒤 보안 리뷰 반영" 절의 목록이다(ag·ack man 페이지 주장은 원문으로 잰다). 반영 뒤 커밋(이 일지의 인계 5·6 절도 싣는다)하고, ag·ack 표를 가른 것은 PR 본문이 말하지 않은 결정이라 순서 1의 1대로 푸시 전에 PR 본문을 고친 뒤 푸시한다. claude-review 둘째 회차(02:01)의 Minor·Nit 은 보류 이유를 PR 코멘트에 남기고, 뒤로 넘기는 리팩터링(옵션 파서 하나로 합치기 등)은 일지 "다음"이나 회고 후보에 적는다. 푸시 뒤 `@coderabbitai review` 를 남기고 순서 1의 2대로 대기를 띄운다. docs/journal/2026-10-23-22-env-read-glob-rg.md
확인할 선행 조건: 주 체크아웃은 main이다. 형제 세션(003~006, 008)이 같은 날 나란히 돈다
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-23T02:17:05Z

## 셀프 리뷰(새 세션, 기점 b471dc75, 커밋 0·바뀐 파일 4·미추적 0)

> 사용자: 대기열 422를 티켓 .scratch/harness/issues/007-env-read-glob-matches-rg.md로 쓰고 한다

인계 6 으로 열려 워크트리에 들어왔다. 두 축을 띄우기 전에 밀 주장 가운데 ag·ack man 페이지 주장을 원문으로 쟀다. man 페이지(`doc/ag.1.md`, ack 3 의 POD)와 함께 파서의 정의(ag `src/options.c`, ack 3 `lib/App/Ack/ConfigLoader.pm`)를 받아 읽었다(세션 스크래치패드, 2026-10-23).

- 반영 전 판의 주장은 틀렸다. ack 3 의 man 페이지는 `-A NUM`·`-g PATTERN` 으로 적지만 파서는 `A|after-context:-1`(값이 선택인 숫자)이고 `g` 는 값 없는 플래그다. 그 판의 ack 표가 `-A`·`-B`·`--after-context`·`--before-context`·`-g` 를 값 옵션으로 두어, 훅 함수가 `ack -A ANTHROPIC .env`·`ack -B ANTHROPIC .env`·`ack --after-context ANTHROPIC .env` 를 지나보냈다(훅 함수로 봤다. ack 는 이 PC 에 없어 실제로는 재지 않았고, ack 가 `KEY` 를 패턴으로 `.env` 를 파일로 읽는다는 것은 파서 정의와 Getopt::Long 의 값이 선택인 숫자 규칙에서 읽은 것이다). b471dc75 의 판도 같은 꼴(rg 표를 함께 쓴 `-A`·`-B`)이라 이 PR 이 연 구멍은 아니다.
- 고친 것: 표의 근거를 파서 정의로 바꿨다. ack 표는 값 필수(`=s`·`=i`)인 것과 `--pager`(값이 선택인 문자열. Getopt::Long 이 `-` 로 시작하지 않는 다음 낱말을 먹는다)만 두고 `-t`·`-T`·`--type` 등을 더했다. ag 표는 getopt 문자열의 `A:B:C:` 와 `required_argument` 인 긴 옵션(`--workers`·`--color-*` 등)을 더했다. 막는 표에 ack `-A`·`-B`·`--after-context` 셋을, 막지 않는 표에 `ack -t python .env`(`.env` 가 패턴)를 더했고, 옛 막는 사례 `ack -t ANTHROPIC .env` 는 `-t` 가 값을 먹어 뺐다. 두 시험 파일 302개 초록.

두 축을 띄웠다(표준 sonnet·high, 명세는 본 세션 모델). 표준 축은 Major 1, Minor 4, Nit 2를, 명세 축은 Major 1, Minor 1을 냈다. 밀 주장 넷(`_rg_selects` 의 rg 14.1.1, `_excludes_every_env` 의 GNU grep 3.1, 역슬래시 빼기, ag·ack 표와 파서 소스)은 두 축 모두 맞다고 봤다(rg·grep 은 실제 도구로, 표는 받아 둔 소스 발췌로).

고친 것:
- Major(명세). `--match` 를 ack 표에 넣자 `_pattern_given_by_option` 이 그것을 몰라 `ack --match KEY .env` 를 새로 지나보냈다(기점 판은 막았다. `--match=KEY` 와 `.env --match KEY` 는 기점 판도 지나보냈다). `_pattern_given_by_option` 이 `--match` 를 패턴을 주는 옵션으로 안다. 표 위 주석에 패턴을 주는 값 옵션의 조건을 적었다.
- Major(표준). 역슬래시 이스케이프를 rg 의 고르는 glob 에서만 풀어, Grep 도구 glob `\.e\nv` 와 grep `--include='\.env'`·`--include='.e\nv'` 를 지나보냈다(GNU grep 3.1 이 둘 다 `.env` 를 읽은 것을 표준 축이 손으로 봤다). `_glob_readings` 로 모아 `_rg_selects`·`_reaches_env` 가 함께 쓴다.
- Minor(표준). grep `--exclude='\.env*'` 의 거짓 양성을 모듈 독스트링과 시험에 적었다. 모듈 독스트링의 "문서로만 지었다"를 파서 소스로 고치고 `_ACK_VALUE_OPTIONS` 를 더했다(명세 Minor 와 같은 지적). 표 항목(ag `-G`·`--workers`, ack `--type`·`--pager`)을 막는 표와 막지 않는 표에 고정했다. 주석의 "두 판이 틀렸다"를 "이 표의 앞선 두 판이"로, `_rg_selects` 의 근거를 시험으로 고쳤다.
- 기점 판(b471dc75)의 훅을 스크래치패드에 꺼내 같은 입력을 대니 막을 것 여덟(`ack -A`·`-B`·`--after-context`, `--match` 둘, grep `--include` 둘, Grep 도구 `\.e\nv`)을 지나보냈고 지금 판은 모두 막는다.

남긴 것:
- Nit(표준). `_env_samples_matched` 와 `_env_samples_excluded` 의 leaf 계산이 겹친다. 불리언 인자를 피하려고 나눈 것이라 둔다.
- 범위 밖으로 넘기는 것(회고 후보): ack `--files-from .env` 처럼 값 옵션의 값으로 준 `.env` 를 보지 않는 꼴은 grep `-f .env` 와 같은 부류다(인계 4 의 셀프 리뷰 절 남긴 것). ag·ack 로 경로 없이 저장소를 훑는 꼴을 판정하지 않는 것은 기점 판과 같다.

반영으로 새로 쓴 문장(PR 봇 회차에 밀 주장): `_glob_readings` 독스트링의 "GNU grep 3.1 이 `--include='\.env'`·`--include='.e\nv'` 로 읽었는데"(표준 축이 손으로 봤다), 모듈 독스트링의 "grep 의 `--exclude='\.env*'` 도 grep 이 `.env` 꼴을 빼는데"(같은 축), `_AG_VALUE_OPTIONS` 위 주석의 ack `--pager` 와 Getopt::Long 규칙.

다시 돌린 명령: 두 시험 파일 317개 초록, 바뀐 파일의 ruff 둘 초록(format 하나를 고쳤다), `tools/mutate.py --check` 로 변이 표 원문 확인. 나머지 손으로 치는 검증은 커밋의 pre-commit 으로 갈음한다.
