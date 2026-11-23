# 2026-11-23 (23:58) 실제 문서 검색 서버 이미지로 한 번 돌리고, 가짜 서버와 다른 것을 남긴다

세션 제목: `feature/07-real-rag-engine-image-once`. 브랜치 같은 이름, 워크트리 `.claude/worktrees/07-real-rag-engine-image-once`, 기준은 origin/dev. 모델 `claude-sonnet-5-5` / high. next-session 지시문으로 연 새 세션이다.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/base-agent/issues/07-real-rag-engine-image-once.md
>
> 다음 작업: 문서 검색 서버의 실제 이미지를 띄워 05의 실제 모델 사례 열넷을 한 번 돌리고, 가짜 서버와 다른 것을 프로브 기록에 남긴다
> 다음 단계: 구현
> 브랜치: feature/07-real-rag-engine-image-once
> 이번 요청 범위: PR과 병합까지

이 세션 안에서 사용자가 따로 방향을 고른 일은 없다.

## 한 것

- **실제 이미지를 띄웠다.** `njh6803/rag-engine-server:0.1.0-rc.1`과 워커를 rag-engine main `5e80700`의 배포 구성에서 프록시와 리랭커를 뺀 compose(`probes/real_rag_engine/compose.yaml`)로 올렸다. 임베딩 서버는 TEI cpu-1.9.4(bge-m3), 저장소는 pgvector. 다이제스트는 프로브 README에 적었다.
- **문서 넷을 가짜 표본과 같은 글로 만들어 넣었다.** `make_documents.py`(DOCX, PDF 둘, HWPX). 한 창보다 긴 문서는 HWPX 하나(전문 29,516자, 첫 창 19,975자)다.
- **사례 열넷을 한 번 돌렸다.** 둘째 실행에서 열둘이 통과, (13)(14)가 실패했다. 모델이 조각의 글로 복직 절차를 답해 `get_document`를 부르지 않았고, 두 사례의 전제(답이 전문에만 있다)가 실제 서버에서 성립하지 않기 때문이다. 스킬의 잘못이 아니다. 첫 실행은 Docker Desktop이 죽어(물리 메모리 여유 0.6GB) 판정할 수 없었고 버렸다.
- **프로브를 실제 서버로 돌릴 수 있게 했다.** `skill_follow.py`에 환경 변수 `SKILL_FOLLOW_DOC_SEARCH_URL`과 `SKILL_FOLLOW_DOC_SEARCH_AUTHORIZATION`을 더했다. 조각으로 답할 수 없는 사례 "긴 문서의 전문 승인(마지막 조항)"을 더해 3회차 모두 측정이었다. `get_document` 한 번에 `offset` 없음, 승인 카드 한 번, 첫 창에서 멈췄다.
- **토큰 측정.** `result_size.py`. 검색 결과 하나는 가짜 309토큰, 실제 353~355토큰이고, 무관한 질의는 실제 서버가 열 개를 돌려주어 645토큰(결과 열 개 6,447)이다.
- **시험 모듈의 실제 서버 자리.** `tests/test_assistant_llm.py`의 `DocSearch`에 `fake` 칸을 두고 (1)의 갱신일 단언과 (14)의 내용 단언을 가짜 서버일 때만 보게 했다. 독스트링에 (13)(14)가 실제 서버에서 멈춤 단계에서 실패하는 것을 적었다.
- **프로브 README 새 절.** "2026-11-23 결과"에 띄운 것, 넣은 문서, 열네 사례의 결과, 가짜 서버와 다른 것의 표, 고치지 않은 것, 말할 수 없는 것을 근거의 종류와 함께 적었다.
- **기능을 닫았다.** 티켓 01~06이 done이라 같은 커밋에서 `.scratch/base-agent/plan.md`에 `**끝:** 2026-11-23`을 적고 `tools/plan_table.py`를 돌렸다. 기능 단락 `docs/release-notes/features/base-agent.md`도 실었다(기능의 티켓 01과 03의 커밋이 제품 경로를 고쳤다).

## 가짜 서버와 달랐던 것 (줄여서)

항목마다의 근거(프로브가 찍은 것, 조사 스크립트와 `curl`로 손으로 본 것, 실패 출력을 손으로 본 것, rag-engine의 코드를 읽은 것)는 프로브 README의 같은 표 마지막 칸에 적었다. 이 일지는 그것을 줄인 것이다.

