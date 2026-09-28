---
status: accepted
date: 2026-09-28
---

# 원칙 III은 TypeScript에도 걸리고 typescript-eslint가 판정한다

헌법 원칙 III은 `Any`, `cast`, `type: ignore`, `pyright: ignore`라는 파이썬의 말로만 적혀 있어 TypeScript에 대해서는 침묵한다. 슬라이스 3에서 `web/`이 생기고, 그 타입의 원천은 `openapi.json`에서 생성한 클라이언트다(ADR 0021). TS의 `as` 하나는 그 계약을 조용히 덮는다. **원칙 III을 TypeScript로 넓힌다. `any`, 타입 단언(`as`와 꺾쇠 단언, `as const`는 제외), 비null 단언 `!`, `@ts-ignore`와 `@ts-nocheck`를 쓰지 않는다. `@ts-expect-error`는 타입 테스트 파일(`*.test-d.ts`)에서만 설명과 함께 쓴다. 판정자는 typescript-eslint이고, 타입 기반 규칙(`no-unsafe-*`)까지 켜며, ESLint의 인라인 설정을 끈다(`linterOptions.noInlineConfig`).** 원칙의 문장이 바뀌므로 거버넌스상 major(3.0.0)다. `@ts-expect-error`를 타입 테스트에 남기는 이유는 그것이 억제가 아니라 단언이기 때문이다. 그 줄에 에러가 없으면 컴파일이 실패하고, "이 코드는 컴파일되면 안 된다"를 고정하는 자리다. 파이썬 쪽에서 같은 일을 하는 것은 pyright 프로브다.

## Considered Options

- **원칙은 파이썬만, TS는 `strict`만.** 비용이 0이다. 그러나 `strict`는 명시적 `any`도 `as`도 막지 않는다. ADR 0013이 pyright strict에 대해 적은 것과 같은 구멍이다. 거부했다.
- **web 지침으로만 둔다.** 헌법 밖 `.claude/rules/`의 한 줄이다. 교정 루프의 강제력 사다리에서 린터보다 아래 층이라, 헌법 원칙 하나가 사람 판단에 걸린다. ADR 0013이 거부한 모양 그대로다. 거부했다.
- **원칙 III 규칙의 끄기 주석만 막는다.** 다른 규칙은 설명을 붙여 끌 수 있다. 그러나 eslint-comments 플러그인이 새 의존성으로 들고, 원칙 III의 규칙 목록이 설정 두 곳에 산다. 거부했다. `noInlineConfig`는 ESLint 내장 한 줄이고, 정당한 예외는 설정 파일에 경로와 함께 들어가 리뷰에 diff로 보인다.
- **`@ts-expect-error`를 전면 금지하고 `expectTypeOf`만 쓴다.** "컴파일되면 안 된다"는 주장을 테스트로 고정할 길이 좁아진다. 거부했다. 어디서나 설명과 함께 허용하는 안은 제품 코드의 억제가 되어 거부했다.

## Consequences

- **TypeScript는 5.9에 고정한다.** npm 최신인 7.0.2에서 typescript-eslint 8.70.1은 `typescript-eslint does not support TS 7.0`을 내며 시작부터 거부했다. 5.9.3에서는 `no-unsafe-*`와 단언 금지가 탐침의 다섯 건을 모두 잡았다(`.scratch/web-admin/probes/ts7_lint.sh`). 7.0.2는 JS 컴파일러 API를 내보내지 않아 openapi-typescript의 생성도 죽는다(`gen_run.mjs`). 올리는 날은 판정자가 먼저 서야 한다.
- **판정자는 언어마다 하나다.** 파이썬은 `tools/check_type_escapes.py`(ADR 0013)이고 TS는 ESLint다. 한 언어 안에서 판정자가 둘로 갈리지 않는다.
- **생성물을 판정 범위에서 빼지 않는다.** openapi-typescript는 재귀 `Json`에서 TS2502를 내고 그것을 `any`로 둔다. 그래서 생성 스크립트가 그 자리를 `unknown`으로 바꿔 생성물의 우회를 0으로 만든다. 빼는 목록을 두면 ADR 0013이 경계한 모양(범위를 손으로 두 곳에 적는다)이 된다. 대상 글롭은 `.d.ts`도 든다. ADR 0013이 `.pyi`를 범위에 넣은 이유와 같다.
- **tsconfig의 `strict`를 끄는 것도 우회다.** 타입 기반 규칙은 타입 정보에 기대므로, 설정 한 줄이 파일 하나의 단언보다 세다. ADR 0013의 `typeCheckingMode`와 같은 자리이고, `strict`가 켜져 있는지를 검사가 본다. ESLint 규칙이 아니라 설정을 읽는 검사라 판정자와 별개이고, 자리는 명세가 정한다.
- **헌법 개정은 web-admin의 첫 티켓이 한다.** http-channel의 첫 티켓이 원칙 IV를 개정한 것과 같다. `principles.md`의 원칙 III 문장이 두 언어를 말하게 되고, `docs/constitution/README.md`의 버전이 3.0.0이 된다.
