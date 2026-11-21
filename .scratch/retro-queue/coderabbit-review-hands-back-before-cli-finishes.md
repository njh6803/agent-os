# coderabbit-review-hands-back-before-cli-finishes: `coderabbit-review`가 CLI 리뷰를 백그라운드로 띄운 채 리뷰가 끝나기 전에 중간 보고로 턴을 끝내, 본 세션이 출력 파일을 보고 두 번 다시 불러서야 트리아지를 받았다

**상태:** 열림
**어디로:** `.claude/agents/coderabbit-review.md` 3단계(다섯 번째에): CLI는 Bash의 `timeout`을 600000으로 주어 돌리고, 백그라운드로 넘어가면 보고하지 않고 끝 알림을 받은 뒤 트리아지해 한 번만 보고한다
**승인:** 자체 승인 2026-11-17, 1회차, 일지 2026-11-17-1747-postgres-foundation-design.md. ADR 불필요

서브에이전트의 보고는 결과마다 하나만 본 세션에 닿는다. 중간 보고를 먼저 낸 턴 뒤에 다시 불러 받은 트리아지 보고는 거부되어 오지 않았고, 한 번 더 불러서 받았다. 턴 한도에서 보고 없이 멈춘 대기열 0559와 같은 정의의 다른 사건이다.
