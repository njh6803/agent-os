# 2026-09-29 (03) web-admin 티켓 01 — 헌법·하네스·web 뼈대

02 세션의 지시문으로 연 새 세션이다. `/implement .scratch/web-admin/issues/01-constitution-harness-web-skeleton.md`로
시작했고 브랜치는 `feature/01-constitution-harness-web-skeleton`, 주 체크아웃에서 했다. 대기열 50은 병합되지 않아 이
PR에서는 claude-review의 코멘트 0개 가드가 꺼진다. 산출물은 다섯이다.

- 헌법 3.0.0. 원칙 III이 TypeScript를 말한다. `tech.md`의 웹·프론트 구성·원격·CI 행, `operations.md`의 머리·가드레일·
  클론 뒤 설치·문서 위치
- `web/` pnpm 워크스페이스 뼈대. 기준 tsconfig, ESLint 판정자(`eslint.config.mjs`)와 그 변이 테스트, tsconfig 검사
  (`tools/check-tsconfig.ts`), Prettier, Vitest, `verify` 스크립트. pre-commit의 web-verify 훅과 `ci.yml`의 web 단계
- 하네스. 중첩 지침 파일 검사(`tools/check_instructions.py`), 게이트 훅의 pnpm·Playwright 모양, 페이로드 둘,
  `.claude/rules/web-workspace.md`, 검증 명령을 넷으로 세던 문장들, PR 템플릿, KICKOFF.md 두 곳
- 티켓 03·04·05의 "01이 남긴 메모", 티켓 01의 "이 티켓이 정한 것", 변이 파일 `harness_mutations.toml`
- 이 일지

> 사용자: "/implement .scratch/web-admin/issues/01-constitution-harness-web-skeleton.md 다음 작업: … 헌법·하네스·web
> 뼈대 — 원칙 III을 TypeScript로 넓히고, 검증 명령 다섯과 web 워크스페이스 뼈대와 ci.yml을 세운다 … 이어받을 상태:
> PR #97의 claude-review Minor … 는 PR #98에서 닫혔다 … 02가 병합되어 03은 이제 01만 기다린다 … 이번 요청 범위:
> 구현·리뷰·커밋· PR·병합까지"

## 이 티켓이 정한 것

원천은 티켓 끝의 같은 이름의 절이다. 여기에는 줄기만 둔다.

- ESLint 설정은 `.mjs`다. ESLint 10은 `.ts` 설정에 jiti(새 의존성)나 불안정 플래그를 요구했다.
- verify는 린트·포맷·타입·단위 테스트·tsconfig 검사다. 포맷은 명세의 넷 밖이라 PR에서 사용자가 본다.
- typescript-eslint는 8.70.1이다. pnpm 11의 `minimumReleaseAge`가 하루 안 된 8.71.0에 예외 목록을 쌓으려 했다.
- boundaries 7의 `entry-point`는 폐기 예정이라 barrel을 `dependencies`의 `fileInternalPath`로 판정한다.
- `app/`의 외부 import는 `next`·`react`만, 전역 `fetch`는 `globalThis`·`window`·`self` 속성도, 생성 클라이언트 패키지의
  `fetch` 예외는 지금 둔다.

## 잰 것

- **tsconfig 밖의 파일은 규칙이 아니라 파싱 오류로 빨개진다.** 프로젝트 서비스가 "was not found by the project
  service"를 낸다. 변이 테스트가 "빨갛다"만 봤다면 사례 전부가 엉뚱한 이유로 통과했다. 그래서 사례마다 규칙 ID를
  단언하고, 임시 트리의 앱·패키지마다 기준을 extends하는 tsconfig를 둔다. 그러면 타입 기반 규칙이 앱 자리에서 돈다.
