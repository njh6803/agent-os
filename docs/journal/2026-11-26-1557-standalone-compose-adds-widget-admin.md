# 2026-11-26 widget-admin-server 04: 단독 compose에 위젯 관리 서버를 더한다

브랜치 `feature/04-standalone-compose-adds-widget-admin`. 티켓은 `.scratch/widget-admin-server/issues/04-standalone-compose-adds-widget-admin.md`다. 이 파일은 구현 세션이 셀프 리뷰 직전에 인계하며 낸 앞부분이고, 이어받는 세션이 같은 파일에 이어 쓰고 커밋한다.

## 사용자 프롬프트

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 `.scratch/widget-admin-server/issues/04-standalone-compose-adds-widget-admin.md`다.

이어 붙은 지시문(전문은 세션 기록)의 칸은 이렇다. 다음 작업은 단독 compose를 띄우면 위젯 쪽 PostgreSQL과 위젯 관리 서버가 함께 뜨고 방문자용 포트의 `/widget-settings/<사이트 이름>`이 위젯 설정을 내는 것이다. 단계는 구현이고 새 워크트리 `04-standalone-compose-adds-widget-admin`, 브랜치 `feature/04-standalone-compose-adds-widget-admin`, 모델은 Sonnet 5.5·high다. 이번 요청의 범위는 "PR과 병합까지"이고 병합은 워크트리용 `merge.md`("워크트리에서 병합할 때")를 따른다. 티켓 03(PR 644)은 이미 dev에 들어 있다. 이 세션의 제목은 브랜치 이름이었다.

## 한 것(커밋 전, 워크트리에 있다)

범위는 수정 26개, 미추적 3개 위에 이 단락 아래의 추가분이다. 커밋은 아직 없다.

- 이미지: `deploy/images/widget-admin.Dockerfile`과 `.dockerignore`(미추적), `docker-bake.hcl`(대상 `widget-admin`, `group "default"`).
- 판 내기: `tools/release_ci.py`의 `IMAGES`, `.github/workflows/release.yml`(반복문 셋, `--grype`, 첫째 잡의 출력, 둘째 잡의 `DIGEST_*`, 아티팩트 대조, 번호 태그 반복문의 하이픈 고침 `tr - _`). `.github/workflows/ci.yml`은 주석 둘만 고쳤다.
- 배포 파일: `compose.yaml`(서비스 셋, 볼륨 `widget-database`, 세 곳 모두 `${WIDGET_ADMIN_DATABASE_PASSWORD:?…}`), `proxy/site.conf`(상류 `up_widget_admin`, location `/widget-settings/`와 `= /widget-settings`), `.env.example`, 배포 안내 `README.md`(3-1, 4, 7, 8, 9, 11, 12, 13절).
- 시험: `tests/tools/test_deploy_guide.py`(위젯 쪽 PostgreSQL 전제·권한, 13절 표 대조, ports·user 없음, 그리고 이 세션의 마지막 추가분 아래), `tests/test_postgres_image_pin.py`(PostgreSQL 서비스 둘이 같은 digest), `tests/tools/test_release_ci.py`, `tests/tools/test_release_workflow.py`(워크플로의 이름 목록 맞대기와 bash 반복문 실행), `tests/tools/test_check_notes.py`, `tests/test_postgres_migration_shape.py`.
- 노트: `tools/check_notes.py`의 `PRODUCT_MIGRATION_FOLDERS`(폴더 둘, 꼴 시험이 이 값 하나에서 폴더를 읽는다), `docs/release-notes/upgrade/widget-admin-server.md`(올릴 때 할 일, 미추적), `docs/release-notes/features/widget-admin-server.md`(기능 단락, 미추적), `.scratch/widget-admin-server/plan.md`에 `**끝:** 2026-11-26`(이 티켓이 기능의 마지막이다. 02는 이미 done).
- 문서: `docs/constitution/tech.md`(레지스트리·CI 칸 "넷"을 "다섯"으로), `operations.md`, `README.md`(헌법 판 3.1.9), 루트 `README.md`.
- 단독 배포 e2e: `web/packages/e2e-standalone/e2e/{stack,deployment.e2e,env,migrations,migrations.test}.ts`, `playwright.config.ts`(위젯 관리 서버 사례 여덟, 이미지 다섯 짓기, 위젯 쪽 `psql`, 마지막 판 번호를 두 폴더에서 읽기).
- 티켓: 체크박스를 닫고 `Status: done`으로 바꿨다. "사람이 할 일" 칸 하나는 일부러 열어 두었다(사람이 Docker Hub에서 공개 저장소를 만든다). `uv run python tools/plan_table.py`를 돌렸다.

