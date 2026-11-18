# postgres-foundation 명세: serve는 표의 판이 맞는 PostgreSQL에 닿아야 뜨고, 단독 compose는 PostgreSQL과 한 번 도는 migrate를 더하며, 시험은 미리 띄운 테스트 컨테이너 하나를 함께 쓴다

Status: ready-for-agent

슬라이스 9(`postgres-foundation`). 설계는 설계 인터뷰(일지 2026-11-17-1747)와 ADR 0066이 정했고, 이 명세는 그 결정이 명세에 넘긴 자리를 채운다. 이 명세는 `/to-spec`으로 새 세션에서 썼고 설계 인터뷰를 다시 열지 않았다. 이 세션의 일지는 `docs/journal/2026-11-18-1544-postgres-foundation-spec.md`이고, 사람에게 물은 하나의 화면과 답이 거기 글자 그대로 있다. 용어는 `CONTEXT.md`의 단독 배포, 제품 판, 운영자, 배포 파일 묶음, 릴리스 노트, 노트 조각을 따른다. 이 명세의 "표의 판"은 ADR 0066 머리가 정한 말로, alembic(표를 만들고 올리는 도구)이 판 기록 표 `alembic_version`에 적는 마이그레이션의 번호이고 제품 판과 다르다. "코드를 읽었다"는 이 브랜치의 기준 커밋 `1aac0cfdd`(origin/dev)의 코드다. 측정은 `.scratch/postgres-foundation/probes/`이고, 폴더마다 재는 것과 다시 돌리는 명령과 잰 판은 그 `README.md`의 표에 있다. 측정은 모두 이 PC(Windows 10)의 Docker Desktop 위에서 돌았다. 서버와 Docker를 다시 켜는 갈래만 그 위에 띄운 Docker-in-Docker 컨테이너(컨테이너 안에서 도는 Docker 엔진) 안에서 흉내 냈다(Further Notes).

**넘겨받은 것은 아래 표의 서른 행이다.** ADR 0066 Consequences "명세가 짓는 것"이 늘어놓은 것을 물음 하나씩 나눈 열아홉, 같은 Consequences "재지 않은 것"이 명세에 넘긴 여덟 가운데 위 열아홉과 겹치지 않는 다섯, 같은 Consequences가 티켓에 넘겼지만 명세가 티켓이 쓸 내용을 적은 넷, 기능 계획 본문의 수락 조건 둘이다. "재지 않은 것"의 나머지 셋(권한과 상태 확인, `@`·`:`·`/`가 든 주소, alembic이 모르는 번호)과, 같은 물음을 다른 곳(ADR의 결정 본문, 설계 일지 2026-11-17-1747 "다음")이 다시 든 것은 그 행에 괄호로 붙였다. "재지 않은 것"이 첫 티켓에 넘긴 셋은 명세가 미리 쟀고 표에 넣지 않았다("의존성과 타입"). 답한 자리의 따옴표는 이 명세의 절 이름이다.

| 넘긴 곳 | 넘긴 것 | 답한 자리 |
|---|---|---|
| ADR 0066 Consequences "명세가 짓는 것" | 연결 문자열과 비밀번호의 변수 이름(결정 "serve와 데이터베이스"의 명령줄 인자를 둘지도) | "연결 문자열과 비밀번호의 변수" |
| 같은 문단 | 다시 시도하는 시간(같은 결정의 횟수도) | "뜰 때의 확인과 다시 시도" |
| 같은 문단 | `serve`가 멈출 때의 문구 전부 | "멈출 때의 글" |
| 같은 문단 | `migrate` 서비스와 PostgreSQL의 상태 확인과 `depends_on` 조건("재지 않은 것"의 상태 확인도) | "단독 compose의 PostgreSQL과 migrate" |
| 같은 문단 | PostgreSQL 컨테이너의 권한(결정 "compose 배치"와 "재지 않은 것"의 읽기 전용 루트와 권한 빼기도) | 같은 절 |
| 같은 문단 | 테스트용 compose 파일의 자리와 포트와 컨테이너 이름(결정 "테스트 데이터베이스"의 rag-engine 포트와 겹치지 않게도) | "테스트 컨테이너" |
| 같은 문단 | 템플릿 데이터베이스와 시험마다의 데이터베이스 이름(같은 결정의 세션 사이에 겹치지 않게도) | "시험 데이터베이스의 이름과 도우미" |
| 같은 문단 | 러너가 컨테이너를 띄우는 방법 | "러너가 테스트 컨테이너를 띄우는 길" |
| 같은 문단 | 컨테이너가 없을 때의 문구 | "멈출 때의 글"의 시험 쪽 표 |
| 같은 문단 | 포트의 이름과 메서드와 선언하는 자리(결정 "층과 조립"도) | "데이터베이스 포트와 조립" |
| 같은 문단 | 마이그레이션 파일의 `downgrade`(결정 "판 되돌리기"도) | "마이그레이션 파일" |
| 같은 문단 | 노트 검사의 짝 판정(결정 "승인 때 함께 확인받는 세부"도) | "노트 검사의 짝" |
| 같은 문단 | 데이터베이스를 쓰는 시험이 처음 무엇을 재는지 | Testing Decisions |
| 같은 문단 | digest(이미지의 내용으로 정해지는 고정 이름이라, 같은 digest는 늘 같은 이미지를 가리킨다)를 적는 세 자리가 같은지를 시험으로 고정할지(Consequences "CI"도) | "저장소 상태 시험" |
| 같은 문단 | compose 밖에서 `serve`를 띄우는 개발자가 붙는 데이터베이스(결정 "serve와 데이터베이스"도) | "개발 PC에서 serve가 붙는 데이터베이스" |
| 같은 문단 | `migrate`가 더 새 표의 판을 판정하는 자리(결정 "표를 올리는 때"와 "재지 않은 것"의 alembic이 모르는 번호에 내는 것도) | "표의 판을 견주는 자리" |
| 같은 문단 | `migrate` 서비스의 재시작 정책 | "단독 compose의 PostgreSQL과 migrate" |
| 같은 문단 | 비밀번호에 주소에서 뜻이 있는 글자가 들 때의 길(결정 "비밀번호와 계정"의 그런 글자가 없는 비밀번호를 만드는 명령을 배포 안내가 줄지와, "재지 않은 것"의 `@`·`:`·`/`가 든 주소를 SQLAlchemy가 읽는 방식도) | "비밀번호에 드는 글자" |
| 같은 문단 | 이미 데이터가 있는 볼륨에서 비밀번호를 바꾸는 길과 그 절차를 배포 안내에 적는 것 | "데이터베이스 비밀번호 바꾸기", "배포 안내" |
| ADR 0066 Consequences "재지 않은 것" | 작업자들(pytest를 프로세스 여럿으로 나눠 돌리는 xdist의 각 프로세스)이 컨테이너 하나를 나눠 쓸 때 템플릿 복제가 시험 하나에 드는 시간(결정 "테스트 데이터베이스"도) | "시험 데이터베이스의 이름과 도우미" |
| 같은 문단 | 빈 첫 마이그레이션으로 판 기록 표에 줄이 남는지(결정 "이 행이 짓는 표"와 설계 일지 "다음"도) | "마이그레이션 파일" |
| 같은 문단 | compose의 변수 치환에 연결 문자열에서 비밀번호를 떼어 낼 다른 문법이 없는지(결정 "비밀번호와 계정"도) | "연결 문자열과 비밀번호의 변수" |
| 같은 문단 | 테스트 도우미를 두 패키지의 시험이 함께 쓸 수 있는지(결정 "위젯 관리 서버"와 설계 일지 "다음"도) | "시험 데이터베이스의 이름과 도우미" |
| 같은 문단 | 서버가 다시 켜져 `serve`가 PostgreSQL보다 먼저 뜰 때 다시 시도와 재시작 정책으로 돌아오는지(결정 "compose 배치"도) | "뜰 때의 확인과 다시 시도" |
| ADR 0066 Consequences "운영"(compose에 PostgreSQL을 더하는 티켓의 몫) | 배포 안내 9절의 명령과 덮어쓰기 파일의 예를 PostgreSQL까지 고치고 고친 명령을 돌려 본 기록을 남기는 것 | "배포 안내" |
| 같은 문단(같은 티켓이 정한다) | 배포 안내 11절이 가운데 자리가 오른 판에 `compose.yaml`을 바꾸라고 적을지 | "배포 안내" |
| ADR 0066 Consequences "모두의 커밋"(데이터베이스 시험을 들이는 티켓의 몫) | 테스트 컨테이너라는 전제와 띄우는 명령을 적을 자리 여섯과 헌법 판 | "모두의 커밋(넘겨받은 것)" |
| ADR 0066 Consequences "재지 않은 것"(같은 티켓의 몫) | CI의 service container(GitHub Actions가 잡 옆에 함께 띄우는 컨테이너)에서 템플릿 복제가 도는지 | "CI" |
| 기능 계획 본문의 수락 조건 | 시험 환경에서 단독 compose를 띄우면 PostgreSQL이 함께 뜨고 `serve`가 닿으며, 내렸다 다시 띄워도 넣어 둔 줄이 남는다 | Testing Decisions의 넷째 |
| 같은 수락 조건 | 이 PC와 CI의 테스트가 데이터베이스를 스스로 띄워 돌고, 없으면 건너뛰지 않고 알린다 | "러너가 테스트 컨테이너를 띄우는 길", "CI", "멈출 때의 글"의 시험 쪽 표 |

**사용자가 고른 것은 하나이고 본문의 세 자리에 "사용자가 골랐다"로 표시했다.** 시험의 이음매 넷이다(Testing Decisions). 추천을 맨 앞에 둔 선택 화면으로 물었고 추천을 골랐다(일지 2026-11-18-1544 "사용자에게 물은 것 하나"). 그 답 하나가 셋을 함께 정해 세 자리에 나눠 표시했다. 이음매 넷(Testing Decisions 머리), 둘째 이음매가 `.claude/rules/http.md`의 예외를 "시작 단계"까지 넓히는 것("사용자가 이 넓힘을 골랐다"), 실제 `serve` 프로세스를 띄우는 시험을 기본 실행에 더하지 않는 것(둘째 이음매의 마지막 항목)이다. 고르지 않은 선택지는 Testing Decisions 끝의 "거부한 안:" 문단에 적었고, 그 설명의 원문은 그 일지에 있다.

**명세가 정한 것은 그 자리에 "명세가 정했다"로 표시했다.** 표시는 이 문단 밖에 스물이고, 모두 절 머리라 그 절 전체에 걸린다. 절 머리에 "명세가 미리 쟀다"라 적은 절 하나("의존성과 타입")는 ADR 0066이 첫 티켓에 넘긴 측정을 명세가 시제품으로 앞당겨 잰 것이고, "넘겨받은 것"이라 적은 절 하나("모두의 커밋")는 넘겨받은 일을 옮겨 적은 절이다. 표시가 없는 것(Testing Decisions에서 사용자가 고른 것 밖의 사례, Out of Scope, Further Notes)은 ADR 0066과 설계 일지, 기능 계획, 기존 규칙에서 왔거나, 표시한 결정을 시험과 문서로 옮긴 것이다.

**이력은 없다.** 명세가 채운 자리는 모두 ADR 0066이 명세에 넘긴 것이고, 채운 값이 ADR 0066의 문장을 거짓으로 만들지 않는다. ADR 0066이 어림으로 둔 문장 넷(빈 첫 마이그레이션으로 판 기록 표에 줄이 남는 것, 변수 치환에 다른 문법이 없는 것, 도우미를 두 패키지의 시험이 함께 쓰는 것, `serve`가 먼저 뜰 때 다시 시도와 재시작 정책이 받치는 것)은 측정이 그대로 세웠다. 거짓을 만들 안 둘은 그 까닭으로 거부했다. `serve`가 비밀번호를 따로 받는 안은 "compose 파일이 그 값으로 연결 문자열을 지어 `migrate`와 `serve`에 넘기며"를("비밀번호에 드는 글자"), 확인을 uvicorn 앞의 따로 연 루프에서 하는 안은 "앱은 수명이 열릴 때 연결과 표의 판을 확인하며"를("데이터베이스 포트와 조립") 거짓으로 만든다. ADR 0066이 ADR 0056 결정 "컨테이너 배치"의 "컨테이너는 root가 아닌 사용자로 돌고, 첫 프로세스에는 init을 둔다"에 단 포인터는 PostgreSQL 컨테이너의 권한을 명세에 넘긴다는 표시였다. 이 명세가 그 컨테이너를 uid(리눅스의 사용자 번호) 999와 init(첫 프로세스로 떠서 멈춤 신호를 넘기고 끝난 자식을 거두는 작은 프로그램)으로 띄우므로("단독 compose의 PostgreSQL과 migrate") 그 문장은 PostgreSQL에서도 참이고, ADR 0066의 "공식 PostgreSQL 이미지는 root로 뜨고"는 이미지의 기본값을 적은 사실이라 그대로 참이다.

**거부한 안은 아홉 자리에 "거부한 안:"으로 시작하는 문단으로 적었고, 그 문단들이 든 안은 스물이다.** 그 가운데 하나는 사용자에게 보인 선택지 가운데 고르지 않은 것이고, 그 문단에 그렇게 적었다(Testing Decisions).

## Problem Statement

운영자 관점. 0.1 판부터 운영자 계정과 로그인 상태를 PostgreSQL에 두기로 했는데(ADR 0062), 지금의 단독 배포에는 데이터베이스가 없다. 데이터베이스를 들이면 운영자가 새로 겪는 일이 생긴다. 비밀번호를 어디에 적는지, 판을 올릴 때 표를 누가 언제 올리는지, 옛 판으로 되돌렸을 때 무엇이 일어나는지, 서버를 다시 켰을 때 데이터베이스보다 `serve`가 먼저 뜨면 어떻게 되는지, 비밀번호를 바꾸려면 무엇을 해야 하는지다. 공식 PostgreSQL 이미지는 비밀번호를 데이터 폴더를 처음 만들 때만 쓰므로, 운영자가 `.env`의 비밀번호만 고치면 그다음부터 `serve`가 접속하지 못한다.

개발자(에이전트 세션) 관점. 데이터베이스를 쓰는 시험이 기본 실행에 들면, 같은 PC에서 여러 워크트리와 세션이 동시에 커밋할 때마다 데이터베이스가 있어야 한다. 시험끼리, 세션끼리 서로의 데이터를 건드리지 않아야 하고, 데이터베이스가 없을 때 시험이 건너뛰어 초록으로 보이면 안 된다(원칙 II). 실제 `serve`를 띄우는 e2e와 LLM 시험도 데이터베이스가 있어야 뜬다.

## Solution

`serve`는 환경 변수 `AGENT_OS_DATABASE_URL`로 연결 문자열을 받는다. 값이 없거나 읽히지 않으면 지금 토큰이 빠졌을 때처럼 이유를 찍고 종료 코드 1로 멈춘다. 값이 있으면 앱의 수명이 열릴 때 데이터베이스에 닿는지와 표의 판을 확인한다. 닿지 않으면 정해진 시간 동안 다시 시도하고, 그래도 닿지 않거나, 비밀번호를 받아들이지 않거나, 표의 판이 맞지 않으면 이유를 찍고 멈춘다. 지금 토큰이 빠졌을 때의 진단처럼 첫 줄이 이유이고, 갈래에 따라 두 칸 들인 둘째 줄이 할 일을 적는다. 찍는 글에는 비밀번호가 들지 않는다. 새 명령 `agent-os migrate`가 표를 마지막 판까지 앞으로만 올린다.

운영자는 `.env`에 `openssl rand -hex 32`로 만든 비밀번호 한 줄(`AGENT_OS_DATABASE_PASSWORD`)을 더한다. 단독 compose에는 PostgreSQL 컨테이너와 한 번 돌고 끝나는 `migrate` 서비스가 늘고, compose가 그 비밀번호로 연결 문자열을 지어 `migrate`와 `serve`에 넘긴다. `docker compose up -d --wait`를 치면 PostgreSQL이 준비된 뒤 `migrate`가 표를 올리고 끝나며, 그 뒤 `serve`가 뜬다. 판을 올릴 때도 같은 명령이다. 배포 안내에는 비밀번호를 바꾸는 절차와 PostgreSQL 이미지까지 인터넷이 막힌 서버로 옮기는 명령이 선다.

개발자의 PC에서는 저장소 루트의 테스트용 compose 파일이 PostgreSQL 하나를 데이터를 메모리에 둔 채 `127.0.0.1:25432`에 띄운다. 커밋 때 도는 러너가 그 컨테이너가 답하지 않으면 띄워 두고 내리지 않으며, 모든 워크트리와 세션이 그것을 함께 쓴다. 시험은 작업자마다 만든 템플릿 데이터베이스를 시험마다 복제해 깨끗한 데이터베이스를 받는다. 컨테이너가 없으면 시험은 띄우는 명령 한 줄과 함께 실패한다. CI는 같은 이미지를 잡마다 service container로 붙인다.

## User Stories

