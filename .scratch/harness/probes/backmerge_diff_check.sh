#!/bin/sh
# 되돌려 합칠 것이 남았는지 보는 판정 `git diff --quiet dev...main`(종료 0이면 main에만 있는 변경이 없다,
# 1이면 있다)이 장면마다 기대한 값을 내는지 임시 저장소로 잰다. 근거로 드는 자리:
# `.claude/skills/next-session/SKILL.md` 결정표의 첫 줄과 `merge.md`의 "되돌려 합치기".
#
# 장면마다 두 가지를 단언한다. (1) 그 장면이 실제로 났다는 표지(마지막 커밋 제목이나 병합 커밋의
# 부모 수). (2) 판정의 종료 코드. 표지가 틀린 회차는 측정이 아니라고 세고 종료 코드를 1로 둔다.
# 마지막 줄은 결과 한 줄(JSON)이다.
#
# 돌리는 법: sh .scratch/harness/probes/backmerge_diff_check.sh
set -u
D=$(mktemp -d) || exit 2
cd "$D" || exit 2
git init -q -b main . || exit 2
git config user.email probe@example.invalid
git config user.name probe
git config commit.gpgsign false
git config core.autocrlf false

measured=0
not_measured=0
wrong=0
results=""

# scene <이름> <기대 종료 코드> <표지: 장면이 났다는 명령의 출력과 같아야 하는 값> <표지 명령>
scene() {
  name=$1
  want=$2
  mark_want=$3
  mark_got=$4
  git diff --quiet dev...main
  got=$?
  if [ "$mark_got" != "$mark_want" ]; then
    not_measured=$((not_measured + 1))
    results="$results{\"scene\":\"$name\",\"measured\":false,\"mark_want\":\"$mark_want\",\"mark_got\":\"$mark_got\"},"
    return
  fi
  measured=$((measured + 1))
  if [ "$got" -ne "$want" ]; then
    wrong=$((wrong + 1))
  fi
  results="$results{\"scene\":\"$name\",\"measured\":true,\"want\":$want,\"got\":$got},"
}

echo a > a.txt && git add . && git commit -qm "base"
git branch dev

scene "dev를 막 땄다" 0 "main=dev" "$([ "$(git rev-parse main)" = "$(git rev-parse dev)" ] && echo main=dev || echo differ)"

git checkout -q dev
echo f1 > f1.txt && git add . && git commit -qm "feature 1"
scene "dev만 앞섰다" 0 "feature 1" "$(git log -1 --format=%s dev)"

git checkout -q main
git merge -q --no-ff dev -m "release 1"
scene "출시 직후(main에 merge 커밋만 더 있다)" 0 "2" "$(git rev-list --parents -1 main | wc -w | tr -d ' ' | awk '{print $1-1}')"

git checkout -q dev
echo f2 > f2.txt && git add . && git commit -qm "feature 2"
scene "출시 뒤 dev가 더 나아갔다" 0 "feature 2" "$(git log -1 --format=%s dev)"

git checkout -q main
echo h > h.txt && git add . && git commit -qm "hotfix"
scene "핫픽스가 main에만 있다" 1 "hotfix" "$(git log -1 --format=%s main)"

git checkout -q dev
git merge -q --no-ff main -m "backmerge"
scene "되돌려 합친 뒤" 0 "2" "$(git rev-list --parents -1 dev | wc -w | tr -d ' ' | awk '{print $1-1}')"

git checkout -q main
git merge -q --no-ff dev -m "release 2"
scene "다음 출시 직후" 0 "2" "$(git rev-list --parents -1 main | wc -w | tr -d ' ' | awk '{print $1-1}')"

cd / || exit 2
rm -rf "$D"
echo "{\"measured\":$measured,\"not_measured\":$not_measured,\"wrong\":$wrong,\"scenes\":[${results%,}]}"
if [ "$not_measured" -ne 0 ] || [ "$wrong" -ne 0 ]; then
  exit 1
fi
exit 0
