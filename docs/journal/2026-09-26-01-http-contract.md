# 2026-09-26 (01) HTTP 배관이 공용 층으로 가고 실행 전 실패가 둘로 갈린다 — http-channel 티켓 01

브랜치 `feature/01-contract-shared-http-layer-and-pre-run-failures`, PR #70(`ead0357`로 squash 병합).
http-channel의 계약 티켓이고 나머지 넷을 막고 있었다. 공용 층 `agent_os.http`가 서고, core가 실행 전
실패를 `Absent`(부재)와 `NotResumable`(재개 불가)로 갈라 던지며, 에러 어휘에 `conflict`(409)가 늘었다.
헌법은 2.5.0이다. 관리 API는 그 어휘 하나 말고 그대로 답한다.

사용자 입력은 인계 지시문 하나, Slack 커넥터 연결 알림 셋, PR·병합 지시 하나, 헌법 승인 하나, 회고 판정이었다.

## 선행 조건

지시문대로 Blocked by(헌법 버전 드리프트 정리)는 PR #69로 풀려 있었다. 헌법은 2.4.0에서 minor를 올렸다.
첫 메시지에 붙은 훅의 계기로 앱이 지은 제목이 브랜치 이름으로 바뀌었다.

## 이름 — 부재와 재개 불가

domain-modeling 스킬로 봤다. `Absent`와 `NotResumable`이다. core의 선례(`Mismatch`, `LoopLimitExceeded`)대로
`Error`를 붙이지 않았고, HTTP 어휘(`NotFound`, `Conflict`)를 피했다. 용어집에는 넣지 않았다.
`CONTEXT-FORMAT.md`가 에러 타입 같은 일반 개념을 빼라고 하고, 재개 불가는 용어집의 "재개"와 "일시정지"에서
바로 나온다. 둘 다 `ports.py`의 `PluginError` 옆에 두었다. 던지는 곳은 `run.py`지만 표가 한 곳에서
import하고 가족이 모여 있다.

함정은 `run()`과 `resume()`이 매니페스트 부재를 같은 자리에서 던진다는 것이었다. 그 자리를
`_requested_manifest`(부재)와 `_recorded_manifest`(`PluginError`)로 갈랐다. 재개 쪽을 고정하는 테스트는
구현 전에도 초록이었다. 하위 타입이 없던 때라 그 자리가 `PluginError`를 던졌기 때문이다. 변이로 재개 쪽을
`Absent`로 바꿔 빨강을 보고서야 그 테스트가 무엇을 막는지 확인했다.

## 스크립트 실행 가드

티켓이 "막는 방법은 이 티켓이 정한다"고 넘긴 것이다. 층을 만든 뒤 `python src/agent_os/main.py`를 쳐 보니
`No module named 'http.client'`로 죽었다. 안은 셋이었다.

- `main.py`의 `__main__` 블록을 빼고 `agent_os/__main__.py`를 둔다. 거부했다. `python -m agent_os.main`이
  조용히 아무것도 하지 않는 명령이 된다.
- `main.py` 첫머리에서 `sys.path[0]`을 걷어낸다. 거부했다. import 앞에 코드가 들어가 린트 억제가 들고
  `main.py` 하나만 덮는다.
- `agent_os/http/__init__.py`가 자기 이름이 `agent_os.http`가 아니면 처방을 담은 `ImportError`로 막는다.
  골랐다. 이름이 만든 문제를 이름을 가진 층이 소유한다.

티켓의 "가리지 않는다"를 "가림을 알아채고 처방과 함께 멈춘다"로 읽은 것이고, 명세 축이 그 차이를 Minor로
짚었다. ADR 0016의 "절대 import라 부딪치지 않고"가 모듈 실행에서만 참이라는 것과 이 선택을 그 ADR의
2026-09-25 이력으로 적었다. 테스트가 두 길을 나란히 판정한다.

## fastapi 하한

