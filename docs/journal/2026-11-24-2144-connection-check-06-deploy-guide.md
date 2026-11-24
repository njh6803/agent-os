# 2026-11-24 (21:44) connection-check 티켓 06 배포 안내의 문제 해결 절

브랜치 `feature/06-deploy-guide-troubleshooting-section`, 워크트리 `.claude/worktrees/06-deploy-guide-troubleshooting-section`. 모델 Sonnet 5.5(지시문의 high). 앞 일지 `2026-11-24-1652-connection-check-04-plugin-list.md`의 "다음"이 가리킨 티켓 06을 구현한다. 05(관리 화면 e2e 장면)와 나란히 가는 두 번째 티켓이다.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/connection-check/issues/06-deploy-guide-troubleshooting-section.md
>
> 다음 작업: 단독 배포 안내(deploy/standalone/README.md)에 13절 문제 해결을 더한다
> 이번 요청 범위: PR과 병합까지

## 한 일

- `deploy/standalone/README.md`에 `## 13. 문제 해결`을 맨 뒤에 더하고, 4절의 `docker compose logs migrate` 문단 뒤에 13절을 가리키는 한 줄을 더했다. 13절은 먼저 칠 명령과 상태를 읽는 법, 멈출 때의 글 열다섯 줄의 표, 위젯과 관리 화면, 지금 떠 있는 판, 남에게 보내면 안 되는 출력, 접속 확인, 원격 MCP 주소의 소절로 짠다.
- 제품이 멈출 때 찍는 글을 시험이 읽을 자리를 냈다(아래 "시험이 읽을 자리").
- `tests/tools/test_deploy_guide.py`에 13절 시험 열 개를 더했다(30개 통과).

## 시험이 읽을 자리(티켓 검사 칸 셋째)

선택지는 둘이었다. 사적 상수와 메서드 안의 문자열을 시험이 읽게 이름만 공개하는 길, 글을 짓는 순수 함수를 공개하는 길. pyright strict가 시험에서 사적 이름을 가져오는 것을 막아서 앞의 길은 시험이 쓸 수 없다. 함수를 골랐다.

- `src/agent_os/adapters/postgres/database.py`: 글을 짓는 공개 순수 함수 여덟을 `reason_of` 뒤에 낸다. `retry_notice`, `unreached_text`, `misaligned_text`, `unexpected_text`, `close_text`, `upgrade_failed_text`, `upgraded_text`, `already_current_text`. 클래스의 메서드는 이 함수를 불러 같은 글을 낸다. 글은 한 곳에서만 짓는다.
- `src/agent_os/main.py`: `NO_DATABASE_URL_DIAGNOSTIC`과 `UNREADABLE_DATABASE_URL_DIAGNOSTIC`을 공개 상수로 바꿨다(앞의 이름은 밑줄로 시작했다).
- 시험은 제품 글의 고정된 조각을 "빈 자리"(`<자리>`, `<까닭>`, `<판>`, 기본 다시 시도 30초)로 바꿔 안내의 표와 맞댄다. 제품의 글을 바꾼 사본이면 안내의 검사가 빨개지는지도 변이 시험으로 본다.

## ADR 번호(티켓 검사 칸 넷째): 제품의 글에서 뺐다

`serve`가 연결 문자열 없이 1로 끝날 때의 글이 `(ADR 0066)`을 담았고 안내의 말 검사 목록에 `ADR`이 있다. 안내가 옮기는 조각에서만 괄호를 빼는 길은 그 조각이 제품의 글과 달라져 "제품의 글에서 가져온다"는 뜻이 흐려진다. 그래서 제품의 글에서 번호를 뺐다. 운영자는 ADR 번호를 따라갈 수 없고 글 끝의 "README에 있다"가 이미 갈 곳을 알린다.

