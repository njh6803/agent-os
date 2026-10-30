# 올리기

`/sync-design-system`의 올리기다. 코드(`web/packages/ui`, `web/tools/sync-design-system/`의 짓기 명령과 그 원본, `.claude/rules/web-design.md`)로 산출 전체를 짓고, 그 가운데 바뀐 파일만 아티팩트에 보내고 기록을 새로 쓴다. 명령, 작업 폴더, "확인", "찾았을 때", "보내기"는 [SKILL.md](SKILL.md)의 그 절이다. 화면 작업에서 "계속한다"를 골랐어도 올리기의 확인은 돈다.

## 1. 자리

올리기는 그 입력을 바꾼 PR이 main에 병합된 뒤, `origin/main`을 분리 HEAD로 체크아웃한 깨끗한 작업 트리에서 한다. 병합 전에 올리면 squash로 사라질 브랜치 커밋이 남고, 옛 HEAD로 올리면 그사이 병합된 변경이 빠진다.

- 주 체크아웃이면 `EnterWorktree`로 새 워크트리에 들어가 [SKILL.md](SKILL.md) "명령과 작업 폴더"의 설치를 친 뒤 거기서 한다. 주 체크아웃의 main을 옮기지 않는다.
- 워크트리면 `git status --porcelain`이 비었을 때만 한다. 비지 않았으면 멈추고 바뀐 파일을 사람에게 알린다. 지금 브랜치 이름(`git branch --show-current`)을 `<작업 폴더>/return-branch.txt`에 적고 `git fetch origin` 뒤 `git switch --no-overwrite-ignore --detach origin/main`. 이미 분리 HEAD이고 그 파일이 있으면(같은 올리기를 압축이나 멈춤 뒤에 1부터 다시 한다) 덮어쓰지 않는다. 분리 HEAD의 브랜치 이름은 비어, 덮어쓰면 돌아갈 브랜치를 잃는다.

**돌아가기.** 올리기가 어디서 끝나든 다른 일을 하기 전에 이 자리로 돌아간다. 워크트리면 `return-branch.txt`의 브랜치로 `git switch`하고, 새로 든 워크트리면 `ExitWorktree`(`action: "keep"`)로 나온다. 2의 결정이 "먼저 들인다"·`wait`·`stop`으로 나갈 때, 4의 짓기가 실패할 때, 5에서 보낼 것이 없을 때, 6이 거부로 멈출 때, 다 보낸 뒤가 모두 그렇다. 5에서 보낼 것이 없을 때와 다 보낸 뒤에는 6의 6의 "목록 갱신과 돌아가기"가 돌아가기 전에 할 일을 정한다. 분리 HEAD에 남은 채 "먼저 들인다"의 지시문을 내거나 화면 작업을 이으면, [SKILL.md](SKILL.md)의 "먼저 들인다"가 바꾸지 않는다고 한 브랜치를 잃는다.

## 2. 확인과 결정

확인(`--caller upload`)을 하고, 이 보고를 `first-check.json`으로 남긴다. 결정의 `act`가 계획에 줄 인자를 정한다.

| `act` | `record plan`에 더하는 인자 |
|---|---|
| `upload` | `--check <확인 보고>` |
| `overwrite` | `--check <확인 보고> --overwrite` |
| `uploadClaimMerged` | `--check <확인 보고> --claim-merged` |
| `overwriteClaimMerged` | `--check <확인 보고> --claim-merged --overwrite` |
| `rewriteRecord` | 없음. 계획은 `--artifact-sha256`로 맞댄다(아래 5) |
| `handToUpload` | 들이기가 넘긴 것이다. 확인을 `--caller upload`로 다시 하고 그 결정을 따른다 |

`--claim-merged`가 든 갈래는 보내기 전에 PR 상태 파일(`pr.json`)의 병합 커밋이 지금 HEAD의 조상인지 `git merge-base --is-ancestor <병합 커밋> HEAD`로 본다. 아니면 보내지 않고 `git fetch origin` 뒤 `origin/main`을 다시 체크아웃해 1부터 한다. 병합 전의 HEAD로 보내면 `claim`이 든 파일을 옛 값으로 보내고 `claim`까지 비운다.

## 3. 커밋 맞대기

