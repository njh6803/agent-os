# grep-glob-slash-pattern: **Grep 도구에 `path` `.scratch`와 glob `*/plan.md`를 주자 아무것도 찾지 못했고, 같은 `path`에 `**/plan.md`를 주자 찾았다**(`CLAUDE.md` 환경 함정의 "패턴에 `/`가 들면 `**/`로 연다."는 Glob 줄에만 있고 Grep 줄에는 없다)

**상태:** 열림
**어디로:** `CLAUDE.md` 환경 함정의 Grep 줄: glob에 `/`가 들면 `**/`로 연다. Grep의 glob에 `/`가 들고 `**/`로 시작하지 않을 때 알리는 계기 훅이 더 높은 층이면 그쪽으로 한다. 새 지침 문장이라 문턱은 다섯 번째 반복이고 그 전에는 회차를 센다
**승인:** 자체 승인 2026-11-07·2026-11-11, 2회차, 일지 2026-11-07-2053-public-demo-plan.md·2026-11-11-1532-release-image-design-round3.md(2회차). ADR 불필요

본 것은 이 세션의 한 사례다. Glob 쪽의 같은 함정은 닫힌 대기열 0211의 chore가 `CLAUDE.md`에 적었다. 그 항목의 사건(시간 초과, 다른 워크트리의 파일)과는 다른 일이라 잇지 않는다. 그 `CLAUDE.md` 줄을 어긴 Glob 쪽의 사례는 `glob-slash-pattern-narrowed-path`가 세고, 그 항목의 계기 훅이 Grep의 `glob`까지 덮으면 이 항목도 함께 닫힌다.
