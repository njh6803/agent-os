# 2026-11-07 (14:00) 전체 계획을 기능 계획과 티켓에서 도구가 만든다 (retro-queue-per-item 05)

세션 제목: `feature/05-plan-table-generated`. 브랜치 `feature/05-plan-table-generated`, 워크트리 `.claude/worktrees/05-plan-table-generated`. 모델 Sonnet 5.5 / high. 일부를 서브에이전트(`migrate-plans`, `docs-skills`, `docs-constitution`)에 맡겼고, 아래에서 "서브에이전트 보고"라고 적은 것은 그 보고를 이 세션이 읽은 것이다.

## 사용자 프롬프트

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. … 인자: .scratch/retro-queue-per-item/issues/05-plan-table-generated.md

지시문의 다음 작업은 "전체 계획을 기능 계획과 티켓에서 도구가 만들게 한다"이고 구현 단계, 어디서는 새 세션(`tidy-checkouts` 뒤 `EnterWorktree`, name `05-plan-table-generated`), 모델 `Sonnet 5.5 / high`, 읽을 것은 `docs/journal/2026-11-07-1047-journal-names-by-time.md`의 "다음", 이번 요청 범위는 "PR과 병합까지"였다. 03·04는 main에 병합돼 있었고 06은 이 티켓이, 07은 06이 막는다. `tidy-checkouts`는 `05-default-model-required-and-checked` 워크트리를 지우지 못했다(`agent-os.exe`·`python.exe`가 모듈을 쥐고 있었다). 그대로 남겼고 PR 본문에 적는다.

## 한 일

1. **시험을 먼저.** `tests/tools/test_plan_table.py`(25개)를 새로 쓰고 `tests/test_plan_status.py`를 다시 썼다. 도구가 없는 상태에서 `tools.plan_table` import가 실패하는 빨강(ImportError)을 먼저 봤다. 끝 줄 시험은 기존 `test_plan_status.py`의 행 판정을 옮긴 것이다.
2. **도구.** `tools/plan_table.py`. 기능 계획(`.scratch/<slug>/plan.md`, `**슬라이스:**` 줄이 있는 것만)과 티켓의 `Status:`에서 `.scratch/plan.md`를 만든다. 칸은 `| 슬라이스 | 기능 | 내용 | Blocked by | Status |`이고 행은 슬라이스 숫자 순, 그다음 slug 순이다. 상태는 `끝` 줄이 있으면 done, done 티켓이 있으면 in-progress, 아니면 todo다. 티켓 상태는 `tools/check_ticket.status_of`를 공유한다. 프론티어는 done이 아니고 이 저장소의 막는 기능이 모두 done인 기능이고, `rag-engine:<slug>`를 막는 기능은 "다른 저장소를 기다리는 기능"에 따로 적는다. `--check`는 쓰지 않고 다르면 1, 깨진 입력(줄 빠짐, slug 불일치, 없는 막는 기능, 모르는 티켓 상태, 잘못된 끝 날짜, 손 파일 없음)은 경로와 까닭을 찍고 2다.
3. **이행.** 서브에이전트 `migrate-plans`가 표 51행으로 기능 계획 51개와 `.scratch/plan-head.md`를 만들었다. 이 세션이 검증했다: slug 집합, 슬라이스·Blocked by, 상태(옛 표와 0건 차이), 본문 글자 일치. 프론티어 문단의 지금 서술은 옮기지 않았다.
4. **커밋 검사.** `tools/check_ticket.py` 면제에 `.scratch/<slug>/plan.md`(`harness`와 `retro-queue` 밖, 하위 폴더 제외)와 `.scratch/plan-head.md`를 더했다. 독스트링과 `tests/tools/test_check_ticket.py`(면제·면제 밖·CI)를 고쳤고, `check_ticket_mutations.toml`에 변이 4개(8~11번)를 더해 `tools/mutate.py`로 돌렸다. 모두 기대한 빨강이었고 소스에 변이가 남지 않았다.
5. **설계 줄과 설계 인터뷰의 계기.** 네 곳(`CLAUDE.md` 작업 규약 1, `grill-with-docs` 설명, `tools/hook_grill_design_check.py` 알림과 못 보는 것, `next-session` 결정표)을 "명세도 기능 계획의 `**설계:**` 줄도 없으면 설계 인터뷰, 설계 줄이 있고 명세가 없으면 명세" 하나로 맞췄다. `grill-with-docs`의 산출물 단계가 설계 줄을 적고 도구를 돌리게 했다. 훅 시험은 `spec.md`·설계 줄·"기능 계획"을 단언하고 옛 문구 "가 없는 설계 단계"가 없음을 본다.
6. **스킬·지침·문서.** `next-session`, `to-spec`, `to-tickets`, `code-review`, `implement`(마지막 티켓의 끝 줄과 도구), `spec-reviewer`, `web-design.md`, `CLAUDE.md`, `docs/agents/issue-tracker.md`(전체 계획 절, 끝 줄 규칙, 나란히 돈 마지막 티켓 둘), `README.md`, `KICKOFF.md`, `kickoff/claude-md-template.md`, `.scratch/approval-rules/spec.md`, `docs/constitution/operations.md`를 고쳤다. 헌법 판을 3.0.68에서 3.0.69로 올렸다. ADR 0045 이력에 항목을 더했고, ADR 0024·0025·0046의 현재형 문장 셋 뒤에 `(바뀜: ADR 0045)`를 달았다.
7. **카나리아.** 고친 하네스 파일 여덟마다 그 경로를 `source`로 든 명세를 고치거나 더했다. 고침: `spec_reviewer_evidence_kinds`, `web_design_showcase`, `code_review_brief_and_reflect`, `implement_ticket_status`, `next_session_fable_design_spec`, `next_session_ui_design_row`, `to_spec_recount_each_reflection`, `to_tickets_path_rule`, `claude_md_grill_new_feature`. 새로 둠: `grill_with_docs_design_line`(이 스킬을 원천으로 든 명세는 하나도 없었다). 새 `claude -p` 세션에서 모두 돌렸고 전부 통과 4(실험군 3, 대조군 1, "없음" 섞임 0)다. 대조군은 `--control-commit`으로 옛 판을 줬다(`277b4e59`, `528bd257`, `02b21d0`, `c1903e0`, `6bd52b06`, `caaa062b`, `e7ca8193^`). claude 2.1.318, 이 PC, 2026-11-07. 각 명세 머리의 `# 최신 결과:` 줄을 고쳤다.
8. **열린 항목.** 523(`bug-perf-review`가 `plan.md` diff를 읽지 못함)과 532(프론티어 문단과 기능 행의 글자 충돌)를 읽고 둘 다 닫았다(`.scratch/retro-queue/0523.md`, `0532.md`의 상태 줄). 523의 "같은 뿌리의 다음 작업 찾기는 385"는 이 항목의 몫이 아니다.

