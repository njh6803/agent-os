#!/bin/sh
# hook_bash_msys_pathconv 한 번의 시간을 등록 모양(tools/launch_hook.py 를 거쳐)으로 잰다(대기열 195).
# 입력은 둘이다. git 이 아닌 흔한 Bash 명령(침묵)과, 바뀔 인자가 든 git(알림)이다. 일곱 번씩 밀리초와
# 그 실행이 알렸는지(출력에 additionalContext 가 있는지)를 찍는다. 기대와 다르면 1로 끝난다.
# 돌리는 법: 저장소 루트에서 `sh .scratch/harness/probes/msys_pathconv/time_hook.sh`.
set -eu
root=$(cd "$(dirname "$0")/../../../.." && pwd)
for i in 1 2 3 4 5 6 7; do
  for case in "침묵|ls -la tools" "알림|git show origin/main:.scratch/retro-queue.md"; do
    expected=${case%%|*}
    command=${case#*|}
    payload="{\"tool_name\": \"Bash\", \"tool_input\": {\"command\": \"$command\"}}"
    start=$(date +%s%N)
    output=$(printf '%s' "$payload" | uv run --project "$root" --no-sync python "$root/tools/launch_hook.py" hook_bash_msys_pathconv.py)
    end=$(date +%s%N)
    case $output in
      *additionalContext*) actual=알림 ;;
      *) actual=침묵 ;;
    esac
    echo "$command $(( (end - start) / 1000000 ))ms $actual"
    if [ "$actual" != "$expected" ]; then
      echo "실패: 기대는 $expected 이다" >&2
      exit 1
    fi
  done
done
