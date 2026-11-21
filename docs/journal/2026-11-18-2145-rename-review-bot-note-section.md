# 2026-11-18 리뷰 봇 워크플로의 절 이름 "릴리스 노트 조각"을 "릴리스 노트 원고"로 바꾼다

앞 일지(`2026-11-18-1559-rename-workflow-terms.md`)의 "다음" 첫 항목을 잇는다. 용어집의 낯선 이름을 쉬운 이름으로 바꾸는 일 가운데 대기열 항목 `glossary-plain-names-left`의 몫으로는 넷째 PR이다(604, 605, 607에 이어). 이름 열다섯을 처음 바꾼 PR 603까지 세면 다섯째다. 앞 PR 607이 바꾸지 않고 넘긴 한 줄, 리뷰 봇 워크플로 `.github/workflows/claude-code-review.yml` 67행의 절 이름만 바꾼다. 이 단계에서 사용자에게 새로 물은 것은 없고, 사용자의 새 프롬프트도 없다.

## 앞 PR의 병합 (PR 607)

둘째 푸시(`c52289f15`)의 결과와 다음 회고가 셀 두 사건은 PR 607의 마지막 코멘트에 적었다(`next-session` `merge.md` 2의 "뒤로 넘긴 일"). `tools/wait_ci.py 607`이 "끝: 모두 통과. CodeRabbit: Review rate limited"로 끝났고, claude-review는 둘째 회차에도 "지적 없음"이었다. `gh pr merge 607 --squash --match-head-commit`으로 병합했고 dev의 병합 커밋은 `b74a8adf2`다. 원격 브랜치는 병합과 함께 지워졌다(`git ls-remote --exit-code`가 2). 주 체크아웃 미갱신: 루트는 dev.

다음 작업을 고르는 표(`next-session` `SKILL.md`의 결정표)에서 고른 줄은 "하네스·문서만 고친 PR이었고 같은 주제가 남았다"이고 이 세션에서 잇는다. 낸 지시문은 이렇다.

```
다음 작업: 받는 세션이 쓸 .scratch/harness/issues/rename-review-bot-note-section.md. 리뷰 봇 워크플로 .github/workflows/claude-code-review.yml 67행의 절 이름 "릴리스 노트 조각"을 "릴리스 노트 원고"로 바꾼다
다음 단계: 구현
어디서: 이 세션. 같은 주제가 남았고 컨텍스트가 자산이다
시작 프롬프트: 대기열 glossary-plain-names-left의 리뷰 봇 워크플로 한 줄을 티켓 .scratch/harness/issues/rename-review-bot-note-section.md로 쓰고 한다
브랜치: chore/rename-review-bot-note-section
모델: 없음
읽을 것: docs/journal/2026-11-18-1559-rename-workflow-terms.md의 "다음", docs/agents/issue-tracker.md
이어받을 상태: PR 607 둘째 푸시의 결과와, 다음 회고가 셀 두 사건(문서만 바꾼 둘째 커밋의 pre-commit 703.5초, 둘째 커밋 직후의 인계 계기 308,307 토큰)은 PR 607의 마지막 코멘트에 있다
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 dev. 병합은 이 워크트리 사본의 next-session merge.md의 "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

## 한 것

- 브랜치 `chore/rename-review-bot-note-section`을 `origin/dev`(`b74a8adf2`)에서 땄다.
- 기록 밖에서 옛 이름 "노트 조각"이 남은 곳을 `git grep -n -e "노트 조각"`(일지와 ADR 제외)으로 다시 훑었다. 용어집의 뜻으로 남은 곳은 워크플로 67행 하나였다. 그 밖에 걸린 곳은 앞 티켓이 옛 이름을 남겨도 된다고 정한 자리다(그 티켓의 "바꾸지 않는 것"과 수용 기준 둘째 줄. 끝난 기능 release-image의 명세와 티켓, `.scratch/release-image/plan.md`의 ADR 0056 이력 제목 인용, done인 harness 티켓, 대기열 항목의 기록, 용어집의 피할 말 줄).
- `docs/constitution/operations.md`의 절 제목은 이미 `## 릴리스 노트 원고`(40행)이고, 리뷰 파이프라인 3(94행)도 그 이름으로 가리킨다. 리뷰 봇이 찾는 "느낌표의 기준" 문단은 46행에 그대로 있다.
- 워크플로 67행의 "릴리스 노트 조각"을 "릴리스 노트 원고"로 바꿨다. 같은 줄의 "판을 올릴 때"는 판 계열 이름을 바꿀 때 따로 고친다(대기열 항목 `glossary-plain-names-left`의 "`rename-workflow-terms` 티켓의 셀프 리뷰가 잡아 더 적는 하나다" 단락).
- 대기열 항목 `glossary-plain-names-left`의 "반영한 것"에 이 한 줄을 옮기고, 남은 목록에서 뺐다.

