#!/usr/bin/env bash
# filesystem_read_retry.py 의 측정 전부를 차례로 돌린다(README 의 그 줄). 저장소 루트에서
# `bash .scratch/harness/probes/precommit_xdist/filesystem_read_retry_all.sh <고치기 전 시험 사본.py>`.
# 사본은 `git show aa93cf7b:tests/adapters/test_filesystem.py > <저장소 밖>/before.py` 로 만든다.
# 결과는 results/filesystem_read_retry/ 에 쓰고 덮는다. 측정마다 요약 한 줄(.line, retry_sleep_floor 는
# .json 이 곧 요약이라 없다), 표준 오류(.err), 종료 코드(.exit)를 그 파일 옆에 남긴다.
set -u
before="${1:?고치기 전 시험 사본의 경로}"
here=.scratch/harness/probes/precommit_xdist
probe=$here/filesystem_read_retry.py
floor=$here/retry_sleep_floor.py
out=$here/results/filesystem_read_retry
mkdir -p "$out"

run() {
  name="$1"
  shift
  uv run python "$probe" "$@" --out "$out/$name.json" > "$out/$name.line" 2> "$out/$name.err"
  echo $? > "$out/$name.exit"
}

run_floor() {
  name="$1"
  shift
  uv run python "$floor" "$@" > "$out/$name.json" 2> "$out/$name.err"
  echo $? > "$out/$name.exit"
}

run trace_b0 trace 10
run trace_b16 trace 60 --burners 16
run trace_b32 trace 10 --burners 32
run trace_b16_above trace 10 --burners 16 --priority above
run trace_b16_high trace 10 --burners 16 --priority high
run test_b0 test 40 --test-file "$before" --test-file tests/adapters/test_filesystem.py
run test_b16 test 120 --burners 16 --test-file "$before" --test-file tests/adapters/test_filesystem.py
run test_b32 test 60 --burners 32 --test-file "$before" --test-file tests/adapters/test_filesystem.py
run test_pytest2 test 400 --pytest-loads 2 --test-file "$before" --test-file tests/adapters/test_filesystem.py
run_floor sleep_floor_b0 300
run_floor sleep_floor_b16 300 --burners 16
run_floor sleep_floor_short_b0 300 --delays 0.0002,0.0002,0.0002,0.0002,0.0002
