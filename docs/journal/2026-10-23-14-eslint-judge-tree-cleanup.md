# 2026-10-23 (14) 판정자 테스트가 앞 실행이 남긴 임시 트리를 지운다

> 사용자: (next-session 지시문을 첫 메시지로 받았다) "대기열 379를 티켓 .scratch/harness/issues/006-eslint-judge-tree-cleanup.md로 쓰고 한다 … 어디서: 새 세션. 나란히 여는 6 중 4. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 … 이번 요청 범위: PR과 병합까지"

## 체크아웃

제목을 `chore/006-eslint-judge-tree-cleanup`로 바꾸고 `EnterWorktree`(`006-eslint-judge-tree-cleanup`)로 들어가 브랜치 이름을 `chore/006-eslint-judge-tree-cleanup`로 바꿨다. 묶음의 넷째라 `tidy-checkouts`는 돌지 않았다. 워크트리에 `web/node_modules`와 `.venv`가 없어 `pnpm -C web install --frozen-lockfile`과 `uv sync`를 쳤다.

## 정한 것

- **`verify`의 첫 단계에도 청소를 넣는다.** 대기열 379의 처방은 `beforeAll`의 청소였다. 그런데 `verify`는 `check:api-client → lint → format → typecheck → test → check:tsconfig` 차례이고, 남은 트리의 위반 사례 파일은 린트를 먼저 빨갛게 해 `test`의 `beforeAll`까지 가지 못한다. `web/judge-Lft001`에 앞 실행과 같은 모양의 트리(위반 사례 파일, api-client로 가는 junction, 프로젝트 tsconfig)를 만들고 `pnpm -C web exec eslint --max-warnings 0 judge-Lft001`을 치니 오류 2개(`no-explicit-any`, `no-meaningless-void-operator`)로 종료 1이었다(손으로 봤다). 그래서 지우는 함수를 `web/tools/judge-trees.ts`에 두고 `beforeAll`과 `verify`의 첫 단계(`clean:judge-trees`)가 함께 부른다. 만드는 이름(`makeJudgeTree`)과 지우는 이름의 원천도 그 모듈 하나다.
- **지우는 꼴.** web/ 바로 아래에서 이름이 `judge-`와 영숫자 여섯(`mkdtempSync`가 붙이는 꼴)인 디렉터리만 지운다. 그 이름의 링크와 파일, 꼴이 다른 이름은 남긴다. `rmSync`에 `maxRetries: 5`를 준다(대기열 65가 적은 윈도우의 순간 잠김).
- **가르지 않는 것.** 트리가 앞 실행의 것인지 지금 도는 다른 실행의 것인지 가르지 않는다(pid 표지를 두지 않았다). 같은 체크아웃에서 verify 둘이 함께 돌면 한쪽의 청소가 다른 쪽의 트리를 지운다. 이 청소 전에도 한쪽의 린트가 다른 쪽의 트리를 읽어 빨갰던 경우라 모듈 독스트링의 못 보는 것에 적었다.

## 한 일

- 티켓 `.scratch/harness/issues/006-eslint-judge-tree-cleanup.md`(번호는 지시문의 006. 쓴 뒤 `sibling_overlap.py`를 다시 쳐 겹침 없음).
- `web/tools/judge-trees.ts`: `makeJudgeTree`, `removeLeftoverJudgeTrees`, 명령 진입(`node tools/judge-trees.ts [루트]`, 지운 트리를 한 줄씩 쓴다).
- `web/tools/judge-trees.test.ts`(시험 열): 남은 트리 지우기, 트리 안의 junction 대상이 남는다, 여럿, 없음, 꼴이 다른 이름, 판정자 트리 이름의 링크와 파일은 남긴다, 새 트리는 지우는 이름이다, 명령, `verify`의 청소가 린트와 Prettier보다 앞이다. 시험을 먼저 써서 모듈이 없어 수집 오류로 빨간 것을 보고, 모듈을 쓴 뒤 `verify` 순서 시험 하나만 빨간 것을 보고 `package.json`을 고쳤다.
- `web/package.json`: `clean:judge-trees` 스크립트와 `verify`의 첫 단계.
- `web/eslint.config.test.ts`: `beforeAll`이 `removeLeftoverJudgeTrees(WEB)` 뒤 `makeJudgeTree(WEB)`. 머리 주석에 한 문장.
- 대기열 379를 이 티켓으로 닫았다.

## 검사

