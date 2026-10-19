#!/usr/bin/env bash
# mutate_no_grandchild_bound.py 의 측정을 차례로 돌린다(README 의 그 줄). 저장소 루트에서
# `bash .scratch/harness/probes/precommit_xdist/mutate_no_grandchild_bound_all.sh <단계>`.
# 단계 `repro` 는 고치기 전 판(`5e7fa88d` 의 시험 파일을 임시 폴더로 꺼낸다)의 양성 대조 넷, 부하 없음,
# CPU 를 태우는 프로세스 32개, pytest 세 벌의 차례다. 단계 `after` 는 고친 판(작업 트리의 시험 파일)을
# 부하 없음, 32개, pytest 세 벌에서 잰다. 단계 `pair` 는 프로세스 48개 옆에서 두 판을 회차마다 번갈아
# 잰다(`after` 의 부하에서 고친 판이 8초를 넘긴 회차가 없어 고친 길의 표지를 얻으려고 더했다. 처음에는
# 64개 옆에서 두 판을 따로 쟀는데, 끝의 부하 정리가 30초 넘김으로 끊겨 두 측정 모두 결과 없이 부하
# 128개를 남겼다. 일지 2026-10-20-05). 결과는
# results/mutate_no_grandchild_bound/ 에 쓰고 덮는다. 측정마다 요약 한 줄(.line), 표준 오류(.err), 종료
# 코드(.exit)를 그 파일 옆에 남기고, pytest 부하를 건 측정은 부하의 출력(<이름>_pytest<i>.txt)도
# 남긴다. pytest 부하를 건 측정은 그 부하가 끝나면 회차도 멈춘다.
set -u
export PYTHONUTF8=1
phase="${1:?단계(repro, after, pair)}"
here=.scratch/harness/probes/precommit_xdist
probe=$here/mutate_no_grandchild_bound.py
out=$here/results/mutate_no_grandchild_bound
mkdir -p "$out"

run() {
  name="$1"
  shift
  uv run python "$probe" "$@" --out "$out/$name.json" > "$out/$name.line" 2> "$out/$name.err"
  echo $? > "$out/$name.exit"
}

case "$phase" in
  repro)
    before="$(mktemp -d)/test_mutate_5e7fa88d.py" || exit 1
    git show 5e7fa88d:tests/tools/test_mutate.py > "$before" || exit 1
    for control in slow-before slow-kill slow-drain slow-after; do
      run "control_$control" 2 --control "$control" --test-file "$before"
    done
    run b0 10 --test-file "$before"
    run b32 60 --burners 32 --test-file "$before"
    run pytest3 2000 --pytest-loads 3 --test-file "$before"
    ;;
  after)
    run after_b0 10
    run after_b32 60 --burners 32
    run after_pytest3 2000 --pytest-loads 3
    ;;
  pair)
    before="$(mktemp -d)/test_mutate_5e7fa88d.py" || exit 1
    git show 5e7fa88d:tests/tools/test_mutate.py > "$before" || exit 1
    run pair_b48 30 --burners 48 --test-file "$before" --test-file tests/tools/test_mutate.py
    ;;
  *)
    echo "단계는 repro, after, pair 가운데 하나다: $phase" >&2
    exit 2
    ;;
esac
