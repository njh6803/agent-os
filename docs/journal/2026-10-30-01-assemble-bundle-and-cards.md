# 2026-10-30 (01) design-card-build 01 짓기 명령의 묶음·카드·글꼴

next-session 지시문으로 연 새 세션이다(나란히 여는 2 중 1, 다른 하나는 03 올리기 계획). 2026-10-29에 시작해 자정을 넘겼다. 주 체크아웃이 미갱신이라 `tidy-checkouts`를 먼저 돌고, 주 체크아웃에서 브랜치를 따지 않고 `EnterWorktree`(이름 `01-assemble-bundle-and-cards`)로 들어가 브랜치를 `feature/01-assemble-bundle-and-cards`로 바꿨다(기준 `f6df25c8`). 대화가 길어 한 번 압축됐다.

> 사용자: "다음 작업: .scratch/design-card-build/issues/01-assemble-bundle-and-cards.md. 올리기 도구의 assemble 명령이 컴포넌트 묶음·카드·글꼴·옛 이름을 짓고, pnpm -C web verify가 chromium으로 카드가 그려지는지 보게 한다 / 다음 단계: 구현 / 어디서: 새 세션. 나란히 여는 2 중 1. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 01-assemble-bundle-and-cards)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / … / 이어받을 상태: 임시 디자인 시스템 아티팩트 64VW1b5F8tRcCeTZBwZA29는 사용자가 남겨 두기로 했다. 지우지 않고 다시 묻지 않는다. 이 PC에서 pre-commit의 pytest는 다른 시간 시험(tests/tools/test_probe_kit.py, tests/tools/test_rerun_runner.py, tests/channel/cli/test_interrupt.py, tests/tools/test_hook_edit_during_commit.py)이 부하에서 한 번씩 막을 수 있다. 단독 실행이 통과하면 SKIP 없이 같은 커밋을 한 번 더 시도하고, SKIP=pytest는 사람에게 묻는다 / 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다 / 이번 요청 범위: PR과 병합까지"

## 체크아웃 정리

루트는 main이고 깨끗해 `3ee0be4f`에서 `f6df25c8`로 당겼다. 지운 것은 워크트리 `04-admin-frame-common-states`와 그 브랜치, 로컬 브랜치 `worktree-05-admin-plugin-screens`다. 남긴 것은 프로세스(pwsh)가 쥔 셋(`024`, `03-admin-adopt`, `design-card-build-spec`)과, 병합된 PR이 없거나 도는 세션이 있거나 바뀐 파일·앱의 표지가 있는 워크트리들이다. 휴지통의 `node_modules` 열여덟은 esbuild 등이 쥐어 남았다. 사람에게 넘길 것은 없었다.

## 짓기 명령

`web/tools/sync-design-system/assemble.ts`를 새로 두고 명령 표(`main.ts`)에 `assemble` 한 줄을 더했다. 짓는 길은 프로브 `vite_cli_tool.mts`가 잰 모양 그대로다. 디자인 시스템 패키지의 `package.json`에서 `bin`을 읽어 vite CLI와 Tailwind CLI를 찾고, `process.execPath`로 셸 없이 패키지 자리에서 띄운다. vite 설정은 import 없는 `.mjs` 글로 지어 명령의 임시 폴더에 쓰고, 플러그인 셋(JSX 대체, `storybook/test` 대체, 컴포넌트 모듈을 전역 `AgentOsUi`로 돌리는 해석기)은 그 글 안의 객체다. 임시 폴더에 짓고 규칙(금지 문자열, 크기 한도, 카드 README)으로 판정한 뒤 지날 때만 `--out`으로 옮긴다. 판정은 시험이 복사본을 망가뜨려 부를 수 있게 `judgeAssembled(폴더)`로 내보냈다.

시험은 `assemble.test.ts` 하나다. beforeAll에서 명령을 임시 폴더로 한 번 돌리고, 같은 산출을 파일 검사 열, 규칙 판정 일곱, chromium 그리기 열(카드 아홉과 토큰 덮기)이 읽는다. 그리기 문서의 React 전역은 시험이 같은 vite CLI 길로 짓는다(`viteBuild`를 명령과 같이 쓴다). 페이지 토큰 CSS는 받은 사본을 시험 자료 `fixtures/page-tokens.css`로 두고, Prettier가 선택자를 줄마다 갈라 `web/.prettierignore`에 까닭과 함께 넣었다.

