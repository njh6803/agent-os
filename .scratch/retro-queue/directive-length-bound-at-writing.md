# directive-length-bound-at-writing: 지시문을 쓰는 자리(`directive.md`·`handoff.md`)가 딥링크 상한(URL 8000자)을 모른 채 "이어받을 상태"를 길게 적어, `open-session`이 쏘기 전에 거부하고 지시문을 줄여 다시 열었다

**상태:** 열림
**어디로:** `.claude/skills/next-session/directive.md` 3(본문)이나 `handoff.md`의 "이어받을 상태" 항목에 상한과 줄이는 길(세부는 일지의 절로 옮기고 지시문은 그 절을 가리킨다)을 한 줄(5회차에). 상한은 `tools/open_session.ps1`의 `$maxUrl`이 원천이고 `.claude/skills/open-session/SKILL.md` 44줄은 거부 뒤의 처방만 적는다
**승인:** 자체 승인 2026-11-10, 1회차, 일지 2026-11-09-2258-pilot-portal-spec.md. ADR 불필요

인계 지시문의 첫 판은 URL 8299자로 상한을 넘어 스크립트가 `fired=` 전에 멈췄고(그 일지 "인계 (새 세션, 2026-11-10)"), "이어받을 상태"의 세부를 일지의 "남은 단계" 절로 옮겨 줄인 둘째 판으로 열었다. 거부는 스크립트가 했으니 손상은 없고 열기 한 번이 더 들었다.
