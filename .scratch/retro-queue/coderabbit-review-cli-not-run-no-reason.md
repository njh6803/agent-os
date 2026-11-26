# coderabbit-review-cli-not-run-no-reason: **`coderabbit-review` 서브에이전트가 CLI를 돌리지 않았고 보고에 그 이유를 적지 않았다**(정의 1단계는 CLI나 로그인이 없으면 그 사실을 보고하라고 하고 `Seat: not assigned`만으로는 종료하지 않게 이미 고쳐 두었다. 본 세션이 보고에서 CLI 지적이 없는 것을 보고 따로 `coderabbit review --agent --committed --base origin/dev`를 돌려서야 `Seat: not assigned`에서도 리뷰가 도는 것을 확인했다)

**상태:** 열림
**어디로:** `.claude/agents/coderabbit-review.md`의 보고 끝: 요약 줄에 `CLI: 돌았다`나 `CLI: 못 돌았다(이유)`를 반드시 적게 해, `Seat:` 줄이 비어 있어도 CLI가 돌았는지가 보고에서 갈리게 한다. 본 세션이 그 줄 없는 보고를 받으면 서브에이전트를 다시 부르지 않고 CLI를 직접 돈다는 한 줄도 같은 자리에 적는다. 원인은 가르지 않았다(정의는 이 세션 시작 뒤 바뀌지 않았고, 서브에이전트가 왜 CLI를 건너뛰었는지는 보고에 없었다)
**승인:** 자체 승인 2026-11-26, 0578의 7회차(0578은 6회차로 닫혔다. 닫힌 뒤 이은 행은 없었다), 일지 2026-11-26-1553-admin-login-ticket-03.md. ADR 불필요
