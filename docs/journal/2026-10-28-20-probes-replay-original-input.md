# 2026-10-28 (20) 다른 날의 결과를 설명하는 측정에 그때의 입력을 다시 넣는 갈래를 더한다 (harness 026)

next-session 지시문으로 연 새 세션이다. 나란히 여는 여덟 가운데 여덟째라 `tidy-checkouts`는 돌지 않았고(묶음의 첫 세션이
돈다), 주 체크아웃에서 브랜치를 따지 않고 워크트리 `026-probes-replay-original-input`에 들어가
`chore/026-probes-replay-original-input`으로 바꿨다.

> 사용자: "대기열 506을 티켓 .scratch/harness/issues/026-probes-replay-original-input.md로 쓰고 한다"

## 세 줄 계획

(1) `.claude/rules/probes.md` 셋째 항목에 양성 대조의 한 꼴(그때 결과를 낸 입력을 글자 그대로 다시 넣는 갈래를 먼저 둔다)과
대기열 506의 사례를 더한다. (2) 대기열 506을 티켓 026으로 닫는다. (3) 계약(`sdk/`, `openapi.json`, 헌법)에는 닿지 않는다.

## 한 것

- 사례는 일지 2026-10-28-08의 320 절에서 옮겼다. 그 일지를 읽었다: 2026-10-16에 거부된 명령 넷은 코드나 heredoc 본문에
  git 명령 글이 들었고, 그 측정은 git 글이 없는 명령만 넣어 "같은 모양이 지나갔다"고 적었다.
- `tools/sibling_overlap.py`가 `probes.md`를 원천으로 든 카나리아 명세 여섯을 알렸다. 이 PR 안에서 통과한 적이 없어
  사전 확인으로 갈음할 수 없으므로, 새 문장의 명세 `.scratch/harness/probes/canary/probes_rule_replay_original_input.toml`을
  더해 일곱을 `tools/canary.py`로 돌렸다(claude 2.1.302, 실험군은 `5ccb51a0` 위의 커밋하지 않은 판). 일곱 모두 통과 4였다.
  `probes_rule_conclusion_hook`은 `--control-commit 77ecd319`, `probes_rule_kill_and_snapshot`은 `--control-commit 528bd257`로
  돌렸다. 결과는 각 명세의 `# 최신 결과:` 줄에 적었다.
- 린트 둘(`ruff check .`, `ruff format --check .`)은 초록이었다.
- `tools/run_checks.py`를 카나리아와 리뷰 서브에이전트 둘이 함께 도는 동안 백그라운드로 돌렸다. pytest가 26분 걸려
  둘이 실패했다. `tests/channel/cli/test_interrupt.py`의 닫기 도중 한 번 누르는 사례(자식이 30초 안에 끝나지 않았다)와
  `tests/tools/test_rerun_runner.py`의 오염 두 번 사례(`run()`이 1)다. 둘만 `uv run pytest -q <두 시험>`으로 다시 치니 통과했다
  (270초). 둘 다 시간에 기대는 시험이고 이 변경은 문서뿐이라 부하가 겹친 탓으로 본다(어림. 부하를 갈라 재지 않았다). 나머지
  검사는 통과였고, 커밋의 pre-commit이 다시 돈다.

## 셀프 리뷰

base `5ccb51a0`, 고친 파일 둘(`probes.md`, 대기열), 미추적 셋(티켓, 카나리아 명세, 이 일지), 커밋 0.

표준 축(sonnet, high): Major 둘, Minor 넷, Nit 둘. 명세 축: Major 하나, Minor 셋, Nit 하나. 두 축이 같은 Major 둘을 냈다.
- Major(두 축): 첫 판의 까닭 문장(다시 내지 못하면 입력 밖의 무엇이 달라진 것이라는 문장)이 닫힌 주장인데, 이 사건의 가드가 같은 꼴에도
  결과가 갈린다(`.claude/agents/bug-perf-review.md` 3단계, `CLAUDE.md` 환경 함정). 유효. 정의 23행을 열어 봤다.
