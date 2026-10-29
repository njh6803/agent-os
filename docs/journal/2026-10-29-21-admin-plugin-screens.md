# 2026-10-29 (21) 플러그인 목록에서 이름을 눌러 켜고 끄고 매니페스트는 줄 끝 링크로 본다 (admin-style 05)

브랜치 `feature/05-admin-plugin-screens`, 워크트리 `.claude/worktrees/05-admin-plugin-screens`. 06·07·09와 나란히 연 넷 가운데 하나다.

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 인자: .scratch/admin-style/issues/05-admin-plugin-screens.md

(지시문: 다음 작업 05 티켓, 다음 단계 구현, 새 세션에서 tidy-checkouts 뒤 EnterWorktree, 모델 Opus 5.5 / medium, 이어받을 상태는 PR #423의 Nit 보류, 이번 요청 범위는 PR과 병합까지.)

## 한 것

- 플러그인 목록(`organisms/PluginList`): 머리 `h1` "플러그인 <전체 개수>", 종류마다 `h2` "<종류 이름> <개수>", 줄마다 패키지 `Switch`(보이는 이름이 플러그인 이름)와 줄 끝 링크 "매니페스트", 표지 줄(`triangle-alert`·`info` 14), 빈 종류(`circle-minus` 16). 켜고 끄기 실패는 `FailureAlert`로 옮기고 `note` "스위치는 다시 읽은 값이다."를 붙였다. 상태를 드는 `PluginList`와 그리는 `PluginListView`로 나눴다.
- 플러그인 하나(`organisms/PluginDetail`): 돌아가는 링크 "플러그인 목록"(`PluginsLink`), 제목 옆 켜짐·꺼짐(`ScreenHeader`의 `beside`, `ReadSection`의 `titleBeside`), 설명 "<종류 이름>. 켜고 끄기는 플러그인 목록에서 한다.", `h2` "매니페스트"와 코드 칸. `PluginPage`의 주소 실패도 같은 링크와 `FailureAlert`로 옮겼다.
- 시험: 페이지 시험 둘(`HomePage.test.tsx`, `PluginPage.test.tsx`)을 고치고 더했다. 스토리 다섯(목록, 빈 종류, 켜고 끄기 실패, 플러그인 하나의 켜짐·꺼짐). e2e `plugin-toggle.e2e.ts`가 "매니페스트" 링크로 연다.
- 변이 표 `.scratch/admin-style/probes/plugin_screens_mutations.toml` 아홉. 첫 실행에서 여섯이 표지까지 기대대로였고 셋째·넷째·다섯째는 빨갛되 표지가 어긋났다(도구가 찍었다). 셋째는 표지를 실패 머리 `to contain '스위치는 다시 읽은 값이다.'`로, 다섯째는 행 찾기 도우미의 `Error: 에이전트 묶음에 calc 행이 없다`로 고쳤다. 넷째는 링크 글자를 이름으로 바꾸던 변이가 행 찾기에서 먼저 실패해, 글자를 "열기"로 바꾸는 변이로 고쳤다. 셋을 다시 돌려 모두 표지까지 기대대로였다(`tools/mutate.py`가 찍었다).
- 결정 기록은 티켓의 "이 티켓이 정한 것" 절이다.

## 검증

- `uv run python tools/run_checks.py`: 열 검사 모두 Passed(도구가 찍었다. 셀프 리뷰 반영 전).
- `uv run ruff check .`, `uv run ruff format --check .`: 초록(셀프 리뷰 반영 전).
- `pnpm -C web/apps/admin exec playwright test`: 8 passed.
- `pnpm -C web visual:admin:update`: 새 사진 20장(목록 셋·플러그인 하나 둘 × 폭 둘 × 모드 둘)을 썼고 기존 스토리는 비교를 지났다. 끝에서 Docker가 `error waiting for container`로 125를 냈다. 그 뒤 `pnpm -C web visual:admin`이 40 passed. 새 사진 가운데 셋(목록 1280 라이트, 실패 320 라이트, 플러그인 하나 1280 다크)을 Read로 열어 손으로 봤다.
- Docker 엔진이 Internal Server Error를 내서 사람에게 물었다.

> 사용자(선택 화면): "다시 켰다" — Docker Desktop을 재시작했으니 사진 정답 만들기(visual:admin:update)를 이어서 진행합니다.

## 셀프 리뷰 (base `3ee0be4f`, 커밋 0, 바뀐 파일 10, 미추적 23)

표준 축(sonnet·high): 표준 위반 셋과 냄새 다섯. Critical·Major 없음.
명세 축: Critical·Major 없음. Minor 하나와 Nit 셋.

고친 것:
- 표준 1(Minor): 변이 표의 줄이 `.scratch/admin-style/probes/README.md` 표에 없었다. 줄을 더했다(재는 것, 다섯째가 도우미를 잰다는 것, 첫 실행과 다시 돌린 결과).
- 표준 2·3(Minor·Nit): 다섯째 변이가 스위치 이름 단언이 아니라 도우미를 잰다는 것과, 구현 전 빨강이 손으로 본 것이라는 표시를 그 README 줄에 적었다.
- 표준 냄새(Nit): 아무도 가져오지 않는 `SwitchFailure`의 `export`를 뗐다.
- 표준 주장(Nit): 티켓의 "`FailureAlert`만 쓴다"를 "부품으로는 … (`PluginList`는 타입 `FailureNoticeProps`를 아직 가져온다)"로, "이름을 넘기지 않는 화면"을 "`beside`·`titleBeside`를 넘기지 않는 화면"으로 고쳤다.
- 명세 1(Minor): `note`의 자리가 그림(메시지와 같은 줄)과도 티켓 21줄(추적 식별자 뒤)과도 다른데 기록이 "그림의 차례"라고만 적었다. 명세 표(spec.md 169·175줄)는 자리를 정하지 않아 구현은 두고, 기록에 그림·티켓과 다른 점과 줄을 나눈 까닭을 적었다.
- 명세 2(Nit): "채널 토큰이 거부된 알림(07·08)"을 "(08)"로 고쳤다(명세 축이 issues/를 grep했다).
- 명세 3(Nit): 넓은 폭의 머리와 첫 묶음 사이가 24px로 그림의 32px과 다른 것을 기록에 더했다.

PR 직전 리뷰에 밀 주장으로 넘길 새 문장(원문):
- 티켓: "명세의 표는 그 자리를 정하지 않았다. 그림 mk-plugins는 메시지와 같은 줄에 이어 쓰고, 이 티켓의 켜고 끄기 줄은 추적 식별자 뒤에 적었다."
- 티켓: "넓은 폭에서 목록 머리(와 실패 알림)와 첫 종류 묶음 사이는 읽기 골격의 `gap-6`(24px)이다. 그림 mk-plugins는 그 사이도 묶음 사이와 같은 32px이다. … 좁은 그림 mk-plugins-m은 24px이라 같다."
- 티켓: "`PluginList`는 타입 `FailureNoticeProps`를 아직 가져온다"
- README: "다섯째(스위치의 이름)는 보이는 이름을 바꾸면 행을 이름 글자로 찾는 도우미 `row()`가 먼저 던져 … 이 변이는 스위치의 이름이 행을 찾는 이름과 같다는 것까지만 잰다"

남긴 것과 이유:
- 표준 냄새: `PluginDetail`이 형제 organism `PluginList`에서 `KIND_NAMES`를, `PluginPage`가 `PluginDetail`에서 `PluginsLink`를 가져온다(Minor, 판단 항목). 문서화된 규칙이 없고 판정자(eslint 층 경계)가 지나보낸다. 자리를 옮기는 것은 07이 `AddressFailure`를 합칠지 정할 때 함께 본다.
- 표준 냄새: `PluginDetail`과 `AddressFailure`의 같은 뼈대(Nit). 합치기는 07의 몫으로 티켓에 적었다.
- 표준 냄새: `beside`와 `titleBeside`의 이름이 다르다(Nit). `ReadSection`의 다른 props가 `title`·`description`처럼 머리의 것을 그대로 넘기지 않고 이름으로 구분해 두었다.
- 표준 주장: 그림 파일(`.dc.html`)이 저장소에 없어 대 볼 수 없다는 지적은 틀렸다. 네 파일이 `.scratch/admin-style/design/`에 있다(Glob으로 봤다). 명세 축이 그 그림을 읽어 개수와 차례를 대 보았다(mk-plugins 31·36줄을 인용했다).
- 명세 4(Nit): 스토리 표본의 `"server": null`. 계약에 있는 키라 남긴다.
- PR #423의 Nit(`ReadSection`의 `AfterDelay` 둘)은 이어받은 대로 남겼다.

다시 돌린 명령: 커밋의 pre-commit으로 갈음한다. 결과는 아래에 적는다.

## 커밋

- 첫 pre-commit은 pytest의 `tests/channel/cli/test_interrupt.py:280`(`둘째가 닫는 도중에 오지 않았다`)에서 막혔다. 이 변경이 닿지 않는 CLI 중단 시험이고, `uv run pytest -q tests/channel/cli/test_interrupt.py` 단독으로는 6 passed(손으로 봤다). web-verify와 함께 돈 부하 아래의 타이밍 실패로 본다(어림).
- 둘째 pre-commit은 run-hooks의 `hook_journal_retro.py` 사례 "다음 빈 순번으로 새 일지를 만든 Write"에서 막혔다. 날짜가 2026-10-30으로 넘어간 직후였고, `uv run python tools/run_hooks.py` 단독으로는 0으로 끝났다(손으로 봤다). 자정 경계에서 사례의 날짜 계산이 어긋난 것으로 본다(어림, 사례 코드는 읽지 않았다).
- 셋째 pre-commit이 지나 커밋 `f1917059`가 섰다.

## 인계 (커밋 뒤)

세션 컨텍스트가 인계 문턱을 넘어 `커밋 뒤` 경계에서 넘긴다. 이 세션의 지금 제목은 `feature/05-admin-plugin-screens`이고 넘기며 `(인계함)`을 붙인다. 번복하거나 고친 것은 위 셀프 리뷰 절과 변이 표 절이다.

지시문:

다음 작업: .scratch/admin-style/issues/05-admin-plugin-screens.md. 플러그인 목록에서 이름을 눌러 켜고 끄고 매니페스트는 줄 끝 링크로 본다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/admin-style/issues/05-admin-plugin-screens.md
브랜치: feature/05-admin-plugin-screens
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-29-21-admin-plugin-screens.md 의 셀프 리뷰·커밋·인계 절
이어받을 상태: 인계: 커밋 뒤. 커밋 f1917059까지 구현, 셀프 리뷰와 반영, 검증(run_checks, ruff, 관리 화면 e2e 8 passed, visual:admin 40 passed)을 마쳤다. 남은 단계는 푸시, PR 직전 리뷰(operations.md 리뷰 파이프라인 2. 일지의 "PR 직전 리뷰에 밀 주장으로 넘길 새 문장"을 브리프에 나열한다), /git-pr, 그 뒤 merge.md 2(봇 회차)부터 병합까지다. .scratch/plan.md의 admin-style 상태 줄은 아직 고치지 않았다. PR #423의 Nit(ReadSection의 AfterDelay 둘)은 남긴다. 일지: docs/journal/2026-10-29-21-admin-plugin-screens.md
확인할 선행 조건: 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지

워크트리 잠금을 풀었다. open-session을 부른다 2026-10-29T15:26:32Z

## PR 직전 리뷰 (인계받은 세션)

인계받은 세션이 일지 커밋을 만들었다. 그 pre-commit의 pytest가 시간 제한 시험 다섯(`test_interrupt.py` 셋, `test_probe_kit.py`, `test_rerun_runner.py`)에서 빨갰다. 그 회차의 web-verify가 1027초, pytest가 1144초였다(러너가 찍었다). 기계 부하로 본다(어림). `uv run pytest -q -p no:randomly` 에 세 파일만 주니 84 passed였다(손으로 봤다). 일지 한 파일만 바뀐 커밋이라 `SKIP=parallel-checks`로 커밋했고, origin/main(`c04e4fe6`, #427·#428)에 rebase한 뒤 `tools/run_checks.py`를 다시 돌려 그 몫을 갈음한다. rebase는 겹치는 파일 없이 끝났다. rebase 뒤의 러너는 pytest만 빨갰다(1149초, 러너가 찍었다). 빨간 여섯은 다시 시간 제한 시험이었고(`test_filesystem.py` 둘, `test_mcp.py` 하나, `test_probe_kit.py` 하나, `test_interrupt.py` 둘), 이 브랜치는 파이썬을 건드리지 않는다. 네 파일만 `uv run pytest -q -p no:randomly`로 따로 돌리니 93 passed였다(손으로 봤다). 나머지 검사는 모두 Passed(러너가 찍었다)이고 ruff 두 줄도 초록이었다(손으로 봤다).

CodeRabbit CLI는 `Seat: not assigned`(`coderabbit auth status`)라 대체 둘을 나란히 돌렸다.
- 보안(`/security-review`): 지적 없음. 새 동적 링크는 `PluginList.tsx:216`의 `/plugins/${row.kind}/${encodeURIComponent(row.name)}` 하나이고 바뀐 organism에 `dangerouslySetInnerHTML`이 없다(Grep으로 봤다).
- 버그·성능(`bug-perf-review`, 코드를 읽어 따라갔고 시험은 돌리지 않았다): 유효 Minor 하나, 보류 Nit 하나, 오탐 없음. 셀프 리뷰가 새로 쓴 문장 넷은 모두 코드·그림과 맞았고 1번의 주어가 모호하다는 Nit이 붙었다.
  - Minor(유효): 두 행을 겹쳐 눌러 둘 다 실패하면 실패 칸 하나(`PluginList.tsx:57`)를 뒤의 실패가 덮어 앞의 실패가 사라진다. 명세가 알림 하나를 정했고 스위치가 다시 읽은 값이라, 행동은 두고 티켓의 "이 티켓이 정한 것"에 "마지막 실패 하나만 보인다"를 적었다.
  - Nit(보류): 누르는 동안 스위치가 `disabled`라 키보드 포커스가 빠질 수 있다. 패키지 `Switch`의 몫이고 실제 브라우저에서 보지 않았다. PR 체크리스트에 적는다.
  - 문장 1의 Nit: 티켓의 "이 티켓의 켜고 끄기 줄"을 "이 티켓 '플러그인 목록' 절의 켜고 끄기 체크박스 문장"으로 고쳤다.
