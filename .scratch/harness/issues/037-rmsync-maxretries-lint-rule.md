# 037: 재귀 rmSync 가 maxRetries 없이 EPERM 으로 끝나는 종류를 판정자가 잡는다

**What to build:** 윈도우에서 `rmSync(경로, { recursive: true, force: true })` 는 다른 프로세스가 잠깐 쥔 파일이 있으면 `EPERM` 으로 끝난다. 판정자 시험의 `afterAll`(대기열 65), 판정자 임시 트리(379), 관리 화면 e2e 준비(`web/apps/admin/e2e/stack.ts`, 543)에서 자리만 바꿔 되풀이됐다. 사례마다 그 자리를 고쳐 온 것이 종류를 없애지 못했으므로, 종류 전체를 판정자가 막는다. 처방은 대기열 543 의 앞쪽 갈래다. `web/eslint.config.mjs` 의 `RESTRICTED_SYNTAX` 에 `recursive: true` 인 `rmSync` 호출이 `maxRetries` 를 주지 않으면 잡는 selector 를 더하고, `web/eslint.config.test.ts` 에 걸리는 사례와 지나는 사례를 붙인다. 공용 도우미(뒤쪽 갈래)는 고르지 않는다. 도우미는 새 직접 호출을 막지 못해 결국 같은 규칙이 필요하고, 규칙은 도우미 없이도 종류를 닫는다.

켜기 전에 `web/` 의 재귀 `rmSync` 자리를 세어(대기열 543 은 열둘 가운데 `maxRetries` 를 준 곳이 `web/tools/judge-trees.ts` 하나라고 적었다. 기준 커밋에서 다시 세니 열다섯 곳이고 `maxRetries` 가 있던 곳은 `judge-trees.ts` 와 `assemble.ts` 둘이어서 고칠 곳은 열셋이다) 모두 고친다. 규칙이 보지 못하는 자리(옵션을 변수로 넘기는 호출, 문자열 키)는 설정 주석에 적는다.

한계도 티켓에 남긴다. `maxRetries` 는 일시 잠김을 다시 시도해 넘기는 것이고, 다른 프로세스가 그 폴더를 작업 폴더로 쥔 경우는 못 푼다(위젯 e2e 일지 `docs/journal/2026-10-24-10-widget-e2e.md` 46행은 `maxRetries: 10, retryDelay: 200` 으로도 막지 못했다고 적는다). 그래서 이 티켓은 "재시도 없이 끝나는 종류"를 닫는 것이고, 관리 화면 e2e 정리가 이 재시도로 실제로 지나는지는 반영 뒤 e2e 를 쳐서 본다.

**대기열:** 543

**Status:** done

## 수용 기준

- [x] `web/eslint.config.test.ts` 에 걸리는 사례(`maxRetries` 없는 `rmSync(…, { recursive: true, force: true })`, `fs.rmSync` 꼴, `retryDelay` 만 준 호출)와 지나는 사례(`maxRetries` 를 준 호출, 재귀가 아닌 `rmSync`, 옵션을 펼친 호출)를 먼저 써서, 규칙을 켜기 전에 걸리는 사례가 빨갛다는 것을 본다. 사례는 규칙 ID `no-restricted-syntax` 와 메시지의 표지를 본다
- [x] `web/eslint.config.mjs` 의 `RESTRICTED_SYNTAX` 에 selector 를 더하고, 설정 주석에 잡는 자리와 보지 못하는 자리를 적는다
- [x] 켜기 전 `web/` 의 위반 자리를 린트로 세어 일지에 적고 모두 `maxRetries` 를 준다
- [x] 관리 화면·위젯 e2e 정리(`stack.ts`)가 재시도로 지나는지 e2e 를 쳐서 본다. 지나지 못하면 그 사실을 일지와 대기열에 남기고 별도 행으로 쓴다
- [x] 대기열 543 을 이 티켓으로 닫는다
- [x] 검증 명령이 모두 초록이다
