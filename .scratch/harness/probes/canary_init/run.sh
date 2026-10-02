#!/bin/sh
# 카나리아 세션(operations.md 환경 규약 상세)의 init 이벤트에 무엇이 실리는지 변형마다 잰다.
# 대기열 85 — `--tools Skill`로 좁혀도 claude.ai 커넥터가 실렸다(일지 2026-10-01-08).
#
# 돌리는 법: 저장소 루트에서 `sh .scratch/harness/probes/canary_init/run.sh <출력 디렉터리>`.
# `claude` CLI와 인증이 든다. 변형마다 haiku 호출 하나다. 출력 디렉터리에는 변형별 stream-json이
# 남고, 요약은 `summarize.py`가 init의 `tools`·`mcp_servers`·`skills`만 골라 찍는다.
set -eu

out="${1:?출력 디렉터리를 준다}"
mkdir -p "$out"
out="$(cd "$out" && pwd)"
here="$(cd "$(dirname "$0")" && pwd)"
prompt="OK라고만 답한다."
base="--setting-sources project,local --model haiku --output-format stream-json --verbose --max-turns 1"

run() {
  name="$1"
  shift
  # 프롬프트는 stdin으로 준다. `--tools`·`--mcp-config`는 가변 인자라 뒤의 인자를 삼킨다(첫 판에서
  # 프롬프트가 도구 이름과 설정 파일 경로로 읽혔다).
  # shellcheck disable=SC2086
  printf '%s' "$prompt" | claude -p $base "$@" > "$out/$name.jsonl" 2> "$out/$name.err" || true
}

run A_skill --tools Skill
run B_skill_strict --tools Skill --strict-mcp-config
run C_skill_strict_empty --tools Skill --strict-mcp-config --mcp-config '{"mcpServers":{}}'
ENABLE_CLAUDEAI_MCP_SERVERS=false run D_skill_env --tools Skill
run E_read_strict --tools Read --disallowed-tools 'Read(./.claude/**)' --strict-mcp-config

uv run python "$here/summarize.py" "$out"
