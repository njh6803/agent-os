# 2026-11-24 (16:37) 위젯 관리 서버의 명세 (widget-admin-server)

파일 이름의 시각은 이 일지를 만든 때다. 세션은 그보다 앞서 시작했다.

## 사용자 프롬프트

> 사용자: `/to-spec widget-admin-server`

지시문 없이 연 세션이다. 설계 인터뷰는 portal-admin의 설계(일지 2026-11-15-1312)와 ADR 0064가 끝냈고, Agent OS 쪽 데이터베이스의 도구와 시험 방법은 ADR 0066이 정했다.

## 시작 전 확인

- 나란히 도는 세션을 봤다(`ListAgents`, `list_sessions`). widget-admin-server를 맡은 세션은 없었다. `uv run python tools/sibling_overlap.py`는 "번호 겹침 없음", "함께 고친 파일 없음"이었다.
- 주 체크아웃에서 `EnterWorktree(name=widget-admin-server-spec)`로 들어와 브랜치를 `docs/widget-admin-server-spec`으로 바꿨다. 기준은 `origin/dev`의 `7770ac0c1`이다.
- 기능 계획 `.scratch/widget-admin-server/plan.md`, ADR 0064 전문, ADR 0066의 결정 "serve와 데이터베이스"부터 "위젯 관리 서버"까지를 읽었다. 코드(테스트 도우미와 마이그레이션과 경계 검사), 웹·이미지·출시 도구, 앞선 명세 넷과 용어집은 서브에이전트 셋이 읽어 보고했다.

## 손으로 본 것

- 하위 폴더의 `conftest.py`가 `tests/database.py`의 픽스처 함수를 다른 접두로 불러 같은 이름의 픽스처를 지으면, 그 폴더의 시험은 그 접두의 데이터베이스를, 뿌리의 시험은 `agent_os` 접두의 데이터베이스를 받았다. 임시 파일 `tests/zz_override_check/conftest.py`(접두 `wa_probe`, 하는 일이 없는 마이그레이션 함수), `tests/zz_override_check/test_child.py`, `tests/test_zz_override_parent.py`를 두고 `uv run pytest -q -s -p no:cacheprovider tests/zz_override_check tests/test_zz_override_parent.py`와 같은 명령에 `-n 2`를 붙여 쳤다. 둘 다 3 통과였고, 찍힌 이름은 `wa_probe_test_…`, `wa_probe_template_…`, `agent_os_test_…`, `agent_os_template_…`였다. 임시 파일은 지웠다.
- 생성 클라이언트가 쓰는 `openapi-fetch` 0.17.0은 본문이 없는 요청에 `Content-Type`을 붙이지 않는다(주 체크아웃의 `web/node_modules/.pnpm/openapi-fetch@0.17.0/node_modules/openapi-fetch/dist/index.mjs` 60~63줄, 코드를 읽었다). `Accept`도 붙이지 않는다(같은 파일을 grep해 0건).
- 단독 배포 e2e(`e2e-standalone`)는 CI에서 main으로 가는 PR과 main 푸시에서만 시험하고 다른 때는 첫 스텝이 건너뛴다(`.github/workflows/ci.yml`의 그 잡, 코드를 읽었다).

## 사용자에게 물은 것과 답

시험 경계를 확인받는 물음 하나와, 명세가 혼자 정하기에 대가가 큰 갈림 둘을 한 화면으로 물었다. 화면의 사실을 대 보라는 훅이 두 번 막았고(질문 문장을 고쳐 새 화면이 됐다), 그 사이에 CI의 그 잡과 프록시 설정(`limit_req_status 429`, 토큰 주소의 `rate=30r/m`과 `burst=10`)과 의존성 목록을 대 보고 첫째 질문 문장을 고쳤다.

### 1. 시험 자리

> 질문: 위젯 관리 서버를 어느 자리에서 시험할까요? 파이썬 시험은 진짜 데이터베이스(테스트 컨테이너)에 위젯 설정을 직접 넣고 서버를 HTTP로 불러 답을 보는 시험이고, 커밋마다 돕니다. 단독 배포 e2e는 배포 파일 묶음을 진짜 이미지로 띄워 앞단 프록시를 지나 부르는 시험이고, CI에서는 main으로 가는 PR에서만 돌며 배포 파일을 건드린 티켓은 손으로 칩니다.
>
> - 파이썬 시험과 단독 배포 e2e (Recommended): 답의 모양, 등록되지 않은 사이트의 답, 다른 출처에 여는 머리, 시작 검사는 파이썬 시험이 봅니다. 공개 주소의 경로가 프록시를 지나 닿는지와 compose를 내렸다 올려도 값이 남는지는 단독 배포 e2e가 봅니다. 계약 파일과 생성 클라이언트가 코드와 같은지도 검사합니다. 대가는 그 e2e가 이미지 하나를 더 지어 그만큼 길어진다는 것입니다(얼마나 길어지는지는 재지 않은 어림입니다).
> - 파이썬 시험만: 프록시 설정, 이미지, compose는 시험하지 않습니다. 내렸다 올려도 값이 남는지는 파이썬 시험이 서버 프로세스를 껐다 켜서 봅니다. 시험은 짧지만, 프록시의 경로 줄이나 compose의 서비스가 틀려도 자동 시험으로는 드러나지 않습니다.

> 사용자: 파이썬 시험과 단독 배포 e2e (Recommended)

### 2. 설치 묶음

> 질문: 위젯 관리 서버의 파이썬 코드를 Agent OS와 같은 설치 묶음에 넣을까요? 설치 묶음(휠)은 파이썬 프로그램을 깔 때 쓰는 파일 하나이고, 지금은 pyproject.toml 하나가 agent_os 패키지 하나를 담습니다.
>
> - 한 묶음에 패키지 둘 (Recommended): pyproject.toml 하나에 widget_admin 패키지와 widget-admin 명령을 더합니다. 의존성 잠금과 판 번호가 하나이고, 검사 도구(pyright, pytest, ruff)의 설정은 거의 그대로입니다. 두 패키지가 서로 import하지 못하게 하는 것은 import-linter가 막습니다. 대가는 위젯 관리 서버의 이미지에도 Agent OS의 코드와 쓰지 않는 의존성(모델 SDK, MCP, LangChain 등)이 함께 들어 이미지가 그만큼 커진다는 것입니다.
> - 묶음을 둘로 나누기: 저장소 안에 pyproject.toml을 하나 더 두어(uv 워크스페이스) 위젯 관리 서버의 의존성을 따로 적습니다. 이미지가 작고 나중에 떼어 내기 쉽습니다. 대가는 검사 도구, 이미지 빌드, 판 번호를 넣는 출시 도구를 두 묶음에 맞춰야 하고, 그 조합이 서는지를 명세가 먼저 재야 해서 명세와 첫 티켓이 길어진다는 것입니다.

> 사용자: 묶음을 둘로 나누기

추천과 다른 답이다. 그래서 명세가 두 묶음의 조합(uv 워크스페이스에서 검사 도구, 시험, 이미지 빌드, 판 번호를 넣는 길)을 재고 나서 Implementation Decisions를 쓴다(to-spec 3단계의 측정 규칙).

### 3. 요청 제한

