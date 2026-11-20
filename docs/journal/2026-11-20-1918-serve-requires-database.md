# 2026-11-20 (19:18) serve는 표의 판이 맞는 데이터베이스에 닿아야 뜬다

브랜치 `feature/03-serve-requires-database`, 워크트리 `.claude/worktrees/03-serve-requires-database`. 모델 Sonnet 5.5 / high. 티켓은 `.scratch/postgres-foundation/issues/03-serve-requires-database.md`(기능의 셋째 티켓이다. 04가 나란히 돌아, 둘 가운데 늦게 병합하는 쪽이 `**끝:**` 줄과 기능 단락을 쓴다).

## 사용자 프롬프트

> 사용자(붙여 넣은 지시문): .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. … 인자: .scratch/postgres-foundation/issues/03-serve-requires-database.md
>
> 다음 작업: .scratch/postgres-foundation/issues/03-serve-requires-database.md. `serve`는 표의 판이 맞는 데이터베이스에 닿아야 뜬다
> 다음 단계: 구현
> 브랜치: feature/03-serve-requires-database
> 모델: Sonnet 5.5 / high
> 이번 요청 범위: PR과 병합까지

> 사용자(선택 화면의 답, 로컬 모델 시험의 비용 확인): 질문 "로컬 모델 시험(llm_local)을 돌려도 될까요? 이 시험은 Runpod(GPU 서버를 빌려 주는 서비스)에서 서버를 빌려 오픈 모델 둘(Gemma 4, gpt-oss-20b)을 띄우고, 계산기 예시가 도구를 제대로 부르는지 본 뒤 서버를 지웁니다. 이번 변경이 main.py와 어댑터 폴더(src/agent_os/adapters/)를 고쳐서 병합 조건에 듭니다. 예상 비용은 도구가 방금 찍은 값으로, 첫 후보(RTX A5000 서버 둘, 시간당 $0.54)가 보통 30분에 $0.27, 최악 90분에 $0.81입니다. 재고가 없으면 다음 후보로 넘어가고 가장 비싼 A40 둘이면 최악 $1.77입니다. 90분이 지나면 타이머가 서버를 지웁니다."에 라벨 "돌린다 (추천)", 설명 "--yes를 붙여 칩니다. 위 범위의 Runpod 요금이 계정에 청구됩니다. 결과(통과 수와 쓴 시간)는 일지와 PR에 적습니다."를 골랐다.

## 설계에서 티켓과 달라진 것

- **포트의 메서드가 둘이 아니라 넷이다.** 티켓은 `startup_problem()`과 `close()` 둘을 말한다. 멈출 때의 글은 "확인하다 뜻밖의 오류로 멈췄다"와 "연결을 닫다 오류가 났다"도 있는데, 이 글에는 자리(`호스트:포트/이름`)와 까닭(오류 번호, 가장 안쪽 `OSError`의 이름)이 들어가고 둘 다 어댑터만 안다. 이 층(`agent_os.http`)이 그 글을 지으면 주소 조각을 알아야 해서 원칙 IV와 비밀번호가 새지 않는다는 원칙 V를 함께 지키기 어렵다. 그래서 글을 짓는 일을 어댑터에 두고 포트에 `unexpected_problem(error)`와 `close_problem(error)`를 더했다. 둘 다 동기 함수다. 어댑터는 포트를 import하지 않고 시그니처로 만족한다.
- 확인 미들웨어 `CheckDatabase`는 `app.add_middleware`의 마지막 호출이라 가장 바깥이다. lifespan 메시지만 만지고 HTTP 요청은 그대로 지나보낸다. 닫기는 한 번만 한다(플래그). 앱 자신의 시작 단계나 끝 단계가 실패해도 연결 묶음을 닫는다.

## 검사

- **포트의 모양(티켓 20번째 줄).** 메서드 하나(`close_problem`)를 뺀 어댑터를 포트 타입에 대입하는 임시 파일을 지어 `uv run pyright`를 쳤다. `"Lacking" is incompatible with protocol "Database"`, `"close_problem" is not present (reportAssignmentType)`로 걸렸다. 조립 자리(`create_app` 호출)에 직접 넘긴 첫 시도는 다른 필수 인자 누락(`reportCallIssue`)이 먼저 나와 포트 검사를 가려서, 대입 한 줄로 바꿔 같은 검사를 따로 봤다. 확인 뒤 임시 파일을 지웠고 `git status`에 남지 않았다. 편집기 진단은 이 폴더가 아닌 사본의 패키지를 읽어 "could not be resolved"를 냈다. 그건 믿지 않고 `uv run pyright`의 결과만 봤다.
- **README의 세 명령을 이 PC에서 돌렸다.** `docker compose -f compose.test.yaml up -d --wait`(이미 떠 있어 `Running`/`Healthy`), `AGENT_OS_DATABASE_URL=postgresql://agent_os:agent_os@127.0.0.1:25432/agent_os`로 `uv run agent-os migrate`(`표를 없음에서 0001으로 올렸습니다.`), 같은 주소로 `uv run agent-os serve --model claude-opus-5 --port 8071`(관리·채널 토큰은 환경에 줬다). 서버 기록에 `Application startup complete.`가 찍혔고 `GET /health`가 `200 {"status":"ok"}`였다. 포트는 다른 세션과 겹치지 않게 8071을 줬다(README는 기본 포트).
- **표가 없는 데이터베이스에서 멈추는 모습(Windows).** 같은 환경에서 주소의 데이터베이스만 표가 없는 `postgres`로 바꿔 `serve`를 띄우니 종료 코드 3이었고 출력은 `Waiting for application startup.` 다음에 `ERROR:    데이터베이스의 표가 이 판보다 뒤처져 있습니다. agent-os migrate 를 먼저 돌리십시오.`, `  표의 판은 없음이고 이 판의 마지막 판은 0001입니다.`, `ERROR:    Application startup failed. Exiting.`였다. 역추적은 없었다. 이 PC의 Windows 실행이라 티켓이 말한 리눅스 컨테이너에서의 확인은 아래 "리눅스 컨테이너"에 따로 적는다.
- **규칙을 바꿨으니 카나리아.** `.claude/rules/http.md`를 바꿨고 `tools/sibling_overlap.py`가 그 파일을 원천으로 든 명세 셋을 짚었다. `claude -p`로 셋을 돌려 모두 통과 4, 실패 0, "없음" 섞임 0이었다(`http_rule_continuation_422.toml`, `http_rule_pre_owner_damage.toml`, `http_rule_llm_widget.toml`. 실험군은 규칙의 `paths` 안 파일, 대조군은 `README.md`를 읽었고 두 갈래의 커밋은 `7b52bbd61`이다). 세 명세의 `# 최신 결과:` 줄을 고쳤다. 커밋하기 전의 작업 트리로 돌렸다.
- **헌법 판.** `tools/sibling_overlap.py`가 낸 형제의 가장 높은 판 3.1.3(origin/dev)보다 높게 3.1.4로 올렸다.
- 어댑터에 `close_problem`의 글을 재는 시험을 더했다(`tests/adapters/test_postgres_database.py`).

