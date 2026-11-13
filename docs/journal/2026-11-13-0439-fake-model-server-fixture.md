# 2026-11-13 (04:39) 가짜 모델 서버 픽스처 구현

세션 제목 `feature/04-fake-model-server-fixture`. 브랜치 `feature/04-fake-model-server-fixture`, 워크트리 `.claude/worktrees/04-fake-model-server-fixture`, 기준 커밋 `a4eea81ff`(origin/dev). 모델 Sonnet 5.5 / high. next-session 지시문으로 연 새 세션이다. 첫 턴에 제목을 바꾸고 `EnterWorktree`로 들어와 `git branch -m`으로 브랜치 이름을 티켓 stem에 맞췄다(`EnterWorktree`가 `worktree-04-fake-model-server-fixture`로 만들었다). 파일 이름의 시각은 컨텍스트가 인계 문턱을 넘어 이 일지를 만든 때다.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/local-model/issues/04-fake-model-server-fixture.md
>
> 다음 작업: .scratch/local-model/issues/04-fake-model-server-fixture.md. 어댑터 시험과 CLI 시험이 붙을 가짜 모델 서버 픽스처를 세운다
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 3 중 3. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/local-model/issues/04-fake-model-server-fixture.md
> 브랜치: feature/04-fake-model-server-fixture
> 모델: Sonnet 5.5 / high
> 읽을 것: docs/journal/2026-11-12-2214-local-model-tickets.md의 "다음". 나란히 여는 나머지 티켓은 .scratch/local-model/issues/01-contract-openai-compatible-model-provider.md, .scratch/local-model/issues/02-broken-tool-call-arguments-fail-model-call.md
> 이어받을 상태: 없음. 티켓 04는 막는 티켓이 없고 05가 이 픽스처에 기댄다
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 dev. tidy-checkouts는 묶음의 첫 세션이 돈다. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: 구현·리뷰·커밋까지

## 한 것

- 티켓 `Status:`를 `in-progress`로 바꿨다(첫 편집). 아직 `done`이 아니고 체크박스도 그대로다.
- 시험을 먼저 썼다. `tests/adapters/test_fake_model_server.py`가 모듈이 없어 수집 단계에서 `ModuleNotFoundError`로 빨갰다(원칙 II). 그 뒤 `tests/adapters/fake_model_server.py`를 짓고 17개가 초록이 됐다. 시험은 표준 라이브러리 `http.client`로 민다. `langchain-openai`는 05가 들인다.
- 픽스처 모양. `FakeModelServer(*응답)`을 `with`나 `start()`·`stop()`으로 쓴다. 응답은 `Reply`(상태, 본문 바이트, `content_type`, `headers`, `delay_seconds`)이거나 `Received`를 받아 `Reply`를 짓는 함수다. 도우미는 `Reply.json`·`Reply.text`·`completion`·`tool_call`·`error_reply`다. 정한 응답이 바닥나면 404와 오류 본문으로 답하고 그 요청도 적는다. 받은 요청은 `requests`(메서드·`path`·`target`·헤더·본문), 연결은 `opened_connections`·`closed_connections`·`connections_settled(within)`로 읽는다. HTTP/1.1이고 서버가 연결을 닫지 않는다. `base_url`은 `/v1`까지다.
- 셈의 시점. 요청은 응답 함수를 돌리기 전에 적는다(시험이 그 순서를 단언한다). `closed_connections`는 `finish()`에서 센다. 기다릴 시간을 준 응답의 연결은 클라이언트가 먼저 끊어도 그 시간이 끝난 뒤에야 센다(독스트링에 적었다).
- 변이 표 `.scratch/local-model/probes/fake_model_server_mutations.toml`(변이 다섯)을 커밋 전에 돌려, 다섯 모두 기대한 빨강과 표지를 확인했다(`PYTHONUTF8=1 uv run python tools/mutate.py <표>`). 표지는 단언 메시지에 값을 끼워 넣은 문구라 시험 파일 원문에 없다.
- 새 워크트리 규약대로 `uv sync`와 `pnpm -C web install --frozen-lockfile`을 쳤다.

## 번복하거나 고친 것

