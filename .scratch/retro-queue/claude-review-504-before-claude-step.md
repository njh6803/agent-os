# claude-review-504-before-claude-step: **PR 봇 claude-review가 Claude 단계가 시작되기 전에 `Unexpected HTTP response: 504`(종료 127)로 빨개져 `tools/wait_ci.py`가 "끝: 실패 claude-review"로 끝났고, 리뷰는 돌지 않았다**(PR #499 헤드 8ebfcd6. `tools/gh_run_summary.py`로 보니 한도 문구 "You've hit your weekly limit"는 없었다. 일지 2026-11-09-1229 "PR 봇 회차 1")

**상태:** 열림
**어디로:** `.github/workflows/claude-code-review.yml`: Claude 단계 앞의 호출이 5xx로 끝나면 한 번 다시 시도한다. 또는 `tools/wait_ci.py`가 claude-review의 빨강을 `tools/gh_run_summary.py`의 가름(한도, 인프라 실패, 리뷰 실패)으로 나눠 인프라 실패는 "다시 돌릴 것"으로 알린다. 닫힌 327(한도의 빨강을 실패로 셈)과 같은 자리라 그 처방과 맞춘다
**승인:** 자체 승인 2026-11-09, 1회차, 일지 2026-11-09-1229-mcp-http-design.md. ADR 불필요