## 셀프 리뷰

`/code-review`를 base `b74a8adf2`(origin/dev의 merge-base)로 돌렸다. 범위는 바뀐 추적 파일 둘(워크플로, 대기열 항목)과 미추적 파일 둘(티켓, 이 일지)이고 커밋은 없다. 표준 축은 sonnet·high, 명세 축은 이 세션의 모델을 이었다.

**표준 축.** Critical·Major는 없었고 Minor 둘과 Nit 둘이었다. 밀 주장(남은 곳이 67행 하나, 40·46·94행, 가드 정규식이 이 PR의 네 파일을 지나는 것, 대기열의 반영한 것과 남은 목록)은 표준 축이 `git grep`과 Read로 손으로 대 보고 모두 맞다고 적었다.

- [Minor] 티켓이 "가드 스텝이 다른 파일과 함께 실은 PR을 실패로 만든다"의 근거로 `operations.md` 48행과 리뷰 파이프라인 3을 들었다. 48행은 "다른 파일과 함께 싣지 않는다"는 규칙만 말하고, 리뷰 파이프라인 3(94행)은 건너뜀도 가드도 말하지 않는다. 건너뜀의 근거는 100행의 초록 착시 항목이고, 가드의 근거는 워크플로의 그 스텝(107~113행)과 PR 서식의 `.github/` 줄이다. 100행을 열어 맞는 것을 봤다. **고친다.** 대기열 항목의 마지막 단락도 같은 근거를 들어 함께 고친다. 앞 티켓 `rename-workflow-terms`는 done이라 기록이므로 그대로 둔다.
- [Minor] 티켓의 "봇이 읽는 문단은 같다"는 맞지만, 봇이 Grep으로 "느낌표의 기준"을 찾으면 46행과 94행 두 줄이 걸린다. 프롬프트는 줄 번호를 하나로 여긴다. 이 diff가 만든 틈이 아니고 이름을 바꾸기 전에도 같은 두 줄이 걸렸다. **티켓에 한 문장을 더한다.** 프롬프트를 고치는 일은 이 PR의 범위 밖이라 "다음"과 회고 후보로 넘긴다.
- [Nit] 티켓의 "가드 스텝", "하네스 탐침"과 일지의 "결정표"에 풀이가 없다(`CLAUDE.md` 원칙의 쉬운 말 규칙). **고친다.** 처음 나오는 자리에 짧은 풀이를 붙인다.
- [Nit] 일지에 검증 결과와 "다음"이 아직 없다. 커밋 뒤와 단계를 닫을 때 쓰므로 고칠 것이 없다.

**명세 축.** Critical·Major는 없었고 Minor 넷과 Nit 둘이었다. 수용 기준 다섯은 모두 맞다고 적었다. 가드의 필터에 이 PR의 네 경로를 넣어 손으로 돌려 걸리는 것이 없었고(대조로 넣은 `.scratch/plan.md`는 걸렸다), `tools/plan_table.py --check`가 0으로 끝났다. 앞 티켓 20행과 앞 일지 "다음" 첫 항목의 미래형 문장이 이 변경으로 닫히고, 이 변경 뒤에 거짓이 되는 미래형 문장은 없다고 적었다.

