# 2026-10-28 (12) 변이를 돌리는 실행도 표지의 메아리를 보다 (harness 020)

## 시작

세션을 연 지시문의 시작 프롬프트와 범위다. 세션 제목은 `chore/020-mutate-run-echo-check` 이다.

> 사용자: 대기열 502를 티켓 .scratch/harness/issues/020-mutate-run-echo-check.md로 쓰고 한다 (브랜치 chore/020-mutate-run-echo-check, 모델 Opus 5.5 / medium 레벨 스윕의 갈래, 나란히 여는 8 중 2, 이번 요청 범위: PR과 병합까지. 같은 파일을 대상으로 둔 350·455·517 은 이번에 열지 않는다)

`EnterWorktree` 로 `020-mutate-run-echo-check` 워크트리를 만들고 브랜치 이름을 바꿨다. 이 세션은 묶음의 첫 세션이 아니라 `tidy-checkouts` 를 돌지 않았다. 티켓을 쓴 직후 다시 친 `tools/sibling_overlap.py` 에서 겹침이 없었다(이 브랜치의 새 번호: 티켓 020).

## 한 것

- `tools/mutate.py` 의 `_validate`(변이를 돌리는 `measure` 의 1단계)가 원문 확인에 더해 `_echo_problems` 를 본다. 걸리면 `SpecError` 로 기준선 전에 끝나고 `main` 이 "변이 파일 오류(아무 파일도 쓰지 않았다)"와 함께 2로 끝낸다. 전체 실행은 표의 변이 모두를, 고른 실행은 고른 변이만 본다(`_run_table` 이 `select` 한 표를 `measure` 에 넘긴다, 코드 읽기).
- 모듈 독스트링(사용법 끝 문장, 표지 메아리 절, 하는 일 1단계)과 `.claude/rules/probes.md` 첫 항목의 메아리 문장을 맞췄다.
- 시험: `test_변이를_돌리는_실행도_메아리에_걸리면_기준선_전에_끝낸다` 세 갈래(전체, 번호, `--since`). 고치기 전 판에서 셋 다 러너 대역의 `AssertionError: 변이 파일 오류인데 테스트를 돌렸다` 로 빨갰다(`uv run pytest -q tests/tools/test_mutate.py -k 기준선_전에_끝낸다` 를 손으로 쳤다).
- 기존 시험 `test_못_보는_것_첫_실패에서_멈춘_변이는_뒤의_시험만_찍는_표지를_놓쳐_어긋난다` 가 새 판정에 걸렸다. 그 표지 `MARKER-B` 가 시험 파일의 `print('MARKER-B')` 에 글자 그대로 있었다. 시험이 재는 것(`-x` 가 뒤 시험을 돌리지 않아 표지가 없다)은 그대로 두고 `print('MARKER' + '-B')` 로 원문에서 뗐다.
- 변이 표 `.scratch/harness/probes/mutate_run_echo_mutations.toml`(변이 하나).

## 셈

변이 표 가운데 이번 고침으로 전체 실행이 1단계에서 멈출 표: 작업 트리의 142(커밋된 141과 이 티켓의 새 표) 가운데 16, 메아리 161건(세션 스크래치 스크립트가 표마다 `read_spec` 과 `_echo_problems` 를 불러 센 것을 손으로 봤다. 커밋하지 않았다). 가장 많은 표는 `.scratch/token-usage/probes/token_report_mutations.toml`(63)과 `.scratch/token-usage/probes/session_usage_hook_mutations.toml`(26)이다. 그 표는 다시 돌릴 때 표지를 고르거나 메아리가 없는 변이를 번호로 골라 돌린다. 판정은 파일 단위라 같은 파일의 다른 시험에만 있는 글자도 센다(독스트링의 못 보는 것). 그래서 이 수에는 거짓 양성이 섞일 수 있다.

## 검증

