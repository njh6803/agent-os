# stale-web-design-canaries: 카나리아 명세 셋(`web_design_artifact`, `web_design_colors`, `web_design_props_icon_card`)의 기대 글이 원천 `.claude/rules/web-design.md`에 없어, 그 규칙을 고친 PR마다 `tools/canary.py --preflight`가 셋을 "원천에 카나리아가 없다"로 막는다

**상태:** 열림
**어디로:** 고침: `.scratch/design-artifacts/probes/canary/web_design_artifact.toml`, `.scratch/design-refresh/probes/canary/web_design_colors.toml`, `.scratch/design-refresh/probes/canary/web_design_props_icon_card.toml`의 기대를 지금 원천 글로 고치고 다시 돌린다(대조군은 그 글이 원천에 처음 든 커밋의 부모). 다섯 번째에 검사: 0539의 어디로 줄(`tools/sibling_overlap.py`의 하네스 알림이 바뀐 원천을 드는 명세마다 사전 확인의 원천 칸을 보게 한다)
**승인:** 자체 승인 2026-11-13, 0539의 2회차, 일지 2026-11-13-2149-02-markdown-citations-sources-and-stars.md. ADR 불필요

0539(넷, 2026-10-29)가 2026-11-13에 만료된 뒤 같은 셋을 이 일지가 다시 봤다. 앞 티켓 일지(2026-11-12-1809)도 같은 셋을 이 변경 이전부터 낡은 명세로 적었으나 대기열에 회차를 더하지 않았다. 넷째였던 `tidy_skill_cwd_owner.toml`은 이번 사전 확인의 대상이 아니라 보지 않았다.
