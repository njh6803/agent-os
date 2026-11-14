# 09: 실제 모델 시험: 위젯 미리보기 페이지에서 고지를 확인하고 calc에 질문하면 답이 서고 익명 주체의 트레이스가 남는다

**What to build:** 기여자가 `uv run --env-file .env pytest -m llm_portal`을 치면, 위젯 미리보기 페이지 e2e가 실제 모델로 돈다. 위젯 미리보기 페이지를 `?site=` 없이 열어 첫 사이트(익명, 에이전트 `calc`)에서 고지를 확인하고 요청 하나를 보내면 위젯에 출력이 서고, 트레이스에 `llm_called`가 남으며 그 실행의 주체가 `anon-` 접두를 단다(스토리 1, 12). 기능 계획의 수락 첫째("calc 예시에 질문할 수 있고")에서 07이 픽스처 에이전트로 세운 흐름의 "calc 예시" 몫을 이 시험이 맡는다. 기본 `pytest`와 CI는 이 시험을 돌리지 않는다. 위젯 미리보기 페이지나 서버의 최종 사용자 경로를 건드렸을 때 손으로 친다.

09는 07 뒤이고 08과 나란히 돈다. 07의 확인 흐름만 있으면 서고, 08의 사이트 바꾸기와는 사례가 겹치지 않는다. 08과 둘 다 위젯 미리보기 페이지 e2e의 준비를 고칠 수 있으니, 나중에 병합하는 쪽이 main을 받아 그 파일을 맞춘다. 명세 묶음 E의 마커이고, 묶음 E의 문서 가운데 마커의 것을 이 티켓이 고친다(명세 "고칠 자리의 묶음"의 주석).

근거는 `.scratch/pilot-portal/spec.md`의 "실제 모델 e2e 하나"와 그 2026-11-10 명세 검토 주석, "고칠 자리의 묶음"의 E 줄과 그 주석이다. 선례는 위젯의 `tests/test_widget_llm.py`와 위젯 e2e의 `e2e/calc.llm.ts`, 그 준비의 LLM 모드(02가 `@agent-os/e2e-stack`으로 옮긴다)다. 앞선 결정은 ADR 0050의 결정 "테스트"다.

**Blocked by:** 07 (처음 온 최종 사용자가 고지 덮개에서 확인한 뒤 질문한다). 07의 확인 흐름과 위젯 미리보기 페이지 e2e 준비, 트레이스를 읽는 길을 쓴다

**Status:** done

### 마커와 래퍼

- [x] **`pyproject.toml`에 마커 `llm_portal`을 더하고 `addopts`의 제외에 넣는다.** 시험 준비 코드가 실제 모델 마커를 나열한 목록에도 더해, 그 시험이 돈 실행 끝에 트레이스의 토큰 합계가 찍힌다. 그 목록과 그것을 보는 시험은 `tests/`를 `llm_widget`으로 grep해 찾는다
- [x] **`tests/test_portal_llm.py`가 `tests/test_widget_llm.py`와 같은 모양으로 위젯 미리보기 페이지 e2e의 Playwright 프로젝트 `llm`을 자식으로 돌린다.** 트레이스 자리로 `tmp_path` 아래를 `AGENT_OS_PORTAL_TRACES`로 넘기고 `AGENT_OS_PORTAL_LLM=1`을 준다. 키가 없으면 skip이 아니라 실패한다(`.claude/rules/tests.md`)

### LLM 모드의 준비와 사례

- [x] **위젯 미리보기 페이지 e2e의 Playwright 프로젝트 `llm`은 `AGENT_OS_PORTAL_LLM=1`일 때만 선다.** 그때 준비는 위젯 e2e처럼 저장소의 플러그인 루트를 임시 플러그인 루트에 옮기고, 위젯 미리보기 페이지 설정의 첫 사이트(익명)가 에이전트 `calc`를 열며 사이트 파일의 그 사이트도 `calc`를 열 에이전트로 든다(명세 "실제 모델 e2e 하나"의 주석). CI의 `e2e-portal`은 그 변수를 두지 않아 이 프로젝트가 서지 않는다
- [x] **사례 하나가 `?site=` 없이 위젯 미리보기 페이지를 열어 고지를 확인하고, 입력창 "질문"에 요청 하나를 보내 출력이 서는 것과, 트레이스의 `llm_called`, 실행 주체의 `anon-` 접두를 본다**

### 문서

- [x] **마커의 문서를 고친다.** `.claude/rules/tests.md`, `CLAUDE.md` 검증 명령(`uv run --env-file .env pytest -m llm_portal`과 치는 때: 위젯 미리보기 페이지·서버의 최종 사용자 경로를 건드렸을 때), `docs/constitution/operations.md`의 LLM 테스트 절, `.github/workflows/ci.yml` 머리 주석의 "LLM 호출 테스트(-m llm, -m llm_widget)는 돌리지 않는다." 줄이다. 그 밖에 실제 모델 마커를 나열하거나 둘로 세거나 치는 때를 적은 자리(시험 준비 코드의 독스트링, `.claude/rules/http.md`, `.github/PULL_REQUEST_TEMPLATE.md`의 체크리스트 등)는 살아 있는 문서와 코드를 `llm_widget`으로 grep해 찾아 함께 고친다. 헌법을 고치면 판을 patch로 올린다
- [x] **바꾼 rules는 새 세션에서 그 경로의 파일을 Read로 열어 실리는 것을 본다**(작업 규약 3)

### 검증

- [x] **빨강을 먼저 본다**(헌법 원칙 II). 실제 모델 시험은 구현 전에 빨갛지 않을 수 있다(07이 흐름을 이미 들였다). 그러면 단언 하나를 일부러 틀리게 두어 이 시험이 그 단언으로 빨개지는 것을 본 뒤 되돌린다
- [x] **`uv run --env-file .env pytest -m llm_portal`이 초록이다.** 워크트리에서 쓸 `.env` 경로는 `docs/constitution/operations.md`의 LLM 테스트다
- [x] **위젯 미리보기 페이지 e2e(`pnpm -C web/apps/portal exec playwright test`)가 로컬에서 그대로 초록이다.** 기본 프로젝트가 LLM 모드의 변경에 흔들리지 않는 것을 본다
- [x] **검증 명령이 모두 초록이다.** 손으로 치는 다섯과 `-m llm_portal`, 위젯 미리보기 페이지 e2e다
- [x] **이 티켓이 기능의 마지막으로 닫히면 그 커밋이 `.scratch/pilot-portal/plan.md`에 `**끝:**` 줄을 적는다.** 08이 나중에 닫히면 08이 적는다(이 티켓을 닫을 때 08은 `ready-for-agent`라 적지 않았다)(`CLAUDE.md` 지도)
