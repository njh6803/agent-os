# 2026-11-13 (21:06) 디자인 시스템 묶음 파일이 U+FFFD를 이스케이프로 쓰게 해 올리기가 거부되지 않게 한다

세션 제목 `chore/ds-bundle-escape-replacement-char`. 브랜치 `chore/ds-bundle-escape-replacement-char`(앱이 만든 `claude/optimistic-cohen-01f2be`를 바꿨다), 워크트리 `.claude/worktrees/elegant-dijkstra-aaddb9`, 기준 브랜치 `dev`. 모델 `claude-opus-5-5`. 티켓 `.scratch/harness/issues/ds-bundle-escape-replacement-char.md`, 대기열 `ds-upload-replacement-char-rejected`. 다른 세션(`local_bcac6d8c-7fb8-459e-9df0-4092dca2dbe6`)이 연 곁 세션이고, 사용자가 이 일과 answer-markdown 티켓 02를 나란히 돌리기로 했다(02는 `web/packages/ui`를, 이 일은 `web/tools/sync-design-system/`을 고쳐 파일이 겹치지 않는다).

## 받은 일

사람이 친 프롬프트는 없고, 이 세션을 연 세션이 보낸 일이 첫 메시지다. 그 원문이다. 다만 원문의 할 일 2에는 이스케이프 글 대신 U+FFFD 글자가 그대로 들어 있어서, 그 자리만 뜻대로 6글자 이스케이프 글로 적었다(아래 "셀프 리뷰").

> 세션: 대기열 항목 `.scratch/retro-queue/ds-upload-replacement-char-rejected.md`(자체 승인 2026-11-13, ADR 불필요)를 반영한다.
>
> 시작하기 전에: `CLAUDE.md` 작업 규약과 `docs/agents/issue-tracker.md`대로 harness 티켓 `.scratch/harness/issues/<slug>.md`를 `in-progress`로 쓰고, 브랜치를 `chore/<slug>`로 맞추며, 세션 제목을 그 브랜치로 바꾼다. 대기열 항목의 모양과 닫는 규칙은 `.scratch/retro-queue/README.md`를 따른다.
>
> 할 일:
> 1. 먼저 재현한다. 원인은 압축된 산출을 읽고 어림한 것이고 원본 패키지는 대 보지 않았다. 짓기 산출(`_ds_bundle.js`, `components/bundle.js`)에 U+FFFD가 이스케이프 없이 드는 자리와 그 글자가 온 패키지를 확인한다.
> 2. `web/tools/sync-design-system/assemble.ts`의 `libConfig`가 그 글자를 `\uFFFD` 이스케이프로 쓰게 고친다. 원인이 다르면 실제 원인에 맞게 고친다.
> 3. `web/tools/sync-design-system/assemble.test.ts`에 산출에 U+FFFD가 그대로 들지 않는다는 시험을 먼저 실패하게 쓰고 통과시킨다.
> 4. `/sync-design-system 올리기`를 다시 해서 웹의 디자인 시스템에 마크다운 부품이 올라가는지 본다.
>
> 끝난 모습: 시험과 `CLAUDE.md`의 검증 명령이 초록이고, 올리기가 거부 없이 끝나며, 대기열 항목이 규칙대로 닫힌다. `/code-review` 셀프 리뷰를 반영한 뒤 PR을 열고 규약대로 병합까지 한 뒤 `next-session`으로 지시문을 낸다.

## 한 것