## 측정

- **전체 검사.** `uv run python tools/run_checks.py`가 모두 통과했다(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest 319초, web-verify 524초). 그 뒤 `tests/test_plan_status.py`의 `datetime.date.today()`를 ruff `call-date-today` 때문에 `datetime.datetime.now(tz=datetime.UTC).astimezone().date()`로 바꾸고, 카나리아 명세 둘(`claude_md_grill_new_feature`, `next_session_ui_design_row`)과 티켓 상태를 고쳤다. 이 뒤의 변경은 커밋의 pre-commit이 다시 돈다. `uv run ruff check .`와 `uv run ruff format --check .`는 통과했다.
- **번호 대조 도구.** `uv run python tools/sibling_overlap.py`가 카나리아 알림 없이 끝났고, 남은 알림은 이 일지가 없던 동안의 `일지 2026-11-07-1400` 인용뿐이었다(이 파일을 만들어 풀린다).

## 결정·번복·확인

- **카나리아 대조군 문제.** 옛 카나리아(`Fable 5.1 / xhigh`, `설계 인터뷰부터 한다`, `/ui-design <slug>`, 보여 주기용 스토리 두 문장)는 이미 main에도 있어 대조군이 가를 수 없다. 그 명세들은 질문과 카나리아를 이번에 바뀐 문장으로 갈았고, `web_design_showcase`·`implement_ticket_status` 등은 옛 카나리아를 두고 대조군을 그 문장이 들어오기 전 판으로 줬다.
- **`to_tickets_path_rule` 첫 판.** 둘째 물음이 카나리아가 든 문장 바로 뒤 문장을 옮기라고 하지 않아 실험군이 통과 1·실패 3이었다. 물음을 고쳐 통과 4다. 명세 머리에 적었다.
- **끝 날짜 어긋남(PR 본문에 적을 것).** 옛 프론티어 문단이 적은 닫힌 날짜와 기능 계획의 `끝`이 다른 것: design-system 옛 2026-10-07, 끝 2026-10-11. mcp-shutdown 옛 2026-10-21, 끝 2026-10-22. design-card-build 옛 2026-10-29, 끝 2026-10-30. design-artifacts·design-reverse-sync는 옛 문단에서 날짜를 같은 꼴로 뽑지 못해 새 세션이 `git log`로 다시 맞댄다. `끝` 날짜는 마지막 티켓 병합 커밋의 날짜이고(티켓이 없는 design-artifacts는 그 행이 done이 된 커밋의 날짜), 옛 문단은 그날 쓴 서술이라 어긋날 수 있다.
- **`CONTEXT.md`의 "기능(전체 계획의 행)".** 고치지 않기로 했다. 표의 행이 기능을 가리키는 것은 여전히 참이고(생성한 표도 행을 든다), 기능 계획은 "기능의 한 줄 요약과 본문을 든 파일"로 다른 용어를 요구하지 않는다. 판단을 PR 본문에 적는다.
- **ADR 0024의 포인터.** 티켓이 든 ADR 0025·0046 밖에 ADR 0024 65번 줄에도 같은 현재형 문장이 있어 `(바뀜: ADR 0045)`를 달았다. ADR 0044 89번 줄은 행 문장이 생성한 표에도 참이라 두었다(애매한 쪽이라 PR 본문에 적는다).
- **서브에이전트 `docs-skills`가 지시를 벗어나** `tools/hook_grill_design_check.py`를 고쳤다. 결과가 티켓의 요구와 같아 두었고, 시험을 이 세션이 조였다.
- **인계.** 이 세션의 컨텍스트가 인계 문턱(20만 토큰)을 넘은 채 `셀프 리뷰 직전`에 와서 `handoff.md`대로 넘긴다. 방금 불린 `code-review`는 이 세션이 밟지 않았다(서브에이전트도 띄우지 않았다). 셀프 리뷰는 새 세션이 한다.

