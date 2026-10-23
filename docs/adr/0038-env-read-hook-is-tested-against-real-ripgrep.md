---
status: accepted
date: 2026-10-23
---

# `.env` 읽기 훅의 glob 판정은 pytest가 실제 rg를 띄워 맞대고, rg는 PATH나 Claude Code 실행 파일에서 찾는다

`tools/hook_env_read.py`는 Grep 도구와 Bash의 rg가 `.env`를 읽으려 하면 막는 훅이다. 그 판정은 하류(rg)가 glob을 읽는 그대로 읽는다는 주장이고, 그 주장을 손으로 본 꼴의 시험으로만 지켜 왔다. 그래서 중괄호를 bash처럼 읽은 판이 Grep 도구의 `{.env}`를 지나보냈고, 다른 일로 그 함수를 고치던 PR #349의 셀프 리뷰가 잡아 그 PR에서 고쳤다(일지 2026-10-22-11, 대기열 422, 239의 3회차. `.claude/rules/tools.md`의 하류 판정 항목을 어겼다). 이 결정을 쓰며 실제 rg와 맞대 보니 구멍이 더 있었다. Grep 도구는 glob 칸을 공백과 쉼표로 나눠 rg의 `--glob` 여럿으로 넘기는데 훅은 통째로 봐 `*.md,.env`·`*.md .env`를 지나보냈다. rg의 `-g`는 무시·숨김 규칙을 이기는데 훅의 Bash 길은 `--hidden`과 `--no-ignore`가 함께 있을 때만 rg를 막아 `rg -g .env KEY .`와 `rg -g '{.env}' KEY .`를 지나보냈다(일지 2026-10-23-33. 2026-10-23 claude 2.1.302의 Grep 도구와 rg 14.1.1로 손으로 봤다). 셀프 리뷰가 이 시험으로 묶은 짧은 옵션 속의 `-g`(`rg -ig .env`)와 대소문자를 가리는 빼기(`-g .env -g '!.ENV'`)를 더 찾았다. **`tests/tools/test_hook_env_read_rg.py`가 `git init`한 임시 폴더에 gitignore 된 가짜 `.env`를 두고, glob 사례마다 실제 rg가 그것을 내는지와 훅의 판정이 같은지 본다. rg는 PATH의 `rg`를 먼저 쓰고, 없으면 PATH의 `claude` 실행 파일을 실행 이름 `rg`로 띄운다. CI의 `python` 잡은 pytest 전에 apt로 ripgrep을 깐다. 어느 rg도 없으면 건너뛰지 않고 실패한다(원칙 II).**

**Claude Code 실행 파일을 쓰는 까닭.** 이 PC의 PATH에는 rg가 없다. Claude Code 실행 파일(`~/.local/bin/claude.exe`)을 실행 이름 `rg`로 띄우면 `ripgrep 14.1.1 (rev 0049fd75eb)`로 답했다(손으로 봤다). Grep 도구는 PATH에 rg가 없는데도 돌므로 그 내장 rg를 쓴다고 본다(어림이다. Claude Code의 코드는 읽지 않았다). 그래서 Claude Code로 일하는 기계라면 따로 깔 것이 없고, 시험이 맞대는 rg가 Grep 도구의 rg와 같은 판이다.

**판.** rg의 판은 저장소가 고정하지 않는다. 이 PC는 Claude Code가 들고 온 14.1.1이고, CI는 러너 이미지의 apt 꾸러미다. `ci.yml`의 `python` 잡은 `ubuntu-latest`이고, 그것이 가리키는 ubuntu-24.04 러너 이미지 20261012.334.1의 README(`actions/runner-images`의 `images/ubuntu/Ubuntu2404-Readme.md`)를 받아 grep하니 ripgrep이 없었다(손으로 봤다). apt가 까는 판은 재지 않았고 ubuntu 24.04의 꾸러미 판(14.1.0)으로 어림한다. 판이 갈려 결과가 갈리면 CI나 Claude Code를 올린 PC가 먼저 본다. 그것이 이 시험이 잡으려는 것이다.

## Considered Options

- **PyPI의 `ripgrep` 휠을 dev 의존성으로 잠근다.** 판을 `uv.lock`이 고정해 두 자리가 같은 rg로 돈다. 그러나 15.1.0의 파일은 macOS arm64와 manylinux x86_64 휠과 소스뿐이라(2026-10-23 PyPI JSON을 받아 봤다), 이 PC(Windows)에서는 소스를 빌드하다 실패했다(`uv run --no-project --with ripgrep`이 maturin 휠 설치에서 멈췄다). 거부했다.
- **실제 rg는 프로브로만 맞대고, 시험은 손으로 본 규칙을 표로 고정한다.** ADR과 CI 변경이 없지만, Claude Code나 rg가 glob을 다르게 읽게 되어도 시험은 모른다. 대기열 422가 적은 처방보다 약하다. 사용자가 두 안을 견주어 이 결정을 골랐다(일지 2026-10-23-33).
- **rg가 없으면 건너뛴다.** 원칙 II에 걸린다. 거부했다.

## Consequences

- **rg 전제를 적는다.** `tech.md`의 테스트 행, `operations.md` 가드레일의 기계마다 까는 것(pwsh 옆), `README.md`의 시작 절, `.pre-commit-config.yaml` 머리의 준비 목록이다. 헌법 버전은 patch다. 게이트 수와 손으로 치는 검증 명령은 그대로다.
- **Grep 도구가 glob을 나누는 규칙은 실제 rg로 맞대지 못한다.** 그 규칙은 Grep 도구 안에 있어 pytest가 부를 수 없다. 훅의 `grep_tool_globs`가 손으로 본 규칙을 따르고, 시험은 그것이 낸 조각을 rg에 넘긴다. 규칙 자체는 손으로 본 표가 고정한다. Claude Code가 그 규칙을 바꾸면 다시 손으로 본다. 손으로 본 꼴은 넷이고(`*.md,x`, `*.md x`, `{x}`, `{*.md},x`), 중괄호와 쉼표가 섞인 다른 꼴(`a,{.env}`)도 쉼표로 나누지 않는다고 미루어 본다. 그 어림이 틀리면 거짓 음성이다.
- **못 보는 것.** CI는 Claude Code를 깔지 않으므로, 실행 이름으로 띄우는 길은 이 PC(Windows)에서만 쟀다. 리눅스의 Claude Code 실행 파일과 클라우드 세션에서 그 길이 같은지는 보지 않았다(클라우드 세션은 PATH에 `claude`가 있다고 어림한다). rg의 판 사이의 동작 차이는 그 판이 CI나 이 PC에 들어온 뒤에야 본다.
