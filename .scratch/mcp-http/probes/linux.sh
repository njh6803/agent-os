#!/bin/sh
# Linux 컨테이너 안에서 `http_close.py`를 돌린다. 저장소 루트를 /repo 에 읽기 전용으로 붙여 띄운다
# (프로브가 `tools/probe_kit.py`를 저장소 루트에서 가져온다). 띄우는 명령은 같은 폴더의 README.md 에
# 있다. 인자는 그대로 프로브에 넘긴다(사례 이름). 환경 하나를 /tmp 에 만들고 판은 저장소의 uv.lock 과
# 같게 고정한다(mcp 2.3.0, anyio 4.15.1, uvicorn 0.53.0, starlette 1.6.0, httpx2 2.13.0).
set -u
cd /tmp || exit 1
pip install -q --root-user-action=ignore uv==0.10.8 || exit 1
export UV_PYTHON_DOWNLOADS=never
uv venv /tmp/env -q --python 3.12 || exit 1
uv pip install -q --python /tmp/env/bin/python mcp==2.3.0 anyio==4.15.1 uvicorn==0.53.0 \
    starlette==1.6.0 httpx2==2.13.0 || exit 1
PYTHONUTF8=1 /tmp/env/bin/python /repo/.scratch/mcp-http/probes/http_close.py "$@"
echo "exit $?"
