# 2026-11-12 (03:54) 리뷰 봇이 dev→main PR을 건너뛰게 한다 (harness dev-review-bot-off)

세션 제목 `chore/dev-review-bot-off`. 브랜치 같은 이름, 워크트리 `.claude/worktrees/dev-review-bot-off`. 모델 Sonnet 5.5 / high(지시문).

## 사용자 프롬프트

> 다음 작업: .scratch/harness/issues/dev-review-bot-off.md. 리뷰 봇 워크플로(claude-code-review.yml)가 머리 브랜치가 dev인 PR을 건너뛰게 한다
> 다음 단계: 구현
> 이번 요청 범위: PR과 병합까지

## 결정

- **조건에 머리 저장소 비교를 더했다.** 티켓은 "머리 브랜치가 `dev`인 PR(base `main`)"만 말했다. 포크가 브랜치 이름을 `dev`로 지어도 리뷰가 건너뛰어지지 않도록 `head.repo.full_name == github.repository`를 함께 본다. 명세에 없는 항이지만 건너뛰는 쪽으로 새는 길을 막는 방향이라 넣었고, 주석과 티켓 표 여섯째 행에 밝혔다.
- **주석은 ADR의 결정만 인용한다.** 처음 쓴 문장은 "리뷰는 dev에 들어간 티켓 PR마다 이미 끝났다"는 이유를 ADR 인용 괄호 앞에 두었는데, ADR 0043 Consequences "티켓 검사와 봇"은 이유 없이 "리뷰 봇은 dev→main에서 끄고 hotfix에서는 돈다"까지만 말한다. 셀프 리뷰 두 축이 같은 지적을 냈고 이유 문장을 걷었다.

## 한 일

- `.github/workflows/claude-code-review.yml`: 잡 `if`를 `!draft && !(머리 저장소 == 이 저장소 && 머리 브랜치 == 'dev' && base == 'main')`으로 바꾸고 머리 주석 네 줄을 더했다. 코멘트 0개 가드는 같은 잡의 스텝이라 함께 건너뛴다.
- `.scratch/harness/issues/dev-review-bot-off.md`: 수용 기준을 닫고 확인한 근거 절(여섯 경우 표)을 더했다.

## 검증

- 임시 PR이 아니라 조건식을 읽어 손으로 따졌다. 여섯 경우(dev→main 건너뜀, hotfix→main·feature/chore/docs→dev·포크의 dev→main 돎)를 `uv run python -c` 한 줄로도 돌려 같은 결과를 봤다. 그 한 줄은 커밋한 프로브가 아니다.
- `yaml.safe_load`로 `if`가 한 줄 문자열로 접히는 것을 봤고, `uv run zizmor --offline --strict-collection --config .github/zizmor.yml .`가 지적 없음이다.
- `uv run ruff check . && uv run ruff format --check .` 초록. `uv run python tools/run_checks.py`는 pytest 한 건(`tests/tools/test_rerun_runner.py::test_파일럿에서는_인계로_멈추지_않는다`)이 빨갰고 나머지는 초록이었다. 그 시험은 단독으로 통과했고(66초), 커밋의 pre-commit이 같은 러너를 다시 돌려 전부 초록이었다(pytest 441초, web-verify 544초). 원인은 재지 않았다. 부하가 큰 병렬 실행에서 시간에 기댄 시험이 흔들린 것으로 읽었다.
- 실제 dev→main PR에서 건너뛰는 모습은 아직 못 봤다. dev가 서고 첫 dev→main PR이 열릴 때 처음 본다.

## 셀프 리뷰

범위: base cd77e4096, 파일 둘, 커밋 0개, 미추적 0개. 표준 축과 명세 축 모두 Critical·Major 0.

- 고친 것: 주석의 이유 문장(위 결정), 티켓 근거 절의 "파이썬으로 돌렸다"를 "손으로 따졌다, 커밋한 프로브가 아니다"로 낮춤.
- 남긴 것: `docs/constitution/operations.md` 리뷰 파이프라인에 dev→main 예외를 적는 일은 `dev-base-skills-docs` 티켓이 그 절을 이미 문서 목록에 들고 있어 거기에 둔다. 대소문자 `Dev` 브랜치도 건너뛰어지는 점(GitHub 식의 `==`는 대소문자를 가리지 않는다)은 push 권한이 있어야 만들 수 있어 두었다.

## PR 직전 리뷰