1. As an 운영자, I want 단독 compose를 띄우면 PostgreSQL이 함께 뜨기, so that 데이터베이스를 따로 설치하지 않는다.
2. As an 운영자, I want `.env`에 데이터베이스 비밀번호 한 줄만 더하면 되기, so that 비밀 값을 고칠 파일이 하나로 남는다.
3. As an 운영자, I want 비밀번호를 만드는 명령이 배포 안내에 있기, so that 주소를 깨는 글자가 든 비밀번호를 쓰지 않는다.
4. As an 운영자, I want 판을 올릴 때 판 번호만 바꾸고 `docker compose up -d`를 치면 표가 저절로 올라가기, so that 따로 칠 명령을 잊어 `serve`가 멈추는 일이 없다.
5. As an 운영자, I want `docker compose up -d --wait`가 `migrate`가 끝나고 `serve`가 정상이 될 때까지 기다린 뒤 성공으로 끝나기, so that 떴는지를 명령 하나의 결과로 안다.
6. As an 운영자, I want 표가 뒤처진 채로 `serve`를 띄우면 무엇을 먼저 칠지 한 줄로 알려 주기, so that 헤매지 않는다.
7. As an 운영자, I want 옛 판으로 되돌렸을 때 `migrate`와 `serve`가 표를 건드리지 않고 백업을 복원하라고 알려 주기, so that 옛 판이 새 표를 망가뜨리지 않는다.
8. As an 운영자, I want 서버를 다시 켜서 `serve`가 데이터베이스보다 먼저 뜨더라도 잠시 기다렸다 붙기, so that 재부팅 뒤에 손대지 않아도 서비스가 돌아온다.
9. As an 운영자, I want 비밀번호가 틀렸을 때는 기다리지 않고 바로 이유를 찍기, so that 다시 시도하는 시간만큼 헛되이 기다리지 않는다.
10. As an 운영자, I want 멈출 때 찍는 글에 비밀번호가 들지 않기, so that 컨테이너 기록이 비밀을 흘리지 않는다.
11. As an 운영자, I want 비밀번호가 맞지 않는다는 글이 비밀번호를 바꾸는 절차를 가리키기, so that `.env`만 고친 실수를 바로 안다.
12. As an 운영자, I want 이미 데이터가 있는 데이터베이스의 비밀번호를 바꾸는 절차가 배포 안내에 있기, so that 비밀번호를 바꾸다 서비스를 멈추지 않는다.
13. As an 운영자, I want 컨테이너를 내렸다 다시 띄워도 데이터베이스의 데이터가 남기, so that 판 올림이 데이터를 지우지 않는다.
14. As an 운영자, I want PostgreSQL이 밖으로 포트를 열지 않고 compose의 네트워크 안에서만 닿기, so that 밖에서 보이는 공격면이 늘지 않는다.
15. As an 운영자, I want PostgreSQL 컨테이너도 필요한 만큼의 권한으로만 돌기, so that 그 컨테이너가 뚫려도 호스트로 번지기 어렵다.
16. As an 운영자, I want 인터넷이 막힌 서버로 PostgreSQL 이미지까지 옮기는 명령이 배포 안내에 있기, so that 폐쇄망에서도 같은 판이 뜬다.
17. As an 운영자, I want 이 판으로 올릴 때 `compose.yaml`을 바꾸고 비밀번호 줄을 더하라는 할 일이 릴리스 노트에 서기, so that `v0.1.0-rc.1`에서 올린 뒤 `serve`가 뜨지 않는 일이 없다.
18. As an 운영자, I want 표를 바꾸는 판마다 노트의 "올릴 때 할 일"에 백업 안내가 서기, so that 되돌릴 길을 미리 마련한다.
19. As an 운영자, I want `/health`가 지금처럼 프로세스만 보기, so that 데이터베이스가 잠깐 끊겨도 상태 확인과 배포의 기다림이 흔들리지 않는다.
20. As an 운영자, I want 컨테이너가 몇 개 뜨고 `migrate`가 끝난 뒤 어떤 상태로 보이는지 배포 안내가 적기, so that 끝난 `migrate`를 고장으로 오해하지 않는다.
21. As a 개발 세션, I want 커밋 때 도는 러너가 테스트 컨테이너가 없으면 스스로 띄우기, so that 데이터베이스 시험 때문에 커밋 전에 따로 칠 것이 없다.
22. As a 개발 세션, I want 손으로 친 pytest가 컨테이너가 없으면 띄우는 명령 한 줄과 함께 실패하기, so that 건너뛴 시험을 초록으로 읽지 않는다.
23. As a 개발 세션, I want 여러 워크트리와 세션이 컨테이너 하나를 함께 써도 서로의 데이터베이스를 건드리지 않기, so that 동시에 커밋해도 시험이 엉키지 않는다.
24. As a 개발 세션, I want 시험마다 깨끗한 데이터베이스를 빠르게 받기, so that 시험이 서로의 줄에 기대지 않고 전체 시험 시간도 크게 늘지 않는다.
25. As a 개발 세션, I want 테스트 컨테이너의 포트와 이름이 rag-engine의 것과 겹치지 않기, so that 두 저장소의 시험을 한 PC에서 함께 돌린다.
26. As a 개발 세션, I want 개발 PC에서 `serve`를 띄울 데이터베이스와 명령이 README에 있기, so that 위젯으로 확인할 때 데이터베이스를 따로 마련하지 않는다.
27. As a 개발 세션, I want e2e와 LLM 시험이 자기 데이터베이스를 만들고 `migrate` 뒤에 `serve`를 띄우기, so that 실제 `serve`를 띄우는 시험이 데이터베이스 때문에 깨지지 않는다.
28. As a 개발 세션, I want 새 마이그레이션 파일을 더한 PR의 제목에 느낌표가 없으면 노트 검사가 빨갛기, so that 표를 바꾸는 판의 노트에서 백업 안내가 빠지지 않는다.
29. As a 개발 세션, I want 마이그레이션 번호가 겹치거나 건너뛰거나 되돌리는 함수가 들면 시험이 빨갛기, so that 나란히 짠 두 브랜치가 같은 번호를 들고 와도 병합 전에 안다.
30. As a 개발 세션, I want PostgreSQL 이미지를 적는 세 자리가 어긋나면 시험이 빨갛기, so that 배포와 시험과 CI가 다른 판으로 돌지 않는다.
31. As a 개발 세션, I want core나 HTTP 층이 데이터베이스 라이브러리를 import하면 경계 검사가 빨갛기, so that 데이터베이스 코드가 어댑터 한 곳에 머문다.
32. As a 개발 세션, I want `serve`의 시작 확인을 실제 데이터베이스 없이 가짜로 시험하기, so that 그 시험이 빠르고 데이터베이스의 상태에 흔들리지 않는다.
33. As a 개발 세션, I want CI의 잡이 배포와 같은 이미지의 데이터베이스를 붙여 돌기, so that 이 PC와 CI가 같은 것을 시험한다.
34. As an admin-login 세션, I want 표를 더하는 마이그레이션의 꼴과 그 PR의 규칙이 명세에 있기, so that 첫 표를 이 행의 규약대로 바로 짓는다.
35. As a widget-admin-server 세션, I want 테스트 도우미를 다른 패키지의 시험에서 쓰는 길이 명세에 있기, so that 위젯 관리 서버의 시험이 같은 컨테이너를 쓴다.
36. As an ops-backup-upgrade 세션, I want 볼륨과 계정과 데이터베이스의 이름이 명세에 있기, so that 백업과 복원 명령을 그 이름으로 짓는다.
37. As a diag-bundle 세션, I want `serve`와 `migrate`가 멈출 때 찍는 글의 목록이 명세에 있기, so that 진단 묶음이 어떤 줄을 모을지 안다.
38. As a 플러그인 개발자, I want 데이터베이스 없이 `serve`를 띄웠을 때의 글이 무엇을 할지 알려 주기, so that 처음 띄울 때 막히지 않는다.
39. As an 운영자, I want 처음 띄우기가 끊겨 데이터베이스가 반쯤 만들어졌을 때 멈춘 글이 고치는 길을 가리키기, so that 다시 띄워도 뜨지 않는 까닭을 헤매지 않는다.

## Implementation Decisions

구현 파일의 경로와 코드 조각은 새로 짓지 않는다. 규칙 문서·ADR·시험 선례의 경로와, ADR 0066이 명세에 이름을 짓게 넘긴 것(환경 변수, 테스트용 compose 파일의 자리, 데이터베이스와 컨테이너의 이름, 포트의 이름과 메서드)과 다른 기능과 세션이 쓰고 읽는 자리(마이그레이션 파일의 꼴, 멈출 때의 글)는 적는다. 프로브의 시제품이 결정을 글보다 정확히 담는 부분은 옮기고 그렇게 적는다.

### 연결 문자열과 비밀번호의 변수(명세가 정했다)

- `serve`와 `agent-os migrate`는 연결 문자열을 환경 변수 `AGENT_OS_DATABASE_URL` 하나로만 받는다. 명령줄 인자는 두지 않는다. 연결 문자열에는 비밀번호가 들어 있고, 명령줄 인자는 같은 기계의 다른 사용자가 프로세스 목록으로 볼 수 있기 때문이다. 지금의 두 토큰도 환경 변수로만 받는다(`src/agent_os/main.py`를 읽었다).
- 값의 꼴은 `postgresql://계정:비밀번호@호스트:포트/데이터베이스`다. 드라이버 이름이 붙은 꼴(`postgresql+asyncpg://`)이나 다른 이름은 받지 않는다. 어댑터가 읽은 뒤 드라이버를 asyncpg로 바꿔 붙는다. 그래서 운영자와 개발자는 드라이버를 몰라도 되고, 드라이버를 바꾸는 날에도 운영자의 값은 그대로다.
- 단독 배포의 `.env`에는 비밀번호 한 줄 `AGENT_OS_DATABASE_PASSWORD`만 둔다(ADR 0066 결정 "비밀번호와 계정"). 계정과 데이터베이스의 이름은 모두 `agent_os`이고 compose 파일에 적는다. compose는 `postgresql://agent_os:${AGENT_OS_DATABASE_PASSWORD}@postgres:5432/agent_os`를 지어 `migrate`와 `serve`의 `AGENT_OS_DATABASE_URL`로 넘기고, 같은 비밀번호를 PostgreSQL 컨테이너의 `POSTGRES_PASSWORD`로 넘긴다. `.env`에 그 줄이 없을 때 compose가 무엇을 하는지는 아래 "단독 compose의 PostgreSQL과 migrate"가 정한다.
- compose의 변수 치환에는 연결 문자열 한 줄에서 비밀번호를 떼어 낼 문법이 없다. Compose 명세와 Docker 문서와 구현(compose-go v2.16.1의 `template/template.go`)의 원문을 받아 대 보았다. 이름 뒤에 올 수 있는 것으로 Compose 명세는 `:-`, `-`, `:?`, `?` 넷을 적고, Docker 문서는 거기에 `:+`, `+`를 더한 여섯을 적으며, 구현도 그 여섯만 받는다. 두 문서는 그 밖의 셸 꼴(`${VARIABLE/foo/bar}` 같은 것)을 받지 않는다는 문장으로 끝난다. Docker Compose 5.6.1은 `#`, `%`, `##`, `/`, `:0:6`, `${#V}`를 모두 `invalid interpolation format`으로 거부했다(`.scratch/postgres-foundation/probes/compose_shape/README.md` 5가와 "받아 읽은 원문"). 그래서 ADR 0066이 어림으로 둔 "다른 문법이 없다"가 섰고, 비밀번호 한 줄에서 주소를 짓는 길이 남는다.

거부한 안: 연결 문자열 전체를 `.env`의 한 줄로 둔다. PostgreSQL 컨테이너에 넘길 비밀번호를 그 줄에서 꺼낼 수 없어, 운영자가 같은 비밀번호를 두 줄에 적게 된다(ADR 0066 결정 "승인 때 함께 확인받는 세부"의 셋째). 명령줄 인자 `--database-url`을 더 둔다. 위의 프로세스 목록 까닭으로 두지 않는다.

### 비밀번호에 드는 글자(명세가 정했다)

compose는 비밀번호를 고치지 않고 연결 문자열에 그대로 끼워 넣으므로(ADR 0066이 손으로 봤다), 주소에서 뜻이 있는 글자가 든 비밀번호는 주소를 깨뜨릴 수 있다. 그렇게 지은 주소를 SQLAlchemy가 읽고 접속하는 것을 `.scratch/postgres-foundation/probes/stack/`이 쟀다(그 README "비밀번호의 글자"). 깨진 것은 셋이다. `p@ss`는 주소가 비밀번호 `p`와 호스트 `ss@127.0.0.1`로 읽혀 닿지 못했다. `p@s:s/w`는 읽을 때 `ValueError`였다. `p%41ss`는 `%41`이 `A`로 풀려 비밀번호가 맞지 않았다. 16진수 64자, `:`, `/`, `%ss`, `?`, `#`, 빈칸, `+`, `&`, 한글이 든 비밀번호와, 값을 주소에 맞게 바꿔 지은 주소와 `URL.create`로 지은 주소는 모두 접속했다.

- 배포 안내는 비밀번호를 `openssl rand -hex 32`로 만들라고 적고(관리 토큰과 같은 명령이다, 배포 안내 3-1), 영문자와 숫자만 쓰라고 적는다. 까닭은 위 측정이다. `@`가 들면 주소의 자리가 바뀌거나 주소를 읽지 못하고, `%` 뒤에 16진수 두 자리가 오면 다른 비밀번호로 풀린다. `:`와 `/`는 혼자 들었을 때는 접속했지만 `@`와 함께 들면 주소를 읽지 못했다(`p@s:s/w`). 영문자와 숫자만 쓰면 이 갈래가 하나도 생기지 않는다.
- `serve`와 `migrate`는 연결 문자열에 `@`가 둘 이상이면 그 주소를 읽지 못한 것으로 본다(아래 "멈출 때의 글"의 "읽지 못했다"). 계정과 비밀번호를 호스트와 가르는 `@`는 하나여야 하므로, 둘째 `@`는 비밀번호나 계정에 든 것이다. SQLAlchemy는 비밀번호를 첫 `@` 앞에서 자르고 나머지를 호스트·포트·데이터베이스·질의로 읽으므로, 이 판정이 없으면 비밀번호의 조각이 그 자리에 들어가 닿지 못했다는 글의 자리(`<자리>`)에 찍힌다(원칙 V). 같은 프로브가 compose가 짓는 꼴에 열여섯 값을 넣어 견주었다. SQLAlchemy가 호스트·포트·데이터베이스를 다르게 읽은 다섯(`p@ss`, `p@s:s/w`, `x@h/db`, `x@h?q=1`, `x@h:1/db`)은 모두 `@`가 둘 이상이었고, 이 판정이 다섯을 모두 거부하고 나머지 열하나는 하나도 거부하지 않았다(그 README "비밀번호의 글자"). 읽은 호스트에 `@`가 드는지만 보는 판정은 뒤의 셋을 놓친다. 셋 모두 호스트가 `h`로 읽혀 `@`가 남지 않기 때문이다. 이 판정은 계정 이름이나 질의에 `@`가 든 주소도 받지 않는다. 이 배포의 주소에는 둘 다 없다(계정은 `agent_os`이고 질의를 붙이지 않는다). 읽을 때 `ValueError`가 나는 꼴도 같은 갈래이고, 값을 되울리지 않는다.
- `%` 뒤에 16진수 두 자리가 오는 비밀번호는 주소의 자리가 그대로이고 비밀번호만 달라지므로 위 판정이 받고, 접속에서 위 "멈출 때의 글"의 "비밀번호" 갈래로 나온다. 그 글의 둘째 줄이 바꾼 비밀번호를 확인하라고 가리킨다.

거부한 안: `serve`가 비밀번호를 따로 받아 `URL.create`로 주소를 짓는다(비밀번호의 글자를 가리지 않는다). `serve`가 받는 변수가 둘이 되고, ADR 0066의 "compose 파일이 그 값으로 연결 문자열을 지어 `migrate`와 `serve`에 넘기며"가 거짓이 된다. 운영자가 비밀번호를 스스로 고르는 일은 안내의 명령으로 줄인다.

### 데이터베이스 포트와 조립(명세가 정했다)

