# dev-branch-create: dev를 main에서 따고 전환을 닫는다

**What to build:** 앞의 네 티켓(`dev-branch-transition`, `dev-review-bot-off`, `dev-base-tools`, `dev-base-skills-docs`)이 병합된 뒤에 `origin/dev`를 `origin/main`의 머리에서 따고, ADR 0043 Consequences "전환"을 닫는다. dev를 따는 일(아래 3)은 PR이 아니라 푸시 하나다. 따는 순간부터 도구가 `origin/dev`를 기준으로 쓴다(`dev-branch-transition`의 규칙). 닫을 때 할 일의 편집(아래)은 dev를 딴 뒤에 하므로, ADR 0043 Consequences "전환"("그 뒤에 연 PR부터 dev로")대로 그 PR은 dev로 간다. 그러면 main의 `.scratch/plan-head.md`는 다음 dev→main 출시 때까지 옛 문장을 든다. release-image 세션은 dev의 사본을 읽으므로 막히지 않지만, 이 시차를 PR 본문에 적는다.

순서는 이렇다.

1. 앞의 네 티켓이 모두 done이고 main에 병합됐는지 본다(`.scratch/harness/issues/`의 `Status:`와 `git log origin/main`).
2. **사람의 몫을 사용자에게 알리고 답을 받는다.** 아래는 GitHub 설정이라 사람이 하거나 사용자가 승인한 뒤에 한다. (가) `main`의 `required_linear_history`(`tools/protection.json`)가 dev→main의 merge 커밋을 막는다. 끌지, 관리자 우회(`enforce_admins: false`)에 기댈지 정한다. (나) `dev`를 보호 브랜치로 둘지와 필수 검사(`verify`), strict 여부. 정하면 `tools/protection.json`에 dev의 설정을 더한다. (다) LLM 호출 테스트를 main PR의 CI에서 돌리려면 API 키 시크릿이 필요하다(ADR 0043 Consequences "CI 분담"). 이 세션은 키를 다루지 않는다.
3. 사용자가 승인한 뒤에 `git push origin origin/main:refs/heads/dev`로 dev를 딴다. 딴 뒤 `origin/dev`가 `origin/main`과 같은 커밋인지 본다.
4. 딴 뒤에 새 브랜치에서 `uv run python tools/sibling_overlap.py`와 `uv run python tools/check_ticket.py`가 dev를 기준으로 도는지 실제로 본다. 티켓 PR 하나를 dev로 열어 CI의 `ticket` 잡이 지나는지도 본다.

**닫을 때 할 일 넷.**

- `.scratch/plan-head.md`에서 release-image가 dev 전환을 기다린다고 적은 문장을 걷고, `.scratch/release-image/plan.md` 본문의 첫 문장과 ADR 0056 Consequences "dev 전환이 먼저다"가 가리키는 세 곳(전체 계획 머리, 기능 계획 본문, 일지 "다음"과 지시문)이 더는 전환을 기다리라고 말하지 않게 맞춘다. 걷은 뒤 `uv run python tools/plan_table.py`를 돌려 결과를 같은 커밋에 싣는다.
- 같은 전환을 문서 검색 서버 저장소(rag-engine)에 하라고 그 저장소의 세션에 줄 지시문을 **사용자에게 낸다**(그 저장소는 건드리지 않는다). 지시문에는 그 저장소가 agent-os의 규약 ADR을 따른다고 적고 다른 점만 적는 **얇은 ADR 한 장**을 두라는 요건을 싣는다. 공통 ADR 저장소와 공통 하네스 저장소는 두지 않고 일하는 방식의 원천은 agent-os이다(일지 2026-11-11-1532 "인계한 세션에서 사용자가 정했다").
- 지시문을 낼 때 대기열 `rag-engine-port-by-hand`(`.scratch/retro-queue/rag-engine-port-by-hand.md`)에 회차를 더한다(지금 0회차). 지시문 하나가 회차 하나다.
- 일지의 "다음"이 이 줄들을 걷는 시점은 지시문을 낸 뒤다. 지시문을 내기 전에는 `.scratch/plan-head.md`의 dev 전환 문단과 release-image 기능 계획 본문의 그 대목(지시문을 낸다는 문장)을 걷지 않는다.

**전환 뒤의 후보.** 두 저장소(`C:\project\agent`, `C:\project\rag-engine`)의 공통 파일을 비교해 벌어진 곳을 알리는 점검 도구가 다음 하네스 일이다(대기열 `rag-engine-harness-drift`, 사용자 승인 2026-11-11). 이 티켓이 하지 않고, 결과를 아침 보고에 싣는 것은 사용자가 확인하지 않았으니 그 티켓을 여는 세션이 사용자에게 묻는다.

**대기열:** rag-engine-port-by-hand, rag-engine-harness-drift

**Status:** ready-for-agent

**막는 티켓:** 앞의 네 티켓이 모두 done이다.

## 수용 기준

- [ ] 사람의 몫 (가)~(다)를 사용자에게 알렸고 답을 티켓 끝에 적었다
- [ ] `origin/dev`가 사용자 승인 뒤에 `origin/main`의 머리에서 섰고 같은 커밋이다
- [ ] dev를 기준으로 `sibling_overlap`·`check_ticket`이 돌고 dev로 연 티켓 PR의 CI가 지났다
- [ ] `.scratch/plan-head.md`에서 release-image가 dev 전환을 기다린다고 적은 문장이 걷혔고 `uv run python tools/plan_table.py` 결과가 같은 커밋에 실렸다
- [ ] 문서 검색 서버 저장소에 줄 지시문을 사용자에게 냈고, 얇은 ADR 한 장 요건이 들었으며, `rag-engine-port-by-hand`에 회차를 더했다
- [ ] 실제 이미지의 compose e2e 잡은 이 티켓이 만들지 않았다(release-image의 첫 티켓이 더한다)
- [ ] 검증 명령이 모두 초록이다