- **기준 커밋.** 받은 기록의 `commit`이다. 기록이 없거나 `commit`이 null이면(첫 올리기, 첫 올리기가 첫 호출 뒤에 멈춘 때, 편집이 꺼진 동안 기록을 잃은 때) 받은 색인 `lastChange`의 `via`가 든 커밋이다. `via`는 `agent-os main@<짧은 SHA>`이고, 옛 올리기가 남긴 부분 올리기의 꼴 `agent-os 부분 main@<짧은 SHA>`도 그 커밋으로 읽는다. 올리기는 늘 산출 전체를 지어, 부분 올리기가 빠뜨린 파일도 이번 계획이 맞춘다. `via`에 커밋이 없으면 멈추고 사람에게 묻는다.
- **조상.** `git merge-base --is-ancestor <기준 커밋> HEAD`가 실패하면 아티팩트가 지금 HEAD보다 새 코드를 든다. `git fetch origin` 뒤 다시 체크아웃해 1부터 하고, 그래도 실패하면 보내지 않고 멈춘다. 옛 코드로 되돌리지 않는다.

## 4. 산출

산출 폴더 `<작업 폴더>/out/`은 아티팩트의 `project/` 아래에 놓일 내용 전부다. 앞 시도의 `out/`과 `<작업 폴더>/output-paths.json`을 지운 뒤 `assemble --out <작업 폴더>/out --paths <작업 폴더>/output-paths.json`을 친다. 명령은 비지 않은 산출 폴더를 거부하고 스스로 지우지 않는다. `--paths`가 쓴 목록은 이번 산출의 경로 전부이고, 다 보낸 뒤 지난 산출 목록이 된다(6의 6).

보고가 `"ok": false`면 짓기가 실패한 것이다. 보내지 않고 그 `error`를 사람에게 보인 뒤, 1의 "돌아가기"대로 돌아가 멈춘다.

## 5. 계획

`record plan --local <작업 폴더>/out (--record check-<n>/web/project/sync-record.json | --artifact-sha256 <작업 폴더>/sha256.json) [위 표의 인자] --previous-output web/tools/sync-design-system/previous-output.json > <작업 폴더>/plan.json`.

- **`--artifact-sha256`.** 받은 폴더에 기록이 없거나 결정이 `rewriteRecord`면 기록 대신 쓴다. 파일 목록(`list`의 `scope: "files"`)으로 경로를 받고, 산출에 있는 경로를 `read`의 `paths`로 받아 결과가 내는 파일마다의 sha256을 `{"project/<경로>": "<sha256>"}`로 적는다. 목록은 경로·종류·바이트만 내고 sha256은 읽기가 낸다(ADR 0025의 2026-10-21 이력).
- **`--previous-output`.** 늘 저장소의 지난 산출 목록 `web/tools/sync-design-system/previous-output.json`을 준다. 계획은 그 목록에 있고 이번 산출에 없는 경로를 지울 경로로 낸다. 그 목록의 뜻과, 목록에 없어 계획이 지우지 않는 파일은 `upload.ts`의 머리 독스트링이 원천이다.
- **첫 정식 올리기.** 보고의 `firstCanonical`이 true면 받은 기록(기록이 없으면 받은 sha256 목록)에 정식 자리의 카드(`project/components/<이름>/preview.html`)가 없는 첫 정식 올리기다. 계획이 `tokens.json`을 지문과 상관없이 보낼 파일에 넣는다. 옛 별칭(`components/<무리>/<이름>/…`, `_preview/`, `_vendor/`, `_ds_sync.json`)은 지난 산출 목록에 있고 이번 산출에 없어 지울 경로로 나온다. 6의 3이 색인에 `upgraded`를 더하고, 6의 6이 옛 별칭이 남았는지 본다.
- **README의 옮기기 절.** `send`에 `project/README.md`가 들면, 그 README를 `read`로 받아 "## Migrated from the standalone version" 절이 있는지 본다. 그 절은 단독 앱에서 옮길 때 아티팩트 README 끝에 붙은 것이고(옮긴 날짜, 지도와 보고서의 자리, 캔버스·슬라이드의 복사 목록), README 원본에는 없어 보내면 지워진다. 절이 있으면 계획을 지은 뒤 6의 1 전에 그 절을 둘지 AskUserQuestion으로 묻고, 답을 받기 전에는 보내지 않는다. 결정표가 내는 선택지가 아니라 아래 두 길을 이 줄대로 짓는다.
  - 두는 길은 산출의 README를 받은 바이트로 바꿔 계획을 다시 짓는 것이고, 지우는 길은 그대로 보내는 것이다.
  - 물음의 설명에 셋을 적는다. 그 절이 드는 옛 카드 경로와 `_vendor/`·`_preview/`는 첫 정식 올리기가 지우는 파일이다(첫 정식 올리기 뒤면 이미 지워졌다). 캔버스가 목업에 복사할 파일 목록은 새 README 본문이 든다. 두는 길은 받은 옛 README를 그대로 두어 새 본문을 버리므로, README가 지운 `.prompt.md`를 계속 가리키고 다음 올리기마다 같은 물음이 나온다.
  - 그 절 앞까지가 산출 README에 빈 줄 하나를 더한 것과 같으면 두는 길을 추천으로 앞에 두고, 첫 올리기(티켓 08)에서 사람이 그 길을 골랐다고 적는다. 그 앞까지도 다르면 README 본문이 바뀐 것이라 추천을 두지 않는다.
  - 2026-10-27 첫 올리기는 그 절 앞까지가 그때 산출의 README에 빈 줄 하나를 더한 것과 같았고, 사람이 고른 대로 산출의 README를 아티팩트의 바이트로 바꿔 보내지 않았다. 기록은 그 바이트를 든다. 그 절을 페이지의 설정 마치기가 쓰는지는 재지 않았다.