## 이 세션이 번복하거나 고친 것

- 번호 태그 반복문: 하이픈이 든 이미지 이름이 셸 변수 이름이 되지 못해 `tr - _`로 `DIGEST_WIDGET_ADMIN`을 만든다. 이미지·짓기 대상·저장소 이름은 `widget-admin`과 `agent-os-widget-admin` 그대로다. 이 PC의 Git Bash에서 그 반복문을 실제로 돌려 다섯 이름이 풀리는 것을 시험(`tests/tools/test_release_workflow.py`)이 본다. 리눅스 bash에서 돈 것은 아직 없다. CI가 본다.
- 목록 맞대기 시험의 변이가 처음에는 합집합에 가려 하나를 빼도 안 빨개졌다. 반복문마다 키를 따로 두고 치환으로 하나씩 빼게 고쳤다.
- 이미지 pin 시험이 처음에는 위젯 쪽을 같이 바꿨다. Agent OS 쪽만 보게 `widget=OLD`로 떼어 냈다.
- e2e에서 TypeScript의 `as unknown`은 원칙 III가 금지한다. 주석을 단 `const x: unknown = JSON.parse(...)`로 고쳤다.
- 이 세션의 마지막 추가분(커밋 전, 미리 알려 두는 것): `:?` 필수 표시를 지키는 자동 시험이 없다는 것을 변이로 알았다. compose의 `${WIDGET_ADMIN_DATABASE_PASSWORD:?…}` 한 곳을 `${…}`로 바꿔도 119개 시험이 모두 통과했다. 그래서 `tests/tools/test_deploy_guide.py`에 `필수_표시_없는_위젯_비밀번호`와 시험 셋(저장소 상태, 필수 표시 하나 빠짐, 읽는 곳 하나 빠짐)을 더했다. 같은 변이를 실제 compose에 다시 넣으니 이번에는 종료 1이고 `가 없는 참조` 줄이 났다. 프록시도 `/widget-settings/` 위치의 규칙(`add_header`·`limit_req` 없음, 위젯 관리 서버로 넘기는 줄은 그 위치의 한 줄뿐)을 지키는 시험이 e2e뿐이라 `프록시의_위젯_설정_문제`와 시험 넷을 더했다. 이 시험들은 변이를 문자열 치환으로 넣어 본 것이고(파일에 넣은 것은 첫 변이뿐이고 되돌렸다), `-k "프록시 or 세_곳 or 위젯_쪽_비밀번호"`로 거른 시험 여덟(새 시험 일곱과 이름이 걸린 기존 하나로 짐작한다. 세어 보지는 않았다)이 통과했고 pyright와 `check_type_escapes`도 초록이다. 프록시 쪽 변이(`add_header`, 둘째 `proxy_pass`)는 실제 `site.conf`에 파일로 넣어 보지 않았다.

## 개발 PC에서 실제로 친 것

