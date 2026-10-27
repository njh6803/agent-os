# 2026-10-27 (10) 관리 화면의 organisms가 데이터와 처리기를 props로 받는다 (admin-style 티켓 02)

티켓 `.scratch/admin-style/issues/02-admin-organisms-take-props.md`의 구현 세션이다. 브랜치 `feature/02-admin-organisms-take-props`, 워크트리 `02-admin-organisms-take-props`. 이 세션의 제목은 `feature/02-admin-organisms-take-props`였고, 셀프 리뷰 직전에 인계 계기(컨텍스트 230,025 토큰)가 와서 새 세션에 넘긴다. 아래는 넘기는 시점까지다. 커밋은 아직 없다.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/admin-style/issues/02-admin-organisms-take-props.md
>
> 다음 작업: 기능 admin-style의 티켓 .scratch/admin-style/issues/02-admin-organisms-take-props.md. 관리 화면의 organisms가 데이터와 처리기를 props로 받게 옮긴다
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 2 중 2. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 02-admin-organisms-take-props)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/admin-style/issues/02-admin-organisms-take-props.md
> 브랜치: feature/02-admin-organisms-take-props
> 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
> 읽을 것: docs/journal/2026-10-27-09-admin-style-tickets.md의 "다음". 나란히 도는 형제는 .scratch/admin-style/issues/01-ui-settings-icon-password-widths.md
> 이어받을 상태: 이 티켓이 판정자로 막는 일은 ADR 0021 이력 초안으로 제안하고, 그 초안은 사용자의 승인을 받는다(CLAUDE.md 작업 규약 5, 티켓 02에 적혀 있다). 승인 없이 판정자 변경을 확정하지 않는다
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. tidy-checkouts는 묶음의 첫 세션이 돈다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

이 세션에서 사용자의 다른 메시지는 없었다. ADR 0021 이력 초안의 승인은 아직 받지 않았다.

## 한 것

- organisms(`AdminTokenForm`, `ChannelTokenForm`, `PluginList`, `PluginDetail`, `RunList`, `RunDetail`, `RunDecision`, `ReadSection`)가 `hooks/queries`와 토큰 스토어를 부르지 않고 값과 처리기를 props로 받는다. 읽기 골격은 `ReadState<T>`(값, 실패, 다시 읽는 중, 새로 고침)를 props로 받고, 다시 읽다 실패하면 보인 것을 지우는 행동은 `ReadSection` 한 자리에 그대로다.
- pages가 훅을 부른다. `AdminScreen`이 토큰 스토어와 `useAdminTokenEntry`를 읽고, 화면마다 `Connected*` 컴포넌트(`HomePage`의 `ConnectedPluginList`, `PluginPage`의 `ConnectedPluginDetail`, `RunsPage`의 `ConnectedRunList`, `RunPage`의 `ConnectedRunDetail`·`ConnectedRunDecision`)가 읽기 훅을 불러 넘긴다. SWR 응답을 읽기 골격의 props로 옮기는 것은 새 파일 `components/pages/read.ts`의 `readOf`다.
- 결정 자리의 꺼짐 미리 알림이 읽는 플러그인 목록은 `RunPage`가 `usePlugins(decisionPlaceStands(trace, channelTokenEntered))`로 결정 자리가 설 때만 읽어 넘긴다. `usePlugins`에 `active` 인자(기본 참)를 더했고, 자리가 서는 조건은 `RunDecision`의 `decisionPlaceStands`가 낸다.
- 판정자 제안(승인 전, 커밋하지 않음): `web/eslint.config.mjs`에 요소 `store`(`stores`)를 세우고, organisms·templates가 `hooks/queries`·`stores`·`@agent-os/api-client`를 값으로 import하는 것을 막는 정책(`dependency: { kind: "value" }`)을 더했고, atoms·molecules의 층 정책에 `store`를 더했다. `web/eslint.config.test.ts`에 빨강 여섯(molecules→stores, organisms→생성 클라이언트(초록에서 옮김), organisms→hooks/queries barrel, organisms→stores, organisms의 같은 줄 `type` 지정자, templates→hooks/queries)과 초록 둘(organisms의 `import type`, pages→hooks/queries·stores)을 더했고, barrel 판정 사례 `DeepQuery`를 organisms에서 pages로 옮겼다(organisms의 그 import는 새 정책도 막아 barrel 판정력을 잃는다).
- `isRejection`을 `hooks/queries/admin`에서 `api/failure`로 옮겼다. 훅이 아닌 실패 해석 함수이고, 옮기지 않으면 `RunDecision`의 값 import를 새 정책이 막는다.
- 문서: ADR 0021에 이력 초안 "2026-10-27 서버 데이터와 토큰은 pages가 읽고 organisms와 templates는 그 값을 props로 받는다"(승인 전), `docs/constitution/tech.md` 프론트 구성 문장, `.claude/rules/web-workspace.md`의 templates 줄, `.claude/rules/web-admin.md`의 꺼짐 미리 알림 문장(목록은 `RunPage`가 결정 자리가 설 때만 읽어 넘긴다).
- 변이 표 `.scratch/admin-style/probes/organisms_props_mutations.toml`과 그 프로브 README의 줄.

## 결정

- 훅을 pages 맨 위로 올리지 않고 원래 organism 자리에 `Connected*`를 둔다. 관리 토큰이 받아들여진 뒤, 주소를 푼 뒤에만 서던 자리라 요청이 시작되는 때가 옮기기 전과 같다.
- `useDecision`은 트레이스 값의 갈래 안(`RunDetail`의 `decision` 슬롯이 그리는 `ConnectedRunDecision`)에서 부른다. 다시 읽다 실패하면 결정의 훅도 함께 걷히고 보낸 결정의 연결을 끊는 옮기기 전 동작을 지킨다.
- 판정자 초안의 갈래: `import type`은 지나고 같은 줄의 `type` 지정자는 값으로 센다(`verbatimModuleSyntax`에서 그 줄은 모듈을 싣는다). `api/`는 막지 않는다(응답 타입과 실패 해석을 organisms가 쓰고, 요청 함수는 토큰을 인자로 받으며 토큰은 스토어에만 있다). 거절되면 판정자 변경과 그 사례를 되돌리고 `web-workspace.md`의 templates 줄을 organisms까지 넓힌다(티켓 02).

## 번복하거나 고친 것

- `pauseOf`에 형식 1 검사를 넣었다가 뜻이 흐려져 되돌리고 `decidablePause` 헬퍼로 바꿨다.
- 변이 표의 첫 변이("결정 자리가 서지 않아도 목록을 읽는다")를 처음에는 빨강으로 기대했는데, 첫 실행에서 초록이었다. 결과를 본 뒤 기대를 초록으로 바꿨다. 까닭은 실행 하나의 시험이 관리 토큰 확인을 위해 `GET /plugins`에 늘 빈 목록을 답해(`web/apps/admin/testing/token.ts`의 `acceptTokens`) 더 읽은 목록이 처리하지 않은 요청이 되지 않고, 목록 요청의 수를 세는 시험도 없어서다. 실행 하나의 두 시험 파일 전체로 넓혀도 초록이었다. 그래서 그 자리는 지금의 시험이 고정하지 않는 자리로 적는다. 다섯째(결정의 훅을 값의 갈래 밖에 둔다)도 같은 까닭으로 초록 기대다.

