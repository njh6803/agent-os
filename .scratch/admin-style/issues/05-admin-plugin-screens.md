# 05: 플러그인 목록에서 이름을 눌러 켜고 끄고, 매니페스트는 줄 끝의 링크로 본다

**What to build:** 운영자가 플러그인 목록에서 종류(에이전트, MCP, 스킬, 모델)마다 묶인 줄과 종류마다의 개수를 보고, 플러그인 이름이나 스위치를 눌러 그 자리에서 켜고 끈다. 플러그인 하나의 매니페스트는 같은 줄 끝의 "매니페스트" 링크로 열고, 그 화면에서 켜짐·꺼짐을 아이콘과 글자로, 매니페스트를 들여 쓴 JSON으로 본다. 읽을 수 없는 매니페스트, 로더가 없는 스킬·모델, 등록된 것이 없는 종류는 아이콘과 한 줄로 보이고, 켜고 끄지 못하면 어느 플러그인이 실패했는지와 스위치가 다시 읽은 값이라는 것을 알림으로 본다.

근거는 `.scratch/admin-style/spec.md`의 "플러그인 목록과 플러그인 하나" 전부, "화면 머리와 공통 상태"의 실패 알림 표에서 켜고 끄기 행, Testing Decisions "동작"의 플러그인 줄과 "e2e"(그 2026-10-27 주석의 `plugin-toggle.e2e.ts`)다. 이름이 스위치의 이름인 것은 사용자가 골랐다(일지 2026-10-26-16). 그림은 `mk-plugins.dc.html`, `mk-plugins-m.dc.html`, `mk-plugin.dc.html`, `mk-plugin-m.dc.html`이다. 본문의 최대 폭 `content`는 명세 "패키지에 더하는 것"의 기준 폭 주석과 이 절의 2026-10-27 주석이 근거이고 01이 지었다. 화면 머리, 빈 줄, 링크, 코드 칸, 실패 알림의 모양은 04가 지었다.

**Blocked by:** 04

**Status:** done

### 시작 전

- [x] `/ui-design`의 "웹 편집 확인"을 위 그림 넷과 옮긴 `canvas.json`에 먼저 한다. 지금 계정이 화면 Design 아티팩트를 읽지 못하면 03처럼 멈추고 사람에게 넘긴다. 다르면 멈추고 사람에게 묻는다

### 플러그인 목록

- [x] **플러그인 목록과 플러그인 하나의 본문은 넓어도 최대 폭 `content`(880px)를 넘지 않는다.** 그림 `mk-plugins.dc.html`·`mk-plugin.dc.html`의 28줄이다
- [x] `h1`은 "플러그인 <전체 개수>", 설명은 "종류마다 등록된 플러그인을 켜고 끈다."다. 종류마다 `h2` "<종류 이름> <개수>"이고 차례는 에이전트, MCP, 스킬, 모델이다. 개수는 데이터가 있을 때만 붙는다
- [x] **줄마다 패키지 `Switch`(보이는 이름이 플러그인 이름)와 같은 줄 끝의 링크 "매니페스트"(플러그인 하나로 간다)다.** 이름이나 스위치를 누르면 그 자리에서 켜고 끄는 요청이 간다. 지금은 이름이 플러그인 하나로 가는 링크다. "켜짐"·"꺼짐" 글자는 스위치가 그린다. "매니페스트" 링크의 포인터 목표는 24px 이상이다
- [x] 읽을 수 없는 매니페스트의 줄은 `triangle-alert` 14와 "읽을 수 없는 매니페스트: <이유>"이고, 스킬·모델의 줄은 `info` 14와 "로더가 생기기 전에는 효과가 없다"다. 빈 종류는 `circle-minus` 16과 "등록된 것이 없다"(빈 줄)다. 표지가 있는 줄을 켜고 끌 수 있는지는 지금 행동 그대로다
- [x] **켜고 끄기의 실패 알림**은 화면 머리 아래에 선다. 제목 "켜고 끄지 못했다: <종류 경로>/<이름>", 본문은 메시지, 고정폭의 추적 식별자(있을 때), "스위치는 다시 읽은 값이다."다. 스위치는 다시 읽은 값이다(지금 행동)