- 단독 배포 e2e: `pnpm -C web/packages/e2e-standalone exec playwright test`, `21 passed (4.0m)`, 종료 0. 시작과 끝의 `date +%s` 차이가 240초다. 이미지 다섯을 지었지만 serve와 위젯 관리 서버의 계층 캐시가 따뜻했다. 위젯 사례 여덟(넣은 설정의 200과 열린 머리 셋, 등록되지 않은 이름·`%2F`·끝의 `%0A`의 404 봉투와 머리 셋, `down` 뒤 `up`에도 남는 값, `widget-admin-migrate`의 `Exited (0)`과 위젯 쪽 `alembic_version`, uid 10001과 묶음 판, 호스트 포트 셋, 프록시가 끊는 네 경로, 루프백 진단)가 모두 든다.
- 시간 견줌(어림): 이미지마다 캐시 없이(`--no-cache`) 하나씩 지었다. 위젯 관리 서버 26초(바탕 이미지는 로컬에 있었고, 같은 시간에 `run_checks.py`가 돌고 있었다), 위젯 테스트 페이지 54초, serve 100초, 관리 화면 163초, 위젯 191초. 가장 오래 걸린 위젯 191초가 `BUILD_MS` 15분(900초)의 약 21%다(다섯이 나란히 돌면 더 걸릴 수 있다). e2e 전체 4.0분(캐시가 따뜻했다)은 CI `e2e-standalone`의 20분과 견줘 여유가 5배이고, 그 20분 주석이 적은 6배 남짓보다 줄었다. 위젯 관리 서버 이미지 26초가 판 내기 `build`에 더해도 30분 한도에는 크게 못 미친다. 제한은 올리지 않았고, 20분 주석에 이미지가 넷일 때의 측정이라는 말과 다섯째 이미지의 어림을 덧붙였다. 티켓이 줄어 보이면 사람에게 알리라고 했으므로 PR 본문과 보고에 싣는다. 이 PC의 시간은 CI 리눅스의 시간이 아니다.
- 리눅스 bash: 워크플로의 `var="DIGEST_$(… | tr - _)"` 줄로 시험과 같은 스크립트를 만들어 Debian 파이썬 이미지(`python@sha256:5e2bdb1b…`, bash 5.2.37, Linux 6.18)에서 돌렸다. 다섯 이미지 모두 `이름=value-이름`으로 풀렸다(`widget-admin=value-widget-admin` 포함).
- 비밀번호 줄이 빠진 `.env`(앞선 컨텍스트에서 쳤다): `docker compose config`와 `up -d`가 그 이름을 든 글로 종료 1이고 컨테이너가 하나도 생기지 않는다.
- 배포 안내 9절(`docker compose pull` 한 줄만 뺐다. 로컬 이름공간이라 레지스트리에 없다): 묶음을 `tools/release.py bundle --number 0.0.1 --namespace agent-os-hand`로 짓고 이미지 다섯을 로컬에서 지은 뒤 풀어 띄웠다. `config --images`가 일곱 줄(우리 이미지 다섯, `nginx@`, `postgres@`)을 냈고 `save.txt`에 `agent-os-proxy:local`과 `agent-os-postgres:local`이 들었다. `docker save` 종료 0, `sha256sum -c`가 `OK`, 태그를 지운 뒤 `docker load`로 되살려 `이미지가 같다`가 떴다. 덮어쓰기 파일(`proxy`, `postgres`, `widget-admin-postgres` 셋)을 만들어 `up -d --wait`가 종료 0이고 `proxy`와 `postgres` 둘과 `widget-admin-postgres`가 `agent-os-*:local` 이미지로 돌았다. 안내의 글자를 바꾸지 않았다.
- 배포 안내 12절의 위젯 쪽 네 줄(데이터가 있는 위젯 쪽 볼륨에서): `.env`의 새 값으로 바꾼 뒤 그대로 쳤다. 종료 0, 40초, `Enter new password for user "widget_admin":` 두 줄이 찍혔고 `/widget-settings/handsite`가 바꾸기 전과 뒤 모두 200이며 넣어 둔 값(`손 검증`)이 그대로다. `widget-admin-migrate` 로그는 `표가 이미 마지막 판(0001)입니다.`다. 손 검증용 스택·볼륨·이미지는 지웠다.
- 손 검증용 파일은 스크래치패드 `.../scratchpad/hand/`(채우기 `fill.ts`, `build.sh`, `up.sh`, `pw.sh`, `sec9.sh`)에 있고 저장소에 싣지 않는다.

## 검증

`uv run python tools/run_checks.py`(백그라운드)의 결과: check-ticket, check-notes, zizmor, lint-imports, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest(930.5초)가 통과했고 web-verify만 `deployment.e2e.ts`의 prettier 서식으로 빨갰다. `prettier --write`로 고친 뒤 `pnpm -C web verify`가 종료 0이다. `uv run ruff check .`와 `uv run ruff format --check .`가 초록이다. 위의 마지막 추가분 이후에는 해당 시험 파일의 ruff·pyright와 `check_type_escapes`, 이름으로 거른 새 시험만 다시 쳤고 전체 `run_checks.py`는 다시 치지 않았다(커밋의 pre-commit이 돌린다). `-m llm` 계열은 이 티켓이 LLM 시험의 범위(`operations.md` LLM 테스트)를 건드리지 않아 치지 않았다. 옛 표현("이미지 넷" 따위)은 `git grep`으로 기록 밖에서 다시 찾아 둘만 남았다. `docs/release-notes/features/release-image.md`(그 기능의 단락)와 `tests/tools/test_release_workflow.py` 머리 독스트링(지난 사고의 기록)이고 둘 다 고치지 않는다.

## 셀프 리뷰(`/code-review origin/dev`)

범위: 기준 `d211b37c4`, 파일 28개, 커밋 0개, 미추적 5개. 표준 축은 sonnet·high, 명세 축은 이 세션의 모델로 돌렸다. 이 세션이 인계하지 못해(`open-session` 호출이 거부됐다) 같은 세션에서 이었다.

