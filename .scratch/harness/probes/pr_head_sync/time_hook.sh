#!/bin/sh
# hook_pr_head_sync 한 번의 시간을 래퍼 전의 등록 모양(uv run --no-sync python 으로 훅을 바로)으로 잰다.
# 래퍼(tools/launch_hook.py)의 몫은 hook_registration/time_launch.sh 가 잰다.
# 세 길을 다섯 번씩 돌려 밀리초와 판정(deny 또는 silent)을 찍는다.
#   other — 리뷰를 부르지 않는 명령. 훅이 받는 입력의 대부분이고 git 도 gh 도 부르지 않는다.
#   local — 선택자 없는 `gh pr ready` 를 푸시하지 않은 커밋 위에서. git 만 부르고 막는다.
#   gh    — `gh pr ready <PR>` 를 저장소 루트에서. `gh pr view` 가 네트워크로 PR head 를 읽는다.
# 쓰는 법: 저장소 루트에서 `sh .scratch/harness/probes/pr_head_sync/time_hook.sh <임시 디렉터리> [PR 번호]`.
# PR 번호의 기본값 118 은 병합된 PR 이라 브랜치가 지금 브랜치와 달라 지나간다. gh 와 인증이 든다.
set -eu
root=$(cd "$(dirname "$0")/../../../.." && pwd)
scratch="${1:?임시 디렉터리를 준다}"
pr="${2:-118}"
mkdir -p "$scratch"
scratch="$(cd "$scratch" && pwd)"
rm -rf "$scratch/origin.git" "$scratch/unpushed"
git init -q --bare -b chore/x "$scratch/origin.git"
git init -q -b chore/x "$scratch/unpushed"
git -C "$scratch/unpushed" -c user.name=t -c user.email=t@t commit -q --allow-empty -m pushed
git -C "$scratch/unpushed" remote add origin "$scratch/origin.git"
git -C "$scratch/unpushed" push -q -u origin chore/x
git -C "$scratch/unpushed" -c user.name=t -c user.email=t@t commit -q --allow-empty -m unpushed

# 페이로드의 cwd 는 훅을 띄운 쪽의 경로다. Git Bash 의 `pwd` 는 `/c/...` 꼴이라 파이썬 자식의 cwd 로
# 쓰면 OSError 로 지나간다(첫 판에서 local 이 silent 였다). Windows 면 `pwd -W` 로 `C:/...` 를 넘긴다.
native() { (cd "$1" && { pwd -W 2>/dev/null || pwd; }); }
root_cwd=$(native "$root")
unpushed_cwd=$(native "$scratch/unpushed")
other="{\"tool_input\": {\"command\": \"git status --short\"}, \"cwd\": \"$root_cwd\"}"
local="{\"tool_input\": {\"command\": \"gh pr ready\"}, \"cwd\": \"$unpushed_cwd\"}"
gh="{\"tool_input\": {\"command\": \"gh pr ready $pr\"}, \"cwd\": \"$root_cwd\"}"
for label in other local gh; do
  eval "payload=\$$label"
  for i in 1 2 3 4 5; do
    start=$(date +%s%N)
    out=$(printf '%s' "$payload" | uv run --project "$root" --no-sync python "$root/tools/hook_pr_head_sync.py")
    end=$(date +%s%N)
    case "$out" in *deny*) verdict=deny ;; "") verdict=silent ;; *) verdict=other ;; esac
    echo "$label $(( (end - start) / 1000000 ))ms $verdict"
  done
done
