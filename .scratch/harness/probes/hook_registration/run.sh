#!/bin/sh
# 훅 등록의 실행 래퍼(tools/launch_hook.py, 대기열 91)가 실제 Claude Code 세션에서 어떻게 도는지 변형마다 잰다.
#   A_registered      — 저장소의 등록 그대로. 래퍼를 거친 훅 열하나 아래에서 Bash 가 돈다.
#   B_missing_wrapped — 없는 훅을 래퍼로 등록한 것을 더한다. 막지 않고 Bash 가 돈다.
#   C_missing_direct  — 같은 없는 훅을 옛 모양(`python <훅 경로>`)으로 등록한 것을 더한다. 대조군이고 막힌다.
#   D_firing          — 저장소의 등록 그대로 맨 `python` 을 부른다. 래퍼를 거친 hook_bash_python_stub 이 막는다.
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

run() {
  name="$1"
  command="$2"
  shift 2
  prompt="Bash 도구로 \`$command\` 를 한 번만 실행한다. 다른 명령은 치지 않는다. 그 뒤 도구 결과를 한국어 한 줄로 옮긴다."
  # 프롬프트는 stdin으로 준다. `--tools`·`--allowed-tools`·`--settings` 뒤에 두면 가변 인자가 삼킨다(canary_init).
  # shellcheck disable=SC2086
  printf '%s' "$prompt" | claude -p $base --allowed-tools "Bash($command)" "$@" \
    > "$out/$name.jsonl" 2> "$out/$name.err" || true
}

run A_registered "echo canary-A"
run B_missing_wrapped "echo canary-B" --settings "$here/missing_wrapped.json"
run C_missing_direct "echo canary-C" --settings "$here/missing_direct.json"
run D_firing "python --version"

uv run python "$here/summarize.py" "$out"
