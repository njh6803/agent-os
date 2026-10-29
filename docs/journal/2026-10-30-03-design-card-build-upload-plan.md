# 2026-10-29 design-card-build 03: 올리기 계획이 첫 정식 올리기를 가르고 몫을 나누며 보낼 색인을 짓는다

next-session 지시문으로 연 새 세션이다(나란히 여는 2 중 2). 제목을 브랜치 이름으로 바꾸고, 주 체크아웃에서 브랜치를 따지 않고 `EnterWorktree`(이름 `03-upload-plan-first-canonical`)로 들어가 브랜치를 `feature/03-upload-plan-first-canonical`로 바꿨다. `tidy-checkouts`는 묶음의 첫 세션 몫이라 돌지 않았다. 워크트리의 기준은 `f6df25c8`이다.

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/design-card-build/issues/03-upload-plan-first-canonical.md / 다음 작업: … 올리기 계획이 첫 정식 올리기를 가르고, 보낼 파일을 호출 몫으로 나누며, 색인의 libraries와 upgraded를 짓는다 / 다음 단계: 구현 / 어디서: 새 세션. 나란히 여는 2 중 2. … / 이번 요청 범위: PR과 병합까지"

## 한 것 (커밋 전)

- `web/tools/sync-design-system/upload.ts`: `planUpload`가 첫 정식 올리기(`firstCanonical`)를 가르고 그때 `tokens.json`을 앞 시도의 `sent` 갈래보다 먼저 보낸다. 지난 산출 목록의 지울 경로는 받은 기록의 `files`에 든 것만 낸다(기록이 없으면 목록대로). 보낼 파일과 지울 경로를 호출 몫(`calls`)으로 나눈다(경로 255·16MiB, 기록·색인을 경로로 세고 바이트는 `RECORD_LIMIT`과 새 `INDEX_LIMIT` 512,000만큼 남긴다, 지울 경로와 `_ds_sync.json`은 뒤로). 보낼 색인을 짓는 `indexToSend`(묶음이 있으면 `libraries`를 React·ReactDOM 18.3.1과 `global`로, 첫 정식 올리기면 `upgraded`가 없을 때만 더한다).
- `record.ts`: `record plan` 보고에 `firstCanonical`·`calls`가 들고, `record index --local --plan --index --at --out` 하위 명령을 더했다(입력과 출력은 티켓의 "결과" 절).
- 결정: 보낼 색인은 새 하위 명령 `record index`가 짓는다(티켓이 이 티켓에 맡긴 결정). `lastChange`는 세션이 적은 색인을 입력으로 받는다. `libraries` 항목의 꼴(`name`, `version`)은 Design System 형식 판 `1793232764-0442`의 `SKILL.md`(Artifact 도구의 `read`로 `type_url`을 읽었다)에서, `global`은 프로브 README의 웹 저장 판 `1793178461-b394`에서 따랐다. 사용자가 남겨 둔 임시 아티팩트 `64VW1b5F8tRcCeTZBwZA29`는 `read`가 "artifact not found"로 끝나 읽지 못했다.
- 시험: `upload.test.ts`에 사례를 더했고 `record-check.test.ts`에 명령 사례 셋. 옛 별칭 48개 사례는 구현 전부터 초록이었다(명세가 말한 그대로). 나머지 열일곱은 구현 전에 빨갰다(`pnpm -C web exec vitest run tools/sync-design-system/upload.test.ts`로 손으로 봤다). `tools/sync-design-system/` 455개 초록, eslint·tsc·prettier 지남(손으로 친 명령).
- 변이: `.scratch/design-card-build/probes/upload_plan_mutations.toml` 스물둘, "변이 22 모두 기대대로"(도구가 찍은 줄). 선례 표의 원문 넷을 옮기고 두 표를 다시 돌렸다. 결과는 두 프로브 README의 2026-10-29 절.

## 번복하거나 고친 것

- 첫 변이 실행에서 표지 넷이 출력에 없었다. 14는 변이가 `_ds_sync.json`을 두 번 넣어 다른 단언이 빨개진 것이라 편집 둘로 바꿨고, 19·20·21은 손으로 넣어 받은 출력의 실패 머리와 `Received` 쪽 차이 줄로 다시 골랐다.
- 옛 변이 표 둘을 파이썬 `write_text`로 고치자 윈도에서 CRLF가 됐다(git 경고로 봤다). 바이트로 LF로 되돌렸다.
- 바이트 나누기 사례는 처음 판이 기록 몫을 지워도 빨개지지 않는 크기라, 둘이 16MiB에 들지만 기록 몫을 더하면 넘는 크기로 바꿨다. 기록이 없을 때 지난 목록대로 지우는 사례를 더했다.

