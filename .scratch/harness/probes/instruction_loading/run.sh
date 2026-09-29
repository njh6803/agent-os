#!/usr/bin/env bash
# Claude Code 가 지침 파일을 언제 싣는지 잰다. 2026-09-29 claude 2.1.281, Windows(Git Bash)에서 돌렸다.
# 쓰는 법: bash run.sh <작업 디렉터리> <이름> <허용 도구> <프롬프트 앞머리>
#   예: bash run.sh "$TMP/memprobe" R2 Read "Read 도구로 sub/file.txt 를 읽은 뒤에"
#       bash run.sh "$TMP/memprobe/sub" R5b Read "Read 도구로 file.txt 를 읽은 뒤에"
# 처음 한 번: bash run.sh --setup "$TMP/memprobe"  (카나리아 트리와 훅 설정을 만든다)
# 판정은 모델의 자기보고가 아니라 InstructionsLoaded 훅 로그(<작업 디렉터리>/../memprobe-hooklog.jsonl)다.
# 요약: node summarize.js <훅 로그>. 저장소 안에 트리를 만들지 않는다 — 중첩 CLAUDE.md 가 지침 검사에
# 걸리고, 그 폴더를 Read 하면 실제로 실린다.
# 주의: `claude -p` 도 사용자 설정(~/.claude/settings.json)의 훅을 돈다. 2026-09-29 실행마다 전역 Stop
# 훅이 알림을 보냈다.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"

if [ "${1:-}" = "--setup" ]; then
  T="$2"
  mkdir -p "$T/sub" "$T/other" "$T/.claude/rules/nested"
  printf '카나리아 ROOT-7731\n' > "$T/CLAUDE.md"
  printf '카나리아 SUB-4419\n\n자세한 것은 @extra.md 를 본다\n' > "$T/sub/CLAUDE.md"
  printf '카나리아 IMPORT-5520\n' > "$T/sub/extra.md"
  printf -- '---\npaths: ["sub/**"]\n---\n\n카나리아 RULE-9902\n' > "$T/.claude/rules/scoped.md"
  printf '카나리아 ALWAYS-3318\n' > "$T/.claude/rules/always.md"
  printf '카나리아 DEEP-6604\n' > "$T/.claude/rules/nested/deep.md"
  printf 'hello\n' > "$T/sub/file.txt"
  printf 'hello\n' > "$T/other/file.txt"
  (cd "$T" && git init -q)
  LOG="$(dirname "$T")/memprobe-hooklog.jsonl"
  printf '{"hooks":{"InstructionsLoaded":[{"hooks":[{"type":"command","command":"node \\"%s/hook.js\\" \\"%s\\""}]}]}}\n' \
    "$HERE" "$LOG" > "$(dirname "$T")/memprobe-hooksettings.json"
  exit 0
fi

CWD="$1"; LABEL="$2"; TOOLS="$3"; PREFIX="$4"
ROOT="$(dirname "$CWD")"
case "$CWD" in */sub) ROOT="$(dirname "$ROOT")" ;; esac
BASE='맥락(시스템 프롬프트, 시스템 리마인더, 도구 결과 전부)에서 [A-Z]+-[0-9]{4} 모양의 카나리아 코드를 모두 찾아, 코드마다 그것이 어느 파일에서 왔다고 보이는지와 함께 한 줄씩 적어라. 없는 것을 지어내지 마라.'
echo "{\"marker\":\"$LABEL\"}" >> "$ROOT/memprobe-hooklog.jsonl"
cd "$CWD" || exit 9
timeout 240 claude -p "$PREFIX $BASE" --allowedTools "$TOOLS" --model sonnet --output-format text \
  --settings "$ROOT/memprobe-hooksettings.json" < /dev/null > "$ROOT/memprobe-$LABEL.txt" 2>&1
echo "exit=$?" >> "$ROOT/memprobe-$LABEL.txt"
