# 2026-10-26 (17) 사진 비교가 몇 픽셀 차이로 흔들리는 원인을 재서 고친다 (harness 016)

## 사용자 프롬프트

> 사용자: 대기열 414를 티켓 .scratch/harness/issues/016-visual-focus-flake.md로 쓰고 한다 (next-session 지시문. 나란히 여는 여덟 가운데 일곱째이고, 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(016-visual-focus-flake)로 들어가 브랜치를 바꾼다. 브랜치 chore/016-visual-focus-flake, 범위는 PR과 병합까지. 처방은 "포커스 링 전환을 찍는 시점을 재서 찍기 전 대기로 고친다")

> 사용자: 대기열 414를 티켓 .scratch/harness/issues/016-visual-focus-flake.md로 쓰고 한다 (아래 "인계" 절의 지시문으로 연 둘째 세션. `git worktree list`에서 찾은 이 워크트리에 EnterWorktree(path)로 들어가 셀프 리뷰부터 잇는다. 범위는 PR과 병합까지)

> 사용자: 대기열 414를 티켓 .scratch/harness/issues/016-visual-focus-flake.md로 쓰고 한다 (아래 "인계 (커밋 뒤)" 절의 지시문으로 연 셋째 세션. 같은 워크트리에 EnterWorktree(path)로 들어가 바뀐 정답의 까닭 재기부터 잇는다. 범위는 PR과 병합까지)

> 사용자: 대기열 414를 티켓 .scratch/harness/issues/016-visual-focus-flake.md로 쓰고 한다 (아래 "인계 (셀프 리뷰 직전, 셋째 세션)" 절의 지시문으로 연 넷째 세션. 같은 워크트리에 EnterWorktree(path)로 들어가 셀프 리뷰(기점 90a89c13)부터 잇는다. 범위는 PR과 병합까지)

> 사용자: 대기열 414를 티켓 .scratch/harness/issues/016-visual-focus-flake.md로 쓰고 한다 (아래 "인계 (커밋 뒤, 넷째 세션)" 절의 지시문으로 연 다섯째 세션. 같은 워크트리에 EnterWorktree(path)로 들어가 origin/main 합치기부터 잇는다. 범위는 PR과 병합까지)

> 사용자: 대기열 414를 티켓 .scratch/harness/issues/016-visual-focus-flake.md로 쓰고 한다 (아래 "인계 (PR 연 뒤, 다섯째 세션)" 절의 지시문으로 연 여섯째 세션. 같은 워크트리에 EnterWorktree(path)로 들어가 첫 `@coderabbitai review` 코멘트와 봇 회차부터 잇는다. 범위는 PR과 병합까지)

> 사용자: 대기열 414를 티켓 .scratch/harness/issues/016-visual-focus-flake.md로 쓰고 한다 (아래 "인계 (셀프 리뷰 직전, 여섯째 세션)" 절의 지시문으로 연 일곱째 세션. 같은 워크트리에 EnterWorktree(path)로 들어가 셀프 리뷰(기점 18770829)부터 잇는다. 범위는 PR과 병합까지)

> 사용자: 대기열 414를 티켓 .scratch/harness/issues/016-visual-focus-flake.md로 쓰고 한다 (아래 "인계 (커밋 뒤, 일곱째 세션)" 절의 지시문으로 연 여덟째 세션. 같은 워크트리에 EnterWorktree(path)로 들어가 PR 본문 넓히기부터 잇는다. 범위는 PR과 병합까지)

## 결정

- **고침은 찍기 전 대기가 아니라 브라우저 실행 인자 `--disable-partial-raster`다.** 대기열 414와 지시문은 원인을 포커스 링 전환의 찍는 시점으로 보고 찍기 전 대기를 처방했다. 재 보니 흔들린 그림은 크롬의 부분 래스터가 낸 그림과 타일 전체를 다시 그린 그림 둘 가운데 하나였고, 어느 쪽이 찍히는지가 시점에 달렸다(아래 "진단"). 글 입력의 올림은 기다려도 부분 래스터의 그림 그대로라 대기로는 고쳐지지 않는다. 문턱을 넓히지 않는다는 행의 선은 지켰다.
- **인자는 `@agent-os/ui/visual`의 `BROWSER_ARGS` 한 자리에 두고 패키지와 위젯의 설정이 함께 쓴다.** 두 설정은 "같은 조건"이고, 한쪽만 바뀌면 다시 흔들린다.
- **설정이 인자를 넘기는지는 사진이 아니라 브라우저의 명령줄로 본다.** 인자를 빼면 패키지의 스위치 포커스 사진은 빨갛지만, 위젯의 화면 사진은 인자 없이 세 번 돌려도 초록이었다. 그래서 두 사진 비교에 브라우저가 받은 명령줄(CDP `SystemInfo.getInfo`)에 `BROWSER_ARGS`가 모두 있는지 보는 시험을 하나씩 두었다(`missingBrowserArgs`). 사진은 회차에 따라 달라도 명령줄은 늘 같다.
- **ADR 0026의 이력은 두지 않는다.** 정답 사진은 한 벌이고 고정한 이미지 안에서만 찍는다는 결정은 그대로이고, 인자는 그 결정 안에서 결정성을 지키는 구현 세부다.
- **정답 사진은 `--update-snapshots=all`로 전부 다시 쓴다.** `visual:update`(`changed`)는 비교가 실패한 사진만 다시 쓰는데, pixelmatch가 갈린 픽셀을 모두 안티에일리어싱으로 보아 빼면 비교가 통과해 옛 바이트가 남는다(여러 줄 글 입력의 라이트 올림이 그랬다). 그러면 정답이 "이 인자로 찍은 그림"이라는 말이 사진마다 참이 아니다. 픽셀이 같은 사진은 다시 써도 바이트가 그대로라 diff에 들지 않았다.

## 진단

흔들린 세 번(웹 코드를 건드리지 않은 PR의 `visual` 잡)의 아티팩트를 받아 `ci_diff.mjs`로 풀었다. 세 사진 모두 갈린 픽셀이 둥근 모서리에서 테두리와 바탕 사이의 중간색으로 칠한 픽셀 몇 개였고(알파는 모두 255) 채널 차가 1~3이었다. 실패 머리의 N(1, 3, 6)은 차이 그림의 빨강 수와 같았고, 노랑(pixelmatch가 안티에일리어싱으로 보아 뺀 픽셀)까지 더하면 디코더가 센 갈린 자리와 같았다. 첫 판은 N과 디코더 수를 바로 맞대 셋 다 어긋났다(1·2, 3·29, 6·17).

그다음 같은 이미지에서 세 사진의 스토리를 프로브(`flake.probe.mts`)로 되풀이해 찍었다. 찍은 바이트를 옛 정답과 맞대 같으면 A, 다르면 B로 갈랐다.

- 인자 없이(지금의 설정) 알림은 곧바로 찍으면 거의 늘 A였고(88번 중 87번. 첫 실행 `flake-smoke`에서 한 번 B. 결과 줄이 16/36에서 끊긴 판 `flake-final-before`의 8번은 세지 않는다) 1.5초 기다려 찍으면 늘 B였다. 한 페이지에서 차례로 찍으면 0~100ms는 대체로 A, 200~400ms 사이에 B로 넘어가 3200ms까지 B였다. 창을 정답 폭(496px)으로 열면 기다려도 A였지만(창 밖 띠의 가설) 곧바로 찍으면 사진마다 12번 중 1~2번 B였고, 애니메이션 프레임 둘을 기다려도 A였다.
- 글 입력과 스위치는 인자 없이 곧바로 찍든 기다려 찍든 늘 A였다. 그런데 CI에서는 그 둘도 B가 찍혔다.
- 컨테이너의 chromium은 GPU 없이 소프트웨어로 래스터한다(`SystemInfo.getInfo`의 `rasterization: disabled_software`). 크롬은 바뀐 영역만 다시 그리는 부분 래스터를 켜 두는데, 부분 래스터로 그린 타일과 타일 전체를 그린 타일이 가장자리의 중간색 픽셀에서 반올림이 갈릴 수 있다는 가설을 세웠다.
- `--disable-partial-raster`를 주자 알림은 곧바로 찍든 기다려 찍든 B, 글 입력의 올림과 스위치의 포커스도 B였다(글 입력의 포커스와 스위치의 올림은 A 그대로). 인자를 준 갈래는 찍는 때에 따라 갈리지 않았다.
- 양성 대조: CI가 올린 실제 그림 셋의 sha256이 인자를 준 갈래가 찍은 사진과 바이트까지 같았다. CI에서 흔들린 그림은 타일 전체를 그린 그림이다. 왜 그 회차에 전체를 그렸는지(기계의 부하, 타일 작업의 순서)는 재지 않았고 어림이다.

그래서 흔들림은 "포커스 링 전환을 찍는 시점"이 아니라 "부분 래스터 그림과 전체 그림 가운데 어느 쪽이 찍히느냐"였다. 찍기 전 대기는 알림만 B로 옮기고 글 입력·스위치는 A에 남겨, 다른 쪽으로 흔들릴 자리를 남긴다. 인자로 부분 래스터를 끄면 그림이 하나뿐이다. 최종 측정의 수는 `.scratch/harness/probes/README.md`의 `visual_flake/` 행이 적는다.

## 한 것

- `web/packages/ui/visual/index.ts`에 `BROWSER_ARGS`(`--disable-partial-raster`)를 두고 패키지와 위젯의 `visual/playwright.config.ts`가 `launchOptions.args`로 쓴다. 문턱(`maxDiffPixels: 0`, `threshold: 0`)은 그대로다.
- 같은 파일에 `missingBrowserArgs(browser)`를 두고, 패키지의 `storybook.visual.ts`와 위젯의 `stories.visual.ts`에 "브라우저가 사진 비교의 실행 인자를 모두 받고 떠 있다"를 하나씩 더했다.
- 정답 사진을 그 인자로 컨테이너 안에서 전부 다시 썼다. 패키지 422장 가운데 70장, 위젯 75장 가운데 6장의 픽셀이 바뀌었고 바이트만 바뀐 사진은 없었다(`changed_baselines.mjs`). 바뀐 것은 버튼·아이콘 버튼의 포커스 링(1픽셀)과 누름 바탕, 버튼 모음(`atoms-button--showcase-admin-actions`), 알림, 스위치의 포커스, 글 입력의 올림, 글 입력의 오류 아이콘, 위젯의 대화 화면이다. 오류 아이콘만 채널 차가 45(다크)·46(라이트)이었고(느낌표 획의 세로 한 줄 6픽셀) 나머지는 1~5였다.
- 프로브 `.scratch/harness/probes/visual_flake/`(CI 아티팩트 풀기, 컨테이너 안의 되풀이 찍기, 바이트 맞대기, 바뀐 정답 세기)와 변이 표 `visual_flake_mutations.toml`을 커밋했다.

## 검사

- 결정성: 인자를 켠 설정으로 정답을 `--update-snapshots=all`로 두 번 전부 다시 썼다. 두 번째 실행은 다시 쓴 사진이 0장이었고, 첫 번째 결과의 사본과 `diff -rq`로 패키지 422장, 위젯 75장이 바이트까지 같았다. 두 번째 실행의 알림 시험 넷이 30초 시간 초과로 끝나 알림만(`-g molecules-alert--`) 한 번 더 다시 써서 0장, 바이트까지 같은 것을 봤다. `--update-snapshots=all`은 바이트가 다른 사진만 다시 쓰고 알린다(첫 실행의 알림 47장이 `changed_baselines.mjs`의 수와 맞았다). 비교 모드는 pixelmatch가 안티에일리어싱으로 보는 픽셀을 빼서 흔들려도 지날 수 있어, 결정성은 이 바이트 대조로 봤다.
- 시간 초과는 그 시각의 기계 부하로 본다. 같은 실행에서 60~72번 시험이 줄줄이 느려졌고(알림 밖의 시험 포함), 첫 실행에서는 27~31번이 그랬다. 인자를 켠 비교 모드 실행에서 알림 시험은 5~7초였다. 나란히 여는 여덟 세션이 함께 돌던 때다. 인자가 CI의 시간을 늘리는지는 PR의 `visual` 잡을 main의 직전 실행과 맞대 본다.
- 변이(`visual_flake_mutations.toml`): 셋 모두 기대대로 빨강이었다. `BROWSER_ARGS`를 비우면 스위치 포커스의 사진이, 패키지와 위젯의 설정이 `args: []`를 넘기면 각자의 실행 인자 시험이 빨갰다. 표지는 손으로 변이를 넣어 실패 출력을 본 뒤 `Received` 차이 줄(`+   "--disable-partial-raster",`)로 골랐다. 시험 코드 조각에는 인자의 글자가 없다. 표의 첫 판은 위젯 대화 화면의 사진 변이를 두었는데 초록이라 어긋났다. 인자를 비운 작업 트리에서 `-g pages-widgetscreen--`로 고른 19개 시험을 세 번 더 돌려도 모두 통과해, 그 변이를 빼고 설정 변이로 바꿨다(이 PC에서 본 것이다. 기점의 CI는 인자 없이 옛 위젯 정답으로 초록이었고, 옛 정답은 새 정답과 3~21픽셀이 달라 CI의 인자 없는 그림은 이 PC의 것과 갈린다. 명세 축 리뷰가 커밋하지 않은 스크래치 스크립트로 Playwright의 비교기에 대 본 수이고 이 세션이 다시 돌려 같았다).

## 인계 (셀프 리뷰 직전)

세션 컨텍스트가 인계 문턱을 넘은 채 셀프 리뷰 직전에 와서(`hook_handoff`) 넘긴다. 이 세션의 제목은 `chore/016-visual-focus-flake`이고 넘기며 `chore/016-visual-focus-flake (인계함)`으로 바꾼다. 아무것도 커밋하지 않았다.

이 세션이 번복하거나 고친 것:

- 대기열 414와 지시문의 처방(찍기 전 대기)을 번복했다(위 "결정"과 "진단").
- 정답 다시 쓰기를 `visual:update`(`changed`)에서 `--update-snapshots=all`로 바꿨다(위 "결정"). `changed`로 한 번 다시 쓴 뒤 안티에일리어싱으로만 갈린 사진이 옛 바이트로 남은 것을 보고 바꿨다.
- 변이 표의 첫 판에 둔 위젯 대화 화면의 사진 변이가 초록이라, 그것을 빼고 실행 인자 시험(`missingBrowserArgs`)과 두 설정의 변이로 바꿨다(위 "검사"). `index.ts` 주석의 "인자를 빼면 그 사진들이 늘 빨갛다"도 그에 맞게 고쳤다.

남은 일(차례대로):

