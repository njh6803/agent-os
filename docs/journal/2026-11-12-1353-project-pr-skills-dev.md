# 2026-11-12 (13:53) git-pr-merge와 git-pr-feedback의 프로젝트 사본을 dev 모델에 맞게 둔다

세션 제목 `chore/project-pr-skills-dev`. 브랜치 `chore/project-pr-skills-dev`, 워크트리 `.claude/worktrees/project-pr-skills-dev`, 티켓 `.scratch/harness/issues/project-pr-skills-dev.md`. 모델 `claude-sonnet-5-5`.

## 사용자 프롬프트

세션의 첫 메시지는 `implement` 스킬을 이 티켓에 대고 돌리라는 지시문이다. 지시문이 가리킨 티켓 파일은 저장소 어디에도 없어서(`git log --all`로도 안 나왔다) 이 세션이 `in-progress` 티켓으로 먼저 썼다.

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. (중략) 인자: .scratch/harness/issues/project-pr-skills-dev.md
> 다음 작업: .scratch/harness/issues/project-pr-skills-dev.md. git-pr-merge와 git-pr-feedback의 프로젝트 사본을 dev 모델에 맞게 둔다 / 이어받을 상태: 사용자가 둘째 길(프로젝트 사본)을 골랐다. 범위는 두 스킬뿐이고 사용자 수준 파일은 고치지 않는다 / 확인할 선행 조건: 같은 이름이면 사용자 수준 스킬이 프로젝트 사본을 가릴 수 있다(어림). 사본을 쓰기 전에 새 세션에서 실제로 불러 어느 쪽이 실리는지 잰다. 가려지면 이름을 달리하는 길을 사용자에게 묻는다 / 이번 요청 범위: PR과 병합까지

## 이름 우선순위 측정과 결정

`claude -p --model claude-sonnet-5-5 --allowedTools Skill`로 새 세션을 띄워 손으로 봤다(티켓 결과 1. 커밋한 프로브는 없다). 같은 이름의 프로젝트 사본은 사용자 수준 원본에 가려졌고, 다른 이름의 프로젝트 스킬은 발견됐다. 한 번씩 돌린 결과이고 되풀이하지 않았다.

사용자에게 사본 이름을 물었다. 질문과 받은 답은 다음과 같다.

> 질문: 프로젝트 사본을 원본과 같은 이름(git-pr-merge, git-pr-feedback)으로 두면 사용자 수준 원본이 이겨서 사본이 쓰이지 않는 것을 새 세션에서 재 보았습니다. 사본을 어떻게 둘까요?
> 사용자(고른 라벨): 다른 이름으로 둔다 (Recommended)
> 그 설명: 사본을 pr-merge, pr-feedback 같은 새 이름으로 두고, 이 이름을 부르는 살아 있는 파일(next-session의 merge.md, tidy-checkouts, to-tickets, operations.md, 킥오프 런북 셋. 기록 문서는 뺀 어림)을 새 이름으로 바꾼다. 원본은 그대로라 다른 프로젝트에 영향이 없다. 치르는 값: 습관대로 /git-pr-merge를 치면 원본이 돌아 출시 PR(dev→main)도 squash로 병합하려 할 수 있고(merge.md 4가 적은 동작), 목록에 비슷한 스킬이 둘 보인다.

결정: 사본 이름은 `pr-merge`와 `pr-feedback`이다. 원본은 고치지 않는다.

## 인계 시점까지 한 일 (셀프 리뷰 직전)

세션 컨텍스트가 인계 문턱을 넘어 `셀프 리뷰 직전` 경계에서 새 세션에 넘긴다. 아래는 모두 이 워크트리에 커밋하지 않은 변경이다. 세션 제목은 인계 직전 `chore/project-pr-skills-dev`였다.