- `pnpm -C web exec vitest run tools/judge-trees.test.ts eslint.config.test.ts --project node`: 두 파일 71개 통과(이 PC, Windows, Node 24.19.0). junction 대상이 남는 시험이 여기서 통과했고, Linux의 심볼릭 링크 길은 CI가 본다.
- `web/judge-Lft001`을 둔 채 `pnpm -C web verify`를 백그라운드로 쳤다. 첫 단계가 `남은 판정자 트리를 지웠다: …\web\judge-Lft001`을 찍었고, 그 뒤 `web/packages/api-client`는 그대로였고 `git status`에 변경이 없었다(손으로 봤다). 린트, Prettier, 타입체크, vitest(파일 30개, 시험 403개), `check:tsconfig`가 통과해 종료 0이었고, 끝난 뒤 `web/judge-*`가 남지 않았다.
- 아직 치지 않은 것: `uv run python tools/run_checks.py`, ruff 두 줄, `/code-review`.

## 인계

경계: 셀프 리뷰 직전. 세션 컨텍스트가 218,807 토큰으로 문턱 200,000을 넘었다. 이 세션의 지금 제목은 `chore/006-eslint-judge-tree-cleanup`이다. 커밋하지 않은 변경이 이 워크트리에 있다(위 한 일 전부와 이 일지). 새 세션은 `/code-review`(고정점 origin/main, 티켓 006)부터 한다. 같은 워크트리에서 `pnpm -C web verify`와 `tools/run_checks.py`를 함께 띄우지 않는다. 이번 청소가 서로의 판정자 트리를 지운다.

인계 지시문:

