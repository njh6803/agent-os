# rag-engine-harness-drift: **agent-os와 문서 검색 서버 저장소(rag-engine)가 같은 이름으로 가진 스킬과 훅이 서로 벌어져도 알리는 것이 없다**(사용자가 공통 저장소를 두지 않고 agent-os를 일하는 방식의 원천으로 두기로 정하며, 두 저장소의 공통 파일을 비교해 벌어진 곳을 알리는 점검 도구를 dev 전환 뒤에 만들기로 했다)

**상태:** 열림
**어디로:** `tools/`의 새 점검 도구(dev 브랜치 전환의 harness 티켓이 닫힌 뒤에 harness 티켓으로 연다. 결과를 아침 보고(`tools/morning_collect.py`)에 싣는 것은 결정을 받은 세션의 제안이고 사용자가 따로 확인하지 않아, 티켓을 여는 세션이 사용자에게 묻는다)
**승인:** 사용자 승인 2026-11-11, 1회차, 일지 2026-11-11-1532-release-image-design-round3.md. ADR 불필요

비교할 두 저장소는 이 PC의 `C:\project\agent`와 `C:\project\rag-engine`이다. 2026-11-11에 이름만 대 봤고 내용은 비교하지 않았다. 스킬(`.claude/skills/*/SKILL.md`)은 agent-os에 18개, rag-engine에 17개이고 이름이 같은 것이 16개다. 훅(`tools/hook_*.py`에서 보고 도구 `hook_report.py`를 뺀 것)은 agent-os에 43개, rag-engine에 24개이고 rag-engine의 24개는 모두 agent-os에 같은 이름으로 있다(두 저장소를 Glob으로 셌다). 무엇을 공통 파일로 볼지와 일부러 다르게 둔 곳을 어떻게 적어 둘지는 티켓이 정한다. 공통 저장소나 플러그인으로 뽑는 때는 `rag-engine-port-by-hand`가 센다.
