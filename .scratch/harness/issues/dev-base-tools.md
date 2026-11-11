# dev-base-tools: `origin/main`을 기준으로 박은 도구를 기준 브랜치 규칙으로 바꾼다

**What to build:** `dev-branch-transition` 티켓의 "기준 브랜치 규칙"(`hotfix/*`는 main, 그 밖은 `origin/dev`가 있으면 dev, 없으면 main)을 나머지 도구에 싣는다. 대상은 `tools/`에서 `origin/main`·`main`을 기준으로 박은 곳이다.

- `tools/sibling_overlap.py`: 형제(병합된 기준 브랜치, 열린 PR의 head, 다른 워크트리)와 merge-base의 기준을 규칙으로 바꾼다. 이 도구가 가장 크고 독스트링이 `origin/main`을 수십 번 든다. 열린 PR의 head를 모을 때 PR의 base도 본다. dev를 기준으로 할 때 main이 앞서 가진 번호(ADR, 헌법 판)는 main에도 있는 것으로 센다(dev→main 사이에 hotfix가 낀 경우)는 점을 시험으로 고정한다.
- `tools/tidy_checkouts.py`: 병합 판정의 `origin/main`(분리 HEAD가 닿는지, 체크아웃되지 않은 브랜치의 끝이 닿는지)을 규칙의 기준으로 바꾼다. `PROTECTED_BRANCHES`에 `dev`를 더한다. 루트가 main에 있다는 전제(주 체크아웃을 `origin/main`으로 당긴다)는 `dev-base-skills-docs`가 스킬에서 정하므로, 이 티켓은 도구가 기준을 둘 다(`origin/main`과 `origin/dev`)로 보는 것이 안전한지부터 정한다. 지우는 길이므로 `.claude/rules/tools.md`의 반박 시험 항목대로 임시 저장소에서 판정을 깨려는 입력으로 반박한다.
- 나머지: `tools/mutate.py`(`origin/main`이 기본 비교 대상), `tools/wait_ci.py`(충돌 안내 문구), `tools/morning_collect.py`·`tools/morning_sources.py`·`tools/morning_report.py`(어느 브랜치의 병합을 세는지), `tools/rerun_*.py`, `tools/hook_prompt_directive.py`(안내 문구의 "병합한 main"), `tools/hook_pr_head_sync.py`(독스트링의 예), `tools/check_constitution_version.py`(부모 판이나 `origin/main`과 견주는 곳), `tools/export_openapi.py`와 `tools/canary.py`·`tools/run_hooks.py`는 `main`이 브랜치 이름이 아닌 곳(`__main__`, 임시 저장소의 브랜치 이름)을 먼저 가려 바꿀 곳만 바꾼다.

- `tools/check_ticket.py`의 `ticket_stem`: `hotfix/*` 브랜치를 티켓 모양으로 알아보지 못한다(`ticket_stem('hotfix/x')`가 None이라 면제 모양 밖의 파일을 바꾸면 판정 7로 막히고, 막는 글은 `feature/NN-<slug>`나 `chore/<slug>`로 바꾸라고 안내한다). ADR 0043 "티켓 검사와 봇"은 hotfix→main이 티켓 PR이라 그대로 지난다고 적는다. `dev-branch-transition`의 셀프 리뷰 명세 축이 찾은 빈칸이다. 핫픽스가 가리킬 티켓 파일의 자리(`.scratch/harness/issues/<slug>.md`인지 기능 티켓인지)와 브랜치 이름 규칙을 이 티켓이 정해 `ticket_stem`·`_blocked` 안내문·시험에 싣는다. 정하기 어려우면 사용자에게 묻는다.

먼저 `tools/`를 `origin/main`·`refs/remotes/origin/main`·`"main"`으로 Grep해 목록을 만들고(`__main__`과 `def main`은 뺀다), 곳마다 기준 브랜치 규칙을 적용할지, 둘 다 볼지, 그대로 둘지를 티켓 끝에 표로 적는다. 크기가 한 세션에 안 들면 이 티켓을 `sibling_overlap`와 `tidy_checkouts`와 나머지 셋으로 나누고 새 티켓 파일을 쓴다.

**대기열:** 없음

**Status:** ready-for-agent

**막는 티켓:** `dev-branch-transition`이 병합된 뒤에 한다. `dev-base-skills-docs`와 파일이 겹치지 않아 나란히 돌 수 있다.

## 수용 기준

- [ ] 티켓 끝에 곳마다의 결정표가 있다(바꾼다, 둘 다 본다, 그대로 둔다와 까닭)
- [ ] `origin/dev`가 없을 때 모든 도구가 지금과 같은 결과를 낸다는 시험이 있다
- [ ] `origin/dev`가 있고 브랜치가 `feature/*`·`chore/*`·`docs/*`일 때는 dev를, `hotfix/*`일 때는 main을 기준으로 한다는 시험이 있다
- [ ] `tidy_checkouts`와 `sibling_overlap`의 변경은 임시 저장소에서 판정을 깨려는 입력으로 반박했고 그 결과를 티켓 끝에 적는다
- [ ] `hotfix/*` 브랜치가 커밋 검사를 티켓 PR로 지나는 규칙이 서고 `ticket_stem`의 시험이 있다
- [ ] 독스트링의 `origin/main` 잔존이 기준 브랜치 규칙을 말하는 곳에는 0이다(기록이나 일지 인용은 제외)
- [ ] 검증 명령이 모두 초록이다
