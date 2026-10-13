#!/bin/sh
# tools/sibling_overlap.py 가 형제 워크트리의 PR 이 병합됐는지 물을 때 드는 시간을 길마다 잰다(대기열 194).
#   ls-remote   — `refs/pull/*/head`·`refs/pull/*/merge`. 열린 PR 을 읽으려고 도구가 이미 친다.
#   open        — `gh api …/pulls?state=open`. 도구가 이미 친다.
#   closed-rest — `gh api …/pulls?state=closed --paginate` 에서 병합된 것. 따로 물을 때의 REST 길.
#   merged-gql  — `gh pr list --state merged`. 따로 물을 때의 GraphQL 길.
# 세 번씩 돌려 밀리초와 받은 줄 수를 찍고, 끝에 PR 의 수(`ls-remote` 의 head ref)와 병합 없이 닫힌
# PR 의 수를 찍는다. 종료 코드가 0 이 아니거나 받은 줄이 0 인 회차(비었다)는 측정이 아니라
# `측정 아님` 으로 따로 세고, 하나라도 있으면 1 로 끝난다. 열린 PR 과 병합 없이 닫힌 PR 은 0 줄이
# 맞을 수 있으므로 그 둘은 줄 수를 보지 않고 종료 코드만 본다.
# 쓰는 법: 저장소 루트에서 `sh .scratch/harness/probes/sibling_overlap_merge_cost.sh <임시 디렉터리>`.
# origin 이 github.com 이어야 하고 gh 와 인증이 든다.
set -u
scratch="${1:?임시 디렉터리를 준다}"
mkdir -p "$scratch"
url=$(git remote get-url origin)
# 매치하지 못하면 아무것도 내지 않는다(`-n` 과 `p`). 점이 든 저장소 이름도 받는다
repo=$(printf '%s' "${url%.git}" | sed -nE 's#^.*github\.com[:/]([^/]+/[^/]+)/?$#\1#p')
[ -n "$repo" ] || { echo "origin 이 github.com 이 아니다: $url" >&2; exit 2; }
ms() { date +%s%3N; }
missed=0

run() {
  label=$1; shift
  start=$(ms)
  "$@" > "$scratch/$label.txt" 2> "$scratch/$label.err"
  code=$?
  end=$(ms)
  lines=$(grep -c . "$scratch/$label.txt")
  case "$label" in open | unmerged) may_be_empty=1 ;; *) may_be_empty=0 ;; esac
  if [ "$code" -ne 0 ] || { [ "$may_be_empty" -eq 0 ] && [ "$lines" -eq 0 ]; }; then
    echo "$label 측정 아님(종료 $code, 줄 $lines): $(head -c 200 "$scratch/$label.err")"
    missed=$((missed + 1))
  else
    echo "$label $((end - start))ms 줄 $lines"
  fi
}

for i in 1 2 3; do
  run ls-remote git ls-remote origin 'refs/pull/*/head' 'refs/pull/*/merge'
  run open gh api "repos/$repo/pulls?state=open&per_page=100" --paginate \
    --jq '.[] | "\(.number) \(.head.sha)"'
  run closed-rest gh api "repos/$repo/pulls?state=closed&per_page=100" --paginate \
    --jq '.[] | select(.merged_at) | "\(.number) \(.head.sha)"'
  run merged-gql gh pr list --repo "$repo" --state merged --limit 1000 \
    --json number,headRefOid --jq '.[] | "\(.number) \(.headRefOid)"'
done
echo "PR $(grep -c 'refs/pull/[0-9]*/head$' "$scratch/ls-remote.txt")개(마지막 ls-remote 의 head ref)"
run unmerged gh api "repos/$repo/pulls?state=closed&per_page=100" --paginate \
  --jq '.[] | select(.merged_at == null) | .number'
echo "병합 없이 닫힌 PR: $(tr '\n' ' ' < "$scratch/unmerged.txt")"
[ "$missed" -eq 0 ] || { echo "측정 아님 $missed 회차" >&2; exit 1; }
