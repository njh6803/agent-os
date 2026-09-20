## 변경사항

<!-- 무엇을 바꿨는지는 diff가 보여준다. 리뷰어(사람과 봇)가 필요한 것은 "왜"와 "남긴 위험"이다 -->

### 변경 유형

- [ ] `feat` 새 기능
- [ ] `fix` 버그 수정
- [ ] `refactor` 리팩토링 (기능 변경 없음)
- [ ] `test` 테스트만
- [ ] `docs` 문서·지침
- [ ] `chore` 빌드·의존성·설정·하네스
- [ ] `perf` 성능
- [ ] `style` 포맷만

### 왜 이렇게 했나

<!-- 대안이 있었다면 왜 택하지 않았는지. 여러 티켓에 걸쳐 구속력을 갖는 결정이면 docs/adr/ 링크 -->

### 남긴 위험

<!-- 이 PR이 하지 않은 것, 다음 티켓으로 미룬 것, 확신이 없는 판단. 없으면 "없음" -->

## 변경된 영역

<!-- 실제로 바뀐 경로만 체크한다. 괄호는 그 영역을 바꿀 때 같이 확인할 것 -->

- [ ] `src/agent_os/sdk/` — 계약 (디스크 형식이 바뀌면 `schema_version`과 ADR, 플러그인이 보는 표면이 바뀌면 ADR)
- [ ] `src/agent_os/core/` — 포트 다섯 밖의 새 포트가 없는가, 프로바이더 import가 없는가
- [ ] `src/agent_os/channel/`, `admin/` — 서로 import하지 않는가, 조립은 `main`·`server`인가
- [ ] `src/agent_os/adapters/` — 포트를 상속하지 않고 시그니처로 만족하는가
- [ ] `plugins/` — 매니페스트와 디렉터리의 `kind`가 맞는가
- [ ] `tests/` — `src/` 미러링, Fake는 픽스처에서 포트 타입으로 annotate
- [ ] `.claude/`, `tools/`, `.pre-commit-config.yaml` — 하네스 (실제 실행으로 확인했는가, 새 검사는 변이로 빨강을 봤는가)
- [ ] `docs/`, `CLAUDE.md`, `CONTEXT.md`, `CODING_STANDARDS.md` — 지침·헌법·ADR (원천 하나, CLAUDE.md 200줄 이하)
- [ ] `.github/` — 워크플로 (별도 PR로 먼저 병합)

## 체크리스트

<!-- 실제로 실행한 것만 체크한다. 안 돌렸으면 비워 두고 이유를 한 줄 적는다 -->

- [ ] `uv run ruff check . && uv run ruff format --check .`
- [ ] `uv run pyright`
- [ ] `uv run lint-imports`
- [ ] `uv run pytest -q` (LLM 테스트를 건드렸다면 `uv run --env-file .env pytest -m llm`도)
- [ ] 커밋 전 `/code-review`로 셀프 리뷰하고 Critical·Major를 반영했다. 보류한 지적은 별도 티켓으로 뺐다
- [ ] `sdk`·`core`·`adapters`를 건드렸다면 `coderabbit-review` 서브에이전트를 돌렸다(주기당 3회, PR마다 한 번)
- [ ] 결정을 바꿨다면 그것을 참조하는 스킬·훅·rules·명세도 같이 고쳤다
- [ ] 새 환경 변수는 `.env.example`에 있다

## 확인 방법

```bash
uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest -q
```

<!-- 위 외에 확인한 시나리오, 재현 절차, 실행한 명령과 결과 -->

## 관련 티켓

<!-- .scratch/<slug>/issues/NN-<slug>.md 경로. 명세는 .scratch/<slug>/spec.md -->

## 리뷰어 참고

<!-- 특히 봐줬으면 하는 부분, 불확실했던 판단. 기준은 CODING_STANDARDS.md의 심각도와 리뷰 관점 넷.
     봇은 CodeRabbit이 보안·성능, Claude Code Review가 유지보수성·경계. 코멘트 0개인 초록은 리뷰 없음일 수 있다(operations.md) -->
