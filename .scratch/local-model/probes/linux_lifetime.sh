#!/bin/sh
# 리눅스 컨테이너 안에서 openai_compat.py 의 사례를 돈다. 수명 사례(cases_lifetime.py)를 리눅스의
# 이벤트 루프로 다시 재려고 둔다. /repo 는 읽기 전용으로 붙인 워크트리이고 /out 은 출력 폴더다.
# 컨테이너 밖(저장소 루트, Git Bash)에서 이렇게 부른다. 이미지는 python:3.12.10-slim-bookworm 이다.
#
#   MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd -W):/repo:ro" -v "<출력 폴더>:/out" \
#     python:3.12.10-slim-bookworm sh /repo/.scratch/local-model/probes/linux_lifetime.sh <사례 이름…>
#
# 사례 이름이 없으면 108 사례 전부를 돈다. 출력 폴더에는 uname.txt, list.txt, lifetime.jsonl(사례마다의
# JSON 줄 전부), stdout.txt(화면 출력), stderr.txt, exit.txt(프로브의 종료 코드)가 생긴다. 이 스크립트도
# 프로브의 종료 코드로 끝나므로 docker run 의 종료 코드가 그 값이다. 출력 폴더를 지우지 않는다.
# 환경은 openai_compat.py 를 Windows 에서 돌리는 make_env.py 와 같은 판이다.
# 저장소 락의 런타임 의존(dev 제외)을 깔고 그 위에 langchain-openai==1.6.2 를 얹는다.
# 2026-11-12 명세 검토가 세션 스크래치패드에서 지어 돈 판을 옮겼고, PR 직전 리뷰가 끝의 세 줄로
# 프로브의 종료 코드를 넘기게 고쳤다(일지 2026-11-12-2214).
set -e
export PYTHONDONTWRITEBYTECODE=1
pip install -q uv==0.10.8
cd /repo
uv export --frozen --no-emit-project --no-hashes -q --no-dev -o /tmp/runtime.txt
uv export --frozen --no-emit-project --no-hashes -q -o /tmp/all.txt
uv venv -q /tmp/env --python /usr/local/bin/python3.12
uv pip install -q --python /tmp/env/bin/python -r /tmp/runtime.txt -c /tmp/all.txt langchain-openai==1.6.2
uname -a > /out/uname.txt
/tmp/env/bin/python /repo/.scratch/local-model/probes/openai_compat.py --list > /out/list.txt
set +e
/tmp/env/bin/python /repo/.scratch/local-model/probes/openai_compat.py --out /out/lifetime.jsonl "$@" > /out/stdout.txt 2> /out/stderr.txt
rc=$?
echo "exit=$rc" > /out/exit.txt
exit "$rc"
