"""run.sh 의 G 변형(대조군)이 Stop 에 등록하는 훅. Stop 에 `additionalContext` 를 내면 대화가
이어지는지 본다.

래퍼(tools/launch_hook.py)는 Stop 에서 `additionalContext` 를 내지 않는다(대기열 93). 그 근거인
"대화를 잇는다"를 문서만이 아니라 세션으로 재려고 둔다. 처음 한 번만 내고, 받은 Stop 입력의
`stop_hook_active` 를 환경 변수 `PROBE_LOG` 의 파일에 한 줄씩 적는다. 두 번째부터는 아무것도 내지
않아 끝없이 잇지 않는다.
"""

from __future__ import annotations

import json
import os
import sys

payload = json.load(sys.stdin.buffer)
log = os.environ.get("PROBE_LOG")
seen = 0
if log:
    if os.path.exists(log):
        with open(log, encoding="utf-8") as f:
            seen = len(f.readlines())
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"stop_hook_active={payload.get('stop_hook_active')}\n")
if seen == 0:
    context = "대조군 알림이다. 이 문구를 받았으면 '대조군 알림을 받았습니다' 라고 한 줄 더 답한다."
    output = {"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": context}}
    print(json.dumps(output, ensure_ascii=False))