릴리스 노트를 WebFetch로 요약하게 했더니 `fastapi.sse`가 0.68.0에 들어왔다는 틀린 답이 나왔다. 믿지 않고
`gh api repos/fastapi/fastapi/contents/fastapi/sse.py?ref=<태그>`로 태그를 대 봤다. 0.134.0에는 없고
0.135.0에는 있다. 같은 태그의 `sse.py`와 `routing.py`에서 15초 keepalive와 `Cache-Control`·
`X-Accel-Buffering` 헤더도 확인했다. 하한은 `fastapi>=0.135`다.

## 테스트 먼저, 그리고 변이

빨강을 먼저 봤다. core 여섯(부재와 재개 불가), 서버의 import 경로(모듈 없음), 스크립트 실행 하나였다.
초록 뒤 변이 일곱이 전부 잡혔다.

- import-linter: 어댑터에 `agent_os.http` import(금지 계약), core에 같은 import(층 계약)
- 표의 순서를 뒤집음
- 재개의 기록 에이전트 부재를 `Absent`로
- 일시정지 아님을 `PluginError`로
- 빈 트레이스를 `NotResumable`로
- 스크립트 가드 제거

층 계약만으로는 어댑터 → `http`가 합법이다. 위 층이 아래 층을 import하는 것은 막지 않기 때문이다. ADR
0016이 "층 하나와 금지 하나"라고 한 이유를 변이가 그대로 보여 줬다.

## 티켓 경계

인증 모듈을 옮기며 독스트링의 "`http-channel` 은 이 결정을 물려받지 않는다" 문단을 고쳤다. 그런데 02가 그
문단을 고치는 체크박스를 갖고 있어서 원문으로 되돌렸다. 인증은 import 한 줄만 바뀐 순수 이동으로 남았다.
409의 에러 문서도 미리 넣었는데 리뷰 두 축이 04의 몫이라고 짚어 뺐다. 형제 티켓을 먼저 읽었으면 둘 다 없었다.

## 셀프 리뷰

- 표준 축: Minor 2·Nit 7.
- 명세 축: 체크박스 18 가운데 17 충족, 1 부분(스크립트 가드의 해석, Minor). Nit 4.
- Critical·Major는 두 축 모두 없었다.

두 축 브리프에 밀 주장을 나열했다. 표준 축은 같은 diff 때문에 거짓이 된 보편 주장 둘을 잡았다. 테스트
독스트링의 "run() 과 매니페스트를 읽는 자리가 같아서"와, 검증하지 않는 "같은 진단과 종료 코드"다.

고친 것:
- 불리언 플래그로 두 고장을 흉내 내던 가짜를 둘로 나눴다(`CODING_STANDARDS.md`).
- 위의 독스트링 둘.
- `PluginError` 독스트링의 "채널 쪽 표".
- 매니페스트 읽기 함수의 이름.
- 409 에러 문서.

## PR 리뷰

- **CodeRabbit CLI**는 돌리지 않았다. `coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`였다.
  PR 체크리스트에 그대로 적었다.
- **CodeRabbit PR**은 `@coderabbitai review`로 요청해 27파일을 보고 "No actionable comments"였다. 시간당
  한도를 다 썼다. 보류한 것이 둘이다.
  - Docstring 커버리지 경고(59%): 저장소는 모든 함수에 독스트링을 요구하지 않는다.
  - 보안 제안(실행 라우트가 생기면 접근 못 하는 실행과 없는 실행을 구분하지 못하게 하라): 신원이 하나인
    지금은 해당이 없고(ADR 0015), 채널 라우트 티켓이 볼 자리다.
- **claude-review**는 지적이 없었다. 원칙 IV 문언과 스크립트 가드는 "사용자 승인이 필요한 항목이라 이
  리뷰의 지적으로 올리지 않았다"고 적었다.
- 병합 전에 두 실행의 `headSha`가 `9624a9a`이고 PR head가 로컬 HEAD와 같은 것을 봤다.

## 헌법 승인

