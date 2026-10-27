# 올리기

`/sync-design-system`의 올리기다. 코드(`web/packages/ui`, 빌린 빌드의 설정, `.claude/rules/web-design.md`)의 판을 아티팩트에 보내고 기록을 새로 쓴다. 바뀐 파일만 보낸다. 명령, 작업 폴더, "확인", "찾았을 때", "보내기"는 [SKILL.md](SKILL.md)의 그 절이다. 화면 작업에서 "계속한다"를 골랐어도 올리기의 확인은 돈다.

## 1. 자리

올리기는 그 입력을 바꾼 PR이 main에 병합된 뒤, `origin/main`을 분리 HEAD로 체크아웃한 깨끗한 작업 트리에서 한다. 병합 전에 올리면 squash로 사라질 브랜치 커밋이 남고, 옛 HEAD로 올리면 그사이 병합된 변경이 빠진다.

- 주 체크아웃이면 `EnterWorktree`로 새 워크트리에 들어가 [SKILL.md](SKILL.md) "명령과 작업 폴더"의 설치를 친 뒤 거기서 한다. 주 체크아웃의 main을 옮기지 않는다.
- 워크트리면 `git status --porcelain`이 비었을 때만 한다. 비지 않았으면 멈추고 바뀐 파일을 사람에게 알린다. 지금 브랜치 이름(`git branch --show-current`)을 `<작업 폴더>/return-branch.txt`에 적고 `git fetch origin` 뒤 `git switch --no-overwrite-ignore --detach origin/main`. 이미 분리 HEAD이고 그 파일이 있으면(같은 올리기를 압축이나 멈춤 뒤에 1부터 다시 한다) 덮어쓰지 않는다. 분리 HEAD의 브랜치 이름은 비어, 덮어쓰면 돌아갈 브랜치를 잃는다.

**돌아가기.** 올리기가 어디서 끝나든 다른 일을 하기 전에 이 자리로 돌아간다. 워크트리면 `return-branch.txt`의 브랜치로 `git switch`하고, 새로 든 워크트리면 `ExitWorktree`(`action: "keep"`)로 나온다. 2의 결정이 "먼저 들인다"·`wait`·`stop`으로 나갈 때, 4의 산출 스크립트로 멈출 때, 5에서 보낼 것이 없을 때, 6이 거부로 멈출 때, 다 보낸 뒤가 모두 그렇다. 분리 HEAD에 남은 채 "먼저 들인다"의 지시문을 내거나 화면 작업을 이으면, [SKILL.md](SKILL.md)의 "먼저 들인다"가 바꾸지 않는다고 한 브랜치를 잃는다.

## 2. 확인과 결정

확인(`--caller upload`)을 하고, 이 보고를 `first-check.json`으로 남긴다. 결정의 `act`가 계획과 빌드 판정에 줄 인자를 정한다.

| `act` | `record plan`·`record needs-build`에 더하는 인자 |
|---|---|
| `upload` | `--check <확인 보고>` |
| `overwrite` | `--check <확인 보고> --overwrite` |
| `uploadClaimMerged` | `--check <확인 보고> --claim-merged` |
| `overwriteClaimMerged` | `--check <확인 보고> --claim-merged --overwrite` |
| `rewriteRecord` | 없음. 계획은 `--artifact-sha256`로 맞댄다(아래 5) |
| `handToUpload` | 들이기가 넘긴 것이다. 확인을 `--caller upload`로 다시 하고 그 결정을 따른다 |

`--claim-merged`가 든 갈래는 보내기 전에 PR 상태 파일(`pr.json`)의 병합 커밋이 지금 HEAD의 조상인지 `git merge-base --is-ancestor <병합 커밋> HEAD`로 본다. 아니면 보내지 않고 `git fetch origin` 뒤 `origin/main`을 다시 체크아웃해 1부터 한다. 병합 전의 HEAD로 보내면 `claim`이 든 파일을 옛 값으로 보내고 `claim`까지 비운다.

