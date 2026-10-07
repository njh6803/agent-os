# 2026-10-07 (11) CI 잡의 체크아웃이 토큰을 .git/config 에 남기지 않는다

PR #158(design-system 티켓 02)이 띄운 작업 칩의 일이다. 주 체크아웃에서 PR #158·#160이 병합된 main(`49d9630`)으로
`chore/checkout-persist-credentials`를 땄다. 세션을 시작했을 때는 #158이 열려 있어서, 병합될 때까지 기다린 뒤 당겼다.
순번은 05~09를 #160이 썼다. 처음에는 10으로 썼는데, 셀프 리뷰가 형제 워크트리 `tidy-checkouts-tool`의 미커밋 일지
`2026-10-07-10-tidy-checkouts-tool.md`와 대기열 141을 찾아 11과 142로 옮겼다. 그 둘은 이 세션이 처음 확인한 뒤에 생겼다.

## 계기

> 사용자: "저장소 C:\project\agent 의 `.github/workflows/ci.yml` 에서 `python`, `web`, `e2e` 세 잡의 `actions/checkout@v4` 단계에 `with: persist-credentials: false` 를 더하는 chore 다. 배경: PR #158(design-system 티켓 02, 사진 비교 게이트)의 CodeRabbit 리뷰가 새 `visual` 잡에 대해 "PR 코드를 짓고 돌리는 잡이 체크아웃 토큰(GITHUB_TOKEN)을 .git/config 에 남긴다(CWE-522, Minor)"고 짚었고, 그 PR 은 `visual` 잡에만 넣었다(그 단계 위에 주석이 있다). 세 잡도 PR 코드를 실행하므로 같은 하드닝이 맞는지 보고, 각 잡이 체크아웃 뒤에 git 자격 증명이 필요한 명령(push, 인증된 fetch 등)을 쓰지 않는지 확인한 뒤 넣는다. `verify` 잡은 체크아웃하지 않는다. 시작 전에 main 을 동기화하고(PR #158 병합 뒤) CLAUDE.md 의 작업 규약을 따른다: 브랜치 `chore/<slug>`, 워크플로 변경 PR 은 claude-review 코멘트 0개 가드가 꺼지므로 코멘트를 손으로 본다(docs/constitution/operations.md 리뷰 파이프라인). 헌법을 바꾸지 않으면 버전은 그대로다."

## 확인한 것

`persist-credentials`가 정하는 것은 체크아웃이 `.git/config`에 쓰는 `http.https://github.com/.extraheader` 하나다. 막으려는
위협은 PR 코드가 그 파일을 직접 읽어 토큰을 가져가는 것이고, 끄면 잃는 것은 그 헤더로 인증하던 git 명령, 곧 그 체크아웃
안에서 `github.com`을 상대로 도는 push·fetch다. 그래서 세 잡이 체크아웃 뒤에 그런 명령을 치는지 봤다.

- **CI가 돌리는 코드의 git 호출.** `tools/`, `tests/`, `web/`(Vitest의 `web/eslint.config.test.ts`가 `ls-files`를 친다)의 git
  호출은 모두 로컬 저장소나 임시 저장소를 상대로 하고, `fetch`·`clone`·`pull`·`ls-remote`는 없다. 원격을 쓰는 것은
  `tools/run_hooks.py`의 `_unpushed_repository`와 `tests/tools/test_hook_pr_head_sync.py`의 `_푸시한_저장소`가 `remote add`로
  임시 디렉터리의 bare 저장소를 붙여 `push`하는 것뿐이라 네트워크에 닿지 않는다. PR #160이 더한 `tools/run_checks.py`와
  `tools/hook_session_web_deps.py`에는 git 호출이 없다. 첫 판은 하위 명령을 여덟으로 닫아 적었는데, 그것은 내 정규식이 잡은
  모양뿐이었다. 셀프 리뷰가 `commit`·`config`·`cat-file`·`worktree add`·`add`·`hash-object`·`update-index`·`checkout`·`reset`을
  더 찾았고, 모두 로컬이다.
- **의존성.** `pyproject.toml`, `package.json`들, `web/pnpm-lock.yaml`에 git 원천 의존성이 없다. `uv sync`와
  `pnpm install`은 레지스트리에서 받는다.
- **액션.** `setup-uv`·`pnpm/action-setup`·`actions/cache`의 캐시는 캐시 API의 토큰을 쓴다. `setup-node`는 git을 쓰지 않는다.
- **`gh`.** `verify` 잡의 `gh api`는 `GH_TOKEN` 환경 변수로 인증하고 `.git/config`를 읽지 않는다. 그 잡은 체크아웃하지 않는다.
- 저장소는 공개라서, 놓친 fetch가 있어도 인증 없이 통한다.

