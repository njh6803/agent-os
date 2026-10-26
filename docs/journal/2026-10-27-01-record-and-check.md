# 2026-10-27 (01) design-reverse-sync 05 기록과 확인 명령

## 시작

세션을 연 지시문의 시작 프롬프트와 범위다. 2026-10-26에 열었고 날이 바뀐 뒤 이 일지를 만들었다.

> 사용자: /implement .scratch/design-reverse-sync/issues/05-record-and-check.md (나란히 여는 3 중 3, 브랜치 feature/05-record-and-check, 읽을 것: "docs/journal/2026-10-26-11-build-tokens-json.md 의 "다음". 나란히 도는 티켓은 .scratch/design-reverse-sync/issues/03-token-comments.md, .scratch/design-reverse-sync/issues/04-import-command.md", 이어받을 상태: "PR #356의 claude-review 셋째 회차(99b0b51)에서 보류한 셋이 이 파일들에 걸린다(까닭은 PR #356의 2026-10-26 코멘트). 첫째, build.ts와 tokens-json.ts의 색 리터럴 판정을 하나로 모으는 일은 04가 한다. 둘째와 셋째, tokens-json.ts를 정규 꼴과 차이 목록으로 나누기와 diffType의 added/removed 되풀이 줄이기는 04도 같은 파일을 만지므로 이 티켓에서 하지 않는다. 04·05 가운데 뒤에 병합하는 쪽이 일지 "다음"에 넘긴다", 확인할 선행 조건: "주 체크아웃 미갱신: 루트는 main. tidy-checkouts는 묶음의 첫 세션이 돈다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다", 이번 요청 범위: PR과 병합까지)

## 한 것

- 커밋하지 않은 것(이 워크트리, 기점 `71433a0d`). 모두 `web/tools/sync-design-system/` 아래다.
  - 맞대는 값(`file-hash.ts`): 기록에 드는 경로, 뿌리 README의 사람 몫(페이지 스크립트 판 `1792564314-af13`에서 옮겼다), 파일 종류마다의 맞대는 값. 기록·`pending`·확인·보낼 것이 이 함수 하나를 쓴다.
  - 기록(`sync-record.ts`): 꼴 판 1, 읽기의 네 결과(풀림, 풀리지 않음, 모르는 꼴 판, 어긋난 꼴), 다음 기록(첫 호출은 앞 기록에 `pending`을 얹고, 마지막 호출은 보낸 것과 지운 것을 합치고 `pending`을 비운다), 들여쓰기 없는 JSON과 512,000바이트 한도. `claim`은 받은 그대로 지킨다.
  - 보낼 것과 빌드(`upload.ts`): 보낼 파일·지울 경로를 내는 `planUpload`와 빌드가 필요한지 가르는 `needsBuild`.
  - 확인(`check.ts`): 결과 넷(명세의 다섯째인 들이는 중은 06이 더한다)과, 스킬이 `check paths`가 빈 목록을 낼 때까지 받기를 되풀이한 뒤 `check judge`를 부르는 받기 계약. 읽지 못한 경로는 `absent`(없다는 까닭)와 `failed`(다른 까닭)로 받는다.
  - 기록 명령(`record.ts`): `record plan`, `record needs-build`, `record write`. 공용 읽기는 `io.ts`, 명령 표는 `main.ts`의 두 줄이고, `command.ts` 머리의 오류 종류 설명을 이 티켓의 쓰임(`input`의 입력끼리 어긋남, `limit`의 기록 한도)에 맞췄다.
  - 시험 다섯 파일(`file-hash`, `sync-record`, `upload`, `check`, 자식 프로세스로 명령을 띄우는 흐름 시험 `record-check`). 이 폴더의 vitest node 시험이 셀프 리뷰 전 187개, 반영 뒤 194개 초록이었다.
  - 변이 표 `.scratch/design-reverse-sync/probes/record_check_mutations.toml`(셀프 리뷰 전 39개, 반영 뒤 47개)와 그 README의 행·결과 절.
  - 06·07 티켓에 "05가 넘긴 것" 문단을 더했다. 06의 29행은 지금 코드에서 지은 `tokens.json`을 확인 명령의 입력으로 더하는 일도 06의 몫이라고 고쳤다(05의 판정에는 쓰이지 않아 더하지 않았다).
- 빨강: 구현 전에는 모듈이 없어 시험 파일이 모두 빨간 것만 봤다. 단언 하나하나의 빨강은 변이 표로 봤다(`tools/mutate.py`가 "변이 39 모두 기대대로"로 끝났다).