## 확인한 것

- 페이지 시험 다섯 파일 137개가 옮기기 전과 뒤에 모두 초록이었고, 시험 파일은 고치지 않았다(이 세션이 vitest로 손으로 돌렸다).
- 변이 표: `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/admin-style/probes/organisms_props_mutations.toml`에서 둘째·셋째·넷째가 표지 `Unable to find an element with the text`와 함께 빨강, 첫째(기준을 바꾼 뒤)·다섯째가 초록이었다(탐침이 찍었다. 첫째의 마지막 실행은 "기준선 … Test Files 2 passed (2), Tests 59 passed (59)", "결과 초록"). `--check`로 다섯 변이의 원문이 지금 파일에 한 번씩 있다는 것도 봤다(탐침이 찍었다).
- 판정자 사례: 정책을 넣기 전 `pnpm -C web exec vitest run eslint.config.test.ts -t "판정자가"`가 새 빨강 여섯만 `AssertionError: expected [] to include 'boundaries/dependencies'`로 실패했고(6 failed, 49 passed), 넣은 뒤 55 passed였다(손으로 봤다). 값만 거르는 `dependency.kind`를 잠깐 빼자 `import type` 초록 사례가 새 정책의 메시지로 빨개졌다(손으로 봤다). 그래서 거름이 타입 import를 지나보내고, 같은 줄의 `type` 지정자는 값으로 세어진다.
- 앱 코드에 판정자: `pnpm -C web exec eslint --max-warnings 0 apps/admin/components apps/admin/hooks apps/admin/stores apps/admin/api apps/widget`이 `isRejection`을 옮기기 전에는 `RunDecision.tsx:6` 하나로, 옮긴 뒤에는 0으로 끝났다(손으로 봤다). 위젯은 고칠 것이 없었다.
- 관리 화면 `tsc --noEmit`, `uv run ruff check .`, `uv run ruff format --check .`가 0으로 끝났다(손으로 봤다).
- `uv run python tools/run_checks.py`는 백그라운드로 띄웠다가 인계 때문에 멈췄다. 결과를 쓰지 않는다.

## 인계 때 남은 것

- 셀프 리뷰(`/code-review`, 기준 origin/main)와 반영.
- 셀프 리뷰를 반영한 뒤 ADR 0021 이력 초안을 쉬운 말로 보여 사용자의 승인을 받는다. 승인되면 판정자를 그대로 두고, 거절되면 위 "결정"의 거절 갈래.
- `docs/constitution/tech.md`를 고쳐 헌법 판을 올려야 한다(`sibling_overlap.py`가 알렸다. 형제 가운데 가장 높은 판은 3.0.56, 문구 수정이라 patch).
- 바꾼 rules 둘(`.claude/rules/web-admin.md`, `.claude/rules/web-workspace.md`)은 카나리아 명세가 없다고 `sibling_overlap.py`가 알렸다(`docs/constitution/operations.md` 환경 규약 상세).
- 명세 `.scratch/admin-style/spec.md` 292줄의 "지침을 organisms까지 넓힌 것"에 승인 결과를 덧붙이는 일, 티켓의 "이 티켓이 정한 것"(판정자 결정과 까닭, 시험이 고정하지 않는 두 자리, 훅을 마운트하는 깊이), 티켓 `done`.
- 프로브 README의 함께 고친 파일 후보: 워크트리 `admin-style-to-spec`도 `.scratch/admin-style/probes/README.md`를 고쳤다(`sibling_overlap.py`).

## 인계 지시문

