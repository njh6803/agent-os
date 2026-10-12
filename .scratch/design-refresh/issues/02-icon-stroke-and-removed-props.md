# 02: 아이콘의 선과 크기, 그리고 디자인이 없앤 prop 넷

**What to build:** 위젯과 관리 화면이 쓰는 `@agent-os/ui`의 아이콘이 크기와 상관없이 화면에서 1.5px의 선으로 그려지고, 크기는 14·16·20px 셋이다. 버튼은 더 이상 크기를 고르지 않는다(높이는 04에서 밀도가 정하고, 그때까지는 지금의 40px다). 카드는 그림자 없이 테두리로 선다. 진행 표시는 채움의 톤을 고르지 않고, 값을 모르면 끝을 모르는 막대 대신 도는 표시와 이름을 보인다. 움직임 줄이기를 켜면 그 도는 표시가 멈춘다. 디자인이 없앤 모양을 고르던 prop 넷(버튼의 `size`, 카드의 `elevation`, 진행 표시의 `tone`, 아이콘의 `"24"`)이 패키지의 계약에서 빠진다.

01과 나란히 돈다. 둘은 서로를 막지 않는다. 03이 둘을 기다린다. 아직 패키지를 들인 앱이 없어 prop을 빼도 고칠 앱의 호출은 없다. 패키지 밖에서 그 이름을 드는 것은 `.design-sync/`의 둘이다. `story-constants.js`는 이 티켓이 고친다. 사용 규약(`conventions.md`)이 안내하는 props(`size`, `tone`, `elevation`)는 05가 고친다. 그 검사기는 동기화 때만 돌아 그때까지 낡은 채 초록으로 남는다.

근거는 `.scratch/design-refresh/spec.md`의 "아이콘" 절, "컴포넌트 아홉"의 1(버튼)·3(아이콘)·5(진행 표시)·6(카드), Testing Decisions의 "컴포넌트 스토리"와 "빠지는 스토리와 단언", "문서와 설정" 절과 그 2026-10-12 명세 검토·to-tickets 주석이다. 모양의 원천은 디자인 파일 `.scratch/design-system/design/Agent OS Design System.dc.html`의 2절이고 `design.mjs --refresh`의 `components`가 상태 표와 치수를 낸다. props의 원천은 지금 코드이고 디자인 파일 5.2절의 props 표는 따르지 않는다(사용자가 골랐다).

**Blocked by:** None (can start immediately)

**Status:** done

### 아이콘

- [x] **선은 화면에서 1.5px이다.** lucide-react의 `nonScalingStroke`로 그린 요소마다 `vector-effect: non-scaling-stroke`를 달고 `strokeWidth`를 1.5로 둔다. `absoluteStrokeWidth`는 쓰지 않는다. 크기를 클래스로 주기 때문이다(명세가 lucide-react 1.51.0 설치본을 읽었다. 설치된 판이 다르면 그 파일을 다시 읽는다). 불러오는 중의 도는 표시도 같은 선이다
- [x] **크기는 셋이다.** `"14"`, `"16"`, `"20"`이고 기본은 `"20"`이다. `"24"`와 그 디자인 토큰(`icon-l`)을 뺀다. `IconName` 열여섯과 그 이름은 그대로다
- [x] **단언.** 아이콘 스토리가 그린 요소의 계산된 `vector-effect`가 `non-scaling-stroke`이고 `stroke-width`가 1.5인지 본다. 크기 셋의 폭이 14·16·20px인지 본다

### 디자인이 없앤 prop

- [x] **버튼의 `size`를 뺀다.** 타입 `ButtonSize`와 그 내보내기, 작은 크기의 스토리와 단언을 함께 뺀다. 높이는 지금의 조작 높이(40px)로 두고, 04가 밀도를 따르는 높이로 옮긴다. 아이콘 버튼의 `size`(`"m"`, `"s"`)는 그대로다(명세)
- [x] **카드의 `elevation`을 뺀다.** 카드는 그림자 없이(`box-shadow`가 `none`) 바탕과 테두리로 선다. 타입 `CardElevation`, 상수 `CARD_ELEVATIONS`와 그 내보내기, 그림자 단계의 스토리를 뺀다. `.design-sync/story-constants.js`가 그 상수를 다시 내보내므로 그 줄도 뺀다(남기면 다음 동기화의 빌드가 깨진다). 그림자의 디자인 토큰 `shadow-1`~`shadow-3`을 뺀다. 떠 있는 것의 그림자 `float`는 04가 더한다
- [x] **진행 표시의 `tone`을 뺀다.** 타입 `ProgressTone`과 위험 톤의 스토리를 뺀다. 채움은 한 색이다. 새 디자인의 채움은 `text-muted`이고, 그 이름은 03이 세운다. 그때까지는 지금의 흐린 글자색 쓰임새 토큰(`muted`)을 쓴다
- [x] **값을 모르면 막대 대신 도는 표시를 보인다.** `value`가 `null`이면 트랙을 그리지 않고 16px의 도는 표시(흐린 글자색)와 이름을 사이 8px로 보인다. `role="progressbar"`, 값을 모를 때 `aria-valuenow`가 없는 것, `value`·`max`·`label`은 그대로다. 도는 표시는 움직임 줄이기에서 멈춘다(`motion-reduce:animate-none`). 값 모름 막대의 움직임(`animate-progress`)과 그 keyframes를 뺀다. 스토리가 값을 모를 때 `aria-valuenow`가 없고 도는 표시가 있는지 본다
- [x] **움직임 줄이기의 사례를 다시 겨눈다**(명세 검토). 사진 비교의 움직임 줄이기 목록(`SPINNERS`)에 있는 값 모름 진행 막대의 사례를 지우지 않고, 진행 표시 안의 도는 표시와 그 움직임 이름(`spin`)으로 바꾼다. 줄이기에서 `animation-name`이 `none`이고, 아니면 `spin`인지 본다

