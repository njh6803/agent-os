# 2026-09-28 (03) 대기열 27·29 — 바이트 보존 변이 도구, 설계 라운드 UI, 프로브의 자리

02 세션이 연 새 세션이다. 주 체크아웃에서 했고 브랜치는 `chore/mutation-tool-and-grill-rounds`, PR #89(squash
`25ff0e3`)다. web-admin 설계 인터뷰 전에 하기로 한 chore의 1순위 둘을 닫았다. 산출물은 넷이다.

- `tools/mutate.py`와 `tests/tools/test_mutate.py`, 그리고 그것을 가리키는 `implement` 스킬과 PR 템플릿의 하네스 줄
- `grilling` 사본(라운드를 `AskUserQuestion`으로)과 `check_instructions.py`의 `PATCHED_SKILLS`
- 프로브 규약(`docs/agents/issue-tracker.md`, `CLAUDE.md`의 트래커 줄, `spec-reviewer`)과 옛 프로브를 옮긴
  `.scratch/{http-channel,plugin-toggle,admin-api,first-slice,interrupts,harness}/probes/`
- 대기열 27·29에 취소선, 20·37에 근거, 40·41 새 줄(회고), 이 일지

> 사용자: ".scratch/retro-queue.md 의 27과 29를 chore 브랜치 하나로 반영한다. 먼저 일지 2026-09-28-02의 "다음"을 읽는다
> … 읽을 것: 일지 2026-09-28-02의 "다음", .scratch/retro-queue.md 의 27·29(같은 자리를 건드리는 37·39도 함께 볼지는
> 그 절이 적었다) … 이번 요청 범위: 구현·리뷰·커밋까지. PR과 병합은 사용자가 말할 때"
> 사용자: (범위) "27·29만, 37·39는 따로 (Recommended)"
> 사용자: (도구 포인터) "implement 스킬 + PR 템플릿 (Recommended)"
> 사용자: (프로브 규약) "트래커 문서 + 포인터 + 검토자 (Recommended)"
> 사용자: (옛 프로브) "근거로 드는 것만 옮긴다 (Recommended)"
> 사용자: (하네스 자리) ".scratch/harness/probes/ (Recommended)"
> 사용자: "PR·병합"

## 정한 것

1. **변이 도구의 모양.** TOML 변이 파일(파일·원문·치환·대상 테스트·기대·반복)을 받는다. 원문이 파일에 정확히 한
   번인지 먼저 모두 보고, 대상 테스트의 기준선이 초록일 때만 변이를 넣고, `finally`에서 바이트 그대로 되돌린다.
   pytest 종료 코드 0은 초록, 1은 빨강, 나머지(수집 오류, 없는 경로, 선택된 테스트 없음)와 skip이 섞인 초록은
   오류이고 오류는 기대가 무엇이든 어긋남이다. 도구의 종료 코드는 0(기대대로), 1(어긋남이나 기준선 빨강),
   2(변이 파일 오류, 아무것도 쓰지 않음), 3(테스트를 못 돌렸거나 되돌리지 못함). 하위 pytest는
   `PYTHONDONTWRITEBYTECODE=1`과 `-p no:cacheprovider`로 돌고, 변이를 쓴 직후와 되돌린 직후에 그 소스의
   바이트코드 캐시를 지운다. TOML은 리터럴 여러 줄 문자열이 코드 조각을 이스케이프 없이 담고 `tomllib`가 표준이라
   골랐다. 검증은 이미 런타임 의존성인 pydantic에 맡겨 원칙 III을 지키며 strict를 지난다.
2. **프로브 규약.** 명세·ADR·코드 주석이 근거로 드는 프로브는 `.scratch/<slug>/probes/`(하네스는 `harness`)에
   커밋하고 `README.md` 표에 프로브마다 한 줄을 둔다. 근거를 드는 자리는 파일 이름으로 가리킨다. 옛 근거는 날짜나
   "명세 검토의 프로브"로 가리키므로 옛 문서의 문장은 두고 README가 그 말을 파일로 잇는다.
