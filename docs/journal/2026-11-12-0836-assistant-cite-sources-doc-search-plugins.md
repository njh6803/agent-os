# 2026-11-12 (08:36) 기본 에이전트 assistant와 스킬 cite-sources, 연결 doc-search

세션 제목: `feature/03-assistant-cite-sources-doc-search-plugins`. 브랜치 같은 이름, 워크트리 `.claude/worktrees/03-assistant-cite-sources-doc-search-plugins`, 기준 커밋 `10c1d37a3`(#538). 모델 `claude-sonnet-5-5` / high. next-session 지시문으로 연 새 세션이다. 첫 턴에 제목을 바꾸고 `tidy-checkouts`를 돈 뒤 `EnterWorktree`(name `03-assistant-cite-sources-doc-search-plugins`)로 들어가 브랜치를 티켓 stem으로 바꿨다.

## 사용자 프롬프트

> 사용자: 다음 작업: .scratch/base-agent/issues/03-assistant-cite-sources-doc-search-plugins.md. 기본 에이전트 assistant와 스킬 cite-sources, 연결 doc-search, 규칙 파일의 표를 기본 플러그인 루트에 둔다
> 다음 단계: 구현
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 03-assistant-cite-sources-doc-search-plugins)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/base-agent/issues/03-assistant-cite-sources-doc-search-plugins.md
> 브랜치: feature/03-assistant-cite-sources-doc-search-plugins
> 모델: Sonnet 5.5 / high
> 읽을 것: docs/journal/2026-11-11-2035-fake-doc-search-server-fixture.md …
> 이어받을 상태: 없음
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

## 한 것

- **플러그인 셋과 규칙 파일.** `plugins/agents/assistant/{plugin.toml,agent.py}`, `plugins/mcp/doc-search/plugin.toml`, `plugins/skills/cite-sources/{plugin.toml,SKILL.md}`를 두고 `plugins/rules.toml`에 `[agents.assistant]` 표를 더했다. 매니페스트와 프롬프트 상수, 스킬 문서, 규칙 표는 명세의 코드 블록과 바이트까지 같다(파이썬으로 읽어 견주었다. 셀프 리뷰의 명세 축 서브에이전트가 따로 같은 결과를 보고했다). 에이전트 코드는 calc의 꼴에 calc의 일 이름만 뺀 것이다(ADR 0051이 복사를 정했다).
- **꾸러미 시험.** `tests/test_assistant_plugin.py` 16개. 저장소의 `plugins/`를 임시 루트에 복사해 `doc-search`의 주소만 02 픽스처의 것으로 바꾸고, 실제 플러그인·MCP 어댑터와 대본 모델로 `run`/`resume`을 부른다. 서버는 모듈 범위 픽스처로 하나만 띄우고(시험마다 띄우면 한 시험이 7~100초 걸렸다) 시험마다 기록의 몫을 `_Since`로 잘라 읽는다. 티켓 "꾸러미 시험" 여덟 항목을 모두 단언한다. 같은 파일에 매니페스트 글자 시험 둘(에이전트·연결)이 있다. `tests/test_calc_plugin.py`의 규칙 파일 시험은 표 둘로 고쳤다.
- **프로브.** `skill_follow.py`가 저장소의 `plugins/`를 임시 루트에 복사해 `doc-search`의 주소만 바꿔 쓰고, 02의 픽스처 서버(`--expect-authorization`)를 띄우며, CLI에 환경 변수 `DOC_SEARCH_AUTHORIZATION`을 준다. 모드 넷은 `--tool-cap 1`, `--search-down`, `--empty-index`, `--text-max-chars 320`으로 옮겼다. `probes/draft/`와 `probes/fake_doc_search.py`를 지웠다(`git rm`).
- **실제 모델 한 바퀴.** 사례 스물여덟을 한 바퀴 돌았다(`--rounds 1`, 측정 28, 측정 아님 0, 종료 코드 0). 판정이 초안 7과 모두 같았고, 결과는 프로브 README 새 절 "2026-11-12 결과"에 적었다. 스킬의 글자는 고치지 않았다. 기록(`skill_follow.json`)은 스크래치패드에 있고 커밋하지 않았다.
- **문서.** 프로브 README의 표 행, "다시 돌 때", "잰 판", 지운 서버를 가리키던 문장을 새 꼴로 고쳤다. 명세의 지운 경로 일곱 곳을 저장소의 플러그인과 픽스처를 가리키게 고쳤다. 프로브 README 2026-11-11 절의 "인증과 Host 확인이 없고"는 티켓 02의 PR 직전 리뷰가 손으로 본 값(Host 421, Origin 403)에 맞게 고쳤다(프로브 서버는 지운 뒤라 이 판으로는 재지 않았고, 그렇다고 적었다).

## 검증

- `uv run ruff check .`와 `uv run ruff format --check .`: 통과(2107 files).
- `uv run python tools/run_checks.py`: 열 단계 모두 Passed (check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright-linux, pyright, run-hooks, pytest 397초, web-verify 578초). 이 실행은 셀프 리뷰 반영 전의 작업 트리에서 돌았다.
- 셀프 리뷰 반영 뒤: 고친 시험 셋(`test_assistant_plugin.py`, `test_calc_plugin.py`, `test_fake_doc_search.py`)과 `ruff`를 다시 돌렸다. 전체는 커밋의 pre-commit으로 갈음한다.
- `-m llm`·e2e·사진 비교는 돌리지 않았다. 이 변경은 위젯, 질문 페이지, 서버의 최종 사용자 경로를 건드리지 않았다. 실제 모델을 부르는 것은 위 프로브 한 바퀴다.

