# 2026-11-07 (10:47) 일지를 날짜·시각·제목으로 짓고 번호를 받지 않는다 (retro-queue-per-item 04)

세션 제목: `feature/04-journal-names-by-time`. 브랜치 `feature/04-journal-names-by-time`, 워크트리 `.claude/worktrees/04-journal-names-by-time`. 모델 Sonnet 5.5 / high. 일부를 서브에이전트에 맡겼고, 아래에서 "서브에이전트 보고"라고 적은 것은 그 보고를 이 세션이 읽은 것이다.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/retro-queue-per-item/issues/04-journal-names-by-time.md

지시문의 다음 작업은 "일지를 날짜·시각·제목으로 짓고 번호를 받지 않게 한다"이고 구현 단계, 어디서는 새 세션(`EnterWorktree`, name `04-journal-names-by-time`), 모델 `Sonnet 5.5 / high`, 03(리뷰 봇 경로 거르기)과 나란히 여는 둘 가운데 하나, 이번 요청 범위는 "PR과 병합까지"였다. 02는 PR 483으로 병합돼 있었고, 이 세션은 `tidy-checkouts`를 돌지 않는다(묶음의 첫 세션 몫).

## 한 일

1. **시험을 먼저.** `tests/test_journal_names.py`를 새 꼴 이름, 전환일 상수, 같은 분 겹침, 옛 꼴 같은 날 순번 겹침, 규약 전 이름으로 다시 썼다. `tests/tools/test_morning_collect.py`에는 아침 보고가 main에 가장 늦게 더해진 일지 가운데 `## 다음`을 든 첫 일지를 고르는 사례를 더했다. 바꾸기 전 도구로 빨간 것을 먼저 봤다.
2. **번호 대조 도구.** `tools/sibling_overlap.py`에서 일지 순번의 읽기·겹침·다음 빈 번호·이름순 뒤처짐·옮길 번호·머리 줄 안내를 걷었다. 없는 일지 인용 검사는 남기고, 인용을 파일 이름의 접두(`<인용>-`)로 풀게 했다(`일지 2026-11-06-14`가 `2026-11-06-1432-…`에 맞지 않는다). 같은 날 옛 꼴과 새 꼴의 차례는 `journal_order`가 정한다. 이 브랜치의 일지는 새 플래그 `--journal`이 찍는다.
3. **훅과 러너.** `tools/hook_journal_retro.py`가 새 일지 Write에서 번호 도구를 자식으로 돌리지 않고 파일 이름이 시각 꼴인지만 본다. `hook_choice_facts`·`hook_prompt_directive`·`run_hooks.py`·`hook_payloads.toml`의 번호 문장과 번호 저장소를 맞췄다.
4. **스킬·지침·문서.** `retro`·`code-review`·`next-session`의 `merge.md`·`handoff.md`, `.claude/rules/tools.md`, `CLAUDE.md`, `docs/constitution/operations.md`의 일지 규칙, `KICKOFF.md`를 새 이름과 "이 브랜치의 일지"로 고쳤다. 헌법 판을 3.0.67에서 3.0.68로 올렸다(형제가 쓴 가장 높은 판이 3.0.67이었다). ADR 0045 이력에 2026-11-07 항목 하나를 더했다.
5. **카나리아.** 고친 파일마다 그 경로를 원천으로 든 명세를 두었다. `next_session_number_body_batch`를 고치고 새 명세 넷(`next_session_handoff_journal_name`, `code_review_journal_name`, `retro_branch_journal`, `tools_rule_journal_name_hook`)을 더했다.
6. **프로브.** `journal_number_hook/run.py`는 지워진 `journal_repository`를 가져오지 않게 하고 B·C 변형을 은퇴시켰다. `journal_cite_scan.py`는 일지를 이름 전체로 든다. 두 프로브 README 행을 고쳤다.
7. **열린 항목.** 439·476·569를 읽었다. 439는 이미 만료(2026-11-07, ADR 0036)였다. 476(자정을 넘기며 훅의 다음 빈 순번 사례가 어긋남)과 569(다음 빈 번호 줄의 일지 번호를 옮겨 적자 종료 1)는 일지 순번을 보는 훅과 번호 줄이 없어져 할 일이 사라졌으므로 이 PR에서 닫는다.

## 측정

- **일지 훅의 시간(등록 제한을 다시 정한 근거).** 명령 `uv run python .scratch/harness/probes/guard_hooks_time.py`(2026-11-07, 이 PC). 이름이 시각 꼴이 아닌 새 일지 Write를 `tools/launch_hook.py` 래퍼를 거쳐 다섯 번 쟀고 263~328ms였다. 서브에이전트가 도는 때라 같은 실행의 다른 훅도 276~354ms였다. 번호 도구를 자식으로 돌리던 옛 판은 한 번에 9~11초였다(대기열 232). 등록 제한은 45초에서 다른 Write·Edit 훅과 같은 20초로 줄였다. `.claude/rules/tools.md`의 그 항목과 `guard_hooks_time.py` 머리 주석에 같은 수를 적었다.
- **실제 저장소에서의 일지 이름 시험.** `uv run pytest tests/test_journal_names.py`가 13개 통과했다. `TRANSITION_DAY`는 이 PR이 마지막으로 origin/main을 합친 날 2026-11-07이다.
- **번호 대조 도구의 시험.** `uv run pytest tests/tools/test_sibling_overlap.py -q`가 통과했다(서브에이전트가 고친 뒤 이 세션이 다시 돌렸다). 서브에이전트 보고에는 일지 순번을 겨눈 시험 일곱을 지웠다는 목록이 있고, 지운 시험마다 같은 위험을 지금 재는 시험(`--journal`, 인용 접두, 이름 순서)이 있다.

