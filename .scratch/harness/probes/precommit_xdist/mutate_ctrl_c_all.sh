#!/usr/bin/env bash
# mutate_ctrl_c.py 의 측정 전부를 차례로 돌린다(README 의 그 줄). 저장소 루트에서
# `bash .scratch/harness/probes/precommit_xdist/mutate_ctrl_c_all.sh <고치기 전 시험 사본.py>`.
# 사본은 `git show 88fed982:tests/tools/test_mutate.py > <저장소 밖>/before.py` 로 만든다.
# 결과는 results/mutate_ctrl_c/ 에 쓰고 덮는다. 측정마다 요약 한 줄(.line), 표준 오류(.err), 종료 코드
# (.exit)를 그 파일 옆에 남기고, pytest 부하를 건 측정은 부하의 출력(<이름>_pytest<i>.txt)도 남긴다.
# pytest 두 벌은 그 부하가 끝나면 회차도 멈춰(2026-10-19 에는 한 번에 38~59회차) 네 번 잇는다. pytest 세 벌은 시간 제한
# 시험의 상한이 빨갰던 부하라(open_session_pattern_timed.py 의 그 측정) 두 번 더 건다. 부하로 띄운
# pytest 가 그 시험을 고친 판으로 돌고, 실패는 요약의 pytest_load_failed 에 실린다. no-tree 대조는 부하
# 아래에서도 돌려, 고친 판정이 손자를 끝내지 못한 회귀를 부하에서도 빨강으로 읽는지 본다.
set -u
export PYTHONUTF8=1
before="${1:?고치기 전 시험 사본의 경로}"
here=.scratch/harness/probes/precommit_xdist
probe=$here/mutate_ctrl_c.py
out=$here/results/mutate_ctrl_c
mkdir -p "$out"

run() {
  name="$1"
  shift
  uv run python "$probe" "$@" --test-file "$before" --test-file tests/tools/test_mutate.py \
    --out "$out/$name.json" > "$out/$name.line" 2> "$out/$name.err"
  echo $? > "$out/$name.exit"
}

run no_tree 10 --control no-tree
run late_kill 10 --control late-kill
run late_write 10 --control late-write
run no_tree_b32 10 --control no-tree --burners 32
run no_tree_pytest2 200 --control no-tree --pytest-loads 2
# 2026-10-19 의 첫 실행에서 no_tree_b32 의 고친 판 회차에 1초를 넘는 틈(1534ms)이 있었다. 판정이 도는 동안의
# 틈(judge_quiet_ms)과 지키는 스레드의 표본 간격(judge_sample_gap_ms)을 가르려고 회차를 늘려 다시 잰다
run no_tree_b32_gaps 30 --control no-tree --burners 32
run b0 20
run b16 60 --burners 16
run b32 30 --burners 32
for round in 1 2 3 4; do
  run "pytest2_r$round" 200 --pytest-loads 2
done
for round in 1 2; do
  run "pytest3_r$round" 200 --pytest-loads 3
done