### 사진과 문서

- [x] **사진.** 정답을 컨테이너에서 다시 만든다(`pnpm -C web visual:update`). 아이콘이 든 스토리는 선이 바뀌어 모두 다시 찍힌다. 없어진 스토리(버튼의 작은 크기, 카드의 그림자 단계, 진행 표시의 위험 톤)의 정답 사진은 지운다. 남은 사진이 모두 지금 스토리의 것인지 본다
- [x] **`<Name>.md`.** 아이콘, 버튼, 카드, 진행 표시의 쓰는 법에서 출처를 디자인 파일 v3에서 재탐색 디자인 파일로 바꾸고, 새 모양과 어긋나는 문장(선 굵기와 24px, 버튼의 크기, 카드의 그림자 단계, 진행 표시의 위험 톤과 값 모름 막대)을 고친다
- [x] **`.claude/rules/web-design.md`.** 이 티켓이 prop을 처음 빼므로 컴포넌트 공통의 props 문장을 고친다. "props 표(디자인 파일 05절)가 계약의 최소다"를, props는 지금 코드가 계약이고 재탐색 디자인 파일 5.2절의 props 표는 초안이라 따르지 않는다는 뜻으로 바꾼다. 아이콘의 선(크기와 상관없이 화면 1.5px)과 크기 셋, 카드에 그림자가 없다는 것도 고친다. 고친 rules는 새 세션에서 패키지의 파일을 Read해 실리는지 보고 일지에 적는다(`CLAUDE.md` 작업 규약 3)
- [x] **함께 고칠 말.** `ButtonSize`, `CardElevation`, `CARD_ELEVATIONS`, `ProgressTone`, `animate-progress`, `icon-l`, `shadow-1`, `shadow-2`, `shadow-3`, `1.75`, 그리고 대소문자를 가리지 않은 `elevation`이 살아 있는 문서와 코드에서 0인지 본다. 기록은 제외하고(명세의 잔존 grep 절), `.design-sync/`의 사용 규약과 NOTES, 관리 화면의 화면 프롬프트(`.scratch/admin-style/design/screens-prompt.md`)는 05가 고친다
- [x] **원칙 III.** `as`·`any`·`!` 없이 쓴다. design-system 티켓 01이 정한 props 타입의 모양(`props.ts`의 머리 주석)을 따른다
- [x] **이 기능의 첫 병합인지는 병합 직전에 판정한다.** `git fetch` 뒤 `origin/main`의 `.scratch/plan.md`에서 design-refresh 행이 아직 `todo`이면(01이 먼저 병합되지 않았으면) 이 PR이 `in-progress`로 바꾼다
- [x] `CLAUDE.md`의 검증 명령이 모두 초록이고 사진 비교 명령도 로컬에서 초록이다(`packages/ui`를 건드린다)

### 이 티켓이 정할 것

PR에서 사용자가 이름과 모양을 본다. 결정과 근거는 일지에 적고, 여기에 "이 티켓이 정한 것" 절을 더한다.

1. 값을 모르는 진행 표시의 구조(progressbar 요소 안에서 도는 표시와 이름의 배치, 그리고 값을 아는 막대와 같은 자리를 차지하는지)
2. 움직임 줄이기 사례가 겨누는 도는 표시의 위치

### 이 티켓이 정한 것

근거와 고른 까닭은 일지 2026-10-13-05이다.

1. **값을 모르는 진행 표시는 progressbar 요소 안의 한 줄이다.** 자식은 도는 표시(svg)와 이름(span) 둘이고 그 차례이며 트랙이 없다. 사이는 8px(`gap-2`)이고 세로 가운데에 맞춘다. 도는 표시를 앞에 둔 것은 디자인 파일의 표본이 회전 아이콘을 이름 앞에 그렸기 때문이다. 도는 표시의 색은 progressbar 요소의 `text-muted`가 물려주고, 이름은 값을 알 때와 같은 span(`text-small text-text`)이다. **막대와 같은 자리를 차지하지 않는다.** 줄의 높이는 이름 한 줄(20px)이고 막대 모양(이름 20 + 사이 8 + 트랙 6 = 34px)보다 낮아, 값을 알게 되면 사이와 트랙만큼(14px) 자란다. 디자인 파일이 막대와 회전을 다른 모양으로 그리고(props 표의 `kind`), 비워 둔 트랙 자리는 막대가 빠진 것처럼 보이기 때문이다.
2. **움직임 줄이기 사례는 progressbar 요소의 직계 svg 하나를 겨눈다.** 선택자는 `[role=progressbar]:not([aria-valuenow]) > svg`이고 움직임 이름은 `spin`이다. progressbar의 자식 가운데 svg는 도는 표시 하나뿐이라, 사례의 `toHaveCount(1)`이 그것만 잡는다.
