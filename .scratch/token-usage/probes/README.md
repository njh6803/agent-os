# 토큰 사용 명세의 프로브

`.scratch/token-usage/spec.md`가 정한 값(큰 결과 알림의 문턱, 인계의 단계 경계)과 ADR 0033 이력 2026-10-16이 든 수를 낸다.
ADR 0033 본문의 수는 `.scratch/harness/probes/token_usage/`가 냈다.

| 프로브 | 무엇을 재나 | 근거로 드는 곳 | 다시 돌 때 |
|---|---|---|---|
| `measure.py results <시간>` | 이 저장소의 Read·Bash·PowerShell 결과 글자 수 분포와, 범위 없이 받은 결과가 문턱(1만~4만 자)을 넘은 수·글자의 몫·기록 항목 무게의 몫 | 명세 "큰 결과 알림 훅" | 저장소 루트에서 `PYTHONUTF8=1 uv run python .scratch/token-usage/probes/measure.py results 168`. 이 PC의 `~/.claude/projects/`(폴더 이름 `C--project-agent`로 시작) |
| `measure.py boundaries <시간>` | 메인 세션 컨텍스트가 20만을 넘은 뒤 처음 오는 경계의 종류, 그 지점의 세션 컨텍스트, 그 뒤 환산 비용. ADR 0033의 경계(커밋, PR 열기)와 셀프 리뷰 시작을 더한 경계를 견준다 | 명세 Problem Statement와 "인계 훅", ADR 0033 이력 2026-10-16 | 같은 자리에서 `... measure.py boundaries 168`. 단가표는 `.scratch/harness/probes/session_cost/costs.py` |