- **덮어쓰기와 색인.** `act`가 덮어쓰기(`overwrite`, `overwriteClaimMerged`)이고 확인 보고의 `index`(또는 `further.index`)가 비지 않았거나, `act`가 `uploadClaimMerged`이고 받은 `claim`의 `index`가 받은 기록의 `index`와 다르면, 보낼 색인의 그 목록(`assetGroups`, `blobs`, `docs`, `sections`)을 받은 기록의 `index`의 것으로 되돌린다. 병합된 `claim`이 든 색인 편집은 들이기에서 사람이 "버린다"를 고른 것도 이 올리기가 되돌린다(명세 "찾았을 때"의 "덮어쓴다" 항목). 계획은 색인 목록을 다루지 않는다. 그렇게 색인에서 빠진 항목이 `project/` 아래 경로를 들면 그 경로를 지울 경로에 더하고, 경로를 가를 수 없으면 지우지 않고 그 항목을 사람에게 보인다.
- 보고의 `send`가 보낼 파일, `delete`가 지울 경로, `calls`가 그 둘을 호출마다 나눈 몫이다(6의 4). `ignored`(산출에 든 기록, 색인, 페이지가 다시 짓는 파일)는 보내지 않는다. 기록과 색인은 6에서 따로 짓는다.
- **보낼 것이 없을 때.** 받은 기록이 있고, 결정이 `rewriteRecord`가 아니며, `send`와 `delete`가 비고, `clearClaim`이 false이고, 받은 기록에 `pending`이 없고, "덮어쓰기와 색인"이 되돌린 목록도 없으면 6의 1~5를 하지 않는다. 6의 6의 "목록 갱신과 돌아가기"대로 돌아가 "맞출 것이 없다"고 알리고 끝낸다. 앞 올리기가 다 보낸 뒤 목록을 커밋하기 전에 끊겼으면 아티팩트는 이미 이번 산출과 같은데 목록만 옛것이라, 여기서 갱신하지 않으면 그 뒤 더해진 경로를 코드가 빼도 지우지 못한다. 목록이 달라 갱신하면 그 앞에 6의 6의 "카드"와 "옛 별칭"을 그 조건과 상관없이 한다. 앞 올리기가 마지막 호출 뒤 이 확인 전에 끊겼을 수 있고, 첫 정식 올리기였어도 이번 계획의 `firstCanonical`은 기록이 이미 정식 배치라 false다. 끊긴 올리기와 같은 HEAD에서 다시 들어도 늘 짓고 계획하므로 이 갱신에 닿는다. 그때 계획은 옛 목록에만 있고 받은 기록에 없는 경로(끊긴 올리기가 이미 지운 것)를 지울 경로로 내지 않는다. 기록이 없거나 `rewriteRecord`면 보낼 파일이 없어도 6에서 기록을 새로 쓴다. 쓰지 않으면 다음 확인이 또 판단할 수 없음을 낸다. 화면 작업이 그리기 전마다 올리기를 부르므로, 이때 기록과 색인만 다시 보내면 바뀐 것 없는 `lastChange`가 쌓인다.

