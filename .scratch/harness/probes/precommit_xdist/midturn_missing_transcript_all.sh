#!/usr/bin/env bash
# midturn_missing_transcript.py 의 측정을 차례로 돌린다(README 의 그 줄). 저장소 루트에서
# `bash .scratch/harness/probes/precommit_xdist/midturn_missing_transcript_all.sh <고치기 전 시험 사본.py> <단계>`.
# 사본은 `git show 5e7fa88d:tests/tools/test_hook_midturn_korean.py > <저장소 밖>/before.py` 로 만든다.
# 단계 `repro` 는 고치기 전 판만 잰 재현과 양성 대조 넷이고, `pair` 는 고치기 전 판과 고친 판(저장소의
# 시험)을 한 회차에 차례로 불러 같은 부하에서 잰다. 결과는 results/midturn_missing_transcript/ 에 쓰고
# 덮는다. 측정마다 요약 한 줄(.line), 표준 오류(.err), 종료 코드(.exit)를 그 파일 옆에 남기고, pytest
# 부하를 건 측정은 부하의 출력(<이름>_pytest<i>.txt)도 남긴다. pytest 부하를 건 측정은 그 부하가 끝나면
# 회차도 멈춘다.
set -u
export PYTHONUTF8=1
before="${1:?고치기 전 시험 사본의 경로}"
phase="${2:?단계(repro 또는 pair)}"
here=.scratch/harness/probes/precommit_xdist
probe=$here/midturn_missing_transcript.py
out=$here/results/midturn_missing_transcript
mkdir -p "$out"

run() {
  name="$1"
  shift
  uv run python "$probe" "$@" --out "$out/$name.json" > "$out/$name.line" 2> "$out/$name.err"
  echo $? > "$out/$name.exit"
}

case "$phase" in
  repro)
    for control in waits slow-start slow-exit slow-parent; do
      run "control_$control" 5 --test-file "$before" --control "$control"
    done
    run b0 30 --test-file "$before"
    run b32 150 --burners 32 --test-file "$before"
    run pytest2 2000 --pytest-loads 2 --test-file "$before"
    run pytest3 2000 --pytest-loads 3 --test-file "$before"
    ;;
  pair)
    run pair_b0 30 --test-file "$before" --test-file tests/tools/test_hook_midturn_korean.py
    run pair_b32 150 --burners 32 --test-file "$before" \
      --test-file tests/tools/test_hook_midturn_korean.py
    for round in 1 2; do
      run "pair_pytest3_r$round" 2000 --pytest-loads 3 --test-file "$before" \
        --test-file tests/tools/test_hook_midturn_korean.py
    done
    ;;
  *)
    echo "단계는 repro 또는 pair 다: $phase" >&2
    exit 2
    ;;
esac
