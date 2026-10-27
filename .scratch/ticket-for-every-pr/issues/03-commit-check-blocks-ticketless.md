# 03: 커밋 검사가 티켓 없는 커밋을 막는다

**What to build:** 티켓 없이 하네스나 제품 코드를 커밋하면 커밋이 멈추고, 화면에 무엇이 빠졌는지와 할 일이 뜬다. `chore/NNN-<slug>`와 `feature/NN-<slug>` 브랜치는 그 이름의 티켓 파일이 이 브랜치의 변경에 들어야 지난다. `docs/<slug>` 브랜치는 면제 모양만 바꾸었거나 harness 티켓을 하나라도 실었으면 지난다. main, 분리 HEAD, 원격이 없는 클론, 규약 전에 딴 브랜치는 지난다. 변경을 마치고 손으로 친 러너(`uv run python tools/run_checks.py`)에서도 같은 판정이 지금 색인으로 돈다. 막히는 커밋은 러너 한 바퀴를 다 기다린 뒤에 글이 보인다(사용자가 골랐다).

근거는 `.scratch/ticket-for-every-pr/spec.md`의 "이음매", "면제 모양", "커밋 검사", "전환"과 각 절의 2026-10-21 명세 검토 주석, Testing Decisions의 "커밋 검사"와 "변이", 사용자 스토리 5·6·9·33·34·35·38·39다. 결정은 ADR 0037이다. 진짜 커밋으로 시험하는 것과 러너 안에 두는 것은 사용자가 골랐다. 병합 커밋의 측정은 `.scratch/ticket-for-every-pr/probes/merge_commit/`이다.

이 티켓은 CI를 다루지 않는다. 독스트링과 문서에 "CI가 같은 판정을 한다", "CI가 잡는다"를 적지 않는다. 그 문장과 잡은 04가 붙인다. 이 티켓과 04 사이의 main에서는 훅을 건너뛴 커밋이 오늘처럼 PR까지 지나고, `.pre-commit-config.yaml`의 러너 훅 주석이 그은 경계(CI도 도는 검사)는 04를 기다린다.

**Blocked by:** 01, 02

**Status:** done

### 검사

- [x] **자리.** 새 검사(id `check-ticket`, 파일은 `tools/check_ticket.py`)를 `tools/run_checks.py`의 `CHECKS`에 더한다. pre-commit에 새 항목을 두지 않는다. 건너뛰기는 그 id의 `SKIP`이다. 표준 라이브러리만 쓰고 git을 부를 때마다 시간 제한을 둔다(`.claude/rules/tools.md`)
- [x] **바뀐 파일(C).** 이 브랜치와 `origin/main`의 merge-base에서 지금 색인까지의 차이이고, 이름 바꾸기는 지운 것과 더한 것 둘로 센다(rename 감지를 끈다). 병합을 마무리하는 커밋이면 merge-base를 `git merge-base origin/main HEAD <MERGE_HEAD>`로 구하고, `MERGE_HEAD`는 작업 트리 루트의 경로가 아니라 ref 이름(`git rev-parse -q --verify MERGE_HEAD`)으로 찾는다(링크드 워크트리에서는 그 워크트리의 git 디렉터리에 있다)
- [x] **판정 일곱**을 명세의 차례 그대로 둔다. 1 분리 HEAD이거나 main이면 지남, 2 `origin/main`이 없으면 한 줄을 알리고 지남, 3 전환이면 지남, 4 C가 비었거나 모두 면제 모양이면 지남, 5 티켓 모양 브랜치는 그 티켓이 C에 있고 색인에 남아 있어야 지남(`feature/NN-<slug>`는 `.scratch/<어느 slug>/issues/NN-<slug>.md`, `chore/NNN-<slug>`는 `.scratch/harness/issues/NNN-<slug>.md`), 6 `docs/<slug>`는 C에 harness 티켓이 하나라도 있으면 지남(번호와 브랜치는 맞대지 않는다), 7 그 밖은 막음
- [x] **면제 모양**은 명세 "면제 모양"의 표 그대로다. `.scratch/<slug>/`로 시작하는 네 모양은 `<slug>`가 `harness`이면 면제가 아니다. 표에 없는 기능 폴더의 파일(`design.md`, `mock/` 등)은 면제가 아니다
- [x] **전환.** 이 브랜치의 첫 자기 커밋(`origin/main`에 없는 커밋 가운데 가장 오래된 것)의 부모 트리에 이 검사의 파일이 없으면 지나고 그렇다는 한 줄을 낸다. 자기 커밋이 없으면 HEAD를 그 자리로 본다. merge-base의 트리로 가르지 않는다(main을 합치는 순간 막힌다). "가장 오래된 것"은 커밋 날짜가 아니라 위상 순서로 가른다. 부모가 모두 `origin/main` 쪽에 있는 자기 커밋이다(명세가 날짜로 가르기를 거부한 까닭인 시계와 rebase를 그대로 피한다). 규약 전 브랜치를 검사가 든 main으로 rebase하면 딴 자리가 옮겨져 판정을 받는다. 막히면 막는 글의 길(티켓을 쓰고 브랜치 이름을 바꾼다)을 따른다(명세 "전환"의 2026-10-21 주석)
- [x] **막는 글(stderr).** 면제 모양 밖의 바뀐 파일(앞의 열 개와 나머지 수), 브랜치가 티켓 모양이면 찾은 티켓 경로, 티켓을 쓸 자리와 번호를 받는 명령(`uv run python tools/sibling_overlap.py`), 브랜치 이름을 바꾸는 명령(`git branch -m <새 이름>`. 이미 푸시했으면 새 이름으로 푸시하고 옛 원격 브랜치를 지운다. 열린 PR이 있으면 사람에게 묻는다), 규약 원천(`docs/agents/issue-tracker.md`)을 싣는다. 가리키는 티켓 파일이 디스크에는 있는데 C에 없으면 알림 하나를 더한다. 그 티켓의 `Status:`를 in-progress로 고치고(이미 고쳤으면 그대로) 그 파일을 스테이지하라는 글이다. pre-commit은 훅이 도는 동안 스테이지하지 않은 고침을 치워 고친 것과 고치지 않은 것이 커밋에서 갈리지 않는다(명세의 2026-10-21 주석)
- [x] **독스트링.** 판정, 면제 모양(이것이 모양의 원천이다), 전환(위상 순서, rebase), 러너에 둔 값(막히는 커밋은 러너 한 바퀴 뒤에 글이 보이고 고친 뒤 한 바퀴를 더 돈다. 대기열 192가 곧바로 멈추기를 들이면 사라진다), 못 보는 것(pre-commit을 거치지 않은 커밋은 지난다. 티켓의 내용은 보지 않는다. `docs/` 브랜치에 harness 티켓을 하나 쓰고 회고 반영이 아닌 일을 실어도 지난다. 면제 모양만 고치는 PR은 고침이 무엇이든 지난다. 지나는 갈래가 내는 한 줄(전환, `origin/main` 없음)은 러너가 통과한 검사의 출력을 찍지 않아 커밋과 손으로 친 러너에서 보이지 않고, 검사를 바로 칠 때 보인다)

