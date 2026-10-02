#!/bin/sh
# hook_midturn_korean 한 번의 시간을 래퍼 모양(tools/launch_hook.py 를 거쳐)으로 잰다.
#   found   — 트랜스크립트의 마지막 tool_use 를 자기 호출로 준다(끝의 TAIL_BYTES 를 읽고 판정한다).
#   absent  — 없는 id 를 준다(WAIT_SECONDS 까지 다시 읽고 지나간다 — 병렬 첫 호출의 상한).
#   subagent — agent_id 를 준다(트랜스크립트를 읽지 않는다).
# 다섯 번씩 돌려 밀리초를 찍는다.
# 쓰는 법: 저장소 루트에서 `sh .scratch/harness/probes/pretool_text/time_hook.sh <트랜스크립트 경로>`.
# 큰 트랜스크립트를 준다(2026-10-02 에 이 저장소의 가장 큰 것이 31MB 였다).
set -eu
root=$(cd "$(dirname "$0")/../../../.." && pwd)
transcript=${1:?트랜스크립트 경로를 넘긴다}
# 훅의 파이썬이 그 경로를 파일로 보지 못하면(Git Bash 의 /c/… 모양) 훅이 파일 없는 길로 바로 끝나 세
# 경우가 모두 같은 값을 낸다. 그때는 재지 않고 멈춘다(셀프 리뷰가 잡았다). 경로는 훅처럼 stdin 으로
# 넘긴다 — 명령 인자로 넘기면 Git Bash 가 /c/… 를 C:/… 로 바꿔 줘 가드가 지나간다.
if ! printf '%s' "$transcript" | uv run --project "$root" --no-sync python -c \
  "import pathlib, sys; sys.exit(0 if pathlib.Path(sys.stdin.read()).is_file() else 1)"; then
  echo "파이썬이 파일로 보지 못하는 경로다: $transcript — C:/… 모양으로 준다" >&2
  exit 1
fi
last_id=$(grep -o '"type":"tool_use","id":"[^"]*"' "$transcript" | tail -1 | sed 's/.*"id":"//; s/"$//')
echo "마지막 tool_use: ${last_id:-없음}, 크기 $(wc -c < "$transcript") 바이트"
for label in found absent subagent; do
  case $label in
    found) extra=""; id=$last_id ;;
    absent) extra=""; id="toolu_absent" ;;
    subagent) extra=', "agent_id": "a1"'; id=$last_id ;;
  esac
  payload="{\"hook_event_name\": \"PreToolUse\", \"tool_use_id\": \"$id\", \"transcript_path\": \"$transcript\"$extra}"
  for i in 1 2 3 4 5; do
    start=$(date +%s%N)
    printf '%s' "$payload" | uv run --project "$root" --no-sync python "$root/tools/launch_hook.py" \
      hook_midturn_korean.py > /dev/null
    end=$(date +%s%N)
    echo "$label $(( (end - start) / 1000000 ))ms"
  done
done
