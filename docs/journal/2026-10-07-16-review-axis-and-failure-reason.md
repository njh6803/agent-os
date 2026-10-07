# 2026-10-07 (16) 리뷰 축이 빌 때의 대체와 실패 까닭 단언

next-session 지시문으로 연 새 세션의 하네스 chore다. 대기열 136·144를 한 PR로 닫고 123·137에 회차를 더한다. 세션은 주
체크아웃에서 열렸고, 지시문대로 `tidy-checkouts`를 먼저 돈 뒤 `EnterWorktree(name=review-axis-and-failure-reason)`로
들어가 `origin/main`(`394c465`, #163)에서 `chore/review-axis-and-failure-reason`을 땄다. 작업 중에 #162가 병합되어
`61884df`로 빨리 감았다(대기열 파일을 고치기 전이라 겹침이 없었다). 첫 커밋 뒤에 #165(`5c069d4`)가 들어와 병합했다.
#165가 136에 3회차(일지 13)를 더해 대기열 행이 충돌했고, 이 브랜치의 회차(일지 15)와 합쳐 4회차로 풀었다. 승인받은 ADR
이력의 "회차 셋, PR #156·#158·#163"도 "회차 넷"으로 고쳤다. 결정은 그대로다.

> 사용자: "대기열 136·144를 한 PR로 반영하고 123·137에 회차를 더한다(리뷰 축이 빌 때의 대체, 실패 까닭 단언)"

## 첫 턴의 tidy-checkouts

- **루트.** `chore/checkout-persist-credentials`에 스테이지된 일지 수정이 있어 깨끗하지 않았다. 루트는 건드리지 않았다.
  주 체크아웃 미갱신: 루트는 `chore/checkout-persist-credentials`(깨끗하지 않다). 이 세션이 진행되는 동안 다른 세션이
  루트를 `61884df`로 옮겼다(`tools/sibling_overlap.py`의 출력).
- **워크트리.** 실행 중인 세션 하나의 제목("Disable checkout credential persistence in CI jobs")이 체크아웃된 어느 브랜치와도
  맞지 않아, 스킬 3의 판정 3대로 어느 워크트리도 지우지 않았다. 판정 1을 지난 후보는 `01-tokens-story-seam-and-buttons`,
  `02-visual-comparison-gate`, `canary-procedure-and-runner`, `confident-wright-2d3ebf`, `mutation-check-and-launch-notice`,
  `open-session-quitting-app`, `parallel-open-session`, `pre-commit-fetch-and-empty-scope`, `probe-conventions`,
  `retro-hook-and-mutation-files`, `silly-carson-627e95`, `tidy-before-worktree`, `tidy-checkouts-tool`이고, 사람에게
  넘길 것은 prunable `05-admin-hides-decision-for-end-user`, PR 머리가 다른 `skill-check-and-retro-section`, 분리 HEAD
  `unruffled-lalande-9017fa`다.
- 이 스킬은 루트의 옛 사본(#163 전)이었다. 루트가 main이 아니어서 #163의 `tools/tidy_checkouts.py`를 부르는 판이 실리지
  않았고, 판정은 스크래치 스크립트로 했다. 지운 것이 없어 결과는 같다.

## 어떻게 했나

- **136의 버그·성능 대체는 사용자가 골랐다.** 행이 "이 행을 닫는 세션이 따로 정한다"고 맡겼다. 넷을 보였다. 프로젝트
  서브에이전트, CodeRabbit을 한도 뒤에 다시 부르기, 사용자 설치 플러그인 `code-review:code-review`, 대체하지 않기.

  > 사용자: (고른 것) "서브에이전트 (Recommended)"

  플러그인은 저장소 밖이라 클라우드 세션에 없고 성능을 보지 않는다. 다시 부르기는 #162에서 리뷰를 받았지만 #163에서는
  다시 불러도 막혔다. 서브에이전트는 `coderabbit-review`와 같은 트리아지(유효·오탐·보류)라 본 세션이 두 결과를 같은
  방식으로 반영한다.
- **123·137의 회차는 지시문을 따랐다.** 일지 15의 회고는 `cd` 실수와 이유를 안 보는 테스트를 "1회차, 일지에만"으로 적었다.
  그 세션은 두 사건이 이미 대기열에 있는 줄 몰랐고, 다음 지시문이 "cd 실수는 123의 2회차, 이유를 안 보는 테스트는
  144의 4회차"로 바로잡았다. 137의 2회차는 #163의 claude-review가 네 회차 연속 새 Minor를 낸 것이다(일지 15 "PR 리뷰
  반영"). 123은 3회차가 되면 훅 후보로 자리를 정한다.
- **144는 사용자가 "규칙으로"를 골랐다.** `CLAUDE.md` 교정 루프대로 `CODING_STANDARDS.md`의 한 줄은 그 말 뒤에만 넣는다.

  > 사용자: (고른 것) "규칙으로"

  테스트 쪽은 판단 기준(리뷰가 본다), 탐침 쪽은 `docs/agents/issue-tracker.md`의 프로브와 근거 절에 두었다. 기계 판정은
  거짓 양성이 많아 두지 않았다. 종료 코드만 보는 단언과 까닭까지 보는 단언을 문법으로 가르지 못한다.
- **ADR 0006에 `## 이력` 절을 새로 두었다.** 0006의 옛 `## 개정 이력`은 `tools/check_adr_pointers.py`가 이력 절로 보지
  않아, 본문 포인터가 "가리킨 이력 제목이 없다"로 빨갰다. 0005처럼 파일 끝에 `## 이력`을 두고 그 아래 `###`로 썼다. 초안의
  승인은 대기열 126대로 셀프 리뷰를 반영한 뒤에 물었다. 리뷰가 이력의 PR 서술을 두 번 고쳤으므로, 먼저 물었다면 승인받은
  글이 바뀌었을 것이다.

  > 사용자: (고른 것) "승인"

## 바꾼 것

- `.claude/agents/bug-perf-review.md`: 새 서브에이전트. 범위 잡기, 실패 시나리오 찾기, 트리아지, 보고 형식.
- `docs/constitution/operations.md` 리뷰 파이프라인 2단계(대체 둘)와 초록 착시의 CodeRabbit 한도 항목.
  `docs/constitution/README.md` 3.0.19.
- `.github/PULL_REQUEST_TEMPLATE.md`의 `coderabbit-review` 줄, `CODING_STANDARDS.md`(판단 기준 한 줄, 리뷰 관점 끝 줄),
  `docs/agents/issue-tracker.md` 프로브 절, ADR 0006 이력과 본문 포인터.
- 새 서브에이전트를 가리키는 자리: `README.md` 트리, `KICKOFF.md`(구조 표, 복사 목록, 기능 순서 7),
  `.claude/skills/to-tickets/SKILL.md` 1단계의 순서.
- `.scratch/retro-queue.md`: 136·144 닫힘, 123·137 회차.

## 잔존 grep

옛 문장("축이 비는 것을 PR 체크리스트에 그대로 적는다", "CLI 슬라이스 리뷰 결과를 그 PR 코멘트로 링크", "좌석이 있을 때만",
"없으면 돌리지 않고 그 사실을 적는다", "PR 직전 CodeRabbit CLI가 맡는다")을 md·yml·py·toml·ts에서 찾았다. 남은 것은
기록(일지, 닫힌 대기열 행, ADR 0006의 2026-09-21 항목과 0009)과 `KICKOFF.md` 8단계의 좌석 사실, 그리고
`.github/workflows/claude-code-review.yml`의 2행 주석과 59행 프롬프트다. 그 파일은 바꾼 PR을 리뷰 봇이 건너뛰어 별도
PR이어야 하므로 작업 칩으로 넘겼다(같은 파일의 대기열 146과 묶을지 그 세션이 본다). `coderabbit-review`가 좌석 없음으로
끝나는 자리는 이 PR에서 대체 안내를 붙였다.

## 검사

- 검증 명령: `uv run pytest -q` 1846 통과(7 deselected), `ruff check`·`ruff format --check`, `pyright`, `lint-imports`,
  `pnpm -C web verify`(22파일 312개), 지침 검사, ADR 포인터 검사가 모두 초록이다. 셀프 리뷰를 반영한 뒤에도 같은 수로
  다시 돌았다. 판정 명령은 파이프 없이 돌리고 로그 파일로 봤다.
- `ruff format`이 본 파일이 464에서 465로 늘어 확인했다. `--verbose` 출력을 보니 이 판의 `ruff format`은 마크다운도 세고,
  그 사이에 이 일지를 새로 만들었다. `ruff check`는 추적한 파이썬 파일 190개와 `pyproject.toml`을 그대로 봤다.
- **새 서브에이전트의 실제 실행.** 이 세션은 주 체크아웃에서 시작해 워크트리로 들어와 서브에이전트도 주 체크아웃의 옛
  사본이 실린다(`operations.md` 모드 표). 실제로 이 세션의 `coderabbit-review`는 새로 붙인 대체 안내를 내지 않았고,
  `bug-perf-review`는 목록에 없었다. 그래서 워크트리에서 `claude -p`(`--setting-sources project,local --strict-mcp-config
  --model sonnet`, 읽기 전용 git 명령과 읽기 도구만 허락)를 띄워 그 서브에이전트를 부르게 했다. init의 `agents`에
  `bug-perf-review`가 있었고, `subagent_type: bug-perf-review` 호출이 정의한 형식(기준과 범위의 첫 줄, 시나리오·근거·제안,
  끝의 오탐과 요약)으로 보고를 냈다(스크래치 스크립트, 손으로 봤다). 그 보고는 아래 PR 직전 절에 있다.

## 셀프 리뷰

`/code-review`(기준 `61884df`, 수정 10·미추적 1, 커밋 0). 표준 축(sonnet) Minor 4·Nit 4와 smell 셋, 명세 축 Minor 2·Nit 2였다.
Critical·Major는 없었다.

- **고친 것.**
  - 명세 Minor: "한도에 걸린 PR이 셋 이어졌다"는 회차 셋을 이어진 PR로 쓴 것이었다. 그 사이의 #157과 다시 불러 리뷰를
    받은 #162가 빠져, ADR이 거부한 "다시 부르기"의 근거가 한쪽뿐이었다. 그 문장을 고치며 "#157도 한도로 리뷰가 없었다"와
    "#164는 리뷰를 받았다"를 새로 썼는데, 표준 축이 둘 다 일지와 다르다고 짚었다(#157은 둘째 회차에 리뷰를 받았고, #164는
    일지가 다시 요청한 데까지만 적는다). 일지가 적은 것만 남겼다.
  - 표준 Minor: 대체의 계기가 좌석·한도뿐이라 `coderabbit-review`의 미설치·인증 오류 길에서 축이 비었다. 계기를 "미설치,
    로그인·좌석 없음, 한도 초과"로 넓히고, 그 에이전트의 안내는 단계마다가 아니라 "CLI 없이 끝나는 모든 길" 한 줄로 모았다.
  - 표준 Minor: `bug-perf-review`가 `git diff --stat`으로 범위를 잡아, 긴 경로가 줄고 한글 경로가 8진수로 나와 다음 명령에
    넘길 수 없었다. `-c core.quotepath=false`와 `--name-only`로 바꿨다.
  - 표준 Minor: `KICKOFF.md` 체크리스트의 "서브에이전트 둘"을 셋으로. 표준 Nit: `CODING_STANDARDS.md` 판단 기준 머리에 뒤에
    더한 줄의 표시법, "같은 보고 형식"을 "같은 트리아지"로, ADR 0006의 두 이력 절에 안내 한 줄. 명세 Nit: PR 템플릿
    리뷰어 참고의 "PR 직전 CLI 결과", issue-tracker 항목에서 승인 문구 밖의 쓰기 의무 한 구절을 뺐다.
- **남긴 것.**
  - 대체 둘의 이름이 여러 문서에 다시 적힌 것(Shotgun Surgery). 런북·템플릿·스킬은 실리는 때가 달라 각자 포인터가
    필요하고, 원천은 `operations.md` 2단계다.
  - `bug-perf-review`의 트리아지와 보고 모양이 `coderabbit-review`와 겹치는 것. 본 세션이 두 결과를 같은 방식으로 반영하려고
    맞췄다.
  - `CLAUDE.md:60`의 "PR 직전 CLI". 2단계 제목을 가리키는 포인터라 그대로다.
  - `claude-code-review.yml`의 두 자리(위 잔존 grep).

## PR 직전 보안·버그·성능 축

`coderabbit-review`는 `Seat: not assigned`(Plan: Free)라 1단계에서 멈췄다. 그래서 이 PR이 세우는 대체 둘을 처음으로 돌렸다.

- **버그·성능(`bug-perf-review`, 위 `claude -p`).** 범위 15개 파일, 유효 2·보류 1이었다. 고친 것: `coderabbit-review`의 대체
  안내가 종료 길을 열거만 해 리뷰 도중의 비정상 종료에서 안내가 빠진다는 것(일반형 "findings를 내지 못하고 끝나는 모든
  길"로), 이 일지의 빈 절. 보류였던 "새 세션에서 불리는가"는 그 실행 자체가 답이다.
- **보안(`/security-review`).** 커밋 전에 처음 불렀을 때 그 명령이 모은 diff와 바뀐 파일 목록이 비었다. 이 브랜치에는
  미커밋 변경만 있었고, 커밋 목록에는 이 브랜치에 없는 `origin/main`의 #165가 나왔다. 그 명령은 커밋된 범위만 모은다고
  보고(어림), `operations.md` 2단계와 PR 템플릿에 "커밋한 뒤에 돌린다"를 적었다. 그 실행에서는 실제 diff를 하위 작업에 직접
  넘겨 같은 기준으로 봤고 발견이 없었다(새 서브에이전트의 도구는 `coderabbit-review`와 같고 나머지는 문서다). 커밋하고
  #165를 병합한 뒤(`58f6d68`) 다시 부르자 이 브랜치의 파일 13개와 diff를 모았다(#165의 파일은 들지 않았다). 같은 기준으로
  차이를 다시 봤고 발견이 없었다.
- 새 서브에이전트는 만든 지 한참 뒤에 이 세션의 에이전트 목록에도 올라왔다. `kickoff/pitfalls.md`의 "세션 중에 만든
  `.claude/agents/*.md`" 줄과 같은 동작이다. 실제 실행 확인은 그 전에 `claude -p`로 했다.

## 다음
