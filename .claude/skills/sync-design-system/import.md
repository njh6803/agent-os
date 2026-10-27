# 들이기

`/sync-design-system`의 들이기다. 아티팩트의 웹 편집을 디자인 토큰 CSS(`web/packages/ui/src/styles/theme.css`)와 저장소 파일에 옮기고, 티켓 하나와 PR 하나로 병합한 뒤 올리기로 아티팩트를 코드에 다시 맞춘다. 명령, 작업 폴더, "확인", "찾았을 때", "보내기"는 [SKILL.md](SKILL.md)의 그 절이다.

들이기 하나에 티켓 하나다. 이름은 `NN-web-edit-<slug>`, 브랜치는 `feature/NN-web-edit-<slug>`이고, 번호는 `origin/main`의 `.scratch/design-reverse-sync/issues/`에서 가장 큰 번호의 다음이다(`git fetch origin` 뒤 `git ls-tree --name-only origin/main .scratch/design-reverse-sync/issues/`). 들이기끼리는 `claim`으로 한 번에 하나만 돈다.

## 1. 자리

확인(`--caller import`)부터 한다. 결정이 `import`나 `inheritImport`면 지금 자리를 가른다.

- **이 들이기의 티켓 브랜치다**(지금 브랜치가 `feature/NN-web-edit-<slug>` 꼴이고, 그 이름의 티켓 파일 `NN-web-edit-<slug>.md`가 `origin/main`의 이 폴더에 없다). 번호와 slug는 그 이름의 것을 쓰고 2로 간다. "먼저 들인다"가 연 세션은 첫 턴에 지시문의 워크트리 문장대로 브랜치를 지시문의 이름으로 이미 바꿨으므로 여기다. 그 이름의 티켓이 `origin/main`에 있으면 병합된 앞 들이기의 브랜치라 아래 "다른 작업의 브랜치"다.
- **주 체크아웃의 main이다**(`git rev-parse --show-toplevel`이 `git worktree list`의 첫 줄과 같고 `git branch --show-current`가 `main`이다). 번호와 slug를 정하고 `EnterWorktree`(name은 `NN-web-edit-<slug>`)로 새 워크트리에 들어가, [SKILL.md](SKILL.md) "명령과 작업 폴더"의 설치를 친 뒤 `git branch -m feature/NN-web-edit-<slug>`로 브랜치 이름을 바꾼다. 확인부터 다시 한다.
- **새 워크트리다**(`git rev-list --count origin/main..HEAD`가 0이고 `git status --porcelain`이 비었다). 번호와 slug를 정하고, 설치를 아직 치지 않았으면 쳐서 `git branch -m feature/NN-web-edit-<slug>`. 확인부터 다시 한다.
- **다른 작업의 브랜치다.** 브랜치를 바꾸지 않는다. [SKILL.md](SKILL.md)의 "먼저 들인다"로 새 세션을 열고, 지금 세션은 하던 일로 돌아간다.

끝: 지금 브랜치가 이 들이기의 티켓 브랜치이고, 그 브랜치에서 돈 확인의 결정이 `import`나 `inheritImport`다. 새 들이기는 늘 자기 새 브랜치에서 확인부터 한다. 병합된 브랜치에서 이어받지 않는 것도 그래서다(결정표가 그 자리를 `stop`으로 낸다).

## 2. 티켓

코드를 고치기 전에 `.scratch/design-reverse-sync/issues/NN-web-edit-<slug>.md`를 쓴다. 그 파일이 이미 있으면(쓴 뒤 `claim`을 쓰기 전에 끊겼다) 새로 쓰지 않고 거기에 이어 적는다. 꼴은 이 폴더의 다른 티켓(제목 줄, `**What to build:**`, `**Blocked by:**`, `**Status:** in-progress`, 체크박스)이다. 절은 넷이다.

- **찾은 웹 편집.** 확인 보고의 디자인 토큰(벌, 전과 후)과 디자인 토큰 밖 파일.
- **사람이 고른 것.** 고를 때마다 `> 사용자:` 인용으로 더한다.
- **판정 결과.** 걸린 짝과 고른 값.
- **수용 기준.** 검증 명령이 모두 초록이다, 사진을 다시 만들었는지, PR을 열기 직전과 병합 직전에 기록을 다시 읽어 `claim`이 자기 것인지 본다, 고친 디자인 토큰 CSS가 `pnpm -C web verify`의 포맷 검사를 지난다. 병합은 이 스킬을 거치지 않을 수 있어, 다시 읽기를 티켓에 둔다.