### 플러그인 하나

- [x] 링크 "플러그인 목록"(돌아가기), `h1` 플러그인 이름과 그 옆의 켜짐(`circle-check` 16, "켜짐")이나 꺼짐(`circle-minus` 16, "꺼짐"), 설명 "<종류 이름>. 켜고 끄기는 플러그인 목록에서 한다.", `h2` "매니페스트"와 코드 칸이다

### 시험

- [x] 페이지 시험(`HomePage.test.tsx`, `PluginPage.test.tsx`)이 이름(스위치의 이름)을 누르면 켜고 끄는 요청이 가고, "매니페스트" 링크가 플러그인 하나로 가는지 본다. 이름을 링크로 찾던 단언은 바뀐다. 종류의 `h2`와 개수, 표지 줄, 빈 종류, 켜고 끄기 실패 알림의 제목·본문을 본다
- [x] 스토리가 목록(종류 넷과 표지 줄), 빈 종류, 켜고 끄기 실패, 플러그인 하나의 켜짐과 꺼짐을 그리고, 두 프로젝트에서 클래스 판정과 axe, 가로 스크롤 없음을 지난다. 표본 값은 그림의 것이다
- [x] `plugin-toggle.e2e.ts`가 플러그인 하나를 "매니페스트" 링크로 연다. 그 파일의 "허가"는 08이 고친다. 이 티켓과 08이 나란히 돌면 그 파일이 부딪칠 수 있으니 늦게 병합하는 쪽이 main을 합치고 둘 다 남긴다
- [x] `pnpm -C web visual:admin:update`로 새 스토리의 정답을 만들고, 바뀐 사진을 사람이 보고 PR 본문에 적는다