고친 것(지적을 코드에서 먼저 재 보았다):

- 올리는 노트와 11절이 프록시를 다시 읽히는 일을 빠뜨렸다(명세 축 Major). 임시 compose로 `up -d --no-deps proxy`를 쳐서 위젯 비밀번호만 바꿔도 `Running`으로 남는 것을 봤다. 노트에 4단계(6절의 두 명령)를 더하고 11절에 항목을 더했다. 같은 시험에서 `docker compose config --hash`는 무관한 변수만 더해도 `proxy` 해시가 달라져 근거로 쓸 수 없었다.
- 12절의 "Agent OS 쪽 `serve`는 멈추지 않습니다"는 거짓이었다(명세 축 Major). 같은 방법으로 `serve`(`env_file: .env`)는 위젯 비밀번호만 바꿔도 `Recreated`였다. 문장을 "마지막 줄의 `up -d`가 `.env`를 통째로 받는 `serve`도 다시 만들므로 Agent OS 쪽 요청도 몇 초 끊깁니다"로 고쳤다.
- 12절과 13절이 "위젯이 '위젯 설정을 받아 오지 못했습니다.'를 보입니다"를 지금 동작으로 적었다(표준 축 Major). `web/`에 `/widget-settings`를 부르는 위젯 코드가 없다(`widget-login-state`가 todo). 위젯이 이 경로를 읽는 기능이 들어온 뒤의 동작이라고 한정했다. 시험이 강제하는 낱말 `위젯 설정을 받아 오지 못했습니다.`는 남았다.
- `widget-admin.Dockerfile` 머리 주석이 "test_release_ci.py 가 같은지 본다"고 적었으나 그런 시험이 없었다(두 축 Major). `tests/tools/test_release_ci.py`에 `serve.Dockerfile`과 `PYTHON_IMAGE`·`UV_IMAGE`가 같은지 보는 시험과 변이 시험을 더했다.
- 티켓의 "리눅스 bash에서 한 번 돌려 일지에 적는다"가 근거 없이 닫혀 있었다(명세 축 Major). 위 "리눅스 bash" 줄대로 돌렸다.
- 이미지마다 짓는 시간이 둘뿐이었다(명세 축 Major). 나머지 셋은 캐시 없이 손으로 지어 시간을 적었다(위 시간 견줌 줄. 커밋한 프로브가 아니라 스크래치패드 스크립트로 한 번씩 돌렸다). `ci.yml`의 20분 주석에 이미지가 넷일 때의 값이라는 말을 덧붙였다.
- `docs/constitution/tech.md`의 "최종 사용자 접두사와 위젯만 넘기며"가 `/widget-settings/` 때문에 거짓이 되어 고쳤다(표준 축 Minor).
- 반복문 변이 시험이 셋 중 첫째만 뺐다. 이제 셋을 하나씩 뺀다(표준 축 Minor).
- `REQUIRED`의 `widget-admin-postgres:`가 13절의 `widget-admin-postgres:5432`에도 맞았다. 9절 덮어쓰기 예의 두 줄(`widget-admin-postgres:`와 `image: agent-os-postgres:local`)로 좁혔다(명세 축 Minor).

남긴 것과 이유:

- `PRODUCT_MIGRATIONS`를 두 폴더로 바꾸라는 티켓 문구(명세 축 Minor): 그 이름은 `tests/tools/test_check_notes.py`가 폴더 하나의 문자열로 읽는다. 새 이름 `PRODUCT_MIGRATION_FOLDERS`가 폴더 목록의 원천 하나가 되어 티켓의 목적(원천 하나)은 이뤄진다.
- `docs/release-notes/features/release-image.md`의 "이미지 넷"(표준 축 Minor): 그 기능이 나왔을 때의 사실을 적은 기록이다.
- `test_release_workflow.py`의 `_bash()` 하드코딩(두 축 Nit): 윈도 경로가 실제로 있을 때만 쓰고 없으면 `PATH`의 `bash`로 넘어가 리눅스에서도 돈다.
- `위젯_관리_서버의_멈출_때의_글`과 `제품의_멈출_때의_글`의 중복, `STANDALONE_POSTGRES_COUNT`, `"0001_sites.py"` 이름, 되풀이 단언(표준 축 Nit)과 13절 표의 설명 줄(명세 축 Nit): 지금은 두지 않는다. 고칠 만큼 같은 실수가 쌓이면 그때 합친다.
- 범위 넘침으로 본 `필수_표시_없는_위젯_비밀번호`와 `프록시의_위젯_설정_문제`(명세 축 Nit): 티켓의 두 기준을 자동으로 지키는 보강이라 둔다.