- [Minor] 티켓의 가드 근거 인용. 표준 축의 첫 Minor와 같은 지적이다. 위대로 **고친다.**
- [Minor] 티켓이 "대기열 항목의 마지막 단락"이라 가리킨 말은 마지막 단락(사용자가 그대로 두기로 한 이름)이 아니라 "`rename-workflow-terms` 티켓의 셀프 리뷰가 잡아 더 적는 하나다" 단락에 있다. **고친다.** 이 일지의 "한 것"에도 같은 말이 있어 함께 고친다.
- [Minor, 원래 있던 문장] 67행의 "(그 줄이 길어 Grep은 내용을 생략하고 번호만 준다)"가 이 PC에서는 맞지 않는다. 이 세션의 Grep 도구로도 46행은 내용까지 나오고 94행만 생략됐다. 문장대로 생략된 줄을 고르면 94행(가리키는 줄)을 연다. 수용 기준 1("그 밖의 글자는 그대로다")대로 이 PR에서는 고치지 않고, 표준 축의 둘째 Minor와 묶어 티켓에 적고 "다음"으로 넘긴다.
- [Minor] 병합 뒤의 빈 기간. 이 PR을 dev에 병합하면 다음 출시 PR까지 main의 이 파일과 dev의 것이 달라, main에서 딴 핫픽스 PR도 리뷰 봇이 건너뛸 것이고 가드가 코멘트 0개로 claude-review를 빨갛게 만들 것이다. `operations.md` 100행은 건너뛸 것이라는 어림까지만 적고 가드의 빨강은 적지 않았다. Grep 도구로 `.claude/skills`의 `*.md`와 `operations.md`에서 핫픽스와 claude-review·리뷰 봇·가드를 함께 다룬 줄을 찾았고, 그 100행과 `pr-merge`·`merge.md`의 병합 확인 줄(한도로 빨간 claude-review만 실패로 세지 않는다) 밖에는 없었다. **티켓에 "병합 뒤의 빈 기간" 단락을 더하고**, PR 본문의 남긴 위험과 "다음"에 적는다. 가드를 고치는 일은 이 파일을 다시 바꾸는 PR이라 이 PR에서 하지 않는다.
- [Nit] 일지의 "넷째 PR"이 무엇을 기준으로 셌는지 없다. **고친다.**
- [Nit] 티켓 수용 기준 2와 이 일지가 "앞 티켓의 '바꾸지 않는 것'"이라 한 자리에는 그 티켓 수용 기준 둘째 줄의 목록(용어집의 피할 말 줄, 대기열 기록)도 든다. **고친다.**

**고친 것.** 반영하며 새로 쓴 사실 문장은 아래와 같다. PR 직전 리뷰에 밀 주장으로 넘긴다(CLI 리뷰는 주장을 넘기는 인자가 없어, 서브에이전트 브리프에 싣는다).

- 티켓: "이 파일을 바꾼 PR은 리뷰 봇이 리뷰하지 않고 건너뛴다(`docs/constitution/operations.md` 100행). 그리고 같은 워크플로의 가드 스텝(리뷰 봇이 코멘트를 남겼는지 세는 마지막 단계, `Fail when Claude left no comment`)은 그 PR이 일지·대기열·티켓·하네스 탐침(`.scratch/harness/probes/`) 밖의 파일을 함께 실으면 실패한다(그 스텝의 103~113행, PR 서식의 `.github/` 줄). 그래서 이 파일은 다른 파일과 함께 싣지 않는다(`operations.md` 48행)."
- 티켓: "다만 그 글자로 찾으면 `operations.md`의 두 줄이 걸린다. 46행은 그 문단이고, 94행은 그 문단을 가리키는 리뷰 파이프라인 3이다. 프롬프트는 걸리는 줄을 하나로 여기고 "그 줄이 길어 Grep은 내용을 생략하고 번호만 준다"고 적었지만, 이 PC의 Grep 도구는 46행을 내용까지 보이고 94행만 생략했다(2026-11-18에 손으로 봤다. CI의 Claude Code 판으로는 보지 않았다). 이 둘은 이름을 바꾸기 전에도 같았고, 이 티켓은 그 안내를 고치지 않는다."
- 티켓의 "병합 뒤의 빈 기간" 단락 전체. 그 안의 "기준 커밋 `b74a8adf2`에서 origin/main과 dev의 이 파일은 같고, dev에만 있는 커밋 가운데 이 파일을 바꾼 것은 없다"는 `git diff --stat origin/main b74a8adf2 -- .github/workflows/claude-code-review.yml`과 `git log --oneline origin/main..b74a8adf2 -- .github/workflows/claude-code-review.yml`이 둘 다 빈 출력인 것을 손으로 봤다. 처음에는 이 파일을 dev에서 바꾸는 것이 이번이 처음이라고 썼다가, dev 전환 뒤의 이력 전체를 보지 않았으므로 확인한 사실만 남겼다. 가드가 실패를 내는 줄도 처음에 107~113행이라 썼다가, 이 파일인지 가르는 조건이 103행에서 시작해 103~113행으로 고쳤다.
- 대기열 항목: "그 파일을 바꾼 PR은 리뷰 봇이 건너뛰고(`docs/constitution/operations.md` 100행), 그 워크플로의 가드 스텝이 … 실패로 만든다(그 스텝의 103~113행, PR 서식의 `.github/` 줄. 따로 내는 규칙은 `operations.md` 48행)."

