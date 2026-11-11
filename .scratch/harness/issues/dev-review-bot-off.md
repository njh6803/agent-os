# dev-review-bot-off: 리뷰 봇이 dev→main PR을 건너뛰게 한다

**What to build:** ADR 0043 Consequences "티켓 검사와 봇"은 리뷰 봇을 dev→main PR에서 끄고 hotfix PR에서는 돌린다고 정했다. `.github/workflows/claude-code-review.yml`이 머리 브랜치가 `dev`인 PR(base `main`)에서는 돌지 않게 조건을 더한다. 건너뛴 잡이 필수 검사에 걸리지 않는지는 이 워크플로가 필수 검사가 아니라는 사실(`tools/protection.json`의 필수 검사는 `verify` 하나)로 본다.

이 파일을 바꾼 PR은 봇이 건너뛰므로(`docs/constitution/operations.md` 리뷰 파이프라인의 "자기 워크플로 파일이 다른가") 이 티켓은 따로 병합한다. 그래서 그 PR의 보안·버그·성능 몫은 PR 직전 리뷰(CLI나 대체 둘)가 맡고 유지보수성·경계 몫은 셀프 리뷰가 맡는다. 같은 PR에서 다른 워크플로나 도구를 건드리지 않는다.

**대기열:** 없음

**Status:** ready-for-agent

**막는 티켓:** `dev-branch-transition`(기준 브랜치 규칙)이 병합된 뒤에 한다.

## 수용 기준

- [ ] 머리 브랜치가 `dev`인 PR에서 `claude-code-review.yml`의 리뷰 잡이 건너뛰어지고, `hotfix/*`·`feature/*`·`chore/*`·`docs/*` PR에서는 그대로 돈다. 임시 PR이나 워크플로의 조건식을 읽은 근거로 어느 쪽을 확인했는지 티켓 끝에 적는다
- [ ] 주석에 ADR 0043 Consequences "티켓 검사와 봇"을 근거로 적는다
- [ ] 워크플로 감사(zizmor)와 검증 명령이 초록이다
- [ ] PR 본문에 이 PR은 자기 워크플로 파일을 바꿔 봇이 건너뛴다는 것과 대신 돈 리뷰를 적는다
