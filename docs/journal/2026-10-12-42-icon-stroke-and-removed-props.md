# 2026-10-12 (42) design-refresh 02: 아이콘의 선을 화면 1.5px로 하고 디자인이 없앤 prop 넷을 뺀다

## 계기

일지 2026-10-12-36의 "다음"이 design-refresh의 티켓 01과 02를 나란히 구현하는 것이었다. 이 세션은 나란히 여는 둘 가운데
둘째라 `tidy-checkouts`를 돌지 않고(첫 세션이 돈다), 지시문의 "어디서"대로 주 체크아웃에서 브랜치를 따지 않은 채
`EnterWorktree(name=02-icon-stroke-and-removed-props)`로 `origin/main`(`6b439aa`)에서 워크트리를 만들고 브랜치를
`feature/02-icon-stroke-and-removed-props`로 바꿨다.

> 사용자: "다음 작업: .scratch/design-refresh/issues/02-icon-stroke-and-removed-props.md. 아이콘의 선을 화면 1.5px로 하고 디자인이 없앤 prop 넷을 뺀다"

## 어떻게 했나

- **아이콘의 선.** lucide-react 1.51.0(설치본이 명세가 읽은 판과 같다)의 `nonScalingStroke`를 `Icon`과 `Spinner`에 주고
  `strokeWidth`를 1.5 하나로 두었다. 설치본의 `buildLucideIconNode.mjs`가 그린 요소마다 `vector-effect: non-scaling-stroke`를
  달고, `Icon.mjs`가 그 prop을 그대로 넘기는 것을 읽었다. 같은 판의 타입 선언은 `absoluteStrokeWidth`를 `@deprecated`로 적고
  `nonScalingStroke`를 쓰라고 한다. 크기는 `"14"`·`"16"`·`"20"` 셋이고 `"24"`와 `--spacing-icon-l`을 뺐다.
- **스토리의 단언.** 계산값 도우미에 `strokesOf`와 `SCREEN_STROKE`를 더했다. svg가 그린 요소마다 계산된 `vector-effect`와
  `stroke-width`를 읽고, 그린 요소가 없으면 던진다. 스토리가 이 목록을 자기 길이만큼의 기대와 맞대므로 빈 목록은 늘
  맞기 때문이다. 아이콘의 크기 셋과 열여섯 이름,
  값 모름 진행 표시의 도는 표시가 이것으로 `non-scaling-stroke`와 `1.5px`를 본다. 상태 배지와 알림이 쓰는 `iconShape`는 같은
  `Icon`으로 기대 모양을 그려, 그린 요소에 붙은 `vector-effect`까지 맞아 그대로 초록이다.
- **버튼의 `size`.** `ButtonSize`와 크기 맵을 걷고 높이(`h-control-m`), 안쪽(`px-4`), 글자(`text-body`)를 기본 클래스에 넣었다.
  아이콘과 불러오는 중의 도는 표시는 지금의 20px이다. 04가 밀도의 높이와 16px 아이콘으로 옮긴다. 타입체크가 알림 스토리의
  `<Button size="s">` 둘을 잡아 걷었고, `Alert.md`의 "작은 보조 버튼"도 거짓이 되어 "보조 버튼"으로 고쳤다.
- **카드의 `elevation`.** `CardElevation`, `CARD_ELEVATIONS`, 그림자 맵을 걷어 카드가 그림자 없이 선다. 기본 카드 스토리의
  단언을 `box-shadow`가 `none`인 것으로 뒤집었다. `@theme inline`의 `--shadow-1`~`--shadow-3`을 뺐고, 그 색 `--shadow-color`는
  04의 `float`가 쓰므로 남겼다. `.design-sync/story-constants.js`의 `CARD_ELEVATIONS` 줄을 뺐다.
- **진행 표시의 `tone`과 값 모름.** `ProgressTone`을 걷고 채움을 지금의 흐린 글자색(`bg-muted`) 하나로 두었다. 값을 모르면
  트랙을 그리지 않고 도는 표시와 이름을 한 줄에 놓는다(아래 "정한 것"). `--animate-progress`와 `@keyframes progress`를 뺐다.