- **재현.** 새 워크트리라 `pnpm -C web install --frozen-lockfile`부터 쳤다(없으면 `main.ts`가 `@agent-os/ui`를 찾지 못해 `ERR_MODULE_NOT_FOUND`로 끝났다). 고치기 전의 `assemble`을 스크래치패드에 돌려 `grep -P '\x{FFFD}'`로 훑으니 산출 804개 가운데 `components/bundle.js`와 `_ds_bundle.js` 둘에만, 두 자리였다. 둘 다 템플릿 리터럴 안이었다(같은 `grep -oP`로 앞뒤 글을 찍어 손으로 봤다). 앞뒤 글의 모양(숫자 문자 참조 범위 판정, 서로게이트 짝 판정)으로 짚은 두 패키지의 원본을 `grep -n 'FFFD'`로 대 보니 `micromark-util-decode-numeric-character-reference@2.0.2`(`index.js` 29행)와 `micromark-util-sanitize-uri@2.0.1`(`index.js` 89행)이고, 둘 다 `"\uFFFD"` 이스케이프로 썼다. 판은 `web/node_modules/.pnpm`의 폴더 이름과 vite의 `package.json`에서 읽었다(vite 8.3.1, rolldown 1.2.11). 원본이 이스케이프이고 산출이 글자 그대로이므로 압축이 바꿔 쓴 것으로 본다. 대기열 항목의 어림이 맞았다.
- **시험 먼저.** `assemble.test.ts`의 "짓기 명령의 산출"에 글꼴 밖의 산출 파일에 U+FFFD가 그대로 들지 않고, 묶음 JS에 `\uFFFD` 이스케이프가 있다는 시험을 더했다. 고치기 전에는 `expected [ '_ds_bundle.js', …(1) ] to deeply equal []`로 실패했다.
- **고침.** rolldown 1.2.11의 타입 선언(`dist/shared/binding-BTa6BPQe.d.mts`)에서 `CodegenOptions.asciiOnly`(문자열·태그 없는 템플릿·정규식 리터럴과 식별자의 ASCII 밖 글자를 이스케이프한다)를 읽었다. vite 8.3.1의 `dist/node/chunks/node.js`를 읽으니 출력 설정을 지은 뒤 `...output`으로 사용자의 `rolldownOptions.output`을 펼쳐, `output.minify`를 주면 vite의 값을 덮는다(코드를 읽은 것이다). 그래서 `libConfig`가 `output.minify`를 `{ compress: true, mangle: true, codegen: { asciiOnly: true } }`(상수 `MINIFY`)로 준다. 고친 뒤 `pnpm -C web exec vitest run --project node tools/sync-design-system/assemble.test.ts`에서 시험 45개(chromium으로 묶음과 카드를 그리는 시험 포함)가 통과했다. 다시 지은 산출을 손으로 보니, 두 자리는 `` `\uFFFD` ``이고(`grep -i 'fffd'`), `components/`의 README 밖 파일과 `_ds_bundle.js`에 ASCII 밖 글자가 없으며(`grep -P '[^\x00-\x7F]'`), 묶음 JS는 190,035바이트에서 190,209바이트가 됐다(`wc -c`).

## 판단한 것

- **산출 글을 사후에 바꾸지 않고 코드 생성 설정으로 고쳤다.** 묶음 글에서 U+FFFD만 `\uFFFD`로 바꾸는 길도 있었지만, 태그된 템플릿의 raw 글이나 주석에 든 글자까지 바꿔 뜻이 달라질 수 있다. `asciiOnly`는 그런 자리를 이스케이프하지 않는다고 위 타입 선언이 적는다. 한국어 글자도 함께 이스케이프되지만 묶음과 카드는 사람이 읽는 글이 아니다. 묶음 JS는 174바이트만 늘었고, 스토리의 한국어 글이 든 카드 열 개는 12~28% 커졌지만 한도 안이다(고치기 전과 뒤의 산출을 `wc -c`로 손으로 쟀다).
- **판정(`assertAssembled`)에 U+FFFD를 더하지 않았다.** 시험이 지금 소스로 산출 전체를 훑고, 그 시험은 `pnpm -C web verify`(CI)에서 돈다. 받은 일은 시험을 더하는 것까지라 판정은 넓히지 않았다.
- **올리기와 대기열 닫기를 이 PR 밖으로 뺐다.** 올리기 절차(`.claude/skills/sync-design-system/upload.md` 1)가 입력을 바꾼 PR이 병합된 뒤 `origin/dev`의 분리 HEAD에서 올리라고 한다. 올리면 지난 산출 목록에 마크다운 카드의 두 경로(`project/components/Markdown/README.md`, `preview.html`)가 더해져 목록이 바뀌는데, 그 목록은 같은 절차 6의 6대로 티켓을 가리키는 브랜치에만 실린다. 이 PR의 티켓은 그때 이미 병합되어 다시 열 수 없으므로(`docs/agents/issue-tracker.md`), 병합 뒤 `origin/dev`에서 새 harness 티켓의 `chore/` 브랜치를 따 티켓을 먼저 커밋하고, 그 브랜치를 돌아갈 브랜치로 삼아 올린 뒤 목록을 거기 싣는다(6의 6의 첫 갈래). 그 PR이 대기열 항목을 닫는다. 이 PR에서는 대기열 항목의 본문에 반영한 몫을 적고 상태를 `열림`으로 둔다(`.scratch/retro-queue/README.md`의 부분 반영).
- **인계하지 않았다.** 셀프 리뷰 직전에 인계 계기가 왔지만, 이 세션은 다른 세션이 연 곁 세션(`get_session`의 `parentSessionId`가 있고 `detached`가 거짓)이라 `next-session` `handoff.md` 1의 인계하지 않는 때다.