**남긴 것.** 프롬프트의 Grep 안내(두 줄이 걸린다, 46행은 생략되지 않는다)와 병합 뒤의 빈 기간에 가드가 빨개지는 것. 둘 다 이 워크플로 파일을 다시 바꾸는 일이라 이 PR의 범위 밖이고, "다음"과 회고 후보로 넘긴다.

## 커밋 (`17eeb8c25`)

pre-commit이 716.9초 걸려 모두 `Passed`였다(pytest 635.9초, web-verify 716.3초, run-hooks 154.2초, pyright 60.1초, pyright-linux 70.1초). 이 커밋은 `.py` 없이 워크플로 한 줄과 일지·티켓·대기열 항목만 바꿨다. 대기열 `docs-only-commit-precommit-slow-again`이 다루는 종류의 사건이다. ruff 둘은 `.py`가 없어 Skipped라 손으로 쳤다(`uv run ruff check .`가 `All checks passed!`, `uv run ruff format --check .`가 `2433 files already formatted`). 카나리아 명세 모양과 헌법 판 검사는 해당 파일이 없어 Skipped였고, 이 커밋에는 그 둘이 볼 파일이 없다. 인용 대조가 경고 1건을 냈다. 셀프 리뷰 반영에서 지운 초안 문장을 이 일지가 따옴표로 옮긴 자리라, 따옴표를 떼고 풀어 썼다.

처음 친 커밋은 제목이 79자라 commit-msg 훅의 72자 제한에 걸렸고, PreToolUse 훅이 pre-commit을 돌기 전에 막았다. 제목에서 "릴리스 노트 원고로"를 빼 다시 쳤다.

커밋을 백그라운드로 띄운 직후 인계 계기가 왔다(230,008 토큰, 단계 경계 `커밋 뒤`). 커밋이 끝나기 전이었다. 이 세션은 다른 세션이 연 곁 세션이라 `next-session` `handoff.md` 14행대로 넘기지 않고 이었다. 대기열 `handoff-trigger-before-background-commit-ends`가 다루는 종류의 사건이다.

## PR 직전 리뷰

`coderabbit-review` 서브에이전트를 돌렸다. CodeRabbit CLI 0.7.5가 `Plan: Free`, `Seat: not assigned`에서 끝까지 돌았고(종료 코드 0, `review_completed`), 바뀐 네 파일을 모두 보고 지적 3건을 냈다.

- [Minor] 일지가 남긴 것을 "다음"에 넘긴다고 쓰는데 "다음" 절이 없다. **유효, 지금 고칠 것은 없다.** "다음"은 단계를 닫을 때 쓰는 절이라 병합 전에 회고와 함께 쓴다. 그때 남긴 두 항목(프롬프트의 Grep 안내, 병합 뒤의 빈 기간에 가드가 빨개지는 것)을 싣는다.
- [Major 표시] dev에만 병합한 뒤 main에서 딴 핫픽스 PR이 claude-review 실패로 막히는가. **보류.** 티켓의 "병합 뒤의 빈 기간" 단락과 이 일지의 셀프 리뷰 절이 이미 적은 위험이고 새 정보가 없다. 액션이 건너뛰는지는 `operations.md` 100행의 어림이라 심각도를 Major로 올릴 근거가 없다. PR 본문의 남긴 위험에 적었다.
- [오탐] 일지 본문의 경로를 상대 경로 링크로 바꾸라는 지적. 일지는 코드 서식으로 경로를 적는 것이 관례이고 링크를 요구하는 규칙이 없다.

