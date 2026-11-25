# 2026-11-25 widget-admin-server 02: 화면용 클라이언트 패키지

세션 제목: `feature/02-widget-admin-client-package`. 이 세션은 구현과 문서와 린트·타입 검증까지 마치고, 컨텍스트가 인계 문턱(20만 토큰)을 넘은 채 `셀프 리뷰 직전`에 와서 새 세션에 넘겼다. 커밋하지 않은 변경이 워크트리에 그대로 있다.

## 사용자 프롬프트 원문(요지)

> .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/widget-admin-server/issues/02-widget-admin-client-package.md

지시문의 값: 브랜치 `feature/02-widget-admin-client-package`, 모델 Sonnet 5.5 / high, 이번 요청 범위는 PR과 병합까지, 나란히 여는 03과 함께 고치는 파일은 루트 `README.md`뿐이다.

## 결정

- 생성 도구 `web/tools/generate-api-client.ts`를 두 대상(`api-client`, `widget-admin-client`)으로 넓혔다. api-client 생성물의 바이트는 그대로다. 스크립트 이름 `generate:api-client`·`check:api-client`는 바꾸지 않고 두 대상을 모두 다룬다. CLI는 `--target <이름>`을 받고, 이름도 계약도 없으면 두 대상을 모두 돈다.
- 공개 경로용 팩토리 `createPublicClient(baseUrl: URL)`는 `credentials: "omit"`을 싣고 머리를 더하지 않는다. `PublicPaths`는 `/widget-settings/{site}` 하나만 든다.
- 계약의 `schema_version`은 `integer`(리터럴 아님)이고 생성 타입에서 `number`로 나온다. 변이(`schema_version: 1`, 칸을 선택으로)로 tsc와 eslint가 실제로 빨개지는 것을 보고 되돌렸다.
- ESLint 네 자리(안쪽 import 규칙, atoms·molecules 정책, organisms·templates 정책, 패키지 안 `openapi-fetch` 허용)에 이 패키지를 더했다. `eslint.config.test.ts`의 사례는 설정을 고치기 전에 정확히 여섯 개가 빨강인 것을 먼저 봤다.
- 임시 트리에는 `openapi-fetch`가 없어, 패키지 안 import 허용 사례는 실제 `clients.ts`를 판정 대상으로 삼은 시험(`eslint.config.test.ts`가 단언한다)으로 바꿨다.
- 헌법 판을 3.1.6 → 3.1.7로 올렸다. `sibling_overlap`이 형제의 가장 높은 판을 3.1.6으로 보고했다.
- `.claude/rules/web-workspace.md`는 고치지 않았다(티켓이 정한 대로).

## 이 세션이 고친 것(번복 포함)

- `Headers.keys`가 `lib: dom`에 없어(TS2339) `request.headers.forEach`로 머리 이름을 모으게 바꿨다.
- `Record<never, never>` 비교가 `no-generated-empty-object-type`에 걸려 `toEqualTypeOf<Required<Settings>>()`로 바꿨다.
- `--target` 뒤 값이 없을 때 조용히 지나가던 것을 `?? ""`로 막아 "모르는 대상"으로 처리하게 했다.

## 확인한 것과 못 한 것

- 확인: `uv run ruff check .`, `ruff format --check .`, `pnpm -C web run lint`·`format`·`typecheck`·`check:tsconfig`·`check:api-client`, `tests/tools/test_web_images_manifests.py`, `eslint.config.test.ts`+`generate-api-client.test.ts`+`packages/widget-admin-client` 시험 135개.
- 못 함: `tools/run_checks.py` 한 바퀴(백그라운드로 돌던 것은 인계하며 멈췄다. 새 세션이 다시 돌려야 한다), 단독 배포 e2e(Docker, 호스트 80·443·3000 포트 비어 있어야 함), 셀프 리뷰, 커밋, PR.
- 티켓 `.scratch/widget-admin-server/issues/02-widget-admin-client-package.md`의 남은 체크박스: "마지막 티켓이면"과 "검증" 둘. Status는 아직 `in-progress`다. 닫을 때 `done`으로 바꾸고 `uv run python tools/plan_table.py`를 돈다.
- 마지막 티켓 판정: 지금은 04가 03에 막혀 있고 03·04가 모두 `ready-for-agent`이며 열린 PR이 없어 이 티켓이 마지막이 아니다. 병합 직전에 `git fetch origin` 뒤 04의 상태를 다시 본다. 04가 먼저 done이면 이 티켓이 `.scratch/widget-admin-server/plan.md`에 `**끝:**` 줄을 적고 `docs/release-notes/features/widget-admin-server.md`를 싣는다.

## PR 직전 리뷰에 밀 주장(새로 쓴 사실 문장)

