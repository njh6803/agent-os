#!/bin/sh
# ADR 0032 의 근거. 같은 브랜치나 같은 경로로 워크트리를 한 번 더 만들면 git 이 막는지 임시 저장소에서 잰다.
# 쓰는 법: sh worktree_duplicate_checkout.sh <임시 폴더의 절대 경로>
# 그 폴더는 비우고 다시 만든다. 저장소 안의 폴더를 주지 않는다.
# 종료 코드: 0 이면 두 거부가 모두 기대한 문구로 났다. 1 이면 문구가 달랐다(측정이 아니다).
# 2026-10-15 이 PC(git 2.32.0.windows.2)의 결과: 같은 브랜치는 `fatal: 'feat' is already checked out at ...`,
# 같은 경로는 `fatal: '../wt-a' already exists`, 둘 다 git 의 종료 코드 128 이었다.
set -u
base="$1"
rm -rf "$base"
mkdir -p "$base"
cd "$base" || exit 9
git init -q repo
cd repo || exit 9
git -c user.name=t -c user.email=t@t commit -q --allow-empty -m init
git worktree add -q -b feat ../wt-a

echo "--- 같은 브랜치 두 번째 add"
out_branch=$(git worktree add ../wt-b feat 2>&1)
code_branch=$?
echo "$out_branch"
echo "git 종료 코드: $code_branch"

echo "--- 같은 경로 두 번째 add"
out_path=$(git worktree add -b feat2 ../wt-a 2>&1)
code_path=$?
echo "$out_path"
echo "git 종료 코드: $code_path"

echo "--- porcelain"
git worktree list --porcelain

status=0
case "$out_branch" in
  *"is already checked out at"*) [ "$code_branch" -eq 128 ] || { echo "표지 불일치: 브랜치 종료 코드"; status=1; } ;;
  *) echo "표지 없음: 같은 브랜치 거부 문구가 아니다. 측정이 아니다"; status=1 ;;
esac
case "$out_path" in
  *"already exists"*) [ "$code_path" -eq 128 ] || { echo "표지 불일치: 경로 종료 코드"; status=1; } ;;
  *) echo "표지 없음: 같은 경로 거부 문구가 아니다. 측정이 아니다"; status=1 ;;
esac
exit $status
