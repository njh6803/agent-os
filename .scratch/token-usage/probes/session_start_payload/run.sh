#!/bin/sh
# SessionStart 훅이 받는 입력을 대화형 세션과 `claude -p` 세션에서 잰다(티켓 04의 헤드리스 가르기).
# 탐침 훅(`dump_session_start.py`)을 `--settings` 로만 붙인다. 헤드리스 갈래는 저장소 밖의 빈
# 디렉터리에서 `--setting-sources project,local` 로 사용자 전역 훅을 빼고 돈다(선례
# `.scratch/harness/probes/stop_payload/run.sh`). 대화형 갈래는 이 스크립트가 설정만 쓰고 명령을
# 찍는다. 그 명령을 사람이나 세션이 터미널에서 대화형으로 띄우고, 시작 화면이 뜨면 프롬프트를 보내지
# 않고 끈다. 대화형은 신뢰한 폴더에서만 훅이 돌므로 그 명령은 저장소 루트에서 띄운다.
#
# 쓰는 법: 저장소 루트에서 `sh .scratch/token-usage/probes/session_start_payload/run.sh <저장소 밖 디렉터리>`.
# 결과는 그 디렉터리의 `start.jsonl`(훅이 받은 것, 갈래마다 한 줄)과 `out.json`(claude -p 의 결과)이다.
set -eu
work=${1:?저장소 밖 디렉터리를 넘긴다}
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../../.." && pwd)
mkdir -p "$work"
work=$(cd "$work" && pwd)
rm -f "$work/start.jsonl"
for label in headless interactive; do
  hook="uv run --project \\\"$root\\\" --no-sync python \\\"$here/dump_session_start.py\\\" \\\"$work/start.jsonl\\\" $label"
  cat > "$work/settings-$label.json" <<EOF
{"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "$hook", "timeout": 30}]}]}}
EOF
done
(
  cd "$work"
  claude -p --setting-sources project,local --settings "$work/settings-headless.json" --model haiku \
    --output-format json "Reply with the single word OK." > "$work/out.json"
)
echo "대화형 갈래: 저장소 루트에서 claude --settings \"$work/settings-interactive.json\""
cat "$work/start.jsonl"
