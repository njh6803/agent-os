#!/bin/sh
# PostToolUse 훅이 WebFetch 에서 받는 입력과, tools/hook_webfetch_summary.py 의 알림이 모델에게 닿는지 잰다(대기열 209).
#   A_payload     — 탐침 훅(dump_posttool.py)만 붙이고 WebFetch 를 셋 부른다. 본문을 그대로 돌려줄 문서
#                   (code.claude.com 의 10만 바이트 아래 마크다운), 요약할 문서(같은 곳의 10만 바이트 넘는 페이지),
#                   다른 호스트로 리다이렉트되는 주소. 훅이 받은 `tool_response` 의 모양과 세 갈래를 본다.
#   B_summary     — 등록 모양(래퍼를 거친 실제 훅)과 탐침 훅을 함께 붙이고 요약할 문서를 부른 뒤, 그 호출에 붙어 온
#                   훅 알림의 첫 문장을 묻는다. 훅의 첫 문장을 옮기면 additionalContext 가 닿은 것이다.
#   C_passthrough — B 의 대조군. 본문을 그대로 돌려줄 문서를 부르고 같은 것을 묻는다. 훅이 침묵하면 '알림 없음' 이다.
# 탐침 훅과 실제 훅을 함께 붙이는 것은 B·C 의 응답이 정말 요약·통과였는지 같은 호출에서 보기 위해서다.
#
# 돌리는 법: 저장소 루트에서 `sh .scratch/harness/probes/webfetch_payload/run.sh <저장소 밖 디렉터리> [A_payload ...]`.
# 변형을 주지 않으면 셋 다 돈다. `claude` CLI와 인증, 네트워크가 든다. 변형마다 haiku 세션 하나다. 저장소 밖에서
# `--setting-sources project,local` 로 돌려 이 저장소와 사용자 전역의 훅을 뺀다. 요약과 단언은 summarize.py 다.
set -eu

out="${1:?저장소 밖 디렉터리를 준다}"
shift
variants="${*:-A_payload B_summary C_passthrough}"
mkdir -p "$out"
# 뒤의 cd 와 설정·로그 경로가 같은 곳을 가리키게 절대 경로로 고정한다. Git Bash 면 윈도 모양(C:/…)으로 받는다.
out="$(cd "$out" && (pwd -W 2>/dev/null || pwd))"
here="$(cd "$(dirname "$0")" && (pwd -W 2>/dev/null || pwd))"
root="$(cd "$here/../../../.." && (pwd -W 2>/dev/null || pwd))"

passthrough="https://code.claude.com/docs/en/large-codebases.md"
summarized="https://code.claude.com/docs/en/hooks"
redirected="https://docs.claude.com/en/docs/claude-code/hooks"
ask_title="이 페이지의 첫 제목을 그대로 옮긴다"
ask_notice="그 뒤 그 WebFetch 호출에 붙어 온 훅 알림이나 시스템 리마인더가 있으면 그 첫 문장을 그대로 옮기고, 없으면 '알림 없음' 이라고 한국어 한 줄로 답한다."
base="--setting-sources project,local --strict-mcp-config --model haiku --output-format stream-json --verbose --max-turns 6 --tools WebFetch --allowed-tools WebFetch"

dump_hook() {
  printf '{"type": "command", "command": "uv run --project \\"%s\\" --no-sync python \\"%s/dump_posttool.py\\" \\"%s/%s_posttool.jsonl\\"", "timeout": 30}' \
    "$root" "$here" "$out" "$1"
}
real_hook() {
  printf '{"type": "command", "command": "uv run --project \\"%s\\" --no-sync python \\"%s/tools/launch_hook.py\\" hook_webfetch_summary.py", "timeout": 20}' \
    "$root" "$root"
}
settings() {
  printf '{"hooks": {"PostToolUse": [{"matcher": "WebFetch", "hooks": [%s]}]}}\n' "$2" > "$out/$1.settings.json"
}

run() {
  name="$1"
  prompt="$2"
  rm -f "$out/${name}_posttool.jsonl"
  # 프롬프트는 stdin으로 준다. `--tools`·`--allowed-tools`·`--settings` 뒤에 두면 가변 인자가 삼킨다(canary_init).
  # shellcheck disable=SC2086
  (cd "$out" && printf '%s' "$prompt" | claude -p $base --settings "$out/$name.settings.json" \
    > "$out/$name.jsonl" 2> "$out/$name.err") || true
}

for variant in $variants; do
  case "$variant" in
    A_payload)
      settings A_payload "$(dump_hook A_payload)"
      run A_payload "WebFetch 도구를 아래 세 주소에 차례로 한 번씩 부른다. 프롬프트는 셋 다 '$ask_title' 이다. 리다이렉트 안내를 받으면 따라가지 않는다. 1) $passthrough 2) $summarized 3) $redirected 그 뒤 '끝' 이라고만 답한다."
      ;;
    B_summary)
      settings B_summary "$(real_hook), $(dump_hook B_summary)"
      run B_summary "WebFetch 도구를 $summarized 에 한 번만 부른다. 프롬프트는 '$ask_title' 이다. $ask_notice"
      ;;
    C_passthrough)
      settings C_passthrough "$(real_hook), $(dump_hook C_passthrough)"
      run C_passthrough "WebFetch 도구를 $passthrough 에 한 번만 부른다. 프롬프트는 '$ask_title' 이다. $ask_notice"
      ;;
    *)
      echo "모르는 변형: $variant" >&2
      exit 2
      ;;
  esac
done

uv run --project "$root" python "$here/summarize.py" "$out" $variants