1. 셀프 리뷰(`/code-review`, 기점 `origin/main`, 티켓 `.scratch/harness/issues/016-visual-focus-flake.md`)와 반영. 미추적 파일이 많다(프로브 폴더, 변이 표, 티켓, 일지).
2. 검증 명령 전부(`CLAUDE.md`). 사진 비교 둘은 이미 이 판에서 초록이었지만 리뷰 반영 뒤에 다시 친다.
3. 커밋. 그 뒤 최종 프로브 두 판을 돈다. 고치기 전은 `--browser-args none --baseline 92b61458`, 고친 뒤는 `--browser-args config --baseline HEAD`이고, 둘 다 `--reps 4 --cases alert,textfield,switch --conditions now,wait,timeline`(이 세션이 고치기 전 판을 7/37에서 인계로 멈췄다). 출력 폴더는 저장소 밖 절대 경로로 준다. 이어 `same_bytes.mjs <CI 폴더> --baseline HEAD <두 출력 폴더>`와 `ci_diff.mjs <CI 폴더>`.
4. `.scratch/harness/probes/README.md`에 행 둘(`visual_flake/`, `visual_flake_mutations.toml`). 근거의 종류, 이미지 판(chromium headless shell 153.0.8010.12), 날짜, 결과의 수를 적는다. 변이 표의 2026-10-26 결과는 셋 모두 기대대로 빨강이다.
5. 티켓의 수용 기준 체크와 Status `done`, 대기열 414 행 닫기(`**닫힘 (.scratch/harness/issues/016-visual-focus-flake.md, …)**`).
6. PR. 본문의 바뀐 사진 목록은 `node .scratch/harness/probes/visual_flake/changed_baselines.mjs 92b61458`의 출력이다(패키지 70장, 위젯 6장). PR의 `visual` 잡에서 알림 시험의 걸린 시간을 main의 직전 실행과 맞대 본다(위 "검사"의 시간 초과). 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다.

이 세션만 아는 것: 흔들린 세 실행(`39725276747`, `39786765789`, `39941987396`)의 아티팩트를 `C:/Users/User/AppData/Local/Temp/claude/C--project-agent/8a058eeb-cbf3-4b50-930c-96c245c3b5dc/scratchpad/ci/`(r1·r2·r3)에 풀어 두었다. 없어졌으면 `gh run download <실행> -D <새 빈 폴더>`로 다시 받는다. 같은 스크래치패드에 앞선 탐색 실행의 출력(`flake-*`)과 두 번 다시 쓴 정답의 첫 사본(`ref-ui-1`, `ref-widget-1`)이 있다.

인계 지시문:

```
다음 작업: .scratch/harness/issues/016-visual-focus-flake.md. 사진 비교가 몇 픽셀 차이로 흔들리는 원인(크롬의 부분 래스터)을 재서 브라우저 실행 인자와 다시 만든 정답으로 고친다(대기열 414)
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 414를 티켓 .scratch/harness/issues/016-visual-focus-flake.md로 쓰고 한다
브랜치: chore/016-visual-focus-flake
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-26-17-visual-focus-flake.md 의 "인계 (셀프 리뷰 직전)" 절
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. 남은 단계, 멈춘 프로브, CI 아티팩트의 자리는 일지의 "인계 (셀프 리뷰 직전)" 절이다. docs/journal/2026-10-26-17-visual-focus-flake.md
확인할 선행 조건: 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다(세션에 실리는 스킬은 세션을 시작한 체크아웃의 사본이다)
이번 요청 범위: PR과 병합까지
```

넘기기: 제목을 바꿨고, 고치기 전 프로브를 멈춘 뒤 그 실행이 남긴 컨테이너(마운트 `/out`이 `flake-final-before`인 것을 보고)를 `docker stop`으로 껐다. 그 실행이 Playwright를 복사한 임시 폴더 `C:/Users/User/AppData/Local/Temp/visual-flake-nwxFqI`가 남았을 수 있다. 워크트리 잠금을 풀었다.

open-session을 부른다 2026-10-26T09:56:36Z

## 셀프 리뷰 (둘째 세션)

이어받은 세션이 `/code-review`를 돌렸다. 기점 `92b61458`, 바뀐 텍스트 파일 6과 사진 76, 커밋 0, 미추적 11. 앞 세션이 남긴 임시 폴더(`visual-flake-nwxFqI`)는 이미 없었고 사진 비교 컨테이너도 돌지 않았다.

표준 축(sonnet, high):

- Major: 코드 주석과 변이 표가 프로브를 근거로 드는데 README 행이 없다. → 고친다. 남은 단계 4이고 최종 프로브 두 판 뒤에 쓴다.
- Major: 정답을 다시 만드는 `visual:update`가 `--update-snapshots=changed`라, 이 세션이 밟은 함정(안티에일리어싱으로만 갈린 사진이 옛 바이트로 남는다)을 다음 사람이 다시 밟는다. → 남긴다. 대기열 215(사용자 승인 2026-10-13)가 그 고침(`--update`를 `all`로, 그 시험, "픽셀까지 비교" 문장, ADR 0026 이력)을 이미 든다. 이 PR은 `all`로 직접 다시 썼고, 215의 2회차로 그 행에 센다.
- Minor: "오류 아이콘만 채널 차가 45"는 다크 45, 라이트 46이다. → 고친다.
- Minor: 위젯 화면을 인자 없이 돌린 횟수가 `index.ts`는 세 번, 변이 표는 네 번이다. → 고친다. 네 번(화면 스토리 19개를 세 번, 첫 판 변이 한 번)이고 이 PC에서 손으로 돌린 것이다.
- 판단: 인과 서술이 잰 것보다 앞선다(CI의 그 회차가 왜 전체 그림을 찍었는지는 어림). → 고친다. `BROWSER_ARGS` 주석에 재지 않았다는 구절을 둔다. 프로브의 `now` 갈래가 `toHaveScreenshot`의 경로가 아니라는 지적은 남긴다. 그 갈래는 두 그림을 끌어내려는 것이고, 실제 경로의 결정성은 `toHaveScreenshot`으로 정답을 두 번 다시 쓴 바이트 대조(위 "검사")가 본다.
- Nit: `index.ts` 머리 주석이 브라우저 인자를 말하지 않는다. → 고친다.
- Nit: 두 실행 인자 시험의 본문이 같다. → 남긴다. 두 사진 비교가 각자의 설정으로 브라우저를 띄워 시험도 각자 둔다. 함수는 함께 쓴다.
- Nit: `BROWSER_ARGS`를 비우면 실행 인자 시험이 헛돈다. → 남긴다. 그 변이는 패키지의 사진이 잡고(변이 표 첫 변이), 시험이 인자의 글자를 다시 적으면 같은 사실이 두 자리에 선다.
- Nit: `run.mjs`가 `meta.json`이 없거나 명령줄이 요청한 인자와 다른 실행도 측정으로 센다. → 고친다(`.claude/rules/probes.md` 첫 항목).
- Nit: `png.mjs`의 `const path = label;` 별칭. → 고친다.

명세 축(Opus, 상속):

- Minor: "인자를 빼면 빨갛다·빼도 초록"이 이 PC에서 본 것인데 늘 그런 일처럼 적혔다. 옛 위젯 정답 6장은 새 정답과 안티에일리어싱을 빼고도 3~21픽셀이 달라, 인자 없이 옛 정답으로 초록이던 기점의 CI(`40279175497`)와 이 PC의 인자 없는 그림이 갈린다. CI r1의 실제 그림(인자 없이 찍힘)도 새 스위치 포커스 정답과 바이트까지 같다. → 고친다. `index.ts`, 위젯 시험 주석, 티켓 기준 3의 괄호, 변이 표 머리를 "이 PC에서"로 좁힌다.
- Minor: 바뀐 76장의 까닭을 재는 단계가 없다(오류 아이콘 4장과 버튼 모음 4장은 일지의 분류에도 없다). → 고친다. 커밋 뒤 인자 없이 정답을 전부 다시 써 옛 정답과 대 보는 판을 더하고, 일지의 분류에 버튼 모음을 더한다.
- Minor: 패키지 설정의 "픽셀 하나, 색 차이 하나도 허용하지 않는다"와 `web/tools/visual.ts`의 "`--update` 는 정답과 다른 사진과 없는 사진만 다시 쓴다"가 이 PR의 측정으로 거짓임이 드러난다. → 남긴다. 둘 다 대기열 215의 몫이다. 뒤의 것은 215의 `--update` 고침이 맡고, 앞의 것은 215의 문장 목록에 없어 그 행에 더한다.
- Nit: 채널 차 45·46(위와 같다), 갈린 픽셀은 알파 255라 "반투명 픽셀"이 아니다, "화면 스토리 셋…19개"의 "셋"이 개수로 읽힌다, `missingBrowserArgs` 주석의 `meta.json`은 커밋된 파일이 아니라 `run.mjs`의 출력이다, 정답 폭 창에서 곧바로 찍은 갈래(`wide`)의 B가 일지에서 빠졌다. → 모두 고친다. 앞 세션의 탐색 출력을 다시 세어 보니 `wide`는 사진마다 12번 중 1~2번 B(넷을 합쳐 48번 중 6번)였고, 인자 없이 곧바로 찍은 알림도 첫 실행(`flake-smoke`)에서 8번 중 1번 B였다. 이 둘도 고친다. 갈린 픽셀의 알파는 `ci_diff.log`의 세 짝 48픽셀 모두 255였다.

고친 것: 위 "고친다" 전부(실행 인자를 다시 재는 판과 README 행은 커밋 뒤). 남긴 것: 대기열 215의 몫 둘(갱신 모드, 설정과 도구의 문장)과 Nit 셋(시험 본문, 헛도는 변이, 프로브의 `now` 갈래), 까닭은 위 줄마다. 대기열 215 행에 2회차와 설정의 문장을 더했다.

PR 직전 리뷰에 밀 주장(반영하며 새로 쓴 문장):

- `index.ts`: "그 회차가 왜 부분 래스터를 거치지 않은 그림을 찍었는지는 재지 않았다", "이 PC 에서 인자를 빼면 스위치의 포커스 같은 사진이 빨갰다", "위젯의 화면은 이 PC 에서 인자를 빼도 사진 비교를 지났다(손으로 네 번, 변이 표 머리)", "둥근 모서리의 중간색 픽셀 몇 개(채널마다 1~3)"
- `visual_flake_mutations.toml` 머리: "CI 에서는 켠 채로도 새 정답의 그림이 찍힌 회차가 있어(흔들린 첫 실행의 실제 그림)", "`-g pages-widgetscreen--` 로 고른 19개 시험을 세 번 돌렸고 … 이 PC 에서 네 번 모두 초록이었다"
- 이 일지의 "진단"·"한 것"·"검사": "96번 중 95번. 첫 실행 `flake-smoke`에서 한 번 B", "곧바로 찍으면 사진마다 12번 중 1~2번 B", "알파는 모두 255", "채널 차가 45(다크)·46(라이트)", "옛 정답은 새 정답과 3~21픽셀이 달라"
- 티켓 Comments: "중간색으로 칠한 불투명 픽셀(알파 255)"
- `run.mjs` 머리와 표지: 명령줄이 없거나 요청과 다르면 결과 전부를 측정 아님으로 센다. `config`는 패키지 설정의 `BROWSER_ARGS`가 그 인자를 든다고 본다
- 대기열 215: 2회차와 설정의 문장

반영 뒤 검증: ruff 둘 초록. `tools/run_checks.py`는 pytest 하나로 빨갰다(1 failed, 5589 passed, 536.07초. 나머지 아홉 검사는 통과, web-verify 520.0초). 빨간 것은 `tests/tools/test_probe_kit.py::test_배출은_줄이_계속_와도_제한_시간에_끝난다`이고 자식 파이썬이 `drain(0.5)` 안에 한 줄도 내지 못해 `assert lines`가 빈 목록이었다. 이 브랜치는 파이썬을 건드리지 않았다. 같은 시험이 같은 꼴로 빨간 것은 일지 2026-10-22-21, 2026-10-23-14, 2026-10-23-27에 이어 넷째이고 대기열에 행이 없다. 회고 후보로 둔다. 그 시험만 단독으로 치자 1 passed였다(209.97초). `pnpm -C web visual`은 108 passed, 1 failed(17.6분)였고, 빨간 것은 `molecules-textfield--single`의 사진 시험이 `page.goto`에서 30초 시간 초과로 끝난 것이다(사진 차이가 아니다). 그 시험만 `-g`로 다시 치자 1 passed(5.8초)였다. `pnpm -C web visual:widget`은 43 passed(2.0분)였다. 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다. 위젯 e2e와 `-m llm_widget`은 치지 않았다. 바꾼 것은 위젯의 사진 비교 설정과 정답이고 위젯 앱·api-client·서버 경로는 아니다.

커밋 `90a89c13`(`chore: 사진 비교가 부분 래스터를 끄고 그 인자로 다시 만든 정답과 맞댄다 (harness 016)`, 95 files). pre-commit은 모두 통과했다(pytest 457.0초, web-verify 466.5초, 변이 표·마크다운 표·줄 구분 문자·인용·커밋 메시지 통과). ruff 둘은 `.py`가 없어 Skipped였고 위에서 손으로 친 결과가 초록이다.

## 인계 (커밋 뒤)

세션 컨텍스트가 인계 문턱을 넘은 채 커밋 뒤에 와서(`hook_handoff`) 넘긴다. 이 세션의 제목은 `chore/016-visual-focus-flake`이고 넘기며 `chore/016-visual-focus-flake (인계함)`으로 바꾼다. 푸시하지 않았고 PR은 없다.

이 세션이 번복하거나 고친 것: 위 "셀프 리뷰 (둘째 세션)"의 "고친다" 전부. 앞 세션의 일지 서술 가운데 "곧바로 찍으면 늘 A"(96번 중 95번이었다), "정답 폭으로 열면 기다려도 A"(곧바로 찍으면 사진마다 12번 중 1~2번 B였다), "반투명 픽셀"(알파 255였다), "채널 차가 45"(45·46)를 고쳤다. 인계 지시문의 남은 일 3에 바뀐 76장의 까닭을 재는 판(아래 1)을 더했다.

남은 일(차례대로):