- `uv run pytest -q -n 4 tests/tools/test_mutate.py`: 셀프 리뷰 반영 전에 235 passed(손으로 쳤다). 그 전 실행에서 `MARKER-B` 시험 하나가 새 판정에 걸려 빨갰고, 위 한 것의 넷째 줄처럼 고쳤다.
- 변이 표(셀프 리뷰 반영 뒤 커밋 전 작업 트리): `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/mutate_run_echo_mutations.toml` 이 "변이 1 모두 기대대로"를 찍었다(도구 출력, 실패 이름 `…기준선_전에_끝낸다[전체]`). 끝난 뒤 `git diff --stat` 에 변이가 남지 않았다.
- `uv run pyright tools/mutate.py tests/tools/test_mutate.py`: 0 errors(반영 전).
- 카나리아: `tools/sibling_overlap.py` 가 `.claude/rules/probes.md` 를 바꿨다고 알린 여섯을 `tools/canary.py` 로 돌렸다(claude 2.1.302, 실험군은 `7d27ae45` 위의 커밋하지 않은 판, 셀프 리뷰 반영 뒤). `probes_rule`, `probes_rule_kill_and_snapshot`(`--control-commit 528bd257`), `probes_rule_marker_other_reading`, `probes_rule_stream_delete_marker`, `probes_rule_uncommitted_edit` 은 통과 4. `probes_rule_conclusion_hook`(`--control-commit 77ecd319`)은 두 번 돌려 통과 3·실패 1, 통과 2·실패 2였다. 실패 셋은 모두 실험군 회차가 Sonnet 5.5 의 안전 장치 거절(`API Error: … safeguards flagged`)로 답을 내지 못한 것이고, 답한 실험군 회차 셋과 대조군 둘은 모두 통과였다(러너 출력). 거절은 측정이 아니라 더 돌리지 않았다. 이번에 바꾼 것은 첫 항목이고 이 명세가 묻는 것은 셋째 항목이다. 여섯의 `# 최신 결과:` 줄을 고쳤다.
- 나머지 손으로 치는 다섯은 커밋의 pre-commit 으로 갈음한다.
- 첫 커밋 시도의 pre-commit: pytest 만 빨갰다(1111.7초, web-verify 1092.7초. 다른 세션이 함께 돌던 때다). 실패는 이 변경과 무관한 `tests/tools/test_rerun_runner.py::test_같은_갈래가_두_번_든_파일럿의_두_회차가_함께_돌아도_번호가_다르다` 의 `assert 1 == 2`(두 회차가 함께 돈 최대 번호가 1)였고, 그 시험만 홀로 다시 돌리니 통과했다(4.84초, 손으로 쳤다). 부하에서 두 회차가 겹치지 않은 것으로 어림한다. 대기열 후보로 넘긴다.

## 셀프 리뷰

기점 `7d27ae45`, 바뀐 파일 셋, 커밋 0, 미추적 셋(티켓, 변이 표, 이 일지).

- 표준 축: Major 하나. 변이 표의 표지 `기준선_전에_끝낸다[번호]`·`[since]` 는 빨강 기대 pytest 변이에 붙는 `-x` 때문에 출력에 없다(서브에이전트가 같은 모양의 시험을 `pytest -q -x` 로 손으로 돌려 `[전체]` 만 찍힌 것을 봤다. 도구 독스트링의 `-x` 못 보는 것과 맞다). 고쳤다: 표지를 `[전체]` 와 `AssertionError: 변이 파일 오류인데` 로 줄이고 그 까닭을 표 머리 주석에 적었다. Minor: 프로브 README 행이 없다(변이를 돌린 뒤 더한다). 사실 오류: "커밋된 표 142개"는 141개에 이 새 표를 더한 수다. 고쳤다. Nit 둘: `_file_problems + _echo_problems` 의 중복은 `_picked_problems` 로 모았고, 새 시험이 `_원문_확인` 헬퍼로 실행을 부르던 이름 어긋남은 `main` 을 바로 부르게 고쳤다.
- 명세 축: Critical·Major 없음. 같은 수(142·"변이 161개")를 Minor 로 냈고 "메아리 161건"으로 고쳤다. 고른 실행은 `select` 한 표만 `measure` 에 가고, `_validate` 를 부르는 곳은 `measure` 하나라 메아리 판정이 빠지는 길이 없다(서브에이전트가 코드와 grep 으로 봤다). 옛 표현의 잔존 0. 16개 표의 README 재현 명령이 이제 1단계에서 2로 끝난다는 것은 티켓과 이 일지의 셈 절에 적었고, 각 README 행은 고치지 않았다(그 표를 다시 돌릴 때 표지를 고른다).

고친 것 줄의 새 사실 문장(PR 직전 리뷰에 밀 주장으로 넘긴다): "이 브랜치의 작업 트리에 있는 표 142개(커밋된 141개와 이 티켓의 새 표) 가운데 16개가 메아리 161건을 가져", "빨강을 기대한 pytest 변이에는 `-x` 가 붙어 첫 갈래(`[전체]`)에서 멈추므로, 뒤 갈래(`[번호]`, `[since]`)의 이름은 표지로 두지 않는다".
