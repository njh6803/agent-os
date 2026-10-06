# 2026-10-06 (13) design-system 명세: 탐색의 v3를 받아 디자인 토큰과 판정의 자리를 정한다

일지 2026-10-06-12의 세션이 낸 지시문으로 연 새 세션이다. 워크트리 `.claude/worktrees/design-system-spec`이고
origin/main(`eff1542`)에서 `docs/design-system-spec`을 땄다. 순번은 main과 형제 워크트리의 `docs/journal/`에 13이 없어
13이다. 주 체크아웃은 main(`eff1542`)이고 이 세션은 당기지 않았다.

## 탐색 결과를 받는다

지시문의 "이어받을 상태"대로 내려받기 전에 탐색이 끝났는지 물었다.

> 사용자(질문에 답): "v3 로 만들었어"

지시문의 링크는 v2 파일을 가리켰다. 내장 브라우저가 로그인 화면에서 멈춰 사용자가 그 창에서 로그인했다(대신하지 않았다).
`file=`을 뗀 프로젝트의 파일 목록에는 `Agent OS 디자인 시스템 v3.dc.html`과 `support.js`만 있었다. Claude Design의 대화를
글로 읽으니 사용자가 v3 말고는 지우라고 했고, 문서 정리(기초 → 컴포넌트 → 패턴 → 화면 → 구현 연결)가 v3에 들어가
있었다. 붙여 넣은 글은 앞 판(`<기본 테마 이름>` 자리표시와 "허가와 사유를 붙인 거부")이었는데, Claude Design이 기본
테마를 먹으로 두고 버튼 글자를 앞서 정한 "승인"으로 두었다고 답해 둔 상태였다.

내보내기는 디자인 파일을 연 채 Share → Export → Project HTML이었고, 창이 Project archive(ZIP, 바로, 사용량 없음)와
Standalone HTML(Claude가 합침, 사용량 한도를 씀)을 물었다. 파일 이름·출처를 보이고 내려받기 허락을 받은 뒤 둘을 물었다.

> 사용자(질문에 답): "Project archive (Recommended)"

내려받기를 누르자 다운로드 폴더에 `<GUID>.tmp`(64,556바이트, ZIP)가 생겼고 사용자의 화면에는 Windows 저장 창이 떠 있었다.
`unzip`으로 세 파일이 다 든 것을 본 뒤 정해진 자리(`C:\project\Agent OS 디자인 시스템 v3.zip`)로 옮겼다.

> 사용자: "파일 저장뜨던데 tmp파일로 그냥 진행해도 되나?"

된다고 답했다. 임시 파일은 이미 옮겼고 `unzip -t`가 초록이었으니 창은 취소하면 된다고 했다.

> 사용자: "그러 파일 저장 창이 뜨면 바로 취소 누르면 안되겠네?"

맞다고 답했다. 옮기기 전에 취소하면 Chromium 계열은 보통 임시 파일을 지운다(일반 동작이고 재지 않았다). 다음부터는
그 창에서 정해진 자리를 고르면 된다. 이 동작을 `exploration-prompt.md`의 하는 법 4와 "고른 뒤" 1·2, 런북
`kickoff/prompting.md`의 사람에게 남기는 일에 적었다. "확인하지 않았다"로 남았던 내장 브라우저의 내려받기가 이것으로 닫혔다.

## 고른 뒤 2~5

- 파일: ZIP에서 `.dc.html`과 `support.js`를 `design/`으로 옮겼다(`.thumbnail`은 뺐다). 줄 구분 문자 검사에 걸릴 글자는
  없었다. 표의 기준 커밋은 하는 법의 명령(`--until`을 `--` 앞에)으로 `eff1542`이고 "(어림)"을 붙였다. 붙여 넣은 3단계 글이
  PR #152 브랜치의 것이라 그 병합 커밋과 같다.
- 기본 테마: Claude Design의 추천을 보이고 물었다.

> 사용자(질문에 답): "먹 (Recommended)"

- 글꼴: 다섯 테마 모두 한글은 Noto Sans KR이고 고정폭만 JetBrains Mono(먹·공문·자두)와 IBM Plex Mono(청록·황토)로
  갈렸다. 예약 글꼴 이름은 Noto Sans KR이 `Source`뿐, JetBrains Mono는 없음, IBM Plex는 `Plex`이고 google/fonts의 사본에도
  그대로였다(라이선스 원문을 읽었다). 그래서 IBM은 저자의 패키지를 골랐는데, `@ibm/plex-mono` 2.5.0이 postinstall로
  `ibmtelemetry`를 돌려 pnpm 11이 설치를 멈췄다.

