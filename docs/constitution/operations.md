# Agent OS 헌법 · 검증과 운영

커밋, 병합, 트래커, LLM 테스트, 가드레일을 만질 때 읽는다. 검증 명령 넷은 `CLAUDE.md`에 있고 실제로 돌려 통과한 명령만 적는다.

## LLM 테스트
LLM을 실제로 호출하는 테스트는 `llm` 마커를 붙인다. 기본 `pytest -q`는 이 마커를 제외한다. `uv run --env-file .env pytest -m llm`이 돌리며, `.env`의 `ANTHROPIC_API_KEY`가 없으면 skip이 아니라 실패한다. `.env`는 커밋하지 않는다. 원칙 I의 판정은 이 명령이다. CI가 생겨도 매 푸시에서는 돌리지 않는다. 손으로 돌리는 계기는 LLM 테스트 파일을 건드렸을 때가 아니라 그 테스트가 지나는 코드(`core/run.py`·`core/loop.py`, 어댑터, `channel/`, `main.py`)를 건드렸을 때다 — PR #46이 테스트를 한 줄도 안 고치고 그 아래 배관을 전부 바꿨다(대기열 1). 돌렸으면 일지 검사 절에 통과 수와 트레이스의 토큰 합계를 적는다.

## 가드레일
자동 검사는 둘이고 내용은 같다 — 훅 러너만 pre-commit에 먼저 들어가 CI가 뒤따르고, 인용 대조는 경고만이라 pre-commit에만 있다. 로컬 pre-commit 훅이 커밋마다, GitHub Actions CI(`.github/workflows/ci.yml`)가 푸시와 PR마다 ruff, ruff-format, pyright, import-linter, pytest(기본 마커), 지침 검사, 타입 우회 검사를 돈다. 마크다운 표 검사(`tools/check_md_tables.py`, 대기열 44)와 줄 구분 문자 검사(`tools/check_line_separators.py`, 대기열 22)는 pre-commit이 스테이지된 파일에 돌리고, CI에서는 pytest의 저장소 상태 테스트(`test_이_저장소의_…`)가 저장소 전체에 돌린다. 훅 페이로드 실행(`tools/run_hooks.py`, 대기열 24)은 pre-commit에만 있고 CI에는 다음 워크플로 PR에서 더한다. 타입 우회 검사가 원칙 III의 판정자다 — pyright strict가 `Any`·`cast`·억제 주석을 하나도 잡지 않아서 `tools/check_type_escapes.py`가 대신 판정한다. 훅은 각자 설치해야 하므로 CI가 최종 판정이다. main은 보호 브랜치다. 필수 검사 `verify`, 최신 main 기준(strict), 선형 이력, 강제 푸시와 삭제 금지, 관리자 우회 허용(혼자일 때). 경위는 ADR 0005. 병합은 여전히 `/git-pr-merge`로 한다. 스킬이 체크를 먼저 보기 때문이다. 클론 뒤 `uv run pre-commit install`을 한 번 하면 pre-commit과 commit-msg 두 훅이 깔린다. 훅이 안 걸린 저장소는 그 자체가 결함이다. 훅 시스템은 pre-commit 하나만 둔다. 둘이면 `.git/hooks/pre-commit` 한 자리를 다퉈 한쪽이 조용히 안 걸린다. 파이썬 파일이 안 바뀐 커밋에서도 pyright·import-linter·pytest는 돈다(`always_run`). CI에 경로 필터를 걸게 되면 미매칭은 skip이 아니라 실패로 만든다. 원칙 IV 중 "플러그인은 sdk만 import한다"는 import-linter가 아니라 `tests/test_plugins_boundary.py`가 판정한다 — 플러그인은 `root_packages` 밖이다(ADR 0018). 원칙 II의 "skip된 테스트는 초록이 아니다"는 `tests/conftest.py`가 판정한다. 바뀐 마크다운의 20자 이상 따옴표 인용을 저장소와 대조하는 `tools/check_quotes.py`(대기열 42)는 경고만 내므로 pre-commit에만 있고 CI에는 없다.

에이전트 자신의 도구 출력에 비밀이 실리는 것은 게이트가 보지 않는다. `.claude/settings.json`의 `permissions.deny`가 `.env`의 Read·Edit를 막고, `tools/hook_env_read.py`가 Bash로 읽는 길(`cat .env`, `< .env`, `.env`를 빼지 않은 저장소 전체 grep)과 `.env`를 경로로 준 Grep을 막는다(대기열 43 — 2026-09-28 감사에서 서브에이전트의 grep 한 번에 키 값이 도구 출력에 실렸다). 못 보는 것은 그 훅의 독스트링. Claude Code 훅의 원천은 그 설정 파일이고 훅마다 이유는 `tools/hook_*.py` 독스트링에 있다.