- `docs/constitution/operations.md`·`docs/constitution/tech.md`·`README.md`의 "계약 둘, 생성 클라이언트 둘" 문장과 tech.md 26행의 "거기서 생성하는 화면용 클라이언트는 `web/packages/widget-admin-client`이고 `packages/api-client`와 따로 선다"는 문장(처음 일지에 인용을 글자 그대로 옮기지 않았던 것을 셀프 리뷰가 잡아 고쳤다).
- `web/packages/widget-admin-client/src/clients.ts`의 주석: `openapi-fetch 0.17.0`은 본문 없는 요청에 `Content-Type`·`Accept`를 붙이지 않는다. `clients.test.ts`가 가짜 `fetch`로 받은 요청의 머리를 단언한다(이 세션에서 통과한 것을 봤다. 위 "확인한 것"의 시험 135개에 든다). 0.17.0의 소스를 이 세션에서 다시 읽지는 않았다.

## 셀프 리뷰(두 번째 세션, 2026-11-25)

범위: base `085fa7b93`(HEAD와 같다), 커밋 0개, 변경 파일 열셋, 미추적 여덟(패키지 일곱과 이 일지). 표준 축은 sonnet·high, 명세 축은 세션 모델이 돌았다. 두 축 모두 Critical·Major 없음이다. 근거의 종류: 두 서브에이전트가 소스를 읽어 낸 보고이고, 시험은 명세 축 서브에이전트가 `tests/tools/test_web_images_manifests.py` 5개와 vitest 두 파일 18개를 돌려 통과를 봤다고 보고했다(이 세션이 직접 돌려 보지는 않았다).

고친 것:

- `clients.ts` JSDoc의 "모든 요청에"를 "기본으로"로 좁히고, 호출마다 넘기는 `credentials`·`headers`가 기본값을 덮는다고 적었다. 근거: 이 세션이 `web/packages/widget-admin-client/node_modules/openapi-fetch/dist/index.mjs` 70~76행을 Bash `sed`로 읽었다(`...baseOptions, ...init` 순서). 코드를 읽은 것이고, 덮어쓰는 호출의 시험은 만들지 않았다.
- `clients.ts` 머리 주석의 "브라우저는 `*`와 자격 증명을 함께 쓰는 답을 읽지 않으므로"에 명세가 이를 기억에 기댄 어림으로 적었다는 단서를 붙였다(명세 242행을 Grep으로 읽었다).
- `generate-api-client.test.ts`의 시험 제목을 "…고쳐 쓰지 않고 실패한다"에서 "모르는 대상 이름이면 최신성 검사가 실패하고 알려진 대상 이름을 보여 준다"로 바꿔 단언과 맞췄다.
- 이 일지의 tech.md 26행 인용을 글자 그대로로 고쳤다(tech.md 26행을 Read로 읽었다).

남긴 것과 이유:

- `CONTRACT`·`GENERATED`·`WIDGET_ADMIN_*` 별칭과 `generate(contract, target = API_CLIENT_TARGET)`의 인자 중복(표준 축 Minor/Nit): 기존 api-client의 시험과 도구가 같은 이름을 쓰고 있어 이 티켓의 체크박스 밖이다. 호출처는 두 대상을 모두 `TARGETS`로 돌려 기본값을 타지 않는다(코드를 읽은 것).
- `chosen` 중첩 삼항(Nit): 판단 항목이고 도구가 잡지 않는다. 남긴다.
- `index.ts`가 `components`·`paths`를 내보내는 것(명세 축이 범위 넘침으로 냈다): api-client의 `index.ts`가 같은 줄을 낸다(Bash로 두 파일을 읽었다). 오탐으로 판정했다.
- 루트 `README.md` `web/tools` 줄이 길다(겉모양): 남긴다.
- 일지 맨 끝의 "open-session을 부른다" 줄: 하네스가 붙이는 줄이라 지우지 않는다.

## 다시 돌린 것과 결과(두 번째 세션)

