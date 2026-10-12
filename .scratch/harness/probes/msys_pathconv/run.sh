#!/usr/bin/env bash
# Git Bash(MSYS)가 네이티브 프로그램에 넘기는 인자 가운데 무엇을 경로(목록)로 바꾸는지 잰다.
# 저장소 루트에서 `bash .scratch/harness/probes/msys_pathconv/run.sh` 로 돈다. Git Bash 에서만 뜻이 있다.
#
# A. 모양마다 기본 셸과 `MSYS_NO_PATHCONV=1` 아래에서 네이티브 프로그램(uv 가 띄운 python)이 받은 인자.
#    한 호출에 모두 넘긴다. 변환은 인자마다 따로 일어난다. A2 는 탭과 개행이 든 모양이다.
# B. 같은 모양을 MSYS 프로그램(/usr/bin/printf, /usr/bin/echo)에 넘긴 것.
# C. git 이 실제로 실패하는지와 우회 셋이 지나가는지. 종료 코드를 찍는다. 기본 git show 의 오류에
#    바뀐 인자가 없으면(다른 까닭의 실패) 1로 끝난다.
set -u
# 윈도 경로(C:/…)로 둔다. `/c/…` 로 부르면 MSYS_NO_PATHCONV=1 아래에서 파이썬이 argv.py 를 못 찾는다.
here=$(cd "$(dirname "$0")" && pwd -W)

# 앞 묶음은 일지의 옛 가설(콜론 양쪽에 `/`)을 가르는 것, 뒤 묶음은 tools/hook_bash_msys_pathconv.py 의
# 판정 조건을 하나씩 건드리는 것이다. 그 테스트의 표가 이 출력을 옮긴다.
shapes=(
  'origin/main:.scratch/retro-queue.md'
  'origin/main:README.md'
  'a76107e:.scratch/retro-queue.md'
  'HEAD:src/agent_os/main.py'
  'origin/main:src/agent_os/main.py'
  'origin/main:src'
  'HEAD~1:tools/canary.py'
  'feature/x:feature/x'
  'HEAD:refs/heads/chore/x'
  'refs/heads/a:refs/remotes/origin/a'
  'a/b:c/d'
  'a/b:c'
  'a:b/c'
  'a/b:c/d:e/f'
  'a/b:c:d/e'
  'origin/main:./src/x.py'
  'https://github.com/a/b'
  'git@github.com:njh6803/agent-os.git'
  'localhost:8000/api'
  '/c/project:/d/x'
  '--format=a/b:c/d'
  'x=a/b:c/d'
  'C:/project/agent'
  '@{u}:src/x.py'
  ':src/x.py'
  ':/message'
  'origin/main:.scratch'
  'origin/main:.env.example'
  'origin/main:.github/workflows/ci.yml'
  'origin/main:/x'
  'origin/main://x'
  'origin/main:../x'
  'origin/main::.x'
  'origin/main:.x::y'
  'HEAD~1:.scratch/x.md'
  'main:.scratch/x.md'
  'origin/main:.scratch/*.md'
  'origin/main:.scratch/[x].md'
  'origin/main:.scratch/x.md:y'
  'origin/main@{1}:.scratch/x.md'
  'origin/~x:.y'
  'a@@b/c:.d'
  '~/x:.y'
  '+refs/heads/a:.b'
  'origin\main:.x'
  '..:.x'
  'x=origin/main:.x'
  'x=y:origin/main:.x'
  '--format=origin/main:.x'
  '-Lorigin/main:.x'
  'see origin/main:.x'
  'fix: origin/main:.x'
  'a b/c:.d e'
  'origin/main:.sc`x'
  "origin/main:.sc'x"
  'origin/main:.scratch/x?.md'
  'a:b=origin/main:.x'
  '-Lx:origin/main:.y'
  '-x,origin/main:.y'
  'origin/main:.gitignore'
  '+//:/'
  '%//:/'
  '@/a:.b'
)

echo "== A. 네이티브(uv → python). 모양 | 기본 | MSYS_NO_PATHCONV=1"
default=$(uv run python "$here/argv.py" "${shapes[@]}")
disabled=$(MSYS_NO_PATHCONV=1 uv run python "$here/argv.py" "${shapes[@]}")
expected=${#shapes[@]}
for column in "$default" "$disabled"; do
  lines=$(printf '%s\n' "$column" | wc -l)
  if [ "$lines" -ne "$expected" ]; then
    echo "실패: 모양 $expected 개인데 받은 줄이 $lines 개다. argv.py 가 돌지 않았다" >&2
    exit 1
  fi
done
# 변환이 실제로 일어났다는 전제. Git Bash 가 아닌 bash(WSL 등)면 두 열이 같아 아무것도 재지 못한다.
case $(printf '%s\n' "$default" | head -1) in
  *';'*) ;;
  *)
    echo "실패: 첫 모양이 바뀌지 않았다. Git Bash(MSYS) 가 아닌 셸이다" >&2
    exit 1
    ;;
esac
paste -d '|' <(printf '%s\n' "${shapes[@]}") <(printf '%s\n' "$default") <(printf '%s\n' "$disabled")

echo "== A2. 네이티브. 탭과 개행이 든 모양(A 의 표에 두면 줄이 갈린다). 받은 것을 차례로"
uv run python "$here/argv.py" $'see\torigin/main:.x' $'see\norigin/main:.x'

echo "== B. MSYS 프로그램(/usr/bin/printf, /usr/bin/echo). 모양 | 받은 것"
/usr/bin/printf '%s|%s\n' 'origin/main:.scratch/retro-queue.md' 'origin/main:.scratch/retro-queue.md' \
  'a/b:c/d' 'a/b:c/d'
/usr/bin/echo "origin/main:.scratch/retro-queue.md|$(/usr/bin/echo 'origin/main:.scratch/retro-queue.md')"

echo "== C. git 의 종료 코드. 기본 git show 는 실패의 까닭(바뀐 인자)이 오류에 있는지도 본다"
show_error=$(git show 'origin/main:.scratch/retro-queue.md' 2>&1 > /dev/null)
echo "git show 기본: $?"
case $show_error in
  *"origin\\main;.scratch\\retro-queue.md"*) ;;
  *)
    echo "실패: git show 의 오류에 바뀐 인자가 없다. 다른 까닭으로 실패했다: $show_error" >&2
    exit 1
    ;;
esac
quiet_output=$(git rev-parse --verify --quiet 'origin/main:.scratch/retro-queue.md' 2>&1)
echo "rev-parse --verify --quiet 기본: $?, 출력 ${#quiet_output}자"
MSYS_NO_PATHCONV=1 git rev-parse --verify --quiet 'origin/main:.scratch/retro-queue.md' > /dev/null
echo "MSYS_NO_PATHCONV=1: $?"
MSYS2_ARG_CONV_EXCL='*' git rev-parse --verify --quiet 'origin/main:.scratch/retro-queue.md' > /dev/null
echo "MSYS2_ARG_CONV_EXCL='*': $?"
git rev-parse --verify --quiet 'origin/main:./.scratch/retro-queue.md' > /dev/null
echo "콜론 뒤에 ./ (저장소 루트에서): $?"
git rev-parse --verify --quiet 'origin/main:README.md' > /dev/null
echo "왼쪽에만 / (origin/main:README.md): $?"