## 셀프 리뷰 (이어받은 세션, 2026-10-30)

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/design-card-build/issues/03-upload-plan-first-canonical.md … 이어받을 상태: 인계: 셀프 리뷰 직전. … 이번 요청 범위: PR과 병합까지"

`/code-review`, 기점 `f6df25c8`(origin/main의 merge-base), 수정 파일 9개, 미추적 2개, 커밋 0개. 표준 축(sonnet·high)과 명세 축 모두 Critical·Major는 없었다.

- 표준 축: 확정 위반 없음(원칙 III 위반 없음). 주장 검증 Minor 여섯(일지의 시험 개수 455, "열일곱", 변이 22는 다시 돌리지 않음, `global` 꼴은 맞음, 16MiB의 출처 문장은 어림, 앞 네 변이의 표지가 흔한 문구), 나누기의 경계(판단 항목), 냄새 넷(`indexToSend`의 불리언 둘, `splitCalls`의 수준 혼합, `record plan`의 `calls` 복사, 변이 표 머리의 "시간 제한" 단정).
- 명세 축: Minor 둘(결과 절의 "한 파일이 한 호출에 들지 않으면 `limit` 오류다"가 틀림: 남은 큰 파일이 중간 호출에는 드는데도 멈춘다. 첫 몫의 예약만 끄는 변이가 없다), Nit 둘(독스트링의 배너 인용 "옮김을 마치라"가 원문에 없다, 변이 표 머리의 "딱").

고친 것:
- 나누기의 경계(두 축). `splitCalls`가 남은 하나를 마지막 몫에 넣지 못하면 중간 몫으로 보내고 마지막 몫은 기록과 색인만 싣게, 첫 항목이 `pending` 기록과 함께 들지 않으면 첫 몫이 기록만 싣게 고쳤다. 고치기 전에 두 사례를 더해 `limit` 오류로 빨간 것을 봤다(`pnpm -C web exec vitest run --project node tools/sync-design-system/upload.test.ts -t <사례>`, 손으로 봤다). 정확히 16MiB인 파일은 이제 중간 호출에 혼자 들어, 멈추는 사례를 16MiB+1로 옮겼다.
- 고친 문장(PR 직전 리뷰에 밀 주장): `upload.ts` `splitCalls` 독스트링의 "그래서 `limit` 오류는 기록도 색인도 싣지 않는 호출에조차 들지 않는 파일에만 난다.", 티켓 결과 절의 같은 뜻 문장, 변이 표 머리의 "앞의 것을 끄면 남은 것이 중간 몫에는 들고 마지막 몫의 예약(경로 둘, 기록·색인 한도)에는 들지 않는 폭에서만 빈 마지막 몫이 더 나고, 뒤의 것을 끄면 빈 몫을 끝없이 쌓는다(어떻게 끝나는지는 돌려 보지 않았다)."
- 변이 넷을 더했다(남은 하나의 길, 첫 몫이 기록만 싣는 길, 첫 몫의 경로 예약, 첫 몫의 바이트 예약). "변이 26 모두 기대대로"(도구가 찍은 줄). 프로브 README의 2026-10-30 절.
- 배너 인용을 명세 33·46줄의 "No move is perfect"로 고쳤다.

남긴 것과 이유:
- `indexToSend`의 불리언 둘: 명세가 정한 서로 독립인 두 변환(묶음이 있으면 `libraries`, 첫 정식 올리기면 `upgraded`)이라 한 함수가 두 일을 하는 신호가 아니다.
- `record plan`의 `calls` 복사: 지워 보니 `readonly UploadCall[]`이 `JsonValue`에 들지 않아 tsc가 빨갰다(`pnpm -C web verify`). 타입 때문에 필요한 줄이라 되돌렸다.
- 앞 네 변이의 표지: `-t`로 그 사례 하나만 돌고, 그 사례에서 그 문구를 낼 수 있는 단언이 불리언 단언 하나뿐이다.
- 16MiB의 출처 문장: 지금 절차 `upload.md`와 명세에서 물려받은 값이고 더 보수적이다. 이 티켓에서 바꾸지 않는다.
- 위 "한 것"의 "455개"와 "열일곱": 셀프 리뷰 표준 축은 반영 전 456개를 봤고, 지금은 사례 둘을 더해 458개다(`pnpm -C web exec vitest run --project node tools/sync-design-system`). "열일곱"은 구현 전 판으로 되돌려 다시 재지 않았다.

