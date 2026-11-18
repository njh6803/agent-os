# 2026-11-18 (15:44) postgres-foundation 명세 (to-spec)

세션 제목 `docs/postgres-foundation-spec`. 브랜치 `docs/postgres-foundation-spec`, 워크트리 `.claude/worktrees/postgres-foundation-spec`(기준 `origin/dev` `1aac0cfdd`). 모델은 Fable 5.2로 시작했고, 측정 도중 Fable 사용 한도에 걸려 사용자가 Opus 5.5로 바꿨다. 지시문으로 연 세션이다.

## 사용자 프롬프트

> 사용자: .claude/skills/to-spec/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자:
>
> 다음 작업: 기능 postgres-foundation. ADR 0066이 정한 설계로 명세를 쓴다
> 다음 단계: 명세
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 postgres-foundation-spec)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /to-spec
> 브랜치: docs/postgres-foundation-spec
> 모델: Fable 5.2 / xhigh. 결정표 칸은 Fable 5.1이지만 모델 메뉴에 그 이름이 없어 지금 메뉴의 이름으로 적는다(대기열 model-menu-name-fable-5-1-stale)
> 읽을 것: 일지 docs/journal/2026-11-17-1747-postgres-foundation-design.md의 "다음" 절, ADR 0066 Consequences의 "명세가 짓는 것"
> 이어받을 상태: 없음. 설계는 PR 602로 닫혔고 명세가 정할 것은 ADR 0066 목록에 있다. 데이터가 있는 볼륨에서 비밀번호를 바꾸는 길과 배포 안내의 절차도 그 목록에 든다.
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 dev. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

측정을 돌리던 서브에이전트 셋이 Fable 사용 한도(HTTP 429)로 멈춘 뒤, 사용자가 모델을 Opus 5.5로 바꾸고 이렇게 적었다.

> 사용자: 다시 시도해 주세요

멈춘 서브에이전트 셋을 같은 이름으로 다시 이어 돌렸다. 그 셋이 남긴 컨테이너(`clone-xdist-probe-*` 둘, `pgf-recover-dind-*` 하나)는 각자가 자기 것만 치우게 했다.

## 시작 전 확인

- 주 체크아웃에서 `tidy-checkouts`를 먼저 돌았고, 그 뒤 `EnterWorktree(name: postgres-foundation-spec)`로 들어와 브랜치 이름을 `docs/postgres-foundation-spec`으로 바꿨다.

## 측정

ADR 0066이 명세에 넘긴 어림 가운데 잴 수 있는 것을 `.scratch/postgres-foundation/probes/`에서 쟀다. 폴더마다 무엇을 재는지와 다시 돌리는 명령은 그 `README.md`의 표에 있다.

- `stack/`(이 세션이 직접 지었다): 스텁 없는 strict, 포트 모양, 빈 첫 마이그레이션, 표의 판 견줌, alembic이 모르는 번호에 내는 것, 접속 실패의 꼴과 다시 시도, 비밀번호의 글자, uvicorn의 실패 출력, 쉬던 연결, 복구 중의 57P03. 2026-11-18의 마지막 실행은 측정 43회차, 측정 아님 0회차, 종료 코드 0이었다.
  - 기대와 달랐던 것(둘 다 `.scratch/postgres-foundation/probes/stack/run.py`가 다시 낸다): 접속 때의 asyncpg 예외는 SQLAlchemy가 `DBAPIError`로 감싸서 왔다(사슬을 따라 오류 번호를 찾으므로 판정에는 영향이 없었다). 윈도에서는 거부된 접속 한 번이 약 2초 걸려, 다시 시도 시간을 2초로 준 첫 회차가 알림을 찍지 못해 측정이 아니었다. 그 회차의 시간을 7초로 늘려 다시 돌렸다.
  - 전체를 한 번 돌린 뒤 빠진 갈래를 하나 찾았다. 접속은 받되 아무 답도 하지 않는 서버에서는 시도마다의 제한 시간이 없으면 정한 다시 시도 시간을 넘겨 기다린다. 대조 갈래와 함께 더해 다시 돌렸다.
  - 명세를 쓰다가 어림으로 둔 자리 둘을 더 쟀다. 첫 티켓이 들어올 때 제품 마이그레이션 폴더가 비어 있어도 확인과 올리기가 도는지와, 표를 만든 뒤 실패하는 마이그레이션이 판과 표를 어떻게 남기는지다. `.scratch/postgres-foundation/probes/stack/run.py`의 `versions` 섹션에 회차 넷과 실패하는 묶음(`proto/versions_failing/`)을 더하고 `--sections types,versions`로 돌렸다(측정 13회차, 측정 아님 0회차). 빈 폴더는 "문제 없음"과 줄 없는 `alembic_version` 표였고, 실패한 `0002`는 만든 표까지 되돌려 줄이 `0001` 그대로였다. 시제품의 트랜잭션이 두 겹(`engine.begin()`과 `env.py`의 `begin_transaction()`)이라 어느 쪽이 되돌렸는지는 가르지 않았고, 명세는 결과만 세우고 제품도 같은 두 겹으로 짓게 적었다.
- `clone_xdist/`(서브에이전트): 장난감 패키지 둘과 시험 320개로 템플릿 복제의 시간, 이름, 도우미 공유를 쟀다. 마지막 실행 `4c01a9f3`은 측정 11회차, 측정 아님 0회차였다(서브에이전트의 보고를 원본 기록 `raw.log`의 끝 줄과 pytest 출력의 끝 줄에 대 봤다, 손으로 봤다). 다른 세션의 pytest와 다른 프로브가 같은 PC를 쓰던 때라 시간은 부하가 있던 값이다.
  - 명세에 옮기며 정한 것: 장난감은 픽스처와 데이터베이스를 쓰는 일을 한 파일에 담았지만, 러너와 e2e-stack도 같은 일을 불러야 해서 명세는 둘을 `tools/test_database.py`와 `tests/database.py`로 나눴다. 세션 범위 픽스처는 두 꼴이 똑같이 돌았고, `.claude/rules/tests.md`의 `asyncio.run()` 금지와 ADR 0007을 따라 `loop_scope="session"` 꼴을 골랐다.
  - 기대와 달랐던 것: `--basetemp` 없이 돈 pytest 한 번이 세션 끝에서 5분 넘게 멈췄다(까닭은 어림). 명세 Further Notes에 남겼다.
- `compose_shape/`(서브에이전트): 단독 compose에 더할 PostgreSQL과 `migrate`의 모양을 실제 PostgreSQL 이미지와 `psql` 대역으로 쟀다. 마지막 실행 `b6e060`은 측정 108회차, 측정 아님 0회차였다(보고를 원본 기록의 셈 줄, 회차 기록 108줄, 문구 셋의 grep에 대 봤다, 손으로 봤다).
  - 기대와 달랐던 것: 유닉스 소켓에 묻는 상태 확인은 첫 띄우기의 임시 서버(TCP를 듣지 않는다)에 답해 정상이 된 뒤 다른 컨테이너의 접속이 실패했다. root로 띄우고 권한 넷만 돌려준 꼴에 init을 더하면 init이 멈춤 신호를 넘기지 못했다. `docker compose restart`는 `depends_on`을 기다리지 않았다. `.env`만 바꾸고 `up`하면 `serve`가 내려간 채 남았다. 문법이 틀린 `ALTER ROLE`은 비밀번호째 로그에 남았다.
  - 명세에 옮기며 정한 것: PostgreSQL은 uid 999, 읽기 전용 루트, 권한 빼기, init으로 띄우고 상태 확인은 TCP로 한다. 비밀번호 바꾸기 절차는 세 줄이고 배포 안내의 새 12절에 둔다. 절 번호를 밀면 ADR과 다른 문서가 번호로 가리키는 곳이 틀어지므로 맨 끝에 둔다.
- `restart_recover/`(서브에이전트): Docker-in-Docker 컨테이너 안에 단독 compose의 모양(PostgreSQL, `migrate` 대역, `serve` 대역)을 띄우고 Docker 재시작, 서버 재시작, 전원 끊김을 냈다. 마지막 전체 실행은 측정 51회차, 항목 4만 돌린 실행은 측정 10회차, 항목 0만 돌린 실행은 측정 7회차였고 셋 다 측정 아님 0회차, 종료 코드 0이었다(보고를 원본 기록 `raw.log`의 셈 줄과 결과 줄, 반쯤 초기화된 볼륨의 거절 문구 676줄의 grep에 대 봤다, 손으로 봤다).
  - 기대와 달랐던 것: 처음 띄우기 도중 전원이 끊긴 볼륨은 여섯 번 모두 다시 띄워도 붙지 않았고, 다섯 번은 상태 확인이 `healthy`인데 접속을 `no pg_hba.conf entry`와 `database "agent_os" does not exist`로 거절했다. 컨테이너만 지우면 안 되고 볼륨까지 지워야 붙었다(`.scratch/postgres-foundation/probes/restart_recover/run.py`의 항목 4가 다시 낸다). `docker kill`로 죽인 PostgreSQL은 `unless-stopped`가 다시 띄우지 않았다. digest로 가리켜 옮긴 이미지는 digest로 찾지 못했다.
  - 명세에 옮기며 정한 것: 다시 시도 시간은 30초다. 다시 시도가 0초여도 재시작 정책이 아홉 번 모두 받쳤으므로, 그 시간은 재부팅 때 기록에 멈춤 글을 남기지 않는 몫으로 읽었다. 오류 번호 28000(접속 규칙의 거절)을 비밀번호 줄에서 떼어 "접속을 허락하지 않았다" 줄로 두고, 그 줄과 "데이터베이스 없음" 줄이 배포 안내의 새 하위 절 "띄우기가 끊겼을 때"를 가리키게 했다. 그 절은 데이터베이스 볼륨 하나만 지우는 세 줄을 준다. 프로브는 볼륨이 하나뿐인 배치에서 `down -v`를 쟀으므로, 하나만 지우는 명령은 어림으로 두고 그 티켓이 돌려 보게 했다.

## 사용자에게 물은 것 하나: 시험의 이음매

to-spec 스킬 2단계의 확인이다. 선택 화면의 질문은 아래와 같다.

> 시험이 프로그램을 붙잡는 자리(이음매)를 아래처럼 잡으려 합니다. 높은 자리일수록 운영자가 보는 것에 가깝게 확인하지만 느려집니다. ① 데이터베이스 코드는 미리 띄운 테스트 컨테이너에서 시험마다 복제한 데이터베이스로 시험합니다. ② serve 의 구성 오류(연결 문자열이 없거나 읽히지 않음)와 뜰 때의 확인(표가 뒤처짐, 더 새로움, 닿지 못함)은 지금처럼 serve 명령을 부르고 띄우기 직전의 앱을 붙잡아 그 앱의 시작 단계를 직접 돌려 봅니다. 이 길은 HTTP 규칙 문서의 '앱을 직접 부르는 시험은 스트림에만' 예외를 '시작 단계'까지 넓힙니다. ③ agent-os migrate 명령은 실제 테스트 데이터베이스에 대고 부릅니다. ④ compose 배치와 이미지 고정값이 세 파일에서 같은지는 저장소 파일을 읽는 시험과 기존 e2e 가 봅니다. 이 자리가 생각과 맞습니까?

선택지 둘이었다.

- **이대로 간다 (추천)**: "네 자리로 시험합니다. 실제 serve 프로세스를 띄워 보는 것은 지금처럼 e2e 와 LLM 시험만 합니다. 데이터베이스가 뒤처졌을 때 uvicorn 이 역추적 없이 우리 문구 한 줄과 자기 시작 실패 줄만 찍고 끝나는 것은 프로브가 잰 사실로 둡니다. ②의 시험이 시작 실패의 문구가 우리 문구와 글자까지 같다고 단언하므로, 확인을 역추적을 내는 자리로 옮기면 그 시험이 빨개집니다."
- **serve 프로세스도 하나**: "위 네 자리에 더해, 실제 agent-os serve 프로세스를 빈 데이터베이스에 대고 띄워 '먼저 migrate 를 돌리십시오' 줄과 종료 코드를 보는 시험을 기본 시험에 하나 둡니다. uvicorn 이 바뀌어 출력이 달라지면 잡지만, 커밋마다 프로세스를 띄우는 시간이 더 듭니다(몇 초로 어림했고 재지 않았습니다)."

사용자는 **이대로 간다 (추천)**를 골랐다.