## 바꾼 것

- `.github/workflows/ci.yml`: `python`·`web`·`e2e` 잡의 체크아웃에 `persist-credentials: false`. 근거는 잡마다 두지 않고
  머리 주석에 한 번 둔다(잡을 더할 때 `verify`의 `needs`에 넣으라는 규약과 같은 자리). PR #158이 `visual` 단계 위에 둔 주석은 그
  자리로 합쳤다. 자격 증명이 필요한 잡이 생기면 그 잡에서만 켜고 까닭을 적는다는 것도 거기 적었다.

헌법은 바꾸지 않아 버전은 그대로다. `operations.md`의 가드레일 절은 잡 구조를 적을 뿐 체크아웃 설정을 적지 않아 고치지
않았다.

## 검사

- `ci.yml`을 PyYAML로 읽어 잡마다 체크아웃 단계의 값을 뽑았다. `python`·`web`·`e2e`·`visual`이 `False`이고 `verify`는
  체크아웃이 없다.
- 검증 명령: ruff 둘, pyright 0 errors, lint-imports 5 kept, pytest 1750 통과, `pnpm -C web verify`(Vitest 312 통과).
- 실제 실행: PR #162의 CI가 `201fef0`에서 `python`·`web`·`e2e`·`visual`·`verify` 모두 초록이다. 세 잡이 자격 증명 없이 끝까지
  돌았으니 위 확인이 맞았다.
- **PR 리뷰.** claude-review는 지적 없음이었다. main을 병합하기 전의 실행은 `ci.yml`을 바꿔 코멘트 0개 가드가 꺼졌으므로
  코멘트를 손으로 봤다.
  CodeRabbit은 첫 요청이 한도에 걸렸고, 한도가 풀린 뒤 다시 요청해 `49d9630..201fef0`을 리뷰했다. 지적 없음이고, 보안 검토가
  세 잡이 끈 자격 증명에 기대지 않는다고 적었다. CodeRabbit CLI는 좌석이 없어(`Seat: not assigned`) 돌리지 않았다. 이 일지
  줄을 더한 커밋은 CodeRabbit이 시간당 한 번인 리뷰를 다 쓴 뒤라 리뷰되지 않는다(요약 코멘트의 "0 remain").

## 셀프 리뷰

`/code-review`, base `49d9630`, 수정 2, 미추적 1, 커밋 0. 소스 파일이 없어 표준 축은 sonnet이다. 명세는 사용자 지시문이다.
명세 축은 Major 하나·Minor 둘·Nit 둘, 표준 축은 Minor 둘·Nit 넷이었다. 겹친 것은 둘이다.

- **고쳤다, 명세 Major(번호가 형제 워크트리와 겹침).** 일지 10과 대기열 141을 형제 워크트리 `tidy-checkouts-tool`이 미커밋으로
  먼저 썼다. 이 세션이 처음 봤을 때는 없었다. 둘 다 커밋 전이라 이쪽이 11과 142로 옮기고, 옛 번호를 가리킨 인용(대기열 50의
  일지 이름, 142행의 일지 이름, 회고의 대기열 번호, 작업 칩의 지시문)을 고쳤다.
- **고쳤다, 두 축 Minor(git 하위 명령의 닫힌 열거).** 내 정규식이 잡은 모양만 적었다. 판정 기준(네트워크에 닿는가)으로 다시
  적었다.
- **고쳤다, 명세 Minor(대기열 50의 회차).** 오늘 둘만 셌다. `git log -- .github/workflows/`로 행의 승인 뒤부터 다시 세어
  7회차로 적었고, main을 병합할 때 PR #164의 기점(가드가 생긴 PR #10)을 따라 #43을 넣어 8회차로 고쳤다.
- **고쳤다, 두 축 Nit(`ci.yml` 주석의 push).** `python` 잡에도 임시 bare 저장소로 가는 `push`가 있어, 주석을 github.com 을
  상대로 한 명령으로 좁혔다.
- **고쳤다, 표준 Minor·Nit.** 이 절이 없던 것, '확인한 것' 첫 문단의 보편 주장(헤더를 읽는 것은 git뿐이다. 위협은 PR 코드가
  파일을 직접 읽는 것이다), 대기열 142행의 '무엇'이 한 문장을 넘던 것. 줄을 넘는 인용은 따옴표를 풀었고, 계기의 사용자
  인용 안 따옴표는 원문대로 되돌렸다(처음에 `\"`로 바꿨었다).