다시 돌린 명령: `pnpm -C web verify` 0으로 끝났다. `uv run ruff check .`와 `uv run ruff format --check .`가 통과했다.

## 커밋 전 검증

- `uv run python tools/run_checks.py`: 아홉 검사가 통과하고 pytest가 1 failed, 6005 passed(660초)였다. 실패는 `tests/tools/test_probe_kit.py`의 배출 시험 하나였고, 그 파일을 단독으로 돌리자 15 passed였다.
- 첫 커밋 시도: pre-commit의 pytest만 1 failed(`tests/tools/test_rerun_runner.py`, 905.9초). 그 파일 단독 63 passed.
- 같은 커밋을 SKIP 없이 다시: pytest만 4 failed, 6002 passed(1057.5초). 실패는 `test_probe_kit.py` 하나, `test_rerun_runner.py` 둘, `tests/channel/cli/test_interrupt.py` 하나(Ctrl+C 자식이 30초 안에 끝나지 않음)로 모두 인계에 적힌 시간 민감 시험이다. `test_interrupt.py` 단독 6 passed. 다른 검사(pyright 둘, lint-imports, check-ticket, zizmor, check-type-escapes, check-instructions, run-hooks, web-verify, 표·줄 구분 문자·변이 표 원문)는 두 시도 모두 통과했다.

> 사용자(선택 화면, "커밋 방식"): "pytest만 빼고 커밋" — "SKIP=pytest로 커밋합니다. 다른 검사는 그대로 돌고, 빠진 pytest는 PR의 CI가 다시 돌려 판정합니다. 곧바로 PR로 갈 수 있습니다."

## 인계

세션 컨텍스트가 문턱을 넘은 채 `셀프 리뷰 직전`에 와서 넘긴다. `uv run python tools/run_checks.py` 백그라운드 실행은 끝나기 전에 멈췄다(결과 없음). 새 세션은 셀프 리뷰(`/code-review`, 기점 `origin/main`)부터 하고, 반영 뒤 검증 명령을 모두 돌린 다음 티켓을 `done`으로 바꿔 커밋하고 PR과 병합까지 간다. 티켓의 마무리 체크박스(검증 명령 초록)는 미리 표시했으니 검증으로 확인한다. 이 세션의 지금 제목은 `feature/03-upload-plan-first-canonical`이다.

인계 지시문:

```
다음 작업: .scratch/design-card-build/issues/03-upload-plan-first-canonical.md. 올리기 계획이 첫 정식 올리기를 가르고, 보낼 파일을 호출 몫으로 나누며, 색인의 libraries와 upgraded를 짓는다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/design-card-build/issues/03-upload-plan-first-canonical.md
브랜치: feature/03-upload-plan-first-canonical
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: 일지 docs/journal/2026-10-30-03-design-card-build-upload-plan.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 기점 origin/main, 명세 .scratch/design-card-build/spec.md)부터 한다. 구현·시험·변이 표는 마쳤고 tools/run_checks.py 전체 실행은 결과 없이 멈췄으니 반영 뒤 다시 돌린다. 티켓의 체크박스는 모두 표시했고 Status는 in-progress다(PR 전에 done). 임시 디자인 시스템 아티팩트 64VW1b5F8tRcCeTZBwZA29는 사용자가 남겨 두기로 했다. 지우지 않고 다시 묻지 않는다. 이 PC에서 pre-commit의 pytest는 다른 시간 시험(tests/tools/test_probe_kit.py, tests/tools/test_rerun_runner.py, tests/channel/cli/test_interrupt.py, tests/tools/test_hook_edit_during_commit.py)이 부하에서 한 번씩 막을 수 있다. 단독 실행이 통과하면 SKIP 없이 같은 커밋을 한 번 더 시도하고, SKIP=pytest는 사람에게 묻는다. 일지 docs/journal/2026-10-30-03-design-card-build-upload-plan.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-29T14:34:21Z

## 인계 (커밋 뒤)

이어받은 세션(제목 `feature/03-upload-plan-first-canonical`)이 셀프 리뷰와 반영을 마치고 `d910cecb`를 커밋했다. pre-commit은 사용자가 고른 대로 `SKIP=pytest`로 돌았고 나머지 검사는 통과했다(위 "커밋 전 검증"). 세션 컨텍스트가 문턱을 넘은 채 `커밋 뒤`에 와서 넘긴다. 푸시와 PR은 아직이다. 새 세션은 PR 직전 리뷰(`docs/constitution/operations.md` 리뷰 파이프라인 2)부터 하고, 그 브리프에 위 "셀프 리뷰"의 "고친 문장" 셋을 밀 주장으로 넣는다. pytest를 뺀 커밋이라 PR의 CI pytest 결과를 반드시 본다.

인계 지시문:

```
다음 작업: .scratch/design-card-build/issues/03-upload-plan-first-canonical.md. 올리기 계획이 첫 정식 올리기를 가르고, 보낼 파일을 호출 몫으로 나누며, 색인의 libraries와 upgraded를 짓는다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/design-card-build/issues/03-upload-plan-first-canonical.md
브랜치: feature/03-upload-plan-first-canonical
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: 일지 docs/journal/2026-10-30-03-design-card-build-upload-plan.md 의 "셀프 리뷰", "커밋 전 검증", "인계 (커밋 뒤)"
이어받을 상태: 인계: 커밋 뒤. d910cecb까지 셀프 리뷰 반영, 티켓 done, 검증을 마치고 커밋했다(pre-commit은 사용자가 고른 SKIP=pytest. 실패는 시간 민감 시험 넷이고 단독으로 모두 통과). 남은 단계는 PR 직전 리뷰(밀 주장은 일지 "셀프 리뷰"의 고친 문장 셋), 푸시, PR(/git-pr), 반영과 병합(merge.md)이다. pytest를 뺀 커밋이라 CI의 pytest를 꼭 본다. 임시 디자인 시스템 아티팩트 64VW1b5F8tRcCeTZBwZA29는 사용자가 남겨 두기로 했다. 지우지 않고 다시 묻지 않는다. 일지 docs/journal/2026-10-30-03-design-card-build-upload-plan.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-29T16:35:26Z

