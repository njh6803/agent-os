#!/bin/sh
# dind 컨테이너("리눅스 서버") 안에서 GET 을 보낸다. 안쪽 dockerd 가 꺼져 있어도 돈다.
#
#   client.sh <제한 시간(초)> <주소>...
#
# 주소마다 한 줄을 낸다(탭으로 가른다). 주소들은 함께 보내고 준 차례대로 찍는다.
#
#   REPLY <주소> <상태> <본문 첫 줄> <wget 의 오류 줄>
#
# 상태는 HTTP 상태 코드이고, 응답을 받지 못했으면 0 이다(연결 거부, 시간 초과). busybox wget 은
# 2xx 가 아닌 응답의 본문을 내지 않아 그때 본문은 빈다.
limit="$1"
shift
work="$(mktemp -d)"
index=0
for url in "$@"; do
	index=$((index + 1))
	(
		wget -q -S -T "$limit" -O "$work/$index.body" "$url" 2>"$work/$index.err"
		echo "$?" >"$work/$index.code"
	) &
done
wait
index=0
for url in "$@"; do
	index=$((index + 1))
	status="$(sed -n 's/^ *HTTP\/[0-9.]* \([0-9][0-9][0-9]\).*/\1/p' "$work/$index.err" | tail -n 1)"
	if [ -z "$status" ]; then
		status="$(sed -n 's/.*server returned error: HTTP\/[0-9.]* \([0-9][0-9][0-9]\).*/\1/p' "$work/$index.err" | tail -n 1)"
	fi
	body="$(head -c 300 "$work/$index.body" 2>/dev/null | head -n 1 | tr '\t' ' ')"
	note="$(grep '^wget:' "$work/$index.err" | tr '\n\t' '  ')"
	printf 'REPLY\t%s\t%s\t%s\t%s\n' "$url" "${status:-0}" "$body" "$note"
done
rm -rf "$work"