- 형식의 판이 `1.1.0`이고 `search`에 입력 인자 `min_score`가 더해졌다(가짜 서버는 `1.0.0`). 리랭커가 있는 지식베이스에만 쓸 수 있다.
- 결과 칸 열세 개와 `get_document` 열네 칸의 이름은 같다. 오류의 모양(`type`·`title`·`status`·`code`·`request_id`)도 같고, 인증은 401, `RAG_ALLOWED_HOSTS`에 없는 `Host`는 421에 본문이 일반 글이다.
- 실제 서버는 문서의 모든 글을 어느 조각에든 넣는다(블록 하나가 조각 하나는 아니다. 법인차량은 문단 192개가 조각 72개다). 가짜 서버가 "전문에만 있다"고 둔 복직 절차(7일)와 해외 출장 일비(60달러)도 조각에 있다.
- 무관한 질의에도 열 개를 돌려주고 점수는 RRF라 0.0143~0.0164다.
- 모델은 조각으로 답할 수 있으면 전문 읽기를 부르지 않는다. 부르면 첫 창만 읽고 멈춘다.

## 고치지 않은 것

- 가짜 서버가 실제 서버의 판 `1.1.0`과 `min_score`를 따라가지 못했다. ADR 0048이 맞추라고 하지만 이번 열네 사례의 판정은 그 둘에 기대지 않았고, 이 PC의 구성에는 리랭커가 없어 흉내 내려면 가짜 서버에 리랭커의 있고 없음을 더해야 한다. 후속 몫이다.
- 스킬은 고치지 않았다. 그래서 05를 다시 치지 않았다.

## 한 번 본 흔들림

`search`가 `SSE stream ended without a response`로 끝난 적이 있다(토큰 측정의 첫 판, 질의 넷 가운데 둘). 같은 시각 14개 사례 실행이 같은 서버를 쓰고 있었고 `embedding_ms`가 16,634였다. 혼자 돌린 둘째 측정에서는 네 질의 모두 성공했다. 부하가 원인인지는 가르지 못했다.

## 환경에서 겪은 것

- 첫 실행 도중 Docker Desktop이 내려갔다(CLI 프로세스가 `MemoryError`, 테스트 데이터베이스 연결 실패). 다시 띄우고 처음부터 돌렸다. 이 PC의 물리 메모리 여유가 TEI(4GB)를 올린 채로 0.6~0.9GB였다. 앞으로 실제 서버를 띄운 채 다른 작업을 겹치지 않는다.
- `.env`라는 이름의 파일을 도구가 쓰지 못해 환경 파일을 `rag.env`로 저장소 밖에 뒀다.
- `result_size.py`가 윈도에서 임시 폴더를 지우다 `PermissionError`를 냈다(가짜 서버의 stderr 파일 잠금). `ignore_cleanup_errors=True`로 고쳤다.

## 검증

- `uv run python tools/run_checks.py`: 통과(종료 코드 0. pytest 442초, web-verify 603초, pyright 51초, lint-imports, check-notes, check-ticket, check-instructions, check-type-escapes, run-hooks, zizmor). 기능 단락과 일지를 쓴 뒤에 돌았다.
- `uv run ruff check .`와 `uv run ruff format --check .`: 통과. `pnpm -C web install --frozen-lockfile`은 돌렸고 `pnpm -C web verify`는 `run_checks.py`의 web-verify 단계가 돌았다.
- 돌리지 않은 것: `-m llm_widget`·`-m llm_portal`(위젯과 서버의 최종 사용자 경로를 건드리지 않았다), 로컬 모델 시험(병합 조건의 범위를 건드리지 않았다), e2e 셋과 사진 비교(웹과 배포 파일을 건드리지 않았다). 열네 사례는 실제 서버로 한 번 돌았다(위).
- 셀프 리뷰 반영 뒤(2026-11-24): `uv run --env-file ../../../.env pytest -m llm tests/test_assistant_llm.py`를 가짜 서버로 쳤고 `14 passed in 235.12s`(토큰 193,335 = 입력 189,450 + 출력 3,885, 모델 호출 35건. 시험이 마지막에 찍은 줄이다). 프로브의 새 사례를 가짜 서버로 한 회차 돌려 측정 1회차, 측정 아님 0회차였다(프로브가 찍었다). `skill_follow.py`의 환경 변수 둘의 검사는 `--only`로 세 갈래(URL만, 토큰만, 서버 모드가 필요한 사례)를 손으로 쳐 모두 이유를 찍고 2로 끝났다. `ruff check`와 `ruff format`은 고친 `.py` 셋에서 통과했다.