```
다음 작업: .scratch/admin-style/issues/02-admin-organisms-take-props.md. 관리 화면의 organisms가 데이터와 처리기를 props로 받게 옮긴다
다음 단계: 구현
어디서: 새 세션. 인계 줄이라 같은 브랜치·워크트리를 잇는다. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/admin-style/issues/02-admin-organisms-take-props.md
브랜치: feature/02-admin-organisms-take-props
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-27-10-admin-organisms-take-props.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 기준 origin/main, 티켓 02)부터 한다. 일지 docs/journal/2026-10-27-10-admin-organisms-take-props.md. ADR 0021 이력 초안(2026-10-27)은 아직 사용자의 승인을 받지 않았다. 셀프 리뷰를 반영한 뒤 보여 승인받고, 승인 없이 판정자 변경을 커밋하지 않는다(CLAUDE.md 작업 규약 5). 그 밖에 남은 일은 그 일지의 "인계 때 남은 것"이다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-27T08:17:46Z

## 이어받은 세션

위 인계 지시문으로 연 새 세션이다. 같은 워크트리(`02-admin-organisms-take-props`)에 `EnterWorktree(path)`로 들어갔다. 지시문 밖의 사용자 메시지는 아직 없다.

### 셀프 리뷰

`/code-review`, 기준 origin/main(`4f783dc0`). 범위는 바뀐 파일 25개, 미추적 3개(`components/pages/read.ts`, 변이 표, 이 일지), 커밋 0개. 명세는 티켓 02와 `.scratch/admin-style/spec.md`.

표준 축(sonnet·high)이 낸 것과 판정:

- Major. ADR 0021 이력 초안의 제목("organisms와 templates는 그 값을 props로 받는다")과 `tech.md` 프론트 구성("organisms·templates는 그 값과 처리기를 props로 받으며")이, 같은 초안 본문과 `web-workspace.md`의 "templates는 슬롯만 받고 데이터는 props로도 받지 않는다"와 어긋난다. 고친다(제목과 `tech.md`를 organisms는 props, templates는 슬롯으로).
- Minor. `decisionPlaceStands`와 `RunDecision`의 JSX가 자리가 서는 조건을 두 곳에 적는다. 남긴다. 두 자리는 같은 파일에 붙어 있고 독스트링이 서로를 가리킨다. 위험한 쪽(자리가 서는데 목록을 읽지 않는 것)은 변이 둘째가 빨강으로 잡고(위 "확인한 것"의 변이 표 줄, 탐침이 찍었다), 반대쪽(서지 않는데 더 읽는 것)은 요청 하나가 늘 뿐이며 시험이 고정하지 않는 자리로 티켓에 적는다.
- Minor. 프로브 README에서 변이 표 안내가 `hash_match` 코드 블록과 그 뒤의 "받은 폴더는" 문단 사이에 끼었다. 고친다(문단 뒤로 옮긴다).
- Nit. 변이 표의 `expect_output`(`Unable to find an element with the text`)이 어느 글자 찾기가 실패해도 나는 머리다. `.claude/rules/probes.md` 첫 항목이 고른 단언이 실패할 때만 나는 문구를 요구하므로 고친다(변이를 넣어 실패 출력을 보고 찾는 글자까지 넣는다).
- Nit. `usePlugins(active = true)`가 위치 불리언 인자다(`CODING_STANDARDS.md` "불리언 플래그 인자를 만들지 않는다"). 남긴다. 함수가 두 가지 일을 하는 갈래가 아니라 관리 토큰이 없을 때와 같은 읽기의 문(SWR의 null 키)이고, 쪼개면 키와 요청 함수가 두 벌이 된다.
- Nit. `RunDecisionProps`가 `useDecision`의 반환을 풀어 받고(Data Clumps 후보), `PluginsRead`가 `Pick<ReadState<…>, "data" | "error">`와 같은 모양이다. 남긴다. `PluginsRead.data`의 독스트링은 다시 읽다 실패해도 옛 목록이 남는다는, 읽기 골격과 다른 뜻을 적는다. 결정의 값은 Storybook 스토리가 하나씩 채울 칸이다.
- Nit. `web/eslint.config.mjs`의 atoms·molecules 메시지 "생성 클라이언트는 api 도메인 폴더가 부른다"가 사실 서술인지 규칙인지 흐리다. 고친다.

명세 축(본 세션 모델)이 낸 것과 판정. 옛 동작 대조 여덟(읽기 훅·처리기·요청 시점·결정의 훅 자리·판정자 옛 사례)은 모두 같다고 했고, 판정자 시험 55개와 페이지 시험 137개를 돌려 초록이었다고 적었다(서브에이전트가 돌렸다).

- Major. 표준 축의 Major와 같다(초안 제목과 `tech.md`가 templates도 데이터를 props로 받는다고 적는다). 고친다.
- Minor. 초안의 "데이터를 가져와 채우는 것은 pages다"를 판정자가 보게 되어 뺀다는 문장에 반례가 있다. organism이 `swr`와 `api/plugins`의 요청 함수를 함께 import해도 판정자가 지나보낸다(서브에이전트가 stdin 탐침으로 봤다). 고친다. 판정자에 `swr` 금지를 더하고, `web-workspace.md`의 그 줄은 판정자가 보지 못하는 `api/`의 요청 함수를 적는 줄로 바꾼다.
- Minor. 초안의 "토큰은 스토어에만 있어, organisms가 그것을 부를 길은 props로 토큰을 받는 것뿐이다"에 반례가 있다. `AdminTokenForm`은 스토어에 들기 전의 토큰을 입력칸에서 쥔다. 고친다.
- Nit. 초안의 "위젯은 이미 이 모양"은 맞지만 위젯 쪽은 판정자가 아니라 관례가 지킨다(위젯에는 `hooks/queries`도 `stores`도 없다). 고친다(그 사실을 초안에 적는다).
- Nit. 막는 범위가 templates와 atoms·molecules→`stores`까지 넓다. 남긴다. 티켓이 "어디까지 막을지는 ADR 초안이 정한다"고 적었고, 사용자 승인이 그 범위를 본다.
- Nit. 명세 292줄의 "지금은 organisms가 훅을 직접 부른다"가 이 변경으로 거짓이 된다. 인계 때 남은 일(그 줄에 승인 결과를 덧붙인다)과 함께 고친다.

고친 것(셀프 리뷰 반영):

- 판정자: organisms·templates가 `swr`를 값으로 import하는 것을 막는다(`{${API_CLIENT},swr}`). 사례 셋을 실제 관리 화면 자리에 더했다(organism→`swr` 빨강, organism→`swr/infinite` 빨강, organism의 `import type`으로 받은 `swr` 타입 초록). 정책을 넣기 전 `pnpm -C web exec vitest run eslint.config.test.ts -t "swr"`에서 빨강 둘이 `AssertionError: expected [] to include 'boundaries/dependencies'`로 실패했고(2 failed, 1 passed), 넣은 뒤 `-t "swr|판정자가|생성 클라이언트"`가 61 passed였다(손으로 봤다). atoms·molecules 메시지는 "생성 클라이언트를 부르지 않는다"로, organisms·templates 메시지는 `swr`와 "organisms 에 props 로"를 넣어 고쳤다.
- ADR 0021 이력 초안: 제목을 "서버 데이터와 관리·채널 토큰은 pages가 읽고 organisms는 그 값을 props로 받는다"로(`CONTEXT.md`가 "토큰" 단독을 피하라고 적어 좁혔다), 굵은 결정문에 `swr`와 "templates는 지금처럼 슬롯만 받는다"를, `swr` 갈래를 더했고, `api/` 갈래·`web-workspace.md` 갈래·Considered Options의 `api/` 줄을 반례에 맞게 고쳤다.
- `docs/constitution/tech.md` 프론트 구성: "organisms는 그 값과 처리기를 props로 받으며, templates는 슬롯만 받고".
- `.claude/rules/web-workspace.md`의 templates 줄에 organisms가 `api/`의 요청 함수를 부르지 않는다는 것과 판정자가 `api/`를 막지 않는 까닭을 더했다.
- 프로브 README의 변이 표 안내를 `hash_match`의 "받은 폴더는" 문단 뒤로 옮겼다.
- 변이 표의 표지 셋을 찾는 글자까지 든 실패 머리로 바꿨다. 변이를 손으로 넣어 고른 시험을 돌려 실패 머리를 봤다(`Unable to find an element with the text: /꺼진 플러그인이 있어 재개할 수 없다/`, `…: haiku.`, `…: 채널 토큰을 넣었다.`, 셋 다 `pnpm -C web exec vitest run <파일> -t <이름>`을 손으로 돌렸다). 바꾼 뒤 `--check`가 "변이 5 모두 원문이 한 번씩 있다", 전체 실행이 "변이 5 모두 기대대로"였다(탐침이 찍었다). 도구가 커밋하지 않은 변경이 있는 전체 실행이라고 알렸으므로 커밋 뒤에 한 번 더 돈다.

PR 직전 리뷰에 밀 주장으로 넘길 새 사실 문장(원문):

1. ADR 0021 이력: "`swr`를 값으로 import하는 파일은 `hooks/queries`와 시험 도구뿐이다."
2. ADR 0021 이력: "모듈 이름은 서브패스를 떼고 맞춰 `swr/infinite`도 막힌다(판정자 사례가 잰다)." 와 `web/eslint.config.mjs` 주석 "모듈의 source 는 서브패스를 뗀 패키지 이름과 맞춘다(swr/infinite 도 swr 다. 판정자 테스트가 잰다)."
3. ADR 0021 이력: "위젯의 organisms와 templates는 이 넷을 import하지 않아 고칠 것이 없다. 위젯에는 `hooks/queries`와 `stores`가 없고 서버에 요청하는 함수는 `api/`에 있어, 위젯 쪽은 아래 `api/` 갈래와 같이 지침이 지킨다."
4. ADR 0021 이력: "organisms가 쥐는 토큰은 props로 받은 것이나 관리 토큰을 넣는 자리의 입력칸에서 막 받은 것이고, 그 토큰으로 요청 함수를 부르는 길은 판정자가 보지 않는다."
5. `.claude/rules/web-workspace.md`: "관리 화면의 organisms가 같은 barrel의 응답 타입과 실패 해석을 써서 판정자는 `api/`를 막지 않는다."

### ADR 0021 이력 초안의 승인

셀프 리뷰를 반영한 뒤 초안의 범위(막는 것: organisms·templates → `hooks/queries`·`stores`·`swr`·생성 클라이언트, atoms·molecules → `stores`. 지나는 것: `import type`, organisms → `api/`)와 거절 갈래를 표로 보이고 물었다.

> 질문: 화면 부품(organisms·templates)이 SWR 훅·토큰 저장소·swr·생성 클라이언트를 import하면 커밋 전 검사가 막게 할까요?
>
> 사용자: 자동 검사로 막는다 (Recommended) — "ADR 0021 이력 초안대로 ESLint 층 규칙을 커밋한다. 부품 파일에서 hooks/queries·stores·swr·생성 클라이언트를 값으로 import하면 pnpm -C web verify와 그것을 도는 pre-commit이 빨갛게 막는다. import type과 api/는 지나가고, api/의 요청 함수를 부르지 않는 것은 web-workspace.md 지침과 리뷰가 본다. tech.md 문구를 고치고 헌법 판을 지금의 3.0.56에서 3.0.57(문구 수정)로 올린다."

고르지 않은 선택지는 "지침 한 줄로만 둔다"(ESLint 규칙과 판정자 사례를 되돌리고 지침만 둔다)였다. 그래서 판정자 변경을 그대로 커밋한다.

### 승인 뒤에 한 것

- ADR 0021 이력의 Considered Options에서 "사용자가 이 초안을 거절하면 이 안으로 간다"를 승인 결과로 고쳤다.
- 헌법 판을 3.0.57로 올렸다(`docs/constitution/README.md`, 스택 표의 문구 하나). 형제 가운데 가장 높은 판이 3.0.56이었다(`uv run python tools/sibling_overlap.py`의 출력).
- 명세 292줄의 "지금은 organisms가 훅을 직접 부른다"를 "티켓 02 전에는 organisms가 훅을 직접 불렀다"로 고치고 승인 결과를 덧붙였다.
- 티켓에 "이 티켓이 정한 것"(판정자 결정과 범위, 훅을 마운트하는 깊이, 시험이 고정하지 않는 두 자리)을 쓰고 체크박스를 표시했다. 검증 명령 체크박스는 전체 검사 뒤에 표시한다.
- 바꾼 rules 둘의 카나리아 명세를 `.scratch/admin-style/probes/canary/`에 새로 썼다(`sibling_overlap.py`가 명세 없음으로 알렸다). `--preflight`가 통과 2였고, `uv run python tools/canary.py <명세> <스크래치 출력>`이 둘 다 통과 4였다(실험군 세 회차가 바뀐 문장을 옮기고 대조군이 "없음". 탐침이 찍었다, claude 2.1.302, 커밋 `4f783dc0` 위의 작업 트리).

고치며 한 번 틀린 것: `web-workspace.md`에 처음 위젯의 요청 함수 자리를 `lib/`로 적었는데, `lib/token`의 `requestToken`은 부모 창에 메시지로 토큰을 묻는 함수이고 위젯의 서버 요청은 `api/runs`였다(코드를 읽었다). 커밋 전에 고쳤다.

### 검증

- `uv run ruff check .`와 `uv run ruff format --check .`가 "All checks passed!"와 "1096 files already formatted"로 끝났다(러너가 찍었다).
- `uv run python tools/run_checks.py`는 `web-verify` 하나만 빨갰다. `pnpm -C web verify`의 Prettier 단계가 이 브랜치가 고친 `web/eslint.config.mjs`와 `web/eslint.config.test.ts`를 "Code style issues found in 2 files"로 막아, 그 뒤의 타입체크와 vitest는 돌지 않았다. 나머지(check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright-linux, pyright, run-hooks, pytest 563.3초)는 Passed였다(러너가 찍었다). 고치기 전의 사본을 남기지 않아 Prettier가 무엇을 바꿨는지는 보지 못했다. `prettier --write`로 두 파일을 맞추고 `pnpm -C web verify`를 다시 돌렸다.
- 다시 돌린 `pnpm -C web verify`는 0으로 끝났다. Prettier가 "All matched files use Prettier code style!", vitest가 "Test Files 68 passed (68)", "Tests 1360 passed (1360)"을 찍었고 타입체크와 `check-tsconfig`도 지났다(러너가 찍었다). 손으로 치는 다섯이 이로써 모두 초록이다. 커밋의 pre-commit이 같은 다섯을 다시 돈다.
- 첫 커밋 시도는 pre-commit에 막혔다(러너가 찍었다). 둘이었다. 하나는 변이 표 검사(`tools/mutate.py --staged`)다. conversation 기능의 `.scratch/conversation/probes/continuation_mutations.toml` 11번("결정 자리의 형식 조건을 형식 2 로 되돌린다")의 원문이 `RunDecision.tsx`에서 사라졌다. 형식 조건이 지역 변수에서 `decidablePause`의 반환으로 옮겨 갔기 때문이다. 원문을 새 모양으로 고치고 `--since origin/main`으로 그 하나를 돌려 기대대로 빨갰고(`형식 3` 사례 하나가 failed, 탐침이 찍었다), 그 프로브 README에 한 줄을 더했다. 다른 하나는 pytest의 `tests/tools/test_rerun_runner.py::test_같은_갈래가_두_번_든_파일럿의_두_회차가_함께_돌아도_번호가_다르다`(`assert 1 == 2`, 두 회차가 함께 돈 수)다. 이 브랜치가 건드리지 않은 하네스 시험이고, 직전의 `run_checks.py`에서는 지났으며, 그것만 다시 돌리니 "1 passed"였다(손으로 봤다). 함께 돈 web 검사와 pytest의 부하에서 동시 실행 시간이 어긋난 것으로 어림하고 고치지 않았다.
- 인용 대조 경고(막지 않는다) 열넷은 모두 이 브랜치가 고친 옛 문장을 옮긴 기록이거나(ADR 0021의 옛 `web-workspace.md` 줄, 헌법 README 3.0.57 문단의 옛 `tech.md` 문구, 일지의 옛 초안 제목과 도구 출력), main의 헌법 README에 이미 있던 문장이었다(`git grep`으로 origin/main을 봤다). 고치지 않았다.
- 다시 친 커밋 `790416df`의 pre-commit은 모두 Passed였다(pytest 646.1초, web-verify 659.0초, 변이 표 검사 포함. 러너가 찍었다). ruff 둘은 스테이지된 `.py`가 없어 Skipped였고, 위의 손으로 친 ruff 뒤로 `.py`를 고치지 않았다.

### 인계 때 남은 것(둘째)

이 세션은 "커밋 뒤" 경계에서 인계 계기(컨텍스트 252,442 토큰)를 받아 새 세션에 넘긴다. 이 세션의 지금 제목은 `feature/02-admin-organisms-take-props`다. 사용자의 메시지는 지시문과 위 ADR 승인의 답 하나뿐이었다. 커밋 뒤에 쓴 이 절은 커밋하지 않았다.

- 변이 표 전체 실행(`PYTHONUTF8=1 uv run python tools/mutate.py .scratch/admin-style/probes/organisms_props_mutations.toml`)을 커밋 뒤에 한 번 더 돈다. 커밋 전의 실행에서 도구가 그렇게 알렸다.
- PR 직전 리뷰(`docs/constitution/operations.md` 리뷰 파이프라인 2). 이 세션이 친 `coderabbit auth status`는 `Seat: not assigned`였다. 그래서 대체 둘을 돌린다. `/security-review`는 커밋하고 origin/main을 합친 뒤에 돌리고(이 세션이 fetch한 때 origin/main은 브랜치를 딴 `4f783dc0`에서 움직이지 않았다), `bug-perf-review` 서브에이전트의 브리프에는 위 "PR 직전 리뷰에 밀 주장으로 넘길 새 사실 문장" 다섯을 원문으로 나열한다.
- PR 본문의 체크리스트와 리뷰어 참고에 적을 것: 첫 커밋 시도에서 흔들린 pytest 하나(위 검증 절), conversation 기능의 변이 표 11번을 고친 것, 셀프 리뷰가 남긴 판단 항목(위 셀프 리뷰 절), 시험이 고정하지 않는 두 자리(티켓의 "이 티켓이 정한 것").
- PR을 열고(`/git-pr`) 봇 회차를 돈 뒤, 이 워크트리 사본의 `next-session` "워크트리에서 병합할 때"로 병합한다. admin e2e, 위젯 e2e, 사진 비교는 이번 변경이 중계·서버 라우트·`packages/ui`·`apps/widget`을 건드리지 않아 로컬에서 칠 일이 없고 CI가 본다.

## 인계 지시문(둘째)

```
다음 작업: .scratch/admin-style/issues/02-admin-organisms-take-props.md. 관리 화면의 organisms가 데이터와 처리기를 props로 받게 옮긴다
다음 단계: 구현
어디서: 새 세션. 인계 줄이라 같은 브랜치·워크트리를 잇는다. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/admin-style/issues/02-admin-organisms-take-props.md
브랜치: feature/02-admin-organisms-take-props
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-27-10-admin-organisms-take-props.md
이어받을 상태: 인계: 커밋 뒤. 구현, 셀프 리뷰와 반영, ADR 0021 이력의 승인, 검증, 커밋까지 마쳤다. 아직 푸시하지 않았고 PR도 없다. 남은 것은 변이 표 전체 실행, PR 직전 리뷰(대체 둘), PR 열기와 봇 회차, 워크트리에서 병합하는 길이고, 그 세부와 커밋하지 않은 일지 절은 일지의 "인계 때 남은 것(둘째)"에 있다. 일지 docs/journal/2026-10-27-10-admin-organisms-take-props.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