## 3. claim 쓰기

1. 기록을 다시 받는다(`read`의 `paths`에 `project/sync-record.json`, `claim-<n>/again.json`으로 복사).
2. `record claim --record claim-<n>/again.json --expect check-<n>/web/project/sync-record.json --out send-<n>/project/sync-record.json --check check-<n>/check.json --web check-<n>/web --branch <지금 브랜치> --ticket <티켓 경로> --at <시각>`. 결정이 `inheritImport`면 `--inherit <보고의 inherit>`를 더한다. 두 기록의 `claim`이 다르다는 `input` 오류면 그사이 다른 세션이 쓴 것이라 확인부터 다시 한다.
3. [SKILL.md](SKILL.md)의 "보내기"로 그 기록 하나를 보낸다.
4. 확인을 다시 돌린다. 결과가 `importing`이고 `claim.own`이 true이며 결정이 `resumeImport`여야 한다. 아니면 다른 세션이 덮은 것이라 멈추고 보고의 `claim.branch`를 사람에게 알린다.

## 4. 들이기 명령

1. `record base --record check-<n>/web/project/sync-record.json --out <작업 폴더>/base.json`(`check-<n>`은 3의 마지막 확인이다). 기준본은 `claim`이 이어받은 기준본이 있으면 그것, 아니면 기록의 기준본이다. `claim`의 사본은 기준본이 아니다.
2. `git show HEAD:web/packages/ui/src/styles/theme.css > <작업 폴더>/theme.committed.css`. 들이기 명령은 늘 이 파일을 `--css`로 받아 다시 돈다. 고친 CSS 위에 다시 돌면 옮긴 값이 코드 쪽 바뀜으로 섞인다.
3. `import --web check-<n>/web/project/tokens.json --base <작업 폴더>/base.json --css <작업 폴더>/theme.committed.css --out web/packages/ui/src/styles/theme.css [--answers <작업 폴더>/answers.json] > <작업 폴더>/import.json`.
4. 보고의 `asked`와 `contrast.failures`를 사람에게 묻고(아래), 답을 `answers.json`(`{"<자리 id>": "web" | "code" | "suggested"}`)에 적어 3을 다시 친다. 끝: 답을 적은 마지막 실행의 `contrast.failures`가 비었고, `asked`에 남은 것은 모두 사람이 이미 고른 것이다(답 파일로 답하지 않는 묻는 것은 다시 돌려도 남는다). 그 전에는 커밋하지 않는다. 걸린 값은 고를 때까지 커밋하지 않고 올리기도 막힌다.
5. 사람이 들이기로 고른 묻는 것(대응 바꾸기 등)은 4가 끝난 뒤 세션이 디자인 토큰 CSS를 손으로 고친다. 갈래와 시험은 `.claude/rules/web-design.md`의 대응과 덮기 문단대로다.

묻는 것은 [SKILL.md](SKILL.md)의 "찾았을 때"처럼 보이고 AskUserQuestion으로 묻는다. 꼴의 원천은 `web/tools/sync-design-system/import.ts`의 "답"과 `Asked`의 독스트링이다.

- **코드와 웹이 다르게 바꾼 자리**(`conflict`). "웹 값", "코드 값", "웹에서 다시 고친다". `webReason`이 null이 아니면 스크립트가 웹 값을 옮기지 못하는 자리라, 사람이 웹 값을 고르면 답 파일에 `web`을 적지 않고 세션이 5처럼 고친다.
- **명암비에 걸린 자리**(`contrast.failures`). 걸린 짝과 실제 명암비, 제안 값을 보이고 "제안 값으로 들인다"(`suggested`, 제안 값이 null이면 내지 않는다), "그 디자인 토큰만 코드 값으로 되돌린다"(`code`), "웹에서 다시 고친다"로 묻는다. 걸린 웹 값을 그대로 쓰는 선택지는 내지 않는다. 코드와 웹이 다르게 바꾼 자리는 `web`을 고른 실행에서야 판정되어 제안이 나므로, 답을 고친 실행 뒤마다 `failures`를 다시 본다.
- **그 밖의 묻는 것**(`mapping`, `partial`, `alias`, `added`·`removed`, `typeField`, `familyNote` 등). 보고의 까닭을 보이고 "들인다"(세션이 5처럼 고친다), "코드 값을 둔다", "웹에서 다시 고친다"로 묻는다. 더하기와 지우기가 한 계열에 함께 있으면 "이름을 바꾼 것일 수 있다"를 함께 적는다.
- **디자인 토큰 밖 편집**(확인 보고의 `files` 가운데 `tokens.json` 밖, `index`). 무엇이 바뀌었는지 보이고 "저장소 파일에 옮긴다"와 "버린다"로 묻는다. 옮기는 것은 그 파일을 짓는 저장소 원본을 평소처럼 고치는 일이다. 지침 문서 `project/guidelines/web-design.md`의 원본은 Claude Code의 규칙 파일 `.claude/rules/web-design.md`라 바뀐 곳을 보이고 사람과 문장을 정해 고친다. "버린다"를 고른 편집은 병합 뒤의 올리기가 코드의 판으로 되돌린다.

