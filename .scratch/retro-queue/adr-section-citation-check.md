# adr-section-citation-check: **문서가 `ADR NNNN 결정 "X"`처럼 ADR의 절 이름과 함께 든 인용이, 실제로는 그 ADR의 다른 절(Consequences, Considered Options)에 있었다**(widget-login-state 화면 PR의 README와 시작 프롬프트에서 셋. `tools/check_quotes.py`는 따옴표 안 글자가 저장소에 있는지만 봐 절이 틀린 인용을 지나보냈다. 셋 가운데 하나는 셀프 리뷰 표준 축의 보고가 먼저 그렇게 적은 것을 반영이 옮겼다)

**상태:** 열림
**어디로:** `tools/check_quotes.py`(또는 그 옆의 새 검사): `ADR <네 자리> <절 이름> "<글>"` 꼴(절 이름은 결정, Considered Options, Consequences, 이력)의 인용이 그 ADR 파일의 그 절 안에 있는지 본다. 같은 실수를 밀 주장 목록으로 잡는 길은 열린 0347이 센다
**승인:** 자체 승인 2026-11-15, 2회차, 일지 2026-11-15-1319-widget-login-state-screens.md·2026-11-15-1312-portal-admin-design.md. ADR 불필요