- Major(두 축): 사례가 규칙이 말하는 갈래(그날 입력을 글자 그대로)를 보이지 않는다. 유효. 일지 2026-10-28-08의 밀 주장 1과 정의
  23행에 그날 거부된 짧은 `-c`를 본 세션에서 다시 쳐 다시 거부됐다는 기록이 있었는데 사례가 그것을 빠뜨렸다.
- Minor(두 축): 카나리아를 돌리기 전에 티켓 수용 기준을 [x]로 적었다. 리뷰를 띄운 뒤 일곱이 모두 통과해 지금은 맞다.
- Minor(명세): 대기열 506의 "세 번째 반복이면 계기 훅 후보"가 닫힌 행에 묻힌다. 유효.
- Minor(표준): 일지가 비었다. 이 절과 아래 절로 채웠다.
- Minor(표준): 같은 항목의 "이 항목을 어긴 결론이 세 번 리뷰에서야 잡혔다"가 사례를 더한 뒤에도 그대로다. 보류. 그 문장은 훅을
  더한 까닭으로 대기열 346과 일지 둘을 들어 그때의 셈을 적은 기록이고, 506은 그 훅이 돌지 않는 자리(서브에이전트 정의)의 사건이다.
- Minor(표준): 카나리아 질문이 사례 문장과도 맞을 수 있다. 보류. 그 축이 적었듯 `expect` 두 조각이 규칙 문장에만 있어 거짓 통과는 막힌다.
- Nit(표준): 닫힘 표지의 티켓 경로 백틱, 카나리아 명세를 적지 않음. 둘 다 고쳤다.
- Nit(명세): "같은 모양이 지나갔다"는 정의 원문과 글자를 대 볼 수 없다. 보류. 사례는 그 말을 따옴표로 옮기며 일지 08의 리뷰 절이
  쓴 말을 따랐고, 정의는 그 뒤 고쳐져 원문이 남지 않았다.

고친 것:
- `probes.md` 까닭 문장: "다시 내지 못하면 그날과 지금 사이에 입력 밖의 무엇이 달라졌거나 같은 입력에도 결과가 갈리는 것이라,
  그 갈래를 여러 회차 넣어 둘을 가른다."
- `probes.md` 506 사례: "셀프 리뷰 명세 축이 잡은 뒤에야 그날 거부된 짧은 `-c` 하나를 본 세션에서 글자 그대로 다시 쳐 다시
  거부되는 것을 봤고, git 글이 든 갈래를 더했다. 그 갈래의 `-c`는 지나가, 가드가 같은 꼴에도 결과가 갈린다고 정의를 고쳤다(손으로
  봤다, 일지 2026-10-28-08)"
- 대기열 506 닫힘 표지: 티켓 경로 백틱, 카나리아 명세, "세 번째 반복이면 계기 훅 후보"는 179를 이은 다음 행이 회차와 함께
  이어받는다.
- 카나리아 `probes_rule_replay_original_input.toml`의 둘째 `expect`를 "같은 입력에도 결과가 갈리는 것이라"로 바꿨다.

다시 돌린 것: 일곱 명세의 사전 확인(`tools/canary.py --preflight`, 커밋 대조군 둘은 `--control-commit`과 함께)이 모두 통과했다.
같은 PR에서 같은 claude 판으로 통과한 뒤 원천 본문과 `expect`만 고쳐 `operations.md` 카나리아 항목의 갈음 조건에 맞는다.
각 명세의 `# 최신 결과:` 줄 뒤에 갈음을 덧붙였다. 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다.

PR 직전 리뷰에 밀 주장(셀프 리뷰를 반영하며 새로 쓴 사실 문장): 위 "고친 것"의 `probes.md` 두 문장과 대기열 닫힘 표지.

커밋 `c8615ef6`의 pre-commit은 모두 통과했다(러너 911.98초, ruff 둘과 헌법 판 검사는 `.py`·헌법 파일이 없어 `Skipped`).
ruff 둘은 앞서 손으로 쳐 초록이었다. 인용 대조가 경고 하나를 냈다. 이 일지의 셀프 리뷰 절이 첫 판의 까닭 문장을 따옴표로
옮긴 자리라 따옴표를 떼고 풀어 썼다(커밋하지 않았다).