## 셀프 리뷰 (2026-11-24, 기준 origin/dev의 merge-base `d144094d9`, 변경 파일 여섯과 미추적 다섯, 커밋 0)

두 축 모두 Critical은 없다. 표준 축(sonnet·high)과 명세 축의 지적을 코드와 문서에 대 보고 판정했다.

- **고친다(Major).** (1) README의 사례 수가 낡았다. 사례는 스물아홉이고 서버 모드가 여섯, 별도 구성이 여덟이다(`skill_follow.py`의 `server=`가 여섯). (2) "문서의 모든 블록이 조각이다"는 거짓이다. 법인차량은 문단 192개가 조각 72개에 든다. 맞는 말은 "문서의 모든 글이 어느 조각에 든다"이다. README 표, 시험 독스트링, 이 일지가 같다. (3) "관련 있는 질의 셋"에 근거 없는 질의("출산 축하금은 얼마야?")가 들었다. (4) PDF 쪽 번호가 문단마다 달랐다(연차 3·5쪽, 출장비 5·6쪽). (5) 다이제스트를 12자리로 잘라 적었다. 전체를 적는다. (6) `survey`는 저장소에 없는 스크립트라 근거 표기를 조사 스크립트의 출력이고 스크립트와 원본은 남기지 않았다는 말로 바꾸고 "말할 수 없는 것"에 적는다. (7) 거부 경로와 빈 전문을 실제 서버에서 재지 않았다는 말을 거부 쪽에도 적는다. (8) 티켓 첫 차림(rag-engine `**끝:**` 확인)의 결과를 적는다. (9) `skill_follow.py`의 환경 변수 검사: URL만 주면 이유 없는 종료, 토큰만 주면 검사 없이 가짜 서버로 가서 401, 가짜 토큰과 같은 값이면 오탐. 둘 중 하나만 주면 이유를 말하고 2로 끝나게 한다. (10) 시험 독스트링의 닫힌 주장("둘 다 실패한다"는 한 회차의 관찰이다), 사례를 고치지 않고 환경 변수 둘만 준다는 문장과 단언 분기의 어긋남. (11) compose 주석의 절 이름(이 티켓 절), 근거 없는 리랭커 문장(기본 설치에서도 켜지 않는다는 말), `rag.env`로 다시 띄우는 법. (12) `make_documents.py` 독스트링(항목 수, 절 이름, 줄 이음, "문장 단위"). (13) `score`가 RRF 점수라는 말의 근거(rag-engine `domain/entities.py` 543행과 `server/tool_models.py` 108행, 코드를 읽은 것)와 "질의가 무엇이든 열 개"의 범위, `min_score` 근거 문장의 한계.
- **남긴다.** 가짜 서버를 `1.1.0`과 `min_score`에 맞추는 일(세션 카드를 내려 했지만 이 저장소의 훅이 모델이 내는 카드를 막아 아래 "다음"에 적는다). `EXTERNAL_URL` 분기가 세 곳이라는 Repeated Switches와 `if doc_search.fake` 두 곳은 프로브·시험의 판단 항목이고 지금 분기를 합치면 더 읽기 어려워 그대로 둔다. 빈 전문과 거부 경로의 실제 서버 측정은 스택을 다시 올려야 하고(이 PC의 메모리 여유가 0.6GB까지 줄었다) 후속 몫이다.
- **다시 돌릴 것.** 가짜 서버로 열네 사례 한 번, 프로브의 새 사례 한 회차, 검증 전체.

## 2026-11-24 세션 (셀프 리뷰 이후. 제목 `feature/07-real-rag-engine-image-once`, 곧 `(인계함)`)

사용자 프롬프트(next-session 지시문. 모델 `claude-sonnet-5-5` / high):

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/base-agent/issues/07-real-rag-engine-image-once.md
>
> 다음 작업: … 문서 검색 서버의 실제 이미지로 사례 열넷을 한 번 돌리고 가짜 서버와 다른 것을 프로브 기록에 남긴 작업을 셀프 리뷰부터 이어 마친다
> 이번 요청 범위: PR과 병합까지