- **남겼다, 표준 Nit(머리 주석의 "잡을 더해도 같고"가 생기지 않은 잡에 대한 규약).** 같은 주석에서 잡을 더할 때 `verify`의
  `needs`에 넣으라는 규약과 같은 종류이고, 새 잡을 더하는 사람이 읽을 자리다. 강제는 대기열 142가 맡는다.

## PR #164와의 충돌

이 PR이 리뷰를 마친 뒤 작업 칩의 세션이 연 PR #164(`claude-code-review.yml`의 체크아웃과 가드)가 먼저 병합되어, 이 PR이
`.scratch/retro-queue.md`에서 충돌했다. 그 세션이 이 세션에 메시지로 알렸고, 이 브랜치는 주 체크아웃에 체크아웃되어 있어
그 세션이 손대지 못했다. `git merge origin/main`으로 풀었다.

- 50행: main의 닫힌 행을 그대로 두고 승인 칸에 이 PR의 회차와 일지 이름을 더했다. 회차는 #164의 기점을 따라 8이다.
- 142행: `claude-code-review.yml`에 아직 빠져 있다는 구절이 #164로 거짓이 되어 고쳤다. #164 일지의 근거를 더해 2회차다.
  main이 더한 141·144~147행 사이에 번호대로 두었다.
- 병합 뒤 이 PR의 claude-review는 main의 새 워크플로로 돈다. 가드가 자기 파일을 바꾼 PR에서만 꺼지므로 `ci.yml`만 바꾼 이
  PR에서는 코멘트를 센다. #164 일지의 "다음"이 그 첫 실행의 로그에서 볼 셋을 적었고, `e529c59`의 실행(37586700928) 로그로
  봤다. 체크아웃 단계 안의 `Removing auth`가 includeIf 항목 넷을 지웠다. 액션이 `.claude` 등을 되살리려 `origin/main`을 받는
  fetch는 체크아웃 토큰 없이 지나갔다(공개 저장소). 가드는 건너뛰지 않고 그 실행 뒤의 `claude[bot]` 코멘트를 1로 셌다.
  claude-review는 지적 없음이다.

## 회고

후보 둘을 냈고 둘 다 승인됐다. 이 PR에서 반영하지 않고 대기열로 갔다.

> 사용자: (고른 것) "1. zizmor 검사,2. 대기열 50 회차"

1. **워크플로 하드닝을 zizmor로 판정한다(대기열 142).** 이 PR이 세운 규약은 `ci.yml` 머리 주석뿐이다. PR #158이 새 잡에서
   빠뜨린 것은 CodeRabbit이 잡았고, `claude-code-review.yml`의 체크아웃은 그때 빠져 있었다(PR #164가 고쳤다). 기계가 판정할 수
   있는 규칙이라 지침보다 검사가 맞는 층이다. 같은 도구가 과한 `permissions`와 템플릿 주입도 본다. 새 도구라 ADR이 필요하다.
   1회차였고, 일지 2026-10-07-14가 근거(액션의 지우기가 checkout v7에서 헛돌았다)를 더해 main 병합 때 2회차로 적었다.
2. **claude-review의 코멘트 0개 가드가 `ci.yml`만 바꾼 PR에서도 꺼진다(대기열 50, 8회차).** 액션은 자기 파일을 바꾼 PR에서만
   건너뛰는데 가드는 `.github/workflows/` 아래 어느 파일이든 보고 꺼진다. 가드가 생긴 PR #10 뒤에 `ci.yml`만 바꾼 PR은
   #43·#99·#103·#117·#119·#156·#158이고(`git log -- .github/workflows/`), 이 PR이 여덟째다. 일지 2026-09-29-03과 2026-09-30-02는
   그래서 코멘트를 손으로 봤다고 적었다. 첫 판은 오늘 둘만 세어 2회차로, 셀프 리뷰 뒤에는 행의 승인일부터 세어 7회차로
   적었다가 일지 2026-10-07-14의 기점을 따라 #43을 넣었다. 행은 PR #164가 닫았다.

일지에만 남기는 것: pytest를 `| tail -3`에 넘겼다가 `tools/hook_bash_gate_pipe.py`가 경고해, 그 실행을 멈추고 파일
리다이렉트로 다시 돌렸다. 훅이 설계대로 잡은 것이다. 일지 초안을 "다음"까지 한 번에 써서 retro가 셀프 리뷰와 PR보다
먼저 돌았다.

## 다음

- `.github/workflows/claude-code-review.yml`의 체크아웃은 작업 칩으로 띄운 세션이 PR #164로 고쳤고, 이 PR보다 먼저
  병합됐다. 겹침은 위 "PR #164와의 충돌"대로 이 브랜치가 풀었다.