## 셀프 리뷰 (base `10c1d37a3`, 변경 추적 파일 11개와 미추적 6개, 커밋 0)

표준 축(sonnet·high)과 명세 축 모두 Critical·Major는 없었다.

- **고친 것.**
  - 프로브 README 새 절의 시험이 저장소 쪽을 명세의 글과 대 본다는 문장이 사실이 아니었다(시험은 정해진 문장 한 줄만 대 본다). "손으로 봤다"와 시험의 범위를 적도록 고쳤다.
  - 같은 절 "두 끝에 닿은 실행은 없다"의 범위를 기본 구성 26개로 좁혔다. "잰 판" 칸에 2026-11-12 판(모델, 라이브러리 판, 기준 커밋과 작업 트리)을 더했다.
  - `skill_follow.py` 독스트링의 끝에 닿은 실행이 판정 글에 그대로 드러난다는 문장을 고쳤다. 턴의 끝은 `run_finished`가 없어 측정 아님 사유로, 도구 호출의 끝은 단계별 출력의 `ok=False rule=None` 줄에만 남는다.
  - `_serving`의 `except RuntimeError`가 `yield`를 감싸 회차 본문의 `RuntimeError`가 "가짜 검색 서버가 뜨지 않았다"로 바뀌던 것을 `ExitStack`으로 띄우는 일만 감싸도록 고쳤다. 서버를 띄워 접속하고, 본문의 `RuntimeError`가 그대로 나오는 것을 스크래치 스크립트로 봤다(손으로 봤다).
  - 미래형으로 낡은 문장: 픽스처 두 모듈 독스트링의 "붙을 서버다(03이 … 적었다)"와 명세의 "두 끝 자체는 아직 코드에 없어".
  - `"6" in failed.error`를 실제 문구 `"6턴 안에 멈추지 않았다"`로 좁혔다.
- **남긴 것.**
  - `CountingClock`이 `test_calc_plugin.py`와 같은 클래스로 두 번 있다(Duplicated Code, Minor). calc 시험을 건드리지 않으려 남겼다.
  - 전문 읽기 단언의 `"7일 전까지 복직원을"`은 서버 모듈 상수가 아니라 시험에 적은 글자다(Nit). 표본의 글자에 기댄다는 것은 서버 독스트링이 적는다.
  - `agent.py` 독스트링 "세 자리에 있다"는 매니페스트의 `mcp`·`skills` 칸도 같은 이름을 적는다는 점에서 느슨하다(Nit). ADR 0051과 티켓의 문구를 따랐다.
  - 프로브 README 새 절의 수치는 스크래치패드의 기록에서 나왔고 커밋하지 않았다. 명세 축이 재현하지 못했다고 적었다.

## 남은 일 (이 세션의 요청 범위는 PR과 병합까지)

커밋 `88fc883d9`까지 마쳤다. 티켓은 `done`이고(04~07이 열려 있어 기능 계획의 `**끝:**` 줄은 쓰지 않았다), `plan_table.py`는 `.scratch/plan.md`를 바꾸지 않았으며(출력 없음, `git status`에 변화 없음), pre-commit은 통과했다. 남은 것은 PR 직전 리뷰(`coderabbit-review`), 푸시, PR, 봇 회차, 병합이다. 병합은 `merge.md`의 "워크트리에서 병합할 때"를 따른다. 이 일지의 인용 두 곳(커밋 뒤에 따옴표를 뗐다)은 커밋 `88fc883d9`에 든 판과 다르니 이 일지 수정을 다음 커밋에 싣는다.

## PR 직전 CodeRabbit CLI (인계받은 세션)

`coderabbit-review` 서브에이전트가 `coderabbit review --agent --include-untracked --base origin/main`을 17개 파일 전체에 돌렸다(CLI 0.7.5, `Seat: not assigned`, `Plan: Free`). `review_completed`에 findings 0건, 종료 코드 0이었다. 유효·오탐·보류 모두 0건이라 고칠 것이 없다. 서브에이전트가 읽다가 본 참고 하나는 판정이 아니다. `doc-search`의 `url`이 평문 http라 `Authorization` 헤더가 http로 가는데, 컨테이너 내부 망을 전제한 주소이고 밖으로 열 때는 https여야 한다는 점이다(Minor 이하). 이 변경은 명세의 글자를 그대로 옮긴 것이라 지금 고치지 않았다. 주소의 선택은 rag-engine과 맞추는 일이고 이 티켓의 몫이 아니다.

## 인계

경계 `커밋 뒤`. 세션 제목은 `feature/03-assistant-cite-sources-doc-search-plugins`였다. 컨텍스트가 인계 문턱을 넘어 이 세션은 인계한다. 뒤에 이 세션이 한 일은 없다.

open-session을 부른다 2026-11-11T23:47:32Z
