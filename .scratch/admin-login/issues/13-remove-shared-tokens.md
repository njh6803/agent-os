# 13: 공유 토큰을 걷는다(느낌표)

**What to build:** `serve`는 공유 토큰(모두가 함께 쓰던 비밀 글) 둘, `AGENT_OS_ADMIN_TOKEN`과 `AGENT_OS_CHANNEL_TOKEN`을 읽지 않고, 둘이 없어도 뜬다. 판을 올린 배치의 `.env`에 둘이 남아 있으면 변수마다 "더 쓰지 않습니다. 지워도 됩니다" 한 줄을 이름과 함께 찍고 그대로 뜬다(값은 찍지 않는다). 공유 토큰을 `Authorization` 머리에 실어 운영자 경로(최종 사용자 경로와 `/health`를 뺀 관리 API와 `/runs`)를 부르면 401이고, 그 401에는 `WWW-Authenticate: Bearer`가 없다. 운영자 경로는 로그인 쿠키로만 열린다. 단독 배포 안내는 토큰을 만들어 넣는 대신, 서버에서 첫 계정을 만들고 SSH 포트 포워딩으로 연 `http://127.0.0.1:3000/`에서 로그인하라고 안내한다. 모든 시험과 e2e 하네스는 계정으로 로그인해 받은 쿠키로 돈다.

이 티켓이 "공유 토큰과 쿠키를 함께 받는 기간"을 닫는다. PR 제목에 느낌표(`feat!:`처럼 붙이는 `!`. 판을 올리는 사람이 손으로 할 일이 있다는 표지)를 붙인다. 판을 올리는 운영자가 `.env`에서 두 토큰을 지워야 하기 때문이다.

근거는 명세 `.scratch/admin-login/spec.md`의 "공유 토큰을 없애는 자리", "공유 토큰과 쿠키를 함께 받는 기간", "경로"의 "401의 머리", "계약과 생성물"의 "생성 클라이언트 패키지", "배포 안내"의 "토큰을 말하는 줄"과 "올리는 사람에게 요구하는 셋", Testing Decisions의 "HTTP 시험"(마지막 문장), "공유 토큰을 걷는 것", "단독 배포 e2e"(관리 토큰을 쓰던 시험), "실제 모델"(마지막 문장)이다. 결정은 ADR 0062 결정 "자격", ADR 0056(루프백 진단)이다. 이 티켓의 "명세 검토"는 일지 `docs/journal/2026-11-25-1007-admin-login-tickets.md`의 "명세 검토(spec-reviewer)" 절을 가리킨다.

**Blocked by:** 05, 09

**Status:** done

### 서버

- [x] `serve`가 두 토큰 변수를 읽지 않고, 남은 변수마다 "더 쓰지 않습니다. 지워도 됩니다" 한 줄을 이름과 함께 찍는다. 비거나 같은 토큰으로 뜨지 않던 진단을 걷는다
- [x] 접두사→자격 표에서 공유 토큰(`SharedToken`)을 걷는다. 표에 없는 경로의 기본값은 운영자 로그인이다. `create_app`은 토큰 인자를 받지 않는다
- [x] 공유 토큰의 권한 갈래(권한 넷을 가진 것으로 보던 것)와 운영자 경로 401의 `WWW-Authenticate: Bearer`를 걷는다. 최종 사용자 경로의 401은 그 머리를 지금 그대로 싣는다
- [x] `--host`가 루프백(그 컴퓨터 자신만 닿는 주소, `127.0.0.1` 같은 것)이 아닐 때의 진단 문구가 토큰을 말하는 자리를 로그인을 말하게 고친다. 루프백만 받는 규칙과 컨테이너 안의 예외(ADR 0056)는 그대로다
- [x] `tools/export_openapi.py`가 토큰 없이 앱을 짓는다. `openapi.json`이 바뀌면 같은 커밋에 싣는다

### 생성 클라이언트와 하네스