1. 바뀐 정답의 까닭 재기(명세 축 Minor). 두 설정(`web/packages/ui/visual/playwright.config.ts`, `web/apps/widget/visual/playwright.config.ts`)의 `launchOptions: { args: [...BROWSER_ARGS] },`를 Edit로 `launchOptions: { args: [] },`로 바꾸고, `pnpm -C web visual --update-snapshots=all`과 `pnpm -C web visual:widget --update-snapshots=all`을 차례로 백그라운드로 쳐 출력을 저장소 밖 파일 둘에 받는다(이 세션의 비교 모드 실행은 패키지 17.6분, 위젯 2.0분이었다). 두 정답 폴더를 저장소 밖 폴더 `<그림 폴더>/web/packages/ui/visual/snapshots`, `<그림 폴더>/web/apps/widget/visual/snapshots`로 복사하고, `git checkout -- web/packages/ui/visual web/apps/widget/visual`로 되돌린 뒤 `git status`가 깨끗한지 본다. 그다음 `node .scratch/harness/probes/visual_flake/attribution.mjs 92b61458 90a89c13 <그림 폴더> <패키지 기록> <위젯 기록>`. 각 기록에서 실패는 실행 인자 시험 하나여야 하고(그것이 인자 없이 떴다는 표지다), 시간 초과가 섞이면 그 기록이 측정 아님이 되니 그 판을 다시 돈다. 결과의 세 갈래 수를 PR 본문의 "까닭"과 README 행에 적는다.
2. 최종 프로브 두 판(앞 세션이 고치기 전 판을 7/37에서 멈췄다). 1에서 설정을 되돌린 뒤에 돈다. 정적 빌드가 있어야 한다(`pnpm -C web visual`이 짓는다). 고치기 전은 `node .scratch/harness/probes/visual_flake/run.mjs --out <저장소 밖 절대 경로 A> --browser-args none --baseline 92b61458 --reps 4 --cases alert,textfield,switch --conditions now,wait,timeline`, 고친 뒤는 `--out <B> --browser-args config --baseline 90a89c13`에 나머지 같은 인자. 러너는 이제 명령줄이 요청과 다르면 측정 아님으로 센다(`argsMatched`). 이어 `node .scratch/harness/probes/visual_flake/same_bytes.mjs <CI 폴더> --baseline 90a89c13 <A> <B>`와 `node .scratch/harness/probes/visual_flake/ci_diff.mjs <CI 폴더>`.
3. `.scratch/harness/probes/README.md`에 행 둘(`visual_flake/`, `visual_flake_mutations.toml`). 표의 열은 파일, 재는 것, 근거로 드는 자리, 다시 돌 때다. 근거의 종류, 이미지 판(chromium headless shell 153.0.8010.12), 날짜, 결과의 수(1과 2, 앞 세션의 탐색 실행 수는 위 "진단")를 적는다. 변이 표의 2026-10-26 결과는 셋 모두 기대대로 빨강이다. `visual_flake/`의 파일은 `ci_diff.mjs`, `png.mjs`, `run.mjs`·`probe.config.mts`·`flake.probe.mts`, `same_bytes.mjs`, `changed_baselines.mjs`, `attribution.mjs`, `sizes.mjs`(창보다 큰 정답 사진을 센다)다.
4. 티켓의 수용 기준 체크와 Status `done`, 대기열 414 행 닫기(`**닫힘 (.scratch/harness/issues/016-visual-focus-flake.md, …)**`).
5. 둘째 커밋. 커밋 전에 `git branch --show-current`와 `uv run python tools/sibling_overlap.py`(이 세션이 볼 때 일지 08~10을 쓴 형제가 넷 있었다. 먼저 병합되면 이 일지 번호를 옮긴다).
6. 푸시와 PR. 본문의 바뀐 사진 목록은 `node .scratch/harness/probes/visual_flake/changed_baselines.mjs 92b61458`의 출력(패키지 70장, 위젯 6장)이고 까닭은 1의 결과다. PR 직전 리뷰(`docs/constitution/operations.md` 리뷰 파이프라인 2)의 브리프에 위 "PR 직전 리뷰에 밀 주장"을 나열한다. PR의 `visual` 잡에서 두 사진 비교 단계의 걸린 시간을 main의 직전 실행(`40279175497`: 패키지 3분 18초, 위젯 53초)과 맞대 본다.
7. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다.

이 세션만 아는 것: 흔들린 세 실행의 아티팩트는 여전히 `C:/Users/User/AppData/Local/Temp/claude/C--project-agent/8a058eeb-cbf3-4b50-930c-96c245c3b5dc/scratchpad/ci/`(r1·r2·r3)에 있다. 앞 세션의 탐색 출력(`flake-*`)도 같은 스크래치패드에 있고, 갈래별 수는 이 세션의 `C:/Users/User/AppData/Local/Temp/claude/C--project-agent/f519b5fe-5550-4ba7-8295-b168cb61137a/scratchpad/wide_counts.cjs <그 스크래치패드>`가 찍는다. 명세 축이 옛·새 정답을 Playwright 비교기로 대 본 스크립트는 같은 스크래치패드의 `aa_check.cjs`다. 회고 후보: `test_probe_kit.py`의 배출 시험 흔들림 넷째(위 "반영 뒤 검증"), 대기열 215 2회차(행에 셌다).

인계 지시문:

```
다음 작업: .scratch/harness/issues/016-visual-focus-flake.md. 사진 비교가 몇 픽셀 차이로 흔들리는 원인(크롬의 부분 래스터)을 재서 브라우저 실행 인자와 다시 만든 정답으로 고친다(대기열 414)
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 414를 티켓 .scratch/harness/issues/016-visual-focus-flake.md로 쓰고 한다
브랜치: chore/016-visual-focus-flake
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-26-17-visual-focus-flake.md 의 "셀프 리뷰 (둘째 세션)" 절과 "인계 (커밋 뒤)" 절
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰를 반영해 90a89c13으로 커밋했고 푸시와 PR은 아직이다. 남은 단계(바뀐 정답의 까닭 재기, 최종 프로브 두 판, 프로브 README 행, 티켓과 대기열 닫기, 둘째 커밋, PR, 병합)와 CI 아티팩트의 자리는 일지의 "인계 (커밋 뒤)" 절이다. docs/journal/2026-10-26-17-visual-focus-flake.md
확인할 선행 조건: 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다(세션에 실리는 스킬은 세션을 시작한 체크아웃의 사본이다)
이번 요청 범위: PR과 병합까지
```

넘기기: 제목을 `chore/016-visual-focus-flake (인계함)`으로 바꿨다. 도는 백그라운드 작업은 없었다(리뷰 서브에이전트 둘과 검증·커밋 명령은 모두 끝났다). 워크트리 잠금은 이미 풀려 있었다(`is not locked`).

open-session을 부른다 2026-10-26T11:28:16Z

## 셋째 세션