### 시험(진짜 커밋)

- [x] **이음매.** 임시 저장소(원격 하나와 그 main)를 만들고 `.git/hooks/pre-commit`에 이 검사를 부르는 짧은 심을 두고(실행 권한을 준다. 리눅스의 git은 실행 권한이 없는 훅을 건너뛴다. `.claude/rules/tests.md`), 진짜 `git commit`을 쳐서 막힘·지남과 막는 글의 낱말(빠진 티켓 경로, 번호 명령, 브랜치 명령)을 본다. git을 띄울 때 `tools.run_hooks.REPO_LOCATION_VARS`를 벗긴다. 선례는 `tests/tools/test_hook_edit_during_commit.py`, `tools/run_hooks.py`의 `committing_repository`, `tests/tools/test_sibling_overlap.py`, `tests/tools/test_tidy_checkouts.py`다
- [x] **사례.** 면제 모양만 바꾼 커밋, 면제 모양에 harness 폴더의 명세·프로브를 섞은 커밋(막힘), `chore/NNN-<slug>`에서 그 티켓을 실은 커밋과 빠뜨린 커밋, 다른 번호의 티켓을 실은 커밋(막힘), `feature/NN-<slug>`에서 다른 기능 폴더의 같은 이름 티켓, `docs/` 브랜치의 harness 티켓, 앱 워크트리 모양(`claude/<이름>`)의 막힘, 고치지 않은 `ready-for-agent` 티켓의 커밋(알림), 디스크에 쓰고 한 번도 `git add`하지 않은 새 티켓의 커밋(알림. 새 harness 티켓에서 가장 흔한 길이다), 일부 파일만 커밋하는 길(`git commit <경로>`), `-a`, `--amend`, 이름 바꾸기, 분리 HEAD, `origin/main` 없음, 규약 전 브랜치와 그 브랜치가 main을 합친 뒤(지남), 그 브랜치를 검사가 든 main으로 rebase한 뒤(판정을 받는다), 커밋 날짜가 위상 순서와 어긋난 자기 커밋(`GIT_COMMITTER_DATE`로 만든다. 위상 순서로 첫 자기 커밋을 고른다), 면제 브랜치가 `origin/main`을 합치며 충돌을 풀고 친 커밋(main이 면제 밖 파일을 들여와도 지남)을 일반 클론과 링크드 워크트리에서 하나씩, 충돌 없는 병합(훅이 돌지 않아 지남), 워크트리에서의 커밋
- [x] **진짜 pre-commit의 사례 둘.** 임시 저장소에 pre-commit을 깔고 이 검사를 부르는 설정으로(그 설정은 이 저장소의 러너 `main`을 부르지 않는다. `main`은 작업 폴더를 이 저장소의 루트로 고정해 임시 저장소가 아니라 진짜 저장소를 판정한다. 러너의 `run`에 이 검사 하나와 임시 저장소를 작업 폴더로 넘겨 부르는 짧은 진입 스크립트를 두고, 검사의 명령은 절대 경로로 준다), 티켓을 고치고 스테이지하지 않은 커밋이 위 알림으로 막히는 것을 본다. 심은 pre-commit의 치우기를 거치지 않는다. 같은 설정으로 일부 파일만 커밋하는 길(`git commit <경로>`)에서 git이 훅에 준 임시 색인(`GIT_INDEX_FILE`)이 pre-commit과 러너를 거쳐 검사까지 닿아, 그 경로의 티켓만 실은 커밋이 지나고 빠뜨린 커밋이 막히는 것을 본다(명세 검토가 재지 못한 것. 러너는 자식에게 환경을 그대로 물려준다는 독스트링만 읽었다). 검사는 git을 부를 때 이 변수를 벗기지 않는다
- [x] **빨강을 먼저 본다.** 검사를 러너에 넣기 전, 또는 판정 5의 맞대기가 없는 첫 판으로 막혀야 하는 사례가 빨간 것을 본다