## 브랜치와 병합
- 원격은 GitHub(`njh6803/agent-os`, 공개). main은 보호 브랜치다(가드레일 절). 티켓마다 `feature/<NN>-<slug>` 브랜치를 따고 혼자여도 PR을 연다. 티켓 밖의 하네스·설정 변경은 `chore/<slug>`, 티켓 밖의 제품 코드 수정은 `fix/<slug>`(대기열 23), 문서만 바꾸면 `docs/<slug>`. main 위의 커밋은 `tools/hook_git_main_commit.py`가 막는다. 브랜치 이름은 그 작업을 하는 세션의 제목이기도 하다(`open-session`). `/git-pr`이 `.github/PULL_REQUEST_TEMPLATE.md`를 채운다.
- 병렬 브랜치는 PR 전에 main에 rebase한다. 병합은 `/git-pr-merge`의 squash이고 main 이력은 PR 단위다. PR 제목이 곧 main의 커밋 제목이므로 컨벤셔널 커밋 형식이다. 리뷰는 아래 리뷰 파이프라인.
- 병렬 작업은 프론티어(막힌 것이 없는 티켓)에서만 하고, 티켓마다 워크트리 하나다. 일지는 `docs/journal/<날짜>-<NN>-<슬러그>.md`이고 `NN`은 그날의 순번이다. 같은 날 세션 둘이 쓰면 순번이 갈라 주고, "최신 파일"은 이름 정렬로 정한다.
- 커밋 메시지는 컨벤셔널 커밋, 한국어. 형식(`<타입>: <제목>`, 72자, 마침표 없음)은 commit-msg 훅이 판정하고, 본문의 "왜 그렇게 했는지와 남긴 위험"은 리뷰가 본다.
- PR을 연 세션이 반영과 병합까지 한다(`/git-pr-feedback`, `/git-pr-merge`). PR 생성이나 병합은 세션을 끝내는 사건이 아니라 `next-session` 스킬의 계기이고, 계기는 훅(`tools/hook_pr_next_session.py`)이 넣는다. 지시문은 병합 뒤에 실행된다. 세션을 끝내는 것은 지시문의 "어디서"가 새 세션일 때뿐이며, 그때 `open-session` 스킬이 같은 체크아웃에 연다(딥링크, 워크트리 없음). "이 세션"이면 이어간다. 어느 쪽인지는 결정표(스킬)가 정하고, 사용자가 이어서 지시하면 따른다.

## 리뷰 파이프라인
세 축이다. 표준·명세, 보안·버그·성능, 유지보수성·경계. 축 이름은 이 줄이 원천이다. 판단 기준과 심각도의 원천은 `CODING_STANDARDS.md`이고 여기는 누가 언제 무엇을 보는지만 적는다.

1. **커밋 전 셀프 리뷰.** `/code-review`가 표준 축(`CODING_STANDARDS.md`)과 명세 축(`.scratch/<slug>/spec.md`)을 본다. 범위는 merge-base 이후 커밋과 미커밋 작업 전부이고, 문서만 바뀐 변경도 면제하지 않는다. Critical·Major는 커밋 전에 고친다. 건너뛰지 않는다. Minor·Nit은 별도 티켓으로 뺄 수 있다. 보고를 받은 뒤 그대로 구현하지 않고 근거를 먼저 확인하는 것은 이 축도 2단계와 같다. 아래 초록 착시의 반대편이다. 범위를 잡는 법과 반영 절차는 스킬 1·6단계.
2. **PR 직전 CodeRabbit CLI.** `coderabbit-review` 서브에이전트(`.claude/agents/`)가 보안·버그·성능 축을 PR 전에 한 번 본다. 트리아지(유효·오탐·보류)만 하고 수정은 본 세션이 한다. CLI 상한은 개발자당 시간당 3회이고 롤링 윈도다(공식 요금제 문서의 rate limits 표, 2026-09-21 확인). 공개 저장소라 OSS 플랜이지만 CLI 상한은 무료 플랜과 같다. "PR마다 한 번, `sdk`·`core`·`adapters`가 우선"은 한도가 아니라 우리 선택이다. 시간당 3회면 커밋마다도 돌 수 있으므로 바꾸려면 ADR을 남긴다. `coderabbit --usage`는 청구 주기 누적과 초기화 날짜만 보여주고 시간당 잔량은 보여주지 않는다.
   - **CLI가 연결 단계에서 즉시 끝나는 것은 한도가 아니라 좌석 미배정이다.** 증상은 `You are not a member of the requested organization`이고 확인은 `coderabbit auth status`의 `Seat: not assigned`다(2026-09-23 실측). **좌석 배정에는 유료 구독이 필요하다** — 공식 문서 `management/seat-assignment`가 요청의 전제를 "active paid subscription"으로 적고 체험 종료 후에는 불가하다고 명시한다. 배정 화면은 조직 설정의 Team Management이고 구독 상태는 Subscription and Billing이지만, `Plan: Free`에서는 거기 배정할 좌석이 없다. 2026-09-22까지는 CLI가 실제로 돌았으므로(일지 `2026-09-22-10`, finding 3건) 체험 종료로 끊긴 것으로 본다. **유료 전환 전까지 PR 직전 CLI 축은 구조적으로 비어 있고** 보안·버그 축은 PR 봇 하나다 — 그것도 OSS 시간당 한도에 걸리므로, 축이 비는 것을 PR 체크리스트에 그대로 적는다.
