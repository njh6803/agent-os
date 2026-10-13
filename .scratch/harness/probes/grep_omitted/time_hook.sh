#!/bin/sh
# hook_grep_omitted 한 번의 시간을 등록 모양(tools/launch_hook.py 를 거쳐)으로 잰다(대기열 145).
# 입력은 둘이다. 생략 없는 일치(침묵)와 생략된 일치 줄이 든 결과(알림)다. 일곱 번씩 밀리초와 그 실행이
# 알렸는지(출력에 additionalContext 가 있는지)를 찍는다. 기대와 다르면 1로 끝난다.
# 돌리는 법: 저장소 루트에서 `sh .scratch/harness/probes/grep_omitted/time_hook.sh`. `.venv` 가 있어야 한다.
set -eu
root=$(cd "$(dirname "$0")/../../../.." && pwd)
plain='{"tool_name": "Grep", "tool_response": {"mode": "content", "content": "a.txt:1:PROBE short"}}'
omitted='{"tool_name": "Grep", "tool_response": {"mode": "content", "content": "a.txt:1:PROBE short\na.txt:2:[Omitted long matching line]"}}'
for i in 1 2 3 4 5 6 7; do
  for case in "침묵|$plain" "알림|$omitted"; do
    expected=${case%%|*}
    payload=${case#*|}
    start=$(date +%s%N)
    output=$(printf '%s' "$payload" | uv run --project "$root" --no-sync python "$root/tools/launch_hook.py" hook_grep_omitted.py)
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
