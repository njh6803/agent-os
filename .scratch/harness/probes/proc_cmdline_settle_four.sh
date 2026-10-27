#!/usr/bin/env bash
# proc_cmdline_settle.py 를 넷 함께 돌려 서로가 부하가 되게 한다(README 행). 인자는 하나마다의 회차 수.
# 출력은 넷의 요약을 차례로 찍고, 하나라도 0 이 아니면 그 코드로 끝난다.
set -u
count="${1:-300}"
here="$(dirname "$0")"
outs=()
pids=()
for i in 1 2 3 4; do
  out="$(mktemp)"
  outs+=("$out")
  uv run python "$here/proc_cmdline_settle.py" "$count" >"$out" 2>&1 &
  pids+=("$!")
done
status=0
for i in 0 1 2 3; do
  wait "${pids[$i]}" || status=$?
  cat "${outs[$i]}"
  rm -f "${outs[$i]}"
done
exit "$status"