- 포트의 이름은 `Database`이고 `agent_os.http`에 선언한다. ADR 0062가 계정과 로그인 상태의 포트를 `agent_os.http`에 두기로 한 자리와 같다. 메서드는 둘이다. `startup_problem()`은 데이터베이스에 닿아 표의 판을 견주고, 문제가 없으면 없음을, 있으면 멈출 때의 글(아래 "멈출 때의 글")을 돌려준다. `close()`는 연결 묶음을 닫는다. 둘 다 비동기다. 어댑터는 이 포트를 import하지 않고 시그니처로 만족한다(원칙 IV, ADR 0016).
- 포트가 SQLAlchemy의 타입을 주고받지 않으므로 SQLAlchemy는 `agent_os.adapters` 밖으로 나가지 않는다(ADR 0066 결정 "층과 조립"). 계정과 로그인 상태의 저장 포트는 admin-login이 같은 층에 더하고, 같은 어댑터 객체가 그 포트들도 만족할 수 있다.
- `main`이 `AGENT_OS_DATABASE_URL`을 읽어 어댑터의 데이터베이스 객체를 짓고 `create_app`에 넘긴다. 다시 시도한다는 알림(아래)을 찍을 자리로 표준 오류를 함께 넘긴다. `create_app`은 그 객체를 받는 인자를 하나 더하고, 그 인자는 기본값이 없다. `serve`가 도는 길이 하나라서(ADR 0066 결정 "serve와 데이터베이스") 데이터베이스 없는 앱을 짓는 길을 두지 않는다. 데이터베이스가 필요 없는 기존 시험은 가짜 데이터베이스를 넘긴다. 계약 파일을 뽑는 `tools/export_openapi.py`도 `create_app`을 부르고, 지금 포트마다 불리면 곧바로 터지는 자리표시자(`_SchemaOnlyPlugins` 등)를 넘긴다(코드를 읽었다). 데이터베이스에도 같은 꼴의 자리표시자를 넘긴다. 스키마를 뽑는 데는 수명이 돌지 않으므로 그 자리표시자는 불리지 않는다. 그 도구는 `app.openapi()`만 부르고(158줄), 수명 함수가 예외를 던지게 둔 FastAPI 앱에서 `openapi()`는 수명을 열지 않았다. 같은 앱을 `TestClient`로 열면 열렸다(손으로 봤다).
- 확인하는 자리는 `create_app`이 앱에 더하는 순수 ASGI 미들웨어(요청이 앱에 닿기 전에 가로채는 층)다. 수명이 열리는 첫 메시지를 받으면 앱의 시작 단계보다 먼저 `startup_problem()`을 부른다. 글이 오면 연결 묶음을 닫고, 앱의 시작 단계를 부르지 않은 채 `lifespan.startup.failed`에 그 글을 실어 보낸다. 그래서 MCP 서버 같은 앱의 시작 일은 하나도 돌지 않는다. 글이 없으면 앱의 수명을 그대로 돌리고, 수명이 끝나면 연결 묶음을 닫는다. ADR 0066의 "앱은 수명이 열릴 때 연결과 표의 판을 확인하며 수명이 닫힐 때 연결 묶음을 닫는다"를 이 자리가 맡는다. 시제품은 `.scratch/postgres-foundation/probes/stack/proto/gate.py`이고 마흔 줄이다.
- 이 자리를 고른 까닭은 uvicorn이 내는 것이다(같은 프로브 README "uvicorn의 실패 출력"). 미들웨어가 두 줄 글(아래 "멈출 때의 글")을 실어 `lifespan.startup.failed`를 보내면 uvicorn은 시작 알림 두 줄(`Started server process`, `Waiting for application startup.`), `ERROR: <첫 줄>`, 두 칸 들여쓴 둘째 줄 그대로, `ERROR: Application startup failed. Exiting.`의 다섯 줄만 찍고 역추적 없이 종료 코드 3으로 끝났다. 같은 확인을 FastAPI의 수명 함수에서 예외로 던지면 역추적이 붙어 15줄이었다. 꺼질 때는 확인이 한 번, 닫기가 한 번 불렸다. 윈도 호스트에서 uvicorn을 띄워 잰 것이고, 리눅스 컨테이너의 `serve`가 같은 줄을 찍는지는 재지 않았다(그 README "재지 못한 것").
- 그래서 `serve`의 종료 코드는 둘로 갈린다. 연결 문자열이 없거나 읽히지 않는 구성 오류는 지금의 구성 오류처럼 1이고, 뜰 때의 확인에서 멈추면 uvicorn의 시작 실패 코드 3이다. 명령줄 실행(`agent-os run`)의 3(멈춤)과 숫자가 같지만 다른 명령이다. `serve`가 3을 1로 바꾸게 하지 않는다. uvicorn이 시작 실패에서 프로세스를 끝내는 길을 가로채야 하고, compose의 재시작 정책은 종료 코드를 가리지 않는다.
- 기존 시험이 쓰는 `app.router.lifespan_context(app)`은 미들웨어를 지나지 않는다(`tests/test_main.py` 1668줄 근처를 읽었다). 그 시험들은 가짜 데이터베이스를 넘기고 그대로 둔다. 미들웨어를 지나는 시험은 아래 Testing Decisions의 둘째가 따로 짓는다.

거부한 안: `main`이 uvicorn을 부르기 전에 따로 이벤트 루프를 열어 확인한다. 확인과 앱이 다른 루프에서 연결을 열게 되어 연결 묶음을 두 번 짓고, ADR 0066의 "앱은 수명이 열릴 때 연결과 표의 판을 확인하며"가 거짓이 된다. 수명 함수에서 예외로 던진다. 위의 역추적이 운영자에게 보인다.

### 뜰 때의 확인과 다시 시도(명세가 정했다)

- "닿았다"는 연결 하나를 열어 판 기록 표의 판을 읽은 것이다. 읽은 판을 견주는 것은 아래 "표의 판을 견주는 자리"다.
- 실패는 갈래 다섯으로 가른다. 갈래는 예외의 클래스가 아니라 예외와 그 원인 사슬에서 찾은 PostgreSQL의 오류 번호(SQLSTATE)와 `OSError` 여부로 가른다. SQLAlchemy가 드라이버의 예외를 `DBAPIError`로 감싸서 오기 때문이고(같은 README "접속 실패의 꼴"), 그래야 asyncpg를 import하지 않아 스텁 없이 pyright strict를 지난다(아래 "의존성과 타입").
  1. 잠시 뒤 다시 시도할 것: 오류 번호가 없고 사슬에 `OSError`가 있는 것(접속 거부, 이름 풀이 실패, 시도의 제한 시간, 끊긴 연결), 오류 번호가 08로 시작하는 것(연결 예외), 57P03(데이터베이스가 아직 시작하는 중). `docker kill -s KILL`로 죽인 PostgreSQL이 복구하는 동안 접속이 받은 것이 57P03과 오류 번호 없는 `ConnectionError`였다(같은 README, 한 회차에 57P03 487번과 `ConnectionError` 12번). 서버를 다시 켠 직후의 복구도 같은 것을 낸다고 본다(어림. 서버를 다시 켜는 갈래는 restart_recover 프로브가 psql 대역으로 재서 오류 번호를 보지 않았다, 아래 "서버나 Docker가 다시 켜질 때"). 08 계열은 만들어 보지 못했고, 연결 예외의 번호라 이 갈래에 넣은 것은 PostgreSQL의 오류 번호 표를 기억에 기대어 읽은 어림이다(같은 README). compose의 서비스 이름은 그 컨테이너가 서기 전에 풀리지 않으므로 이름 풀이 실패도 이 갈래다.
  2. 비밀번호: 28P01. 다시 시도하지 않고 바로 멈춘다. 닿았지만 받아들이지 않은 것이라 기다려도 바뀌지 않는다.
  3. 접속을 허락하지 않음: 28000. 바로 멈춘다. 서버의 접속 규칙(`pg_hba.conf`)에 그 접속을 허락하는 줄이 없거나 로그인을 막은 계정(`NOLOGIN`)이다. 같은 프로브가 둘을 만들어 잰 오류 번호가 모두 28000이었다(접속 규칙에서 TCP 줄을 지운 서버는 `no pg_hba.conf entry for host …`, 로그인을 막은 계정은 `role "…" is not permitted to log in`). 처음 띄우기가 끊긴 볼륨에서 PostgreSQL이 다른 컨테이너의 접속을 같은 `no pg_hba.conf entry`로 거절했다(`.scratch/postgres-foundation/probes/restart_recover/README.md` 항목 4). 그 볼륨이 실제로 낸 오류 번호는 대역이 psql이라 보지 않았고, 같은 문구라 같은 28000이라고 읽는다(어림). 비밀번호와 나눈 까닭은 멈출 때의 글이 가리키는 곳이 다르기 때문이다(아래 "멈출 때의 글").
  4. 데이터베이스 없음: 3D000. 바로 멈춘다.
  5. 그 밖: 바로 멈춘다.
- 다시 시도하는 시간은 30초이고, 시도 사이에 1초를 쉰다. 첫 실패 뒤에 알림 한 줄을 표준 오류에 찍고(아래 "멈출 때의 글"), 그 뒤로는 찍지 않는다. 시간은 시도 사이에서만 보므로, 마지막 시도가 그 시간을 넘겨 시도 하나의 제한 시간만큼 더 걸릴 수 있다.
- 시도 하나에는 5초의 제한 시간을 건다. 접속은 받되 답하지 않는 서버에서 제한 시간이 없으면 정한 시간을 넘겨 기다렸다(같은 README, 3초로 정한 다시 시도가 제한 시간 없이는 10초 뒤에도 기다렸고, 시도마다 1초를 걸자 4.0~4.1초에 돌아왔다). 윈도에서는 거부된 접속 한 번이 2초 가까이 걸렸으므로(같은 README) 5초는 거부를 시간 초과로 잘못 읽지 않는다.
- 연결 묶음은 꺼낼 때마다 연결이 살아 있는지 확인한다(SQLAlchemy의 `pool_pre_ping`). 데이터베이스를 다시 띄운 뒤 그 확인이 없으면 첫 질의가 `InterfaceError`로 실패했고, 있으면 첫 질의가 성공했다(같은 README "쉬던 연결"). 운영 중에 데이터베이스가 내려갔다 올라와도 `serve`를 다시 띄우지 않아도 된다.
- `migrate`도 같은 확인과 다시 시도를 한다. compose에서 `migrate`는 PostgreSQL의 상태 확인이 정상이 된 뒤에 뜨지만, 손으로 친 `migrate`와 개발 PC에서도 같은 길로 돈다.
- **서버나 Docker가 다시 켜질 때.** 근거는 `.scratch/postgres-foundation/probes/restart_recover/`다. 그 프로브는 PostgreSQL, 한 번 도는 `migrate`, `serve`의 배치를 Docker-in-Docker 컨테이너 안의 엔진에 띄우고, Docker만 다시 켜기, 서버를 정상으로 껐다 켜기, 전원 끊김의 세 사건을 냈다. `migrate`와 `serve`는 `psql`로 접속을 되풀이하는 셸 대역이었고, `serve` 대역의 다시 시도 시간을 0초, 5초, 30초로 바꿔 사건마다 세 번씩 모두 27번 돌렸다(그 README "결과"). 아래 값은 마지막 전체 실행의 것이다.
  - 27번 모두 PostgreSQL과 `serve`가 사람 손 없이 다시 떴다. `migrate`는 `exited(0)` 그대로 다시 돌지 않았고, 사건 전에 넣은 줄이 남았다. `serve`가 PostgreSQL보다 먼저 뜬 것이 사건마다 아홉 번 가운데 서너 번이었다. 그래서 ADR 0066 결정 "compose 배치"가 어림으로 둔 "`serve`가 PostgreSQL보다 먼저 뜰 수 있다고 보고, 그때는 `serve`의 다시 시도와 재시작 정책이 받친다고 본다"가 섰다.
  - 다시 시도 시간이 30초면 아홉 번 모두 `serve`가 재시작 없이 첫 삶에서 붙었고, 처음 뜬 뒤 붙기까지 가장 길게 0.70초였다. 바로 앞의 전체 실행에서는 전원 끊김 뒤 PostgreSQL이 복구에 몇 초를 써 5.09초까지 갔다(그 README "시간의 분포" 아래 둘째 항목. 그 두 회차의 PostgreSQL은 컨테이너가 시작한 뒤 4.41·3.57초에야 접속을 받는다는 기록을 찍었다).
  - 다시 시도 시간이 0초여도 아홉 번 모두 붙었다. 일곱 번은 첫 시도가 실패해 1로 끝난 뒤 재시작 정책이 다시 띄워 붙었다. 다시 시도가 없어도 재시작 정책이 받치는 셈이다. 그래서 다시 시도 시간이 맡는 몫은, 다시 켤 때마다 운영자가 보는 기록에 멈춤 글이 남지 않게 하는 것이다.
  - PostgreSQL 프로세스가 죽은 때부터 접속을 받는다는 기록(`database system is ready to accept connections`)이 찍히기까지 가장 오래 걸린 것은 표에 많은 줄을 쓴 직후 죽은 회차다. 마지막 전체 실행에서는 2.91·3.18초였고, 그 앞의 실행에서 6.92초까지 갔다(그 README 항목 3). 다른 컨테이너에서 새로 건 접속은 그 기록보다 0.04~2.75초 늦게 처음 됐다(같은 README "시간의 분포" 아래 넷째 항목. 그 늦음에는 측정 대역이 시도마다 건 제한 시간이 든다). 데이터베이스가 크면 복구가 이보다 길 수 있다(어림, 그 README "재지 못한 것"). 잰 가장 긴 값에 그 늦음을 더해도 10초가 안 되어 30초는 그 세 배쯤이고, 그보다 길어지면 재시작 정책이 받친다.
  - `migrate`는 재시작 정책이 `"no"`라 다시 시도 말고는 받쳐 줄 것이 없다. compose가 `depends_on`을 기다리지 않고 `migrate`를 PostgreSQL보다 먼저 띄우는 `docker compose restart`(아래 "단독 compose의 PostgreSQL과 migrate")에서는 이 30초가 받친다고 본다(어림).
  - 붙기 전에 대역이 받은 거절은 `Connection refused`, `FATAL: the database system is starting up`, `FATAL: the database system is not yet accepting connections`였다. 앞의 것은 위 갈래 1의 `OSError`다. 대역은 psql이라 오류 번호를 싣지 않으므로, 뒤의 둘이 stack 프로브가 복구 중에 받은 57P03과 같은 번호라는 것은 어림이다. PostgreSQL이 꺼지는 동안 들어온 접속에 찍힌 `the database system is shutting down`도 그 번호라고 본다(어림). 그 번호가 아니면 갈래 5로 바로 멈추고, 재시작 정책이 다시 띄운다.
  - PostgreSQL 컨테이너가 멈춰 있을 때 대역은 이름 풀이 실패 한 번에 6.6초쯤 썼다(그 README "실패의 문구"). 실제 `serve`에서는 시도 하나의 제한 시간 5초가 그것을 끊고, 시간 초과는 갈래 1이라 다시 시도한다고 본다(어림).

### 멈출 때의 글(명세가 정했다)

`serve`와 `migrate`가 멈출 때와 다시 시도할 때 찍는 글은 아래가 전부다. 글은 ADR 0066이 정한 두 문장에 맞춰 높임말로 쓴다. 지금의 토큰 글(`src/agent_os/main.py`의 `_NO_ADMIN_TOKEN_DIAGNOSTIC` 등)은 그대로 둔다. 글의 꼴은 지금의 진단과 같다. 첫 줄이 이유이고, 둘째 줄부터는 두 칸 들여 설명한다. 영문 이름 뒤에는 지금의 진단처럼 조사 앞에 한 칸을 띄운다.

`<자리>`는 주소의 `호스트:포트/데이터베이스`다. 계정과 비밀번호는 싣지 않는다. `<까닭>`은 오류 번호가 있으면 `오류 번호 <번호>`, 없으면 사슬에서 찾은 가장 안쪽 `OSError`의 클래스 이름(`ConnectionRefusedError`, `gaierror`, `TimeoutError` 등), 그것도 없으면 바깥 예외의 클래스 이름이다. 드라이버가 낸 글은 싣지 않는다. 드라이버의 글에 계정 이름이나 주소의 조각이 섞일 수 있어서다. `<초>`는 다시 시도하는 시간이다. `<판>`은 판 기록 표의 번호이고, 표가 없으면 `없음`이다.

