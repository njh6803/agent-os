#!/bin/sh
# dind 컨테이너의 주 프로세스. 안쪽 dockerd 를 띄우고, 끝나면 다시 띄운다.
#
# 왜. 공식 dind 이미지의 진입 스크립트는 dockerd 를 컨테이너의 주 프로세스로 두어, dockerd 를 끄면
# 컨테이너가 끝난다. 그러면 "Docker 데몬만 다시 켠다"(리눅스 서버의 `systemctl restart docker`)를
# 흉내 낼 수 없다. 이 스크립트가 주 프로세스로 남아 systemd 의 그 몫만 대신한다.
#
# - dockerd 가 끝나면 1초 뒤 다시 띄운다. 프로브는 dockerd 에 TERM 을 보내 "데몬만 다시 켠다"를 낸다.
# - TERM 을 받으면(바깥의 `docker stop`·`docker restart`) dockerd 에 넘기고 끝날 때까지 기다린 뒤
#   끝난다. dockerd 는 TERM 을 받으면 자기 컨테이너들을 멈추고 끝난다(서버를 정상으로 끄는 길).
# - 진입 스크립트에 `dockerd` 를 첫 인자로 주면 TCP 소켓(2375)을 더하지 않는다. 유닉스 소켓만 연다.
# pid 재사용으로 상관없는 프로세스에 TERM 이 가지 않게 한다. 회차마다 표지를 dockerd 의 환경 변수
# (RI_SUPERVISE_MARK)에 싣고, TERM 을 보내기 직전에 그 pid 의 환경에서 표지를 확인한다. dockerd 의
# 기동 인자는 바꾸지 않는다(측정 대상의 기동 방식이 달라지지 않게).
stopping=""
child=""
mark=""
count=0

on_term() {
	stopping=1
	if [ -n "$child" ]; then
		case "$(tr '\0' ' ' <"/proc/$child/environ" 2>/dev/null)" in
		*"$mark"*) kill -TERM "$child" 2>/dev/null ;;
		esac
	fi
}
trap on_term TERM INT

while [ -z "$stopping" ]; do
	count=$((count + 1))
	mark="ri-supervise-$$-${count}-$(date +%s%N)"
	echo "supervise: dockerd start ${count}"
	RI_SUPERVISE_MARK="$mark" dockerd-entrypoint.sh dockerd --host=unix:///var/run/docker.sock &
	child=$!
	while kill -0 "$child" 2>/dev/null; do
		wait "$child"
	done
	child=""
	echo "supervise: dockerd exit ${count}"
	if [ -z "$stopping" ]; then
		sleep 1
	fi
done
echo "supervise: stop"
