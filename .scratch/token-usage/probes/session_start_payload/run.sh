#!/bin/sh
# SessionStart 훅이 받는 입력을 대화형 세션과 `claude -p` 세션에서 잰다(티켓 04의 헤드리스 가르기).
# 탐침 훅(`dump_session_start.py`)을 `--settings` 로만 붙인다. 헤드리스 갈래는 저장소 밖의 빈
# 디렉터리에서 `--setting-sources project,local` 로 사용자 전역 훅을 빼고 돈다(선례
# `.scratch/harness/probes/stop_payload/run.sh`). 대화형 갈래는 이 스크립트가 설정만 쓰고 명령을
# 찍는다. 그 명령을 사람이나 세션이 터미널에서 대화형으로 띄우고, 시작 화면이 뜨면 프롬프트를 보내지
# 않고 끈다. 대화형은 신뢰한 폴더에서만 훅이 돌므로 그 명령은 저장소 루트에서 띄운다. 끈 뒤 찍힌 확인
# 명령으로 대화형 갈래의 줄을 단언한다.
#
# 쓰는 법: 저장소 루트에서 `sh .scratch/token-usage/probes/session_start_payload/run.sh <저장소 밖 디렉터리의 절대 경로>`.
# 결과는 그 디렉터리의 `start.jsonl`(훅이 받은 것, 갈래마다 한 줄)과 `out.json`(claude -p 의 결과)이다.
# 이 스크립트는 인자 폴더의 `start.jsonl` 을 지우고 설정 파일을 덮어쓴다. 그래서 인자를 검사한다
# (`.claude/rules/probes.md`, 선례 `.scratch/harness/probes/worktree_duplicate_checkout.sh`).
#   - 절대 경로(`/…`, 또는 Windows 계열 셸에서 `C:/…`)가 아니면 종료 2 로 멈춘다.
#   - 이미 있는 폴더는 비어 있거나 이 스크립트가 심은 표지 파일(.session_start_payload_probe)이 있을 때만 쓴다.
# 종료 코드: 0 이면 헤드리스 갈래의 줄이 표지(SessionStart, startup, ATTENDED 변수)를 모두 지났다.
# 1 이면 측정이 아니다(`check_start.py`). 2 면 인자가 안전하지 않아 아무것도 하지 않았다.
set -u
LC_ALL=C
export LC_ALL
work="${1:-}"
marker=".session_start_payload_probe"

case "$work" in
  /*) ;;
  [A-Za-z]:[/\\]*)
    # 드라이브 문자 경로는 Windows 계열 셸에서만 절대 경로다. POSIX 에서는 현재 폴더 아래의 상대 경로다.
    case "$(uname -s 2>/dev/null || :)" in
      CYGWIN*|MINGW*|MSYS*) ;;
      *) echo "인자가 절대 경로가 아니다: 아무것도 하지 않았다" >&2; exit 2 ;;
    esac
    ;;
  *) echo "인자가 절대 경로가 아니다: 아무것도 하지 않았다" >&2; exit 2 ;;
esac
if [ -e "$work" ]; then
  if [ ! -d "$work" ]; then
    echo "폴더가 아니다: 아무것도 하지 않았다" >&2
    exit 2
  fi
  if [ ! -f "$work/$marker" ] && [ -n "$(ls -A "$work")" ]; then
    echo "비어 있지 않고 이 스크립트의 표지가 없는 폴더다: 아무것도 하지 않았다" >&2
    exit 2
  fi
fi

here=$(cd "$(dirname "$0")" && pwd) || exit 9
root=$(cd "$here/../../../.." && pwd) || exit 9
mkdir -p -- "$work" || exit 9
: > "$work/$marker" || exit 9
work=$(cd "$work" && pwd) || exit 9
rm -f -- "$work/start.jsonl" || exit 9
for label in headless interactive; do
  hook="uv run --project \\\"$root\\\" --no-sync python \\\"$here/dump_session_start.py\\\" \\\"$work/start.jsonl\\\" $label"
  cat > "$work/settings-$label.json" <<EOF || exit 9
{"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "$hook", "timeout": 30}]}]}}
EOF
done
(
  cd "$work" || exit 9
  claude -p --setting-sources project,local --settings "$work/settings-headless.json" --model haiku \
    --output-format json "Reply with the single word OK." > "$work/out.json"
)
echo "대화형 갈래: 저장소 루트에서 claude --settings \"$work/settings-interactive.json\""
echo "끈 뒤 확인: uv run python \"$here/check_start.py\" \"$work/start.jsonl\" interactive"
uv run --project "$root" --no-sync python "$here/check_start.py" "$work/start.jsonl" headless