PR 직전 리뷰에 밀 주장(이 반영으로 새로 쓴 사실 문장, 원문):

- 올리는 노트: "프록시 컨테이너는 정의가 그대로라 `up -d`가 다시 만들지 않고, 묶음의 `proxy/site.conf`는 읽는 폴더에 얹혀 있을 뿐이라 그대로는 옛 설정으로 답합니다."와 "이 단계를 빠뜨리면 `/widget-settings/<사이트 이름>`이 기본 경로의 404로 답합니다."
- 배포 안내 12절: "마지막 줄의 `up -d`는 `.env`를 통째로 받는 `serve`도 다시 만들므로(`.env`의 어느 줄이 바뀌어도 그렇습니다), 그동안 Agent OS 쪽 요청도 몇 초 끊깁니다."
- 배포 안내 11절: "`docker compose up -d`는 프록시 컨테이너의 정의가 그대로면 다시 만들지 않으므로, 두 명령을 치기 전까지 프록시는 옛 설정으로 답합니다."
- `ci.yml`: "이 측정은 이미지가 넷일 때의 것이다. … 20분의 여유는 5배 남짓으로 줄었다고 어림한다"
- `tech.md`: "최종 사용자 접두사와 위젯, 위젯 설정(`/widget-settings/`)만 넘기며"

다시 돌린 명령: 시험 여섯 파일(`test_release_ci`, `test_release_workflow`, `test_deploy_guide`, `test_check_notes`, `test_postgres_image_pin`, `test_postgres_migration_shape`) 285개가 통과했다(251초). 세 시험 파일의 `ruff check`와 `ruff format --check`가 초록이다. 전체 검사는 커밋의 pre-commit이 돈다.

## PR 직전 리뷰(CodeRabbit CLI)

`coderabbit-review` 에이전트는 CLI가 도는 동안 턴 한도(40)에 닿아 보고 없이 끝났다(결과 파일이 0바이트였다). 그러나 CLI 자체는 리뷰를 마치고 결과를 로컬에 저장해 두었고, `coderabbit review findings`로 꺼냈다(4건, 기준 `origin/dev`).

- major, `deploy/standalone/compose.yaml:158`(질문): 새 이미지의 최종 단계에 `/etc/agent-os/image`가 있는가. 있다. `widget-admin.Dockerfile` 58행이 최종 단계(`FROM … AS widget-admin`)에서 root 소유로 굽는다. 고칠 것 없음(종료 1로 재시작을 반복하는 일은 없다. 표지가 없을 때 시작하지 않는 쪽은 e2e의 "루프백이 아닌 주소에 묶으려는 위젯 관리 서버" 시험이 본다).
- minor, `deployment.e2e.ts:600`: 재기동 시험이 앞선 시험의 `insertWidgetSite()`에 기댄다. 맞다(`--grep`으로 이 시험만 돌리면 404). 시험 안, `down` 앞에서도 `insertWidgetSite()`를 부른다(이미 있으면 그대로 두는 문이라 겹쳐도 안전하다).
- minor, `test_deploy_guide.py:677`: 넘기는 줄을 `/widget-settings/` 위치 밖으로 옮기고 빈 위치를 남기면 문제 0으로 지나간다. 맞다. 위치 안에 그 줄이 있는지도 보게 했고, 줄을 다른 위치로 옮긴 변이 시험을 더했다.
- minor, `test_release_ci.py:425`: 변이가 digest가 `5`로 시작한다는 데 기댄다. 맞다. 지금 박힌 값을 읽어 마지막 글자 하나를 바꾸게 했다.

다시 돌린 명령: `test_deploy_guide.py`와 `test_release_ci.py` 114개 통과, 두 파일 `ruff check`·`ruff format --check` 초록. TS 쪽(`deployment.e2e.ts`)은 커밋의 pre-commit(`pnpm -C web verify`)이 돈다. e2e는 이 한 줄 추가 뒤 다시 돌리지 않았다.

## 첫 커밋 시도의 pre-commit 실패와 고침