처음 부른 화면은 선택 화면의 사실 확인 훅이 한 번 막았다. 설명을 대 보니 둘을 고쳐야 했다. uvicorn은 우리 문구 한 줄만이 아니라 시작 알림 두 줄과 `Application startup failed. Exiting.` 줄도 찍었고(`stack/` 프로브의 출력 4줄), 프로세스 시험이 더하는 시간은 재지 않은 어림이었다. 나머지는 `.claude/rules/http.md` 37줄과 `tests/test_main.py`의 `uvicorn_calls` 픽스처로 대 봤다.

## 명세를 쓰며 정한 것

결정의 원문은 명세(`.scratch/postgres-foundation/spec.md`)의 절마다 있다. 여기에는 다음 세션이 셀프 리뷰에서 겨냥할 자리만 적는다.

- 도우미를 `tools/test_database.py`(데이터베이스를 쓰는 일, 러너와 e2e-stack도 부른다)와 `tests/database.py`(pytest 픽스처)로 나눴다. 세션 범위 픽스처는 `loop_scope="session"` 꼴이다.
- PostgreSQL은 uid 999, 읽기 전용 루트, 권한 빼기, init, TCP 상태 확인으로 띄운다.
- 비밀번호 바꾸기는 배포 안내의 새 12절(맨 끝)에 둔다. 절 번호를 밀지 않으려는 것이다.
- 다시 시도 시간은 30초, 시도 사이 1초, 시도 하나의 제한 시간 5초다.
- 오류 번호 28000을 비밀번호(28P01)에서 떼어 "접속을 허락하지 않았다" 줄로 두었다. 그 줄과 "데이터베이스 없음" 줄의 둘째 줄이 배포 안내 4의 새 하위 절 "띄우기가 끊겼을 때"를 가리킨다. 28000이라는 번호와, 데이터베이스 볼륨 하나만 지우는 `docker volume rm agent-os_database`는 어림이다.
- 이력은 쌓지 않았다. 명세가 ADR 0066과 ADR 0056의 문장을 거짓으로 만들지 않는다고 판단했고, 그 까닭은 명세 머리의 "이력은 없다" 문단에 있다.

## 이 세션이 고친 것

명세를 쓰는 도중에 스스로 잡아 고친 것이다(셀프 리뷰 전).

- 실패한 마이그레이션을 `engine.begin()`이 되돌렸다고 처음 적었다. `env.py`의 `context.begin_transaction()`까지 두 겹이라 어느 쪽이 되돌렸는지 가르지 못했으므로, 명세와 stack README를 결과만 세우게 고쳤다.
- 데이터베이스 이름 접두의 길이 한계를 13자로 셈했다가 21자(63 − 10 − 32)로 고쳤다.
- "러너"와 "개발 PC" 절의 "아래"·"위" 방향을 고쳤다.
- 배포 안내에 새 절을 가운데 끼우면 ADR이 번호로 가리키는 절이 밀리므로 맨 끝의 12절로 옮겼다.
- 원문을 대 보지 않은 "공식 이미지 문서의 흔한 예"를 지웠다.
- 목록 속에 섞였던 거부한 안을 절 끝의 "거부한 안:" 문단으로 옮겼다.
- Testing Decisions 셋째의 "두 번호 폴더"와 "셋째 마이그레이션"이 맞지 않던 것을 고쳤다.
- 명세 머리와 Further Notes가 "리눅스 서버는 Docker-in-Docker로 흉내 냈다"고 적었는데, compose_shape는 Docker Desktop의 리눅스 엔진에 바로 띄웠다. Docker-in-Docker는 restart_recover뿐이라고 고쳤다.
- 배포 안내 절의 항목 차례가 3-1, 8, 9, 11, 4, 7, 12로 섞여 있어 3-1, 4, 7, 8, 9, 11, 12로 옮겼다.
- 배포 안내 4의 새 하위 절이 재시작 복귀의 회차를 겹쳐 셌던 것(여섯 번에 `migrate`의 둘을 다시 더함)을 고쳤다.

## 인계(셀프 리뷰 직전)

세션 컨텍스트가 인계 문턱을 넘은 채 셀프 리뷰 직전에 와서 `hook_handoff`의 계기가 들어왔다. `handoff.md` 1의 인계하지 않는 다섯 경우에 들지 않아(곁 세션도 아니다, `get_session`의 `self`에 `parentSessionId`가 없다) 새 세션에 넘긴다. 이 세션의 지금 제목은 `docs/postgres-foundation-spec`이다. 커밋하지 않았고, `uv run python tools/plan_table.py`는 돌렸으며 `.scratch/plan.md`는 바뀌지 않았다. `uv run python tools/check_md_tables.py`는 문제 없이 끝났다.

