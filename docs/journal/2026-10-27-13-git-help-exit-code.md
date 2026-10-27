# 2026-10-27 (13) 푸시 훅의 도움말 시험을 git 의 종료 코드에서 떼다 (harness 018)

## 시작

세션을 연 지시문의 시작 프롬프트와 범위다. 세션 제목은 `chore/018-git-help-exit-code` 이다.

> 사용자: 티켓 .scratch/harness/issues/018-git-help-exit-code.md를 쓰고 한다. 티켓의 내용은 아래 지시문의 "이어받을 상태"다 (브랜치 chore/018-git-help-exit-code, 모델 Opus 5.5 / medium 레벨 스윕의 갈래, 이번 요청 범위: PR과 병합까지)

`EnterWorktree` 로 `018-git-help-exit-code` 워크트리를 만들고 브랜치 이름을 바꿨다. `tools/sibling_overlap.py` 가 낸 다음 빈 티켓 번호 018 로 티켓을 썼고, 쓴 직후 다시 친 대조에서 겹침이 없었다.

## 한 것

- 두 시험(`tests/tools/test_hook_push_behind_main.py`, `tests/tools/test_hook_push_delete_open_pr.py`)의 `test_도움말_판정이_실제_git_과_같다` 에서 도움말 갈래의 종료 코드 단언(129)을 지우고 사용법 표지와 푸시 여부로만 가르게 했다. `--` 뒤의 `-h` 갈래의 `returncode != 129` 도 지웠고, 그 갈래는 표지 부재 단언이 대신 본다.
- 129 를 git 의 동작으로 적은 독스트링·주석(`tools/hook_push_behind_main.py` 의 `asks_help`, 두 시험 파일)을 고쳤다. 판마다 다른 종료 코드의 이력과 근거의 종류는 티켓 한 곳에 둔다.

## 검증

- 두 시험 파일만: 이 PC(git 2.32)에서 172 passed(손으로 쳤다).
- `uv run python tools/run_checks.py`(고치기 전 판): pytest 하나가 빨갰다. `tests/tools/test_rewrap_comments.py::test_이_저장소의_파이썬_파일에는_감을_줄이_없다` 였고, 셀프 리뷰를 반영하며 넘친 독스트링 줄이었다. `tools/rewrap_comments.py` 로 감은 뒤 그 시험만 다시 돌려 통과했다. 나머지는 통과(web-verify 703.6초).
- 커밋 `a62799b7` 의 pre-commit: 모두 Passed(pytest 580.7초, web-verify 624.8초). 카나리아 명세·헌법 판은 해당 파일이 없어 Skipped.

## 셀프 리뷰

기점 `4f783dc0`, 바뀐 파일 셋, 커밋 0, 미추적 1(티켓).

- 표준 축: 독스트링이 129 를 이력으로 새로 적어 수용 기준 2 와 어긋난다, 2.55 의 129 는 통과에서 미룬 것인데 근거 종류가 없다(판단 항목), 같은 이력이 세 곳에 중복된다(smell). 고쳤다: 이력과 근거 종류를 티켓에만 두고 코드는 티켓을 가리킨다.
- 명세 축: Critical·Major 없음. Minor(근거 종류)는 위와 같이 고쳤다. git 태그 원문을 받아 읽어 v2.56.0 이 `PARSE_OPT_HELP` 를 `exit(0)` 으로 가른 것을 확인했고(코드 읽기), 티켓에 그 문장을 더했다. Nit(`asks_help` 의 줄 감기)은 이 변경 전의 감기라 두었다.

고친 것 줄의 새 사실 문장(PR 직전 리뷰에 밀 주장으로 넘겼다): "v2.55.0 의 `parse-options.c` 는 `PARSE_OPT_HELP` 와 `PARSE_OPT_ERROR` 를 함께 `exit(129)` 로 끝내고 v2.56.0 은 `PARSE_OPT_HELP` 를 `exit(0)` 으로 갈랐다".

## PR 직전 리뷰

`coderabbit auth status` 가 `Seat : not assigned` 라 대체 둘을 돌렸다.

- `/security-review`: 발견 없음. 바뀐 실행 코드가 없다.
- `bug-perf-review`: 유효 0, 보류 0. 서브에이전트가 코드를 읽어 판정했다(실행은 하지 않았다). 갈래가 섞이지 않고, 티켓의 소스 문장이 태그 원문(`gh api` 로 받은 v2.55.0·v2.56.0 `parse-options.c`)과 맞는다. 보충: v2.56.0 은 `PARSE_OPT_HELP_ERROR` 를 새로 두어 129 를 유지한다.

## PR