| 갈래 | 누가 | 종료 코드 | 글 |
|---|---|---|---|
| 변수가 없거나 비었다 | `serve`, `migrate` | 1 | `AGENT_OS_DATABASE_URL 이 비어 있습니다. serve 와 migrate 는 PostgreSQL 데이터베이스가 있어야 돕니다(ADR 0066).` / `  단독 배포에서는 compose 가 .env 의 AGENT_OS_DATABASE_PASSWORD 로 이 값을 짓습니다. 개발 PC 의 값은 README 에 있습니다.` |
| 읽지 못했다 | `serve`, `migrate` | 1 | `AGENT_OS_DATABASE_URL 을 읽지 못했습니다. postgresql://계정:비밀번호@호스트:포트/데이터베이스 꼴이어야 합니다.` / `  값에는 비밀번호가 들어 있어 여기 찍지 않습니다. 비밀번호에 @ 가 들면 주소를 읽지 못하므로, 비밀번호는 영문자와 숫자만 씁니다.` |
| 다시 시도한다(멈추지 않는다) | `serve`, `migrate` | 없음 | `데이터베이스(<자리>)에 아직 닿지 못해 최대 <초>초 동안 다시 시도합니다.` |
| 닿지 못했다 | `serve`, `migrate` | `serve` 3, `migrate` 1 | `데이터베이스(<자리>)에 닿지 못했습니다. <초>초 동안 다시 시도했습니다(<까닭>).` |
| 비밀번호 | `serve`, `migrate` | `serve` 3, `migrate` 1 | `데이터베이스(<자리>)가 계정이나 비밀번호를 받아들이지 않았습니다(<까닭>).` / `  .env 의 비밀번호만 바꿨다면 데이터베이스 안의 비밀번호도 바꿔야 합니다. 배포 안내의 "데이터베이스 비밀번호 바꾸기"를 보십시오.` |
| 접속을 허락하지 않았다 | `serve`, `migrate` | `serve` 3, `migrate` 1 | `데이터베이스(<자리>)가 이 접속을 허락하지 않았습니다(<까닭>).` / `  처음 띄우기가 끝나기 전에 서버가 꺼졌다면 데이터베이스가 반쯤 만들어진 채 남았을 수 있습니다. 배포 안내의 "띄우기가 끊겼을 때"를 보십시오.` |
| 데이터베이스 없음 | `serve`, `migrate` | `serve` 3, `migrate` 1 | `데이터베이스(<자리>)가 없습니다(<까닭>). 주소의 데이터베이스 이름을 확인하십시오.` / `  처음 띄우기가 끝나기 전에 서버가 꺼졌다면 데이터베이스가 반쯤 만들어진 채 남았을 수 있습니다. 배포 안내의 "띄우기가 끊겼을 때"를 보십시오.` |
| 그 밖 | `serve`, `migrate` | `serve` 3, `migrate` 1 | `데이터베이스(<자리>)에 접속하지 못했습니다(<까닭>).` |
| 표가 뒤처졌다 | `serve` | 3 | `데이터베이스의 표가 이 판보다 뒤처져 있습니다. agent-os migrate 를 먼저 돌리십시오.` / `  표의 판은 <판>이고 이 판의 마지막 판은 <판>입니다.` |
| 표가 더 새롭다 | `serve`, `migrate` | `serve` 3, `migrate` 1 | `데이터베이스가 이 판보다 새롭습니다. 되돌리려면 올리기 전의 백업을 복원하십시오.` / `  표의 판은 <판>이고 이 판이 아는 마지막 판은 <판>입니다.` |
| 올렸다 | `migrate` | 0 | `표를 <판>에서 <판>으로 올렸습니다.` |
| 이미 마지막 판이다 | `migrate` | 0 | `표가 이미 마지막 판(<판>)입니다.` |
| 올리다 실패했다 | `migrate` | 1 | `표를 올리다 실패했습니다(<까닭>). 표의 판은 올리기 전 그대로 <판>입니다.` 뒤에 그 예외의 역추적을 찍는다 |

- 표가 뒤처진 글의 뒷 문장(`agent-os migrate 를 먼저 돌리십시오.`)과 더 새로운 표의 두 문장은 ADR 0066 결정 "표를 올리는 때"에서 왔다. ADR의 글에서 바꾼 것은 셋이다. 명령 이름을 감싼 백틱을 지웠고, 영문 이름 뒤 조사 앞에 한 칸을 띄웠으며(위 글의 꼴), ADR이 따옴표 안에서 마침표 없이 끝낸 문장 끝에 마침표를 달았다. 뒤처진 글의 앞 문장(`데이터베이스의 표가 이 판보다 뒤처져 있습니다.`)은 명세가 더했다. 판 번호를 둘째 줄로 뺀 것은 ADR의 글을 첫 줄에 고치지 않고 두려는 것이다.
- "올리다 실패했다"는 마이그레이션 파일 자체의 잘못이라 개발자가 고칠 것이므로 역추적을 함께 찍는다. 그 역추적에 연결 문자열이 비밀번호째 실리지 않는지는 Testing Decisions의 셋째가 본다(원칙 V). "판은 올리기 전 그대로"는 명세가 쟀다. 어댑터가 올리기 전체를 `engine.begin()`으로 감싸고 alembic 환경이 그 연결에서 다시 트랜잭션을 여는 시제품에서, `0001`인 데이터베이스에 표 하나를 만든 뒤 예외를 던지는 `0002`를 올렸다. 그 예외가 그대로 올라왔고, 판 기록 표의 줄은 `0001` 그대로였으며 `0002`가 만든 표는 남지 않았다(`.scratch/postgres-foundation/probes/stack/README.md`의 판 견줌 표). 두 겹 가운데 어느 것이 되돌렸는지는 가르지 않았으므로, 제품도 시제품과 같은 두 겹으로 짓는다. 첫 티켓은 Testing Decisions의 셋째에서 실제 `migrate`로 같은 것을 다시 본다.
- "접속을 허락하지 않았다"와 "데이터베이스 없음"의 둘째 줄은 restart_recover 프로브의 항목 4에서 왔다. 처음 띄우기 도중 전원이 끊긴 볼륨은 다시 띄워도, PostgreSQL이 상태 확인에는 `healthy`로 답하면서 다른 컨테이너의 접속은 `no pg_hba.conf entry`로 거절하고 데이터베이스 `agent_os`는 없다고 했다(여섯 번 가운데 다섯 번). 실제 `migrate`가 둘 가운데 어느 거절을 받는지는 대역이라 재지 않았으므로, 두 글에 같은 둘째 줄을 단다. 고치는 길은 아래 "배포 안내"의 4다.
- `serve`가 멈출 때 uvicorn은 첫 줄 앞에 `ERROR:`와 빈칸을 붙이고, 둘째 줄은 두 칸 들여쓴 그대로 따로 한 줄로 찍는다. 그 뒤에 `ERROR: Application startup failed. Exiting.`이 선다. stack 프로브가 표가 뒤처진 두 줄 글로 윈도 호스트에서 쟀다(위 "데이터베이스 포트와 조립").

시험이 테스트 데이터베이스를 찾지 못했을 때의 글은 아래다. pytest의 픽스처와 e2e-stack이 같은 글을 쓴다(ADR 0066 결정 "실제 serve를 띄우는 시험"). 한 줄로 끝나는 명령을 그대로 붙여 넣을 수 있게 마지막에 둔다.

| 갈래 | 글 |
|---|---|
| `AGENT_OS_TEST_DATABASE_URL`이 없어 기본 주소를 썼다 | `테스트 데이터베이스(127.0.0.1:25432/agent_os)에 닿지 못했습니다(<까닭>). 이 명령으로 띄우십시오: docker compose -f compose.test.yaml up -d --wait` |
| `AGENT_OS_TEST_DATABASE_URL`이 있다 | `AGENT_OS_TEST_DATABASE_URL 이 가리키는 테스트 데이터베이스(<자리>)에 닿지 못했습니다(<까닭>).` |

### 표의 판을 견주는 자리(명세가 정했다)

- `serve`의 확인과 `migrate`는 같은 견줌을 쓴다. 판 기록 표의 판을 읽고, 이 판의 마이그레이션 파일이 가진 번호들과 견준다. 판이 마지막 번호와 같으면 맞다. 표가 없거나 판이 아는 번호 가운데 하나면 뒤처졌다. 판이 모르는 번호면 더 새롭다.
- `migrate`는 alembic을 부르기 전에 이 견줌을 하고, 더 새로우면 표를 건드리지 않고 멈춘다. alembic만 부르면 모르는 번호에서 `alembic.util.exc.CommandError: Can't locate revision identified by '0002'`가 역추적과 함께 나고, 운영자가 할 일을 알려 주지 않는다(같은 README "빈 첫 마이그레이션과 표의 판 견줌"이 alembic만 불러 봤다). 같은 회차에서 우리 견줌은 옛 판의 `migrate`가 표를 건드리지 않게 했다.
- 모르는 번호는 모두 "더 새롭다"로 본다. 다른 제품이 쓰던 데이터베이스를 잘못 가리킨 경우와 가르지 못하지만, 지원하는 데이터베이스는 단독 compose가 띄우는 것 하나이고(ADR 0066 결정 "이미지와 지원 범위") 그 데이터베이스에는 이 제품만 판을 적는다.

### 마이그레이션 파일(명세가 정했다)

- 마이그레이션 파일과 그것을 적용하는 코드는 `agent_os.adapters` 안 한 곳에 두고, 휠과 이미지에 함께 든다(ADR 0066 결정 "층과 조립"). alembic의 설정 파일(`alembic.ini`)은 두지 않고 어댑터가 설정을 코드로 짓는다. 설정 파일을 거치면 주소와 경로가 configparser의 `%` 해석을 지나고, 패키지 안에 파일을 하나 더 실어야 한다. 마이그레이션을 돌리는 alembic의 `env.py`는 어댑터가 연 연결을 받아 쓰고 스스로 이벤트 루프를 열지 않는다. 그래서 이미 도는 루프 안에서도 적용할 수 있다. 시제품은 `.scratch/postgres-foundation/probes/stack/proto/migrations/`다.
- 번호는 `0001`부터 하나씩 오르는 네 자리 수이고, 파일 이름은 `<번호>_<짧은 영문 이름>.py`다. 파일마다 앞 번호를 가리키고, 마지막 번호는 하나다. 이 번호가 alembic의 판 번호(revision)이고, 판 기록 표에 적히는 값이다.
- 파일에는 표를 올리는 함수 `upgrade`만 두고 되돌리는 함수 `downgrade`는 두지 않는다(ADR 0066 결정 "판 되돌리기"). alembic은 `downgrade`가 없어도 올리기를 했다. 시제품의 첫 마이그레이션은 `upgrade` 하나만 두었고, 빈 데이터베이스에 적용해 표 `alembic_version` 하나와 줄 `0001`이 생겼으며, 다시 적용해도 그대로였다(같은 README). 그래서 ADR 0066 결정 "이 행이 짓는 표"가 어림으로 둔 "빈 마이그레이션으로 판 기록 표에 줄이 남는지"가 섰다. 이 행의 첫 마이그레이션 `0001`은 표를 만들지 않는다(ADR 0066 결정 "이 행이 짓는 표"). 기능 계획의 수락 조건 "넣어 둔 줄"은 이 줄이다.
- 새 마이그레이션 파일은 손으로 쓴다. 설정 파일이 없어 `alembic revision` 명령은 그대로 돌지 않는다. 앞 파일의 꼴을 따라 번호와 앞 번호를 적는다. 이미 dev에 들어간 파일은 고치지 않고 새 파일을 더한다. 운영자의 데이터베이스는 이미 그 파일로 올라가 있을 수 있다.
- 위 셋(번호의 차례, 앞 번호의 사슬, `downgrade`가 없는 것)은 저장소 상태 시험이 본다(아래 "저장소 상태 시험").

거부한 안: rag-engine처럼 `downgrade`를 두고 `NotImplementedError`를 던지게 한다. 되돌리는 명령을 제품이 내지 않으므로 그 함수는 불리지 않는 코드이고, 저장소 상태 시험이 "없다"를 보는 편이 단순하다. 설정 파일을 패키지 안에 둔다. 위의 `%` 해석과 파일 하나가 는다.

### agent-os migrate(명세가 정했다)

- `agent-os`의 새 하위 명령이다. 받는 것은 `AGENT_OS_DATABASE_URL` 하나이고 인자가 없다. 위 "뜰 때의 확인과 다시 시도"대로 닿을 때까지 기다린 뒤, 위 "표의 판을 견주는 자리"대로 견주고, 맞으면 "이미 마지막 판"을, 뒤처졌으면 alembic의 `upgrade head`로 올린 뒤 "올렸다"를 찍고 0으로 끝난다. 그 밖은 위 "멈출 때의 글"의 줄을 찍고 1로 끝난다.
- 올리기 전체를 한 트랜잭션으로 돌린다. 둘이 같은 데이터베이스에 함께 도는 경우는 다루지 않는다(ADR 0066 결정 "표를 올리는 때", multi-instance가 다시 본다).
- `serve`와 달리 플러그인, 트레이스, 토큰을 읽지 않는다. 그래서 단독 compose의 `migrate` 서비스에는 연결 문자열 하나만 넘긴다.

### 단독 compose의 PostgreSQL과 migrate(명세가 정했다)

근거는 `.scratch/postgres-foundation/probes/compose_shape/`다. 그 프로브는 아래 모양을 Docker Desktop의 리눅스 엔진(WSL2)에서 실제 PostgreSQL 이미지로 띄웠고, `migrate`와 `serve`는 `psql`을 부르는 셸 대역이었다(그 README "재지 못한 것"). 그 README의 "제안하는 compose 조각"이 이 절의 모양을 YAML로 담는다.

- **`postgres` 서비스.** 이미지는 `postgres@sha256:b9f6b8ff03b62f3cfd9d9ba3fe56226a9991c79d3fb46fd46536263bf02be553`(ADR 0066 결정 "이미지와 지원 범위")이고, 이미지 줄 위에 `postgres:18`(Debian trixie)이라고 주석을 단다. 환경은 `POSTGRES_USER`와 `POSTGRES_DB`가 `agent_os`, `POSTGRES_PASSWORD`가 `${AGENT_OS_DATABASE_PASSWORD:?.env 에 AGENT_OS_DATABASE_PASSWORD 가 없다}`다. 이름 있는 볼륨 `database`를 `/var/lib/postgresql`에 붙인다. compose의 프로젝트 이름이 `agent-os`이므로 Docker의 볼륨 이름은 `agent-os_database`다(지금의 `agent-os_plugins`와 같은 꼴). `ports`는 두지 않는다. 같은 네트워크의 `migrate`와 `serve`만 서비스 이름 `postgres`로 닿는다. 재시작 정책은 다른 서비스와 같은 `unless-stopped`다.
- **`postgres`의 권한.** `user: "999:999"`, `read_only: true`, `cap_drop: [ALL]`, `security_opt: ["no-new-privileges:true"]`, tmpfs `/var/run/postgresql`, `init: true`로 띄운다. 이 꼴(프로브의 1나)은 빈 볼륨에서도 데이터가 있는 볼륨에서도 떴고, 첫 프로세스의 권한 집합이 비었으며, 루트에 쓰려 하면 `Read-only file system`으로 거부됐다. 빈 볼륨으로 처음 뜰 때 데이터 폴더(`18`과 `18/docker`)가 999:999 소유로 만들어졌다. 소켓 폴더의 tmpfs를 빼면 처음과 다시 모두 `could not create lock file "/var/run/postgresql/.s.PGSQL.5432.lock": Read-only file system`으로 끝났다. `init: true`를 둔 1나는 첫 프로세스가 uid 999의 `docker-init`이었고 깨끗이 멈췄다(그 README의 결과 표 1). init은 우리 이미지 넷과 프록시처럼 두어 ADR 0056 결정 "컨테이너 배치"의 "첫 프로세스에는 init을 둔다"를 지킨다.
- **`postgres`의 상태 확인.** `pg_isready -h 127.0.0.1 -U agent_os -d agent_os`로 TCP에 묻고, 시간 설정은 지금 파일의 공용 앵커(`interval` 30s, `timeout` 10s, `retries` 3, `start_period` 30s, `start_interval` 2s)를 그대로 쓴다. 유닉스 소켓에 묻는 꼴은 쓰지 않는다. 빈 볼륨으로 처음 뜰 때 진입 스크립트가 TCP를 듣지 않는 임시 서버를 먼저 띄우므로(진입 스크립트 297줄의 `-c listen_addresses=''`, 손으로 봤다), 소켓 확인이 그 임시 서버에 답해 정상이 된 뒤 다른 컨테이너의 접속이 실패했다(세 번 모두 정상 뒤의 접속 17개 가운데 2개). TCP 확인은 아홉 회차 모두 정상 뒤의 접속 실패가 0이었다. `start_interval` 2s는 200ms보다 정상이 최대 1.75초 늦었다(그 README의 결과 표 2다). 그 늦음은 첫 띄우기에서만 드는 값이라 앵커를 바꾸지 않는다.
- **`migrate` 서비스.** `serve`와 같은 이미지(`${AGENT_OS_NAMESPACE}/agent-os-runtime:${AGENT_OS_VERSION}`)로 `agent-os migrate`를 돌린다(ADR 0066 결정 "표를 올리는 때"). 재시작 정책은 `"no"`이고, `depends_on`은 `postgres`의 `service_healthy`다. 환경은 `AGENT_OS_DATABASE_URL` 하나이고(위 "agent-os migrate"), `.env`를 통째로 받지 않는다. 루트는 `serve`처럼 읽기 전용이고 볼륨을 붙이지 않는다. 실제 `agent-os migrate`가 읽기 전용 루트에서 도는지는 대역이라 재지 않았다(어림). 단독 배포 e2e가 첫 실행에서 본다.
- **`serve`.** 지금의 줄에 `depends_on`으로 `migrate`의 `service_completed_successfully`를 더하고, 환경에 `AGENT_OS_DATABASE_URL`을 위 "연결 문자열과 비밀번호의 변수"의 꼴로 더한다. `serve`는 지금처럼 `.env`를 통째로 받으므로 비밀번호 줄도 받는다(ADR 0066 Consequences "신뢰와 노출"). 프록시와 다른 서비스에는 `depends_on`을 두지 않는다(ADR 0066 결정 "compose 배치").
- **`.env`에 비밀번호가 없을 때.** 줄이 없거나 값이 비면 `docker compose config`도 `up -d`도 종료 1로 끝나고, `required variable AGENT_OS_DATABASE_PASSWORD is missing a value: .env 에 AGENT_OS_DATABASE_PASSWORD 가 없다`를 찍으며, 컨테이너를 하나도 만들지 않았다(그 README 5나). 값이 빈 `.env`에서는 이미지를 받는 `docker compose pull`과 이미지 목록을 내는 `docker compose config --images`도 같은 글로 종료 1이었다(같은 README 5마). 배포 안내 9절이 인터넷이 되는 PC에서 치는 두 명령이 여기에 걸리므로 그 절을 고친다(아래 "배포 안내"의 9). 같은 이름의 값이 운영자의 셸에 있으면 `.env`보다 앞섰다(같은 5나).
- **띄울 때 compose가 하는 것.** 셋 다 대역으로 쟀다(그 README 3).
  - `up -d --wait`는 끝난 `migrate`의 `Exited (0)`을 실패로 보지 않고, `serve`가 정상이 된 뒤 0으로 돌아왔다. 차례는 PostgreSQL 정상, `migrate` 시작과 끝, `serve` 시작이었다. 판을 바꿀 때는 옛 `serve`가 멈춘 뒤 `migrate`가 돌아, 옛 `serve`와 새 `migrate`가 겹치지 않았다.
  - `up -d`를 다시 치면 `migrate`가 같은 컨테이너로 다시 돌고 `serve`는 그대로였다. 실제 `migrate`는 "이미 마지막 판"으로 0을 낸다(위 "멈출 때의 글").
  - `migrate`가 1로 끝나면 `up -d`와 `up -d --wait` 모두 종료 1과 `service "migrate" didn't complete successfully: exit 1`을 냈고, `serve`는 만들어지기만 하고 뜨지 않았다. 까닭을 고친 뒤 `up -d --wait`를 다시 치면 `migrate`가 새로 돌고 `serve`가 떴다.