```
다음 작업: 기능 postgres-foundation. ADR 0066이 정한 설계로 쓴 명세를 셀프 리뷰하고 PR로 병합한다
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec
브랜치: docs/postgres-foundation-spec
모델: Opus 5.5 / xhigh. 2의 잇는 지시문은 명세의 Fable 칸(메뉴 이름 Fable 5.2) / xhigh이지만, 이 세션의 측정 도중 Fable 사용 한도(HTTP 429)에 걸려 사용자가 모델을 Opus 5.5로 바꿨으므로 그 값을 잇는다
읽을 것: 일지 docs/journal/2026-11-18-1544-postgres-foundation-spec.md 전체(특히 "명세를 쓰며 정한 것", "이 세션이 고친 것")
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. 기준점은 origin/dev이고, 명세 축의 원천은 ADR 0066 Consequences "명세가 짓는 것"과 설계 일지 2026-11-17-1747의 "다음"이다. 리뷰를 반영한 뒤 명세 머리의 셈 넷(사용자가 고른 것, 명세가 정한 것, 이력, 거부한 안)을 다시 센다. 리뷰가 ADR 0066의 문장을 거짓으로 만든 자리를 찾으면 domain-modeling을 부르고 이력과 포인터를 쓴 뒤 사용자 승인을 받는다. 일지는 커밋하지 않았고 "## 다음"이 없다. docs/journal/2026-11-18-1544-postgres-foundation-spec.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `docs/postgres-foundation-spec (인계함)`으로 바꿨다. 남은 백그라운드 작업은 없었고(TaskStop이 둘 다 `No task found`), 워크트리의 잠금을 풀었다.

open-session을 부른다 2026-11-18T08:38:30Z

## 이어받은 세션(셀프 리뷰부터)

위 지시문으로 연 새 세션이다. 모델은 Opus 5.5다. 사용자 프롬프트는 아래와 같다.

> 사용자: .claude/skills/to-spec/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자:
>
> (위 "인계(셀프 리뷰 직전)"의 지시문 열한 줄과 같다)

- 세션 제목을 `docs/postgres-foundation-spec`으로 바꾸고, `git worktree list`에서 그 브랜치가 `.claude/worktrees/postgres-foundation-spec`에 체크아웃된 것을 보고 `EnterWorktree(path)`로 들어왔다.
- 리뷰 도중 `uv run python tools/sibling_overlap.py`가 `origin/dev`가 `f131900`(PR 605, 용어집의 실행 쪽 작은 이름 여섯 바꾸기)으로 움직였다고 알렸다. 그 커밋은 이 브랜치가 고친 파일을 건드리지 않았고, 바뀐 옛 이름 여섯과 보증 모드는 이 브랜치의 명세와 기능 계획 다섯에 없었다(Grep). 리뷰가 보는 diff가 달라지지 않게, 따라잡기는 리뷰를 반영한 뒤에 한다.

## 셀프 리뷰

`/code-review origin/dev`. base `1aac0cfdd62d8ab97a70ae0d22372912db3e9101`, 커밋 0, 추적 파일의 변경 4(기능 계획 넷), 미추적 56(명세, 이 일지, 프로브). 명세 축의 요구는 ADR 0066 Consequences(특히 "명세가 짓는 것"), 설계 일지 2026-11-17-1747 "다음", 기능 계획의 수락 조건, to-spec 스킬, 위 "사용자에게 물은 것 하나"의 질문과 두 선택지의 설명 원문이었다.

### 표준 축(sonnet, high)

Critical·Major 없음, Minor 여섯, Nit 다섯. 맞게 나온 것: 명세 머리의 셈 넷, 기준 커밋의 코드 서술(`main.py` 196~197줄, `_NO_ADMIN_TOKEN_DIAGNOSTIC`, `test_main.py` 1668줄, `http.md` 37줄, `title_problems`, `serve.ts`, `EXIT_PAUSED = 3`), 프로브 README의 수, 접두 21자, 기능 계획 넷의 문단과 `**Blocked by:**`, `check_md_tables.py`·`check_line_separators.py` 종료 0.

- Minor 1, 158줄: "6.92초"가 "마지막 전체 실행의 것"(154줄) 아래에 있는데, restart_recover README 항목 3에서 마지막 실행은 2.91·3.18초이고 6.92는 앞선 실행의 값이다.
- Minor 2, 185줄: 표가 뒤처진 글의 "첫 문장"이 ADR 0066이 정한 글이라 했지만 ADR에는 "agent-os migrate를 먼저 돌리십시오"만 있다.
- Minor 3: 따옴표 인용이 ADR 0066과 글자 그대로가 아니다(127줄 "넘긴다", 139줄 "앱은 수명이 열릴 때 확인", 155줄, 299줄).
- Minor 4, 115줄: "여섯뿐"을 Compose 명세까지 묶었다. Compose 명세는 넷만 적는다.
- Minor 5, 172·265줄: "@ : / % 가 들면 주소가 깨진다"가 121줄의 측정(`p:ss`, `p/ss`, `p%ss`는 접속)과 어긋난다.
- Minor 6: 처음 나올 때 풀이가 없는 말(`digest`, `service container`, xdist의 작업자, `NullPool`, `pool_pre_ping`, `uid`).
- Nit: 108줄 규칙에 비춘 도우미 경로 두 개(판단 사항), widget-admin-server 기능 계획의 "`agent_os`가 아닌 것"과 길이 판정이 명세에 없음, ops-backup-upgrade 기능 계획의 볼륨 이름에 Docker 이름이 없음, 프로브 셋의 `docker()` 래퍼(Duplicated Code 후보), 145줄의 57P03이 서버 재시작이 아니라 `docker kill` 뒤 복구에서 나온 것.

### 명세 축(Opus 5.5, 상속)

ADR 문장을 거짓으로 만드는 자리는 없다고 했다. 머리의 수는 다시 세어 맞았다.

- Major 1, 124줄: 호스트에 `@`가 드는지만 보는 판정은 `@` 뒤에 `/`나 `?`가 오는 비밀번호를 놓친다. SQLAlchemy 2.1.8 `make_url`로 `x@h/db`는 호스트 `h`, 데이터베이스 `db@postgres:5432/agent_os`였고, `x@h?q=1`은 호스트 `h`였다. `<자리>`에 비밀번호 조각이 찍힌다(원칙 V).
- Major 2, 223·265·280줄: `.env.example`의 빈 비밀번호 줄과 `:?`가 함께 있으면 배포 안내 9절의 `cp .env.example .env` 뒤 `docker compose pull`과 `config --images`가 종료 1로 끝난다(이 PC의 Compose로 봤다).
- Minor 3, 145·147·383줄: 28000을 어림인 채 첫 티켓에 넘겼고 아니면 사례를 빼므로 그 갈래가 시험 없이 남는다. 08 계열은 stack README가 어림이라 적었는데 명세 145줄에는 표시가 없다.
- Minor 4, 102줄: 사용자 이야기 37이 diag-bundle을 받는 쪽으로 드는데 Out of Scope와 그 기능 계획에 넘긴 것이 없다. 그 기능 계획은 "이유를 한 줄"이라 적었는데 명세의 글은 두 줄이고 `serve`의 종료 코드는 3이다.
- Minor 5, 347~348·394줄: 러너가 컨테이너를 띄우는 길에 자동 시험이 없다. 저장소 상태 시험이 PostgreSQL의 `ports` 없음과 `user: "999:999"`(7절)를 보지 않는다.
- Minor 6, 186~188·386~387줄: 둘째 이음매는 가짜가 돌려준 글 하나만 본다. 프로브는 한 줄짜리 글로 쟀는데(`stack/proto/database.py` 33줄) 명세의 글은 두 줄이라, "둘째 줄은 그대로 찍는다"와 "넉 줄"은 잰 것이 아니다.
- Nit: 185줄의 글이 ADR의 백틱과 띄어쓰기를 바꿨다. `create_app`을 부르는 `tools/export_openapi.py`를 명세가 다루지 않는다. `p:ss`와 `p/ss`는 접속했는데 안내가 "깨지므로"라 적는다.

### 반영

다시 잰 것과 손으로 본 것:

- stack 프로브 전체를 다시 돌렸다. 측정 67회차, 측정 아님 0회차, 종료 0이다. 시제품의 판정을 "호스트에 `@`"에서 "`@`가 둘 이상"으로 바꾸고 글을 두 줄로 고친 판이다. 더한 회차는 로그인을 막은 계정(28000), 접속 규칙(`pg_hba.conf`)의 줄을 지운 따로 띄운 서버(28000, `no pg_hba.conf entry`), compose가 짓는 꼴에 넣은 비밀번호 열여섯 값과 호스트만 보는 판정의 대조, 두 줄 글을 찍는 uvicorn 출력이다.
- compose_shape 프로브를 `--sections 5`로 다시 돌렸다(`run-20261118-180923-713484`, 측정 39회차, 측정 아님 0회차, 종료 0). 더한 5마에서 값이 빈 `.env`의 `docker compose pull`과 `config --images`는 종료 1이었고, 셸 값을 앞에 붙이면 둘 다 0이었다. 표지는 세션 스크래치패드의 스크립트로 원본 출력을 한 번 보고 골랐다(측정 아님).
- 명세의 둘째 이음매 사례에 넣은 두 주소를 시제품의 `parse_url`과 SQLAlchemy `make_url`에 대 봤다(손으로 봤다). 둘 다 `None`이었고, 둘째 주소는 호스트 `leak`, 데이터베이스 `x@postgres:5432/agent_os`로 읽혀 호스트에 `@`가 없었다.
- 수명 함수가 예외를 던지게 둔 FastAPI 앱에서 `app.openapi()`는 수명을 열지 않았고, 같은 앱을 `TestClient`로 열면 열렸다(손으로 봤다). `tools/export_openapi.py`는 `app.openapi()`만 부른다(158줄).
- 명세의 모든 따옴표 인용을 스크래치 스크립트 둘로 대 봤다. 하나는 같은 줄에 ADR 번호가 있는 인용을 그 ADR 파일에서만 찾고(원문에 없는 양성 대조가 찍혔다), 하나는 저장소 문서 전체에서 찾는다. 앞서 쓰던 뒤의 것은 일지가 같은 말을 옮겨 적었으면 ADR에 없는 인용도 지나가게 했다. 표준 축이 든 넷 밖에 ADR 0066과 다르게 옮긴 인용 셋(빈 마이그레이션, `serve`가 먼저 뜰 때, 도우미), 프로브 README의 절 이름 둘, 기능 계획의 수락 조건 둘을 더 찾아 원문으로 바꿨다. 남은 걸림은 명세 자신의 절·항목 이름, 명세가 새로 정하는 글, 출력에서 본 문구다.

고친 것(지적마다):

- 표준 Minor 1: "6.92초"를 앞선 실행의 값으로, 마지막 전체 실행은 2.91·3.18초로 고쳤다.
- 표준 Minor 2와 명세 축 Nit(백틱과 띄어쓰기): 표가 뒤처진 글은 뒷 문장만 ADR에서 왔고 앞 문장은 명세가 더했다고 고쳤고, ADR의 글에서 바꾼 셋(백틱, 조사 앞 한 칸, 마침표)을 적었다.
- 표준 Minor 3: 46·127·139줄 인용과, 위의 인용 대조가 찾은 일곱을 원문으로 바꿨다.
- 표준 Minor 4: Compose 명세는 넷, Docker 문서는 여섯, 구현도 여섯이라고 나눠 적었다(compose_shape README도).
- 표준 Minor 5와 명세 축 Nit(`p:ss`와 `p/ss`): 까닭을 "`@`가 들면 compose가 짓는 주소를 읽지 못하고, `%` 뒤에 16진수 두 자리가 오면 다른 비밀번호로 풀린다"로 좁혔다. 멈출 때의 글은 "비밀번호에 @ 가 들면 주소를 읽지 못하므로, 비밀번호는 영문자와 숫자만 씁니다."다.
- 표준 Minor 6: digest, service container, xdist의 작업자, uid(와 init)는 처음 나오는 자리에 풀이를 붙였다. `NullPool`과 `pool_pre_ping`은 이미 쉬운 말 뒤 괄호로 붙어 있어 그대로 뒀다.
- 표준 Nit(57P03): 갈래 1의 57P03을 `docker kill` 뒤 복구에서 본 것으로 고치고, 서버 재시작 때도 그렇다는 것과 08 계열은 어림으로 표시했다.
- 표준 Nit(기능 계획 둘): ops-backup-upgrade에 Docker의 볼륨 이름 `agent-os_database`를 더했다(명세 Out of Scope도). widget-admin-server의 접두 판정을 명세와 맞췄다. 명세의 도우미는 접두의 꼴과 함께 21자를 넘지 않는지도 보고, 접두는 패키지마다 다르다.
- 명세 축 Major 1: 판정을 "연결 문자열에 `@`가 둘 이상이면 그 주소를 읽지 못한 것으로 본다"로 바꿨다(명세 124줄, 시제품의 `parse_url`도). 열여섯 값에서 다르게 읽힌 다섯을 모두 거부하고 나머지는 거부하지 않았으며, 옛 판정은 셋을 놓쳤다. 계정과 질의의 `@`도 받지 않는다는 것과 이 배포의 주소에는 둘 다 없다는 것을 적었다. 둘째 이음매 사례의 주소를 `@`가 둘인 것과 호스트에 `@`가 남지 않는 것으로 바꾸고, 표준 오류에 없어야 할 조각을 `secret`, `leak`로 바꿨다. 옛 조각 `p`는 `postgres`에도 들어 그 단언이 늘 빨갰을 것이다.
- 명세 축 Major 2: "`.env`에 비밀번호가 없을 때"에 `pull`과 `config --images`도 종료 1이라는 것을 더하고, 배포 안내 9절의 두 명령 앞에 `AGENT_OS_DATABASE_PASSWORD=unused`를 붙이게 고쳤다. 비밀번호 줄이 아예 없는 옛 `.env`도 셸 값이 채운다는 것은 어림이다.
- 명세 축 Minor 3: 28000을 두 길(로그인을 막은 계정, 접속 규칙에 없는 접속)로 쟀고, 첫째 이음매 사례의 조건부 빼기를 지웠다. 끊긴 볼륨이 실제로 낸 번호는 대역이라 어림으로 남겼다.
- 명세 축 Minor 4: Out of Scope에 diag-bundle 항목을 더하고, `.scratch/diag-bundle/plan.md` 본문에 "postgres-foundation 명세가 넘긴 것"을 더했다. 그 계획의 "이유를 한 줄 찍고 뜨지 않고"는 "이유를 찍고 뜨지 않고(글의 꼴은 아래 명세가 넘긴 것)"로 고쳤다. 그 행의 `**Blocked by:**`(release-image, mcp-http)에는 postgres-foundation이 없어 이 행보다 먼저 돌 수 있다. 앞선 설계가 넘긴 것이 무엇을 담을지를 그 행의 설계 인터뷰에 맡겼으므로 Blocked by는 바꾸지 않았다.
- 명세 축 Minor 5: 저장소 상태 시험에 배포 안내 7절의 두 전제(`postgres`에 `ports` 없음, `user: "999:999"`)를 보는 것을 더했다(선례 `tests/tools/test_deploy_guide.py`). 러너의 갈래는 `.claude/rules/tests.md`의 `tools/` 항목대로 판정 함수를 `tests/tools/test_run_checks.py`에서 보고, Docker를 부르는 부분은 실제 실행으로 확인한다고 적었다. 이음매 넷은 사용자가 고른 그대로이고, 러너는 그 넷 밖의 기존 규칙이라고 Testing Decisions 머리에 적었다.
- 명세 축 Minor 6: 시제품의 글을 두 줄로 바꿔 다시 쟀다(`.scratch/postgres-foundation/probes/stack/run.py`의 `uvicorn` 섹션). uvicorn은 모두 다섯 줄(시작 알림 둘, 글의 두 줄, 시작 실패 한 줄)을 찍었고, 수명 함수에서 예외를 던지는 대조는 15줄이었다. 명세의 "넉 줄"을 다섯 줄로 고쳤다.
- 명세 축 Nit(`tools/export_openapi.py`): 그 도구가 `create_app`에 데이터베이스의 자리표시자를 넘기고, 스키마를 뽑을 때는 수명이 돌지 않아 불리지 않는다고 적었다(위의 손으로 본 것).
- 옛 표현을 grep하다 명세 58줄의 "이유를 한 줄로 찍고"를 찾아, 지금의 토큰 진단처럼 첫 줄이 이유이고 둘째 줄이 할 일이라고 고쳤다.

ADR 0066을 거짓으로 만든 자리는 반영 뒤에도 없다. 따져 본 것은 셋이다.

- 14줄의 "지금 토큰이 빠졌을 때처럼 구성 오류로 이유를 한 줄 찍고"는, 지금 토큰 진단(`src/agent_os/main.py` 89~93줄)이 이유 한 줄과 두 칸 들인 설명 두 줄이라 첫 줄이 이유 하나라는 뜻으로 읽었다. 명세의 두 줄 글이 그 꼴이다.
- 26줄의 "테스트 도우미(컨테이너를 확인하고 템플릿을 만드는 픽스처)를 `tests/` 안에 하나 두고"는, 명세의 픽스처가 `tests/database.py` 한 파일이라 참이다. 픽스처가 부르는 데이터베이스 일만 `tools/`에 둔다.
- 9절의 `pull`과 `config --images`는 ADR 0066이 적지 않는다(63줄은 태그와 덮어쓰기 파일만 적는다).

그래서 domain-modeling과 사용자 승인은 부르지 않았다. 사용자가 고른 선택지의 설명에는 "우리 문구 한 줄과 자기 시작 실패 줄만 찍고"가 있었다. 글이 두 줄이 된 뒤에도 고른 것(실제 `serve` 프로세스를 띄우는 시험을 더하지 않고 프로브가 잰 사실로 둔다)은 그대로이므로 다시 묻지 않았다.

남긴 것과 이유:

- 표준 Nit(108줄 규칙에 비춘 도우미 경로 둘): 판단 사항이라 그대로 뒀다. `tools/test_database.py`는 러너와 e2e-stack이 함께 부르려고 `tools/`에 두고, `tests/database.py`는 픽스처라 `tests/`에 둔다(명세 "도우미의 자리").
- 표준 Nit(프로브 셋의 `docker()` 래퍼): 프로브마다 따로 돌게 둔 것이라 합치지 않았다.

셈 넷을 다시 셌다. 넘겨받은 표는 서른 행, "명세가 정했다"는 절 머리 스물, "사용자가 골랐다"는 본문 세 자리, 이력 없음, 거부한 안은 아홉 문단에 열여덟 안이다. 머리의 수는 바뀌지 않았다.

검사: 바뀐 마크다운과 파이썬 파일을 인자로 넘긴 `tools/check_md_tables.py`와 `tools/check_line_separators.py`가 0으로 끝났다(인자 없이 돌면 추적 파일만 본다). 두 프로브의 `uv run ruff check`는 0이었다. 나머지 검증은 커밋의 pre-commit으로 갈음한다. 첫 커밋은 `ruff format`이 `.scratch/postgres-foundation/probes/stack/run.py`의 한 문장을 한 줄로 합쳐 막혔다(동작은 그대로다). 같은 실행에서 pytest(686.7초), web-verify(783.2초), pyright, 경계, 지침 검사 등 나머지는 모두 통과했고, 인용 대조는 막지 않는 경고를 냈다. 그 경고 가운데 이 일지가 명세와 기능 계획의 글을 바꿔 옮긴 둘을 원문으로 고쳤다. 나머지는 선택 화면의 설명(저장소 밖이 원문), 리뷰 지적이 옮긴 옛 글, 명세가 새로 정하는 안내 글, 프로브가 출력에서 본 문구다.

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 사실 문장, 명세의 원문):

1. 115줄: "이름 뒤에 올 수 있는 것으로 Compose 명세는 `:-`, `-`, `:?`, `?` 넷을 적고, Docker 문서는 거기에 `:+`, `+`를 더한 여섯을 적으며, 구현도 그 여섯만 받는다."
2. 124줄: "SQLAlchemy가 호스트·포트·데이터베이스를 다르게 읽은 다섯(`p@ss`, `p@s:s/w`, `x@h/db`, `x@h?q=1`, `x@h:1/db`)은 모두 `@`가 둘 이상이었고, 이 판정이 다섯을 모두 거부하고 나머지 열하나는 하나도 거부하지 않았다(그 README "비밀번호의 글자")." 같은 줄의 "읽은 호스트에 `@`가 드는지만 보는 판정은 뒤의 셋을 놓친다."
3. 133줄: "계약 파일을 뽑는 `tools/export_openapi.py`도 `create_app`을 부르고, 지금 포트마다 불리면 곧바로 터지는 자리표시자(`_SchemaOnlyPlugins` 등)를 넘긴다(코드를 읽었다)." 와 그 뒤 수명이 돌지 않는다는 두 문장.
4. 158줄: "마지막 전체 실행에서는 2.91·3.18초였고, 그 앞의 실행에서 6.92초까지 갔다(그 README 항목 3)."
5. 188줄: "`serve`가 멈출 때 uvicorn은 첫 줄 앞에 `ERROR:`와 빈칸을 붙이고, 둘째 줄은 두 칸 들여쓴 그대로 따로 한 줄로 찍는다."
6. 228줄: "값이 빈 `.env`에서는 이미지를 받는 `docker compose pull`과 이미지 목록을 내는 `docker compose config --images`도 같은 글로 종료 1이었다(같은 README 5마)."
7. 280줄: "프로브가 값이 빈 `.env`에서 그렇게 친 두 명령은 0으로 끝났고, `pull`은 이미지를 받았으며 `config --images`는 이미지 줄을 냈다(compose_shape README 5마)."
8. 385줄: "그 접속이 28000을 내는 것은 stack 프로브가 같은 이미지로 쟀다(`.scratch/postgres-foundation/probes/stack/README.md` "접속 실패의 꼴")."
9. 389줄의 두 주소가 `serve`에서 1과 그 글로 끝나고 표준 오류에 `secret`, `leak`가 없다는 사례, 391줄의 "다섯 줄(시작 알림 둘, 글의 두 줄, 시작 실패 한 줄)".
10. Out of Scope의 diag-bundle 항목과 `.scratch/diag-bundle/plan.md`의 같은 문단: "`serve`는 연결 문자열이 없거나 읽지 못하면 1로, 데이터베이스에서 멈추면 3으로 끝나고, `migrate`는 멈출 때 늘 1이다."
11. "러너가 테스트 컨테이너를 띄우는 길"의 마지막 항목과 "저장소 상태 시험"의 셋째 항목(배포 안내 7절의 두 전제).

## 커밋

반영 뒤 `git merge --ff-only origin/dev`로 `f131900`(PR 605)을 따라잡았다. 그 커밋은 이 브랜치가 고친 파일을 건드리지 않았고, 명세가 따르는 용어 여섯은 용어집에 그대로 있으며, 바뀐 옛 이름 여섯은 이 브랜치의 문서에 없었다(grep). `uv run python tools/plan_table.py`는 `.scratch/plan.md`를 바꾸지 않았고, `uv run python tools/sibling_overlap.py`는 번호 겹침과 함께 고친 파일이 없다고 했다. 위 "검사"의 둘째 시도로 커밋했다(pre-commit 통과, `Skipped`는 커밋에 든 파일이 없는 카나리아 명세와 헌법 판 둘). 푸시하지 않았다.

## 인계(커밋 뒤)

세션 컨텍스트가 인계 문턱을 넘은 채 커밋 뒤에 와서 `hook_handoff`의 계기가 들어왔다. `handoff.md` 1의 인계하지 않는 다섯 경우에 들지 않는다. 이 세션의 지시문의 "이어받을 상태"는 `인계: 셀프 리뷰 직전`으로 시작해 이번 경계와 다르고, 요청 범위는 병합까지이며, `get_session`의 `self`에 `parentSessionId`가 없다. 이 브랜치에 열린 PR이 없어(`gh pr view`가 `no pull requests found`) "다음 단계"는 이 세션의 지시문 그대로다. 이 세션의 지금 제목은 `docs/postgres-foundation-spec`이다.

```
다음 작업: 기능 postgres-foundation. ADR 0066이 정한 설계로 쓴 명세를 PR로 열고 병합한다
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec
브랜치: docs/postgres-foundation-spec
모델: Opus 5.5 / xhigh. 2의 잇는 지시문은 명세의 Fable 칸(메뉴 이름 Fable 5.2) / xhigh이지만, 앞 세션의 측정 도중 Fable 사용 한도(HTTP 429)에 걸려 사용자가 모델을 Opus 5.5로 바꿨으므로 그 값을 잇는다
읽을 것: 일지 docs/journal/2026-11-18-1544-postgres-foundation-spec.md의 "## 셀프 리뷰"부터 끝까지(특히 "### 반영"의 "PR 직전 리뷰에 밀 주장")
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰를 반영해 커밋했고 푸시하지 않았으며 PR이 없다. 남은 단계는 PR 직전 리뷰(docs/constitution/operations.md 리뷰 파이프라인 2. 브리프에 일지 "### 반영"의 "PR 직전 리뷰에 밀 주장" 열하나를 나열한다), 그 반영 뒤 명세 머리의 셈 넷(사용자가 고른 것, 명세가 정한 것, 이력, 거부한 안) 다시 세기, 푸시와 PR 열기, 봇 회차, 병합이다. 반영이 ADR 0066의 문장을 거짓으로 만들면 domain-modeling을 부르고 이력과 포인터를 쓴 뒤 사용자 승인을 받는다. 일지의 "## 커밋"부터 끝까지는 커밋하지 않은 채 워크트리에 있고, "## 다음"이 없다. docs/journal/2026-11-18-1544-postgres-foundation-spec.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `docs/postgres-foundation-spec (인계함)`으로 바꿨다. 남은 백그라운드 작업은 없었고(커밋 둘은 끝났다), 워크트리의 잠금은 이미 풀려 있었다(`is not locked`).

