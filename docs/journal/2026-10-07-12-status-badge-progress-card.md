# 2026-10-07 (12) design-system 티켓 03: 상태 배지·진행 표시·카드

일지 2026-10-07-03의 "다음"으로 연 새 세션이다. 04(글 입력·스위치·알림)와 나란히 여는 둘 가운데 첫째라, 지시문대로 주
체크아웃에서 `tidy-checkouts`를 먼저 돌고 `EnterWorktree`로 `.claude/worktrees/03-status-badge-progress-card`에 들어가
origin/main(`49d9630`)에서 `feature/03-status-badge-progress-card`를 땄다. 순번은 main의 09, 나란히 도는
`tidy-checkouts-tool` 워크트리의 10, 주 체크아웃에서 커밋 전인 11(`checkout-persist-credentials`) 다음이라 12다.

## 정리

`tidy-checkouts`는 루트를 옮기지 않았다. 루트가 `chore/checkout-persist-credentials`에 있고 `ci.yml`이 고쳐진 채였으며
(PR 없음) 그 일을 하는 세션이 돌고 있었다. 루트의 HEAD는 `origin/main`과 같았다. 판정 3에서 제목이 체크아웃된 어느
브랜치와도 맞지 않는 실행 중 세션("Disable checkout credential persistence in CI jobs")이 있어 워크트리는 하나도 지우지
않았고, 어디에도 체크아웃되지 않은 병합된 로컬 브랜치 다섯(`chore/canary-procedure-and-runner`,
`chore/hook-registration-fail-open`, `chore/mutate-any-runner`, `chore/mutate-restore-guard`, `docs/design-system-tickets`)만
지웠다. 병합되고 깨끗한 워크트리 아홉, 무시된 빌드 산출물(`dist/`, `storybook-static/`)이 남은 01·02, 반쯤 지워진
`05-admin-hides-decision-for-end-user`, 분리 HEAD 하나, 등록 없는 폴더 여섯은 보고만 하고 지시문을 이었다.

## 이 세션이 정한 것

티켓 파일의 "이 티켓이 정한 것" 절이 원천이고 여기는 근거다.

- **배지는 `w-fit`이다.** 처음 만든 사진 31장을 손으로 보다가 폭 320px 카드 안의 배지가 카드 폭(286px)만큼 늘어난 것을
  찾았다. 카드가 `flex flex-col`이라 자식이 가로로 늘어난다. 카드의 정렬(`items-start`)을 바꾸면 04의 글 입력처럼 폭을
  채워야 할 자식도 줄어들어, 배지 쪽을 고쳤다. `self-start`는 가로 묶음(`items-center`)에 놓인 배지의 세로 정렬까지 바꾸므로
  고르지 않았다. 고치기 전에 카드의 320px 스토리에 배지의 폭이 카드 폭의 반보다 작은지 보는 단언을 더해 `expected 286 to be less
  than 159`로 빨간 것을 봤다. 고친 뒤 바뀐 사진은 그 스토리의 둘뿐이었다(사진 31장의 md5를 앞뒤로 견줬다).
- **진행 표시는 바깥 요소가 progressbar다.** 디자인 파일의 그림은 이름 줄과 트랙을 감싼 `div` 안에 트랙이 있지만, props 표의
  요소가 `<div role="progressbar">`이고 이름이 `aria-label`이다. 그래서 progressbar가 이름 글자와 트랙을 함께 담고 01의
  규칙대로 나머지 속성을 받는다. progressbar의 자식은 접근성 트리에서 꾸밈이라 이름을 두 번 읽지 않는다는 것은 ARIA의
  정의에서 나온 어림이다(화면 읽기 프로그램으로 듣지 않았다).
- **값 모름 막대는 멈추면 35%에 선다.** 01이 둔 `progress` keyframes는 `left`를 -30%에서 100%로 옮긴다. 움직임이 없으면
  `left`가 정해지지 않아 왼쪽에 붙고, 그러면 값이 30%인 막대와 같아 보인다. `left-7/20`을 두어 움직임 줄이기와 사진(Playwright가
  무한 움직임을 멈춰 찍는다)에서 디자인 파일의 정지 그림처럼 가운데에 서게 했다. 사진 변이가 그것을 지킨다(아래).
- **카드의 테두리는 `border`다.** 디자인 파일은 테두리를 inset 그림자(`inset 0 0 0 1px var(--divider)`)로 그렸는데, 그 모양이면
  elevation `"0"`에도 `box-shadow`가 남아, `"0"`이면 `box-shadow`가 `none`이어야 한다는 티켓의 요구와 맞지 않는다.
