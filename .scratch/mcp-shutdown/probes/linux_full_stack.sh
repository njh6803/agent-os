#!/bin/sh
# Linux 컨테이너 안에서 full_stack.py 를 돌린다. 저장소 루트를 /repo 에 읽기 전용으로 붙여 띄운다.
# 띄우는 명령은 같은 폴더의 README.md 에 있다. 사본과 그 .venv 는 컨테이너의 /tmp 에 만든다.
# 첫 인자를 주면 그 폴더를 사본의 원본으로 쓴다(다른 커밋의 트리를 따로 붙였을 때). 없으면 /repo 다.
# pyright 가 내려받는 node 는 libatomic1 을 요구하는데 slim 이미지에는 없다(첫 회차가 종료 코드
# 127 로 그것을 보였다). 그래서 먼저 설치한다.
set -u
apt-get update -qq >/dev/null && apt-get install -y -qq libatomic1 >/dev/null || exit 1
pip install -q --root-user-action=ignore uv==0.10.8 || exit 1
export UV_PYTHON_DOWNLOADS=never
python /repo/.scratch/mcp-shutdown/probes/full_stack.py --source "${1:-/repo}"
echo "exit $?"