[njh6803/agent-os#406](https://github.com/njh6803/agent-os/pull/406) 을 열었다. 열자마자 인계 계기(컨텍스트 215,604 토큰, 경계 `PR 연 뒤`)가 와서 같은 브랜치·워크트리의 새 세션에 넘긴다. 봇 회차(`@coderabbitai review` 요청 포함), CI 확인, 병합은 새 세션이 한다. 이 세션의 제목은 `chore/018-git-help-exit-code (인계함)` 으로 바꾼다.

## 인계 지시문

```
다음 작업: PR #406(chore/018-git-help-exit-code) 반영·병합. 티켓 .scratch/harness/issues/018-git-help-exit-code.md
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 티켓 .scratch/harness/issues/018-git-help-exit-code.md를 쓰고 한다. 티켓의 내용은 아래 지시문의 "이어받을 상태"다
브랜치: chore/018-git-help-exit-code
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: 일지 docs/journal/2026-10-27-13-git-help-exit-code.md(커밋하지 않았다. 이어 쓰고 커밋한다), 티켓 018
이어받을 상태: 인계: PR 연 뒤. 순서 1의 2(봇 회차)부터 한다. 첫 `@coderabbitai review` 코멘트도 새 세션이 남긴다. 구현·셀프 리뷰·PR 직전 리뷰(대체 둘, 지적 0)는 끝났고 커밋은 a62799b7 하나다. git 2.56 에서 초록인지는 이 PR 의 CI python 잡으로만 본다(이 PC 는 git 2.32). PR #403 은 이 PR 의 병합을 기다리며 이 세션은 그 PR 을 건드리지 않는다. 일지: docs/journal/2026-10-27-13-git-help-exit-code.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-27T12:45Z

## 둘째 세션

인계 지시문으로 연 새 세션이다. 제목을 `chore/018-git-help-exit-code` 로 바꾸고 `EnterWorktree(path)` 로 이 워크트리에 들어왔다.

> 사용자: 티켓 .scratch/harness/issues/018-git-help-exit-code.md를 쓰고 한다. 티켓의 내용은 아래 지시문의 "이어받을 상태"다 (지시문의 이어받을 상태: 인계: PR 연 뒤, 이번 요청 범위: PR과 병합까지)

### 봇 회차 (첫 회차)

`@coderabbitai review` 를 남기고 `tools/wait_ci.py 406` 을 기다렸다. 끝 줄은 `끝: 모두 통과` 였다.

- CI: 모든 잡이 통과했다(`gh pr checks 406`). 그런데 python 잡(실행 40504585236, 첫 시도)의 로그는 이미지 `20261012.334.1`, `git version 2.55.0` 이었다(`gh run view --log` 로 손으로 봤다). 옛 이미지라 수용 기준 3 의 git 2.56 쪽을 보지 못한 판이다. 셀프 리뷰 두 축도 같은 것을 짚었다(아래).
- 그래서 python 잡만 `gh run rerun 40504585236 --job 122190524173` 으로 다시 돌렸다. 둘째 시도(잡 122196831859)는 이미지 `20261025.353.1`, `git version 2.56.0` 에 걸려 `5724 passed, 8 deselected` 로 통과했다(로그를 손으로 봤다). PR #403 이 열 갈래로 빨갰던 이미지와 같다. 출력이 `-q` 라 두 시험 파일의 이름은 로그에 없고, `FAILED` 줄이 0 인 것으로 두 파일이 지났다고 본다.
- 러너 이미지는 시도마다 갈려, "이 PR 의 CI 로 본다"는 길은 첫 시도만으로는 닫히지 않았다. 잡 로그의 `Version:` 과 `git version` 줄을 봐야 어느 판을 봤는지 안다.
- claude-review: 지적 없음.
- CodeRabbit: 무료 한도에 걸려 리뷰하지 않았다(`Review rate limited`). 회차로 세지 않는다. PR 직전 리뷰(대체 둘)가 대체다.

고칠 것이 없어 반영 커밋은 없다.

### 셀프 리뷰 (둘째 세션)

기점 `a62799b7`, 바뀐 파일 하나(`.scratch/retro-queue.md`), 커밋 0, 미추적 1(이 일지).

- 두 축의 Major(같은 지적): 위 CI 줄의 첫 판이 "python 잡이 통과했다(9분 1초, 러너의 git 2.56)" 로 git 판을 잡 로그 없이 적었다. 고쳤다: 잡을 다시 돌려 git 2.56.0 판을 보고 위 CI 줄을 로그의 값으로 다시 썼다.
- 명세 축 Minor, 표준 축 판단 항목: 회고 1 의 "같은 일을 다룬 행은 찾지 못했다" 가 맞은 행(300, 144)을 가린 기록이 없었다. 고쳤다: 두 행을 가른 이유를 적고 행 500 에 `CODING_STANDARDS.md` 22줄을 넓히는 길을 더했다.
- 표준 축 판단 항목: 행 500 의 "main 의 필수 검사가 빨개졌다" 가 main 의 손상으로 읽힌다. 고쳤다: PR #403 의 검사로 적었다(main 의 push CI 는 빨갛지 않았다고 서브에이전트가 `gh` 로 봤다). 회고 3·5 의 기각 조건을 적었다.
- 남긴 것: 일지 머리 쪽의 `open-session을 부른다 …` 한 줄(앞 세션이 쓴 표지라 두었다), 행 500 의 무엇 칸 길이(491~493 과 같은 꼴).

고친 것 줄의 새 사실 문장: 위 CI 줄 셋(이미지와 git 판, `5724 passed`).

회고와 "다음"을 실은 이 일지와 대기열 행 둘(500, 501)을 커밋해 병합 전에 푸시한다.

## 회고

후보 일곱. 승인 둘, 기각 다섯, 넘김 없음. 만료할 행은 없었다(`tools/queue_open_rows.py` 를 이 브랜치와 `--ref origin/main` 으로 돌렸다).

1. 승인(대기열 500, 1회차): 시험이 외부 도구의 판마다 바뀔 수 있는 세부(`git push -h` 의 종료 코드)를 단언해, 러너 이미지의 git 이 오르자 코드 변경 없이 새 이미지에 걸린 PR(#403)의 필수 검사가 빨개져 병합이 막혔다. 이번 사례의 고침은 이 PR 이다. 같은 종류를 미리 막는 것은 기계로 가를 수 없는 판단이라 층은 `CODING_STANDARDS.md` 이고, 더하는 것이라 세 번째에 반영한다. 대기열을 `러너 이미지`, `git 판`, `종료 코드` 로 grep 했다. 맞은 닫힌 행 둘은 같은 일이 아니다. 300 은 이 시험을 만든 행이고(시험이 종료 코드를 단언하게 된 출처일 뿐 같은 처방이 아니다), 144 는 `CODING_STANDARDS.md` 22줄(실패를 기대하는 테스트는 실패의 까닭까지 단언한다)의 원천으로, 종료 코드만 보면 엉뚱한 실패가 초록이 된다는 거짓 초록 쪽이다. 이번 사건은 맞는 동작이 외부 도구의 판에 따라 빨개진 반대쪽이라 새 행으로 두고, 행 500 의 처방에 22줄을 넓히는 길을 함께 적었다.
2. 기각: 셀프 리뷰를 반영하며 넘친 독스트링 줄을 `tests/tools/test_rewrap_comments.py` 가 `run_checks.py` 에서 잡았다. 이미 있는 검사가 그 자리에서 잡았다.
3. 기각: 셀프 리뷰 표준 축이 종료 코드 이력을 독스트링에 새로 적은 것과 근거의 종류가 없는 것을 잡았다. 리뷰가 제 몫을 한 것이고(`docs/agents/issue-tracker.md` 의 근거 규칙), 새 판단 기준이 아니다. 검사로 옮길 몫은 일지의 근거 종류를 짚는 훅(harness 010)이 이미 맡는다.
4. 기각: CodeRabbit 이 무료 한도로 리뷰하지 않았다. `wait_ci.py` 의 통과 줄과 리뷰 파이프라인 3 이 알렸고, PR 직전 리뷰가 대체다.
5. 기각: 첫 세션이 PR 을 연 직후 컨텍스트 215,604 토큰으로 인계했다. 인계 계기가 설계대로 돈 것이라 고칠 실수나 비용이 없다(사건 없음).
6. 승인(대기열 501, 421 부터 세어 13회차): 둘째 세션이 일지를 Bash heredoc(`cat >>`)으로 덧붙이며 잡 로그를 보지 않은 git 판("러너의 git 2.56")을 본 것처럼 적었다. 그 잡은 git 2.55.0 이었고 셀프 리뷰 두 축이 Major 로 잡았다. 구현 때 실리는 근거 규칙(`docs/agents/issue-tracker.md` 프로브와 근거 절)을 어긴 사건이라 회차로 센다. 그 규칙의 계기 훅 `tools/hook_journal_evidence.py` 는 편집 도구에만 붙어(독스트링의 "못 보는 것" 첫 항목) 이 편집에 닿지 않았다. 처방을 든 445 가 닫혀 새 행 501 로 잇고, 층은 그 훅을 Bash 의 일지 쓰기에도 넓히는 것이다. 회차 3 이상이라 chore 배치 조건에 든다.
7. 기각: 수용 기준 3 의 "git 2.56 쪽은 이 PR 의 CI 로 본다" 가 러너 이미지의 점진 배포 때문에 첫 시도에서 옛 판(2.55.0)을 봤다. `wait_ci.py` 가 이미지 판을 알리게 하는 길이 있지만, 러너 판에 기대는 검증은 이 티켓에서 처음 났고, 판을 보지 않고 적은 잘못은 6 이 센다.

## 다음

PR njh6803/agent-os#406 을 병합한다. 이 세션은 워크트리에서 병합하므로 주 체크아웃을 당기지 않는다. 뒤로 넘긴 봇 지적은 없다. 이 PR 의 병합을 기다리던 PR #403 은 그 PR 의 세션이 main 을 합쳐 다시 돌린다.
