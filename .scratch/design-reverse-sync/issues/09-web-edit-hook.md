# 09: 계기 훅 — 화면 코드를 처음 고친 세션에 웹 편집을 확인하라고 한 번 알린다

**What to build:** PostToolUse(Write|Edit) 계기 훅 하나가 `web/packages/ui/` 아래나 `web/apps/<앱>/` 아래 파일을 고친 호출에서, 세션과 에이전트마다 한 번 `additionalContext`로 "디자인 시스템 아티팩트에 웹 편집이 있을 수 있다. 방금 고친 파일은 그대로 두고, 화면을 더 고치기 전에 Skill 도구로 `/sync-design-system`의 확인을 부른다"는 뜻과 그 스킬의 "찾았을 때" 절을 가리키는 포인터를 넣는다. 막지 않는다. 서브에이전트에는 확인을 하지 말고 끝 보고 첫머리에 부모가 확인할 것을 적으라고 알린다. 들이기 세션과 이 기능의 구현 티켓 세션(브랜치 `feature/NN-<slug>`이고 작업 트리에 그 티켓 파일이 있다)에는 알리지 않는다(스토리 16·17·22·25).

근거는 `.scratch/design-reverse-sync/spec.md`의 "계기 훅" 전부와 그 2026-10-22 주석(서브에이전트에 알림이 닿는다는 근거와 어림), "편집 켜기와 사람의 확인"의 2026-10-22 주석(계기 훅과 그 문서는 09, 편집 켜기는 10), Testing Decisions의 "계기 훅"이다. 결정은 ADR 0025의 2026-10-21 이력 (3)이고, 이 훅은 사용자가 설계에서 정한 것이라 더하는 문턱을 거치지 않는다(ADR 0036 21행의 포인터. ADR 0036 본문에서 고칠 것은 없다).

08(첫 올리기) 뒤에 돈다. 등록은 이 티켓의 PR에 든다. 병합된 뒤 10이 편집을 켤 때까지는 쓸모없는 알림이 나므로, 10을 이 병합 바로 뒤에 돈다. 이 티켓은 10을 막는다.

**Blocked by:** 08

**Status:** done

### 판정

- [x] **경로, 표지, 브랜치 차례로 본다.** 침묵한 판정도 표지에 남겨 세션·에이전트마다 한 번만 판정한다. 들이기 브랜치에서 침묵한 세션의 둘째 쓰기는 다시 판정하지 않는다
- [x] **경로는 `tool_input.file_path`에서 `web/packages/ui/` 또는 `web/apps/<앱>/` 아래인지 본다.** `web/tools` 등 다른 `web/` 아래는 침묵한다
- [x] **표지는 선례 `tools/hook_scratch_probe_rule.py`처럼 세션 id와 `agent_id`로 만든다.** 세션을 모르거나 표지를 쓰지 못하면 호출마다 알린다
- [x] **작업 트리는 고친 파일의 경로에서 찾는다.** `CLAUDE_PROJECT_DIR`은 워크트리 세션에서 주 체크아웃을 가리키기 때문이다(`.claude/rules/tools.md`의 디렉터리 항목). 브랜치는 그 작업 트리의 `HEAD`(워크트리면 `.git` 파일이 가리키는 자리의 것)를 읽고 git을 띄우지 않는다
- [x] **브랜치가 `feature/NN-<slug>`이고 그 작업 트리에 `.scratch/design-reverse-sync/issues/NN-<slug>.md`가 있으면 침묵한다.** 티켓 파일이 없는 `feature/` 브랜치는 알린다
- [x] **`agent_id`가 오면 서브에이전트용 알림을 낸다.** "`web/` 아래를 고쳤다. 부모 세션이 이 세션에서 `/sync-design-system` 확인을 했는지 본다"를 끝 보고 첫머리에 적으라는 뜻이다
- [x] **꼴이 어긋난 입력은 예외 없이 침묵한다**
- [x] **알림은 선택지를 풀어 쓰지 않는다.** 스킬의 "찾았을 때"를 가리키기만 한다