- **검증 러너(`uv run python tools/run_checks.py`, 백그라운드).** check-notes, check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright-linux, pyright, run-hooks, web-verify가 통과했고 pytest는 `1 failed, 7978 passed, 8 warnings in 1389.18s (0:23:09)`였다. 빨강은 `tests/channel/cli/test_interrupt.py::test_도구_호출_도중에_한_번_누르면_서버를_닫고_중단으로_끝난다`의 "Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다"(실제 하위 프로세스와 30초 시간 단언)이다. 이 파일만 홀로 돌리니 `6 passed in 317.10s`였다. 이 시험이 지나는 길은 이번에 고친 `_serve`·`_migrate`·`create_app`이 아니고, pytest 한 바퀴가 CLAUDE.md가 적은 8분이 아니라 23분 걸린 만큼 기계가 막혀 있었다(같은 시각 `@playwright/mcp` 노드 프로세스 약 30쌍이 남아 있었고 Defender `MsMpEng`이 CPU 257%였다. 둘 다 손으로 본 값이다). 그래서 부하로 난 시간 단언으로 읽는다(재현은 홀로 돌려 통과한 것까지이고 원인 증명은 아니다).
- **`uv run ruff check .`** 통과. **`uv run pyright`** 오류 0.
- **`uv run --env-file ../../../.env pytest -m llm`:** `23 passed, 7983 deselected in 1024.27s`. `LLM 토큰 합계 268,110(입력 262,818, 출력 5,292). 트레이스 30개, 모델 호출 62건. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다.`
- **`-m llm_widget`:** `1 passed, 8005 deselected in 501.78s`, `LLM 토큰 합계 17,047(입력 16,785, 출력 262). 트레이스 2개, 모델 호출 4건.` 앞선 세 번은 실패했다. 아래 "e2e를 막은 것 둘"에 원인이 있다.
- **`-m llm_portal`:** `1 passed, 8005 deselected in 297.63s`, `LLM 토큰 합계 6,997(입력 6,925, 출력 72). 트레이스 1개, 모델 호출 2건.`
- **관리 화면 e2e(`pnpm -C web/apps/admin exec playwright test`):** 9개 가운데 8개 통과, `decision.e2e.ts`의 첫 사례 하나가 승인 뒤 `run_finished`가 5초 안에 서지 않았다는 기대 시간 초과로 실패했다(그 실행은 멈춤까지 8초 걸렸다). 그 파일만 홀로 돌리니 `3 passed (58.8s)`였고 같은 사례가 8.0초(실패 때는 14.9초)에 통과했다. 부하로 난 기대 시간 초과로 읽는다.
- **위젯 e2e:** `19 passed (1.5m)`. **위젯 테스트 페이지 e2e:** `41 passed (2.0m)`. **단독 배포 e2e(`pnpm -C web/packages/e2e-standalone exec playwright test`, 80·443·3000이 비어 있는 것을 `netstat`으로 보고 쳤다):** `14 passed (5.1m)`. 이 PC의 443을 쥐던 `rag-engine` 프록시는 이번에 떠 있지 않아 멈추지 않았다.
- **`uv run --env-file ../../../.env python tools/llm_local.py run`:** `--yes` 없이 쳐 예상 비용을 보이고(종료 코드 4, 아무것도 띄우지 않았다) 사용자의 답(위 "사용자 프롬프트"의 둘째 답)을 받은 뒤 `--yes`로 쳤다. 후보 셋(pods의 RTX A5000 둘, RTX 3090 둘, A40 둘)은 `terraform apply 실패(종료 코드 1, 시간 제한 False)`였고, 넷째 후보 shared A40 하나에서 `2 passed, 8004 deselected in 103.31s`, `LLM 토큰 합계 6,314(입력 6,191, 출력 123). 트레이스 2개, 모델 호출 4건.`이었다. 기록 묶음은 `gpu` A40, `layout` shared, `passed` 2, `elapsed_seconds` 417.7, `cost_per_hour` 0.59, `price_table_date` 2026-11-13, `test_exit_code` 0, `exit_code` 0, `reason` "시험이 끝났다", 회차 파일 `C:\Users\User\.agent-os\llm-local\feature%2F03-serve-requires-database\records\round-0001-20261120T122626Z.json`이다. **묶음의 `commit`은 `7b52bbd616029d1f7edecc1b8c30b89ad4f63e6b`(기준 dev의 끝)다.** 이 변경을 아직 커밋하지 않은 작업 트리로 돌렸기 때문이다. 규약(`operations.md` LLM 테스트의 "기록과 유효함")은 시험한 커밋과 브랜치 끝 사이의 차이가 범위의 경로를 건드렸는지로 유효를 가르는데, 글자대로 읽으면 이 기록은 `src/agent_os/`의 변경을 건너 무효다. 실제로 시험한 내용이 커밋할 내용과 같은지 대 볼 수 있도록 시험 때 작업 트리의 해시를 남긴다: `git diff HEAD -- src pyproject.toml uv.lock | sha256sum`의 앞 16자가 `af6f627e40eb0cb1`이고(추적 파일 `adapters/postgres/database.py`, `main.py`, `server.py`), 추적하지 않는 새 파일 `src/agent_os/http/database.py`의 `sha256sum` 앞 16자가 `f4c57f38a1369549`다. 셀프 리뷰 반영이 `src/`를 바꾸면 이 해시가 어긋나고, 그때는 다시 돌려야 하며 다시 띄울 때도 비용 확인을 받는다. 같으면 시험한 내용이 그대로 커밋된 것이다. 글자대로의 무효를 어떻게 다룰지(기록의 커밋이 기준 커밋인 채 병합 조건을 채웠다고 볼지)는 새 세션이 `merge.md`의 "병합 전"을 읽고 정하며, 정하지 못하면 PR 열기 전에 사용자에게 묻는다. 이 판단은 내 어림이다.
- **리눅스 컨테이너에서 `serve`(티켓 36번째 줄).** 단독 배포 e2e가 이 작업 트리로 지은 이미지 `agent-os-e2e/agent-os-runtime:0.1.0-rc.1`을 `docker run`으로 띄웠다(`--add-host=host.docker.internal:host-gateway`, 데이터베이스는 테스트 컨테이너, 셸 `MSYS_NO_PATHCONV=1`). 스크립트는 세션 스크래치패드에 두었다가 지웠고 커밋하지 않았다. 회차마다 표지를 단언했고(컨테이너의 `uname -s`가 `Linux`, 기대한 글, `Application startup failed. Exiting.`, `Traceback` 없음, 종료 코드 3, 모르는 번호 갈래는 `UPDATE 1`), 첫 판은 Git Bash가 `/app/plugins`를 `C:/Program Files/Git/app/plugins`로 바꿔 `기본 모델 플러그인이 없다`로 종료 1이 되어 표지 없는 회차 9개가 모두 "측정 아님"으로 잡혔다. 경로 변환을 끈 둘째 판은 측정 아님 0이다. 갈래 1(표가 없는 빈 데이터베이스): `INFO:     Started server process [7]`, `INFO:     Waiting for application startup.`, `ERROR:    데이터베이스의 표가 이 판보다 뒤처져 있습니다. agent-os migrate 를 먼저 돌리십시오.`, `  표의 판은 없음이고 이 판의 마지막 판은 0001입니다.`, `ERROR:    Application startup failed. Exiting.`, 종료 코드 3. 갈래 2(`alembic_version`의 번호를 `9999`로 바꾼 데이터베이스): 같은 꼴에 글이 `ERROR:    데이터베이스가 이 판보다 새롭습니다. 되돌리려면 올리기 전의 백업을 복원하십시오.`, `  표의 판은 9999이고 이 판이 아는 마지막 판은 0001입니다.`이고 종료 코드 3이다. 두 갈래 모두 역추적이 없다. 만든 데이터베이스는 도구의 `drop`으로 지웠다.