> 질문: 누구나 읽는 위젯 설정 주소에 요청 수 제한을 둘까요? 위젯은 뜰 때마다 이 주소를 한 번 부르고, 서버는 부를 때마다 데이터베이스를 한 번 읽습니다. 제한은 앞단 프록시가 접속 주소(IP)마다 세므로, 회사처럼 여러 사람이 한 IP로 나가는 곳에서는 그 사람들이 한 몫을 나눠 씁니다.
>
> - IP마다 넉넉히 제한 (Recommended): 초당 10번, 한꺼번에 50번까지 몰려도 받고, 넘으면 429로 답합니다. 한 곳에서 쉬지 않고 부르는 것을 막습니다. 대가는 한 IP 뒤에서 아주 많은 사람이 같은 순간에 페이지를 열면 일부 위젯이 '위젯 설정을 받아 오지 못했습니다'를 보일 수 있다는 것입니다(수는 어림입니다).
> - 제한하지 않기: 회사 네트워크에서 막힐 걱정이 없습니다. 대가는 한 곳에서 쉬지 않고 부르면 그만큼 데이터베이스가 읽힌다는 것입니다.
> - 토큰 주소와 같게: 위젯 테스트 페이지의 토큰 주소처럼 IP마다 분당 30번, 한꺼번에 10번까지입니다. 규칙이 하나로 맞지만, 한 IP 뒤에서 1분에 30번 넘게 페이지를 열면 막힙니다.

> 사용자: 제한하지 않기

추천과 다른 답이다.

## 두 묶음의 측정

명세의 Implementation Decisions를 쓰기 전에 `.scratch/widget-admin-server/probes/uv_workspace/run.py`를 세 번 돌렸다. 결과와 갈래와 재지 못한 것은 그 폴더의 `README.md`가 원천이고, 여기에는 실행의 차례만 적는다.

- 첫 시도는 세션 스크래치패드 아래의 사본 나무에서 윈도의 경로 길이 한도에 걸려 풀지 못했다. 사본 나무를 `C:/project/uvws<번호>`로 옮겼다.
- 첫 실행(`C:/project/uvws1`)은 pyright의 `extraPaths`를 적지 않은 설정이라 `widget_admin`의 스텁 없음 진단 5건이 났다.
- 둘째 실행(`C:/project/uvws2`)은 멤버의 `src`만 적은 설정이라 `agent_os`의 같은 진단 269건이 났고, ruff 묶음 판정 회차가 캐시 때문에 측정 아님이었다.
- 셋째 실행(`C:/project/uvws3`)은 `extraPaths`에 루트와 멤버의 `src`를 함께 적고 앞의 두 설정을 대조 회차로 남겼으며, ruff 회차에 `--no-cache`를 붙였다. 측정 29회차, 측정 아님 0회차로 0으로 끝났다.

사본 나무 넷(`C:/project/uvws1`, `C:/project/uvws2`, `C:/project/uvws3`, 스크래치패드 아래의 첫 시도)은 프로브가 지우지 않으므로 사람이 손으로 지운다. 프로브가 이미지 둘(`uv-workspace-probe/widget-admin:probe`, `uv-workspace-probe/serve-sync:probe`)을 남겼다(`docker image ls`로 손으로 봤다. 대조 이미지는 짓기가 실패해 남지 않았다).

## 손으로 본 것(이어서)

- 테스트 컨테이너에서 `docker compose -f compose.test.yaml exec -T postgres createdb -U agent_os <이름>`이 0으로 끝났고, 같은 이름으로 다시 치면 `database "…" already exists`와 1이었다. 만든 데이터베이스는 곧 `dropdb`로 지웠다. 명세 "개발 PC에서 붙는 데이터베이스"가 README에 적을 명령이다.

## 셀프 리뷰 전에 고친 것

명세를 쓴 뒤, 셀프 리뷰를 부르기 전에 이 세션이 스스로 고친 것이다.

- 서두의 수. "거부한 안:" 문단은 열일곱이 아니라 열두 자리였고 든 안은 스물넷이 아니라 스물하나였으며, 사용자에게 보인 선택지 가운데 고르지 않은 것은 셋이 아니라 넷이었다(grep으로 세었다). ADR 0064 Consequences "명세가 짓는 것"의 "셋을 더 적는다"를 한 행에 묶었던 것을 세 행으로 나눠 넘겨받은 것이 서른세 행이 됐다. "사용자가 골랐다"가 Further Notes에도 한 번 있어 그 자리를 절 이름으로 바꾸고, Testing Decisions 머리에 그 표시를 붙였다. 표시 없는 절의 목록에 "사람이 할 일"을 더했다.
- 수명 구동자 `LifespanDriver`의 자리. `tests/test_server.py`가 아니라 `tests/fake_database.py`였다(Grep으로 찾았다).
- pyright `extraPaths`의 해석을 잰 판과 설정의 범위로 좁혔다(프로브 README와 명세 둘 다).
- portal-admin 명세의 "저장 경로"를 읽고 Further Notes를 고쳤다. 그 명세는 접두사를 이 명세에 맡기고 운영자용 경로 일곱을 한 머리 아래에 모을지를 그 계약 티켓에 맡겼다. `/operator/`를 정하면 그 갈림이 좁혀진다고 적고, 같은 것을 portal-admin 기능 계획에 넘겼다.
- 이력 없음의 첫째 근거에 ADR 0064 Consequences "운영"의 "아홉"도 Agent OS 쪽 `migrate`를 세지 않았다는 것을 더했다.

## 인계

셀프 리뷰를 부르자 인계 계기(`셀프 리뷰 직전`, 컨텍스트 297,657 토큰)가 와서 `next-session` `handoff.md`대로 넘긴다. 셀프 리뷰는 새 세션이 한다. 이 세션의 지금 제목은 `docs/widget-admin-server-spec`이다. `get_session`의 `self`에 PR 629가 묶여 있었는데 그 PR은 dev를 main에 낸 출시 PR(머리 `dev`)이라 이 일과 무관하다.

