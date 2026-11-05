# 2026-11-06 (03) approval-rules 01 계약: 트레이스의 적용 규칙·서버 칸

## 시작

> 사용자: 다음 작업: .scratch/approval-rules/issues/01-contract-trace-applied-rule-and-server-fields.md. 트레이스의 적용 규칙·서버 칸을
> 계약으로 더한다(sdk, openapi.json, 생성 TS 타입) / 다음 단계: 구현 / 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로
> tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고
> EnterWorktree(name은 01-contract-trace-applied-rule-and-server-fields)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 시작
> 프롬프트: /implement .scratch/approval-rules/issues/01-contract-trace-applied-rule-and-server-fields.md / 브랜치:
> feature/01-contract-trace-applied-rule-and-server-fields / 모델: Sonnet 5.5 / high / 읽을 것:
> docs/journal/2026-11-05-11-approval-rules-tickets.md의 "다음" 절 / 이어받을 상태: 없음. 01이 병합돼야 02와 03이 나란히 돌 수 있다.
> 05는 04 바로 뒤에 한다. / 이번 요청 범위: 구현·리뷰·커밋까지

지시문대로 `tidy-checkouts`를 먼저 돌고 `EnterWorktree`로 이 워크트리에 들어와 브랜치를 바꿨다. 정리 보고의 세부(지운 것과 남긴 것)는 이 세션의 컨텍스트가 압축될 때 일지로 옮기지 못해 여기 적지 못한다.

## 한 것

티켓 01의 수용 기준을 모두 구현했다. 근거는 아래 "검증"의 명령 결과다.

- **sdk(`src/agent_os/sdk/events.py`, `__init__.py`).** 닫힌 목록 별칭 `AppliedRule`(`deny`, `requires_approval`, `ask`, `allow`, `default`)과 선택 칸 셋 `ToolCalled.rule`, `RunPaused.rule`, `RunPaused.server`(기본값 없음)을 더했다. `ToolCalled`에는 `server`가 없다(mcp-trust가 정한다). `server`에는 패턴을 걸지 않았다. 독스트링은 한 줄이고 논증은 `#` 주석에 뒀다. 트레이스 헤더의 형식은 3 그대로다.
- **런타임 전용 판정(`src/agent_os/core/run.py`의 `_reject_runtime_only`).** 에이전트가 세 칸 가운데 하나라도 채운 `tool_called`·`run_paused`를 내면 쓰지 않고 `run_failed`(원인 `agent_code`)로 끝낸다. 재생 구간에서도 같다(판정이 `ctx.replay_event` 앞이다). 이 판정을 04가 아니라 01이 맡는 까닭은 티켓 본문 그대로, 01과 04 사이에 에이전트가 채운 칸이 트레이스에 남으면 04 뒤 그 트레이스의 재개가 `agent_code`로 끝나기 때문이다.
- **계약 파일.** `openapi.json`과 `web/packages/api-client/src/generated/openapi.ts`를 도구로 다시 뽑았다.
- **관리 화면.** `EventItem.tsx`의 `FIELD_NAMES`에 `rule: "적용 규칙"`, `server: "서버"`를 더했고, 이벤트 리터럴(`RunDetail.stories.tsx`, `RunPage.test.tsx`, `RunPage.decision.test.tsx`)에 새 칸을 적었다. 사진 정답은 `RunDetail` 스토리 열둘의 마흔여덟 장이 바뀌었다(`organisms-rundetail--{decision-failed, decision-invalid, decision-panel, disabled-plugins, end-user-run, events-only, format-one, no-channel-token, plugins-unknown, stream-cut, stream-frames, unreadable-frame}`의 1280·320 × 라이트·다크). 하나(`decision-panel-1280-light`)를 열어 멈춤 카드 끝에 "적용 규칙 rule"과 "서버 server"가 `null`로 서는 것을 눈으로 봤다.
- **최종 사용자 면.** 투영 코드(`channel/http/items.py`)는 고치지 않았다. 칸을 채운 이벤트도 항목이 두 칸을 싣지 않는 것을 시험으로 고정했다.
- **문서.** `.claude/rules/sdk.md`에 세 칸 항목(값 다섯, 형식 3 그대로, required이고 null 허용, `server`에 패턴 없음, 필드 이름 표 두 줄, 옛 코드가 새 칸의 줄을 거부하는 비대칭)을, `.claude/rules/core.md`의 런타임 전용 항목에 세 칸 예외를 더했다. 고치기 전에 `writing-for-agents`를 불렀다. 옛 표현("런타임만 내는 둘")의 잔존을 살아 있는 문서에서 Grep했고 고친 자리 외에는 없었다(기록 문서는 고치지 않는다).
- **plan.md와 티켓.** 티켓 01의 `Status`를 `done`으로, plan.md의 approval-rules 행을 `in-progress`로 바꿨다(`tests/test_plan_status.py`의 규약).