- **`SPINNERS`는 이름을 두고 항목의 모양만 바꿨다.** `.claude/rules/web-design.md`가 이 이름을 가리키므로 이름을 바꾸면
  rules를 고치고 새 세션에서 다시 불러 봐야 한다. 이 PR은 rules를 고치지 않는다.

## TDD와 변이

스토리 셋(17개)을 컴포넌트보다 먼저 써서 돌렸고, 세 파일 모두 vitest의 `Failed to import test file`로 빨갰다. 이 빨강은 모듈이 없어서라
단언 하나하나의 이빨은 재지 않는다. 그래서 구현 뒤에 변이 표 `.scratch/design-system/probes/atoms_mutations.toml`(지금
33개)을 돌렸다. 스토리 테스트 30개는 단언마다 하나씩(글자, 숨은 아이콘, 쓰임새 토큰의 색, 높이, Tab, `aria-valuenow`·`aria-valuemax`,
`value`·`max`의 기본값, 이름, 보이는 이름, 막대 비율, 톤, 트랙의 높이와 바탕, 움직임, `as`, elevation 셋, padding, 테두리, 모서리, 320px의
넘침과 배지 폭)이고, 새 컴포넌트의 클래스와 새 스토리의 그림에 afterEach의 클래스 판정이 걸리는지도 하나씩 본다. 사진 쪽 셋은
값 모름 막대의 움직임 줄이기, 멈춘 막대의 자리, 배지의 아이콘과 글자 사이다. 첫 판 32개가 모두 기대대로 빨갰고 기준선 열일곱이
모두 초록이었다(로그의 `기준선` 줄을 셌다). 14:16에 띄워 14:23에 끝났다(로그 파일의 만든 시각과 마지막 쓴 시각). 셀프
리뷰를 반영하며 진행 표시의 시그니처와 배지 스토리가 바뀌어(아래) `value` 기본값의 변이를 더한 33개를 다시 돌렸고, 33개 모두
기대대로였으며 기준선 열일곱이 초록이었다(14:41:54에 띄워 14:50에 끝났다).

변이 표를 처음 쓸 때 원문 넷이 `--check`에서 걸렸다. TOML의 `'''` 여러 줄 문자열은 닫는 따옴표 앞의 줄바꿈을 원문에 넣어, 줄의
일부만 적은 원문(`Math.max(value / max, 0)` 등)이 실제 줄과 맞지 않았다. 온전한 줄로 고쳤다. 02의 변이 표가 `-g
"atoms-button--loading 의 도는"`으로 움직임 테스트의 이름을 겨누므로 테스트 이름의 앞부분을 그대로 두었고, 표 셋(`ui`, `visual`,
`atoms`)의 `--check`가 모두 지났다.

## 사진

새 스토리 17개의 정답 사진 31장을 `pnpm -C web visual:update`로 컨테이너 안에서 만들었다(다크 스토리는 다크 한 장씩). 만들기 전의
`pnpm -C web visual`은 그 17개가 "A snapshot doesn't exist"로 빨갛고 나머지 36개(새 움직임 테스트 포함)가 지났다. 기존 79장은
바뀌지 않았다(`git status`에 고친 사진이 없다). 배지 넷의 라이트·다크, 값 있음·값 모름 막대, 다크의 위험 막대, 그림자 넷의
라이트·다크, 320px 카드를 손으로 봤다. 다크의 그림자는 바탕과 대비가 작아 거의 보이지 않는다. `--shadow-color`의 값대로다.

## 셀프 리뷰

`/code-review`(base `49d9630`, 고친 파일 3, 미추적 11과 사진 31, 커밋 0)를 두 축 나란히 돌렸다. 소스가 든 변경이라
sonnet으로 내리지 않았다. 두 축 모두 Critical·Major는 없었다. 표준 축은 Minor 8·Nit 4, 명세 축은 Minor 3·Nit 5였고 겹치는
것이 셋이었다.

