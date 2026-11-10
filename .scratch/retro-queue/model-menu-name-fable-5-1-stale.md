# model-menu-name-fable-5-1-stale: 결정표와 지시문이 설계 인터뷰·명세 단계의 모델로 적는 `Fable 5.1`이 지금 모델 메뉴에 없어, `open-session`이 새 세션을 열다 모델을 고르는 자리에서 멈춘다

**상태:** 열림
**어디로:** `docs/adr/0029-session-model-is-picked-before-send.md`의 새 이력(결정표의 `Fable 5.1 / xhigh`를 지금 메뉴의 이름으로 바꾸는 사용자 결정)과, 그 값을 적은 `.claude/skills/next-session/SKILL.md`·`directive.md`, `docs/model-selection.md`, 카나리아 명세 넷(`.scratch/harness/probes/canary/`), `tools/rerun_cost.py`, `tools/token_report.py`, `tests/tools/test_rerun_cost.py`. 이름을 무엇으로 바꿀지는 사용자 몫이다(ADR 0029의 2026-10-31 이력이 사용자의 결정으로 적은 값이라 retro가 바꾸지 못한다)
**승인:** 사용자 승인 2026-11-10(선택 화면에서 "병합 뒤 따로 고침"을 골랐다), 1회차, 일지 2026-11-10-1345-doc-qa-agent-design.md. ADR 필요

앞 세션의 `open_session.ps1 -Action send`가 "5초 안에 모델 메뉴의 'Fable 5.1' 을(를) 찾지 못했다."로 끝났고, 그 세션이 원래 쓰던 모델은 `Fable 5.2`였다(일지 293줄). 이름이 적힌 자리는 `Fable 5.1`을 Grep한 결과 42개 파일, 139곳이고 대부분은 일지와 기록이다. 이 항목이 열려 있는 동안 설계 인터뷰나 명세 지시문의 "모델" 줄은 열 때 사람이 지금 메뉴에서 고를 수 있는 이름으로 임시로 적는다.