3. **PR 리뷰.** 봇 둘이 역할을 나눈다. CodeRabbit(`.coderabbit.yaml`)이 보안·버그·성능, Claude Code Review(`.github/workflows/claude-code-review.yml`)가 유지보수성(리뷰 관점 넷)과 경계(import-linter가 못 보는 원칙 IV 위반, `sdk` 계약 변경의 동반 수정). CI가 자동 검사. 별이 10개 미만인 공개 저장소는 CodeRabbit이 자동으로 돌지 않으므로(PR #12 실측), PR을 연 직후 에이전트가 `gh pr comment <번호> --body "@coderabbitai review"`로 요청한다. OSS 플랜의 PR 리뷰 상한은 저장소 별 수에 따라 시간당 1~10회이고 우리는 별이 적어 하한 쪽이다. CodeRabbit 체크는 한도를 넘거나 요청이 없어도 `pass`가 되므로 필수 검사(가드레일 절)에 넣지 않고 코멘트가 있는지로 판정한다. 셋이 초록이고 코멘트를 반영한 뒤 `/git-pr-merge`. 이력은 ADR 0006.
4. **반영.** `/git-pr-feedback`이 CI 결과와 코멘트를 읽어 반영한다. 보류한 지적은 별도 티켓.

봇의 초록은 리뷰했다는 뜻이 아니다(선행 저장소 실측).
- CodeRabbit(PR)은 비공개+무료에서 작성자에게 시트가 없으면 변경 요약(Walkthrough)만 남기고 `pass`가 되고, 시간당 한도를 넘으면 "Review rate limited"로도 `pass`다(PR #2 실측 둘). 공개 저장소에서는 전체 리뷰가 무료라 켰다. 한도 초과의 `pass`는 남으므로 코멘트가 있는지 본다.
- Claude Code Review는 **자기 워크플로 파일**(`claude-code-review.yml`)을 바꾼 PR에서 건너뛰면서 `pass`가 된다. 액션이 그 파일을 기본 브랜치의 것과 비교해 다르면 실행하지 않는다(PR #3·#6 실측, 로그 경고 "Skipping action due to workflow validation"). 그 파일의 변경은 별도 PR로 먼저 병합한다. 다른 워크플로 파일(`ci.yml`)만 바꾼 PR은 건너뛰지 않는다.
- Claude Code Review는 플러그인을 쓰던 동안 코멘트 없이 `pass`가 되곤 했다(PR #2·#4·#5). 플러그인이 서브에이전트를 백그라운드로 띄우고 턴을 끝내는데 헤드리스 실행이 그 전에 종료됐다. 그래서 워크플로를 직접 프롬프트(단일 에이전트, 요약 코멘트 하나가 완료 조건)로 바꾸고, 실행 시작 뒤 생긴 `claude[bot]` 코멘트가 0개면 잡을 실패시키는 스텝을 둔다(2026-09-20 회고 후보 1, PR #10). 그 워크플로부터는 코멘트가 없는 초록이 나오지 않아야 하고, 나오면 `uv run python tools/gh_run_summary.py <run-id>`로 결과 블록·경고·Claude의 말을 본다.
- Claude Code Review는 PR 헤드의 `.claude/`, `CLAUDE.md`, `.mcp.json`을 쓰지 않고 main의 것으로 되돌린다. 하네스를 바꾼 PR은 병합된 뒤에야 리뷰에 반영된다.
- 병합 전에 코멘트가 실제로 있는지 본다. 코멘트 0개인 초록은 "리뷰 없음"으로 읽고 이유를 확인한다.
- **`gh pr checks`의 초록이 현재 HEAD의 것이 아닐 수 있다.** 푸시 직후 GitHub가 PR head를 갱신하기 전에 조회하면 이전 커밋의 결과가 그대로 보인다(PR #44 실측. 새 커밋에 대한 워크플로 실행이 하나도 없는데 세 축이 전부 `pass`였다). 위아래의 다른 항목들이 "리뷰가 돌지 않았는데 pass"인 것과 달리 이것은 **다른 커밋의 pass를 현재 것으로 읽는 것**이라, 코멘트가 있는지로는 잡히지 않는다 — 그 코멘트도 이전 커밋의 것이다. 판정은 `gh run list --branch <브랜치> --json headSha`로 **어느 커밋이 검사됐는지** 보는 것이고, 병합 직전에 `gh pr view --json headRefOid`와 `git rev-parse HEAD`가 같은지 먼저 본다. 동기화는 몇십 초 걸릴 수 있다.
- CodeRabbit이 초록으로 지나가는 사유가 하나 더 있다. **별이 10개 미만인 저장소는 자동 리뷰를 받지 않는다**(PR #43 실측, "This repository does not receive automatic reviews because it has fewer than 10 stars"). 공개라서 무료인 것과 자동으로 도는 것은 다르다. 수동으로 `@coderabbitai review`를 남겨야 하고, **그 코멘트 뒤에 푸시하면 "Pull request base or head changed"로 아무것도 하지 않는다**(같은 PR 실측). 요청은 마지막 푸시 뒤에 남긴다.
- PR #43이 "반례"로 적혀 있던 것은 조건을 잘못 읽은 것이었다. #43은 `ci.yml`만 바꿨고 건너뛴 #3·#6은 둘 다 `claude-code-review.yml` 자체를 바꿨다(2026-09-28 `git show --stat`으로 확인). 조건은 위 항목대로 "자기 워크플로 파일이 다른가"이고 반례가 아니다. 판정은 언제나 "코멘트가 실제로 있는가"다.
- CodeRabbit PR 리뷰는 OSS 시간당 한도에 자주 걸린다(첫 슬라이스 PR 일곱 중 다섯이 "Review rate limited"로 `pass`). 그 PR의 보안·버그 축은 PR 직전 CLI 슬라이스 리뷰 결과를 그 PR 코멘트로 링크한 것이 대체이고, 링크가 없으면 리뷰 없음이다.

전제 둘은 사람이 한 번 한다. `claude setup-token`으로 만든 토큰을 저장소 시크릿 `CLAUDE_CODE_OAUTH_TOKEN`에 등록, 로컬 `coderabbit auth login`. 에이전트는 토큰과 시크릿을 다루지 않는다. 등록 여부만 `gh secret list`로 본다. 이름과 시각만 나온다.

## 이슈 관리
로컬 마크다운. 전체 계획은 `.scratch/plan.md`, 기능별 명세와 티켓은 `.scratch/<feature-slug>/`. 규약은 `docs/agents/issue-tracker.md`. 팀원이 생겨 티켓 번호가 충돌하면 setup 스킬을 다시 돌려 트래커를 바꾼다.

## TODO
`TODO(<기능슬러그>/<티켓번호>): 설명` 형식만 쓴다. ruff TD 규칙이 판정한다. 티켓 없는 TODO는 금지다.

## 문서 위치
문서는 범위가 있는 곳에 둔다. 저장소 전체에 해당하면 루트 `docs/`, 한 앱에만 해당하면 그 앱 안(README, 중첩 `CLAUDE.md`). 같은 사실을 두 곳에 두지 않고, 지역 문서는 루트를 요약하지 않고 가리키며, 루트가 지역 문서를 색인한다. 헌법, 용어집, ADR 번호열은 하나다. 지역 결정도 루트 ADR 열에 넣고 제목에 범위를 적는다.

## 환경 규약 상세
명령을 치기 전에 알아야 하는 것은 `CLAUDE.md` 환경 함정에 있다. 그 밖에 선행 저장소가 겪은 것과 가끔 쓰는 것.
- ruff E501은 표시 폭 기준이라 한글 한 글자가 2로 세어진다.
- `PYTHONUTF8=1`은 `.claude/settings.json`의 `env`가 넣는다(대기열 40). 설정 `env`의 값이 Bash 도구의 명령에 보이는 것을 사용자 설정의 다른 값으로 실측했다(2026-09-28). 훅 프로세스 쪽은 재지 못했고 훅은 어차피 stdin을 바이트로 읽는다. 사용자 터미널에서 도는 pre-commit은 이 밖이라 conftest가 stdout을 UTF-8로 고정한다.
- 환경이 없어 skip된 테스트는 초록이 아니다. `tests/conftest.py`가 skip이 하나라도 있으면 세션을 실패로 끝낸다(2026-09-28). `-m`의 deselect는 skip이 아니다.
- `alembic.ini` 같은 ini 계열은 환경변수로 인코딩을 못 바꾼다. ASCII만.
- pyright 프로브는 `tests/` 아래에 둔다. 점 디렉터리와 `include` 밖은 검사 없이 "0 errors"다. 분석 여부는 `--outputjson`의 `summary.filesAnalyzed`로 본다. `--pythonpath`는 `[tool.pyright]`의 `venvPath`·`venv`에 덮여 무시되니 임시 환경은 `--venvpath`로 넘긴다.