## e2e를 막은 것 둘(이 변경의 결함이 아니다)

- **임시 폴더의 떠돌이 `inspect.py`.** `-m llm_widget` 첫 판이 `테스트 데이터베이스를 표를 올리지 못했다`로 실패했고, 역추적이 `C:\Users\User\AppData\Local\Temp\inspect.py`(2026-11-17 10:26, 244바이트, `.scratch/search-eval/...report-rerank-100.json`을 읽는 스크래치)를 표준 라이브러리 `inspect` 대신 불러오고 있었다. e2e 묶음이 `python -m agent_os.main ...`을 작업 폴더 `tmpdir()`로 띄우는데(`serve`의 기존 길도 같다), `-m`은 작업 폴더를 `sys.path` 맨 앞에 두기 때문이다. 이 파일은 다른 세션이 남긴 것으로 보여 지우지 않고 이름만 `inspect.py.stray-shadows-stdlib`로 바꿨다(되돌리기: 그 이름을 원래대로). 임시 폴더에 표준 라이브러리 이름과 겹치는 다른 `.py`나 패키지는 없었다(손으로 본 점검). 이 PC에서만 생기는 문제이고 CI에는 해당 없다. 코드는 고치지 않았다.
- **부하로 느린 시작.** 둘째·셋째 판은 `serve`가 60초 안에 서지 못했고(출력 비어 있음), 셋째 판은 `migrate`가 120초 제한에 걸렸다(`spawnSync … ETIMEDOUT`). 같은 시험을 둘째 실패 뒤 `diagnosing-bugs`로 풀었다. 작업 폴더를 임시 폴더로 두고 `import agent_os.main` 하는 시간을 두 체크아웃(변경이 든 작업 트리와 변경 전 dev인 주 체크아웃)에서 번갈아 쟀더니 주 체크아웃도 64.4초, 44.2초, 24.5초, 작업 트리는 126.7초, 49.9초, 18.9초였다(스크래치 스크립트, 지웠다). 차이는 내 변경이 아니라 차가운 파일 캐시와 기계 부하로 읽고, 데워진 뒤 넷째 판이 통과했다. 이 반복에 쓴 디버그 표지(`DEBUG-3f7a`)는 저장소에 남지 않았다(grep으로 봤다).

## 이 세션이 번복하거나 고친 것