PR과 병합 지시를 받았지만 헌법 문언은 요약으로만 전해졌다. 거버넌스("개정은 … 사용자가 승인한다")와
티켓("PR에서 사용자가 바뀐 문언을 본다")대로 원칙 IV의 실제 문장과 ADR 이력을 보여 주고 물었다.
금지 열거에 `agent_os.http`를 더한 이유는 이렇다. 그 열거는 core 위의 층을 다 드는 꼴이라, `http`만
빠지면 방향이 이미 막더라도 허용으로 읽힌다.

> 사용자: (헌법 승인) "승인하고 병합 (Recommended)"

## 줄 끝 문자

변이 스크립트와 파이썬 heredoc 편집의 `Path.write_text`가 윈도의 텍스트 모드로 작업 트리에 CRLF를 썼다.
`.gitattributes`의 `eol=lf`가 커밋을 정규화했고, 병합 뒤 체크아웃으로 작업 트리도 LF가 됐다.

## 갈린 곳

- 이름, 용어집에서 뺀 것, 가드 방식, 금지 열거에 `http`를 더한 것은 추천대로 승인됐다.
- parametrize id를 ASCII로 썼다. 저장소 선례(한국어 id 셋)와 다르다. pytest가 비ASCII id를
  `끝남`처럼 이스케이프해 실패 출력이 읽히지 않아서다.
- CodeRabbit PR의 두 지적을 보류했다(위).
- CodeRabbit CLI는 좌석이 없어 돌리지 않았다.

## 번복하거나 고친 것

- fastapi 하한: 요약 도구의 0.68.0 → 태그로 잰 0.135.0.
- 인증 독스트링 선수정 → 원문 복원(02의 몫).
- 409 에러 문서 선반영 → 뺐다(04의 몫).
- 불리언 플래그 가짜 → 둘로.
- 테스트 독스트링 둘과 `PluginError` 독스트링의 "채널 쪽 표".
- `_requested_agent`·`_recorded_agent` → `_requested_manifest`·`_recorded_manifest`.
- 한국어 parametrize id → ASCII.

## 회고

후보 다섯, 하나 승인, 넷 기록.

> 사용자: (회고 판정) "기록만 (Recommended)", "기록만 (Recommended)", "20에 더한다 (Recommended)", "둘 다 기록만 (Recommended)"

1. **요약 도구에 버전 사실을 물었다(1회차).** 믿었으면 계약의 하한이 틀렸다. 태그의 파일로 재는 것이
   맞는 길이었다. 기록만.
2. **형제 티켓이 가진 것을 먼저 손댔다(1회차).** 리뷰 두 축이 잡았고 비용은 수정 하나였다. 기록만.
3. **대기열 20의 근거.** 표준 축이 거짓이 된 보편 주장 둘을 잡은 것을 20에 적었다. 새 줄이 아니다.
4. **작업 트리의 CRLF(2회차).** 1회차는 일지 2026-09-24-01이다. 커밋에는 피해가 없었다. 다음이 3회차라
   규칙 후보가 된다. 기록만.
5. **pytest의 비ASCII id 이스케이프(1회차).** 기록만.

## 검사

pytest 460 passed·3 deselected, `-m llm` 3 passed(`run.py`와 LLM 테스트의 헬퍼를 건드려 돌렸다), pyright
0 errors(67 files), lint-imports 4 kept, ruff, 지침 검사, 타입 우회 0. 변이 일곱 전부 빨강.

## 다음

- **http-channel 티켓 02(채널 토큰)가 풀렸다.** 03~05는 차례로 앞 티켓에 막힌다. 시작 프롬프트는
  `/implement .scratch/http-channel/issues/02-channel-token.md`.
- 02가 이 티켓에서 물려받는 것:
  - `agent_os/http/auth.py`는 순수 이동이라 "`http-channel` 은 이 결정을 물려받지 않는다" 문단이
    그대로다. 그 문단과 `.claude/rules/http.md`의 인증 문장을 두 토큰과 접두사 표로 고치는 것이 02의
    체크박스다.
  - `_DOCUMENTED_ERRORS`에는 409가 없다. 재개 라우트의 04가 더한다.
- CodeRabbit PR이 낸 보안 제안(접근 못 하는 실행과 없는 실행의 구분)은 채널 라우트가 생기는 03·04가
  볼 자리다.