**제품 변경**: 운영자가 보는 `serve`·`migrate`의 연결 문자열이 없을 때의 글이 바뀐다. 옛 글의 끝 `(ADR 0066)`이 없어졌고 그 밖의 글은 같다. 이 글을 보던 기존 시험(`tests/postgres_support.py`의 `NO_URL`)을 새 글로 고쳤다. 마지막으로 병합하는 티켓이 기능 단락에 이 변경을 싣는다(아래 "기능을 닫는 일").

## 돌려 본 것(티켓 13절 칸 열째, 열한째)

실제 배포 파일 묶음을 풀어 이 PC의 Docker에서 띄웠다(스크래치 폴더에서 프로젝트 이름만 바꿔, 지어낸 값만 든 `.env`로. 진짜 비밀번호나 키는 쓰지 않았다). 아래는 손으로 쳐서 출력을 읽은 것이다.

- `docker compose ps --all`: `migrate`는 `Exited (0)`, 나머지는 `Up ... (healthy)`로 나왔다(4절의 서술과 같다).
- `docker compose exec serve agent-os --version`은 `0.1.0-rc.1`을 찍었다. `.env`의 `AGENT_OS_VERSION`은 다음에 띄울 판이라 다를 수 있다는 서술은 코드를 읽어 적었다.
- `docker compose config`와 `docker inspect <serve 컨테이너>`의 출력에 지어낸 데이터베이스 비밀번호가 그대로 들어 있었다(그 값을 찾는 낱말 세기 도구로 개수만 봤고 값은 찍지 않았다). 그래서 13절이 두 출력을 남에게 보내지 말라고 적는다.
- 멈출 때의 글을 실제 리눅스 컨테이너에서 봤다(티켓 13절 칸 넷째). `serve`에 잘못된 비밀번호를 준 덧씌움 파일로 띄웠더니 `docker compose logs serve`가 이렇게 찍었다(머리 `ERROR:` 뒤가 공백 넷이다).

  ```
  serve-1  | INFO:     Started server process [7]
  serve-1  | INFO:     Waiting for application startup.
  serve-1  | ERROR:    데이터베이스(postgres:5432/agent_os)가 계정이나 비밀번호를 받아들이지 않았습니다(오류 번호 28P01).
  serve-1  |   .env 의 비밀번호만 바꿨다면 데이터베이스 안의 비밀번호도 바꿔야 합니다. 배포 안내의 "데이터베이스 비밀번호 바꾸기"를 보십시오.
  serve-1  | ERROR:    Application startup failed. Exiting.
  ```

  까닭이 `ERROR:` 머리가 붙은 첫 줄이고, 끝의 `Application startup failed. Exiting.`은 웹 서버가 붙인 줄이다. 안내가 그 두 줄의 뜻을 가른다. 글은 같은 모양으로 되풀이됐다(`restart: unless-stopped`가 다시 띄웠다).
- 다시 시작하는 동안의 상태: 한 번의 `ps --all`은 `Up Less than a second (health: starting)`(막 다시 뜬 순간)을 보였고, 반복해 읽는 도중 `Restarting` 줄도 한 번 잡혔다(읽는 반복문이 그 줄에서 멈췄다). 종료 코드 칸 `(3)`이 붙은 `Restarting (3)` 전체 줄은 파일에 남기지 못했다. 안내는 `Restarting`이라는 낱말과 뜻만 적고 괄호의 숫자는 적지 않는다.
- `Created` 상태는 이번 배포에서 만들어 보지 않았다. 안내의 `Created` 서술은 4절의 기존 서술("띄우기가 끊겼을 때")과 같은 뜻을 가리키며, 새로 잰 것이 아니다.
- 처음 `docker compose start serve`로 `serve`를 멈추려 한 것은 실패했다(`start`가 `depends_on`을 따라 `migrate`와 `postgres`를 함께 올려 `serve`가 정상으로 떴다). 그래서 덧씌움 파일로 `serve`만 다시 만드는 길로 바꿨다. 끝낸 뒤 덧씌움 없이 `up -d --wait`로 되돌렸고 모든 서비스가 `healthy`였다.
- 마지막으로 `docker compose down --volumes`로 탐침 배포를 내렸다. `docker ps -a`에 그 프로젝트 컨테이너가 남지 않았다.

