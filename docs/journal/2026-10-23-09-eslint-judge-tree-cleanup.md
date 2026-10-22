# 2026-10-23 (09) 판정자 테스트가 앞 실행이 남긴 임시 트리를 지운다

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
읽을 것: docs/agents/issue-tracker.md(harness 티켓의 서식·상태). 일지 docs/journal/2026-10-23-09-eslint-judge-tree-cleanup.md(이 워크트리에만 있다)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 고정점 origin/main, 티켓 006)부터 한다. 그 뒤 run_checks와 ruff 두 줄, 커밋, PR, 병합. 일지 docs/journal/2026-10-23-09-eslint-judge-tree-cleanup.md
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