- **boundaries의 요소 패턴은 경로 끝에서부터 맞춘다**(`partialMatch` 기본값). 그래서 `components/atoms` 같은 패턴이
  `app/`이든 `src/app/`이든 걸린다. 앱 이름은 경로 앞쪽이라 파일 범주(`**/apps/*/**`)의 캡처로 잡았다. 앞이 빈 실제
  배치와 앞에 임시 디렉터리가 붙은 배치 모두 둘째 캡처가 앱 이름이다(micromatch로 쟀다).
- **`no-restricted-syntax`는 파일마다 한 번만 설정된다.** 서버 파일 블록이 그것을 다시 적으면 enum·`"use server"`
  금지가 그 파일에서 사라진다. 금지 구문을 상수 하나에 두고 펼쳐 쓴다.
- **ESLint 10은 `.ts` 설정을 읽지 못한다**(jiti가 없으면 `The 'jiti' library is required`).
- **`tsc --showConfig`는 `strict: true`를 아홉 플래그로 풀어 낸다.** 입력 파일이 없으면 TS18003으로 끝난다. 검사는
  TypeScript API로 `extends`를 풀고, 목록은 테스트가 `--showConfig`와 대조한다.

## TDD와 변이

- **tsconfig 검사.** 테스트를 먼저 써 수집 오류를 보고 구현했다. 저장소 상태 테스트는 구현 뒤라 기준 tsconfig의
  `strict`를 끈 변이에서 빨강을 봤다.
- **판정자.** 규칙 없는 설정(파서만)에서 빨강 사례 전부가 빨간 것을 보고 규칙을 더했다. 이때 **거짓 초록 하나**를 잡았다.
  "끄기 주석이 끄려던 위반이 보고된다"가 규칙 없는 설정에서도 초록이었다. 규칙 ID가 "Definition for rule … was not
  found" 오류에도 찍혀 두 번 세어졌다. 규칙 ID가 아니라 위반 메시지를 세도록 좁혔다.
- **초록 가드.** `@ts-expect-error`를 전역으로만 막은 중간 설정에서 타입 테스트 파일의 초록 사례가 빨개졌다. 나머지
  넷(`as const`, barrel 경유, organisms→atoms, `app/`→pages·templates)은 설정을 지나치게 넓힌 변이에서 빨개졌다.
- **파이썬.** 지침 검사와 게이트 훅은 스텁·빈 패턴에서 빨강을 봤다. 제외 셋과 Playwright 모양은 `tools/mutate.py`로
  변이 넷을 넣어 모두 기대대로 빨강이다(`harness_mutations.toml`). mutate.py는 pytest만 돌아 TS 쪽에 쓰지 않았다.
- **실행.** pre-commit의 web-verify 훅이 다섯 단계를 도는 것을 `--verbose`로 봤고, `any` 한 줄을 둔 임시 파일로 훅이
  빨간 것을 봤다. 세션 중 이 저장소의 게이트 훅이 파이프에 넣은 `pnpm run verify`를 실제로 경고했다.

## 셀프 리뷰

`/code-review`(base `c6a0ca6`, 파일 37, 커밋 0, 미추적 0). 두 축이 나란히 돌았다.

- **명세 축 Major.** 새 중첩 지침 파일 검사가 두 문장과 부딪혔다. KICKOFF.md 181행은 모노레포에 패키지별 중첩
  `CLAUDE.md`를 권하고, 219행이 이 검사를 새 프로젝트에 복사하게 한다. 리뷰를 확인하다 헌법에서도 같은 충돌을 찾았다.
  `operations.md`의 문서 위치가 "한 앱에만 해당하면 그 앱 안(README, 중첩 `CLAUDE.md`)"이었다. 헌법 문장이라
  물었다.

