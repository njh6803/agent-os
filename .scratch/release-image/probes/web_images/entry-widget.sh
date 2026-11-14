#!/bin/sh
# 시제품(측정용) 위젯 진입 스크립트. 컨테이너가 뜰 때 사이트 파일(AGENT_OS_SITE_FILE)로 빌드한 뒤 서비스를 시작한다.
# 최종 진입 스크립트가 아니다. 줄 머리가 RI_PROBE 인 줄은 프로브(run.py)가 읽는 표지다.
#
# 환경 변수(모두 측정용)
#   RI_PROBE_WAIT_URL   주면 빌드가 끝난 뒤 wait.mjs 를 뒤에서 띄워 첫 200 의 시각을 찍는다
#   RI_PROBE_MEMSAMPLE  1 이면 빌드 동안 0.2초마다 cgroup 의 memory.current 와 anon·file 을 찍는다
#   RI_PROBE_PORT       듣는 포트(기본 3000). 호스트는 늘 127.0.0.1 이다
set -u

now() { date +%s.%N; }
cg() { cat "/sys/fs/cgroup/$1" 2>/dev/null | tr '\n' ' '; }

echo "RI_PROBE entry t=$(now) uid=$(id -u) gid=$(id -g) home=${HOME-<unset>} pid=$$ site_file=${AGENT_OS_SITE_FILE-<unset>}"
if [ -e .next/BUILD_ID ]; then
  echo "RI_PROBE prior-build present id=$(cat .next/BUILD_ID)"
else
  echo "RI_PROBE prior-build absent"
fi

sampler=""
# sampler 의 명령줄에 이 회차만 쓰는 표지를 넣는다. 끄기 직전에 그 pid 의 명령줄에서 표지를 확인한다(pid 재사용 방지).
sampler_mark="ri-sampler-$$-$(date +%s%N)"
if [ "${RI_PROBE_MEMSAMPLE:-}" = 1 ]; then
  # 서브셸은 명령줄이 이 스크립트와 같아 표지를 싣지 못한다. 그래서 따로 sh 를 띄우고 표지를 $0 으로 준다.
  sh -c '
    while :; do
      echo "RI_PROBE mem t=$(date +%s.%N) current=$(cat /sys/fs/cgroup/memory.current 2>/dev/null | tr "\n" " ")$(awk '"'"'$1=="anon"||$1=="file"{printf "%s=%s ", $1, $2}'"'"' /sys/fs/cgroup/memory.stat)"
      sleep 0.2
    done
  ' "$sampler_mark" &
  sampler=$!
fi

echo "RI_PROBE build-start t=$(now)"
node tools/start.ts build
code=$?
echo "RI_PROBE build-exit code=$code t=$(now)"
if [ -n "$sampler" ]; then
  case "$(tr '\0' ' ' <"/proc/$sampler/cmdline" 2>/dev/null)" in
    *"$sampler_mark"*) kill "$sampler" 2>/dev/null ;;
    *) echo "RI_PROBE sampler-gone-or-reused pid=$sampler (끄지 않았다)" ;;
  esac
fi
echo "RI_PROBE memory.peak $(cg memory.peak)"
echo "RI_PROBE memory.max $(cg memory.max)"
echo "RI_PROBE memory.events $(cg memory.events)"
echo "RI_PROBE memory.swap.peak $(cg memory.swap.peak)"
if [ "$code" -ne 0 ]; then
  exit "$code"
fi

port="${RI_PROBE_PORT:-3000}"
if [ -n "${RI_PROBE_WAIT_URL:-}" ]; then
  node /probe/wait.mjs "$RI_PROBE_WAIT_URL" &
fi
echo "RI_PROBE start-exec t=$(now)"
exec node tools/start.ts start --hostname 127.0.0.1 --port "$port"
