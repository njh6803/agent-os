#!/usr/bin/env bash
# eslint_program_timeout.py 의 측정을 차례로 돌린다(README 의 그 줄). 저장소 루트에서
# `bash .scratch/harness/probes/precommit_xdist/eslint_program_timeout_all.sh <단계>`.
# 단계 `repro` 는 고치기 전 판의 양성 대조, 부하 없음, pytest 세 벌, pytest 세 벌과 CPU 를 태우는
# 프로세스 16개를 차례로 잰다. 각 부하에서 저장소 설정 그대로(before)와 제한을 600초로 늘린 판(observe)을
# 함께 잰다. 16개에서 60초를 넘기지 않아(가장 긴 것 56.9초) 단계 `heavy` 가 32개로 before 판을 잰다.
# observe 판은 32개에서 재지 않는다. 대조가 보였듯 넘김으로 보고된 시험도 끝난 뒤에 보고되어, before
# 판의 걸린 시간이 실제로 끝난 시간이다. 32개 옆 측정 한 번이 한 시간 걸려 처음 띄운 observe 판은 끊었다.
# 단계 `control` 은 양성 대조만 다시 돈다(첫 대조 회차가 vitest 의 명령줄 옵션 때문에 측정 없이 끝났다).
# 단계 `after` 는 고친 판의 대조(slow-pass)와, 고친 판을 부하 없음과 pytest 세 벌과 프로세스 32개에서
# before 판으로만 잰다(제한을 늘리지 않은 저장소 설정이 고친 판이다). 결과는 results/eslint_program_timeout/
# 에 쓰고 덮는다. 측정마다 요약 한 줄(.line), 표준 오류(.err), 종료 코드(.exit)를 그 파일 옆에 남기고,
# pytest 부하를 건 측정은 부하의 출력(<이름>_pytest<i>.txt)도 남긴다. pytest 부하를 건 측정은 그 부하가
# 끝나면 회차도 멈춘다.
set -u
export PYTHONUTF8=1
phase="${1:?단계(repro, control, heavy, after)}"
here=.scratch/harness/probes/precommit_xdist
probe=$here/eslint_program_timeout.py
out=$here/results/eslint_program_timeout
mkdir -p "$out"

run() {
  name="$1"
  shift
  uv run python "$probe" "$@" --out "$out/$name.json" > "$out/$name.line" 2> "$out/$name.err"
  echo $? > "$out/$name.exit"
}

case "$phase" in
  repro)
    run control_slow 1 --control slow
    run b0_before 3
    run b0_observe 3 --mode observe
    run pytest3_before 100 --pytest-loads 3
    run pytest3_observe 100 --pytest-loads 3 --mode observe
    run pytest3_b16_before 100 --pytest-loads 3 --burners 16
    run pytest3_b16_observe 100 --pytest-loads 3 --burners 16 --mode observe
    ;;
  control)
    run control_slow 1 --control slow
    ;;
  heavy)
    run pytest3_b32_before 100 --pytest-loads 3 --burners 32
    ;;
  after)
    run after_control_slow_pass 1 --control slow-pass
    run after_b0 3
    run after_pytest3_b32 100 --pytest-loads 3 --burners 32
    ;;
  *)
    echo "단계는 repro, control, heavy, after 가운데 하나다: $phase" >&2
    exit 2
    ;;
esac
