# 2026-09-29 (05) 생성 클라이언트 — 계약에서 타입을 생성하고 클라이언트 둘이 각자 제 토큰을 싣는다

web-admin 티켓 03. 일지 04의 "다음"(03이 05~08의 임계 경로)을 이어 새 세션에서 했다. 브랜치는
`feature/03-generated-api-client`, 주 체크아웃이다. 요청 범위는 구현·리뷰·커밋·PR·병합까지다.

## 한 것

- `web/packages/api-client`(`@agent-os/api-client`)를 세웠다. 생성물 `src/generated/openapi.ts`, 관리·채널 클라이언트 둘
  (`clients.ts`), 재개 스트림을 프레임으로 읽는 것(`stream.ts`)이다.
- 생성 스크립트 `web/tools/generate-api-client.ts`가 openapi-typescript의 출력에서 재귀 `Json` 한 자리만 `unknown`으로
  바꾸고 Prettier를 돌린다. `--check`가 verify의 첫 단계다.
- typecheck가 워크스페이스 패키지마다 돈다(`pnpm -r exec tsc --noEmit`).
- 판정자에서 패키지의 전역 `fetch` 예외를 거두고, atoms·molecules가 이 패키지를 import하는 것을 막았다.

정한 것과 그 이유는 티켓 파일의 "이 티켓이 정한 것"이 원천이다. 뒤 티켓(04·05·08)에 넘길 것은 각 티켓의 "03이 남긴
메모"에 적었다.

## 구현 중에 멈춘 자리 — `--immutable`

클라이언트 타입 테스트를 쓰다가 `GET /plugins`의 `data`를 순회할 수 없는 것을 봤다(TS2488). openapi-fetch 0.17.0(최신)의
응답 타입 `Readable<T>`는 배열을 `T extends (infer E)[]`로 알아보는데, `--immutable`의 `readonly E[]`는 여기 들지 않는다.
그래서 키를 재매핑하는 객체 갈래로 떨어지고, 배열성과 메서드의 호출 가능성이 함께 지워진다. 설계 프로브 `gen_run.mjs`는
생성물만 봤고, `jsdom_sse.sh`는 스트림을 단언으로 받아 이 자리를 재지 않았다.

두 안을 잰 뒤 물었다. 헬퍼에 readonly 갈래를 패치하는 안도 세 자리를 모두 풀었다. 처음에는 `node_modules`에서 재고
되돌렸고, 셀프 리뷰 뒤 같은 프로브에 패치 변형으로 넣었다.

> 사용자(질문에 답): "--immutable 거두기 (Recommended)" — 보인 ADR 0021 이력 초안 그대로

ADR 0021에 2026-09-29 이력을 쌓았다. 근거 프로브는 `.scratch/web-admin/probes/immutable_readable.sh`다.

같은 측정에서 하나를 더 찾았다. 결정 경로의 본문을 인라인 객체 리터럴로 주면 `parseAs: "stream"`의 `data`가
`unknown`이다. 판별 유니온 본문에서 openapi-fetch의 옵션 추론이 제약으로 떨어진다. `Decision` 타입의 값으로 주면
`ReadableStream`이다. 사용법의 문제라 결정하지 않고 08의 메모와 타입 테스트의 주석에 적었다.

## 잰 것

- openapi-typescript의 API 출력과 CLI 출력이 두 생성물(`--immutable`과 가변) 모두 머리 주석 밖에서 바이트까지 같았다.
  CLI는 Redocly 설정을 따로 찾아 규칙이 API 기본값과 다르지만(셀프 리뷰가 찾았다), 이 계약에서는 차이가 없다.
- 가공하지 않은 생성물에 tsc를 돌리면 TS2502가 `Json` 자리 하나에서 났다. 변환 뒤에는 0이고, 생성물은
  `strictTypeChecked` 판정을 예외 없이 지났다.
- `pnpm -r exec tsc --noEmit`은 루트 도구를 PATH에서 찾고, 패키지의 타입 에러에서 1로 끝났다.
- boundaries는 junction 링크(pnpm의 윈도우 링크 모양)로 풀린 워크스페이스 패키지를 external로 분류했다.

## TDD와 변이

테스트를 먼저 썼지만, 구현 전의 빨강은 모듈 부재였다. 그래서 `probes/api_client_mutations.mjs`로 변이를 넣었다.
`tools/mutate.py`가 pytest만 돌아서 같은 규약(원문이 한 번, 기준선, 바이트 그대로 되돌리기, 오류는 빨강이 아니다)을
따르는 러너를 프로브로 두었다. 처음 돌렸을 때 하나가 초록이었다. `rest`를 프레임 시작이 아니라 마지막 줄 시작에서
잘라도 테스트가 지나갔다. 조각 경계가 `data:` 줄과 그 프레임을 닫는 빈 줄 사이에 오는 경우를 재는 테스트가 없었다.
서버가 두 개행을 다른 조각으로 보내면 프레임이 통째로 사라지는 모양이다. 테스트를 더했고, 셀프 리뷰 뒤 `baseUrl` 변이를
더해 23 모두 기대대로 빨강이다.