open-session을 부른다 2026-11-07T05:13:30Z

## 셀프 리뷰

인계받은 새 세션이 돌렸다. 범위: base `277b4e59`(origin/main), 추적 파일 변경 39개, 미추적 56개, 커밋 0개. 표준 축(sonnet·high)과 명세 축(본 세션 모델)을 서브에이전트로 나란히 돌렸다. 두 축을 합치거나 순위를 매기지 않고 적는다.

**표준 축.** Major 둘, Minor 다섯, 갈래 둘, smell 넷.
- Major 1. `tools/plan_table.py` 독스트링과 ADR 0045 이력 "`설계` 줄은 도구가 읽지 않고…"가 설계 줄을 `hook_grill_design_check`가 읽는다고 적었다. 그 훅은 파일을 열지 않고 호출마다 같은 문장을 낸다(그 독스트링의 못 보는 것). 훅 파일을 직접 열어 맞다고 확인했다.
- Major 2(확인 필요). 설계 줄이 있는 기능 계획이 0개다. 확인: `mcp-http`와 `doc-qa-agent` 본문이 "설계 인터뷰가 먼저 볼 것"을 아직 앞에 두고 있어 설계를 마친 기능이 아니다. 줄을 적지 않는 것이 맞다.
- Minor 3. 첫 줄 뒤에 빈 줄이 끼면 `**슬라이스:**`가 읽히지 않아 그 기능이 종료 0으로 표에서 빠진다. 명세 축도 같은 지적(c)을 냈다.
- Minor 4. 설계 줄을 읽지 않고 싣지 않는다는 시험이 없다. Minor 5. 종료 코드 서술이 닫힌 목록처럼 읽히는데 코드는 더 많은 자리에서 2를 낸다. 갈래 6·7. 설계 인터뷰가 끊긴 경우와 새 기능의 슬라이스 번호를 고르는 규칙, 나란히 돈 마지막 티켓 둘의 `implement` 안내.
- smell. `Feature.tickets`는 티켓이 아니라 상태 문자열이다. `drift_message`가 `--check`의 비교를 되풀이한다. 상태 리터럴이 흩어져 있다.