- 티켓의 "메서드는 둘이다"를 넷으로 바꿨다(위 "설계에서 티켓과 달라진 것").
- `database.ts`의 `prepareDatabase`가 `migrate`를 임시 폴더(`tmpdir()`)에서 돌리는 것은 `serve.ts`의 `startServe`와 같은 작업 폴더로 맞추려고 일부러 둔 것이다. 떠돌이 `inspect.py`는 그 길을 따라 드러났을 뿐이고 코드는 바꾸지 않았다.
- 문서: `.claude/rules/http.md`(앱 조립 항목에 데이터베이스 포트와 `CheckDatabase`, 미들웨어 차례의 바깥 끝에 `CheckDatabase`, 테스트 항목에 `FakeDatabase`와 `LifespanDriver`의 시작·끝 수명 주기 쓰임), `docs/constitution/operations.md`(LLM 테스트 절: `serve`를 띄우는 `llm`·`llm_widget`·`llm_portal`이 테스트 컨테이너를 요구하고 `llm_local`은 아니다), `CLAUDE.md`(검증 명령의 테스트 줄에 같은 전제), `README.md`(관리 화면 절의 `serve` 블록에 컨테이너 띄우기·`AGENT_OS_DATABASE_URL`·`migrate`), `docs/constitution/README.md`(판 3.1.4, 마지막 개정 2026-11-20). 규칙 파일을 고치기 전에 `writing-for-agents`를 불렀다. 낡은 표현을 저장소 전체에서 찾았더니 살아 있는 문서에는 없고 명세·티켓·일지의 기록에만 있었다.
- README의 세 명령(`docker compose -f compose.test.yaml up -d --wait`, 같은 주소로 `migrate`와 `serve`)은 이 PC에서 돌렸다: 컨테이너 `Running`/`Healthy`, `migrate`가 `표를 없음에서 0001으로 올렸습니다.`, `serve`(포트 8071을 줬다)가 `Application startup complete.`를 찍고 `GET /health`가 `200 {"status":"ok"}`. 표가 없는 `postgres` 데이터베이스로 바꿔 띄우니 종료 코드 3과 위 두 줄 글이었다(Windows).

## 인계 직전의 상태

- 바꾼 파일은 모두 커밋하지 않았다. 남은 단계: 셀프 리뷰와 반영, 티켓 Status를 `done`으로 하고 체크박스 채우기, 커밋(pre-commit), PR(느낌표 없는 제목), 봇 회차, 병합. `04`가 먼저 병합됐으면 `**끝:**` 줄과 `uv run python tools/plan_table.py`와 `docs/release-notes/features/postgres-foundation.md`를 같은 커밋에 싣는다.
- 형제가 같은 파일을 고쳤다: 워크트리 `04-guard-new-migration-prs`가 `.github/workflows/ci.yml`과 `docs/constitution/operations.md`를 고쳤다(`tools/sibling_overlap.py`). 병합 때 글자 충돌 후보다.

## 인계

이 세션(제목 `feature/03-serve-requires-database`)은 컨텍스트가 인계 문턱을 넘어 `셀프 리뷰 직전`에서 새 세션에 넘긴다. 셀프 리뷰(`/code-review`)는 새 세션이 한다. 이 세션이 띄운 백그라운드 작업은 모두 끝났다(비용을 승인받은 `llm_local`도 끝난 뒤 넘겼다). 방금 이 세션에서 `code-review` 스킬이 불렸으나 서브에이전트는 띄우지 않았다.

- 남은 단계: 셀프 리뷰와 반영(Critical·Major), 티켓 Status를 `done`으로 하고 체크박스 채우기, `tools/sibling_overlap.py`와 `git branch --show-current` 확인, 커밋(pre-commit), 푸시와 PR(제목에 느낌표 없음, 본문에 위 검사의 기록과 포트가 넷이 된 이유), `merge.md`의 봇 회차, 병합. 04가 먼저 병합됐으면 같은 커밋에 `**끝:**` 줄과 `uv run python tools/plan_table.py`와 `docs/release-notes/features/postgres-foundation.md`를 싣는다(티켓 9번째 문단).
- 셀프 리뷰에 같이 넘길 것: 포트가 둘이 아니라 넷이라는 어긋남(티켓 "포트와 조립" 첫 줄과 명세), 고친 규칙 `.claude/rules/http.md`를 새 세션에서 불러 보는 일(작업 규약 3. 이 세션은 `claude -p` 카나리아 셋으로 갈음했고 통과 4씩이었다), 일지 "검사"의 `llm_local` 기록이 글자대로는 무효라는 점과 해시 대조.
- 이 세션이 다른 곳에서 손댄 것: 임시 폴더의 `inspect.py`를 `inspect.py.stray-shadows-stdlib`로 이름만 바꿨다(위 "e2e를 막은 것 둘"). 사용자에게 알린다.

인계 지시문:

```
다음 작업: .scratch/postgres-foundation/issues/03-serve-requires-database.md. serve는 표의 판이 맞는 데이터베이스에 닿아야 뜬다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/postgres-foundation/issues/03-serve-requires-database.md
브랜치: feature/03-serve-requires-database
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: 일지 docs/journal/2026-11-20-1918-serve-requires-database.md의 "## 검사"와 "## 인계"
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. 검증 명령(-m llm·llm_widget·llm_portal·llm_local, e2e 넷, 카나리아 셋 포함)은 셀프 리뷰 전에 모두 돌았다. 일지 "검사"에 결과가 있고, llm_local 기록이 글자대로는 무효인 점과 시험 때 src의 해시가 거기 적혀 있다. 반영이 src를 바꾸면 해시가 어긋나 llm_local을 다시 돌려야 하고 그때 비용 확인을 사용자에게 받는다. 포트는 티켓의 둘이 아니라 넷이다(일지 "설계에서 티켓과 달라진 것"). docs/journal/2026-11-20-1918-serve-requires-database.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-11-20T12:28:05Z

## 셀프 리뷰와 반영 (2026-11-20, 이어받은 세션)

범위: base `7b52bbd61`(HEAD와 같다), 추적 파일 29개 변경, 추적하지 않는 새 파일 5개, 커밋 0개. 두 축 서브에이전트(표준은 sonnet·high)가 돌았고 Critical은 없었다.

고친 것:
- **Major, `.claude/rules/http.md`의 앞 판 문장(그 글에는 주소 조각도 비밀번호도 싣지 않는다)은 거짓이었다.** 어댑터의 글은 `호스트:포트/데이터베이스 이름`을 싣는다(`DatabaseUrl.place`). "글은 어댑터가 짓고(`http`는 주소 조각을 모른다), 거기에는 `호스트:포트/데이터베이스 이름`만 싣고 계정과 비밀번호는 싣지 않는다(원칙 V)"로 고쳤다.
- **Major(명세 축은 Major, 표준 축은 Minor), `ruff format --check`가 1파일에서 빨갰다.** `adapters/postgres/database.py`의 `class Failure` 앞 빈 줄 하나가 모자랐다. `uv run ruff format`으로 고쳤다. 지금은 `2501 files already formatted`.
- `docs/constitution/operations.md` LLM 테스트 절의 앞 판 문장(시험이 `database` 픽스처로 표를 올린 데이터베이스를 받는다)은 `llm`에만 맞았다. `llm`은 `database` 픽스처로, `llm_widget`과 `llm_portal`은 e2e-stack이 `serve`를 띄우기 전에 각자 받는다고 고쳤다(`tests/test_widget_llm.py`와 `tests/test_portal_llm.py`에는 `database` 픽스처가 없다).
- `tests/fake_database.py` 독스트링의 인용 "시작 단계"는 http.md에 없는 글자열이었다. "시작과 끝의 수명 주기"로 바로잡았다.
- `README.md`: "이유 한 줄"을 "이유"로 바꿨다(힌트가 붙은 두 줄 글도 있다).
- 시험을 더했다. `tests/test_check_database.py` 셋: 안쪽 앱이 스스로 시작을 실패시킬 때, 종료를 실패시킬 때, 아무 말 없이 끝날 때 닫기가 한 번 불린다(`CheckDatabase`의 독스트링이 약속한 길이다. 리뷰어가 임시 스크립트로 맞는 것을 먼저 확인했고 이제 시험이 고정한다). `tests/test_main.py`: 닫기마저 실패하는 사례가 닫기를 시도했는지(`["startup_problem", "close_started"]`), 포트 적합성 시험의 빈 단언을 `unexpected_problem`의 글 단언으로. 관련 시험 71개 통과, pyright 오류 0.
- 티켓: 체크박스 23개를 채우고 `Status: done`, 첫 체크박스에 포트가 넷이 된 사정을 덧붙였다.

남긴 것과 이유:
- 닫기 실패 글을 버리는 길(`_guard`의 시작 실패, 앱이 스스로 낸 실패, `finally`)이 있다는 표준 축의 Minor(CQS). 시작이 이미 실패해 그 글이 나가는 길이라 닫기 실패 글까지 더 싣지 않는 것은 티켓("닫기가 실패해도 `lifespan.startup.failed`를 보낸다")과 같다. 나머지 두 길은 이미 앱이 실패 메시지를 보낸 뒤이거나 보낼 수 없는 자리다.
- `web/apps/admin/e2e/stack.ts`가 `prepareDatabase`의 사본을 든 것(Duplicated Code). 관리 화면 e2e가 e2e-stack 패키지를 쓰지 않던 선례라 합치려면 별도 변경이다. migrate 실패 뒤 drop이 던지면 원래 오류를 가리는 문제와 migrate 작업 폴더 차이는 그 사본을 합칠 때 같이 본다.
- `ci.yml`의 service container 블록이 네 번 같은 것(YAML이라 줄일 길이 없다. 01의 digest 시험이 모두 읽는 구조다).
- `_read_database_url() -> DatabaseUrl | str`의 `isinstance` 반복(Primitive Obsession). 아직 쓰는 곳이 `_serve`와 `_migrate` 둘이고 모양을 바꾸면 01의 `migrate` 시험이 같이 움직여 이 티켓의 몫이 아니다.
- 명세 Testing Decisions 둘째의 "가짜 MCP 서버" 대신 수명 함수를 기록자로 감싼 `_StartupJobs`를 쓴 것. 순서(확인 뒤에야 시작 일이 돈다)는 재고, MCP 연결 자체는 재지 않는다.
- README 자리: 티켓의 "시작 절"은 README에서 `serve` 명령이 있는 절이 "관리 화면" 하나뿐이어서 거기 두었다.

`llm_local` 기록과 `src` 해시: 리뷰 중 `uv run ruff format`이 `src/agent_os/adapters/postgres/database.py`에 빈 줄 하나를 더해 `git diff HEAD -- src pyproject.toml uv.lock`의 해시가 시험 때의 `af6f627e40eb0cb1`에서 `e17e3ad13774679d`로 바뀌었다. 그 파일에서 더한 빈 줄만 되돌리면 해시가 다시 `af6f627e40eb0cb1`이 되는 것을 손으로 쟀다(되돌렸다가 다시 서식을 입혔다). 시험한 내용과 커밋할 내용은 줄 바꿈 서식 한 줄 말고는 같다. 새 파일 `src/agent_os/http/database.py`의 해시는 그대로 `f4c57f38a1369549`다. 그래서 `llm_local`을 다시 돌리지 않았다. 이 판단은 내 어림이고, `merge.md`의 병합 전에서 다시 본다.

## 커밋과 인계 (2026-11-21, 이어받은 세션)

커밋 `7c8e2c81c`(로컬, 아직 푸시하지 않았다)를 만들었다. pre-commit이 네 번 돌았다. 첫 번째는 변이 표의 원문이 `ci.yml`에 다섯 번 나와 막혔고(각 변경을 앞뒤 줄로 한 번만 나오게 고쳐 `--check`와 변이 19·20 실행으로 확인했다), 둘째와 셋째는 같은 기계에서 다른 세션이 pytest `-n 8`과 `run_checks`를 돌리는 동안 걸린 시간 단언 시험 둘(`test_probe_kit`, `test_rerun_runner`)과 web-verify의 `page.goto` 30초 초과, pytest 4200초 제한으로 빨갰다. 시간 단언 둘은 홀로 돌리면 78개가 통과했다(395초). 넷째가 통과했다. 이 변경이 깨뜨린 시험은 없었다.

검증 명령 가운데 pre-commit이 갈음하지 못하는 것(-m llm 넷, e2e, 사진 비교, 카나리아)은 앞 세션의 기록이 "검사"에 있다. 카나리아 셋은 셀프 리뷰에서 한 문장을 고친 `.claude/rules/http.md` 앞의 것이고 다시 돌리지 않았다. 고친 문장은 카나리아 명세(422 이어가기, 소유자 손상 전, llm_widget)와 관계가 없다고 본 내 판단이다. PR 본문에 그대로 적는다.

사용자에게 알릴 것: 앞 세션이 임시 폴더의 `inspect.py`를 `inspect.py.stray-shadows-stdlib`로 이름만 바꿨다(위 "e2e를 막은 것 둘").

04(`#612`)가 먼저 `origin/dev`에 병합됐다(`0ff9e2775`). 그래서 이 PR이 기능의 마지막 티켓을 닫는다. 같은 PR에 `**끝:**` 줄(규칙은 `docs/agents/issue-tracker.md`), `uv run python tools/plan_table.py` 출력, `docs/release-notes/features/postgres-foundation.md`를 싣는다. `sibling_overlap`은 헌법 3.1.4가 겹치지 않는다고 했고, `origin/dev`가 `.github/workflows/ci.yml`을 함께 고쳤으니 기준 브랜치를 합칠 때 글자 충돌을 푼다.

