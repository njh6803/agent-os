#!/usr/bin/env bash
# 임포트와 paths 의 경계 사례를 claude -p 로 잰다. 2026-09-29 claude 2.1.281, Windows(Git Bash)에서 돌렸다.
# 쓰는 법(저장소 루트에서): bash .scratch/harness/probes/import_comments/run.sh <저장소 밖의 빈 디렉터리>
# 판정은 모델의 자기보고가 아니라 InstructionsLoaded 훅 로그(<디렉터리>/hooklog.jsonl)다. 임포트는
# 시작 때, paths 규칙은 sub/file.txt 를 Read 할 때 실린다. --setting-sources project,local 로 사용자
# 전역 설정(훅의 알림 등)을 뺀다. 인증은 설정이 아니라 그대로 쓰인다.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
OUT="$1"
TREE="$OUT/tree"
LOG="$OUT/hooklog.jsonl"
mkdir -p "$OUT"
rm -rf "$TREE" "$LOG"
(cd "$REPO" && PYTHONUTF8=1 uv run python "$HERE/cases.py" build "$TREE") || exit 9
(cd "$TREE" && git init -q)
printf '{"hooks":{"InstructionsLoaded":[{"hooks":[{"type":"command","command":"node \\"%s\\" \\"%s\\""}]}]}}\n' \
  "$HERE/../instruction_loading/hook.js" "$LOG" > "$OUT/settings.json"
cd "$TREE" || exit 9
timeout 300 claude -p 'Read 도구로 sub/file.txt 를 읽어라. 다른 파일은 읽지 마라. 그 뒤 한 단어로 끝났다고만 답하라.' \
  --allowedTools Read --model haiku --output-format text \
  --setting-sources project,local --settings "$OUT/settings.json" < /dev/null > "$OUT/answer.txt" 2>&1
echo "exit=$?"
(cd "$REPO" && PYTHONUTF8=1 uv run python "$HERE/cases.py" summarize "$LOG")