- `uv run ruff check . && uv run ruff format --check .`: 통과(이 세션이 돌려 출력을 봤다).
- `uv run python tools/run_checks.py`(백그라운드, 셀프 리뷰 반영 전에 시작한 한 바퀴): check-notes, check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, web-verify 통과. pytest는 8252개 통과에 1개 실패였다. 실패는 `tests/tools/test_rerun_runner.py::test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다`이고 3초 대기(`hang=3.0`)를 쓰는 시험이다. 같은 시험을 `uv run pytest -q tests/tools/test_rerun_runner.py -k 오염이_한_번이면`으로 단독으로 돌리자 20초에 통과했다. 부하 아래의 시간 흔들림으로 본다(원인을 재지는 않은 어림이다). 러너는 리뷰 반영 앞에 돌았고, 반영한 것은 주석·시험 제목·일지·티켓뿐이라 커밋의 pre-commit이 다시 돈다.
- `pnpm -C web run lint`·`format`·`typecheck`: 반영 뒤에 통과(출력을 봤다).
- 단독 배포 e2e `pnpm -C web/packages/e2e-standalone exec playwright test`: 15개 통과(14.4분). 시작 전에 포트 80·443·3000이 비어 있는 것을 `Get-NetTCPConnection`으로 봤고 `docker info`가 29.9.2를 냈다.
- 첫 커밋 시도의 pre-commit: check-notes, check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright 둘, run-hooks, web-verify, pytest, 표·줄 구분 문자·헌법 판 검사가 통과했고, mutation tables(`tools/mutate.py --staged`)가 빨강이었다(출력을 봤다). `web/tools/generate-api-client.ts`를 넓혀 `.scratch/web-admin/probes/api_client_mutations.toml`의 변이 둘(3. 최신성 검사가 어긋남을 보고하지 않는다, 4. 최신성 검사가 생성물을 고쳐 쓴다)의 원문이 0번이 됐기 때문이다. 원문을 `target` 인자판으로 고치고 4번의 되돌릴 생성물에 widget-admin-client 것을 더했다. `uv run python tools/mutate.py --check .scratch/web-admin/probes/api_client_mutations.toml`은 25개 모두 한 번씩이고, `PYTHONUTF8=1 uv run python tools/mutate.py <표> --since origin/dev`로 둘을 돌려 둘 다 기대대로 빨강이었다(4번은 시험 셋이 빨개서 표의 옛 주석 "하나만"을 고쳤다). 이 실행이 끝난 뒤 `git status`에서 생성물은 바뀌지 않았다. 교훈: 작업 규약 3의 "코드를 옮기거나 고쳤으면 그 코드를 겨누던 변이 파일을 `--check`로 본다"를 이 세션이 커밋 전에 하지 않았고 pre-commit이 잡았다(전체 한 바퀴가 20분이 넘어 한 번 더 도는 값이 컸다).
- 둘째 커밋 시도의 pre-commit: 변이 표 검사가 이번에는 표를 고친 변이 둘(3·4번)에 `expect_output`이 없다고 막았다(대기열 350의 검사). 변이를 손으로 넣어 시험 출력을 본 뒤 표지를 달았다. 3번은 `AssertionError: expected +0 to be 1 // Object.is equality`, 4번은 비교 출력의 `* @description 살아 있는지만 답한다.`이다(시험 파일에 글자 그대로 있는 `살아 있는지만 답한다.` 문장은 접두 없이는 표지가 못 돼 접두를 붙였다). `--check`가 통과했고 변이 둘을 다시 돌려 표지와 함께 기대대로 빨강이었다. 손으로 넣은 변이는 되돌린 뒤 `git diff --stat`이 비어 있는 것을 봤다.
- 같은 시도에서 `run-hooks`(`hook_ruff_line_width.py`의 한글 줄 E501이 context 대신 silent), pytest의 `tests/channel/cli/test_interrupt.py` 셋(Ctrl+C 자식이 30초 안에 끝나지 않았다)과 `tests/tools/test_rerun_runner.py`의 오염 시험이 실패했다. 이번 커밋에는 `.py` 파일이 없고(변이 표와 문서와 web 코드뿐), 앞 커밋 시도에서는 같은 이 시험들 가운데 `test_interrupt`가 통과했다. `uv run pytest -q tests/channel/cli/test_interrupt.py tests/tools/test_rerun_runner.py`를 단독으로 돌리자 69개가 모두 통과했다(123초, 출력을 봤다). 원인은 시간 제한을 쓰는 시험이 전체 실행의 부하(그 실행이 27분 걸렸다)와 다른 세션들의 부하 아래에서 흔들린 것으로 본다. 부하를 재지는 않은 어림이다.
- 마지막 티켓 판정: 병합 직전 `git fetch origin` 뒤 origin/dev에서 03·04가 `ready-for-agent`이다. 이 티켓은 마지막이 아니라서 끝 줄과 기능 단락은 싣지 않았다. `uv run python tools/plan_table.py`를 돌렸고 `.scratch/plan.md`는 바뀌지 않았다.

## 하네스에서 겪은 것

- 전체 `grep -rn ... .`는 훅(`.env` 노출 방지)에 막힌다. Grep 도구나 경로를 좁힌 명령을 쓴다.
- Bash에서 하위 폴더로 `cd`하면 훅이 막는다. `pnpm -C web ...`나 경로 인자를 쓴다. `pnpm -C web eslint`는 안 되고 `pnpm -C web exec eslint`로 쓴다.

open-session을 부른다 2026-11-25T10:41Z
