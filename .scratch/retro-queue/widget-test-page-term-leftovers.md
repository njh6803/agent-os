# widget-test-page-term-leftovers: 용어집이 "위젯 테스트 페이지"로 정한 뒤에도 옛 이름("위젯 미리보기 페이지", "질문 페이지")이 살아 있는 문서에 남아 있다.

**상태:** 열림
**어디로:** `CLAUDE.md`(위젯 미리보기 페이지로 적은 검증 명령 줄), `docs/adr/0050-portal-is-one-node-server-hosting-many-sites-and-signing-anonymous-site-tokens.md`(질문 페이지), `.claude/rules/tests.md`, `README.md`, 그 밖에 `git grep -l "위젯 미리보기 페이지"`가 내는 살아 있는 문서와 코드 주석. 일지와 프로브 기록은 기록이라 고치지 않는다. 계약과 헌법(CLAUDE.md, ADR)에 닿으므로 ADR 초안과 사용자 승인이 따로 필요하다
**승인:** 사용자 승인 2026-11-17, 1회차, 일지 2026-11-16-2249-ci-publishes-release-from-main.md. ADR 불필요(용어집 `CONTEXT.md`가 이미 정한 이름을 따르는 것이고 결정은 바뀌지 않는다. 다만 ADR 0050 본문은 기록이라 이력에 읽는 법을 적는 방식이 맞는지 그 세션이 정한다)

`CONTEXT.md`의 "위젯 테스트 페이지(Portal)"는 Avoid에 "위젯 미리보기 페이지"와 "질문 페이지"를 든다. 그런데 2026-11-17에 `git grep -l "위젯 미리보기 페이지" -- . ':!docs/journal'`가 157개 파일을 냈다. 판 내기 PR(release-image 티켓 11)은 그 PR이 고치는 파일 안에서만 새 이름으로 바꿨다(배포 안내, 명세, `docs/constitution/operations.md`, `docs/constitution/tech.md`, 단독 배포 e2e의 두 파일). CLAUDE.md와 ADR 0050은 사용자가 이번 PR에서 고치지 말라고 해서 두었다.

바꾸는 길은 `.scratch/harness/issues/rename-portal-to-widget-preview.md`가 지난번에 간 길과 같다. 조사가 붙는 자리는 끝 글자가 같아 그대로 맞고, 시험 이름과 화면에 찍히는 글, 그것을 맞대는 시험도 함께 바뀐다. 코드 이름 `portal`, 경로 `/portal/`, 마커 `llm_portal`, CI 잡 `e2e-portal`은 그대로다.
