# 저장소의 판 번호가 0.0.0이 된다 (release-image 티켓 01)

브랜치 `feature/01-repo-version-reads-0-0-0`. 이 세션의 제목은 인계 직전까지 `feature/01-repo-version-reads-0-0-0`이다.

## 사용자 프롬프트 원문

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/release-image/issues/01-repo-version-reads-0-0-0.md
>
> 다음 작업: .scratch/release-image/issues/01-repo-version-reads-0-0-0.md. 저장소의 판 번호를 0.0.0으로 바꾼다(`agent-os --version`, 저장소 `openapi.json`, serve의 `/openapi.json`)
> 다음 단계: 구현
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고 … EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/release-image/issues/01-repo-version-reads-0-0-0.md
> 브랜치: feature/01-repo-version-reads-0-0-0
> 모델: Sonnet 5.5 / high
> 읽을 것: 일지 docs/journal/2026-11-14-1748-release-image-tickets.md의 "다음"
> 이어받을 상태: 앞 세션의 pre-commit에서 시간에 기대는 시험(test_rerun_runner, test_interrupt 등)이 PC 부하(CPU 100%, 다른 세션 다섯)로 번갈아 빨갰다(같은 일지의 "셋째 커밋"). 로컬 pytest를 뺀 SKIP=pytest는 그 커밋 한 번만 사용자가 승인했다
> 이번 요청 범위: PR과 병합까지

사용자의 다른 말은 없었다. 이 세션이 한 결정은 아래 둘이다.

## 한 것

- `tidy-checkouts`: 주 체크아웃을 `c21a4fc3b`에서 `4e3752592`(origin/dev)로 당겼고, 병합된 로컬 브랜치 `worktree-release-image-tickets` 하나를 지웠다. 남긴 워크트리는 점유, 앱 표지, 병합된 PR 없음, 바뀐 파일, 다시 만들 수 없는 무시된 항목 때문이고 사람에게 넘길 것은 없었다.
- 워크트리 `01-repo-version-reads-0-0-0`에 들어가 임시 브랜치 `worktree-01-repo-version-reads-0-0-0`를 `feature/01-repo-version-reads-0-0-0`으로 바꿨다. `uv sync`를 쳤다.
- 티켓 `Status`를 `in-progress`로 바꿨다가 끝에 `done`으로 바꾸고 체크박스 여섯을 모두 채웠다. 기능의 마지막 열린 티켓이 아니라 기능 계획의 `**끝:**` 줄은 적지 않았다. `uv run python tools/plan_table.py`를 돌려 `.scratch/plan.md`가 바뀌었다.
- 판 바꾸기: `pyproject.toml`의 `version`을 `0.0.0`으로, `uv lock`으로 `uv.lock`의 자기 패키지 항목을 바꿨다("Updated agent-os v0.1.0 -> v0.0.0"). `uv sync --locked`가 지나가 설치된 판이 `0.0.0`이 되었다. `PYTHONUTF8=1 uv run python tools/export_openapi.py`로 `openapi.json`의 `info.version`만 바꿨다. `uv run agent-os --version`이 `0.0.0`을 찍는다.
- `web/packages/api-client`의 생성물에는 판 칸이 없어 바꾸지 않았다(grep으로 봤다).
- 시험 셋을 더했다. 번호는 글자로 박지 않고 설치된 패키지의 판(`importlib.metadata.version("agent-os")`)과 견준다.
  - `tests/test_server.py`의 `test_serve_의_API_문서_판_칸이_설치된_패키지의_판이다`: `/openapi.json`(관리 토큰)의 `info.version`.
  - `tests/channel/cli/test_main.py`의 `test_version_옵션은_설치된_패키지의_판을_찍는다`.
  - 새 파일 `tests/test_repo_version.py`: `pyproject.toml`의 판이 `0.0.0`, `uv.lock`의 자기 패키지 항목과 `openapi.json`의 판 칸이 `pyproject.toml`과 같다. 이 파일의 첫 시험이 구현 전의 빨강이었다(`'0.1.0' == '0.0.0'`).
  - 앞의 둘은 구현 전부터 초록인 가드라(코드가 이미 `importlib.metadata`로 읽는다), 변이 표 `.scratch/release-image/probes/repo_version_mutations.toml`로 빨강을 봤다. 변이 둘(서버와 CLI가 `"9.9.9"`를 박는다)이 모두 기대대로 빨개졌다. `--check`도 지났다. 프로브 `README.md`의 표에 그 줄을 더했다.