## PR 직전 리뷰 (세 번째 세션, 2026-10-30)

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 이어받을 상태: 인계: 커밋 뒤. … 이번 요청 범위: PR과 병합까지"

`coderabbit auth status`가 `Seat: not assigned`라 대체 둘을 돌렸다. `/security-review`를 위해 origin/main(`c04e4fe6`)을 먼저 합쳤다(겹치는 파일 없음, 병합 커밋 `1ef6d301`).

- `/security-review`: 확신도 8 이상의 HIGH·MEDIUM 없음. 입력은 CLI 플래그와 서버의 색인·기록이고, 서버나 기록에서 온 경로로 파일을 열거나 쓰거나 지우는 코드가 없다. `{...index}` 복사는 `Object.prototype`을 바꾸지 않는다. `libraries`는 고정 상수다.
- `bug-perf-review`: 밀 주장 셋 가운데 1·2(`splitCalls` 독스트링과 티켓 결과 절의 "`limit` 오류는 … 호출에조차 들지 않는 파일에만 난다")는 반례가 없었다. 서브에이전트가 `planUpload`를 직접 불러 0개, 1개, 정확히 16MiB(`[[0,0],[1,0],[0,0]]`), 16MiB+1(`limit`), 253·254·255·600개, 16MiB 둘 등의 몫을 봤다. 무한 반복은 없고 파일 20000개에 102ms였다(여기까지 서브에이전트의 보고이고, 이 세션은 다시 돌리지 않았다). 지적 1건(Minor, 유효): 변이 표 머리에서 뒤의 것(`!first`)을 끄면 빈 몫을 끝없이 쌓는다고 적은 문장이 틀렸다. 첫 몫이 아니면 `take`의 예약이 0이라 `taken`이 0일 때 `!fits(1, head.bytes, 0, 0)`이 이미 참이고, 그 변이는 동치다(이 세션이 `upload.ts` 134~151줄을 읽어 확인했다. 변이는 돌려 보지 않았다).

고친 것: 변이 표 머리의 그 문장을 "끄는 변이가 동치라 표에 두지 않는다"와 그 까닭으로 바꿨다. 코드의 중복 조건은 남겼다. 지우면 그 줄을 겨누는 변이("첫 몫이 기록만 싣지 못하면")의 원문을 다시 지어야 하고, 동작은 같다. `tools/mutate.py … --check`가 변이 26 모두 원문이 한 번씩 있다고 찍었다(손으로 봤다).

main이 그사이 `3b78de25`(#429)로 앞서 다시 합쳤고, `tools/sibling_overlap.py`가 main의 최신 일지 2026-10-29-21보다 이 일지가 이름순으로 앞이라고 알려 `--move`로 이 일지를 2026-10-29-20에서 2026-10-30-03으로 옮겼다.