## 3. 커밋 맞대기

- **기준 커밋.** 받은 기록의 `commit`이다. 기록이 없거나 `commit`이 null이면(첫 올리기, 첫 올리기가 첫 호출 뒤에 멈춘 때, 편집이 꺼진 동안 기록을 잃은 때) 받은 색인 `lastChange`의 `via`가 든 커밋이다. `via`가 `agent-os main@<짧은 SHA>`면 그 커밋, `agent-os 부분 main@<짧은 SHA>`(부분 올리기)면 그 커밋 뒤로 바뀐 것으로 보아 빌드가 필요하다. `via`에 커밋이 없으면 멈추고 사람에게 묻는다.
- **조상.** `git merge-base --is-ancestor <기준 커밋> HEAD`가 실패하면 아티팩트가 지금 HEAD보다 새 코드를 든다. `git fetch origin` 뒤 다시 체크아웃해 1부터 하고, 그래도 실패하면 보내지 않고 멈춘다. 옛 코드로 되돌리지 않는다.
- **빌드가 필요한지.** `git -c core.quotePath=false diff --name-only <기준 커밋> HEAD > <작업 폴더>/changed.txt` 뒤 `record needs-build --changed <작업 폴더>/changed.txt [위 표의 인자]`. 보고의 `needed`와 `because`가 답이다. 부분 올리기 `via`면 `needed`가 false여도 빌드한다.

## 4. 산출

산출 폴더는 아티팩트의 `project/` 아래에 놓일 내용이다.

- **빌드가 필요 없다.** `<작업 폴더>/out/`에 `build --out <작업 폴더>/out/tokens.json`, `.design-sync/foundations/`를 통째로 `out/foundations/`에, `.claude/rules/web-design.md`를 `out/guidelines/web-design.md`에 둔다. 빌드가 저장소 원본을 그대로 옮기는 파일이다.
- **빌드가 필요하다.** 빌드 산출은 저장소 뿌리의 `ds-bundle/`이다. 빌드한 커밋은 `.ds-sync/ds-bundle-commit`에 있다. 그 값이 `git rev-parse HEAD`와 같고 `ds-bundle/`이 있으면 저장소 뿌리에서 `node .design-sync/upload-output.mjs <작업 폴더>/out <작업 폴더>/output-paths.json`으로 올릴 것만 산출 폴더에 옮겨 5에 간다. `ds-bundle/`에는 채점 사진과 판정 파일 같은 부산물이 섞여 있어, 그대로 주면 계획이 그것까지 보낸다. 스크립트는 산출 폴더가 비지 않았으면 종료 2로 멈추니 앞 시도의 `out/`은 지우고 친다. 종료 2의 나머지(인자, 저장소 뿌리가 아닌 자리, 목록을 쓸 폴더가 없다)는 출력대로 고쳐 다시 친다. 종료 3(그 밖의 오류로 읽기·복사·쓰기가 멈췄다)이면 `out/`을 지우고 한 번 다시 치고, 또 3이면 보내지 않고 그 출력을 사람에게 보이고 멈춘다. 종료 1(`ds-bundle/`에 모르는 맨 위 항목이 있거나 꼭 있어야 할 항목이 없다)이면 보내지 않고 그 출력을 사람에게 보이고 멈춘다. 모르는 항목은 번들 스킬의 판이 바뀌며 생긴 것이라, 올릴지 사람과 정해 스크립트의 목록과 `.design-sync/NOTES.md`에 적는 일이다. 그 고침은 1의 "돌아가기"대로 돌아간 브랜치에서 PR로 하고, 병합된 뒤 1부터 다시 한다. 스크립트가 `.design-sync/` 아래라 그때 3의 "빌드가 필요한지"가 필요하다고 내어 `/design-sync`를 다시 부탁한다. 그 값이 HEAD와 다르거나 `.ds-sync/ds-bundle-commit`이나 `ds-bundle/`이 없으면 낡은 산출을 쓰지 않고, 사람에게 아래 문구로 부탁한 뒤 턴을 끝낸다(기다리는 동안은 [SKILL.md](SKILL.md)의 "멈춘 상태").

  > 빌드가 필요한 올리기입니다(<`because` 요약>). 여기서 `/design-sync`를 한 번 쳐 주세요. 치면 업로드는 하지 않고 빌드 스크립트만 써서 `/sync-design-system`의 올리기를 잇습니다.

