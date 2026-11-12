#!/usr/bin/env bash
# 티켓 01 의 단위 시험이 구현보다 먼저 빨강을 본 적이 없는 규칙에 변이를 넣어 시험이 빨개지는지 본다(implement 스킬의 변이 절).
# 파일 하나를 sed 로 바꾸고 시험을 돌린 뒤 원본으로 되돌린다. 기대: 변이마다 vitest 의 실패 집계가 `failed` 를 든다.
# 변이가 파일을 바꾸지 못했으면 측정이 아니라고 적는다. 되돌리기는 변이마다 바로 하고, 끊겼을 때를 위해 trap 도 둔다.
# 쓰는 법: bash mutate_unit_tests.sh  (어느 폴더에서든)
set -u
ROOT="$(git rev-parse --show-toplevel)"
UI="$ROOT/web/packages/ui/src"
BACKUP="$(mktemp -d)"
CURRENT_FILE=""
CURRENT_BACKUP=""
NOT_MEASURED=0
restore() { if [ -n "$CURRENT_BACKUP" ] && [ -f "$CURRENT_BACKUP" ]; then cp "$CURRENT_BACKUP" "$CURRENT_FILE"; fi; }
cleanup() { restore; rm -rf "$BACKUP"; }
trap cleanup EXIT

run_mutation() {
  local label="$1" file="$2" from="$3" to="$4"
  CURRENT_FILE="$file"
  CURRENT_BACKUP="$BACKUP/current"
  cp "$file" "$CURRENT_BACKUP"
  sed -i "s#$from#$to#" "$file"
  if cmp -s "$file" "$CURRENT_BACKUP"; then
    echo "MEASURE-NONE $label: 변이가 파일을 바꾸지 못했다"
    NOT_MEASURED=$((NOT_MEASURED + 1))
    return
  fi
  local out
  out="$(pnpm -C "$ROOT/web" exec vitest run --project node --project ui-pages packages/ui/src 2>&1)"
  cp "$CURRENT_BACKUP" "$file"
  # 변이가 코드를 깨뜨려 파일을 읽지 못한 실행은 시험이 규칙에서 빨개진 것이 아니다. 측정 아님으로 센다.
  if echo "$out" | grep -qE 'SyntaxError|Transform failed|Failed to resolve|Cannot find module|Failed to parse'; then
    echo "MEASURE-NONE $label: 변이가 파일을 읽지 못하게 했다(시험이 아니라 불러오기가 실패했다)"
    NOT_MEASURED=$((NOT_MEASURED + 1))
    return
  fi
  # 어느 시험이 빨개졌는지 첫 줄을 함께 찍는다. 의도한 규칙의 시험인지는 읽는 쪽이 이 줄로 본다.
  echo "RESULT $label: $(echo "$out" | grep -E 'Tests +' | tr -s ' ') / 첫 실패: $(echo "$out" | grep -m1 -E '^ FAIL ' | tr -s ' ')"
  CURRENT_BACKUP=""
  CURRENT_FILE=""
}

run_mutation "user-info-allowed" "$UI/markdown/link-url.ts" 'url.username !== "" || url.password !== ""' 'false'
run_mutation "depth-limit-raised" "$UI/markdown/plugin.ts" 'MAX_CONTAINER_DEPTH = 10;' 'MAX_CONTAINER_DEPTH = 100;'
run_mutation "allow-list-off" "$UI/markdown/options.ts" '  allowedElements: ALLOWED_ELEMENTS,' ''
run_mutation "table-no-focus" "$UI/components/molecules/Markdown.tsx" 'aria-label="표" tabIndex={0}' 'aria-label="표"'
run_mutation "link-hidden-text-off" "$UI/components/molecules/Markdown.tsx" '<span className="sr-only">(새 탭에서 열림)</span>' ''
run_mutation "link-rel-off" "$UI/components/molecules/Markdown.tsx" 'rel="noopener noreferrer"' ''
run_mutation "soft-break-off" "$UI/markdown/plugin.ts" '    softBreaksToBreaks(tree);' ''
run_mutation "url-transform-off" "$UI/markdown/options.ts" 'urlTransform: (url: string): string => linkHref(url) ?? "",' 'urlTransform: (url: string): string => url,'

# 측정 아님이 하나라도 있으면 종료 코드를 0으로 두지 않는다(결론은 측정인 회차만으로 낸다).
if [ "$NOT_MEASURED" -gt 0 ]; then
  echo "측정 아님 ${NOT_MEASURED}회: 위 MEASURE-NONE 줄을 본다"
  exit 1
fi