## 검증

빨강을 먼저 봤다(원칙 II). sdk 시험은 `ImportError: cannot import name 'AppliedRule'`로, 웹은 `tsc`의 타입 오류(`EventItem`의 `FIELD_NAMES`와 리터럴 일곱 곳)로 빨갛다. 근거는 그때 친 명령의 출력이다.

초록은 아래 명령의 출력에서 읽었다.

- `uv run pyright`: 오류 0, 경고 0, 정보 0(출력 로그).
- `uv run python tools/check_type_escapes.py`: 출력 없이 종료. `uv run lint-imports`: 계약 6 지킴 0 깨짐. `uv run ruff check . && uv run ruff format --check .`: 통과.
- `pnpm -C web verify`: 종료 코드 0. 시험 파일 96개, 시험 1606개 통과(vitest 요약).
- 관리 화면 사진 비교 `pnpm -C web visual:admin`: 처음에 24건 실패(열두 스토리 × 폭 둘, 의도한 변화였다). `pnpm -C web visual:admin:update`로 정답을 컨테이너 안에서 다시 만든 뒤 다시 쳐서 통과.
- 관리 화면 e2e `pnpm -C web/apps/admin exec playwright test`: 9개 통과.
- 위젯 e2e와 `-m llm`·`-m llm_widget`은 치지 않았다. 위젯과 api-client의 손으로 쓴 코드가 `ToolCalled`·`RunPaused`·`AppliedRule`을 쓰지 않는 것을 Grep으로 확인했고(생성 파일만 든다), 투영 코드는 바뀌지 않았다.
- 규칙 파일(`sdk.md`, `core.md`)을 바꿨으므로 `tools/sibling_overlap.py`가 알린 카나리아 명세 여섯(`.scratch/end-user-continuation/probes/canary/{core_rule_runtime_only_events, core_rule_shortcuts, core_rule_pre_owner_damage, core_rule_read_cap_thread, sdk_rule_failure_cause, sdk_rule_shortcut_patterns}.toml`)을 새 `claude -p` 세션으로 `tools/canary.py`에 돌렸다(claude 2.1.318, 커밋 `15f11711`의 작업 트리). 여섯 모두 통과 4, 실패 0, "없음" 섞인 통과 0이다. 각 명세의 `# 최신 결과:` 줄을 고쳤다.
- 전체 `tools/run_checks.py`는 따로 치지 않았다. 커밋의 pre-commit이 같은 명령들을 돌고 그 결과로 갈음한다(`CLAUDE.md` 검증 명령 절). 그 결과는 커밋 뒤 아래 "남은 일"에 옮긴다.

## 셀프 리뷰(`/code-review`)

범위는 기준 `15f11711`, 파일 17개(작업 트리 변경, 커밋 0, 미추적 0). 표준 축은 sonnet·high, 명세 축은 본 세션 모델이다.

- **표준 축.** 하드 위반 없음, Critical·Major 없음.
  - 고친 것(Minor 둘, Nit 하나): 시험 둘에 똑같던 네 줄을 `_assert_forged_failure` 도우미로 모았다(`tests/core/test_run.py`). `_reject_runtime_only` 독스트링의 "계약 쪽이 먼저 서 있어야 하는 까닭" 문장은 시점 서술이라 낡기 쉬워 불변식("에이전트가 채운 칸이 트레이스에 남으면 그 트레이스의 재개가 재생 구간에서 `agent_code`로 끝나므로 쓰기 전에 막는다")만 남겼다. 양성 대조 시험 이름을 "세 칸이 빈 … 지금처럼 통과한다"에서 `test_규칙_칸이_빈_tool_called_는_막히지_않고_통과한다`로 바꿨다(`tool_called`의 칸은 하나다).
  - 남긴 Nit: `events.py`의 주석 블록이 `RunPaused`의 칸까지 `ToolCalled` 위에서 설명한다(두 이벤트가 칸의 뜻을 나눠 쓰므로 한 자리에 둔 것이고, 읽는 자리가 달라 찾기 어렵다는 지적은 받는다. 계약 주석을 옮기는 일은 이 티켓의 수용 기준 밖이라 두었다). `test_events.py`의 `kind` 인자에 따른 `raw` 분기와 `test_end_user.py`의 `model_dump()` 일치에 겹치는 부분 문자열 단언도 두었다. 단언이 틀리지 않고 읽기에만 걸린다.
