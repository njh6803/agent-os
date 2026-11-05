# 2026-11-05 (03) skill-plugin 04: 관리 화면이 스킬 켜고 끄기의 효과를 사실대로 말하고, 꺼진 스킬로 막힌 결정을 미리 알린다 (구현 세션)

세션 제목은 `feature/04-admin-skill-toggle-and-decision-preview`이다(인계 뒤에는 `(인계함)`이 붙는다). 티켓은 `.scratch/skill-plugin/issues/04-admin-skill-toggle-and-decision-preview.md`이다.

## 사용자 프롬프트

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다.
> 인자: .scratch/skill-plugin/issues/04-admin-skill-toggle-and-decision-preview.md
> 다음 단계: 구현 / 어디서: 새 세션(나란히 여는 2 중 1, 주 체크아웃 미갱신이라 tidy-checkouts를 먼저 돌고 EnterWorktree로 새 워크트리에 들어간다) / 브랜치: feature/04-admin-skill-toggle-and-decision-preview / 모델: Sonnet 5.5 / high / 읽을 것: .scratch/skill-plugin/issues/05-calc-uses-answer-format-skill.md(나란히 도는 형제, 함께 고치는 파일은 없다), 일지 2026-11-05-01의 "결정" 절 / 이어받을 상태: 03은 PR 463으로 병합됐다. 대기열 572는 이 티켓의 몫이 아니다 / 이번 요청 범위: PR과 병합까지 (원문은 줄바꿈이 있는 지시문이었다. 위는 그 값을 옮긴 것이다.)

## 한 것 (모두 커밋하지 않은 작업 트리에 있다)

- 시작: 제목을 브랜치 이름으로 바꾸고 `tidy-checkouts`를 돌았다. 루트를 `3012f78d`에서 `5b255a18`(`origin/main`)로 당겼다. 지울 후보였던 `05-default-model-required-and-checked` 워크트리는 `agent-os.exe`·`python.exe` 프로세스가 쥐고 있어 남겼고, 나머지도 병합되지 않았거나 바뀐 파일이 있거나 실행 중 세션이 쥐고 있어 남겼다. `EnterWorktree`로 들어간 뒤 브랜치를 `feature/04-admin-skill-toggle-and-decision-preview`로 바꿨다(`git branch -m`). `uv sync`와 `pnpm -C web install --frozen-lockfile`을 쳤다.
- 티켓 `Status:`를 `ready-for-agent`에서 `in-progress`로 바꿨다. 체크박스는 아직 체크하지 않았고 `done`으로 바꾸는 것은 PR 직전이다.
- `sync-design-system 확인`: 계기 훅이 화면 코드를 처음 고칠 때 불렀다. 아티팩트에서 받은 파일 17개로 판정했고 `decide`가 `act: continue`(웹 편집 없음)를 냈다.
- 시험을 먼저 썼다(원칙 II).
  - `web/apps/admin/components/pages/RunPage.decision.test.tsx`: 도우미 `skillPlugin`, `calcSelecting`과 사례 넷. 고른 스킬이 꺼졌으면 버튼이 막히고 `스킬 answer-format`이 보인다 / 고르지 않은 스킬이 꺼진 것은 막지 않는다 / `skills`가 빈 에이전트는 꺼진 스킬이 있어도 미리 막지 않는다 / 고른 스킬의 행이 표지면 막지 않고 `스킬 answer-format`도 보이지 않는다.
  - `web/apps/admin/components/pages/HomePage.test.tsx`: "스킬 행에만 … 보인다"를 "어느 종류의 행에도 … 보이지 않는다"로 바꿨다(`NO_EFFECT`가 스킬 행·스킬 묶음·모델·에이전트·MCP 어디에도 없다는 단언).
  - `web/apps/admin/components/organisms/PluginList.stories.tsx`의 `List` play: 안내 줄이 보인다에서 `queryByText`가 `null`이다로.
  - `web/apps/admin/e2e/admin-token.e2e.ts`: 스킬 행 단언이 `not.toContainText`로.