3. **옛 프로브는 근거로 쓰인 것만 옮겼다.** 바꾼 것은 ruff를 지나는 형식, 부수 효과 import 둘의 `noqa`, 원칙 III에
   걸리는 `type: ignore` 하나를 실제 타입(`tuple[RunRow, ...]`)으로, `reveal_type` import 하나, 그리고 리뷰 뒤
   `bisect_fastapi.py`의 `ROOT`와 `probe_send.ps1`의 출력이다. interrupts의 langgraph 프로브는 스크래치패드에서
   사라져 그 세션 서브에이전트 트랜스크립트의 마지막 Write(뒤에 Edit 없음)로 되살렸다. ADR 0001이 "같은 프로브로
   재는 것이 첫 일"이라 예약한 프로브라 2026-09-21의 pyright 출력 둘도 기준값으로 함께 옮겼다.
4. **grilling의 라운드.** 질문마다 추천할 답을 먼저 고르고 그 선택지를 첫 자리로 옮겨 "(Recommended)"를 붙인다.
   frontier가 넷을 넘으면 같은 라운드를 호출 여럿으로 잇는다. 질문 문장은 호출 안에만 둔다.

## TDD와 변이

- 도구는 조각마다 테스트를 먼저 썼다. 빨강의 이유는 매번 하나였다(모듈 없음, 판정 없음, 이름 겹침 검사 없음 등).
  구현 전부터 초록인 가드(원문 횟수, 여러 편집, 명세 모양)는 도구 자신으로 쟀다.
- 첫 자기 적용(변이 열하나)에서 하나가 어긋났다. 오타 키 테스트가 `expect`를 `expected`로 바꿔 필수 키 누락으로도
  빨개져 `extra="forbid"`를 따로 재지 못했다. 필수 키를 두고 오타 키를 더하는 모양으로 고쳤다. 리뷰 반영 뒤 열일곱,
  CodeRabbit 반영 뒤 캐시 셋을 돌렸다. 캐시 셋의 첫 판에서 "되돌린 뒤 지우기"가 살아남았다 — 변이를 쓸 때 이미
  지워서 되돌릴 때의 삭제를 아무것도 재지 않았다. 러너가 변이 동안 캐시를 남기게 고쳐 빨강을 봤다.
- 제품 코드에서는 티켓 02의 "꺼짐을 깨짐 앞에" 변이가 일지 02대로 3 failed였고, 빈 줄 변이는 초록, 문법 오류
  변이는 빨강이 아니라 오류로 가려졌다. 매번 `git hash-object`가 같았고 새 `.pyc`가 생기지 않았다.

## 실제 실행으로 확인한 하네스

- **grilling**: 서브에이전트 드라이런 둘. 첫 판(frontier 넷)은 본문이 "스트리밍은 빼는 편"을 근거로 들면서
  "포함 (Recommended)"을 달았다 — 첫 선택지에 기계적으로 붙인 것으로 읽혀 "먼저 고르고 첫 자리로 옮긴다"로
  고쳤다. 둘째 판(frontier 여섯)은 호출 둘(넷, 둘)로 나뉘었고 여섯 모두 본문의 근거와 추천이 같았다. 질문 문장은
  두 판 모두 본문에 없었다. 둘째 판이 짚은 "질문은 호출에 한 번만 있다"의 두 번째 읽기(호출마다 질문 하나)도 고쳤다.
- **spec-reviewer**: plugin-toggle 명세의 느슨한 불린 주장 하나만 재게 불렀다. 저장소 밖에 프로브 파일을 쓰고
  근거에 경로를 적었다(ruff도 지나는 스크립트였다).
- **옮긴 프로브**: 스크립트가 그대로 돈다고 README에 적은 것은 돌려서 봤다. 대부분 문서가 적은 값을 다시 냈고
  (`CancelledError`, 204와 `name=calc`, winerror 5, `http.cookies` 가림, 커서가 놓치는 두 길, pyright가 await 누락을
  못 잡음), `probe_torn.py`는 ADR 0012의 다음 이력이 셋째 길을 닫아 결과가 바뀌었다고 README에 적었다.

## 셀프 리뷰

`/code-review main`을 두 축 병렬로 돌렸다. 범위는 base `0e577da`, 추적 파일 9, 미추적 25, 커밋 0이었다.

