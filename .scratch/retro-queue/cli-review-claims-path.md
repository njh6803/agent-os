# cli-review-claims-path: **CodeRabbit CLI가 도는 PR 직전 리뷰에는 밀 주장 목록을 넘기는 길이 없어, 지시문의 "밀 주장을 넘긴다"를 따르려고 서브에이전트(`bug-perf-review`)를 주장 검증 몫으로 따로 띄워야 했다**(base-agent 명세 PR에서 도구 호출 30번을 더 썼고 Minor 하나를 얻었다. 지시문을 쓰는 자리는 CLI가 도는 PR에도 같은 문장을 적는다)

**상태:** 열림
**어디로:** `.claude/skills/code-review/SKILL.md` 6단계의 1(CLI가 도는 PR의 밀 주장 처리를 한 줄로 정한다. 같은 단계를 만지는 열린 0347과 함께 본다)과 `.claude/skills/next-session/directive.md`·`handoff.md`의 지시문 문장
**승인:** 자체 승인 2026-11-11, 3회차, 일지 2026-11-10-1906-base-agent-spec.md·2026-11-11-1555-base-agent-tickets.md·2026-11-11-1532-release-image-design-round3.md(release-image 설계 PR의 회차: 인계 지시문이 밀 주장을 PR 직전 리뷰의 브리프에 실으라고 적었고 CLI가 돌아, `bug-perf-review`를 주장 검증 몫으로 따로 띄웠다. 도구 호출 33번에 지적 0건이었다). ADR 불필요