## 6. 보내기

1. **보내기 직전 확인.** 확인을 새로 한 번 더 한다. 보고가 `first-check.json`과 다르면(`cmp`가 다르다고 하면 두 보고를 열어 찾은 것이 달라졌는지 본다) 보내지 않고 [SKILL.md](SKILL.md)의 "찾았을 때"로 돌아가 2부터 한다. 사람이 고르기를 기다리는 사이에 웹 저장이 낄 수 있다.
2. **파일 목록.** `list`의 `scope: "files"`를 받는다. Artifact 도구는 이 세션이 읽었거나 목록에서 본 경로만 바꾸게 한다.
3. **색인.** 이번 확인이 받은 `project/design-system.json`에서 다른 값은 그대로 두고 `lastChange`의 넷을 새로 적는다. `by`는 이번 올리기를 한 쪽(앞 값의 꼴을 따른다), `at`은 지금, `via`는 `agent-os main@<짧은 SHA>`, `note`는 바뀐 것의 요약이다. 5의 "덮어쓰기와 색인"도 여기서 적는다. 그 색인을 `<작업 폴더>/index.json`에 두고 `record index --local <작업 폴더>/out --plan <작업 폴더>/plan.json --index <작업 폴더>/index.json --at <시각> --out <작업 폴더>/send-index.json`으로 보낼 색인을 짓는다. 명령이 `libraries`(산출에 컴포넌트 묶음이 있을 때)와 `upgraded`(첫 정식 올리기일 때)를 적는다. 화면의 "Finish the migration" 정리는 하지 않는다.
4. **나누기.** 호출은 계획 보고의 `calls`의 몫마다 하나이고, 몫의 차례대로 보낸다. 몫의 한도(255개와 16 MiB 가운데 작은 쪽, 기록과 색인과 지울 경로도 센다)는 `upload.ts`의 `splitCalls`가 원천이다. 5의 "덮어쓰기와 색인"이 더한 지울 경로는 몫에 없으니 마지막 몫에 더하고, 더해서 255개를 넘으면 보내지 않고 사람에게 알린다. 호출마다 새 `send-<n>/project/`에 그 몫의 `send` 파일을 산출에서 모으고, 그 몫의 `delete`를 지울 경로로 주어 [SKILL.md](SKILL.md)의 "보내기"로 보낸다. 기록은 `record write --local <작업 폴더>/out --plan <작업 폴더>/plan.json --index <작업 폴더>/send-index.json --out send-<n>/project/sync-record.json [--record check-<n>/web/project/sync-record.json] [--artifact <받은 폴더>] (--first-call | --commit <git rev-parse HEAD> --at <시각>)`로 짓는다.
   - 몫이 하나면 그 호출이 `--commit`과 `--at`으로 지은 기록과, `send-index.json`을 `send-<n>/project/design-system.json`으로 둔 색인을 함께 싣는다.
   - 몫이 여럿이면 첫 호출은 `--first-call`로 지은 `pending`이 든 기록을, 가운데 호출은 몫만, 마지막 호출은 `--commit`과 `--at`으로 지은 `pending` 없는 기록과 색인을 함께 싣는다.
   - `--artifact`는 첫 올리기만 준다. 아티팩트의 파일 목록 가운데 산출에 없고 기록이 빼는 것도 아닌 파일을 읽어 받은 폴더에 둔 것이다.