메모(04에서): 04가 지은 공통 부품의 이름이다. 화면 머리는 `molecules/ScreenHeader`, 읽기 골격은 `organisms/ReadSection`(머리 아래 자리 `above`, 처음 불러오는 중의 `loadingLabel`, 실패 제목 `failureTitle`), 실패 알림은 `molecules/FailureAlert`(제목, 메시지, 추적 식별자), 글자 링크는 `atoms/TextLink`, 코드 칸은 `atoms/CodeBlock`과 JSON을 두 칸 들여 쓰는 `formatJson`, 빈 줄은 `molecules/EmptyLine`(아이콘 16·20)이다. 04는 부품을 짓고 스토리만 그렸고 화면에는 넣지 않았다. 켜고 끄기의 실패(`organisms/PluginList`의 `above`)와 `PluginPage`의 두 자리(주소를 풀지 못한 실패, 플러그인의 종류가 아닌 주소)는 아직 옛 `molecules/FailureNotice`다. `PluginPage`의 두 자리는 지역 부품 `AddressFailure`가 화면 머리(`ScreenHeader`, 제목은 주소의 이름 조각)와 함께 그리므로, 옮길 때 그 머리를 남긴다(04의 "이 티켓이 정한 것"). `RunPage`에도 같은 뼈대(`useId`, `aria-labelledby` 구역, `ScreenHeader`, 실패 알림)의 같은 이름 지역 부품이 있어, 07과 이 티켓 가운데 먼저 옮기는 쪽이 둘을 한 부품으로 합칠지 정한다(PR #423 claude-review의 Minor). 이 티켓이 `FailureAlert`로 옮긴 뒤 쓰는 곳이 남지 않으면 옛 것을 지운다. 지우기 전에 `FailureNoticeProps`를 옮긴다. `FailureAlert`가 그 타입을 `./FailureNotice`에서 가져오고, `PluginList`의 `SwitchFailure`와 `RunDecision`도 그 타입을 쓴다. 옛 것을 쓰는 곳은 07(`RunPage`)과 08(`RunDecision`)에도 있어, 셋 가운데 마지막에 병합하는 티켓이 지운다.

이 티켓이 정한 것:

- 목록의 전체 개수는 `h1` 안에 둔다(티켓 문장 "`h1`은 '플러그인 <전체 개수>'"). 그림은 개수를 `h1` 옆에 두었다. 종류의 개수는 그림대로 `h2` 안이다. 개수는 읽은 목록이 보일 때만 붙고, 다시 읽다 실패해 행을 지우면 개수도 걷힌다. 플러그인 하나의 켜짐·꺼짐도 같다.
- 플러그인 하나의 켜짐·꺼짐은 제목 옆에 서되 제목의 이름에 들지 않는다. 그 자리로 `molecules/ScreenHeader`에 `beside`, `organisms/ReadSection`에 `titleBeside`를 더했다. `beside`·`titleBeside`를 넘기지 않는 화면의 그림은 그대로다.
- 실패 알림 표의 "본문에 더하는 것"은 `molecules/FailureAlert`의 `note`다. 명세의 표는 그 자리를 정하지 않았다. 그림 mk-plugins는 메시지와 같은 줄에 이어 쓰고, 이 티켓의 켜고 끄기 줄은 추적 식별자 뒤에 적었다. `note`는 메시지 다음 줄, 추적 식별자 앞에 선다. 차례는 그림을 따랐고, 서버의 메시지와 화면이 더한 글을 가르려고 줄을 나눴다. 채널 토큰이 거부된 알림(08)의 "설정에서 다시 넣는다."도 이 자리를 쓸 수 있다.
- 넓은 폭에서 목록 머리(와 실패 알림)와 첫 종류 묶음 사이는 읽기 골격의 `gap-6`(24px)이다. 그림 mk-plugins는 그 사이도 묶음 사이와 같은 32px이다. 읽기 골격의 간격은 다른 화면과 함께 쓰므로 바꾸지 않았다. 좁은 그림 mk-plugins-m은 24px이라 같다.
- 켜고 끄기의 실패는 상태를 드는 `PluginList`와 그 상태를 props로 받아 그리는 `PluginListView`로 나눴다. 스토리가 누르지 않고 실패한 모습을 그린다. 사진은 play가 `userEvent`를 처음 부르기 전의 그림이라(`.claude/rules/web-design.md`) 눌러서 세운 상태는 사진에 들지 않는다.
- `PluginList`와 `PluginPage`는 이제 부품으로는 `FailureAlert`만 쓴다(`PluginList`는 타입 `FailureNoticeProps`를 아직 가져온다). 옛 `molecules/FailureNotice`는 `RunPage`(07)와 `RunDecision`(08)이 아직 써서 지우지 않았다. 07과 08 가운데 마지막에 병합하는 쪽이 `FailureNoticeProps`를 옮기고 지운다(`FailureAlert`와 `PluginList`의 `SwitchFailure`가 그 타입을 가져온다).
- `PluginPage`의 `AddressFailure`와 `RunPage`의 같은 이름 지역 부품은 합치지 않았다. 07이 나란히 돌아 `RunPage`를 고치므로, 합칠지는 07이 정한다. `PluginPage`의 것은 돌아가는 링크, 화면 머리, `FailureAlert`(제목 "플러그인을 읽지 못했다")다.
- PR #423 claude-review 다섯째 회차의 Nit(`ReadSection`의 `AfterDelay`가 둘이라 타이머가 둘 돈다)는 고치지 않았다. 06·07도 `ReadSection`을 지나므로 남긴다.

### 검증

- [x] 검증 명령이 모두 초록이고, `pnpm -C web visual:admin`과 관리 화면 e2e도 초록이다. 모델 경로를 건드리지 않아 `-m llm`·`-m llm_widget`은 칠 일이 없다
