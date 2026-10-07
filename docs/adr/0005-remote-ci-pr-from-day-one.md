---
status: accepted
date: 2026-09-20
---

# 원격, CI, PR은 첫날부터다

헌법 1.x는 "원격 없음, 혼자면 PR 없음, ff 병합"이었다. 2026-09-20 헌법 2.1.0에서 "원격(GitHub), CI, PR은 첫날부터. 혼자여도 같은 리듬. 팀원이 생기면 리뷰 승인 필수와 CODEOWNERS를 더한다"로 바꿨다. 이유 셋. 선행 저장소 둘(`ai-agent-platform`, `agent-runtime-platform`)이 가드레일을 나중에 붙이다 LLM 호출 0줄에서 멈췄다. 사용자의 git-pr·git-pr-merge 스킬이 이미 PR 단위 흐름이라 맞추는 비용이 0이다. 훅은 각자 설치해야 하므로 CI가 최종 판정이어야 한다.

같은 날 실측한 제약이 이 결정의 모양을 정했다. 무료 플랜의 비공개 저장소는 보호 브랜치를 못 켜므로 병합 게이트를 GitHub가 아니라 병합 스킬에 두기로 했다. 규약과 되돌릴 조건은 `docs/constitution/operations.md`의 가드레일 절.

## Consequences

- 티켓마다 `feature/<NN>-<slug>` 브랜치, 혼자여도 PR, squash 병합, main 이력은 PR 단위. 규약은 `docs/constitution/operations.md`의 "브랜치와 병합"과 "가드레일".
- 원격 생성과 시크릿 등록은 사람이 한다. 에이전트는 토큰을 다루지 않고 `gh secret list`로 이름만 본다.
- 하네스 변경 하나가 PR 하나가 되어 첫날 PR 열 개가 나왔다. 그 비용은 회고 후보 5(결정 하나가 파일 열 개)로 관찰 중이다.
- Actions 무료 분량은 계정 단위 월 2,000분이고 모든 비공개 저장소가 나눠 쓴다. 2026-09-20 PR #10에서 소진돼 잡이 시작조차 안 됐다(주석은 결제 실패나 지출 한도를 말하지만 화면은 2,000/2,000). CI가 최종 판정인 구조는 분량이 막히면 병합도 막힌다는 뜻이다. 선택지는 예산, 공개 전환, 리셋 대기였고 2026-09-21 사용자가 공개 전환을 골랐다. 공개 뒤 Actions는 무제한이고 보호 브랜치를 걸었다(필수 검사 `verify`). 게이트가 스킬에서 GitHub로 옮겨졌고 스킬은 그대로 쓴다. (바뀜: 이력 2026-09-29 "관리자 우회는 에이전트에게도 열려 있다") 런북 1단계의 플랜 확인에 남은 분량도 포함한다.

## 이력

### 2026-09-29 관리자 우회는 에이전트에게도 열려 있다

`tools/protection.json`은 `enforce_admins: false`, `required_pull_request_reviews: null`이다. 관리자 토큰으로 도는
에이전트도 main에 직접 푸시하거나 `gh pr merge --admin`으로 필수 검사를 건너뛸 수 있다(GitHub 문서상의 동작이고
재지 않았다). 로컬 `hook_git_main_commit`은 main 위의 커밋만 막는다. `operations.md` 가드레일에 이것을 적고 병합은
체크를 먼저 보는 `/git-pr-merge`로만 한다고 적었다.

