# 05: 첫 정식 올리기로 Components 절에 카드 아홉이 뜨고 배너가 사라진다

**What to build:** 04가 병합된 main에서 `/sync-design-system 올리기`를 돌아 디자인 시스템 아티팩트(https://claude.ai/artifact/8ttLDZQqchfD2ao1XG56GH)에 첫 정식 올리기를 한다. 올린 뒤 사람이 페이지를 열면 지금의 "No components yet." 대신 Components 절에 카드 아홉이 그려지고, 테마 메뉴에서 '… 다크 (Dark)'를 고르면 카드가 다크로 그려진다. "No move is perfect" 배너와 "Finish setting up" 단추가 보이지 않고, Files 보기에 옛 카드 파일(`components/<무리>/<이름>/…`, `_preview/`, `_vendor/`, `_ds_sync.json`)이 남지 않는다. 다 보낸 뒤 바뀐 지난 산출 목록을 이 티켓의 브랜치에 커밋한다. 04가 병합된 뒤 다른 세션의 올리기가 첫 정식 올리기를 먼저 했으면(04의 "What to build"), 이 티켓은 그 결과를 페이지에서 확인하고 목록을 맞추는 것으로 닫는다. 이 기능의 마지막 티켓이다.

근거는 `.scratch/design-card-build/spec.md`의 "티켓의 차례" 마지막 줄, "올리기"("옛 별칭 지우기", "첫 정식 올리기와 `tokens.json`", "나누기", "`upgraded`", "보낸 뒤")와 그 자리들의 2026-10-29 명세 검토 주석, Further Notes의 "재지 않은 페이지 갈래"와 "페이지 판에 기대는 것"이다. 측정에 쓴 임시 Design System 아티팩트(https://claude.ai/artifact/64VW1b5F8tRcCeTZBwZA29)는 사용자가 남겨 두기로 한 것이라 지우지 않는다.

**Blocked by:** 04

**Status:** done

### 시작 전

- [x] 디자인 시스템 아티팩트를 Artifact 도구로 읽어 지금 계정이 주인이나 편집자인지 본다(`docs/agents/issue-tracker.md` 화면 디자인 절의 계정). 둘 다 아니면 멈추고 사람에게 알린다

### 올리기

- [x] `upload.md` 1의 자리(`origin/main`을 분리 HEAD로 체크아웃한 깨끗한 작업 트리)에서 절차대로 한다
- [x] **첫 정식 올리기가 아직이면.** 확인이 받은 기록의 `files`에 정식 자리의 카드(`project/components/<이름>/preview.html`)가 없으면 아래 둘을 본다.
  - 계획이 첫 정식 올리기로 보고 `tokens.json`을 보낼 파일에 넣는다
  - 계획의 지울 경로에 옛 별칭 48개(카드 36, `_preview/` 9, `_vendor/` 2, `_ds_sync.json`)가 모두 든다. 하나라도 빠지면 보내기 전에 멈추고 사람과 정한다. 실제 기록의 `files`에 그 48개가 드는지는 명세가 아티팩트를 읽지 않고 추론한 것이다(명세 "옛 별칭 지우기"의 주석)
- [ ] (해당 없음, 결과 2) **이미 끝났으면.** 기록의 `files`에 정식 카드가 이미 있으면 첫 정식 올리기는 끝났다. 기록의 `files`는 마지막 호출이 받아들여질 때만 새 배치로 바뀌므로(03), 이 티켓의 앞 시도가 마지막 호출까지 보낸 뒤 목록을 커밋하기 전에 끊겼거나 04 병합 뒤 다른 세션의 올리기가 먼저 한 것이다. 이때 계획은 첫 정식 올리기로 보지 않고 기록에 없는 옛 별칭을 지울 경로로 내지 않는 것이 맞다(03의 "목록만 옛것일 때"). 그래서 위 둘 대신 기록의 `files`에 옛 별칭이 하나도 없는지 확인하고, Artifact 도구 `list`의 `scope: "files"`로 실제 Files 목록에도 옛 별칭 48개가 하나도 없는지 확인한다. 기록에는 없는데 실제 목록에 남은 것이 있으면 티켓을 끝내지 말고 사람에게 알린다. 모두 없을 때만 절차를 끝까지 돈다. 보낼 것이 없으면 절차의 "보낼 것이 없을 때"에서 지난 산출 목록만 갱신한다. 누가 언제 올렸는지(색인의 `lastChange`)를 결과에 적고, 아래 "페이지 확인"과 "마무리"는 그대로 한다
- [x] 보낼 파일 수와 몫 수를 이 티켓의 결과에 적는다. 명세는 스물 남짓에 한 호출로 어림했다. 글꼴 파일을 다시 보내면 지난 산출 목록의 `fonts/`와 이름이 다른 까닭을 본다
- [x] README의 옮기기 절 물음은 절차대로 사람에게 묻고 답을 받기 전에는 보내지 않는다
- [x] 마지막 호출의 색인에 `libraries`(react·react-dom 18.3.1)와 `upgraded`가 들고 `source`가 남는다. 첫 정식 올리기가 이미 끝났으면 확인이 받은 색인에서 같은 셋을 본다
- [x] 보낸 뒤의 확인이 `clean`이다

### 페이지 확인

앱 안 브라우저로 디자인 시스템 아티팩트를 열어 손으로 본다. 본 것은 이 티켓의 결과에 화면에 무엇이 보였는지로 적는다.

- [x] Components 절에 카드 아홉이 있고, 카드마다 장면이 그려지며 칸 아래가 잘리지 않았다. 카드의 한글이 Noto Sans KR이다
- [x] 테마 메뉴에서 다크 테마를 고르면 카드가 다크(어두운 바탕, 어두운 폼 조작)로 그려지고, 테마 이름이 '(Light)'·'(Dark)'로 갈린다
- [x] "No move is perfect" 배너와 "Finish setting up" 단추가 보이지 않는다
- [x] Files 보기에 옛 카드 파일, `_preview/`, `_vendor/`, `_ds_sync.json`이 없다
- [ ] (해당 없음, 결과 8) 카드에서 글꼴이 빠졌으면 명세 Further Notes의 "재지 않은 페이지 갈래"(묶음 CSS를 주소로 싣는 갈래)를 먼저 본다
- [ ] (해당 없음, 결과 8) 깨진 카드가 있으면 되돌리지 않고 사람에게 알리며, 고칠 일을 `docs/agents/issue-tracker.md`의 규약대로 티켓으로 쓴다

### 마무리

- [x] 지난 산출 목록을 이번 올리기의 `--paths` 목록으로 바꿔 이 티켓의 브랜치에 커밋한다(`upload.md`의 "보낸 뒤"). 먼저 올린 다른 세션이 같은 목록을 이미 main에 넣었으면 커밋할 것이 없고, 그렇다고 결과에 적는다
- [x] 이 기능의 마지막 티켓이라, 병합할 때 `.scratch/plan.md`의 design-card-build 상태를 done으로 바꾼다
- [x] 검증 명령이 모두 초록이다. 모델 경로, 위젯, 관리 화면을 건드리지 않아 `-m llm`·`-m llm_widget`·e2e·사진 비교는 칠 일이 없다

### 결과

1. **계정과 자리.** Artifact 도구 read의 머리가 `writer`였다. 올리기는 `origin/main`(`fc54912a`)을 분리 HEAD로 꺼낸 깨끗한 워크트리에서 `upload.md` 1~6대로 했다. 확인은 `clean`, 결정은 `upload`였고, 기록의 `commit`(`84542f52`)은 HEAD의 조상이었다.
2. **첫 정식 올리기가 아직이었다.** 확인이 받은 기록의 `files`에 정식 자리의 카드는 0개, 옛 별칭은 48개였다. 앞 시도나 다른 세션이 먼저 올린 흔적은 없었다.
3. **산출과 계획.** 짓기 명령의 산출은 802파일, 카드 9개, 14,495,860바이트였다. 계획은 `firstCanonical`이 true였고, 보낼 파일 26개(`tokens.json` 포함)와 지울 경로 48개를 한 호출(몫 하나)에 실었다. 지울 경로는 카드 36, `_preview/` 9, `_vendor/` 2, `_ds_sync.json` 1로 티켓이 든 48개와 같았다. 명세의 어림(스물 남짓, 한 호출)과 맞는다. 글꼴 파일은 다시 보내지 않았고, `fonts/` 아래에서는 `fonts.css`만 보냈다.
4. **README의 옮기기 절.** 확인이 아티팩트에서 받은 README(보내기 전에 돈 두 번의 확인 사본)에 "## Migrated from the standalone version" 절이 없어 물을 것이 없었다. 두 사본에서 그 머리 문장을 `grep -c`로 세어 모두 0이었다.
5. **보낸 것.** 실제 publish에는 산출 26개와 기록(`sync-record.json`), 색인(`design-system.json`)의 28파일과 지울 경로 48개(null)를 실었다. 색인에는 `libraries`(react·react-dom 18.3.1)와 `upgraded`(`2026-10-30T03:42:10Z`)가 들고 `source`가 남았다. `lastChange.via`는 `agent-os main@fc54912a`이다.
6. **첫 publish의 거부.** 첫 publish는 "haven't viewed the latest version"으로 거부됐고 아무것도 보내지 않았다. 절차대로 확인을 처음부터 다시 돌렸더니 판(`1793331444-ea25`)은 바뀌었지만 기록 해시와 산출은 같았고 `clean`이었다. 경로 없이 `url`만 준 Artifact read의 결과에 Design System 형식의 새 릴리스(`1793316667-952a`)가 보여, 그 릴리스가 아티팩트의 판을 올린 것이 거부의 원인이라고 판단했다. read 결과를 손으로 보고 낸 판단이고, 판이 오른 시각과 릴리스 시각을 대 보지는 않았다. 그 read 뒤 같은 계획으로 다시 보내 받아들여졌다(Version 34, `1793331854-0395`).
7. **보낸 뒤.** 다시 돈 확인이 `clean`이었다. Artifact 도구 `list`의 `scope: "files"`로 본 Files 목록은 880개에서 852개가 됐고, 옛 별칭 48개는 하나도 남지 않았다.
8. **페이지에서 본 것.** 앱 안 브라우저로 2026-10-30에 봤다.
   - Components 절에 Button, Card, Icon, IconButton, Progress, StatusBadge, Alert, Switch, TextField의 아홉 카드가 있고 모두 장면이 그려졌다. 처음 열면 몇 카드(Button, IconButton, Alert, Switch, TextField)가 몇 초 동안 빈 칸이었다가 그려졌다. TextField 카드는 아래쪽 오류 문구 "거부 사유를 적어야 거부할 수 있습니다"와 두 번째 칸(채널 토큰)까지 칸 안에 보여 잘리지 않았다.
   - 카드의 한글이 Noto Sans KR로 그려졌는지는 확인하지 못했다. 스크린샷에서 고딕 계열로 그려진 것은 눈으로 봤다. 카드는 교차 출처 iframe 안에 있어, 앱 안 브라우저의 JavaScript가 계산된 글꼴 이름에 닿지 못했다(카드 iframe의 주소를 따로 열어도 아티팩트 껍데기 페이지로 넘어갔다). 코드로 본 것은 이렇다. 보낸 컴포넌트 묶음 CSS(`components/bundle.css`)가 `font-family:Noto Sans KR`을 선언하고(`grep -o`로 봤다), 글꼴 파일과 `fonts.css`가 Files 목록에 있다. 그래서 이 줄의 체크박스는 Noto Sans KR 부분만 확인하지 못한 채로 닫는다.
   - 테마 메뉴는 여덟 테마(녹청·군청·자조·쪽빛의 라이트와 다크)를 '(Light)'·'(Dark)'로 갈라 보였다. '녹청 다크 (Dark)'에서 카드가 어두운 바탕과 어두운 입력칸으로, '녹청 라이트 (Light)'로 바꾸면 밝은 바탕으로 그려졌다. 본 뒤 다크로 되돌렸다.
   - 페이지 맨 위에 "No move is perfect" 배너와 "Finish setting up" 단추가 없었다. 위 막대에는 공유 단추만 있었다.
   - 깨진 카드는 없어 고칠 티켓은 쓰지 않았다.
9. **목록.** 지난 산출 목록(`web/tools/sync-design-system/previous-output.json`)을 이번 산출의 `--paths` 목록으로 바꿨다. 옛 별칭 48줄이 빠지고 정식 카드의 README·preview 18줄과 컴포넌트 묶음 둘이 더해졌다.
10. **검증.** 커밋 `682f8e52`와 `3b594c63`의 pre-commit이 pyright·lint-imports·pytest·`web-verify`를 포함한 검사를 모두 Passed로 냈다(출력을 손으로 봤다, 일지 2026-10-30-12의 "커밋" 절). `.py`가 없어 `Skipped`였던 ruff 둘은 손으로 쳐 `All checks passed!`, `1181 files already formatted`였다. 모델 경로, 위젯, 관리 화면을 건드리지 않아 `-m llm`·`-m llm_widget`·e2e·사진 비교는 치지 않았다.
