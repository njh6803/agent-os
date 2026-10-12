#!/bin/sh
# hook_bash_cd_outside 한 번의 시간을 등록 모양(tools/launch_hook.py 를 거쳐)으로 잰다(대기열 123).
# 입력은 둘이다. cd 가 없어 정규식 하나로 끝나는 Bash 명령과, 저장소 루트에서 하위 폴더로 옮겨 조상의
# `.git` 을 찾는 cd(침묵)다. 일곱 번씩 밀리초를 찍는다.
# 돌리는 법: 저장소 루트에서 `sh .scratch/harness/probes/cd_outside_hook_time.sh`.
set -eu
root=$(cd "$(dirname "$0")/../../.." && pwd)
for i in 1 2 3 4 5 6 7; do
  for command in "git status --short" "cd web && ls"; do
    payload="{\"tool_name\": \"Bash\", \"tool_input\": {\"command\": \"$command\"}, \"cwd\": \"$root\"}"
    start=$(date +%s%N)
    printf '%s' "$payload" | uv run --project "$root" --no-sync python "$root/tools/launch_hook.py" hook_bash_cd_outside.py > /dev/null
    end=$(date +%s%N)
    echo "$command $(( (end - start) / 1000000 ))ms"
  done
done