| `large_result/run.py`, `large_result/payloads.jsonl` | PostToolUse 훅이 Read·Bash·PowerShell에서 받는 `tool_response`의 모양과, `hook_large_result`의 `result_chars`가 그 출력에서 셈한 글자 수가 같은 호출의 기록 `tool_result` 본문 길이와 맞는지(티켓 06). `run`이 저장소 밖에 픽스처(1200줄 파일, 한글 파일, 1×1 그림)를 짓고 탐침 훅(`dump_posttool.py`, 페이로드 그대로)만 붙인 `claude -p`(haiku)에 여덟 호출을 차례로 시킨 뒤, 페이로드마다 기록의 본문 길이·앞뒤 200자·그림 블록 여부를 붙여 `payloads.jsonl`에 쓴다(`--save`면 이 디렉터리로). `judge`는 여덟 호출이 한 번씩 기록과 함께 있을 때 측정으로 보고, 셈이 기록과 다르면 기대한 차이(`EXPECT_DIFF`) 밖일 때 1로 끝난다 | `tools/hook_large_result.py` 독스트링의 크기 셈, 파일로 옮겨진 출력, stderr 이음새. `tests/tools/test_hook_large_result.py`의 저장한 페이로드 시험 둘. `tools/hook_payloads.toml`의 결과 객체 모양 | 저장소 루트에서 `uv run python .scratch/token-usage/probes/large_result/run.py run <저장소 밖 디렉터리> [--save]`(haiku 세션 하나), 다시 판정만 하면 `... run.py judge`. 2026-10-16(claude 2.1.300) 결과: Read의 `tool_response` 키는 `type`·`file`이고 `file.content`에 줄마다 `<줄 번호>\t`를 붙인 길이가 기록과 같았다(범위 없는 1200줄 46991자, 끝 줄바꿈 뒤의 빈 1201번 줄까지. 범위 준 50줄 2049자, 한글 425자). 그림은 `type`이 `image`이고 기록 본문은 그림 블록뿐이라 0자였다. Bash의 키는 `stdout`·`stderr`·`interrupted`·`isImage`·`noOutputExpected`이고 `stdout`이 기록과 같았다(`seq 1 2000` 8892자, 끝 줄바꿈 없음). stderr로 쓴 줄도 `stdout`에 합쳐 왔고 `stderr`는 비었다(17자). `seq 1 8000`(38893자)은 `persistedOutputPath`·`persistedOutputSize`(38893)가 붙고 `stdout`은 앞 30000자로 잘렸으며, 기록 본문은 `<persisted-output>`으로 싼 경로와 미리보기 2323자였다. PowerShell 키는 `isImage`까지 넷이고 `stdout`이 기록과 같았다(CRLF 줄, 28891자). 판정 0, 기대한 차이는 파일로 옮겨진 것 하나다 |
| `large_result/notice.py` | `hook_large_result`의 알림이 실제 세션의 모델에게 닿는지. B는 등록 모양의 실제 훅과 탐침 훅을 붙여 46991자 Read 뒤 훅 알림의 첫 문장을 묻고, C는 425자 Read의 대조군이다. 탐침 기록이 지시한 범위 없는 Read 하나일 때 측정이고, 모델의 답으로 판정한다(stream-json에는 훅의 additionalContext가 실리지 않는다, `.scratch/harness/probes/webfetch_payload/`) | `tools/hook_large_result.py`의 `LEAD`, `.claude/rules/tools.md`의 새 훅이 함께 하는 넷 | `uv run python .scratch/token-usage/probes/large_result/notice.py <저장소 밖 디렉터리>`(haiku 세션 둘, `--judge`는 다시 판정만). 2026-10-16(claude 2.1.300) 결과: B의 답은 훅의 첫 문장을 옮겼고, C의 답은 "알림 없음"이었다 |
| `large_result/time_hook.sh` | 훅 한 번의 시간을 등록 모양(래퍼를 거쳐)으로 짧은 Bash(침묵), 1만 자 넘는 Bash(알림), 2만 자 넘는 Read(알림)에 일곱 번씩 잰다. 기대와 다르면 1로 끝난다 | `.claude/rules/tools.md` 시간 문단의 `hook_large_result` 문장 | `sh .scratch/token-usage/probes/large_result/time_hook.sh`(`.venv`가 있어야 한다). 2026-10-16 결과(이 PC, 워크트리): 스물하나 모두 기대대로였고 Bash 침묵 352~1034ms, Bash 알림 334~1064ms, Read 알림 329~752ms, 열일곱은 501ms 이하였다. 바로 뒤 `.scratch/harness/probes/grep_omitted/time_hook.sh`도 381~864ms로 그 행의 기록(258~523ms)보다 느렸다. 다른 세션이 여럿 돌던 때다 |
| `large_result_hook_mutations.toml` | `tools/hook_large_result.py`의 문턱(이상으로 바꾸기, 두 값 올리기, Read에 셸 문턱), 범위 판정(offset·limit 하나씩 빼기, 없애기), 셈(줄 번호 접두, startLine, 끝 줄바꿈 뒤의 빈 줄, 파일로 옮겨진 출력, 그림 셸 출력, stderr, 글이 아닌 Read)과 settings.json 매처를 하나씩 깬 변이 열다섯과 대조군 하나(알림 문구의 "약"은 시험이 재지 않는다) | `tests/tools/test_hook_large_result.py`가 무엇을 재는지 | 저장소 루트에서 `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/token-usage/probes/large_result_hook_mutations.toml`. 2026-10-16 결과: 열여섯 모두 기대대로였다 |

표지, 판정의 정의(훅보다 넓은 커밋 판정 포함), 못 보는 것은 `measure.py` 독스트링이 원천이다.

## 결과 (2026-10-16 17:14 UTC, 이 PC, 창 168시간)

두 하위 명령 모두 표지를 지나 0으로 끝났다. 같은 날 16:38 UTC에 돌린 첫 판은 셀프 리뷰를 이름의 끝(`code-review`)으로
갈랐고 불리언 인자가 있었다. 명세의 셀프 리뷰를 반영해 판정을 인계 훅의 것과 맞춘 판이 아래다. 그 뒤 PR 직전 버그 리뷰를
반영해 줄바꿈 없이 잘린 마지막 줄을 넘기게 고쳤다. 아래 실행은 그 전 판이 예외 없이 끝난 것이라 그런 줄이 없었고, 수는
같다.

