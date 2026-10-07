# 2026-10-07 (14) claude-review의 체크아웃이 토큰을 남기지 않고, 코멘트 0개 가드는 자기 파일에서만 꺼진다

PR #162(`ci.yml`의 `persist-credentials: false`)가 띄운 작업 칩의 일이다. 워크트리 `confident-wright-2d3ebf`에서
`origin/main`(`49d9630`)으로 `chore/review-checkout-credentials`를 땄다. 시작했을 때 PR #162는 열려 있었다. 이 일이
배경으로 드는 `ci.yml` 머리 주석과 대기열 142는 그 PR에 있고 main에는 아직 없다.
순번은 14다. 10은 병합된 PR #161(`10-sibling-overlap`)과 열린 PR #163(`10-tidy-checkouts-tool`)이 함께 쓰고, 11은
PR #162, 12·13은 형제 워크트리 `03-status-badge-progress-card`·`04-text-field-switch-alert`의 미커밋 일지가 쓴다. 세션
중에 PR #161이 병합되어 이 브랜치에 main을 병합했다.

## 계기

> 사용자: "저장소 C:\project\agent 의 `.github/workflows/claude-code-review.yml` 에서 `actions/checkout@v7` 단계(`Checkout repository`)에 `persist-credentials: false` 를 더할지 확인하고, 맞으면 더하는 chore 다.
>
> 배경: `ci.yml` 은 체크아웃하는 잡(python, web, e2e, visual)이 모두 `persist-credentials: false` 이고, 그 근거는 `ci.yml` 머리 주석에 있다(PR #158 의 CodeRabbit 지적 CWE-522, 일지 `docs/journal/2026-10-07-11-checkout-persist-credentials.md`). `claude-code-review.yml` 의 체크아웃만 아직 기본값(true)이라 GITHUB_TOKEN(`pull-requests: write`, `issues: write`, `id-token: write`)이 체크아웃 안에 남는다. 그 잡은 PR 코드를 실행하지는 않지만, PR 의 글을 읽는 모델이 `Read` 로 파일을 읽고 `gh pr comment` 로 게시할 수 있다.
>
> 확인할 것:
> 1. `anthropics/claude-code-action@v1` 이 체크아웃이 남긴 git 자격 증명에 기대는지 본다. 액션의 문서와 소스(action.yml, git 인증 설정 부분)를 읽고, 리뷰 전용 흐름(`prompt` 입력, 허용 도구는 `gh pr view|diff|comment`, `git diff|log|show`, 인라인 코멘트 MCP)에서 push 나 인증된 fetch 가 필요한지 판정한다. `gh` 는 `.git/config` 가 아니라 자기 토큰으로 인증한다.
> 2. 필요 없으면 `with:` 에 `persist-credentials: false` 를 더하고, 파일 머리 주석에 근거를 한 줄 둔다. 필요하면 바꾸지 말고 그 근거를 일지에 남긴다.
>
> 주의: 이 파일을 바꾼 PR 에서는 액션이 리뷰를 건너뛰고 초록이 되며, 코멘트 0개 가드도 꺼진다(`docs/constitution/operations.md` 리뷰 파이프라인, 대기열 50). 그래서 이 파일만 바꾸는 별도 PR 로 하고, 리뷰는 CodeRabbit 코멘트와 셀프 리뷰로 손으로 본다. 대기열 142(zizmor 도입)가 먼저 반영되면 zizmor 의 `artipacked` 감사가 이 단계를 가리킬 것이므로 그 결과와 맞춰 본다. 대기열 50(가드를 자기 워크플로 파일로 좁히기)도 같은 파일의 가드 스텝이 대상이라, 함께 하면 PR 하나로 끝난다. CLAUDE.md 의 작업 규약(브랜치 `chore/<slug>`, 검증 명령, `/code-review`, 일지)을 따른다."

## 확인한 것

판정은 "필요 없다"이고, 넣어야 할 까닭이 하나 더 나왔다. 액션은 체크아웃 토큰에 기대지 않을 뿐 아니라, 그 토큰을
지우는 코드가 checkout v7에서 헛돌아 Claude가 도는 동안 토큰이 git 설정에 남아 있었다.

**코드를 읽었다.** `anthropics/claude-code-action@v1`은 2026-10-06에 v1.0.244(커밋 `5898584`)로 옮겨졌고, 그 커밋의
`action.yml`, `src/entrypoints/run.ts`, `src/modes/detector.ts`, `src/modes/agent/index.ts`,
`src/github/operations/git-config.ts`, `src/github/operations/restore-config.ts`, `src/github/token.ts`를 읽었다.

- `pull_request` 이벤트에 `prompt`가 있으면 agent 모드다(`detector.ts`).
- 액션은 먼저 OIDC 토큰을 Claude 앱 토큰으로 바꾼다(`token.ts`. `id-token: write`는 여기 쓰인다). 그 토큰을
  `GH_TOKEN`·`GITHUB_TOKEN` 환경 변수에 넣는다(`run.ts`). 모델의 `gh pr view|diff|comment`와 인라인 코멘트 MCP는 이
  토큰으로 인증한다.
- agent 모드의 준비 단계는 `configureGitAuth`를 부르고, 그 안의 `replaceCheckoutCredentials`가 체크아웃이 남긴
  `http.https://github.com/.extraheader`를 지운 뒤 `origin`의 URL에 앱 토큰을 넣는다(`git remote set-url origin
  https://x-access-token:<앱 토큰>@github.com/...`). 지우는 쪽은 로컬 설정과 `include.path`가 가리키는 파일만 본다.
- 이 흐름에서 네트워크에 닿는 git 명령은 `restoreConfigFromBase`의 `git fetch origin <base> --depth=1` 하나다. PR 헤드의
  `.claude/`·`CLAUDE.md` 등을 base 의 것으로 되돌리는 단계이고 위의 `set-url` 뒤에 돈다. 저장소가 공개라 인증 없이
  통하고, 401을 받는 저장소라면 git이 URL의 앱 토큰을 보낸다. 다만 체크아웃 헤더가 남아 있으면 git은 그 헤더를 모든
  요청에 싣기 때문에, 옛 실행의 이 fetch는 체크아웃 토큰을 실었을 것이다. git의 동작에서 끌어낸 어림이고 재지 않았다.
  실었어도 기대지는 않는다. 처음에는 "앱 토큰으로 인증한다"고 적었는데 명세 축이 이 차이를 짚었다.
- 모델이 쓸 수 있는 git은 `git diff|log|show`이고 모두 로컬이다. push는 없다.
- 그래서 체크아웃 토큰이 없어도 잃는 것이 없다. `persist-credentials: false`이면 지우기는 지울 것이 없어 넘어가고
  (예외를 잡는다), `set-url`은 체크아웃이 `origin`을 여전히 만들어 두므로 그대로 돈다.

**로그를 손으로 봤다.** PR #161의 claude-review 실행(`37576069526`, 2026-10-07)은 같은 액션 커밋 `5898584`와
`actions/checkout@v7`(`3d3c42e`)을 내려받았다. `gh run view 37576069526 --log`에서 본 것:

- 체크아웃은 헤더를 `.git/config`가 아니라 `/home/runner/work/_temp/git-credentials-<uuid>.config`에 쓰고, 로컬 설정에는
  `includeIf.gitdir:<경로>.path` 넷으로 그 파일을 가리켰다. `include.path`가 아니다.
- 액션은 `No existing authentication headers to remove`를 찍고 이어 `Updated remote URL with authentication token`을
  찍었다. 지우는 코드가 `includeIf`를 보지 않아 헤더를 찾지 못한 것이다.
- 그 헤더 파일은 액션이 끝난 뒤 `Post Checkout repository`가 지웠다.

그러니 그 실행에서 Claude가 도는 동안 git 설정에는 체크아웃의 GITHUB_TOKEN(`pull-requests: write`, `issues: write`)이
살아 있었다. 액션의 주석은 checkout v6이 헤더를 `include.path`의 파일로 옮겨 지우기가 헛돈 일을 고친 것이라고 적는데,
v7의 `includeIf` 배치에서 같은 일이 다시 났다. `persist-credentials: false`는 `ci.yml`과 모양을 맞추는 것만이 아니라
이 노출을 닫는다.

**zizmor는 돌리지 않았다.** 대기열 142는 PR #162에 있고 아직 반영되지 않았다. 새 도구라 ADR이 먼저다. `artipacked`가
체크아웃에 `persist-credentials: false`를 요구한다는 것은 zizmor 문서로 아는 것이고, 이 단계가 그 감사를 지나는지는
142를 반영하는 브랜치가 본다.

## 바꾼 것

- `.github/workflows/claude-code-review.yml`
  - 체크아웃의 `with:`에 `persist-credentials: false`를 더했다. 머리 주석에 근거를 한 줄로 두었다.
  - 코멘트 0개 가드(대기열 50): 바뀐 파일 목록에서 `.github/workflows/`로 시작하는 줄을 찾던 것을, 그 파일 이름을 글자
    그대로 한 줄 전체로 찾게 했다(`grep -qxF`). 가드 주석과 건너뛸 때의 메시지도 그 범위로 고쳤다. 액션이 건너뛰는 것은
    자기 파일을 바꾼 PR뿐이라(`operations.md` 리뷰 파이프라인), `ci.yml`만 바꾼 PR에서는 이제 가드가 코멘트를 센다.
- `.github/PULL_REQUEST_TEMPLATE.md`의 `.github/` 줄: "워크플로 파일이 바뀐 PR은 가드가 꺼진다"를 그 파일을 바꾼 PR로
  좁혔다.
- 잔존을 grep했다(`가드가 꺼`, `0개 가드`, `워크플로 파일이 바뀐`, `워크플로 파일을 바꾼`). 열린 대기열 31행의 2026-09-28
  정정이 "코멘트 0개 가드는 `.github/workflows/` 아래 어느 파일이 바뀌어도 건너뛴다"를 들고 있어 지금의 사실로 고쳤다.
  처음에는 이 행을 놓쳤다. grep 출력에서 긴 줄이 생략되어 보이지 않았고, 셀프 리뷰 두 축이 찾았다. 나머지는 일지,
  done인 web-admin의 명세·티켓, 대기열의 닫힌 행 50과 열린 행 84다. 84는 `claude-code-review.yml`의 프롬프트를 바꾸는
  일이라 그 PR은 여전히 가드가 꺼지고, 문장이 참이다. ADR 0006 22행은 액션이 건너뛰는 조건을 말하고 이미 ADR 0021 이력
  포인터가 붙어 있다.
- `.scratch/harness/probes/review_workflow.py`와 README 행: 체크아웃 설정을 판정하고 가드 스텝을 가짜 `gh`로 돌리는
  탐침.
- `.scratch/retro-queue.md` 50행을 닫고 31행의 정정을 고쳤다.

`operations.md`는 고치지 않았다. 리뷰 파이프라인 절은 이미 액션이 자기 파일에서만 건너뛴다고 적고, 가드가 건너뛰는
조건은 적지 않는다. 헌법은 그대로라 버전도 그대로다.

## 검사

- 탐침 `review_workflow.py`: 체크아웃 판정 하나와 가드 사례 일곱(이 워크플로를 바꿈, `ci.yml`만 코멘트 없음·있음, 코드만
  셋, 같은 이름의 다른 경로). 작업 트리는 어긋남 0/8, `origin/main`은 4/8이었다. 반영 전의 판은 체크아웃이 기본값이고,
  가드가 `ci.yml`만 바꾼 두 사례와 `.github/workflows/claude-code-review.yml.orig`가 든 사례에서 건너뛰었다. 첫 판은
  종료 코드만 봐서, bash가 스크립트를 찾지 못한 실행(Windows의 역슬래시 경로, 그다음은 System32의 WSL bash)이 "실패"
  기대와 맞아 버렸다. 그래서 가드의 집계 줄까지 보게 고쳤다. 체크아웃 값은 처음에 찍기만 했는데, 표준 축이 판정하지
  않는다고 짚어 판정에 넣고 이름을 `review_guard.py`에서 바꿨다.
- 손으로 본 것: 가드가 생긴 PR #10(`1635f0b`) 뒤에 워크플로 중 `ci.yml`만 바꾼 PR은 main에 일곱(#43·#99·#103·#117·#119·
  #156·#158, `git log origin/main -- .github/workflows/`)이고 열린 #162까지 여덟이다. `claude[bot]` 코멘트가 차례로
  6·2·3·3·3·2·5·2개 있다(`gh api repos/njh6803/agent-os/issues/<n>/comments`). 새 가드였어도 모두 초록이었다. 처음에는
  #162의 일지가 센 목록(대기열 50 승인 뒤)을 옮겨 #43을 빠뜨렸고, 명세 축이 짚었다.
- 이 PR의 CI에서 액션과 가드는 둘 다 건너뛴다(자기 파일을 바꿨다). 체크아웃 단계의 로그만 바뀐 모양을 보인다. 체크아웃
  토큰 없이 액션이 도는지는 병합 뒤 첫 PR의 claude-review 실행이 처음 보인다.

## 남은 위험

- 액션은 Claude가 도는 동안 앱 토큰을 `.git/config`의 `origin` URL에 둔다(`allowed_non_write_users`가 없을 때의
  `configureGitAuth`). 이것은 `persist-credentials`가 닿지 않는 액션 자신의 설계다. 모델의 `Read`는 그 파일을 읽을 수
  있다. 그 토큰은 액션의 마지막 단계(`Revoke app token`)가 폐기하고, 액션은 이벤트를 일으킨 actor에게 쓰기 권한이 있을
  때만 돈다(`checkWritePermissions`).
- 액션의 지우기가 `includeIf`를 보지 못하는 것은 상류의 결함이다. 이 저장소는 체크아웃이 토큰을 남기지 않으므로 더는
  닿지 않는다. 상류에 알리는 것은 사용자가 정한다.

## 셀프 리뷰

`/code-review`, base `49d9630`, 수정 4, 미추적 2, 커밋 0. `src/`·`tests/`·`tools/`의 소스가 없어 표준 축은 sonnet이다.
명세는 사용자 지시문(위 계기)과 대기열 50행이고, 요구와 리뷰어 참고를 갈라 넘겼다. 표준 축은 Minor 셋·Nit 둘과 판단
항목, 명세 축은 Major 하나·Minor 셋·Nit 넷이었다. 겹친 것은 둘이다(대기열 31행, PR #162와의 겹침).

- **고쳤다, 명세 Major·표준 Minor(열린 대기열 31행의 잔존).** 위 "바꾼 것"의 잔존 grep 항목.
- **고쳤다, 명세 Minor("이 토큰을 쓰지 않고").** git이 남은 헤더를 모든 요청에 실으므로 옛 실행의 base fetch는 체크아웃
  토큰을 실었을 수 있다. 머리 주석과 일지를 "기대지 않는다"로 고쳤다.
- **고쳤다, 명세 Minor(지난 PR 일곱의 반례 #43).** 기점을 가드가 생긴 커밋으로 잡아 여덟으로 다시 셌다.
- **고쳤다, 표준 Minor(탐침이 PowerShell에서 WSL bash를 잡는다).** 독스트링과 README에 Git Bash에서 돈다고 적었다.
  PowerShell에서 돌리면 모든 사례가 이상으로 나와 초록 착시는 없다.
- **고쳤다, Nit 다섯.** 머리 주석을 한 줄로(요구 2), 탐침이 체크아웃 값을 판정하고 이름을 `review_workflow.py`로,
  README에 PyYAML, 독스트링이 반영 전 판에서 어긋나는 가드 사례 셋을 모두 든다, 일지 "남은 위험"의 actor, 순번 문단의
  PR #163.
- **남겼다, 표준 판단 항목(탐침의 smell 넷: `CASES`의 4-튜플, 되풀이되는 `assert isinstance`, 문자열 결과값, `_run`의
  두 일).** 커밋하는 탐침이지만 제품 코드가 아니고 한 번 다시 도는 스크립트다. 이웃 탐침(`coderabbit_schema.py`)과 같은
  모양이다.
- **남겼다, 명세 Nit(탐침은 요청 범위 밖).** 가드를 바꾼 하네스의 확인은 실제 실행이어야 하고(`CLAUDE.md` 작업 규약 3),
  이 PR은 claude-review가 건너뛰어 가드가 실제로 돌 일이 없다. PR 본문에 밝힌다.
- **남겼다, 명세·표준 Minor(PR #162와 겹침).** 두 PR이 대기열 50행을 함께 고친다(#162는 회차와 일지 이름, 이 PR은 닫힘).
  #162가 더하는 142행의 "`claude-code-review.yml`에는 지금도 빠져 있다"는 두 PR이 다 병합되면 거짓이 된다. 나중에
  병합되는 쪽이 50행의 충돌을 풀고(회차와 닫힘을 함께 둔다) 142행의 그 구절을 고친다. #162가 먼저 병합되면 이 브랜치가
  main을 병합하며 한다.