- **티켓.** 지시문이 가리킨 `.scratch/harness/issues/project-pr-skills-dev.md`가 저장소 어디에도 없어서(`git log --all -- <경로>`와 주 체크아웃의 `ls`로 손으로 봤다) 이 세션이 `in-progress`로 먼저 썼다. 지금 `Status:`는 `in-progress`다. 수용 기준 가운데 `operations.md`·`merge.md` 문장, 카나리아, 검증 명령 셋이 안 닫혔다.
- **사본 둘.** `.claude/skills/pr-merge/SKILL.md`와 `.claude/skills/pr-feedback/SKILL.md`를 새로 썼다. 둘 다 `프로젝트 사본` 주석을 달았고 `tools/check_instructions.py`의 `PATCHED_SKILLS`에 `pr-feedback`, `pr-merge`를 더했다. `pr-merge`는 PR 종류별 `--squash`/`--merge`, `--match-head-commit`, `--delete-branch` 없음, 병합 뒤 주 체크아웃이면 `tidy-checkouts`·워크트리면 `merge.md` 3과 4를 따른다. `pr-feedback`은 충돌을 `git merge origin/<baseRefName>`으로 풀고 푸시를 묻지 않는다.
- **이름을 부르는 문서 고침.** `next-session/merge.md`(반영 줄, 병합 길 4, 워크트리 병합 2), `docs/constitution/operations.md`(가드레일 절, 브랜치와 병합 절, 인계 절, 리뷰 파이프라인 3과 4), `tidy-checkouts/SKILL.md`("다른 브랜치다" 갈래, "부르는 곳"), `to-tickets/SKILL.md`를 새 이름으로 바꿨다. `merge.md` 4와 `operations.md` 19의 "이 저장소가 고치지 않는다" 문장은 프로젝트 사본이 있다는 사실로 고쳤다.
- **번복한 것.** 선택지 설명은 바꿀 파일에 킥오프 런북 셋(`KICKOFF.md`, `kickoff/runner.md`, `kickoff/pitfalls.md`)을 넣었으나 바꾸지 않았다. 그 런북은 main 기준인 새 프로젝트가 복사해 가고 그 프로젝트에는 프로젝트 사본이 없어, 이름을 바꾸면 없는 스킬을 가리킨다. 티켓 결과 2에 적었다. 사용자에게 다시 묻지 않았다(고른 것은 사본의 이름이고, 이 범위 판단은 선택지 설명의 "어림"이었다).
- **카나리아.** 옛 문구를 기대하던 `next_session_rate_limit_merge.toml`, `tidy_skill_rate_limit_merge.toml`을 새 문구로 고치고, `pr_merge_skill_kinds.toml`, `pr_feedback_skill_base.toml`을 새로 썼다. `tools/canary.py`로 넷을 돌려(2026-11-12, claude 2.1.322, 실험군은 이 워크트리의 커밋하지 않은 본문) 모두 통과 4, "없음" 섞임 0이었다. 대조군은 옛 문구를 옮기거나 `Unknown skill`로 못 읽었다. 결과는 각 명세의 머리 주석과 티켓 결과 3에 적었다. 처음 `next_session_rate_limit_merge.toml`을 대조군 `4b02bbe29`로 사전 확인하자 실패했고(첫 두 기대 문구가 그 커밋에도 있다), 명세 머리가 적은 `37759ef2`로 통과했다.
- **돌려 본 검사(손으로 봤다).** `uv run python tools/check_instructions.py`는 출력 없이 끝났다. `uv run ruff check .`와 `uv run ruff format --check .`는 통과했다. pyright, `lint-imports`, pytest, `pnpm -C web verify`는 아직 안 돌렸다(커밋의 pre-commit이 갈음한다). 편집기 진단이 `tools/check_instructions.py` 522행의 `_place` 미사용을 알렸는데, 이 세션은 그 줄을 고치지 않았다(내 편집은 `PATCHED_SKILLS` 목록뿐). 이 진단이 기존 것인지는 pyright를 돌려 본 적이 없어 모른다.

인계: 이 세션의 제목을 `chore/project-pr-skills-dev (인계함)`으로 바꿨고(앱이 묻지 않고 바꿨다), 기다리는 백그라운드 작업은 없었으며, `git worktree unlock C:/project/agent/.claude/worktrees/project-pr-skills-dev`는 출력 없이 끝났다.

open-session을 부른다 2026-11-12T05:04:25Z

## 이어받은 세션의 셀프 리뷰 (2026-11-12)

인계 문서가 걱정한 `tools/check_instructions.py` 522행의 `_place` 진단은 `uv run pyright tools/check_instructions.py`가 오류 0으로 끝나 타입체크의 오류가 아니었다(편집기만의 진단).

`code-review`를 base `4b02bbe29`(HEAD와 같다)로 돌렸다. 추적 파일 변경 7, 커밋 0, 미추적 6(새 스킬 둘, 카나리아 명세 둘, 티켓, 일지). 표준 축은 sonnet·high, 명세 축은 기본 모델이다.

**고친 것** (둘 다 짚은 것은 하나로 센다):

