# 2026-10-05 (02) conversation 티켓 04 — 관리 화면이 앞 실행과 덮는 끝을 링크로 그리고 기능을 닫는다

일지 2026-10-05-01의 "다음"이 가리킨 새 세션이다. `/implement .scratch/conversation/issues/04-admin-links-previous-and-covered.md`로
시작했고 브랜치는 `feature/04-admin-links-previous-and-covered`, 주 체크아웃이다. 산출물은 넷이다.

- `EventItem`이 실행 식별자 필드 둘(시작 이벤트의 앞 실행, 요약의 덮는 끝)을 그 실행의 상세로 가는 링크로 그린다. 페이지 테스트 셋과
  적대적 트레이스 테스트의 확장 하나
- 변이 표에 vitest 변이 둘(`probes/continuation_mutations.toml`)
- conversation을 닫는다. `plan.md`의 행을 done으로, 프론티어 문단을 고쳤다. 티켓 04를 done으로, 끝에 "이 티켓이 정한 것"
- PR #133 3회차 리뷰의 Minor 하나(`CONTEXT.md` 동사 표의 `read` 줄)와 이 일지

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/conversation/issues/04-admin-links-previous-and-covered.md
> … 읽을 것: 일지 docs/journal/2026-10-05-01-cli-continue-and-calc-weaves.md의 "다음"과 "PR 리뷰" 절. 03이 먼저 병합됐으므로 04의
> 수용 기준대로 이 PR이 .scratch/plan.md의 conversation 행을 done으로 바꾸고 프론티어 문단을 고친다 … 이어받을 상태: PR #133의
> claude-review 3회차(문서만 바뀐 커밋)가 Minor 하나·Nit 둘을 냈고 병합 뒤라 일지에 적지 못했다 … 이번 요청 범위: PR과 병합까지"

## 이어받은 것

선행 조건: 주 체크아웃이 main이고 깨끗했으며 `git fetch` 뒤 `origin/main`과 같았다(`7bba2b6`). 원격에 feature 브랜치도 열린 PR도
없었다. 값 기반 마스킹의 ADR 0009·0022 이력 초안 세션과 end-user-channel의 계약 티켓은 열리지 않았다(브랜치·PR·`.scratch/end-user-channel/`
없음). 04가 열려 있는 동안 `plan.md`의 conversation 행을 건드린 다른 세션은 없었다(원격 브랜치가 main 하나다). 의존성은 늘지 않아 측정 판과 견줄
것이 없었다.

PR #133의 claude-review 3회차(`7bba2b6`에 든 문서 커밋). 병합 뒤라 그 일지에 들지 못해 여기 적는다.

- **Minor(반영): `CONTEXT.md` 동사 표의 `read` 줄 예에 `_read_paused`가 드는데 그 함수는 `resumed_conversation`으로 고리를 여러 번 읽어
  표의 정의("포트에서 하나를 읽어")와 어긋났다.** 리뷰어가 낸 두 길(뜻을 넓히거나 예에서 빼기) 가운데 뜻을 넓혔다 — "포트에서 입력 하나를
  읽고 판정해 값으로 만든다. 그 값의 멤버를 채우느라 다른 이름의 읽기(`gather`, 명사구)를 안에서 부를 수 있다". 예에서 빼면 `Absent`를
  던지는 `read`의 예가 없어진다. `gather`와의 가름은 그대로다 — `gather`는 읽기의 합 자체가 값이고, `read`는 입력 하나가 값이 되며 안에서
  부르는 읽기는 다른 이름이다. 표가 원천이라 어긋남이 쌓이기 전에 닫았다.
- **Nit(보류) 둘.** `core.md`의 실패 정책 항목 한 줄이 판정 순서 전체를 든 것은 다음에 그 절을 건드릴 때 표나 목록으로. `run_command`의
  키워드 인자 열셋은 PR #133 본문의 후속 후보 그대로(일지 2026-10-05-01 PR 리뷰 절의 2회차 보류와 같은 항목). 이 티켓은 둘 다 지나지
  않는다.

## 구현에서 정한 것

티켓 끝의 "이 티켓이 정한 것" 여섯이다. 여기서는 근거와 대안만 적는다.

- **링크는 필드 이름의 손 목록(`RUN_FIELDS`)으로 가른다.** 생성 타입에서 실행 식별자는 `string`이라 타입으로 가를 수 없고, 필드 이름 표
  (`FIELD_NAMES`)에 "링크다"를 더 적는 모양은 표의 뜻(용어집의 말)을 흐린다. 집합의 원소는 `EventField`라 계약에서 그 필드가 사라지면
  컴파일에서 깨진다. 모르는 종류(`unknown`)의 `raw`에 같은 이름이 들어도 `raw`는 문자열 하나라 링크가 되지 않는다.
