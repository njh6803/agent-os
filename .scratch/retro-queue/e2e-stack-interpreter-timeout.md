# e2e-stack-interpreter-timeout: `@agent-os/e2e-stack`의 `interpreter()`가 `spawnSync("uv", …)`를 제한 시간 없이 불러, `uv`가 멈추면 호출한 시험 준비도 함께 멈춘다.

**상태:** 열림
**어디로:** `web/packages/e2e-stack/src/serve.ts`의 `interpreter()`(39~52행을 읽었다. `spawnSync`에 `timeout`을 준다), 그것을 부르는 `web/packages/e2e-standalone/e2e/docker.ts`의 `repositoryName()`과 `stack.ts`와 e2e-stack을 쓰는 다른 준비 코드
**승인:** 사용자 승인 2026-11-17, 1회차, 일지 2026-11-16-2249-ci-publishes-release-from-main.md. ADR 불필요(도구에 제한 시간을 더하는 고침이고 결정은 바뀌지 않는다)

판 내기 PR(release-image 티켓 11)의 봇 둘째 회차에서 CodeRabbit이 Minor로 지적했다. `repositoryName()`은 `interpreter()`를 인자로 평가한 뒤에야 `succeed()`의 60초 제한이 시작된다. `interpreter()`가 `spawnSync`로 `uv`를 제한 시간 없이 부르고 `spawnSync`는 이벤트 루프를 막으므로, `uv`가 응답하지 않으면 같은 프로세스의 타이머도 돌지 않는다. 정상 실행에서는 영향이 없다. 같은 도우미를 `stack.ts`가 시험 준비마다 이미 쓰고 있어, 이 PR이 고치면 영향이 e2e-stack 패키지 밖으로 번져 PR 범위 밖이라고 보고 보류했다. 제한 시간은 `.claude/rules/tools.md`가 기다리는 도구의 외부 명령에 요구하는 것과 같은 뜻이다(그 규칙은 파이썬 `tools/`를 겨눈다).
