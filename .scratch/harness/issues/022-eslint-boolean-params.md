# 022: ESLint 판정자가 TypeScript 의 불리언 매개변수를 잡는다

**What to build:** `CODING_STANDARDS.md` 의 불리언 플래그 인자 줄은 파이썬(ruff FBT, `tools/check_instructions.py`)만 말하고, `web/eslint.config.mjs` 에는 불리언 매개변수를 보는 규칙이 없다. 그래서 TypeScript 의 불리언 플래그 매개변수를 셀프 리뷰 표준 축이 잡았다(대기열 483, 285 의 6회차). 판정자의 `RESTRICTED_SYNTAX` 에 함수 정의의 불리언 매개변수를 잡는 selector 를 더한다. 잡는 자리는 ruff FBT001·FBT002 에 맞춘다: 주석이 `boolean` 이거나 `boolean` 을 든 유니온인 매개변수와 기본값이 `true`·`false` 인 매개변수다. 이름 붙인 옵션 객체(`{ force }: { readonly force: boolean }`)는 파이썬의 키워드 전용 매개변수에 해당하므로 지나보낸다. 켜기 전에 `web/` 의 위반 수를 재고, 고칠지 판정에서 뺄 자리를 정한다. 그 뒤 `CODING_STANDARDS.md` 의 그 줄이 이 규칙과 규칙이 보지 못하는 자리를 가리킨다.

**대기열:** 483

**Status:** done

## 수용 기준

- [x] `web/eslint.config.test.ts` 에 걸리는 사례(주석 `boolean`, 선택 매개변수 `?: boolean`, `boolean` 을 든 유니온, 기본값 `true`·`false`, 화살표 함수와 메서드)와 지나는 사례(옵션 객체, 불리언이 아닌 기본값)를 먼저 써서, 규칙을 켜기 전에 걸리는 사례가 빨갛다는 것을 본다. 사례는 규칙 ID `no-restricted-syntax` 와 메시지의 표지를 본다
- [x] `web/eslint.config.mjs` 의 `RESTRICTED_SYNTAX` 에 selector 를 더하고, 설정 주석에 잡는 자리와 보지 못하는 자리를 적는다
- [x] 켜기 전 `web/` 의 위반 수와 그 자리를 일지에 적고, 모두 고치거나 판정에서 뺄 자리를 까닭과 함께 정한다
- [x] `CODING_STANDARDS.md` 의 불리언 플래그 줄이 이 규칙과 규칙이 보지 못하는 자리를 가리킨다
- [x] 대기열 483 을 이 티켓으로 닫는다
- [x] 검증 명령이 모두 초록이다