- **`docker compose restart`.** 서비스 전체를 다시 띄우는 이 명령은 `depends_on`을 기다리지 않아, 대역 `migrate`가 PostgreSQL보다 먼저 시작해 서비스 이름을 풀지 못하고 끝났다(종료 2). `serve` 대역은 다시 시작 없이 돌아왔다(그 README 3사). 실제 `migrate`는 이름 풀이 실패를 다시 시도할 갈래로 보므로(위 "뜰 때의 확인과 다시 시도") 그 시간 안에 PostgreSQL이 서면 성공한다고 본다(어림). 배포 안내는 전체를 다시 띄울 때 `restart`가 아니라 `up -d`를 쓰라고 적는다(아래 "배포 안내"의 4).
- 파일 머리의 주석은 "프록시 하나와 이미지 넷"을 PostgreSQL과 한 번 도는 `migrate`까지 적게 고치고, `user` 줄에 PostgreSQL은 이 파일에 적힌 uid 999로 돈다는 것을 더한다.
- `docker compose restart postgres`는 `serve` 컨테이너를 건드리지 않았고, 새 접속은 돌아왔으며, 쥐고 있던 접속은 끊겼다(그 README 3아). 실제 `serve`는 연결 묶음이 꺼낼 때마다 확인하므로(위 "뜰 때의 확인과 다시 시도") 끊긴 연결을 버린다.
- **PostgreSQL만 멈출 때.** `docker kill`이나 `docker stop`으로 멈춘 PostgreSQL은 재시작 정책 `unless-stopped`가 다시 띄우지 않았다(25초 지켜봤다, `.scratch/postgres-foundation/probes/restart_recover/README.md` 항목 3). 같은 KILL 신호라도 바깥에서 PostgreSQL 프로세스에 보내 죽인 것은 재시작 정책이 0.2~0.3초 만에 다시 띄웠으므로, 앞의 둘은 Docker가 시킨 멈춤이라 다시 띄우지 않은 것으로 읽는다. 다시 띄우는 것은 `docker compose up -d`다(아래 "배포 안내"의 4). 어느 쪽이든 `serve` 대역은 다시 시작되지 않았다.
- **상태 확인이 못 보는 것.** 위 TCP 상태 확인은 처음 띄우기 도중 전원이 끊겨 반쯤 만들어진 볼륨에서도 `healthy`였다(같은 README 항목 4). 그래서 그 볼륨에서는 `migrate`가 떠서 멈추고 `serve`는 뜨지 않는다(위 "멈출 때의 글"의 "접속을 허락하지 않았다").
- **권한을 좁힌 PostgreSQL의 재시작.** 위 권한의 꼴로 띄운 PostgreSQL은 Docker를 다시 켠 뒤에도 돌아왔고 줄이 남았다(같은 README 항목 5, 한 번). 서버 재시작과 전원 끊김은 그 꼴로 재지 않았다.

거부한 안: 공식 이미지의 기본대로 root로 띄우고 진입 스크립트가 쓰는 권한 넷(`CHOWN`, `DAC_OVERRIDE`, `SETGID`, `SETUID`)만 돌려준다(프로브의 1다). 떴고 넷 가운데 하나를 빼면 실패했지만, 그 꼴에 init을 더하면 root인 init이 uid 999의 PostgreSQL에 멈춤 신호를 넘기지 못했다(`[FATAL tini (1)] Unexpected error when forwarding signal: 'Operation not permitted'`, 종료 1). 다음 시작은 비정상 종료에서 복구하는 길을 돌았다. `KILL`까지 돌려주면 깨끗이 멈췄지만 돌려줄 권한이 다섯이 된다. 권한 빼기만 둔다(1라). 처음 띄우기에서 `Permission denied`로 끝났다. 상태 확인을 유닉스 소켓으로 묻는다. 위의 임시 서버 때문에 정상 뒤에 다른 컨테이너의 접속이 실패했다. 상태 확인을 `select 1` 같은 실제 질의로 바꾼다. 반쯤 만들어진 볼륨에서 PostgreSQL이 정상이 되지 않아 `migrate`가 뜨지 않지만, 그 볼륨은 어느 쪽이든 손으로 고쳐야 하고, 까닭이 PostgreSQL의 기록에만 남는다. 지금의 꼴이면 `migrate`의 글이 고치는 절을 가리킨다.

### 데이터베이스 비밀번호 바꾸기(명세가 정했다)

공식 이미지는 `POSTGRES_PASSWORD`를 데이터 폴더를 처음 만들 때만 쓴다(ADR 0066 Consequences "명세가 짓는 것"). 그래서 이미 데이터가 있는 볼륨에서는 `.env`와 데이터베이스 안의 계정을 둘 다 바꿔야 한다. 근거는 `.scratch/postgres-foundation/probes/compose_shape/README.md`의 4다.

- **`.env`만 바꾸면.** `up -d`가 종료 1로 끝났다. PostgreSQL 컨테이너는 새 값으로 다시 만들어졌지만 계정의 비밀번호는 옛것이라, `migrate`가 `password authentication failed for user "agent_os"`로 끝나고 `serve`는 만들어지기만 하고 뜨지 않았다. 떠 있던 `serve`가 내려간 채 남는다(4가). 실제 `migrate`는 위 "멈출 때의 글"의 "비밀번호" 줄을 찍고, 그 둘째 줄이 배포 안내의 이 절을 가리킨다.
- **절차.** 운영자는 먼저 `.env`의 `AGENT_OS_DATABASE_PASSWORD`를 새 값으로 고치고, 묶음을 푼 폴더에서 아래 세 줄을 친다. 프로브가 이 세 줄을 데이터가 있는 볼륨에서 그대로 쳤고 세 줄 모두 0으로 끝났으며, 넣어 둔 줄이 남았다(4마, 프로브 폴더의 `change_password.sh`).

  ```bash
  docker compose up -d --wait postgres
  printf '%s\n' '\getenv new POSTGRES_PASSWORD' "ALTER ROLE agent_os PASSWORD :'new'" | docker compose exec -T postgres psql -U agent_os -d agent_os -v ON_ERROR_STOP=1
  docker compose up -d --wait --wait-timeout 600
  ```

  첫 줄은 PostgreSQL 컨테이너만 새 `.env`로 다시 만든다. 첫 줄 뒤에 `migrate`와 `serve`는 건드려지지 않았다. 둘째 줄은 그 컨테이너 안에서 새 값으로 계정의 비밀번호를 바꾼다. 컨테이너 안의 유닉스 소켓은 공식 이미지가 `trust`로 두어 옛 비밀번호를 묻지 않는다(4라, `pg_hba.conf`를 손으로 봤다). 새 값은 psql이 컨테이너의 환경 변수 `POSTGRES_PASSWORD`에서 `\getenv`로 읽는다. 그래서 운영자가 치는 명령줄에도, 컨테이너 안 psql 프로세스의 인자에도 값이 실리지 않고(명령의 글에 값이 없다), PostgreSQL 로그에도 남지 않았다(4마). 셋째 줄은 `migrate`와 `serve`를 새 연결 문자열로 다시 만든다.
- **멈추는 동안.** 둘째 줄이 끝난 때부터 셋째 줄이 `serve`를 다시 띄울 때까지 옛 `serve`의 새 접속은 인증에 실패한다. 이미 쥐고 있던 접속은 그대로 돌았다(4다). 그 틈은 마지막 실행에서 2.7초였다(앞선 두 실행의 5.7초와 6.8초는 손으로 봤다). 안내는 이 틈 동안 요청이 실패할 수 있다고 적는다.
- **로그에 남는 것.** 문법이 틀린 `ALTER ROLE` 문장은 PostgreSQL 로그에 비밀번호째 남았다(`STATEMENT:  ALTER ROLE agent_os PASSWORD '…' BOGUS`, 4라). 그래서 안내는 둘째 줄을 고쳐 치지 말고 그대로 붙여 넣으라고 적는다. 성공한 문장은 남지 않았다(`log_statement`가 `none`).

거부한 안: 볼륨을 지우고 새 비밀번호로 처음부터 띄운다. 데이터를 모두 잃는다. `serve`와 `migrate`를 내린 뒤 바꾼다. 위의 틈은 줄지만 명령이 늘고, 틈 동안 이미 쥔 접속은 돌므로 얻는 것이 작다. 새 값을 `sh -c '… psql -v new="$POSTGRES_PASSWORD"'`로 넘긴다(앞선 판의 절차). 둘째 줄이 도는 동안 그 값이 psql 프로세스의 인자에 실려, 리눅스 서버에서는 호스트의 프로세스 목록으로도 보인다고 본다(어림). psql의 `\password`로 바꾼다. 터미널에서 새 값을 손으로 두 번 쳐야 해 그대로 붙여 넣는 절차가 되지 않고, `.env`의 값과 어긋날 수 있다.

### 배포 안내(명세가 정했다)

`deploy/standalone/README.md`를 아래처럼 고친다. 고친 명령을 실제로 돌려 본 기록은 단독 compose에 PostgreSQL을 더하는 티켓이 그 PR에 남긴다(ADR 0066 Consequences "운영", ADR 0056 결정 "인터넷이 막힌 곳"). 그 티켓은 9절의 명령을 이 명세의 글자 그대로 받지 않고, 돌려 본 꼴로 고쳐 싣는다.

- **3-1 환경 변수 파일.** 채울 칸에 `AGENT_OS_DATABASE_PASSWORD`를 더한다. 데이터베이스의 비밀번호이고, 토큰처럼 `openssl rand -hex 32`로 만든 값을 쓰며, 영문자와 숫자만 쓴다는 것과 그 까닭(`@`가 들면 compose가 짓는 주소를 읽지 못하고, `%` 뒤에 16진수 두 자리가 오면 다른 비밀번호로 풀린다, 위 "비밀번호에 드는 글자")을 적는다. "두 번 쳐서 서로 다른 값을 받습니다"는 세 번으로 고친다. "이 파일의 값을 받는 컨테이너는 `serve` 하나입니다"는 "이 파일을 통째로 받는 컨테이너는 `serve` 하나이고, 데이터베이스 비밀번호는 compose가 PostgreSQL 컨테이너와 `migrate`에도 넘깁니다"로 고친다. 비밀번호는 처음 띄울 때 데이터베이스에 정해지므로, 그 뒤에 이 줄만 고치면 접속하지 못한다는 것과 바꿀 때 따를 절(아래 새 12절)을 함께 적는다. `.env.example`에는 값이 빈 줄 `AGENT_OS_DATABASE_PASSWORD=`를 둔다. 빈 채로 띄울 때 compose가 내는 글은 위 "단독 compose의 PostgreSQL과 migrate"다.
- **4 띄우기와 확인.** 처음 받는 이미지에 PostgreSQL을 더한다. 서비스 표에 두 행을 더한다. `postgres`(데이터베이스, Docker Hub의 공식 이미지 `postgres`를 digest로 고정)와 `migrate`(표를 올리고 끝난다, `<이름공간>/agent-os-runtime`)다. 뜬 것을 보는 문장은 "컨테이너 다섯(`serve`, `admin`, `widget`, `portal`, `postgres`)이 모두 `healthy`이고 프록시가 `Up`이면 떴습니다"로 고치고, `migrate`는 `docker compose ps`에 보이지 않고 `docker compose ps -a`에 `Exited (0)`으로 남는다는 것을 더한다(compose_shape README 3바). `up`이 `service "migrate" didn't complete successfully: exit 1`로 끝나면 `docker compose logs migrate`의 마지막 줄이 까닭이라는 것도 더한다. 5절 머리에는 둘을 더한다. 서비스 전체를 다시 띄울 때는 `docker compose restart`가 아니라 `docker compose up -d`를 친다(위 "단독 compose의 PostgreSQL과 migrate"의 `restart`). `docker stop`이나 `docker kill`로 멈춘 PostgreSQL은 저절로 다시 뜨지 않으므로 `docker compose up -d`로 띄운다(같은 절의 "PostgreSQL만 멈출 때"). 5절의 `docker compose restart serve widget portal`은 `migrate`를 건드리지 않으므로 그대로 둔다.
- **4의 새 하위 절 "띄우기가 끊겼을 때".** 두 경우를 적는다. 근거는 `.scratch/postgres-foundation/probes/restart_recover/README.md`의 항목 4다.
  - `up`이 도는 동안 Docker나 서버가 다시 켜지면 `up`이 1로 끝나고, `migrate`나 `serve`가 만들어지기만 한 채(`Created`) 남는다. Docker는 다시 켜질 때 그런 컨테이너를 띄우지 않았다. 안내는 `docker compose up -d --wait`를 다시 치라고 적는다. 프로브에서 `up -d`를 다시 치면 붙었다(PostgreSQL이 데이터베이스를 만드는 도중에 끊긴 넷과, `migrate`가 일을 시작하기 전에 끊겨 `exited(143)`로 남은 둘). `migrate`가 표를 올리는 도중에 끊긴 갈래는 재지 않았다. 실제 `migrate`는 올리기 전체가 한 트랜잭션이므로(위 "agent-os migrate") 끊기면 표가 올리기 전 그대로라고 본다(어림).
  - 처음 띄우는 `up`이 PostgreSQL이 데이터베이스를 만드는 도중에 전원이 끊기면 볼륨이 반쯤 만들어진 채 남는다. 그 뒤로는 `up`을 다시 쳐도 `migrate`가 "접속을 허락하지 않았다"나 "데이터베이스 없음" 글로 멈추거나(위 "멈출 때의 글"), `docker compose logs postgres`가 `could not open file "global/pg_filenode.map"`을 되풀이한다. 프로브에서는 여섯 번 모두 그랬고, 컨테이너만 지운 뒤 띄운 세 번도 붙지 않았다. 이때는 아직 담긴 데이터가 없으므로 데이터베이스 볼륨을 지우고 다시 띄운다.

    ```bash
    docker compose down
    docker volume rm agent-os_database
    docker compose up -d --wait
    ```

    프로브에서는 볼륨까지 지우는 `docker compose down -v` 뒤에 여섯 번 모두 붙었다. 프로브의 배치에는 볼륨이 데이터베이스의 것 하나뿐이라, 그 명령이 지운 것은 그 볼륨 하나였다. 단독 compose의 `down -v`는 플러그인과 기록의 볼륨까지 지우므로, 안내는 데이터베이스 볼륨 하나만 지운다. 그 볼륨 하나만 `docker volume rm`으로 지운 갈래는 재지 않았다(어림). 안내는 이 길을 처음 띄우기가 한 번도 끝나지 않은 볼륨에만 쓰라고 적는다. 한 번 뜬 볼륨에서 전원이 끊긴 것은 PostgreSQL이 스스로 복구했다(위 "뜰 때의 확인과 다시 시도"의 "서버나 Docker가 다시 켜질 때"). 그 티켓은 9절의 명령처럼 이 세 줄도 갓 띄운 배치에서 돌려, 볼륨 이름이 맞고 새 볼륨으로 처음 띄우기가 다시 도는 것을 본다.