- **변이 표.** 표 다섯의 원문을 현재 코드에 맞춘 뒤(`tools/mutate.py --check`, 다섯 표 모두 변이마다 원문이 한 번씩 있음) 첫 커밋의 pre-commit(`mutation tables`)이 새로 고치거나 더한 변이 21개에 `expect_output`이 없다고 막았다. 서브에이전트가 그 21개(journal_names 5, journal_number_and_guards 3, choice_facts_hook 1, sibling_overlap 12)를 `PYTHONUTF8=1 uv run python tools/mutate.py <표> <번호>`로 이 워크트리에서 실제로 돌려 모두 기대대로 빨강이었고(살아남은 변이 0, 엉뚱한 까닭의 빨강 0), 표지는 출력에서 찾았다. 기준선은 모두 초록이었다(journal_names 13, choice_facts_hook 32, journal_number_and_guards 43과 훅 payload 불일치 0건, sibling_overlap 131). 이미 표지가 있던 sibling_overlap 4개(24·25·26·167)는 돌리지 않았다. 약한 표지가 셋 있다. sibling_overlap 22번(시험 이름 경로), journal_names 3번, journal_number_and_guards 4번("어긋남 1건")이고, 앞의 둘은 시험 단언에 메시지가 없어서다. 시험에 메시지를 더하면 단단해지고 이 PR에서는 시험을 건드리지 않았다. 돌린 뒤 소스·시험 파일에 변이가 남지 않았음을 `git diff --stat -- tools tests`가 빈 것으로 확인했다.

## 결정·번복·확인

- **시험 데이터의 없는 일지 인용.** 도구가 이 브랜치가 더한 줄의 `일지 2026-11-06-1432` 같은 글자를 없는 일지 인용으로 읽어 1로 끝났다. 시험 데이터는 저장소에 있는 일지의 앞부분(`2026-11-07-02`)으로 바꾸거나, 일부러 없는 이름이 필요한 사례는 변수로 조립했다. 도구의 안내가 시키는 길이다.
- **이 일지를 만든 Write에 붙은 옛 순번 알림.** 주 체크아웃에는 아직 옛 `hook_journal_retro`가 있어(워크트리 세션의 훅은 `CLAUDE_PROJECT_DIR`의 주 체크아웃 것이 돈다) 새 이름 `2026-11-07-1047-…`에 순번을 대 보지 못했다는 알림이 왔다. 이 PR이 없애는 동작이라 따르지 않았다. 병합 뒤 주 체크아웃을 당기면 사라진다.
- **프로브 `journal_number_hook`의 A 변형.** 고친 뒤 다시 돌리지 않았다. A의 코드는 그대로이고 import와 두 변형만 걷었다. 은퇴한 변형을 부르면 알리고 1로 끝나는 것은 손으로 봤다.

## 셀프 리뷰

범위: 기준 `9a1d8542`(merge-base), 변경 파일 39개 이상, 커밋 0개(전부 작업 트리), 미추적 5개. 표준 축과 명세 축 서브에이전트가 나란히 돌았다. 아래 "서브에이전트 보고"는 그 보고를 이 세션이 읽은 것이다.