## 인계 (커밋 뒤)

컨텍스트가 인계 문턱을 넘은 채 `커밋 뒤`에 와서 `hook_handoff` 계기대로 넘긴다. 인계하지 않는 다섯에 들지 않았다(커밋 성공,
요청 범위는 PR과 병합까지, 인계로 연 세션이 아니다, `인계 못함` 줄 없음, `get_session`의 `self`에 `parentSessionId` 없음).
이 세션의 지금 제목은 `chore/026-probes-replay-original-input`이고 `(인계함)`을 붙인다. 번복하거나 고친 것은 셀프 리뷰 절의
"고친 것"이다. 남은 것: 이 일지의 커밋하지 않은 변경(인용 경고 고침과 이 절)을 커밋하고, PR 직전 리뷰(`operations.md` 리뷰
파이프라인 2, 밀 주장은 위), 푸시, PR 열기, 봇 회차, 회고와 `## 다음`, 병합이다.

인계 지시문:

```
다음 작업: 받는 세션이 쓴 .scratch/harness/issues/026-probes-replay-original-input.md(대기열 506)를 커밋 뒤부터 이어 PR과 병합까지 한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 506을 티켓 .scratch/harness/issues/026-probes-replay-original-input.md로 쓰고 한다
브랜치: chore/026-probes-replay-original-input
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-28-20-probes-replay-original-input.md, docs/agents/issue-tracker.md
이어받을 상태: 인계: 커밋 뒤. 커밋 c8615ef6까지 규칙 셋째 항목, 티켓, 대기열 506 닫힘, 카나리아(일곱 모두 통과 4, 셀프 리뷰 반영 뒤 사전 확인으로 갈음), 셀프 리뷰 반영을 했다. 일지의 커밋하지 않은 변경(인용 경고 고침, 인계 절)이 워크트리에 있다. 열린 PR은 없다. 남은 것은 그 커밋, PR 직전 리뷰(밀 주장은 일지 셀프 리뷰 절 끝), 푸시, PR 열기, 봇 회차, 회고와 다음, 병합이다. docs/journal/2026-10-28-20-probes-replay-original-input.md
확인할 선행 조건: 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다. sibling_overlap이 형제 024·025와 대기열의 글자 충돌 후보를 알렸다
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-28T04:16:31Z

## 이어받은 세션

> 사용자: "대기열 506을 티켓 .scratch/harness/issues/026-probes-replay-original-input.md로 쓰고 한다"

인계 지시문대로 워크트리 `026-probes-replay-original-input`에 들어왔다. 일지 변경을 커밋하려 했는데 pre-commit의 pytest가
25분 51초 걸려 시험 10개와 오류 1개로 빨갰다(`test_mutate`, `test_probe_kit`, `test_interrupt`, `test_rerun_*`,
`test_check_ticket`. 커밋 명령의 출력 끝을 손으로 봤다). 앞 세션의 러너가 빨갰던 두 시험(`test_interrupt`, `test_rerun_runner`)이 다시 들었고, 이 커밋은 일지
하나뿐이다. 실패한 일곱 파일만 `uv run pytest -q`로 다시 돌리니 523개가 모두 통과했다(19분 16초, 출력 끝을 손으로 봤다). 걸린
시간으로 보아 다른 세션의 부하가 겹친 탓으로 본다(어림. 부하를 갈라 재지 않았다).

PR 직전 리뷰(`operations.md` 리뷰 파이프라인 2). CodeRabbit CLI는 좌석이 없어 대체 둘을 쓴다. `bug-perf-review`(밀 주장 셋을
원천과 대 보게 했다): 유효 Minor 둘, 보류 Minor 하나, 오탐 0. 밀 주장 셋은 원천과 맞는다고 했다.
- 유효(Minor): 대기열 506 닫힘 표지의 "179를 이은 다음 행이 이어받는다"가 가리킬 열린 행이 없다. 고쳤다: 같은 사건이 다시 나면
  이 행의 처방을 가리켜 새 행을 179의 6회차로 연다.
- 유효(Minor): 까닭 문장에 꺼낸 입력이 온전한지 먼저 본다는 말이 없다. 두었다. 그 축도 문장이 틀리지 않고 필수가 아니라고 했고,
  치는 자리의 차이는 "입력 밖의 무엇"에 든다.
- 보류(Minor): 새 카나리아의 둘째 `expect`는 실행이 아니라 사전 확인으로 갈음했다. 두었다. `operations.md` 카나리아 항목의
  갈음 조건(같은 PR·같은 판에서 통과한 뒤 원천 본문과 `expect`만 고침)에 맞는다.

커밋 `a720e0ac`의 pre-commit은 모두 통과했다(출력을 손으로 봤다). origin/main이 `5ccb51a0` 그대로라 합칠 것 없이 내장
`/security-review`를 돌렸다. 지적 0이다. 바뀐 것이 마크다운과 TOML 명세뿐이고, 그 서브태스크가 `tools/canary.py`를 읽어 명세를
`tomllib`로 읽고 하위 프로세스에 인자를 목록으로 넘긴다고 보고했다(그 보고를 옮긴 것이다).

푸시는 `origin/main`보다 2커밋 뒤처졌다는 훅에 막혔다(#413·#414). `git merge origin/main`이 `.scratch/retro-queue.md`를 충돌
없이 합쳤고, `tools/sibling_overlap.py`가 번호 겹침 없음이라 했다(출력을 손으로 봤다). PR #416을 열었다.

봇 첫 회차(PR #416, main을 합친 머리 `dde8ae8c`. `tools/wait_ci.py`가 모두 통과라 했다): CodeRabbit은 고칠 지적 없음, claude-review는
Minor 둘과 Nit 하나(코멘트를 `gh api`로 읽었다).
- Minor: 새 카나리아 머리 줄이 바꾸기 전 `expect`의 실행 결과와 지금 판의 사전 확인 갈음을 한 줄에 섞었다. 고쳤다: 두 사실을
  나눠 적었다.
- Minor: `probes.md` 506 사례가 일지를 읽지 않으면 뜻이 잡히지 않는다. 보류. 같은 항목의 179 사례도 같은 깊이로 적었고, 이
  항목의 사례는 무엇을 어겼고 어떻게 드러났는지를 함께 적는 꼴이다.
- Nit: 카나리아 명세 여섯에 같은 갈음 문구가 복제됐다. 보류. 봇도 지금 구조에서는 어쩔 수 없다고 했다.

## 회고

후보 둘, 승인 0, 기각 둘, 넘김 0.
- 부하가 겹친 pre-commit에서 시간에 기대는 시험 10개와 오류 1개가 빨갰다(위 이어받은 세션 절). 기각. 대기열 306이 이 종류를
  받아들여 닫았다(ADR 0036). retro 5단계대로 새 사례는 회차를 더하지 않고 이 일지에만 적는다. 앞 세션의 러너에서도 같은 둘이
  빨갰다(한 것 절). 봇 회차의 반영 커밋에서도 같은 둘이 다시 빨갰고(pytest 18분 52초, 출력을 손으로 봤다), 같은 커밋을
  다시 쳤다. 셋째(`test_interrupt` 하나, 13분 45초)와 넷째(`test_rerun_runner` 하나, 26분 47초), 다섯째(`test_interrupt`
  하나, 13분 14초)도 빨갰다(출력을 손으로 봤다). 사용자가 pytest를 CI에 맡기라고 정했다.

> 사용자: "SKIP으로 pytest가 든 parallel-checks만 빼고 커밋해. 빠진 나머지 검사는 손으로 치고, pytest는 푸시 뒤 CI의 python 잡으로 확인한 다음 병합해"
- 뒤처진 채 푸시하려 했다. 기각. 푸시 훅이 그 자리에서 막았다.

만료: `uv run python tools/queue_open_rows.py`와 `--ref origin/main`의 "만료할 행"이 둘 다 없음이었다.

## 다음

harness 026은 이 PR로 닫힌다. 다음은 next-session 결정표의 harness 티켓 PR 줄대로 `plan.md`의 프론티어에서 고른다. 같은 묶음의
형제(021~027 가운데 열린 것)는 각자 도는 중이라 다음 작업에 넣지 않는다.
