# 03: atoms 셋 — 상태 배지, 진행 표시, 카드

**What to build:** 위젯과 관리 화면이 `@agent-os/ui`에서 상태 배지, 진행 표시, 카드를 import해 쓴다. 상태 배지는 실행의 일시정지·끝남·실패·결말 없음을 아이콘과 용어집의 말로 보이고, 진행 표시는 값이 있거나 모르는 진행을 막대로 보이며 움직임 줄이기에서 멈추고, 카드는 내용을 올라온 면에 담는다. 셋 모두 다섯 테마 × 두 모드에서 판정되고(Matrix, 모든 스토리의 클래스 판정, axe), 먹의 라이트·다크 정답 사진이 선다.

04와 나란히 돈다. 둘은 서로를 막지 않는다. 03과 04 가운데 마지막에 병합되는 쪽이 이 기능을 닫는다.

근거는 `.scratch/design-system/spec.md`의 "컴포넌트 아홉" 공통과 4~6, Testing Decisions의 상태 배지·진행 표시·카드·폭 320px 항목, 스토리 3·6·14와 그 2026-10-06 명세 검토·to-tickets 주석이다. 디자인 파일 v3의 02절(상태 표와 해부도)과 05절(props 표)이 원천이다. 01이 정한 props 타입의 모양과 파일 자리, 02가 정한 사진 비교 명령을 따른다.

**Blocked by:** 01, 02

**Status:** ready-for-agent

- [ ] **상태 배지(`StatusBadge`).** `<span>`. `status`: `"paused"` | `"done"` | `"failed"` | `"no-outcome"`. 넷의 글자가 용어집의 말(일시정지, 끝남, 실패, 결말 없음)이고 아이콘(`circle-pause`, `circle-check`, `circle-x`, `circle-minus`)은 숨겨져 있다. 색이 쓰임새 토큰(`warning`/`warning-tint`, `success`/`success-tint`, `danger`/`danger-tint`, `muted`/`tint`)의 계산값이다. 높이 24px, `text-caption`. 누르는 곳이 아니다
- [ ] **진행 표시(`Progress`).** `<div role="progressbar">`(공통의 "브라우저 기본 요소" 문장의 예외. 명세의 주석). `value: number | null`, `max`(기본 1), `label`(보이는 이름이자 접근 이름), `tone`: `"accent"`(기본) | `"danger"`. `aria-valuenow`·`aria-valuemax`가 있고, 값을 모르면 `aria-valuenow`가 없다. 트랙은 `tint`, 막대는 `accent`나 `danger`, 높이는 `progress`(6px)다. 값을 모르면 막대가 `animate-progress`로 옮겨 다니고 `motion-reduce:animate-none`을 함께 쓴다
- [ ] **카드(`Card`).** `as`: `"div"`(기본) | `"section"` | `"article"`이 그 요소를 그린다. `elevation` `"0"`은 `box-shadow`가 `none`이고 나머지는 아니다. `padding`: `"3"` | `"4"`(기본). 바탕 `raised`, 테두리 `divider`, 모서리 `l`이다. 카드 전체를 누르는 곳으로 만들지 않는다
- [ ] **스토리.** 컴포넌트마다 변형과 상태 prop의 조합(배지 넷, 진행 표시의 값 있음·값 모름 × 톤 둘, 카드의 `as` 셋 × `elevation` 넷 × `padding` 둘의 대표)을 스토리로 둔다. 01의 `afterEach`가 그 클래스까지 판정한다. globals `mode: "dark"`인 스토리가 컴포넌트마다 하나 이상이다. play가 있는 스토리의 `name`은 행동을 말하는 한국어 문장이다. 모든 스토리가 axe를 지난다
- [ ] **폭 320px.** 카드를 폭 320px의 자리에 그려 `scrollWidth`가 `clientWidth`를 넘지 않는다. 그 스토리는 카드의 스토리 파일에 둔다(04와 같은 파일을 고치지 않게)
- [ ] **`<Name>.md`.** 스토리 옆에 디자인 파일의 "쓰는 법"을 옮긴다
- [ ] **사진.** 새 스토리의 정답 사진을 02의 명령으로 컨테이너에서 만들어 커밋하고, 바뀐 사진이 이 셋의 것뿐인지 본다. 셋은 상호작용 컴포넌트가 아니라 올림·누름·포커스 사진은 없다. 02의 움직임 줄이기 확인에 값 모름 진행 막대(`animation-name`이 줄이기에서 `none`, 아니면 `progress`)를 더한다
- [ ] **원칙 III.** `as`·`any`·`!` 없이 쓴다. 01이 정한 props 타입의 모양을 따르고, 따를 수 없으면 멈춰 보고한다
- [ ] `CLAUDE.md`의 검증 명령이 모두 초록이고 사진 비교 명령도 로컬에서 초록이다
- [ ] **이 기능을 닫는지는 병합 직전에 판정한다**(대기열 104의 한 줄 후보). `git fetch` 뒤 `origin/main`에서 04의 `Status`가 `done`이면 이 PR이 마지막 병합이다. 그때 `.scratch/plan.md`의 design-system 행을 `done`으로, 프론티어 줄을 고치고(web-widget과 admin-style이 풀린다), 두 행이 기다리던 것이 섰다고 적는다. main이 최신 기준이라 뒤에 병합되는 쪽은 앞의 병합을 들인 뒤에야 병합되므로 한쪽은 반드시 본다