**웹에서 다시 고친다.** 사람에게 웹에서 다시 고친 뒤 알려 달라고 하고 턴을 끝낸다. 알리면 확인을 다시 돌리고, 3으로 자기 `claim`의 사본과 해시를 새로 쓴 뒤 4를 1부터 다시 한다.

## 5. 함께 고치는 것과 검증

- 크기(글자 크기·줄 높이·굵기, 간격, 모서리)를 바꾸면 그 값을 글자 그대로 박아 둔 스토리 단언(`web/packages/ui/src`를 그 값으로 grep한다)도 같은 PR에서 고친다.
- 기본 테마(녹청)가 쓰는 값(녹청의 원색, 반투명, 크기)을 바꾸면 `pnpm -C web visual:update`로 정답 사진을 다시 만들고, 바뀐 사진을 사람이 보고 PR 본문에 적는다(`.claude/rules/web-design.md`).
- 티켓의 수용 기준과 `CLAUDE.md`의 검증 명령, 커밋 전의 `/code-review`는 다른 티켓과 같다.

## 6. PR과 병합

1. **PR을 열기 직전.** `git fetch origin` 뒤 번호를 다시 본다. 같은 번호가 `origin/main`에 먼저 들어왔으면 다음 번호로 옮긴다. 차례는 티켓 파일(`git mv`와 그 안의 번호), 브랜치 이름(`git branch -m`), `claim` 다시 쓰기다. 다시 쓰기는 확인의 `check judge`에 `--branch`로 새 이름이 아니라 `claim`이 든 옛 브랜치를 주고, 그 보고로 3의 `record claim`을 새 브랜치와 새 티켓 경로로 친다. 새 이름을 주면 확인이 자기 `claim`을 남의 것으로 본다. 그러면 더 고친 몫이 없을 때는 `record claim`이 이어받을 기준본을 요구하며 멈추지만, 있을 때는 멈추지 않고 남의 `claim` 이어받기로 가서 기준본이 바뀐다. 브랜치를 바꾼 뒤 `claim`을 다시 쓰기 전에 끊기면, 이어받은 세션의 확인은 옛 이름의 `claim`을 PR 없는 남의 `claim`으로 묻는다. `claim`의 브랜치가 지금 브랜치와 slug가 같고 번호만 다르면 그 틈이라고 함께 알린다. 명세 "자기 `claim`"의 2026-10-22 주석이 드문 틈이라 질문 하나로 받은 자리다.
2. 확인을 다시 돌려 `claim.own`이 true인지 본다(옮기지 않았어도 친다). 아니면 PR을 열지 않고 멈춰 그 브랜치를 사람에게 알린다. 그 뒤 `/git-pr`로 연다.
3. **병합 직전.** 같은 다시 읽기를 한 번 더 한다. 병합은 `next-session`의 병합 절차대로다.
4. **병합 뒤.** 이어서 [upload.md](upload.md)의 올리기를 한다. 그 올리기가 `claim`을 비운다. 병합과 올리기 사이에도 `claim`이 남아, 병합 전의 코드를 든 다른 세션이 같은 편집을 새 웹 편집으로 보지 않는다.

## 이어 하기

결정이 `resumeImport`면 자기 `claim`의 들이기를 잇는다(압축이나 인계 뒤). 지금 브랜치의 티켓과 커밋을 보고 끊긴 단계부터 잇는다. 확인 보고의 `further`가 비지 않았으면 `claim` 뒤에 사람이 더 고친 것이다. 그 몫을 보이고 3으로 자기 `claim`을 새로 쓴 뒤 4를 1부터 다시 한다. PR이 열려 있으면 6부터다.