- 빨강을 봤다. 두 vitest 파일에서 실패가 정확히 둘이었다. `HomePage.test.tsx`는 안내 줄이 아직 보인다, `RunPage.decision.test.tsx`는 "꺼진 플러그인이 있어 재개할 수 없다"를 찾지 못한다. 나머지 83개는 초록이었다.
- 구현.
  - `PluginList.tsx`: `WITHOUT_LOADER` 집합과 주석, 안내 줄을 그리던 `<p>`를 지웠다. `Icon`과 `PluginKind` import는 다른 곳에서 쓰여 남는다.
  - `RunDecision.tsx`의 `disabledFor`: 모델 갈래 뒤에 `row.manifest.skills`를 적힌 순서대로 돈다. 그 이름의 스킬 행이 `"manifest" in other`이고 꺼져 있을 때만 `스킬 <이름>`을 더한다. 독스트링에 `skills`와 표지 행을 세지 않는 까닭, 서버의 꺼짐 순서와 같다는 것, mcp 갈래는 표지를 거르지 않는데 스킬은 거른다는 것을 더했다.
- 초록을 봤다. 위 두 vitest 파일 85개가 통과했다.
- `pnpm -C web verify`가 초록이다.
- `pnpm -C web visual:admin`이 빨갰다. 바뀐 것은 `organisms-pluginlist--list`와 `--switch-failed`의 폭 둘(1280, 320) × 라이트·다크 = 여덟 장이었고, 나머지 68개는 통과했다. 티켓의 어림과 같다. 예를 들어 `switch-failed-320-light`는 높이가 1002px에서 982px로 줄었고 안내 줄 한 줄(20px) 몫이다. `pnpm -C web visual:admin:update`로 정답을 컨테이너 안에서 다시 만들었고 `git status`에 바뀐 사진이 정확히 그 여덟 장이다.
- 관리 화면 e2e(`pnpm -C web/apps/admin exec playwright test`)가 초록이다.
- `uv run ruff check .`, `uv run ruff format --check .`가 초록이다. `uv run python tools/run_checks.py`가 초록으로 끝났다(파이썬은 안 건드렸고 pytest·pyright·import-linter·web을 함께 돈다).
- `uv run python tools/check_adr_pointers.py`가 출력 없이 끝났다(정상).
- ADR 0019에 이력 초안을 썼다(`### 2026-11-05 꺼짐 미리 알림이 에이전트가 고른 스킬까지 본다`). 본문 27행의 문장 뒤에 포인터 `(바뀜: 이력 2026-11-05 "꺼짐 미리 알림이 에이전트가 고른 스킬까지 본다")`를 앞선 포인터 뒤에 이었다. `/code-review`를 반영한 뒤 사용자에게 보여주고 승인을 받아야 한다(`CLAUDE.md` 작업 규약 5, 티켓의 ADR 체크박스).

## 근거의 종류

- 시험의 빨강과 초록(vitest 85개 가운데 의도한 둘이 빨갛고 고친 뒤 85개가 통과), `pnpm -C web verify`, `visual:admin`의 빨강(4개 실패에 폭 둘 × 모드 둘, 68개 통과)과 `:update` 뒤 `git status`의 사진 여덟 장, 관리 화면 e2e, ruff 둘, `run_checks.py`, `check_adr_pointers.py`는 이 세션이 그 명령을 쳐서 출력으로 본 것이다.
- `switch-failed-320-light`의 높이 1002px에서 982px는 `visual:admin`의 출력이다. 그 20px이 안내 줄 한 줄의 몫이라는 것은 어림이다. 줄을 지운 변경과 높이 차가 함께 났다는 것만 본 것이고 줄의 높이를 따로 재지 않았다.
- `Icon`·`PluginKind` import가 남는다는 것은 코드를 읽은 것이고, 타입 검사와 린트(`pnpm -C web verify`)가 초록인 것이 그것을 받친다.
- 옛 표현의 잔존 0은 `Grep`으로 `.md`·`.ts`·`.tsx`·`.py`·`.toml`·`.json`을 훑어 본 것이다. 긴 일치 줄이 내용 없이 생략된 곳(명세 줄 7·147, ADR 0040·0041의 줄)은 열어 보지 않았다. 그 줄들은 기록이거나 이 변경이 뜻을 바꾸지 않는 서술로 어림한다. 새 세션이 셀프 리뷰에서 잰다.
- `DisabledPlugins` 스토리에 스킬 사례가 필요 없다는 것은 코드를 읽은 어림이다(티켓의 어림과 같다). `RunDetail`의 사진이 안 바뀐 것은 사진 비교의 출력이다.