> 사용자(질문에 답): "@ibm/plex-mono, 스크립트 끔 (Recommended)"

## 값을 뽑는 길

디자인 파일에는 hex가 글자로 없다. 파일 끝의 스크립트가 테마마다 (색상각, 채도)와 고정된 밝기 단계 열하나로 OKLCH에서
hex를 계산하고(sRGB 밖이면 채도를 줄인다), 같은 스크립트가 디자인 토큰 JSON과 대응표를 만든다. 그 스크립트를 그대로 돌리는
`probes/tokens/design.mjs`를 두었다. 명세는 hex 330개를 다시 적지 않고 이 길을 원천으로 가리킨다.

## 이음매와 측정

to-spec 2단계대로 이음매를 물었다. ADR 0026은 명암비를 단위 테스트로 적었는데, 이음매를 하나로 두려면 브라우저의
계산값으로 재야 했다.

> 사용자(질문에 답): "스토리 테스트 하나 (Recommended)"

to-spec 3단계의 측정 규칙(설계의 ADR이 넘긴 측정도 명세가 받는 자리에서 잰다)대로, ADR 0026이 첫 티켓에 넘긴 넷 가운데
GitHub 러너를 뺀 셋과 셋째 이력이 넘긴 둘을 쟀다. 앞 세션의 `storybook/setup.mjs`로 저장소 밖에 사본을 새로 짓고
`tokens/setup.mjs`가 그 위에 두 층 CSS·글꼴·표본을 얹었다. 결과는 `probes/README.md`의 "결과 — tokens"이고, 고쳐 가며
알게 된 것은 여섯이다.

- `@source "../components"`로 두자 스토리 파일에 쓴 `flex`가 CSS를 만들지 않았고 판정 함수가 그것을 잡았다.
- `--spacing`을 비우면 `p-5`·`w-64`는 `calc(var(--spacing) * n)`조차 만들지 않았다. 그래서 정의 없는 `var()` 판정은
  임의값 판정이 이미 잡는 것만 잡았고, 명세에서 뺐다.
- Next의 글꼴 `url()`은 CSS에서 `../media/…` 상대 경로였다. 프로브가 이것을 `static` 기준으로 풀어 778개 모두 없다고 셌다
  (`next start`의 응답은 모두 200이었다). 프로브의 버그였고 고쳤다.
- 스토리의 `userEvent`는 합성 이벤트라 `:hover`·`:active`가 걸리지 않았다. 그래서 올림과 누름은 사진 비교가 Playwright의
  실제 입력으로 본다. 그 측정도 처음에는 누른 뒤 `blur()`하고 Tab을 눌러 버튼에 포커스가 가지 않았다(순차 탐색의 출발점).
- 사본의 `pnpm verify`가 정적 빌드의 번들에서 lint로 실패했다. ADR 0026이 이미 적은 `.gitignore` 조건과 같아 명세의
  설치 조건에 그대로 두었다.
- 디자인 파일이 재지 않은 짝 가운데 컴포넌트가 쓰는 것(알림 제목, 진행 막대)을 더했다. 셀프 리뷰 뒤 알림 안 포커스 링을
  더하고 쓰지 않는 성공 알림 짝을 빼 43개가 됐다.

셀프 리뷰가 빠진 측정을 짚어 셋을 더 쟀다(아래 셀프 리뷰 절).

- Linux 빌드: 같은 이미지의 컨테이너 안에서 설치하고 지은 정적 빌드가 Windows 빌드의 정답 14장을 바이트까지 같게 지났다.
  CI가 Linux에서 지어도, 로컬이 Windows에서 지어도 정답 한 벌이 선다.
- 움직임: 기본값을 비우면 `animate-spin`과 keyframes도 사라진다. 우리 값 둘을 두자 돌았고 움직임 줄이기에서 멈췄다.
  그 표본의 `inset-y-0`이 규칙을 만들지 않아, `--spacing`을 비우면 0조차 사라진다는 것도 알았다. 간격에 `0`을 둔다.
- 속성 없는 기본값: 데코레이터가 늘 `data-theme`을 달아 "속성 없으면 먹"을 재지 않았었다. 지운 뒤 재니 문서 뿌리와 shadow
  호스트 모두 먹이었다.
- Noto Sans KR의 조각 수는 웹 요약에서 받은 127이 아니라 124였다(패키지 CSS를 셌다).

## ADR