밀 주장으로 넘긴 여섯(티켓의 근거 셋, "느낌표의 기준"이 걸리는 두 줄, 빈 기간의 근거와 가드의 103~124행, 대기열 항목의 고친 괄호, 네 경로가 가드의 허용 경로를 지나는 것)은 서브에이전트가 원문과 대 보고 모두 맞다고 적었다. 액션이 실제로 건너뛰는지는 그 서브에이전트도 재지 않았다.

## PR 봇 리뷰 (PR 608)

PR은 https://github.com/njh6803/agent-os/pull/608 이다. 연 뒤 `@coderabbitai review`를 남기고 `tools/wait_ci.py 608`을 띄웠다. 첫 푸시(`17eeb8c25`)의 결과는 이렇다.

- **CI.** "끝: 모두 통과. CodeRabbit: Review rate limited"로 끝났다(종료 코드 0). claude-review, e2e, e2e-portal, e2e-standalone, e2e-widget, python, ticket, verify, visual, web이 `SUCCESS`였고 llm은 `SKIPPED`였다.
- **claude-review.** 이 PR은 그 워크플로 자신을 바꿨으므로 액션이 리뷰하지 않고 건너뛰었다. 잡 로그를 스크래치패드에 받아 Grep으로 봤다. "Run Claude Code Review" 단계가 `Skipping action due to workflow validation` 경고를 냈고, 그 문구는 워크플로 파일이 저장소 기본 브랜치의 것과 같은 내용이어야 한다고 적었다. 가드 스텝은 "이 워크플로를 바꾼 PR: 액션이 건너뛰므로 코멘트는 세지 않는다"를 찍고 0으로 끝났다. PR에 claude[bot]의 코멘트는 없다. 그래서 초록은 리뷰가 아니라 건너뜀이고 이 봇의 회차는 없다.
- **CodeRabbit.** 무료 한도에 걸려 리뷰하지 않았다(`Review limit reached`, 56분 뒤 다음 리뷰). 이 봇의 회차도 없다. 보안·버그 축은 PR 직전에 돈 CodeRabbit CLI 0.7.5의 결과(PR 본문 체크리스트, 지적 3건 가운데 유효 1·보류 1·오탐 1)가 대신한다(`docs/constitution/operations.md` 108행). 한도가 풀리기를 기다리지 않는다.
- 고친 것도 보류한 것도 없다. 유지보수성 축은 이 PR에서 리뷰 봇이 보지 못하므로, 위 셀프 리뷰의 두 축이 대신했다(PR 서식의 `.github/` 줄).

로그의 경고 문구가 액션이 PR의 파일을 기본 브랜치(dev)의 것과 견준다는 것을 보였다. `operations.md` 100행의 "dev의 그 파일과 비교하므로"와 맞는다. 이 PR을 병합한 뒤 main에서 딴 핫픽스 PR이 나오면 그 PR의 이 파일(main의 옛 글)이 dev의 새 글과 달라 건너뛸 것이라는 어림도 이 문구와 어긋나지 않는다. 운영에서 개발로 합치기 PR이 병합 결과와 머리 가운데 어느 쪽의 파일로 견주어지는지는 이 문구로도 가르지 못한다.

## 회고

retro 스킬을 디스크의 `SKILL.md`로 열어 따랐다. 1단계의 `writing-for-agents`는 이 세션에서 앞서 불렀다. 낸 후보는 열하나다. 승인 셋(회차 둘, 새 항목 하나), 기각 여섯, 일지에만 남기는 것 둘이고 넘김은 없다. 만료는 `uv run python tools/queue_open_rows.py`의 "만료할 항목"이 작업 트리 기준으로 없어, `origin/dev` 기준과 겹치는 항목도 없으므로 닫은 것이 없다.

심각도 순이다.