> 사용자(질문에 답): "둘 다 ADR에 맞춤 (Recommended)" — operations.md 49행을 '앱의 문서는 그 앱 안(README), 앱의
> 지침은 .claude/rules/*.md + paths'로 고치고(헌법 3.0.0에 함께 묶음), KICKOFF.md 181행 권고를 paths 규칙으로 바꾸고
> 139행 검사 목록에 중첩 검사를 더한다.

- **고친 것.**
  - 변이 파일과 프로브 README의 주장이 둘 다 틀렸다("워크트리가 있어야 빨개진다"). 넷 모두 임시 트리나 루트
    `CLAUDE.md`로 빨개진다.
  - 판정자 사례 둘을 더했다. 타입 테스트 파일의 설명 없는 `@ts-expect-error`, `app/`이 층 밖의 앱 파일을 import하는 것.
  - 표준 축이 "쓰이지 않는다"고 본 `app` 요소는 지우면 둘째 사례가 빨개졌다. `app/` 정책을 떠받치는 요소라 지우지 않고
    이름을 `workspace-app`으로 바꾸고 주석을 달았다.
  - 판정자 테스트의 tsconfig를 임시 트리 뿌리 하나에서 앱·패키지마다로 옮겼다. 04 메모가 이것을 잰 것으로 적었었다.
  - 검사 수를 세는 문장 셋(테스트 독스트링 "여덟", 모듈 독스트링 "뒤의 넷", pre-commit 이름)과 "원칙 III의 기계
    판정자" 둘을 고쳤다.
  - verify 단계 목록이 넷에 복제돼 있던 것을 `web/package.json`을 가리키게 줄였다(`operations.md` 하나만 남기고 03
    메모에 적었다).
  - 게이트 훅 독스트링에 web 쪽의 못 보는 것을 적었다. 규칙 파일에서 근거 없는 "식별자는 영문이다"를 뺐고,
    "판정한다"와 "빼는 목록"의 범위를 판정자로 좁혔다.
  - 05 메모에 `operations.md`의 "내용은 같다" 예외에 e2e를 더하는 일을 넘겼다.
- **남긴 것.** `isRecord`가 TS 테스트 두 파일에 같다(세 줄, 공유 모듈을 둘 만큼 쓰이지 않는다). "templates는 슬롯만"의
  import 쪽 절반을 린트로 옮기는 것은 `tech.md`의 "API 호출은 organisms 이상"과 부딪혀 결정이 먼저라 두었다.
  "새 tsconfig는 기준을 extends"를 검사로 올리는 것은 이 티켓 밖이다.

## 검사

리뷰 반영 뒤 파이프 없이 하나씩 돌렸다.

- `uv run pytest -q`: 959 passed, 4 deselected
- `ruff check .` 통과, `ruff format --check .` 통과(291 files), `pyright` 0 errors, `lint-imports` 5 kept
- `tools/check_type_escapes.py`, `tools/check_instructions.py` 통과. 바뀐 마크다운의 표 검사와 줄 구분 문자 검사 통과
- `pnpm -C web verify`: 린트·포맷·타입 통과, Vitest 50 passed, tsconfig 검사 통과
- `tools/run_hooks.py`: 31건, 어긋남 0

잔존 grep은 티켓의 패턴 넷과 셋을 제외(일지, ADR, `.scratch/`, `.claude/worktrees/`)대로 돌렸다. 수를 말하는 패턴은
"그대로 두는 것" 둘(`tools/check_type_escapes.py`, `tests/sdk/test_ids.py`)만 남았다. `검증 명령`·`lint-imports`에
걸린 줄은 수를 말하지 않거나 다섯째 명령을 함께 나열한다. `별도 PR로 먼저`는 둘 다 `claude-code-review.yml`의
범위로 좁혀져 있다.

## PR 리뷰

PR #99. 세 검사가 첫 푸시(`2ff7a23`)에서 초록이었다.

- **CI `verify`.** 로그에 web 단계가 모두 있다(`pnpm -C web install --frozen-lockfile`, eslint, prettier, tsc, vitest 파일
  2 통과, tsconfig 검사). pnpm 스토어 캐시는 첫 실행이라 저장됐다.
- **claude-review.** `ci.yml`을 바꿔 코멘트 0개 가드가 꺼진 PR이라 손으로 봤다. "지적 없음" 요약 코멘트가 있다.
- **CodeRabbit.** Nit 하나. `findTsconfigs`가 `.next/`와 `judge-*` 임시 트리까지 훑는다. 코드는 바꾸지 않았다.
  `judge-*`의 tsconfig는 기준을 extends해 남아도 초록이고, 빼면 "훑어서 전부 본다"는 검사에 제외 목록이 생긴다.
  `.next/`는 04 메모의 빌드 산출물 항목에 더했다.
- **PR 직전 CodeRabbit CLI.** `Seat: not assigned`(Plan: Free)라 돌리지 않았다.

## 사용자 질문 둘 — 지침의 자리, 강제 장치와 컨텍스트

PR의 CI가 도는 동안 사용자가 다른 대화에서 받은 설명 둘을 붙여 넣고 물었다.

> 사용자: "위 내용이 맞아? 우리 프로젝트가 하는 방식이 맞아?" (중첩 CLAUDE.md와 `.claude/rules/`를 비교한 설명)

> 사용자: "추가로 위 내용도 확인해줘. 확인해보고 적용할만한 것은 적용하자. (필요하면 KICKOFF.md도 갱신)" (테스트·lint·
> 권한·hooks·CI의 기준과 컨텍스트 낭비 요인을 다룬 설명)

워크플로 둘(에이전트 23·16)로 공식 문서 두 갈래, CHANGELOG·이슈, `claude -p` 2.1.281 탐침(카나리아와
`InstructionsLoaded` 훅 로그)을 대조했다. 결과 원문은 이 세션의 스크래치패드에 있고 적용 목록은 뒤따르는 chore가 원천이다.

- **지침의 자리.** 이 저장소의 방식(중첩 금지, rules와 `paths`)은 유지한다. 공식 문서(`large-codebases`)의 선택 기준은
  소유권이다. 디렉터리마다 소유자가 제 규약을 유지하면 중첩 `CLAUDE.md`, 한곳에 모으면 `paths` 규칙이다. 붙여 넣은
  설명에서 틀린 곳은 넷이다. 실리는 계기는 "다룰 때"가 아니라 Read다. AGENTS.md는 2.1.277부터 직접 읽는다(CLAUDE.md가
  있으면 가려진다). 실린 파일은 `/memory`가 아니라 `/context`로 본다. "위치면 중첩, 종류면 rules"는 공식 구분이 아니다.
- **이 PR이 쓴 과장 셋을 고쳤다.** "로드 시점 표를 조용히 우회한다", "열 때"(`operations.md` 문서 위치,
  `check_instructions.py` 독스트링, KICKOFF.md (3)). 로드 시점은 `paths` 규칙과 비슷하고, 다른 점은 그 안의 `@` 임포트가
  루트 지침의 검사 밖에 놓인다는 것이다. KICKOFF의 "모노레포도 `paths`가 기본형"은 공식 기준을 인용해 런북의 선택으로
  적었다. CLAUDE.md의 "나머지 다섯은 훅이 돌린다"는 "pre-commit이 돌린다"로 바꿨다(Claude 훅과 헷갈린다).
- **주 세션에서도 재현했다.** `paths` 규칙은 Read 도구로 연 파일에만 실린다. `sed -n`으로 `adapters/clock.py`를 읽으면
  `adapters.md`가 실리지 않았고 Read로 열자 실렸다. 이 세션도 `tools/*.py`를 `cat`으로 읽는 동안 `tools.md`가 빠져 있었다.
- **탐침의 부작용.** `claude -p` 두 번이 사용자 전역 Stop 훅으로 Slack 알림을 보냈다. 판정자 하나가 스크래치패드의
  다른 탐침 트리를 지웠다(그 실행은 근거에서 뺐다). 탐침 세션 기록이 `~/.claude/projects/` 아래에 생겼다. 사용자에게
  알렸다.
