#!/bin/sh
# hook_stop_korean 한 번의 시간을 래퍼 전의 등록 모양(uv run --no-sync python 으로 훅을 바로)으로 잰다.
# 래퍼(tools/launch_hook.py)의 몫은 hook_registration/time_launch.sh 가 잰다.
# 영어 답(막는다)과 한국어 답(지나간다)을 다섯 번씩 돌려 밀리초를 찍는다.
# 쓰는 법: 저장소 루트에서 `sh .scratch/harness/probes/stop_payload/time_hook.sh`.
set -eu
root=$(cd "$(dirname "$0")/../../../.." && pwd)
english='{"stop_hook_active": false, "last_assistant_message": "Now merge. I will check CI and open the PR."}'
korean='{"stop_hook_active": false, "last_assistant_message": "새 커밋의 CI가 통과했습니다. 리뷰를 기다립니다."}'
for label in english korean; do
  eval "payload=\$$label"
  for i in 1 2 3 4 5; do
    start=$(date +%s%N)
    printf '%s' "$payload" | uv run --project "$root" --no-sync python "$root/tools/hook_stop_korean.py" > /dev/null
    end=$(date +%s%N)
    echo "$label $(( (end - start) / 1000000 ))ms"
  done
done