## 고친 것

- 확인의 받을 경로 함수(`nextFetch`)는 처음에 첫 받기의 경로를 빼고 그 뒤에 받을 경로만 냈는데, `check judge`가 첫 받기의 경로를 "받지 않음"으로 보아 흐름 시험이 빨갰다. "아직 받지 않은 경로를 낸다"는 계약으로 다시 짓고, 흐름 시험의 받기 고리와 단위 사례 둘을 더했다.
- `io.ts`의 제어 문자 판정이 ESLint `no-misused-spread`에 걸려 `\p{Cc}` 정규식으로 바꿨다.
- 변이 표의 첫 실행은 표지를 자리표시로 두고 39개 모두 빨간 것을 봤다. `tools/mutate.py`는 표지가 없는 실패 출력의 끝 10줄만 보여 실패 머리가 잘려, 스크래치 스크립트로 변이를 하나씩 넣어 전체 실패 출력을 받고 표지를 골랐다.
- 셀프 리뷰 중에 origin/main에 들어온 harness 015(#390)가 표지 규칙을 "가르려는 다른 해석 아래에서는 나지 않는 관찰"로 고쳤다. 그 기준으로 다시 대 보니, 13번(해시 꼴)의 시험은 입력 일곱을 한 고리로 돌아 다른 입력이 빨개져도 같은 실패 머리가 났다. 고리의 입력마다 이름을 붙여 `expect(값, 이름)`으로 넘기고, 표지를 `AssertionError: 짧은 해시: expected 'ok' to be 'malformed'`로 바꿨다.

## 셀프 리뷰

범위: 기점 `71433a0d`, 작업 트리의 변경 여섯 파일, 미추적 열둘, 커밋 없음. 표준 축은 sonnet·high, 명세 축은 본 세션의 모델로 나란히 띄웠다.

### 표준 축 보고

시험을 돌려 9파일 187개 통과, `mutate.py --check`는 변이 39개의 원문이 모두 한 번씩 있다고 냈다고 적었다.

- (a) 위반 1: `CODING_STANDARDS.md` "출력 인자를 쓰지 않는다". `check.ts`의 `judgeTokens(web, record, classes)`가 `classes`를 고쳐 결과로 삼고, 반환이 `TokensVerdict | CheckReport` 합집합이라 호출부가 `"result" in tokens`로 가른다.
- (a) 위반 2: `CODING_STANDARDS.md` "실패를 기대하는 테스트는 실패의 까닭까지". 오류 종류(`kind`)만 단언하는 자리가 `upload.test.ts` 100-103·213-219·329-345, `sync-record.test.ts` 311-338·475-477, `check.test.ts` 732-743, `record-check.test.ts` 334-337과 `test.each` 340-375에 있다. 같은 `input`을 던지는 자리가 `sync-record.ts`에 여럿이다.
- (b) 실패한 줄이 39개 모두 변이가 겨눈 단언이라는 probes README의 문장은 11에서 거짓이다. 11은 `sync-record.test.ts:254`의 준비 문장 `const again = nextRecord(...)`에서 던지고, 어떤 `expect` 안도 아니다(읽어서 낸 판정). 기준선 37, 두 쌍, 항목별 합 39, `mutate.py`의 끝 10줄은 맞다.
- (b) `file-hash.ts` 15-18행이 판 `1792715827-ef57`의 `app.js`를 손으로 봤다고 적는데 기록이 없다. 시험 자료에는 `Read this README first`, manifest 블록, Quick start 머리가 없어, `file-hash.test.ts`의 `READ_FIRST`·`MANIFEST_BLOCK`은 구현에서 베낀 값이고 그 갈래는 스스로 확인하는 시험이다.
- (b) 05 티켓 3행은 확인 명령이 "지금 코드에서 지은 `tokens.json`"을 받는다고 아직 쓴다.
- (b) 06의 "갈래를 더할 자리는 넷"은 반례가 있다. `record.ts`의 `readCheck`가 `clean`·`edited`·`beforeRecord` 밖의 결과를 `usage`로 거부해, 06이 더할 들이는 중이 거기서 걸린다.
- (b) 07의 "스킬이 맡는 것은 넷"은 `--artifact-sha256`, `--artifact` 폴더, `--changed`, `--commit`·`--at`을 세지 않았다. 07의 46행은 `git diff --name-only`로 남아 새 문단의 `-c core.quotePath=false`와 어긋난다.
- (b) `check.ts` 머리의 "결과는 다섯"과 달리 `CheckReport`는 넷이다. `files`를 "토큰 밖"이라 쓰지만 `tokens.json`이 지워진 것도 넣는다.
- (b) `command.ts`의 `input`을 "입력끼리 맞지 않는다"로 넓혔는데 `upload.ts`와 `record.ts`의 몇 자리는 입력 불일치를 `usage`로 던진다(판단).
- (c) 냄새(판단): `readCheck`·`decisionOf`의 불리언 인자, 아무도 쓰지 않는 `io.ts`의 `readArtifactFile`, 중복(`inputError` 둘, 시험의 `caught` 셋, `upload.ts`와 `sync-record.ts`의 정렬 도우미, `io.ts`의 비교자가 `byPath`의 복사본), `record.ts`가 확인 보고를 글자 값으로 다시 읽는 것(Shotgun Surgery), 판정과 명령 인자 해석이 한 파일에 섞인 것(Divergent Change), `fileEdits`가 `files`가 배열이 아니면 빈 목록으로 지나가는데 `tokens`는 던지는 불일치.

### 명세 축 보고

시험을 돌려 187개 초록, 티켓의 확인·기록·보낼 것과 빌드 사례가 시험 이름과 하나씩 맞고, 512,000바이트 경계와 1,024개 파일·`tokens.json` 세 벌의 합성 기록이 있다고 적었다. A·B·C는 스크래치패드의 탐침(`probe05.ts`, `probe05b.ts`)으로 재현했다고 적었다.

- (a) 웹이 더한 그림·글꼴을 덮어쓰기가 지우지 않는다. 명세는 "웹에서 더한 파일은 지운다"인데, 그림 추가는 확인 보고의 `index`에만 나오고 `files`는 비며(탐침 B), `readCheck`는 `webAdded`를 `files`에서만 고른다.
- (a) 명세는 "색인이 드는 컴포넌트마다의 `components/<이름>/README.md`"를 받으라는데, 코드는 기록의 컴포넌트 폴더에서 고른다(`check.ts:234`). 웹이 새 컴포넌트 폴더에 둔 README는 받지 않는다(탐침 C). 실제 색인에 컴포넌트 목록이 없다는 것도 함께 봤다.
- (b) `io.ts`의 `readArtifactFile`은 쓰이지 않는다.
- (c) 다시 한 올리기가 또 첫 호출에서 멈추면, `nextRecord`의 첫 호출이 이미 지워진 경로를 `pending.delete`에서 빼면서 `files`에는 남겨, 다음 확인이 그 경로를 `removed` 웹 편집으로 낸다(탐침 B2).
- (c) 웹이 고친 `pending`의 지울 경로는 덮어쓸 수 없다. 확인이 `changed`로 내고 `--overwrite`가 되돌릴 파일에 넣어, `planUpload`가 "되돌릴 … 가 이번 산출에 없다"로 멈춘다(탐침 A). 웹이 지운 파일을 코드도 뺀 `removed`도 같은 길로 멈춘다(코드를 읽은 것).
- (c) 07 메모는 덮어쓰기를 `--check <확인 보고> --overwrite`라고만 적는데, 기록에 `pending`이 있으면 `--check`가 없을 때 `usage`이고, `needs-build`의 `--check --overwrite`가 빠졌다.
- (c) 06의 "갈래를 더할 자리는 넷"에 반례가 있다(`readCheck`가 다른 결과를 거부하고, `needs-build`의 `decisionOf`에도 갈래가 필요하다).
- (c) 명세는 "README는 … 사람 몫의 sha256"이라고 README 전체를 말하는데 코드는 뿌리 README에만 적용한다(`file-hash.ts:8-9`). 근거는 `app.js`를 손으로 읽은 것뿐이고 그 원본은 저장소에 없다. 명세가 빼라는 `api/*.md` 가운데 생성 카드가 아닌 것(`project/api/notes.md`)은 기록에 해시된다.
- 주장 검증: "≤512 KB" 인용, 같은 사례를 나눈 쌍이 21·22와 24·25뿐인 것, `check paths`가 두 번째 받기 뒤에 빈 목록을 내는 것은 맞다.

### 판정과 반영

Critical은 없었다. 명세 축 (c)의 둘(이미 지워진 경로, 웹이 고친 지울 경로)은 웹 편집이 아닌 것을 웹 편집으로 내거나 사람이 고른 덮어쓰기를 막는 길이라 Major로 보고 고쳤다. 표준 축 (a) 둘은 `CODING_STANDARDS.md` 위반이라 고쳤다.

- 고침. `judgeTokens`가 분류 표를 고쳐 결과로 삼던 출력 인자를 없애고, `{kind: "judged", pending, …} | {kind: "undecidable", report}` 판별 유니온을 돌려준다.
- 고침. 오류 종류만 단언하던 자리(표준 축이 든 곳 전부와 흐름 시험의 거절 보고)가 문구까지 단언한다. `test.each` 표는 기대 문구를 셋째 칸으로 든다. 받지 않은 경로의 문구는 `nextFetch`가 낸 목록으로 짓되, 그 목록에 지침 문서가 든다는 것을 따로 단언해 구현만으로 짓는 기대값이 되지 않게 했다.
- 고침. 다시 한 올리기의 첫 호출(`nextRecord`)이 이미 지워진 경로(`gone`)도 `pending.delete`에 이어 적는다. 그 호출 뒤에 또 멈추면 다음 확인이 그 경로를 지운 것(`deleted`)으로 가른다.
- 고침. 덮어쓰기의 되돌릴 파일이 이번 산출에 없으면 멈추던 것(`planUpload`의 "되돌릴 … 가 이번 산출에 없다")을 좁혔다. 확인 보고의 웹 편집을 고친 것(`revert`), 지운 것(`webRemoved`, 새 칸), 더한 것(`webAdded`)으로 나누고, 이번 산출에 없는 앞의 둘은 코드가 뺀 것으로 알려진 경로(지난 산출 목록이나 `pending.delete`에 든 것)만 받아 고친 것은 지우고 지운 것은 기록에서만 뺀다(`gone`). 그 밖은 몇 파일만 보내는 산출이 빠뜨린 것과 가를 수 없어 `input` 오류로 멈춘다. 압축 전에는 산출에 없는 되돌릴 파일은 모두 지운다고 정했는데, 다시 보니 몇 파일만 보내는 산출에서 코드에 있는 파일을 지우는 길이라 좁혔다. 지운 것이 산출에 있으면 보내 되살린다. 계획 보고에 `webRemoved`가 더해졌고, `needs-build`는 고친 것과 지운 것을 함께 빌드 판정에 넘긴다.
- 고침. `readCheck(path, overwrite: boolean)`와 `decisionOf(check, overwrite: boolean)`의 불리언 인자를 없앴다. `readCheck`는 보고를 읽기만 하고(`CheckReading`), 덮어쓰기 판단은 인자 값을 받는 `decisionOf(values)`가 한다. `files`가 배열이 아닌 보고는 빈 목록으로 지나가지 않고 `input` 오류다.
- 고침. 공용 도우미(`byPath`, `sortedPaths`, `inputError`)를 `io.ts`로 모으고, 쓰이지 않던 `readArtifactFile`과 정렬 도우미 사본 둘을 지웠다.
- 고침. 사실이 틀린 문장. probes README의 11번(위 표준 축 (b)), `check.ts` 머리의 "결과는 다섯"과 "토큰 밖", 05 티켓 3행(주석을 달았다), 06의 "자리는 넷", 07의 "스킬이 맡는 것은 넷"과 46행의 `git diff`, 07 메모의 `pending`일 때의 `--check`와 `needs-build`의 덮어쓰기 인자. `command.ts`의 `usage`는 "받은 상태로는 부를 수 없는 인자 조합"까지로 설명을 넓혔다(던지는 자리는 그대로다).
- 근거를 적음. `file-hash.ts` 머리가 말하는 판 `1792715827-ef57`의 `app.js`는 2026-10-26에 Artifact 도구의 `read`로 디자인 시스템 아티팩트에서 받은 사본(세션 스크래치패드, sha256 `cda06f02eb477cb408ff7897ef4fbaf1c4cddd50e015179fb752887a9f42871d`)이다. 그 사본에서 문구를 찾아(`needle.py <사본> <폭> <횟수> <문구>…`, 커밋하지 않은 스크래치 스크립트) 손으로 봤다. 생성 카드 정규식은 `Rqe=/^api\/(?:icons\.md|tokens\.md|(?:tokens|components|assets)\/[^/]+\.md)$/`로 구현의 `GENERATED_CARD`와 글자 그대로 같다. 생성 머리 둘은 `CH="## Consuming this system (generated — do not edit)"`, `QXe="## Quick start (generated from tokens.json — do not edit)"`이고, 안내 문장 `NRe`는 시험의 `READ_FIRST`와 끝까지 같다. 구분선 정규식은 `U9="\\r?\\n\\r?\\n---\\r?\\n\\r?\\n"`, manifest 판은 `Tp=3`이다. 그래서 시험의 그 상수들은 구현에서 베낀 값이 아니라 페이지 스크립트에서 온 값이고, 시험 머리에 그렇게 적었다. 저장할 때 README를 다루는 자리는 `se={readme:"README.md",…}`의 `se.readme`를 쓴다(찾은 처음 네 자리 모두).
- 남김. 웹이 더한 그림·글꼴을 덮어쓰기가 지우지 않는 것(명세 축 (a)). 확인 보고의 `index`에만 나오고, 색인의 그림 항목이 파일 경로를 어떻게 드는지 보지 않았으며, 지우는 일은 스킬이 아티팩트에 보내는 일이라 07에 넘겼다(07의 "05가 넘긴 것", `check.ts`·`record.ts`의 못 보는 것).
- 남김. 컴포넌트 README를 색인이 아니라 기록의 컴포넌트 폴더로 고르는 것(명세 축 (a)). 2026-10-26에 받은 색인(`project/design-system.json`)의 키는 열넷(`v`, `assetGroups`, `blobs`, `createdOnFiles`, `docs`, `editing`, `groups`, `layout`, `libraries`, `namespace`, `sections`, `source`, `title`, `lastChange`)이고 컴포넌트를 드는 칸이 없어(`groups`는 `["notes"]`, `libraries`는 빈 배열, `sections`는 빈 객체다. 사본을 JSON으로 풀어 손으로 봤다) 명세대로 지을 입력이 없다. `check.ts`의 못 보는 것에 적었다. 명세의 그 문장을 고칠지는 아래 "다음"에 남긴다.
- 남김. 명세는 README 전체를 사람 몫으로 잰다고 읽히는데 코드는 뿌리 README에만 적용하는 것(명세 축 (c)). 위 사본에서 페이지가 생성 몫을 다루는 README가 뿌리 하나다. 생성 카드가 아닌 `api/*.md`가 기록에 해시되는 것도 페이지의 정규식(`Rqe`)이 그 파일을 다시 짓지 않아서이고, 확인은 `api/` 아래 마크다운을 받지 않으니(못 보는 것) 판정을 바꾸지 않는다.
- 남김. 시험의 `caught` 셋. 시험 파일마다 둔 다섯 줄 도우미이고 이 폴더에 공용 시험 도우미 모듈이 없다.
- 남김. `record.ts`가 확인 보고를 글자 값으로 다시 읽는 것(Shotgun Surgery). 보고는 프로세스 사이의 JSON이라 읽는 쪽이 꼴을 다시 본다. 06이 결과를 더할 때 함께 고칠 자리로 06에 적었다.
- 남김. 판정과 명령 인자 해석이 한 파일에 있는 것(Divergent Change). 판정 함수(`judge`, `nextFetch`)는 인자 해석과 따로 내보내 시험이 판정만 부른다. 06이 갈래를 더해 판정이 커지면 다시 본다.

### 다시 돌린 것

- `pnpm -C web exec vitest run tools/sync-design-system`: 고친 시험을 먼저 돌려 빨강을 봤다(새 사례 여섯과, `byPath`를 옮겨 `check.ts`·`record.ts`가 실리지 않은 사례들). 이미 지워진 경로 사례는 구현을 먼저 고친 뒤에 써서 시험의 빨강을 보지 못했고, 변이 40이 그 빨강이다. 반영 뒤 9파일 194개 초록.
- `pnpm -C web exec eslint --max-warnings 0 tools/sync-design-system`, `pnpm -C web exec tsc --noEmit`, Prettier: 깨끗했다.
- 변이 표: `--check`로 원문 47개를 본 뒤, 바뀐 표지의 일곱과 새 여덟을 하나씩 넣어 전체 실패 출력을 받고 표지를 골랐다. 표 전부를 다시 돌려 "변이 47 모두 기대대로"였다(probes README의 2026-10-27 줄).
- 첫 커밋의 pre-commit(14분, 그 가운데 web 검증이 13분)에서 pytest가 이 변경과 무관한 `tests/tools/`의 시간 시험 둘로 빨갰다. `test_probe_kit.py::test_배출은_줄이_계속_와도_제한_시간에_끝난다`(배출이 빈 목록)와 `test_rerun_runner.py::test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다`(종료 코드 1)다. 두 파일만 따로 돌리니 68개 통과였다(그것도 13분 걸렸다. 이 PC에 다른 세션이 여럿 돌던 때다). 대기열 306이 받아들여 닫은 종류(부하에서 빨개지는 시간 시험)라 회차를 더하지 않고 여기에만 적고, 커밋을 다시 쳤다.