결정 넷(글꼴 패키지라는 새 의존성, 명암비의 자리, 없는 클래스를 잡는 법, 사진 비교 도구)과 잰 것을 ADR 0026의 넷째 이력으로 적고
본문의 다섯 문장에 포인터를 달았다. 초안을 보이고 물었다.

> 사용자(질문에 답): "승인"

## 바꾼 것

- `.scratch/design-system/spec.md`: 새 명세(Status: ready-for-agent).
- `.scratch/design-system/design/`: v3 디자인 파일과 `support.js`, `README.md`의 기본 테마와 표, `exploration-prompt.md`의
  하는 법 4와 "고른 뒤" 1·2(내보내기 메뉴, Project archive, 저장 창과 `.tmp`, `file=`이 지난 판을 가리킬 때).
- `.scratch/design-system/probes/tokens/`: `design.mjs`, `setup.mjs`, `measure.mjs`, `visual.mjs`(+ 설정과 스펙), 표본
  `ui/`. `probes/README.md`에 명령, 표 한 줄, 결과 절.
- `docs/adr/0026-…`: 넷째 2026-10-06 이력과 포인터 다섯.
- `docs/constitution/tech.md` 웹 행: 글꼴 패키지 셋과 사진 비교 도구. `docs/constitution/README.md` 3.0.14.
- `.scratch/plan.md`: design-system 행(명세가 정한 것, 다음은 to-tickets), web-widget·admin-style 행(명세가 넘긴 것),
  프론티어 줄.
- `kickoff/prompting.md`: 저장 창과 임시 파일 한 문장.

## 셀프 리뷰

`/code-review`(base `eff1542`, 바뀐 파일 7, 커밋 0, 미추적 4묶음)를 두 축 모두 sonnet으로 나란히 돌렸다. 표준 축 12건,
명세 축 15건이었다.

- **고쳤다, 표준 축.** 헌법 버전을 3.0.14로 올렸다(`tech.md`를 바꾸면 patch). `exploration-prompt.md`의 "구현 티켓의 단위
  테스트가 열 벌 … 다시 계산한다"가 남아 있었다. 근거의 종류가 틀린 문장 일곱을 고쳤다. 손으로 셈한 4.59와 락의 패키지
  6개에 그 표시를, 사본의 `pnpm verify`를 프로브의 명령 차례에, 첫 실행에서만 본 `@source`의 `flex`에 "손으로 봤다"를
  달았다. 웹 요약에서 받은 조각 127개는 세어 보니 124개였다. "속성 없는 호스트는 먹"은 재지 않았던 것이라 쟀고, "기준 폭은
  둘뿐"은 표본이 쓴 것만 시트에 들어 참일 수밖에 없는 문장이라 고쳐 썼다. 수와 경로도 고쳤다: 대응표의 "열둘"은 판정하는
  열 열, Fontsource `@import`는 다섯, ADR 이력의 결과 README 경로. "남은 측정은 러너"라는 닫힌 주장, 단독 "토큰" 다섯
  자리, `support.js`의 표 행(디자인 파일마다 한 줄로 적었다), 스토리 이름의 한국어 규칙(play가 있는 스토리는 `name`)도
  고쳤다. 기대값 계산이 `setup.mjs`와 `measure.mjs`에 두 벌이라 `design.mjs`로 모았고, `plan.md`의 design-system 행은
  명세를 가리키는 짧은 행으로 줄였다.
- **고쳤다, 명세 축.** ADR이 넘긴 측정을 다시 넘긴 것(Linux 정적 빌드)을 쟀다. 기본값을 비우면 사라지는 움직임을 디자인
  토큰 둘로 두고 쟀다. 임의값 금지와 부딪히는 부품 치수(36·20·48·6·88px)를 이름 있는 간격으로 두었다. 320px 리플로와
  움직임 줄이기의 시험을 정했고, 알림 면 위 포커스 링 짝을 더하고 성공 알림 짝을 뺐다. shadow의 판정은 ADR대로 문서의
  시트를 끈 채 하게 고쳤다. "테마마다 값이 다르다"(먹과 공문의 위험·성공이 같다), "용어집의 말 넷"(여덟이고 켜짐·꺼짐은
  관리 화면의 문구다), props의 `children`·`onClick` 누락, 구현 파일 경로를 고쳤다. admin-style 행에 03.2를, web-widget
  행에 Vite 라이브러리 모드와 폭마다의 사진을 적었다. 예약 글꼴 이름의 출처를 프로브 README의 "읽은 것"에 적었다.
