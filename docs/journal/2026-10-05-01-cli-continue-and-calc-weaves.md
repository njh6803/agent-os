# 2026-10-05 (01) conversation 티켓 03 — CLI가 이어 가기를 받고 calc가 교환을 엮는다

일지 2026-10-04-04의 "다음"이 가리킨 새 세션이다. `/implement .scratch/conversation/issues/03-cli-continue-and-calc-weaves.md`로
시작했고 브랜치는 `feature/03-cli-continue-and-calc-weaves`, 주 체크아웃이다. 산출물은 다섯이다.

- CLI `run`의 `--continuation RUN_ID`(`channel/cli/main.py`, `main.py`). 인자 해석 테스트 셋, 표면 테스트 넷(거절은 parametrize 넷)
- calc가 멤버를 "앞 대화" 블록으로 엮는다(`plugins/agents/calc/agent.py`). 결정적 테스트 셋(`tests/test_calc_plugin.py`, 실물 루트 + 가짜 모델)
- `-m llm` 둘. 실제 CLI로 이어 가 20, 임시 루트에 한도 30을 적은 calc의 셋째 이어 가기가 요약을 지나 14
- 02가 넘긴 메모 넷과 4회차 잔여 둘(`core/run.py`, `core/continuation.py`, `core.md`, `CONTEXT.md` 동사 표), 변이 표에 다섯
- 티켓 03을 done으로, 끝에 "이 티켓이 정한 것", 이 일지

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/conversation/issues/03-cli-continue-and-calc-weaves.md
> … 읽을 것: 일지 docs/journal/2026-10-04-04-runtime-summarizes.md의 "다음"과 "PR 리뷰" 절, 티켓 03 끝의 "02가 넘긴 메모" …
> 이어받을 상태: PR #132의 claude-review 4회차 … 셋이 남는다 — run()의 conversation을 정하는 분기를 함수로 빼기, continuation.py의
> 동사 어휘를 CONTEXT.md 동사 표에 한 줄로, Link.summary_at의 (1,)을 … 각각 해석하는 것 … 이번 요청 범위: PR과 병합까지"

## 이어받은 것

선행 조건: 주 체크아웃이 main이고 깨끗했으며 `git fetch` 뒤 `origin/main`과 같았다(`b393cac`). 원격에 `feature/04-*`도 다른 feature 브랜치도
없었고 열린 PR이 없었다 — 04 세션은 열리지 않았다. 값 기반 마스킹의 ADR 0009·0022 이력 초안 브랜치도, end-user-channel의
브랜치·`.scratch/end-user-channel/`도 없었다. 의존성은 늘지 않아 측정 판과 견줄 것이 없었다.

4회차 잔여 셋 가운데 둘을 닫았다(`SUMMARY_INDEX`, 동사 표). `run()`의 `conversation` 세 갈래는 그대로다 — 2회차 리뷰어의 조건("다음
티켓에서 분기가 더 붙으면")이 오지 않았고 이 티켓도 분기를 더하지 않는다. 함수로 빼려면 요약 이벤트가 있을 때만 유효한 짝(접기
계획과 요약)을 타입으로 묶어야 해서, 분기 셋을 그대로 읽는 쪽이 짧다.

## 구현에서 정한 것

티켓 끝의 "이 티켓이 정한 것" 여덟이다. 여기서는 근거와 대안만 적는다.

- **옵션 이름은 `--continuation`.** 명세가 "HTTP 경로와 같은 낱말"이라 했고 경로가 `/runs/{run_id}/continuation`이다. `--continue`는
  용어집의 피할 말("계속하기")에 가깝고 경로의 낱말도 아니다. 재개와 serve에는 두지 않는다 — 재개는 트레이스가 앞 실행을 안다.