켜지 않는다. Actions 분량이 떨어져 CI가 뜨지 않은 적이 있고(위 Consequences, PR #10), 켜면 그때 사람도 막힌다.
에이전트가 우회한 사건은 0건이다. 한 번이라도 확인되면 다시 본다. 런북 8단계의 "직접 푸시·삭제 금지"는 사실과
달랐다. 직접 푸시를 막는 설정(PR 필수)은 없고, 필수 검사(`verify`, strict)가 검사를 지나지 않은 커밋의 푸시를 막을
뿐이며 관리자는 그것도 우회한다. 런북을 고쳤다.

### 2026-10-06 워크트리에서는 `/git-pr-merge` 대신 같은 체크 뒤 `--delete-branch` 없이 병합한다

2026-09-29 이력은 병합을 체크를 먼저 보는 `/git-pr-merge`로만 한다고 정했다. 그 스킬의 `gh pr merge --delete-branch`는
병합 뒤 작업 폴더에서 `git checkout main`을 친다. 워크트리에서 부르면, main이 어디에도 체크아웃되어 있지 않을 때는
그 워크트리가 main을 가져가 주 체크아웃이 main으로 돌아가지 못하고, 주 체크아웃이 main이면 실패해 원격 브랜치 삭제를
건너뛴다(대기열 39, 2026-10-05 워크트리 감사 서브에이전트가 임시 저장소로 손으로 재현했다). 그래서 워크트리에서는 같은
체크(병합 가능, 검사 실패 없음, PR 머리와 로컬 HEAD의 일치)를 본 뒤 `gh pr merge <번호> --squash --match-head-commit
<HEAD>`로 병합하고, 원격 브랜치는 `git push origin --delete`로 지운다. 주 체크아웃은 그 워크트리 세션이 당기지 않고
사람이나 주 체크아웃 세션에 넘긴다. 절차의 원천은 `next-session`의 "워크트리에서 병합할 때"다. `--admin`과 직접 푸시를
쓰지 않는다는 것은 그대로다.

거부한 안. 사용자 수준 `/git-pr-merge`가 워크트리를 스스로 판정하게 고치는 것은 저장소 밖의 파일이라 이 저장소의
리뷰와 이력에 남지 않는다. 워크트리에서 `--delete-branch`를 막는 훅은 일이 난 적이 없어 막는 훅의 조건
(`.claude/rules/tools.md`)에 못 미친다. 한 번이라도 나면 다시 본다.

### 2026-10-07 pre-commit의 읽기 검사는 러너 하나가 함께 띄운다

pre-commit은 훅을 하나씩 돈다(4.6.2 `commands/run.py`의 `_run_hooks`를 읽었다). 커밋마다 도는 `always_run` 검사 일곱
(pyright, import-linter, pytest, 지침 검사, 타입 우회 검사, 훅 러너, `pnpm -C web verify`)을 차례로 돌면 145.5초이고,
한꺼번에 띄우면 가장 긴 pytest만큼인 73.7초다(`.scratch/harness/probes/precommit_parallel.py`, Linux 컨테이너 CPU 4,
일지 2026-10-07-05). 잰 트리는 `cbb6a6c`다. PR #156이 web verify에 스토리 테스트를 더한 뒤 GitHub Actions의
러너(CPU 4)에서 같은 프로브로 다시 쟀다(실행 37561588972, `.scratch/harness/probes/run_checks_ci_probe.yml`, 일지
2026-10-07-07). Linux는 차례로 115.0초, 한꺼번에 66.5초이고 가장 긴 것은 pytest였다. Windows는 240.0초와 142.5초이고
가장 긴 것은 web verify(pytest는 135.1초)였다. 함께 띄우면 바닥은 pytest와 web verify 중 긴 쪽이다.

**`.pre-commit-config.yaml`에서 일곱을 훅 하나(`parallel-checks`)로 묶고, 그 훅이 부르는 `tools/run_checks.py`가 일곱을
함께 띄운다.**

- ruff 둘은 파일을 고치므로 러너 앞에 따로 둔다. pre-commit이 훅을 순서대로 돌므로 러너는 고친 뒤의 파일을 본다. 받은
  파일만 보는 빠른 검사(마크다운 표, 줄 구분 문자, 변이 표, 인용 대조)도 따로 둔다.
- 러너는 검사가 끝난 차례로 이름·결과·시간 한 줄을 찍고, 실패한 검사는 그 줄 뒤에 모은 출력을 함께 찍는다. 하나라도
  실패하면 1로 끝난다. 훅에 `verbose: true`를 두어 통과한 커밋에서도 그 줄들이 보인다.
- pre-commit의 `SKIP` 환경 변수를 같은 id(`pyright`, `lint-imports`, `pytest`, …)로 읽어, `SKIP=pytest git commit`이
  지금처럼 통한다.
- 명령 목록의 원천은 러너의 `CHECKS` 하나다. CI(`ci.yml`)는 잡마다 명령을 직접 돌아 바뀌지 않는다. 같은 검사를 러너와
  훅에 함께 두면 커밋마다 두 번 돌므로, `CHECKS`의 명령이 글자 그대로 `entry`로 있거나 같은 id의 훅이
  있으면 pytest가 빨갛다. 옵션을 바꿔 적은 명령은 보지 못한다.
- 최상위에 `default_stages: [pre-commit]`을 두고 커밋 메시지 훅만 `stages: [commit-msg]`로 적는다. 훅마다 `stages`를
  적던 것(대기열 118)을 대신해, 새 훅이 commit-msg 단계에서 다시 도는 누락이 생기지 않는다.
- 함께 돌 때 서로 보는 파일은 Vitest의 판정자 테스트가 `web/judge-*`에 쓰는 임시 트리 하나다. 지침 검사의 `os.walk`가
  그 트리를 지나도 찾는 이름이 없고, 도중에 사라진 디렉터리는 건너뛴다(코드를 읽었다).
- 잃는 것은 둘이다. pre-commit 출력의 훅별 줄이 러너 출력 안으로 들어가고, `pre-commit run pytest`처럼 id 하나로 부르는
  길이 없어진다(명령을 직접 친다).

거부한 안은 셋이다.

- **prek.** Rust로 다시 쓴 pre-commit이고, 같은 `priority`의 훅을 함께 돈다(prek 문서 prek.j178.dev를 읽었다). 훅
  시스템을 바꾸는 것이라 체크아웃마다 설치가 바뀌고, `operations.md`의 "훅 시스템은 pre-commit 하나만 둔다"를 다시
  정해야 한다.
- **pytest-xdist만.** pytest는 약 30초가 되지만(일회성 실행으로 손으로 봤다) 나머지는 그대로 차례로 돈다. 러너와 겹치지
  않는 선택이라 따로 다시 본다(ADR 0021의 첫째 2026-10-01 이력).
- **그대로 둔다.** 대기열 118로 커밋 한 번이 약 230초에서 약 150초가 됐지만 여전히 길다.
