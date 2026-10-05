# 04: CORS — 허용 출처의 페이지만 새 접두사의 응답을 읽고 에러 응답에도 헤더가 붙는다

**What to build:** 브라우저가 사이트 파일의 허용 출처에서 보낸 요청은 새 접두사의 응답(200과 401·404·409·422·429·500 전부)에 `Access-Control-Allow-Origin`·`Vary: Origin`·`Access-Control-Expose-Headers`가 붙어 읽을 수 있고, 허용 밖 출처에는 `Allow-Origin`이 없다. 새 접두사의 preflight(`OPTIONS` + `Access-Control-Request-Method`)는 토큰 없이 CORS 응답을 받고, 그 밖의 경로에서 preflight는 401 그대로다. 관리 경로와 `/runs`에는 출처가 있어도 CORS 헤더가 없다. 예기치 않은 500의 봉투에도 헤더가 붙는다.

01의 틈 하나(preflight 401)를 닫는다. 03·05와 나란히 돌 수 있고 02를 막는다 — 429 응답의 CORS 헤더와 `Retry-After` 노출은 02가 이 미들웨어 위에서 잰다.

근거는 `.scratch/end-user-channel/spec.md`의 "CORS", "인증 미들웨어와 접두사 표"(preflight), Testing의 "인증 전수 검사"와 "CORS" 절과 그 2026-10-05 명세 검토·to-tickets 주석, 측정 `cors_scoped.py`다. ADR 0023과 ADR 0011의 2026-10-03 이력이 앞선 결정이다.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] **Starlette의 `CORSMiddleware`를 새 접두사에만 건다.** 경로 접두사로 가르는 작은 ASGI 분기 하나가 접두사 아래는 `CORSMiddleware(인증(앱))`로, 그 밖은 `인증(앱)`으로 보낸다. 분기의 비교는 01이 둔 공용 층의 접두사 비교 함수다. 미들웨어는 `add_middleware`로 건다(프로브가 앱을 밖에서 감싸 `ServerErrorMiddleware` 안쪽에 들어갔던 사례. 일지 2026-10-05-03). 직접 쓰지 않는다
- [ ] **허용 출처는 모든 사이트의 허용 출처를 합친 집합이다.** 사이트별로 가르지 않는다(preflight에는 토큰이 없다). 토큰과 출처를 묶는 것은 범위 밖이다
- [ ] **허용 메서드는 `GET`, `POST`, `OPTIONS`. 허용 헤더는 `Authorization`, `Content-Type`, `Last-Event-ID`. 노출 헤더는 `Retry-After`, `X-Request-Id`.** 자격 증명(쿠키)은 허용하지 않는다. `max_age`는 라이브러리 기본값. 셀프 리뷰 표준 축이 저장소 밖 탐침으로 손으로 봤다 — 설치된 Starlette 1.6.0은 `allow_methods`의 `OPTIONS`를 `Allow-Methods: GET, POST, OPTIONS`로 그대로 싣는다. 테스트가 그 값을 고정한다
- [ ] **preflight는 CORS 미들웨어가 인증 앞에서 답하고 갈래는 셋이다**(설치된 Starlette의 코드를 to-tickets가 읽었다 — `Origin`이 없을 때만 안쪽으로 넘기고, `Origin`이 있는 preflight는 미들웨어가 직접 답한다). 허용 출처의 preflight는 토큰 없이 200. **허용 밖 출처(사이트 파일이 없어 허용 출처가 빈 것도)의 preflight는 라이브러리의 400 평문("Disallowed CORS origin")이고 봉투가 아니다**(to-tickets에서 사용자가 골랐다. 브라우저는 preflight 실패를 페이지 스크립트에 드러내지 않아 봉투가 있어도 읽히지 않고, 명세가 직접 쓰는 안을 거부한 이유가 그대로 든다). `Origin` 없는 `OPTIONS`는 인증의 401이다. 이 400이 봉투 규칙의 유일한 예외라는 것을 `http.md`에 적고 테스트가 셋을 고정한다. `PUBLIC_PATHS`는 `/health` 하나 그대로이고 preflight는 목록의 원소가 아니다(01이 `http.md`에 가름을 적었다)
- [ ] **예기치 않은 500도 CORS 안쪽에서 봉투가 된다.** 추적 식별자 미들웨어를 둘로 가른다 — 식별자 심기는 바깥 그대로(preflight 응답도 식별자를 든다), 핸들러가 놓친 예외의 봉투 변환은 접두사 분기 안 CORS 안쪽. 운영자 면의 변환 자리는 그대로다. 측정 `cors_scoped.py` 사례 7과 대조군이 근거다
- [ ] **인증 전수 검사에 preflight 축을 더한다.** 앱이 아는 모든 경로에 대해 허용 출처의 preflight가 새 접두사에서만 토큰 없이 200이고 그 밖은 401이다(01의 3분법 분류를 쓴다). 기존 테스트 `test_다른_출처의_preflight_는_토큰이_없으면_관리_경로도_채널_경로도_401이다`의 독스트링이 CORS가 없는 것이 곧 차단이라 적은 것을 새 접두사의 예외를 아는 문장으로 고친다(명세 검토 nit)
- [ ] **CORS 테스트.** 허용 출처의 요청에 세 헤더가 200·401·404·409·422·500 모두에 붙고(429는 02가 더한다 — 이 티켓에는 429를 내는 자리가 없다), 허용 밖 출처에는 `Allow-Origin`이 없고, 접두사 밖에는 출처가 있어도 없다. 사이트 둘의 출처가 모두 허용된다. 사이트 파일이 없으면 허용 출처가 비어 어느 출처에도 붙지 않고 preflight는 400이다
- [ ] **`http.md`에 CORS의 자리(접두사 분기, 미들웨어 순서, 변환의 자리)와 헤더 집합, preflight의 예외를 적는다.** 조립 층 독스트링의 미들웨어 순서 문단을 고친다
- [ ] 검증 명령이 모두 초록이다. `server.py`와 공용 층을 건드리고 `channel/`은 건드리지 않으므로 `-m llm`은 돌리지 않는다(채널 라우트를 건드리게 되면 돌린다)