- 변이 5번(끌 때 듣는 소켓을 닫지 않는다)의 첫 판은 `httpd.server_close()`만 뺐는데 시험 하나만 돌리면 초록이었다(`tools/mutate.py`의 출력, `기대 빨강, 결과 초록`). 참조가 사라질 때 CPython이 소켓을 닫아 주는 동치 변이였다는 까닭은 어림이다. 소켓이 닫히는 순간은 재지 않았다. 핸들이 서버를 계속 쥐게 하는 변이(`httpd = self._httpd`와 `pass`)로 바꾸자 같은 도구의 출력이 `기대 빨강, 결과 빨강`이었고 표지 `DID NOT RAISE ConnectionRefusedError`가 찍혔다. 표의 변이마다 시험을 `::`로 하나씩 지정한 것은 러너가 첫 실패에서 멈춰 다른 시험이 먼저 잡혔기 때문이다.
- 자식 프로세스 시험의 첫 판은 자식의 `print`가 윈도 기본 인코딩(cp949)으로 한글을 내 비교가 깨졌다. 자식이 `sys.stdout.buffer`로 바이트를 쓰고 시험이 UTF-8로 풀게 고쳤다.
- 로그를 워크트리 바깥(`.claude/worktrees/fm_gate.log`)에 쓴 것을 지우고 스크래치패드로 옮겼다. 저장소에는 남지 않았다.
- ruff가 짚은 `too-many-statements-in-try-clause`는 응답 쓰기를 `_send` 메서드로 뽑아 고쳤다. `serve_forever`의 `poll_interval`을 0.02로 줄여 끄는 시간을 줄였다.

## 검증

- 린트 둘(`uv run ruff check .`, `uv run ruff format --check .`)은 통과했다.
- `uv run python tools/run_checks.py`(백그라운드, 약 19분). `check-ticket`·`lint-imports`·`zizmor`·`check-instructions`·`check-type-escapes`·`pyright`·`pyright-linux`·`run-hooks`·`web-verify`는 통과했다. `pytest`는 7241개 통과, 3개 실패다. 실패한 `tests/channel/cli/test_interrupt.py` 둘(Ctrl+C를 누른 자식이 30초 안에 끝나지 않았다)과 `tests/tools/test_rerun_runner.py` 하나는 이 티켓이 건드리지 않은 시험이고, 이 두 파일만 홀로 돌리면 69개가 모두 통과했다(157초). 러너가 15분 넘게 돌아 다른 세션과 부하를 나눈 시간 단언으로 본다. 이 판단은 부하 아래 시간 단언의 흔들림이라는 어림이고, 부하를 비교해 재지는 않았다.
- `-m llm`은 이 티켓이 닿지 않는다.

## 인계

컨텍스트가 인계 문턱(20만 토큰)을 넘은 채 `셀프 리뷰 직전` 경계에 왔다. 커밋하지 않은 변경이 워크트리에 있다(티켓 파일, 픽스처, 시험, 변이 표). `/code-review` 스킬을 불렀으나 서브에이전트는 아직 띄우지 않았고 리뷰 보고는 없다. 새 세션이 같은 파일을 이어 쓰고 커밋한다. 티켓 `done` 전환, `uv run python tools/plan_table.py`, 티켓의 체크박스는 아직 하지 않았다.

세션 제목을 `feature/04-fake-model-server-fixture (인계함)`으로 바꿨다(바꾸기 전 제목 `feature/04-fake-model-server-fixture`). 이 세션이 띄운 백그라운드 작업은 모두 끝나 멈출 대기가 없었다. `git worktree unlock C:/project/agent/.claude/worktrees/04-fake-model-server-fixture`는 오류 없이 끝났다.

open-session을 부른다 2026-11-12T19:40:08Z

## 이어받은 세션: 셀프 리뷰와 반영 (2026-11-12T19:42Z 시작, 로컬 날짜 2026-11-13)

앞 세션의 인계 지시문으로 열린 새 세션이다. 첫 턴에 제목을 `feature/04-fake-model-server-fixture`로 바꾸고 `tidy-checkouts`를 돈 뒤 이 워크트리에 들어왔다.

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. (인자: .scratch/local-model/issues/04-fake-model-server-fixture.md) … 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 … 셀프 리뷰(/code-review)부터 한다. … 이번 요청 범위: 구현·리뷰·커밋까지

### tidy-checkouts 결과

- 루트(dev)는 이미 `origin/dev`와 같은 커밋 `f6e7cbb12`라 당길 것이 없었다.
- 병합된 워크트리 가운데 지울 후보는 `06-widget-real-model-assistant-case` 하나였다(판정 `끝낸다`). 그 워크트리를 쥔 쉬는 세션 셋(`local_11252c1b…`, `local_5f2fb610…`, `local_f3d8d0a4…`)의 프로세스를 끄는 `end-holders` 명령은 자동 모드 분류기가 거부했다(`Interfere With Workloads`). 우회하지 않고 그 워크트리를 남겼다. 사용자가 그 세션들을 직접 끄거나 허용 규칙을 더하면 다음 정리가 지운다.
- 휴지통에 남은 둘(`04-custom-agent-guide-and-renamed-copy-test`, `local-model-spec`의 `web/node_modules`)은 `node.exe`(pid 34968)와 `esbuild.exe`(pid 52160)가 쥐고 있어 `empty-trash`는 치지 않았다. 그 프로세스가 끝난 뒤의 정리가 비운다.

