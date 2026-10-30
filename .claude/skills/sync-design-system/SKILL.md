---
name: sync-design-system
description: "Claude 아티팩트의 디자인 시스템과 `web/packages/ui`를 맞춘다. 웹 편집 확인, 들이기·올리기. 사람이 웹에서 디자인 시스템을 고쳤다고 말할 때(인자 없음), 디자인 시스템 아티팩트에 올릴 때(`올리기`), 화면 작업 전과 화면 코드를 처음 고쳤다는 알림을 받았을 때(`확인`) 부른다."
---

<!-- 프로젝트 스킬, model-invoked. 결정은 ADR 0025 이력 2026-10-21 "디자인 시스템 아티팩트의 편집을 tokens.json으로 열고, 사람이 알리거나 화면 작업과 올리기가 찾은 웹 편집을 디자인 토큰 CSS로 들인다"(절차의 자리, 함께 고치는 것)이고, 근거는 `.scratch/design-reverse-sync/spec.md`의 "확인", "찾았을 때", "겹침", "거꾸로 동기화", "올리기", "멈춘 상태의 자리", "스킬"이다. 올리기가 늘 짓기 명령으로 산출 전체를 짓는 것은 ADR 0025 이력 2026-10-28과 `.scratch/design-card-build/spec.md`의 "올리기"다. `/ui-design`이 이름을 들어 부르고, 화면 코드를 처음 고친 세션에는 계기 훅 `tools/hook_web_edit_check.py`가 `확인`으로 부르라고 알린다. -->

# 디자인 시스템 동기화

