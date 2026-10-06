# 2026-10-06 (07) end-user-channel 티켓 04 — CORS: 허용 출처의 페이지만 새 접두사의 응답을 읽고 에러 응답에도 헤더가 붙는다

일지 2026-10-06-01의 "다음"이 가리킨, 나란히 여는 셋(03·04·05) 가운데 둘째 세션이다. `/implement .scratch/end-user-channel/issues/04-cors-on-prefix.md`로
시작했고 브랜치는 `feature/04-cors-on-prefix`, 워크트리 `.claude/worktrees/04-cors-on-prefix`다. 산출물은 여섯이다.

- 공용 층: 새 모듈 `http/cors.py`(`CorsUnderPrefix`와 허용 메서드·헤더·노출 헤더), `errors.py`의 `AssignRequestId`를 둘로 가름(식별자 심기와
  기록은 그대로, 핸들러가 놓친 예외의 변환은 새 `CatchUnexpected`), `sites.py`의 `Sites.origins()`(허용 출처의 합집합)
- 조립: `server.py`가 미들웨어 넷을 바깥에서 안쪽으로 `AssignRequestId` → `CorsUnderPrefix` → `CatchUnexpected` → `RequireToken`으로 건다
- 테스트: `tests/test_server.py`의 CORS 절 아홉(전수 검사의 preflight 축, preflight 세 갈래, 허용 메서드·헤더와 자격 증명, 허용 밖 출처, 접두사 밖,
  사이트 둘, 사이트 파일 없음, 예기치 않은 500, 경로의 출처), `tests/channel/http/test_end_user.py`의 상태 코드 행렬 하나(200·401·404·409·422·500)
- 문서: `.claude/rules/http.md`의 CORS 항목과 `PUBLIC_PATHS`·봉투·모듈 항목, `README.md`의 http 줄, 명세의 닫은 주석 셋, ADR 0023 이력 초안과 포인터,
  ADR 0019 포인터
- 프로브: `cors_scoped.py`를 다시 돌게 고침, 변이 표 `cors_mutations.toml` 16개와 그 README 줄, 02 티켓 끝의 "04가 넘긴 메모"
- 티켓 04를 done으로, 티켓 끝에 "이 티켓이 정한 것", 이 일지

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/end-user-channel/issues/04-cors-on-prefix.md
> 다음 작업: … 허용 출처의 페이지만 새 접두사의 응답을 읽고 에러 응답에도 헤더가 붙는 티켓 … 어디서: 새 세션. 나란히 여는 3 중 2. 주 체크아웃에서
> 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 … 이번 요청 범위: PR과 병합까지"

## 구현에서 정한 것

- **분기는 받은 안쪽 앱 하나 위에 두 사슬을 짓는다.** 명세와 프로브는 분기가 `CORSMiddleware(인증(앱))`과 `인증(앱)`을 스스로 짓는 모양이었다.
  인증을 분기 안에서 지으면 인증이 두 벌이 되고 변환의 자리도 분기마다 따로 정해야 한다. 그래서 인증과 변환은 그대로 `add_middleware`로 걸고
  분기는 바로 안쪽 사슬만 감싼다. 결과의 모양은 명세와 같다 — 접두사 아래는 `CORSMiddleware(변환(인증(앱)))`, 그 밖은 `변환(인증(앱))`.
  변환이 운영자 면에 서는 자리는 식별자 심기와 인증 사이로, 둘이 한 미들웨어였을 때와 같다.
- **분기는 `request.url.path`를 본다.** 처음 쓴 판은 ASGI의 `scope["path"]`였다. 인증 표와 예외 표는 `request.url.path`를 보는데, 이것은
  `scope["path"]`를 URL로 다시 파싱한 값이라 퍼센트 인코딩된 `?`(`/end-user%3Fx`)에서 둘이 갈린다. 인증은 `/end-user`로 보아 서명 토큰을
  요구하는데 분기는 접두사 밖으로 보아, 그 401의 봉투를 페이지가 읽지 못한다. Starlette 1.6.0의 `URL.__init__`을 읽었고 테스트가 고정한다.
- **허용 출처의 합집합은 `Sites`의 질의다.** 조립 층에서 펼치지 않고 사이트 목록이 소유한다(사이트별로 가르지 않는 이유와 함께).

## TDD와 변이

- 구현 전에 새 테스트를 썼다. 빨강 여덟, 초록 셋이었다. 초록 셋은 가드 둘(허용 밖 출처에 `Allow-Origin` 없음, 접두사 밖에 CORS 헤더 없음)과
  기존 테스트(관리·채널 경로의 preflight 401)다 — CORS가 아예 없을 때도 참인 단언이다.
- 구현 뒤 전부 초록. 변이 표 `cors_mutations.toml` 16개가 모두 기대대로 빨강이었다. 가드 셋은 같은 변이("CORS를 앱 전체에")를 가드마다 따로
  겨눴다 — `-k`가 여럿을 고르면 하나만 빨개도 빨강이라 나머지가 재지 않은 채 지나간다. 셀프 리뷰 뒤 테스트 이름 하나를 바꿔 그것을 겨누던
  변이 셋의 `-k`를 고치고 다시 돌렸다(셋 다 기대대로).

