#!/bin/sh
# 훅 등록의 실행 래퍼(tools/launch_hook.py, 대기열 91)가 실제 Claude Code 세션에서 어떻게 도는지 변형마다 잰다.
#   A_registered      — 저장소의 등록 그대로(등록은 모두 래퍼를 거친다). Bash 가 돈다.
#   B_missing_wrapped — 없는 훅을 래퍼로 등록한 것을 더한다. 막지 않고 Bash 가 돈다.
#   C_missing_direct  — 같은 없는 훅을 옛 모양(`python <훅 경로>`)으로 등록한 것을 더한다. 대조군이고 막힌다.
#   D_firing          — 저장소의 등록 그대로 맨 `python` 을 부른다. 래퍼를 거친 hook_bash_python_stub 이 막는다.
#   E_notice_model    — B 와 같은 등록에서 모델에게 그 호출에 붙은 훅 알림의 마지막 문장을 묻는다(대기열 93).
#                       래퍼는 모델에게만 할 일 한 문장(`MODEL_SUFFIX`)을 더하므로, 그 문장을 옮기면
#                       additionalContext 가 닿은 것이다. 사용자에게 간 systemMessage 는 `사용자 알림` 줄이다.
#   F_notice_stop     — 없는 훅을 래퍼로 Stop 에 등록한 것을 더한다. 사용자 알림만 오고 대화가 이어지지 않는다
#                       (답 줄이 하나다).
#   G_context_stop    — F 의 대조군. Stop 에 additionalContext 를 한 번 내는 훅(`stop_context_hook.py`)을 더한다.
#                       대화가 이어지면 답 줄이 둘이다. 그 훅이 받은 `stop_hook_active` 는 `G_stop_payloads.txt` 다.
# A·B 가 돌면 훅 명령의 `${CLAUDE_PROJECT_DIR}` 이 래퍼가 있는 이 체크아웃을 가리킨 것이다(아니면 래퍼를 못 찾아
# 2로 끝나 막힌다).
#
# 돌리는 법: 저장소 루트에서 `sh .scratch/harness/probes/hook_registration/run.sh <출력 디렉터리>`.
# `claude` CLI와 인증이 든다. 변형마다 haiku 세션 하나다. `--setting-sources project,local` 이 사용자 설정(전역
# Stop 훅)을 빼고, `--settings` 의 훅이 실린 것은 C 가 막히는 것으로 본다(프로젝트의 훅이 함께 남는지는 재지 않는다). 요약은
# `summarize.py` 가 Bash 호출의 명령과 도구 결과만 골라 찍는다.
set -eu

out="${1:?출력 디렉터리를 준다}"
mkdir -p "$out"
out="$(cd "$out" && pwd)"
here="$(cd "$(dirname "$0")" && pwd)"
base="--setting-sources project,local --strict-mcp-config --model haiku --output-format stream-json --verbose --max-turns 3 --tools Bash"

ask_result="그 뒤 도구 결과를 한국어 한 줄로 옮긴다."
ask_notice="그 뒤 그 호출에 붙어 온 훅 알림이나 시스템 리마인더가 있으면 그 마지막 문장을 그대로 옮기고, 없으면 '알림 없음' 이라고 한국어 한 줄로 답한다."

run() {
  name="$1"
  command="$2"
  ask="$3"
  shift 3
  prompt="Bash 도구로 \`$command\` 를 한 번만 실행한다. 다른 명령은 치지 않는다. $ask"
  # 프롬프트는 stdin으로 준다. `--tools`·`--allowed-tools`·`--settings` 뒤에 두면 가변 인자가 삼킨다(canary_init).
  # shellcheck disable=SC2086
  printf '%s' "$prompt" | claude -p $base --allowed-tools "Bash($command)" "$@" \
    > "$out/$name.jsonl" 2> "$out/$name.err" || true
}

run A_registered "echo canary-A" "$ask_result"
run B_missing_wrapped "echo canary-B" "$ask_result" --settings "$here/missing_wrapped.json"
run C_missing_direct "echo canary-C" "$ask_result" --settings "$here/missing_direct.json"
run D_firing "python --version" "$ask_result"
run E_notice_model "echo canary-E" "$ask_notice" --settings "$here/missing_wrapped.json"
# shellcheck disable=SC2086
printf '%s' "도구를 쓰지 않고 '확인했습니다' 라고만 답한다." | claude -p $base --settings "$here/missing_stop_wrapped.json" \
  > "$out/F_notice_stop.jsonl" 2> "$out/F_notice_stop.err" || true
rm -f "$out/G_stop_payloads.txt"
# shellcheck disable=SC2086
printf '%s' "도구를 쓰지 않고 '확인했습니다' 라고만 답한다." | PROBE_LOG="$out/G_stop_payloads.txt" \
  claude -p $base --settings "$here/stop_context.json" > "$out/G_context_stop.jsonl" 2> "$out/G_context_stop.err" || true

uv run python "$here/summarize.py" "$out"
echo "G 의 Stop 입력:"
cat "$out/G_stop_payloads.txt" 2>/dev/null || echo "  없음(훅이 돌지 않았다)"