**results 168**: 메인 세션 876개, 서브에이전트 399개. 범위(`offset`·`limit`)를 주지 않은 결과만 문턱과 견줬다. 무게의 분모는
기록에 남은 항목이다(독스트링).

| 도구(메인 세션) | 결과 | 중앙값 | 99% | 문턱 | 넘은 결과 | 그 도구 글자의 몫 | 기록 항목 무게의 몫 |
|---|--:|--:|--:|--:|--:|--:|--:|
| Read | 3,771(범위 준 것 1,719) | 2,933자 | 43,529자 | 1만 | 483 | 50.4% | 5.43% |
| Read | | | | 2만 | 275 | 38.5% | 3.43% |
| Read | | | | 3만 | 150 | 26.1% | 1.70% |
| Bash | 15,893 | 175자 | 10,053자 | 1만 | 164 | 15.8% | 3.10% |
| Bash | | | | 2만 | 10 | 1.6% | 0.42% |
| PowerShell | 363 | 100자 | 2,533자 | 1만 | 1 | 12.8% | 0.03% |

메인 세션에서는 넘은 결과의 수와 세션·대상 쌍의 수가 모든 문턱에서 같았다. 같은 세션에서 같은 대상(파일, 명령)이 문턱을
두 번 넘은 일이 없었다. 서브에이전트에서는 1만 자 Read에서 한 번 있었다. 서브에이전트는 Read 2만 자를 넘은 것이 161개, Bash
1만 자를 넘은 것이 402개였다. Bash 결과의 최대는 메인 세션 24,463자, 서브에이전트 29,581자였다.

**boundaries 168**: 창 안에서 시작한 메인 세션 793개, 모델 호출 22,481회, 환산 비용 $2,886.72(단가표 밖 0회). 20만을 넘지 않은
세션 708개, 40만을 넘은 세션 75개. 20만을 넘은 세션은 85개다.

| 규칙 | 20만을 넘은 뒤 처음 온 것 | 세션 | 그 뒤 비용 |
|---|---|--:|--:|
| ADR 0033(커밋, PR 열기) | 커밋(PR을 열기 전) | 78 | $1,468.01 |
| ADR 0033(커밋, PR 열기) | 경계 없음 | 7 | $52.09 |
| 셀프 리뷰 시작을 더함 | 셀프 리뷰 시작 | 66 | $1,612.16 |
| 셀프 리뷰 시작을 더함 | 커밋(PR을 열기 전) | 13 | $243.36 |
| 셀프 리뷰 시작을 더함 | 경계 없음 | 6 | $39.34 |

| 규칙 | 문턱에서 그 경계까지 호출 중앙값 | 그 사이 40만을 넘은 세션 | 그 경계의 세션 컨텍스트 중앙값 |
|---|--:|--:|--:|
| ADR 0033(커밋, PR 열기) | 98 | 49 | 418,970 |
| 셀프 리뷰 시작을 더함 | 55 | 21 | 327,338 |

모든 경계(20만을 넘었는지와 상관없이)에서 잰 세션 컨텍스트 중앙값은 PR을 열기 전 커밋(216개) 477,328, 그 세션이 PR을 연 뒤의
커밋(194개) 584,724, PR 열기(78개) 524,999, 셀프 리뷰 시작(101개) 297,143이었다. 모음이 서로 달라 한 세션 안에서 얼마나
늘었는지는 이 수로 말할 수 없다.

"그 사이 40만을 넘은 세션"은 지금의 기록(자동 압축 약 96.7만)에서 세션 컨텍스트가 40만을 넘은 것이다. 자동 압축 창을 40만으로
두면 그 세션은 경계보다 압축이 먼저 온다(어림. 압축 뒤의 경로는 재지 않았다). "그 뒤 비용"은 인계했다면 새 세션이 맡았을
몫이고, 새 세션에서 얼마가 될지는 재지 않았다.