```
다음 작업: 기능 widget-admin-server. 위젯 관리 서버의 명세를 셀프 리뷰하고 커밋한 뒤 PR을 열어 병합한다
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec widget-admin-server
브랜치: docs/widget-admin-server-spec
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-24-1637-widget-admin-server-spec.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review origin/dev, 미추적 파일 포함)부터 한다. 명세와 프로브 README 둘, 기능 계획 셋(widget-login-state, portal-admin, ops-backup-upgrade)에 넘긴 문단을 다 썼고 tools/plan_table.py는 돌려 바뀐 것이 없었다. 서두의 수는 리뷰 직전에 다시 셌다. 이력이 없어 ADR 승인은 없다. 끝에 사람에게 사본 나무 넷(C:/project/uvws1, C:/project/uvws2, C:/project/uvws3, 앞 세션 스크래치패드의 uvws-1)과 프로브 이미지 둘(uv-workspace-probe/widget-admin:probe, uv-workspace-probe/serve-sync:probe)을 지우라고 알린다. 일지 docs/journal/2026-11-24-1637-widget-admin-server-spec.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-11-24T09:01:06Z

## 이어받은 세션: 셀프 리뷰부터

위 지시문으로 연 새 세션이다. 사용자가 붙인 지시문은 위 인계 절의 것과 같고 모델 줄만 `Opus 5.5 / xhigh`였다. 세션 제목을 `docs/widget-admin-server-spec`으로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다. 명세 쓰기와 측정은 다시 돌리지 않았다.

### 시작 전 확인

- 브랜치는 `docs/widget-admin-server-spec`이고, 커밋하지 않은 변경은 인계 절이 적은 그대로다(`git status --short`를 손으로 봤다. 고친 기능 계획 셋, 미추적 명세와 프로브 폴더와 이 일지).
- `git fetch origin dev` 뒤 `origin/dev`는 `463d9f1f7`로 앞섰다. 기준 `7770ac0c1`과의 사이는 출시 병합 둘(#629 dev에서 main으로, #630 main에서 dev로)이고, merge-base는 그대로 `7770ac0c1`이다(`git log`와 `git merge-base`를 손으로 봤다).
- `uv run python tools/sibling_overlap.py`는 "이 브랜치의 새 번호 없음", "번호 겹침 없음"으로 끝났다. 함께 고친 파일은 하나다. 잠긴 워크트리 `admin-login-spec`이 커밋하지 않은 채 `.scratch/portal-admin/plan.md`를 고쳤다. 나중에 병합하는 쪽에서 글자가 부딪힐 수 있는 후보다.

### 셀프 리뷰(`/code-review`)

고정점은 `origin/dev`이고 base SHA는 `7770ac0c12a061b5dd47149f9989c8af6efc9330`이다. 범위는 고친 파일 셋(기능 계획 셋), 커밋 0개, 미추적 파일 스물(명세, 프로브 폴더의 열여덟, 이 일지)이다. 표준 축(sonnet, high)과 명세 축(본 세션의 모델)을 나란히 띄웠다. 명세 축의 요구는 to-spec 스킬의 틀과 규칙, 기능 계획, ADR 0064와 0066, 앞선 명세 셋이 넘긴 것, 사용자의 답 셋(라벨과 선택지 설명을 글자 그대로)이고, 앞 세션이 셀프 리뷰 전에 고친 것은 리뷰어 참고로 갈랐다.

#### 표준 축의 보고

Critical 0, Major 0, Minor 7, Nit 5다. 보고가 맞다고 한 것: 서두의 수 전부(표 서른세 행, "명세가 정했다" 스물넷, "사용자가 골랐다" 셋, "거부한 안:" 열둘과 든 안 스물하나와 고르지 않은 선택지 넷), 프로브 29회차, 계약 아홉, 열아홉 항목과 그 차례, `tools/release_ci.py` 259·283줄과 `errors.py`의 상수와 `LifespanDriver`와 `site.conf`의 줄, 세 기능 계획의 문단과 그 Blocked by. smell은 짚은 것이 없다. 지적과 판정은 다음과 같다. 판정의 근거는 이 세션이 다시 연 것이다. 지적에 든 따옴표 안은 고치기 전 명세의 글이라, 고친 뒤의 저장소에는 글자 그대로 없다.

1. Minor. 명세 "읽는 경로"의 "`HEAD`는 Starlette가 `GET` 경로에 함께 받는 그대로 둔다"가 거짓이다. **유효, 고친다.** 손으로 봤다. FastAPI 0.141.1과 Starlette 1.6.0에서 `redirect_slashes=False`로 지은 앱에 `@app.get("/widget-settings/{site}")` 하나를 두고 httpx의 `ASGITransport`로 부르자 `GET`은 200, `HEAD`와 `OPTIONS`와 `POST`는 405(`Allow: GET`), 끝에 `/`가 붙은 경로는 404였다. 스크립트는 표준 축이 세션 스크래치패드에 쓴 것이고, 본 세션이 다시 돌려 같은 출력을 봤다. 커밋하지 않는다.
2. Minor. "저장소를 grep해 8100을 쓰는 곳이 없었다"가 거짓이다. **유효, 고친다.** `web/apps/admin/next.config.test.ts`와 `web/apps/admin/tools/loopback.test.ts`가 상류 주소를 고르는 시험의 값으로 `127.0.0.1:8100`을 쓴다(Grep). 같은 문장의 3001은 저장소 어디에서도 포트로 쓰이지 않는다(Grep으로 나온 것은 `tools/run_hooks.py`의 수열과 `tests/tools/test_rerun_cost.py`의 토큰 수다). 듣는 포트는 serve의 8000과 웹 앱 셋의 3000이다(`deploy/standalone/compose.yaml`, `deploy/standalone/proxy/site.conf`를 Grep했다).
3. Minor. "사이트 파일을 읽지 않는다"를 ADR 0064 결정 "위젯 관리 서버"의 것으로 댔다. **유효, 고친다.** 그 문장은 결정 "시작 검사가 가는 자리"에 있다(ADR 0064 24줄을 읽었다).
4. Minor. "따로 하나씩 선다"는 ADR 0064의 말이 아니다. **유효, 고친다.** ADR 0064 결정 "위젯 관리 서버"는 "Agent OS의 것과 따로 하나 더 생긴다"이고(14줄을 읽었다), "따로 하나씩 선다"는 기능 계획 본문의 말이다.
5. Minor. 프로브가 기준 커밋이 아니라 `HEAD`를 푼다. **유효, 고친다.** `run.py`의 `build_tree`가 `git archive … HEAD`를 친다(읽었다). 구현 티켓이 루트 `pyproject.toml`을 바꾼 뒤 다시 돌리면 사본 나무가 고친 뒤의 판이 되어 대조가 서지 않는다. 기준 커밋을 상수로 들고 그것을 풀게 고친다. 잰 실행은 `HEAD`가 `7770ac0c1`이던 때라 결과는 그대로다.
6. Minor. 명세 "설치 묶음과 패키지와 명령"의 런타임 의존성 목록에 pydantic이 빠졌다. **유효, 고친다.** 루트 `pyproject.toml` 31줄과 장난감 멤버의 `pyproject.toml.tmpl` 8줄이 `pydantic>=2.9`를 적는다(Grep).
7. Minor(판단). 코드 조각과 새 구현 파일의 경로가 명세에 든다. **일부 고친다.** 내보내기 도구의 이름(`tools/export_widget_admin_openapi.py`)은 명세 서두가 든 예외(ADR 0064가 이름을 짓게 넘긴 것, 다른 기능과 운영자가 쓰고 읽는 자리)에 들지 않아 이름을 뺀다. 계약 파일의 자리와 이미지를 짓는 파일은 ADR 0064가 넘긴 이름이고(넘겨받은 것 표의 셋째 행과 열여섯째 행), 프록시의 location 줄은 서두가 적는다고 한 "설정의 줄"이라 둔다.
8. Nit. "약 410줄", "약 510줄"이 어느 파일인지 없고, 사본으로 든다고 한 수명 확인 미들웨어가 빠졌다. **고친다.** `wc -l`로 손으로 봤다. `src/agent_os/adapters/postgres/`의 네 파일이 412줄, `src/agent_os/http/errors.py`가 508줄, `src/agent_os/http/database.py`가 120줄, `src/agent_os/http/paths.py`가 20줄이다.
9. Nit. "401, 403, 409 같은 갈래"의 403에는 Agent OS의 값이 없다. **고친다.** `src/agent_os/http/errors.py`의 `_CODE_BY_STATUS`는 401, 404, 409, 422, 429, 500이다(Grep).
10. Nit. CORS, digest, multi-instance에 처음 나올 때의 풀이가 없다. **고친다.** `CLAUDE.md` 원칙의 첫 풀이 규칙이다.
11. Nit. 명세 "검사 도구의 자리"의 "깔린 라이브러리로 읽어"는 진단의 글(`Stub file not found`)에서 미루어 본 해석이다. **고친다.**
12. Nit. "`ruff check .`와 `ruff format --check .`는 멤버까지 보고"의 표지가 `All checks passed!`뿐이다. **고친다.** 손으로 봤다. 셋째 사본 나무에서 `uv run --directory C:/project/uvws3 --frozen ruff check --show-files .`가 든 파일 675개에 멤버의 `.py` 여섯과 `widget-admin/pyproject.toml`, `tests/widget_admin/`의 둘이 있었다. 루트의 ruff 설정에는 훑는 범위를 좁히는 `include`가 없다(`pyproject.toml` 79~92줄을 Grep했다. 99줄의 `include`는 pyright의 것이다).

#### 명세 축의 보고

Major 1, Minor 3, Nit 3이다. 요구에 없는 동작은 찾지 못했다고 했다. 보고가 맞다고 한 것: "이력은 없다"의 근거 셋, 프로브 README의 수치(계약 아홉, 13 passed, 묶음 20 대 67, 119·228·339MB), `tools/database_for_tests.py`를 경계 입력으로 불러 본 동작, 세 기능 계획에 넘긴 문단이 그 명세들의 가정과 어긋나지 않는다는 것. 줄 번호와 지적에 든 따옴표 안은 보고 당시 명세의 것이다. 판정의 근거는 이 세션이 다시 연 것이다.

1. Major. "판 내기의 단계가 목록 하나를 따른다"(157줄)가 틀렸고, 명세대로 세 자리만 고치면 위젯 관리 서버의 이미지가 지어지지도 올라가지도 않는다. **유효, 고친다.** `.github/workflows/release.yml`이 이미지 이름을 직접 적는다. 반복문 셋(194·268·435줄의 `for image in serve admin widget portal`), 첫째 잡의 출력(61~64줄), 둘째 잡의 환경 `DIGEST_*`(314~317줄), 아티팩트 대조의 인자(333~334줄), 머리 주석의 "이미지 넷"이다(Read). `deploy/images/docker-bake.hcl`의 `group "default"`의 `targets`(43줄)도 따로 적힌 목록이고, `web/packages/e2e-standalone/e2e/stack.ts`도 이미지 넷을 짓는다(Read). `tests/tools/test_release_ci.py`는 짓기 설정의 대상과 저장소 이름만 `IMAGES`와 맞댄다(399·400줄, Read). 고치며 새로 찾은 것: 번호 태그의 반복문(436~437줄)이 `DIGEST_<대문자 이름>`을 간접으로 읽어 하이픈이 든 이름을 읽지 못한다. 손으로 봤다. 이 PC의 Git Bash에서 `var=DIGEST_WIDGET-ADMIN; echo "${!var}"`가 `bad substitution`으로 1이었다. 판 번호를 넣는 것은 출시 도구가 아니라 짓는 파일이라는 것도 고쳐 적었다(`deploy/images/serve.Dockerfile` 43줄의 `sed`를 읽었고, `tools/release.py`에 `pyproject`가 없는 것을 Grep했다). 명세 "판 번호와 출시"를 다시 쓰고, 목록 다섯 자리와 목록 맞대기 시험을 적었다. "티켓을 나눌 때 함께 둘 것"의 배포 변경과 Testing Decisions의 대응 시험 줄에도 더했다. 보고가 든 사용자 답 2의 조건("출시 도구가 함께 서는지 먼저 잰다")은 짓는 파일 쪽이 재서 섰고, 출시 도구와 워크플로는 돌려 재지 않았다고 명세에 적었다.
2. Minor. multi-instance에 넘긴 것을 받는 쪽이 모른다(457줄). **유효, 고친다.** `.scratch/multi-instance/plan.md`에 위젯의 말이 없었다(Read). 그 기능 계획에 "widget-admin-server 명세가 넘긴 것" 문단을 더했다. Blocked by는 admin-crud뿐이지만 계획표에서 multi-instance는 슬라이스 14이고 이 기능은 9다(`.scratch/plan.md` 75·109줄을 Grep했다). Out of Scope 머리에 그것을 적고, 줄 이름에 첫 풀이를 달았다.
3. Minor. 설치 묶음(휠)의 물음을 "기능 계획 본문, ADR 0066 결정 '위젯 관리 서버'도"에 댔다(24줄). **유효, 고친다.** 그 물음은 ADR 0064 14줄에만 있다. ADR 0066에서 '휠'은 16줄 "층과 조립"의 "마이그레이션 파일은 … 휠과 이미지에 함께 든다"뿐이고 결정 "위젯 관리 서버"(26줄)에는 없다(Grep, Read). 괄호를 지웠다.
4. Minor. 데이터베이스를 가짜로 바꾸지 않는다면서, 확인이 예외를 던지는 사례와 핸들러가 놓친 예외의 500은 진짜 데이터베이스로 일으킬 길을 적지 않았다. **유효, 고친다.** 선례로 든 `tests/test_check_database.py`가 `FakeDatabase`를 쓰고(12줄), `tests/test_server.py`의 `_route_that_raises`(530줄)가 예외를 던지는 시험용 경로를 붙인다(Grep). 첫째 이음매에 예외 둘(시험용 경로, 확인만 예외를 던지게 바꾼 데이터베이스 객체)을 적고 머리 시험 줄에서 가리켰다.
5. Nit. "설정 여섯 자리", "하나씩 빼는 대조로"(65·137줄). **고친다.** Solution은 검사 도구의 설정 네 자리로 적었다. "검사 도구의 자리"는 여섯을 두되 프로브 독스트링(`run.py` 11~13줄)처럼 워크스페이스의 멤버와 원천을 한 자리로 센다고 밝혔고, 대조는 넷이고 import-linter는 심은 import를 잡는 양성 대조로 쟀다고 고쳤다(그 측정은 `.scratch/widget-admin-server/probes/uv_workspace/`가 다시 낸다).
6. Nit. "8100을 쓰는 곳이 없었다"(130줄). 표준 축 2와 같은 지적이라 거기서 고쳤다.
7. Nit. "판을 낼 때만 바뀐다"(155줄)가 판 번호 규칙과 맞지 않는다. **유효, 고친다.** 저장소의 판은 늘 `0.0.0`이고 번호는 이미지 안의 사본에만 들어간다(ADR 0056 결정 "저장소의 번호", `tests/test_repo_version.py`의 독스트링을 읽었다).

#### 고친 것, 남긴 것, 다시 돌린 것

- 고친 것: 표준 축 1~12와 명세 축 1~5·7이다(6은 표준 축 2와 같다). 표준 축 7의 계약 파일 자리, 이미지를 짓는 파일 이름, 프록시의 location 줄은 명세 서두의 예외라 두었다.
- 남긴 것: 없다.
- 다시 돌린 것: 프로브 `run.py`는 기준 커밋을 풀게 고친 뒤 `uv run ruff check`와 `uv run ruff format --check`만 쳤다(둘 다 0). 측정 자체는 다시 돌리지 않았다. 잰 실행 때 `HEAD`가 기준 커밋이었기 때문이다. 손으로 치는 다섯 명령은 커밋의 pre-commit으로 갈음하고 결과는 커밋 뒤에 적는다.
- PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 사실 문장):
  - "이미지의 목록은 한 곳이 아니라 저장소의 여러 자리에 따로 적혀 있고(기준 커밋의 코드를 읽었다), 그 모두에 `widget-admin`을 더한다." 와 그 아래 다섯 자리의 줄 번호(release.yml 194·268·435, 61~64, 314~317, 333~334, docker-bake.hcl 43, release_ci.py 259·283).
  - "번호 태그의 반복문은 이미지 이름을 대문자로 바꿔 변수 이름 `DIGEST_<이름>`을 짓고 그 변수를 간접으로 읽는다(436~437줄, 코드를 읽었다)." 와 "대상 이름으로 저장소 이름을 찾는 `tools/release_ci.py`의 `repository`는 하이픈이 든 이름을 받는다(`_BAKE_REPOSITORY`의 꼴, 코드를 읽었다)."
  - "지금 그 시험은 짓기 설정의 대상과 저장소 이름만 `IMAGES`와 맞댄다(399·400줄, 코드를 읽었다)."
  - "serve의 짓는 파일이 빌드 단계 안의 `pyproject.toml` 사본에 `sed`로 번호를 넣고(`deploy/images/serve.Dockerfile` 43줄, 코드를 읽었다)" 와 "출시 도구(`tools/release.py`)에는 `pyproject`가 나오지 않는다(Grep으로 찾았다)."
  - "저장소에서 8100은 관리 화면의 상류 주소를 고르는 시험의 값(`web/apps/admin/next.config.test.ts`, `web/apps/admin/tools/loopback.test.ts`)으로만 나온다."
  - "`HEAD`도 405다. FastAPI의 경로는 `GET`으로 지은 경로에 `HEAD`를 함께 받지 않는다." 와 그 손 확인(FastAPI 0.141.1, Starlette 1.6.0).
  - Testing Decisions의 "핸들러가 놓친 예외는 지은 앱에 예외를 던지는 시험용 경로를 붙여 일으키고(선례는 `tests/test_server.py`의 `_route_that_raises`)".
  - Out of Scope 머리의 "multi-instance는 없지만 계획표에서 이 기능(슬라이스 9)보다 뒤인 슬라이스 14이고".
  - 오류 어휘 여섯(401, 404, 409, 422, 429, 500)이 `_CODE_BY_STATUS`의 전부라는 것.
  - "루트 `pyproject.toml`에서 고치는 자리는 여섯이다(프로브의 독스트링처럼 워크스페이스의 멤버와 원천을 한 자리로, import-linter의 `root_packages`와 독립 계약을 한 자리로 센다)." (괄호의 뒤쪽은 아래 PR 직전 리뷰의 반영으로 더했다)

### 커밋

`git branch --show-current`는 `docs/widget-admin-server-spec`, `tools/sibling_overlap.py`는 새 번호 없음과 번호 겹침 없음으로 끝났다(`origin/dev`는 그대로 `463d9f1`). `tools/plan_table.py`는 바뀐 것이 없었다. 커밋 `3f1726d3f`(파일 24개)의 pre-commit은 모두 통과했다. ruff check, ruff format, 병렬 검사 열하나(check-ticket, lint-imports, check-notes, zizmor, check-type-escapes, check-instructions, pyright, pyright-linux, run-hooks, pytest, web-verify. 모두 1217초), 마크다운 표, 줄 구분 문자, 변이 표, 커밋 메시지다. 카나리아 명세 모양과 헌법 판은 대상 파일이 없어 `Skipped`였다. 손으로 치는 다섯 명령은 이 결과로 갈음한다.

인용 대조가 경고 일곱을 냈고(막지 않는다) 하나씩 봤다. 명세 12줄은 기능 계획 본문의 "함께 넣어"를 "함께 넣는다"로 옮긴 것이라 원문대로 고쳤다. 명세 404줄은 `tech.md`에 새로 쓸 문구라 `문구 후보:` 표지 뒤로 옮겼다. 일지 다섯(121·122·132·138·140줄)은 고치기 전 명세의 글을 옮긴 것이라 두고, 두 보고의 머리에 그렇다고 적었다. 이 고침은 다음 커밋에 든다.

### PR 직전 리뷰 (CodeRabbit CLI)

`coderabbit-review` 서브에이전트가 돌렸다. 브리프에는 기준 브랜치 `origin/dev`, 커밋 하나와 그 뒤의 커밋하지 않은 두 파일, 위 "고친 것, 남긴 것, 다시 돌린 것"의 밀 주장 열, 프로브 `run.py`의 폴더 지우기와 프로세스 끄기를 실었다. 아래는 그 보고의 요지와 이 세션의 판정이다.

- CLI는 0.7.5이고 `coderabbit auth status`는 `Plan: Free`, `Seat: not assigned`였다. 친 명령은 `coderabbit review --agent --include-untracked --base origin/dev`이고 종료 0, 완료 이벤트는 `review_completed`, 지적은 하나였다. 본 파일은 변경 24개 전부다.
- **CLI 지적 (Minor, 서브에이전트는 보류).** 명세 "단독 compose"의 대가 문장. `serve`가 `.env`를 통째로 받아 위젯 쪽 비밀번호도 받으니, 그 값이 플러그인이나 MCP 하위 프로세스에 가는지 보고 ADR 0066과 같은 대가로 뭉뚱그리지 말라는 것이다. **유효, 고친다.** ADR 0066 Consequences "신뢰와 노출"(62줄을 읽었다)이 Agent OS 쪽 비밀번호에 든 노출의 길은 http 모양의 MCP 매니페스트가 환경 변수를 헤더에 싣는 길(ADR 0049)이고, 그것을 막는 허락 목록은 mcp-trust가 맡는다. postgres-foundation은 Agent OS 쪽의 변수 둘을 그 기능 계획에 넘겼는데(`.scratch/mcp-trust/plan.md` 7줄을 읽었다), 이 명세는 위젯 쪽 변수를 넘기지 않았다. 대가 문장에 노출의 길과 mcp-trust를 적고, Out of Scope에 mcp-trust 줄을 더하고, 그 기능 계획에 넘긴 문단을 더했다. mcp-trust의 Blocked by는 approval-rules, pilot-release, mcp-http이고 pilot-release가 이 기능을 기다리므로(`.scratch/plan.md` 69줄) 받는 쪽이 먼저 돌지 않는다. Out of Scope 머리에 그것을 적었다. 서브에이전트가 든 stdio 자식의 환경(mcp 라이브러리가 `env`가 없을 때 무엇을 물려주는지)은 Agent OS 쪽 비밀번호와 같은 처지라 이 명세에 따로 적지 않았다.
- **대 본 주장 1 (Major, 유효, 고친다).** 이미지 목록의 자리에 `.github/workflows/release.yml` 221~222줄, 노트를 짓는 `tools/release.py notes`의 `--grype serve=… admin=… widget=… portal=…`가 빠졌다. 기준 커밋의 파일을 읽어 그 줄을 봤다. `tools/release.py`의 `_warning_lines`(436줄)는 받은 `--grype`만 돌고 `IMAGES`와 대 보지 않는다(Grep). 그래서 빠뜨리면 그 이미지에만 Critical이 있을 때는 223~226줄의 확인이 판 내기를 멈추고, 다른 이미지에도 있을 때는 경고가 서되 그 이미지가 빠진다. 명세의 목록과 목록 맞대기 시험에 더했다. 짓기 설정의 머리 주석(1줄의 "이미지 넷", 10~12줄의 이름 나열)도 서브에이전트가 Minor로 짚어 같은 줄에 더했다.
- **대 본 주장 3 (Minor, 유효, 고친다).** "지금 그 시험은 … 만 `IMAGES`와 맞댄다"가 `IMAGES`를 쓰는 시험이 그것뿐이라고 읽힐 수 있다. 같은 파일의 219·228·234·305줄은 `IMAGES`로 시험 자료를 짓고, 462·475줄은 compose와 배포 안내를 짓기 설정과 맞댄다(Grep). 다른 자리의 목록을 `IMAGES`와 맞대는 시험이 그 하나뿐이라고 고쳤다.
- **대 본 주장 10 (Minor, 유효, 고친다).** 여섯으로 세려면 import-linter의 `root_packages`와 독립 계약도 한 자리로 세야 한다. 괄호에 그것을 더했다.
- **나머지 주장.** 2·4·5·7·8·9는 맞았다고 했다. 2의 `bad substitution`과 6의 `HEAD` 405는 서브에이전트가 다시 재지 않았다(이 세션의 손 확인이 근거다).
- **프로브 점검.** `run.py`는 인자 폴더가 절대 경로가 아니거나 비지 않았으면 멈추고 지우지 않는다. 프로세스를 끄는 자리가 없다. 저장소 파일을 쓰거나 지우는 자리가 없다. **남긴 것 둘(Minor):** 인자가 파일이면 `iterdir()`가 `NotADirectoryError`로 끝난다(멈추기는 한다). `docker image rm -f`가 지우는 이름 셋(`uv-workspace-probe/…:probe`)을 같은 이름으로 만든 이미지가 있으면 함께 지워진다. 둘 다 프로브의 다시 돌리기에만 닿고 결과를 바꾸지 않으므로 고치지 않고 PR 체크리스트에 적는다.

**서두의 수.** 다시 셌고 바뀌지 않았다(표 서른세 행, "명세가 정했다" 스물넷, "사용자가 골랐다" 셋, "거부한 안:" 열둘). `tools/plan_table.py`는 바뀐 것이 없었다.

**PR 봇에 밀 주장(이 반영으로 새로 쓴 문장).** "`--grype` 인자에서 빠지면 … 다른 이미지에도 있으면 경고는 서되 그 이미지는 경고에서 빠진다(221~226줄과 `tools/release.py`의 노트 경고가 받은 점검 결과만 도는 것, 코드를 읽었다)." "지금 그 파일에서 다른 자리의 이미지 목록을 `IMAGES`와 맞대는 시험은 짓기 설정의 대상과 저장소 이름을 보는 하나뿐이다(399·400줄)." 명세 "단독 compose"의 대가 문장과 mcp-trust 기능 계획의 "위젯 쪽 연결 문자열 `WIDGET_ADMIN_DATABASE_URL`은 compose가 위젯 쪽 두 서비스(`widget-admin-migrate`, `widget-admin`)에만 지어 넘기고 `serve`에는 넘기지 않는다."

### 둘째 커밋

`git branch --show-current`와 `tools/sibling_overlap.py`(새 번호 없음, 번호 겹침 없음. 함께 고친 파일은 그대로 `admin-login-spec`의 `.scratch/portal-admin/plan.md` 하나)를 본 뒤 커밋 `ce51ab895`(파일 셋)를 만들었다. pre-commit은 모두 통과했다. ruff 둘은 `.py`가 없어 `Skipped`였고 이 커밋은 `.py`를 바꾸지 않았다. 병렬 검사 열하나는 933초였다. 인용 대조의 경고 둘(이 일지 161·183줄)은 밀 주장 목록이 옮긴 글이 원문과 어긋난 것이라, 커밋 뒤에 원문대로 고쳤다(161줄은 PR 직전 리뷰의 반영으로 늘어난 괄호, 183줄은 빠진 서비스 이름 괄호). 이 고침과 아래 인계 절은 커밋하지 않았다.

## 인계 (커밋 뒤)

둘째 커밋 뒤에 인계 계기(`커밋 뒤`, 컨텍스트 267,926 토큰)가 와서 `next-session` `handoff.md`대로 넘긴다. 이 세션은 곁 세션이 아니다(`get_session`의 `self`에 `parentSessionId`가 없다). 이 세션의 지금 제목은 `docs/widget-admin-server-spec`이다. 사용자 프롬프트는 위 "인계" 절의 지시문 하나이고 모델 줄만 `Opus 5.5 / xhigh`로 바꿔 보냈다. 그래서 아래 지시문의 모델도 그 값을 잇는다. 이 세션이 고친 결정은 없고, 명세에서 바로잡은 사실 문장은 위 표준 축·명세 축·PR 직전 리뷰의 판정에 있다. 프로브 이미지는 `docker images`로 둘(`uv-workspace-probe/serve-sync:probe`, `uv-workspace-probe/widget-admin:probe`), 사본 나무 셋(`C:/project/uvws1`, `uvws2`, `uvws3`)은 `ls`로 남아 있는 것을 봤다.

```
다음 작업: 기능 widget-admin-server. 위젯 관리 서버의 명세를 푸시하고 PR을 열어 병합한다
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec widget-admin-server
브랜치: docs/widget-admin-server-spec
모델: Opus 5.5 / xhigh. 사용자가 앞 지시문의 모델 줄을 이 값으로 바꿔 보냈다
읽을 것: docs/journal/2026-11-24-1637-widget-admin-server-spec.md
이어받을 상태: 인계: 커밋 뒤. 커밋 둘(3f1726d3f 명세·프로브·기능 계획 넷·일지, ce51ab895 PR 직전 리뷰 반영과 mcp-trust 기능 계획에 넘긴 문단)까지 했고 아직 푸시하지 않았다. 셀프 리뷰, PR 직전 리뷰(CodeRabbit CLI)와 그 반영, 서두의 수 세기는 끝났다. 일지의 인용 고침 두 줄과 인계 절은 커밋하지 않은 채 워크트리에 있으니 일지를 이어 쓴 뒤 함께 커밋한다. 남은 단계는 푸시, PR 열기(체크리스트의 PR 직전 리뷰 줄에 남긴 Minor 둘을 적는다. 일지 "PR 직전 리뷰"의 프로브 점검), @coderabbitai review, merge.md 2(봇 회차), 일지의 "다음"과 회고, 병합, 다음 지시문이다. 이력이 없어 ADR 승인은 없다. 끝에 사람에게 사본 나무 넷(C:/project/uvws1, C:/project/uvws2, C:/project/uvws3, 앞 세션 스크래치패드의 uvws-1)과 프로브 이미지 둘(uv-workspace-probe/widget-admin:probe, uv-workspace-probe/serve-sync:probe)을 지우라고 알린다. 일지 docs/journal/2026-11-24-1637-widget-admin-server-spec.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