제목을 `chore/016-visual-focus-flake`로 바꾸고 `git worktree list`에서 찾은 이 워크트리에 EnterWorktree(path)로 들어왔다. 그사이 origin/main이 `9805a5a7`(#389, harness 013, 파이썬 쪽)로 한 커밋 움직였다.

### 바뀐 정답의 까닭

두 설정의 `launchOptions`를 `{ args: [] }`로 바꾸고 `pnpm -C web visual --update-snapshots=all`(108 passed, 1 failed, 9.2분)과 `pnpm -C web visual:widget --update-snapshots=all`(42 passed, 1 failed, 1.4분)을 차례로 쳤다. 두 기록 모두 실패는 실행 인자 시험 하나이고 그 Received 차이 줄이 `+   "--disable-partial-raster",`였다(브라우저가 인자 없이 떴다는 표지). 시간 초과는 없었다. 두 정답 폴더를 저장소 밖에 복사하고 `git checkout -- web/packages/ui/visual web/apps/widget/visual`로 되돌렸다. `git status`에는 이 일지만 남았다.

`attribution.mjs 92b61458 90a89c13 <그림 폴더> <두 기록>`(종료 0, 측정 아님 0): 바뀐 76장이 모두 "옛 정답과 같다"였다(새 정답과 같다 0, 둘 다 아니다 0). 바뀌지 않은 정답과 인자 없는 그림이 다른 사진도 0이었다. 그래서 76장은 이 PC에서 인자가 그 그림을 바꾼 것이고, 인자 밖의 까닭으로 바뀐 사진은 없다.

이 판에서 위젯 화면 6장도 인자 없이 옛 정답의 그림으로 찍혔다. 앞 세션이 `index.ts` 주석에 적은 "위젯의 화면은 이 PC 에서 인자를 빼도 사진 비교를 지났다(손으로 네 번, 변이 표 머리)"와 어긋난다. 그 네 번은 `BROWSER_ARGS`를 비운 뒤 `-g pages-widgetscreen--`로 화면 시험만 골라 돌린 판이라 실행 인자 시험이 돌지 않았고, 브라우저가 인자 없이 떴는지 보는 표지가 없었다. 가르려고 위젯 설정만 `args: []`로 바꿔 비교 모드를 두 번 돌렸다. 두 번 모두 42 passed, 1 failed(2.4분, 2.9분)였고 실패는 실행 인자 시험 하나였다. 표지가 있는 판에서도 화면 시험 19개(정답 35장)는 정답과 맞았다. 그 뒤 설정을 `git checkout`으로 되돌렸다.

두 모드가 갈린 까닭은 Playwright의 반복에 있다고 본다. 설치본 1.63.0의 `toHaveScreenshot`은 `all` 모드에서 정답을 넘기지 않고(`expectScreenshotOptions.expected = helper.updateSnapshots === "all" ? void 0 : expected`), 서버 쪽 `expectScreenshot`은 정답이 있으면 첫 사진을 정답과 맞대 같으면 곧바로 끝내고, 첫 사진이 다르거나 정답이 없으면 잇단 두 사진이 같을 때까지 0·100·250·500ms, 그 뒤로는 1000ms씩 쉬며 찍고, 정답이 있으면 그 안정된 사진을 다시 정답과 맞댄다(`playwright/lib/matchers/expect.js`, `playwright-core/lib/coreBundle.js`를 읽었다). 그래서 인자 없는 위젯은 첫 사진이 새 정답의 그림이라 비교를 지나고, 안정된 사진은 옛 그림이라 다시 쓰는 판에 옛 그림이 남았다고 어림한다. 첫 사진이 달랐다면 안정된 옛 그림을 새 정답과 맞대 빨갰을 것이다. 사진의 차례는 재지 않았다. 고친 것: 변이 표 머리의 위젯 문장을 표지가 있는 두 번으로 바꿨다. `index.ts` 주석의 "손으로 네 번"은 최종 프로브가 그 파일을 들이는 설정을 읽는 동안이라 프로브 뒤에 고친다.

### 최종 프로브

`run.mjs --reps 4 --cases alert,textfield,switch --conditions now,wait,timeline`을 두 판 돌렸다. 둘 다 결과 줄 36/36, `argsMatched` 참, 종료 0이었다.

- 고치기 전(`--browser-args none --baseline 92b61458`, 662초, 부분 래스터 끔 false): 알림 `now` A 15·B 1, `wait` A 0·B 16, `timeline` 0ms 16·0, 100ms 12·4, 200ms 11·5, 400ms 0·16, 800ms 1·15, 1600ms·3200ms 0·16. 글 입력과 스위치는 올림·포커스 모두 모든 갈래·시각에서 A 16·B 0.
- 고친 뒤(`--browser-args config --baseline 90a89c13`, 590초, 부분 래스터 끔 true): 세 사례의 모든 갈래·시각에서 B 0(사진 720장). `meta.json`의 명령줄에 `--disable-partial-raster`가 낱말 하나로 있었다.
- `same_bytes.mjs <CI 폴더> --baseline 90a89c13 <두 판>`(종료 0): CI의 실제 그림 셋이 모두 새 정답과 바이트까지 같았고, 고친 뒤 판의 같은 사진 36장씩과도 같았다. 알림의 실제 그림은 고치기 전 판의 B 21장과도 같았다.
- `ci_diff.mjs <CI 폴더>`(종료 0): 세 짝 모두 측정이었다(스위치 2, 글 입력 29, 알림 17픽셀. 일지 "진단"과 같다).

그 뒤 `index.ts` 주석을 "실행 인자 시험이 빨간 판으로 두 번"으로 고치고, 프로브 README에 행 둘을 더하고, 티켓 기준 1~7을 체크하고 대기열 414를 닫았다. 기준 8은 고친 설정으로 두 사진 비교를 다시 돌려 본다.

## 인계 (셀프 리뷰 직전, 셋째 세션)

셋째 세션이 커밋하지 않은 변경에 셀프 리뷰(`/code-review`, 기점 `90a89c13`)를 부르자 세션 컨텍스트가 인계 문턱을 넘은 채 `셀프 리뷰 직전`에 와서(`hook_handoff`) 넘긴다. 이 세션의 제목은 `chore/016-visual-focus-flake`이고 넘기며 `chore/016-visual-focus-flake (인계함)`으로 바꾼다. 셀프 리뷰의 단계는 밟지 않았다(서브에이전트를 띄우지 않았다).

이 세션이 번복하거나 고친 것: 앞 세션의 "위젯의 화면은 이 PC 에서 인자를 빼도 사진 비교를 지났다(손으로 네 번, 변이 표 머리)"는 실행 인자 시험이 돌지 않아 표지가 없던 판이었다. 표지가 있는 두 판으로 다시 세어 `index.ts` 주석과 변이 표 머리를 고쳤다(위 "바뀐 정답의 까닭"). 결론(위젯은 비교 모드로는 인자 없이도 지난다)은 그대로다.

커밋하지 않은 변경(셀프 리뷰의 범위, `git diff 90a89c13`과 미추적 0):

- `web/packages/ui/visual/index.ts`: `BROWSER_ARGS` 주석의 "손으로 네 번"을 "실행 인자 시험이 빨간 판으로 두 번"으로.
- `.scratch/harness/probes/visual_flake_mutations.toml`: 머리의 위젯 문장을 표지가 있는 두 판으로.
- `.scratch/harness/probes/README.md`: 행 둘(`visual_flake/`, `visual_flake_mutations.toml`).
- `.scratch/harness/issues/016-visual-focus-flake.md`: 기준 1~7 체크, Comments에 바뀐 정답의 까닭. 기준 8과 Status는 그대로(in-progress).
- `.scratch/retro-queue.md`: 414 행 닫기.
- 이 일지의 "셋째 세션" 절.

셀프 리뷰에 밀 주장(이 세션이 새로 쓴 사실 문장. 나열 밖도 잰다): README 두 행의 수 전부(최종 프로브의 A:B, 사진 720장, `same_bytes`의 36장·57장 가운데 B 21장, `ci_diff`의 2·29·17, `attribution`의 76·0·0, `changed_baselines`의 76·70·6, `sizes`의 12·14, 탐색 실행의 96번 중 95번·48번 중 6번), "인자를 준 그림이 타일 전체를 그린 그림이라는 것은 인자의 이름에서 읽은 어림이다", 변이 표 머리의 "두 번 모두 실행 인자 시험만 빨갛고 … 화면 사진 19개는 이 PC에서 초록이었다", 티켓 Comments의 "기준 3의 괄호가 말하는 '인자를 빼도 초록'은 비교 모드의 일이다", 대기열 414 닫힘 문장, Playwright 1.63.0의 두 모드에 대한 서술(`expect.js`의 `expectScreenshotOptions.expected = helper.updateSnapshots === "all" ? void 0 : expected`와 `coreBundle.js`의 `expectScreenshot`).

남은 일(차례대로):

1. 셀프 리뷰(`/code-review`, 기점 `90a89c13`, 티켓 `.scratch/harness/issues/016-visual-focus-flake.md`)와 반영.
2. 두 사진 비교를 고친 설정 그대로 다시 친다(`pnpm -C web visual`, `pnpm -C web visual:widget`). 이 세션이 띄운 판은 18/109에서 인계로 멈췄다. 초록이면 티켓 기준 8을 체크하고 Status를 `done`으로. 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다.
3. 둘째 커밋. 커밋 전에 `git branch --show-current`와 `uv run python tools/sibling_overlap.py`. origin/main은 `9805a5a7`(#389)로 움직였다.
4. origin/main을 합치고 PR 직전 리뷰. CodeRabbit CLI는 좌석이 없어(`coderabbit auth status`의 `Seat: not assigned`, 이 세션이 봤다) 대체 둘(`/security-review`, `bug-perf-review`)이고, 그 브리프에 앞 세션의 "PR 직전 리뷰에 밀 주장"(위 "셀프 리뷰 (둘째 세션)")과 이 절의 주장, 1의 반영으로 새로 쓴 문장을 나열한다.
5. 푸시와 PR. 본문의 바뀐 사진 목록은 `node .scratch/harness/probes/visual_flake/changed_baselines.mjs 92b61458 90a89c13`의 출력(패키지 70장, 위젯 6장)이고, 까닭은 위 "바뀐 정답의 까닭"이다. PR의 `visual` 잡에서 두 사진 비교 단계의 걸린 시간을 main의 직전 실행(`40279175497`: 패키지 3분 18초, 위젯 53초)과 맞대 본다.
6. 이 단계를 닫는 회고(`retro`)와 일지 "다음"을 병합 전에 푸시하고, 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다.

이 세션만 아는 것: 저장소 밖의 출력은 이 세션 스크래치패드 `C:/Users/User/AppData/Local/Temp/claude/C--project-agent/53f51b7a-3211-4ade-b04c-2648496cf52c/scratchpad/`에 있다. 인자 없이 다시 쓴 그림 `renders-noargs/`와 그 기록 `attr-ui.log`·`attr-widget.log`, 인자 없는 위젯 비교 `widget-noargs-1.log`·`widget-noargs-2.log`, 최종 프로브 `final-before/`·`final-after/`와 기록, 사례별 합을 찍는 `agg.cjs <run.mjs 출력 폴더>…`. 흔들린 세 실행의 CI 아티팩트는 여전히 `C:/Users/User/AppData/Local/Temp/claude/C--project-agent/8a058eeb-cbf3-4b50-930c-96c245c3b5dc/scratchpad/ci/`(r1·r2·r3)다. 회고 후보(앞 세션 것에 더해): 표지 없는 수동 판의 결과가 주석·변이 표의 근거 문장으로 들어갔다가 표지 있는 판에서 어긋났다(probes 규칙 첫 항목의 수동 판 갈래).

인계 지시문:

```
다음 작업: .scratch/harness/issues/016-visual-focus-flake.md. 사진 비교가 몇 픽셀 차이로 흔들리는 원인(크롬의 부분 래스터)을 재서 브라우저 실행 인자와 다시 만든 정답으로 고친다(대기열 414)
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 414를 티켓 .scratch/harness/issues/016-visual-focus-flake.md로 쓰고 한다
브랜치: chore/016-visual-focus-flake
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-26-17-visual-focus-flake.md 의 "셋째 세션" 절과 "인계 (셀프 리뷰 직전, 셋째 세션)" 절
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경(바뀐 정답의 까닭 재기와 최종 프로브 두 판의 결과, 프로브 README 행 둘, 티켓 기준 1~7, 대기열 414 닫기)이 워크트리에 있고 셀프 리뷰(/code-review, 기점 90a89c13)부터 한다. 남은 단계(두 사진 비교 다시 치기, 둘째 커밋, PR 직전 리뷰, PR, 회고, 병합)와 저장소 밖 출력의 자리는 일지의 "인계 (셀프 리뷰 직전, 셋째 세션)" 절이다. docs/journal/2026-10-26-17-visual-focus-flake.md
확인할 선행 조건: 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다(세션에 실리는 스킬은 세션을 시작한 체크아웃의 사본이다)
이번 요청 범위: PR과 병합까지
```

넘기기: 제목을 `chore/016-visual-focus-flake (인계함)`으로 바꿨다. 두 사진 비교를 다시 치던 백그라운드 작업을 TaskStop으로 멈추고, 그 실행이 남긴 컨테이너(마운트 `/web`이 이 워크트리의 `web`인 것을 보고)를 `docker stop`으로 껐다. 그 실행의 임시 폴더(`agent-os-visual-NihL9s`)는 남지 않았다. 워크트리 잠금은 이미 풀려 있었다(`is not locked`).

open-session을 부른다 2026-10-26T12:35:46Z

## 넷째 세션

제목을 `chore/016-visual-focus-flake`로 바꾸고 `git worktree list`에서 찾은 이 워크트리에 EnterWorktree(path)로 들어왔다. origin/main은 그사이 `3acbd867`(#388, harness 011. `.claude/rules/probes.md` 첫 항목, `tools/mutate.py`, 프로브 README, 대기열을 건드렸다)까지 움직였다.

### 셀프 리뷰 (넷째 세션)

`/code-review`, 기점 `90a89c13`, 바뀐 파일 6, 커밋 0, 미추적 0. 리뷰가 도는 동안 두 사진 비교를 고친 설정 그대로 백그라운드로 다시 쳤다(반영이 동작을 바꾸면 다시 친다).

표준 축(sonnet, high). 밀 주장의 수는 앞 세션의 저장소 밖 출력으로 모두 대 보아 맞았다(최종 프로브의 A:B와 720장, `same_bytes`의 36장·21장, `ci_diff`, `changed_baselines`, `attribution`, `sizes`, 두 기록, 위젯 비교 모드 두 번, 탐색 실행의 96번 중 95번·48번 중 6번).

- Minor: 티켓 기준 4가 체크됐는데 PR 본문은 아직 없다. → 고친다. 체크를 풀고, PR 본문을 파일로 쓴 뒤 커밋 전에 다시 체크한다.
- Minor: README 변이 행의 "비교 모드는 첫 사진이 정답과 같으면 곧바로 지나고"는 반쪽이다. 첫 사진이 다르면 잇단 두 사진이 같아질 때까지 찍고 그 사진을 정답과 맞댄다(`coreBundle.js` 22787~22806행을 이 세션이 열어 봤다). → 고친다. README 행과 이 일지 "셋째 세션"의 같은 문장에 그 갈래를 더한다.
- Minor: 위젯 비교 모드 두 번이 손으로 친 판이라는 것이 `index.ts` 주석, 변이 표 머리, 티켓 Comments에서 빠졌다(`docs/agents/issue-tracker.md` 프로브와 근거). → 고친다.
- Minor: README의 `ci_diff` 줄이 표지를 최종형으로만 적고, 첫 판의 기준(N과 디코더 수를 바로 맞대 셋 다 어긋났다)과 바꾼 까닭이 없다(같은 절 셋째 항목). → 고친다.
- Nit: 대기열 414 닫힘 문장의 "원인은 크롬의 부분 래스터였고"가 재지 않은 부분(그 회차가 왜 끈 그림을 찍었는지)까지 단정한다. → 고친다. 잰 것(인자를 주면 그림이 하나다, CI의 그림이 끈 그림과 같다)과 재지 않은 것을 나눠 적는다.
- Nit: origin/main의 #388이 변이 도구에 "시험 원문의 표지" 알림을 더했다. → 합친 뒤 `visual_flake_mutations.toml`의 표지가 그 알림에 걸리는지 본다.

명세 축(Opus, 상속). 밀 주장의 수는 원본으로 다시 셌고 아래 말고는 맞았다.

- Minor: 기준 4의 체크가 앞당겨졌다(표준 축과 같다). → 고친다(위).
- Minor: "화면 사진 19개"의 19는 시험 수이고 그 정답은 35장이다(`widget-noargs-1.log`·`-2.log`의 `✓ … pages-widgetscreen--` 줄 19개씩, `web/apps/widget/visual/snapshots/`의 `pages-widgetscreen--*` 35장. 이 세션이 `grep -c`와 `ls`로 다시 셌다). → 고친다. 변이 표 머리, README 변이 행, 이 일지 "셋째 세션"을 "화면 시험 19개(정답 35장)"로.
- Nit: 비교 모드 서술의 빠진 갈래(표준 축과 같다)와, 어림이 그 갈래에서도 서는 까닭(첫 사진이 달랐다면 안정된 옛 그림을 맞대 빨갰을 것이다), 0·100·250·500ms 뒤의 1000ms. → 고친다.
- Nit: 탐색 실행의 "96번 중 95번"에 결과 줄이 16/36에서 끊긴 판(`flake-final-before`)의 8번이 들었다. 빼면 88번 중 87번이다(이 세션이 서브에이전트의 스크래치 스크립트 `agg2.cjs`를 읽고 앞 세션의 탐색 출력에 돌려 다시 셌다: `flake-alert1` 48, `flake-alert3` 32, `flake-smoke` 8 가운데 B 1, `flake-final-before` 8). → 고친다. README와 이 일지 "진단".
- Nit: 이 일지 "셋째 세션"과 그 인계 절이 옮긴 옛 주석 문장이 원문(`90a89c13`의 `index.ts`)과 글자가 다르다. → 고친다. 원문 그대로 옮긴다.
- Nit: 티켓 본문의 "(바뀐 자리만 다시 그리는 그림이 시점에 따라 갈린다)"가 어림인 기전을 사실처럼 쓰고, README의 "고친 뒤의 최종 판 둘"이 두 판 모두 고친 판처럼 읽힌다. → 고친다. 티켓은 잰 것(두 그림 가운데 하나로 찍혔고 알림은 시점에 따라 갈렸다, 끄면 하나였다)으로, README는 "최종 판 둘(고치기 전과 고친 뒤, …)"로.

고친 것: 두 축의 지적 전부(위 "고친다"). 표준 축 Nit의 #388 확인은 코드로 했다. origin/main의 `tools/mutate.py`의 `_echo_problems`는 변이의 `tests` 인자 가운데 `-`로 시작하지 않는 것을 러너 자리 기준의 파일 경로로 읽고 읽지 못하면 넘는다. 이 표의 인자는 `-g`와 시험 이름 조각이라 파일로 읽히지 않아 알림에 걸리지 않는다(코드를 읽었다. 합친 뒤 그 도구의 `--check`로 이 표를 골라 실제로 넘는지 본다).

커밋 첫 시도는 pre-commit의 pytest가 2 failed, 5588 passed(929.4초)로 막았다. 빨간 둘은 `tests/adapters/test_filesystem.py::test_다른_프로세스가_운영자_파일을_연_채여도_교체가_재시도_안에서_성공한다`(교체가 `PermissionError`로 재시도 안에 끝나지 못했다)와 `tests/tools/test_rerun_runner.py::test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다`(`board.run()`이 1)이고, 이 브랜치는 파이썬을 건드리지 않았다. 둘만 따로 치자 2 passed(40.7초)였다. 앞 시도의 pytest가 457초였던 것의 두 배라 다른 세션들이 함께 돈 부하로 본다(어림). 앞의 것은 프로브 README의 `mutate_no_grandchild_bound` 행이 pytest 부하 아래에서 빨간 것을 이미 적었다. 회고 후보로 둔다. 같은 커밋을 다시 쳤다. 다시 돌린 명령: 리뷰가 도는 동안 친 두 사진 비교가 고친 설정 그대로 초록이었다(`pnpm -C web visual` 109 passed 12.2분, `pnpm -C web visual:widget` 43 passed 2.5분). 반영은 주석과 기록 문장뿐이라(`index.ts`는 주석 한 문장) 그 결과로 티켓 기준 8의 사진 비교 몫을 본다. 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다.

PR 직전 리뷰에 밀 주장(반영하며 새로 쓴 문장):

- `index.ts`: "손으로 친 두 판이고 두 판 모두 실행 인자 시험이 빨갰다"
- 변이 표 머리: "을 손으로 두 번 돌렸는데 … 화면 시험 19개(정답 35장)는 이 PC 에서 초록이었다"
- 티켓: "(인자 없이는 같은 코드의 사진이 두 그림 가운데 하나로 찍혔고 알림은 찍는 시점에 따라 갈렸다. 부분 래스터를 끄면 그림이 하나였다)", Comments의 "손으로 친 두 판이고 두 판 모두 실행 인자 시험이 빨갰다"
- README `visual_flake/` 행: "첫 판은 N과 디코더가 센 수를 바로 맞댔는데 세 짝 모두 디코더 쪽이 많아(1·2, 3·29, 6·17)", "88번 중 87번 A(결과 줄이 16/36에서 끊긴 판의 8번은 세지 않았다)", "최종 판 둘(고치기 전과 고친 뒤, …)"
- README 변이 행: "화면 시험 19개(정답 35장)", "다르면 잇단 두 사진이 같아질 때까지 찍어 그 사진을 정답과 맞댄다. `all` 모드는 정답 없이 잇단 두 사진이 같을 때까지 찍는다. 같은 위젯 설정에서 안정된 사진은 옛 그림이었으므로(`all` 판), 비교 모드가 지난 것은 첫 사진이 새 정답의 그림이었기 때문으로 어림한다"
- 대기열 414: "인자로 부분 래스터를 끄면 찍는 때와 상관없이 그림이 하나였고, CI의 실패한 그림 셋이 끈 그림과 바이트까지 같았다(그 회차가 왜 끈 그림을 찍었는지는 재지 않았다)"
- 이 일지 "셋째 세션": "첫 사진이 다르거나 정답이 없으면 잇단 두 사진이 같을 때까지 0·100·250·500ms, 그 뒤로는 1000ms씩 쉬며 찍고, 정답이 있으면 그 안정된 사진을 다시 정답과 맞댄다", "첫 사진이 달랐다면 안정된 옛 그림을 새 정답과 맞대 빨갰을 것이다"

다시 친 커밋 `5f25f59b`(`chore: 바뀐 정답의 까닭과 최종 프로브를 적고 티켓을 닫는다 (harness 016)`, 7 files)의 pre-commit은 모두 통과했다(pytest 812.2초, web-verify 736.0초, run-hooks 274.2초, 변이 표·마크다운 표·줄 구분 문자·인용·커밋 메시지·check-ticket 통과). ruff 둘은 `.py`가 없어 Skipped였고 커밋 전에 손으로 친 결과가 초록이다(`All checks passed!`, `1054 files already formatted`).

## 인계 (커밋 뒤, 넷째 세션)

세션 컨텍스트가 인계 문턱을 넘은 채 `커밋 뒤`에 와서(`hook_handoff`) 넘긴다. 이 세션의 제목은 `chore/016-visual-focus-flake`이고 넘기며 `chore/016-visual-focus-flake (인계함)`으로 바꾼다. 푸시하지 않았고 PR은 없다.

이 세션이 번복하거나 고친 것: 위 "셀프 리뷰 (넷째 세션)"의 "고친다" 전부. 앞 세션들의 서술 가운데 "화면 사진 19개"(시험 19개, 정답 35장), "96번 중 95번"(끊긴 판을 빼면 88번 중 87번), 비교 모드의 반쪽 서술(첫 사진이 다를 때의 갈래), 옛 주석 문장의 인용(원문과 글자가 달랐다), 티켓 본문의 기전 서술을 고쳤다. 티켓 기준 4의 체크를 풀었다가 PR 본문의 초안(아래)을 쓴 뒤 다시 체크했다. 일지 번호를 `2026-10-26-07`에서 `2026-10-26-17`로 옮겼다(`sibling_overlap.py --move`).

남은 일(차례대로):

1. origin/main을 합친다(`git fetch origin`, `git merge origin/main`). 이 세션이 볼 때 origin/main은 `71433a0d`(#356)였고, `.scratch/harness/probes/README.md`와 `.scratch/retro-queue.md`를 함께 고쳐 글자 충돌 후보다. 합친 뒤 `PYTHONUTF8=1 uv run python tools/mutate.py --check .scratch/harness/probes/visual_flake_mutations.toml`에 이 표의 변이 이름을 골라, #388이 더한 "시험 원문의 표지" 알림에 걸리지 않는지 본다(코드로는 걸리지 않는다고 읽었다, 위 "셀프 리뷰 (넷째 세션)"의 고친 것 줄). 합친 뒤에도 `uv run python tools/sibling_overlap.py`를 친다.
2. PR 직전 리뷰(`docs/constitution/operations.md` 리뷰 파이프라인 2). `coderabbit auth status`로 좌석을 보고, 없으면 대체 둘(`/security-review`, `bug-perf-review` 서브에이전트)이다. `bug-perf-review`의 브리프에 밀 주장은 "셀프 리뷰 (둘째 세션)"의 "PR 직전 리뷰에 밀 주장", "인계 (셀프 리뷰 직전, 셋째 세션)"의 "셀프 리뷰에 밀 주장", 위 "셀프 리뷰 (넷째 세션)"의 "PR 직전 리뷰에 밀 주장"이다.
3. PR 본문을 채우고 푸시와 PR. 제목은 첫 커밋과 같은 `chore: 사진 비교가 부분 래스터를 끄고 그 인자로 다시 만든 정답과 맞댄다 (harness 016)`. 본문 초안은 저장소 밖(아래)에 있고 자리표 셋이 남았다. `CHECKLIST`(템플릿의 체크리스트 줄에 커밋 `5f25f59b`의 pre-commit 결과, 손으로 친 ruff 둘, `-m llm`·`-m llm_widget`·e2e를 치지 않은 까닭(파이썬과 위젯 앱·api-client·서버 경로를 건드리지 않았다), 셀프 리뷰, 2의 결과), `VERIFY_NOTES`(두 사진 비교가 고친 설정으로 초록이었다: `pnpm -C web visual` 109 passed 12.2분, `pnpm -C web visual:widget` 43 passed 2.5분. 그 뒤의 변경은 주석·기록 문장뿐이다), `CI_TIMING`(PR의 `visual` 잡의 두 단계 걸린 시간을 main의 직전 실행 `40279175497`의 패키지 3분 18초, 위젯 53초와 맞댄 결과. CI 뒤에 `gh pr edit`로 채운다). 채우기는 `node <스크래치패드>/fill.cjs <본문> <자리표> <내용 파일 또는 -문자열>`. PR을 연 뒤 next-session 순서 1의 2(봇 회차)대로 한다.
4. 이 단계를 닫는 회고(`retro`)와 일지 "다음"을 병합 전에 푸시하고, 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다. 회고 후보(앞 세션들 것에 더해): pre-commit의 pytest에서 이 브랜치가 건드리지 않은 시험 둘이 부하로 빨갰다(위 첫 시도 줄. `test_filesystem.py`의 교체 재시도 시험은 프로브 README의 `mutate_no_grandchild_bound` 행이 부하 아래에서 빨간 것을 이미 적었고, `test_rerun_runner.py`의 오염 시험은 이 세션이 처음 봤다), 셀프 리뷰 두 축이 앞 세션이 쓴 수(19개, 96번)를 다시 세어 단위와 표지 없는 판을 잡았다.

이 세션만 아는 것: 저장소 밖의 출력은 이 세션 스크래치패드 `C:/Users/User/AppData/Local/Temp/claude/C--project-agent/0215ba90-4e0b-41ee-9633-39b1c3a2d5f8/scratchpad/`에 있다. PR 본문 초안 `pr-body.md`(자리표 `CHECKLIST`, `VERIFY_NOTES`, `CI_TIMING`), 자리표를 채우는 `fill.cjs`, 바뀐 정답 목록 `changed.txt`(이미 본문에 넣었다), 두 사진 비교의 기록 `visual-ui.log`·`visual-widget.log`, 두 커밋 시도의 기록 `commit.log`(막힌 첫 시도)·`commit2.log`(`5f25f59b`), 커밋 메시지 `commit-msg.txt`, 명세 축 서브에이전트가 남긴 `count.cjs`·`agg2.cjs`. 앞 세션의 출력(`53f51b7a-…/scratchpad/`)과 CI 아티팩트(`8a058eeb-…/scratchpad/ci/`)의 자리는 위 "인계 (셀프 리뷰 직전, 셋째 세션)"이고 그대로 있다.

인계 지시문:

```
다음 작업: .scratch/harness/issues/016-visual-focus-flake.md. 사진 비교가 몇 픽셀 차이로 흔들리는 원인(크롬의 부분 래스터)을 재서 브라우저 실행 인자와 다시 만든 정답으로 고친다(대기열 414)
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 414를 티켓 .scratch/harness/issues/016-visual-focus-flake.md로 쓰고 한다
브랜치: chore/016-visual-focus-flake
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-26-17-visual-focus-flake.md 의 "넷째 세션" 절과 "인계 (커밋 뒤, 넷째 세션)" 절
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰를 반영해 5f25f59b로 커밋했고(티켓 done, 대기열 414 닫힘) 푸시와 PR은 아직이다. 일지의 인계 절은 커밋하지 않았다. 남은 단계(origin/main 합치기와 변이 표의 원문 확인, PR 직전 리뷰, PR 본문 자리표 채우기와 PR, 회고, 병합)와 저장소 밖 PR 본문 초안의 자리는 일지의 "인계 (커밋 뒤, 넷째 세션)" 절이다. docs/journal/2026-10-26-17-visual-focus-flake.md
확인할 선행 조건: 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다(세션에 실리는 스킬은 세션을 시작한 체크아웃의 사본이다)
이번 요청 범위: PR과 병합까지
```

넘기기: 제목을 `chore/016-visual-focus-flake (인계함)`으로 바꿨다. 도는 백그라운드 작업은 없었다(리뷰 서브에이전트 둘, 두 사진 비교, 두 커밋 시도는 모두 끝났다). `docker ps`는 Docker 엔진의 Internal Server Error로 답하지 않아 남은 컨테이너를 보지 못했다(두 사진 비교는 종료 0으로 끝났다). 워크트리 잠금은 이미 풀려 있었다(`is not locked`).

open-session을 부른다 2026-10-26T13:57:25Z

## 다섯째 세션

제목을 `chore/016-visual-focus-flake`로 바꾸고 `git worktree list`에서 찾은 이 워크트리에 EnterWorktree(path)로 들어왔다.

### origin/main 합치기

`71433a0d`(#356)까지 합치자 `.scratch/harness/probes/README.md`가 글자 충돌이었다. 두 쪽 모두 표 끝에 행을 더한 것이라 충돌 표지만 지워 두 쪽 행을 모두 남겼다(이 브랜치의 두 행이 main의 세 행 앞에 온다). 병합 커밋의 첫 시도는 pre-commit의 pytest가 1 failed, 5619 passed(1430.4초)로 막았다. 빨간 것은 넷째 세션 첫 시도와 같은 `tests/tools/test_rerun_runner.py::test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다`(`board.run()`이 1)이고, 그 시험만 따로 치자 1 passed(15.5초)였다. 같은 커밋을 다시 쳐 `a87b4f71`이 모두 통과했다(pytest 688.5초, web-verify 597.7초). 그 시험은 B 갈래를 3초 붙잡는 동안 A 갈래가 두 번 오염되는 차례에 기대어, 부하가 크면 차례가 바뀐다고 어림한다(시험 코드를 읽었다. 재지 않았다).

`sibling_overlap.py`를 치자 origin/main이 `c7efd9ba`(#390, harness 015)로 또 움직였고, 그 커밋이 `.claude/rules/probes.md` 첫 항목에 "표지는 그것으로 가르려는 다른 해석 아래에서는 나지 않는 관찰로 고른다"를 더했다(대기열 367). 그래서 합친 뒤 이 브랜치의 표지를 그 조항에 대 봤다. `run.mjs`의 `argsMatched`, `attribution.mjs`의 실행 인자 시험 Received 줄, 설정 변이 둘의 `+   "--disable-partial-raster",`는 인자가 없거나 그 시험이 다른 까닭으로 빨개진 해석 아래에서는 나지 않는다. 사진 변이의 표지(`Snapshot: molecules-switch--off-`와 `-focus.png`)는 그렇지 않았다. Playwright 1.63.0의 `toHaveScreenshot`은 정답이 있을 때 시간 초과(`Timeout …`, `Failed to take two consecutive stable screenshots.`)로 끝나도 같은 `handleDifferent`로 `Snapshot:` 줄을 찍는다(`expect.js`의 `handleDifferent`와 `coreBundle.js`의 `expectScreenshot`을 읽었다). 그래서 표지를 실패 머리의 `are different.` 바로 뒤에 빈 줄과 여섯 칸 들여쓴 `Snapshot: molecules-switch--off-` 줄이 이어진 문구로 바꿨다(호출 기록의 `are different.`는 `- `로 시작하고 `Snapshot:` 줄 뒤에 온다). 변이 도구는 출력을 텍스트 모드로 읽어 줄바꿈이 `\n`이다(`run_command`를 읽었다).

바꾼 표지로 변이를 다시 돌리지 못했다. `docker ps`와 `docker version`이 엔진의 `Internal Server Error`로 답했고(Docker Desktop의 프로세스는 오전 11시 10분부터 떠 있었다), 다른 세션도 쓰는 Docker를 다시 시작하지 않았다. 대신 앞선 세션들이 저장한 사진 비교 기록 열다섯을 스크래치 스크립트(`C:/Users/User/AppData/Local/Temp/claude/C--project-agent/48c35404-50ee-4b17-b3d3-ac8dfc1a64ff/scratchpad/marker_check.cjs`)로 훑었다. `Snapshot:` 줄이 있는 기록 여섯(첫 세션의 `ui-flag1.log`·`visual-once.log`·`widget-flag1.log` 등)의 `Snapshot:` 줄 24개가 모두 픽셀 차이 갈래였고, 새 표지는 그 24개에만 맞았다(손으로 봤다). 시간 초과 갈래의 `Snapshot:` 줄은 열다섯 어디에도 없어, 시간 초과에 맞지 않는다는 쪽은 코드를 읽은 것이다. 고른 변이 셋의 `tools/mutate.py --check`는 "원문 확인: 변이 3 모두 원문이 한 번씩 있다"였고 #388의 표지 메아리 알림은 나지 않았다. 프로브 README의 변이 행에 바꾼 까닭과 이 확인을 적었다. `Snapshot:` 줄이 있던 기록 여섯은 `8a058eeb-cbf3-4b50-930c-96c245c3b5dc/scratchpad/`의 `ui-flag1.log`(7)·`visual-once.log`(2)·`widget-flag1.log`(3), `c10dddc8-641e-4a22-a1f8-78deb59de7cc/scratchpad/`의 `visual_widget.log`(1)·`visual_widget2.log`(1), `ec568c47-f7ff-4549-a1da-d6386aa86bf9/scratchpad/`의 `rep-before.log`(10)다(모두 `C:/Users/User/AppData/Local/Temp/claude/C--project-agent/` 아래, 괄호는 `Snapshot:` 줄 수). 병합 커밋 `3068aee0`(#390 합치기와 표지 변경)의 pre-commit은 모두 통과했다(pytest 682.2초, web-verify 604.1초). ruff 둘은 `.py`가 없어 Skipped였고 손으로 쳐 초록이었다(`All checks passed!`, `1064 files already formatted`).

### PR 직전 리뷰 (다섯째 세션)

CodeRabbit CLI는 좌석이 없어(`coderabbit auth status`의 `Seat: not assigned`) 대체 둘을 돌렸다. `/security-review`는 기준(신뢰도 0.8 이상의 HIGH·MEDIUM)을 넘는 취약점이 없었다. 프로브의 `git`·`docker`는 모두 셸 없이 배열 인자로 뜨고, `--out` 지우기는 절대 경로·저장소 밖·비었거나 표지 파일이 있을 때만이다. `bug-perf-review`는 Critical·Major 없이 유효 넷, 보류 둘, 오탐 넷이었다(도구 호출 예산 40에서 멈췄다).

- 유효 Minor: `ci_diff.mjs`와 `attribution.mjs`가 빈 입력(짝이 없는 폴더, 정답 사진이 없는 판)에도 종료 0이다. → 고쳤다. 빈 폴더와 첫 커밋 `7aca1dcf`로 둘 다 "측정 아님"과 종료 1을, CI 아티팩트와 셋째 세션의 그림으로 다시 돌려 2·29·17과 76·0·0(측정 아님 0)을 봤다.
- 유효 Nit: `changed_baselines.mjs`의 `Math.max(...)` 펼치기가 갈린 픽셀이 많으면 인자 수 한도에 걸린다. → `reduce`로 고쳤다. 다시 돌린 출력이 넷째 세션의 `changed.txt`와 글자까지 같았다.
- 유효 Minor: `run.mjs`의 `docker run`에 시간 제한이 없고, Ctrl-C로 끊으면 임시 폴더가 남는다. → 남긴다. 고치는 값은 `--name`, 시간 제한, 넘기면 `docker rm -f`로 작지만, Docker 엔진이 응답하지 않아 고친 판을 돌려 볼 수 없다. PR 체크리스트에 적는다.
- 유효 Minor: `run.mjs`의 결과 줄 표지가 시험 안에서 건너뛴 턴(`renderedAs`가 거짓)을 세지 않는다. → 남긴다. 고치려면 러너가 행마다 사진 수를 맞대야 하고 같은 까닭으로 돌려 볼 수 없다. 최종 판 둘은 표의 180행이 모두 4장씩(사진 720장, 스크래치 `shots_sum.cjs`로 `summary.json`을 세어 손으로 봤다)이라 건너뛴 턴이 없었다. README `visual_flake/` 행의 못 보는 것에 적었다.
- 보류: 새 표지 확인의 "기록 여섯"이 어느 파일인지 적히지 않았다. → 위 줄에 적고 README에서 이 절을 가리켰다. 두 설정에 `retries`가 없어(Grep) 한 시도의 픽셀 빨강과 다른 시도의 `-focus.png`가 합쳐 맞는 길은 없다.
- 보류: 리뷰가 닫지 못한 사실 문장. → 이 세션이 다시 셌다. 화면 정답 `pages-widgetscreen--*` 35장(`ls`), 인자 없는 위젯 비교 기록의 화면 시험 줄 19(`grep -c`), `sizes.mjs` 12·14(다시 돌렸다), 까닭 재기 두 기록의 `108 passed`·`1 failed`와 `42 passed`·`1 failed`(`grep`), 대기열 414 닫힘 문장(잰 것과 재지 않은 것을 나눠 적었다). 탐색 실행의 88번 중 87번·48번 중 6번은 넷째 세션의 명세 축이 `agg2.cjs`로 다시 센 것이라 다시 세지 않았다.
- 오탐 넷: `missingBrowserArgs`의 `split(" ")`(리눅스 컨테이너에서만 돈다), 세션을 닫지 않는다(`finally`에서 `detach`), 새 표지가 시간 초과에도 맞는다(코드상 아니다), `--out`의 저장소 밖 판정(다른 드라이브면 거짓 거절로 안전한 쪽).
- 참고(지적 아님): 오류 아이콘 4장의 채널 차 45~46과 위젯 `reconnecting-dark`의 112픽셀은 흔들린 세 사진과 성질이 달라 보인다는 말. 76장 모두 `attribution.mjs`로 인자 없는 그림이 옛 정답과 같았으므로 까닭은 인자다.

반영은 `45bfdfe0`으로 커밋했다(pre-commit 모두 통과). 첫 푸시는 origin/main이 한 커밋(#393, harness 014) 앞서 있다며 훅이 막았다. 합친 병합 커밋 `54c042aa`는 충돌이 없어 pre-commit 없이 만들어졌고, 그래서 `tools/run_checks.py`를 손으로 쳐 열 검사가 모두 통과했으며(pytest 832.0초, web-verify 783.0초) ruff 둘과 `sibling_overlap.py`도 초록이었다. #393은 `.claude/skills/open-session/SKILL.md`를 바꿨다. 그 뒤 푸시하고 PR [njh6803/agent-os#394](https://github.com/njh6803/agent-os/pull/394)를 열었다.

## 인계 (PR 연 뒤, 다섯째 세션)

세션 컨텍스트가 인계 문턱을 넘은 채 `PR 연 뒤`에 와서(`hook_handoff`) 넘긴다. 이 세션의 제목은 `chore/016-visual-focus-flake`이고 넘기며 `chore/016-visual-focus-flake (인계함)`으로 바꾼다. 인계하지 않는 때 다섯에는 해당하지 않았다. 범위가 PR과 병합까지이고, 지시문의 이어받을 상태는 `인계: 커밋 뒤`로 경계가 다르며, `get_session`의 `self`에 `parentSessionId`가 없고, 이 세션이 쓴 `인계 못함` 줄도 없다.

이 세션이 번복하거나 고친 것: 사진 변이의 표지를 #390의 조항에 맞춰 `are different.` 뒤의 `Snapshot:` 줄 문구로 바꿨고(위 "origin/main 합치기"), PR 직전 리뷰의 유효 지적 둘로 프로브 세 파일(`ci_diff.mjs`, `attribution.mjs`, `changed_baselines.mjs`)을 고쳤으며, 프로브 README의 변이 행과 `visual_flake/` 행을 그에 맞춰 고쳤다. 앞 세션이 끝낸 진단과 정답은 바꾸지 않았다.

남은 일(차례대로):

1. 봇 회차(next-session 순서 1의 2). PR을 연 뒤 `@coderabbitai review` 코멘트를 아직 남기지 않았다. 이 세션이 연 직후의 상태는 통과 2, 대기 6, 실패 0이었다.
2. CI가 끝나면 PR 본문의 CI 시간 줄을 `gh pr edit`로 채운다. 그 줄은 "인자를 끈 브라우저가 사진 비교의 걸린 시간을 늘리는지는 … 결과는 CI가 끝난 뒤 이 줄에 적는다."이고, 이 PR의 `visual` 잡의 두 단계(패키지, 위젯) 걸린 시간을 main의 직전 실행 `40279175497`(패키지 3분 18초, 위젯 53초)과 맞대 그 문장을 결과로 바꾼다. 본문 원문은 아래 스크래치패드의 `pr-body.md`이고 `gh pr view 394 --json body`로도 받는다.
3. 회고(`retro`)와 일지 `## 다음`을 병합 전에 푸시한다(next-session 순서 1의 3). 회고 후보는 앞 인계 절의 것에 더해 셋이다. `tests/tools/test_rerun_runner.py`의 오염 시험이 pre-commit의 pytest에서 부하로 빨간 것이 두 번째다(넷째 세션 첫 시도, 이 세션의 병합 커밋 첫 시도). Docker 엔진이 `Internal Server Error`로 답해 바꾼 표지로 변이를 다시 돌리지 못했다. 브랜치가 사는 동안 main에 선 규약(#390의 표지 조항)이 이미 커밋한 표지를 다시 고치게 했다.
4. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다.

이 세션만 아는 것: 저장소 밖의 출력은 이 세션 스크래치패드 `C:/Users/User/AppData/Local/Temp/claude/C--project-agent/48c35404-50ee-4b17-b3d3-ac8dfc1a64ff/scratchpad/`에 있다. PR 본문 `pr-body.md`(연 그대로), 그 자리표에 넣은 `checklist.md`·`verify-notes.md`, 표지 확인 스크립트 `marker_check.cjs`, 사진 수를 센 `shots_sum.cjs`, 기록 `merge-commit*.log`·`commit3.log`(`45bfdfe0`)·`run_checks.log`(`54c042aa`), 다시 돌린 프로브 출력 `ci_diff2.log`·`attr2.log`·`changed2.txt`. 자리표를 채우던 `fill.cjs`는 넷째 세션 스크래치패드(`0215ba90-4e0b-41ee-9633-39b1c3a2d5f8/scratchpad/`)에 있다.

인계 지시문:

```
다음 작업: .scratch/harness/issues/016-visual-focus-flake.md. 사진 비교가 몇 픽셀 차이로 흔들리는 원인(크롬의 부분 래스터)을 재서 브라우저 실행 인자와 다시 만든 정답으로 고친다(대기열 414)
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 414를 티켓 .scratch/harness/issues/016-visual-focus-flake.md로 쓰고 한다
브랜치: chore/016-visual-focus-flake
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-26-17-visual-focus-flake.md 의 "다섯째 세션" 절과 "인계 (PR 연 뒤, 다섯째 세션)" 절
이어받을 상태: 인계: PR 연 뒤. PR njh6803/agent-os#394를 열었고 첫 @coderabbitai review 코멘트와 봇 회차부터 한다. CI가 끝나면 PR 본문의 CI 시간 줄을 채우고, 회고와 일지 "다음"을 병합 전에 푸시한다. 일지의 인계 절은 커밋하지 않았다. 남은 단계와 회고 후보, 저장소 밖 출력의 자리는 일지의 "인계 (PR 연 뒤, 다섯째 세션)" 절이다. docs/journal/2026-10-26-17-visual-focus-flake.md
확인할 선행 조건: 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다(세션에 실리는 스킬은 세션을 시작한 체크아웃의 사본이다)
이번 요청 범위: PR과 병합까지
```

넘기기: 제목을 `chore/016-visual-focus-flake (인계함)`으로 바꿨다. 이 세션이 띄운 백그라운드 작업은 없었다(PR을 연 뒤 `wait_ci.py` 대기를 띄우지 않았다). 워크트리 잠금은 이미 풀려 있었다(`is not locked`). #393이 `open-session` 스킬을 바꿨으므로 Skill 도구 대신 이 워크트리 사본의 `.claude/skills/open-session/SKILL.md`를 Read로 열어 따른다(`CLAUDE.md` 환경 함정).

open-session을 부른다 2026-10-26T16:13:03Z

## 여섯째 세션

제목을 `chore/016-visual-focus-flake`로 바꾸고 `git worktree list`에서 찾은 이 워크트리에 EnterWorktree(path)로 들어왔다.

### 봇 회차 (여섯째 세션)

`@coderabbitai review`를 남기고 `tools/wait_ci.py 394`를 백그라운드로 띄웠다. 끝 줄은 "모두 통과. CodeRabbit: Review rate limited"였다. CodeRabbit은 무료 한도에 걸려 리뷰를 내지 않았으므로 이 회차는 세지 않는다. 그 PR의 보안·버그 축은 PR 본문 체크리스트에 적은 PR 직전 리뷰(`/security-review`, `bug-perf-review`)가 대체한다(`docs/constitution/operations.md` 리뷰 파이프라인).

claude-review 첫 회차(`54c042aa`):

- Minor: `BROWSER_ARGS` 독스트링이 열 줄이 넘고, 측정 이력(횟수, 손으로 친 판, 재지 않았다)이 프로브 README·일지와 두 자리에 선다. → 고쳤다. 원인, 찍기 전 대기로는 고치지 못한 것, 시험이 사진이 아니라 명령줄을 보는 까닭, 프로브 README 행과 변이 표의 경로만 남겼다. 둘째 세션 셀프 리뷰가 "재지 않았다"를 넣은 까닭(인과를 잰 것보다 앞세우지 않는다)은 인과 문장을 빼고 본 것("흔들렸다", "그림이 하나였고")만 적어 지켰다. 변이 표의 원문 블록은 `export` 줄뿐이라 이 주석에 닿지 않는다.
- Nit: 두 실행 인자 시험의 본문이 같다. → 남긴다. 리뷰도 한 줄이라 두어도 된다고 했고, 둘째 세션의 셀프 리뷰가 같은 지적을 같은 까닭으로 남겼다.
- Nit: `missingBrowserArgs`가 명령줄을 공백으로 가른다. → 남긴다. 리뷰도 지금 인자로는 문제가 없다고 했고, 독스트링이 그 한계를 적는다.

CI의 `visual` 잡(`40356180912`)은 패키지 3분 17초, 위젯 50초였고, 이 브랜치를 딴 `92b61458`의 main 실행(`40279175497`)은 3분 18초, 53초였다(두 실행의 `playwright test` 단계 시각을 `gh run view`로 맞댔다). 이 줄은 처음에 `40279175497`을 "main의 직전 실행"이라 적었고 일곱째 세션 셀프 리뷰가 바로잡았다(아래 "셀프 리뷰 (일곱째 세션)"). PR 본문의 그 줄을 `gh pr edit`로 결과 문장으로 바꿨다.

origin/main이 `b84691e0`(#391, harness 012)로 움직여 합쳤다. 프로브 README와 대기열을 함께 고쳤지만 글자 충돌은 없었다. `git diff --name-only HEAD...origin/main`의 일곱 파일은 `.env` 읽기 훅과 그 시험·변이 표·티켓·일지라, 이 브랜치가 따를 새 규약은 없었다.

## 회고

후보 일곱. 승인 둘, 기각 다섯, 넘김 없음. 만료한 행은 여섯이다(170·172·173·183·208·210. 이 브랜치와 `--ref origin/main`의 두 출력에 모두 들었다).

1. 승인(대기열 430, 6회차): 표지 없는 수동 판의 결과가 주석·변이 표의 근거 문장으로 들어갔다. 첫 세션이 `BROWSER_ARGS`를 비우고 `-g pages-widgetscreen--`로 화면 시험만 돌려, 브라우저가 인자 없이 떴다는 표지(실행 인자 시험의 빨강)가 없는 판이었다. 셋째 세션이 표지 있는 두 판으로 다시 세었다(위 "바뀐 정답의 까닭"). 구현 때 실리는 `.claude/rules/probes.md` 첫 항목을 어긴 사건이라 회차로 세고, 닫힌 339를 이은 열린 430에 더했다. 430의 처방(스크래치 `.py` 프로브가 `Rounds`를 가져오지 않으면 짚는 훅)은 손으로 친 판을 덮지 않는다. 그 행을 반영하는 chore가 이 회차를 함께 본다.
2. 승인(대기열 480, 1회차): 코드 주석의 측정 이력을 두 리뷰가 반대로 밀었다. 넷째 세션 셀프 리뷰가 `docs/agents/issue-tracker.md`의 "근거는 무엇으로 섰는지 밝힌다"로 "손으로 친 두 판"을 주석에 더하게 했고, PR의 claude-review가 그 이력을 README로 넘기라고 Minor로 짚었다. 자동 검사로 가를 수 없는 판단이라 층은 그 지침의 문장이고, 더하는 것이라 세 번째에 반영한다.
3. 기각(대기열 306이 받아들여 닫은 종류의 새 사례): pre-commit의 pytest에서 이 브랜치가 건드리지 않은 시간 시험 셋이 부하로 빨갰고 따로 치면 지났다. `tests/tools/test_probe_kit.py::test_배출은_줄이_계속_와도_제한_시간에_끝난다`(둘째 세션. 같은 시험이 같은 꼴로 빨간 일은 일지 2026-10-22-21·2026-10-23-14·2026-10-23-27·2026-10-26-03에도 있다), `tests/adapters/test_filesystem.py`의 교체 재시도 시험(넷째 세션), `tests/tools/test_rerun_runner.py::test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다`(넷째 세션과 다섯째 세션의 병합 커밋, 두 번). 306은 커밋을 다시 치는 값을 받아들이고 닫혔으므로 회차를 더하지 않고 여기만 적는다.
4. 기각: Docker 엔진이 `Internal Server Error`로 답해, 바꾼 표지로 사진 변이를 다시 돌리지 못했고 PR 직전 리뷰의 `run.mjs` Minor 둘을 고친 판도 돌려 볼 수 없었다. 다른 세션도 쓰는 Docker를 다시 시작하지 않은 것은 맞는 판단이고 하네스가 고칠 자리가 없다. PR 본문의 남긴 위험과 아래 "다음"에 적었다.
5. 기각: 브랜치가 사는 동안 main에 선 표지 조항(#390)이 이미 커밋한 표지를 다시 고치게 했다. `CLAUDE.md` 환경 함정의 커밋 전 줄(origin/main이 움직였으면 이 브랜치가 든 파일과 대조한다)이 그 자리에서 알렸고 다섯째 세션이 따랐다.
6. 기각: 셀프 리뷰 두 축이 앞 세션이 쓴 수(시험 19개와 정답 35장, 끊긴 판을 넣은 96번)를 다시 세어 잡았다. 리뷰가 제 몫을 한 것이고 새 판단 기준이 아니다.
7. 기각: CodeRabbit이 시간당 한도로 리뷰하지 않았다. 리뷰 파이프라인 3과 `wait_ci.py`의 통과 줄이 알렸고, PR 직전 리뷰가 대체다.

## 다음

PR njh6803/agent-os#394를 병합한다. 이 세션은 워크트리에서 병합하므로 주 체크아웃을 당기지 않는다. claude-review의 보류한 Nit 둘(시험 본문, 명령줄 공백 가르기)은 뒤로 넘긴 일이 아니라 고치지 않기로 한 것이다.

Docker 엔진이 응답하지 않아 남긴 셋도 뒤로 넘기지 않고 받아들여 닫는다. 셋은 바꾼 표지로 사진 변이(`visual_flake_mutations.toml`의 첫 변이)를 다시 돌리기, `visual_flake/run.mjs`의 `docker run`에 시간 제한과 끊겼을 때의 정리를 두기, 결과 줄 표지가 시험 안에서 건너뛴 턴을 세게 하기(PR 직전 `bug-perf-review`의 Minor 둘)다. 넘겨받을 티켓이나 대기열 행이 없어 넘긴다고 적어도 읽을 쪽이 없었다(일곱째 세션 셀프 리뷰의 명세 축). 바꾼 표지가 실제 출력과 어긋나면 그 변이는 초록이 아니라 `표지 없음`과 어긋남으로 끝나(`tests/tools/test_mutate.py`의 `test_표지를_적은_변이는_기대대로여도_출력에_표지가_없으면_어긋난다`) 다음에 돌리는 사람이 곧바로 본다. 바꾼 표지는 앞선 세션들이 저장한 사진 비교 기록의 픽셀 차이 줄 24개에만 맞았다(다섯째 세션, 손으로 봤다). `run.mjs`는 사람이 손으로 돌리는 프로브이고 임시 폴더를 운영체제의 임시 폴더 아래에 만들며(`mkdtempSync(join(tmpdir(), …))`, 코드를 읽었다), 최종 판 둘에는 건너뛴 턴이 없었다. 셋 다 PR 본문의 "남긴 위험"에 적혀 있고, 표지와 건너뛴 턴은 프로브 README의 두 행에도 있다.

## 인계 (셀프 리뷰 직전, 여섯째 세션)

claude-review 반영과 회고·"다음"을 쓴 뒤 셀프 리뷰(`/code-review`, 기점 `18770829`)를 부르자, 세션 컨텍스트가 인계 문턱을 넘은 채 `셀프 리뷰 직전`에 와서(`hook_handoff`) 넘긴다. 셀프 리뷰의 단계는 밟지 않았다(서브에이전트를 띄우지 않았다). 이 세션의 제목은 `chore/016-visual-focus-flake`이고 넘기며 `chore/016-visual-focus-flake (인계함)`으로 바꾼다. 인계하지 않는 때 다섯에는 해당하지 않았다. 계기를 낸 스킬 호출은 성공했고, 범위는 PR과 병합까지이며, 지시문의 이어받을 상태는 `인계: PR 연 뒤`로 경계가 다르고, 이 세션이 쓴 `인계 못함` 줄이 없으며, `get_session`의 `self`에 `parentSessionId`가 없다.

인계 절은 `## 다음`을 쓰지 않는다고 하지만, 이 세션은 계기가 오기 전에 회고와 "다음"을 이미 썼다. 회고(위 `## 회고`, 대기열의 만료 여섯·430의 6회차·새 행 480)는 다시 돌지 않는다. 셀프 리뷰가 고친 것이 회고나 "다음"을 바꾸면 그 절만 고친다.

커밋한 것: `18770829`(origin/main #391을 합친 병합 커밋. 충돌이 없어 pre-commit은 커밋 메시지 검사만 돌았다). 푸시하지 않았다. PR의 헤드는 아직 `54c042aa`다.

커밋하지 않은 변경(셀프 리뷰의 범위, `git diff 18770829`, 미추적 0):

- `web/packages/ui/visual/index.ts`: `BROWSER_ARGS` 독스트링을 줄였다(claude-review 첫 회차 Minor, 위 "봇 회차 (여섯째 세션)").
- `.scratch/retro-queue.md`: 만료 여섯(170·172·173·183·208·210), 430의 6회차, 새 행 480.
- 이 일지: 다섯째 세션의 인계 절(그 세션이 커밋하지 않았다), 여섯째 세션 절, 회고, 다음, 이 인계 절.

셀프 리뷰에 밀 주장(이 세션이 새로 쓴 사실 문장. 나열 밖도 잰다): `index.ts`의 "이 인자를 주면 찍는 때와 상관없이 그림이 하나였고, 찍기 전에 기다리는 것으로는 고치지 못했다", "인자를 빼도 정답과 맞는 사진(위젯의 화면)이 있어", PR 본문과 이 일지의 CI 시간(패키지 3분 17초·위젯 50초, main 3분 18초·53초), 대기열 480 행의 괄호(셀프 리뷰가 근거의 종류를 주석에 더하게 했다는 것은 위 "셀프 리뷰 (넷째 세션)"의 셋째 Minor), 회고 3의 시험 이름과 회차(둘째 세션의 "넷째", `test_rerun_runner.py`의 두 번).

남은 일(차례대로):

1. 셀프 리뷰(`/code-review`, 기점 `18770829`, 티켓 `.scratch/harness/issues/016-visual-focus-flake.md`)와 반영.
2. 커밋. 커밋 전에 `git branch --show-current`와 `uv run python tools/sibling_overlap.py`. 바꾼 `.py`가 없어 pre-commit의 ruff 둘이 Skipped이므로 손으로 친다. `index.ts`는 주석만 바꿨다. 사진 비교는 다시 치지 않아도 된다(동작이 바뀌지 않았다).
3. 푸시하고 `@coderabbitai review`를 남긴 뒤 `tools/wait_ci.py 394`를 백그라운드로 띄운다. claude-review는 둘째 회차라 Critical·Major만 고친다. 첫 회차의 보류한 Nit 둘(시험 본문 중복, 명령줄 공백 가르기)의 이유를 PR 코멘트로 남긴다(이 세션은 아직 남기지 않았다). CodeRabbit은 2026-10-26T16:08Z 무렵 "46분 뒤"라 한 무료 한도에 걸려 있었다.
4. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다.

이 세션만 아는 것: 저장소 밖 출력은 이 세션 스크래치패드 `C:/Users/User/AppData/Local/Temp/claude/C--project-agent/55ec03da-d417-4eb6-ac7c-e09c8ba353dc/scratchpad/`에 있다. 고친 PR 본문 `pr-body-live.md`(이미 `gh pr edit`로 올렸다), 만료 스크립트 `expire_rows.py`, 대기열 칸을 찍는 `row_cells.py`.

인계 지시문:

```
다음 작업: .scratch/harness/issues/016-visual-focus-flake.md. 사진 비교가 몇 픽셀 차이로 흔들리는 원인(크롬의 부분 래스터)을 재서 브라우저 실행 인자와 다시 만든 정답으로 고친다(대기열 414)
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 414를 티켓 .scratch/harness/issues/016-visual-focus-flake.md로 쓰고 한다
브랜치: chore/016-visual-focus-flake
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-26-17-visual-focus-flake.md 의 "여섯째 세션" 절과 "인계 (셀프 리뷰 직전, 여섯째 세션)" 절
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경(claude-review 첫 회차 Minor로 줄인 BROWSER_ARGS 독스트링, 회고의 대기열 변경, 일지의 여섯째 세션 절·회고·다음)이 워크트리에 있고 셀프 리뷰(/code-review, 기점 18770829)부터 한다. 18770829(origin/main #391 합치기)는 푸시하지 않았다. 회고는 이미 돌았다. 남은 단계(커밋, 푸시와 봇 회차, 보류한 Nit 둘의 PR 코멘트, 병합)와 밀 주장은 일지의 "인계 (셀프 리뷰 직전, 여섯째 세션)" 절이다. docs/journal/2026-10-26-17-visual-focus-flake.md
확인할 선행 조건: 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다(세션에 실리는 스킬은 세션을 시작한 체크아웃의 사본이다)
이번 요청 범위: PR과 병합까지
```

넘기기: 제목을 `chore/016-visual-focus-flake (인계함)`으로 바꿨다. 도는 백그라운드 작업은 없었다(`wait_ci.py` 대기는 "모두 통과"로 끝났다). 워크트리 잠금은 이미 풀려 있었다(`is not locked`). 이 세션은 주 체크아웃(#393 전)에서 시작해, `open-session`은 Skill 도구 대신 이 워크트리 사본의 `.claude/skills/open-session/SKILL.md`를 Read로 열어 따른다.

open-session을 부른다 2026-10-26T16:29:07Z

## 일곱째 세션

제목을 `chore/016-visual-focus-flake`로 바꾸고 `git worktree list`에서 찾은 이 워크트리에 EnterWorktree(path)로 들어왔다. 주 체크아웃(`c7efd9ba`)과 이 워크트리 사이에 바뀐 스킬은 `open-session` 하나라(`git diff --name-only c7efd9ba HEAD -- .claude/skills`) `code-review`는 Skill 도구로 불렀다. origin/main은 `18770829` 뒤로 움직이지 않았다(`git log 18770829..origin/main`이 비었다).

### 셀프 리뷰 (일곱째 세션)

기점 `18770829`, 바뀐 파일 3(`index.ts`, 대기열, 이 일지), 커밋 0, 미추적 0.

표준 축(sonnet, high):

- Minor: 줄인 `BROWSER_ARGS` 주석이 근거의 범위와 종류를 뺐다. "인자를 빼도 정답과 맞는 사진(위젯의 화면)이 있어"는 이 PC에서 손으로 두 판 돌린 것인데 종류 표시가 없고(`docs/agents/issue-tracker.md` 프로브와 근거의 "근거는 무엇으로 섰는지 밝힌다"), "찍는 때와 상관없이 그림이 하나였고"는 프로브가 잰 흔들린 세 사진의 것인데 모든 사진으로 읽힌다. 둘째 세션 명세 축이 "이 PC에서"로 좁힌 것을 여섯째 세션의 줄이기가 되돌렸다. → 고쳤다. 주석을 줄인 모양은 두고 "이 PC 에서 프로브로 재 보니 흔들린 세 사진은", "다만 위젯의 화면 사진은 이 PC 에서 인자를 빼고 손으로 돌려도 정답과 맞아"로 범위와 종류를 되살렸다(뒤의 것은 아래 명세 축 첫 줄을 함께 반영한 문구다). 대기열 480의 처방(손으로 본 경위는 README 행에 둔다)은 아직 반영되지 않았으므로 지금 규칙대로 종류 한 구절을 두었다. 같은 주석의 같은 갈등이라 480의 회차는 더하지 않는다. 횟수와 판의 경위는 README 행에 두어 claude-review 첫 회차의 Minor(측정 이력을 두 자리에 세우지 않는다)도 지킨다. 여섯째 세션 "봇 회차" 절의 "인과 문장을 빼고 본 것(…)만 적어 지켰다"는 이 고침으로 근거의 종류까지 적은 판이 됐다.
- Minor: 회고 3의 "(둘째 세션, 같은 시험이 같은 꼴로 빨간 넷째)"가 뒤의 "(넷째 세션)"과 붙어 넷째 세션으로 읽힌다. 뜻은 같은 시험의 넷째 발생이다(위 "셀프 리뷰 (둘째 세션)"의 반영 뒤 검증 줄). → 고쳤다. 앞선 세 일지 번호를 적고 "넷째 발생"으로 바꿨다.
- Nit: 대기열 430의 "무엇" 칸은 "339의 5회차"이고 승인 칸만 6회차다. → 남긴다. 431(75의 5회차와 6회차)과 445가 같은 모양이다.
- 확인된 것(지적 아님): CI 시간(`40356180912` 패키지 197초·위젯 50초, `40279175497` 198초·53초, `gh run view --json jobs`), 480 행 괄호와 넷째 세션 셀프 리뷰 셋째 Minor의 대응, `git diff --name-only 54c042aa 18770829`의 일곱 파일, 만료 여섯이 모두 1회차이고 승인 2026-10-12라 14일을 넘긴 것(`queue_open_rows.py --today 2026-10-27`에 더 만료할 행이 없다), 만료 표시 문구가 행 4·13과 같은 모양인 것. 주석이 가리키는 README 174행과 변이 표, `missingBrowserArgs`는 모두 있다.

명세 축(Opus, 상속):

- Minor: "인자를 빼도 정답과 맞는 사진(위젯의 화면)이 있어"가 근거보다 넓고, "있어"(있다는 것)가 시험이 명령줄을 보는 까닭을 싣지 못한다. 까닭은 위젯의 화면 시험이 이 PC의 비교 모드에서 인자 없이도 지난 것이다(티켓 Comments, 변이 표 머리). → 고쳤다. 표준 축 첫 줄과 같은 자리라 한 번에 "다만 위젯의 화면 사진은 이 PC 에서 인자를 빼고 손으로 돌려도 정답과 맞아, 설정이 인자를 넘기는지는 사진이 아니라 `missingBrowserArgs` 의 시험이 본다"로 고쳤다. 기준 2(주석이 원인과 프로브를 가리킨다)는 지켜진다고 봤다.
- Minor: 일지 "봇 회차 (여섯째 세션)"와 PR 본문의 "main의 직전 실행(`40279175497`)"이 틀렸다. PR 실행 `40356180912`의 헤드 `54c042aa`가 합친 #393의 main 실행 `40350734181`(15:35Z)이 그보다 앞서 돌았고, `40279175497`은 이 브랜치를 딴 `92b61458`의 실행이다. → 고쳤다. `gh run view 40350734181 --json jobs`로 그 실행의 `playwright test` 단계 시각을 손으로 봐 패키지 3분 25초(15:35:56~15:39:21), 위젯 55초(15:39:25~15:40:20)였고, PR 본문의 그 줄을 세 실행으로 고쳐 `gh pr edit`로 올렸다(본문에 `40350734181`이 실린 것을 `gh pr view`로 봤다). 여섯째 세션 절의 그 줄은 이름표를 고치고 바로잡았다고 적었다. 다섯째 세션 인계 절의 같은 이름표는 그 세션이 남긴 지시의 기록이라 두었다. 결론(인자를 끈 브라우저가 걸린 시간을 늘리지 않았다)은 바뀌지 않는다.
- Nit: 여섯째 세션 "봇 회차" 절이 인용한 "그림이 하나였다"는 주석 원문이 아니다(원문은 "그림이 하나였고"). → 고쳤다.
- Nit: 회고 3의 "넷째 발생"은 일지 `2026-10-26-03-proc-cmdline-settle.md` 130행의 같은 시험·같은 꼴(0.5초 배출에 줄 없음)을 빠뜨렸다. → 고쳤다. 차례 수를 빼고 그 일지까지 넷을 "에도 있다"로 적었다(일지 폴더를 그 시험 이름으로 Grep해 이 일지 밖의 네 파일을 봤다). 기각 판정은 바뀌지 않는다.
- Minor: "다음"이 뒤로 넘긴 셋(바꾼 표지로 사진 변이 다시 돌리기, `run.mjs`의 `docker run` 시간 제한과 정리, 건너뛴 턴 세기)을 받을 쪽이 없다. 대기열에 행이 없고 티켓도 없다. → 고쳤다. Docker 엔진이 여전히 `Internal Server Error`로 답해(`docker version`) 이 세션에서도 돌릴 수 없었다. 대기열은 머리말대로 회고가 승인한 후보만 받아 이 셋의 자리가 아니고, harness 티켓은 그 일을 하는 세션이 쓴다(`docs/agents/issue-tracker.md`). 그래서 "다음"을 받아들여 닫는 문장으로 고치고 까닭을 적었다. 표지가 어긋나면 변이가 초록이 아니라 어긋남으로 끝나는 것은 `uv run pytest -q`로 `tests/tools/test_mutate.py`의 `test_표지를_적은_변이는_기대대로여도_출력에_표지가_없으면_어긋난다`를 돌려 본다(아래 다시 돌린 명령).
- 확인된 것(지적 아님): 로컬 Playwright 1.63.0 chromium에 경계 입력 넷을 준 스크래치 스크립트(이 세션 스크래치패드의 `mba.mts`)로 `missingBrowserArgs`가 명령줄을 본다는 것, `mutate.py --check`로 변이 셋의 원문이 모두 한 번씩 있다는 것, CI 시간 3분 17초·50초·3분 18초·53초, `queue_open_rows.py --ref 18770829`의 만료 대상과 고친 뒤 남은 만료 0, 480 번호가 겹치지 않는 것(`sibling_overlap.py`).

PR 직전 리뷰에 밀 주장(반영하며 새로 쓴 문장): 이 PR은 이미 열렸고 PR 직전 리뷰는 다섯째 세션에 돌았다. 그래서 아래 문장은 PR 봇 회차가 겨냥하도록 여기 적는다.

- `index.ts`: "이 PC 에서 프로브로 재 보니 흔들린 세 사진은 이 인자를 주면 찍는 때와 상관없이 그림이 하나였고", "다만 위젯의 화면 사진은 이 PC 에서 인자를 빼고 손으로 돌려도 정답과 맞아"
- PR 본문과 여섯째 세션 절: `40350734181`의 3분 25초·55초, "그 헤드가 합친 #393의 main 실행"
- "다음": "표지가 실제 출력과 어긋나면 그 변이는 초록이 아니라 `표지 없음`과 어긋남으로 끝나", "`run.mjs`는 … 임시 폴더를 운영체제의 임시 폴더 아래에 만들며", "셋 다 PR 본문의 "남긴 위험"에 적혀 있고, 표지와 건너뛴 턴은 프로브 README의 두 행에도 있다"
- 회고 3: 같은 시험이 같은 꼴로 빨간 일이 있는 이 일지 밖의 일지 넷

고친 것: 위 "고쳤다" 전부(`index.ts` 주석, 일지의 이름표·인용·회고 3·"다음", PR 본문의 CI 시간 줄). 남긴 것: 표준 축의 Nit 하나(430의 "무엇" 칸, 431·445와 같은 모양). 다시 돌린 명령: `uv run pytest -q`로 `test_mutate.py`의 표지 시험 둘(`test_표지를_적은_변이는_기대대로여도_출력에_표지가_없으면_어긋난다`, `test_표지가_모두_있으면_기대대로다`)이 `2 passed in 676.51s`였다(이 PC에 다른 세션이 여럿 돌던 때다). `pnpm -C web exec prettier --check packages/ui/visual/index.ts`가 통과했다. 바꾼 `.py`가 없어 ruff 둘을 손으로 쳐 `All checks passed!`, `1069 files already formatted`였다. 나머지 손으로 치는 다섯은 이 커밋의 pre-commit으로 갈음한다. `index.ts`는 주석만 바꿔 사진 비교는 다시 치지 않는다(Docker 엔진도 응답하지 않았다).

커밋 `4f3b4960`(`chore: 브라우저 인자 주석을 잰 범위와 함께 줄이고 회고를 싣는다 (harness 016)`, 3 files). pre-commit은 모두 통과했다(pytest 979.8초, web-verify 724.2초, 변이 표·마크다운 표·줄 구분 문자·커밋 메시지 통과). ruff 둘은 `.py`가 없어 Skipped였고 위에서 손으로 친 결과가 초록이다. 인용 대조 경고 다섯 가운데 넷은 이 세션이 고쳐 지운 옛 문구(회고 3, CI 시간 줄의 이름표)와 PR 본문의 문구를 인용한 것이고, 하나("인과 문장을 빼고 본 것만 적어 지켰다")는 원문과 글자가 달라 "본 것(…)만"으로 고쳤다(이 고침은 아래 인계와 함께 커밋되지 않았다).

## 인계 (커밋 뒤, 일곱째 세션)

세션 컨텍스트가 인계 문턱을 넘은 채 `커밋 뒤`에 와서(`hook_handoff`) 넘긴다. 이 세션의 제목은 `chore/016-visual-focus-flake`이고 넘기며 `chore/016-visual-focus-flake (인계함)`으로 바꾼다. 인계하지 않는 때 다섯에는 해당하지 않았다. 계기를 낸 커밋은 성공했고, 범위는 PR과 병합까지이며, 이 세션을 연 지시문의 이어받을 상태는 `인계: 셀프 리뷰 직전`으로 경계가 다르고, 이 세션이 쓴 `인계 못함` 줄이 없으며, `get_session`의 `self`에 `parentSessionId`가 없다.

이 세션이 번복하거나 고친 것: 여섯째 세션이 줄인 `BROWSER_ARGS` 주석에 잰 범위와 근거의 종류를 되살렸고, 여섯째 세션 절의 CI 시간 이름표("main의 직전 실행")를 바로잡아 PR 본문의 그 줄도 세 실행으로 고쳐 올렸으며(`gh pr edit`), "다음"의 뒤로 넘긴 셋을 받아들여 닫는 문장으로 바꿨다(위 "셀프 리뷰 (일곱째 세션)"). 회고는 다시 돌지 않았다. 회고 3의 괄호만 고쳤다.

커밋한 것: `4f3b4960`(셀프 리뷰 반영, 대기열, 일지의 다섯째~일곱째 세션 절·회고·다음). `18770829`(origin/main #391 합치기)와 함께 푸시하지 않았다. PR의 헤드는 아직 `54c042aa`다. 커밋하지 않은 것은 이 인계 절과 바로 위 문단, 469행 인용 고침이다.

남은 일(차례대로):

1. PR 본문 넓히기(next-session 순서 1의 1). 이 커밋이 대기열을 바꿨는데(만료 여섯 170·172·173·183·208·210, 430의 6회차, 새 행 480) PR 본문은 그것을 말하지 않는다(`gh pr view 394 --json body`를 `480|430|만료`로 grep해 0이었다). 푸시하기 전에 `gh pr edit`로 "변경된 영역"이나 "왜 이렇게 했나"에 그 셋을, 체크리스트의 셀프 리뷰 줄(지금 "두 번: 기점 `92b61458`, `90a89c13`")에 기점 `18770829`의 셋째 셀프 리뷰를 더한다. 본문 원문은 이 세션 스크래치패드의 `pr-body.md`(CI 시간 줄을 고쳐 올린 판)이고 `gh pr view 394 --json body`로도 받는다.
2. 이 인계 절을 커밋하고 푸시한다. 커밋 전에 `git branch --show-current`와 `uv run python tools/sibling_overlap.py`. 바꾼 `.py`가 없으면 ruff 둘을 손으로 친다.
3. `@coderabbitai review`를 남기고 `tools/wait_ci.py 394`를 백그라운드로 띄운다. claude-review는 이 푸시가 둘째 회차라 Critical·Major만 고친다. 첫 회차의 보류한 Nit 둘(두 실행 인자 시험의 본문이 같다, `missingBrowserArgs`가 명령줄을 공백으로 가른다)의 이유를 PR 코멘트로 남긴다(까닭은 위 "봇 회차 (여섯째 세션)"의 두 Nit 줄). CodeRabbit은 앞 회차에 한도로 리뷰하지 않아 이 푸시가 첫 회차일 수 있다.
4. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다. 회고와 "다음"은 이미 커밋에 실렸다.

이 세션만 아는 것: 저장소 밖 출력은 이 세션 스크래치패드 `C:/Users/User/AppData/Local/Temp/claude/C--project-agent/7e3c0e1b-a4b2-40d4-a34b-3e533c005902/scratchpad/`에 있다. 고쳐 올린 PR 본문 `pr-body.md`, 커밋 메시지 `commit-msg.txt`, 커밋 기록 `commit.log`(`4f3b4960`의 pre-commit), 명세 축이 쓴 `missingBrowserArgs` 경계 입력 스크립트 `mba.mts`. Docker 엔진은 이 세션에서도 `Internal Server Error`로 답했다(`docker version`).

인계 지시문:

```
다음 작업: .scratch/harness/issues/016-visual-focus-flake.md. 사진 비교가 몇 픽셀 차이로 흔들리는 원인(크롬의 부분 래스터)을 재서 브라우저 실행 인자와 다시 만든 정답으로 고친다(대기열 414)
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 414를 티켓 .scratch/harness/issues/016-visual-focus-flake.md로 쓰고 한다
브랜치: chore/016-visual-focus-flake
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-26-17-visual-focus-flake.md 의 "일곱째 세션" 절과 "인계 (커밋 뒤, 일곱째 세션)" 절
이어받을 상태: 인계: 커밋 뒤. 4f3b4960(셀프 리뷰 반영, 대기열, 일지의 회고·다음)을 커밋했고 18770829와 함께 푸시하지 않았다. 푸시 전에 PR 본문을 이 커밋의 대기열 변경과 셋째 셀프 리뷰로 넓히고(gh pr edit), 커밋하지 않은 인계 절을 커밋해 푸시한 뒤 봇 회차(claude-review 둘째 회차, 첫 회차의 보류한 Nit 둘의 PR 코멘트)와 병합을 한다. 남은 단계와 스크래치 자리는 일지의 "인계 (커밋 뒤, 일곱째 세션)" 절이다. docs/journal/2026-10-26-17-visual-focus-flake.md
확인할 선행 조건: 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다(세션에 실리는 스킬은 세션을 시작한 체크아웃의 사본이다)
이번 요청 범위: PR과 병합까지
```

넘기기: 제목을 `chore/016-visual-focus-flake (인계함)`으로 바꿨다. 도는 백그라운드 작업은 없었다(서브에이전트 둘, pytest, 커밋이 모두 끝났다). 워크트리 잠금은 이미 풀려 있었다(`is not locked`). `open-session`은 #393이 바꿔 Skill 도구 대신 이 워크트리 사본의 `.claude/skills/open-session/SKILL.md`를 Read로 열어 따른다.

open-session을 부른다 2026-10-26T17:25:25Z

## 여덟째 세션

제목을 `chore/016-visual-focus-flake`로 바꾸고 `git worktree list`에서 찾은 이 워크트리에 EnterWorktree(path)로 들어왔다. `git fetch origin` 뒤 `git log 18770829..origin/main`이 비어, origin/main은 움직이지 않았다.

PR 본문을 넓혔다(next-session 순서 1의 1). "왜 이렇게 했나"에 회고 줄(만료한 1회차 행 여섯, 430의 6회차, 새 행 480)을, 체크리스트의 셀프 리뷰 줄에 기점 `18770829`의 셋째 셀프 리뷰를 더하고, pre-commit과 ruff 줄을 이 세션의 커밋으로 고쳐 푸시 전에 `gh pr edit`로 올린다. 본문 원문은 이 세션 스크래치패드 `C:/Users/User/AppData/Local/Temp/claude/C--project-agent/4e07694a-6282-488c-acb5-190462a6d4bd/scratchpad/pr-body.md`다.

이 일지만 실은 커밋의 첫 시도에서 pre-commit의 pytest가 시간에 기대는 시험 셋에서 빨갰다(`tests/channel/cli/test_interrupt.py::test_닫는_도중에_한_번_더_누르면_닫기를_기다리지_않고_끝난다`의 30초 초과, `tests/tools/test_rerun_runner.py`의 동시 실행 수 시험과 오염 시험). 셋만 따로 치니 `3 passed in 43.33s`였다. 둘째 시도는 같은 파일의 다른 동시 실행 시험(`test_같은_갈래가_두_번_든_파일럿의_두_회차가_함께_돌아도_번호가_다르다`, 1초 매달리는 두 회차의 최대 동시 수가 2가 아니라 1)만 빨갰고, 그 파일만 따로 치니 `53 passed in 615.52s`였다(따로 친 판도 10분이 걸릴 만큼 이 PC에 부하가 있었다). 셋째 시도로 커밋했다. 회고 3이 기각한 꼴(대기열 306)이라 회차를 더하지 않는다. `test_rerun_runner.py`의 오염 시험은 이 브랜치에서 세 번째다.

주 체크아웃 미갱신: 루트는 main. 이 세션은 워크트리에서 병합하므로 주 체크아웃을 당기지 않고, 병합한 워크트리도 지우지 않는다(next-session "워크트리에서 병합할 때" 4).
