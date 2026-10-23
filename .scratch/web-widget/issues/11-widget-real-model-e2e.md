# 11: 실제 모델 e2e — `uv run --env-file .env pytest -m llm_widget`이 저장소의 계산 에이전트로 위젯에서 요청 하나를 끝까지 보낸다

**What to build:** 개발자가 `uv run --env-file .env pytest -m llm_widget`을 치면, 마커 `llm_widget`을 단 파이썬 시험 하나가 위젯 e2e의 Playwright 프로젝트 `llm`을 자식 프로세스로 돌린다. 그 프로젝트는 06의 준비(실제 serve·Next·nginx)에 실제 모델 키를 넘겨, 저장소의 계산 에이전트(`plugins/agents/calc`)로 iframe 위젯에서 요청 하나를 보내 출력이 서는 것까지 본다. 키가 없으면 실패하고, 실행 끝에 토큰 합계 줄이 찍힌다. 이 명령은 원칙 I의 판정 명령(`-m llm`)과 따로다. 기본 실행과 `-m llm`은 이 시험을 돌리지 않는다. 프로젝트 `llm`은 감싸는 시험이 준 `AGENT_OS_WIDGET_LLM=1`이 있을 때만 서므로, 06이 정한 로컬 명령과 CI의 `e2e-widget`은 그 프로젝트를 돌리지 않는다.

아래 목록은 한 티켓에 든다. 갈라 들이면 키 없는 CI가 실제 모델을 부르거나, 아무도 돌리지 않는 프로젝트가 생긴다(명세 검토).

근거는 `.scratch/web-widget/spec.md`의 Testing Decisions 6이다. ADR 0024 이력 2026-10-23 "실제 모델을 부르는 위젯 e2e는 LLM 시험 하나가 감싼다"가 앞선 결정이고, 명령을 원칙 I의 판정과 떼는 까닭과 거부한 안 넷이 거기 있다. 측정은 `.scratch/web-widget/probes/pnpm_spawn.py`와 그 README의 2026-10-23 결과다.

**Blocked by:** 06 (nginx 틀과 위젯 e2e)

**Status:** ready-for-agent

### Playwright 프로젝트 `llm`

- [ ] **위젯 e2e에 프로젝트 `llm`을 둔다.** 계산 에이전트로 위젯에서 요청 하나를 보내 출력이 서는 것까지 본다. 모델이 도구를 부를지는 단언하지 않는다
- [ ] **serve의 환경에 부모의 환경을 펼쳐**(06의 준비) `.env`의 키가 serve까지 닿는다. 트레이스 자리는 감싸는 시험이 준 경로다
- [ ] **프로젝트 `llm`은 환경 변수 `AGENT_OS_WIDGET_LLM=1`이 있을 때만 Playwright 설정의 프로젝트 목록에 든다.** 감싸는 시험만 그 변수를 자식의 환경에 준다. 그래서 06이 정한 로컬 명령(프로젝트를 지정하지 않은 `playwright test`)과 CI `e2e-widget`은 플래그 없이 그 프로젝트를 돌리지 않는다. CI에서만 빼면 이 티켓이 병합된 뒤로 07~10의 "위젯 e2e를 로컬에서 친다"가 실제 모델을 부르고, 키가 없는 셸에서는 빨개진다(PR 직전 리뷰)
- [ ] **그 설정은 위젯 앱의 vitest `node` 시험이 본다.** 변수가 없으면 프로젝트 목록에 `llm`이 없고, 있으면 든다. 조건을 빼면 빨개지는 것을 먼저 본다(원칙 II)

### 감싸는 파이썬 시험

- [ ] **마커 `llm_widget`을 `pyproject.toml`에 선언하고 기본 실행의 제외(`addopts`의 `-m`)에도 더한다.** 기본 `uv run pytest -q`와 `-m llm`은 이 시험을 돌리지 않는다
- [ ] **키가 없으면 실패한다.** 지금의 LLM 시험과 같은 규칙이다(그 시험들의 `ANTHROPIC_API_KEY` 단언)
- [ ] **토큰 합계.** `tests/conftest.py`가 `llm`과 함께 `llm_widget` 마커의 시험도 세게 고친다. 그 시험은 `tmp_path`를 serve의 트레이스 자리로 넘긴다. conftest의 독스트링(기본 실행의 제외를 `-m "not llm"`으로 적은 문장들)도 같이 고친다. 그 셈은 pytester 시험이 먼저 빨갛게 본다(선례 `tests/test_conftest.py`의 토큰 합계 시험 둘). `llm_widget` 마커의 시험이 `tmp_path`에 남긴 트레이스가 합계 줄에 들고, 기본 실행에서는 합계 줄이 찍히지 않는다
- [ ] **pnpm은 이름이 아니라 `shutil.which("pnpm")`이 준 경로로 띄운다.** 이 PC의 Windows에서는 `uv run --env-file` 아래의 pytest가 `pnpm`을 이름으로 띄우지 못했다(`FileNotFoundError`). 넘기는 인자는 고정 글자이고 cmd.exe의 메타 문자(`&`, `^`, `%`)가 들지 않는다
- [ ] **기준 다섯.**
  - Playwright의 JSON 리포터로 통과 1, 건너뜀 0을 단언한다. 종료 코드 0만 보면 Playwright 쪽에서 모두 건너뛴 실행이 초록이 된다
  - `tmp_path`의 트레이스에 `llm_called`가 있다. 키가 serve에 닿지 않으면 모델 호출이 없어 빨개진다
  - 화면에 선 출력이 그 트레이스의 `run_finished`의 `output`과 같다
  - `shutil.which("pnpm")`이 없으면 pnpm을 깔라는 문구로 실패한다
  - 제한 시간에 걸리면 Playwright가 띄운 프로세스까지 정리한다. `.cmd`를 거친 자식을 끊어도 손자 node가 남을 수 있다(명세 검토가 출력 파이프 없이 끊은 회차에서 손자가 살아 있었다고 보고했고, 그 명령은 남지 않았다)
