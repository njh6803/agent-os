#!/bin/sh
# hook_line_separators 한 번의 시간을 등록 모양(tools/launch_hook.py 를 거쳐)으로 잰다(대기열 160).
# 입력은 날것 줄 구분 문자가 없어 침묵하는 Edit 둘이다. 보통 파이썬 파일(tools/run_hooks.py, 약 29KB)과
# 큰 텍스트 파일 web/pnpm-lock.yaml(약 200KB). 일곱 번씩 밀리초를 찍는다.
# 돌리는 법: 저장소 루트에서 `sh .scratch/harness/probes/line_separators_hook_time.sh`.
set -eu
root=$(cd "$(dirname "$0")/../../.." && pwd)
for i in 1 2 3 4 5 6 7; do
  for file in tools/run_hooks.py web/pnpm-lock.yaml; do
    payload="{\"tool_name\": \"Edit\", \"tool_input\": {\"file_path\": \"$root/$file\"}}"
    start=$(date +%s%N)
    printf '%s' "$payload" | uv run --project "$root" --no-sync python "$root/tools/launch_hook.py" hook_line_separators.py > /dev/null
    end=$(date +%s%N)
    echo "$file $(( (end - start) / 1000000 ))ms"
  done
done
