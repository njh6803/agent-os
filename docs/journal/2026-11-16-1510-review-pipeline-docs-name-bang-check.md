# 리뷰 파이프라인 문서에 느낌표 맞춤을 적는다 (harness review-pipeline-docs-name-bang-check)

브랜치 `chore/review-pipeline-docs-name-bang-check`.

## 사용자 프롬프트 원문

이 세션의 첫 메시지는 앞 세션이 낸 지시문이었고, 사용자의 다른 말은 없었다.

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. (중략) 인자: .scratch/harness/issues/review-pipeline-docs-name-bang-check.md
>
> 다음 작업: 받는 세션이 쓸 .scratch/harness/issues/review-pipeline-docs-name-bang-check.md. 리뷰 봇이 느낌표 맞춤도 본다는 사실을 operations.md 리뷰 파이프라인 3과 CODING_STANDARDS.md 32행에 한 구절씩 더한다
> 이번 요청 범위: PR과 병합까지

## 한 것

- 티켓이 아직 없어(지시문이 "받는 세션이 쓸"이라 했다) 먼저 `in-progress`로 쓰고 문서를 고친 뒤 `done`으로 바꿨다. 일은 PR 589가 일지 "다음"에 넘긴 두 자리를 따라가는 것이다.
- `docs/constitution/operations.md` 리뷰 파이프라인 3: claude-review가 유지보수성과 경계 두 축을 본 뒤 그 밖에 PR 제목 접두의 느낌표 맞춤도 본다고 적었다. 기준은 "릴리스 노트 조각" 절의 "느낌표의 기준"을 가리키고, 느낌표와 `upgrade/` 파일의 짝은 노트 검사가 CI에서 본다는 구절을 곁들였다.
- `CODING_STANDARDS.md` 32행: "이 넷과 경계, PR 제목 접두의 느낌표가 변경과 맞는지는 PR의 Claude Code Review가 본다"로 고쳤다.
- 헌법 파일(`operations.md`)을 고쳤으므로 `docs/constitution/README.md`의 판을 3.0.103에서 3.0.105로 올렸다. `sibling_overlap.py`가 형제 `feature/09-standalone-compose-runs-real-images`의 워크트리에서 3.0.104를 본다고 해서 그 판을 비워 두고 안내 문장을 같은 파일에 더했다(손으로 읽은 출력).

## 확인

- 프롬프트 3번(`claude-code-review.yml` 67행)을 Read로 읽어 새 구절과 대조했다. 어긋남이 없다(손으로 봤다).
- `uv run ruff check . && uv run ruff format --check .`가 통과했다(손으로 봤다).
- `uv run python tools/plan_table.py`가 `.scratch/plan.md`를 바꾸지 않았다(`git status --short`에 나타나지 않았다).

## 셀프 리뷰

`/code-review` 두 축, base `716e51d25`, 수정 파일 둘과 미추적 파일 하나(티켓), 커밋 0개. Critical·Major 없음.

- 고친 것: 표준 축 지적 하나. 느낌표 맞춤을 유지보수성·경계와 나란히 적으면 `operations.md` 45행의 "세 축이다"와 겹쳐 읽힐 수 있어, "두 축을 본 뒤 그 밖에 맞춤도 본다"로 고쳤다.
- 남긴 것: 명세 축 Minor(42행 문단이 3번을 가리키지 않음)는 티켓이 의도적으로 두었다고 밝힌 부분이다. `.coderabbit.yaml` 5행 주석은 틀리지 않았다. `docs/adr/0006-review-pipeline.md`는 결정 기록이라 새 ADR 없이 고치지 않았다. ADR 0006에 이력을 남길지는 사용자 판단이 필요해 정하지 않았다.
- 다시 돌린 명령: 린트 둘은 손으로 통과를 봤다. 전체 러너는 커밋의 pre-commit 결과로 갈음하며 결과는 이 일지의 "커밋 뒤"와 PR 본문에 적는다.

## PR 직전 CodeRabbit CLI (이어받은 세션)

아래는 `coderabbit-review` 서브에이전트의 보고에서 옮긴 값이고 이 세션이 CLI를 직접 치지는 않았다. `coderabbit review --agent --include-untracked --base origin/dev`가 종료 코드 0으로 `review_completed`를 냈다(`coderabbit auth status`는 `Plan: Free`, `Seat: not assigned`. 이 줄은 옮기기만 한다). findings는 1건(minor)이었고 오탐으로 판정했다. 일지 9행의 `(중략)`을 중립 요약으로 보완하라는 문체 제안인데, 7행이 첫 메시지가 앞 세션의 지시문이었다고 이미 밝힌다. 유효·보류는 0건이다.

## 인계 (커밋 뒤)