- **CLI는 하위 타입을 가르지 않는다.** `_report`의 `except PluginError` 하나가 거절 넷을 그대로 받는다. 면마다 응답이 다른 것은 HTTP의
  일이고 CLI의 답은 진단과 종료 코드 1 하나다(ADR 0022·0023). 그래서 CLI 코드는 옵션을 받아 `run()`에 넘기는 것뿐이다.
- **남의 실행은 손으로 쓴 트레이스다.** CLI의 주체는 OS 사용자 하나라 달리 만들 수 없다. `JsonlTrace.write`로 시작·종료 이벤트를 쓰고
  주체만 바꿨다. 끝나지 않음은 시작 이벤트 하나만 쓴 트레이스, 고리 깨짐은 없는 앞 실행을 가리키는 끝난 트레이스다.
- **calc의 블록은 `PROMPT`의 `{previous}` 자리다.** 빈 대화면 빈 문자열이라 이 티켓 전의 프롬프트와 글자 그대로 같다. 테스트가 그
  문자열을 리터럴로 박아 둔다 — 상수를 import해 비교하면 상수가 바뀌어도 초록이라 "그 전과 같다"를 재지 못한다. 블록 머리글이
  지시가 아니라 데이터라고 적는 것은 sdk 멤버의 신뢰 경계다.
- **calc의 결정적 테스트는 실물 루트를 읽는다.** `FilesystemPlugins(REPO_ROOT / "plugins")`로 저장소의 calc와 `everything` 매니페스트를
  그대로 읽고, 도구 포트만 연결은 열리되 도구가 없는 가짜다. 가짜 모델이 받은 메시지와 트레이스의 `llm_called.prompt`가 같은지도
  함께 본다. 요약 사례는 런타임이 쓴 모양의 요약 이벤트를 손으로 둔 두 실행의 고리다(요약은 런타임만 내므로 `run()`으로는 만들 수
  없다).
- **LLM 테스트의 한도는 30, 첫 요청은 25자.** 처음에는 명세 문장 그대로 한도 22로 두 교환을 다 접었다(목표 6자). 첫 실행은 모델이
  목표를 넘겨 약 70자로 쓰고 20을 남겨 지났지만, 둘째 실행은 요약이 "5" 하나라 셋째가 -1을 냈다. 작은 목표의 요약이 무엇을 남기는지는
  모델의 몫이라 거기에 단언을 걸 수 없다. 첫 요청을 25자로 늘려 둘째 교환(13)이 절반(15) 안에 들어 원문 꼬리로 남게 했다 — 셋째가
  "거기"를 아는 것이 런타임이 정한 규칙(꼬리)으로 선다. 계기는 여전히 셋째에서만 서고 덮는 끝은 첫 실행이다.
- **`_read_paused`가 멤버까지 읽는다.** 02 메모의 "`Link`가 `run.py`로 샌다"를 `_Resumption`(시작 이벤트, 일시정지, 재생 기록, 멤버)으로
  닫았다. `resumed_conversation`을 그 안에서 불러 판정 순서(없음 → 형식 1 → 손상 → 일시정지 아님 → 자리 → 고리)가 한 함수에 있고,
  `resume()`은 `Link`를 모른다. `run.py`의 `Link` import가 사라졌다.
- **`_BOUNDARY`는 `_NOT_REPLAYED`.** 요약 이벤트가 든 뒤로 "경계"라는 이름이 뜻과 어긋났다. `core.md`의 같은 이름을 함께 고쳤고 변이
  표의 원문은 튜플의 내용이라 이름에 걸리지 않았다.
- **동사 표를 `CONTEXT.md`에 처음 두었다.** `CODING_STANDARDS.md`가 "동사가 정해지면 `CONTEXT.md`에 동사 표를 두고 그것이 원천"이라
  했고 아직 없었다. `continuation.py`의 다섯(`read`, `gather`, `check`, `plan`, `<명사>_of`)으로 시작한다.

## TDD와 변이