- **7 고치지 말 것.** `ports`의 항목에 PostgreSQL을 어느 주소에도 발행하지 않는다는 것을 더한다. 발행하면 데이터베이스가 비밀번호 하나로 서버 밖에 열린다. `user:`의 항목에 PostgreSQL의 `user: "999:999"`를 바꾸지 않는다는 것을 더한다. 데이터 폴더가 그 uid의 소유로 만들어지기 때문이다(위 "단독 compose의 PostgreSQL과 migrate").
- **8 플러그인 폴더와 기록 폴더.** 절 머리를 "데이터를 담는 볼륨"으로 바꾸고, 데이터베이스의 데이터가 이름 있는 볼륨 `agent-os_database`에 든다는 것과 판을 바꾸거나 `docker compose down` 뒤에 다시 띄워도 남는다는 것을 더한다(남는 것은 Testing Decisions의 넷째가 본다). 데이터베이스의 백업과 복원은 이 안내가 아직 다루지 않는다고 적는다(ops-backup-upgrade, Out of Scope). 하위 절 "이름 있는 볼륨 대신 호스트 폴더를 쓰려면"은 플러그인과 기록 폴더만 다루고 데이터베이스 볼륨은 바꾸지 말라고 한 줄 더한다. 호스트 폴더를 붙인 데이터베이스는 재지 않았다(`.scratch/postgres-foundation/probes/compose_shape/README.md` "재지 못한 것").
- **9 인터넷이 막힌 서버로 이미지 옮기기.** PostgreSQL 이미지도 프록시 이미지처럼 digest로 고정하므로(`postgres@sha256:…`), 파일로 옮기면 digest를 잃는 것도 같다. 그것을 PostgreSQL 이미지로 쟀다. digest로 가리켜 `docker save`한 파일을 다른 엔진에서 `docker load`하면 이름 없이 이미지 id만 찍혀 그 digest로 찾지 못했고, 태그로 가리켜 옮기면 그 태그로 돌았다. 옮긴 쪽 이미지의 RepoDigests에는 원래와 다른 digest가 붙었다(`.scratch/postgres-foundation/probes/restart_recover/README.md` 항목 0). 그래서 태그 `agent-os-postgres:local`을 붙여 옮기고 덮어쓰기 파일로 그 태그를 쓰게 한다. 인터넷이 되는 PC의 `.env`는 `.env.example`을 베낀 것이라 비밀번호 칸이 비어, 지금의 `docker compose pull`과 `docker compose config --images | sort -u > images.txt`가 `:?` 때문에 종료 1로 끝난다(위 "단독 compose의 PostgreSQL과 migrate"의 "`.env`에 비밀번호가 없을 때"). 그 PC는 아무것도 띄우지 않으므로 두 명령 앞에 쓰이지 않는 값을 붙여 `AGENT_OS_DATABASE_PASSWORD=unused docker compose pull`과 `AGENT_OS_DATABASE_PASSWORD=unused docker compose config --images | sort -u > images.txt`로 고친다. 프로브가 값이 빈 `.env`에서 그렇게 친 두 명령은 0으로 끝났고, `pull`은 이미지를 받았으며 `config --images`는 이미지 줄을 냈다(compose_shape README 5마). 비밀번호 줄이 아예 없는 옛 `.env`도 셸 값이 채운다고 본다(어림. 5마는 빈 값만 쟀다). 그 PC의 `.env`에 진짜 비밀번호를 적게 하지 않는 것은 그 PC가 데이터베이스를 띄우지 않기 때문이다. 안내는 이 값이 그 두 명령에만 쓰이고 서버로 옮기지 않는다고 적는다. 인터넷이 되는 PC의 명령은 이어서 지금의 `docker tag "$(grep '^nginx@' images.txt)" agent-os-proxy:local` 뒤에 `docker tag "$(grep '^postgres@' images.txt)" agent-os-postgres:local`을 더하고, `grep -v '^nginx@' images.txt > save.txt`를 `grep -v -e '^nginx@' -e '^postgres@' images.txt > save.txt`로 바꾸며, `echo agent-os-postgres:local >> save.txt`를 더한다. `migrate`는 `serve`와 같은 이미지라(위 "단독 compose의 PostgreSQL과 migrate") `sort -u`가 한 번만 남기고, 옮길 이미지는 하나만 는다. 덮어쓰기 파일의 예에는 `postgres:` 아래 `image: agent-os-postgres:local`을 더한다. 절 머리 문단의 "프록시 이미지는 digest로 고정되어 있는데"는 두 이미지를 함께 적게 고친다.
- **11 판을 바꿀 때.** 둘을 더한다. 첫째, 표를 올리는 일은 `docker compose up -d`가 `migrate` 서비스로 하므로 운영자가 따로 칠 명령이 없다. 둘째, 노트의 "올릴 때 할 일"이 `compose.yaml`을 바꾸라고 적은 판은 새 묶음의 `compose.yaml`로 통째로 바꾼다. 운영자가 바꾼 것은 7절대로 `compose.override.yaml`에 두었으므로 통째로 바꿔도 잃는 것이 없다. 데이터베이스를 들이는 판의 노트가 그 할 일과 비밀번호 줄을 적는다(위 "노트 검사의 짝"). 끝자리만 오른 판의 "`.env`의 판 번호 한 줄만"은 그대로 둔다. ADR 0066 Consequences "운영"이 적은 대로 정식 판 뒤에는 참이고, 출시 후보 단계에서는 이 절의 첫 문장(노트를 먼저 읽는다)이 신호다. 표를 바꾼 판에서 그 앞의 판으로 되돌리면 옛 판의 `migrate`가 "표가 더 새롭다"로 멈추고 `serve`가 뜨지 않는다는 것과, 되돌리는 길은 올리기 전의 백업을 복원하는 것이고 그 절차는 아직 이 안내에 없다는 것을 적는다.
- **새 12절 "데이터베이스 비밀번호 바꾸기".** 위 "데이터베이스 비밀번호 바꾸기"의 세 줄과 그 풀이, 멈추는 틈, 둘째 줄을 고쳐 치지 말라는 것을 싣는다. 맨 끝에 두어 지금의 절 번호를 바꾸지 않는다. ADR 0066과 다른 문서가 "배포 안내 9절", "11절"처럼 번호로 가리키기 때문이다. 3-1에서 이 절을 가리킨다. `serve`와 `migrate`의 진단은 번호가 아니라 절 이름으로 가리킨다(위 "멈출 때의 글").

### 테스트 컨테이너(명세가 정했다)

- 테스트용 compose 파일은 저장소 루트의 `compose.test.yaml`이다. 배포 파일 묶음의 원본인 `deploy/` 밖에 두어 제품 변경의 경로 목록(release-image 명세 "제품 변경의 경로 목록")에 들지 않게 한다. 확장자는 배포의 `compose.yaml`과 같게 `.yaml`이다.
- compose의 프로젝트 이름은 `agent-os-test`, 서비스 이름은 `postgres`, 컨테이너 이름은 `agent-os-test-postgres`다. 프로젝트 이름을 파일에 적어, 어느 워크트리에서 띄워도 같은 컨테이너 하나가 된다. 폴더 이름으로 프로젝트를 정하면 워크트리마다 다른 컨테이너가 떠서 포트가 부딪친다.
- 이미지는 단독 compose와 같은 digest다(ADR 0066 결정 "이미지와 지원 범위"). 계정, 비밀번호, 데이터베이스 이름은 모두 `agent_os`인 시험용 값이고 파일에 적는다. 그 컨테이너는 `127.0.0.1`에만 열리고 데이터가 메모리에만 있어 비밀 값이 아니다.
- 포트는 `127.0.0.1:25432`다. rag-engine이 쓰는 55432·55433과 겹치지 않고(ADR 0066 결정 "테스트 데이터베이스"), 윈도가 잠깐 쓰는 포트를 나눠 주는 동적 범위(49152~65535)와 이 PC가 다른 프로그램에 잡아 둔 범위 밖이다. 잡아 둔 범위는 2026-11-18에 손으로 봤다(`netsh interface ipv4 show excludedportrange protocol=tcp`의 출력은 7895, 7936, 50000~50059, 52441~53040 사이의 다섯 묶음, 53663~53762였다).
- 데이터 폴더(`/var/lib/postgresql`)는 tmpfs(메모리 위의 파일 시스템)다. 컨테이너를 다시 띄우면 데이터가 모두 사라진다. 그래서 디스크에 안전하게 쓰려고 기다리는 설정 셋(`fsync`, `synchronous_commit`, `full_page_writes`)을 서버 인자로 끈다. 잃을 데이터가 없기 때문이다. 템플릿 복제의 측정은 이 설정으로 했고(`.scratch/postgres-foundation/probes/clone_xdist/README.md` "환경"), 끈 것과 켠 것의 시간 차이는 재지 않았다(어림).
- 상태 확인은 단독 compose의 PostgreSQL과 같은 명령이고(아래 "단독 compose의 PostgreSQL과 migrate"), `up -d --wait`가 그것이 정상이 되기를 기다린다.
- 시험이 붙는 주소는 `AGENT_OS_TEST_DATABASE_URL`이 있으면 그 값, 없으면 `postgresql://agent_os:agent_os@127.0.0.1:25432/agent_os`다. CI는 이 변수로 service container를 가리킨다.

### 시험 데이터베이스의 이름과 도우미(명세가 정했다)

근거는 `.scratch/postgres-foundation/probes/clone_xdist/`다. 저장소의 모양을 줄인 장난감(패키지 둘, 시험 320개, 공용 도우미 하나)으로 쟀고, 시간 값은 모두 다른 프로브와 다른 세션의 pytest가 같은 PC를 함께 쓰던 때의 값이다(그 README 머리의 굵은 글씨).

- **도우미의 자리.** 도우미는 둘로 나눈다. 데이터베이스를 쓰는 일(테스트 데이터베이스의 주소를 고르는 것, 서버가 답하는지 보는 것, 데이터베이스를 만들고 지우는 것, 위 "멈출 때의 글"의 시험 쪽 글)은 `tools/test_database.py` 한 모듈에 두고, pytest 픽스처는 `tests/database.py`에 두어 그 모듈을 부른다. 러너(`tools/run_checks.py`)와 e2e-stack도 같은 일을 해야 해서, 픽스처만 든 파일 하나로는 셋이 함께 쓰지 못한다. `tests/tools/`의 시험이 이미 `tools`를 import한다. 둘 다 `agent_os`도 위젯 관리 서버의 패키지도 import하지 않는다. 패키지마다 다른 것 둘(마이그레이션을 올리는 함수와 데이터베이스 이름의 접두)은 그 패키지의 시험 폴더에 있는 `conftest.py`가 픽스처를 지을 때 인자로 넘긴다.
- **두 패키지가 함께 쓴다.** 장난감에서 도우미는 두 패키지 어느 것도 import하지 않았고(글자로 적힌 import에도, 새 인터프리터에서 불렀을 때 실린 모듈에도 없었다. 양성 대조인 패키지의 conftest를 부르면 그 패키지가 실렸다), 모든 시험이 자기 패키지의 데이터베이스에서 자기 표와 `alembic_version`만 봤다. 두 패키지의 첫 판 번호가 둘 다 `0001`이어도 부딪히지 않았다(그 README 요약). 그래서 ADR 0066 결정 "위젯 관리 서버"가 어림으로 둔 "테스트 도우미(컨테이너를 확인하고 템플릿을 만드는 픽스처)를 `tests/` 안에 하나 두고 두 패키지의 시험이 함께 쓸 수 있는지"가 섰다. 픽스처는 그 문장대로 `tests/` 안의 한 파일(`tests/database.py`)이고, 픽스처가 부르는 데이터베이스 일만 `tools/`에 둔다(위 "도우미의 자리"). 위젯 관리 서버의 시험이 어느 폴더에 들고 그 접두가 무엇인지는 widget-admin-server의 명세가 정한다(그 기능 계획에 적었다).
- **이름.** 템플릿은 `<접두>_template_<uuid4의 16진수 32자>`, 시험마다의 데이터베이스는 `<접두>_test_<같은 32자>`이고, e2e-stack이 만드는 것은 `<접두>_e2e_<같은 32자>`다. agent_os의 접두는 `agent_os`다. 테스트 컨테이너 하나를 워크트리와 세션이 함께 쓰므로 무작위 토막으로 겹치지 않게 한다. 장난감에서 pytest 실행 둘이 한 컨테이너를 함께 쓰자 데이터베이스 이름 656개가 모두 달랐다. PostgreSQL의 이름은 63바이트까지이므로 접두는 21자까지다(63에서 `_template_` 열 자와 무작위 32자를 뺀 값). 도우미는 접두가 소문자, 숫자, 밑줄로만 되어 있고 21자를 넘지 않는지 보고, 아니면 시험을 띄우기 전에 멈춘다. 접두는 패키지마다 다르다(위 "도우미의 자리").
- **만들고 지우는 때.** 템플릿은 pytest의 세션 범위 픽스처가 만든다. xdist의 작업자는 저마다 세션이므로, 작업자마다 패키지마다 하나가 생기고 마이그레이션을 거기에 한 번 올린다. 시험마다의 픽스처는 템플릿을 복제하고(`CREATE DATABASE … TEMPLATE`, 기본 전략), 시험이 끝나면 `DROP DATABASE … WITH (FORCE)`로 지운다. 템플릿은 세션이 끝날 때 지운다. 관리 연결은 시험의 루프에 매이지 않게 연결을 묶어 두지 않는다(SQLAlchemy의 `NullPool`). 위 두 실행이 끝난 뒤 남은 데이터베이스는 0이었다.
- **세션 범위 픽스처의 꼴.** 템플릿을 만드는 픽스처는 `loop_scope="session"`인 비동기 픽스처다. 동기 픽스처가 `asyncio.run`을 부르는 꼴도 장난감에서 똑같이 돌았지만(그 README 요약 "세션 범위 픽스처의 두 꼴"), `.claude/rules/tests.md`가 시험에서 `asyncio.run()`을 직접 부르지 않게 하고 ADR 0007이 한 저장소에 두 방식을 두지 않게 한다. 두 꼴이 실패할 자리(이미 도는 루프 안에서 처음 불릴 때, 루프에 매인 객체를 다른 루프로 넘길 때)는 갈래를 두지 않았다(어림).
- **마이그레이션을 올리는 길.** 위 "마이그레이션 파일"의 길(alembic에 연결을 넘기고 `run_sync`로 부른다)이 세션 루프 안에서도 시험의 루프 안에서도 막히지 않았고, 새 연결로 본 템플릿에 표와 판이 있었다(그 README 요약).
- **걸린 시간.** 작업자 여덟(`-n 8`)이 함께 돌 때 시험 하나의 복제 문은 중앙값 116.8~122.7ms였고, 관리 연결을 맺는 것까지 넣은 준비와 지우기는 중앙값 232.8~271.3ms였다(세 번). 작업자 하나에서는 34.0ms와 106.7ms였다. 템플릿 없이 시험마다 빈 데이터베이스에 마이그레이션을 올린 대조는 같은 실행에서 준비가 중앙값 260.2ms로 복제 갈래(163.5~190.3ms)보다 길었지만, 장난감의 마이그레이션이 작아 pytest 전체 시간은 복제 갈래의 범위 안이었다. 템플릿이 아끼는 몫이 마이그레이션이 클수록 는다는 것은 어림이다. 복제 전략을 `FILE_COPY`로 바꾼 갈래는 부하와 갈리지 않아 판정하지 못했으므로 기본 전략을 쓴다.
- **서버가 없을 때.** 주소를 고르는 세션 범위 픽스처가 서버를 보고, 답하지 않으면 `pytest.fail`로 실패한다. 그 픽스처를 받는 시험은 모두 위 "멈출 때의 글"의 시험 쪽 글로 setup 오류가 되고, skip이 아니다(원칙 II). 장난감에서 시험 80개가 모두 setup 오류였고 오류마다 도우미의 한 줄이 있었으며 종료 코드는 1이었다.
- **명령줄 입구.** `tools/test_database.py`는 명령줄에서 `create <접두>`와 `drop <이름>`을 받는다. `create`는 빈 데이터베이스를 `<접두>_e2e_…` 이름으로 만들고 그 주소를 표준 출력에 한 줄로 찍는다. 템플릿을 거치지 않는다. e2e-stack은 그 뒤 `agent-os migrate`를 스스로 돌리기 때문이다(아래 "실제 serve를 띄우는 시험의 데이터베이스"). 서버가 답하지 않으면 시험 쪽 글을 표준 오류에 찍고 1로 끝난다.
- 시험 프로세스가 죽어 지우지 못한 데이터베이스는 컨테이너를 다시 띄울 때까지 남는다. 이름이 무작위라 다음 시험과 부딪히지 않는다. 남은 것을 치우는 일은 이 명세가 다루지 않는다(Out of Scope).

거부한 안: 도우미를 `tests/`의 파일 하나에 둔다(장난감의 꼴). 러너와 e2e-stack이 pytest 픽스처 파일을 부르게 된다. 세션 범위 픽스처를 동기 픽스처의 `asyncio.run`으로 짓는다. 장난감에서 똑같이 돌았지만 위의 규칙과 어긋난다. 복제 전략을 `FILE_COPY`로 둔다. 쓰는 기록(WAL)은 시험마다 228.8KB로 기본 전략의 4519~4744KB보다 작았지만, 요청 체크포인트가 888로 늘었고 시간은 부하와 갈리지 않았다(clone_xdist README 요약).

### 러너가 테스트 컨테이너를 띄우는 길(명세가 정했다)

