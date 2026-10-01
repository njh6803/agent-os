#!/bin/sh
# Stop 훅이 받는 입력을 잰다. 저장소 밖의 빈 디렉터리에서 `claude -p` 를 돌리고 탐침 훅을
# `--settings` 로만 붙인다. `--setting-sources project,local` 로 사용자 전역 훅(Stop 알림 등)을
# 뺀다. 프롬프트는 텍스트 블록 둘 사이에 도구 호출 하나를 끼운 턴이라, `last_assistant_message`
# 가 턴 전체인지 마지막 텍스트인지 가른다.
#
# 쓰는 법: 저장소 루트에서 `sh .scratch/harness/probes/stop_payload/run.sh <저장소 밖 디렉터리>`.
# 결과는 그 디렉터리의 `stop.jsonl`(훅이 받은 것)과 `out.json`(claude -p 의 결과)이다.
set -eu
work=${1:?저장소 밖 디렉터리를 넘긴다}
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../../.." && pwd)
mkdir -p "$work"
rm -f "$work/stop.jsonl"
hook="uv run --project \\\"$root\\\" --no-sync python \\\"$here/dump_stop.py\\\" \\\"$work/stop.jsonl\\\""
cat > "$work/settings.json" <<EOF
{"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "$hook", "timeout": 30}]}]}}
EOF
cd "$work"
claude -p --setting-sources project,local --settings "$work/settings.json" --model haiku \
  --allowed-tools 'Bash(echo hi)' --output-format json \
  "Write the single word ALPHA. Then run the Bash command: echo hi. Then write the single word OMEGA." \
  > "$work/out.json"
cat "$work/stop.jsonl"