첫 커밋은 pre-commit의 변이 표 확인(`tools/mutate.py --staged`)에서 막혔다(나머지 검사는 708초 안에 모두 통과). `tools/check_notes.py`의 `PRODUCT_MIGRATIONS` 줄을 `PRODUCT_MIGRATION_FOLDERS`로 바꾸자 `.scratch/postgres-foundation/probes/migration_guard_mutations.toml`의 변이 둘(4번, 5번)이 원문으로 쥔 줄이 사라졌다. 이 표가 가리키는 파일을 고쳤는데 표를 같이 보지 않은 것이다. 고친 것: 두 변이의 `old`를 새 줄에 맞췄다. 4번은 처음에 `new`가 위젯 폴더까지 빼서 위젯 시험이 먼저 빨개지고 고르려던 표지(`env.py` 문구)가 나오지 않았다. 그래서 `new`가 위젯 폴더는 그대로 세게 고쳤다. 위젯 폴더를 목록에서 빼는 6번 변이를 더했다. `--staged` 문제 0, 4·5·6번 모두 기대대로 빨강이다.

## 남은 것(이어받는 세션이)

이 절은 인계 때 쓴 것이다. 셀프 리뷰는 위 절대로 마쳤다.

1. 먼저 `git fetch origin`. `origin/dev`가 이 브랜치의 기준(`d211b37`)보다 앞서 있다(2026-11-26 15:57에 `36c1f5d`). 합친 뒤 저장소 상태 시험(`test_이_저장소의_…`)과 `tools/check_notes.py`를 돌리고, 새 ADR이나 헌법 판이 같은 번호를 가져갔는지 `uv run python tools/sibling_overlap.py`로 본다(헌법 판은 지금 3.1.9로 올렸다).
2. 셀프 리뷰 두 축을 돌려 Critical·Major를 고친다. 이어 PR 직전 `coderabbit-review`(CLI가 막히면 `bug-perf-review`)를 돌린다. 이 변경이 `tools/release_ci.py`와 워크플로를 고쳤으므로 리뷰 브리프에 이 일지의 "고친 것"의 사실 문장(하이픈 고침, 한 곳만 바꾼 변이)을 밀 주장으로 넘긴다.
3. 커밋(Bash heredoc이나 `git commit -F`, 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`), 푸시, PR. 제목은 느낌표를 붙인다(예: `feat!: 단독 compose에 위젯 관리 서버와 위젯 쪽 PostgreSQL을 더한다 (widget-admin-server 04)`). PR 본문에 위젯 쪽 `.env` 줄과 compose 교체가 필요한 점, 개발 PC에서 친 9절·12절 결과, e2e 시간 견줌, 그리고 아래 "사람에게 알릴 것"을 싣고 끝에 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`를 붙인다. PR을 열면 `get_status`로 확인하고 필요하면 `bind_pr`한 뒤 Auto-fix를 제안한다.
4. 병합은 워크트리용 `merge.md`("워크트리에서 병합할 때")를 Read로 열어 따른다. 요청 범위가 병합까지이므로 묻지 않고 한다. 병합 직전에 기준 브랜치를 한 번 더 합치고 저장소 상태 시험을 돌린다(이 티켓이 기능의 마지막이므로 `**끝:**` 줄과 기능 단락이 이미 든 채로).
5. 회고(`retro`)는 단계를 닫는 세션이 이 일지까지 읽고 돈다. 후보로 볼 만한 것: 시험이 자동으로 지키는 것과 e2e·손 검증만 지키는 것 사이의 틈(`:?` 필수 표시를 지키는 시험이 없었던 것, 같은 postgres-foundation 02에서 같은 기준을 손 검증으로만 뒀다). 이 세션이 메워 둔 것을 어떻게 볼지는 retro가 정한다.

## 사람에게 알릴 것

이 티켓이 든 판을 처음 내기 전에, Docker Hub의 계정 아래에 공개 저장소 `agent-os-widget-admin`을 사람이 먼저 만들어야 한다. 만들기 전에 판을 내면 올리기가 실패한다. PR 본문과 보고에 싣는다.

## 이 세션의 제목

`feature/04-standalone-compose-adds-widget-admin`(인계하며 `feature/04-standalone-compose-adds-widget-admin (인계함)`으로 바꿨다. 잠금도 풀었다).

open-session을 부른다 2026-11-26T06:59Z
인계 못함 셀프 리뷰 직전: open_session.ps1 호출이 자동 허용 분류기에 거부됐다(2026-11-26T07:00Z UTC, 이유 `Unsanctioned Communication`. 티켓 03 세션과 같은 거부다). 제목을 되돌렸고 이 세션에서 셀프 리뷰부터 잇는다. 워크트리 잠금은 이미 풀었고 다시 잠그지 않았다.
