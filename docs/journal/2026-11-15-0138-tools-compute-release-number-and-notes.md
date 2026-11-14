# 도구가 판 번호와 릴리스 노트와 배포 파일 묶음을 짓고 번호 태그를 판정한다 (release-image 티켓 04)

브랜치 `feature/04-tools-compute-release-number-and-notes`. 이 세션의 제목은 인계 직전까지 `feature/04-tools-compute-release-number-and-notes`이다.

## 사용자 프롬프트 원문

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/release-image/issues/04-tools-compute-release-number-and-notes.md
>
> 다음 작업: .scratch/release-image/issues/04-tools-compute-release-number-and-notes.md. 도구가 판 번호와 릴리스 노트와 배포 파일 묶음을 짓고 번호 태그를 판정하게 한다
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 3 중 3. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/release-image/issues/04-tools-compute-release-number-and-notes.md
> 브랜치: feature/04-tools-compute-release-number-and-notes
> 모델: Sonnet 5.5 / high
> 읽을 것: 나란히 도는 나머지 티켓 .scratch/release-image/issues/02-example-mcp-server-runs-without-npx.md, .scratch/release-image/issues/03-processes-bind-container-network-in-image.md
> 이어받을 상태: 티켓 01이 PR 570으로 병합되어 02·03·04가 풀렸다. 01의 일지(docs/journal/2026-11-14-2318-repo-version-reads-0-0-0.md)에는 병합을 마친 뒤에야 '다음' 절이 없다는 것을 알았다. 세 세션이 함께 돌아 PC 부하로 시간에 기대는 시험이 번갈아 빨개질 수 있다(같은 일지의 '커밋과 PR 직전 리뷰'에 첫 시도 빨강과 홀로 돌려 통과한 기록이 있다)
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 dev. tidy-checkouts는 묶음의 첫 세션이 돈다. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

사용자의 다른 말은 없었다. 세션 중간에 사용자가 두 번 "한동안 응답이 없다"는 알림을 보냈고, 그때마다 지금 하는 일을 한 줄로 알리고 이었다.

## 한 것

- 세션 제목을 브랜치 이름으로 바꾸고, `EnterWorktree`로 워크트리 `04-tools-compute-release-number-and-notes`에 들어가 임시 브랜치 `worktree-04-…`를 `feature/04-tools-compute-release-number-and-notes`로 바꿨다. `uv sync`(`uv run`이 처음 부르며 `.venv`를 만들었다)와 `pnpm -C web install --frozen-lockfile`을 쳤다. 이 세션은 나란히 여는 묶음의 첫 세션이 아니라 `tidy-checkouts`는 돌지 않았다.
- 티켓 `Status`를 `in-progress`로 바꿨다(첫 편집). 아직 `done`으로 바꾸지 않았고 체크박스도 비어 있다.
- 명세 "저장소의 자리", "제품 변경의 경로 목록", "판 설정 파일", "번호", "커밋 제목이 서는 자리", "배포 파일 묶음", "판 내기 워크플로", "릴리스 노트", "노트 검사", "취약점 점검", Testing Decisions와, probe README 2번(번호 태그 조회)·7번(커밋 고르기)을 읽었다.
- 실패하는 시험을 먼저 썼다(`tests/tools/test_release.py`, 첫 실행은 import 오류로 수집 실패). 그 뒤 `tools/release.py`를 지었다. `uv run pytest tests/tools/test_release.py`가 74개 통과였다(손으로 쳤다). 그 뒤에 스크립트 진입점 시험 하나(`test_스크립트로_불러도_돌고_구성_오류는_종료_코드_1이다`)를 더하고 `EXISTING` 입력을 실제 출력 꼴로 바꿨는데, 그 두 변경은 아직 돌리지 않았다.

## 설계 결정(이 세션이 정했다)