- **값이 문자열일 때만 링크다.** 이어 가지 않은 실행의 `previous_run`은 `null`이고 지금처럼 글자 `null`이다. 화면이 빌드된 뒤 서버가 같은
  이름에 다른 모양을 보내도 글자로 떨어진다.
- **`href`는 트레이스의 값을 `/runs/` 뒤 `encodeURIComponent` 조각으로만 받는다.** 실행 목록의 링크(`RunList`)와 같은 모양이다. "글자로만
  그린다"(web-admin 스토리 32)와의 양립을 그리는 자리의 주석에 적었다 — 값이 텍스트 자식 밖(`href`)에 드는 유일한 자리이고, 빗금·물음표·
  우물 정자·콜론이 모두 인코딩되어 `javascript:`로 시작하는 값도 같은 경로 아래의 식별자 글자가 된다. 적대적 트레이스 테스트에 그 값을
  두어 `href`가 `/runs/` 뒤 인코딩한 조각 하나인 것을 단언한다.
- **`Object.entries<unknown>(event)`.** 값을 `FieldValue`의 prop으로 넘기자 ESLint(`no-unsafe-assignment`)가 `any` 대입을 잡았다. 기존
  코드는 `asText(value: unknown)`의 인자로만 넘겨 걸리지 않았다. 원칙 III의 판정자가 제 일을 한 사례고, 타입 인자로 `unknown`을 명시해
  닫았다.
- **기능을 닫는 판정.** 시작 때 `git fetch` 뒤 `origin/main`의 03 티켓 `Status:`가 `done`이었다. 병합 직전에 다시 본다.

## TDD와 변이

- 테스트 넷을 구현 전에 썼다. 둘이 빨갰다 — 링크 테스트(역할 `link`를 찾지 못함)와 적대적 트레이스의 `javascript:` 앞 실행 링크. 둘은
  구현 전부터 초록인 가드다(이어 가지 않은 실행의 앞 실행은 글자, 요약 이벤트의 필드 이름 — 01이 표를 세웠다).
- 가드 둘에 변이 둘을 겨눴다. 값이 `undefined`가 아니면 링크(`null`에 `encodeURIComponent`가 "null"을 낸다), `summary`의 용어집 말을
  "요약"으로. 둘 다 기대대로 빨갰고(`-t`로 그 테스트 하나씩, 각 1 failed) 나머지 28은 원문이 그대로다(`--check` 30 모두 한 번씩).
- 구현 뒤 테스트 쪽 전제로 떨어진 것은 없다. 린트가 잡은 것은 구현 쪽(`any`) 하나다.

## 셀프 리뷰

`/code-review main`을 두 축 병렬로 돌렸다. 범위는 base `7bba2b6`, 수정 7, 커밋 0, 미추적 1(이 일지)이었다.

- **표준 축**: Critical·Major 0, Minor 3, Nit 3. **명세 축**: Critical·Major 0, Minor 1, Nit 2. 누락과 범위 추가는 없었다.
  - **Minor(두 축 공통, 반영): 티켓 6항의 인용이 `CONTEXT.md` 원문과 글자가 달랐다.** 원문 그대로 고쳤다.
  - **Minor(표준, 반영): 티켓의 "검증 명령이 모두 초록이다"가 일지의 근거 없이 체크됐다.** 일지의 검사 절을 자리 표시로 두고 리뷰를
    돌린 탓이다. 아래 검사 절이 근거다.
  - **Minor(두 축 공통, 반영): 일지의 "브랜치가 하나뿐이다".** 로컬에는 브랜치 서른과 워크트리 열아홉이 있다. "원격 브랜치가 main
    하나다"로 좁혔다.
  - **Nit(반영) 셋.** `plan.md` 행의 미래형("뒤에 병합되는 쪽이 닫는다")을 과거형 한 문장으로. 프로브 README 행의 "티켓 01·02의
    가드"를 "01~04"로. 테스트의 기대값 둘(`covered`, 적대적 트레이스)이 `encodeURIComponent`로 구현을 되짚던 것을 리터럴로.
  - **Nit(보류): 실행 상세 경로 모양(`/runs/` 뒤 `encodeURIComponent`)이 `RunList`와 `EventItem` 두 자리에 있다.** 둘뿐이고
    `RunList`는 이 티켓 밖이다. 셋째가 생기면 함수 하나로 뽑는다. 받는 티켓은 없고 다음에 실행 링크를 더하는 쪽이 본다.
  - 주장 검증은 모두 지났다. "예외 하나"(값이 속성에 드는 자리는 `href` 하나), "링크 둘뿐", README의 수, 생성 타입의 식별자 필드
    둘, 잔존 0("텍스트 자식으로만"은 기록에만), 미래형은 `plan.md`의 그 문장 하나뿐이었고 고쳤다.
