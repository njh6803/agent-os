# ds-upload-markdown-cards: 디자인 시스템을 다시 올려 마크다운 부품을 웹에 싣고 지난 산출 목록을 바꾼다

**What to build:** harness 티켓 `ds-bundle-escape-replacement-char`(PR #560)가 짓기 명령이 U+FFFD를 이스케이프로 쓰게 고쳤다. 그 PR이 dev에 병합되었으니 `/sync-design-system 올리기`를 `origin/dev`의 분리 HEAD에서 다시 해, 2026-11-10 뒤에 더한 마크다운 부품(카드 `Markdown`)을 웹의 디자인 시스템에 싣는다. 올리기 절차는 `.claude/skills/sync-design-system/upload.md`이고, 이 브랜치는 그 절차 1의 돌아갈 브랜치다. 올린 뒤 바뀌는 지난 산출 목록 `web/tools/sync-design-system/previous-output.json`을 같은 절차 6의 6의 첫 갈래대로 이 브랜치에 싣고, 대기열 항목을 닫는다.

**대기열:** ds-upload-replacement-char-rejected

**Status:** in-progress

## 수용 기준

- [ ] 올리기가 Artifact 도구에 거부되지 않고 끝났고, 보낸 뒤 확인이 `clean`이다
- [ ] 아티팩트의 Components 절에서 카드가 모두 그려지는지 앱 안 브라우저로 봤다(절차 6의 6의 "카드")
- [ ] `previous-output.json`이 이번 산출의 경로 목록과 같다
- [ ] 대기열 항목 `ds-upload-replacement-char-rejected`를 `.scratch/retro-queue/README.md`의 닫힘 꼴로 닫았다
