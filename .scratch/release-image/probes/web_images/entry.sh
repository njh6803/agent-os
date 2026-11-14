#!/bin/sh
# 시제품(측정용) 진입 스크립트. 관리 화면과 위젯 미리보기 페이지가 쓴다. 표지 한 줄을 찍고 받은 명령으로 갈아탄다(exec).
# 그래서 받은 명령의 프로세스가 이 셸의 pid 를 그대로 잇는다(init 없이 띄우면 pid 1).
#
# 환경 변수(측정용)
#   RI_PROBE_WAIT_URL   주면 wait.mjs 를 뒤에서 띄워 첫 200 의 시각을 찍는다
set -u
echo "RI_PROBE entry t=$(date +%s.%N) uid=$(id -u) gid=$(id -g) home=${HOME-<unset>} pid=$$ hostname_env=${HOSTNAME-<unset>} port_env=${PORT-<unset>}"
if [ -n "${RI_PROBE_WAIT_URL:-}" ]; then
  node /probe/wait.mjs "$RI_PROBE_WAIT_URL" &
fi
exec "$@"