## 셀프 리뷰

`/code-review`를 base `0e06c9cf7`로 돌렸다. 범위는 수정 파일 셋(`assemble.ts`, `assemble.test.ts`, 대기열 항목), 미추적 하나(티켓), 커밋 0개다. 일지는 리뷰를 띄운 뒤에 만들어 범위 밖이다. 명세는 티켓, 대기열 항목, 이 세션을 연 세션의 요청(올리기와 항목 닫기를 병합 뒤로 미룬 것은 리뷰어 참고로 넘겼다)이다. 표준 축(sonnet·high)은 Minor 1, Nit 2를, 명세 축은 빠진 것·범위 넘침 0과 Minor 2, Nit 2를 냈다. 두 축 모두 산출을 다시 지어 재현 수치(804개, 두 자리, 판과 행 번호, 190,035→190,209바이트)를 대 보고 맞다고 했다. 명세 축은 고친 산출의 이스케이프를 글자로 되돌리면 묶음과 카드가 고치기 전과 바이트까지 같다고 해, "압축과 이름 줄이기는 그대로"를 바이트로 받쳤다.

- 고친 것(표준 Minor): 도구 인자에 적은 6글자 이스케이프 글이 도구에서 풀려, 시험의 `includes(…)`와 주석, `MINIFY` 독스트링, 티켓, 대기열 항목, 이 일지에 U+FFFD 글자가 그대로 들었다. 시험은 그래도 맞게 돌았지만, 이 사건의 글자를 저장소에 들인 셈이다. 대기열 항목의 어디로 줄은 앞 세션이 쓴 원문부터 같은 글자였다. 처음에는 `sed 's/…/\\u…/'`로 바꾸려 했는데, GNU sed가 치환 글의 `\u`를 "다음 글자를 대문자로"로 읽어 `FFFD`만 남겼다. 그래서 node로 역슬래시(`String.fromCharCode(92)`)를 넣어 다시 고쳤다. 고친 뒤 다섯 파일의 U+FFFD 바이트는 `grep -cP '\x{FFFD}'`로 0개다.
- 고친 것(표준 Nit, 명세 Nit): 모듈 독스트링의 보편 주장("묶음과 장면은 ASCII 밖의 글자를 이스케이프로 쓴다")을 "코드 생성은 … 이스케이프하지 않는 자리는 `MINIFY` 에 적는다"로 좁히고, `MINIFY` 독스트링에 rolldown이 드는 예외 다섯을 모두 적었다.
- 고친 것(명세 Minor): 티켓의 What to build가 올리기를 이 티켓의 일로 적어 "이 티켓 밖" 문단과 엇갈렸다. 올리기를 What to build에서 뺐다. 또 "6의 6대로 새 harness 티켓"은 조건 없이는 틀렸다. 병합 뒤 이 워크트리에서 올리면 돌아갈 브랜치가 병합된 이 티켓의 브랜치라, 6의 6의 첫 갈래가 그 브랜치에 싣게 한다. 그래서 새 티켓의 브랜치를 먼저 따 돌아갈 브랜치로 삼는다고 고쳤다.
- 고친 것(명세 Nit): 카드 열 개가 12~28% 커진 것을 티켓에 적었다. 리뷰는 9~28%라 했으나 손으로 다시 재니 가장 작은 Icon이 3,734→4,174바이트(11.8%)였다.
- 남긴 것: 표준 Nit 3(시험은 U+FFFD만 지키는데 설정은 ASCII 밖 전부를 이스케이프한다). 시험 이름이 U+FFFD로 한정되어 있고, Artifact 도구가 거부한 글자는 U+FFFD뿐이라 그대로 둔다. `build.minify: true`가 `output.minify`와 함께 남은 것도 vite가 CSS 압축과 주석 설정에 쓰므로 둔다(표준 축도 맞다고 했다).
- PR 직전 리뷰에 밀 주장: 티켓의 "이 티켓 밖" 문단(병합 뒤 새 티켓의 브랜치를 먼저 따 돌아갈 브랜치로 삼는 순서가 `upload.md` 1·6의 6과 맞는지), 카드 크기 "12~28%", `MINIFY` 독스트링의 "태그된 템플릿의 글, JSX 의 이름·글·속성 문자열, hashbang, 보존 주석의 글자는 이스케이프하지 않는다".
- 다시 돌린 명령: 손으로 치는 다섯은 커밋 `c0cd710c0`의 pre-commit으로 갈음했다. `check-ticket`, `zizmor`, `lint-imports`, `check-instructions`, `check-type-escapes`, `pyright`, `pyright-linux`, `run-hooks`, `pytest`(1018.6초), `web-verify`(1215.2초), 커밋 메시지 검사가 Passed였다. ruff 둘은 `.py`가 없어 Skipped라 `uv run ruff check .`과 `uv run ruff format --check .`을 손으로 쳐서 둘 다 0으로 끝났다. 앞서 커밋 메시지 훅이 제목 84자를 72자 넘김으로 막아 제목을 줄였다.
- PR 직전 리뷰: `coderabbit-review` 서브에이전트가 CLI 0.7.5(`Plan: Free`, `Seat: not assigned`)로 `coderabbit review --agent --include-untracked --base-commit 0e06c9cf7…`를 끝까지 돌려 `review_completed`, 지적 0건이었다(본 파일 다섯). 밀 주장 셋 가운데 "이 티켓 밖" 문단과 `MINIFY` 독스트링은 맞다고 했고, "카드 12~28%"는 Markdown 하나만 대 보고 나머지는 판정하지 못했다고 했다. 그 열 개는 이 세션이 고치기 전과 뒤의 산출을 `wc -c`로 모두 잰 값이라(가장 작은 Icon 11.8%, 가장 큰 Markdown 27.6%) 그대로 둔다. 참고로 낸 정규식 `.source` 변화(`asciiOnly`가 높은 코드포인트를 서로게이트 쌍으로 쓴다)는 고칠 일이 아니라고 했다.
- 회고 후보: 이스케이프 글을 적으려던 자리에 U+FFFD 글자가 그대로 드는 일이 이 사건 하나에서 세 번 났다(rolldown 압축, 앞 세션의 대기열 항목, 이 세션의 도구 인자). 추적 파일의 글에 U+FFFD가 없는지 보는 저장소 상태 시험이 잡을 수 있다.

