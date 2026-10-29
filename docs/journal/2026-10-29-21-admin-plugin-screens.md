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