## 글꼴 대조

티켓의 "시작 전"대로 그리기 판정 전에 먼저 봤다. 처음에는 커밋하지 않은 스크래치 스크립트로, 셀프 리뷰 전에 그것을 프로브 `probes/font_route.mjs`로 옮겨 다시 쟀다. 두 길(`file://`, 요청 가로채기 `route`) 모두 지은 그대로의 `../../fonts/`는 Noto Sans KR 실림 5·글꼴 오류 0, `../fonts/`로 바꾼 것은 실림 0·오류 5였다(프로브가 찍은 요약, 회차 4 측정 4). 시험은 산출을 고치지 않는 `route` 길을 골랐다(프로브 README "2026-10-29 글꼴 대조").

## 변이

`probes/assemble_mutations.toml`에 변이를 지었다. 첫 전체 실행은 24 가운데 표지 없음 4였고, 변이를 손으로 넣어 실패 출력을 본 뒤 그리기 시험과 글꼴 주소 시험을 칸을 한 객체로 맞대는 꼴로 바꾸고 표지를 diff의 `+` 줄로 골랐다. 다른 단언의 실패에도 실리는 표지 셋도 고치고 변이 하나를 더해 25가 됐다. 바꾼 것과 새것 열을 다시 돌려 모두 기대대로였다(`tools/mutate.py`가 찍은 판정). 고친 까닭과 재지 않은 것은 프로브 README "2026-10-29 짓기 명령의 변이"에 적었다.

## 결과에 적은 측정

- 바꾼 시험 파일 하나(`pnpm -C web exec vitest run --project node tools/sync-design-system/assemble.test.ts`)는 27 통과, Duration 47.26초였다. 압축 전에는 같은 명령이 18.33초였다. 이 PC에 다른 세션의 부하가 있었다(어림).
- 같은 판에서 `--out`을 달리해 두 번 지은 산출이 `diff -r`로 같았고 `--paths` 목록도 `cmp`로 같았다. 파일 794, 글꼴 770개 이름이 커밋 `35028cba`의 `.design-sync/upload-output.json`과 `diff` 0, 묶음 CSS의 `data:font/woff2` 2(커밋하지 않은 스크래치 스크립트 `fonts_check.sh`로 손으로 봤다). 그 짓기의 `time`은 16.5초(real)였다.
- 시험이 `vitest run` 전체에 더한 시간은 아직 재지 못했다. 시험 파일을 넣은 `pnpm exec vitest run`(440.04초)과 `--exclude tools/sync-design-system/assemble.test.ts`를 준 실행(482.06초)이 둘 다 시험 84 파일 1467개를 돌아, 빼기가 먹지 않았고 부하로 걸린 시간이 42초 엇갈렸다. 그래서 node 프로젝트를 JSON 리포터로 돌려(`pnpm -C web exec vitest run --project node --reporter=json --outputFile=<파일>`) 이 파일의 `endTime - startTime`을 읽었다. 17.06초였고, 파일 39·시험 933 모두 통과, 프로젝트의 첫 시작부터 마지막 끝까지 172.39초였다(커밋하지 않은 스크래치 스크립트 `file_time.py`로 리포트를 읽어 손으로 봤다). 티켓 결과에 옮겼다.

## 인계 전 상태

이 세션의 제목은 `feature/01-assemble-bundle-and-cards`다. 컨텍스트가 인계 문턱을 넘은 채 셀프 리뷰 직전에 와서 `셀프 리뷰 직전`으로 넘긴다. 아무것도 커밋하지 않았다. 워크트리에 있는 변경은 티켓(`in-progress`, 체크박스는 마무리 마지막 줄 말고 모두 채웠다, 결과 절), `web/tools/sync-design-system/`의 `assemble.ts`·`assemble.test.ts`·`main.ts`·`fixtures/page-tokens.css`, `web/.prettierignore`, 프로브 `font_route.mjs`·`assemble_mutations.toml`과 프로브 README의 두 줄·세 절, 이 일지다.