## PR #560 병합

PR #560을 열고 `@coderabbitai review`를 남긴 뒤 `uv run python tools/wait_ci.py 560`을 기다렸다. 끝 줄은 `끝: 모두 통과. CodeRabbit: Finished`였다. CodeRabbit은 "No actionable comments were generated in the recent review."였고, claude-review는 "지적 없음."이었다(봇 첫 회차, 고친 것 없음). `headRefOid`와 `git rev-parse HEAD`가 `c0cd710c0…`로 같아 `gh pr merge 560 --squash --match-head-commit …`로 병합했다. dev의 병합 커밋은 `ad7dff584`다. `git fetch --prune origin` 뒤 `git ls-remote --exit-code --heads origin refs/heads/chore/ds-bundle-escape-replacement-char`가 2로 끝나, 원격 브랜치는 자동 삭제로 지워졌다. 주 체크아웃 미갱신: 루트는 `dev`이고 `0e06c9cf7`에 있다(`git worktree list`의 첫 줄).

## 올리기

병합 뒤 `git switch -c chore/ds-upload-markdown-cards origin/dev`로 후속 harness 티켓 `.scratch/harness/issues/ds-upload-markdown-cards.md`의 브랜치를 땄다. 브랜치가 `origin/dev`를 upstream으로 잡아, 맨 `git push`가 dev로 가지 않게 `git branch --unset-upstream`을 쳤다. 그 티켓과 이 일지를 먼저 커밋해 작업 트리를 비운 뒤, 이 브랜치를 돌아갈 브랜치로 삼아 올린다.