- 테스트 열하나(인자 셋, 표면 넷, calc 셋, LLM 하나는 함수로 둘)를 구현 전에 썼다. 아홉이 빨갰다 — 인자 해석 둘은 `RunArgs`에 필드가
  없어 `AttributeError`와 도움말 부재, 표면 넷은 `unrecognized arguments`, calc 둘은 블록 부재. 둘은 구현 전부터 초록인 가드다(이어
  가지 않은 실행의 프롬프트 리터럴, 재개와 serve의 옵션 거절). LLM 둘은 구현 뒤 실제 모델로 처음 돌렸다.
- 구현 뒤 테스트 쪽 전제로 떨어진 것이 둘. `_events` 이름이 같은 파일의 기존 도우미(스트림 조각)와 겹쳐 pyright가 잡았다
  (`_trace_events`로). LLM 테스트의 한도 22는 위 "구현에서 정한 것" — 첫 실행은 지났고 전체 스위트의 둘째 실행에서 떨어졌다. 02가 적은
  관찰(산술을 독스트링에 적은 사례는 맞았다)이 여기서는 비껴갔다. 산술은 맞았고 틀린 것은 모델이 목표를 지킬
  것이라는 전제가 아니라, 모델이 목표를 넘길 것이라는 전제였다.
- 변이 표에 다섯을 더했다. calc가 빈 대화에 블록 붙이기, calc가 요약을 교환 뒤에 두기, CLI가 앞 실행을 넘기지 않기, 재개가 옵션 받기,
  `_read_paused`가 멤버를 다시 읽지 않기. `_read_paused`와 `SUMMARY_INDEX`로 02의 변이 둘의 원문이 옮겨 간 것을 `--check`가 잡아 고쳤다.
  옮긴 둘과 가까운 둘, 새 다섯의 아홉을 돌려 모두 기대대로 빨갰다(프로브 README).
- `Path.write_text`가 윈도우에서 줄 끝을 CRLF로 바꿔 파일 다섯이 통째로 바뀌었고 변이 표의 `--check`가 원문 0번으로 열여덟을 냈다.
  바이트로 되돌리고 뒤의 스크립트는 전부 `write_bytes`다. `tools/check_line_separators.py`가 커밋에서 잡았겠지만 그 전에 변이 표가 먼저
  알렸다.

## 셀프 리뷰

`/code-review main`을 두 축 병렬로 돌렸다. 범위는 base `b393cac`, 수정 12, 커밋 0, 미추적 1(`tests/test_calc_plugin.py`)이었다. 리뷰가
도는 동안 LLM 스위트의 둘째 실행이 떨어져 한도를 22에서 30으로 고쳤고, 표준 축은 그 중간 트리(코드 22, 일지 30)를 봤다.