- 도구는 파일 하나 `tools/release.py`이고 하위 명령 셋(`number`, `notes`, `bundle`)과 순수 함수(`judge_number_tag`, `classify`, `ensure_untaken`, `plan_release`, `render_notes`, `build_bundle`)로 짠다. 다른 도구를 import하는 길은 커밋 검사의 `PATTERN` 하나뿐이고, 스크립트로 부를 때 저장소 루트를 `sys.path`에 넣는 방식은 `tools/plan_table.py`의 선례를 따랐다.
- 제품 경로 목록은 `PRODUCT_PATHS`(튜플 다섯) 한 자리다. 05의 노트 검사가 같은 것을 쓰도록 05 티켓 끝에 메모를 남겼다.
- 커밋 고르기는 `git log --no-merges --full-history --topo-order --reverse <지난 태그>..<머리> -- <경로>`다. 첫 부모 따라가기와 기본 단순화는 쓰지 않는다. 시험이 출시 병합(둘째 부모 쪽 커밋), 되돌려 합치기와 핫픽스, 바꾸고 되돌린 한 쌍을 임시 저장소로 짓는다.
- 번호 도구의 출력은 `release=`, `number=`, `tag=`, `previous_tag=`의 `key=value` 네 줄이다. 판을 내지 않아도 종료 0이고, 구성 오류는 `release: <까닭>`을 stderr에 적고 종료 1이다.
- 판 설정 파일은 작업 트리의 `deploy/release.toml`을 읽는다. 파일이 없거나 비면 칸이 없는 것이다. 칸 하나(`candidate_for`) 밖의 키나 표, 틀린 꼴은 구성 오류다.
- 노트의 머리 이름은 명세가 이름을 주지 않은 셋(경고, 소개, 기능 소개)을 이 세션이 정했다. 나머지 넷은 명세의 이름 그대로다(올릴 때 할 일, 새 기능, 고친 것, 그 밖의 변경). 느낌표 커밋은 "올릴 때 할 일"에만 서고 `### 제목` 아래에 `upgrade/` 파일의 글을 둔다. 기능 단락과 할 일 글은 판을 내는 커밋에 있는 글을 읽고, 그 파일이 지워졌으면 더한 커밋의 것을 쓴다(기능 단락은 지워졌으면 싣지 않는다).
- 노트의 범위의 시작은 새 번호보다 작은 태그 가운데 출시 후보면 가장 큰 것, 정식 판이면 정식 판 가운데 가장 큰 것이다. 새 번호의 태그가 이미 있어도(다시 돌리기) 같은 범위가 나온다.
- 경고는 Grype 결과(`matches`와 `descriptor`가 있는 거르지 않은 JSON)에서 `severity`가 Critical이고 `fix.state`가 `fixed`인 것이다. 이미지·CVE·꾸러미·판이 같은 것은 한 줄이고, ID가 CVE가 아니면 `relatedVulnerabilities`의 CVE를 쓴다. 이미지 이름 차례로 낸다.
- 묶음의 자리 표지는 `@AGENT_OS_VERSION@`(판 번호, `v` 없음)와 `@AGENT_OS_NAMESPACE@`다. compose의 `${…}`와 겹치지 않는다. 그 밖의 `@AGENT_OS_…@`가 남으면 묶음을 짓지 않는다. 풀면 `agent-os-<판 번호>/`에 틀의 파일이 바로 든다. 시각과 소유자와 gzip 이름을 고정해 같은 입력이면 바이트가 같다. 이 결정은 09 티켓 끝에 메모로 남겼다.
- 번호 태그 판정은 `TagVerdict`(`ATTACH`, `KEEP`, `REJECT`, `HOLD`)를 낸다. 조회 출력에서 맨 앞 칸에서 시작하는 첫 `Digest:` 줄을 읽는다.
- 명세 번호 규칙 6(계산한 태그가 이미 있다)은 로컬 태그로는 닿을 길이 없다. 가장 큰 태그가 지난 판이라 계산한 번호가 늘 그보다 크다. 그래서 `ensure_untaken`을 방어로 두고 그 함수만 따로 시험했다. 시험 사례 목록에는 있던 사례이므로 이 사실을 일지와 11 티켓 메모에 남긴다.
- 11이 부를 번호 태그 판정의 명령줄은 이 티켓이 더하지 않았다(티켓이 순수 함수만 요구한다). 11 티켓 끝에 메모를 남겼다.