```
다음 작업: .scratch/harness/issues/006-eslint-judge-tree-cleanup.md(이 워크트리에 커밋하지 않은 채 있다). 판정자 테스트의 beforeAll과 verify의 첫 단계가 앞 실행이 남긴 web/judge-* 트리를 junction을 따라가지 않고 지운다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 379를 티켓 .scratch/harness/issues/006-eslint-judge-tree-cleanup.md로 쓰고 한다
브랜치: chore/006-eslint-judge-tree-cleanup
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/agents/issue-tracker.md(harness 티켓의 서식·상태). 일지 docs/journal/2026-10-23-14-eslint-judge-tree-cleanup.md(이 워크트리에만 있다)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 고정점 origin/main, 티켓 006)부터 한다. 그 뒤 run_checks와 ruff 두 줄, 커밋, PR, 병합. 일지 docs/journal/2026-10-23-14-eslint-judge-tree-cleanup.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-22T17:46:11Z

## 이어받기

> 사용자: (인계 지시문을 첫 메시지로 받았다) "대기열 379를 티켓 .scratch/harness/issues/006-eslint-judge-tree-cleanup.md로 쓰고 한다 … 이어받을 상태: 인계: 셀프 리뷰 직전. … 이번 요청 범위: PR과 병합까지"

새 세션이 제목을 `chore/006-eslint-judge-tree-cleanup`로 바꾸고 `git worktree list`에서 찾은 이 워크트리에 `EnterWorktree(path)`로 들어왔다. 커밋하지 않은 변경 일곱(추적 셋, 미추적 넷)이 그대로 있었다.

## 셀프 리뷰

`/code-review`, 고정점 `origin/main`, base `975bf04c`. 추적 파일 셋이 바뀌었고 미추적 넷, 커밋 없음. 표준 축(sonnet·high)과 명세 축(본 세션 모델)을 나란히 띄웠다.

- 표준 축: Critical·Major 없음, Minor 2, Nit 1. (1) 독스트링의 "Git Bash 의 `rm -rf` 는 junction 을 따라가 실제 패키지를 지울 수 있어"는 근거가 대기열 65의 문장뿐이고, 일지 2026-10-16-22는 리뷰어가 반대(junction만 지우고 대상은 남는다)를 재현했다고 적었다. (2) 참고 규칙(`.claude/rules/tools.md`, 루트 `tools/**`에만 걸린다): 못 본다고 적은 것 둘(verify 둘의 겹침, 재시도 뒤 던짐)에 시험이 없다. Nit: 루트가 없으면 `readdirSync`가 ENOENT로 던진다. 주장 검증은 CI가 Linux에서 이 시험을 돈다, `symlinkSync(…, "junction")`이 Linux에서 심볼릭 링크다, `mkdtempSync`의 이름 60개가 정규식에 맞는다(Windows만), `maxRetries`가 EPERM을 재시도한다(Node 문서), 기본 루트가 web/이다가 맞음이었다.
- 명세 축: 빠진 것과 범위 넘침 없음. Minor 4, Nit 2. (1) Prettier를 빨갛게 하는 것은 위반 사례 파일이 아니라 `JSON.stringify` 한 줄로 쓴 프로젝트 `tsconfig.json`이다(사례 62개를 web의 Prettier 설정으로 대 보니 모두 서식이 맞았다, 손으로 봤다). (2) Git Bash `rm -rf` 문장: 이 PC의 Git Bash(MSYS 3.1.7, coreutils 8.32)에서 junction이 든 트리를 `rm -rf`하자 대상 파일이 남았다(손으로 봤다). (3) 티켓의 "두 번 났고 두 번 다"는 반례가 있다(일지 2026-10-20-01의 `web/judge-jZnujf/`, 2026-10-12-13의 끊긴 커밋 훅). (4) 프로브 `.scratch/harness/probes/precommit_xdist/time_web_steps.py`의 "여섯 단계를 차례로 잇는다"가 이제 일곱 단계라 잔존이다. Nit: 독스트링의 "한쪽의 린트가 다른 쪽의 트리를 읽어 빨갰다"는 출처가 없고 기록(일지 2026-10-07-18)은 Prettier다. Nit: `verify`가 실제로 밟는 길(루트 없이 부르기)을 시험이 밟지 않는다. 수용 기준 1~5와 대기열 379의 닫힘은 함수를 불러 보고 맞다고 했다(`makeJudgeTree` 500번이 모두 정규식에 맞았다).

반영:

- 고친 것: Prettier 까닭을 독스트링·시험 주석·티켓에서 "위반 사례 파일은 린트를, 한 줄로 쓴 프로젝트 tsconfig.json 은 Prettier 를"로 고쳤다. 손으로 다시 봤다. `web/judge-Pr0001`에 같은 모양의 tsconfig와 위반 사례 하나를 두고 `prettier --check`를 파일마다 치자 tsconfig는 종료 1, 위반 사례 파일은 종료 0이었다(스크래치패드 `prettier_leftover.mjs`, 끝에 트리를 지웠다). Git Bash `rm -rf` 문장은 지우고 "손으로 지울 때도 링크를 따라가지 않는 것을 시험이 보는 이 명령을 쓴다"로 바꿨다. 티켓의 횟수는 앞 세션의 러너가 멈춰 남은 세 번(일지 2026-10-20-01·2026-10-20-16·2026-10-22-11)과 그 전의 둘(2026-09-30-02의 `EPERM`, 2026-10-12-13의 끊긴 커밋 훅)로 고쳤고, 티켓의 Git Bash 문장 자리에는 지우는 명령을 분류기가 거부한 기록(2026-10-22-11)을 적었다. 독스트링의 겹침 문장은 "지울 수 있다(재지 않았다)"와 "한쪽의 Prettier 가 다른 쪽의 트리를 읽어 빨갰다(일지 2026-10-07-18)"로 고쳤다. 위 정한 것 절의 같은 말("린트가 다른 쪽의 트리를 읽어")은 그때의 기록이라 두었다. 프로브 독스트링·주석과 프로브 README의 행은 "검사 여섯 단계(첫 단계인 판정자 트리 청소는 빼고)"로 고쳤다. 프로브는 단계를 `pnpm -C web run <단계>`로 하나씩 불러 청소 단계를 돌지 않는다(코드를 읽었다). 같은 말을 쓴 ADR 0035의 Considered Options와 ADR 0026 본문은 결정 시점의 셈이라 `.claude/rules/adr.md`의 "달지 않는 것"대로 두었다. 시험 하나를 더했다. 모듈을 임시 `web/tools/`에 옮겨 루트 없이 부르면 그 web의 남은 트리를 지운다(작업 디렉터리도 임시 자리). 기본 루트를 `process.cwd()`로 바꾼 변이를 손으로 넣자 이 시험만 빨갰고(`expected '' to contain …`), 되돌린 뒤 파일 하나 11개가 통과했다.
- 남긴 것: 표준 축 (2)의 못 보는 것 둘에 시험을 두지 않았다. 그 규칙은 루트 `tools/**`에만 걸리고, 겹침은 verify 둘을 함께 띄워야 재현되며 재지 않았다고 적었다. 재시도 뒤 던짐은 Node `rmSync`의 동작을 잡지 않는 것뿐이다. 표준 축 Nit(없는 루트의 ENOENT)도 두었다. `verify`는 늘 있는 web/을 넘기고, 틀린 인자로 던지면 그 단계가 빨개 조용히 지나가지 않는다.
- PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 문장): "남은 트리의 위반 사례는 다음 verify 의 린트를, 한 줄로 쓴 프로젝트 tsconfig.json 은 Prettier 를 빨갛게 한다", "손으로 지울 때도 링크를 따라가지 않는 것을 시험이 보는 이 명령을 쓴다", "같은 체크아웃에서 verify 둘이 함께 돌면 한쪽의 청소가 다른 쪽의 판정자 테스트가 쓰는 도중의 트리를 지울 수 있다(재지 않았다). 그렇게 겹친 경우는 이 청소 전에도 한쪽의 Prettier 가 다른 쪽의 트리를 읽어 빨갰다(일지 2026-10-07-18)", 티켓의 "앞 세션의 러너가 멈춰 남은 것이 세 번이고 세 번 다 다음 세션이 손으로 치웠다(일지 2026-10-20-01, 2026-10-20-16, 2026-10-22-11). 그 전에도 `afterAll`의 `rmSync`가 `EPERM`으로 실패하거나(일지 2026-09-30-02) 커밋 훅이 끊겨(일지 2026-10-12-13) 남은 적이 있다", 프로브의 "첫 단계인 판정자 트리 청소(`clean:judge-trees`)는 검사가 아니라 재지 않고".
- 다시 돌린 명령: 아래 다시 돌린 검사 절에 적는다.

## 다시 돌린 검사

- `uv run ruff check .` 통과, `uv run ruff format --check .` 통과(965파일).
- `uv run python tools/run_checks.py`(백그라운드): check-ticket, zizmor, check-instructions, lint-imports, check-type-escapes, pyright-linux, pyright, run-hooks, web-verify(346.1초)가 통과했고 pytest가 1 failed, 4344 passed(468.23초)로 빨갰다. 빨간 것은 `tests/channel/cli/test_interrupt.py::test_닫는_도중에_한_번_더_누르면_닫기를_기다리지_않고_끝난다`이고, `_시각`이 `cancelled` 파일을 빈 채로 읽어 `ValueError`가 났다. 이 변경이 건드리지 않은 시험이고, 일지 2026-10-23-03에 같은 시험이 같은 꼴로 빨간 기록이 있다. 그 파일만 다시 돌리니 6 passed(152.24초)였다. 부하에서 빨개지는 시간 시험의 사례라 대기열 306을 닫은 결정(ADR 0036)대로 회차를 더하지 않고 여기에만 적는다. 손으로 치는 다섯은 커밋의 pre-commit 결과로 갈음한다.
- 첫 커밋 시도는 pre-commit의 pytest가 막았다(1 failed, 4344 passed, 547.20초). 이번에 빨간 것은 `tests/tools/test_probe_kit.py::test_배출은_줄이_계속_와도_제한_시간에_끝난다`이고, 자식 파이썬이 `drain(0.5)` 안에 한 줄도 내지 못해 `assert lines`가 빈 목록이었다. 앞의 러너에서 빨갰던 `test_interrupt.py` 시험은 이번에 통과했다. 이 변경이 건드리지 않은 시험이고, 일지 2026-10-22-21에 같은 시험이 같은 꼴로 빨갰고 그때 대기열에 기록이 없어 회고 후보로 두었다. 이것이 그 둘째 사례다. 그 파일만 단독으로 치자 15 passed(2.09초)였다. 회고가 셀 수 있게 여기에 적고 같은 커밋을 다시 쳤다.
- 다시 친 커밋은 pre-commit의 검사가 모두 통과했다(web-verify 512.0초, pytest 579.5초).

## 인계 (커밋 뒤)

경계: 커밋 뒤. 세션 컨텍스트가 309,146 토큰으로 문턱 200,000을 넘었다. 셀프 리뷰를 반영한 변경과 이 일지를 커밋했고, 아직 푸시하지 않았으며 PR이 없다. 이 절은 커밋하지 않은 채 워크트리에 있다. 새 세션은 PR 직전 리뷰부터 한다. 넘기기 전 이 세션의 제목은 `chore/006-eslint-judge-tree-cleanup`이다.

인계 지시문:

```
다음 작업: .scratch/harness/issues/006-eslint-judge-tree-cleanup.md(브랜치에 커밋했고 아직 푸시하지 않았다). 판정자 테스트의 beforeAll과 verify의 첫 단계가 앞 실행이 남긴 web/judge-* 트리를 junction을 따라가지 않고 지운다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 379를 티켓 .scratch/harness/issues/006-eslint-judge-tree-cleanup.md로 쓰고 한다
브랜치: chore/006-eslint-judge-tree-cleanup
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/agents/issue-tracker.md(harness 티켓의 서식·상태). 일지 docs/journal/2026-10-23-14-eslint-judge-tree-cleanup.md(인계 절은 그 워크트리에 커밋하지 않은 채 있다)
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰를 반영한 변경까지 커밋했고 pre-commit이 통과했다. 푸시하지 않았고 PR이 없다. 남은 단계는 PR 직전 리뷰(docs/constitution/operations.md 리뷰 파이프라인 2. CodeRabbit CLI가 돌지 못하면 origin/main을 합친 뒤 /security-review와 bug-perf-review를 나란히. bug-perf-review에 밀 주장은 일지 셀프 리뷰 절의 목록), 푸시, PR, 봇 회차, 워크트리에서 병합이다. 일지의 인계 절은 다음 커밋에 싣는다. 일지 docs/journal/2026-10-23-14-eslint-judge-tree-cleanup.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-22T18:49:56Z
인계 못함 커밋 뒤

`tools/open_session.ps1 -Action send`가 `fired=03:50:39.518`, `page=`, `folder=C:\project\agent`, `model=Opus 5.5`, `effort=xhigh`까지 간 뒤 "모델을 고르는 사이 입력창의 지시문이 바뀌었다. 보내지 않았다."로 멈췄다(`sent=` 없음). 같은 때(18:51Z 무렵) 003 브랜치의 인계 세션이 연 새 세션 `chore/003-probe-conclusion-evidence-kind`가 목록에 새로 나타나, 두 딥링크가 겹친 것으로 본다(어림). 같은 파일로 다시 돌리면 세션이 둘 생길 수 있어 다시 열지 않았다. 제목을 `chore/006-eslint-judge-tree-cleanup`로 되돌리고 이 세션에서 PR 직전 리뷰부터 잇는다. 이 세션은 자동 압축이 받는다.

## PR 직전 리뷰

범위는 `975bf04c..HEAD`(커밋 `ec1c54de` 하나)다. origin/main이 `975bf04c` 그대로라 합칠 것이 없었다. CodeRabbit CLI가 `Seat: not assigned`로 돌지 못해 `/security-review`와 `bug-perf-review`(셀프 리뷰 절의 밀 주장 다섯을 브리프에 실었다)를 나란히 띄웠다.

- 보안 축(`/security-review`): 발견 없음. 지우는 대상은 `readdirSync`가 돌려준 바로 아래 항목 가운데 `^judge-[A-Za-z0-9]{6}$`에 맞고 `Dirent.isDirectory()`가 참인 것뿐이라 경로 탐색이 성립하지 않고, 맨 위의 링크는 거르며 트리 안의 링크는 `rmSync`가 따라가지 않는다. 루트 인자는 CLI 값이고 외부 명령을 띄우지 않는다. 같은 체크아웃에서 verify 둘이 겹치는 경우와 판정과 지우기 사이의 바꿔치기는 경쟁 조건이라 제외 기준대로 내지 않았다. 지적이 없어 오탐 필터 서브태스크는 띄우지 않았다.
- 버그·성능 축(`bug-perf-review`, 호출 40): 유효 1, 보류 2, 오탐 5. (유효, Minor) 정규식 `^judge-[A-Za-z0-9]{6}$`가 사람이 지은 여섯 글자 이름의 폴더(`web/judge-config/`, `web/judge-design/`)까지 지운다. 임시 web/에 두 폴더를 두고 `removeLeftoverJudgeTrees`를 부르자 둘 다 지워졌다(리뷰어가 손으로 봤다). 커밋하지 않은 내용이면 되살릴 수 없다. (보류, Nit) `import.meta.main`은 Node 24.2부터라 `engines`의 `>=24 <25` 가운데 24.0~24.1에서는 명령이 아무것도 하지 않고 0으로 끝난다(리뷰어의 기억, 재지 않았다). (보류, Minor) 독스트링에서 시험을 CI의 Linux에서 본다는 문장은 CI가 아직 돈 적이 없어 근거가 없고, `EPERM`을 `maxRetries`로 견딘다는 문장은 재지 않았다. 밀 주장 일곱 가운데 Prettier 문장, 겹친 verify 문장, 티켓의 횟수, 프로브 문장은 맞음이었다(Prettier는 재지 않았다고 적었다). 손으로 지울 때의 명령 문장은 Windows에서 맞음이고 Linux는 CI 뒤다. 오탐으로 가른 다섯은 링크 따라가기(트리 안 junction, 순환 junction, 끊긴 junction, 바깥 파일과의 하드 링크, 읽기 전용 파일, 판정자 이름의 junction을 임시 web/에서 손으로 지워 봤다), 대소문자, vitest 병렬 워커(`fileParallelism:false`), pytest가 `web/judge-*`를 만들거나 읽는지, 기본 루트다.

반영:

- 고친 것: 정규식 폭은 표지로 가른다. `makeJudgeTree`가 새 트리에 표지 파일 `.judge-tree`(`MARKER`)를 심고, `removeLeftoverJudgeTrees`는 이름이 맞는 디렉터리 가운데 `lstatSync`로 본 표지가 일반 파일인 것만 지운다. 확장자가 없는 이름이라 ESLint와 Prettier가 읽지 않는다. 시험을 먼저 썼다. "이름이 판정자 트리의 모양이어도 표지가 없는 디렉터리는 안의 파일과 함께 남긴다"(`judge-config`와 메모, 표지 자리가 디렉터리인 `judge-Dir123`, 표지 자리가 바깥 파일로 가는 파일 링크인 `judge-Lnk123`)가 판정을 넣기 전에 셋을 모두 지워 빨갰고, 넣은 뒤 파일 하나 12개와 판정자 테스트를 함께 73개가 통과했다. 이름의 꼴 시험과 판정자 이름의 링크 시험에는 표지를 넣어 두 시험이 표지에 기대지 않게 했고, 이름 판정을 뺀 변이와 `isDirectory` 판정을 뺀 변이를 손으로 넣자 각각 그 시험 하나만 빨갰다. 진짜 web/에 표지가 든 `judge-Mrk001`(api-client로 가는 junction 포함)과 메모가 든 `judge-config`를 두고 `pnpm -C web run clean:judge-trees`를 치자 앞의 것만 지웠고, `web/packages/api-client/package.json`과 `git status`는 그대로였으며 메모가 남았다(손으로 봤다, 스크래치패드 `marker_setup.mjs`, 끝에 `judge-config`를 지웠다). 표지가 없는 판정자 트리(표지를 들이기 전에 남은 트리, 만든 뒤 표지를 쓰기 전에 멈춘 빈 트리)도 남기므로 독스트링의 못 보는 것에 적고 손으로 지울 길(표지를 만들고 이 명령)을 적었다. 그 입력은 위 새 시험의 `judge-Dir123`·`judge-config`와 같은 모양이다. 독스트링 두 문장은 근거의 종류대로 고쳤다. "이 PC 의 Windows 에서 통과했고, Linux 에서는 CI 의 web 잡이 같은 시험을 돈다"와 "`maxRetries` 로 다섯 번까지 다시 시도한다(Node `fs.rm` 문서, 재지 않았다)"다. 뒤의 것은 `web/node_modules/@types/node/fs.d.ts`의 `RmOptions.maxRetries` 설명(`EPERM`을 재시도하고, 재시도 횟수이며, `recursive`가 참일 때만 쓴다)을 열어 봤다. 티켓의 수용 기준 1·2에 표지를 더했다.
- 남긴 것: `import.meta.main`은 이 PR 전부터 `web/tools/check-tsconfig.ts`, `web/tools/generate-api-client.ts`, `web/tools/visual.ts`, `web/apps/admin/tools/start.ts`가 같은 꼴로 써 이 PR이 들인 위험이 아니고, 24.0~24.1에서는 "명령으로 부르기" 시험이 빨개져 드러난다. `engines`를 좁히는 것은 web 전체의 일이라 두었다.
- 다음 층(PR 봇)에 밀 주장(반영으로 새로 쓴 문장): "사람이 지은 `judge-config` 같은 폴더도 이름의 꼴에는 맞아서 표지로 가른다. 그 이름의 링크와 파일, 꼴이 다른 이름, 표지가 없거나 표지 자리가 디렉터리·링크인 것은 남긴다", "표지가 없는 판정자 트리(표지를 들이기 전에 남은 트리, 만든 뒤 표지를 쓰기 전에 멈춘 빈 트리)도 남긴다. 판정자 트리인 것을 눈으로 확인했으면 그 안에 표지 파일을 만들고 이 명령으로 지운다", "`maxRetries` 로 다섯 번까지 다시 시도한다(Node `fs.rm` 문서, 재지 않았다)".

origin/main이 `e205147d`(harness 004, #359)로 움직여 반영 전에 합쳤다. 겹친 파일 둘(`.scratch/harness/probes/README.md`, `.scratch/retro-queue.md`)은 충돌 없이 합쳐졌고, 이 브랜치의 diff는 바뀌지 않았다. 반영 커밋의 첫 시도는 pre-commit의 web-verify가 Prettier로 막았다(새 시험의 긴 줄 하나, 495.0초). 고친 시험 파일에 Prettier를 돌리지 않고 커밋했다. 나머지 검사(pytest 494.4초 포함)는 통과했다. `prettier --write`로 그 줄을 감싸고, 인용 대조가 경고한 이 절의 따옴표 인용 하나를 서술로 바꾼 뒤 다시 쳤다.

다시 친 반영 커밋 `e6ab25cf`는 pre-commit의 검사가 모두 통과했다(web-verify 317.8초, pytest 469.1초). ruff 둘은 스테이지된 `.py`가 없어 Skipped라 손으로 쳤고 통과했다(967파일). 푸시 전에 origin/main이 `690de5bf`(harness 008, #358)로 또 움직여 합쳤다. 겹친 파일은 같은 둘이고 충돌이 없었다. 그 PR이 일지 2026-10-23-11을 먼저 들여와, `sibling_overlap.py`가 이 일지를 2026-10-23-09에서 2026-10-23-14로 옮기라고 했고 `--move`로 옮겼다. 옛 번호를 가리킨 인용은 이 브랜치의 변경에 없었다(대기열 379의 닫힘 줄은 티켓 경로를 가리킨다).

## PR

옮김 커밋 `e144637f`도 pre-commit의 검사가 모두 통과했고(web-verify 322.0초, pytest 452.7초), 두 번째 합치기로 `.py`가 들어와 ruff 둘을 다시 손으로 쳐 통과했다(969파일). 푸시하고 PR #362를 열었다(`gh api`로 템플릿을 채운 본문, 머리 `e144637f`). 앱의 PR 감시는 이미 이 세션에 묶여 있었다. `@coderabbitai review` 코멘트를 남기고 `tools/wait_ci.py 362`를 백그라운드로 띄웠다. 커밋 뒤와 PR 연 뒤의 인계 계기가 왔지만 위 `인계 못함 커밋 뒤` 줄이 있어 next-session "인계할 때" 1대로 넘기지 않았다.

`wait_ci.py`가 모두 통과로 끝났다(CodeRabbit은 `Review rate limited`로 리뷰 없음, claude-review·e2e·python·ticket·verify·visual·web 통과). Linux의 `web` 잡이 `judge-trees.test.ts`를 돌아 통과했으므로, 독스트링의 Linux 문장이 실행으로 맞았다.

claude-review 1회차(머리 `e144637f`): Critical·Major 없음, Minor 2, Nit 2.

- 고친 것: (Minor) `removeLeftoverJudgeTrees`가 지우면서 지운 경로도 돌려줘 `CODING_STANDARDS.md`의 CQS("함수는 무언가를 하거나 무언가에 답하거나 둘 중 하나다")를 어긴다. 질의 `findLeftoverJudgeTrees(root): string[]`(이름이 맞고 표지가 든 디렉터리)와 명령 `removeLeftoverJudgeTrees(root): void`로 나눴다. 지울지의 판정은 명령이 안에서 그 질의를 불러 가르므로, 경로 목록을 받아 아무것이나 지우는 함수는 두지 않았다. 명령은 질의로 목록을 얻고 지운 뒤 그 목록을 찍는다. 시험을 먼저 고쳐 질의를 부르는 셋이 `findLeftoverJudgeTrees is not a function`으로 빨간 것을 봤고, 지우는 시험은 반환값 대신 남았는지·지워졌는지로 단언한다. 나눈 뒤 파일 하나 13개와 판정자 테스트를 함께 74개가 통과했다.
- 남긴 것: (Minor) verify 순서 시험이 `judge-trees.test.ts`에 있어 그 파일이 청소 로직과 verify 배선 두 까닭으로 바뀐다. 봇도 허용 범위라 했고, 티켓 수용 기준 4(청소가 린트와 Prettier보다 앞)를 청소 모듈 곁에 둔다. (Nit) `dirname(import.meta.dirname)`이 모듈과 시험에 따로 든다. web 도구와 시험이 모두 쓰는 관용 표현이다(`web/tools/check-tsconfig.ts:108` 등). (Nit) 머리 독스트링이 길다. `.claude/rules/tools.md`가 못 보는 것을 적으라고 해서 길어졌고 봇도 작성자 재량이라 했다. 셋의 이유는 PR 코멘트에 남긴다.

## 회고

후보 여섯, 승인 셋(모두 회차), 기각 셋, 넘김 없음. 심각도 순이다.

1. **승인(회차), 대기열 442, 361의 3회차.** `.claude/rules/tools.md`의 지우거나 덮어쓰는 도구 항목은 커밋 전에 판정을 깨려는 입력으로 반박하라고 하고, 그 입력의 예로 커밋하지 않은 파일을 든다. 이 PR의 첫 판은 링크, 파일, 꼴이 다른 이름으로는 반박했지만 같은 꼴의 이름을 사람이 지은 폴더(`judge-config`)와 그 안의 커밋하지 않은 메모는 넣지 않았다. 그래서 그 폴더를 지우는 길이 셀프 리뷰를 지나 PR 직전 `bug-perf-review`에서야 나왔다(위 "PR 직전 리뷰"). 그 rules는 이 세션에서 Read 도구로 `web/tools/judge-trees.ts`를 열 때 실렸다(손으로 봤다). 구현 때 실리는 지침을 어겨 리뷰가 잡은 사건이라 회차로 센다. 같은 항목의 사건인 278(1회차)과 그것을 이은 361(278의 2회차)이 모두 닫혔고 361을 이은 열린 행이 없어, 새 행을 361의 3회차로 썼다. 세 번째라 더하는 것의 문턱을 지났다. 처방은 지침보다 한 층 위인 계기 훅이다(지우는 호출을 쓰는 Write·Edit에 반박할 입력을 넣는다. 308이 닫힌 101의 4회차로 계기 훅을 든 꼴). 이 PR의 범위 밖이라 chore가 반영한다.
2. **승인(회차), 대기열 360, 3회차.** 커밋 뒤의 인계 열기가 `모델을 고르는 사이 입력창의 지시문이 바뀌었다`로 멈췄다(위 "인계 (커밋 뒤)"). 같은 때 003 브랜치의 인계 세션이 연 새 세션이 목록에 나타나 두 딥링크가 겹친 것으로 봤다(어림, 가르지 않았다). 같은 멈춤을 다른 인계 열기와 겹친 것으로 센 2회차(일지 2026-10-21-06)와 같은 꼴이라, 쏘기 전에 기계 전체의 잠금을 잡으라고 처방한 열린 행 360에 회차를 더했다. 회차 3이라 chore 계기다. 이 세션은 인계하지 못해 자동 압축을 받고 이어 갔다.
3. **승인(회차), 대기열 404, 5회차(고침).** 1의 처방이 새 훅이라 `uv run python tools/hook_report.py`를 돌렸다(창 2026-09-25~2026-10-22). 뺄 후보는 `hook_prompt_directive.py` 하나였는데, 이 세션의 첫 턴(2026-10-22T17:47:35Z)에 그 훅의 문맥이 `hookEvent`가 `UserPromptSubmit`인 첨부로 왔다(세션 기록을 Grep으로 손으로 봤다). 그 도구가 UserPromptSubmit의 알림을 세지 못하는 같은 결함이라 404에 회차를 더했고, 뺄 후보는 거짓 양성이라 넘기지 않았다. 아직 판단하지 않는 훅은 `hook_push_delete_open_pr.py`와 `hook_session_web_deps.py`다.
4. **기각, 이미 있는 검사가 막았다.** PR 직전 리뷰의 반영 커밋을, 고친 시험 파일에 Prettier를 돌리지 않고 쳐서 pre-commit의 web-verify가 495.0초 뒤에 막았다(위 "PR 직전 리뷰"). 커밋하는 그 자리에서 막은 검사가 있다.
5. **기각, 리뷰가 제 몫을 했다.** `removeLeftoverJudgeTrees`가 지우면서 지운 경로를 돌려준 CQS 위반을 셀프 리뷰와 PR 직전 리뷰가 지나쳤고 claude-review 1회차가 잡았다(위 "PR"). 리뷰가 잡도록 둔 기준(`CODING_STANDARDS.md`)이라 회차 셈에서 빼고, 검사로 옮길 꼴도 표준에 더할 새 판단 기준도 아니다.
6. **기각, 이미 있는 검사가 알렸다.** 같은 반영 커밋에서 인용 대조가 이 일지의 따옴표 인용 하나를 경고했다.

만료: `uv run python tools/queue_open_rows.py`를 이 워크트리와 `--ref origin/main`(fetch 뒤 `690de5bf`)으로 돌렸고, 만료할 행은 둘 다 없었다. 1의 새 행은 처음에 440으로 썼는데, 열린 PR #360이 그 번호를 먼저 가져가 `sibling_overlap.py --move`로 442로 옮겼다.

일지에만 남기는 것:

- 부하 아래에서 빨간 시간 시험 둘(`test_interrupt.py`, `test_probe_kit.py`, 위 "다시 돌린 검사")은 306이 받아들여 닫은 종류의 새 사례라 회차를 더하지 않는다.
- 정정. 위 셀프 리뷰 절의 남긴 것은 `.claude/rules/tools.md`가 루트 `tools/**`에만 걸린다고 적었다. 그 rules의 `paths`는 `tools/**`이지만 이 세션에서 `web/tools/judge-trees.ts`를 Read 도구로 열 때 실렸다(1과 같다). 그 남김의 첫 까닭은 틀렸다. 남긴 판단은 그대로다. 그 항목(독스트링의 못 보는 것을 시험으로 고정한다)은 훅과 검사가 대상이고 이 모듈은 `verify`의 청소 단계이며, 나머지 까닭도 그대로다.

## 다음

- harness 006을 이 PR(#362)로 닫는다. 같은 주제는 남지 않는다. 다음 작업은 결정표가 정한다.
- 이 회고로 대기열 360(3회차)과 442(361의 3회차)가 chore 계기가 됐다.
- claude-review 1회차에서 남긴 셋은 뒤로 넘긴 일이 아니다(이유는 PR 코멘트).