- **표준 축**: Critical 0, Major 1, Minor 2, Nit 2. **명세 축**: Critical·Major 0, Minor 2, Nit 3.
  - **Major(표준, 리뷰 시점의 사실)**: LLM 셋째 테스트의 코드(한도 22)와 일지·티켓(30)이 서로 달랐다. 리뷰가 도는 동안 고치던
    자리였고 지금은 코드·독스트링 산술·티켓 5번·프로브 README가 30으로 같다. 리뷰어의 산술 검증(22 기준 `plan_fold`와 일치)은
    옛 판에 대한 것이고 새 판의 산술은 테스트 독스트링에 적었다.
  - **Minor(표준·명세 공통, 반영): 동사 표의 `read` 줄에 반례.** `_read_paused`는 없으면 None이 아니라 `Absent`를 던진다. 줄을
    "없음은 None이거나, 없음이 곧 거절인 자리에서는 `Absent`"로 고치고 예 둘을 들었다. 표준 축이 든 빠진 이름 둘은 `summarize`
    줄을 더하고, 명사구 이름(`resumed_conversation`, `NEW_CONVERSATION`)은 값을 말하는 것이라 표 밖이라고 적었다.
  - **Minor(표준, 반영): `_BOUNDARY` 잔존 하나.** 티켓 02의 체크박스 문장. 티켓 02는 done이지만 conversation이 `plan.md`에서 닫히지
    않아 살아 있는 문서로 세는 것이 맞다. 괄호에 개명을 적었다.
  - **Minor(명세, 반영): 일지가 diff에 없었다.** 이 파일이다.
  - **Nit(반영) 넷.** 티켓 1의 "(인자 오류 2)"를 테스트가 종료 코드 2로 단언하게 했다. calc 테스트 모듈 독스트링의 근거 절을 Testing
    "CLI"에서 명세 "calc"의 명세 검토 괄호로. 테스트 독스트링의 "메시지"(피할 말)를 "받은 것"·"프롬프트"로. CLI 모듈 독스트링에
    `--continuation`과 "끝난 실행에 안내를 찍지 않는다"를 더했다 — rules에 CLI 파일이 없어 그 독스트링이 CLI 결정의 원천이다.
  - **Nit(보류) 둘.** 기존 LLM 테스트의 `[e for e in … if not isinstance(e, UnknownEvent)]`가 새 도우미 `_trace_events`와 같은
    모양인데, 이번 diff 밖의 줄이라 두었다. LLM 셋째 테스트가 첫 답이 5자를 넘으면 깨지는 것은 독스트링이 조건("모델이 '5'면")을
    밝혀 두었다.
  - 표준 축의 판단 항목. `run_command`의 키워드 인자 열셋(Data Clumps, 포트 다섯 묶음은 후속 후보), `previous_run` 배관이 넷을 지나는
    것(CLI 배관의 본질), `_missing(directory)`의 미사용 인자(parametrize의 균일 시그니처). 셋 다 두었다. 리뷰 관점 넷은 `_Resumption`·
    `_previous_block`·`SUMMARY_INDEX`가 값을 하고, 이름이 용어집과 맞고, 모듈의 변경 이유가 하나이며, 테스트가 행동을 본다고 답했다.
- 고친 뒤 검증 명령을 모두 다시 돌렸다(아래 검사 절). 변이 표의 원문 확인도 다시 지났다.

## PR 리뷰