### 셀프 리뷰

범위: base `a4eea81ff`(`origin/dev`와의 merge-base), 수정 추적 파일 1개(티켓), 미추적 4개(픽스처, 시험, 변이 표, 일지), 커밋 0개. 표준 축은 서브에이전트 `sonnet`·`high`, 명세 축은 이 세션의 모델을 이어받았다. 시험 17개는 두 축 모두 홀로 돌려 통과를 확인했다. Critical·Major는 없었다.

판정(지적마다):

1. 표준 축, 프로브 README에 변이 표 행이 없다(Minor, 하드). `docs/agents/issue-tracker.md` 프로브와 근거 절이 요구한다. 고쳤다. `.scratch/local-model/probes/README.md` 표에 `fake_model_server_mutations.toml` 행을 더했다.
2. 표준 축, 티켓 체크박스·`Status: done`·`plan_table`이 아직 안 됐다(Nit). 고쳤다. 체크박스를 모두 `[x]`로, `Status`를 `done`으로 바꾸고 `uv run python tools/plan_table.py`를 돌려 `.scratch/plan.md`(한 줄)까지 싣는다. 열린 티켓이 01·02·03·05·06으로 남아 있어 기능 계획의 `**끝:**` 줄은 적지 않았다.
3. 표준 축, 시험이 없는 동작(`start()` 두 번 → `RuntimeError("이미 떠 있다")`, 끈 뒤 `port` 읽기 → `RuntimeError`)과 어긋난 시험 이름(Minor·Nit). 고쳤다. 한 시험의 이름을 행동에 맞게 바꾸며 두 동작을 단언하고, `stop()`을 두 번 불러도 실패하지 않는다는 것은 별도 시험으로 뗐다.
4. 표준 축, `assert CHAT_PATH == "/v1/chat/completions"`는 상수를 제 값과 견주는 동어반복(Nit). 지웠다.
5. 두 축 모두, 기한 시험의 `(1, 0)` 단언이 `SLOW_SECONDS=2.0`이라는 짧은 틈에 기댄다(Minor). 고쳤다. 끊은 직후 셈의 단언은 아직 기다릴 시간 안일 때만 하고(`still_waiting`), 셈이 끝난 시각이 기다릴 시간 이후인지를 따로 단언한다. 시계 오차는 0.1초로 덮었다. 이 형태가 변이를 잡는지를 위해 변이를 하나 더했다(아래).
6. 명세 축, 변이 표에 "처리를 마친 연결을 기다릴 시간 안에 센다"를 되돌리는 변이가 없다(약함). 고쳤다. 변이 4를 더했다(응답을 짓자마자 센다). 기대한 빨강과 표지 `끊은 직후 셈 (1, 1)`을 `tools/mutate.py`로 봤다.
7. 명세 축, 변이 표의 "동치 변이" 주석이 일지의 어림과 어긋난다(약함). 고쳤다. 표 주석에 어림이라고 적었다. 소켓이 닫히는 순간은 재지 않았다.
8. 명세 축·표준 축, 시험이 쓰지 않는 곁가지(`enqueue`, `Reply.headers`, `do_PUT`·`do_PATCH`·`do_DELETE`, `origin`)는 티켓의 "체크박스가 요구하는 것만 쓴다"에 걸린다(Minor). 지웠다. `origin`은 `base_url` 안으로 접었다. 05가 `headers`나 다른 메서드가 필요하면 05가 더한다. `completion(finish_reason)`은 도구 호출 응답 시험이 쓰므로 남겼다.
9. 표준 축, `Handler.setup`·`finish`가 `owner._lock`·`owner._opened`·`owner._closed`를 직접 만진다(Feature Envy 가능). 고쳤다. `FakeModelServer._connection_opened`·`_connection_closed`로 옮겨 `finish`의 `finally`는 한 줄 호출만 남았다. 변이 3의 대상 문구를 `self._closed += 1`로 따라 고쳤다.
10. 표준 축, "함수는 서버 스레드에서 돈다"는 독스트링 서술을 시험이 단언하지 않는다. 고쳤다. `test_응답_함수는_요청을_받은_뒤_그_자리에서_돈다`가 응답 함수가 시험 스레드가 아닌 스레드에서 돈다는 것도 단언한다.

남긴 것(이유 한 줄씩):