결정과 이 세션이 고친 것:

- 그리기 시험의 기준 주소는 요청 가로채기(`route`) 길이다(위 "글꼴 대조").
- 그리기 시험과 글꼴 주소 시험을 칸마다의 단언에서 한 객체 맞대기로 바꿨다. 변이의 표지가 그 단언만의 문구가 되게 하려는 것이다(위 "변이").
- 그리기 변이의 좁히기는 `-t "(?<!Icon)Button 카드는"`이다. vitest의 `-t`가 묶음 이름까지 든 전체 이름과 맞춰, `Button 카드는`은 IconButton도 고르고 `^Button`과 `그리기 Button`은 아무것도 고르지 않았다(손으로 봤다).
- 일지를 `2026-10-29-22`로 만들었다가 날짜가 바뀌어 훅이 알린 대로 `2026-10-30-01`로 옮겼다.

남은 일(새 세션):

1. 티켓 결과의 "eslint와 strict" 줄은 `pnpm -C web verify`를 다 돈 뒤 고친다. 지금 문장(verify의 typecheck가 지났다)은 이 세션이 verify 전체로 보지 않은 것이다. 이 세션이 친 것은 두 파일의 eslint(0)와, 압축 전의 tsc(0)다.
2. `/code-review`(base `f6df25c8`, 미추적 포함, 티켓 01). 이 세션은 Skill만 불렀고 단계는 밟지 않았다.
3. 검증 명령 전체(`uv run ruff check . && uv run ruff format --check .`, `uv run python tools/run_checks.py`).
4. 커밋한 뒤 변이 표 전체를 다시 돌린다(시험을 고쳐 앞의 전체 실행은 옛 시험을 잰 것이다). `font_route.mjs`도 커밋한 판에서 다시 돌려 프로브 README의 `HEAD`와 커밋하지 않은 변경 수를 고친다. 그 뒤 티켓을 `done`으로 바꾸고 PR, CI에서 새 node 시험이 chromium을 띄우는지 보고 마무리 마지막 체크박스를 채운 뒤 병합한다.

## 인계

`셀프 리뷰 직전`의 인계 계기(`hook_handoff`, 세션 컨텍스트 328,317 토큰)를 받아 `next-session` `handoff.md`대로 넘긴다. 인계하지 않는 다섯에 들지 않았다(곁 세션이 아니다: `get_session`의 `self`에 `parentSessionId`가 없다). 지시문:

```
다음 작업: .scratch/design-card-build/issues/01-assemble-bundle-and-cards.md. 올리기 도구의 assemble 명령이 컴포넌트 묶음·카드·글꼴·옛 이름을 짓고, pnpm -C web verify가 chromium으로 카드가 그려지는지 보게 한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/design-card-build/issues/01-assemble-bundle-and-cards.md
브랜치: feature/01-assemble-bundle-and-cards
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: 일지 docs/journal/2026-10-30-01-assemble-bundle-and-cards.md의 "인계 전 상태"
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. 일지 docs/journal/2026-10-30-01-assemble-bundle-and-cards.md. 임시 디자인 시스템 아티팩트 64VW1b5F8tRcCeTZBwZA29는 사용자가 남겨 두기로 했다. 지우지 않고 다시 묻지 않는다. 이 PC에서 pre-commit의 pytest는 다른 시간 시험(tests/tools/test_probe_kit.py, tests/tools/test_rerun_runner.py, tests/channel/cli/test_interrupt.py, tests/tools/test_hook_edit_during_commit.py)이 부하에서 한 번씩 막을 수 있다. 단독 실행이 통과하면 SKIP 없이 같은 커밋을 한 번 더 시도하고, SKIP=pytest는 사람에게 묻는다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목은 `feature/01-assemble-bundle-and-cards (인계함)`으로 바꿨고(앱이 바꿨다고 알렸다), 띄운 백그라운드 작업은 모두 끝나 멈출 것이 없었으며, `git worktree unlock C:/project/agent/.claude/worktrees/01-assemble-bundle-and-cards`가 0으로 끝났다.

open-session을 부른다 2026-10-29T15:22:55Z

함께 볼 것: 나란히 도는 03 워크트리(`03-upload-plan-first-canonical`)도 `.scratch/design-card-build/probes/README.md`를 고쳐, 나중에 병합하는 쪽에서 글자 충돌 후보다(`tools/sibling_overlap.py`가 알렸다). origin/main은 `c04e4fe6`(admin-style 07)로 움직였고 이 브랜치가 고친 파일과 겹치지 않는다(`git diff --name-only HEAD...origin/main`).

## 이어받은 세션

위 지시문으로 연 새 세션이다. 제목을 `feature/01-assemble-bundle-and-cards`로 바꾸고, `git worktree list`에서 이 브랜치의 워크트리를 찾아 `EnterWorktree(path)`로 들어왔다. 워크트리의 변경은 위 "인계 전 상태"와 같았다.

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/design-card-build/issues/01-assemble-bundle-and-cards.md / 다음 작업: … / 이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. … / 이번 요청 범위: PR과 병합까지"

## 셀프 리뷰

범위: base `f6df25c8`, diff에 잡힌 수정 파일 4, 커밋 0, 미추적 6(`assemble.ts`, `assemble.test.ts`, `fixtures/page-tokens.css`, `font_route.mjs`, `assemble_mutations.toml`, 이 일지). 표준 축은 sonnet·high, 명세 축은 본 세션 모델로 나란히 돌렸다.

**표준 축.** Critical·Major 0. 두 축 모두 지은 산출의 수(794, 아홉, 770, 열하나, 25, 27)와 "같은 바이트", "비지 않으면 아무것도 쓰지 않는다"를 다시 돌려 맞다고 봤다.

- Minor: `LibBuild.scene: boolean`이 플러그인 묶음을 가른다(`CODING_STANDARDS.md` 14행 "갈래를 고르는 데이터클래스·인터페이스의 불리언 칸은 열거(TypeScript는 문자열 유니온)로 둔다"). → 고친다.
- Minor: `problemsOf`의 `present`가 문제를 쌓으면서 `boolean`을 돌려준다(같은 파일 18행 CQS). → 고친다.
- Minor: 명령이 판정에서 멈추는 길, `limit`과 `input`을 가르는 분기, `--paths`가 `--out` 안일 때의 `usage`에 시험이 없다. → 고친다(아래 명세 축 첫 항목과 같이).
- Minor: `font_route.mjs`의 표지(`faces > 0 && text > 0`)는 양성과 음성 모두에서 참이고, 티켓의 멈춤 조건(갈리는지)을 프로브가 판정하지 않고 찍기만 한다. → 고친다. 표지에 문서가 카드 자리에서 열렸는지를 더하고, 길마다 갈렸는지를 요약에 찍는다.
- Minor: `command.ts` 독스트링의 `input`·`limit` 설명이 짓기 명령의 쓰임(빌드 실패, 바이트 한도)을 담지 않는다. → 고친다.
- Nit: 시험의 `IMPORT_STATEMENT`(`[;\n]`)가 명령(`[;\n}]`)보다 느슨하다. → 고친다(시험을 명령만큼 엄하게 두고, 따로 짓는다고 주석을 단다). 시험의 대소문자 무시는 명령보다 엄해 둔다.
- Nit: `place`의 안쪽 `catch {}`가 모든 이름 바꾸기 오류에서 복사로 넘어간다. → 주석만 고친다. 복사도 실패하면 `output` 오류로 끝나 묻히지 않는다.
- Nit: 티켓 결과의 typecheck 문장, 일지와 티켓의 짓기 시간 엇갈림, 부하에서 57초 걸린 짓기. → 티켓 문장은 검증 명령 뒤에 고친다. 나머지는 기록이라 두고, 시간은 티켓이 이미 한 번씩 잰 값으로 적었다.

**명세 축.** 티켓의 요구 문장은 base 판과 같다.

- Minor: "규칙을 어기면 … `--out`에는 아무것도 없다"를 시험이 명령으로 보지 않는다. `assemble()`의 `throw`를 지워도 빨개지는 것이 없다. → 고친다. 판정을 `CommandError`를 던지는 함수 하나로 두어 명령과 시험이 같은 함수를 부르고, 시험은 오류의 종류와 문구를 맞댄다.
- Minor: 변이 25 가운데 15는 고치기 전의 시험으로만 돌았고, `_ds_bundle.js`가 정식 자리와 같은지에는 변이가 없다. → 커밋 뒤 전체를 다시 돌리고(인계 전 상태의 남은 일 4), 그 변이를 하나 더한다.
- Minor: showcase 스토리 열하나가 모두 `render`를 가져, args 합치기와 meta의 `component`로 그리는 길을 어떤 시험도 지나지 않는다. → 남긴다. 그 길을 지나는 장면이 지금 소스에 없고, 시험이 지나게 하려면 패키지 밖의 스토리를 짓는 이음매가 든다(이 티켓의 체크박스에 없는 표면). 명령 독스트링의 못 보는 것과 티켓 결과에 적는다.
- Nit: `--paths`가 산출 폴더 안이면 `usage`로 끝내는 것은 요구에 없다. → 둔다. 목록 파일이 산출에 섞이지 않게 하는 해가 없는 방어이고, 시험을 더한다.
- Minor: 명세의 `data-scene="<스토리 이름>"`을 코드는 내보낸 이름으로 쓴다. → 남긴다. 명세가 근거로 든 프로브가 내보낸 이름을 썼고(`card_build.mjs` 237행), `web/`을 glob 없이 `data-scene`으로 grep하면 명령과 그 시험뿐이고, 시험은 `[data-scene]`의 수만 세어 값을 읽지 않는다(처음 친 glob 든 grep은 명령 파일도 찾지 못해 0이었다). 명세는 사용자만 부르는 스킬이 쓰므로 고치지 않고, 이 해석을 티켓 결과에 적는다.
- Minor: 목록 파일을 `place()` 뒤에 써서, `--paths`에 폴더를 주면 `"ok": false`인데 `--out`에 794개가 남고 다시 짓지 못한다(리뷰어가 실제로 돌려 봤다). → 고친다. 목록 파일을 먼저 쓰고 옮긴다.
- Minor: 티켓 결과의 typecheck 문장(verify의 typecheck가 지났다는 옛 문장)은 이 세션이 친 것이 아니다. → 검증 명령 뒤에 실제로 친 명령으로 고친다.
- Nit: 독스트링 9행의 React 18.3.1 문장은 명세가 어림이라 적은 것이다(`spec.md` 120행). → 어림으로 고친다.
- Nit: 독스트링 43행의 옛 문장(없던 산출 폴더는 한 번에 이름을 바꿔 옮긴다는 것)은 다른 드라이브에서 맞지 않는다. → 고친다.

**고친 것.** `LibBuild.kind: "bundle" | "scene"`. 판정을 `assertAssembled`(어기면 `CommandError`를 던진다) 하나로 두어 명령과 시험이 같이 부르고, `problemsOf`는 있어야 하는 파일과 한도의 표 하나에서 없음·크기를 내도록 고쳐 `present`를 없앴다. 시험은 오류의 종류와 문구를 맞대고, 섞인 경우(크기와 README 없음이면 `input`)와 목록 파일이 산출 폴더 안인 경우(`usage`)를 더해 29개다. 목록 파일을 산출을 옮기기 전에 쓴다. 독스트링(React 18 어림, 못 보는 것 둘), `place`의 주석, `command.ts`의 `input`·`limit`, 시험의 `IMPORT_STATEMENT`를 고쳤다. `font_route.mjs`는 표지에 문서의 자리를 더하고 길마다의 갈림(`splits`)을 찍는다. 변이 표는 겨누던 줄이 바뀐 셋과 표지가 바뀐 다섯을 고치고 셋(옛 이름 묶음 JS, 섞인 경우, 목록 파일 자리)을 더해 28이다(`tools/mutate.py --check`가 `원문 확인: 변이 28 모두 원문이 한 번씩 있다`를 찍었다). 고친 판에서 `assemble.test.ts` 하나가 29 통과(Duration 97.40초), `--paths`에 폴더를 준 실행이 `--out`을 만들지 않았다(손으로 봤다, 티켓 결과).

**PR 직전 리뷰에 밀 주장**(반영으로 새로 쓴 문장, 원문):

- `assemble.ts` 독스트링: "목록 파일이 산출 폴더 안이면 `usage` 오류다." / "목록 파일은 산출을 옮기기 전에 써서, 쓰지 못하면 산출 폴더에 아무것도 없다."
- 같은 독스트링의 못 보는 것: "장면이 meta 와 스토리의 `args` 를 합치는 길과 `render` 없이 meta 의 `component` 로 그리는 길은, 지금 showcase 스토리가 모두 `render` 를 가져 시험이 지나지 않는다." / "산출을 옮기다 끊기면 산출 폴더에 옮긴 데까지 남고, 목록 파일은 이미 쓰여 있다. 없던 산출 폴더는 이름을 바꿔 한 번에 옮기지만, 이름을 바꾸지 못하면(다른 드라이브 등) 비어 있던 폴더처럼 복사로 옮긴다."
- 같은 독스트링: "패키지의 React 19 가 JSX 로 내는 요소 표식을 페이지의 React 18.3.1 이 그리지 않는다고 보기 때문이다(두 판의 표식이 다르다는 지식에서 낸 명세의 어림이다. React 18.3.1 에 그 표식을 넣어 그려 보지는 않았다)."
- `assertAssembled` 독스트링: "오류의 종류는 크기만 넘었으면 `limit`, 그 밖은 `input` 이고, 문구는 문제마다의 문구를 `; ` 로 이은 것이다. 명령과 시험이 이 함수 하나로 판정한다."
- `place`의 주석: "이름을 바꾸지 못하면(다른 드라이브 등) 복사로 옮긴다. 복사도 실패하면 아래에서 `output` 오류다."
- `command.ts`: "짓기 명령에서는 빌드가 실패했거나 지은 산출이 형식의 규칙(금지 문자열, 카드 README)을 어긴 것도 든다." / "형식의 한도(테마 8, 색 600, 다른 계열 60, 짓기 명령의 묶음·카드·카드 README 의 바이트)"
- 시험의 주석: "파일 검사의 금지 문자열은 명령의 판정과 따로 짓되 그보다 느슨하지 않게 둔다(대소문자는 모두 가리지 않는다)."
- `font_route.mjs` 머리 주석의 표지·결과 문단, 변이 표 머리의 "명령이 판정을 부르는 줄(`assertAssembled(stage)`)을 지우는 변이도 두지 않았다" 문장, 티켓 결과의 새 네 줄(eslint와 strict, 장면의 이름, 시험이 지나지 않는 길, 실패하면 `--out`이 빈다).

**남긴 것.** args·`component` 길의 시험(이음매가 든다), `data-scene`의 이름(근거 프로브와 같다), `--paths` 자리 방어(해가 없다), 일지의 엇갈림(기록). 까닭은 위 항목마다 적었다.

**다시 돌린 명령.** `uv run ruff check .`(All checks passed)와 `uv run ruff format --check .`(1173 files already formatted), `uv run python tools/run_checks.py`(열 검사 모두 `Passed`, `web-verify` 644.5초, `pytest` 499.2초, 종료 0)였다.

## 커밋

첫 커밋 시도는 commit-msg 훅의 판정을 앞당기는 훅이 제목 81자를 막아 제목을 줄였다. 다음 시도는 pre-commit의 `pytest`가 `tests/tools/test_rerun_runner.py::test_같은_갈래가_두_번_든_파일럿의_두_회차가_함께_돌아도_번호가_다르다` 하나로 실패해 막혔다(1 failed, 6005 passed, 714.16초). 지시문이 부하에서 막을 수 있다고 적은 시간 시험이다. 그 시험만 단독으로 돌리자 통과해(216.44초) SKIP 없이 같은 커밋을 다시 친다. 같은 실행의 인용 대조 경고 넷은 이 일지의 인용이었다. 원문을 줄여 옮긴 하나는 원문 그대로 고쳤고, 반영으로 사라진 옛 문장 둘과 도구 출력 하나는 따옴표를 떼거나 코드 스팬으로 바꿨다.
