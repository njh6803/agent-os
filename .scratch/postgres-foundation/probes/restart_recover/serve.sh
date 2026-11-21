#!/bin/sh
# `serve` 대역과 지켜보는 대역(watch). 진짜 `serve` 가 아니라, 뜰 때 데이터베이스에 다시 시도하는
# 모양만 흉내 낸다(ADR 0066 결정 "serve와 데이터베이스").
#
# - PROBE_MODE=serve: 뜨면 RETRY_SECONDS 초 동안 RETRY_INTERVAL 초 간격으로 `pg_isready` 와
#   `psql … -c "select 1"` 을 시도한다. `select 1` 이 되면 "probe-connected" 를 찍고 오래 잠든다.
#   RETRY_SECONDS 가 지나도록 못 하면 "probe-giving-up" 을 찍고 1로 끝난다. RETRY_SECONDS=0 이면
#   첫 실패에서 바로 끝난다. REQUIRE_TABLE 이 있으면 붙은 뒤 표(probe_rows)가 있는지 보고, 없으면
#   "probe-schema-behind" 를 찍고 3으로 끝난다(진짜 `serve` 가 "표의 판이 뒤처졌다"며 멈추는 자리).
#   AFTER_CONNECT=exit 이면 붙은 뒤 잠들지 않고 0으로 끝난다(양성 대조용).
# - PROBE_MODE=watch: 끝없이 같은 시도를 되풀이하며 시도마다 한 줄을 찍는다. 붙어도 멈추지 않는다.
#
# 시도마다 찍는 줄: probe-attempt mode=… n=… since_ms=… took_ms=… ready_code=… ready=[…]
# query_code=… query=[…]. since_ms 는 뜬 뒤 시도를 시작한 때, took_ms 는 두 명령에 걸린 시간이다.
# 시각은 `docker logs -t` 가 줄마다 붙이는 것을 프로브가 읽는다.
host="${DB_HOST:-postgres}"
mode="${PROBE_MODE:-serve}"
limit="${RETRY_SECONDS:-30}"
pause="${RETRY_INTERVAL:-0.5}"
after="${AFTER_CONNECT:-sleep}"
require="${REQUIRE_TABLE:-}"

now_ms() {
	echo $(($(date +%s%N) / 1000000))
}

flat() {
	printf '%s' "$1" | tr '\n\t' '  ' | sed 's/  */ /g; s/ $//'
}

# 1번 프로세스는 손잡이가 없는 TERM 을 무시한다. 손잡이를 두어 데몬이 멈출 때 곧 끝나게 한다.
trap 'echo "probe-term mode=$mode"; exit 143' TERM INT

started="$(now_ms)"
echo "probe-start mode=$mode host=$host retry_seconds=$limit"
attempt=0
while :; do
	attempt=$((attempt + 1))
	begin="$(now_ms)"
	ready_text="$(pg_isready -h "$host" -U agent_os -d agent_os -t 1 2>&1)"
	ready_code=$?
	query_text="$(psql -h "$host" -U agent_os -d agent_os -tA -c 'select 1' 2>&1)"
	query_code=$?
	end="$(now_ms)"
	echo "probe-attempt mode=$mode n=$attempt since_ms=$((begin - started)) took_ms=$((end - begin)) ready_code=$ready_code ready=[$(flat "$ready_text")] query_code=$query_code query=[$(flat "$query_text")]"
	if [ "$mode" = serve ]; then
		if [ "$query_code" -eq 0 ]; then
			if [ -n "$require" ]; then
				table="$(psql -h "$host" -U agent_os -d agent_os -tA -c "select to_regclass('public.probe_rows') is not null" 2>&1)"
				if [ "$table" != t ]; then
					echo "probe-schema-behind mode=$mode n=$attempt table=[$(flat "$table")]"
					exit 3
				fi
			fi
			echo "probe-connected mode=$mode n=$attempt since_ms=$((end - started))"
			if [ "$after" = exit ]; then
				exit 0
			fi
			sleep infinity &
			wait $!
		fi
		if [ $((end - started)) -ge $((limit * 1000)) ]; then
			echo "probe-giving-up mode=$mode n=$attempt since_ms=$((end - started))"
			exit 1
		fi
	fi
	sleep "$pause"
done