- **명세 축.** Critical·Major 없음, 요청하지 않은 동작 없음. 보고가 낸 것은 사진 정답 재생성 미완(그 뒤에 했다)과 Minor 둘이다.
  - 고친 것: 직렬화 스키마 시험이 `RunPaused.rule`의 `AppliedRule` 참조와 `RunPaused.server`의 `string | null`을 직접 단언하게 했다.
  - 남긴 것: `web/apps/admin/e2e/traces.ts`와 `web/packages/api-client/src/stream.test.ts`의 칸 없는 옛 줄 픽스처는 타입을 달지 않아 새 칸이 없어도 깨지지 않는다. 관리 화면 e2e가 통과해 필드 줄 수 단언에 걸리지 않음을 확인했다(위 e2e 9개). 명세의 제목 "두 칸"과 구현의 세 칸 차이는 명세 쪽 표현이라 고치지 않았다(기록).
- 두 보고 모두 서브에이전트의 것이고, 지적마다 코드와 명세를 대조해 판정했다. 서브에이전트가 낸 사실 문장은 판정에 쓰기 전에 Grep이나 실행으로 대 봤다(`test_run.py`의 10개, `test_events.py`의 37개 시험을 다시 돌려 통과).

## 사용자 결정

없음. 티켓과 명세가 정한 것을 그대로 구현했다.

## 회고

후보 여섯을 냈고 판정은 승인 1, 기각 5, 넘김 0이다. 판정과 그 근거는 모두 에이전트가 정했다. 근거의 종류는 대화 기록과 저장소를 읽은 것, `tools/queue_open_rows.py`의 출력, Grep의 수다.

- **승인: 새 세션 첫 턴 `tidy-checkouts` 보고를 그 턴에 일지로 옮기지 않았다.** 사건은 이 세션이다. 컨텍스트가 압축된 뒤 일지를 쓰려니 보고의 세부가 요약에 없어 "세부를 적지 못했다"고 적어야 했다. `docs/journal/`의 `## 체크아웃 정리` 제목은 33개 일지에 있는데(Grep으로 셌다) 그것을 시키는 지침은 `.claude/` 아래에 없다(Grep에서 `tidy-checkouts/SKILL.md`의 제목 한 줄만 나왔다). 같은 꼴(보고를 받은 턴에 일지로 옮기지 않는다)의 244·536은 리뷰 보고라 같은 행으로 세지 않고 새 행에 둔다. 더하는 것이라 문턱 전이고 대기열 576(1회차)로 갔다. 되돌림은 PR 하나다.
- **기각: 반복문이 든 `sed`를 앱 가드가 거부했다.** 이미 있는 앱 가드가 그 자리에서 막았고 `CLAUDE.md` 환경 함정이 그 모양을 적고 있다. 스크립트 파일로 바꿔 지나갔다.
- **기각: 하위 폴더로 `cd`하는 명령을 훅이 막았다.** 이미 있는 훅이 막았다(대기열 225·252의 처방).
- **기각: 로그를 주 체크아웃 쪽 상대 경로로 보냈다가 바로 지웠다.** 한 번이고, 만든 파일을 바로 지웠다(손상으로 세지 않았다. 지운 뒤 주 체크아웃의 상태를 다시 보지는 않았다). 스크래치패드를 쓰라는 지침이 시스템 프롬프트에 이미 있다.
- **기각: `vitest --project admin`처럼 없는 프로젝트 이름을 줬다.** 한 번이고 오류가 이름을 바로 알려 줬다.
- **기각: plan.md 행을 `sed`로 고칠 때 칸 순서를 잘못 읽어 한 번 헛쳤다.** 사건 없이 떠올린 것에 가깝고 `tests/test_plan_status.py`가 어긋남을 잡는다.

만료할 행은 없었다(`tools/queue_open_rows.py`가 "만료할 행 (없음)"을 냈다).

## 다음

- 지금 단계(구현·리뷰·커밋)가 끝나면 다음은 이 브랜치의 PR을 열고 병합하는 것이다. 01이 병합돼야 02(규칙 파일 읽기)와 03(도구의 서버 이름·같은 이름 검사)이 나란히 돌 수 있다. 05는 04 바로 뒤에 한다.
- 병합 뒤 새 세션에서 02·03을 나란히 연다(`next-session`의 병렬 규칙).

## 남은 일

- 커밋의 pre-commit 결과를 여기에 옮긴다.