- `pr-merge` 1단계가 `state`를 읽지 않아 병합 뒤 끊겼다 다시 들어오면 4단계에 닿지 못했다(병합된 PR은 `mergeable`이 `UNKNOWN`이라 5번 재조회 뒤 중단한다. 표준 Major 1, 명세 c2). `state`를 읽고 `MERGED`면 2·3단계를 건너뛰어 4단계로 가고, `CLOSED`면 중단하게 했다. 큐·auto-merge로 올린 뒤에도 같은 갈래로 돌아온다(표준 9).
- 3단계 머리 SHA 대조가 출시 PR·되돌려 합치기 PR에서 틀리게 멈췄다(머리가 dev·main이라 로컬 HEAD가 원격보다 뒤처질 수 있다. 표준 Major 2). 티켓 PR과 핫픽스만 로컬 HEAD와 대고, 둘째 종류는 `gh pr view`가 방금 준 값을 쓰게 했다. 값은 2단계 대기 뒤에 다시 읽는다(명세 c3).
- 1단계의 충돌·차단이 출시 PR·되돌려 합치기 PR을 `pr-feedback`으로 보냈다. 그 스킬은 머리 브랜치에 base를 병합하므로 dev를 main에 합친다(표준 Major 3, 명세 c5). 이 두 종류는 사용자에게 넘기게 했고, `UNSTABLE`은 차단이 아니라고 적었다(`merge.md` 워크트리 1과 같다).
- 티켓 PR의 머리 접두 목록이 `operations.md` 18보다 좁았다(표준 4, 명세 c4). "머리가 dev·main·`hotfix/*`가 아닌 브랜치"로 고쳤다.
- 4단계가 출시 PR·되돌려 합치기 PR의 "3을 건너뛴다" 예외를 옮기지 않았고 원격 브랜치 정리도 하지 않았다(명세 a2, 표준 6). 티켓 PR·핫픽스만 `merge.md` 워크트리 3으로 원격 브랜치를 확인하게 했다.
- `gh pr checks`·`gh pr view --comments`·`gh pr diff`에 번호가 없어 다른 브랜치에서 부르면 엉뚱한 PR을 본다(명세 c1). `pr-merge`와 `pr-feedback`의 명령에 번호를 줬다.
- `pr-feedback` 4단계에 봇 둘째 회차부터 Critical·Major만 고치는 규칙의 포인터를 더했다(표준 8).
- `merge.md` 워크트리 2의 끝 문장이 "대신 `/pr-merge`를 쓴다"로 직접 치는 명령과 겹쳤다(표준 7, 명세 c7). "1과 2를 `/pr-merge`가 대신 해도 되고, 3~5는 이 절이 정하며, 병합 명령은 한 번만 친다"로 고쳤다.
- 새 프로젝트가 복사할 글이 `/pr-merge`를 부르는데 복사 목록에 두 사본이 없었다(명세 a1). `KICKOFF.md` 복사 목록에 항목 한 줄을 더하고 티켓 결과 2에 이유를 적었다.

**남긴 것**:

- `pr-merge` 1단계가 `merge.md` "병합 방법"의 표를 다시 적었다(표준 5, Duplicated Code). 스킬이 혼자 읽혀야 하고 카나리아 명세가 그 문장을 스킬 본문에서 찾으므로 두되, 원천이 `merge.md`라고 적었다.
- 런북 본문(`KICKOFF.md` 단계, `kickoff/`)이 사용자 수준 이름을 부르는 것은 새 프로젝트가 사본을 들이기 전까지 맞다. 불일치는 티켓 결과 2에 적었다.

