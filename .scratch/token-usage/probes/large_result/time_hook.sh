#!/bin/sh
# hook_large_result 한 번의 시간을 등록 모양(tools/launch_hook.py 를 거쳐)으로 잰다(티켓 06).
# 입력은 셋이다. 짧은 Bash 출력(침묵), 1만 자를 넘는 Bash 출력(알림), 2만 자를 넘는 범위 없는 Read(알림)다.
# 일곱 번씩 밀리초와 그 실행이 알렸는지(출력에 additionalContext 가 있는지)를 찍는다. 기대와 다르면 1로 끝난다.
# 돌리는 법: 저장소 루트에서 `sh .scratch/token-usage/probes/large_result/time_hook.sh`. `.venv` 가 있어야 한다.
set -eu
root=$(cd "$(dirname "$0")/../../../.." && pwd)
long=$(printf 'x%.0s' $(seq 1 10001))
small='{"tool_name": "Bash", "tool_input": {"command": "echo hi"}, "tool_response": {"stdout": "hi", "stderr": "", "isImage": false}}'
bash_big='{"tool_name": "Bash", "tool_input": {"command": "seq"}, "tool_response": {"stdout": "'$long'", "stderr": "", "isImage": false}}'
read_big='{"tool_name": "Read", "tool_input": {"file_path": "C:/x.txt"}, "tool_response": {"type": "text", "file": {"content": "'$long$long'", "startLine": 1}}}'
for i in 1 2 3 4 5 6 7; do
  for case in "Bash 침묵|$small" "Bash 알림|$bash_big" "Read 알림|$read_big"; do
    expected=${case%%|*}
    payload=${case#*|}
    start=$(date +%s%N)
    output=$(printf '%s' "$payload" | uv run --project "$root" --no-sync python "$root/tools/launch_hook.py" hook_large_result.py)
    end=$(date +%s%N)
    case $output in
      *additionalContext*) actual="${expected% *} 알림" ;;
      *) actual="${expected% *} 침묵" ;;
    esac
    echo "$i $expected $(( (end - start) / 1000000 ))ms $actual"
    if [ "$actual" != "$expected" ]; then
      echo "실패: 기대는 $expected 이다" >&2
      exit 1
    fi
  done
done
