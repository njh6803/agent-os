# 01: 디자인 시스템 패키지가 설정 아이콘, 가린 한 줄 입력, 기준 폭 셋을 낸다

**What to build:** 관리 화면이 쓸 다섯이 디자인 시스템 패키지(`@agent-os/ui`)에 더해진다. 아이콘 이름에 Lucide `settings`가 들고, `TextField`의 한 줄 변형이 가린 입력(`type` `"password"`)을 그리며, 디자인 토큰 CSS에 컨테이너 기준 폭 `split`(784px)과 기준 폭 `form`(440px)·`content`(880px)이 선다. 디자인 시스템을 고치는 사람은 패키지 Storybook의 `Icon`·`TextField` 스토리와 판정 스토리 `Responsive`에서 그것을 보고, 사진 비교가 바뀐 모양을 정답으로 든다. 관리 화면은 아직 패키지를 들이지 않으므로(03) 운영자에게 보이는 변화는 없다. 위젯은 패키지의 컴포넌트와 토큰으로 그리므로 위젯의 사진도 다시 본다.

근거는 `.scratch/admin-style/spec.md`의 "패키지에 더하는 것" 전부(2026-10-27 명세 검토 주석의 기준 폭 둘 포함)와 Testing Decisions의 "패키지"와 그 주석이다. `split`은 ADR 0026의 2026-10-26 이력 "관리 화면의 본문은 본문 칸의 컨테이너 기준 폭 하나로 가른다"가 앞선 결정이고, `form`과 `content`는 사용자가 2026-10-27에 골랐다(일지 2026-10-27-09). 판단 기준은 `.claude/rules/web-design.md`다. 이 티켓은 화면 파일(`.scratch/admin-style/design/`)을 따르지 않으므로 웹 편집 확인 없이 돈다.

**Blocked by:** None (can start immediately)

**Status:** done

### 아이콘

- [x] **아이콘 이름(`IconName`)에 Lucide의 `settings`가 든다.** 크기 셋(14·16·20)과 선 굵기 규칙은 다른 열여섯과 같다
- [x] 아이콘 전부를 그리는 `Icon` 스토리가 `settings`까지 그리고, `Icon.md`의 목록이 열일곱이다

### 가린 한 줄 입력

- [x] **`TextField`의 한 줄 변형이 `type`으로 `"text"`(기본)와 `"password"`를 받는다.** 받지 않으면 지금처럼 `text`다. 여러 줄 변형은 `type`을 받지 않고, 그것은 타입이 막는다
- [x] 가린 입력의 변형 스토리가 있고, play가 그 입력의 `type`이 `password`이며 레이블로 찾아진다고 본다
- [x] `TextField.md`가 `type`을 적고, 새 변형 스토리의 id가 `.design-sync/config.json`의 `overrides.TextField.skip`에 든다(Claude Design 카드에는 보여 주기용 스토리만 오른다, `.claude/rules/web-design.md`의 카드 항목)

### 기준 폭

- [x] **디자인 토큰 CSS(`web/packages/ui/src/styles/theme.css`)의 기준 폭에 `split` 784px, `form` 440px, `content` 880px이 든다.** 지금의 `wide`(360px)와 같은 자리다. 그 자리의 이름은 `@<이름>:` 컨테이너 변형과 `max-w-<이름>` 최대 폭 둘에 쓰인다
- [x] **판정 스토리 `Responsive`에 `@split:` 표본이 더해져** 784px 경계의 양쪽에서 갈리는지 보고, 패키지 시트의 조건 목록 단언에 784px이 든다. Tailwind는 쓰인 변형만 규칙을 내므로(어림, 명세 주석) 표본 없이는 그 단언이 784px을 보지 못한다. 스토리 이름("기준 폭 둘이 359px 과 360px 사이와 시트의 조건 둘에서 갈린다")처럼 기준 폭을 수로 든 글도 새 표본에 맞게 고친다
- [x] 같은 자리에서 `max-w-form`과 `max-w-content`의 계산 최대 폭이 440px과 880px인지 본다
- [x] 판정이 값을 실제로 보는지, 세 값 가운데 하나를 바꿔 그 단언이 빨개지는 것을 한 번 손으로 본다(커밋하지 않는다). 관리 화면의 시험은 폭 320과 1280이라 784가 다른 값이어도 초록이므로, 그 값을 지키는 것은 이 판정 하나다

### 사진

- [x] `pnpm -C web visual`과 `pnpm -C web visual:widget`을 치고, 빨개지면 바뀐 사진을 보고 `visual:update`·`visual:widget:update`로 정답을 컨테이너 안에서 다시 만든다. 바뀐 사진은 PR 본문에 적는다

### 검증

- [x] 검증 명령이 모두 초록이다(`CLAUDE.md` 검증 명령. 이 티켓은 모델 경로와 위젯·관리 화면 앱의 코드를 건드리지 않아 `-m llm`·`-m llm_widget`과 e2e는 칠 일이 없다)