1. **승인(회차로 세는 것).** 커밋을 백그라운드로 띄운 직후 인계 계기가 커밋이 끝나기 전에 왔다(230,008 토큰). 앞 단계 PR 607의 둘째 커밋 직후에도 한 번 왔다(308,307 토큰, 그 PR의 마지막 코멘트가 이 회고에 넘겼다). 열린 항목이 이미 처방한 사건이다. `handoff-trigger-before-background-commit-ends`에 더해 8회차다.
2. **승인(회차로 세는 것).** 워크플로 한 줄과 일지·티켓·대기열 항목만 바꾼 커밋의 pre-commit이 716.9초였다(pytest 635.9초, web-verify 716.3초). PR 607의 둘째 커밋도 일지·티켓·대기열 항목만 바꿨는데 703.5초였다(그 PR의 마지막 코멘트가 넘겼다). 열린 항목이 처방한 사건이다. `docs-only-commit-precommit-slow-again`에 더해 14회차다. 나란히 돈 다른 세션의 부하는 재지 않았다.
3. **승인(새 항목, 고침).** 리뷰 봇 프롬프트(67행)의 Grep 안내가 사실과 다르다. "느낌표의 기준"으로 찾으면 `operations.md`의 두 줄(46행, 94행)이 걸리고, 이 세션의 Grep 도구는 46행을 내용까지 보였다. 셀프 리뷰의 두 축이 짚었다. 틀린 사실의 고침이라 사건 하나로 반영하는 종류이고(층: 프롬프트 자체를 고친다), PR 하나로 되돌릴 수 있다. 이 파일을 다시 바꾸는 PR을 따로 내야 해서 이 세션에서는 반영하지 않고, 새 항목 `review-bot-bang-grep-two-lines`(1회차)에 둔다. 같은 67행을 바꾸는 판 계열 PR과 묶도록 `glossary-plain-names-left`에도 그 항목을 가리키는 구절을 더했다.
4. **기각.** 병합 뒤의 빈 기간에 main에서 딴 핫픽스 PR의 claude-review가 빨개질 수 있다. 아직 그런 핫픽스 PR이 없어 사건 없이 떠올린 것이다. 티켓과 PR 본문의 남긴 위험, 아래 "다음"에 적었다.
5. **기각.** 티켓이 가드의 근거로 `operations.md` 48행과 리뷰 파이프라인 3을 든 것은 앞 티켓과 대기열 항목에서 물려받은 틀린 인용이었다. 셀프 리뷰 두 축이 잡았다. 리뷰가 잡도록 둔 기준(`code-review` 두 브리프의 인용 검증)을 리뷰가 잡은 것이라 회차 셈에서 빠진다. 근거 괄호의 줄이 그 사실을 말하는지는 기계로 가를 수 없어 검사로 옮길 수도 없다.
6. **기각.** 티켓이 "대기열 항목의 마지막 단락"이라 자리를 잘못 가리켰다. 5와 같은 까닭이다.
7. **기각.** 커밋 제목이 79자라 72자 제한에 걸렸다. PreToolUse 훅이 pre-commit을 돌기 전에 그 자리에서 막았다.
8. **기각.** 이 일지가 지운 초안 문장을 따옴표로 옮겼다. 인용 대조(`check-quotes`)가 커밋에서 경고했고 다음 커밋에서 고쳤다.
9. **기각.** 일지 파일을 만들 때, 주 체크아웃 경로(`C:\project\agent\docs\journal\`)에 쓸 뜻이 없던 파일을 쓰는 호출 하나를 잘못 함께 보냈다. 앱의 워크트리 가드가 그 자리에서 막아 파일은 생기지 않았다.
10. **일지에만.** PR을 연 뒤에도 인계 계기가 왔다(249,107 토큰, 단계 경계 `PR 연 뒤`). 명령이 성공한 뒤의 정상 경계이고, 곁 세션이라 `handoff.md` 14행대로 넘기지 않았다. 1의 항목이 다루는 사건(커밋이 끝나기 전에 온 계기)이 아니다.
11. **일지에만.** 셀프 리뷰를 고치며 쓴 닫힌 주장(이 파일을 dev에서 바꾸는 것이 처음이다)을 리뷰에 넘기기 전에 스스로 근거를 다시 열어 확인한 사실만 남겼다. `code-review` 6단계 1의 "근거를 끝까지 열고 쓴다"가 그 자리에서 작동했다.

## 다음

이 PR이 병합되면 작업 규약 쪽 이름 셋(노트 조각, 되돌려 합치기, 루트 브랜치)은 모두 끝난다. 남은 것은 아래와 같다.

- **화면 쪽 이름 둘**(다음 작업). 거꾸로 동기화 → 웹 편집 반영, 원색 토큰 → 색 단계 토큰. 원색 토큰의 풀이는 디자인 시스템 아티팩트에 올라가는 원본(`web/tools/sync-design-system/artifact-source/README.md`, `foundations/colors/index.html`)에도 있어, 그 PR은 병합 뒤 `sync-design-system` 올리기까지 해야 끝난다(앞 일지 `2026-11-18-1559-rename-workflow-terms.md`의 "다섯을 둘로 나눈 까닭". 그 둘이 고치는 스킬과 규칙을 원천으로 든 카나리아 명세는 16개였다).
- **병합 뒤의 빈 기간.** 이 PR을 dev에 병합하면 다음 출시 PR이 main에 올릴 때까지 main과 dev의 `.github/workflows/claude-code-review.yml`이 다르다. 그동안 main에서 딴 핫픽스 PR의 claude-review가 빨갛게 나오면, 그 잡 로그의 "Run Claude Code Review" 단계에 `Skipping action due to workflow validation` 경고가 있는지 먼저 본다. 있으면 리뷰 봇이 이 빈 기간 때문에 건너뛴 것이고 가드가 코멘트 0개로 실패한 것이다. 출시 PR이 dev를 main에 올리면 이 기간이 끝난다.
- **남은 이름 바꾸기**(대기열 `glossary-plain-names-left`). 계약 파일에 닿지 않는 작은 이름(서버 파일, 전송, 관리자, 넘김), 큰 이름(고지, 운영자 파일, 규칙 파일, 사이트 파일), 계약 파일에 닿는 이름(저자, 교환, 주체, 컨텍스트, 상한, 표지. 병합 전에 사용자에게 알리고 로컬 모델 시험의 범위에 드는지 본다), 그리고 맨 뒤의 제품 판과 판 계열이다. 쓰인 곳의 수는 일지 `2026-11-18-1422-rename-small-run-terms.md`에 있고 시작할 때 다시 센다. 2026-11-18에 더 고른 이름의 PR이 로컬 모델 시험의 범위에 닿으면 예상 비용을 보이고 다시 묻는다.
- **판 계열의 리뷰 봇 워크플로 PR.** 판 계열을 바꿀 때 67행의 "판을 올릴 때"는 다시 이 파일만 싣는 PR로 낸다. 그 PR에 대기열 `review-bot-bang-grep-two-lines`(Grep 안내 고침)를 함께 싣는다.
- **이 앞 PR의 카나리아가 남긴 한계와 원천과 어긋난 카나리아 셋.** 앞 일지의 "다음"대로 남았다. `next_session_fable_cut_row`, `next_session_model_line`, `tidy_skill_cwd_owner`는 대기열 `stale-web-design-canaries`(3회차)가 같은 종류를 센다.
- **rag-engine.** 같은 결정을 rag-engine에 맞추는 지시문은 사용자에게 냈고, 사용자가 아직 답하지 않았다.
- **열여섯 이름의 영어 표기.** 일지 `2026-11-17-2031-plain-words-in-written-artifacts.md`의 "다음"이 남긴 물음이고 사용자가 아직 답하지 않았다.
- **회차 5 이상인 대기열 항목.** 이 회고로 `handoff-trigger-before-background-commit-ends`가 8회차, `docs-only-commit-precommit-slow-again`이 14회차가 됐다. 하네스 chore를 고를 때의 계기다.
- **앞 일지의 "다음"에서 그대로 남은 것.** 끝난 기능의 변이 표에 남은 `-k` 여섯(`mutation-table-test-filter-stale-after-rename`), `CLAUDE.md` 밖에 남은 "위젯 미리보기 페이지"(`widget-test-page-term-leftovers`), e2e가 `serve`를 시스템 임시 폴더에서 띄우는 것(`e2e-serve-cwd-is-system-temp-dir`), 회차를 한꺼번에 띄우는 프로브의 띄우기 예외(`probe-parallel-launch-outside-round`).