워크트리 잠금 풀기는 `is not locked`로 끝났다(이미 풀려 있었다).

open-session을 부른다 2026-10-27T09:45:27Z

## 이어받은 세션(둘째)

위 인계 지시문(둘째)으로 연 새 세션이다. 같은 워크트리에 `EnterWorktree(path)`로 들어갔다. 지시문 밖의 사용자 메시지는 없었다. `git fetch origin main` 뒤 origin/main은 브랜치를 딴 `4f783dc0`에서 움직이지 않았다(손으로 봤다).

### 변이 표 전체 실행(커밋 뒤)

`PYTHONUTF8=1 uv run python tools/mutate.py .scratch/admin-style/probes/organisms_props_mutations.toml`이 커밋 `790416df` 위에서 "변이 5 모두 기대대로"였다(탐침이 찍었다). 둘째·셋째·넷째가 빨강, 첫째·다섯째가 초록이었고, 작업 트리에는 일지만 바뀌어 있었다.

### PR 직전 리뷰

`coderabbit auth status`가 `Seat: not assigned`였다(손으로 봤다). 그래서 대체 둘 가운데 `bug-perf-review` 서브에이전트를 먼저 돌렸다. 브리프에는 위 "PR 직전 리뷰에 밀 주장으로 넘길 새 사실 문장" 다섯을 원문으로 나열했다. `/security-review`는 아직 돌리지 않았다. 변이 도구가 작업 트리를 바꾸는 동안이라 미뤘고, 아래 반영 뒤에 커밋하고 돌린다.

