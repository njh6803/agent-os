# ds-upload-markdown-react-18-fix: 디자인 시스템을 다시 올려 React 18에서 그려지는 마크다운 카드를 웹에 싣는다

**What to build:** 기능 `answer-markdown`의 티켓 04(PR #564, dev 병합 커밋 `db2c888d1`)가 `Markdown.tsx`의 컨텍스트 제공자를 `.Provider` 꼴로 고쳐 디자인 시스템 페이지가 싣는 React 18.3.1에서도 Markdown 카드가 그려지게 했다. 그러나 웹의 디자인 시스템 아티팩트는 아직 고치기 전 묶음이라 Components 절의 Markdown 칸에는 "This preview could not run..." 문구만 뜬다. `/sync-design-system 올리기`를 `origin/dev`의 분리 HEAD에서 해 고친 부품을 아티팩트에 싣고, 앱 안 브라우저로 Markdown 카드가 장면을 그리고 칸 아래가 잘리지 않는지 손으로 본다. 올리기 절차는 `.claude/skills/sync-design-system/upload.md`이고, 이 브랜치는 그 절차 1의 돌아갈 브랜치다. 올린 뒤 바뀌면 지난 산출 목록 `web/tools/sync-design-system/previous-output.json`을 같은 절차 6의 6의 첫 갈래대로 이 브랜치에 싣는다. 앞의 올리기 티켓은 `.scratch/harness/issues/ds-upload-markdown-cards.md`다. 카드가 여전히 안 그려지면 오류 모양을 일지에 적고 멈춰 사용자에게 알린다.

**대기열:** 없음

**Status:** done

## 수용 기준

- [x] 올리기가 끝까지 보내졌고(Artifact 도구가 거부하면 확인부터 다시 해 웹 편집이 없음을 보고, 같은 내용을 `force` 없이 다시 보낸다), 보낸 뒤 확인이 `clean`이다. 첫 보내기가 "You haven't viewed the latest version of this artifact"로 한 번 거부됐고(아티팩트 판은 `1794621629-6da7` 그대로였다), 확인을 처음부터 다시 해 앞 확인과 같음을 본 뒤 같은 내용을 다시 보내 받아들여졌다(판 43 `1794636666-d3b5`). 앞 티켓이 적은 것과 같은 갈래다
- [x] 아티팩트의 Components 절에서 Markdown 카드가 장면을 그리고 칸 아래가 잘리지 않는지 앱 안 브라우저로 봤다(절차 6의 6의 "카드"). 열 카드가 모두 그려졌고 Markdown 칸도 그려졌으며 마지막 출처 줄이 잘리지 않았다. 본 것은 일지 `docs/journal/2026-11-14-1512-ds-upload-markdown-react-18-fix.md`에 적었다
- [x] `previous-output.json`이 이번 산출의 경로 목록과 같다(`cmp`로 같아 바꾸지 않았다)
- [x] 검증 명령이 모두 초록이다(이 브랜치는 문서만 바꿨다. `.py`가 없어 pre-commit의 ruff가 `Skipped`일 수 있어 `uv run ruff check .`와 `uv run ruff format --check .`는 손으로 쳐 통과를 봤다. 나머지 손으로 치는 명령은 이 커밋의 pre-commit 결과로 갈음하고 그 결과는 PR 본문에 적는다. `-m llm`·e2e·사진 비교는 코드를 건드리지 않아 치지 않았다)