### 독스트링과 등록

- [x] **독스트링에 왜, 판정, 한 번, 못 보는 것을 적는다.** 못 보는 것은 명세대로 Bash(`sed -i`, heredoc)로 고친 파일, `web/` 밖에서 화면에 닿는 파일, 침묵한 뒤 브랜치를 바꾼 세션이 고친 파일이고, 항목마다 그 입력을 시험 하나로 고정한다(`.claude/rules/tools.md`의 못 보는 것 항목)
- [x] **따로 등록하는 까닭을 적는다.** Write·Edit에 이미 붙은 PostToolUse 훅에 판정을 얹을 수 있는지 먼저 보고(선례의 "왜 따로 등록하는가"와 대기열 336), 따로 두면 그 까닭을 적는다
- [x] **`.claude/settings.json`의 첫 `Write|Edit` 묶음에 래퍼 모양(`tools/run_hooks.py`의 `REGISTRATION`)으로 등록한다**
- [x] **`/sync-design-system`이 이 훅을 부르는 쪽으로 들게 한다.** 07은 아직 없는 훅을 적지 않아(07 셀프 리뷰), 그 스킬의 설명(`description`의 `확인` 갈래), 머리 주석의 부르는 쪽, 인자 표의 `확인` 줄에 이 훅의 알림을 더한다. ADR 0025의 2026-10-21 이력 "절차의 자리"가 계기 훅의 알림을 받은 세션이 확인을 부른다고 정했다. 스킬을 고치기 전에 Skill 도구로 `writing-for-agents`를 부르고, 고친 스킬은 아래 카나리아에 함께 넣는다
- [x] **`.claude/rules/tools.md`의 훅 시간 항목에서 Write·Edit에 붙는 훅 목록에 이 훅을 더한다.** 시간은 재거나, 재지 않았으면 다른 계기 훅과 같은 약 0.2초로 어림한다고 적는다. 규칙 파일을 고치기 전에 Skill 도구로 `writing-for-agents`를 부른다

### 시험과 검증

- [x] **순수 함수 시험**(`tests/tools/`, 선례 `tests/tools/test_hook_scratch_probe_rule.py`): 패키지 아래 Write(알림), 앱 아래 Edit(알림), `web/tools` 아래(침묵), 같은 세션의 둘째 쓰기(침묵), 서브에이전트(서브에이전트용 알림), 들이기 티켓 브랜치(침묵), 들이기 티켓 브랜치에서 침묵한 뒤의 둘째 쓰기(다시 판정하지 않는다), 워크트리의 `.git` 파일을 따라 읽은 브랜치, 티켓 파일이 없는 `feature/` 브랜치(알림), 꼴이 어긋난 입력(예외 없이 침묵), 못 보는 것의 항목들
- [x] **`tools/hook_payloads.toml`에 발동 하나와 발동하지 말아야 할 실제 입력 하나를 더하고 `tools/run_hooks.py`로 돌린다**
- [x] **판정의 빨강을 `tools/mutate.py`로 본다.** 변이 명세는 `.scratch/design-reverse-sync/probes/`에 둔다(선례 `.scratch/harness/probes/probe_conclusion_hook_mutations.toml`)
- [x] **바꾼 `.claude/rules/tools.md`와 `/sync-design-system`을 카나리아로 새 세션에서 불러 본다**(`tools/canary.py`, 명세는 `.scratch/design-reverse-sync/probes/canary/`. 스킬은 07의 `sync_design_system_skill.toml` 꼴)
- [x] **알림이 실제 세션의 모델에게 닿는지는 10의 사람 확인이 본다.** 서브에이전트의 Write에 알림이 닿는지도 10이 본다(명세 "계기 훅"의 주석)
- [x] 검증 명령이 모두 초록이다
- [x] **기능을 닫지 않는다**