- [ ] **각 기준은 되돌리면 빨개지는 것을 먼저 본다**(원칙 II). 예: Playwright 프로젝트를 모두 건너뛰게 하면 첫째가, serve의 환경에서 키를 빼면 둘째가 빨개진다

### 지침

- [ ] **`docs/constitution/operations.md`의 LLM 테스트 절**에 `llm_widget`의 명령, 치는 때(위젯, api-client의 위젯 몫, 서버의 최종 사용자 경로와 항목의 투영을 건드렸을 때), 원칙 I의 판정이 아니라는 것, core만 고친 작업은 이 명령을 치지 않고 위젯까지의 길은 CI의 `e2e-widget`이 모델 없는 에이전트로 본다는 것, 워크트리에서 `.env`를 읽는 경로(`--env-file ../../../.env`)를 적는다
- [ ] **`CLAUDE.md` 검증 명령 절의 둘을 고친다.** 테스트 줄의 첫 괄호에 위젯의 실제 모델 e2e의 명령과 치는 때를 더하고, pre-commit이 갈음하지 않는 것을 든 문장의 `-m llm` 곁에 `-m llm_widget`을 더한다. 하네스 문서이므로 새 세션에서 실려 읽히는 것을 확인한다(`CLAUDE.md` 작업 규약 3)
- [ ] **새 마커가 거짓으로 만드는 닫힌 문장을 고친다.** LLM 시험이 모두 `llm` 마커이고 기본 실행이 그 하나만 뺀다고 닫은 문장과, 사이트 파일과 서명 토큰의 조립을 실제 소켓과 실제 모델로 지나는 자리를 "유일한"으로 닫은 문장이다. 그런 말(`llm` 마커와 백틱 없이 쓴 llm 마커, `-m "not llm"`, `-m llm`, "유일한 자리")로 저장소 전체를 grep해 살아 있는 문서에 잔존이 0인지 본다(`CLAUDE.md` 작업 규약 4). `-m llm`의 일치에는 그 명령을 그대로 안내하는 문장도 들어, 하나씩 읽어 닫은 문장만 고친다. 지금 아는 자리는 `tests/conftest.py`의 독스트링, `tests/test_main.py` 머리 독스트링의 "llm 마커가 붙은 것만 실제 모델을 부른다", `tests/test_conftest.py`의 기본 실행을 `-m "not llm"`으로 적은 독스트링 둘, `tools/llm_tokens.py` 머리 독스트링, `.coderabbit.yaml`의 "llm 마커 없이 기본 실행에 들어가는지", `tools/hook_env_read.py`가 LLM 테스트 명령으로 `-m llm`만 안내하는 문구, `.claude/rules/tests.md`의 "LLM을 실제로 호출하는 테스트는 `llm` 마커를 붙인다", `docs/constitution/operations.md` LLM 테스트 절의 같은 문장과 "기본 `pytest -q`는 이 마커를 제외한다", `.claude/rules/http.md`의 "실제 소켓과 실제 모델로 지나는 유일한 자리다"다
- [ ] `operations.md`는 헌법 문서이므로 `docs/constitution/README.md`의 판을 patch로 올린다(`tools/check_constitution_version.py`가 본다). 바꾼 rules는 새 세션에서 실려 읽히는 것을 확인한다(`CLAUDE.md` 작업 규약 3)

### 검증

- [ ] `CLAUDE.md`의 검증 명령이 모두 초록이다
- [ ] `uv run --env-file .env pytest -m llm_widget`이 초록이고, 일지에 통과 수와 토큰 합계 줄을 적는다. `-m llm`도 돌려 이 시험이 끼지 않은 것을 본다
