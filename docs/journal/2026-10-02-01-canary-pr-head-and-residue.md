# 2026-10-02 (01) 카나리아의 커넥터, PR head 확인 훅, 잔존을 세는 문서 — 대기열 85·86·87

하네스 chore 배치의 다음 묶음이다. 지시문은 일지 2026-10-01-08·09의 "다음"이 가리킨 next-session 지시문에서 왔다.
브랜치는 `chore/canary-pr-head-and-residue`다. 데스크톱 앱 세션이 주 체크아웃에서 시작했고, 주 체크아웃이 #118 병합
전(`43a6905`)에 머물러 있어 `git pull --ff-only`로 `f120f9a`까지 당긴 뒤 `EnterWorktree`로 만든 워크트리에서 일했다.
세션 제목은 UserPromptSubmit 훅의 지시대로 브랜치 이름으로 바꿨다.

> 사용자: ".scratch/retro-queue.md의 85·86·87(operations.md 묶음과 PR head 확인 훅)을 chore PR 하나로 반영한다"

앞 PR의 끝을 여기 남긴다(일지 08에는 3회차까지 있다). PR #118의 4회차(`4bebdda`)는 `ci`와 Claude Code Review가
초록이었고 claude-review는 지적이 없었다. 병합은 `f120f9a`다(`gh pr view 118`, `gh run list`로 봤다). CodeRabbit은 그
PR에서 2회차(`86b5a0c`까지)만 봤다.

이 세션은 당기기 전에 시작해 Stop 훅(대기열 83)이 실리지 않았다. 일지 08의 "다음"이 적은 첫 세션 확인은 다음 세션
몫이다. 이 세션이 띄운 `claude -p` 카나리아들은 당긴 뒤의 설정을 실었지만 답이 짧아 판정 하한 아래였다.

## 자리를 정한 것

- **85.** 먼저 쟀다(아래 잰 것 절). `--strict-mcp-config`를 더하자 claude.ai 커넥터가 빠졌으므로 조건은 그대로 두고
  `operations.md` 환경 규약 상세의 명령에 그 플래그를 넣었다. 첫 탐침에서 `--tools`와 `--mcp-config`가 가변 인자라
  뒤에 둔 질문을 삼켰다. 그래서 명령은 질문을 stdin으로 받는다고 적었다.
- **86.** 행은 "다르면 계기"였다. PreToolUse의 계기(`additionalContext`)는 명령을 그대로 돌리므로 claude-review는 옛
  head를 리뷰하고 CodeRabbit 요청은 버려진다. 구현 전에 물었다.

  > 사용자(질문에 답): "막기 (Recommended)"

  - `tools/hook_pr_head_sync.py`를 PreToolUse `Bash|PowerShell`에 등록했다. 잡는 명령은 명령 위치의 `gh pr ready`
    (`--undo` 제외)와, CodeRabbit을 부르는 `gh pr comment`다. 판정은 두 단계다. 선택자 없이 쳤으면 로컬 HEAD가
    upstream(`@{u}`)에 없을 때 gh를 부르기 전에 막는다. 그 밖에는 `gh pr view --json headRefOid,headRefName`으로 읽은
    PR head가 지금 브랜치의 것이고 로컬 HEAD에 못 미칠 때 막는다. PR 쪽이 앞섰거나, 다른 브랜치의 PR이거나, PR
    head가 로컬에 없으면 지나간다.
  - 로컬 단계를 둔 이유는 페이로드 표의 발동 사례를 네트워크 없이 돌리기 위해서다. 푸시하지 않은 커밋이 있으면 PR
    head는 기껏해야 upstream이라 로컬 HEAD와 같을 수 없으므로, 행의 조건 안에 드는 부분이다(명세 축도 같게 봤다).
    러너에 `${UNPUSHED_REPO}` 픽스처를 더했다.
  - 실제 입력을 트랜스크립트에서 뽑아 보니 `git push … && gh pr comment N --body "@coderabbitai review"`처럼 푸시와
    요청을 한 명령에 묶은 것이 많았다. 훅은 명령이 돌기 전에 판정하므로 이 모양도 막는다. 지연 사건과 같은 모양이라
    막는 것이 맞고, 거부 이유는 먼저 푸시하고 같아진 뒤 다시 치라고 안내한다.
  - `operations.md` 리뷰 파이프라인의 `gh pr checks` 지연 항목에 리뷰를 부르는 쪽의 지연과 이 훅을 더했다.
    `KICKOFF.md`의 훅 목록(열에서 열하나), 매처 수, `.claude/rules/tools.md`의 훅 비용 줄도 고쳤다.