### 사람이 친 턴

사람이 `/design-sync`를 치면 그 턴은 번들 스킬 본문(단독 Claude Design이 닫힌다는 알림과 업로드 지시)으로 시작한다. 그 턴은 이 절을 따른다. 번들 스킬 본문의 업로드(`DesignSync`)는 하지 않고 빌드 스크립트만 쓴다.

1. **풀린 폴더.** 스킬 본문 앞에 실린 "Base directory" 줄의 폴더다. 없으면 `claude --version`의 판으로 임시 폴더의 `claude/bundled-skills/<판>/` 아래 `design-sync` 폴더를 찾는다. 그 판의 폴더가 없으면 멈추고 묻는다.
2. **빌린 빌드.** `.ds-sync/ds-bundle-commit`을 지우고, `.design-sync/NOTES.md`의 "돌리는 법"(설치, 패키지 빌드, 참조 Storybook, 변환기 인자, "아티팩트에 올리기"의 driver, 목록 타일과 기초 카드의 복사, 사용 규약 검사)대로 `ds-bundle/`을 짓는다. 검사가 지나면 `build --out ds-bundle/tokens.json`을 치고 `git rev-parse HEAD`를 `.ds-sync/ds-bundle-commit`에 쓴다.
3. 이 문서 2의 확인부터 다시 한다. 4는 방금 지은 산출의 커밋이 HEAD와 같아 다시 부탁하지 않고 `upload-output.mjs`로 `<작업 폴더>/out`을 지으며, 5가 그 `out/`으로 계획을 짓는다. `ds-bundle/`을 산출 폴더로 바로 주지 않는다. 기다리는 사이의 웹 저장은 그 확인과 6의 보내기 직전 확인이 거른다. 이 턴이 인계받은 세션이라 1의 자리가 아니면 1부터 한다.

## 5. 계획

`record plan --local <산출 폴더> (--record check-<n>/web/project/sync-record.json | --artifact-sha256 <작업 폴더>/sha256.json) [위 표의 인자] [--previous-output <지난 산출 목록>] > <작업 폴더>/plan.json`.