- **표준 축**: Major 1 — `main`이 `OSError`를 `measure` 전체에 걸어, 되돌리는 쓰기가 실패하면 "명세 오류"와 2를
  내고 파일은 변이된 채 남았다(실측). `RestoreError`와 종료 코드 3으로 갈랐다. Minor(UTF-8이 아닌 변이 파일이
  트레이스백의 1, 전부 skip된 실행이 초록, 종료 코드·매핑·파싱 테스트 없음, CLAUDE.md 포인터가 원천보다 좁음,
  README "파일마다 한 줄")와 판단(`Run`이 도메인 용어 "실행"과 겹침 → `PytestResult`, implement의 "명세"가
  leading word와 겹침 → "변이 파일", 결과를 버리는 검증 루프 → `_validate`)을 반영했다. 밀 주장은 1e·1h만 틀렸다.
- **명세 축**: Minor 3 — 조사를 "프로브" 낱말로만 걸러 ADR 0012·0007의 "쟀다·실측" 근거를 놓침, CLAUDE.md 포인터,
  spec-reviewer에 Write가 없어 40줄 heredoc 상한에 걸림. Nit 3(대기열 10의 옛 템플릿 인용, "명세", 테스트 주석의
  근거 자리가 README에 없음). 첫째는 짝을 보지 않은 스크래치패드 열한 곳을 다시 훑어 admin-api·first-slice·interrupts·harness를
  더 옮겼다. "주장만" 적힌 자리가 받치는 스크립트와 불확실 하나(`d56cf2da/probe.py`)는 두었다.

## PR 리뷰

PR #89. CodeRabbit CLI는 `Plan: Free`, `Seat: not assigned`(이 PR에서 확인)라 PR 직전 축을 돌리지 않았다.

- **claude-review**: `ddff8c2`에 지적 없음. `37994cd`에 지적 없음과 Nit 하나 — `test_main_은_변이_파일을_읽지_못하면_…`이
  인자 없음(`argv=[]`)까지 묶어 이름이 그 분기를 말하지 않는다. 맞는 지적이지만 선택 사항이라 새 푸시를 만들지
  않았다(보류, 다음에 그 파일을 고칠 때).
- **CodeRabbit**: 인라인 셋(모두 Minor)과 nitpick 하나(Trivial, 보안 분류 CWE-532). 반영 — 바이트코드 캐시 삭제,
  `bisect_fastapi.py`의 `ROOT`, `probe_send.ps1`은 입력창 값의 길이만. `probe_tree.ps1`은 화면의 글이 측정 대상이라
  두고 README에 출력을 옮길 때의 주의를 적었다. 보류 — `probe_uvicorn_shutdown.py`의 SSE 버퍼링(ADR 0014 이력의
  수치를 낸 스크립트를 그대로 둔다). CodeRabbit이 철회했다. 반영 뒤 재리뷰는 시간당 한도에 걸렸고, 스레드 답글이
  `37994cd`를 직접 읽고(스크립트까지 돌려) 두 수정을 확인했다. PR #80과 같은 판단으로 기다리지 않고 병합했다(대기열 41).
- squash `25ff0e3`, 원격 브랜치는 `--delete-branch`가 지웠다. 주 체크아웃이라 main 최신화가 그대로 됐다.

## 갈린 곳

- **옛 문서의 근거 문장은 바꾸지 않았다.** ADR·명세·티켓·코드 주석 스무 곳 가까이가 날짜로 프로브를 가리킨다.
  고치면 ADR 문장을 건드리게 되어 README가 거꾸로 잇게 했다. plugin-toggle 명세의 "커밋하지 않았다"만 거짓이 되어
  날짜 괄호를 더했다.
- **옛 프로브의 내용은 측정 기록으로 둔다.** 리뷰가 두 번 로직 수정을 제안했다(SSE 버퍼링, 캐시). 도구의 캐시는
  고쳤고 프로브의 로직은 두었다. 기준은 "그 파일이 근거를 낸 스크립트인가"다.
- **하네스 프로브의 자리**는 규약이 기능 slug만 다뤄 사용자에게 물었다(`harness`).

## 번복하거나 고친 것

- grilling 센티널 주석의 "세션마다 같은 라운드를 두 번"은 보편 주장이라 일지 셋으로 밀어 보니 거짓이었다(두 번 올린
  것은 2026-09-26-06뿐). README의 "넷"(윈도 의미 프로브는 다섯)과 "바꾼 것은 형식뿐"(`noqa`, `ROOT`)도 같은 가족이라
  고쳤다. 대기열 20의 모양 그대로다.
