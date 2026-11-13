# ds-upload-markdown-cards: 디자인 시스템을 다시 올려 마크다운 부품을 웹에 싣고 지난 산출 목록을 바꾼다

**What to build:** harness 티켓 `ds-bundle-escape-replacement-char`(PR #560)가 짓기 명령이 U+FFFD를 이스케이프로 쓰게 고쳤다. 그 PR이 dev에 병합되었으니 `/sync-design-system 올리기`를 `origin/dev`의 분리 HEAD에서 다시 해, 2026-11-10 뒤에 더한 마크다운 부품(카드 `Markdown`)을 웹의 디자인 시스템에 싣는다. 올리기 절차는 `.claude/skills/sync-design-system/upload.md`이고, 이 브랜치는 그 절차 1의 돌아갈 브랜치다. 올린 뒤 바뀌는 지난 산출 목록 `web/tools/sync-design-system/previous-output.json`을 같은 절차 6의 6의 첫 갈래대로 이 브랜치에 싣고, 대기열 항목을 닫는다.

**대기열:** ds-upload-replacement-char-rejected

**Status:** done

## 수용 기준

- [x] 올리기가 Artifact 도구에 거부되지 않고 끝났고, 보낸 뒤 확인이 `clean`이다. 이 `clean`은 웹 편집을 가르는 확인 명령의 결과이고, 카드가 그려지는지는 다음 기준에서 따로 봤다. 결과를 본 뒤 이 기준의 거부를 이 티켓이 닫으려던 U+FFFD 거부로 좁혀 읽고 체크했다. 그 거부는 없었다. 다른 까닭의 거부가 두 번 있었다("You haven't viewed the latest version of this artifact"). 좁혀 읽은 까닭은 둘이다. 그 두 거부는 아티팩트 종류의 페이지 파일이 판을 올려 난 것이라 이 티켓의 고침과 상관이 없고, 같은 내용을 세 번째에 보내 받아들여졌다(아래 결과)
- [x] 아티팩트의 Components 절에서 카드가 모두 그려지는지 앱 안 브라우저로 봤다(절차 6의 6의 "카드"). 아홉 개는 그려지고 Markdown 카드는 깨졌다. 고칠 일은 `.scratch/answer-markdown/issues/04-markdown-card-renders-on-react-18.md`다
- [x] `previous-output.json`이 이번 산출의 경로 목록과 같다
- [x] 대기열 항목 `ds-upload-replacement-char-rejected`를 `.scratch/retro-queue/README.md`의 닫힘 꼴로 닫았다

## 결과

- 확인 `clean`, 결정 `upload`. 기록의 `commit`(`9bf65c75f`)은 `origin/dev`(`ad7dff584`)의 조상이다. 산출은 804개 파일과 카드 열 개이고, 계획은 보낼 파일 16개(묶음 넷, 카드 열 개, `components/Markdown/README.md`, `guidelines/web-design.md`), 지울 경로 0개, 호출 하나였다. `project/README.md`가 보낼 파일에 없어 옮기기 절은 묻지 않았다.
- 첫 보내기 직전에 아티팩트 판이 `1794510674-1f19`에서 `1794576423-43d5`로 바뀌었다. 두 판의 파일 목록(862개)을 눈으로 견줘 찾은 차이는 아티팩트 종류의 페이지 파일(`artifact-type/app.css`, `artifact-type/app.js`)의 바이트였다(손으로 봤다. 줄마다 도구로 대 보지는 않았다). 그 판에서 확인이 받는 파일 17개는 앞 판과 같았고, 이번에 덮어쓸 13개 파일의 sha256도 기록과 같았다. 거부마다 절차대로 확인부터 다시 했고, 둘째 거부 뒤 `url`만 준 `read`(페이지 읽기)를 한 다음 넷째 확인을 거쳐 보낸 것이 받아들여졌다(판 41 `1794576819-4601`). `paths`를 준 읽기만으로는 도구가 최신 판을 본 것으로 치지 않은 것으로 보인다(두 번 거부된 결과에서 낸 어림이다). `url`만 준 `read`는 SKILL.md "보내기"가 따르지 말라고 한 도구 안내의 "다시 읽기" 몫이다. 합치지는 않았고, 넷째 확인이 첫 확인과 같아 웹 편집을 덮지 않았다. 확인이 깨끗한데도 도구가 최신 판을 보지 않았다고 거부하는 갈래가 절차에 없어 회고 후보로 남긴다.
- 보낸 뒤 확인 `clean`. 앱 안 브라우저(사람이 claude.ai에 로그인해 주었다)로 Components 절을 봤다. Button, Card, Icon, IconButton, Progress, StatusBadge, Alert, Switch, TextField는 그려지고 칸 아래가 잘리지 않았다. Markdown 칸에는 "This preview could not run: a script it needs did not load, or threw while loading. Showing the static preview."가 떴다. 원인의 어림과 근거는 04 티켓에 적었다. 절차대로 되돌리지 않았다.