- [x] 토큰을 받는 옛 클라이언트 둘(`createAdminClient(adminToken)`, `createChannelClient(channelToken)`)을 걷고, 경로 목록을 고정한 타입 시험을 맞춘다
- [x] e2e 하네스(시험이 서버를 띄우고 준비하는 코드. `web/packages/e2e-stack` 패키지, 관리 화면·위젯·위젯 테스트 페이지의 `e2e/stack.ts`, `web/packages/e2e-standalone/e2e/`)가 두 토큰을 넣던 준비를 서버 명령으로 계정을 만들고 로그인하는 길로 바꾼다. 쿠키를 받는 길은 09가 관리 화면 e2e에서 잰 결과를 따른다
- [x] 파이썬 시험(`tests/test_server.py`, `tests/channel/http/`, `tests/test_main.py`)을 공유 토큰에서 로그인 도우미로 옮긴다
- [x] `tests/test_assistant_llm.py`의 `-m llm` 시험을 실제 `serve`에 로그인한 뒤 `Cookie` 머리를 직접 실어 `/runs`를 부르는 길로 바꾼다(05가 `tests/test_main.py`에서 들인 길과 같다)

### 배포 파일과 안내

- [x] `deploy/standalone/.env.example`과 루트 `.env.example`에서 두 토큰을 뺀다
- [x] `deploy/standalone/README.md`를 `토큰`과 `TOKEN` 둘로 grep해(187행처럼 변수 이름만 들고 한글 "토큰"이 없는 줄이 있다), 두 토큰을 말하거나 그 수에 기대는 문장을 모두 첫 계정과 로그인의 안내로 바꾼다(명세 "배포 안내"의 "토큰을 말하는 줄". 그 항목이 든 예 가운데 66행의 "세 번 쳐서"는 데이터베이스 비밀번호 하나만 남아 한 번이 된다). 로그인은 SSH 포트 포워딩으로 연 `http://127.0.0.1:3000/`에서 한다(14가 8443으로 바꾼다). 루트 `README.md`의 토큰 안내도 같이 고친다. `tests/tools/test_deploy_guide.py`의 필수 낱말을 맞춘다
- [x] 이 PR의 `docs/release-notes/upgrade/` 조각(판을 올리는 사람이 읽는 안내 한 토막)에 "`.env`의 `AGENT_OS_ADMIN_TOKEN`과 `AGENT_OS_CHANNEL_TOKEN`을 지우십시오. 남겨 두면 `serve`가 지우라는 줄을 찍습니다"와, 올린 뒤 첫 계정을 만드는 명령을 싣는다

### 규칙과 옛 표현

- [x] `.claude/rules/http.md`의 자격 항목에서 공유 토큰과 함께 받는 기간의 줄을 걷고 운영자 로그인을 적는다. 규칙 파일을 고치기 전에 Skill 도구로 `writing-for-agents`를 부른다
- [x] `AGENT_OS_ADMIN_TOKEN`, `AGENT_OS_CHANNEL_TOKEN`, `SharedToken`, `createAdminClient`, `createChannelClient`, "관리 토큰", "채널 토큰"을 저장소 전체에서 grep해 살아 있는 문서와 코드에 잔존이 0인지 본다(기록인 ADR과 일지와 릴리스 노트는 그대로 둔다). 예외는 둘이다. 이 티켓이 더한 "더 쓰지 않습니다" 줄과 그 시험(위 "서버"의 첫 항목과 아래 "시험"의 첫 항목)은 두 변수 이름을 일부러 쓴다. 이 기능의 명세와 티켓은 걷는 일을 적은 글이라 이름이 남는다

### 시험

- [x] 두 토큰 변수가 남은 `.env`로 `serve`가 뜨며 변수마다 "더 쓰지 않습니다" 줄을 이름과 함께 찍고 값을 찍지 않는다
- [x] 공유 토큰으로 운영자 경로를 부르면 401이고 `WWW-Authenticate`가 없다. 최종 사용자 경로의 401에는 그 머리가 있다

### 검증

- [x] `CLAUDE.md`의 검증 명령이 모두 초록이다
- [x] 서버 라우트와 api-client와 e2e 하네스를 모두 고치므로 관리 화면 e2e, 위젯 e2e, 위젯 테스트 페이지 e2e를 로컬에서 친다. 단독 배포 e2e(`pnpm -C web/packages/e2e-standalone exec playwright test`, Docker와 빈 80·443·3000 포트)도 로컬에서 친다. 그 잡의 시험은 base가 main인 PR에서만 돌고 dev로 가는 PR에서는 곧바로 성공으로 끝나기 때문이다(`.github/workflows/ci.yml`의 머리 주석)
- [x] `channel/`과 `main.py`를 고치므로 LLM 시험의 병합 조건 범위에 든다. `-m llm`, `-m llm_widget`, `-m llm_portal`을 치고, 로컬 모델 시험은 `--yes` 없이 쳐 예상 비용을 사용자에게 보이고 확인받은 뒤 돌린다