- **87.** `operations.md` 문서 위치에 잔존 grep이 보는 살아 있는 문서와 기록을 가르는 문단을 두었다. code-review 주장
  검증 5가 그 절을 가리킨다. 행의 "어디로"에는 없지만 `CLAUDE.md` 작업 규약 4에도 포인터를 넣었다. claude-review
  봇은 `operations.md`가 아니라 `CLAUDE.md`를 읽기 때문이다(`.github/workflows/claude-code-review.yml` 2단계).
- 헌법은 3.0.6(patch, 운영의 문구 셋)이다. 처음에는 3.0.5로 올렸는데, 같은 날 3.0.5로 올린 PR #119(대기열 89)가 먼저
  병합되어 main을 합치며 3.0.6으로 다시 매겼다(아래 PR 리뷰 절).

## 잰 것

- **카나리아 세션의 init(프로브 `.scratch/harness/probes/canary_init/`, claude 2.1.286).** `--tools Skill`만 주면 도구
  77개(`Skill`과 커넥터 셋의 도구 76 — Atlassian 41, Docs 8, Slack 27)와 서버 셋이 실렸다. `--strict-mcp-config`를
  더하면 도구 `Skill` 하나에 서버 0이었고, 빈 `--mcp-config`를 더해도, `ENABLE_CLAUDEAI_MCP_SERVERS=false`만 줘도
  같았다. `--tools Read --disallowed-tools 'Read(./.claude/**)' --strict-mcp-config`는 `Read` 하나에 서버 0이었다.
  다섯 모두 스킬 36개에 `code-review`가 있었다. stdin 질문이 닿았는지는 B·E의 결과 이벤트를 손으로 봤다(답 `OK`).
  첫 판은 질문을 인자 끝에 두어 A·C·D가 `Input must be provided`나 질문을 설정 파일 경로로 읽은 오류로 끝났다.
- **바꾼 code-review 스킬을 새 세션에서 불렀다(손으로 봤다).** 고친 명령 그대로(`--strict-mcp-config`, stdin 질문,
  `--tools Skill`, sonnet) 5번 항목이 가리키는 경로를 물었다. 워크트리에서 띄운 세 번이 모두 Skill을 부르고
  `docs/constitution/operations.md`를 옮겼고, 주 체크아웃(바꾸기 전 사본)의 대조군은 "없음"이었다. 세 번 다 init의
  `tools`가 `["Skill"]`, `mcp_servers`가 `[]`였다.