## 시험(티켓 검사 칸)

- 13절의 필수 낱말 스물둘(`docker compose ps --all`, `docker compose logs`, `docker compose exec serve agent-os --version`, `AGENT_OS_VERSION`, `docker compose config`, `docker inspect`, `Application startup failed. Exiting.`, `ERROR:`, `접속 확인`, `붙지 못함`과 읽는 예 셋, `20초`, `헤더` 따위. 절 제목 `## 13. 문제 해결`은 이 스물둘 밖에서 `열세째_절`이 따로 본다)을 13절만 잘라 찾는다. 4절에 이미 있는 `Exited (0)`, `Ready`, 위젯의 종료 1 같은 낱말이 13절에서 빠지면 안내 전체에서는 초록이라, 13절만 자르는 시험이 따로 있다.
- 표의 글 열다섯 가운데 하나를 뺀 안내가 빨개지는지, 낱말 하나를 뺀 안내가 빨개지는지, 13절이 없는 안내가 모든 항목을 빠진 것으로 보는지를 시험한다.
- 이 저장소의 안내가 지나는 시험(`test_이_저장소의_13절의_표는_제품이_멈출_때_찍는_글을_빠짐없이_싣는다` 등)과 짝이 되는 빨간 시험 둘을 뒀다.

## 시험을 먼저 쓰지 못한 것

13절 시험을 안내보다 먼저 썼고 빨간 것을 본 뒤 안내를 썼는지는 이 세션의 컨텍스트가 압축된 뒤라 되짚어 확인하지 못했다. 시험이 빨개지는 길은 시험 파일 안의 변이 사례(낱말 하나나 표의 글 한 줄이 빠진 안내, 제품의 글을 바꾼 사본)가 지킨다. 공개 함수로 글을 옮긴 리팩터링은 기존 시험(`tests/postgres_support.py`의 `NO_URL` 한 줄만 고쳤다)이 그대로 초록인 채 끝났다고 이 세션이 앞서 적어 두었으나 그 실행의 출력은 이 일지에 옮기지 못했다.

## 로컬 모델 시험 승인

> 사용자: (선택 화면 "로컬 모델 시험"의 답) "돌린다". 선택지 설명은 "--yes를 붙여 돌립니다. 도구는 타이머가 90분 뒤 파드를 지운다고 알렸습니다(도구의 출력을 읽은 것이고 지우는 것까지 보지는 않았습니다)."

질문은 `uv run --env-file ../../../.env python tools/llm_local.py run`을 `--yes` 없이 쳐서 낸 예상 비용을 그대로 보였다. 가장 싼 후보에서 어림 30분 $0.27, 최악 90분 $0.81, 재고가 없어 다음 후보로 넘어가면 최대 $1.77(A40 파드 둘, 90분). 이 값은 도구가 Runpod 가격 페이지를 웹 요약으로 읽어 2026-11-13에 적은 것이라 원문과 대지 않은 어림이다. 이 답을 받은 뒤에만 `--yes`를 붙였다.

`--yes`로 돌린 결과(도구 출력을 읽었다): 앞 후보 둘(RTX A5000 둘, RTX 3090 둘)은 "재고 없음"(API 400)으로 파드를 못 띄웠고, 셋째(A40 둘)는 한 파드만 만들어지고 다른 하나가 재고 없음으로 실패해 apply가 실패했으며, 넷째(shared, A40 하나)에서 서버가 떠 `uv run pytest -m llm_local`이 4 passed(73.17초)로 끝났다. 기록 묶음의 값은 gpu A40, layout shared, 경과 776.6초, 시간당 $0.59, 가격표 날짜 2026-11-13, 모델 `GotoAI-Inc/gemma-4-26B-A4B-it-W4A16`과 `openai/gpt-oss-20b`, 엔진 vLLM 0.33.0, 토큰 입력 6,191 출력 128(모델 호출 4건, 트레이스 2개), 종료 사유 "시험이 끝났다"다. 회차 파일은 `C:\Users\User\.agent-os\llm-local\feature%2F06-deploy-guide-troubleshooting-section\records\round-0001-20261124T133727Z.json`이다. 시험이 끝난 뒤 `mcp__plugin_runpod_runpod__list-pods`가 빈 목록을 돌려줘 남은 파드가 없음을 봤다(셋째 후보에서 만들어진 파드도 남지 않았다). 비용은 시간당 $0.59에 경과 776.6초를 곱한 어림으로 약 $0.13이다(셋째 후보에서 잠깐 떴던 파드의 몫은 더하지 못했다).