변이를 쓰다가 테스트 하나의 약점도 찾았다. 최신성 검사가 생성물을 고쳐 쓰지 않는지 보는 테스트가 실행 직전의 파일과
비교해, 앞 테스트가 이미 고쳐 썼다면 초록이 됐다. 실행 뒤의 파일이 진짜 계약에서 생성한 것과 같은지로 바꿨다.

`--immutable`을 거두며 커밋 전 생성물이 옛 모양으로 남아 있던 동안 저장소 상태 테스트가 빨갛게 섰다. 최신성 검사의
실제 빨강이다.

러너를 고치다 한 번은 `&&` 앞의 치환 스크립트가 실패해 러너가 돌지 않았는데, 같은 이름의 로그 파일에 남은 첫 실행의
결과를 새 결과로 읽을 뻔했다. 로그를 지우고 다시 돌렸다(새로 더한 변이가 목록에 없어서 알아챘다).

## 셀프 리뷰

`/code-review`(base `5772785`, 추적 파일 14, 미추적 5항목, 커밋 0)를 돌렸다. 두 축 모두 Critical·Major는 없었다.

고친 것:

- **두 축이 같이 찾은 셋.**
  - 변이 러너 머리의 자기 모순. 최신성 검사와 판정자 설정의 변이가 들어 있는데 "여기 없다"고 적었다.
  - 원문에 없는 따옴표 인용. `stream.ts`와 티켓이 `adapters/jsonl.py`의 `_require_raw_run` 독스트링을 말을 바꾼 채
    따옴표로 옮겼다(인용 대조 훅도 커밋에서 같은 자리를 경고했다).
  - 커밋된 근거가 없는 주장 둘. 패치 안이 풀렸다는 것과 CLI와 API의 바이트 비교다. 프로브에 패치 변형과 바이트 비교를
    넣었다.
- **Standards.**
  - "남은 것도 `raw`로 온다"는 거짓이었다. 끝의 빈 줄만 빠진 완전한 프레임은 이벤트로 온다. 테스트를 더하고 문장을
    고쳤다.
  - "다시 켜는 조건"의 판정 자리가 가변 배열과 같은지를 봤다. 그러면 고쳐진 뒤 다시 켜도 빨갛게 남는다. 순회와 원소
    대입으로 바꿨다.
  - 변이 러너가 tsc의 종료 코드 2를 빨강으로 셌다. 문법 오류도 2다. 변이마다 진단이 날 파일을 적어 판정하게 했다. 그러자
    내 첫 처방("TS1xxx는 문법 오류")이 `satisfies`의 TS1360에서 틀린 것이 드러났다.
  - 프로브가 1·2·3을 각 자리에서 확인하지 않았고, 3을 대입으로 봤다. 줄 표지와 타입 일치로 바꿨다.
  - `CODING_STANDARDS.md`의 두 규칙에 맞췄다. 불리언 플래그 규칙에 따라 `write`와 `check`로 갈랐고, try 블록 규칙에 따라
    `framesFrom`을 뺐다. `unknownJson`은 `replaceRecursiveJson`이 됐다.
- **Spec.**
  - 명세 651행의 옛 문장을 고쳤다.
  - `baseUrl`이 실행되는 곳이 없어, `"/api"`로 되돌려도 초록이었다. `clients.test.ts`를 더했다. 한글 토큰은 헤더의
    ByteString 변환에서 던져 ASCII로 바꿨다(실제 토큰은 ASCII다).

남긴 것:

- **`data` 줄이 없는 블록이 사라지는 것(Spec).** SSE 명세의 동작이다. 제어 블록(`retry:`·`id:`)을 원문으로 내면 잡음이
  된다. 못 보는 것으로 코드와 티켓에 적었고, PR에서 본다.
- **토큰의 브랜드 타입(Standards, Primitive Obsession).** ADR 0021이 거부했다.
- **결정 래퍼(Standards, 서드파티 경계).** 함정은 `readFrames(data)`에서 컴파일로 잡힌다. 08의 설계다.
- **판정자가 막지 않는 HTTP 길 셋(Standards).** `openapi-fetch` 직접 import, `EventSource`·`XMLHttpRequest`, 상대 경로 import다.
  05의 메모로 넘겼다. 05는 03에 막혀 있다.

## 검사

커밋 전에 `CLAUDE.md`의 검증 명령 다섯을 돌렸다. pytest 1013 통과, ruff 두 명령, pyright 0, lint-imports, `pnpm -C web
verify`(테스트 90) 모두 초록이다. pre-commit 전용인 지침 검사와 타입 우회 검사도 초록이다. 변이 러너 23과 프로브
`immutable_readable.sh`는 종료 0이다.