CodeRabbit CLI가 끝까지 돌았다(`Seat: not assigned`, `Plan: Free`에서도 `review_completed`). 지적 1건(Minor): 티켓이 "검증 명령이 초록"에 체크했는데 근거 절에 pytest 한 건 빨강이 적혀 있다는 것. 근거 절이 정직하게 적었고 pre-commit이 같은 러너를 초록으로 돌렸으므로 그 사실을 근거 절에 더했다. 우회 길은 없다(포크 PR은 비밀을 받지 못하고 `pull_request_target`은 `.github`에 없다). 삭제된 포크의 `head.repo`가 null이면 잡이 도는 쪽이다. 그 리뷰가 덧붙인 주의 하나, 건너뛰는 강도는 `dev` 브랜치 보호와 같다.

## 회고

낸 후보 셋, 판정은 승인 0, 기각 3, 넘김 0이다.

- `tests/tools/test_rerun_runner.py::test_파일럿에서는_인계로_멈추지_않는다`가 `run_checks.py`의 병렬 pytest에서 한 번 빨갛고 단독으로는 통과했다(66초). **기각**: 부하에서 따로 돌리면 지나는 시험이 빨개지는 종류는 이미 받아들여 닫았다(`.scratch/retro-queue/0306.md`, ADR 0036 결정). 새 사례는 회차를 더하지 않고 일지에만 적는다는 닫는 말에 따라 위 검증 절에만 적었다. 이 시험이 시간 단언 때문인지는 재지 않았다(어림).
- 주석에 ADR이 말하지 않은 이유 문장을 ADR 인용 괄호 곁에 두었다. **기각**: `code-review` 두 브리프의 주장 검증 2번(인용)이 겨냥한 기준을 어겨 리뷰가 잡았다. 리뷰가 제 몫을 했으므로 회차에서 뺀다(retro 4단계).
- 서브에이전트를 일 없이 한 번 띄워 대기용으로 쓰려 했다. **기각**: 사건 하나이고 손상이 없으며 검사로 잡을 수 없는 판단이다.
- 대기열 점검: 만료할 항목 21개(승인 줄의 가장 늦은 날짜가 2026-10-28)를 `uv run python tools/queue_open_rows.py`와 `--ref origin/main` 두 출력에 모두 든 것만 `만료 2026-11-12 (ADR 0036)`로 닫았다(`.scratch/retro-queue/` 상태 줄 21개, 0242 0381 0411 0491 0503 0504 0505 0507 0508 0509 0510 0511 0512 0513 0521 0522 0524 0525 0526 0529 0534). 회차 5 이상은 chore 배치의 대상 그대로(`420` 등 열한 개). 새 항목은 쓰지 않았다.

## 인계: 커밋 뒤

컨텍스트가 인계 문턱(20만 토큰)을 넘은 채 커밋 뒤 경계에 왔다. 구현, 셀프 리뷰 반영, PR 직전 리뷰(CodeRabbit CLI), 회고, 커밋 둘(`c6d9aa92c`, `daf0f650d`, 둘 다 pre-commit 통과)까지 했고 열린 PR은 없다. 새 세션이 할 일은 푸시, PR 열기(본문에 자기 워크플로 파일을 바꿔 봇이 건너뛴다는 것과 대신 돈 PR 직전 리뷰를 적는다), 첫 `@coderabbitai review` 코멘트, 봇 회차, 병합(`merge.md`의 워크트리에서 병합할 때)이다. 이 일지에 쓴 "인계" 절과 한 줄은 아직 커밋하지 않았다.

open-session을 부른다 2026-11-11T19:15:00Z

## 다음

1. **`dev-base-tools`**, **`dev-base-skills-docs`**: 나란히 도는 중이다. 후자의 문서 목록에 `operations.md` 리뷰 파이프라인이 들어 있으니, 그 절에 "dev→main PR에서는 `claude-code-review.yml`이 건너뛴다"를 적는 것이 이 PR이 남긴 일이다.
2. **`dev-branch-create`**: 위 둘이 병합된 뒤. 사용자에게 먼저 물을 것에 **`dev` 브랜치 보호**를 더한다. 리뷰 봇을 건너뛰는 조건이 `dev`라는 이름에 기대므로, push 권한이 있는 누구나 `dev`에 직접 올려 리뷰 없이 main으로 보낼 수 있는 길을 `dev` 보호(PR 필수, 훅의 직접 커밋 금지와 별개)가 막는다.
3. **병합 직후**: 워크트리에서 병합하므로 주 체크아웃은 갱신되지 않는다. 새 세션이 `tidy-checkouts`를 먼저 돈다(`merge.md`).
