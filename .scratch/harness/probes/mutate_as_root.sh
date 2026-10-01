#!/bin/sh
# tests/tools/test_mutate.py 를 root(uid 0)인 리눅스 컨테이너에서 돌린다(대기열 80).
#
# 사용: 저장소 루트에서 sh .scratch/harness/probes/mutate_as_root.sh [이미지] [pytest 인자 ...]
# 윈도우의 Git Bash 와 Docker Desktop(리눅스 컨테이너)을 가정한다. 이미지는 python3 과 pydantic 이
# 든 리눅스 이미지이고 기본값은 이웃 저장소가 남긴 것이다. 이미지를 내려받지 않는다(--pull never,
# 로컬에 없으면 실패한다). pytest 와 그 플러그인은 이 체크아웃의 .venv(uv sync)에서 순수 파이썬
# 패키지만 골라 붙인다. 저장소와 .venv 는 읽기 전용으로 붙여, 테스트가 그 둘에 쓰지 않는다는 것도
# 함께 본다. 첫 줄에 uid 와 파이썬·pydantic·pytest 의 판을 찍는다.
# 대조군은 PROBE_USER=10001 sh .scratch/harness/probes/mutate_as_root.sh 처럼 root 가 아닌 uid 로 돈다.
set -eu

user="${PROBE_USER:-0}"

image="${1:-agent-runtime-platform-api:latest}"
[ $# -gt 0 ] && shift

repo="$(pwd -W 2>/dev/null || pwd)"
site="$repo/.venv/Lib/site-packages"
if [ ! -d "$site" ]; then
  echo "$site 가 없다. 저장소 루트에서 uv sync 뒤에 돌린다" >&2
  exit 2
fi

inner='
set -eu
mkdir -p /tmp/pure
for name in pytest _pytest pluggy iniconfig packaging pygments pytest_asyncio py.py; do
  cp -r "/site/$name" /tmp/pure/
done
for info in /site/pytest-*.dist-info /site/pytest_asyncio-*.dist-info /site/pluggy-*.dist-info; do
  cp -r "$info" /tmp/pure/
done
export PYTHONPATH=/tmp/pure PYTHONDONTWRITEBYTECODE=1
echo "uid $(id -u) $(python3 -c "import platform, pydantic, pytest
print(\"python\", platform.python_version(), \"pydantic\", pydantic.VERSION, \"pytest\", pytest.__version__)")"
cd /repo
python3 -m pytest -q -p no:cacheprovider tests/tools/test_mutate.py "$@"
'

MSYS_NO_PATHCONV=1 docker run --rm --pull never --user "$user" \
  -v "$repo:/repo:ro" -v "$site:/site:ro" \
  --entrypoint sh "$image" -c "$inner" sh "$@"