워크트리 잠금 풀기는 `is not locked`로 끝나 넘어갔다. 이 세션이 띄운 백그라운드 작업은 남은 것이 없었다.

open-session을 부른다 2026-11-24T10:54:01Z

## 이어받은 세션: 푸시부터

위 "인계 (커밋 뒤)" 절의 지시문으로 연 새 세션이다. 사용자 프롬프트는 그 지시문과 글자가 같았다(첫 줄은 open-session이 옮긴 "`.claude/skills/to-spec/SKILL.md` 를 읽어 그대로 따른다"로 시작하고 인자는 `widget-admin-server`다). 세션 제목을 `docs/widget-admin-server-spec`으로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다. 명세 쓰기, 측정, 리뷰는 다시 돌리지 않았고, 이 세션이 고친 결정과 명세의 문장은 없다.

- 브랜치는 `docs/widget-admin-server-spec`이고 커밋하지 않은 변경은 이 일지 하나였다(`git status --short`를 손으로 봤다).
- `git fetch origin dev` 뒤 `origin/dev`는 `463d9f1f7`이었고, 기준 `7770ac0c1`과의 내용 차이는 없었다(`git diff --stat 7770ac0c1 origin/dev`가 비었다). `tools/sibling_overlap.py`는 새 번호 없음, 번호 겹침 없음이었고, 함께 고친 파일은 그대로 `admin-login-spec`의 `.scratch/portal-admin/plan.md` 하나였다.
- 첫 푸시를 훅이 막았다(`origin/dev`보다 2커밋 뒤처졌다). `git merge --no-edit origin/dev`로 합쳤다(merge 커밋 `c82aed369`. `git diff --stat HEAD~1 HEAD`가 비어 내용 차이가 없었고, 출력에는 커밋 메시지 검사의 `Passed` 한 줄만 찍혔다). 그 뒤 푸시했다.
- 둘째 커밋에서 ruff 둘이 `Skipped`였으므로 저장소 전체로 손으로 쳤다. `uv run ruff check .`는 `All checks passed!`, `uv run ruff format --check .`는 `2554 files already formatted`였다.
- PR 632(`https://github.com/njh6803/agent-os/pull/632`)를 열었다. 체크리스트의 PR 직전 리뷰 줄과 "남긴 위험"에 프로브 점검의 Minor 둘을 적었다. `@coderabbitai review`는 아직 남기지 않았다.