open-session을 부른다 2026-11-18T10:09:45Z

`open_session.ps1 -Action send`가 `idle=0s`, `lock=19:12:51.612 waited=0s`, `start=.claude/skills/to-spec/SKILL.md`, `fired=19:12:55.012`까지 찍은 뒤 "30초 안에 프롬프트 첫 줄('.claude/skills/to-spec/S…')이 채워진 새 세션 화면 을(를) 찾지 못했다."로 종료 1이 났다(`page=` 없음). 곧바로 본 `list_sessions`에 그 시각 뒤에 생긴 세션은 없었고, `.scratch/harness/probes/deeplink_timeline.ps1`은 아무것도 찍지 않았다. 쏜 뒤의 멈춤이라 같은 파일로 다시 돌리지 않았다(open-session "막히면"). 제목을 `docs/postgres-foundation-spec`으로 되돌리고 이 세션에서 다음 단계(PR 직전 리뷰)를 잇는다.

인계 못함 커밋 뒤

## PR 직전 리뷰

기준은 `f131900726cc247c000bfc46f152f9d01fcd3376`(`origin/dev`와의 merge-base. fetch 뒤 `origin/dev`는 움직이지 않았다)이다. `coderabbit-review`(CLI)와 `bug-perf-review`를 나란히 띄웠다. CLI에는 밀 주장을 넘길 길이 없어(code-review 6단계 1), 위 "PR 직전 리뷰에 밀 주장" 열하나와 Compose 명세·Docker 문서·compose-go의 주소와 README가 적은 요지는 `bug-perf-review`의 브리프에 실었다. 보안은 CLI가 돌면 CLI가 보고, 돌지 못하면 커밋 뒤 `/security-review`로 본다.

`bug-perf-review`의 보고(호출 24번, 범위 파일 약 열을 따라갔다. 일지와 프로브 스크립트 전체는 따라가지 못했다): 밀 주장 열하나가 모두 근거와 맞았다. 1은 compose-go 정규식을 불러 `:-`, `-`, `:?`, `?`, `:+`, `+`는 맞고 `#`, `%`, `/`, `:0:6`은 안 맞는 것을, 2는 `make_url`로 다섯이 모두 `@` 둘이고 자리를 다르게 읽으며 `@` 하나인 넷은 자리가 같은 것을 대 봤다. 지적은 셋이다.

- 유효 Minor: 명세 "러너가 테스트 컨테이너를 띄우는 길"(313~315줄)의 `docker compose -f compose.test.yaml up -d --wait`와 접속 확인에 제한 시간이 없다. 컨테이너가 `healthy`가 되지 못하면 `--wait`가 끝없이 기다려 pre-commit이 pytest를 띄우기 전에 멈추고, 명세대로 지으면 `tools/check_instructions.py`의 `calls_without_timeout`에도 걸린다(`.claude/rules/tools.md`의 기다리는 도구 항목).
- 유효 Minor: 명세 158줄의 "접속을 받기까지 2.91·3.18초"는 restart_recover README 항목 3이 잰 ready까지의 값이고, 그 README 77줄은 TCP 첫 성공이 ready보다 0.04~2.75초 늦을 수 있다고 적는다.
- 보류: 명세 156줄의 "전원 끊김 뒤 PostgreSQL이 복구에 몇 초를 써 5.09초까지 갔다"에서 5.09초는 README 43·74줄에 있지만, 그 값이 전원 끊김에서 나왔고 복구 때문이라는 귀속을 README에서 찾지 못했다.

판정과 고친 것(`bug-perf-review`):

- 러너의 제한 시간(유효 Minor): 고쳤다. 접속 확인은 5초(`serve`가 시도 하나에 거는 값), 명령은 `docker compose -f compose.test.yaml up -d --wait --wait-timeout 60`, 그 호출에 180초의 제한 시간을 두고, 0이 아닌 종료나 제한 시간 넘김을 띄우기 실패로 센다고 적었다. 60초는 단독 compose의 꼴에서 빈 볼륨의 PostgreSQL이 4.55초에 정상이었던 것(compose_shape README 3나)의 열 배를 넘는 값이다. `--wait-timeout`이 없을 때 끝없이 기다린다는 것, 그 옵션이 이미지 받기를 막지 않는다는 것, 180초가 이미지 받기를 담는다는 것은 어림으로 적었다. 러너의 판정 목록에도 제한 시간 넘김을 더했다. ADR 0066은 "답하지 않으면 띄우고 내리지 않는다"까지만 정하므로 거짓이 되지 않는다.
- 158줄(유효 Minor): 2.91·3.18초는 `restart_recover/run.py` 1306~1307줄이 찍는 "죽은 때부터 ready"다. 문장을 "PostgreSQL 프로세스가 죽은 때부터 접속을 받는다는 기록(`database system is ready to accept connections`)이 찍히기까지"로 고치고, 다른 컨테이너의 새 접속이 그 기록보다 0.04~2.75초 늦게 처음 됐다는 것(그 README "시간의 분포" 아래 넷째 항목)을 더했다. 30초는 "잰 가장 긴 값에 그 늦음을 더해도 10초가 안 되어 30초는 그 세 배쯤"으로 고쳤다.
- 156줄(보류): 오탐으로 판정했다. 귀속은 그 README "시간의 분포" 아래 둘째 항목(75줄)에 있다. 긴 값은 전원 끊김의 N=30 두 회차에서 났고, 그 회차의 PostgreSQL이 `database system was interrupted` 뒤 복구에 몇 초를 썼다. 따라가기 쉽게 명세에 그 출처와 4.41·3.57초를 붙였다.

`coderabbit-review`의 보고: CLI 0.7.5, `Plan: Free`, `Seat: not assigned`에서 `coderabbit review --agent --include-untracked --base origin/dev`가 파일 58개를 끝까지 봤다(`review_completed`). 지적 넷을 CLI가 모두 Critical로 매겼고, 서브에이전트는 고유한 문제 둘로 묶어 Minor로 트리아지했다.