## 검증(손으로 쳐서 출력을 읽었다)

- `uv run python tools/run_checks.py`(백그라운드): check-notes, check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright 둘, run-hooks, pytest(1148.5초), web-verify(1176.1초) 모두 Passed.
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 2551 files already formatted.
- `uv run --env-file ../../../.env pytest -m llm -q`: 24 passed, 8152 deselected(690.78초). 출력의 토큰 줄: "LLM 토큰 합계 262,454(입력 256,957, 출력 5,497). 트레이스 30개, 모델 호출 61건. 트레이스를 남기지 않은 LLM 테스트 2개는 세지 못했다."
- `pnpm -C web/packages/e2e-standalone exec playwright test`(포트 80·443·3000을 비운 뒤): 15 passed(2.4분).
- `uv run python tools/sibling_overlap.py`: 번호 겹침 없음, 함께 고친 파일 없음.

## 셀프 리뷰

범위: base `767a9be59`, 추적 파일 6개의 변경과 미추적 일지 1개, 커밋 없음. 표준 축은 sonnet·high, 명세 축은 세션 모델로 서브에이전트 둘이 돌았다. 둘 다 Critical·Major는 없었고 Minor와 Nit이다(서브에이전트의 보고를 읽었다).

### 고친 것

- 안내의 보편 주장(표준·명세 둘이 냈다): "이 글들에는 … 데이터베이스 드라이버가 낸 글도 들지 않습니다"와 "`serve`와 `migrate`가 멈출 때 찍는 글에는 비밀번호가 없습니다"가 `표를 올리다 실패했습니다` 행의 "뒤에 자세한 기록이 길게 붙는다"와 부딪쳤다(명세 postgres-foundation의 같은 행은 그 역추적에 마이그레이션의 값이 실릴 수 있다고 적는다). 고친 문장: "표의 글에는 계정도 비밀번호도 데이터베이스 드라이버가 낸 글도 들지 않습니다. 다만 맨 아래 `표를 올리다 실패했습니다`의 줄 뒤에 붙는 자세한 기록은 이 표 밖이고, 그 기록에는 마이그레이션이 다루던 값이 실릴 수 있습니다." 남에게 보내면 안 되는 출력 소절의 끝은 "위 표의 글에는 비밀번호가 없습니다. 그래도 기록 전체를 남에게 보내기 전에는 한 번 훑어보십시오."로, `올리다 실패` 행에는 "그 기록은 남에게 보내기 전에 한 번 훑어보십시오"를 더했다.
- "판 번호와 함께 알리십시오"가 데이터베이스 표의 판(`<판>`)과 헷갈릴 수 있었다(명세 축). `확인하다 멈췄다`와 `올리다 실패` 두 행을 "떠 있는 판의 번호(아래 "지금 떠 있는 판")"로 고쳤다.
- "다시 시도하는 알림은 `ERROR:` 머리 없이 찍힙니다"는 컨테이너 기록으로 본 것이 아니었다(명세 축). 이 문장을 "다시 시도하는 알림 한 줄도 그 사이에 찍힐 수 있습니다"로 낮췄다. 실제 컨테이너에서 본 것은 비밀번호가 틀린 때의 다섯 줄뿐이다.
- `docker compose config`와 `docker inspect`가 보이는 값(명세·표준 축): 이 세션이 개수로 잰 것은 지어낸 데이터베이스 비밀번호 하나다. 안내를 "`docker compose config`: 데이터베이스 비밀번호가 그대로 보이고, 쓰는 Compose 판에 따라 관리 토큰, 채널 토큰, API 키도 보일 수 있습니다. 컨테이너에 대한 `docker inspect`: `serve`는 `.env`를 통째로 받으므로(`deploy/standalone/compose.yaml`의 `env_file: .env`를 읽었다) 그 값들이 그대로 보입니다."로 고쳤다. `config`가 `env_file`을 펼치는지는 이 세션이 재지 않았고, `inspect`가 컨테이너 환경 변수를 찍는 것은 Docker의 동작을 아는 것으로 적었으나 토큰이 보이는지는 지어낸 토큰으로 재지 않았다.
- 위젯 종료 1(표준 축): "…것입니다"를 "대개 …것입니다"로 낮췄다(`web/apps/widget/tools/start.ts`가 사이트 파일 밖의 이유로도 1을 낸다는 지적이고, 이 세션은 그 파일을 읽지 않았다. 티켓이 그 서술을 요구했고 "대개"가 그 요구를 해치지 않는다고 판단했다).
- 안내가 4절 표에 없는 `proxy`를 가리키지 못하던 것과 4절이 `docker compose ps`를 쓰는데 "4절처럼 `ps --all`"이라 한 것을 고쳤다("서비스 이름(4절 표의 이름과 `proxy`)", "`ps --all`의 상태로 보십시오(4절에서 상태를 보는 것과 같되, 끝난 컨테이너까지 보입니다)").
- 시험의 구멍(표준 둘, 명세 하나): `없는_글`이 13절 전체에서 줄을 찾아, 예시 기록의 같은 줄이나 다른 행의 같은 줄(`_HALF_BUILT_HINT`)이 빠진 행을 가렸다. 지금은 글마다 첫 줄을 든 표의 행 하나를 찾고 그 행에 나머지 줄이 모두 있는지 본다. 새 시험 둘(`test_표의_행에서만_설명_줄이_빠진_안내를_예시_기록에_같은_줄이_있어도_잡는다`, `test_같은_안내_줄을_쓰는_두_행_가운데_한_행에서만_빠져도_잡는다`)이 그 구멍 둘을 막는다. 직접 돌려 첫 시험은 한 번 빨갰고(제품 글의 둘째 줄이 한 문장 더 길었다) 시험의 줄을 제품 글에서 가져오게 고쳐 초록을 봤다.
- 갈래 목록의 복제(표준·명세): `STOP_TEXT_LABELS`가 스스로와 견준다는 지적에, `Failure`와 `Alignment`의 모든 갈래(맞는 `CURRENT`는 뺀다)가 제품의 글 목록에 든 것을 보는 시험(`test_제품의_접속_실패와_표_견줌의_갈래마다_표의_글이_하나씩_있다`)을 더했다. 제품에 갈래가 늘면 빨개진다.
- `misaligned_text(Alignment.CURRENT, …)`가 조용히 "더 새롭다" 글을 내던 것(표준 Nit): 공개 함수가 되었으니 `BEHIND`·`AHEAD`만 받고 `CURRENT`는 `ValueError`로 하게 고쳤고 시험(`test_맞는_표에는_맞지_않는_글이_없다`)을 더했다. 호출처 둘(`startup_problem`, `migrate`)은 `CURRENT`를 먼저 걸러 이 길을 지나지 않는다(코드를 읽었다).
- 이 일지의 필수 낱말 서술: 절 제목이 스물둘에 든 것처럼 읽히던 것(표준 축)을 위처럼 고쳤다.
- 고친 뒤 `uv run pytest tests/tools/test_deploy_guide.py -q`는 34 passed, `uv run pytest tests/adapters tests/test_main.py -q -k "postgres or database or main"`은 345 passed(329.71초), `uv run ruff check .`은 All checks passed(손으로 쳐서 출력을 읽었다).