- 도구 독스트링의 예시가 이름("꺼짐을 깨짐 앞에")과 다른 변이였다. 실제로 돌린 변이로 바꾸고 파싱과 원문 일치를 쟀다.
- `lint-imports`를 `PYTHONUTF8=1` 없이 `/dev/null`로 돌려 rich가 cp949로 죽은 가짜 1을 봤다(대기열 40).
- `cd`로 프로브 폴더에 들어간 명령이 세션의 작업 디렉터리를 바꿨다. 일지 02에 이어 2회차라 일지에만 둔다.
- heredoc 훅이 91줄과 49줄 heredoc을 막았다. 둘 다 Write로 파일을 쓰고 경로를 넘겼다. 훅이 제 일을 했다.
- grilling 사본의 작업 파일이 CRLF였다. 9월 19일 checkout 때 `core.autocrlf`로 그렇게 된 것이고 Edit은 파일의 줄 끝을
  따랐다. `.gitattributes`의 `eol=lf`가 커밋에서 LF로 되돌렸다(커밋된 blob의 CR 0).
- ADR 0014의 2026-09-26 이력이 fastapi 하한을 "이분 탐색"했다고 적었지만 `bisect_fastapi.py`는 차례로 훑는다. README는
  스크립트대로 적었고 ADR 문구는 두었다.

## 회고

후보 넷, 넷 다 추천대로 갔다.

> 사용자: (회고 1) "설정 env 후보로 대기열에 (Recommended)"
> 사용자: (회고 2) "대기열에 올린다 (Recommended)"
> 사용자: (회고 3) "근거를 더한다 (Recommended)"
> 사용자: (회고 4) "근거를 더한다 (Recommended)"

1. **대기열 40(새 줄).** `PYTHONUTF8=1`을 `.claude/settings.json`의 `env`로. 환경 함정 첫 줄을 어긴 것이라 강제력이
   높은 층으로 옮긴다. 반영 전에 Bash 명령과 훅에 먹는지 잰다.
2. **대기열 41(새 줄).** 한도 초과로 전체 재리뷰가 비어도 스레드 답글이 수정을 확인했으면 덮인 것으로 본다는
   `operations.md` 예외 한 줄. PR #80에 이은 2회차. ADR 뒤다.
3. **대기열 20의 15회차.** 기준은 뜻인데 찾기는 낱말("프로브")로 해 "쟀다·실측" 근거를 놓쳤다.
4. **대기열 37의 4회차.** PR 구독이 봇의 리뷰·요약 갱신·코멘트를 알림으로 전달해 사람의 "끝났어?" 없이 이어 갔다.
   37의 전제를 반영 전에 다시 잰다.

회고를 먼저 돌리고 일지를 Write하므로 retro 훅이 조건대로 발동한다. 이 단계의 회고는 방금 끝났으므로 다시 돌리지 않는다(대기열 28).

## 검사

커밋마다 돌렸다. 마지막(CodeRabbit 반영 뒤) 결과다.

- pytest 663 passed, 4 deselected
- ruff check와 ruff format 통과(`.scratch/*/probes/` 포함)
- pyright 0 errors
- lint-imports 4 kept
- 지침 검사와 타입 우회 검사 통과
- `-m llm`은 돌리지 않았다. LLM 테스트가 지나는 코드(`src/`)를 건드리지 않았다

## 다음

- **web-admin 설계 인터뷰**(`/grill-with-docs`). 프론티어는 web-admin 하나이고 `.scratch/web-admin/`이 없다. 대기열 27이
  반영되어 `grilling`이 라운드를 `AskUserQuestion`으로 올린다. plugin-toggle이 넘긴 것은 `plan.md`의 web-admin 행에 있다.
  설계가 프로브를 근거로 들면 `.scratch/web-admin/probes/`에 커밋한다(`docs/agents/issue-tracker.md`).
- 남은 하네스 chore: 37·39(둘 다 `next-session` 1단계. 37은 4회차 근거대로 전제를 다시 잰다), 40(`PYTHONUTF8` 설정 env).
- 보류: claude-review의 테스트 이름 Nit(위 PR 리뷰), ADR 0014의 "이분 탐색" 문구, spec-reviewer가 plugin-toggle 명세의
  불린 예시가 거짓 쪽만 든다고 한 nit, "주장만" 자리의 옛 스크립트와 불확실 하나(`d56cf2da/probe.py`). 앞 세션의 보류 둘
  (CodeRabbit의 fsync Nit, 여러 워커에 걸친 즉시 끄기)은 그대로다.