디자인 시스템의 원천은 코드(`web/packages/ui`)이고, Claude 아티팩트의 디자인 시스템(https://claude.ai/artifact/8ttLDZQqchfD2ao1XG56GH, 아래 "아티팩트")은 그 사본이다. 사람이 아티팩트를 웹에서 고치면 그 웹 편집을 코드에 들이고(들이기), 코드가 바뀌면 아티팩트에 보낸다(올리기). 아티팩트의 `project/sync-record.json`(기록)이 마지막으로 올린 해시와 디자인 토큰 기준본, 들이는 중인 세션의 `claim`을 든다.

판단은 스크립트가 한다. 이 스킬은 Artifact 도구·`gh`·`git`으로 바깥 값을 받아 파일로 넘기고, 스크립트가 낸 선택지를 사람에게 묻고, 고른 대로 보낸다. 받을 경로, 보낼 파일, 선택지를 스킬이 손으로 짓지 않는다. 낱말은 명세 "낱말"대로다. "올리기"는 디자인 시스템 올리기, 올릴 산출 전체를 짓는 일은 "짓기"(짓기 명령 `assemble`)다. 디자인 토큰은 "토큰"으로 줄이지 않는다.

## 인자

| 인자 | 부르는 쪽(`--caller`) | 하는 일 |
|---|---|---|
| `확인` | `screen` | 아래 "확인"만 하고 "찾았을 때"대로 멈추거나 화면 작업으로 돌아간다. `/ui-design`의 그리기 전 단계와, 세션이 `web/packages/ui`나 `web/apps/<앱>` 아래를 처음 고쳤을 때 계기 훅(`tools/hook_web_edit_check.py`)이 알리는 확인이 이것이다. 서브에이전트에는 그 훅이 확인 대신 끝 보고에 적을 문장을 알리고, 그 보고를 받은 부모 세션은 이 세션에서 아직 확인을 하지 않았고 그 훅이 침묵하는 세션(들이기 세션, design-reverse-sync의 구현 티켓 세션)이 아닐 때 이것을 부른다 |
| `올리기` | `upload` | 확인 뒤 보낸다. [upload.md](upload.md) |
| 없음, 또는 사람이 "디자인 시스템을 고쳤다"고 말했다 | `import` | 확인 뒤 찾은 것을 들인다. [import.md](import.md) |

## 명령과 작업 폴더

스크립트는 저장소 뿌리(워크트리면 워크트리 뿌리)에서 `node web/tools/sync-design-system/main.ts <명령> <인자…>`로 부른다. 명령마다의 인자와 보고의 칸은 `web/tools/sync-design-system/`의 그 모듈 독스트링이 원천이다(`check-command.ts`, `decide.ts`, `record.ts`, `import.ts`, `build.ts`, `assemble.ts`). 보고는 표준 출력의 JSON 한 줄이다. 다른 명령의 입력이 되는 보고는 `> <파일>`로 받는다. `"ok": false`면 그 `error`를 사람에게 보이고 멈춘다.

작업 폴더는 세션 스크래치패드 아래 `sync-design-system/`이다. 아래에서 `check-<n>/`, `claim-<n>/`, `send-<n>/`, `<작업 폴더>/`로 시작하는 경로는 모두 이 작업 폴더 아래의 것이고, 스크립트와 `git`에는 절대 경로로 준다. 스크립트를 저장소 뿌리에서 부르므로, 상대 경로로 주면 저장소 안에 풀려 작업 트리를 더럽힌다. 그 밖의 상대 경로(`web/…`)는 저장소 뿌리의 것이다. 확인 한 번마다 새 폴더 `check-<n>/`을 만든다. 받은 폴더(`check-<n>/web/`)에 앞 확인의 파일이 남아 있으면 지금 웹에 없는 파일을 있다고 읽기 때문이다. 시각 인자는 `date -u +%Y-%m-%dT%H:%M:%SZ`의 값이다.

새 워크트리에 들어가면 스크립트를 부르기 전에 `pnpm -C web install --frozen-lockfile`을 친다. `web/node_modules`가 없으면 `main.ts`가 들이는 `import.ts`가 `@agent-os/ui/contrast`를 찾지 못해, 어느 명령이든 JSON 보고 없이 `ERR_MODULE_NOT_FOUND`로 끝난다(셀프 리뷰 서브에이전트가 `node_modules` 없는 사본에서 쳐 봤다). 들이기는 검증 명령도 돌므로 `uv sync`도 친다. 두 명령에 줄 시간 제한은 `implement` 스킬의 첫 문단이다.

## 확인

끝: `check-<n>/check.json`에 `check judge`의 보고가 있고, 결정표의 보고(`decide`)가 나왔다.

1. **받을 경로.** 확인을 시작할 때 빈 받은 폴더 `check-<n>/web/`을 만들고 `check-<n>/reads.json`에 `{"absent": [], "failed": {}}`를 쓴다. 아직 아무것도 받지 않은 첫 `check paths`에도 `--web`이 읽을 폴더가, 다 읽힌 확인에도 3의 `--reads`가 받을 파일이 있어야 한다(없는 폴더나 파일을 주면 `input` 오류로 멈춘다). 그 뒤 `check paths --web check-<n>/web --reads check-<n>/reads.json`. 보고의 `paths`가 비면 3으로 간다.
2. **받기.** Artifact 도구 `read`에 아티팩트 `url`과 그 `paths`를 준다. 결과가 알리는 자리의 파일을 `check-<n>/web/<경로>`(`project/…` 그대로)로 복사한다. 읽지 못한 경로는 `reads.json`(`{"absent": [...], "failed": {경로: 문구}}`)에 더한다. 도구가 그 경로가 없다는 까닭(첫 올리기가 본 문구는 `no file is published at that path in the served version`)을 냈을 때만 `absent`이고, 그 밖과 가를 수 없는 문구는 `failed`에 도구의 문구 그대로 적는다. 잠깐의 도구 오류를 `absent`로 적으면 웹에서 지운 것으로 읽혀, "저장소 파일에 옮긴다"가 저장소 원본을 지우는 PR이 선다. 1로 돌아간다.
3. **판정.** `build --out check-<n>/code-tokens.json`으로 지금 코드의 `tokens.json`을 짓고, `check judge --web check-<n>/web --reads check-<n>/reads.json --branch <지금 브랜치> --code-tokens check-<n>/code-tokens.json --inherit-out check-<n>/inherit.json > check-<n>/check.json`. 지금 브랜치는 `git branch --show-current`이고, 비면(분리 HEAD) `HEAD`를 준다. 보고에 `inherit`이 있을 때만 그 파일을 쓴다. 비었으면 앞 실행의 파일일 수 있다.
4. **결정.** 보고의 `result`가 `importing`이면 `gh pr list --head <claim.branch> --state all --json number,state,url,mergeCommit > check-<n>/pr.json`을 치고 `decide`에 `--pr check-<n>/pr.json`을 준다. `gh`가 실패하면 `--pr-error`에 그 문구를 준다. `decide --caller <위 표> --check check-<n>/check.json [--pr … | --pr-error …]`의 `kind`가 `ask`면 "찾았을 때", `act`면 아래 "할 일"이다.

판단할 수 없음의 까닭이 아티팩트를 읽지 못한 것(`readFailed`, `noIndex`, `indexUnreadable`, `tokensUnreadable`)이면 도구가 낸 문구와 `claude auth status`가 낸 지금 계정을 함께 보인다. 지금 계정이 아티팩트의 주인도 편집자도 아니면 "artifact not found"가 난다(`docs/agents/issue-tracker.md` 화면 디자인 절의 계정 항목). 계정은 저장소 어디에도 적지 않는다.

## 찾았을 때

웹 편집을 찾았거나 판단할 수 없을 때 묻는 자리는 이 절 하나다. 들이기와 올리기도 이 절로 묻는다.

1. 찾은 것을 보인다. `check.json`의 `tokens`(디자인 토큰마다 벌, 전과 후), `files`(고친·더한·지운 파일), `index`(바뀐 색인 목록)를 표로 보이고, 들이는 중이면 `claim`의 브랜치·티켓·시각과 `further`(그 뒤에 더 고친 몫)를 함께 보인다. 결정표의 `notes`를 그대로 덧붙인다.
2. AskUserQuestion 하나로 묻는다. 선택지는 결정표의 `choices`를 그 차례로, 라벨은 `label`, 설명은 `effect` 그대로 쓴다. 선택지를 더하거나 고쳐 쓰지 않는다.
3. 사람이 고른 선택지의 `act`를 아래 "할 일"대로 한다.

## 할 일

| `act` | 할 일 |
|---|---|
| `continue` | 화면 작업으로 돌아간다. `notes`가 병합 커밋을 들면 `git merge-base --is-ancestor <그 커밋> HEAD`를 보고, 품지 않았으면 main을 합친 뒤 잇는다. 사람이 "계속한다"를 골랐으면 아래 "멈춘 상태"대로 적고, 같은 세션의 화면 작업에서는 다시 묻지 않으며 그리기 전의 올리기도 부르지 않는다. 그 올리기는 자기 확인을 다시 돌려, 웹 편집이면 같은 것을 올리기의 선택지("먼저 들인다", "덮어쓴다")로 곧바로 다시 묻고 판단할 수 없음이면 다시 묻거나 멈춘다. "지금 코드 값으로 계속한다"의 설명은 웹 편집을 다음 확인이 다시 찾는다고 말한다 |
| `upload`, `overwrite`, `uploadClaimMerged`, `overwriteClaimMerged`, `rewriteRecord`, `handToUpload` | [upload.md](upload.md)의 올리기를 그 `act`로 잇는다 |
| `import`, `inheritImport` | 부르는 쪽이 `import`면 [import.md](import.md)의 들이기. `screen`이나 `upload`면 아래 "먼저 들인다" |
| `resumeImport` | [import.md](import.md)의 "이어 하기" |
| `clearClaim` | 아래 "claim 지우기" 뒤 확인부터 다시 한다 |
| `wait` | 그 브랜치를 사람에게 알리고 지금 일을 멈춘다. 화면 작업이면 아래 "멈춘 상태"의 병합을 기다림이다 |
| `stop` | `notes`를 보이고 멈춘다 |

**먼저 들인다.** 지금 세션은 브랜치를 바꾸지 않는다. 들이기를 새 세션에 넘긴다. 번호는 `git fetch origin` 뒤 `git ls-tree --name-only origin/main .scratch/design-reverse-sync/issues/`에서 가장 큰 번호의 다음이고, slug는 바뀐 것을 짧게 이른다(`teal-gray-50`). 지시문은 `next-session`의 `directive.md` 형식으로 짓는다. 다음 작업은 `.scratch/design-reverse-sync/issues/<NN>-web-edit-<slug>.md`(받는 세션이 쓴다)와 찾은 것의 한 줄, 다음 단계는 구현, 시작 프롬프트는 `/sync-design-system`, 브랜치는 `feature/<NN>-web-edit-<slug>`, 이번 요청 범위는 PR과 병합, 그 뒤 올리기까지다. 어디서의 워크트리 문장은 `next-session` `directive.md` 5가 정한다. Skill 도구로 `open-session`을 불러 그 세션을 연다. 새 세션은 자기 새 브랜치에서 확인부터 다시 한다. 지금 세션은 그 병합을 기다린다.

**claim 지우기.** 기록을 다시 받아(`read`의 `paths`에 `project/sync-record.json`) `record claim --record <다시 받은 기록> --expect check-<n>/web/project/sync-record.json --out send-<n>/project/sync-record.json --clear`로 지운 기록을 짓고, 아래 "보내기"로 그 파일 하나를 보낸다.

## 보내기

들이기의 `claim`과 올리기가 같이 쓴다.

- 보낼 파일을 `<작업 폴더>/send-<n>/project/<경로>`에 모은다. Artifact 도구 `publish`에 아티팩트 `url`, `root`는 `send-<n>`의 절대 경로, `file_path`는 그 안의 파일 하나의 절대 경로, `files`는 나머지 `{"project/<경로>": "project/<경로>"}`와 지울 경로 `{"project/<경로>": null}`을 준다.
- `force`와 `overwrite_unread`는 주지 않는다. 그 둘이 그사이 사람이 웹에서 저장한 것을 덮는다.
- 거부되면 아무것도 보내지 않은 채 멈추고 확인부터 다시 한다. 도구의 안내(다시 읽고 합쳐 보낸다)를 따르지 않는다. 합치면 그사이의 웹 편집을 덮는다. 티켓 02가 임시 아티팩트에서 본 거부는 사람이 바꾼 파일을 보낸 때였고, 새 경로는 거부되지 않았다(`.scratch/design-reverse-sync/probes/README.md`의 "임시 아티팩트에서 손으로 본 것"). 그래서 들이기는 PR 직전과 병합 직전에 `claim`을 다시 읽는다.

## 멈춘 상태

사람의 답을 기다리는 동안 세션을 넘기면 `next-session`의 "이어받을 상태"에 아래를 적는다.

- **고를 때까지 기다림.** "웹 편집 확인: 고를 때까지 기다림"과 찾은 것의 요약. 이어받은 세션은 확인을 다시 돌려 다시 묻는다.
- **올리기 중.** 올리기가 분리 HEAD에서 도는 동안 넘기면 그 단계와 돌아갈 브랜치([upload.md](upload.md) 1이 `<작업 폴더>/return-branch.txt`에 적은 값)를 적는다. 이어받은 세션은 그 브랜치로 돌아간 뒤 올리기를 1부터 다시 한다.
- **병합을 기다림.** "먼저 들인다"를 고른 화면 세션은 일지와 "이어받을 상태"에 기다리는 들이기의 브랜치를 적고, 그 브랜치가 병합될 때까지 화면 작업을 잇지 않는다. 병합 뒤 main을 합쳐 잇는다.
- **계속한다.** 사람이 "지금 코드 값으로 계속한다"나 "확인 없이 계속한다"를 골랐으면 일지에 `> 사용자:` 인용으로, "이어받을 상태"에 그 선택을 적는다.

`claim`은 아티팩트에 있어 어느 세션에서나 확인이 다시 읽는다. 적은 것을 잃어도 확인이 다시 묻는 것이 값의 전부다.

## 재지 못한 것

처음 돌려 볼 때 다르면 이 절과 그 자리를 고친다. 첫 올리기(티켓 08, 2026-10-27)가 위 "보내기"의 `publish` 모양(새 경로 셋과 바꾼 경로 셋을 한 호출로 보냈다), `read`가 없는 경로에 내는 문구(위 "확인" 2)를 봤다. 남은 것은 아래 넷이다.

- 색인의 그림·글꼴 항목이 파일 경로를 어떻게 드는지([upload.md](upload.md)의 "덮어쓰기와 색인"). 첫 올리기 때 색인의 `assetGroups`의 `files`와 `blobs`가 비어 있어 보지 못했다. 들이기가 "저장소 파일에 옮긴다"를 고른 색인 편집이, 병합 뒤의 올리기가 색인 목록을 기록의 것으로 되돌린 다음에 어떻게 남는지도 그 자리에서 본다.
- 한 호출의 한도(255개)에 지울 경로(`files`의 null)도 드는지. 계획의 몫 나누기(`upload.ts`의 `splitCalls`)는 드는 쪽으로 센다. 첫 올리기는 지울 경로가 없었다.
- 나눠 보낸 호출들이 판 하나로 묶이는지, 호출마다 판이 하나씩 생기는지(명세 "기록"의 "중간 실패"가 어림한 것). 첫 올리기는 한 호출이었다.
- 판 하나에 드는 파일 수의 한도. 도구 설명은 511개, 형식 설명은 1,024개라 적는다. 첫 올리기는 목록 머리가 875개(`project/` 밖 13개 포함)인 판에 새 경로 셋을 더해 받아들여졌으니 511개는 막지 않았다. 보낸 뒤 목록을 다시 받지 않아 판 16의 수는 878개로 어림했고, 1,024개 쪽은 재지 못했다.
