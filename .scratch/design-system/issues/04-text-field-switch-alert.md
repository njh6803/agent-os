# 04: molecules 셋 — 글 입력, 스위치, 알림

**What to build:** 위젯과 관리 화면이 `@agent-os/ui`에서 글 입력, 스위치, 알림을 import해 쓴다. 글 입력은 라벨이 늘 보이고 오류를 아이콘과 글로 함께 알리며, 스위치는 라벨 전체가 누르는 곳이고 지금 상태를 켜짐·꺼짐 글로 보이며, 알림은 실패만 화면 읽기 프로그램을 끊고(`role="alert"`) 닫기 버튼을 둘 수 있다. 셋 모두 다섯 테마 × 두 모드에서 판정되고(Matrix, 모든 스토리의 클래스 판정, axe), 먹의 라이트·다크 정답 사진과 실제 입력의 상태 사진이 선다.

03과 나란히 돈다. 둘은 서로를 막지 않는다. 03과 04 가운데 마지막에 병합되는 쪽이 이 기능을 닫는다.

근거는 `.scratch/design-system/spec.md`의 "컴포넌트 아홉" 공통과 7~9, Testing Decisions의 글 입력·스위치·알림·폭 320px·모든 스토리 항목, 스토리 2·7·8·9·15와 그 2026-10-06 명세 검토·to-tickets 주석이다. 디자인 파일 v3의 02절(상태 표와 해부도)과 05절(props 표)이 원천이다. 01이 정한 props 타입의 모양(복합 컴포넌트가 나머지 속성을 어느 요소로 넘기는지 포함)과 파일 자리, 02가 정한 사진 비교 명령을 따른다. 알림의 닫기는 01의 아이콘 버튼이다.

**Blocked by:** 01, 02

**Status:** ready-for-agent

- [ ] **글 입력(`TextField`).** `<label>`과 `<input type="text">` 또는 `<textarea>`. 라벨로 찾는다(`getByLabelText`). 글을 넣으면 `onChange`가 값을 받는다. `variant` `"single"`(기본)은 높이 `control-m`, `"multi"`는 높이 88px 이상이고 세로로만 늘어난다. `error`이면 `aria-invalid="true"`이고, 테두리와 도움말이 `danger`이며, 도움말 앞에 `danger` 색의 `circle-x` 아이콘이 있다(디자인 파일이 아이콘을 이름으로 적지 않아 to-tickets가 정했다). 도움말과 오류는 `aria-describedby`로 이어진다. `optional`이면 라벨 옆에 "선택"이 보인다. 자리 글자는 라벨을 대신하지 않는다. `disabled`이면 쓸 수 없음의 색이 디자인 파일 상태 표대로다(바탕 `disabled-surface`와 `divider` 테두리, 글자·라벨 `disabled-text`)
- [ ] **스위치(`Switch`).** `<label>` 안의 `<input type="checkbox" role="switch">`. 라벨을 눌러도 바뀌고 `onChange`가 새 값을 받는다. 라벨 아래의 상태 글이 켜짐·꺼짐이다. `disabled`이면 바뀌지 않고, 쓸 수 없음의 색이 디자인 파일 상태 표대로다(트랙 `disabled-surface`와 `divider` 테두리, 손잡이와 글자 `disabled-text`). 트랙은 `switch-w`×`switch-h`(36×20px), 손잡이 12px, 줄 높이는 `row-touch`(48px) 이상이다. 꺼짐은 `raised` 트랙에 `border` 테두리와 `muted` 손잡이, 켜짐은 `accent`에 `on-accent` 손잡이다. 오류 상태는 없다
- [ ] **알림(`Alert`).** `<div>`. 실패(`tone="danger"`)는 `role="alert"`, 경고와 정보는 `role="status"`다. 톤마다 아이콘은 실패 `circle-x`, 경고 `triangle-alert`, 정보 `info`이고 `<tone>` 색이다(to-tickets가 디자인 파일의 아이콘 이름으로 정했다). 바탕은 `<tone>-tint`, 제목은 `text`, 본문은 `muted`다. `actions`는 버튼과 링크의 자리다. `onClose`가 있으면 투명·작은 아이콘 버튼 `x`가 있고 이름이 "닫기"이며 누르면 불린다. 알림 자체는 포커스를 받지 않는다
- [ ] **포커스 링**(스토리 2, 명세 검토). 글 입력, 스위치, 알림의 닫기 버튼 모두 Tab으로 포커스하면 outline이 `solid`이고 색이 `--focus`의 값이다. 알림 면 위의 포커스 링 짝은 Matrix가 이미 본다
- [ ] **스토리.** 컴포넌트마다 변형과 상태 prop의 조합(글 입력의 두 변형 × `help`·`error`·`optional`·`disabled`, 스위치의 켜짐·꺼짐·`disabled`, 알림의 톤 셋 × `actions`·`onClose`의 있음과 없음)을 스토리로 둔다. 01의 `afterEach`가 그 클래스까지 판정한다. globals `mode: "dark"`인 스토리가 컴포넌트마다 하나 이상이다. play가 있는 스토리의 `name`은 행동을 말하는 한국어 문장이다. 모든 스토리가 axe를 지난다
- [ ] **폭 320px.** 알림과 글 입력(두 변형)을 폭 320px의 자리에 그려 `scrollWidth`가 `clientWidth`를 넘지 않는다. 그 스토리는 각 컴포넌트의 스토리 파일에 둔다(03과 같은 파일을 고치지 않게)
- [ ] **`<Name>.md`.** 스토리 옆에 디자인 파일의 "쓰는 법"을 옮긴다
- [ ] **사진.** 새 스토리의 정답 사진을 02의 명령으로 컨테이너에서 만들어 커밋한다. 상호작용 컴포넌트의 실제 입력 상태를 02의 모양으로 더한다. 글 입력의 올림(`border-hover`)·키보드 포커스, 스위치의 올림·누름·키보드 포커스, 알림 닫기 버튼의 올림·누름·키보드 포커스다. 디자인 파일 상태 표가 없다고 적은 상태(글 입력의 누름, 알림 자체의 올림·누름·포커스)는 찍지 않는다. 바뀐 사진이 이 셋의 것뿐인지 본다
- [ ] **원칙 III.** `as`·`any`·`!` 없이 쓴다. 01이 정한 props 타입의 모양을 따르고, 따를 수 없으면 멈춰 보고한다
- [ ] `CLAUDE.md`의 검증 명령이 모두 초록이고 사진 비교 명령도 로컬에서 초록이다
- [ ] **이 기능을 닫는지는 병합 직전에 판정한다**(대기열 104의 한 줄 후보). `git fetch` 뒤 `origin/main`에서 03의 `Status`가 `done`이면 이 PR이 마지막 병합이다. 그때 `.scratch/plan.md`의 design-system 행을 `done`으로, 프론티어 줄을 고치고(web-widget과 admin-style이 풀린다), 두 행이 기다리던 것이 섰다고 적는다. main이 최신 기준이라 뒤에 병합되는 쪽은 앞의 병합을 들인 뒤에야 병합되므로 한쪽은 반드시 본다
