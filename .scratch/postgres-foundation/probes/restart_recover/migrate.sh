#!/bin/sh
# `migrate` 대역. 진짜 `agent-os migrate` 가 아니라, 한 번 돌아 표를 만들고 줄 하나를 더한 뒤 0으로
# 끝나는 모양만 흉내 낸다(ADR 0066 결정 "표를 올리는 때"). 줄 수가 곧 이 스크립트가 돈 횟수다.
# MIGRATE_DELAY 초를 먼저 잔다(처음 띄우기가 끊기는 창을 넓히는 데 쓴다).
delay="${MIGRATE_DELAY:-0}"

trap 'echo "migrate-term"; exit 143' TERM INT

echo "migrate-start delay=$delay"
if [ "$delay" != 0 ]; then
	sleep "$delay" &
	wait $!
fi
psql -h postgres -U agent_os -d agent_os -v ON_ERROR_STOP=1 \
	-c "create table if not exists probe_rows (id bigserial primary key, note text not null, added_at timestamptz not null default now())" \
	-c "insert into probe_rows (note) values ('migrate')"
code=$?
echo "migrate-done code=$code"
exit "$code"