`bug-perf-review`의 보고(기준 `4f783dc0`, 파일 34개, 호출 43, vitest·eslint는 돌리지 않음)와 판정:

- Major. 밀 주장 5가 사실과 다르다. organisms가 값으로 가져오는 `api/` 도메인은 요청 함수가 없는 `api/failure` 하나뿐이고, 요청 함수가 든 `api/plugins`·`api/traces`·`api/approval`에서는 타입만 `import type`으로 가져온다. 그래서 ADR 0021 이력의 "`api/`는 막지 않는다"의 까닭("그 barrel은 요청 함수와 함께 … 실패 해석을 내고")과 거부한 안 "`api/`까지 막는다"의 까닭("organisms의 import를 모두 바꿔야 한다")이 서지 않는다. 유효. `git grep`으로 커밋 `790416df`의 organisms·templates·molecules에서 `api/` import를 모두 보고 확인했다(손으로 봤다).
- Minor. 밀 주장 4의 토큰 열거가 틀렸다. `ChannelTokenForm`도 입력칸에서 채널 토큰을 쥐고, props로 토큰을 받는 organism은 없다. 유효. 두 파일의 props와 제출 처리기를 읽었다.
- 보류. 밀 주장 2(`swr/infinite`도 막힌다)를 돌려 보지 못했다. 닫았다. `pnpm -C web exec vitest run eslint.config.test.ts -t "swr"`가 "3 passed"였다(손으로 봤다).
- 밀 주장 1·3은 맞다고 했다.

### 반영(승인 전, 커밋하지 않음)

규칙을 강제력이 가장 높은 층에 둔다는 기준으로, `api/`를 지침에 두는 대신 판정자가 `api/failure` 밖의 `api/` 도메인 값 import를 막게 넓혔다. 사용자가 승인한 범위("`import type`과 `api/`는 지나가고")를 바꾸는 것이라 ADR 0021 이력 고침의 승인이 다시 필요하다. 작업 규약 5에 따라 셀프 리뷰를 반영한 뒤 묻는다. 아직 묻지 않았다.