- pre-commit의 러너(`tools/run_checks.py`)는 pytest 검사를 띄우기 전에 테스트 데이터베이스를 한 번 본다. `AGENT_OS_TEST_DATABASE_URL`이 있으면 아무것도 하지 않는다. 사람이 다른 데이터베이스를 가리킨 것이므로 그 길을 바꾸지 않는다. 없으면 기본 주소에 5초의 제한 시간으로 접속해 질의 하나를 해 보고, 답하면 그대로 간다. 5초는 `serve`가 시도 하나에 거는 제한 시간과 같다(위 "뜰 때의 확인과 다시 시도"). 보는 일은 시험의 픽스처와 같은 `tools/test_database.py`의 것을 부른다(위 "시험 데이터베이스의 이름과 도우미").
- 답하지 않으면 `docker compose -f compose.test.yaml up -d --wait --wait-timeout 60`을 치고, "테스트 컨테이너를 띄웠습니다" 한 줄을 찍는다. 컨테이너를 내리지 않는다(ADR 0066 결정 "테스트 데이터베이스"). 다른 세션이 이미 쓰고 있을 수 있어서다.
- **제한 시간.** 위 명령의 `--wait-timeout 60`과 함께, 그 명령을 부르는 호출에도 180초의 제한 시간을 둔다(`.claude/rules/tools.md`의 기다리거나 되풀이하는 도구 항목). `--wait-timeout`이 없으면 컨테이너가 끝내 정상이 되지 못할 때 `--wait`가 돌아오지 않고, `--wait-timeout`은 상태 확인을 기다리는 시간만 막아 이미지를 받는 시간은 막지 않는다고 본다(둘 다 어림. 재지 않았다). 그래서 호출의 제한 시간을 따로 둔다. 단독 compose의 꼴에서 빈 볼륨의 PostgreSQL은 이 PC에서 시작한 뒤 4.55초에 정상이었으므로(compose_shape README 3나) 60초는 그 열 배를 넘는다. 180초는 이미지를 받는 시간까지 담으려고 고른 값이고 재지 않았다(어림). 명령이 0이 아닌 값으로 끝나거나 어느 제한 시간이든 넘기면 아래의 띄우기 실패로 센다. 넘겨서 끊은 때에도 컨테이너는 내리지 않는다.
- 띄우기가 실패해도(0이 아닌 종료와 제한 시간 넘김) 러너는 멈추지 않고 실패한 까닭 한 줄을 찍은 뒤 pytest를 그대로 띄운다. 그 뒤의 판정은 pytest의 실패가 한다(위 "멈출 때의 글"의 시험 쪽 글). 두 세션이 동시에 띄우다 하나가 이름이 겹쳐 실패해도, 다른 세션이 띄운 컨테이너가 답하면 시험은 돈다(어림. 동시에 띄우는 갈래는 재지 않았다).
- 손으로 치는 `uv run pytest`는 컨테이너를 띄우지 않는다(ADR 0066). 시험이 Docker를 부르면 시험을 돌린 결과가 기계의 상태를 바꾼다.
- 러너의 이 판정(변수가 있으면 보지 않는다, 답하면 띄우지 않는다, 답하지 않으면 띄우고 한 줄을 찍는다, 띄우기가 실패하거나 제한 시간을 넘겨도 pytest 검사를 띄운다)은 Docker도 접속도 부르지 않는 함수로 떼어 `tests/tools/test_run_checks.py`에서 본다. Docker를 부르는 부분은 그 티켓이 테스트 컨테이너를 내린 채 러너를 한 번 돌려 컨테이너가 뜨는 것을 보고 일지에 적는다. 둘 다 `.claude/rules/tests.md`의 `tools/` 항목(순수 함수는 `tests/tools/`에서 보고, 셸을 부르는 부분은 실제 실행으로 확인한다)을 따른 것이다.

### 개발 PC에서 serve가 붙는 데이터베이스(명세가 정했다)

- compose 밖에서 `serve`를 띄우는 개발자는 테스트 컨테이너의 기본 데이터베이스 `agent_os`에 붙는다. 주소는 시험의 기본 주소와 같은 `postgresql://agent_os:agent_os@127.0.0.1:25432/agent_os`다. 순서는 테스트 컨테이너 띄우기, 그 주소로 `agent-os migrate`, 같은 주소로 `agent-os serve`다. README의 시작 절이 이 세 명령을 적는다(아래 "모두의 커밋").
- 시험은 이 데이터베이스를 템플릿을 만들고 지우는 관리 연결로만 쓰고 그 안의 표를 건드리지 않는다(위 "시험 데이터베이스의 이름과 도우미"). 그래서 개발자의 `serve`와 시험이 함께 돌아도 서로의 줄에 닿지 않는다.
- 데이터가 메모리에 있으므로 컨테이너를 다시 띄우면 개발자의 데이터도 사라진다. 그때는 `migrate`부터 다시 친다. 개발 중의 데이터는 버려도 되는 것으로 본다.

거부한 안: 개발자용 데이터베이스를 따로 둔다(디스크에 남는 둘째 컨테이너나 둘째 compose 파일). 데이터가 남지만, 개발자가 띄우고 지킬 컨테이너와 포트가 하나 더 는다.

### 실제 serve를 띄우는 시험의 데이터베이스(명세가 정했다)

- e2e-stack(`web/packages/e2e-stack`)은 `serve`를 띄우기 전에 테스트 컨테이너에 자기 데이터베이스를 하나 만들고, 그 주소로 `agent-os migrate`를 돌린 뒤, 같은 주소를 `AGENT_OS_DATABASE_URL`로 주어 `serve`를 띄운다. 준비를 정리할 때 그 데이터베이스를 지운다. 데이터베이스를 만들고 지우는 일은 아래 "시험 데이터베이스의 이름과 도우미"의 명령줄 입구를 부른다. 지금 e2e-stack은 부모의 환경을 펼쳐 `serve`에 넘기므로(`serve.ts`를 읽었다) 개발자의 셸에 `AGENT_OS_DATABASE_URL`이 있어도 자기 값으로 덮는다.
- 컨테이너가 없으면 위 "멈출 때의 글"의 시험 쪽 글로 실패한다.
- `-m llm`, `-m llm_widget`, `-m llm_portal`의 시험도 `serve`를 띄우므로(`.claude/rules/http.md`의 테스트 항목) 같은 길을 쓴다. pytest 쪽은 픽스처가, 위젯과 위젯 테스트 페이지의 e2e는 e2e-stack이 맡는다.
- 단독 배포 e2e(`web/packages/e2e-standalone`)와 판 내기의 시험은 compose의 PostgreSQL을 그대로 쓴다. 그 패키지가 지어 쓰는 `.env`에 무작위 비밀번호 줄을 더한다.

### CI(명세가 정했다)

- `python`, `llm`, `e2e`, `e2e-widget`, `e2e-portal` 잡에 같은 digest의 PostgreSQL을 service container로 붙인다(ADR 0066 Consequences "CI"). 계정, 비밀번호, 데이터베이스 이름은 테스트 컨테이너와 같은 `agent_os`이고, 데이터 폴더를 tmpfs로 둔다. 테스트 컨테이너가 끄는 속도 설정 셋은 service container에 서버 인자를 넘기는 길을 보지 않아 정하지 않는다(어림). 그 PR의 CI 시간을 본 티켓이 정한다. 러너의 5432에 열고, 잡의 환경에 `AGENT_OS_TEST_DATABASE_URL`을 그 주소로 준다. 잡은 상태 확인이 정상이 된 뒤에 단계를 시작한다. 상태 확인 명령은 위 "단독 compose의 PostgreSQL과 migrate"의 것과 같다.
- `e2e-standalone`과 `release.yml`의 시험은 compose를 띄우므로 따로 붙이지 않는다.
- CI의 service container에서 템플릿 복제가 도는지는 python 잡에 데이터베이스 시험을 들이는 티켓이 그 PR의 CI로 본다(ADR 0066 Consequences "재지 않은 것"). 같은 이미지이고 같은 SQL이므로 결정이 바뀔 여지는 작다고 본다(어림).

### 노트 검사의 짝(명세가 정했다)

- 노트 검사(`tools/check_notes.py`)의 제목 판정에 짝 하나를 더한다. PR이 마이그레이션 파일을 새로 더했는데 제목에 느낌표가 없으면 문제다. 느낌표가 있으면 `docs/release-notes/upgrade/`에 새 조각이 있어야 한다는 지금의 판정(`title_problems`를 읽었다)이 그 뒤를 잇는다. ADR 0066 결정 "승인 때 함께 확인받는 세부"의 첫째가 정한 "새 마이그레이션 파일을 더하는 PR은 느낌표 PR"을 기계가 본다.
- 조각의 글은 검사하지 않는다. 그 PR의 조각은 "올리기 전에 데이터베이스를 백업하십시오. 되돌리려면 그 백업을 복원합니다"를 싣고, 그 글은 PR 서식과 리뷰가 본다. 글을 검사하면 표현을 조금만 바꿔도 빨개진다.
- 이 행에서 첫 마이그레이션 `0001`을 더하는 PR은 단독 compose에 PostgreSQL을 더하는 PR과 같다(아래 "티켓을 나눌 때 함께 둘 것"). 그 PR은 운영자가 `compose.yaml`을 바꾸고 비밀번호 줄을 더해야 하므로 어차피 느낌표 PR이고, 그 조각이 그 할 일과 위 백업 글을 함께 싣는다. 그 판에는 아직 백업할 데이터베이스가 없으므로 백업 글은 "다음에 표를 바꾸는 판부터"의 안내로 읽힌다.

### 저장소 상태 시험(명세가 정했다)

- PostgreSQL 이미지의 digest를 적는 세 자리(`deploy/standalone/compose.yaml`, `compose.test.yaml`, `.github/workflows/ci.yml`의 service container 다섯)가 모두 같은 값인지 보는 시험을 둔다(ADR 0066 Consequences "CI"). 하나만 바꾸면 빨개진다. 선례는 같은 파일 여럿을 읽어 맞대는 저장소 상태 시험이다(`tests/tools/test_check_md_tables.py`처럼 pytest가 저장소의 파일을 읽는다).
- 마이그레이션 폴더의 파일들이 위 "마이그레이션 파일"의 꼴(번호의 차례, 앞 번호의 사슬, 마지막 번호 하나, `downgrade`가 없음)인지 보는 시험을 둔다. 나란히 짠 두 브랜치가 같은 번호를 들고 오면, 나중에 병합하는 쪽이 기준 브랜치를 합친 뒤 이 시험이 빨개진다.
- 배포 안내 7절이 적는 PostgreSQL의 두 전제가 `deploy/standalone/compose.yaml`과 맞는지 보는 시험을 둔다. `postgres` 서비스에 `ports`가 없고, `user`가 `"999:999"`다. 앞의 것이 깨지면 데이터베이스가 비밀번호 하나로 서버 밖에 열리고, 뒤의 것이 바뀌면 그 uid의 소유로 만들어진 데이터 폴더와 어긋난다(위 "배포 안내"의 7). 선례는 안내의 전제를 compose 파일로 대 보는 `tests/tools/test_deploy_guide.py`의 `test_compose가_우리_이미지에_user를_더하지_않는다는_안내의_전제가_맞다`와 그 시험이 쓰는 `compose의_user`다.

### 의존성과 타입(명세가 미리 쟀다)

- 새 런타임 의존성은 `sqlalchemy[asyncio]`, `asyncpg`, `alembic` 셋이고, `asyncpg-stubs`는 넣지 않는다(ADR 0066 결정 "도구 묶음"). 우리 코드는 asyncpg를 import하지 않는다(위 "뜰 때의 확인과 다시 시도"). 판의 묶음과 `docs/constitution/tech.md`의 표는 의존성을 선언하는 첫 티켓이 정하고 고친다(같은 결정).
- 첫 티켓에 넘긴 측정 셋을 명세가 시제품으로 미리 쟀다(`.scratch/postgres-foundation/probes/stack/`, SQLAlchemy 2.1.8, asyncpg 0.32.0, alembic 1.20.1, asyncpg-stubs 없음). pyright strict가 그 폴더의 파일 15개를 분석해 시제품 쪽 오류 0이었고, 타입 우회는 0이었다. 포트를 import하지 않는 어댑터가 조립 자리에서 포트와 맞대졌고, 일부러 어긋낸 어댑터 둘은 `reportArgumentType`으로 걸렸다. 시제품은 ADR 0066이 적은 `postgres:18`(Debian trixie)의 digest로 띄운 데이터베이스에서 모든 갈래를 돌았다. 그래서 ADR 0066 Consequences "재지 않은 것"의 첫 티켓 몫 셋(스텁 없는 잠금의 strict, Debian 판에서 도는지, 실제 패키지로 포트의 모양)은 이 판에서 섰다. 첫 티켓은 실제 패키지에서 같은 판정을 pyright와 시험으로 다시 본다.

### 모두의 커밋(넘겨받은 것)

ADR 0066 Consequences "모두의 커밋"이 데이터베이스 시험을 들이는 티켓에 맡긴 일이다. 그 티켓은 테스트 컨테이너라는 전제와 띄우는 명령(`docker compose -f compose.test.yaml up -d --wait`)을 아래 자리에 함께 적고 헌법 판을 patch로 올린다(ADR 0038의 선례).

- `docs/constitution/tech.md`의 테스트 줄
- `docs/constitution/operations.md` 가드레일의 기계마다 까는 것과 LLM 테스트 절
- `README.md`의 시작 절. 위 "개발 PC에서 serve가 붙는 데이터베이스"의 세 명령도 함께 적는다
- `.pre-commit-config.yaml` 머리의 준비 목록
- `CLAUDE.md`의 검증 명령. LLM 시험과 e2e를 손으로 칠 때 테스트 컨테이너가 떠 있어야 한다는 것을 그 괄호에 더한다

### 티켓을 나눌 때 함께 둘 것(명세가 정했다)

티켓의 수와 경계는 `/to-tickets`가 정한다. 이 명세가 정하는 것은 한 변경에 함께 실어야 하는 것과 먼저 와야 하는 것이다.

- 데이터베이스 시험을 기본 실행에 들이는 변경은 의존성, 어댑터, `agent-os migrate`, 테스트 컨테이너, 도우미, 러너, CI `python` 잡의 service container, 위 "모두의 커밋"의 자리를 함께 싣는다. 그 변경이 dev에 오르는 순간부터 모든 세션의 커밋이 테스트 컨테이너를 요구하므로, 띄우는 길과 그것을 알리는 글이 같은 커밋에 있어야 한다. 이 변경의 제품 마이그레이션 폴더는 비어 있고, 시험은 시험용 마이그레이션 폴더를 쓴다. 파일이 없는 폴더로도 확인과 올리기가 돈다. 시제품에서 빈 데이터베이스를 빈 폴더로 확인하면 "문제 없음"이었고, 올리면 예외 없이 줄 없는 `alembic_version` 표만 생겼으며, 그 뒤 다시 확인해도 "문제 없음"이었다(stack 프로브 README의 판 견줌 표).
- 단독 compose에 PostgreSQL과 `migrate`를 더하는 변경은 첫 마이그레이션 `0001`, `.env.example`의 비밀번호 줄, 배포 안내, 단독 배포 e2e의 고침, 저장소 상태 시험 가운데 compose 파일을 읽는 둘(digest 세 자리를 맞대는 것과 배포 안내 7절의 전제를 보는 것), `docs/release-notes/upgrade/`의 조각을 함께 싣고, 제목에 느낌표를 붙인다(ADR 0066 결정 "승인 때 함께 확인받는 세부"의 첫째). 배포 안내 9절의 고친 명령을 실제로 돌려 본 기록을 그 티켓의 일지에 남긴다(ADR 0066 Consequences "운영").
- `serve`가 데이터베이스를 요구하게 하는 변경은 포트, 미들웨어, `create_app`의 인자, 구성 오류, e2e-stack의 데이터베이스, CI `llm`·`e2e`·`e2e-widget`·`e2e-portal` 잡의 service container, `.claude/rules/http.md` 37줄의 예외를 넓히는 고침(아래 Testing Decisions의 둘째)을 함께 싣는다. 그 변경이 오른 뒤로는 데이터베이스 없이 `serve`가 뜨지 않으므로, `serve`를 띄우는 모든 시험이 같은 변경에서 데이터베이스를 얻어야 한다.
- 순서는 데이터베이스 시험을 들이는 변경, 단독 compose의 변경, `serve`가 데이터베이스를 요구하게 하는 변경이다. `serve`의 변경이 단독 compose의 변경보다 먼저 dev에 오르면, 그사이에 다른 기능의 출시 PR이 main에 닿을 때(next-session `merge.md`의 "출시 PR"은 끝나지 않은 기능의 조각도 함께 올린다) 단독 배포 e2e와 판 내기의 시험이 `serve`가 뜨지 않아 실패하거나, 그 시험을 지나지 못한 판이 나간다. 단독 compose의 변경이 먼저 오르면 `serve`는 그동안 받은 연결 문자열을 쓰지 않을 뿐이다. 그래서 운영자가 손댈 것(compose 바꾸기와 비밀번호 줄)은 단독 compose의 변경 하나에 모이고, `serve`의 변경은 느낌표가 없다.
- 노트 검사의 짝은 어느 때 들어와도 되지만 이 기능이 닫히기 전에 든다. 이 기능 뒤에 admin-login이 둘째 마이그레이션을 더하기 때문이다.
- 하네스를 고치는 `.claude/rules/http.md`의 고침은 그 티켓의 세션이 새 세션에서 불러 본다(작업 규약 3).

## Testing Decisions