- **`--artifact-sha256`.** 받은 폴더에 기록이 없거나 결정이 `rewriteRecord`면 기록 대신 쓴다. 파일 목록(`list`의 `scope: "files"`)으로 경로를 받고, 산출에 있는 경로를 `read`의 `paths`로 받아 결과가 내는 파일마다의 sha256을 `{"project/<경로>": "<sha256>"}`로 적는다. 목록은 경로·종류·바이트만 내고 sha256은 읽기가 낸다(ADR 0025의 2026-10-21 이력).
- **`--previous-output`.** 빌드 산출 전체를 맞춘 올리기만 `.design-sync/upload-output.json`을 준다. 빌드가 필요 없는 올리기의 산출 폴더에는 원본을 옮기는 파일만 있어, 주면 나머지 빌드 산출을 모두 지울 경로로 낸다. 주지 않으면 지난 빌드에만 있던 경로를 지우지 못하고, 코드가 뺀 파일을 되돌리는 덮어쓰기는 계획이 `input` 오류로 멈춘다. 그 목록의 뜻과 다 보낸 뒤 새로 적어 싣는 까닭은 `.design-sync/NOTES.md`의 "아티팩트에 올리기"다.
- **README의 옮기기 절.** 빌드 산출 전체를 맞춘 올리기의 `send`에 `project/README.md`가 들면, 그 README를 `read`로 받아 "## Migrated from the standalone version" 절이 있는지 본다. 있으면 보내면 그 절이 지워지므로, 계획을 지은 뒤 6의 1 전에 그 절을 둘지 AskUserQuestion으로 묻고 답을 받기 전에는 보내지 않는다. 결정표가 내는 선택지가 아니라 아래 두 길을 이 줄대로 짓는다. 그 절 앞까지가 산출 README에 빈 줄 하나를 더한 것과 같으면 두는 길(산출의 README를 받은 바이트로 바꿔 계획을 다시 짓는다)을 추천으로 앞에 두고, 첫 올리기(티켓 08)에서 사람이 그 길을 골랐다고 적는다. 그 앞까지도 다르면 README 본문이 바뀐 것이라 두는 길은 새 본문을 버리니, 보내면 그 절이 지워진다고 알리고 묻는다. 절의 내용과 까닭은 `.design-sync/NOTES.md`의 Re-sync risks다.
- **덮어쓰기와 색인.** `act`가 덮어쓰기(`overwrite`, `overwriteClaimMerged`)이고 확인 보고의 `index`(또는 `further.index`)가 비지 않았거나, `act`가 `uploadClaimMerged`이고 받은 `claim`의 `index`가 받은 기록의 `index`와 다르면, 보낼 색인의 그 목록(`assetGroups`, `blobs`, `docs`, `sections`)을 받은 기록의 `index`의 것으로 되돌린다. 병합된 `claim`이 든 색인 편집은 들이기에서 사람이 "버린다"를 고른 것도 이 올리기가 되돌린다(명세 "찾았을 때"의 "덮어쓴다" 항목). 계획은 색인 목록을 다루지 않는다. 그렇게 색인에서 빠진 항목이 `project/` 아래 경로를 들면 그 경로를 지울 경로에 더하고, 경로를 가를 수 없으면 지우지 않고 그 항목을 사람에게 보인다.
- 보고의 `send`가 보낼 파일, `delete`가 지울 경로다. `ignored`(산출에 든 기록, 색인, 페이지가 다시 짓는 파일)는 보내지 않는다. 기록과 색인은 6에서 따로 짓는다.
- **보낼 것이 없을 때.** 받은 기록이 있고, 결정이 `rewriteRecord`가 아니며, `send`와 `delete`가 비고, `clearClaim`이 false이고, 받은 기록에 `pending`이 없고, "덮어쓰기와 색인"이 되돌린 목록도 없으면 6을 하지 않는다. 1의 "돌아가기"대로 돌아가 "맞출 것이 없다"고 알리고 끝낸다. 끝내기 전에, 빌드 산출 전체를 맞춘 올리기였으면 6.6의 목록 갱신만 한다. 앞 올리기가 보낸 뒤 목록을 커밋하기 전에 끊겼으면 아티팩트는 이미 이번 산출과 같은데 목록만 옛것이라, 여기서 갱신하지 않으면 그 뒤 더해진 경로를 코드가 빼도 지우지 못한다. 끊긴 올리기와 같은 HEAD에서 다시 들면 기록의 커밋이 HEAD라 3의 "빌드가 필요한지"가 필요 없다고 내어 이 갱신에 닿지 않는다. 그때는 끊긴 올리기가 새로 더한 경로가 지난 목록에 들지 않고, 코드가 뒤에 그 파일을 빼도 아티팩트에 남을 뿐이다. 기록이 없거나 `rewriteRecord`면 보낼 파일이 없어도 6에서 기록을 새로 쓴다. 쓰지 않으면 다음 확인이 또 판단할 수 없음을 낸다. 화면 작업이 그리기 전마다 올리기를 부르므로, 이때 기록과 색인만 다시 보내면 바뀐 것 없는 `lastChange`가 쌓인다.

## 6. 보내기