5. **거부.** 어느 호출이든 거부되면 남은 호출을 보내지 않고 멈추고 확인부터 다시 한다. 앞 호출이 보낸 기록의 `pending`이 확인과 계획에 멈춘 자리를 알린다.
6. **보낸 뒤.** 확인을 한 번 더 해 결과가 `clean`인지 본다. 계획의 `clearClaim`이 true였으면 `claim`도 비었다.
   - **카드.** `clean`이고 보낸 파일에 `project/components/` 아래 경로나 `project/_ds_bundle.*`가 들었으면, 앱 안 브라우저로 아티팩트의 Components 절을 한 번 열어 카드가 모두 그려지고 칸 아래가 잘리지 않았는지 본다. 페이지는 React 18.3.1을 싣고 패키지는 React 19로 짓고 시험하므로, React 19에만 있는 API를 쓴 컴포넌트도 여기서 깨진 카드로 드러난다. 카드 칸의 높이는 그려진 장면을 따르는데, 늦게 자라는 내용은 칸 아래가 잘릴 수 있다.
   - **옛 별칭.** 계획의 `firstCanonical`이 true였으면 파일 목록(`list`의 `scope: "files"`)을 다시 받아 옛 별칭이 남지 않았는지 본다.
   - 깨진 카드나 남은 옛 별칭을 보면 되돌리지 않고 사람에게 알리며, 고칠 일을 `docs/agents/issue-tracker.md`의 규약대로 티켓으로 써서 아래 "목록 갱신과 돌아가기"가 고르는 브랜치에 싣는다.
   - **목록 갱신과 돌아가기.** `<작업 폴더>/output-paths.json`(4의 `--paths`가 쓴 목록)이 `web/tools/sync-design-system/previous-output.json`과 다르면 그 파일로 바꿔 커밋한다. 그 파일은 커밋 검사의 면제 모양이 아니라서(`tools/check_ticket.py`) 티켓을 가리키는 브랜치에만 실린다. 싣는 브랜치와 차례는 1의 자리로 가른다. 주 체크아웃의 main은 옮기지 않는다(1).
     - 돌아갈 브랜치(`return-branch.txt`)가 티켓 모양(`feature/<NN>-<slug>`, `chore/<NNN>-<slug>`)이면 1의 "돌아가기"대로 그 브랜치로 돌아간 뒤, 거기서 목록과 위 티켓을 그 브랜치의 일과 함께 커밋한다.
     - 돌아갈 브랜치가 명세 브랜치(`docs/<slug>`)이거나 1에서 새로 든 워크트리였으면, 돌아가기 전에 지금 자리에서 `docs/agents/issue-tracker.md`의 규약대로 harness 티켓을 쓰고 그 stem으로 `git switch -c chore/<NNN>-<slug>`를 친 뒤 목록과 위 티켓을 커밋한다. 그 브랜치는 따로 PR로 병합한다. 그 뒤 1의 "돌아가기"대로 돌아간다.
     - 목록이 같으면 1의 "돌아가기"대로 돌아가고 위 티켓은 돌아간 브랜치에 싣는다. 새로 든 워크트리였으면 `ExitWorktree` 전에 그 티켓만 싣는 `docs/<slug>` 브랜치를 딴다(티켓만 쓰는 PR은 면제다).

끝: 마지막 호출이 받아들여졌고, 보낸 뒤 확인이 `clean`이며, 카드와 옛 별칭을 볼 올리기였으면 그 결과를 알렸다. 5에서 보낼 것이 없어 끝냈으면 그 알림이 끝이고, 목록이 달라 갱신했으면 카드와 옛 별칭의 결과도 알렸다.

## 못 보는 것

확인이 받는 것은 처음 받는 셋(색인, 기록, `tokens.json`)과, 그 뒤 기록의 `pending`·`claim`과 색인 `docs`에 든 경로, 기록에 든 마크다운(`api/` 아래는 뺀다), 기록의 컴포넌트 폴더 README다(`check.ts`의 `fetchList`와 머리 주석의 못 보는 것). 그래서 누가 Claude Code에 든 옛 디자인 시스템 업로드 스킬(번들 스킬)로 옛 파일을 다시 올리면, 확인이 웹 편집으로 찾는 것은 기록에 든 마크다운(README와 `guidelines/`의 둘)뿐이다. 옛 카드 파일 가운데 `.html`, `_preview/`, `_vendor/`, `_ds_sync.json`과 덮어쓴 `_ds_bundle.*`는 마크다운이 아니라서, `.prompt.md`는 첫 정식 올리기 뒤 기록에 없고 README도 아니라서 받지 않아, 찾지 못한 채 아티팩트에 남는다.