### 변이

- [x] `.scratch/ticket-for-every-pr/probes/check_ticket_mutations.toml`에 다섯을 두고 `tools/mutate.py`로 각각이 위 사례 하나를 빨갛게 하는 것을 본다. 판정 5의 맞대기를 지운 변이, 면제 모양에서 harness를 빼는 조건을 지운 변이, 전환의 트리를 merge-base로 바꾼 변이, 병합을 마무리하는 커밋의 merge-base에서 `MERGE_HEAD`를 뺀 변이, `MERGE_HEAD`를 작업 트리 루트의 `.git/MERGE_HEAD` 경로로 찾게 바꾼 변이(링크드 워크트리 사례가 빨개진다)다. 표지는 고른 단언이 실패할 때만 나오는 문구다(`.claude/rules/probes.md` 첫 항목). 그 폴더의 `README.md` 표에 변이 표의 줄을 더한다(`docs/agents/issue-tracker.md` 프로브와 근거)

### 문서

- [x] `docs/agents/issue-tracker.md` 규약 절에 면제 모양의 원천이 이 검사의 독스트링이라는 문장을 넣는다
- [x] `docs/constitution/operations.md` 가드레일 절의 자동 검사 목록에 커밋 검사(러너의 검사)를 더한다. CI 잡이 돈다는 말은 붙이지 않는다. 헌법 patch 판을 올린다(번호 도구의 "형제가 쓴 가장 높은 헌법 판"보다 높게)
- [x] **러너 검사의 수**를 든 살아 있는 자리를 고친다. `CLAUDE.md` 검증 명령 절의 게이트 수(열넷)와 pre-commit이 돌리는 수(일곱), 루트 `README.md` 원천 표의 커밋마다 도는 검사 수(여덟), `tools/run_checks.py` 독스트링의 검사 수다. 커밋 검사를 `CLAUDE.md`의 "CI도 돌리고" 무리에는 넣지 않는다(04). 고친 뒤 저장소를 다시 grep해 그 수를 든 다른 살아 있는 자리가 없는지 본다
- [x] `KICKOFF.md`의 검사 러너 줄(`CHECKS`)에 커밋 검사를 더한다

### 검증

- [x] **전환의 실제 실행.** 이 티켓의 브랜치는 검사가 없던 자리에서 땄다. 검사를 러너에 더한 뒤 이 브랜치에서 검사를 바로 쳐서(`uv run python tools/check_ticket.py`) 전환의 한 줄을 내고 0으로 끝나는 것을 보고, 그 뒤의 커밋에서 러너가 이 검사를 `Passed`로 찍는 것을 본다. 러너는 통과한 검사의 출력을 찍지 않아(`tools/run_checks.py`의 `_report`) 커밋에서는 한 줄이 보이지 않고, 이 브랜치는 판정 5로도 지나므로 `Passed`만으로는 전환으로 지났는지 가르지 못한다. 둘 다 일지에 적는다
- [x] 첫 편집으로 이 티켓의 `Status:`를 `in-progress`로 바꿔 첫 커밋에 싣고, PR을 열기 전에 `done`으로 바꾼다
- [x] 원칙 III를 지킨다
- [x] 검증 명령이 모두 초록이다