1. **보내기 직전 확인.** 확인을 새로 한 번 더 한다. 보고가 `first-check.json`과 다르면(`cmp`가 다르다고 하면 두 보고를 열어 찾은 것이 달라졌는지 본다) 보내지 않고 [SKILL.md](SKILL.md)의 "찾았을 때"로 돌아가 2부터 한다. 사람이 고르거나 `/design-sync`를 쳐 주기를 기다리는 사이에 웹 저장이 낄 수 있다.
2. **파일 목록.** `list`의 `scope: "files"`를 받는다. Artifact 도구는 이 세션이 읽었거나 목록에서 본 경로만 바꾸게 한다.
3. **색인.** 이번 확인이 받은 `project/design-system.json`에서 다른 값은 그대로 두고 `lastChange`의 넷을 새로 적는다. `by`는 이번 올리기를 한 쪽(앞 값의 꼴을 따른다), `at`은 지금, `via`는 빌드 산출 전체를 맞춘 때만 `agent-os main@<짧은 SHA>`이고 파일 몇 개만 보내면 `agent-os 부분 main@<짧은 SHA>`, `note`는 바뀐 것의 요약이다. 5의 "덮어쓰기와 색인"도 여기서 적는다. 화면의 "Finish the migration" 정리는 하지 않는다.
4. **나누기.** 한 호출은 255개와 16 MiB 가운데 작은 쪽까지다(명세 "기록"의 "중간 실패"가 도구 설명과 형식 설명에서 고른 값이다). 기록과 색인도 센다. 지울 경로도 드는지는 재지 못해 드는 쪽으로 센다. 한 호출에 들면 `record write --local <산출 폴더> --plan <작업 폴더>/plan.json --index <보낼 색인> --out send-<n>/project/sync-record.json [--record check-<n>/web/project/sync-record.json] [--artifact <받은 폴더>] --commit <git rev-parse HEAD> --at <시각>`으로 기록을 짓고, `send`의 파일과 기록과 색인을 `send-<n>/project/`에 모아 [SKILL.md](SKILL.md)의 "보내기"로 보낸다. 나누면 첫 호출은 `--first-call`로 지은 `pending`이 든 기록과 첫 몫을, 가운데 호출은 다음 몫을, 마지막 호출은 `--commit`과 `--at`으로 지은 `pending` 없는 기록과 색인과 남은 몫을 보낸다. `send`에 `project/_ds_sync.json`이 들면 마지막 호출에 싣는다. 몫을 나누기 전에 그 파일을 마지막 몫에 먼저 넣고 나머지를 나눠, 마지막 호출도 한도 안에 든다. 다음 빌드의 driver가 `--remote`로 읽는 기준점이라, 앞 호출에 실린 채 뒤 호출이 거부되면 아티팩트에 아직 없는 카드를 다시 채점하지 않고 넘긴다(번들 스킬은 이 파일을 맨 끝에 쓴다). `--artifact`는 첫 올리기만 준다. 아티팩트의 파일 목록 가운데 산출에 없고 기록이 빼는 것도 아닌 파일을 읽어 받은 폴더에 둔 것이다.
5. **거부.** 어느 호출이든 거부되면 남은 호출을 보내지 않고 멈추고 확인부터 다시 한다. 앞 호출이 보낸 기록의 `pending`이 확인과 계획에 멈춘 자리를 알린다.
6. **보낸 뒤.** 확인을 한 번 더 해 결과가 `clean`인지 본다. 계획의 `clearClaim`이 true였으면 `claim`도 비었다. 1의 "돌아가기"대로 돌아간다. 빌드 산출 전체를 맞춘 올리기였고 `<작업 폴더>/output-paths.json`이 `.design-sync/upload-output.json`과 다르면, 돌아간 브랜치에서 그 파일로 바꿔 그 브랜치의 일과 함께 커밋한다. 1에서 새로 든 워크트리였으면 `ExitWorktree` 전에 그 워크트리에서 `git switch -c chore/<이름>`으로 브랜치를 따서 싣는다. 주 체크아웃의 main은 옮기지 않는다(1).

끝: 마지막 호출이 받아들여졌고, 보낸 뒤 확인이 `clean`이다. 5에서 보낼 것이 없어 끝냈으면 그 알림이 끝이다.