## 프로브를 고친 것

`cors_scoped.py`를 지금 코드로 다시 돌리자 두 곳에서 어긋났다. 티켓 01 뒤로 인증 표의 값이 `SharedToken`인데 프로브는 문자열을 넘겨, 표가
아무것도 막지 않아 사례 (2)·(3)이 405·200이었다(01에서 이미 썩어 있었다). 그리고 이 티켓이 `AssignRequestId`에서 변환을 떼어 내 대조군 (7')은
예외가 그대로 터졌다. 코드 주석과 `http.md`가 이 프로브의 사례 7과 대조군을 근거로 들어(`docs/agents/issue-tracker.md`의 "쟀다"는 커밋한
프로브가 다시 내는 것에만), 표의 값을 `SharedToken`으로 감싸고 대조군은 프로브의 변환을 분기 바깥에 두도록 고쳤다. 같은 판으로 다시 돌려
README의 2026-10-05 표와 같았다.

## 셀프 리뷰

`/code-review`(base `8df4d87`, 변경 12개, 미추적 2개, 커밋 0개). 표준 축은 하드 4·반증 5·smell 4, 명세 축은 빠진 수용 기준 0에 지적 6이었다.

고친 것:

- 살아 있는 문서의 거짓 문장 넷. 명세 214행("지금은 추적 식별자 미들웨어 하나가 … 함께 하는데")과 206·395행에 닫은 주석을 달았다. ADR 0023의
  "층"("CORS는 … 인증 미들웨어가 맡는다")은 이력 초안과 포인터로, ADR 0019의 "CORS가 없는 것이 곧 차단이다"는 관리 화면의 중계가
  `/api/end-user/*`도 넘기므로 `(바뀜: ADR 0023)`으로 표시했다.
- "허용 헤더 셋만"은 거짓이었다. Starlette가 CORS 안전 목록 헤더(`Accept`·`Accept-Language`·`Content-Language`)를 늘 더한다. 테스트 이름과
  `http.md`·`cors.py`에 적었다.
- "봉투 규칙의 유일한 예외"의 열거가 닫히지 않았다. to-tickets에서 사용자가 고른 것은 허용 밖 출처의 400이고, 허용 밖의 메서드·헤더·private
  network는 같은 라이브러리 검사의 같은 400이다. 예외의 범위를 "라이브러리의 preflight 검사에 걸린 것"으로 적었다.
- "그 밖의 경로에서 preflight는 401"에 반례 `/health`(인증을 지나 라우터의 405)가 있었다. "allowlist 밖"으로 좁혔다.
- `AssignRequestId` 독스트링이 "둘이 한 미들웨어였을 때는 … 붙지 않았다"고 겪은 일처럼 적었는데, 그때 저장소에는 CORS가 없었다. 조건문으로 고쳤다.
- nit: "헤더를 내지 않을 뿐"(허용 밖 출처에도 `Expose-Headers`는 붙는다), "사례 7"(바깥이면 붙지 않는 것은 대조군 7'), 테스트의 인용
  "allowlist 가"(ADR 원문은 "allowlist가"), "가장 바깥"(`ServerErrorMiddleware`가 더 바깥), lifespan만 든 문장(websocket scope도 경로가 있다),
  `_preflight`의 인자 이름 `headers`(→ `asked`).

남긴 것:

- 미들웨어 순서의 설명이 `http.md`와 `server.py` 독스트링에 겹친다(Duplicated Code). 티켓이 두 곳을 다 요구했다.
- 프로브의 불리언 인자 `catch_inside`가 두 곳에서 동작을 가른다. 프로브 코드이고 처음 판부터 있던 인자다.
- 축 밖: `auth.py`의 `_prepared`와 `dispatch`의 `match`에 기본 갈래가 없어 `Credential`이 아닌 값을 넘기면 요청이 그대로 지나간다. 옛 프로브의
  (3)이 그 실례다. 지금 막는 것은 pyright뿐이고 조립은 타입이 맞는 값만 넘긴다. 이 티켓의 범위가 아니다.

## 검사

- `uv run pytest -q`: 1581 통과(셀프 리뷰 반영 뒤 두 파일 205 통과)
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright`, `uv run lint-imports`: 초록
- `pnpm -C web verify`: 초록(Vitest 270)
- pre-commit의 넷(`check_instructions`, `check_type_escapes`, `check_md_tables`, `check_line_separators`)과 `check_adr_pointers`: 초록
- 바꾼 `http.md`를 새 `claude -p` 세션(`--setting-sources project,local --strict-mcp-config --model sonnet --tools Read`, `.claude/**` 읽기
  거부)에서 불러 봤다. init의 `tools`가 `Read` 하나, `mcp_servers`가 비었고, `server.py`를 연 세션이 preflight 400이 봉투 규칙의 유일한
  예외라는 것을 `.claude/rules/http.md`에서 읽었다고 답했다. 그 문장은 `server.py`에 없다.
- `-m llm`은 돌리지 않았다. `channel/` 소스를 건드리지 않았다(티켓의 마지막 체크박스).
