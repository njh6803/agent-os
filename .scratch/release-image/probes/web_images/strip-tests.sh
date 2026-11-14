#!/bin/sh
# 이미지 안의 사본에서 앱의 시험·스토리·e2e 파일을 지운다(저장소의 파일은 그대로다). next build 의 타입 검사는 앱의
# tsconfig 가 드는 파일 전부를 보므로, 이 파일들이 남아 있으면 시험 쪽 패키지(vitest, storybook 등)의 타입이 있어야 한다.
# .storybook 의 선언 파일(*.d.ts)은 남긴다. 위젯의 element/index.ts 가 쓰는 `*.css?inline` 의 모양을
# .storybook/css-inline.d.ts 가 선언해, 그것까지 지우면 운영 빌드의 타입 검사가 TS2307 로 멈췄다(첫 판에서 봤다).
# 사용: strip-tests.sh <앱 폴더(절대 경로)>
#
# 폴더를 지우는 스크립트라 저장소의 앱 폴더를 잘못 받아도 지우지 않게 둘을 막는다. 절대 경로가 아니면 멈추고,
# 그 폴더나 윗 폴더에 .git 이 있으면(저장소 체크아웃이다) 멈춘다. 이미지 안의 사본은 web/ 만 복사하므로 .git 이 없다.
set -eu
app="$1"
case "$app" in
  /*) ;;
  *) echo "RI_PROBE refused: 절대 경로가 아니다 app=$app" >&2; exit 2 ;;
esac
test -f "$app/package.json"
dir="$app"
while [ "$dir" != "/" ] && [ -n "$dir" ]; do
  if [ -e "$dir/.git" ]; then
    echo "RI_PROBE refused: 저장소 체크아웃이다(.git 이 $dir 에 있다) app=$app" >&2
    exit 2
  fi
  dir=$(dirname "$dir")
done
find "$app" -type f \
  \( -name '*.test.ts' -o -name '*.test.tsx' -o -name '*.test-d.ts' -o -name '*.stories.tsx' \) \
  -not -path '*/node_modules/*' -delete
if [ -d "$app/.storybook" ]; then
  find "$app/.storybook" -type f -not -name '*.d.ts' -delete
fi
rm -rf "$app/e2e" "$app/testing" "$app/visual" "$app/playwright.config.ts"
echo "RI_PROBE stripped app=$app left=$(find "$app" -type f \( -name '*.ts' -o -name '*.tsx' \) -not -path '*/node_modules/*' | wc -l)"