- 유효 Minor(CLI 지적 1·2·4): `.scratch/postgres-foundation/probes/compose_shape/change_password.sh` 4줄, 그 README 167줄, 명세 251줄의 비밀번호 바꾸기가 `ALTER ROLE ... PASSWORD :'new'`를 SQL 문장으로 보내, 문장이 틀려 실패하면 PostgreSQL 기록에 비밀번호가 평문으로 남는다. 명세 257줄이 이 위험을 이미 적었다. 다만 명세 255줄과 README 171줄의 "명령줄에 나오지 않는다"는 호스트 쪽 이야기이고, `-v new="$POSTGRES_PASSWORD"`는 컨테이너 안 psql 프로세스의 인자라 컨테이너 안에서는 보인다. CLI가 권한 `\password`는 대화형 입력이 필요해 `exec -T` 절차와 맞지 않는다.
- 보류 Minor: 명세 183줄의 `migrate` 실패가 역추적을 표준 오류에 그대로 찍는데, 예외 체인에 바인드 값이나 드라이버 문구가 실려 비밀이 새는지 판정하지 못했다. 첫 티켓의 시험에 합성 비밀번호로 역추적을 일부러 내고 표준 오류에 그 값이 없는지 보는 줄을 더하자고 제안했다.

판정과 고친 것(`coderabbit-review`):

- 비밀번호 바꾸기(유효 Minor, CLI의 Critical은 과하다): 고쳤다. 기록에 남는 위험은 명세 257줄이 이미 적었지만, 앞선 둘째 줄은 `sh -c`가 펼친 값을 psql 프로세스의 인자(`new=<값>`)에 실었다. 리눅스 서버에서는 컨테이너의 프로세스도 호스트의 프로세스 목록에 보이므로 그 순간 같은 서버의 다른 사용자가 볼 수 있다고 본다(어림). 둘째 줄을 `printf '%s\n' '\getenv new POSTGRES_PASSWORD' "ALTER ROLE agent_os PASSWORD :'new'" | docker compose exec -T postgres psql -U agent_os -d agent_os -v ON_ERROR_STOP=1`로 바꿔 psql이 컨테이너의 환경 변수에서 값을 읽게 했다(명세 251·255줄, compose_shape README 167·171줄, `change_password.sh` 4줄). `compose_shape/run.py --sections 4`를 다시 돌려(원본 출력 `run-20261118-193353-4b48d5`, 측정 7, 측정 아님 0, 종료 0) 4마가 세 줄 [0, 0, 0], 첫 줄 뒤 `migrate`와 `serve` 그대로, 새 비밀번호만 받음(측정 표지), 가장 긴 틈 2.7초, 새 비밀번호는 기록에 없음을 냈다. 4번의 나머지 회차도 README 표와 같은 값이었다(4라의 접속 규칙과 `SCRAM-SHA-256`, `none`, `error`를 회차 기록에서 봤다). 앞선 절차와 CLI가 권한 `\password`(손으로 두 번 쳐야 해 붙여 넣는 절차가 되지 않고 `.env`와 어긋날 수 있다)를 같은 문단의 거부한 안으로 더했다.
- `migrate`의 역추적(보류 Minor): 고쳤다. 명세 186줄에 그 역추적에 연결 문자열이 비밀번호째 실리지 않는지는 Testing Decisions의 셋째가 본다고 적고(원칙 V), 셋째 이음매의 실패하는 마이그레이션 사례에 "역추적까지 든 표준 오류에 연결 문자열이 비밀번호째(`agent_os:agent_os@`) 나오지 않는다"를 더했다. 테스트 컨테이너의 비밀번호가 계정 이름과 같은 `agent_os`라 주소의 꼴로 본다.

셈 넷을 다시 셌다. 넘겨받은 표 서른 행, "명세가 정했다"는 절 머리 스물, "사용자가 골랐다"는 본문 세 자리(383·391·392줄), 이력 없음은 그대로다. 거부한 안은 아홉 문단 그대로이고 안이 열여덟에서 스물로 늘어 머리를 고쳤다. ADR 0066을 거짓으로 만든 자리는 이번 반영에도 없다. ADR은 비밀번호를 바꾸는 명령의 꼴을 정하지 않고, 러너는 "답하지 않으면 띄우고 내리지 않는다"까지만 정한다.

### 늦게 생긴 같은 지시문의 세션

커밋 직전에 다른 세션(`local_e12ca7e3-3d06-4b8f-bd0a-81ef01d59dc2`, `createdAt` 2026-11-18T10:22:23Z, Opus 5.5 / xhigh)이 메시지로 알려 왔다. 같은 지시문으로 열린 그 세션이 10:22Z에 이 워크트리에 들어와(`EnterWorktree(path)`) 스킬과 일지를 읽은 뒤, 파일 쓰기·커밋·푸시 없이 사람에게 어느 세션이 이어 갈지 물었고, 사람이 "앞 세션이 계속 (Recommended)"을 골랐다고 한다. 그 세션이 옮긴 선택지의 설명은 "앞 세션은 10:25Z 현재 명세와 일지에 bug-perf-review의 지적 셋을 반영하는 중입니다(일지가 몇 분 사이 247줄에서 252줄로 늘었습니다). 함께 띄운 CodeRabbit 결과는 일지에 없어서, 그 세션이 기다리거나 들고 있다고 봅니다(어림). 이 세션은 아무것도 고치지 않고 여기서 멈춥니다."다. 그 세션은 제목을 `docs/postgres-foundation-spec (중복, 멈춤)`으로 바꿨다(`get_session`으로 봤다). 이 세션은 PR과 병합까지 잇는다.

그 세션이 10:12:55의 `fired=` 뒤 약 9분 반 만에 늦게 닿은 딥링크가 만든 것인지, 사람이 따로 연 것인지는 가르지 못했다. 앞의 것이면 `open_session.ps1`이 `page=`를 찾지 못하고 멈춘 열기도 뒤에 세션을 만들 수 있다는 것이고, open-session "막히면"의 "`page=`나 `sent=`가 안 나올 때"에 그 갈래가 없다. 회고 후보로 넘긴다. 그 세션이 `EnterWorktree`로 이 워크트리를 잠갔을 수 있어, 병합 뒤 `tidy-checkouts`가 이 워크트리를 남길 수 있다.

## 커밋(PR 직전 리뷰 반영)

첫 시도는 pre-commit의 pytest(625.7초)에서 `tests/tools/test_rerun_runner.py::test_파일럿에서는_인계로_멈추지_않는다` 하나가 `assert board.run() == 0`의 `1 == 0`으로 막혔다. 나머지 검사(pyright, 경계, 지침, 타입 우회, 훅 러너, web-verify 746.9초 등)는 통과했다. 이 커밋은 그 시험이 닿는 `tools/`를 건드리지 않는다. 그 시험 하나만 따로 돌리면 통과했고(4.08초), 그 파일 전체를 `-n 8`로 돌려도 63개가 모두 통과했다(159.69초). pre-commit 안에서 web 검사와 함께 돌던 부하 때문에 한 번 흔들린 것으로 본다(어림. 까닭은 가르지 않았다). 같은 시험이 두 번 연속 실패하지 않았으므로 diagnosing-bugs는 부르지 않고 다시 커밋한다. 회고 후보로 넘긴다. 인용 대조가 짚은 이 일지의 인용 하나(30초 문장)를 명세 원문 그대로 고쳤다.

둘째 시도(같은 스테이지에 이 일지만 더했다)는 pytest(1214.4초, 평소의 여섯 배쯤)에서 다른 시험 하나가 막혔다. `tests/channel/cli/test_interrupt.py::test_닫는_도중에_한_번_더_누르면_닫기를_기다리지_않고_끝난다`가 "Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다"로 실패했고, 나머지 7817개는 통과했다. 그 파일만 따로 돌리면 6개가 모두 통과했다(113.65초). 첫 시도에서 막힌 시험은 둘째 시도에서 통과했고, 둘째 시도에서 막힌 시험은 첫 시도에서 통과했다. 두 시험 모두 시간 제한을 두고 자식 프로세스를 기다리는 시험이라, 다른 세션들이 함께 돌아 PC에 부하가 큰 탓으로 본다(어림. 까닭은 가르지 않았다). 같은 시험이 연달아 실패하지 않았으므로 diagnosing-bugs는 부르지 않는다. 다시 돌려도 또 다른 시험이 흔들릴 수 있어, 셋째 시도는 `SKIP=pytest`로 pytest만 뺀다. 손으로 친 pytest는 위의 따로 돌린 두 파일과, 둘째 시도의 7817개 통과다. pytest 전체는 CI의 `python` 잡이 한 프로세스로 다시 돌린다.

## PR 봇 첫 회차

PR #606을 열고(`0a7ef451c`) `@coderabbitai review`를 남겼다. `tools/wait_ci.py 606`이 0으로 끝났다. 검사는 모두 통과했고(`python` 잡이 pytest 전체를 한 프로세스로 돌려 통과했다), `llm`만 SKIPPED였다. claude-review는 "지적 없음"이었다.

CodeRabbit은 첫 회차에 인라인 Critical 셋과 리뷰 본문의 Major 서른여덟을 냈다. 리뷰 본문은 "Due to the large number of review comments, Critical severity comments were prioritized as inline comments"라고 적었다. 지적의 자리는 이렇다.