### 남긴 것

- 표준 Nit `Middle Man`(`_describe`와 `_misaligned_text`가 모듈 함수 한 줄을 부르기만 한다)과 `Data Clumps`(`(place, reason)`): 호출처가 하나이거나 크기가 작고, 함수를 클래스 밖으로 내는 것이 이 티켓의 목적이라 그대로 둔다.
- 명세 축의 `.scratch/postgres-foundation/spec.md:176`에 남은 `(ADR 0066)`: 끝난 기능의 명세로 기록이라 잔존으로 세지 않는다(`docs/constitution/operations.md` 문서 위치). 고치지 않는다.
- `serve`가 3으로 끝나는 것은 명세 축이 코드 주석으로만 봤다고 했다. 이 세션은 실제 컨테이너에서 `serve`가 되풀이해 다시 시작하는 것을 보았으나(위 "돌려 본 것") 종료 코드 칸 `(3)`이 붙은 줄은 파일에 남기지 못했다. 안내가 `Restarting`의 괄호 숫자를 적지 않으므로 그대로 둔다.

### 커밋의 pre-commit 첫 시도가 막은 것

첫 커밋 시도에서 `check-mutations`가 빨개 막혔다(커밋 로그를 읽었다). 제품의 글을 함수로 옮기며 변이 표 `.scratch/postgres-foundation/probes/database_tests_mutations.toml`의 변이 둘("뜻밖의 오류 글에 예외의 글을 싣는다", "그 밖 글의 끝을 바꾼다")이 가리키던 원문이 `database.py`에서 0번 나왔다. 옛 글의 위치를 가리키는 다른 표를 함께 고치는 일이 이 세션의 계획에 없었다. 표의 `old`·`new`를 새 위치(`return unexpected_text(self._place, reason_of(error))`와 `Failure.OTHER` 갈래의 `return f"데이터베이스({place})에 접속하지 못했습니다({reason})."`)로 고쳤다. `uv run python tools/mutate.py --staged`가 "문제 0"으로 끝났고, 두 변이를 `uv run python tools/mutate.py <표> 8 22`로 돌려 둘 다 기대대로 빨개지는 것을 봤다(기준선 12 passed·43 passed, 변이 8은 `tests/test_migrate_command.py`에서 1 failed, 변이 22는 `tests/adapters/test_postgres_database.py`에서 1 failed). 같은 `database.py`를 가리키는 다른 표의 변이 32개는 `--staged`가 원문이 한 번씩 있는 것으로 확인했다. 이 일은 "제품의 글 위치를 옮기면 그 글을 가리키는 변이 표를 함께 본다"는 점검이 계획에서 빠진 것이고, 훅이 커밋에서 잡았다.

