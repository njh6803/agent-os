#!/bin/sh
# hook_webfetch_summary 한 번의 시간을 등록 모양(tools/launch_hook.py 를 거쳐)으로 잰다(대기열 209).
# 입력은 둘이다. 본문을 그대로 돌려준 결과(침묵)와 요약(알림)이다. 일곱 번씩 밀리초와 그 실행이
# 알렸는지(출력에 additionalContext 가 있는지)를 찍는다. 기대와 다르면 1로 끝난다.
# 돌리는 법: 저장소 루트에서 `sh .scratch/harness/probes/webfetch_payload/time_hook.sh`. `.venv` 가 있어야 한다.
set -eu
root=$(cd "$(dirname "$0")/../../../.." && pwd)
passthrough='{"tool_name": "WebFetch", "tool_response": {"bytes": 17, "code": 200, "result": "# Hooks reference"}}'
summary='{"tool_name": "WebFetch", "tool_response": {"bytes": 268811, "code": 200, "result": "# Hooks reference"}}'
for i in 1 2 3 4 5 6 7; do
  for case in "침묵|$passthrough" "알림|$summary"; do
    expected=${case%%|*}
    payload=${case#*|}
    start=$(date +%s%N)
    output=$(printf '%s' "$payload" | uv run --project "$root" --no-sync python "$root/tools/launch_hook.py" hook_webfetch_summary.py)
    end=$(date +%s%N)
    case $output in
      *additionalContext*) actual=알림 ;;
      *) actual=침묵 ;;
    esac
    echo "$i $expected $(( (end - start) / 1000000 ))ms $actual"
    if [ "$actual" != "$expected" ]; then
      echo "실패: 기대는 $expected 이다" >&2
      exit 1
    fi
  done
done