이 세션의 일: 위 "셀프 리뷰" 절의 반영, 가짜 서버로 열네 사례와 프로브의 새 사례 확인, 커밋.

- 결정: 가짜 서버를 `1.1.0`과 `min_score`에 맞추는 후속은 세션 카드를 내려 했으나 이 저장소의 훅이 모델이 내는 카드(`own_initiative`)를 막아 이 일지의 "다음"에 적었다.
- 커밋 `e51ca5056`(브랜치 `feature/07-real-rag-engine-image-once`). 첫 시도는 pre-commit의 `check-notes`가 막았다(기능 단락 `docs/release-notes/features/base-agent.md`가 666자라 400자 제한을 넘었다. 같은 실행에서 pytest 632.8초, web-verify 766.1초, pyright, lint-imports 등은 통과였고 따옴표 대조 경고 4건은 인용 부호를 풀어 없앴다). 단락을 381자로 줄여 다시 커밋했고 pre-commit 전부 통과했다(checks 1121.62초: pytest 828.6초, web-verify 1118.5초, pyright 68.9초와 pyright-linux 73.6초, run-hooks 176.4초, check-notes, check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, 표·줄 구분 문자·변이 표 검사, 커밋 메시지 검사. 카나리아 명세와 헌법 판 검사는 파일이 없어 Skipped. 따옴표 대조 경고 없음). 위 "검증"의 `run_checks` 몫은 이 커밋의 pre-commit 결과로 갈음한다. e2e 셋과 사진 비교는 웹과 배포 파일을 건드리지 않아 돌리지 않았다.
- 이 세션의 컨텍스트가 인계 문턱을 넘은 채 `커밋 뒤` 경계에 와서 넘긴다. 아직 푸시하지 않았다. 남은 일은 origin/dev(이 세션이 본 `7b13a60`. 이 브랜치의 변경과 겹치는 파일은 없었다)와 합치고 `uv run python tools/plan_table.py`를 돌려 `.scratch/plan.md`가 바뀌면 싣는 일, 푸시, PR(`/git-pr`), 봇 회차, 병합이다. 합친 뒤의 검증은 PR의 CI가 본다(합침이 하네스나 `src/`에 닿으면 `run_checks`를 다시 친다).

open-session을 부른다 2026-11-23T16:05Z

## 이전 세션의 인계 (셀프 리뷰 직전. 2026-11-24의 새 세션이 이어 받았다)

컨텍스트가 인계 문턱을 넘은 채 셀프 리뷰 직전에 와서 넘긴다. 이 세션의 제목은 `feature/07-real-rag-engine-image-once (인계함)`로 바꾼다. 커밋하지 않은 변경이 워크트리에 있다. 새 세션은 셀프 리뷰(`/code-review`, 기준 origin/dev)부터 하고, 그 반영, 가짜 서버로 열네 사례 한 번, 커밋, 푸시, PR, 병합 차례다. 실제 서버 스택은 내렸고(compose 프로젝트 `rag-engine-real`, 볼륨 삭제) 더 필요하지 않다. 테스트용 데이터베이스(`agent-os-test-postgres`)는 떠 있다.

open-session을 부른다 2026-11-23T15:10Z

## 다음

- 가짜 서버(`tests/fake_doc_search_server.py`)를 실제 서버의 판 `1.1.0`과 `search`의 `min_score`에 맞춘다(후속 티켓 후보. ADR 0048이 맞추라고 한다. 리랭커가 있고 없음을 가짜 서버에 어떻게 더할지가 정할 일이다. 근거는 프로브 README "2026-11-23 결과"의 "고치지 않은 것").
- 실제 서버에서 거부 경로(사례 (14)의 뜻)와 빈 전문(파싱 전의 문서)을 재지 않았다. 스택을 다시 올려야 하고 이 PC의 물리 메모리 여유(0.6~0.9GB)가 모자라 다른 작업과 겹치지 않게 돌려야 한다.
- 전문 읽기에서 첫 창만 읽고 "찾지 못했다"고 답할 때 사용자에게 문서가 잘려 읽혔다는 말이 가지 않는다. 바꿀지는 정해지지 않았다.