- **고쳤다.**
  - 진행 표시의 `value`가 필수였다. props 표의 기본값은 `null`이다(두 축). 값 모름 스토리가 `value`를 넘기지 않게 바꿔 tsc가
    TS2322로 빨간 것을 본 뒤 기본값을 두었다. 그 기본값을 겨누는 변이를 하나 더했다(33개).
  - 진행 표시가 `aria-valuemin`을 받아 쓰는 쪽이 최소값을 덮을 수 있었다. 막대는 최소값을 0으로 두므로 받지 않는다.
  - `Progress.tsx`의 "자식은 꾸밈"이 어림인데 사실처럼 적혔다(어림이라고 적었다).
  - `Card.md`의 "줄은 카드의 폭을 채운다"에 같은 diff의 배지라는 반례가 있었다.
  - 프로브 README에 새 변이 표의 행이 없었다(두 축).
  - 02 티켓의 "값 모름 진행 막대는 03이 같은 자리에 더한다"가 미래형으로 남았다(두 축. 날짜 주석을 달았다).
  - 배지 스토리의 render 둘과 기대값 두 벌이 겹쳤다(상태별 기대값 맵 하나로 모았다).
  - `SPINNERS` 주석이 목록을 전부처럼 적었다(컴포넌트마다 하나라고 고쳤다).
  - 변이 표 주석이 `divider`가 `tint`와 같다는 근거로 규칙 파일을 들었는데 그 규칙은 `disabled-surface`만 적는다(theme.css로
    고쳤다).
  - 일지의 따옴표 인용 둘이 원문과 달랐다(인용을 풀었다).
  - 티켓의 `Status`가 아직 `ready-for-agent`였다(`done`).
- **확인하고 고치지 못했다.** 카드의 나머지 속성이 `div`의 것이라 section·article에서도 ref와 이벤트가 `HTMLDivElement`로
  적힌다. 셋이 함께 지는 `HTMLElement`의 속성(`NativeProps<"section">`)으로 바꾸자 그 ref가 div의 ref에 맞지 않아 tsc가
  TS2322로 거부했다. 다형 제네릭은 타입 단언 없이 넘기기 어렵다(원칙 III). TypeScript 5.9의 lib.dom을 읽으니 다른 것은
  낡은 `align` 하나라 `div`의 것으로 두고 그 사실을 주석과 티켓에 적었다.
- **근거를 보고 두었다.**
  - 변이 이름의 "모두"(라이트·다크, 값 있음·값 모름)가 판정보다 세다는 지적은 두 변이 모두 로그가 실패한 스토리 둘을 이름으로
    들어 맞다.
  - `Progress.md`의 "움직임 줄이기 설정이면 가운데에 멈춘다"에서 줄이기 경로가 재는 것은 animation-name뿐이다. 자리는 멈춘
    사진의 변이가 잰다. 움직임이 없을 때 `left-7/20`이 서는 것은 같은 규칙이라 두었다.
  - `ELEVATION_CLASS`의 앞 공백은 `Button.tsx`의 `LIVE_CLASS` 이어 붙이기와 같은 모양이다.
  - `${what}가`의 조사는 두 값이 모두 모음으로 끝난다.
  - `aria-valuenow`를 끝 값 밖에서 자르지 않는 것은 범위 밖의 값을 넘기는 쪽의 몫으로 두었다. `max`만 0이면 `value / max`가
    Infinity라 막대가 꽉 차고, `value`와 `max`가 모두 0이면 폭이 `NaN%`라 막대의 폭이 서지 않는다(코드를 읽은 어림. 그려 보지
    않았다).
  - `SPINNERS`라는 이름이 이제 진행 막대도 담는다. 이름을 바꾸면 `.claude/rules/web-design.md`를 고치고 새 세션에서 불러 봐야
    해서, rules를 고치는 다음 하네스 일에 묶는다.
- **사용자가 볼 것.** 디자인 파일의 진행 표시는 이름 옆에 "지금 하는 일"(고정폭 흐린 글자, 예: `orders.search`)을 그리는데
  props 표에는 없어 두지 않았다. 쓰는 쪽은 그것을 `label`에 담거나 진행 표시 밖에 둔다.

## 검사

- 검증 명령(리뷰 반영 뒤): `uv run pytest -q` 1750 통과(7 deselected), `ruff check`·`ruff format --check`, `pyright`,
  `lint-imports`, `pnpm -C web verify`(25파일 329개) 모두 초록. 사진 비교 `pnpm -C web visual` 53개 통과(스토리 사진 40, 실제 입력
  6, 미디어 특성 6, 정적 빌드의 경로 1). 판정 명령은 파이프 없이 돌리고 로그 파일로 봤다. web 파일만 바꿔 LLM 테스트와 e2e는 돌리지 않았다(중계·시작
  래퍼·api-client·서버 라우트를 건드리지 않는다).
- 커밋 직전에 `git fetch` 뒤 `HEAD..origin/main`이 비었고, 나란히 도는 04의 워크트리가 일지 13을 쓰고 있어 순번이 겹치지
  않았다.