### 다시 돌린 명령

- 안내 시험, 어댑터 시험, ruff는 위 대로. 나머지(pyright, 경계, web 등)는 커밋의 pre-commit이 돈다.
- PR 직전 리뷰에 밀 주장(이 세션이 반영하며 새로 쓴 사실 문장): 안내 13절의 "표의 글에는 계정도 비밀번호도 데이터베이스 드라이버가 낸 글도 들지 않습니다. 다만 맨 아래 `표를 올리다 실패했습니다`의 줄 뒤에 붙는 자세한 기록은 이 표 밖이고, 그 기록에는 마이그레이션이 다루던 값이 실릴 수 있습니다", "`serve`는 `.env`를 통째로 받으므로 그 값들이 그대로 보입니다", "다시 시도하는 알림 한 줄도 그 사이에 찍힐 수 있습니다", "대개 사이트 파일이 없거나 깨졌거나 읽히지 않는 것입니다", `misaligned_text`가 `CURRENT`에 `ValueError`를 던진다는 독스트링.

## 인계 1(커밋 뒤에 넘긴다)

제목이 `feature/06-deploy-guide-troubleshooting-section`이었던 세션이 넘긴다(넘기며 `(인계함)`을 붙인다). 이 세션은 구현, 검증, 셀프 리뷰(서브에이전트 둘), 회고(위 `## 회고`)를 마치고 커밋 `5a027b51f`(`git log`로 읽었다)를 이 브랜치에 만들었다. 푸시하지 않았고 PR도 없다. 이 "인계" 절은 커밋하지 않았다. 새 세션이 다음 커밋(봇 회차의 반영 커밋이나 일지만 실은 커밋)에 싣는다.

