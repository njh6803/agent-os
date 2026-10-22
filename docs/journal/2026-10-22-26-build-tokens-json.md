# 2026-10-22 (26) design-reverse-sync 02 tokens.json 짓기와 맞대기

## 시작

세션을 연 지시문의 시작 프롬프트와 범위다.

> 사용자: /implement .scratch/design-reverse-sync/issues/02-build-tokens-json.md (나란히 여는 2 중 2, 브랜치 feature/02-build-tokens-json, 이어받을 상태: "티켓의 임시 아티팩트 단계는 사람이 브라우저에서 값을 고쳐 저장하고 지우기를 확인해야 하므로, 그 앞에서 사람에게 부탁하고 기다린다. 디자인 시스템 아티팩트의 편집은 이 기능이 닫히기 전까지 꺼 둔다", 이번 요청 범위: PR과 병합까지)

## 임시 아티팩트 승인

티켓의 임시 아티팩트 단계 앞에서, 만들 것(`claude auth status`로 본 계정 njh4803에 Design System 형식의 비공개 임시 아티팩트, 편집이 켜진 채 지은 `tokens.json`과 사람 몫만 든 README)과 부탁할 것 셋(고치지 않고 열기, `gray-50` 녹청 라이트 값을 `#f0f4f8`로 바꾸고 `radius-m` 설명에 `버튼과 카드의 모서리`를 넣어 저장, 지우기 확인)을 보이고 물었다.