- 판정자: 요소 `api`에 `capture: ["domain"]`을 달고, organisms·templates의 값 import 금지에 `{ to: { element: { type: "api", captured: { domain: "!failure" } } } }`를 더했다. 메시지에 "api/failure 밖의 api"를 넣었다. 실험으로 stdin 탐침 셋을 손으로 돌렸다(`pnpm -C web exec eslint --stdin --stdin-filename apps/admin/components/organisms/PluginList.tsx < <파일>`). `api/plugins`의 `listPlugins`를 값으로 가져오면 `boundaries/dependencies`가 그 정책의 메시지로 빨갰고, 같은 폴더의 `import type`과 `api/failure`의 `describeFailure`는 출력 없이 0으로 끝났다. `pnpm -C web exec eslint --max-warnings 0 apps/admin/components apps/admin/hooks apps/admin/stores apps/admin/api apps/widget`이 0으로 끝나 앱 코드는 고칠 것이 없었다(손으로 봤다). 위젯의 organisms·templates는 `api/`를 import하지 않는다(`git grep`).
- 판정자 사례(`web/eslint.config.test.ts`): organisms가 요청 함수가 든 `api` 도메인을 barrel로 import하는 사례(`organisms/Runs.ts`)를 지나보낼 사례에서 위반 사례로 옮겼다. barrel 판정 사례 `DeepApi`와 "barrel 을 거친 import" 사례는 새 정책과 겹쳐 판정력을 잃으므로 pages로 옮겼다(`pages/DeepApi.ts`, `pages/Runs.ts`). 지나보낼 사례 둘을 더했다(`organisms/RunsType.ts`의 `import type`, `organisms/Failure.ts`의 `api/failure`). 임시 트리에 `apps/admin/api/failure/index.ts`를 더했다. 정책 줄을 빼고 돌리면 새 위반 사례 하나만 `AssertionError: expected [] to include 'boundaries/dependencies'`로 실패했고(1 failed, 59 passed, `-t "판정자가|api"`), 넣은 뒤 전체 74 passed였다(둘 다 손으로 봤다).
- 변이 표에 여섯째("판정자가 api/failure 도 막는다", `captured`를 지운다)를 더했다. 손으로 넣어 실패 출력을 본 뒤(그 지나보낼 사례만 실패, 받은 보고의 메시지가 실렸다) 표지를 그 메시지 머리로 골랐고, `tools/mutate.py <표> 6`이 "변이 1 모두 기대대로"였다(탐침이 찍었다). 프로브 README의 줄을 "여섯"으로 고쳤다.
- ADR 0021 이력: 굵은 결정문에 "`api/failure` 밖의 `api/` 도메인"을 더했고, 위젯 문장을 "이것들을 import하지 않아 고칠 것이 없다(… `api/runs`에 있으며 pages가 부른다)"로, `api/` 갈래를 "`api/`는 `api/failure`만 지난다"로, `web-workspace.md` 갈래를 새 지침 줄에 맞게, Considered Options의 "`api/`까지 막는다"를 "`api/`는 막지 않고 지침에 둔다"(첫 초안이 이 안이었고 까닭이 사실과 달랐다)와 "`api/` 전체를 막는다"로 고쳤다. 토큰 문장은 `CONTEXT.md`가 "토큰" 단독을 피하라고 적어 관리 토큰·채널 토큰으로 썼다. 본문에 이 이력이 거짓으로 만드는 문장은 없었다(`grep "organisms"`).
- `.claude/rules/web-workspace.md`의 templates 줄: "서버에 요청하는 함수는 `api/`의 도메인에 두고, 실패 해석만 내는 `api/failure`에는 두지 않는다. 판정자가 organisms에 값 import를 여는 `api/` 도메인이 `api/failure` 하나뿐이다". 고치기 전에 `writing-for-agents`를 불렀다. 카나리아 명세 `web_workspace_organisms.toml`의 질문과 기대를 새 문장으로 바꿔 `uv run python tools/canary.py <명세> <스크래치 출력>`이 통과 4였다(실험군 세 회차가 새 문장을 옮겼고 대조군이 "없음". 탐침이 찍었다, claude 2.1.302, 커밋 `790416df` 위의 작업 트리).
- 티켓 "이 티켓이 정한 것", 명세 292줄의 승인 덧붙임, 헌법 README 3.0.57 문단을 같은 범위로 고쳤다. `tech.md`는 `api/`를 들지 않아 그대로이고 헌법 판도 3.0.57 그대로다.
- `pnpm -C web exec prettier --check eslint.config.mjs eslint.config.test.ts`가 통과였다(손으로 봤다).

고치며 한 번 틀린 것: 티켓에 "(사용자 재승인 2026-10-27)"을 먼저 적었다가, 아직 묻지 않았으므로 "(이 넓힘은 아직 사용자의 승인 전이다)"로 고쳤다. 승인을 받으면 그 괄호와 ADR 이력에 승인 결과를 적는다.

셀프 리뷰와 PR 직전 리뷰에 밀 주장으로 넘길 새 사실 문장(원문):

1. ADR 0021 이력: "organisms가 값으로 쓰는 `api/` 도메인은 실패 해석(`describeFailure`, `RequestFailure`, `isRejection`, `UNREACHABLE`)을 내는 `api/failure`뿐이고, 그 도메인에는 요청 함수가 없다."
2. ADR 0021 이력: "요청 함수가 든 도메인(`api/plugins`, `api/traces`, `api/approval`)에서는 응답 타입만 `import type`으로 가져온다."
3. ADR 0021 이력: "organisms가 쥐는 그 토큰은 관리 토큰과 채널 토큰을 넣는 자리의 입력칸에서 막 받은 것뿐이다(지금 props로 그 토큰을 받는 organism은 없다)."
4. ADR 0021 이력: "판정자가 보지 못하는 것은 `api/failure`에 요청 함수를 두는 것과 요청 함수를 `api/` 밖에 두는 것이고"
5. ADR 0021 이력: "위젯의 organisms와 templates는 이것들을 import하지 않아 고칠 것이 없다(위젯에는 `hooks/queries`와 `stores`가 없고, 서버에 요청하는 함수는 `api/runs`에 있으며 pages가 부른다)."
6. ADR 0021 이력 Considered Options: "`failure` 하나를 여는 정책이 앱 코드를 고치지 않고 서므로 거부했다."

### 인계 때 남은 것(셋째)

이 세션은 셀프 리뷰를 부른 직후 "셀프 리뷰 직전" 경계에서 인계 계기(컨텍스트 298,154 토큰)를 받아 새 세션에 넘긴다. 이 세션의 지금 제목은 `feature/02-admin-organisms-take-props`다. 이 절은 커밋하지 않았다.

- 셀프 리뷰(`/code-review`, 기준 HEAD `790416df`, 티켓 02와 명세)와 반영. 브리프의 밀 주장은 바로 위 여섯이다.
- 셀프 리뷰를 반영한 뒤 ADR 0021 이력 고침(막는 범위에 `api/failure` 밖의 `api/`를 더함)을 쉬운 말로 보여 사용자의 승인을 받는다. 승인되면 티켓의 괄호와 ADR 이력(Considered Options의 "`api/`는 막지 않고 지침에 둔다" 줄)에 승인 결과를 적는다. 거절되면 판정자의 `api` 줄과 `capture`, 판정자 사례의 이동과 추가, 변이 여섯째와 README의 "여섯"을 되돌리고, ADR·티켓·명세·헌법 README·지침 줄·카나리아는 "`api/`는 지난다"로 두되 까닭을 사실대로(위 Major) 고친다.
- 커밋한 뒤 `/security-review`(PR 직전 대체의 보안 쪽). 그 전에 origin/main을 다시 fetch해 움직였으면 합친다. 반영으로 판정자를 고쳤으므로 커밋 뒤 변이 표 여섯째를 `--since origin/main`이나 번호로 한 번 더 돈다(이 세션의 실행은 커밋하지 않은 작업 트리에서였다).
- PR 본문에 적을 것: 위 "인계 때 남은 것(둘째)"의 셋째 줄에 더해, PR 직전 리뷰가 돈 것과 결과(이 절의 표), 그 Major로 판정자 범위를 넓히고 사용자가 다시 승인한 것.
- PR을 열고(`/git-pr`) 봇 회차를 돈 뒤, 일지 "다음"과 회고(`retro`)를 마치고, 이 워크트리 사본의 `next-session` "워크트리에서 병합할 때"로 병합한다.

## 인계 지시문(셋째)