- 옛 번호 grep: 살아 있는 문서에서 저장소의 판을 지금 `0.1.0`이라고 말하는 문장은 ADR 0056 결정 "저장소의 번호"의 "`pyproject.toml`의 `version`은 지금의 0.1.0에서 0.0.0으로 한 번 바꾸고" 하나뿐이다(21행. 그 밖의 `0.1.0`은 출시 후보·정식 판 번호, 플러그인 매니페스트의 판, 일지와 프로브 기록이다). 이 문장은 이 변경을 가리키는 결정 시점의 값이고 ADR이라 승인 없이 고치지 않았다. `.claude/rules/adr.md`의 "달지 않는 것"(결정 시점의 수나 근거를 적은 문장)에 들어 포인터도 달지 않았다. 고칠지는 사용자 몫이다.
- 검증: `uv run ruff check . && uv run ruff format --check .` 통과. `uv run python tools/run_checks.py` 전부 통과(check-ticket, lint-imports, zizmor, check-type-escapes, check-instructions, pyright, pyright-linux, run-hooks, pytest 618초, web-verify 1049초, 종료 코드 0). 이어받을 상태에 적힌 시간 시험의 빨강은 이번 러너에서 나지 않았다.
- `uv run python tools/sibling_overlap.py`: 번호 겹침 없음. `.scratch/plan.md`만 워크트리 `mcp-shutdown-spec`과 `widget-login-state-design`이 함께 고쳤다(도구가 만드는 표라 병합 때 다시 돌리면 된다).

## 셀프 리뷰 (이어받은 세션, 2026-11-14)

범위: base `4e3752592`(origin/dev와 같다), 추적 파일 8개의 미커밋 변경, 미추적 3개, 커밋 0개. 서브에이전트 둘이 읽었다(표준 축은 sonnet·high). 두 보고가 "수정하지 않았다"고 적었고 작업 트리는 그대로다.

- 표준 축: 하드 위반 없음. 변이 둘을 서브에이전트가 `tools/mutate.py`로 직접 돌려 기준선 초록, 변이 둘 빨강을 봤다(도구 실행). 프로브 README의 "pytest 9.1.1, Python 3.12.10"은 `uv run pytest --version`, `uv run python --version`과 같다고 봤다(손으로 대 봤다).
- 명세 축: 티켓 체크박스 여섯 대조. `web/packages/api-client/src/generated/openapi.ts`에 판 칸이 없다는 것, `tests/` 아래 `0.1.0`이 모두 플러그인 매니페스트의 판이라는 것을 grep으로 확인했다. `uv lock --check` 통과.
- 고친 것 (Major 하나, Minor 하나):
  - Major, 이 일지의 닫힌 주장(살아 있는 문서에 저장소의 판을 0.1.0이라고 말하는 문장이 없다는 것)이 ADR 0056 21행 하나를 빠뜨렸다. 위 "옛 번호 grep" 줄을 그 하나가 남았다고 고쳤다.
  - 표준 축 주장 검증, `tests/test_repo_version.py` 독스트링의 과장. "개발 PC는 늘 0.0.0을 보이고"와 "정식 판 번호는 git 태그가 정해"는 ADR 0056에 없거나 틀렸다(ADR은 출시 후보의 번호도 태그가 정한다고 적는다). ADR의 문장("소스에서 바로 돌린 것이 판 이미지가 아님을 드러내고", "CI가 이미지를 지을 때 그 판의 번호를 넣어")만 옮기도록 다시 썼다.