> 사용자: 만들고 진행 (추천) — 비공개 임시 아티팩트를 만들어 링크를 드립니다. 이어서 1) 고치지 않고 열기, 2) gray-50 녹청 라이트 값(지금 #f4f8fb)과 radius-m 설명(지금 빈 칸) 고쳐 저장, 3) 지우기 확인을 차례로 부탁드립니다.

## 임시 아티팩트에서 손으로 본 것

차례대로 사람에게 부탁하고 답을 받았다.

> 사용자: 열었다

판 id와 세 파일의 sha256이 열기 전과 같았다. 여는 것만으로는 저장하지 않는다.

> 사용자: 저장했다

읽지 않고 새 파일 하나를 `force` 없이 올리니 거부되지 않았다. 판 검사가 아예 없는지, 파일 단위인지 가르려고 사람에게 한 번 더 저장(`spacing-4` 설명)을 부탁했다. 이 부탁은 승인받은 셋 밖이라 까닭과 건너뛸 길을 함께 적었다.

> 사용자: 저장했다

사람이 고친 같은 파일(`tokens.json`)을 낡은 판 기준으로 올리니 거부됐다. 검사는 파일 단위다.

> 사용자: 지금 지운다 (추천) — 임시 아티팩트를 영구히 지웁니다. 링크가 더는 열리지 않고 되돌릴 수 없습니다. 시험에 쓸 파일 둘(저장된 tokens.json, 생성 몫이 붙은 README)은 서버 해시와 같은 것을 확인해 받아 두었고, 실제 디자인 시스템 아티팩트는 건드리지 않습니다.

지웠다. 수치와 문구는 `.scratch/design-reverse-sync/probes/README.md`의 "임시 아티팩트에서 손으로 본 것"에 옮겼다.

## 한 것

- 커밋 `8c9fb760`: 스크립트의 뼈대(`main.ts`, `command.ts`), 짓기(`theme-css.ts`, `build.ts`), 맞대기(`tokens-json.ts`)와 그 시험.
- 커밋하지 않은 것(이 워크트리): 시험 보강(새 `theme-css.test.ts`, `build.test.ts`·`main.test.ts`·`tokens-json.test.ts`의 사례), 받은 시험 자료 셋(`web/tools/sync-design-system/fixtures/`), `web/.prettierignore` 한 줄(받은 README가 Prettier를 지나지 않는다), 변이 표 `.scratch/design-reverse-sync/probes/sync_script_mutations.toml`, 프로브 README의 변이 표 행과 손으로 본 것, 05·06·07의 "02가 넘긴 것" 문단, 02 티켓의 체크박스(검증, `plan.md` 행, 기능을 닫지 않는다는 셋이 남았다).
- 검증(커밋하지 않은 변경 위): vitest node 프로젝트의 이 폴더 52개 통과, ESLint 0, `pnpm -C web run typecheck` 0, `pnpm -C web run format` 0, `uv run ruff check .`·`uv run ruff format --check .` 0. 변이 표 38개를 모두 다시 돌려 "변이 38 모두 기대대로". `tools/run_checks.py`는 인계로 멈춰 결과가 없다.

## 고친 것

- 페이지가 버리는 테마 id 사례에 `toString`을 넣었다가 뺐다. id를 소문자로 바꾼 뒤 거르므로 걸리지 않는 것이 맞고(페이지도 같다), 기대가 틀렸다.
- 모르는 명령 사례가 `rebuild`를 넣어 메시지에 `build`가 든 것을 단언해 헛단언이었다. `deploy`로 바꿨다.
- 받은 저장본을 되돌리는 사례의 첫 변이(반투명을 여덟 벌로 펴는 줄)가 초록이었다. 그 줄은 올린 꼴과 저장 꼴에 똑같이 걸려, 자간 기본값을 읽는 줄로 바꿨다(표의 주석).
- 일지 첫 절에 적은 전체 이메일을 계정 이름으로 바꿨다.
- 올린 `tokens.json`을 시험 자료로 따로 두었다. 지금 디자인 토큰 CSS로 지은 것과 맞대면 03의 설명 주석이 들어오는 날 받은 저장본 사례가 깨진다.

## 인계 (셀프 리뷰 직전)

세션 컨텍스트가 문턱을 넘은 채 `/code-review`를 부른 자리에서 인계 계기가 왔다. 이 세션의 제목은 `feature/02-build-tokens-json`이었다. 새 세션이 남은 것은 셀프 리뷰(기점은 origin/main과의 merge-base, 범위는 커밋 `8c9fb760`과 커밋하지 않은 변경 전부), 반영, 커밋, 검증, PR, 병합이다. 리뷰가 시험을 고치면 변이 표의 그 번호를 다시 돈다. 커밋 메시지 초안은 이 세션의 스크래치패드 `C:/Users/User/AppData/Local/Temp/claude/C--project-agent/66489337-cc13-4af0-b03b-e91e9c48b9ff/scratchpad/commit-msg-2.txt`에 있다. PR 직전 리뷰에 밀 주장은 프로브 README "임시 아티팩트에서 손으로 본 것"의 해석 둘(여는 것만으로는 저장하지 않는다, 거부는 파일 단위다)과 05·06·07의 "02가 넘긴 것" 문단이다.

제목을 `feature/02-build-tokens-json (인계함)`으로 바꿨고, 띄운 `tools/run_checks.py`를 멈췄으며(멈추기 전까지 나온 검사는 모두 통과), 워크트리 잠금을 풀었다. 주 체크아웃은 main이고 origin/main(`c47bedce`)과 같다. 낸 지시문:

```
다음 작업: .scratch/design-reverse-sync/issues/02-build-tokens-json.md. 디자인 토큰 CSS에서 여덟 벌의 tokens.json을 짓고 두 벌을 값으로 맞대는 스크립트를 세우며, 임시 아티팩트에서 페이지가 저장한 꼴과 낡은 판의 거부를 손으로 본다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/design-reverse-sync/issues/02-build-tokens-json.md
브랜치: feature/02-build-tokens-json
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-22-26-build-tokens-json.md 의 "인계 (셀프 리뷰 직전)" 절(커밋하지 않았고 이 브랜치의 워크트리에 있다)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다(일지 docs/journal/2026-10-22-26-build-tokens-json.md). 리뷰 기점은 origin/main과의 merge-base이고 범위는 커밋 8c9fb760과 커밋하지 않은 변경 전부다. 임시 아티팩트 단계는 사람의 몫까지 끝났고 아티팩트는 지웠다. 디자인 시스템 아티팩트의 편집은 이 기능이 닫히기 전까지 꺼 둔다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-22T12:57:37Z

## 이어받은 세션

> 사용자: /implement .scratch/design-reverse-sync/issues/02-build-tokens-json.md (인계로 연 세션. 이어받을 상태: "인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다", 이번 요청 범위: PR과 병합까지)

이 세션의 제목은 `feature/02-build-tokens-json`이다. `EnterWorktree(path)`로 이 워크트리에 들어왔다. 브랜치를 딴 커밋(`8c9fb760`)과 origin/main(`c47bedce`) 사이에 스킬 차이는 없고 `operations.md`에 커밋 검사 한 문장이 더해졌다.

## 셀프 리뷰

범위: 기점 `96fbe241`(origin/main과의 merge-base), diff 파일 14개, 커밋 1개(`8c9fb760`), 미추적 6개. 표준 축은 sonnet·high, 명세 축은 이 세션의 모델이다. 두 브리프에 `format.md`의 "tokens.json grammar" 절 전문을 실었다(앞 세션 스크래치패드의 사본, 판 `1792564314-af13`).

### 표준 축 보고

통과: 원칙 III(`as const`뿐), TS 시험 이름, `mutate.py --check`(변이 38, 원문 모두 한 번씩), 변이 수와 README 묶음 나열, fixture의 sha256·바이트 수, 인용 셋, `.prettierignore` 줄(예외 조건을 지킨다).

- Minor 1. 변이 표에 `expect_output`이 없다. `probes.md` 첫 항목은 여러 단언 사례를 좁힌 변이에 고른 단언만 실패할 때 나오는 표지를 요구한다. README가 든 `Tests 1 failed`는 판정의 기본 신호다.
- Minor 2. README의 "토큰 화면을 둘러봤다고 답한"은 사용자 답이 아니다(답은 "열었다"뿐). 열기 해석은 어림 수준이다.
- Minor 3. "하나라도 있으면 아무것도 올리지 않으며"는 파일 하나만 보낸 B를 일반화했다. 여러 파일의 원자성은 재지 못한 것에도 없다.
- Minor 4. 05의 "02가 넘긴 것"이 관찰한 형식 판(`7c2b`)과 문법을 읽은 판(`af13`)이 다르다는 것을 쓰지 않았다.
- Minor 5. 미래형 잔존: `spec.md` 183(아티팩트 판 단위의 비교, "티켓 02가 … 본다"), 17, 260, `plan.md` 22.
- Minor 6. `tokens-json.ts`의 `readFamily`가 인자 `taken`을 변형한다(출력 인자, CQS).
- Minor 7. 03이 주석을 달면 깨질 시험(`build.test.ts` 199·256~258, `tokens-json.test.ts` 201)이 03 티켓에 없다.
- Minor 8. 독스트링과 코드가 다르다(실행으로 확인): 테마 차례가 빌림을 거쳐 해시를 바꾼다, 레이어가 사용자 정의 속성을 든 블록에서만 등록된다(`@layer a{:root{color:red}} @layer b{…--x:1} @layer a{…--x:2}`가 `2`), 자기 별칭과 함수가 든 글꼴 스택이 남는다, 앞의 `.`를 떼지 않는다, `zIndex`를 낮추지 않는다.
- Nit. 한도 시험이 `kind`만 본다, `LIMITS.name` 120이 caps에 없다, `limit()`은 동사 표의 `check`다, `Bench`라는 이름, added/removed 블록의 반복, `buildTokensJson`은 시험만 쓴다, `.prettierignore` 대신 확장자를 바꿀 수 있다, `issue-tracker.md`는 Claude Code 계정을 njh6803이라 적는다.

### 명세 축 보고

직접 돌려 맞은 것: 짓기 두 번이 같은 바이트(sha256 `191da4dc`, 맞대는 값 `29bb660d`), 토큰 68/7/23/7/4/3, 테마 차례, 주 버튼 덮기, 소문자, `sans`, `fonts` 없음, 빈 `note`, 받은 두 파일의 차이가 고친 둘뿐(`771d7b32`), `pageRewrite`가 저장본과 글자까지 같다, 시험 52 통과, `web/package.json` 그대로, Blocked by 사슬.

- Minor (c). 파일 단위 해석의 배제가 넘친다. A는 새 경로, B는 바뀐 경로를 보내 "있는 경로에만 아티팩트 판을 견준다"는 가설을 배제하지 못한다. 06의 `claim` 갈래(기록은 그대로이고 `tokens.json`만 바뀐 때)가 재지 못한 것에 없다. 07은 "낡은 판의 publish는 거부되었다"로 시작하지만 티켓의 절차(다른 파일 하나)는 A이고 거부되지 않았다. 명세의 "아티팩트 판 단위의 비교 후 쓰기"가 거짓으로 남았다.
- Minor (c). 열기 해석의 빈틈: 답은 "열었다"뿐이다. 고친 것은 둘인데 판이 셋 생겨, 편집하러 다시 연 때의 저장을 배제하지 못한다.
- Minor (a). `--out`에 폴더를 주면 EISDIR 스택만 나오고 보고 JSON이 없다(티켓 16행 "실패는 … 그 JSON의 오류 칸이다").
- Minor (a). 티켓 20행이 "`CONTEXT.md`의 한국어 이름"을 달라는데 `CONTEXT.md`에 녹청이 없다. 구현은 `themes.ts`를 옮겼고 `app.js`에서 칸 이름을 봤다는 기록이 없다.
- Nit. "명세의 문법 읽기와 다른 점은 없다"인데 저장본의 기본값 채우기와 `fontWeight` 문자열화는 명세 296행의 셋 목록에 없다. `version: 1`과 `name: 120`의 근거가 없다. `theme-css.ts` 9행이 `@media`만 건너뛴다고 쓰지만 `@supports`·`@container`도 건너뛴다. README "부탁 셋"이 넷째 부탁을 뺐다.
- 명세 축의 탐침이 Git Bash 경로 변환으로 `C:\c\Users\User\AppData\Local\Temp\claude\…\scratchpad\spec\…`를 만들었고, 지우기는 안전 검사가 막았다고 했다.

### 판정

고친 것:

- 표준 Minor 8의 레이어: 레이어 등록을 사용자 정의 속성 거르기 앞으로 옮겼다(`theme-css.ts`). 시험 "레이어의 차례는 사용자 정의 속성이 없는 규칙까지 세어 처음 나온 차례다"를 더했고, 옛 동작으로 되돌리는 변이가 그 사례를 빨갛게 한다.
- 명세 (a)의 `--out` 폴더: 쓰기 실패를 `output` 오류로 보고 JSON에 싣는다(`command.ts`의 `ERROR_KINDS`와 `writeOutput`). 시험 "출력 파일을 쓸 수 없으면 output 오류다"와 변이 하나를 더했다.
- 표준 Minor 6: `readFamily`가 인자를 바꾸지 않는다. 앞 계열이 쓴 이름은 `readTokens`가 그때그때 모아 넘긴다. 시험 "같은 이름의 둘째 토큰은 한 계열 안에 있든 앞 계열이 쓴 이름이든 버린다"와 변이 둘(각 거르기를 하나씩 뺀다)을 더했다.
- 표준 Nit: `limit()`을 동사 표의 `check`로 `checkLimit()`이라 고쳤다. 한도·입력·usage·옵션·선택자 실패 사례가 `kind`만 보던 것을 까닭의 문구까지 단언하게 했다.
- 표준 Minor 1: 변이 42개 모두에 `expect_output`을 넣었다. 변이마다 손으로 넣어 받은 실패 출력에서 고른 단언의 실패 머리 메시지를 골랐고, 머리가 값을 줄여(`…(1)`) 같은 사례의 다른 변이와 갈리지 않는 것(05~08, 21·22 등)은 차이 줄을 함께 적었다. 같은 사례를 겨누는 묶음끼리 표지가 겹치지 않는 것을 출력으로 봤다.
- 표준 Minor 8의 나머지와 명세 Nit의 독스트링: 테마 차례가 빌림을 거쳐 값의 차이로 나올 수 있다, 따라 하지 않는 페이지의 정리(가리키는 토큰의 존재와 순환, 글꼴 스택의 문법), 토큰 이름은 `--`만 뗀다, `@layer` 밖의 at-rule 목록, 결합자 안의 의사 클래스, `TokensFile.version`과 `LIMITS.name`의 근거. 서술마다 함수를 불러 대 봤다(스크래치패드의 `claims.ts`·`claims2.ts`). 레이어 서술을 대 보다가 바깥이 다른 같은 이름의 안쪽 레이어(`a.x`와 `c.x`)를 하나로 세는 것이 독스트링에 없어 한 구절을 더했다.
- 표준 Minor 2·3과 명세 (c) 둘: 프로브 README의 "임시 아티팩트에서 손으로 본 것"을 고쳤다. 열기 해석은 어림으로, `publish`의 거부는 두 해석(파일 단위, 이미 있는 경로만 아티팩트 판과 견준다)이 남았다고 적었고, 가르는 갈래와 여러 파일, 시간 지연과 다시 열기의 저장을 재지 못한 것에 더했다. 넷째 부탁을 머리 문단에 적었다.
- 표준 Minor 4와 명세 Nit: 05에 형식 판 둘(`7c2b`에서 관찰, `af13`의 문법을 읽음)과 명세의 셋 밖 정규화 둘(기본값 채우기, 굵기의 문자열화)을 적었다.
- 표준 Minor 5와 명세 (c): `spec.md` 183행에 02가 본 것을 주석으로 달았고, 06·07의 메모를 두 해석과 `claim` 갈래로 다시 썼다.
- 표준 Minor 7: 03에 주석을 달면 깨지는 시험 셋과 겨누는 변이를 넘겼다.
- 명세 (a) 20행: 티켓 02에 구현 메모(`app.js`가 `color.themes[].name`을 120자에서 자른다, `CONTEXT.md`에 이름이 없어 `themes.ts`를 옮겼다)를 달았다.

남긴 것과 까닭:

- 표준 Minor 8의 `zIndex`: 오탐이다. 형식 설명의 "family keys"는 `type.families`의 키이고, 다른 계열의 절 제목(`Z index`)이 키의 대소문자를 지킨다는 것을 보인다.
- 표준 Minor 8의 앞 `.`: 오탐이다. 판 `af13`의 `app.js`가 토큰 이름에서 `--`만 뗀다. 독스트링에 적었다.
- `parse`·`read` 동사가 섞인 것: `CONTEXT.md` 동사 표의 `read`는 포트 읽기라 판단 항목으로 남긴다. `Bench`라는 이름, added·removed 블록의 반복, 시험만 쓰는 `buildTokensJson`도 판단 항목이다.
- `.prettierignore` 대신 확장자를 바꾸는 길: 규칙의 예외 조건(경로와 까닭을 적는다)을 지키므로 그대로 둔다.
- `issue-tracker.md` 41행의 계정 이름(njh6803, `claude auth status`는 njh4803): 이 PR 밖이다. 회고 후보로 넘긴다.
- 명세 축 탐침이 만든 `C:\c\…\scratchpad\spec\…` 폴더: 서브에이전트의 지우기가 막혔다. 사용자에게 알린다.

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 사실 문장, 원문):

1. `theme-css.ts` 머리: "`@layer` 밖의 at-rule(`@media`, `@supports`, `@container` 등) 안의 규칙은 보지 않는다."
2. `theme-css.ts` 머리: "결합자가 든 선택자는 풀지 않고 뿌리에 맞지 않는 것으로 넘겨, 그 안의 의사 클래스도 오류가 아니다. `!important`, 이름 있는 레이어의 미리 선언(`@layer a, b;`), 중첩 레이어(`@layer a { @layer b { … } }` 의 `a.b`)는 보지 않는다. 레이어의 차례는 그 레이어 블록에 바로 든 규칙이 처음 나온 차례이고(사용자 정의 속성이 없는 규칙도 센다), 안쪽 레이어는 바깥 레이어와 따로 세며 바깥이 달라도 이름이 같으면(`a.x` 와 `c.x`) 하나로 센다."
3. `tokens-json.ts` 머리: "토큰 이름은 페이지처럼 앞의 `--` 만 뗀다(형식 설명은 `.` 도 뗀다고 적지만 그 판의 페이지 스크립트는 토큰 이름에서 `--` 만 뗀다)."
4. `tokens-json.ts` 머리: "테마의 차례도 그 자체로는 맞대지 않는다. 다만 첫 테마와, 첫 테마에 값이 없을 때 값을 빌려 올 벌은 차례로 정해지므로, 차례가 바뀌면 벌마다 푼 값이 바뀔 수 있고 그것은 값의 차이로 나온다."
5. `tokens-json.ts` 머리: "따라 하지 않는 페이지의 정리: 다른 토큰을 가리키는 값이 실제로 있는 토큰인지와 자기나 서로를 가리켜 도는지(페이지는 그런 값을 버린다), 글꼴 스택의 문법(형식 설명이 금지하는 글자와 따옴표 짝). 그런 값은 남겨 맞댄다."
6. `TokensFile.version`: "페이지가 저장할 때 쓰는 판(판 1792564314-af13 의 `app.js` 가 `version: 1` 로 다시 쓴다)."
7. `LIMITS`: "그 줄에 없이 페이지 스크립트(판 1792564314-af13 의 `app.js`)가 테마의 표시 이름·글꼴 이름·글자 묶음 이름을 자르는 길이(`name`, 120)."
8. 티켓 02 구현 메모의 `app.js`가 `color.themes[].name`을 읽어 120자에서 자르고 저장본도 그 칸을 지켰다는 문장.
9. 프로브 README "임시 아티팩트에서 손으로 본 것"의 저장 항목(앞 커밋이 옮긴 꼴과 다른 점이 없다, 셋 밖의 둘), `publish` 항목(두 해석이 남았다, "Nothing was published or removed"는 파일 하나를 보낸 갈래의 문구다).
10. `spec.md` 183행 주석: 거부는 보낸 파일과 무관한 아티팩트 판 하나의 비교가 아니었다, 세션이 본 적 없는 새 파일은 그사이 아티팩트가 바뀌었는데도 지나갔다, 늦게 쓴 쪽이 거부된다는 것은 두 해석 모두에서 나오는 어림이다, 거부는 새 판의 내용을 건네지 않고 그 파일을 다시 읽으라고 안내했다.
11. 03의 "02가 넘긴 것"이 든 깨지는 시험 셋과 그 행 번호 없는 사례 이름.

다시 돌린 명령(반영 뒤, 커밋 전): 변이 표 42개를 표지와 함께 돌려 "변이 42 모두 기대대로"(기준선 모두 초록, 표지 없음 0). 이 폴더의 vitest node 프로젝트 55개 통과, ESLint 0, Prettier 0, `pnpm -C web run typecheck` 0. 손으로 치는 다섯은 커밋의 pre-commit으로 갈음하고 결과는 커밋 뒤에 적는다.