## 확인한 것

- `docker buildx imagetools inspect docker.io/library/alpine:3.22`를 빈 `DOCKER_CONFIG`로 돌려(저장된 자격을 보내지 않았다) 종료 0과 `Name:`/`MediaType:`/`Digest:` 세 줄 뒤에 들여쓴 `Manifests:` 쪽이 나오는 것을 봤다. 없는 태그는 종료 1과 `ERROR: …: not found` 한 줄이었다. 시험의 `EXISTING` 입력이 이 꼴이다.
- 이 PC의 시스템 `python`(`C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, `.venv` 밖)으로 `tools/release.py number`를 이 저장소에서 쳤다. 태그와 판 설정 파일이 없어 규칙 5의 구성 오류(`release: 출시 후보 칸(…)도 판 태그도 없어 …`, 종료 1)를 냈다. `notes --number 0.1.0-rc.1`은 이 저장소의 이력 전체로 노트 166줄을 냈다(머리 `## 새 기능`, `## 고친 것`, `## 그 밖의 변경` 셋). CI의 `python3`로 돌아 보는 확인은 CI에서 한다.
- `uv run ruff check .`는 통과했고 `ruff format --check`는 `tools/release.py` 하나를 다시 감을 것으로 냈다가 `ruff format`으로 고쳤다(그 뒤 다시 확인하지 않았다). `uv run pyright tools/release.py tests/tools/test_release.py`는 0건이었다(그 뒤 시험 파일에 스크립트 시험과 입력 갈래를 더했다).

## 셀프 리뷰(/code-review, 이어받은 세션)

범위: base `9a68c2bb9`(origin/dev와의 merge-base), 커밋 0, 미추적 3(`tools/release.py`, `tests/tools/test_release.py`, 이 일지), 수정 4(티켓 04·05·09·11). 표준 축은 sonnet·high, 명세 축은 세션의 모델로 돌렸다. 표준 축은 Critical·Major 없음에 Minor 여럿, 명세 축은 빠진 것 둘, 범위 넘침 둘, 틀려 보이는 것 넷을 냈다.

고친 것(PR 직전 리뷰에 밀 주장은 아래 원문 그대로다):

- 이름을 바꾼 기능 조각을 놓쳤다. `_added` 의 `git log --diff-filter=A` 는 기본으로 이름 바꾸기를 찾아 옮긴 파일을 `R` 로 내서 더해진 것으로 세지 않았다. `--no-renames` 를 주었고 `_upgrade_entry` 의 `diff-tree` 에도 같이 줬다. 시험 `test_범위_안에서_이름을_바꾼_기능_조각은_바꾼_뒤의_이름으로_싣는다` 를 더했고, `--no-renames` 를 빼면 빨강인 것을 봤다.
- 번호 태그 판정이 종료 코드를 보지 않고 `: not found` 로 끝나는 마지막 줄만 보아 `judge_number_tag(127, "sh: 1: docker: not found", …)` 가 `ATTACH` 였다. 종료 코드가 1 일 때만 "없다" 로 읽는다. 시험 `test_종료_코드가_1이_아니면_not_found로_끝나도_붙이지_않는다` 를 더했고, 조건을 빼면 빨강인 것을 봤다.
- 이름공간 정규식이 Docker 경로 한 토막이 허용하는 `a--b`, `a__b` 를 거부했다. `[a-z0-9]+(?:(?:[._]|__|-+)[a-z0-9]+)*` 로 넓혔다. `docker.io/foo` 처럼 `/` 가 든 것은 이름공간이 한 토막이라 계속 거부한다. 시험은 받는 여섯과 거부하는 여덟을 `match` 와 함께 고정한다.
- 독스트링과 티켓 메모의 사실 문장을 고쳤다. "하위 명령 셋과 순수 함수 하나다" 는 닫힌 말이라 `classify` 같은 순수 함수가 더 있다고 적었다. "노트 검사도 같은 것을 쓴다" 는 현재형인데 05 가 아직 없어 "가져다 쓰게 한다" 로 바꿨다. `--grype` 는 이미지마다 한 번씩 거듭 쓰는 플래그라고 독스트링과 11 메모에 적었다(`--grype a=x b=y` 는 종료 2 다). 05 메모가 `classify` 로 꼴에 맞지 않는 제목을 가를 수 있다고 적은 것은 틀렸다(`Revert "…"` 와 쓰레기 제목이 둘 다 `(None, False)`). (가) 는 `PATTERN` 과 `PASS_PREFIXES` 를 직접 쓴다고 고쳤다. 09 메모와 독스트링에 빈 하위 폴더와 실행 권한이 묶음에 들지 않는다고 적었다.
- `Digest:` 줄의 꼴은 커밋한 프로브가 아니라 이 세션이 손으로 본 출력이다. 독스트링, 시험 주석, 11 메모에 "손으로 봤다, 커밋한 프로브는 없다" 로 적고, 11 이 프로브를 고칠 때 README 2번에 옮기게 했다.
- 시험이 없던 못 보는 것에 시험을 더했다. 번호·이름공간 오류에 `match`, UTF-8 이 아닌 파일의 그대로 담기와 빈 하위 폴더 제외, 심볼릭 링크 거부(윈도에서 링크를 만들 권한이 없을 수 있어 `Path.is_symlink` 만 바꿔 같은 길을 밟는다), `--head` (번호와 노트, 없는 리비전은 종료 1).
- `product_commits` 와 `_added` 가 복사하던 `git log` 여섯 인자와 `span` 계산을 `_log` 하나로 모았다. `_upgrade_entry` 의 지역 변수 `done` 이 `_run` 의 `done`(`CompletedProcess`)과 뜻이 달라 `added` 로 바꿨다.

남긴 것과 이유:

- 05·09·11 티켓 끝의 메모는 범위 넘침이 아니다. code-review 스킬 6단계 4가 다음 티켓에 걸리는 것은 받는 쪽 티켓에 적으라고 한다.
- 한 파일 663줄의 Divergent Change, `(repo, since, head)` 의 Data Clumps, 판 번호가 `str` 로 돌며 `parse_version` 으로 다시 읽히는 Primitive Obsession, 오류 문구 한 줄의 중복은 판단 항목이다. 티켓이 도구 한 파일로 정했고, 05 가 `classify` 를 가져다 쓸 때 쪼갤지 본다.
- 시험 89개가 임시 저장소와 git 프로세스를 새로 만들어 한 번에 110초 안팎이다. 시간 단언이 없어 pre-commit 의 병렬 부하에서도 위반은 아니다. 느려지면 `tmp_path_factory` 로 저장소를 나눠 쓴다.
- `_run` 이 자식 환경을 그대로 상속한다. 도구는 CI 에서만 돌고, 시험은 `tests/conftest.py` 가 `GIT_*` 를 벗겨 안전하다.
- 다른 zlib 판 사이에서도 묶음의 바이트가 같은지는 재지 않았다. 시험은 같은 환경 안에서 두 번 지은 바이트가 같다는 것까지만 본다.

다시 돌린 명령: `uv run ruff check`·`ruff format --check`(통과), `uv run pyright tools/release.py tests/tools/test_release.py`(0건), `uv run pytest tests/tools/test_release.py`(89개 통과, 111초). 시스템 `python`(`.venv` 밖)으로 `tools/release.py number` 를 이 저장소에서 쳐 규칙 5의 구성 오류와 종료 1을, `notes --number 0.1.0-rc.1` 로 노트 글을 확인했다. 손으로 친 `uv run python tools/run_checks.py` 는 열 검사가 모두 통과했다(exit 0, 약 16분).

첫 커밋 시도는 pre-commit 의 pytest 에서 두 시험이 빨개 막혔다. `tests/channel/cli/test_interrupt.py::test_서버를_닫기_시작한_뒤에_한_번_누르면_닫기를_마치고_중단으로_끝난다`(자식이 30초 안에 끝나지 않았다)와 `tests/tools/test_rerun_runner.py::test_같은_갈래가_두_번_든_파일럿의_두_회차가_함께_돌아도_번호가_다르다`(동시에 도는 회차가 1이었다)다. 둘 다 이 브랜치가 건드리지 않은 시간에 기대는 시험이고, 세 세션이 함께 돌아 PC 부하가 높던 때다. 그 둘만 `uv run pytest <두 시험> -p no:xdist` 로 홀로 돌리니 39초에 통과했다(손으로 쳤다). 이어 pre-commit 의 인용 대조가 이 일지의 인용 하나를 경고해 따옴표를 뗐다.

## 커밋

`781d86ab0` 로 커밋했다. pre-commit 의 pytest 가 세 번 막힌 뒤(시험은 `test_interrupt.py`, `test_rerun_runner.py`, `test_rerun_gates.py` 의 시간에 기대는 것들이다) 다른 세션의 `git commit` 이 줄어든 때 모두 통과했다(pytest 397.6초, web-verify 683.3초). 이 브랜치가 건드리지 않은 시험이고 훅은 건너뛰지 않았다.

## PR 직전 리뷰(coderabbit-review, CLI 0.7.5)

`Plan: Free`, `Seat: not assigned` 인데 `coderabbit review --agent --committed --base origin/dev` 가 끝까지 돌아 `review_completed` 를 냈다(7개 파일). CLI 축이다. 서브에이전트가 낸 것은 CLI 원본 1건과 자기가 직접 읽고 잰 2건이다.

고친 것(본 세션이 코드로 다시 확인한 뒤 판정했다. 새 시험 셋은 고치기 전에 빨강인 것을 봤다):

- [Major, 서브에이전트가 직접 잰 것] `--head` 가 `-` 로 시작하면 git 옵션으로 읽힌다. `_log` 의 `span` 이 `--` 앞에 놓이고 `_ensure_ancestor` 와 `_read_at` 도 같다. 서브에이전트가 `--head=--output=<파일>` 로 로그가 그 파일에 쓰이고 도구가 `release=false`, 종료 0으로 끝나는 것을 재현했다. `_check_revision` 을 더해 `plan_release` 와 `render_notes` 입구에서 `ReleaseError` 로 거절한다. 시험 `test_머리가_빼기로_시작하면_git_옵션으로_읽히기_전에_거절한다` 가 두 함수와 명령줄을 모두 밟고 파일이 생기지 않는 것까지 본다.
- [Minor, CLI 원본] 범위 밖에서 더해진 기능 조각을 범위 안에서 이름만 바꾸면 새 경로가 더해진 것으로 잡혀 다시 실렸다. 명세 "범위 밖에서 더해진 조각은 그 뒤에 고쳐졌어도 다시 싣지 않는다" 를 어겼다. `_moved_in` 이 지난 판 태그와 머리의 순 변경에서 이름 바꾸기(`diff -M --diff-filter=R`)의 새 경로를 골라 `_added` 에서 뺀다. 범위 안에서 더한 뒤 옮긴 조각은 옛 경로가 지난 판에 없어 계속 싣는다(앞의 `이름을_바꾼_기능_조각` 시험이 그대로 지킨다). 시험 `test_범위_밖에서_더해진_조각은_범위_안에서_이름을_바꿔도_다시_싣지_않는다` 를 더했다.
- [Minor, 서브에이전트가 직접 읽은 것] `main` 이 `OSError` 를 잡지 않아 `build_bundle` 의 `mkdir` 이 `FileExistsError` 로 죽으면 접두 없이 traceback 이었다. `except (ReleaseError, OSError)` 로 묶었다. 시험 `test_묶음을_쓰지_못하면_접두를_붙여_종료_코드_1이다` 를 더했다.

남긴 것과 이유:

- 내용을 절반 넘게 고치며 옮긴 조각은 `git diff -M` 이 이름 바꾸기로 읽지 못해 다시 실린다. 조각 이름은 기능 계획의 slug 여야 해 옮길 일이 드물고, 고치려면 유사도 문턱을 낮춰 다른 오탐을 부른다. `_moved_in` 독스트링에 못 보는 것으로 적었다.
- 서브에이전트가 오탐으로 본 것(심볼릭 링크와 경로 탈출, 정규식 `fullmatch`, 결정성, `$GITHUB_OUTPUT` 주입, grype JSON)은 본 세션이 앞 셀프 리뷰에서 같은 길을 이미 시험으로 고정했거나 입력이 CI 의 것이라 더 고치지 않았다. 마크다운에 이미지 이름과 CVE 번호를 이스케이프 없이 싣는 것은 입력이 CI 의 스캐너 출력이다.

다시 돌린 명령: `uv run ruff check`(통과), `uv run pyright tools/release.py tests/tools/test_release.py`(0건), `uv run pytest tests/tools/test_release.py -p no:xdist`(92개 통과, 42초). 이 수정을 담은 두 번째 커밋의 pre-commit 결과는 PR 본문에 적는다.

## 봇 첫 회차(PR 572, 머리 f5cae16d6)

claude-review 가 Critical·Major 없이 Minor 셋과 Nit 하나를 냈다. 첫 회차라 지적마다 판단했다.

- 고친 것: Nit 의 실패한 `git` 호출 stderr 풀기 두 줄을 `_stderr` 로 모았다. Minor 의 `build_bundle` 한 함수가 맡은 넷(검증, 파일 모으기, 자리 표지 채우기, tar·gzip 짓기)을 `build_bundle`(검증과 조립)·`_collect`(모으기와 채우기)·`_pack`(바이트 짓기)로 나눴다. 검사 순서와 오류 문구는 그대로 두었고(코드를 읽어 맞췄다), `uv run pytest tests/tools/test_release.py -p no:xdist -q` 로 손으로 쳐 92개가 48.71초에 통과했다. `uv run ruff check`와 `uv run pyright tools/release.py tests/tools/test_release.py` 도 통과했다(0건).
- 뒤로 넘긴 것: `tools/release.py` 한 파일에 번호 계산·노트·묶음·태그 판정 넷이 든 Divergent Change 는 11 이 하위 명령을 더하기 전에 쪼갤지 정한다. `judge_number_tag` 는 부르는 곳이 시험뿐이라 11 이 워크플로에서 부르는 하위 명령을 더하지 않으면 그 함수와 시험을 지운다. 둘 다 티켓 11 의 04 메모에 적었다. `ensure_untaken` 은 `plan_release` 가 부르는 것을 코드에서 읽었으므로(`tools/release.py` 의 호출 한 곳) 죽은 코드가 아니고, 로컬 태그로는 닿을 길이 없다는 방어로 남긴다.

## 이어서 할 일

PR #572(https://github.com/njh6803/agent-os/pull/572, base `dev`)를 열었다. 머리는 `f5cae16d6`(수정 커밋)이고 앞 커밋은 `781d86ab0` 이다. 열 때 검사 여덟이 pending 이었고 `@coderabbitai review` 코멘트는 아직 남기지 않았다(새 세션이 남긴다). 이 세션의 앱 PR 연결(`get_status` 가 bound 로 읽었다)은 PR 을 연 세션에 묶여 있다.

- `merge.md` 2(봇 회차)부터 한다. 첫 `@coderabbitai review` 코멘트를 남기고 상태를 한 번 읽어 pending 이면 `tools/wait_ci.py 572` 를 백그라운드로 띄운다. 회차 세기와 뒤로 넘긴 일은 `merge.md` 2대로 한다.
- 봇이 이 PR 에서 새 지적을 내면 위 "남긴 것과 이유" 와 겹치는지 먼저 본다(겹치면 보류 이유를 PR 코멘트에 남긴다).
- 병합은 워크트리 길이다(`--squash --match-head-commit <머리 SHA>`, `--delete-branch` 없음). 병합 뒤 05·09·11 티켓이 04 의 메모를 받아 쓴다. 이 일지의 `## 다음` 절과 회고(`retro`)는 단계를 닫는 마지막 세션이 이 일지까지 읽고 쓴다.

open-session을 부른다 2026-11-14T16:41:02Z
open-session을 부른다 2026-11-14T20:37:21Z
