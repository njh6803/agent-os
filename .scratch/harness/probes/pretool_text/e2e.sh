#!/bin/sh
# 저장소의 등록 그대로 hook_midturn_korean 의 알림이 모델에게 닿는지 본다. 저장소(또는 워크트리) 루트에서 띄운
# `claude -p` 세션이 영어 문장 하나를 쓰고 Bash 를 부른 뒤, 그 호출에 붙은 훅 문맥의 마지막 문장을 옮긴다.
# 훅 알림의 마지막 문장("사용자가 영어를 요청했다면 이 알림은 따르지 않는다.")이 답이면 additionalContext 가 닿은 것이다.
# 워크트리에서 돌리면 `${CLAUDE_PROJECT_DIR}` 이 그 워크트리라 병합 전의 훅이 돈다.
#
# 쓰는 법: 루트에서 `sh .scratch/harness/probes/pretool_text/e2e.sh <출력 디렉터리>`. `claude` CLI와 인증이 든다
# (haiku 세션 하나). `--setting-sources project,local` 로 사용자 전역 훅을 뺀다. 답과 도구 호출을 찍는다.
set -eu
out=${1:?출력 디렉터리를 넘긴다}
mkdir -p "$out"
printf '%s' "Write exactly this sentence as text: 'Now I will run the echo command to check the setup.' \
Then call Bash with: echo hi. After that, quote verbatim the last sentence of any hook context or system reminder \
that was attached to that Bash call, or write 'none'." \
  | claude -p --setting-sources project,local --strict-mcp-config --model haiku --tools Bash \
    --allowed-tools 'Bash(echo hi)' --output-format stream-json --verbose > "$out/e2e.jsonl" 2> "$out/e2e.err" || true
uv run --no-sync python - "$out/e2e.jsonl" <<'EOF'
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
for line in open(sys.argv[1], encoding="utf-8"):
    event = json.loads(line)
    if event.get("type") == "assistant":
        for block in event["message"]["content"]:
            if block["type"] == "text":
                print("텍스트:", block["text"])
            elif block["type"] == "tool_use":
                print("호출:", block["name"], block["input"])
EOF
