# ds-bundle-escape-replacement-char: 디자인 시스템 묶음 파일이 U+FFFD를 이스케이프로 쓰게 해 올리기가 거부되지 않게 한다

**What to build:** `/sync-design-system 올리기`가 짓는 묶음 파일(`_ds_bundle.js`, `components/bundle.js`)에 U+FFFD(바꿈 문자)가 이스케이프 없이 들어, 2026-11-13에 Artifact 도구가 보내기를 거부했다. 그래서 웹의 디자인 시스템에는 2026-11-10 이후 더한 마크다운 부품이 빠져 있다. 먼저 그 글자가 산출의 어느 자리에 들고 어느 패키지에서 오는지 재현해 확인하고, 짓기 설정(`web/tools/sync-design-system/assemble.ts`의 `libConfig`)이 그 글자를 `\uFFFD` 이스케이프로 쓰게 고친다(원인이 다르면 실제 원인에 맞게 고친다). 산출에 그 글자가 그대로 들지 않는다는 시험을 먼저 실패하게 쓰고 통과시킨다. 올리기를 다시 해서 마크다운 부품을 올리는 일은 이 티켓 밖이다(아래 "이 티켓 밖").

**재현(2026-11-13).** 고치기 전의 `assemble`을 돌리니 산출 804개 가운데 `components/bundle.js`와 `_ds_bundle.js`(같은 바이트) 둘에만 U+FFFD가 그대로 들었고, 자리는 두 곳이었다. 하나는 숫자 문자 참조를 푸는 `micromark-util-decode-numeric-character-reference@2.0.2`(`index.js` 29행 `return "\uFFFD"`), 다른 하나는 주소를 정규화하는 `micromark-util-sanitize-uri@2.0.1`(`index.js` 89행 `replace = "\uFFFD"`)다. 두 원본 모두 이스케이프로 썼고, vite 8.3.1의 rolldown 1.2.11 압축이 템플릿 리터럴 안에 글자 그대로 썼다. 대기열 항목의 어림(마크다운 해석 코드, 두 자리)이 맞았다.

**고친 것.** `libConfig`가 rolldown의 `output.minify`를 `{ compress: true, mangle: true, codegen: { asciiOnly: true } }`로 덮는다(`MINIFY`). 압축과 이름 줄이기는 vite의 기본과 같고, 코드 생성만 ASCII 밖의 글자를 이스케이프로 쓴다. 고친 뒤에는 묶음 JS와 카드의 장면에 ASCII 밖의 글자가 없고, 두 자리는 `` `\uFFFD` ``이며, 묶음 JS는 190,035바이트에서 190,209바이트가 됐다. 카드의 장면도 같은 설정으로 지어져 스토리의 한국어 글이 이스케이프되므로, 카드 열 개가 모두 12~28% 커졌다(가장 큰 Markdown이 14,823바이트에서 18,917바이트, 한도 256,000바이트 안). 그래서 다음 올리기는 카드 열 개를 모두 다시 보낸다. 크기는 고치기 전과 뒤의 산출을 `wc -c`로 손으로 쟀다.

**대기열:** ds-upload-replacement-char-rejected

**Status:** done

## 수용 기준

**이 티켓 밖.** 올리기는 이 PR이 dev에 병합된 뒤 `origin/dev`의 분리 HEAD에서 한다(`.claude/skills/sync-design-system/upload.md` 1). 올린 뒤 바뀌는 지난 산출 목록(`web/tools/sync-design-system/previous-output.json`, 마크다운 카드의 두 경로가 더해진다)은 티켓을 가리키는 브랜치에만 실린다(같은 절차 6의 6). 병합 뒤 이 워크트리에서 그냥 올리면 돌아갈 브랜치가 이미 병합된 이 티켓의 브랜치가 되어, 6의 6의 첫 갈래가 병합된 티켓을 다시 여는 자리에 목록을 싣게 된다. 그래서 병합 뒤에는 `origin/dev`에서 새 harness 티켓의 `chore/<slug>` 브랜치를 따 그 티켓을 먼저 커밋하고, 그 브랜치를 돌아갈 브랜치로 삼아 올린다. 목록은 6의 6의 첫 갈래대로 그 브랜치에 싣고, 대기열 항목은 그 PR이 닫는다.

- [x] 짓기 산출에서 U+FFFD가 이스케이프 없이 드는 자리와 그 글자가 온 패키지를 재현해 이 티켓에 적었다
- [x] `web/tools/sync-design-system/assemble.test.ts`에 산출에 U+FFFD가 그대로 들지 않는다는 시험이 있고, 고치기 전에 실패하는 것을 봤다
- [x] 짓기 설정을 고쳐 그 시험이 통과하고, chromium으로 묶음과 카드를 그리는 같은 파일의 시험도 초록이며, `CLAUDE.md`의 검증 명령이 초록이다
- [x] 대기열 항목 `ds-upload-replacement-char-rejected`의 본문에 반영한 몫을 적고 열어 두었다
