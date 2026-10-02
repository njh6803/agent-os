#!/bin/sh
# PreToolUse 시점에 직전 assistant 텍스트가 트랜스크립트에 있는지 잰다(대기열 94의 선행 조건).
#   A1~A3      — 텍스트 ALPHA, Bash 하나, 텍스트 BETA, 한 메시지에 Bash 둘(병렬), 텍스트 OMEGA 로 된 턴.
#                호출마다 훅이 본 트랜스크립트 꼬리에 앞의 텍스트와 자기 tool_use 가 있는지 본다.
#   C_reads    — 텍스트 ALPHA 뒤에 한 메시지에 Read 셋(병렬, 동시에 돌 수 있는 도구). Bash 와 기록 순서가
#                같은지 본다(데스크톱 세션에서 병렬 Read 의 tool_use 와 결과가 번갈아 기록됐다).
#   B_subagent — Agent 도구로 띄운 서브에이전트가 텍스트 SUBTEXT 뒤에 Bash 를 친다. 그 호출의 입력에
#                서브에이전트 표지(agent_id·agent_type)가 오는지, transcript_path 가 어느 파일인지 본다.
# 탐침 훅(`dump_pretool.py`)은 PreToolUse·PostToolUse 에 매처 없이(모든 도구) `--settings` 로만 붙고 막지 않는다.
# A 는 세 번 돌린다(A1·A2·A3). 기록이 쓰이는 때가 경합이면 회차마다 다르다.
#
# 돌리는 법: 저장소 루트에서 `sh .scratch/harness/probes/pretool_text/run.sh <저장소 밖 디렉터리>`.
# `claude` CLI와 인증이 든다(변형마다 haiku 세션 하나). `--setting-sources project,local` 로 사용자 전역
# 훅을 뺀다. 저장소 밖에서 돌려 이 저장소의 프로젝트 훅도 실리지 않는다. 결과는 그 디렉터리의
# `<변형>.pretool.jsonl`(훅이 본 것)과 `<변형>.jsonl`(claude -p 의 stream-json)이다.
set -eu
work=${1:?저장소 밖 디렉터리를 넘긴다}
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../../.." && pwd)
mkdir -p "$work"
work=$(cd "$work" && pwd)
hook="uv run --project \\\"$root\\\" --no-sync python \\\"$here/dump_pretool.py\\\""
cat > "$work/settings.json" <<EOF
{"hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": "$hook", "timeout": 30}]}],
 "PostToolUse": [{"hooks": [{"type": "command", "command": "$hook", "timeout": 30}]}]}}
EOF
base="--setting-sources project,local --strict-mcp-config --settings $work/settings.json --model haiku"
base="$base --output-format stream-json --verbose --max-turns 8"
cd "$work"

run() {
  name="$1"
  prompt="$2"
  shift 2
  rm -f "$work/$name.pretool.jsonl"
  # 프롬프트는 stdin 으로 준다. `--allowed-tools` 뒤에 두면 가변 인자가 삼킨다(canary_init).
  # shellcheck disable=SC2086
  printf '%s' "$prompt" | PROBE_LOG="$work/$name.pretool.jsonl" claude -p $base "$@" \
    > "$work/$name.jsonl" 2> "$work/$name.err" || true
  echo "== $name"
  cat "$work/$name.pretool.jsonl" 2>/dev/null || echo "  훅이 돌지 않았다"
}

for n in 1 2 3; do
run "A$n" "Follow these steps exactly, in order. 1) Write the single word ALPHA as text. \
2) Call Bash with: echo one. 3) Write the single word BETA as text. 4) In one single message, call Bash \
twice in parallel: echo two, and echo three. 5) Write the single word OMEGA as text." \
  --tools Bash --allowed-tools 'Bash(echo *)'
done

for f in a b c; do echo "$f" > "$work/$f.txt"; done
run C_reads "Write the single word ALPHA as text. Then, in one single message, call the Read tool three \
times in parallel on these files: $work/a.txt, $work/b.txt, $work/c.txt. Then write the single word OMEGA." \
  --tools Read --allowed-tools Read

run B_subagent "Write the single word ALPHA as text. Then call the Agent tool once with subagent_type \
general-purpose and this prompt: 'Write the single word SUBTEXT as text, then call Bash with: echo sub, \
then reply DONE.' Then write the single word OMEGA as text." \
  --tools Bash,Agent --allowed-tools 'Bash(echo *)' Agent