### 인계

이 세션(제목 `feature/03-serve-requires-database`)은 컨텍스트가 인계 문턱을 넘어 `커밋 뒤`에서 새 세션에 넘긴다. 이 세션이 띄운 백그라운드 작업은 모두 끝났다.

- 남은 단계: 기준 브랜치(`origin/dev`) 합치기와 `ci.yml` 충돌 풀기, `**끝:**` 줄과 `plan_table.py`와 릴리스 노트를 새 커밋으로 싣기(pre-commit이 길어 부하가 큰 기계에서는 20분을 넘는다. 시간 단언이 빨개지면 홀로 돌려 보고 다시 커밋한다), 푸시와 PR(제목에 느낌표 없음, 본문에 위 검사의 기록과 포트가 넷이 된 이유와 카나리아 가정), `merge.md`의 봇 회차, "병합 전"에서 `llm_local` 기록 유효 판정, 병합.

인계 지시문:

```
다음 작업: .scratch/postgres-foundation/issues/03-serve-requires-database.md. serve는 표의 판이 맞는 데이터베이스에 닿아야 뜬다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/postgres-foundation/issues/03-serve-requires-database.md
브랜치: feature/03-serve-requires-database
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: 일지 docs/journal/2026-11-20-1918-serve-requires-database.md의 "## 셀프 리뷰와 반영"과 "## 커밋과 인계"
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰와 반영과 pre-commit을 지난 커밋 7c8e2c81c가 이 브랜치에 있고 아직 푸시하지 않았다. 일지의 이 절이 든 변경은 커밋하지 않았다. 04(#612)가 origin/dev에 병합돼 이 PR이 기능의 마지막 티켓이다: origin/dev를 합쳐 ci.yml 충돌을 풀고, 끝 줄과 plan_table.py 출력과 docs/release-notes/features/postgres-foundation.md를 싣고, 푸시와 PR, 봇 회차, 병합 전의 llm_local 기록 유효 판정, 병합 순서로 한다. llm_local을 다시 돌리면 비용 확인을 사용자에게 받는다. 포트는 티켓의 둘이 아니라 넷이다. docs/journal/2026-11-20-1918-serve-requires-database.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-11-20T15:49:02Z

## PR 준비 (2026-11-21, 이어받은 세션)

`origin/dev`(04의 `#612`와 `#613`까지)를 합쳤고 충돌은 없었다(`ci.yml`을 양쪽이 고쳤지만 겹치는 줄이 없었다). 이 PR이 기능의 마지막 티켓이라 기능 계획에 `**끝:** 2026-11-21`을 적고 `uv run python tools/plan_table.py`로 `.scratch/plan.md`를 다시 만들었으며, 기능 단락 `docs/release-notes/features/postgres-foundation.md`(328자)를 실었다. 저장소 상태 시험 `tests/test_plan_status.py`는 13개 통과했다.