- **훅 시간(프로브 `pr_head_sync/time_hook.sh`).** 리뷰를 부르지 않는 명령 226~231ms, 로컬 판정 310~337ms(deny),
  gh 길 941~998ms(PR #118은 브랜치가 달라 silent). 첫 판은 Git Bash의 `pwd`가 내는 `/c/...` 경로를 페이로드 `cwd`로
  넘겨, 훅의 git이 OSError로 지나가 로컬 판정이 silent였다. 탐침이 막는 사례를 보지 못한 채 초록처럼 보였던 것이다.
  `pwd -W`로 고쳤다.
- **gh 길을 이 PR로 돌렸다(손으로 봤다, 스크래치패드의 폴링 스크립트).** PR #120을 draft로 연 뒤 커밋 하나를 더하고
  푸시하기 전에 훅에 실제 페이로드를 넣었다. `gh pr ready 120`은 gh 길로 막혔고(0.9초, "PR head 가 아직 `fbdb755` 이고
  로컬 HEAD 는 `7a73cb0` 다"), 선택자 없는 `gh pr comment --body "@coderabbitai review"`는 로컬 판정으로 막혔다(0.2초).
  그 뒤 훅을 1초 간격으로 돌리며 푸시했다. 3.0초에는 upstream이 이미 `7a73cb0`인데 PR head는 `fbdb755`라 막았고, 5.4초에
  PR head가 따라와 지나갔다. 대기열 86의 사건(푸시 직후의 지연)을 훅이 실제로 막는 것을 본 표본 하나다.
- **변이(`.scratch/harness/probes/pr_head_sync_mutations.toml`).** 첫 판의 열아홉은 모두 기대대로 빨강이었다. 셀프
  리뷰를 반영한 뒤 둘(로컬에 없는 PR head, 대소문자 다른 언급)을 더한 스물하나도, PR 리뷰 1회차 반영으로 하나(다른
  이름의 브랜치를 추적하는 upstream)를, 2회차 반영으로 하나(HEAD와 같은 upstream)를 더한 스물셋도 모두 기대대로 빨강이다. pytest 변이는
  앞선 PR head(테스트 둘)를 빼고 저마다 테스트 하나만 빨갰고, main의 로컬 판정 변이는 러너의 어긋남 2건(발동 사례
  둘)이었다. 첫 판의 열아홉이 모두 빨강이었어도, 그중 "모르는 커밋을 조상으로 본다"는 틀린 동작을 고정하고 있었다.
  변이는 테스트가 무엇을 재는지 보여 줄 뿐, 잰 것이 맞는지는 보여 주지 않는다.

## 셀프 리뷰

`/code-review`, base `f120f9a`, 수정 파일 12, 미추적 6(새 파일), 커밋 0. `tools/`와 `tests/`의 파이썬이 바뀌어 두 축
모두 기본 모델이다. 명세는 대기열 85·86·87 행, 지시문, 위 사용자 결정이다(요구와 리뷰어 참고를 가른 파일을 넘겼다).
이 세션에 실린 code-review 사본은 주 체크아웃의 것이라 주장 검증 5는 바꾼 문장을 브리프에 손으로 넣었다.

- **두 축이 같은 Major를 따로 냈다.** PR head가 로컬에 없는 커밋이면 `is_ancestor`가 False를 내서 막았다. 다른
  곳(GitHub 화면의 제안 커밋, 다른 세션)이 푸시한 앞선 head를 아직 가져오지 않은 경우다. 기다려도 같아지지 않고
  푸시는 non-ff로 거부되어, 거부 이유가 안내한 길로는 풀리지 않는다. 표준 축은 bare 저장소와 클론 둘로, 명세 축은
  PR #119의 head를 갖지 않은 클론에서 `gh pr ready 119`로 재현했다. 첫 판의 테스트와 변이가 오히려 그 동작을 고정했다.
- **표준 축의 그 밖.** Minor: 러너 독스트링의 "자리표시자 열"(이제 열하나), "`--strict-mcp-config`가 없으면 커넥터가
  실린다"의 반례(같은 프로브의 환경 변수 변형), 못 보는 것의 빈자리(`cd <다른 저장소> &&`, 대소문자 다른 언급,
  detached HEAD), 문서 위치의 "그 밖의 전부다"의 반례(헌법 README의 버전 이력), 프로브 README의 손으로 본 값과
  `run.sh` 머리 주석. Nit: 타임아웃 주석의 합, 비용 줄의 빠진 PostToolUse 훅, "다르면 막는다"의 단순화. 판단 사항:
  Shotgun Surgery(훅 개수가 산문 여러 곳에), 위치 불리언 인자, 픽스처 세 벌.
- **명세 축의 그 밖.** Minor: 침묵 사례가 지은 입력이다, 페이로드 표 머리의 자리표시자 목록, 87이 행("ADR의 옛 이력")보다
  넓혀 ADR 본문까지 기록으로 쳐서 열린 행 88의 전제와 어긋난다, 닫은 대기열 행에서 승인 문구를 지웠다, "다르면 막는다".
  범위: `CLAUDE.md` 포인터와 stdin 질문은 행 밖이지만 이유가 있다고 했다.
- **고친 것.** 로컬에 없는 PR head는 지나가게 했다(`has_commit`, `judge_pr`, 테스트 둘, 변이 하나). 언급을 대소문자
  없이 찾는다(테스트·변이 하나). `stale_reason`의 `pr_ahead`를 키워드 전용으로. 못 보는 것과 fail-open 열거, 타임아웃
  주석, 러너 독스트링의 수, 표 머리의 자리표시자, 침묵 사례를 실제로 친 명령 둘로(PR #78 세션의 `gh pr ready 78 --undo
  …`, PR #94 세션의 언급 없는 코멘트), `operations.md`·`KICKOFF.md`의 "못 미치면"과 지나가는 조건, 커넥터 문장,
  문서 위치 문단(ADR은 지난 이력 항목만 기록, 살아 있는 문서 안의 이력을 기록에 넣음, 닫힌 열거를 풀었다), 비용 줄,
  프로브 README와 `run.sh` 주석, 대기열 행에 승인 문구와 일지를 되살렸다.
- **남긴 것.** Shotgun Surgery는 두었다. 훅 개수를 산문에 적어 온 관행이고, 이번에 놓친 하나(러너 독스트링)는
  고쳤다. 픽스처 세 벌(러너, 테스트, 셸 탐침)은 실행 자리가 달라 두었다. 명세 축이 실제 침묵 입력으로 든 PR #100의
  코멘트는 뒤에 `&& gh pr comment 100 --body "@coderabbitai review"`가 이어져 발동 사례라 쓰지 않았다.

## 검사

- 리뷰 반영 뒤: `uv run pytest -q` 1206 passed(경고 3은 기존 pytest-asyncio 설정 경고), `uv run ruff check .`·`uv run
  ruff format --check .` 통과, `uv run pyright` 0 errors, `uv run lint-imports` 5 kept, `pnpm -C web verify` 통과(Vitest
  263 passed), `tools/check_instructions.py`·`tools/check_type_escapes.py` 통과, `tools/run_hooks.py` 52건 어긋남 0.
  `src/`를 바꾸지 않아 `-m llm`은 돌리지 않았다. 워크트리에 web 의존성이 없어 `pnpm -C web install --frozen-lockfile`을
  한 번 했다.

## PR 리뷰

PR #120. draft로 열고 위 gh 길을 잰 뒤 ready로 바꿨다. 바꾸기 전에 `gh pr view --json headRefOid`와 `git rev-parse HEAD`가
같은 것을 봤다. PR 직전 CLI는 `coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 돌리지 않았으므로 이 PR의
보안·버그 축은 PR 봇 하나다.

1회차(`15b63a8`). CI 다섯(`python`, `web`, `e2e`, `verify`, `claude-review`)이 초록이었다. CodeRabbit은 00:06 UTC에
"Review rate limited"였고 안내는 "2분 뒤"였다. claude-review는 Minor 둘과 Nit 하나를 냈다.

- 고친 것: 선택자 없는 로컬 판정이 upstream이 PR의 브랜치라고 가정했다(claude, Minor). `git checkout -b x origin/main`
  처럼 base를 추적하는 작업 브랜치는 푸시한 뒤에도 로컬 HEAD가 upstream보다 앞서 영원히 막힌다. "못 보는 것"에 적어
  두었지만 거부 이유의 길로 풀리지 않는 막다른 길이다. 셀프 리뷰의 Major와 같은 모양이다. upstream은 같은 이름의 원격
  브랜치를 추적할 때만 읽게 했다(테스트·변이 하나).
- 고친 것: `reason_for`의 바깥 조건과 `unpushed_reason`의 조건이 겹친다(claude, Minor). 바깥 조건은 git 호출을 아끼는
  것이라 두고, 판정은 안쪽이 한다는 주석을 달았다.
- 둔 것: 헌법 README의 버전 줄이 너무 길다(claude, Nit). 줄을 나누면 같은 줄을 고치는 PR #119와 더 크게 충돌한다.

2회차(`e81f038`). CI 다섯이 초록이었다. head가 같은 것을 본 뒤 남긴 CodeRabbit 요청은 한도가 풀려 돌았고, `e81f038`까지 보고
병합 위험을 Low로 냈다. 지적은 셋이었다.

- 고친 것: `canary_init/summarize.py`가 잘린 JSONL 줄 하나에서 예외로 멈춘다(CodeRabbit, Minor). 그 줄은 건너뛴다.
- 고친 것: 1회차의 주석으로는 겹친 조건이 그대로다(claude, Minor). upstream이 있고 HEAD와 다르다는 조건을 `LocalState`의
  질의 `upstream_if_different` 하나로 빼서 `reason_for`와 `unpushed_reason`이 같은 것을 부르게 했다(변이 하나).
- 고친 것: 독스트링의 "못 보는 것"이 한 문단에 열 개 넘게 이어져 항목마다 대조하기 어렵다(claude, Nit). 불릿으로 나눴다.

2회차를 받는 동안 세션이 다시 시작되었다. 그러자 모든 Bash·PowerShell 호출이 이 훅의 등록에서 막혔다. 다시 시작한
세션은 워크트리의 `.claude/settings.json`(이 훅의 등록)을 실었지만 훅 명령의 `${CLAUDE_PROJECT_DIR}`은 주 체크아웃을
가리켰고, 주 체크아웃에는 아직 이 파일이 없어 파이썬이 2로 끝났다(`.claude/rules/tools.md`가 2026-09-29에 적은 "경로
오류 하나가 모든 Bash를 막는다"가 실제로 났다). 셸 없이 GitHub 도구로 2회차를 읽었다.

> 사용자(질문에 답): "임시 사본 (Recommended)"

워크트리 격리가 주 체크아웃에 쓰는 것을 거부했다.

> 사용자(질문에 답): "지금 병합"

GitHub 도구의 squash 병합(`expectedHeadSha`로 head를 고정)은 충돌로 거부되었다. 그사이 PR #119가 `387b252`로 병합되어
헌법 README의 버전 줄이 둘 다 3.0.5였다.

> 사용자(질문에 답): "워크트리에서 나가기 (Recommended)"

`ExitWorktree`(keep)로 세션을 주 체크아웃에 돌리고, 주 체크아웃의 `tools/hook_pr_head_sync.py`에 워크트리의 훅을
`runpy`로 그대로 도는 임시 위임 파일(커밋하지 않는다)을 두어 셸을 되살렸다. 그 뒤 워크트리 브랜치에서 `origin/main`을
합쳤다. 충돌은 헌법 README 하나였고, main 쪽 줄을 그대로 두고 이 PR의 문장을 3.0.6으로 그 앞에 얹었다. 대기열 표는
85~87(이 PR)과 89·90(PR #119)이 따로 합쳐졌다. 위 지적 셋은 셸이 돌아온 뒤 고쳤다.

## 보고 언어

도구 호출 사이의 중간 문장 몇을 영어로 썼다("Now update the runner docstrings …" 같은 것). 사용자가 고치지는 않았다.
이 세션에는 Stop 훅이 실리지 않았고, 실렸더라도 그 훅은 턴 끝 답만 본다(일지 08의 보고 언어 절과 같다).

## 회고

후보 셋을 냈다. 앞의 둘은 PR을 열기 전에 기록만으로 정해졌고, 셋째는 PR 리뷰 중에 겪어 새 항목으로 승인됐다.

> 사용자(질문에 답): "기록만 (Recommended)", "기록만 (Recommended)"

> 사용자(질문에 답): "새 항목 (Recommended)"

- **91(새로): 훅 등록 명령이 스크립트가 없을 때 막지 않고 지나간다.** 위 PR 리뷰 절의 Bash 전체 차단이다. 등록이
  `python <경로>` 꼴이라 파일이 없으면 2(막기)가 된다. 새 훅을 더한 워크트리 세션이 다시 시작되거나, 새 훅을 병합한 뒤
  주 체크아웃을 당기지 않은 채 워크트리에서 다시 시작한 세션이면 같은 일이 난다. 세션 하나를 통째로 멈추고 모양이
  고정되어 있어 검사 쪽으로 간다.

- **기록만: 막는 훅에서 모름을 False로 접었다.** `is_ancestor`가 로컬에 없는 커밋에 False를 내고, 그 False가 막는 쪽으로
  흘렀다. 첫 판의 테스트와 변이가 그 동작을 고정해 변이 열아홉이 모두 빨강이어도 잡지 못했고, 셀프 리뷰 두 축이 잡았다.
  `.claude/rules/tools.md`에 한 줄을 두는 안은 1회차라 두지 않았다(`CLAUDE.md` 교정 루프). 되풀이되면 규칙 후보다.
  한 줄 후보: "막는 훅에서 모름은 지나가는 쪽으로 접는다".
- **기록만: 대기열 행이 고른 기전이 행의 목적을 막지 못했다.** 86 행은 PreToolUse 훅을 "계기"로 적었는데, 계기는
  명령을 그대로 돌려 옛 head 리뷰를 막지 못한다. 구현 전에 물어 막기로 바꿨다. 1회차라 retro 스킬의 행 형식은 그대로다.
- 일지에만: 탐침이 자기가 재려는 것을 보지 못한 일이 둘이다. `--tools`가 질문을 삼켰고, Git Bash의 `/c/...` 경로가
  훅의 git을 조용히 지나가게 했다. 둘 다 결과 칸(오류 줄, deny·silent 판정)을 찍어 둔 덕에 바로 보였다. `CLAUDE.md`
  환경 함정의 "검사 도구가 내가 생각하는 것을 실제로 봤는지 먼저 확인한다"와 같은 줄기다. 워크트리 가드가 변수·heredoc이
  든 명령을 네 번 거부했다(기억과 `CLAUDE.md`에 이미 있다). 이 세션에 실린 code-review 사본이 주 체크아웃의 것이라
  브리프에 바꾼 문장을 손으로 넣었다(`operations.md` 환경 규약 상세에 이미 있다). 명세 축이 실제 입력의 앞부분만 읽고
  발동 사례를 침묵 사례로 들었다.

## 다음

- 이 PR의 마지막 CI와 병합은 다음 일지에 한 줄 남긴다.
- 주 체크아웃의 `tools/hook_pr_head_sync.py`는 이 세션이 둔 임시 위임 파일이다(미추적). 병합 뒤 그것을 지우고 당긴다.
  미추적 파일이 남아 있으면 당기기가 그 경로에서 멈춘다.
- 일지 08의 "다음"이 적은 Stop 훅의 첫 세션 확인은 아직이다. 당긴 주 체크아웃에서 시작한 세션이 한다.
- 다음 chore 후보는 91(이번에 세션을 멈춘 등록 모양, 하네스 전체에 걸린다), 84(워크플로 파일이라 별도 PR), 88·49(ADR
  본문과 이력의 표시 규약, 같은 대상)다. 87이 ADR 본문을 살아 있는 문서로 정했으므로, 88의 포인터는 잔존 grep이 뒤집힌
  본문 줄을 짚을 때의 답이 된다.