PR 직전 CLI는 `coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 돌리지 않았다. 푸시 뒤 `@coderabbitai review`를 남긴다.

## 검사

판정 명령은 파이프 없이 돌리고 종료 코드를 봤다. 셀프 리뷰 반영 뒤 전부 다시 돌렸다.

- pytest 1421 passed, 6 deselected(경고 셋은 변경 전부터 있던 pytest-asyncio의 것)
- ruff check와 ruff format 통과
- pyright 0 errors
- lint-imports 5 kept
- 지침 검사와 타입 우회 검사 통과. 마크다운 표 검사와 줄 구분 문자 검사를 바뀐 문서에 손으로 돌려 통과
- `pnpm -C web verify` 통과(web은 건드리지 않았다)
- `uv run --env-file .env pytest -m llm` 6 passed(기존 넷, 새 둘). core 실행 모듈과 CLI를 건드렸으므로 돌렸다. `--basetemp`로 남긴
  트레이스는 모두 형식 3이고 `llm_called` 16건과 요약 이벤트 1건의 토큰 합계는 34,208(입력 32,913, 출력 1,295)이다. 요약 호출은 입력
  543, 출력 338이고 요약 글은 "2+3→5 답함"이었다. 한도 22였던 전체 스위트의 둘째 실행은 1 failed(요약 "5", 셋째 출력 -1)였고 그
  실행의 합계는 29,115였다. 합계는 스크래치의 스크립트가 `llm_called`와 `conversation_summarized`의 토큰을 더해 냈다.
- 변이 9 모두 기대대로(옮긴 둘, 가까운 둘, 새 다섯). `--check`는 28 모두 원문이 한 번씩 있다.

## 회고

새 후보는 없고 기록만 남긴다. 승인 대기 중인 둘(일지 2026-10-04-03·04)은 그대로 승인 대기다 — 이 세션도 긴 줄 감기를 훅이 열한 번
알렸고(독스트링 다섯, 주석 둘, 테스트 모듈 독스트링 넷), 토큰 합계 스크립트를 스크래치에 또 지었다(네 번째). 후보 2의 한 줄이 들면
그 스크립트를 `tools/`에 둘지 보기로 한 조건(네 번째)이 찼다.

- **기록만: 테스트 쪽 전제가 틀린 것이 둘.** 이름 겹침(`_events`)과 LLM 한도 22. 02의 셋, 01의 셋에 이어 세 번째 세션이라
  `CLAUDE.md` 교정 루프의 문턱에 닿았다. 그러나 셋의 공통 원인이 하나가 아니다 — 도우미 기본값, 산술, 추가 읽기, 이름 겹침, 모델의
  행동. 규칙 한 줄로 잡히지 않아 후보로 올리지 않는다. LLM 한도만은 교훈이 분명하다: 모델의 출력에 기대는 단언은 런타임이 정한 규칙
  (원문 꼬리)으로 서게 설계하고, 작은 목표의 요약이 무엇을 남기는지에는 단언을 걸지 않는다. 이 문장은 테스트 독스트링에 있다.
- **기록만: `Path.write_text`가 윈도우에서 CRLF를 쓴다.** 편집 스크립트 다섯이 파일 다섯을 통째로 바꿨고 변이 표의 `--check`가
  원문 0번으로 열여덟을 내서 알았다. `write_bytes`로 되돌렸다. 1회차라 기록만. 두 번째가 오면 `CLAUDE.md` 환경 함정 후보다.
- **기록만: 가드레일이 일한 사례.** 변이 표 `--check`가 옮겨 간 원문 둘과 CRLF를 잡았다. 명세 축이 아직 없는 일지를 가리키는
  `[x]`를 잡았다. 표준 축이 편집 중간의 불일치를 Major로 잡았다 — 리뷰와 수정을 겹쳐 돌린 비용이고 결과는 맞았다. 훅이 파이프 단
  판정 명령을 두 번, 긴 heredoc을 두 번 막았다.
- **기록만: 비용.** 셀프 리뷰 두 축 합 35만 토큰(표준 18만·도구 26회, 명세 16만·도구 21회). 변이 아홉 약 15초. `-m llm` 전체 약 2분을
  세 번(둘째가 떨어졌다), 부분 실행 둘. web verify 약 2분을 두 번. 전체 pytest 약 2분을 두 번.

## 다음

- **PR과 병합은 이 세션이다**(지시문의 범위). 병합 직전에 `git fetch` 뒤 `origin/main`의 04 티켓 `Status:`를 다시 본다 — 지금은
  `ready-for-agent`라 이 PR은 기능을 닫지 않고 `plan.md`를 건드리지 않는다. 병합 뒤 `next-session`.
- **04(관리 화면 링크)가 다음이다.** `/implement .scratch/conversation/issues/04-admin-links-previous-and-covered.md`, 브랜치
  `feature/04-admin-links-previous-and-covered`. 04가 conversation을 닫고 `plan.md`의 행을 done으로 바꾼다. 04의 LLM 테스트는 없다.
- **값 기반 마스킹의 ADR 0009·0022 이력 초안**은 아직 열리지 않았다. 요약 글은 여전히 마스킹하지 않고 싣는다.
- end-user-channel은 열리지 않았다. 열리면 CLI와 같은 거절 넷이 최종 사용자 면에서 404로 접히는 것과, 최종 사용자 투영이 요약
  이벤트를 만나는 것을 그 계약 티켓이 본다(`plan.md`의 그 행).
- 프론티어는 그대로 셋이다. conversation(04), end-user-channel(명세), design-system(설계 인터뷰).
- 하네스 쪽에 남은 것: 대기열 100~104. 승인 대기 후보 둘은 위 회고 절. 후보 2가 들면 토큰 합계 스크립트를 `tools/`에 둘지 본다.