**새로 쓴 사실 문장** (PR 직전 리뷰에 밀 주장): `pr-merge` 1단계의 "병합된 PR은 `mergeable`이 `UNKNOWN`이다"(표준 축이 PR #541을 `gh pr view`로 읽어 `state:MERGED`와 `UNKNOWN` 둘을 보았다고 보고했다. 이 세션이 다시 재지는 않았다). `pr-feedback`이 머리 브랜치에 base를 병합해 출시 PR에서는 dev를 main에 합친다는 문장(`pr-feedback` 5단계의 코드와 `merge.md` 4의 금지 문장을 읽어 적었다). `KICKOFF.md` 새 항목의 "복사하지 않으면 새 프로젝트에서 `Unknown skill`이 난다"(카나리아 대조군이 같은 오류를 내서 본 것이고 새 프로젝트로 재 보지는 않았다).

## 검증

셀프 리뷰 반영 뒤 이 워크트리에서 손으로 쳤다(2026-11-12). `uv run ruff check .`와 `uv run ruff format --check .`는 통과했다(2122개 파일). `uv run python tools/run_checks.py`는 종료 코드 0이고 열 줄이 모두 `Passed`였다(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright 둘, run-hooks, pytest 490초, web-verify 653초). 카나리아는 `pr_merge_skill_kinds.toml`을 고친 본문으로 다시 돌려 통과 4였다(티켓 결과 3). 관리 화면·위젯·질문 페이지 e2e와 사진 비교는 이 변경이 `web/`을 건드리지 않아 돌리지 않았다(CI가 돈다).

## 회고

후보 일곱. 승인 없음, 기각 일곱, 넘김 없음. 만료할 항목은 작업 트리와 `origin/dev` 두 셈 모두 없었다(`uv run python tools/queue_open_rows.py`와 `--ref origin/dev`, 둘 다 "만료할 항목: (없음)"). 승인이 없어 항목 찾기와 대기열 쓰기는 하지 않았다.

1. **기각.** `pr-merge` 초안이 병합 뒤 끊겼다 다시 들어오는 갈래(`state:MERGED`)와 출시 PR의 머리 SHA 대조를 놓쳤고, 표준 축이 잡았다. 코드 리뷰 브리프의 "갈래 밟기"가 잡도록 둔 기준이라 리뷰가 제 몫을 했다.
2. **기각.** 스킬 이름을 바꾸면 복사해 가는 글이 부르는 이름이 어긋나는데 `KICKOFF.md` 복사 목록을 안 고쳤고, 명세 축이 잡았다. 브리프의 주장 검증 3("계약 변경이 거짓으로 만드는 문장")이 잡도록 둔 기준이다.
3. **기각.** 인계 문서가 걱정한 `tools/check_instructions.py` 522행의 `_place` 진단은 `uv run pyright tools/check_instructions.py`가 오류 0이라 타입체크 오류가 아니었다. 실수나 비용이 난 사건이 아니다.
4. **기각.** `git fetch ...; git merge-base ...; git diff --stat $(...)` 복합 명령을 워크트리 가드가 거부했다. `CLAUDE.md` 환경 함정에 있는 앱 가드이고 단일 명령으로 나눠 쳤다.
5. **기각.** 주 체크아웃 경로의 `KICKOFF.md`를 Edit하려다 앱이 워크트리 사본을 쓰라고 거부했다. 이미 있는 앱 가드가 그 자리에서 막았다.
6. **기각.** 파이프를 쓴 `pyright ... | tail`에 훅이 경고했고, 영어 중간 문장에도 경고가 붙었다. 이미 있는 훅이 알렸다.
7. **기각.** 습관대로 `/git-pr-merge`를 쳐서 사용자 수준 원본이 도는 사건은 아직 난 적이 없다. 사건 없이 떠올린 것이다. 나면 회차를 세는 항목으로 둔다.

## 다음

이 PR(base dev)을 병합한 뒤 `next-session`이 다음 지시문을 낸다. 이어받을 것:

- **처음 쓰는 병합.** 이 PR은 `/pr-merge`가 아직 병합되지 않은 상태라 워크트리의 병합 길(`merge.md` "워크트리에서 병합할 때" 1~3)로 했다. 병합 뒤 주 체크아웃이 새 `pr-merge`로 처음 병합하는 PR에서 스킬이 실제로 병합되고 4단계가 도는지 본다. 카나리아는 스킬이 실리는지만 보았고 병합 동작은 보지 않았다.
- **습관의 값.** `/git-pr-merge`를 치면 사용자 수준 원본이 돈다(squash, `--delete-branch`, main 고정). 막거나 알리는 훅은 사건이 난 뒤에 회차를 센다(`CLAUDE.md` 교정 루프).
- **남은 이름 불일치.** 새 프로젝트가 `KICKOFF.md` 복사 목록으로 사본을 들이면 런북 본문(`KICKOFF.md` 단계, `kickoff/runner.md`, `kickoff/pitfalls.md`)은 사용자 수준 이름을 부르고 복사된 글은 `/pr-merge`를 부른다. rag-engine 쪽 규약 맞추기(2026-11-11 결정)를 할 때 이 사본 둘도 차이로 알린다.
- **다음 harness 티켓.** `dev-release-pr-step`(워크트리가 있다)이 출시 PR 단계를 정한다. 거기서 출시 PR을 `/pr-merge`가 `--merge`로 병합하는 길과 둘째 출시 PR의 `BEHIND`를 다룬다.
- **chore 계기.** 대기열 0420이 13회차다.
