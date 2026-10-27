# 002: 화면 디자인 스킬 /ui-design과 디자인 폴더 계기 훅을 들인다

**What to build:** ADR 0033의 2026-10-20 이력 "하네스가 스킬을 부르는 자리를 감사하고, 설명에만 기대던 계기를 하네스로 옮긴다"와 ADR 0025의 2026-10-20 이력 "화면은 Claude Code가 화면 디자인 스킬로 그리고, 웹에서 고친 것은 거꾸로 동기화로 코드에 들인다"가 다음 PR로 넘긴 몫이다(skill-call-sites, 일지 2026-10-20-35). 화면 디자인 절차를 프로젝트 스킬 `/ui-design`으로 짓고, 그 한 단계가 Skill 도구로 `frontend-design`을 부른다. `.scratch/<기능>/design/` 아래를 Write·Edit로 쓰면 세션·에이전트마다 한 번 `/ui-design`을 따르라고 알리는 계기 훅을 더한다. `next-session` 결정표에 "화면 디자인" 줄을 더하고, 그 절차를 든 문서(화면 디자인 절, 런북, 화면 프롬프트, 계정 문장)를 스킬에 맞춘다.

두 이력과 `plan.md` admin-style 행의 2026-10-20·2026-10-21 괄호가 이 PR에 정하라고 넘긴 셋도 정한다. 디자인 시스템을 Design 아티팩트에 붙이는 법(디자인 시스템 아티팩트에 `tokens.json`이 아직 없을 때의 순서 포함), 확정한 화면을 받아 `design/`에 옮기는 법, 목업의 웹 편집을 가를 때 무엇을 대 보는지(판 id는 사람이 고치지 않아도 오른다, ADR 0025의 2026-10-21 이력)다. `/ui-design`이 design-reverse-sync의 `/sync-design-system`보다 먼저 들어오므로, 그리기 전에 그 스킬의 확인을 부르는 단계는 design-reverse-sync의 스킬 티켓이 넣는다(`.scratch/design-reverse-sync/spec.md` Out of Scope).

**대기열:** 없음

**Status:** done

## 수용 기준

- [x] `.claude/skills/ui-design/SKILL.md`가 있고, 단계가 ADR 0033 이력의 일곱(설치 확인, 계정 확인, 참고 디자인 조사, `frontend-design` 부르기, Design 아티팩트를 만들어 그리기, 사람이 고르기, `design/`에 옮기고 README 표와 충돌 목록 채우기)이다. 디자인에서 사람이 판단하는 것은 방향과 확정할 화면이고, 그 밖에는 단계가 막혔을 때만 사람을 부른다
- [x] 스킬이 디자인 시스템을 붙이는 법, 화면을 받아 옮기는 법, 목업의 웹 편집을 가르는 법을 적고, 재지 못한 것은 첫 그리기(admin-style)가 확인한다고 적는다
- [x] 디자인 폴더 계기 훅이 시험, `tools/hook_payloads.toml`의 발동·침묵 입력, `.claude/settings.json` 래퍼 등록과 함께 들어오고, `tools/run_hooks.py`가 어긋남 없이 돈다. 시험을 먼저 써서 빨간 것을 본다
- [x] `next-session` 결정표에 "화면 디자인" 줄이 있고 시작 프롬프트가 `/ui-design <기능>`이다
- [x] `docs/agents/issue-tracker.md` 화면 디자인 절, `KICKOFF.md`(설치 목록, 디자인 절차, 복사 목록), `kickoff/prompting.md`(브라우저 요령과 계정 문단), `.scratch/admin-style/design/screens-prompt.md`의 하는 법, `.design-sync/NOTES.md`의 계정 문장이 스킬과 맞는다
- [x] 충돌 목록 파일이 `.scratch/design-system/design/`에 있고 `refresh-prompt.md`가 그것을 가리킨다
- [x] `.claude/rules/tools.md`의 Write·Edit 훅 목록에 새 훅이 든다
- [x] 옛 절차 표현(Claude Design에서 그린다, 계정 고정)이 살아 있는 문서에 남지 않았는지 grep으로 본다
- [x] 새 세션에서 `/ui-design`이 실리는 것을 본다
- [x] 검증 명령이 모두 초록이다