**명세 축.** (a) 셋, (b) 둘, (c) 넷.
- (a) 빨강을 먼저 본다 항목이 도구 없는 ImportError 하나뿐이다. 닫힌 상자 셋(origin/main 맞대기, 끝 날짜 어긋남과 523·532을 PR 본문에 적기)이 일지의 "남은 일"에 아직 있다. 끝 날짜 맞대기가 design-artifacts·design-reverse-sync에서 안 됐다.
- (b) `docs-skills`가 지시 밖인 훅을 고쳤다. ADR 0024에 포인터를 달았다. 둘 다 일지가 이미 적었고 티켓 요구와 같다.
- (c) 슬라이스 줄이 없거나 빈 줄 뒤로 밀리면 오류 없이 표에서 빠진다. 끝 날짜가 design-refresh에서 어긋날 수 있다. done 기능의 고침 티켓을 닫는 커밋이 끝 줄을 다시 적게 읽힌다. 훅 알림에 "설계 줄이 있고 명세가 없으면 명세"라는 절반이 없다.

### 고친 것

근거의 종류. 서브에이전트 보고(표준 축·명세 축)는 그 서브에이전트가 읽거나 돌린 결과이고, 이 세션이 직접 확인한 항목은 아래에 "직접"으로 적는다. 시험 결과와 변이 결과는 이 세션이 `uv run pytest`로 돌려 본 것이다. 문서 서술(grill 알림, `CLAUDE.md`, `grill-with-docs`)에서 읽은 것은 코드나 화면으로 돌려 본 것이 아니다.