- **남겼다.** `measure.mjs`의 shadow 탐색 두 벌(서로 다른 페이지 문맥이다), 프로브의 `CONTRAST_PAIRS` 위치 튜플(프로브에만
  있고 `as const` 튜플을 이름으로 풀어 쓴다. 명세는 모양을 정하지 않는다), KoreanSample에서 고정폭 400이 적재된 것(측정
  출력에 있다). `exploration-prompt.md`와 런북의 내려받기 문장은 요청 밖이라는 지적을 받았지만, "고른 뒤" 1이 "확인하지
  않았다"로 남긴 것을 이 세션이 확인한 것이고 사용자가 물은 것이라 두었다. 명세의 선택자 목록은 프로브가 낸 모양이라
  to-spec의 프로토타입 예외로 두고 절 머리에 출처를 적었다.

## 검사

- 검증 명령: `uv run pytest -q` 1638 통과(7 deselected), `ruff check`·`ruff format --check`, `pyright`, `lint-imports`,
  `pnpm -C web verify`(이 워크트리에서 `pnpm -C web install --frozen-lockfile` 뒤) 모두 초록.
- 지침·ADR 포인터·줄 구분 문자·표 검사가 바뀐 파일과 새 파일에서 초록. 인용 대조는 경고 없음.
- 프로브: 표본을 얹은 사본의 `pnpm verify` 여섯 단계 통과(288개), `measure.mjs`와 `visual.mjs`의 마지막 실행 결과가
  `probes/README.md`의 결과 절과 같다.

## PR 리뷰

PR #153의 claude-review는 지적이 없었다. CodeRabbit은 Trivial 하나를 냈다. 사진 비교 이미지를 태그만으로 고정하면 같은
태그가 다시 빌드될 때 정답 사진이 모두 깨질 수 있어 digest까지 붙이라는 것이고, 명세의 사진 비교 절에 반영했다(값은 사진
비교 티켓이 적는다). CodeRabbit CLI는 좌석이 없어(`Seat: not assigned`) PR 전에 돌지 않았다.

## 회고

후보 다섯을 냈고 넷이 승인됐다.

> 사용자(질문에 답): "1 웹 요약은 근거 아님,2 넘긴 측정의 이유,3 ADR 승인은 리뷰 뒤,5 대기열 122 회차"

1. **웹 요약의 수를 근거로 적었다.** WebFetch의 요약 모델이 준 "`@font-face` 127개"를 명세와 ADR에 사실로 적었고, 셀프
   리뷰가 근거 없음을 짚어 세어 보니 124개였다. 대기열 124(`docs/agents/issue-tracker.md` 프로브와 근거 절).
2. **넘긴 측정의 이유를 적지 않았다.** Linux에서 지은 정적 빌드를 "첫 CI가 본다"고 넘겼는데 로컬 Docker로 잴 수 있었다.
   to-spec에 규칙(38·61)이 있는데도 어긴 것이라 리뷰 층에 둔다. 대기열 125(`spec-reviewer` 체크리스트).
3. **ADR 승인을 셀프 리뷰보다 먼저 물었다.** 리뷰가 승인받은 이력의 수와 근거를 고쳤다. 결정은 바뀌지 않았고 PR 본문에
   고친 자리를 적는다. 대기열 126(to-spec).
4. **프로브가 전부 실패를 내면 프로브부터 의심한다.** Next의 글꼴 778개 "없음"과 Tab 포커스 10/10 실패가 프로브의
   버그였고 독립된 신호(`next start`의 응답 200)로 잡았다. 일지에만 남긴다.
5. **워크트리 가드(대기열 122).** `docker images --format "{{…}}"`, 변수가 든 `sed`, 긴 `node -e`가 git이 아닌데도
   거부됐다. 122에 6회차를 더했다.

## 다음

- **PR의 병합.** 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다. 주 체크아웃은
  main(`eff1542`)에서 당기지 않았다.
- **design-system의 다음은 to-tickets다.** 명세 검토(`spec-reviewer` 서브에이전트)를 먼저 돈다. 측정 사본은 이 세션의
  스크래치에 있어 다음 세션에는 없다. 다시 재려면 `probes/README.md`의 명령 차례를 처음부터 돈다(설치 셋이 npm에 닿는다).
- **ADR 0026 넷째 이력은 승인 뒤 리뷰가 수와 근거를 고쳤다.** 결정 넷은 그대로다. 고친 자리는 PR 본문에 적었다.
- 정해진 자리(`C:\project`)의 `Agent OS 디자인 시스템 v3.zip`은 그대로 두었다.
