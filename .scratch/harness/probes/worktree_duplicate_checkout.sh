#!/bin/sh
# ADR 0032 의 근거. 같은 브랜치나 같은 경로로 워크트리를 한 번 더 만들면 git 이 막는지 임시 저장소에서 잰다.
# 쓰는 법: sh worktree_duplicate_checkout.sh <임시 폴더의 절대 경로>
# 이 스크립트는 인자 폴더를 지우고 다시 만든다. 그래서 인자를 검사한다.
#   - 절대 경로(`/…` 또는 `C:/…`)가 아니면 지우지 않고 종료 2 로 멈춘다.
#   - 이미 있는 폴더는 비어 있거나 이 스크립트가 심은 표지 파일(.worktree_duplicate_checkout_probe)이 있을 때만 지운다.
#     아니면 종료 2 로 멈춘다. 저장소 루트나 홈 같은 폴더는 표지가 없어 지워지지 않는다.
# 종료 코드: 0 이면 두 거부가 모두 기대한 문구와 git 종료 코드 128 로 났다. 1 이면 문구나 종료 코드가 달랐다(측정이 아니다).
# 2 이면 인자가 안전하지 않아 아무것도 하지 않았다.
# 2026-10-15 이 PC(git 2.32.0.windows.2)의 결과: 같은 브랜치는 `fatal: 'feat' is already checked out at ...`,
# 같은 경로는 `fatal: '../wt-a' already exists`, 둘 다 git 의 종료 코드 128 이었다.
set -u
LC_ALL=C
export LC_ALL
base="${1:-}"
marker=".worktree_duplicate_checkout_probe"

case "$base" in
  /*|[A-Za-z]:[/\\]*) ;;
  *) echo "인자가 절대 경로가 아니다: 아무것도 하지 않았다" >&2; exit 2 ;;
esac
if [ -e "$base" ]; then
  if [ ! -d "$base" ]; then
    echo "폴더가 아니다: 아무것도 하지 않았다" >&2
    exit 2
  fi
  if [ ! -f "$base/$marker" ] && [ -n "$(ls -A "$base")" ]; then
    echo "비어 있지 않고 이 스크립트의 표지가 없는 폴더다: 아무것도 하지 않았다" >&2
    exit 2
  fi
fi

rm -rf -- "$base"
mkdir -p -- "$base" || exit 9
cd "$base" || exit 9
: > "$marker"
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