- 남긴 것:
  - Minor, `.scratch/release-image/probes/serve_image/run.py`의 항목 1(판 번호)이 저장소가 0.1.0일 때의 기대(498행 `installed="0.1.0"`, 541행 `"Updated agent-os v0.1.0 -> (dynamic)"`)를 박고 있다. 이 티켓이 닿을 몫이 아니고(티켓 "이 티켓의 체크박스가 요구하는 것만 쓴다") 이 프로브를 다시 돌리는 07이 항목 2, 4, 5, 6, 7만 돌아 닿지 않는다. 항목 1을 다시 돌릴 때 고치도록 받는 쪽인 티켓 07 끝에 메모를 적었다. 07의 Blocked by는 02, 03이라 01을 포함하지 않지만 메모는 07 파일 안에 있어 07을 하는 세션이 읽는다.
  - Minor, `tests/test_repo_version.py`의 둘째·셋째 시험(잠금 파일, `openapi.json`이 `pyproject.toml`과 같다)은 `uv sync --locked`와 `tests/tools/test_export_openapi.py`가 이미 지키는 것과 일부 겹친다. 티켓 첫 체크박스의 "같은 변경에서 함께 바꾼다"를 `pyproject.toml`과 맞대는 고리는 둘 다 새롭다고 보고 남겼다.
  - ADR 0056 21행의 "지금의 0.1.0": 위와 같다. 사용자 몫.
  - 표준 축이 낸 smell 둘(Duplicated Code, Primitive Obsession)은 판단 항목이고 문제가 작아 남겼다.
- 대 보지 못한 것: 일지의 `run_checks.py` 시간(pytest 618초, web-verify 1049초)과 "Updated agent-os v0.1.0 -> v0.0.0" 출력은 앞 세션이 낸 값이고 이 세션이 다시 재지 않았다(서브에이전트도 로그가 없어 대 보지 못했다).

## 커밋과 PR 직전 리뷰

- 커밋 `086d68ef2`. 커밋 전에 `git branch --show-current`가 `feature/01-repo-version-reads-0-0-0`이었고 `uv run python tools/sibling_overlap.py`는 번호 겹침 없음이었다(둘 다 손으로 쳤다).
- pre-commit 첫 시도는 `tests/tools/test_rerun_runner.py::test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다` 하나가 빨개(`assert 1 == 0`) 막혔다(pytest 1 failed, 7313 passed, 837초). 이어받을 상태가 적은 시간 시험 계열이다. 그 시험을 홀로 `uv run pytest -q tests/tools/test_rerun_runner.py -k "오염이_한_번이면"`으로 돌리니 통과했다(1 passed, 75초). 같은 커밋의 둘째 시도는 전부 통과했다(pytest 719.6초, web-verify 1004.0초, 종료 코드 0). `SKIP`은 쓰지 않았다. 이 변경은 그 시험이 읽는 코드를 건드리지 않았다.
- PR 직전 CodeRabbit CLI(`coderabbit-review` 서브에이전트, CLI 0.7.5, `coderabbit review --agent --committed --base origin/dev`): `review_completed`, 지적 0건(유효 0, 오탐 0, 보류 0), 본 파일 12개. `auth status`는 `Plan: Free`, `Seat: not assigned`였고 리뷰는 막히지 않았다. 도구가 낸 출력을 서브에이전트가 옮긴 값이다.

## 남은 일

- PR을 열고 봇 회차(CodeRabbit 요청, claude-review)를 반영한 뒤 병합한다. 이 요청의 범위가 병합까지다.
- 이 티켓은 `openapi.json`에 닿는 계약 티켓이다. 계약의 값(판 칸) 하나만 바뀌고 모양은 그대로다.

## 인계

컨텍스트가 인계 문턱을 넘은 채 `셀프 리뷰 직전` 경계에 와서 새 세션에 넘긴다(`next-session handoff.md`). 제목을 `feature/01-repo-version-reads-0-0-0 (인계함)`으로 바꿨고(바뀌기 전 제목은 `feature/01-repo-version-reads-0-0-0`), 이 워크트리의 잠금을 풀었다.
open-session을 부른다 2026-11-14T14:19Z