좋은 시험은 운영자와 개발자에게 보이는 것을 본다. 찍히는 글, 종료 코드, 판 기록 표의 줄, 뜨는지 아닌지다. 어댑터 안의 갈래 함수나 alembic을 부르는 차례는 단언하지 않는다. 찍히는 글은 글자까지 단언한다. 그 글이 ADR과 이 명세가 정한 것이고, 운영자와 진단 묶음이 그 글을 읽기 때문이다.

이음매는 넷이다(사용자가 골랐다. 이 명세를 쓰며 물었다, 일지 2026-11-18-1544 "사용자에게 물은 것 하나"). 새 이음매는 없고, 둘째는 있는 이음매가 닿는 범위를 넓힌다. 러너처럼 `tools/`에 드는 코드는 이 넷 밖에서 지금의 규칙대로 본다(위 "러너가 테스트 컨테이너를 띄우는 길").

1. **어댑터(실제 테스트 데이터베이스).** 테스트 컨테이너에서 시험마다 복제한 데이터베이스에 어댑터를 붙인다. 시험용 마이그레이션 폴더(번호 둘)를 넘겨 판의 갈래를 만든다.
   - 사례: 빈 데이터베이스는 뒤처졌다. 올린 뒤에는 맞다. 다시 올려도 그대로다. 아는 옛 번호는 뒤처졌다. 판 기록 표에 모르는 번호를 넣으면 더 새롭고, 그때 올리기는 표를 건드리지 않는다. 틀린 비밀번호는 다시 시도하지 않고 바로 비밀번호 글이다. 로그인을 막은 계정(`NOLOGIN`, 시험이 무작위 이름으로 만들고 지운다)으로 접속하면 다시 시도하지 않고 바로 "접속을 허락하지 않았다" 글이다. 그 접속이 28000을 내는 것은 stack 프로브가 같은 이미지로 쟀다(`.scratch/postgres-foundation/probes/stack/README.md` "접속 실패의 꼴"). 없는 데이터베이스 이름은 데이터베이스 없음 글이다. 닫힌 포트는 짧게 준 다시 시도 시간 뒤에 닿지 못했다는 글이고 알림이 한 번 찍힌다. 접속은 받되 답하지 않는 서버(시험 안에서 띄운 빈 TCP 서버)는 다시 시도 시간과 시도 하나의 제한 시간을 더한 만큼 안에 돌아온다. 모든 글에 비밀번호가 없다. 닫은 뒤 연결이 남지 않는다.
   - 다시 시도 시간과 시도의 제한 시간은 시험이 짧게 줄 수 있는 인자로 받는다. 기본값은 위 "뜰 때의 확인과 다시 시도"의 값이다.
   - 선례는 시제품의 측정 `.scratch/postgres-foundation/probes/stack/run.py`의 `errors`, `versions`, `migrate` 섹션이다.
2. **serve의 시작(있는 이음매를 넓힌다).** `_main(["serve"])`을 부르고, 지금처럼 `uvicorn_calls` 픽스처(`tests/test_main.py`)가 uvicorn을 띄우기 직전의 앱을 붙잡는다. `main`이 어댑터를 짓는 자리는 픽스처가 가짜 데이터베이스로 갈아 끼운다. 붙잡은 앱의 수명을 전체 ASGI 앱으로 직접 돌려 미들웨어를 지나게 한다.
   - 사례: 변수가 없거나 비면 종료 코드 1과 그 글이다. 읽지 못하는 값(`mysql://…`, `@`가 둘인 `postgresql://agent_os:secret@leak@postgres:5432/agent_os`, 둘째 `@` 앞에 `/`가 와 호스트에 `@`가 남지 않는 `postgresql://agent_os:secret@leak/x@postgres:5432/agent_os`)이면 1과 그 글이고, 표준 오류에 비밀번호의 조각(`secret`, `leak`)이 없다. 가짜가 글을 돌려주면 `lifespan.startup.failed`의 글이 그 글과 글자까지 같고, 앱의 시작 일(가짜 MCP 서버)이 돌지 않으며, 닫기가 한 번 불린다. 가짜가 없음을 돌려주면 앱이 뜨고 `/health`가 200이며, 수명을 닫으면 닫기가 한 번 불린다.
   - 직접 구동하는 시험이 미들웨어를 지나는 것은 지금 `.claude/rules/http.md` 37줄이 "스트림의 수명에만" 허용한 예외 밖이다. 그 줄에 "시작 단계"를 더해 넓힌다(위 "티켓을 나눌 때 함께 둘 것"). 사용자가 이 넓힘을 골랐다.
   - uvicorn이 이 글을 역추적 없이 다섯 줄(시작 알림 둘, 글의 두 줄, 시작 실패 한 줄)로 찍고 3으로 끝나는 것은 프로브가 잰 사실로 두고, 실제 `serve` 프로세스를 띄우는 시험을 기본 실행에 더하지 않는다(사용자가 골랐다). 확인을 역추적을 내는 자리(수명 함수의 예외)로 옮기면 이 시험의 `lifespan.startup.failed` 단언이 빨개진다.
3. **migrate 명령(실제 테스트 데이터베이스).** `main(["migrate"])`를 복제한 데이터베이스의 주소로 부른다.
   - 사례: 빈 데이터베이스는 "올렸다"와 0이고 판 기록 표에 마지막 번호가 남는다. 다시 부르면 "이미 마지막 판"과 0이다. 모르는 번호가 든 데이터베이스는 더 새롭다는 글과 1이고 판 기록 표가 그대로다. 변수가 없으면 1과 그 글이다. 닿지 않으면 1과 그 글이다. 시험용 폴더에 표 하나를 만든 뒤 예외를 던지는 셋째 마이그레이션을 더한 폴더로 부르면 "올리다 실패했다"와 1이고 판 기록 표가 올리기 전 그대로다(위 "멈출 때의 글"에서 시제품으로 잰 것을 실제 명령으로 다시 본다). 그때 역추적까지 든 표준 오류에 연결 문자열이 비밀번호째(`agent_os:agent_os@`) 나오지 않는다. 테스트 컨테이너는 비밀번호가 계정 이름과 같은 `agent_os`라 그 글자만으로는 가르지 못하므로 주소의 꼴로 본다.
   - 제품 마이그레이션 폴더로 빈 데이터베이스를 올리는 사례 하나를 둔다. 휠에 드는 그 폴더가 실제로 읽히는지를 본다.
4. **저장소 상태 시험과 있는 e2e.** 위 "저장소 상태 시험"의 셋을 pytest로 본다. e2e-stack은 `migrate` 뒤에 `serve`를 띄우므로, 위젯·관리 화면·위젯 테스트 페이지의 e2e가 데이터베이스까지 이어진 `serve`를 지난다. 단독 배포 e2e(`web/packages/e2e-standalone`)에는 사례 하나를 더한다. 띄운 뒤 판 기록 표의 줄이 `0001`이고, `docker compose down`(볼륨은 남긴다)과 `up -d --wait`를 다시 친 뒤에도 `serve`가 정상이고 그 줄이 남는다. 공식 이미지의 데이터 폴더가 18부터 `/var/lib/postgresql/18/docker`로 옮겨, 볼륨을 옛 자리(`/var/lib/postgresql/data`)에 붙이면 다시 만든 컨테이너에서 데이터가 사라진다(ADR 0066이 손으로 본 `PGDATA`). 이 사례가 그것을 막는다. 다시 띄우는 데 드는 시간은 재지 않았다.
   - 기능 계획의 수락 조건 둘은 이 넷이 함께 본다. "시험 환경에서 단독 compose를 띄우면 PostgreSQL 컨테이너가 함께 뜨고 `serve`가 그 데이터베이스에 닿으며, 컨테이너를 내렸다 다시 띄워도 넣어 둔 줄이 남는다"는 넷째의 단독 배포 e2e 사례다(`serve`가 닿는 것은 `serve`가 데이터베이스를 요구하게 하는 변경이 오른 뒤의 실행이 본다). "이 PC와 CI의 테스트가 데이터베이스를 스스로 띄워 돌고, 데이터베이스가 없으면 설계가 정한 대로(건너뛰지 않고) 알린다"는 위 "러너가 테스트 컨테이너를 띄우는 길"과 CI의 service container이고, 없을 때의 글은 첫째와 셋째의 픽스처가 낸다. 그 글은 컨테이너를 내린 채 pytest를 한 번 쳐서 티켓의 일지에 적는다.

데이터베이스를 쓰는 시험이 처음 재는 것은 위 첫째와 셋째의 사례다. 이 행에는 제품의 표가 없으므로(ADR 0066 결정 "이 행이 짓는 표") 줄을 넣고 읽는 시험은 admin-login의 티켓이 처음 짓는다.

거부한 안: 위 넷에 더해, 실제 `agent-os serve` 프로세스를 빈 데이터베이스에 대고 띄워 "먼저 migrate 를 돌리십시오" 줄과 종료 코드를 보는 시험을 기본 실행에 하나 둔다. 사용자에게 보인 선택지 가운데 고르지 않은 것이다(일지 2026-11-18-1544 "사용자에게 물은 것 하나"). uvicorn이 바뀌어 출력이 달라지면 잡지만, 커밋마다 프로세스를 띄우는 시간이 더 든다(몇 초로 어림했고 재지 않았다).

## Out of Scope

이 명세가 정하는 것은 데이터베이스와 거기 닿는 길까지다(ADR 0066 결정 "백업과 주 판 올림"). 다른 기능에 넘기는 것은 받는 쪽의 기능 계획 본문에도 "postgres-foundation 명세가 넘긴 것(2026-11-18, `.scratch/postgres-foundation/spec.md`의 Out of Scope)"으로 적었고, 받는 기능의 `**Blocked by:**`를 대 봤다.

- **운영자 계정과 운영자 로그인 상태의 표**는 admin-login의 것이다(ADR 0062). `**Blocked by:**`에 postgres-foundation이 있다. 그 행이 더하는 마이그레이션은 위 "마이그레이션 파일"의 꼴과 "노트 검사의 짝"을 따르고, 계정과 로그인 상태의 저장 포트는 위 "데이터베이스 포트와 조립"의 `Database`와 같은 층에 둔다. 이 둘을 그 기능 계획에 적었다.
- **위젯 관리 서버의 데이터베이스**는 widget-admin-server의 것이다. `**Blocked by:**`에 postgres-foundation이 있다. 이 행이 짓는 도우미를 그 패키지의 시험이 쓰는 방법은 그 행의 명세가 정하고(ADR 0066 결정 "위젯 관리 서버"), 이 명세는 도우미가 다른 패키지의 마이그레이션 폴더를 받을 수 있게 짓는 데까지 한다(위 "시험 데이터베이스의 이름과 도우미"). 그 사실을 그 기능 계획에 적었다.
- **데이터베이스의 백업과 복원, PostgreSQL의 주 판 올림, 같은 주 판 안에서 digest를 바꾸는 올림의 확인**은 ops-backup-upgrade의 것이다(ADR 0066 결정 "백업과 주 판 올림"). `**Blocked by:**`에 postgres-foundation이 있다. 그 행이 쓸 이름은 볼륨 `database`(compose 프로젝트 `agent-os` 아래라 Docker의 볼륨 이름은 `agent-os_database`), 서비스 `postgres`, 계정과 데이터베이스 `agent_os`이고 그 기능 계획에 적었다.
- **데이터베이스 비밀번호가 http 모양의 MCP 매니페스트를 거쳐 밖으로 나갈 수 있는 길**은 mcp-trust의 것이다(ADR 0066 Consequences "신뢰와 노출"). 그 변수 이름 `AGENT_OS_DATABASE_PASSWORD`와 `AGENT_OS_DATABASE_URL`이 허락 목록의 대상이라는 것을 그 기능 계획에 적었다. 그 행은 `**Blocked by:**`에 postgres-foundation이 없고 pilot-release 뒤에 오므로 이 행보다 늦게 돈다.
- **문제를 살필 때 묶는 파일에 이 행의 글과 종료 코드와 PostgreSQL 컨테이너의 상태를 담는 일**은 diag-bundle의 것이다(사용자 이야기 37). 묶음이 모을 글은 위 "멈출 때의 글"의 표가 전부다. 글은 이유를 적은 첫 줄과, 갈래에 따라 두 칸 들인 설명 줄 하나로 된다. `serve`는 연결 문자열이 없거나 읽지 못하면 1로, 데이터베이스에서 멈추면 3으로 끝나고, `migrate`는 멈출 때 늘 1이다. `serve`가 3으로 멈출 때 uvicorn은 첫 줄 앞에 `ERROR:`를 붙이고 끝에 `ERROR: Application startup failed. Exiting.`을 더한다. 이것을 그 기능 계획에 적었다. 그 행의 `**Blocked by:**`에는 postgres-foundation이 없어 이 행의 티켓보다 먼저 돌 수 있다. 그때는 그 행의 설계 인터뷰가 이 명세의 표를 읽고 무엇을 담을지 정한다. ADR 0066을 쓴 설계가 그 기능 계획에 넘긴 것도 담을지를 그 인터뷰에 맡겼다.
- **`agent-os migrate` 둘이 함께 도는 경우**는 multi-instance의 것이다(ADR 0066이 그 기능 계획에 이미 적었다).
- **트레이스를 데이터베이스로 옮기는 일과 Redis, `agent-os run`이 데이터베이스를 쓸지**는 trace-postgres의 것이다(같다).
- **인터넷이 막힌 곳으로 옮기는 반입 절차 전체**는 deploy-package의 것이다. 이 명세는 배포 안내 9절의 명령을 PostgreSQL까지 넓히는 데까지 한다(같다).
- **시험이 남긴 데이터베이스를 다른 세션의 것과 가려 치우는 일**은 하지 않는다. 테스트 컨테이너를 다시 띄우면 메모리의 데이터가 모두 사라진다(위 "테스트 컨테이너").

## Further Notes

- **측정 환경의 한계.** 리눅스 서버는 하나도 쓰지 않았다. 모든 측정은 이 PC(Windows 10)의 Docker Desktop(엔진 29.9.2, WSL2 커널) 위에서 돌았다. compose의 모양(`compose_shape/`)은 Docker Desktop의 리눅스 엔진에 바로 띄웠고, 서버와 Docker를 다시 켜는 갈래(`restart_recover/`)는 그 위에 띄운 Docker-in-Docker 컨테이너(`docker:29.9.2-dind`) 안의 엔진에서 흉내 냈다. 그래서 systemd가 Docker를 띄우는 차례, 커널이 다시 뜨는 것, 디스크에 아직 쓰지 않은 버퍼가 날아가는 진짜 전원 끊김은 재지 않았다(`.scratch/postgres-foundation/probes/restart_recover/README.md` "재지 못한 것"). 실제 리눅스 엔진 위의 단독 배포는 단독 배포 e2e가 GitHub의 리눅스 러너에서 처음 본다.
- **CI가 받는 이미지의 횟수.** 이 행으로 CI의 잡 다섯이 실행마다 PostgreSQL 이미지를 받는다. Docker Hub가 받는 횟수를 제한하는데(배포 안내 10절), GitHub의 러너에서 그 제한이 어떻게 걸리는지는 보지 않았다(어림). 막히면 service container가 뜨지 못해 그 잡이 실패하고, 그때 받는 길을 바꿀지는 그 실패를 본 세션이 정한다.
- **세션 끝의 멈춤.** 장난감에서 pytest의 임시 폴더 자리(`--basetemp`)를 주지 않고 돈 서버 없음 갈래 세 번 가운데 한 번은 모든 시험이 끝난 뒤 5분 넘게 멈췄다(손으로 봤다). 자리를 준 뒤의 세 번은 멈추지 않았다(clone_xdist README 요약 "pytest가 세션 끝에서 멈춤"). 까닭은 가르지 못했다(어림). 저장소의 러너도 그 자리를 주지 않으므로(`tools/run_checks.py`), 데이터베이스 시험을 들이는 티켓이 러너에서 같은 멈춤을 보면 이것부터 본다.
- **동시 연결.** 테스트 컨테이너는 PostgreSQL의 기본 동시 연결 수(100)로 돈다. 장난감에서 pytest 실행 둘(작업자 넷씩)이 함께 돌 때 시험이 쥔 연결은 많아야 9였다(clone_xdist README 요약 "연결 수"). 장난감의 시험은 연결을 묶어 두지 않고 시험마다 하나를 여닫으므로, 연결 묶음을 쥔 엔진이나 `serve`를 띄우는 실제 시험과 세션 여럿이 겹칠 때 그 수를 넘는지는 재지 않았다(어림). 넘으면 오류 번호 53300(연결이 너무 많다)이 위 "그 밖" 글로 찍히고, 그때 테스트용 compose 파일에서 그 수를 올린다.
- **다시 잴 때.** 프로브마다 다시 돌리는 명령과 잰 판이 그 README에 있다(`.scratch/postgres-foundation/probes/README.md`의 표). SQLAlchemy, asyncpg, alembic, uvicorn, PostgreSQL 이미지의 판을 바꾸는 티켓은 판에 기대는 측정(접속 실패의 꼴, uvicorn이 찍는 것, 빈 첫 마이그레이션)을 다시 돌려 본다. 다시 잰 결과가 이 명세의 문장과 다르면 그 티켓은 구현을 멈추고 이 명세와 ADR 0066으로 돌아간다.