- 80줄짜리 중첩 `Handler`(표준 축, 추상화 수준·Middle Man 계열). 서버 객체를 닫는 클로저가 필요하고 `self.server`를 `cast` 없이 좁힐 수 없어(원칙 III) 남긴다. 판단 호출이다.
- `handle`의 `except OSError: pass`가 핸들러 안의 다른 `OSError`도 삼킨다(표준 축). 클라이언트가 끊을 때만 나는 길이고 독스트링에 적었다. 다른 `OSError`가 나는 길은 이 픽스처에 없다.
- 시험 파일에서 `HTTPConnection(...)`과 `close()`가 열두 번쯤 되풀이된다(표준 축, Nit). 연결을 닫는 시점이 셈 단언의 일부라 컨텍스트 매니저로 묶으면 시점이 흐려진다.
- `connections_settled`는 받은 연결이 0이면 기한까지 기다린 뒤 False를 낸다(명세 축). 독스트링에 적혀 있다. 05가 "연결이 한 번도 안 맺혔다"를 보려면 `opened_connections == 0`을 쓰면 된다. 05의 티켓 메모로 옮길 만한 말이지만 05의 수용 기준을 바꾸지는 않는다.
- 응답 함수가 예외를 내면 어떻게 되는지는 독스트링과 시험이 침묵한다(표준 축). 픽스처를 잘못 쓴 경우이고 05가 그 경로를 쓰지 않는다.

PR 직전 리뷰에 밀 주장(이번 반영으로 새로 쓴 사실 문장):

- 변이 표 주석: `server_close()`만 뺀 첫 판은 시험이 초록이었다(`tools/mutate.py` 출력, `기대 빨강, 결과 초록`). 참조가 사라질 때 CPython이 소켓을 닫아 주어서라고 본다(어림, 소켓이 닫히는 순간은 재지 않았다).
- 프로브 README 새 행: "변이 여섯으로 본다". 여섯 변이 모두 기대대로 빨개졌다(`PYTHONUTF8=1 uv run python tools/mutate.py .scratch/local-model/probes/fake_model_server_mutations.toml`의 마지막 줄 `변이 6 모두 기대대로`, 같은 도구의 `--check`가 `변이 6 모두 원문이 한 번씩 있다`).

### 다시 돌린 것

- 시험 한 파일만: `uv run pytest tests/adapters/test_fake_model_server.py -q` → 18개 통과(5.90초). 시험이 하나 늘었다(`stop()` 두 번을 뗐다).
- 린트 둘: `uv run ruff check .`(`All checks passed!`), `uv run ruff format --check .`(2160개 이미 서식 맞음).
- 변이: 위와 같다.
- 나머지는 커밋의 pre-commit 결과로 갈음하려 했으나 커밋이 두 번 막혔다(아래). 커밋은 아직 만들어지지 않았다.

### pre-commit 결과 (커밋 시도 두 번, 둘 다 막힘)

두 시도 모두 `check-ticket`, `lint-imports`, `zizmor`, `check-instructions`, `check-type-escapes`, `pyright`, `pyright-linux`, `run-hooks`, `web-verify`, 변이 표 원문 검사(`mutation tables`), 마크다운 표·줄 구분 문자·인용 검사는 통과했다(훅 출력). `pytest`만 실패했다.

- 첫 시도(1200.8초): 7243개 중 2개 실패. `tests/tools/test_probe_kit.py::test_배출은_줄이_계속_와도_제한_시간에_끝난다`(0.5초 배출에서 읽은 줄이 0개), `tests/tools/test_rerun_runner.py::test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다`(`board.run()`이 0이 아닌 1).
- 둘째 시도(972.5초): 7242개 통과, 3개 실패. `tests/channel/cli/test_interrupt.py`의 둘(`Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다`)과 위 `test_rerun_runner.py`의 같은 시험 하나.
- 이 세션이 `tests/tools/test_probe_kit.py`와 `tests/tools/test_rerun_runner.py`만 홀로 돌리니 78개가 모두 통과했다(308초, 손으로 쳤다). `test_interrupt.py`는 이 세션이 홀로 돌려 보지 않았다. 앞 세션이 `test_interrupt.py`와 `test_rerun_runner.py` 둘만 홀로 돌려 69개 통과를 봤다(앞 절의 일지).
- 이 변경은 `tools/`와 `channel/cli/`를 건드리지 않았다(`git diff` 범위는 `tests/adapters/`, `.scratch/`, `docs/journal/`). 실패 시험이 매번 조금씩 다르고(첫 시도 둘, 둘째 시도 셋, 앞 세션 셋) 홀로 돌리면 통과하는 것으로 보아 다른 세션과 함께 도는 부하에서 시간 단언이 흔들린 것으로 본다. 이 판단은 어림이다. 기준 브랜치(`origin/dev`)에서 같은 부하로 같은 시험이 빨개지는지는 재 보지 않았다.
