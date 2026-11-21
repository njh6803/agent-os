# ticket-only-harness-pr-blocked-at-ci: 일지의 "다음"이 "새 harness 티켓을 쓴다"고만 적어, 다음 세션이 티켓만 올리는 PR을 계획하게 된다(그 PR은 CI의 `ticket` 검사가 막는다)

**상태:** 열림
**어디로:** `.claude/skills/next-session/directive.md`(또는 `retro`의 일지 "다음" 쓰는 단계): harness 티켓을 새로 쓰라는 지시는 그 일을 하는 PR에 싣는다고 함께 적는다. 새 지침 문장이라 문턱은 다섯 번째 반복이고 그 전에는 회차를 센다. 검사로 옮기는 길은 CI의 `ticket` 판정(`tools/check_ticket.py` 판정 6 뒤의 done 확인)을 로컬에서 같은 모양으로 알리는 것인데, 로컬은 PR이 어떤 티켓을 가리키는지 알기 전이라 `Status:`를 보지 않는다(그 독스트링의 못 보는 것)
**승인:** 자체 승인 2026-11-22, 2회차, 일지 2026-11-21-1935-e2e-standalone-token-rate-limit.md·2026-11-22-0204-e2e-standalone-proxy-serve-resolve.md. ADR 불필요

1회차(앞 일지): 앞 세션이 티켓만 쓰는 `docs/` 브랜치의 PR #619를 열었고 CI의 `ticket` 검사가 "티켓이 done 이 아니라"며 막았다. PR 본문은 "면제 모양이라 통과했다"고 틀리게 적었고, 사용자가 PR을 닫고 구현과 합치기를 골랐다. 일지의 "다음 (갱신 2)"가 "빨가면 … 새 harness 티켓을 쓴다"고만 적었다.

2회차(이번 일지): 그 지시를 이어받은 세션이 같은 모양(티켓과 일지만 올리는 PR)을 계획했다. 실제로 열기 전에 앞 일지와 `tools/check_ticket.py`의 독스트링을 읽어 막혔고, 원인 가르기와 고침을 티켓과 같은 PR에 싣는 길로 바꿨다. 손상은 없었다.