**명세 축(서브에이전트 보고) — 판정과 반영**
- **훅 러너가 빨갛다(Major).** `tools/hook_payloads.toml`의 choice_facts 사례가 아직 `다음 빈 번호`를 기대했다. 같은 시각 `run_checks.py`의 pytest도 같은 사례에서 1건 빨갰다(6530 통과, 1 실패). 기대 조각을 `<날짜>-<HHMM>-<슬러그>.md`로 고쳤고 `tools/run_hooks.py`가 175건 어긋남 0건으로 끝났다.
- **낡은 카나리아 명세 셋(Major).** `code_review_overlap_exit_two`·`next_session_overlap_exit_two`는 "도구가 2로 끝나면 `할 일:` 줄을 따른다"를 기대했는데 그 문장이 일지 번호 받기와 함께 사라졌다. 겨눌 것이 없어 둘 다 지웠다(살아 있는 문서의 참조는 없고 일지와 닫힌 대기열 0251의 기록만 남는다). `tools_rule_guard_hooks`는 "45초" 물음을 걷어 둘로 줄이고 다시 돌려 통과 4였다. 모든 명세의 `expect`가 원천에 글자 그대로 있는지 훑은 스크래치 스크립트는 이 변경과 무관한 다섯을 더 냈고(원천이 이 PR 밖이거나 기준 커밋에서도 없던 문구), 손대지 않았다.
- **프로브 README 변이 표 행(Major).** 83·102·134·138행을 현재 표와 맞췄다(변이 수, 지운 순번 몫).
- **헌법 README 3.0.68 문장(Major).** 훅 시간 항목은 헌법 파일이 아니라 `.claude/rules/tools.md`에 있어서, 바뀐 절을 "운영 브랜치와 병합 절의 문구 하나"로 고치고 규칙 파일의 몫을 따로 적었다.
- **ADR 0045 이력(Minor).** 같은 분의 겹침 처리와 실패 문장을 한 항목으로 더했다.
- **남긴 것.** `JOURNAL_CITE`가 5자리 시각 인용(`일지 2026-11-06-14321`)을 읽지 않고 지나간다는 지적은 인용이 4자리 이하로 정해져 있어 두었다. 아침 보고가 `--diff-filter=A`로만 보므로 rename으로 생긴 일지는 가장 늦게 시도된다는 지적은 origin/main에 일지 rename이 0건이라 지금 발현하지 않아 두었다.
- **PR 본문에 적을 것.** 명세 목록 밖에서 바뀐 곳은 `tests/tools/test_hook_prompt_directive.py`이고, `tools/morning_sources.py`가 `tools.sibling_overlap.journal_order`를 새로 import한다. `README.md`·`kickoff/claude-md-template.md`·`sibling_overlap_merge_cost.sh`·`mutate_231/measure.sh`는 낡은 문구가 없어 고치지 않았다(`kickoff/runner.md` 116행의 옛 이름만 고쳤다).

**표준 축(서브에이전트 보고) — 판정과 반영**
- **`--journal`이 일지가 아닌 파일을 고른다(Major).** `branch_journals`가 부모 폴더만 보고 `.md`나 이름 꼴을 보지 않아, 임시 저장소에서 `docs/journal/README.md`가 가장 늦은 일지로 찍혔다. 시험(`…날짜로_시작하는_마크다운만_든다`)을 먼저 더해 README가 걸려 빨간 것을 보고, 이름이 날짜로 시작하는 `.md`만 세는 `JOURNAL_ANY`로 고쳐 통과했다.
- **독스트링의 못 보는 것(Major).** `branch_journals`에 squash 병합 뒤 main을 합친 브랜치에서 종료 1이 되는 것과 `git mv`한 일지가 안 잡히는 것을, `latest_journal`에 `git mv`한 일지와 얕은 클론 경계 커밋과 한 커밋 안의 시각순을 적었다. 얕은 클론은 코드를 읽은 것이고 돌려 보지 않았다고 독스트링에 적었다.
- **`retro` 2·5단계(Major).** 2단계 괄호가 "더한 일지 또는 가장 늦은 미추적 일지"라 실제 동작(둘을 합친 가장 늦은 것)과 달랐고, 5단계에는 `--journal`이 종료 1일 때의 길이 없었다. 둘 다 고쳤다. 본문 문구만 바뀌어 카나리아 `retro_branch_journal`은 사전 확인으로 갈음했다(통과 1).
- **`code-review` 머리 주석의 잔존(Minor).** "그 번호 받기의 2 갈래를 `할 일:` 줄로 줄이기" 구절에 그 문장이 걷혔다고 덧붙였다.
- **대기열 0476·0569의 인용(Nit).** 파일 이름 전체를 쓴 `일지 2026-11-07-1047-….md`를 규약 꼴 `일지 2026-11-07-1047`로 고쳤다.
- **남긴 것.**
  - 일지가 이미 있는지 확인하는 길이 `merge.md` 3·`handoff.md` 2·`code-review` 6단계·두 훅의 문구에 없어, 컨텍스트 압축 뒤에 다른 분으로 일지를 둘째로 만들 수 있다는 지적: 번호를 받던 때의 안내가 사라진 자리이긴 하나 "이 브랜치의 일지"는 늦은 것 하나를 고르므로 해가 작고, 스킬 본문을 또 바꾸면 카나리아가 다섯 더 걸려 이 PR에서는 두었다. 후속 후보로 적는다(`--journal`이 경로를 찍으면 그 파일을 이어 쓴다는 한 줄).
  - 새 꼴 정규식이 `JOURNAL_FILE`·훅의 `STAMPED_NAME`·시험의 `_STAMPED_NAME` 세 곳에 있고, 짓는 명령 문구가 열 곳 안팎에 복제됐다는 지적: 훅은 서로 import하지 않는 것이 결정이고(`.claude/rules/tools.md`) 문구는 훅이 컨텍스트로 내보내야 해서 불가피하다. 시험의 정규식은 두었다.
  - `journal_order`의 마법수와 `morning_sources`의 `sibling_overlap` import: 값이 셋뿐이고 `morning_sources`가 이미 같은 도구에서 꼴을 가져와 두었다.
  - `TRANSITION_DAY`를 옮기라는 지시가 시험 독스트링과 ADR 이력에만 있고 `merge.md`에는 없다는 지적: 티켓이 정한 자리(시험 독스트링)이고, 어긋나면 시험이 느슨해질 뿐 빨개지지 않는다.

## 다음

(PR을 연 뒤 채운다.)