- 표준 Major 1(직접: `tools/hook_grill_design_check.py` 33~39행과 ADR 0045 116행을 읽었다): `tools/plan_table.py` 독스트링과 ADR 0045 이력의 문장을 "읽는 쪽은 설계 인터뷰를 도는 모델과 스킬이다. 설계 계기 훅(`tools/hook_grill_design_check.py`)은 파일을 열지 않고 호출마다 같은 문장을 낸다"로 고쳤다.
- Minor 3과 명세 (c): 시험 `test_첫_줄_뒤에_빈_줄이_끼어도_필드_줄을_읽어_표에_든다`를 먼저 써 빨강을 봤고(그 기능의 행이 없어 `StopIteration`), `_fields`가 첫 줄 바로 뒤의 빈 줄을 건너뛰게 고쳤다. 전체 계획 `--check`는 그대로 0이다.
- Minor 4: `test_본문에_적은_끝_줄은_읽지_않는다`와 `test_설계_줄은_읽지_않고_표에도_싣지_않는다`를 더했다. 이 둘은 서술을 고정하는 시험이라 처음부터 초록이다.
- Minor 5: 독스트링의 종료 코드를 "깨진 입력은 `PlanError`를 내는 자리 모두다"로 열고 자리를 나열했다. 못 보는 것에 셋을 더했다: 본문에 적은 `**끝:**` 무시, 키 철자 오류가 하네스 기능으로 읽혀 표에서 조용히 빠지는 것, 순환 Blocked by와 달력에 없는 끝 날짜(`2026-13-99`)를 거르지 않는 것. 마지막 둘은 임시 폴더에서 자기 참조, 서로 막기, `2026-13-99`를 돌려 종료 코드가 모두 0인 것을 봤다. `docs/agents/issue-tracker.md` 전체 계획 절의 "도는 때"도 같게 열고 필드 줄 범위와 철자 오류를 적었다.
- 명세 (c) 고침 티켓: `docs/agents/issue-tracker.md`의 끝 줄을 적는 때와 `implement` 스킬에 "끝 줄이 이미 있는 기능(done 기능의 고침 티켓)은 그 줄을 그대로 둔다"를 더했다. `implement_ticket_status` 카나리아의 4번 기대 문장 `**끝:** YYYY-MM-DD(그 커밋의 로컬 날짜)를 적는다`는 그대로 남아 있어 카나리아는 다시 돌리지 않고 사전 확인으로 갈음했다.
- 명세 (a) 빨강: 변이를 손으로 넣어 봤다. A: 티켓이 모두 닫히면 done으로 읽게 하니 `test_티켓이_모두_닫혔어도_끝_줄이_없으면_in_progress다`가 `done`을 받아 빨개졌다. B: 다른 저장소 갈래를 없애 모두 프론티어에 넣으니 `test_다른_저장소를_기다리는_기능은_프론티어에_넣지_않고_따로_적는다`와 `test_순수한_다른_저장소_기능은_막는_이_저장소_기능_없이_따로_적힌다`가 빨개졌다. 두 변이를 되돌린 뒤 시험 41개가 통과했다(소스에 변이가 남지 않았다).
- 명세 (c) 끝 날짜: design-artifacts의 `2026-10-17`은 그 행이 done이 된 c41adadd(#285)의 날짜이고, design-reverse-sync의 `2026-10-28`은 마지막 티켓 11(#413)의 날짜다. design-refresh의 `2026-10-13`은 티켓 05가 #234 시점에 이미 `Status: done (올리기는 병합 뒤 사람이 시작한다)`이었던 날이다(`git show e7ca8193:.scratch/design-refresh/issues/05-claude-design-upload.md`로 손으로 봤다). #239는 같은 티켓 파일을 8줄 고쳤지만(`git show 983bf491 --stat`) 그 내용은 읽지 않았다. 그래서 design-refresh의 끝 날짜는 "티켓이 done이 된 병합의 날짜"라는 한 읽기로 닿았을 뿐 확정이 아니다. design-artifacts와 design-reverse-sync의 날짜 대조는 `git log` 출력을 손으로 본 것이다.

### 남긴 것과 이유

- 표준 갈래 6(설계 인터뷰가 ADR만 쓰고 줄 적기 전에 끊김): ADR 쓰기는 사용자 승인 뒤에 설계 줄을 적는 같은 산출물 단계 안이라 순서가 같다. 이 티켓의 요구가 아니다.
- 새 기능 계획의 슬라이스 번호를 고르는 규칙: 명세에 없다. 후속 후보로 PR 본문에 적는다.
- 표준 갈래 7(`implement`에 나란히 돈 마지막 티켓 둘의 안내가 없다): 티켓은 같은 절(`docs/agents/issue-tracker.md`)에 적으라고만 했고, 실패 문장이 길을 안내한다.
- 명세 (c) 훅 알림의 절반: 알림은 `grill-with-docs`를 부를 때만 나오고 그때는 설계 줄이 없는 기능이라는 뜻이다. 두 갈래를 모두 담은 하나의 조건은 그 훅의 독스트링과 `CLAUDE.md`에 있다. 알림 문장의 "명세도 설계 줄도 없는"은 같은 조건이다.
- smell 넷(이름 `Feature.tickets`, `drift_message` 중복, 리터럴): Nit이라 남긴다.
- 명세 (a)의 닫힌 상자 둘: PR을 열고 병합할 때 하는 일이라 "남은 일"에 둔다(origin/main은 지금 base와 같아 맞댈 것이 없다).

### 다시 돌린 명령

`uv run ruff check .`, `uv run ruff format --check .`, `uv run python tools/plan_table.py --check`, `uv run python tools/check_instructions.py`, `uv run pytest tests/tools/test_plan_table.py tests/test_plan_status.py -q`가 모두 초록(41개 통과)이다. 전체 `tools/run_checks.py`는 커밋의 pre-commit으로 갈음하고 결과는 커밋 뒤에 적는다.

## 회고

후보 6개: 승인 1, 기각 5, 넘김 0. 만료할 항목은 없었다(`uv run python tools/queue_open_rows.py`가 "(없음)"). 같은 일을 다룬 항목은 `--search`로 찾았다.

- **승인 — 못 본다고 적은 주장을 재지 않고, 그 항목을 시험으로 고정하지 않음.** 사건은 `tools/plan_table.py` 독스트링과 ADR 0045 이력이 설계 줄을 `hook_grill_design_check`가 읽는다고 적었는데 그 훅은 파일을 열지 않는 것(표준 축 Major 1)과, "설계 줄은 읽지 않고 싣지 않는다"는 못 보는 것 항목에 시험이 없던 것(Minor 4)이다. 어긴 지침은 `.claude/rules/tools.md`의 "못 본다고 적은 주장도 잰다"와 "새로 적는 항목마다 시험 하나로 고정한다"이고 구현 때 실리는 지침이라 회차로 센다. 닫힌 `0187`을 이은 `0362`(3회차)가 오늘 만료돼, 새 항목 `plan-table-unseen-claim`을 4회차로 이었다. 문턱이 다섯 번째라 지금은 반영하지 않고 대기열 폴더에 두었다.
- **기각 — 서브에이전트 `docs-skills`가 지시 밖 파일을 고침.** 이 일지의 앞 세션 사건이다. 결과가 티켓 요구와 같아 손해가 없었고, 서브에이전트 브리프는 그때그때 쓰이고 훅이 허용 범위를 알지 못해 층을 고를 수 없다. 같은 갈래의 항목은 `--search 서브에이전트.*지시.밖`에 없었다.
- **기각 — 티켓 상자를 PR 시점의 일까지 미리 `[x]`로 닫음.** 명세 축이 짚었으나 일지의 "남은 일"이 그 일을 추적했고 병합 전에 하는 일이라 되돌릴 비용이 없었다. 판정할 검사를 만들 수 없는 모양(의미가 PR 시점 행동)이다.
- **기각 — 카나리아 대조군이 옛 카나리아를 가르지 못함.** 앞 세션이 대조군 통과 수를 보고 질문을 갈았다. `tools/canary.py`가 실험군·대조군 통과 수를 이미 그 자리에서 낸다(`통과 4(실험군 3, 대조군 1)`).
- **기각 — 워크트리 가드가 괄호가 든 정규식과 합친 명령을 거부함.** `CLAUDE.md` 환경 함정과 `retro` 5단계가 이미 적은 길(낱말에 괄호를 쓰지 않고 명령을 하나씩 친다)로 고쳐 쳤다.
- **기각 — Bash에서 윈도 역슬래시 경로를 `uv run python`에 넘겨 파일을 못 찾음.** 슬래시 경로로 고쳐 쳤다. Bash는 POSIX 셸이라는 것은 도구 설명이 이미 적었고, 이 세션 안의 한 번이다.

## 다음

- 커밋 `716e5bb0`(pre-commit 전부 통과, `Skipped` 없음)까지 마쳤고 푸시하지 않았다. 컨텍스트가 인계 문턱을 넘은 채 `커밋 뒤` 경계에 와서 새 세션에 넘긴다. 새 세션은 푸시, PR(`git-pr`), `merge.md` 2의 봇 회차, 병합을 한다. 병합 직전 `git fetch origin` 뒤 origin/main이 움직였으면 합치고 main의 `.scratch/plan.md` 행 집합과 내용 칸을 생성한 표와 다시 맞댄다(지금 origin/main은 base `277b4e59`와 같아 맞댈 것이 없다). 맞댈 일이 생기면 손으로 고친 몫을 기능 계획으로 옮기고 `uv run python tools/plan_table.py`를 다시 돌린다. `mcp-shutdown-spec` 워크트리가 `.scratch/plan.md`를 함께 고치고 있어 그쪽을 나중에 병합하면 글자 충돌이 난다(`tools/sibling_overlap.py` 출력). 이 파일은 도구가 만드는 파일이라 충돌은 도구를 다시 돌려 푼다.
- PR 본문에 적을 것: 끝 날짜 어긋남(design-system 옛 2026-10-07/끝 2026-10-11, mcp-shutdown 옛 2026-10-21/끝 2026-10-22, design-card-build 옛 2026-10-29/끝 2026-10-30. design-artifacts·design-reverse-sync는 `git log`로 대 보니 `끝`과 같았다. design-refresh의 `2026-10-13`은 티켓이 done이 된 #234의 날짜이고 #239의 8줄 고침은 읽지 않았다), `CONTEXT.md`를 고치지 않은 판단, ADR 0024에 `(바뀜: ADR 0045)`를 단 것과 ADR 0044 89번 줄을 둔 것, 닫은 대기열 523·532, `tidy-checkouts`가 지우지 못한 `05-default-model-required-and-checked` 워크트리, 이 세션이 셀프 리뷰로 고친 것(위 "고친 것").
- 후속 후보(셀프 리뷰의 남김): 새 기능 계획의 슬라이스 번호를 고르는 규칙이 명세에 없다. 키 철자가 틀려 슬라이스 줄이 없어진 기능이 오류 없이 하네스 기능으로 읽혀 표에서 빠지는 일은 못 보는 것에만 적었다. `Feature.tickets`는 티켓이 아니라 상태 문자열이라 이름이 어긋난다. `tests/test_plan_status.py`의 `drift_message`가 `--check`의 비교를 되풀이한다.
- 이 PR이 병합되면 `06-round-drive-record`(Blocked by 05)가 풀린다.

open-session을 부른다 2026-11-07T09:17:49Z