## 결정

- **`DisabledPlugins` 스토리에는 스킬 사례를 더하지 않았다.** 티켓이 시작할 때 고르라고 한 것이다. 경고의 모양은 그대로이고 스킬 사례는 vitest가 덮으며, 더하면 문구와 사진이 함께 바뀌어 `RunDetail`의 사진 정답까지 다시 만들어야 한다. 사진 비교가 `RunDetail` 스토리의 변화 없이 초록이었던 것이 이 선택과 맞는다.
- **관리 화면 e2e의 꺼짐 흐름에는 스킬 사례를 더하지 않았다.** 미리 알림은 화면 안의 계산이고 서버를 지나지 않아 vitest로 덮는다(티켓의 마지막 체크박스).
- **`skills` 갈래는 모델의 꼴로 센다.** `mcp`처럼 `manifest`를 보지 않으면 표지 행이 꺼져 있을 때 꺼짐으로 세는데, 읽지 못한 스킬은 켜도 실행이 막히므로 그 까닭을 꺼짐이라 말하면 틀리다. 명세 C의 2026-11-04 검토 주석과 ADR 0041의 2026-11-04 이력이 정한 것이다.
- **옛 표현의 잔존을 살아 있는 문서에서 0으로 확인했다.** `로더가 생기기 전에는 효과가 없다`와 `WITHOUT_LOADER`는 기록(ADR 0017·0040·0041 본문의 포인터가 달린 문장, 명세, 일지, 닫힌 티켓)에만 남는다. 지침이 정한 대로 기록은 고치지 않았다. 코드와 시험에서 남은 곳은 안내 줄이 없다는 단언의 상수와 문구뿐이다.

## 번복하거나 고친 것

- 없다. 시험은 한 번에 의도한 빨강과 초록을 냈다.

## 이 세션이 한 실수

- `Monitor`를 스키마 없이 부르려다 거부당했다. 백그라운드 명령은 끝 알림이 오므로 필요 없었다. 해를 끼친 것은 없다.
- 워크트리 가드가 변수가 든 `cp`·`node` 명령을 거부했다. CLAUDE.md 환경 함정이 말한 모양 그대로라 절대 경로로 하나씩 나눠 쳤다.

## 인계

컨텍스트가 인계 문턱(20만 토큰)을 넘은 채 `셀프 리뷰 직전` 경계에 왔다(방금 불린 `code-review` 스킬이 계기). 새 세션은 커밋하지 않은 변경이 든 같은 워크트리에서 `/code-review`부터 한다. 이 세션은 `code-review`의 어떤 단계도 밟지 않았다.

open-session을 부른다 2026-11-04T17:27:35Z

## 셀프 리뷰 (새 세션, 2026-11-04T17:50Z 무렵)

범위: base `5b255a18`, 파일 16개(사진 여덟 장 포함), 커밋 0개, 미추적 1개(이 일지). 명세 축은 모델 기본 effort로, 표준 축은 sonnet·high로 돌았다. `sync-design-system 확인`은 앞 세션이 한 결과(웹 편집 없음)를 이 작업의 확인으로 갈음해 다시 돌리지 않았다. 그 뒤 고친 것은 `web/apps/admin` 안뿐이다.

### 보고 (Critical·Major 없음)

- 명세 축: 요구 전부 구현, 범위 넘침 없음. Minor 하나: 꺼진 것이 여럿일 때의 순서(모델 뒤 스킬, 적힌 순서)를 고정하는 시험이 없다.
- 표준 축: Minor 둘, Nit 넷.
  - Minor: 새 시험 셋(고르지 않은 스킬, `skills`가 빈 에이전트, 표지 행)이 구현 전부터 초록이었고 변이로 빨강을 본 기록이 없다. 모델 티켓 06은 `decision_model_mutations.toml`로 잡았다.
  - Minor: 독스트링의 "읽지 못한 스킬은 켜져 있어도 실행이 막힌다"가 표지 행만 말한다. `SKILL.md`가 없거나 깨진 스킬은 표지가 아니라 보통 행이고, 서버는 깨짐을 꺼짐보다 먼저 판정하므로 화면이 꺼짐을 알려도 서버는 읽을 수 없다고 답한다.
  - Nit: `disabledFor`의 모델 갈래와 스킬 갈래의 중복(Duplicated Code) / `HomePage.test.tsx`의 `group("스킬")` 단언이 바로 위 `row` 단언을 포함한다 / 독스트링의 "ADR 0041의 2026-11-04 이력"이 같은 날짜의 이력 둘 가운데 어느 쪽인지 모호하다 / ADR 0019 새 이력에서 "Consequences의 해당 줄은 이렇게 읽는다"가 다른 문장 사이에 끼어 있다.