- 커밋의 pre-commit은 첫 시도에서 `check-mutations`가 막았고(위 "커밋의 pre-commit 첫 시도가 막은 것"), 변이 표를 고친 두 번째 시도에서 모두 통과했다(커밋 로그를 읽었다).
- 남은 일: 푸시, PR 직전 리뷰(`coderabbit-review`, CLI가 못 돌면 `bug-perf-review`), PR 열기(`git-pr` 스킬, 본문 끝에 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`), `mcp__ccd_pr__get_status`와 `bind_pr`, 첫 `@coderabbitai review` 코멘트, 봇 회차, 병합. 순서와 방법은 워크트리 사본의 `next-session` `merge.md`("병합 전" 2, "워크트리에서 병합할 때").
- PR 직전 리뷰에 밀 주장은 위 "셀프 리뷰"의 "다시 돌린 명령" 끝에 나열했다.
- 병합 직전에 `git fetch origin` 뒤 기준 브랜치를 합치고, 이 기능의 다른 티켓 `Status:`를 다시 본다. 05의 PR(#634)이 이미 열려 있다. 05가 먼저 병합돼 `done`이면 이 PR이 마지막이라 티켓 06의 "기능을 닫는 일"대로 `**끝:**` 줄, 기능 단락(`docs/release-notes/features/connection-check.md`, 이 티켓의 제품 변경인 `serve`·`migrate`의 연결 문자열 없음 글에서 `(ADR 0066)`이 빠진 것을 담는다), `uv run python tools/plan_table.py`의 결과를 싣는다. 그렇지 않으면 싣지 않고, 병합 뒤 다시 `git fetch origin`으로 05가 그 사이 병합됐는지 본다.
- 이 PR은 `.py`(어댑터와 `main.py`)를 건드렸으므로 `-m llm`과 로컬 모델 시험을 이 세션이 이미 돌렸다(위 "로컬 모델 시험 승인"과 "검증"). 병합 전에 합친 기준 브랜치가 그 범위를 바꾸지 않았다면 다시 돌리지 않는다.

## 인계 받은 세션의 PR 직전 리뷰

인계로 이 일을 넘겨받은 새 세션이 `coderabbit-review` 서브에이전트를 `--base origin/dev`로 돌렸다(보고를 읽었다). CodeRabbit CLI 0.7.5가 끝까지 돌았고(`Seat: not assigned`, `Plan: Free`에서도 리뷰가 끝났다) 지적은 0건이었다. 서브에이전트가 직접 읽어 Critical·Major·Minor 없음, Nit 하나를 냈다.

- Nit: `tests/tools/test_deploy_guide.py`가 `agent_os.main`을 import해 시험을 모으는 단계에서 uvicorn과 LangGraph가 따라 올라온다. 시험이 느려지는 장면은 만들지 못했다고 보고했다. 진단 상수 둘을 `http`나 `adapters`로 옮기는 길은 제품 글의 자리를 또 옮기는 일이라 이 PR에서 하지 않는다. 고치지 않는다.
- 서브에이전트가 옛 이름(`_NO_DATABASE_URL_DIAGNOSTIC` 따위)의 잔존을 grep하지 못했다(훅이 전체 grep을 막았다). 이 세션이 Grep 도구로 `src`와 `tests`를 따로 훑었고 두 옛 이름 모두 0건이었다(손으로 쳐서 출력을 읽었다).

open-session을 부른다 2026-11-24T14:47:39Z

## 회고

이 세션이 단계를 닫으며 돌렸다. 후보 일곱, 판정은 승인 0, 기각 일곱, 넘김 0이다. 만료할 항목은 없었다(`uv run python tools/queue_open_rows.py`와 `--ref origin/dev`의 두 출력 모두 "만료할 항목: (없음)"). 대기열에 항목을 더하거나 회차를 더하지 않았고 새 훅·검사·지침 문장도 더하지 않았다.

- 후보 1, `.env`를 읽으려는 Grep과 Bash가 훅에 막혔다: 기각(이미 있는 훅이 그 자리에서 막았다). 값이 밖으로 나가지 않았고 개수만 세는 스크립트로 돌아갔다.
- 후보 2, 측정이 아닌 스크래치 스크립트를 편집하려다 `.claude/rules/probes.md`를 읽으라는 훅에 두 번 막혔다: 기각(훅이 의도대로 막았고 한 번 읽은 뒤 셋째 호출이 지나갔다. 비용은 호출 두 번이다).
- 후보 3, 파이썬 `Path.write_text`가 `database.py`를 CRLF로 바꿨다: 기각(`hook_line_separators`와 `git ls-files --eol` 대조가 이미 있고, 이 세션이 그 길로 잡아 LF로 되돌렸다).
- 후보 4, 셀프 리뷰 두 축이 안내의 보편 주장(표 밖의 역추적에는 값이 실릴 수 있다는 것과 어긋난 "비밀번호가 없다" 문장)과 재지 않은 일반화(`docker inspect`가 모든 토큰을 보인다)를 잡았다: 기각(리뷰가 제 몫을 한 것이다. `code-review`의 두 브리프가 이미 닫힌 주장과 근거의 종류를 밀도록 적고 있어 4단계의 회차 셈에서 뺀다).
- 후보 5, `docker compose start serve`가 `depends_on`을 따라 `migrate`와 `postgres`를 함께 올려 `serve`를 일부러 멈추려던 첫 실험이 헛돌았다: 기각(이 세션이 실험을 짠 실수이고 하네스 환경의 결함이 아니다. 사실은 이 일지의 "돌려 본 것"에 적었다).
- 후보 6, 컨텍스트가 압축된 뒤라 13절 시험을 안내보다 먼저 썼는지의 순서를 되짚지 못했다: 기각(일지의 한 문장 비용이고, 근거의 종류를 밝히라는 일지 훅의 알림이 그 자리에서 이미 그 문장을 낮추게 했다).

- 후보 7, 제품의 글을 함수로 옮기자 그 글을 가리키던 변이 표가 깨졌다: 기각(`check-mutations`가 커밋의 pre-commit에서 이미 잡아 막았다. 위 "커밋의 pre-commit 첫 시도가 막은 것").

## 다음

- 이 PR이 병합되면 연결 확인 기능에 05(관리 화면 e2e 장면)가 남는다. 05의 PR #634가 이미 열려 있다(`tools/sibling_overlap.py`의 형제 줄을 읽었다). 이 PR이 병합될 때 05가 `done`이고 05의 PR이 이미 병합됐으면 이 PR이 마지막이라 `**끝:**` 줄과 기능 단락(`docs/release-notes/features/connection-check.md`)과 `uv run python tools/plan_table.py`의 결과를 싣는다. 그 기능 단락은 이 티켓이 바꾼 제품 변경(`serve`와 `migrate`가 연결 문자열 없이 끝날 때의 글에서 `(ADR 0066)`이 빠진 것)도 담아야 한다. 05가 아직 열려 있으면 05의 PR이 마지막이라 그 일을 맡는다.
- 병합 뒤에는 `git fetch origin`으로 05가 그 사이 병합됐는지 다시 보고, 둘이 같은 때 서로 마지막이 아니라고 보고 병합했다면 끝 줄과 기능 단락을 싣는 고침 PR을 낸다(`gh pr list`로 같은 PR이 이미 있는지 먼저 본다).
- 13절의 `Restarting` 줄 전체(`Restarting (3)` 꼴)와 `Created` 상태는 이 세션이 파일에 남기지 못했거나 만들어 보지 못했다. 안내는 그 낱말과 뜻만 적었다. 다음에 단독 배포 안내를 만지는 티켓이 두 상태를 직접 만들어 본다.
