#!/bin/sh
# 컨테이너의 1번 프로세스(PostgreSQL 의 postmaster)를 바깥(서버)에서 KILL 한다. Docker 가 시키지 않은
# 죽음(프로세스 충돌, 커널의 메모리 부족 정리)을 낸다. `docker kill` 은 Docker 가 시킨 죽음이라
# 재시작 정책이 다르게 다룰 수 있어 따로 잰다.
#
# pid 만 보고 끄지 않는다. 인자로 받은 컨테이너의 pid 를 지금 다시 읽고, 그 pid 의 명령줄이 postgres 로
# 시작하며 그 pid 의 cgroup 경로에 인자로 받은 컨테이너의 전체 id 가 있을 때만 보낸다. 환경
# 변수(/proc/<pid>/environ)는 표지로 쓰지 않는다. postmaster 가 프로세스 제목을 고치며 그 자리를
# 덮어써, 첫 판이 표지를 찾지 못했다(명령줄도 `postgres ` 로만 읽혔다).
id="$1"
case "$id" in
"" | *[!0-9a-f]*) echo "skip bad id [$id]"; exit 2 ;;
esac
pid="$(docker inspect -f '{{.State.Pid}}' "$id")" || exit 2
line="$(tr '\0' ' ' <"/proc/$pid/cmdline" 2>/dev/null)"
group="$(tr '\n' ' ' <"/proc/$pid/cgroup" 2>/dev/null)"
case "$line" in
postgres*)
	case "$group" in
	*"$id"*)
		if kill -KILL "$pid"; then
			echo "sent $pid [$line] cgroup [$group]"
			exit 0
		fi
		;;
	esac
	;;
esac
echo "skip pid=$pid [$line] cgroup [$group]"
exit 3