### 인계 (PR 연 뒤)

PR을 열자 인계 계기(`PR 연 뒤`, 컨텍스트 237,568 토큰)가 와서 `next-session` `handoff.md`대로 넘긴다. 이 세션은 곁 세션이 아니다(`get_session`의 `self`에 `parentSessionId`가 없다). 이 세션의 지금 제목은 `docs/widget-admin-server-spec`이다. 지시문의 모델은 다음 단계가 `PR 반영·병합`이라 `directive.md` 2의 잇는 지시문대로 `Sonnet 5.5 / high`다. 앞 두 지시문의 `Opus 5.5 / xhigh`는 사용자가 명세 단계의 지시문에서 바꾼 값이라 옮기지 않았다.

```
다음 작업: 기능 widget-admin-server. 위젯 관리 서버의 명세 PR 632에 봇 회차를 반영하고 병합한다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec widget-admin-server
브랜치: docs/widget-admin-server-spec
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-24-1637-widget-admin-server-spec.md
이어받을 상태: 인계: PR 연 뒤. PR 632를 열었고 merge.md 2(봇 회차)부터 한다. 첫 @coderabbitai review 코멘트도 아직 남기지 않았다. 일지는 커밋하지 않은 채 워크트리에 있다(앞 세션의 인용 고침 두 줄과 인계 절, 이 세션의 "이어받은 세션: 푸시부터"와 이 인계 절). 봇 회차의 반영 커밋에 함께 싣고, 일지의 "다음"과 회고(retro)는 단계를 닫는 세션이 병합 전에 마친다. 명세 본문을 고치는 반영이면 서두의 수를 다시 센다(to-spec 3단계). 이력이 없어 ADR 승인은 없다. 끝에 사람에게 사본 나무 넷(C:/project/uvws1, C:/project/uvws2, C:/project/uvws3, 첫 세션 스크래치패드의 uvws-1)과 프로브 이미지 둘(uv-workspace-probe/widget-admin:probe, uv-workspace-probe/serve-sync:probe)을 지우라고 알린다. 일지 docs/journal/2026-11-24-1637-widget-admin-server-spec.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목은 `docs/widget-admin-server-spec (인계함)`으로 바꿨다. 이 세션이 띄운 백그라운드 작업은 없었다. 워크트리 잠금 풀기는 `is not locked`로 끝나 넘어갔다.

open-session을 부른다 2026-11-24T11:06:29Z

## 이어받은 세션: 봇 회차

위 "인계 (PR 연 뒤)" 절의 지시문으로 연 새 세션이다. 사용자 프롬프트는 그 지시문과 글자가 같았고 모델 줄만 `Sonnet 5.5 / high`다. 세션 제목을 `docs/widget-admin-server-spec`으로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다. 명세 본문은 고치지 않았다.

### 검사

- 헤드 `c82aed369`에 `@coderabbitai review`를 남겼다. 첫 요청은 한도에 걸려 "Review rate limited"(3분 뒤 가능)였고, 두 번째 요청이 리뷰를 받았다(Finished, 지적 일곱).
- `python` 잡이 두 시도 연속으로 제한 시간 15분에 취소됐고(실행 45380651521, 11:03:49~11:19:06과 11:20:25~11:35:40) 그 때문에 `verify`가 빨갰다. 이번에는 가벼운 단계가 아니라 pytest 단계 안에서 92%에서 끊겼다(잡 로그의 진행 줄을 손으로 봤다). 이 PR은 문서와 프로브만 바꿔 코드 문제가 아니다. 대기열 `ci-python-job-timeout-margin`이 같은 일이라 그 항목의 4회차로 셌다(3회차는 열린 PR 631이 같은 항목에 적었다. 그 PR이 먼저 병합되면 이 PR이 그 항목의 승인 줄에서 글자 충돌을 푼다). 처방(잡 나누기나 제한 올리기)은 그 항목이 정하므로 이 PR에서 `ci.yml`을 고치지 않았다. 셋째 시도는 아래 푸시로 헤드가 바뀌어 의미를 잃었다.
- `claude-review`는 "지적 없음"이다(첫 회차).

### CodeRabbit 첫 회차(Major 1, Minor 6)와 판정

회차는 봇마다 센다. 이 봇의 첫 리뷰이므로 Minor도 지적마다 판단했다. 근거는 이 세션이 다시 연 것이다.

1. **Major. 명세 "단독 compose"의 대가(369줄): 위젯 쪽 비밀번호를 `serve`의 환경에서 떼어 달라.** 두지 않는다. 같은 안이 명세 371줄에 "거부한 안: 위젯 쪽 비밀번호를 따로 둔 env 파일에 적는다"로 이미 있고 까닭(운영자가 고칠 비밀 파일이 둘이 되고, 배포 안내와 판 내기의 시험이 그 파일을 함께 다뤄야 한다)도 적혀 있다. 이야기 11(고칠 파일이 하나)과도 맞지 않는다. `serve`는 Agent OS 쪽 비밀번호도 같은 `.env`로 받으므로, 위젯 쪽만 떼어 내도 같은 노출의 길(ADR 0049의 http 모양 MCP 매니페스트)에 Agent OS 쪽 비밀번호가 남고, 그 길을 막는 것은 mcp-trust가 맡는다(명세 Out of Scope, 그 기능 계획에 넘겼다). 새 결정이 없어 명세를 고치지 않았다.
2. **Minor. 명세 "프록시"(375줄): `/widget-settings/%2e%2e`가 포털로 간다.** 두지 않는다. 그 요청은 nginx가 정규화한 경로 `/`로 보면 위젯 관리 서버의 경로가 아니라 포털의 루트다. 명세는 점 조각이 든 사이트 이름에 위젯 관리 서버의 404를 약속하지 않았고(사이트 이름의 꼴이 `.`과 `..`을 막는다는 것뿐이다, 220줄), 퍼센트 인코딩된 `/`가 든 이름의 404를 단독 배포 e2e가 보게 했다(378줄). 정규화가 접두 밖으로 나가게 하는 요청은 접두 밖의 경로 몫이다. 봇이 말한 "e2e의 점 세그먼트 목록"은 명세에 없다. nginx의 정규화는 이 세션이 재지 않았고, 명세에도 그 동작을 새로 적지 않았다.
3. **Minor. `run.py` 양성 대조가 파일 이름만 본다.** 고쳤다. 진단 `파일:규칙`이 심은 파일의 `reportAssignmentType`일 때만 센다(`_is_planted_error`). 잰 실행의 `18-pyright-planted.log`에 그 규칙이 심은 파일의 진단으로 있었다(손으로 봤다).
4. **Minor. `-n 2` 회차가 마지막 줄의 `passed`만 본다.** 고쳤다. 경로마다 `--collect-only`로 모은 시험 수를 세어 그 합이 통과 수와 같고 둘 다 0보다 클 때만 센다. 잰 실행은 위젯 시험 1(`25-pytest-widget.log`)과 `tests/test_migrate_command.py` 12(`uv run pytest --collect-only -q tests/test_migrate_command.py`가 12 tests collected)의 합 13이 `26-pytest-both.log`의 `13 passed`와 같았다(손으로 봤다).
5. **Minor. 대조 이미지 회차가 `widget-admin`이 든 줄만 본다.** 고쳤다. `not a workspace member`가 든 줄을 본다. `37-build-control.log`에 있었다(손으로 봤다).
6. **Minor. `database-create` 로그에 접속 주소의 비밀번호가 남는다.** 고쳤다. `Tree.run`에 `secret_stdout`을 더해 그 명령의 표준 출력은 로그에 싣지 않는다. 반환값은 그대로다. 그 로그는 저장소 밖 사본 나무에 있고 비밀번호는 시험 컨테이너의 고정 기본값이었다(`AGENT_OS_TEST_DATABASE_URL`에 따로 넣었다면 그 값이다). 이미 있는 사본 나무의 `28-database-create.log`는 사본 나무와 함께 지우라고 사람에게 알린다(아래 "다음").
7. **Minor. 타입 우회 검사 회차가 종료 0과 빈 출력만 본다.** 두었다. 그 검사기는 정상이면 아무것도 찍지 않아 다른 표지가 없고, 같은 사본 나무에서 심은 `Any`를 잡는 양성 대조 회차가 따로 있다(`24-escapes-planted.log`). 봇이 말한 "같은 실행에 검증용 파일을 넣고 그 진단을 뺀 나머지가 0건"은 정상 회차의 의미를 바꾸는 일이라 하지 않았다.

README는 표지 열 셋(35·56·75줄)을 고치고, 표지를 좁힌 사실과 다시 돌리지 않았다는 것, 로그로 손으로 맞춘 것을 "실행의 차례"에 적었다. `run.py`는 ruff check, ruff format --check, `tools/check_type_escapes.py`가 통과했다. 좁힌 `run.py`는 다시 돌리지 않았다(돌리면 사본 나무와 이미지 짓기에 수십 분이 든다). 구현 티켓이 이 프로브를 다시 돌릴 때 처음 본다.

**서두의 수.** 명세 본문(`spec.md`)을 고치지 않아 다시 세지 않았다. 표 서른세 행, "명세가 정했다" 스물넷, "사용자가 골랐다" 셋, "거부한 안:" 열둘은 그대로다.

**PR 봇에 밀 주장(이 반영으로 새로 쓴 문장).** 프로브 README "실행의 차례"의 새 불릿(표지를 좁힌 것과 로그를 손으로 맞춘 것, 타입 우회 회차를 두는 까닭). 명세에 새로 쓴 사실은 없다.

## 회고

낸 후보 둘, 승인 둘(둘 다 기존 항목의 회차), 넘김 0, 기각 0이다. 둘 다 사건이 이 세션에 있고 되돌림은 PR 하나다.

1. **승인(회차). `python` 잡이 제한 시간에 두 시도 연속 취소됐다.** 열린 `ci-python-job-timeout-margin`의 4회차로 더했다(1회차 PR #624, 2회차 PR #625, 3회차 PR #631, 4회차 이 PR #632). 사건은 위 "검사"다. 층은 이미 그 항목이 정했다(잡 나누기나 제한 올리기이고 올리는 길은 넘김). 다섯 번째에 반영한다.
2. **승인(회차). 프로브의 표지가 재려는 상황보다 느슨했다.** 열린 `probe-round-marked-measured-unconditionally`의 14회차로 더했다(PR의 CodeRabbit 첫 회차가 넷을 짚었고 셀프 리뷰 두 축과 PR 직전 리뷰는 짚지 않았다). 그 항목의 `어디로:`인 훅은 조건이 있어도 느슨한 꼴을 잡지 못한다고 11회차가 이미 적었다. 이미 다섯을 넘겨 쌓이고 있어 반영은 chore 배치가 정한다.

## 다음

- **이 PR(632)은 병합까지 한다.** 병합 뒤 widget-admin-server의 다음은 티켓을 쪼개는 일이다. `to-tickets`는 사용자만 부르는 스킬이다(`CLAUDE.md` 지도). 그 직전에 `spec-reviewer`로 명세를 한 번 검토한다.
- **구현 티켓이 처음 보는 것 둘.** 좁힌 프로브 `run.py`가 다시 도는 첫 실행(위 "CodeRabbit 첫 회차" 3~6), 그리고 단독 배포 e2e가 위젯 관리 서버의 이미지를 짓는 시간(명세의 어림, 재지 않았다).
- **사람이 지울 것.** 사본 나무 넷(`C:/project/uvws1`, `C:/project/uvws2`, `C:/project/uvws3`, 첫 세션 스크래치패드의 `uvws-1`)과 프로브 이미지 둘(`uv-workspace-probe/widget-admin:probe`, `uv-workspace-probe/serve-sync:probe`). 사본 나무 셋째의 `.probe-logs/28-database-create.log`에 시험 컨테이너 접속 주소의 비밀번호가 평문으로 있다(그 사본 나무를 지우면 함께 없어진다).
- **CI 시간.** `python` 잡이 15분에 자주 닿는다. 대기열 `ci-python-job-timeout-margin`이 4회차다. 이 PR 같은 문서 PR도 걸려 병합이 미뤄진다.