커밋 `df1035ae3`(끝 줄·plan_table 출력·기능 단락·일지)의 pre-commit이 한 번에 통과했고, 푸시한 뒤 PR [#615](https://github.com/njh6803/agent-os/pull/615)를 열었다. 제목은 느낌표 없는 `feat: serve는 표의 판이 맞는 데이터베이스에 닿아야 뜬다 (03-serve-requires-database)`이고, 본문은 `.github/PULL_REQUEST_TEMPLATE.md`를 채웠다(포트가 넷이 된 이유, 카나리아를 다시 돌리지 않은 가정, `llm_local` 기록이 글자대로는 무효인 점을 적었다). 느낌표를 붙이지 않은 까닭은 운영자가 올릴 때 손댈 것이 02의 `upgrade/standalone-postgres.md`에 이미 있기 때문이다(내 판단이고 `check_notes`는 이 짝만 본다).

PR 직전 외부 리뷰(`coderabbit-review` 서브에이전트): CodeRabbit CLI 0.7.5가 `Seat: not assigned`(Plan: Free)에서도 `review_completed`, findings 0으로 끝까지 돌았다(서브에이전트의 보고). 서브에이전트가 파일을 직접 읽어 낸 Minor 넷은 모두 병합을 막지 않는다. (1) 데이터베이스가 안 닿는 동안 최대 약 35초 SIGINT·SIGTERM이 먹히지 않는다. uvicorn 소스를 읽어 낸 것이고 신호를 실제로 보내 재지는 않았다. 이 PR에서 고치지 않고 후속으로 넘긴다. (2) 시작 확인이 실패해 닫을 때 닫기 실패 글을 버린다. 위 "남긴 것"의 첫 항목과 같고 티켓이 말한 대로다. (3) `web/apps/admin/e2e/stack.ts`가 e2e-stack의 `prepareDatabase` 사본을 든다. 위 "남긴 것"에 있다. (4) 기존 `migrate` 실패 글의 역추적 전문은 이 PR이 건드린 코드가 아니다.

### 인계 직전의 상태 (PR 연 뒤)

- 푸시한 HEAD는 `df1035ae3`이다. 병합 직전에 `gh pr view 615 --json headRefOid`와 `git rev-parse HEAD`가 같은지 본다. 이 PR이 기능 `postgres-foundation`의 마지막 티켓이다.
- 남은 단계: 첫 `@coderabbitai review` 코멘트(새 세션이 남긴다), `merge.md` 2의 봇 회차(CodeRabbit 한도와 claude-review), 반영, 일지 마무리(이 절 위의 후속 항목 (1)을 일지 "다음"이나 지시문에 옮긴다), 병합 전 3의 `llm_local`, 병합.
- **`llm_local` 기록은 글자대로 무효다.** 기록의 `commit`이 `7b52bbd616029d1f7edecc1b8c30b89ad4f63e6b`(dev의 끝)이고 `git diff --name-only 7b52bbd61 HEAD -- src pyproject.toml uv.lock`가 `src/agent_os/adapters/postgres/database.py`, `src/agent_os/http/database.py`, `src/agent_os/main.py`, `src/agent_os/server.py` 넷을 낸다(이 세션이 손으로 쟀다). 시험 때 작업 트리와 커밋이 같다는 근거는 새 파일의 해시 `f4c57f38a1369549`가 `git show HEAD:src/agent_os/http/database.py | sha256sum`과 같다는 것(손으로 봤다)과, 앞 세션이 잰 `database.py`의 빈 줄 한 줄 차이뿐이다. 추적 파일 셋의 해시는 이 세션이 다시 대 보지 못했다(`git diff`의 index 줄이 서식 한 줄 때문에 달라 같은 바이트로 맞출 수 없었다). 봇 회차에서 `src/`를 또 고치면 어느 쪽이든 다시 돌려야 한다. 다시 돌리면 비용 확인(최악 90분 약 $0.81, 가장 비싼 후보면 $1.77)을 사용자에게 받는다. 기록을 그대로 받아들일지는 새 세션이 `merge.md`의 3과 이 줄을 읽고 정하고, 정하지 못하면 병합 전에 사용자에게 묻는다.
- 형제: `tools/sibling_overlap.py`는 번호 겹침 없음, 헌법 3.1.4가 `origin/dev`의 3.1.3 위에 있다. 이 세션이 `origin/dev`(`0ff9e2775`)를 합쳤고 충돌은 없었다.

사용자에게 알릴 것(앞 세션 일지에서 옮김): 임시 폴더의 `inspect.py`를 `inspect.py.stray-shadows-stdlib`로 이름만 바꿨다(위 "e2e를 막은 것 둘").

이 세션(제목 `feature/03-serve-requires-database`, 인계하면 `(인계함)`)은 컨텍스트가 인계 문턱을 넘어 `PR 연 뒤`에서 새 세션에 넘긴다. 이 세션이 띄운 백그라운드 작업은 모두 끝났다(커밋의 pre-commit, `coderabbit-review` 서브에이전트). 앞 세션이 사용자에게 보인 뒤 이어받은 요청 범위는 PR과 병합까지다.

인계 지시문:

```
다음 작업: .scratch/postgres-foundation/issues/03-serve-requires-database.md. serve는 표의 판이 맞는 데이터베이스에 닿아야 뜬다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/postgres-foundation/issues/03-serve-requires-database.md
브랜치: feature/03-serve-requires-database
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: 일지 docs/journal/2026-11-20-1918-serve-requires-database.md의 "## PR 준비"와 "### 인계 직전의 상태 (PR 연 뒤)"
이어받을 상태: 인계: PR 연 뒤. PR #615(https://github.com/njh6803/agent-os/pull/615)가 열려 있고 푸시한 HEAD는 df1035ae3이다. 이 일지의 이 절에 쓴 변경(PR 준비 이후)은 커밋하지 않았다. 새 세션이 첫 @coderabbitai review 코멘트를 남기고 merge.md 2(봇 회차)부터 한다. 병합 전 3의 llm_local 기록은 글자대로 무효다(기록의 commit이 dev의 끝 7b52bbd61이고 src 파일 넷이 그 뒤 바뀌었다). 시험한 내용과 같은지를 대 본 근거와 못 댄 부분이 일지 "인계 직전의 상태"에 있다. 받아들일지 다시 돌릴지는 새 세션이 정하고 못 정하면 병합 전에 사용자에게 묻는다. 다시 돌리면 비용 확인을 받는다. 뒤로 넘길 일: 데이터베이스가 안 닿는 최대 약 35초 동안 SIGINT·SIGTERM이 먹히지 않을 수 있다는 것(일지의 외부 리뷰 항목 1)을 일지 다음에 옮긴다. 사용자에게 알린다: 앞 세션이 임시 폴더의 inspect.py를 inspect.py.stray-shadows-stdlib로 이름만 바꿨다. docs/journal/2026-11-20-1918-serve-requires-database.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-11-20T16:11:40Z

## 봇 회차와 `llm_local` 기록 판정 (2026-11-21, 이어받은 세션)

`@coderabbitai review`를 남겼고(저장소 별이 10개 미만이라 자동 리뷰는 건너뛴다), `wait_ci`가 머리 `df1035ae3`에서 모든 검사 초록(`CodeRabbit Finished`, `claude-review` 성공, `llm` 건너뜀)으로 끝났다. 두 봇 모두 이 PR의 첫 리뷰라 첫 회차다. 고친 코드는 없고, 지적마다의 판정은 PR 코멘트(`issuecomment-7044765336`)에 있다.

- CodeRabbit Major 1(`llm_local` 기록): 아래 판정으로 닫았다. Major 2(전체 pytest의 `1 failed`와 done): 그 빨강은 부하로 난 시간 단언이고 홀로 돌려 통과했으며 이 머리의 CI `python`·`verify`가 초록이라 보류했다. Minor(`STARTUP_SECONDS`): `_serving`이 쓰는 데이터베이스는 첫 시도에 닿아 재시도가 시험에 들지 않는다. Nitpick(URL 자격 증명 비교): 다른 시험이 맡는다.
- claude-review Minor 둘은 후속으로 넘겼다. 아래 "다음"에 있다.

**`llm_local` 기록 판정: 내용상 유효로 받아들이고 다시 돌리지 않았다.** 기록의 `commit` `7b52bbd61`은 글자대로는 `src` 네 파일을 건너 무효이므로 시험한 내용이 머리 `df1035ae3`와 같은지를 직접 대 봤다.
- 시험 때 작업 트리를 흉내 냈다. 임시 색인에 `7b52bbd61`의 트리를 읽고 임시 작업 폴더에 머리의 `adapters/postgres/database.py`, `main.py`, `server.py`를 두어 `git diff -- <셋>`의 sha256 앞 16자를 손으로 구했다(세션 스크래치패드의 `hashcheck.py`를 `uv run python`으로 돌렸고 커밋하지 않았다. 출력은 `HEAD 그대로: e17e3ad13774679d`와 `기록 해시와 같아지는 빈 줄(줄 번호): [79, 80]`이었다). 머리 그대로는 `e17e3ad13774679d`로, 앞 세션이 서식을 입힌 뒤 잰 값과 같다. 이 방법이 같은 값을 다시 낸다는 확인이다. `database.py`의 79·80줄 빈 줄 둘 가운데 하나를 빼면 기록의 `af6f627e40eb0cb1`과 같아진다. 빈 줄 하나(ruff format이 더한 줄) 차이뿐이다.
- 새 파일 `src/agent_os/http/database.py`: `git show HEAD:… | sha256sum` 앞 16자가 기록의 `f4c57f38a1369549`와 같다.
- `git diff 7b52bbd61 HEAD -- pyproject.toml uv.lock`은 비었고 `tools/llm_local.py`와 `tools/llm_local_server/`도 그대로다. dev에서 합쳐 들어온 변경에는 범위의 경로가 없다.
- 못 본 것: `llm_local`을 이 머리로 다시 돌려 보지 않았다. 판정은 내용이 같다는 대조에 기댄다. 봇 지적으로 범위의 경로를 또 고치면 다시 돌린다.

## 회고

후보 셋을 냈다. 승인 하나, 일지에만 남김 하나, 기각 하나, 넘김 0이다.

- **승인: 커밋하지 않은 작업 트리로 돈 `llm_local` 기록은 시험한 커밋이 기준의 끝으로 찍혀 유효 판정이 글자대로는 늘 무효다(대기열 `llm-local-record-uncommitted-tree`의 1회차).** 사건: 이 티켓의 기록이 `7b52bbd61`로 찍혀 세션 셋이 해시로 같음을 대 보았고, CodeRabbit이 첫 리뷰에서 Major로 짚었다. 층: 도구(기록에 범위 변경의 해시를 남기고 유효 판정이 그것을 견준다). 더하는 것이고 같은 실수의 첫 회차라 반영하지 않고 대기열에 둔다. operations.md의 "기록과 유효함"을 고치게 되면 ADR과 사용자 승인이 따로 필요하다고 항목에 적었다.
- **일지에만 남김: 시간 단언 시험이 부하로 빨갛다(`test_interrupt`, 관리 화면 e2e 한 사례).** 대기열 `0332`가 이 종류를 7회차까지 세고 닫은 종류의 새 사례라 항목을 잇지 않는다(회고 규칙의 "받아들여 닫은 종류"). 둘 다 홀로 돌려 통과했다.
- **기각: 임시 폴더의 떠돌이 `inspect.py`가 표준 라이브러리를 가려 e2e가 실패했다.** 다른 세션이 남긴 한 번의 환경 오염이고 이 PC에서만 난다(CI에는 없다). 앞 세션이 이름을 바꿔 치웠고 검사로 옮길 일반 입력이 아직 없다.
- **만료.** `queue_open_rows.py`와 `--ref origin/dev` 실행이 같은 다섯(470, 500, 574, 575, 581. 승인 줄의 가장 늦은 날짜 2026-11-06)을 냈다. 열린 PR #614가 같은 다섯 파일의 상태 줄을 이미 고치고 있어(`sibling_overlap`이 짚었다) 이 PR에서는 고치지 않았다. 병합 때 글자 충돌을 피한다.

## 다음

1. 이 PR(#615)이 기능 `postgres-foundation`의 마지막 티켓이라 병합하면 기능 계획의 `**끝:**` 줄이 dev에만 있고 main에 없다. 다음 일은 출시 PR이다(`next-session` `merge.md`의 "출시 PR"). 이 세션의 요청 범위가 PR과 병합까지라 열지 않았다.
2. 후속으로 넘긴 것:
   - 데이터베이스가 안 닿는 최대 약 35초 동안 SIGINT·SIGTERM이 먹히지 않을 수 있다(`CheckDatabase`의 재시도가 수명 시작 안에서 도는 동안. 외부 리뷰가 uvicorn 소스를 읽어 낸 것이고 신호를 실제로 보내 재지 않았다). 고치려면 먼저 신호를 보내 재 본다.
   - `src/agent_os/http/database.py`의 `CheckDatabase._close`가 닫는 명령과 실패 글 질의를 섞는다(claude-review Minor 1, CQS). 호출부 셋 가운데 둘은 반환값을 버린다.
   - ADR 0066의 이력에 포트 메서드가 넷(그중 둘은 예외를 글로 바꾸는 `unexpected_problem`·`close_problem`)이고 그 까닭이 원칙 IV·V라는 한 줄을 남긴다(claude-review Minor 2). ADR 이력이라 초안을 보여 주고 사용자 승인을 받는다.
   - CodeRabbit nitpick: `serve` 시험이 어댑터에 넘긴 URL의 계정·비밀번호까지 견주게 한다(실패 출력에는 비교 결과만).
   - `web/apps/admin/e2e/stack.ts`가 e2e-stack의 `prepareDatabase` 사본을 든다(위 "남긴 것").
3. 사용자에게 알린다: 앞 세션이 임시 폴더의 `inspect.py`를 `inspect.py.stray-shadows-stdlib`로 이름만 바꿨다(되돌리기는 그 이름을 원래대로).