- 고친 뒤 검증 명령을 모두 다시 돌렸다(아래 검사 절).

## PR 리뷰

PR #134. PR 직전 CLI는 `coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 돌리지 않았다. 푸시 뒤 `@coderabbitai review`를 남겼다.

> 사용자: "끝났어?"

1회차(`2ab9219`). CI 여섯이 초록이었고 PR 머리와 로컬 HEAD가 같았다. CodeRabbit은 `7bba2b6..2ab9219`를 보고 지적 없음("No actionable
comments")이었다. 보안 검토는 화면의 인코딩과 서버의 식별자 패턴 검증이 서로 다른 통제라고 적었다. claude-review는 Minor 1, Nit 2.

- **Minor(반영): `encodeURIComponent`는 `.`과 `..`을 그대로 돌려주므로 `href`가 `/runs/..`이 되어 브라우저가 `/`로 푼다.** 머리
  주석의 "값이 그 경로 조각 밖으로 나가지 못한다"가 실제보다 강했고 적대적 트레이스 테스트도 그 둘을 덮지 않았다. 리뷰어가 낸 두 길(주석을
  좁히거나, 그 값이면 글자로 그리고 테스트를 더하기) 가운데 뒤를 택했다 — `runHref`가 둘에 null을 돌려주고 `FieldValue`가 글자로
  떨어진다. 계약의 식별자 패턴은 둘을 허락하지 않지만 트레이스는 바깥에서 온 텍스트라 화면이 믿지 않는다(web-admin 스토리 32). 테스트
  둘(`.`, `..`)을 구현 전에 써 빨강(`/runs/.`·`/runs/..` 링크)을 봤다. web에 식별자 술어가 없고 패턴을 손으로 옮기면 계약의 복제라
  둘만 가른다. `RunList`는 같은 모양이지만 이 티켓 밖이고 목록의 식별자는 서버가 어댑터의 파일 이름에서 낸 것이라 두었다(아래 Nit).
- **Nit(보류, 이유가 둘로 늘었다): 경로 모양이 `RunList`와 `EventItem` 두 자리.** 리뷰어는 `.`·`..` 처리가 생기면 한 곳에 둘 이유가
  둘이라 그때 함께 뽑자고 했다. 이 PR은 `EventItem` 쪽에만 `runHref`를 두었다. `RunList`를 고치는 것은 티켓 밖이고, 목록의 식별자에
  `.`·`..`이 들 길은 어댑터가 쓴 파일 이름뿐이다. 다음에 `RunList`나 셋째 자리를 건드리는 쪽이 `runHref`를 공용으로 올린다. 받는
  티켓은 없어 기록으로 둔다.
- **Nit(보류): `isEventField(name) && RUN_FIELDS.has(name)` 두 번 검사.** 리뷰어도 `Set<EventField>`의 컴파일 이점이 이 PR의 의도라
  지금 모양을 유지해도 된다고 했다.

## 검사

판정 명령은 파이프 없이 돌리고 종료 코드를 봤다. 셀프 리뷰 반영 뒤 전부 다시 돌렸고, PR 1회차 반영 뒤 web verify와 변이 표의 원문
확인을 다시 돌렸다(파이썬과 그 밖의 문서는 바뀌지 않았다. pre-commit이 pytest를 다시 돈다).

- `pnpm -C web verify` 통과(생성물 최신성, ESLint, Prettier, tsc, Vitest, tsconfig 검사). `RunPage.test.tsx`는 23 passed, PR 1회차 뒤
  25 passed
- pytest 1421 passed, 6 deselected(경고 셋은 변경 전부터 있던 pytest-asyncio의 것). 파이썬은 바뀌지 않아 `-m llm`은 돌리지 않았다
- ruff check와 ruff format 통과, pyright 0 errors, lint-imports 5 kept
- 지침 검사와 타입 우회 검사 통과. 마크다운 표 검사와 줄 구분 문자 검사를 바뀐 문서에 손으로 돌려 통과
- 변이 2 모두 기대대로 빨강(각 1 failed). `--check`는 30 모두 원문이 한 번씩 있다
- e2e는 늘리지 않았고 중계·시작 래퍼·api-client·서버 라우트를 건드리지 않아 로컬에서 치지 않았다. CI의 `e2e` 잡이 돈다

## 회고

새 후보는 없고 기록만 남긴다. 승인 대기 중인 둘(일지 2026-10-04-03·04, 주석·독스트링 감기 도구와 토큰 합계 한 줄)은 그대로 승인 대기다 —
이 세션은 파이썬을 편집하지 않아 감기 훅의 알림이 없었고 LLM 테스트도 없어 회차를 더하지 않는다.

- **기록만: 가드레일이 일한 사례.** 원칙 III의 TS 판정자가 `Object.entries`의 `any`를 prop에 넘기는 자리에서 잡았다(기존 코드는
  `unknown` 인자라 지나갔다). 훅이 45줄 heredoc을 막았고(Write 도구로), Grep 도구의 제외 glob이 `.env`에 닿는 것을 막았고, 파이프 끝에
  둔 판정 명령을 경고했다. 셀프 리뷰 두 축이 인용의 글자 차이와 근거 없는 체크박스를 잡았다.
- **기록만: Git Bash가 `git show <ref>:<경로>`의 콜론을 경로 변환으로 깨뜨린다(MSYS).** 두 번 겪었고 `origin/main`의 티켓 상태를 보는
  데 썼다. 작업 트리의 파일(`origin/main`과 같은 커밋)로 대신 봤다. 1회차라 기록만. 다음에 오면 `CLAUDE.md` 환경 함정 후보다(우회는
  `MSYS_NO_PATHCONV=1`).
- **기록만: 일지를 자리 표시로 두고 셀프 리뷰를 돌려 Minor가 났다.** 03 세션은 일지가 diff에 없어 Minor였다. 2회차. `next-session`
  1단계(일지는 셀프 리뷰가 고친 것이 실리도록 `/code-review` 뒤에 쓴다)와 명세 축의 요구(일지가 diff에 든다)가 맞서는 자리다. 셋째가 오면 code-review 브리프의
  리뷰어 참고에 "일지의 검사 절은 리뷰 뒤에 채운다"를 넣을지 본다.
- **기록만: 대기열 104의 근거.** 03과 04가 나란히 열릴 수 있는 마지막 티켓 둘이었고, 티켓의 수용 기준 문장("병합 직전 `origin/main`의
  상대 티켓 `Status:`")대로 03은 닫지 않고 04가 닫았다. 규약으로 올릴 때 이 사례가 효과의 근거다.
- **기록만: 비용.** 셀프 리뷰 두 축 합 약 29만 토큰(표준 15만·도구 31회, 명세 14만·도구 19회). 변이 둘 약 1분. web verify 약 2분을 두
  번, 전체 pytest 약 2분을 두 번.

## 다음

- **PR과 병합은 이 세션이다**(지시문의 범위). 병합 직전에 `git fetch` 뒤 `origin/main`의 03 티켓 `Status:`가 그대로 `done`인지 다시
  본다. 병합 뒤 `next-session`.
- **conversation이 닫혔다.** 프론티어는 end-user-channel(설계 끝, 명세가 다음)과 design-system(설계 인터뷰가 다음) 둘이다. 다음은
  end-user-channel 명세(`/to-spec end-user-channel`)로 고른다 — conversation이 넘긴 것(최종 사용자 투영이 요약 이벤트를 만나는 것,
  거절 넷이 최종 사용자 면에서 404로 접히는 것, `DifferentPrincipal`을 쓰는 것)을 받는 쪽이고, web-widget이 그것을 기다린다.
  design-system 인터뷰는 사용자가 자리에 있어야 한다.
- **값 기반 마스킹의 ADR 0009·0022 이력 초안**은 아직 열리지 않았다. 요약 글은 여전히 마스킹하지 않고 싣는다.
- **보류한 Nit 셋.** 실행 상세 경로 모양이 두 자리(`RunList`, `EventItem`. 셋째가 생기면 함수로). `core.md` 실패 정책 항목 한 줄(그 절을
  다음에 건드릴 때 표나 목록으로). `run_command`의 키워드 인자 열셋(CLI를 다음에 지나는 티켓).
- 하네스 쪽에 남은 것: 대기열 100~104. 승인 대기 후보 둘은 위 회고 절.