### 판정

- 순서 시험: 더했다(`꺼진 것이 여럿이면 모델 뒤에 스킬이 매니페스트에 적힌 순서로 보인다`). `calcSelecting`이 선택 인자 `model`을 받는다.
- 변이 표: 더했다(`.scratch/skill-plugin/probes/decision_skill_mutations.toml` 4개). 처음 쓴 순서 변이의 표지 문구가 시험 원문에 그대로 있어 `tools/mutate.py`가 거부했고(대기열 417), 변이가 낸 화면 문구 `모델 sonnet, 스킬 answer-format, 스킬 brief`로 바꿨다.
- 독스트링: "매니페스트를 읽지 못한 스킬"로 좁히고 한계 한 줄을 더했다. ADR 0019 이력에도 같은 한계를 적었다.
- `HomePage.test.tsx`의 중복 단언을 지웠다. 독스트링의 ADR 포인터를 이력 제목으로 바꿨고, ADR 0019의 "Consequences의 해당 줄은 이렇게 읽는다"를 첫 문단 끝으로 옮겼다.
- Duplicated Code는 남긴다. 모델 갈래의 판정을 도우미로 빼면 모델 변이 표(`.scratch/model-plugin/probes/decision_model_mutations.toml`)가 원문으로 드는 두 줄이 사라져 닫힌 티켓의 근거가 깨진다. 같은 모양이 둘뿐이고 mcp 갈래는 모양이 달라 도우미의 값이 작다고 본다.

### 다시 돌린 명령 (이 세션이 쳐서 출력으로 본 것)

- `pnpm -C web exec vitest run` 두 파일(`RunPage.decision.test.tsx`, `HomePage.test.tsx`): 86개 통과.
- `tools/mutate.py .scratch/skill-plugin/probes/decision_skill_mutations.toml`: `--check`에서 원문이 변이마다 한 번씩 있었고, 전체 실행에서 기준선 넷이 초록, 변이 넷이 기대대로 빨강이었다(`변이 4 모두 기대대로`). 실행 뒤 `RunDecision.tsx`에 변이가 남지 않은 것은 `Grep`으로 봤다.
- `uv run python tools/check_adr_pointers.py`: 출력 없이 종료 코드 0.
- `pnpm -C web verify`: 종료 코드 0.
- 갈음한 것: 린트·pyright·pytest·import-linter 등은 파이썬을 건드리지 않았고 커밋이 부르는 pre-commit의 결과로 갈음한다(커밋 뒤 이 일지에 적는다). 관리 화면 e2e와 `visual:admin`은 앞 세션이 초록으로 본 뒤 이 세션이 화면 출력을 바꾸는 코드를 고치지 않았다(시험·독스트링·변이 표·일지·ADR 문장뿐이다)는 코드를 읽은 판단으로 다시 치지 않았다.

### 새로 쓴 사실 문장 (PR 직전 리뷰에 밀 주장)

- 독스트링: "목록은 스킬 문서(`SKILL.md`)를 읽지 않아 문서가 없거나 깨진 스킬도 보통 행이다. 그런 스킬이 꺼져 있으면 화면은 꺼짐을 알리지만 서버는 깨짐을 꺼짐보다 먼저 판정해 읽을 수 없다고 답한다." 근거는 명세 사용자 이야기 16과 "실행 준비의 순서"(깨짐 → 꺼짐), 표준 축 보고가 `core/run.py`를 읽은 것이다. 이 세션은 `run.py`를 직접 열지 않았다.
- ADR 0019 이력: 같은 한계 문장.