- **문서.** 아이콘·버튼·카드·진행 표시의 `<Name>.md`에서 출처를 재탐색 디자인 파일의 절(2.9, 2.1, 2.8, 2.7)로 바꾸고 선 굵기와
  24px, 카드의 그림자 단계, 진행 표시의 위험 톤과 옮겨 다니는 막대를 고쳤다. 카드에는 디자인 파일 2.8의 짝('아주 옅은
  테두리만' / '그림자로 띄운다')을 습니다체로 풀어 한 줄 더했다. 진행 표시의 더한 줄은 하지 않는 것만 디자인 파일 2.7의
  '끝을 모르는데 막대를 채운다'에서 왔고, 해도 되는 것("끝을 모르면 도는 표시를 씁니다")은 내가 지은 짝이다. 그 절의
  해도 되는 것은 '값을 알면 막대와 숫자(3 / 5)를 함께'인데, 이름은 쓰는 쪽이 넘겨 숫자를 강제할 수 없어 옮기지 않았다.
  코드의 머리 주석도 같은 절을 가리키고, 아직 첫 탐색의 값인 색과 치수는 그렇다고 적었다.
- **props의 계약 문장.** `.claude/rules/web-design.md`의 "props 표(디자인 파일 05절)가 계약의 최소다"를 "props는 지금 코드가
  계약이다. 재탐색 디자인 파일 5.2절의 props 표는 초안이라 따르지 않는다"로 바꿨다. 같은 계약을 적은 `props.ts`의 머리 주석도
  함께 고쳤다(작업 규약 4). 처음에는 그 주석에 뺀 prop 넷의 이름을 적었는데, 05의 잔존 grep이 `elevation`을 대소문자 없이
  찾아 그 줄이 잔존으로 셀 것이라 이름을 걷고 명세의 절을 가리키게 했다. 같은 rules에 아이콘의 선(화면 1.5px)과 크기 셋,
  카드에 그림자가 없다는 것을 적었다.

## 정한 것

티켓 파일의 "이 티켓이 정한 것"에 적었다.

1. **값 모름 진행 표시의 구조.** progressbar 요소의 자식이 도는 표시(svg)와 이름(span) 둘이고 트랙이 없다. 도는 표시가 앞이고
   사이 8px, 세로 가운데다. 디자인 파일 2.7의 표본(`role="status"`의 회전 아이콘과 "불러오는 중")이 그 차례였다. 도는 표시의
   색은 progressbar 요소의 `text-muted`가 물려주고 이름은 값을 알 때와 같은 span이다. 막대와 같은 자리를 미리 비워 두지 않았다.
   한 줄(20px)은 막대 모양(34px)보다 낮아 값을 알게 되면 14px 자란다. 디자인 파일의 props 표가 막대와 회전을 `kind`로 가른
   다른 모양이고, 비워 둔 트랙 자리는 막대가 빠진 것처럼 보이기 때문이다. 자라는 것이 거슬리면 쓰는 쪽이 자리를 잡는다.
2. **움직임 줄이기 사례의 자리.** `[role=progressbar]:not([aria-valuenow]) > svg`와 움직임 이름 `spin`이다. 줄이기가 없으면
   `spin`, 줄이기에서 `none`인지 본다. 옛 사례(트랙 안의 막대와 `progress`)를 지우지 않고 다시 겨눴다.

이름의 색은 고르지 않았다. 명세 "컴포넌트 아홉"의 5와 디자인 파일의 상태 표는 이름도 `text-muted`라 적었지만, 색은 03이고 03의
진행 표시 줄에는 그 말이 없다. 03 티켓의 그 줄에 메모로 넘겼다. 명암비 짝의 `accent`/`tint`·`danger`/`tint`(진행 막대와 트랙)는
쓰는 컴포넌트가 없어졌지만 03이 짝 목록을 다시 쓰므로 두었다. 새 채움 `muted`/`tint`는 이미 4.5 기준의 짝으로 있다.

## 검사

- **빨강부터.** 아이콘(크기 셋과 선, 열여섯 이름과 다크), 카드(그림자 없음), 진행 표시(값 있음의 `muted` 채움과 다크, 값 모름의
  구조) 일곱 스토리를 고친 뒤 구현 전에 돌려 일곱 모두 빨간 것을 봤다. 구현 뒤 패키지의 스토리 74개가 모두 지났다.
- **변이(`.scratch/design-refresh/probes/icon_props_mutations.toml`) 여덟 모두 기대대로.** 구현 전의 빨강은 스토리의 첫 단언이
  가려 뒤 단언의 빨강은 보지 못했다. 변이마다 그 단언이 든 스토리 하나로 좁혔다(`-t`, 처음 판은 파일 전체였고 셀프 리뷰가
  짚어 좁혀 다시 돌렸다). 아이콘에서 `nonScalingStroke`를 빼면 크기 셋의 스토리가, 선을 2로 두면 열여섯 이름의 스토리가, 도는
  표시에서 `nonScalingStroke`를 빼거나 20px로 그리거나 줄의 `text-muted`를 빼거나 사이를 4px로 두면 값 모름 스토리가
  빨갰다(나머지는 skipped). 한 스토리 안의 어느 단언이 실패했는지는 판정이 가르지 않는다.
  사진 비교의 움직임 사례는 도는 표시를 멈춘 아이콘(`list`)으로 바꾸면 줄이기가 없을 때가, `Spinner`에서
  `motion-reduce:animate-none`을 빼면 줄이기에서 빨갰다(정적 빌드를 지어 Docker 컨테이너에서, 기준선 초록).
- **기존 변이 표.** `--check`로 design-system의 표 넷을 보니 `atoms_mutations` 14, `ui_mutations` 4, `visual_mutations` 1의 원문이
  사라졌다. 모두 이 티켓이 없앤 모양(카드의 그림자 단계, 값 모름 막대, 진행 표시의 위험 톤, 작은 버튼)이나 고쳐 쓴 파일의
  줄이다. 도구 독스트링대로 옛 프로브의 원문은 썩어도 되는 기록이라 고치지 않았다. `visual_mutations`의 그 하나("그리다 던지는
  스토리는 오류 화면 확인에서 빨갛다")는 작은 버튼 스토리를 빌려 사진 도구의 오류 화면 확인을 재던 것이라, 다시 돌릴 때는 다른
  스토리를 빌려야 한다.
- **사진.** Docker Desktop이 꺼져 있어 켰다. `pnpm -C web visual:update`가 77개 시험을 지나며 정답 92장을 다시 썼다(아이콘이 든
  스토리, 카드, 진행 표시, 버튼). 없어진 스토리 다섯(버튼의 작은 크기 둘, 카드의 그림자 단계, 진행 표시의 위험 톤 둘)의 정답
  열 장을 지웠다. **아이콘 버튼의 사진 10장(`atoms-iconbutton--secondary`의 여덟과 `--small`의 둘)은 아이콘이 들었는데도 옛
  바이트 그대로였다**(명세 축 리뷰가 짚었다). `visual:update`는 `--update-snapshots=changed`라 비교에서 어긋난 사진만 다시
  쓰는데(`web/tools/visual.ts`), 그 비교가 이 열 장을 지나보냈다. Playwright 1.63.0은 pixelmatch에 `threshold`만 넘기고
  pixelmatch의 기본값 `includeAA: false`가 안티에일리어싱으로 판정한 픽셀을 차이에서 빼기 때문이다(설치본
  `playwright-core/lib/coreBundle.js`의 `comparators.ts`와 `third_party/pixelmatch.js` 부분을 읽었다). 아이콘 버튼의 선은 20px
  아이콘에서 약 1.46px(1.75 × 20/24), 16px 아이콘에서 약 1.33px(2 × 16/24)이던 것이 1.5px로 바뀌어, 그 차이가 안티에일리어싱
  픽셀에만 났다고 본다(셈과 어림. 픽셀을 세지 않았다). 그래서 Playwright 인자로
  `pnpm -C web visual --update-snapshots=all`을 넘겨 모두 다시 찍었다. 기준점 대비 바뀐 사진이 102장(지운 10장 따로)이 되었고,
  바이트가 그대로인 69장은 모두 아이콘이 없는 스토리(아이콘 없는 버튼, 스위치, 아이콘 없는 글 입력)였다. 이 갱신 뒤
  `pnpm -C web visual`을 다시 돌려 초록을 봤다(아래 검증). 정적 빌드의 `index.json` 스토리 id와 정답 이름을 맞대는 스크래치 스크립트로 보니 고아 사진이 없고, 사진이 없는
  스토리 열다섯은 모두 판정 스토리(`judgment`)였다. 바뀐 사진 가운데 값 모름 진행 표시, 아이콘 크기 셋, 다크의 카드, 값 있는
  진행 표시를 열어 봤다.
- **rules.** 고친 `web-design.md`의 세 문장이 새 `claude -p` 세션에서 `paths` 안의 파일(`StatusBadge.tsx`)을 Read할 때 실리는지
  `tools/canary.py`로 봤다. 통과 4다(실험군 셋이 세 문장을 글자 그대로 옮겼고 대조군 `README.md`는 "없음", claude 2.1.296).
  명세는 `.scratch/design-refresh/probes/canary/web_design_props_icon_card.toml`이다.
- **잔존 grep.** 이 티켓 몫의 말(`ButtonSize`(`IconButtonSize` 빼고), `CardElevation`, `CARD_ELEVATIONS`, `ProgressTone`,
  `animate-progress`, `icon-l`, `shadow-1`~`shadow-3`, `1.75`, 대소문자를 가리지 않은 `elevation`)이 살아 있는 문서와 코드에서
  `.design-sync/conventions.md`·`NOTES.md`와 화면 프롬프트(05의 몫)에만 남았다.

## 셀프 리뷰

`/code-review`를 기준점 `6b439aa`로 돌렸다(추적 파일 126개 가운데 정답 사진 102장, 미추적 셋, 커밋 0). 두 축 모두 Critical과
Major가 없었다.

- **표준 축(Minor 넷, Nit 넷, 판단 항목 둘).** 고친 것: 버튼·카드·진행 표시의 머리 주석이 출처를 재탐색 디자인 파일로 들면서
  첫 탐색의 값(`divider`, 10px, 6px `tint` 트랙)을 적었다. 그 값이 아직 첫 탐색의 것이라고 적고, 03과 04의 카드 줄에 그 말을
  걷으라는 메모를 남겼다. `contrast.ts`의 짝 주석이 "진행 막대와 트랙"을 들었는데 `accent`·`danger`를 `tint`와 맞댄 짝은 쓰는
  컴포넌트가 없어졌다고 덧붙였다. 변이 여섯이 스토리 파일만 주어 어느 스토리가 빨개도 기대대로로 셌다. `-t`로 그 단언이 든
  스토리 하나로 좁혀 다시 돌렸고, 한 스토리 안의 어느 단언인지는 가르지 않는다고 표와 README 행에 적었다. 일지의 따옴표 인용
  둘이 디자인 파일 원문과 달라 원문으로 고쳤다. "트랙만큼 자란다"를 사이와 트랙만큼(14px)으로, `strokesOf`의 "빈 목록은 어느
  단언에도 맞는다"를 "자기 길이만큼의 기대에 늘 맞는다"로, `iconShape` 독스트링에 `vector-effect`가 모양에 든다는 것을
  고쳤다. README 행의 "잰 판" 칸에 결과 대신 판을 적었다. 남긴 것: 판단 항목 둘. 세 스토리가 되풀이하는 두 줄
  (`strokesOf`와 그 길이만큼의 `SCREEN_STROKE`)은 두었다. `storybook/expect.ts`의 도우미는 모두 계산값을 돌려주기만 하고
  `expect`는 스토리의 play가 부르는 것이 그 모듈의 관례라, 단언을 도우미 안으로 옮기면 그 관례를 깬다. 진행 표시가 `now === null`을 className과 자식에서 두 번 가르는 것은 요소 하나의 속성을 한 자리에 두는 편이 읽기
  쉽다고 보고 두었다.
- **명세 축(Minor 둘, Nit 둘).** 아이콘 버튼의 사진 10장이 옛 선 그대로인 것은 위 사진 항목대로 고쳤다. 마지막 체크박스(검증
  명령과 사진 비교)는 아래 검증을 마친 뒤 표시했다. Nit 둘(자라는 높이, 디자인 파일에서 옮긴 짝)은 표준 축과 같은 지적이다.

## 검증

- `uv run pytest -q` 2197 통과(7 deselected). ruff 둘, pyright, `lint-imports` 초록.
- `pnpm -C web verify` 초록(Vitest 28파일 352개). 사진 비교 `pnpm -C web visual`은 `--update-snapshots=all` 갱신 뒤 77개 통과.
- 리뷰를 반영한 뒤 손으로 치는 다섯은 커밋의 pre-commit 결과로 갈음한다(`CLAUDE.md` 검증 명령 절).
