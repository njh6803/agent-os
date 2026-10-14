#!/usr/bin/env bash
# 대기열 231 측정: sibling_overlap 표의 표본 여섯(1 12 23 34 45 56)을 그대로, 그리고 표에 -x 를 적어 돌려
# 걸린 시간과 판정을 견준다. 인자는 잴 체크아웃(분리 임시 워크트리)과 결과를 쓸 디렉터리다.
#
# 잴 체크아웃은 도구가 빨강 변이에 -x 를 스스로 붙이기 전의 판이다(2026-10-14 에 e445a3d 에서 쟀다). 지금 도구로
# 돌리면 "그대로" 갈래도 변이에 -x 를 받아 견줌이 되지 않는다. 표에 적은 -x 는 기준선에도 붙는다. 그래서 두 갈래의
# 차이에는 기준선 몫(약 10초)이 섞이고, 변이 몫은 결과 파일의 변이 줄에서 따로 센다.
#
# 측정인 회차의 표지는 mutate 의 마지막 줄(`변이 6 모두 기대대로` 또는 `변이 6 중 어긋남`)이다. 두 결과 파일 가운데
# 하나라도 표지가 없으면 측정이 아니라서 1 로 끝난다.
#
# 사용: bash .scratch/harness/probes/mutate_231/measure.sh <임시 워크트리> <결과 디렉터리>
set -u
W=$1
OUT=$2
cd "$W" || exit 9
uv sync -q
export PYTHONUTF8=1
sed 's#tests = \["tests/tools/test_sibling_overlap.py"\]#tests = ["tests/tools/test_sibling_overlap.py", "-x"]#' \
  .scratch/harness/probes/sibling_overlap_mutations.toml > "$OUT/231_x.toml"
for kind in full x; do
  table=.scratch/harness/probes/sibling_overlap_mutations.toml
  [ "$kind" = x ] && table="$OUT/231_x.toml"
  start=$(date +%s)
  uv run python tools/mutate.py "$table" 1 12 23 34 45 56 > "$OUT/231_$kind.txt" 2>&1
  code=$?
  echo "$kind exit $code wall $(( $(date +%s) - start ))s" >> "$OUT/231_wall.txt"
done
status=0
for kind in full x; do
  grep -q -E '^변이 6 (모두 기대대로|중 어긋남)' "$OUT/231_$kind.txt" || { echo "표지 없음: 231_$kind.txt"; status=1; }
done
exit $status
