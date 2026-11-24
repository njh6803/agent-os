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

Critical 0, Major 0, Minor 7, Nit 5다. 보고가 맞다고 한 것: 서두의 수 전부(표 서른세 행, "명세가 정했다" 스물넷, "사용자가 골랐다" 셋, "거부한 안:" 열둘과 든 안 스물하나와 고르지 않은 선택지 넷), 프로브 29회차, 계약 아홉, 열아홉 항목과 그 차례, `tools/release_ci.py` 259·283줄과 `errors.py`의 상수와 `LifespanDriver`와 `site.conf`의 줄, 세 기능 계획의 문단과 그 Blocked by. smell은 짚은 것이 없다. 지적과 판정은 다음과 같다. 판정의 근거는 이 세션이 다시 연 것이다.

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

Major 1, Minor 3, Nit 3이다. 요구에 없는 동작은 찾지 못했다고 했다. 보고가 맞다고 한 것: "이력은 없다"의 근거 셋, 프로브 README의 수치(계약 아홉, 13 passed, 묶음 20 대 67, 119·228·339MB), `tools/database_for_tests.py`를 경계 입력으로 불러 본 동작, 세 기능 계획에 넘긴 문단이 그 명세들의 가정과 어긋나지 않는다는 것. 줄 번호는 보고 당시 명세의 것이다. 판정의 근거는 이 세션이 다시 연 것이다.

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
  - "`HEAD`는 받지 않는다" 쪽의 손 확인(FastAPI 0.141.1, Starlette 1.6.0에서 `HEAD`가 405).
  - Testing Decisions의 "핸들러가 놓친 예외는 지은 앱에 예외를 던지는 시험용 경로를 붙여 일으키고(선례는 `tests/test_server.py`의 `_route_that_raises`)".
  - Out of Scope 머리의 "multi-instance는 없지만 계획표에서 이 기능(슬라이스 9)보다 뒤인 슬라이스 14이고".
  - 오류 어휘 여섯(401, 404, 409, 422, 429, 500)이 `_CODE_BY_STATUS`의 전부라는 것.
