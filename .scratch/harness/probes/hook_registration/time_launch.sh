#!/bin/sh
# 훅 한 번의 시간을 옛 등록 모양(훅을 바로)과 래퍼 모양(tools/launch_hook.py 를 거쳐)으로 번갈아 잰다(대기열 91).
# 훅은 hook_env_read, 입력은 발동하지 않는 `ls` 다. 일곱 번씩 밀리초를 찍는다.
# 돌리는 법: 저장소 루트에서 `sh .scratch/harness/probes/hook_registration/time_launch.sh`.
set -eu
root=$(cd "$(dirname "$0")/../../../.." && pwd)
payload='{"tool_name": "Bash", "tool_input": {"command": "ls"}}'
for i in 1 2 3 4 5 6 7; do
  for shape in direct launch; do
    if [ "$shape" = direct ]; then
      set -- "$root/tools/hook_env_read.py"
    else
      set -- "$root/tools/launch_hook.py" hook_env_read.py
    fi
    start=$(date +%s%N)
    printf '%s' "$payload" | uv run --project "$root" --no-sync python "$@" > /dev/null
    end=$(date +%s%N)
    echo "$shape $(( (end - start) / 1000000 ))ms"
  done
done