컨텍스트가 인계 문턱(200,000)을 넘은 채 `커밋 뒤` 경계에 와서 새 세션에 넘긴다(`next-session handoff.md`). 이 세션의 제목은 `chore/review-pipeline-docs-name-bang-check`였고 `chore/review-pipeline-docs-name-bang-check (인계함)`으로 바꿨다. 곁 세션이 아니다(`get_session`의 `self`에 `parentSessionId`가 없었다. 손으로 봤다). 커밋 `29c9ba41d`까지 했다. pre-commit이 첫 시도에서 종료 코드 0으로 끝났다(백그라운드 명령의 종료 코드를 손으로 봤다). 시간에 기대는 시험이 빨간 일은 이번에는 없었다. 아직 푸시하지 않았고 PR도 없다. 남은 일: `origin/dev`가 앞섰는지 보고 합치기, 푸시, PR(`dev`로, 제목에 느낌표 없음. 올릴 때 운영자가 손댈 것이 없다는 것은 이 세션의 판단이다), 첫 `@coderabbitai review` 코멘트, 봇 회차, 병합(`merge.md`의 "워크트리에서 병합할 때"), 그 뒤 회고. `sibling_overlap.py`가 형제 `feature/09-standalone-compose-runs-real-images`의 헌법 판 3.0.104를 보고 알려서 이 브랜치는 3.0.105로 올렸다. 그 형제가 먼저 병합하면 판 줄 곁의 비워 둔 판 문장을 그 브랜치가 지우므로, 이 브랜치가 병합되기 전에 `sibling_overlap.py`를 한 번 더 쳐서 판이 겹치지 않는지 본다.
open-session을 부른다 2026-11-16T06:36Z

## 이어받은 세션이 한 것

- 인계 절을 커밋했다. 일지 한 파일뿐인 이 커밋의 pre-commit이 세 번 돌았다(러너가 찍은 값을 출력 파일에서 읽었다). 첫 시도는 pytest 958.3초에 `tests/channel/cli/test_interrupt.py` 둘과 `tests/tools/test_rerun_runner.py` 둘이 빨개 종료 1이었고, 둘째는 pytest 1284.0초에 `test_interrupt.py` 하나가 빨개 종료 1이었다. 셋째는 pytest 998.0초, `web-verify` 1084.5초로 통과했다. 이 두 파일만 따로 돌리면 69건이 241.91초에 통과했다(손으로 쳤다). 빨간 시험은 모두 자식 프로세스가 30초 안에 끝나는지, 숨 쉬는 시간이 든 판의 순서를 보는 시간 기대 시험이다. 이 커밋은 코드를 바꾸지 않았다. 기계 부하를 직접 재려던 명령은 분류기 오류로 막혀 부하 때문이라는 설명은 어림이다.
- 푸시하고 PR 591을 `dev`로 열었다(제목에 느낌표 없음). `@coderabbitai review` 코멘트를 남겼다.
- 봇 회차 1: `tools/wait_ci.py 591`이 모두 통과로 끝났다(`claude-review` SUCCESS, CodeRabbit은 `Review rate limited`). `gh pr view 591 --json comments`로 읽은 `claude` 코멘트는 "지적 없음"이었고 CodeRabbit은 "Next included review available in 4 minutes"만 남겼다. 한도로 리뷰가 없던 푸시는 회차로 세지 않으므로, 이 일지를 싣는 다음 푸시 뒤에 `@coderabbitai review`를 한 번 더 남긴다.
- `origin/dev`가 그 사이 앞섰다(`git diff --name-only HEAD...origin/dev`). 겹치는 파일은 없고 헌법 판 줄(`docs/constitution/README.md`)도 건드리지 않았다.

## 회고

후보 둘을 냈고 승인 1, 기각 1, 넘김 0이다.

1. **승인(회차로 센다)**: 문서만 바꾼 커밋의 pre-commit이 세 번에 957~1562초 걸리고 시간 기대 시험이 두 번 빨갰다. 사건은 위 첫 항목이다. 열린 `docs-only-commit-precommit-slow-again`이 같은 사건(문서만 바꾼 커밋, 부하에서 흔들린 시간 제한 시험)을 이미 처방하고 있어 새 항목을 쓰지 않고 그 항목의 승인 줄에 8회차를 더했다(`uv run python tools/queue_open_rows.py --search test_interrupt --search test_rerun_runner --search 부하`로 찾았다. 닫힌 306·332·531도 같은 종류지만 열린 항목이 우선이다). 처방은 재는 chore이고 이 PR에서 하지 않는다.
2. **기각**: 워크트리 가드가 heredoc을 곁들인 `git commit` 복합 명령을 거부했다. 이미 있는 가드가 그 자리에서 막고 알렸으며, `CLAUDE.md` 환경 함정이 이미 적고 있다. 자동 모드 분류기가 세 번 "판정 없음"으로 명령을 막은 일은 다시 시도해 풀린 일시 오류이고 처방할 거리가 없다.

만료: `uv run python tools/queue_open_rows.py`와 `--ref origin/dev` 둘 다 "만료할 항목(…): (없음)"이었다(손으로 쳐서 봤다). 닫은 항목은 없다.

## 다음

- 이 PR(591)의 병합은 이 세션이 마친다(`merge.md` "워크트리에서 병합할 때"). 병합 전에 `sibling_overlap.py`를 다시 쳐서 헌법 판 3.0.105가 형제와 겹치지 않는지 본다.
- 사용자 판단 대기: `docs/adr/0006-review-pipeline.md`의 이력에 "claude-review가 느낌표 맞춤도 본다"를 남길지는 정하지 않았다.
- 뒤로 넘긴 일은 8회차를 더한 `docs-only-commit-precommit-slow-again` 하나뿐이다(재는 하네스 chore, 5회차 이상이라 다음 chore 배치 조건에 든다).