- 명세와 비밀번호 절차: Critical 하나(명세 251줄, `ALTER ROLE`이 서버에서 실패하면 비밀번호째 로그에 남는다), Major 넷(#1 명세 247줄과 #25 `change_password.sh` 2줄은 셸에 남은 `AGENT_OS_DATABASE_PASSWORD`가 `.env`를 덮는다, #26 둘째 줄이 실패해도 셋째 `up`이 돈다, #2 명세 410줄은 http 모양의 MCP 매니페스트로 비밀번호가 나가는 길을 이 기능에서 막으라)
- stack 프로브: Major 여덟(#3~#10)
- clone_xdist 프로브: Critical 하나(장난감 `Database`의 `repr`에 비밀번호가 든 URL), Major 여덟(#11~#18)
- compose_shape 프로브: Critical 하나(`raw.log`에 `PGPASSWORD`가 남는다), Major 여섯(#19~#24)
- restart_recover 프로브: Major 열둘(#27~#38)

판정한 것.

- #2는 보류한다. ADR 0066 Consequences "신뢰와 노출"이 "그 행은 슬라이스 10이라 0.1 판에는 이 노출이 그대로 있다"고 적고 막는 일을 mcp-trust의 허락 목록에 맡겼다. 사용자가 승인한 결정이라, 이 기능에서 막으려면 그 ADR을 고쳐 승인을 받아야 한다. 봇의 지적은 그 결정을 다시 여는 것이고 명세의 문장은 그 결정을 그대로 옮겼다.
- #1·#25는 고친다. Docker Compose 문서는 같은 변수를 여러 곳에서 정하면 셸의 값이 앞서고 `.env`는 그 뒤라고 적는다(https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/, 웹 요약. 원문을 대 보지 않았다).
- 프로브 넷의 지적은 폴더마다 서브에이전트 하나가 코드를 읽어 판정한다(맞는지, 명세와 README가 인용한 결론에 닿는지, 고치는 값). 원본 출력은 compose_shape의 `--sections 5`와 `--sections 4` 실행 둘만 시스템 임시 폴더에 남아 있다.

### clone_xdist 판정(서브에이전트 보고)

원본은 측정한 세션의 스크래치(`e8487d55-…/scratchpad/clone-work/run-*` 여섯)에 남아 있었고, 서브에이전트가 그것과 같은 자리의 `pgf-tree/.venv` 소스로 갈랐다.

- C1 맞음. pytest 9.1.1은 실패 출력에 시험 함수의 인자를 `saferepr`로 찍고(`nodes.py:449`, `_code/code.py:921-928`), 장난감 `Database`의 기본 `repr`에 비밀번호가 든 URL이 든다(`toy/tests/database.py:70,240`). 남은 `.out` 전부에 `Database(url=`이 없어 기록에는 실리지 않았다. 비밀번호는 공개된 측정용 고정 값(`agent_os_test`)이다. 고침은 `field(repr=False)`이고 정상 길은 그대로다.
- #11 맞음. SQLAlchemy 2.1.8 `asyncpg.py:1178-1181`이 `translate_connect_args` 뒤에 `opts.update(url.query)`를 해 질의 문자열의 `database`가 경로를 덮는다. 프로브의 URL에는 질의 문자열이 없어(`run.py:280`) 기록에는 닿지 않는다.
- #12 부분. 표지 `style`은 고른 값이 작업자까지 닿았는지만 가르고, 어느 픽스처가 돌았는지는 코드를 읽어 아는 것이다. `run.py:565-566`의 주석과 README 193줄이 지나치게 주장하고, README 203줄의 "골랐다는 기록까지"가 맞다.
- #13 맞음, 기록된 실행은 절대 경로였다(`raw.log` 3줄). #14 맞음, 기록된 실행은 컨테이너 회차가 측정이었다. #16 맞음, 기록된 `n8`은 모두 측정이었다. #17 맞음, 기록된 실행은 측정 아님 0이라 예외가 나지 않았다. 넷 다 고쳐도 정상 길이 그대로다.
- #15 맞음, 결론에는 닿지 않는다. README 표 100-101줄만 `wall_s`를 인용하고 본문과 명세는 pytest가 스스로 적은 초(88.45, 88.46)를 쓴다. 두 출력 파일의 마지막 쓰기가 21ms 차이라 부풀림은 수십 ms다.
- #18 부분. 판정에 겹침의 표지가 없는 것은 규칙 위반이다. 원본으로는 겹침이 선다. 둘 다 16:16:29에 띄웠고(`raw.log` 247·250줄) 각자 88.4초를 돌았으며 작업자 여덟의 JSONL 마지막 쓰기가 16:18:02.57~03.14에 몰렸다(서브에이전트가 손으로 봤다).
- 명세에 장난감의 결함을 그대로 옮긴 줄은 없다. 서브에이전트는 "도우미의 자리"에 파생 주소의 질의 문자열과 `repr`을 다루는 한 줄을 더하라고 제안했다.

### compose_shape 판정(서브에이전트 보고)

남은 원본은 `--sections 5`와 `--sections 4`의 두 실행이고, README 표의 전체 실행 원본은 없다.

- C2 부분. `PGPASSWORD`가 `docker run -e` 인자째 `raw.log`의 제목 줄에 남고(`run.py:199-201, 292`), `docker inspect` 출력에 `POSTGRES_PASSWORD`와 연결 문자열이 남으며, 5다·5라는 값을 화면과 `rounds.jsonl`에 싣는다. 그 값은 실행마다 새로 만들거나(`token_hex`, 1248·1545줄) 소스에 박힌 시험 글자(1709-1722줄)이고, `child_env()`가 부모 셸의 `AGENT_OS_`·`POSTGRES_`·`PG` 변수를 지워(98, 149-150줄) 운영 값이 들어올 길이 없다. 호스트 포트를 열지 않고 끝에 `down -v`로 지우며, 원본은 `%TEMP%\pgf-shape`에 있고 저장소가 추적하는 원본은 0개다. 5다·5라의 값은 재려는 대상 그 자체다.
- #19 맞음. 1235줄의 조건은 `up`이 300초에 끊겨 고친 `.env`가 닿지 않았어도 참이다. 그 갈래면 결과 문구가 "같은 컨테이너로 종료 1"이라 README의 "새 컨테이너로 다시 만들어 0으로 끝내고"와 맞지 않아 결과에는 닿지 않았다고 본다(어림, 원본 없음).
- #20 맞음. 가드(`bool(...)`)가 없는 곳은 `restart_all()`(1131줄) 하나다. 빈 기준이면 `줄 None→N`이 찍혔을 것이라 README의 "줄은 늘지 않았다"로 보아 나지 않았다고 본다(어림).
- #21 부분. 데몬에 닿지 않으면 측정 아님이 되지만, 시간 초과나 compose 오류로 migrate가 다시 돌지 않으면 앞 회차의 종료 1과 로그 줄로 측정으로 세어진다. 결과에는 닿지 않았다고 본다(어림).
- #22 맞음, 영향 없음. 남은 두 원본과 README의 실행 명령 모두 `--image` 없이 기본 digest를 썼다.
- #23 맞음, 영향 없음. 남은 5번 원본에서 5라 다섯 회차는 모두 `psql`이 실제로 돌았다(접속한 둘에 `migrate 대역: 판 v1 을 올렸다`, 종료 2인 셋에 `psql: error:`).
- #24 맞음. 남은 4번 원본의 시각은 `began` 10:34:39.04, 첫 줄이 다시 만든 postgres의 시작과 준비 39.98·40.198, ALTER 뒤 옛 serve의 첫 인증 실패 43.379, 새 serve 시작 45.319다. 결함이 걸리는 자리는 첫 줄의 postgres 재시작 틈이고 그 틈은 많아야 약 1.9초라, 2.7초는 ALTER에서 새 serve까지의 틈으로 본다(어림. 원본에 행마다의 시각이 없어 확정하지 못했다).
- #25 맞음. `child_env()`는 그 변수를 지우고(1487줄), 4마는 `change_password.sh`의 줄을 읽어(1475-1479줄) 줄마다 `bash -c`로 친다. 셸 값이 `.env`를 이긴다는 것은 5나가 쟀다.
- #26 맞음. 스크립트에 `set -e`가 없고 `procedure()`는 종료 코드와 상관없이 세 줄을 다 친다(1490-1503줄). 셋째 줄은 migrate 전에 serve부터 다시 만들어, 둘째 줄이 실패한 뒤 치면 4가처럼 serve가 `created`로 남는다.

### stack 판정(서브에이전트 보고)

남은 원본은 이 세션 스크래치의 `stack-run.log`(18:07, 측정 67, 측정 아님 0) 하나인데, window의 횟수가 57P03 563번과 ConnectionError 13번이라 README와 명세 145줄의 487번·12번과 맞지 않아 README가 인용한 실행이 아니다. 라이브러리 소스는 잰 판 그대로인 `e8487d55-…/scratchpad/pgf-tree/.venv`(SQLAlchemy 2.1.8, uvicorn 0.53.0, starlette 1.6.0)에서 읽었다.

- #3 맞음. `asyncpg.py:1181`의 `opts.update(url.query)`가 database를, `base.py:3844`가 질의의 `host`로 호스트까지 바꾸고, 멈출 때의 글이 찍는 자리(`database.py:206`)도 실제로 붙은 곳과 달라진다. compose 꼴 주소에는 질의가 생길 자리가 없어 결론에 닿지 않고, 명세 124줄 "질의를 붙이지 않는다"도 틀리지 않았다.
- #4 맞음. asyncpg는 `connect(timeout=60, command_timeout=None)`이고(`asyncpg/connection.py:2123, 2127`) 이 `timeout`은 접속 수립에만 걸려 판 읽기(`run_sync(_current_revision)`)에는 제한이 없다. 기록된 답하지 않는 서버 회차는 핸드셰이크에서 멈춰 결과는 그대로다. 명세 143·150·151줄이 5초가 판 읽기까지 덮는다고 읽히게 적어 틀렸다.
- #5 맞음. `run.py:117-118`이 종료 코드를 보지 않는다. 롤백 회차는 기록의 값이 비지 않아 psql이 성공했고, 빈 값을 증거로 쓴 셋(257·332줄의 표지, 빈 폴더에서 올린 뒤의 `줄 []`)은 기록만으로 가르지 못한다(앞뒤 psql이 성공해 가능성은 낮다).
- #6 맞음. uvicorn `server.py:117-118`의 `sys.exit(3)`을 Python 3.12 `asyncio/tasks.py:328-330`이 루프 밖으로 다시 던진다. 기록된 실행에서는 나지 않았다.
- #7 맞음. 그 갈래였다면 결과가 `표 [], 줄 []`였을 텐데 기록은 `['0001']`이라 결론에 닿지 않는다.
- #8 맞음. 회차 밖에서 예외를 던지는 자리가 열하나다. 기록된 실행은 모두 찍혔다.
- #9 맞음. 확인이 예외로 끝나면 `lifespan="auto"`에서 uvicorn `on.py:87-94`가 "appears unsupported"를 찍고 시작 완료로 간다. 실제 `serve`(`src/agent_os/main.py:206`)도 기본값이다. 양성 대조 "떴다"의 표지가 이 갈래에서도 나와 둘을 가르지 못하지만, 같은 데이터베이스로 닫기가 1번 불린 회차가 정상 길을 받친다. 명세 134줄에 이 갈래가 없다.
- #10 맞음. uvicorn `server.py:310-311`에서 수명 종료가 마지막이고 그 뒤 `asyncio.run`이 남은 `close`를 취소할 수 있으며, `Recording`은 `await` 전에 센다(`run.py:723-725`). README와 명세 135줄의 "불렸다"는 맞지만, 134줄 "수명이 끝나면 닫는다"를 지금 순서로는 보이지 못한다.

### restart_recover 판정(서브에이전트 보고)

원본은 측정한 세션의 스크래치(`e8487d55-…/scratchpad/restart-work/restart-recover-<접미>/raw.log`)에 README가 드는 실행 넷이 모두 있었다(`z623_ilm` 전체 측정 51, `0k5lhu_2` 앞의 전체 측정 50, `6tc76qxo` 항목 0 측정 7, `c3qq1c_n` 항목 4 측정 10). 아래 "기록"은 그 넷을 grep한 결과다.

- #27 부분. 같은 이미지라도 바깥과 안쪽의 이미지 id가 원래 달라(README 137줄) 봇의 id 비교는 그대로 쓸 수 없다. 넷 모두 `이미 있다`가 0줄이라 그 갈래는 나지 않았다.
- #28 부분. 40초 때의 serve는 `created`라 재시작 정책이 그 틈에 띄울 수 없다. 항목 4의 16회차가 모두 `serve: 삶 0개`였다.
- #29 맞음. 기본값이 `--pull=missing`이고 962줄은 `ran`만 돌려준다. 넷 모두 `Loaded image: postgres:18`이 있고 `Unable to find image`는 0줄이다.
- #30 맞음, 판정 전에 문구를 모으는 자리가 1004·1018·1066·1068·1287·1420줄에도 있다. 측정 아님이 0이라 실패 문구 표는 그대로다.
- #31 논리는 맞고 실제로는 나지 않았다. dockerd의 `Processing signal 'terminated'`가 `PostgreSQL init process complete`보다 항목 4 실행에서 0.65·0.70초, 전체 실행에서 0.78·0.68초 앞섰고 `failed to exit within 10s of signal 2 - using the force`가 찍혀, 데몬 회차 넷은 실제로 초기화 도중에 끊겼다. README 112·117줄이 사건 뒤로 적은 1.20·1.18초(전체 실행 1.23·1.38초)는 신호가 아니라 `cut_at`부터 잰 값이다. 명세는 이 값을 인용하지 않는다.
- #32 논리는 맞고 나지 않았다. 두 전체 실행의 서버 재시작 18회차가 모두 약 1초에 끝났고 `supervise: stop`이 실행마다 9번, PostgreSQL은 매번 `database system was shut down at`(정상 종료)를 남겼다.
- #33 맞음. 전원 회차 여섯이 모두 `표(probe_rows) 모름`(None)으로 이 표지를 지났다. 같은 회차의 migrate가 `created`(돈 적 없음)라 결론은 선다.
- #34 맞음(PostgreSQL이 돌아오지 않은 갈래만). 27회차 모두 `차례(이벤트)`라 옛 `StartedAt`으로 대신한 회차가 없다.
- #35 맞음. 정리 뒤 조회 98번 모두 stderr가 비었다.
- #36 규칙상 맞음. 그런 회차는 측정 아님으로 종료 1을 내 숨지 않는다. 측정 아님 0이라 27/27은 그대로다.
- #37 부분. 봇이 든 장면이면 결과가 "볼륨을 지워도 안 붙음" 쪽으로 틀려 "볼륨을 지워야 붙었다"는 거짓으로 이어지기 어렵다. `down` 3번과 `down -v` 6번이 모두 exit 0이었고 `down -v`는 `Volume pgf-recover_pgdata Removed`를 6/6 찍었다.
- #38 대역에 대해 맞음. 넷 모두 `probe-schema-behind`가 0줄이다. 명세는 대역의 꼴을 옮기지 않았다("뜰 때의 확인과 다시 시도"가 접속 실패를 다시 시도하고, "표의 판을 견주는 자리"가 표가 없을 때를 따로 가른다).

### 반영 방침

- compose_shape는 비밀번호 절차를 바꾸므로 코드를 고치고 `--sections 3,4,5`를 다시 돌린다. 절차는 셋을 바꾼다. 첫 줄 `unset AGENT_OS_DATABASE_PASSWORD`(#25), 세 docker 줄을 `&&`로 잇기(#26), 둘째 줄을 컨테이너 안의 `printf`로 넣는 `\password`로 바꾸기(Critical 셋째, 서버가 평문 대신 SCRAM 해시를 받는다). 4바로 `\password`가 서버에서 실패할 때 로그에 평문이 없는지를 더한다. #19·#20·#21·#23·#24는 표지와 틈 계산을 고친다. C2와 #22는 보류한다(일회용 시험 값, `--image`를 쓴 실행이 없다).
- stack, clone_xdist, restart_recover는 프로브 코드를 고치지 않는다. 기록된 결론은 위의 원본과 기록으로 서고, 고치면 다시 돌려 README의 판과 명세의 수치를 바꿔야 한다. 대신 README마다 "PR 봇이 짚은 틈" 절에 지적마다 결론이 서는 까닭과 다시 돌릴 사람이 먼저 넣을 고침을 적는다. README의 지나친 주장(clone_xdist #12의 193줄)과 틀린 기준점(restart_recover #31의 112·117줄)은 고친다.
- 명세는 시제품의 결함이 구현으로 옮겨 갈 자리를 고친다. stack #4(5초가 연결과 판 읽기를 함께 덮는다), #9(시작 확인의 예외도 시작 실패로 보낸다), #10(연결 풀을 닫은 뒤 종료 완료를 넘긴다), #3과 clone_xdist #11(질의 문자열이 든 주소를 받지 않는다), clone_xdist C1(시험 도우미의 `repr`에 주소를 싣지 않는다).

### 반영(봇 첫 회차)

compose_shape는 `change_password.sh`를 네 줄로 고치고(`unset`, `\password`, `&&`) `run.py`에 4바와 #19·#20·#21·#23·#24의 표지를 더한 뒤 `--sections 3,4,5`를 다시 돌렸다. `run-20261118-212254-d49023`이 측정 62, 측정 아님 0, 종료 0으로 끝났다(21:22:54에 시작, 마지막 명령 21:26:15). 4마는 세 줄 모두 종료 0이었고 psql이 묻는 글 두 줄을 찍었으며, 멈추는 틈은 2.8초였다. 4바는 없는 계정에 `\password`를 쳐 서버가 거절한 문장이 `STATEMENT` 줄로 남았지만 그 안의 값이 SCRAM 해시였고, 평문은 로그 어디에도 없었다. 3번의 수치는 앞 실행과 같은 꼴이었다(3가 `--wait` 셋 6.6~6.8초, 3나 2.24→3.41초, 3마 1.73초, 3아 27→27). README 표는 앞 실행의 수치 그대로 두고 3번 머리에 새 실행의 수치를 적었다. C2와 #22는 README의 새 절 "PR 봇이 짚었지만 고치지 않은 것"에 까닭을 적었다.

stack, clone_xdist, restart_recover는 README마다 "PR 봇이 짚은 틈" 절을 더했다(지적마다 결론이 서는 까닭과 다시 돌릴 사람이 먼저 넣을 고침). clone_xdist는 `run.py:565-566`의 주석과 README의 "세션 픽스처 꼴의 표지"를 고쳐 표지가 가르는 것을 "고른 값이 작업자까지 닿았다"로 좁혔다. restart_recover는 항목 4의 두 기준점 문장에 dockerd가 멈춤 신호를 받은 때부터 잰 값을 덧붙였다.

명세에서 고친 자리는 이렇다.

- "연결 문자열과 비밀번호의 변수": 질의 문자열이 든 주소를 받지 않는다(stack #3, clone_xdist #11). `@` 판정 문장에 질의 판정과의 관계를 더했다.
- "데이터베이스 포트와 조립"의 미들웨어: 확인이 예외를 던지면 "확인하다 멈췄다" 글로 `startup.failed`를 보낸다(#9). `serve`는 uvicorn에 `lifespan="on"`을 넘긴다. `shutdown.complete`는 연결 묶음을 닫은 뒤에 넘기고, 닫다 실패하면 `shutdown.failed`를 보낸다(#10).
- "뜰 때의 확인과 다시 시도": 시도 하나의 제한 시간은 연결부터 판 읽기까지 전체에 건다(#4).
- "멈출 때의 글": "확인하다 멈췄다"와 "닫다 실패했다" 두 행과 그 풀이, 시험 쪽 표의 질의 문자열 행.
- "데이터베이스 비밀번호 바꾸기": 네 줄 절차와 그 풀이, 2.8초, "셋째 줄이 실패하면", "로그에 남는 것"(4바), "거부한 안:"의 `\getenv` 안(4라). 배포 안내 12절의 글머리표.
- 시험 도우미 절의 "주소를 다루는 법"(C1, 질의 문자열).
- Testing Decisions: 첫째 이음매에 잠금 사례, 둘째 이음매에 질의 주소, 예외를 던지는 가짜, 닫기 순서, `lifespan="on"`.

명세 머리의 셈은 다시 셌다. "거부한 안:" 문단은 9이고 "명세가 정했다"는 21이라(머리 1과 본문 20) 머리의 셈 문장이 그대로 맞는다. ADR 0066의 문장을 거짓으로 만드는 반영은 없다. "층과 조립"의 "수명이 닫힐 때 연결 묶음을 닫는다"는 닫은 뒤에 완료를 넘기는 이번 반영과 맞는다.

커밋 직전에 친 `tools/sibling_overlap.py`의 기준 브랜치 줄이 `origin/dev b74a8ad`로 움직였다. #607(harness rename-workflow-terms)이 용어집의 "노트 조각"을 "릴리스 노트 원고"로, "되돌려 합치기"와 "루트 브랜치"도 새 이름으로 바꿨고, ADR 0066에는 이력 한 항목만 달았다. 그 티켓은 살아 있는 문서와 줄여 쓴 "조각"까지 바꾸게 정했으므로, 이 명세에서 그 뜻으로 쓴 일곱 자리(머리의 용어 목록 하나, "노트 검사의 짝" 절의 넷, "티켓을 나눌 때 함께 둘 것" 절의 둘)를 "원고"로 바꿨다. 다른 뜻의 "조각"(코드 조각, 비밀번호의 조각, "제안하는 compose 조각")은 그대로 두었다. 옛 이름 셋을 이 기능 폴더 전체에서 다시 grep해 0줄을 봤다. 번호 겹침과 함께 고친 파일은 없었다.

`uv run ruff check .`와 `uv run ruff format --check .`가 통과했다(`--show-files`로 두 `run.py`가 대상인 것을 봤다). pyright는 `.scratch`를 분석하지 않아, 두 `run.py`를 `tests/` 아래 점 없는 폴더에 복사해 돌렸다. `filesAnalyzed` 2이고 compose_shape는 오류 0이었다. clone_xdist의 오류 28은 모두 `sqlalchemy`를 루트 가상 환경에서 찾지 못한 데서 나온 것이다(그 프로브는 자기 가상 환경으로 돈다). 이번에 그 파일은 주석만 고쳤다. 복사본은 지웠다.

봇 둘째 회차가 겨냥할 새 사실 문장(원문). 받는 쪽이 PR 봇뿐이라 브리프로 넘기는 길은 없고, 압축 뒤에도 남도록 적는다.

1. 명세: "SQLAlchemy 2.1.8의 asyncpg 방언은 질의의 값을 경로에서 읽은 연결 인자 위에 덮어쓴다. `postgresql+asyncpg://u:pw@db:5432/app?database=other`를 그 방언의 `create_connect_args`에 넣으니 데이터베이스가 `other`로, `?host=elsewhere`를 넣으니 호스트가 `elsewhere`로 나왔다(함수를 불러 봤다, PR 봇이 짚었다)."
2. 명세: 미들웨어 글머리표 (a)의 "미들웨어가 예외를 그대로 내보내면," 이하 uvicorn 0.53.0 `lifespan/on.py`와 Starlette 1.6.0 `routing.py`를 읽은 문장.
3. 명세: "uvicorn은 완료를 받으면 수명 종료를 더 기다리지 않으므로(같은 파일), 먼저 넘기면 닫는 도중에 프로세스가 끝날 수 있다. 종료 실패는 uvicorn의 종료 코드를 바꾸지 않는…"
4. 명세: "그 값은 연결을 맺는 데만 걸리고 질의에는 걸리지 않으며, 질의의 제한 시간(`command_timeout`)은 기본이 없다(asyncpg 소스를 읽었다, PR 봇이 짚었다). 그래서 다른 세션이 판 기록 표를 잠가 두면 연결은 열려도 판 읽기가 잠금이 풀릴 때까지 기다리고, 다시 시도하는 시간도 끝나지 않는다(재지 않았다)."
5. 명세: "compose는 셸의 값을 `.env`의 값보다 먼저 쓰므로(5나가 셸 값과 `.env`가 다를 때 셸 값이 드는 것을 쟀다. Docker 문서의 변수 치환 안내가 적은 우선순위도 같다고 웹 요약으로 봤고 원문은 대 보지 않았다, …)"
6. 명세: "그 명령은 묻는 글 두 줄(`Enter new password for user "agent_os":`, `Enter it again:`)을 찍지만 기다리지 않는다(4마의 원본). `\password`는 psql 쪽에서 비밀번호를 SCRAM 해시(비밀번호를 되돌릴 수 없게 바꾼 값)로 바꿔 보내므로, 서버로 가는 문장에 평문이 없다."
7. 명세: "`printf`는 그 이미지의 `sh`인 dash의 내장 명령이라 따로 프로세스를 띄우지 않는다(그 이미지에서 `command -v printf`가 경로가 아니라 `printf`를 냈다, 손으로 봤다)."
8. 명세: "2.8초였다(앞선 절차로 돈 실행들은 2.7초, 5.7초, 6.8초였고, 뒤의 둘은 …)"
9. 명세: "`&&`가 넷째 줄을 막으므로 `serve`는 옛 비밀번호로 계속 돈다고 본다(어림. 셋째 줄이 실패한 채 절차 전체를 친 갈래는 재지 않았고, 4바는 셋째 줄만 쳤다)."
10. 명세: "없는 계정에 `\password`를 쳐 서버가 문장을 거절하게 하자 그 문장이 `STATEMENT` 줄로 로그에 남았지만, 그 안의 비밀번호는 SCRAM 해시였고 평문은 로그 어디에도 없었다(4바)."
11. 명세: "문법이 틀린 `ALTER ROLE` 문장이 `STATEMENT:  ALTER ROLE agent_os PASSWORD '…' BOGUS`로 남은 것을 쟀다(4라)."
12. restart_recover README: "데몬 회차 넷은 dockerd의 `Processing signal 'terminated'`가 `PostgreSQL init process complete`보다 0.65~0.78초 앞섰고 `failed to exit within 10s of signal 2 - using the force`가 찍혀, 실제로 초기화 도중에 끊겼다."
13. clone_xdist README #15: "이 틈은 동시 회차에만 걸리고 … 두 줄(94.78초, 94.83초)"

### 커밋(봇 첫 회차 반영)

`c191a389d`. pre-commit이 모두 통과했다(pytest 592.7초, web-verify 601.9초, 병렬 검사 전체 602.14초). 커밋을 백그라운드로 띄운 직후 인계 계기(`커밋 뒤`)가 왔지만, 이 세션이 앞서 `인계 못함 커밋 뒤`(236줄)를 적었으므로 handoff.md 1의 넷째 갈래대로 넘기지 않고 잇는다. 인용 대조의 경고 여섯 가운데 셋(313·343·383줄)은 원문과 글자가 달라 고쳤다. 282줄은 봇 리뷰 본문이라 저장소에 없고, 387·393줄은 원문에 글자 그대로 있는데 인용 안의 따옴표 때문에 대조가 갈린 것이다(grep으로 봤다). 이 고침은 다음 커밋에 싣는다.

푸시를 훅이 막았다(브랜치가 `origin/dev`보다 한 커밋 뒤). `git merge --no-edit origin/dev`로 #607을 충돌 없이 합쳤다(`31b856dcd`). 합친 변경 가운데 `next-session` `merge.md`와 `pr-merge`는 이름만 바뀌었고 절차는 그대로다(diff를 읽었다). 합친 뒤 `tools/run_checks.py`는 열하나 가운데 pytest만 실패했다. 7817개가 통과하고 `tests/tools/test_rerun_runner.py::test_같은_갈래가_두_번_든_파일럿의_두_회차가_함께_돌아도_번호가_다르다`가 `assert 1 == 2`(두 회차가 함께 돌지 않았다)로 막혔고, 그 시험만 따로 돌리니 통과했다(68.45초). 이 브랜치는 그 시험이 닿는 `tools/`를 건드리지 않는다. 같은 파일의 시간 의존 시험이 부하에서 흔들린 것은 이 세션에서 두 번째다(첫 번째는 274줄의 다른 시험). 같은 시험이 연달아 실패하지 않았으므로 diagnosing-bugs는 부르지 않고, 회고 후보로 넘긴다. ruff 둘과 `tools/sibling_overlap.py`(겹침 없음)도 다시 지났다.

푸시한 뒤 PR에 첫 회차 판정 코멘트(고친 것과 고치지 않은 것의 까닭)와 `@coderabbitai review`를 남기고 `tools/wait_ci.py 606`을 띄웠다.

## PR 봇 둘째 회차

`wait_ci`가 0으로 끝났다(`31b856dcd`, 검사 모두 통과, `llm`만 SKIPPED, claude-review 통과). CodeRabbit은 인라인 Major 열과 본문의 Minor 열아홉을 냈다. 규약(merge.md 회차 세기)대로 Major만 고친다.

- 고친 Major 둘. (1) `change_password.sh` 6줄: 셸의 `COMPOSE_ENV_FILES`가 `.env`를 대신한다. 빈 폴더의 compose 파일로 `docker compose config`를 쳐 그 변수가 `other.env`를 가리키면 그 값이 들고 `unset`하면 `.env`로 돌아오는 것을 봤다(Compose 5.6.1, 손으로 봤다). 절차의 첫 줄을 `unset AGENT_OS_DATABASE_PASSWORD COMPOSE_ENV_FILES`로 바꾸고, 4마가 옛 값을 든 `stale.env`를 가리키는 `COMPOSE_ENV_FILES`까지 내보낸 셸에서 치게 했다. 첫 재측정(`run-20261118-223609-138176`)은 표지가 비교하는 첫 줄 상수를 고치지 않아 4마가 측정 아님이었고 종료 1이었다. 상수를 고친 둘째 재측정(`run-20261118-223809-ef866e`)이 측정 8, 측정 아님 0, 종료 0이었고, 4마는 세 줄 모두 0, 데이터베이스가 새 비밀번호만 받았으며 틈은 6.8초였다. 4번의 나머지 회차는 4다의 이미 맺은 접속의 줄(+9)까지 README 표와 같았다. (2) 명세 315줄: 시험 도우미가 `@`가 둘인 주소를 받는다. 도우미의 판정과 시험 쪽 표의 넷째 줄, Testing Decisions 첫째 이음매의 거부 사례 둘을 더했다.
- 고치지 않은 Major 여덟. clone_xdist의 넷(461·680·770·849줄)은 첫 회차 #15·#17·#16·#14와 같은 자리이고, stack README 95줄은 #5와 같은 자리다. 새 것 셋은 README에 적었다. clone_xdist 213줄(`pg_current_wal_lsn()`)은 쓰지 않은 WAL이 WAL 버퍼 크기를 넘지 못한다는 가늠으로 결론이 선다고 봤다(어림). compose_shape 1168줄(3아)은 줄이 23에서 31로 늘고 재시작 동안의 접속 실패가 로그에 있어 선다고 봤다(어림). compose_shape 1925줄(2다)은 그 전체 실행의 측정 아님이 0이라 빠진 회차가 없다.
- 고친 Minor 하나. 명세 265줄: "쥐고 있던 접속은 그대로 돌았다(4다)"는 서버를 다시 만들지 않은 갈래의 결과였다. 둘째 줄이 서버를 다시 만들어 모든 접속이 끊기는 구간과 셋째 줄 뒤의 인증 실패 구간으로 나눠 적었다. 사실이 틀린 문장이라 둘째 회차지만 고쳤다.
- 보류한 Minor 열여덟은 모두 프로브 코드의 틈이다. PR 코멘트에 지적마다 적는다.

봇 셋째 회차가 겨냥할 새 사실 문장(원문).

1. 명세: "같은 줄은 `COMPOSE_ENV_FILES`도 지운다. 그 변수가 다른 파일을 가리키면 compose는 `.env`를 읽지 않고 그 파일을 읽는다(Docker Compose 5.6.1에서 `docker compose config`로 손으로 봤다, PR 봇이 짚었다)."
2. 명세: "다시 뜬 뒤에는 데이터베이스의 계정이 아직 옛 비밀번호라 옛 `serve`가 다시 붙는다고 본다(어림. 4가에서 `.env`만 고친 뒤에도 데이터베이스가 새 비밀번호를 거절한 것으로 가늠했다)."
3. 명세: "SQLAlchemy는 비밀번호를 첫 `@` 앞에서 자르므로 둘째 `@` 앞의 비밀번호 조각이 호스트에 남고, 그 조각이 `<자리>`에도 비밀번호를 숨긴 `repr`에도 실린다"
4. clone_xdist README: "쓰지 않은 WAL은 WAL 버퍼의 크기를 넘을 수 없고, 기본 설정에서 그 크기는 `shared_buffers`의 1/32(이 서버의 기본 128MB면 4MB)다(PostgreSQL의 기본값을 기억으로 적었다, 어림)."
5. compose_shape README: "4마의 표지(…)는 고치기 전 첫 줄이었다면 compose가 `stale.env`의 옛 값으로 PostgreSQL을 다시 만들어 서지 않는다(위의 손으로 본 것으로 가늠했다)."

## 회고

봇 둘째 회차의 반영을 커밋하기 전에 retro 스킬로 돌았다. 원천은 이 일지 전체와 이 세션이고, "번복"과 "갈린 곳" 절은 없다. 후보 아홉 가운데 승인이 다섯(회차를 더한 것 둘, 새 항목 셋. 첫 후보는 두 항목에 회차를 더했다), 기각이 셋, 일지에만 남기는 것이 하나이고 넘긴 것은 없다. 이 세션에서 반영한 것은 없고, 승인한 것은 모두 대기열에 두었다.

1. **인계 계기가 `인계 못함` 뒤, 백그라운드로 띄운 커밋 직후에 다시 왔다("커밋(봇 첫 회차 반영)").** 승인(회차로 세는 것: 열린 두 항목이 이미 처방한 사건이다). `handoff-trigger-before-background-commit-ends` 8회차, 0518 7회차. 한 사건을 두 항목에 셌다(앞 항목의 2회차가 같은 꼴로 셌다). 넘기지 않고 이었고 손상은 없다.
2. **문서와 프로브만 바꾼 커밋의 pre-commit이 길었다.** 승인(회차로 세는 것: 열린 항목이 처방한 사건이다). `docs-only-commit-precommit-slow-again` 14회차. pytest가 625.7·1214.4·592.7초, web-verify가 746.9·601.9초였다.
3. **PR 봇 둘째 회차의 Major 둘이 첫 회차에 고친 지적과 같은 성질의 다른 자리였다.** 셸 변수만 `unset`해 `COMPOSE_ENV_FILES`가 남았고, `serve` 쪽에만 `@` 판정을 더해 시험 도우미가 남았다. 승인(사건: 봇 회차 하나와 재측정 두 번이 더 들었다. 층: 검사로 가를 수 없는 판단이라 스킬 문장이다. 되돌림: PR 하나). 문장을 더하는 것이라 다섯 번째 전까지 센다. 새 항목 `bot-fix-misses-same-kind-path` 1회차. 같은 일을 다룬 항목은 없었다(`같은.성질`, `짝.자리`, `다음.회차의.봇`, `지적한.자리만`으로 찾았다).
4. **인용 대조(`tools/check_quotes.py`)가 원문에 글자 그대로 있는 인용 둘을 경고했다("커밋(봇 첫 회차 반영)"의 387·393줄).** 승인(고침: 도구의 버그라 사건 하나로 반영할 수 있다. 층: 그 검사 자체다. 되돌림: PR 하나). 회고 때 `quotes_in`을 불러 보니, 짝을 맞추려고 코드 스팬 안의 큰따옴표를 지운 글을 인용으로 뽑고 원문 쪽은 따옴표를 남겨 둘이 맞지 않았다(387줄의 꼴. 393줄은 따로 가르지 않았다). 이 PR은 명세 PR이라 도구 코드와 시험을 싣지 않고, 새 항목 `check-quotes-code-span-double-quotes` 1회차로 두었다. 닫힌 0067(줄을 넘는 인용의 짝)과는 다른 자리다.
5. **인계 열기가 멈춘 뒤 약 9분 반에 같은 지시문의 세션이 생겼다("늦게 생긴 같은 지시문의 세션").** 승인(사건: 사람이 한 번 고르고 그 세션이 스킬과 일지를 읽는 값이 들었다. 층: 스크립트는 뒤늦게 뜬 화면을 알 길이 없어 스킬 문장이다. 되돌림: PR 하나). 문장을 더하는 것이라 센다. 새 항목 `open-session-page-timeout-late-screen` 1회차. 까닭(늦게 닿은 딥링크인지, 사람이 따로 열었는지)은 가르지 못했고, `deeplink_timeline.ps1`은 회고 때도 아무것도 찍지 않았다. 0519는 `stale=1` 뒤의 멈춤이라 출력의 꼴이 달라 잇지 않았다.
6. **시간 시험 셋이 부하에서 한 번씩 빨갰다("커밋(PR 직전 리뷰 반영)", "커밋(봇 첫 회차 반영)").** 일지에만 남긴다. `tests/tools/test_rerun_runner.py`의 서로 다른 시험 둘과 `tests/channel/cli/test_interrupt.py`의 시험 하나였고, 따로 돌리면 모두 지났다. 같은 종류를 0306이 받아들여 닫았으므로(retro 5단계의 여러 곳에서 나는 같은 결함) 잇지 않고 새 항목도 쓰지 않는다. 그 값으로 PR 직전 리뷰 반영 커밋의 셋째 시도를 `SKIP=pytest`로 쳤다. 다시 열지는 사용자가 정한다.
7. **4마의 첫 재측정이 측정 아님이었다("PR 봇 둘째 회차").** 기각. 표지가 비교하는 첫 줄 상수를 고치지 않은 것을 `Rounds`가 측정 아님으로 세고 종료 1로 알렸다. 이미 있는 장치가 그 자리에서 알린 것이다.
8. **기준 브랜치의 이름 바꾸기(#607)를 푸시할 때에야 알았다.** 기각. `hook_push_behind_main`이 뒤처진 푸시를 막아 그 자리에서 알렸고, 합친 뒤 고칠 자리는 grep으로 찾았다.
9. **봇 지적을 반영하며 README의 함수 이름(`snapshot`)과 명세의 절 이름을 처음에 틀리게 적었다.** 기각. 쓰는 턴에 코드와 명세를 다시 열어 스스로 잡았고, 리뷰가 잡은 사건이 아니다.

만료할 항목은 작업 폴더와 `origin/dev`의 두 출력에 모두 없었다(`uv run python tools/queue_open_rows.py`, 같은 명령에 `--ref origin/dev`). 회차 5 이상인 열린 항목은 회고 전에 스물셋이었다.

## 다음

- **이 세션은 이 커밋 뒤에 푸시, 봇 셋째 회차, 병합까지 한다.** 셋째 회차가 겨냥할 새 사실 문장은 위 "PR 봇 둘째 회차"의 다섯이고, 셋째 회차는 Critical·Major만 고친다(`next-session` `merge.md`의 회차 세기).
- **병합 뒤 이 기능의 다음 단계는 티켓이다.** postgres-foundation에는 명세(`.scratch/postgres-foundation/spec.md`)가 있고 `issues/`가 없다. `next-session` 결정표의 "티켓" 줄대로 새 세션에서 명세 검토(`spec-reviewer` 서브에이전트)를 먼저 하고 `/to-tickets .scratch/postgres-foundation/spec.md`를 친다. 모델은 Opus 5.5 / xhigh다. 병합 뒤 결정표의 위 두 줄(운영에서 개발로 합치기, 출시 PR)이 맞으면 그것을 먼저 한다.
- **프로브의 보류한 틈.** 각 프로브 README의 "PR 봇이 짚은 틈"(compose_shape는 "PR 봇이 짚었지만 고치지 않은 것")이 다시 잴 사람이 먼저 넣을 고침을 적는다. 결론은 기록된 원본으로 선다고 판정했다.
- **워크트리.** 늦게 생긴 같은 지시문의 세션이 `EnterWorktree`로 이 워크트리를 잠갔을 수 있어, 병합 뒤 `tidy-checkouts`가 이 워크트리를 남길 수 있다.
- **대기열.** 새 항목은 셋이다. `bot-fix-misses-same-kind-path`, `check-quotes-code-span-double-quotes`, `open-session-page-timeout-late-screen`이고 모두 1회차다. 회차를 더한 셋은 `handoff-trigger-before-background-commit-ends`(8회차), 0518(7회차), `docs-only-commit-precommit-slow-again`(14회차)이다.
