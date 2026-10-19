#!/usr/bin/env bash
# open_session_pattern_timed.py 의 측정 전부를 차례로 돌린다(README 의 그 줄). 저장소 루트에서
# `bash .scratch/harness/probes/precommit_xdist/open_session_pattern_timed_all.sh <고치기 전 시험 사본.py>`.
# 사본은 `git show 88fed982:tests/tools/test_open_session.py > <저장소 밖>/before.py` 로 만든다.
# 결과는 results/open_session_pattern_timed/ 에 쓰고 덮는다. 측정마다 요약 한 줄(.line), 표준 오류(.err),
# 종료 코드(.exit)를 그 파일 옆에 남기고, pytest 부하를 건 측정은 부하의 출력(<이름>_pytest<i>.txt)도
# 남긴다. pytest 부하를 건 측정은 그 부하가 끝나면 회차도 멈춘다. 앞의 넷은 고치기 전 판만 잰 재현이고,
# `pair_` 로 시작하는 뒤의 것은 고치기 전 판과 고친 판(저장소의 시험)을 회차마다 번갈아 같은 부하에서 잰다.
# 재현에서 빨강이 난 부하(32개, pytest 세 벌)와 대조로 부하 없음을 다시 걸고, 두 판이 회차를 반씩 나누므로
# 회차를 늘린다.
set -u
export PYTHONUTF8=1
before="${1:?고치기 전 시험 사본의 경로}"
here=.scratch/harness/probes/precommit_xdist
probe=$here/open_session_pattern_timed.py
out=$here/results/open_session_pattern_timed
mkdir -p "$out"

run() {
  name="$1"
  shift
  uv run python "$probe" "$@" --test-file "$before" --out "$out/$name.json" \
    > "$out/$name.line" 2> "$out/$name.err"
  echo $? > "$out/$name.exit"
}

run b0 10
run pytest2 200 --pytest-loads 2
run b32 40 --burners 32
run pytest3 200 --pytest-loads 3
run pair_b0 10 --test-file tests/tools/test_open_session.py
run pair_b32 80 --burners 32 --test-file tests/tools/test_open_session.py
for round in 1 2; do
  run "pair_pytest3_r$round" 200 --pytest-loads 3 --test-file tests/tools/test_open_session.py
done
