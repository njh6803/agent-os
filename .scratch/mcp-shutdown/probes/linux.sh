#!/bin/sh
# Linux 컨테이너 안에서 닫기 프로브를 돌린다. 이 폴더를 /probes 에 읽기 전용으로 붙여 띄운다.
# 띄우는 명령은 같은 폴더의 README.md 에 있다. 첫 인자는 프로브(close_paths 또는 serve_shutdown)이고
# 나머지는 사례다. 환경 둘(mcp 1.30.0 대조군, mcp 2.3.0)을 /tmp 에 만들어 대조군을 한 번, 2.3.0 을
# 런처 없이·런처(kill)·런처(watch)로 세 번 돈다. 프로브가 1로 끝나도 다음을 돈다. 사례를 주지 않으면
# close_paths 의 대조군은 cancel·exit_child_normal·close_fails·cli_ctrl_c·cli_ctrl_c_twice 이고
# 나머지는 사례 전부다. close_paths 는 끝에 셸(bash)이 보는 종료 코드 둘을 찍는다. 처리하지 않은
# KeyboardInterrupt 로 끝난 파이썬과, 처리기의 시제품처럼 SIGINT 를 기본 처리로 되돌려 자기에게
# 보낸 파이썬이다.
set -u
cd /tmp || exit 1
probe="/probes/$1.py"
shift
pip install -q --root-user-action=ignore uv==0.10.8 || exit 1
export UV_PYTHON_DOWNLOADS=never
for version in 1.30.0 2.3.0; do
    env="/tmp/env-$version"
    uv venv "$env" -q --python 3.12 || exit 1
    uv pip install -q --python "$env/bin/python" "mcp==$version" anyio==4.15.1 \
        uvicorn==0.53.0 starlette==1.6.0 || exit 1
done
if [ "$#" -eq 0 ] && [ "$probe" = /probes/close_paths.py ]; then
    /tmp/env-1.30.0/bin/python "$probe" cancel exit_child_normal close_fails cli_ctrl_c \
        cli_ctrl_c_twice
else
    /tmp/env-1.30.0/bin/python "$probe" "$@"
fi
echo "exit $?"
for launcher in none kill watch; do
    /tmp/env-2.3.0/bin/python "$probe" --launcher "$launcher" "$@"
    echo "exit $?"
done
if [ "$probe" = /probes/close_paths.py ]; then
    bash -c '/tmp/env-2.3.0/bin/python -c "raise KeyboardInterrupt" 2>/dev/null
echo "shell: unhandled KeyboardInterrupt $?"'
    bash -c '/tmp/env-2.3.0/bin/python -c "import os, signal
signal.signal(signal.SIGINT, signal.SIG_DFL)
os.kill(os.getpid(), signal.SIGINT)"
echo "shell: SIG_DFL then SIGINT to self $?"'
fi