```
다음 작업: .scratch/admin-style/issues/02-admin-organisms-take-props.md. 관리 화면의 organisms가 데이터와 처리기를 props로 받게 옮긴다
다음 단계: 구현
어디서: 새 세션. 인계 줄이라 같은 브랜치·워크트리를 잇는다. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/admin-style/issues/02-admin-organisms-take-props.md
브랜치: feature/02-admin-organisms-take-props
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-27-10-admin-organisms-take-props.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 기준 HEAD 790416df, 티켓 02)부터 한다. PR 직전 bug-perf-review의 Major를 반영해 판정자가 api/failure 밖의 api/ 도메인 값 import도 막게 넓힌 변경이고, 그 ADR 0021 이력 고침은 아직 사용자의 승인을 받지 않았다. 셀프 리뷰를 반영한 뒤 보여 승인받고, 승인 없이 커밋하지 않는다(CLAUDE.md 작업 규약 5). 그 밖에 남은 일은 그 일지의 "인계 때 남은 것(셋째)"이다. 일지 docs/journal/2026-10-27-10-admin-organisms-take-props.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

워크트리 잠금 풀기는 `is not locked`로 끝났다(이미 풀려 있었다).

open-session을 부른다 2026-10-27T10:21:20Z

## 이어받은 세션(셋째)

위 인계 지시문(셋째)으로 연 새 세션이다. 같은 워크트리에 `EnterWorktree(path)`로 들어갔다. 지시문 밖의 사용자 메시지는 아직 없다. `git fetch origin main` 뒤 origin/main은 브랜치를 딴 `4f783dc0`에서 움직이지 않았다(손으로 봤다).

### 셀프 리뷰(넓힘)

`/code-review`, 기준 HEAD `790416df`. 범위는 커밋하지 않은 바뀐 파일 11개(이 일지 포함), 미추적 0개, 커밋 0개. 명세는 티켓 02와 `.scratch/admin-style/spec.md`이고, 사용자의 첫 승인 답을 글자 그대로 요구에 넣었다. 옮긴 판정자 사례의 옛 판정 다섯을 명세 축에 목록으로 넘겼다. 밀 주장은 바로 위 여섯이다.

명세 축(본 세션 모델)이 낸 것과 판정. 옛 판정 다섯은 모두 같다고 했고, 판정자 사례 74개가 초록이었다고 적었다(서브에이전트가 돌렸다). 밀 주장 1·3·5·6은 맞다고 했다.

- Minor. 밀 주장 4("판정자가 보지 못하는 것은 `api/failure`에 요청 함수를 두는 것과 요청 함수를 `api/` 밖에 두는 것이고")는 닫힌 목록인데 반례가 있다. `hooks/queries` 밖의 훅(`hooks/useHydrated.ts` 자리)이 `swr`와 요청 함수를 부르거나 다시 내보내면, 요청 함수가 `api/` 안에 있어도 organism의 import가 지난다(서브에이전트가 `lintText` 탐침으로 봤다). 그리고 새 지침 줄이 옛 문장 "organisms는 `api/`의 요청 함수를 부르지 않고"를 빼서 그 길을 지침도 보지 않는다. 유효. 고친다. 목록을 일반 조항(판정자는 import한 파일의 자리만 본다)으로 바꾸고 둘을 그 예로 두며, 지침 줄에 organisms가 어떤 길로도 요청 함수를 부르지 않는다는 문장을 되살린다.
- Minor. 승인 표시가 문서마다 다르다. 티켓은 "승인 전"이라 적지만, 명세 292줄과 ADR 0021 이력에는 넓힌 범위가 승인 표시 없이 적혀 있다. 유효. 이 넓힘의 승인을 받는 단계에서 셋(티켓, 명세, ADR의 Considered Options)에 같은 결과를 적는다. 승인 없이 커밋하지 않으므로 그 전에 커밋에 실릴 일은 없다.
- Nit. 밀 주장 2의 "응답 타입만"이 정확하지 않다. `RunDecision.tsx`가 `import type`으로 가져오는 `Decision`은 결정 요청 본문의 타입이다(`api/approval/index.ts`). 유효. 고친다(ADR 233줄, 티켓).
- Nit. templates가 `api/`를 값으로 import하는 판정자 사례가 없다. 정책의 `from`이 organisms와 같아 판정은 같다(서브에이전트가 탐침으로 봤다). 유효. 사례 하나를 더한다. `hooks/queries`에는 templates 사례가 있다.
- Nit. 카나리아 명세 머리 주석의 옛 문장 인용에 원문의 백틱이 빠졌다(`git show 790416df:.claude/rules/web-workspace.md`와 견줘 손으로 봤다). 유효. 고친다.
- 훅이 아닌 함수의 자리: `isPluginKind`(`api/plugins`)는 이제 organisms에서 막히지만 쓰는 곳이 pages 하나라 옮길 것이 없다고 했다. 받아들인다(`git grep isPluginKind`로 손으로 봤다).

표준 축(sonnet·high)이 낸 것과 판정. 새 정책은 실제로 선다고 했다. stdin 탐침 12건(값 import, 같은 줄 `type` 지정자, `import *`, 부수효과 import, 동적 `import()`, 값 다시 내보내기는 막히고, `import type *`, `export type`, `api/failure`와 그 `index`는 지났다)과 앱 코드 eslint 0, 변이 여섯째의 `-t`가 사례 하나만 고른다는 것을 서브에이전트가 돌렸다. 밀 주장 1·3·5·6은 맞다고 했다.

- Major. 명세 292줄에 덧붙인 "사용자가 그 초안을 승인했다. 판정자가 … `api/failure` 밖의 `api/` 값 import를 막고"는 승인 전의 넓힘을 승인된 것처럼 적는다. ADR 0021 이력, 헌법 README 3.0.57 문단, `web-workspace.md`에도 승인 전 표시가 없다. 명세 축의 Minor와 같은 지적이다. 유효. 승인을 묻는 단계에서 결과를 함께 적어 닫는다. 승인 없이 커밋하지 않으므로 표시 없는 문장이 커밋에 실리지 않는다.
- Minor. 변이 표 머리 주석의 "그 지나보낼 사례는 예외를 넣은 뒤에 써서 빨강을 본 적이 없다"는 여섯째 변이가 그 사례를 빨갛게 하므로 읽는 대로면 거짓이고, 머리의 "새 시험이 없고"도 여섯째에는 맞지 않는다. 유효. 고친다(변이를 둔 까닭으로 쓰고, 첫째~다섯째와 여섯째를 가른다).
- Minor. ADR의 "응답 타입만"은 명세 축의 Nit과 같다. 고친다.
- Minor. 밀 주장 4의 닫힌 목록에 `lib/`의 래퍼가 셋째 길로 남는다(관리 화면에는 `lib/`가 없어 지금의 위반은 아니다. 서브에이전트가 설정을 읽었다). 명세 축의 Minor와 같은 지적이다. 일반 조항으로 고칠 때 예로 넣는다.
- Minor. `web-workspace.md`의 "판정자가 organisms에 값 import를 여는 `api/` 도메인이 `api/failure` 하나뿐이다"는 판정자가 하는 일을 다시 적어, 그 파일 머리의 "여기 다시 적지 않는다"와 어긋난다. 유효. 지침 줄을 판정자가 보지 못하는 길(일반 조항)을 적는 문장으로 고치며 뺀다.
- 판단 항목. 같은 열거(`hooks/queries`·`stores`·`swr`·생성 클라이언트·`api/failure` 밖의 `api/`)가 ADR, 티켓, 명세, 헌법 README, ESLint 메시지, 일지에 따로 쓰여, 이번 넓힘 한 번에 여러 파일을 고쳤고 명세의 승인 표시가 어긋났다(Duplicated Code·Shotgun Surgery). 받아들인다. `CLAUDE.md`의 "같은 사실은 한 곳에만 둔다"에 따라 명세 292줄과 헌법 README 3.0.57 문단의 열거를 ADR 0021 이력을 가리키는 말로 줄인다. 티켓의 "이 티켓이 정한 것"은 티켓이 범위와 까닭을 적으라고 요구해 남기고, ESLint 메시지는 위반을 본 사람에게 보이는 글이라 남긴다.
- Nit. ADR 0021 235~237줄의 줄바꿈이 다른 줄과 다르다. 유효. 고친다.

고친 것(셀프 리뷰 반영, 승인 전이라 커밋하지 않음):

- `.claude/rules/web-workspace.md`의 templates 줄: 판정자가 하는 일을 다시 적던 문장을 빼고, "organisms는 서버 요청을 props로 받은 처리기로만 일으킨다. 요청 함수는 `api/failure` 밖의 `api/` 도메인에, 그것을 부르는 훅은 `hooks/queries`에 둔다. 판정자는 import한 파일이 놓인 자리만 보아, …를 거쳐 organisms에 닿으면 지나보낸다"로 고쳤다. 고치기 전에 `writing-for-agents`를 불렀다. 카나리아 명세의 기대를 새 둘째 문장으로 바꾸고 머리 주석의 옛 인용에 백틱을 되살렸다. `uv run python tools/canary.py .scratch/admin-style/probes/canary/web_workspace_organisms.toml <스크래치>`가 통과 4였다(실험군 세 회차가 새 둘째 문장을 옮겼고 대조군 한 회차가 "없음". 탐침이 찍었다, claude 2.1.302, 커밋 `790416df` 위의 작업 트리).
- ADR 0021 이력: "응답 타입만"을 "타입만"으로, 판정자가 보지 못하는 길의 닫힌 목록을 일반 조항("판정자는 import한 파일이 놓인 자리만 본다. 그래서 요청 함수가 막지 않는 자리를 거쳐 organisms에 닿으면 지나보낸다")과 그 예 셋으로, `web-workspace.md` 갈래를 새 지침 줄에 맞게 고쳤고, 줄바꿈을 맞췄다. 고치기 전에 `domain-modeling`을 불렀다.
- 티켓 "이 티켓이 정한 것": "응답 타입만"과 지침 문장을 같은 범위로 고쳤다. 승인 괄호는 승인 단계에서 고친다.
- 명세 292줄과 헌법 README 3.0.57 문단: 막는 목록의 열거를 빼고 ADR 0021 이력을 가리키게 줄였다(명세에서 넓힌 범위를 승인된 것처럼 적던 문장도 이것으로 빠졌다).
- 판정자 사례: templates가 요청 함수가 든 `api` 도메인을 barrel로 import하는 위반 사례(`templates/Runs.ts`)를 더했다. `pnpm -C web exec vitest run eslint.config.test.ts`가 75 passed였고 `prettier --check`가 두 파일 모두 통과였다(손으로 봤다).
- 변이 표: 머리 주석을 첫째~다섯째와 여섯째·일곱째로 갈라 고쳤고, 일곱째("판정자가 organisms 와 templates 의 api 도메인 import 를 막지 않는다", `api` 줄을 지운다)를 더했다. 고르기 전에 그 줄을 손으로 지우고 `pnpm -C web exec vitest run eslint.config.test.ts -t "요청 함수가 든 api 도메인을 barrel"`을 돌려, organisms·templates 두 사례가 모두 `AssertionError: expected [] to include 'boundaries/dependencies'`로 실패하는 것을 봤다(손으로 봤다. 곧바로 되돌렸다). 표지로 처음 고른 집계 줄 `Tests  2 failed`는 `--check`가 "어느 실패에나 찍는 판정 낱말뿐"이라며 거부해, 실패한 시험에만 찍히는 FAIL 줄의 경로(묶음 이름 > 시험 이름) 둘로 바꿨다. 그 뒤 `--check`가 "변이 7 모두 원문이 한 번씩 있다", `tools/mutate.py <표> 6 7`이 "변이 2 모두 기대대로"였다(탐침이 찍었다). 프로브 README의 줄을 "일곱"으로 고쳤다.

셀프 리뷰 반영으로 새로 쓴 사실 문장(PR 직전 리뷰에 밀 주장으로 넘긴다, 원문):

1. ADR 0021 이력: "판정자는 import한 파일이 놓인 자리만 본다. 그래서 요청 함수가 막지 않는 자리를 거쳐 organisms에 닿으면 지나보낸다. `api/failure`에 요청 함수를 두는 것, `hooks/queries` 밖의 훅이나 `lib/`의 함수가 요청 함수를 부르거나 다시 내보내는 것이 그 예다."
2. ADR 0021 이력: "요청 함수가 든 도메인(`api/plugins`, `api/traces`, `api/approval`)에서는 타입만 `import type`으로 가져온다."
3. ADR 0021 이력: "그 토큰으로 `api/`의 요청 함수를 바로 부르는 길이 이것으로 판정자에게 막힌다."
4. `.claude/rules/web-workspace.md`: "판정자는 import한 파일이 놓인 자리만 보아, 요청 함수가 실패 해석만 내는 `api/failure`나 `hooks/queries` 밖의 훅·`lib/`의 함수를 거쳐 organisms에 닿으면 지나보낸다."
5. 헌법 README 3.0.57: "organisms·templates가 서버 데이터와 관리·채널 토큰을 읽는 모듈을 값으로 import하는 것은 판정자가 막는다(범위는 ADR 0021의 2026-10-27 이력)."

남긴 것: 표준 축의 열거 중복 가운데 티켓의 "이 티켓이 정한 것"과 ESLint 메시지(위 판정 줄의 까닭). 승인 표시(두 축의 Major·Minor)는 바로 아래 승인 단계에서 닫는다.

### ADR 0021 이력 고침(넓힘)의 승인

셀프 리뷰를 반영한 뒤 처음 승인한 판과 넓힌 판을 표로 견줘 보이고(막히는 것, 지나는 것, 앱 코드 수정 없음, 여전히 지침이 보는 길), 잡아 주는 것과 치르는 값을 적은 뒤 물었다. 첫 호출은 선택지의 사실을 대 보라는 훅에 한 번 막혔고, 판정자 시험 75개(손으로 돌렸다)와 두 리뷰 축의 확인을 대 본 뒤 같은 질문을 다시 띄웠다.

> 질문: 화면 부품(organisms·templates)이 요청 함수가 든 api/ 폴더를 직접 가져오는 것도 커밋 전 검사가 막게 넓힐까요?
>
> 사용자: api/ 직접 가져오기도 막는다 (Recommended) — "넓힌 판을 커밋한다. 부품 파일이 api/plugins·api/traces·api/approval 같은 요청 함수 폴더를 값으로 import하면 pnpm -C web verify와 pre-commit이 빨갛게 막는다. api/failure와 import type은 지나간다. 다른 길(api/failure에 요청 함수 두기, hooks/queries 밖의 훅이나 lib/ 래퍼)은 web-workspace.md 지침과 리뷰가 본다. ADR 0021 이력·티켓에 이 재승인을 적는다."

고르지 않은 선택지는 "처음 승인한 대로 api/는 둔다"(넓힘을 되돌리고 `api/`는 지침과 리뷰만 본다. ADR의 까닭 문장은 사실대로 고친다)였다. 그래서 넓힌 판을 그대로 커밋한다.
