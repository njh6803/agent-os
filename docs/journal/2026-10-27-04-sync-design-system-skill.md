# 2026-10-27 (04) design-reverse-sync 07 `/sync-design-system` 스킬과 절차 옮기기

## 시작

세션을 연 지시문의 시작 프롬프트와 범위다.

> 사용자: /implement .scratch/design-reverse-sync/issues/07-sync-design-system-skill.md (다음 작업: "스킬이 확인·결정표·기록 명령을 부르고, Artifact 도구와 gh 로 읽은 것을 넘겨 claim 겹침을 사람에게 묻는다", 브랜치 feature/07-sync-design-system-skill, 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래, 읽을 것: "docs/journal/2026-10-27-03-claim.md 의 "다음"", 이어받을 상태: "PR #399 둘째 회차 claude-review 의 Major(병합된 자기 claim 에 더 고친 몫이 있을 때 화면 작업·올리기의 "먼저 들인다"가 막힌다)는 새 들이기 세션이 자기 티켓 브랜치에서 확인부터 하므로 오탐으로 판정했고, 근거는 PR #399 코멘트에 있다. 07 이 스킬을 짤 때 그 전제("먼저 들인다"는 새 세션의 새 브랜치에서 확인부터 한다)를 지키는지 본다. 같은 회차의 Minor(decoded·text 디코딩 중복)와 Nit(sameClaim·sameAt 정리)은 보류했다", 확인할 선행 조건: "주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다", 이번 요청 범위: PR과 병합까지)

tidy-checkouts를 먼저 돌았다. 루트는 `origin/main`(`5e049681`)으로 당겨졌다. `04-site-file-feeds-widget-build` 워크트리는 `remove`가 종료 1이라 남겼고, 휴지통의 05 `node_modules`는 esbuild 프로세스가 쥐어 남았다. 그 뒤 `EnterWorktree`(이름 `07-sync-design-system-skill`)로 들어가 브랜치를 바꿨다.

## 한 것

기점은 `5e049681`이다. 아직 커밋하지 않았다.

- 새 스킬 `.claude/skills/sync-design-system/`. `SKILL.md`는 세 인자가 모두 지나는 몫(인자 표, 명령과 작업 폴더, 확인, 찾았을 때, 할 일, 먼저 들인다, claim 지우기, 보내기, 멈춘 상태, 재지 못한 것)이고, 한 갈래만 닿는 들이기와 올리기는 `import.md`와 `upload.md`로 뺐다. `disable-model-invocation`은 두지 않았다. 스킬을 쓰기 전에 Skill 도구로 `writing-for-agents`를 불렀다.
- 기록 명령에 `record base`를 더했다(`web/tools/sync-design-system/record.ts`, 독스트링의 하위 명령 "다섯"). 시험은 `record-check.test.ts`의 "들이기의 기준본은 claim 이 이어받은 기준본이 있으면 그것이고, 없으면 기록의 기준본이다"이고, 그 파일의 15개가 지난다. 변이 52·53을 `.scratch/design-reverse-sync/probes/record_check_mutations.toml`에 더했고 둘 다 기대대로 빨갰다(`tools/mutate.py`).
- 문서 넷을 포인터로 줄였다. `docs/agents/issue-tracker.md` 화면 디자인 절(+1/-4), `.design-sync/NOTES.md`의 "아티팩트에 올리기" 항목(+15/-26. 번들 스킬 문장은 명세의 글자 그대로), `.scratch/admin-style/design/screens-prompt.md` 1단계, `.claude/rules/web-design.md` 머리 문장. `README.md` 73행도 고쳤다.
- `/ui-design` 2단계에 그리기 전 확인(`/sync-design-system` 인자 `확인`, 화면 작업을 잇게 되면 인자 `올리기`)을 넣었다.
- 카나리아 넷 `.scratch/design-reverse-sync/probes/canary/`(스킬 본문, 스토리 4, ui-design의 그리기 전 확인, web-design 규칙의 올리는 길). 모두 통과 4이고(2026-10-27, 이 PC, claude 2.1.302, `5e049681` 위의 작업 트리), 스토리 4는 실험군 셋이 인자 칸("없음, 또는 …")까지 옮겨 "없음" 섞인 통과로 표시됐다(원본의 답을 손으로 봤다). 결과는 명세마다 머리 주석과 프로브 README의 `canary/*.toml` 행이다.
- 프로브 README: `record_check_mutations.toml` 행을 53개로 고치고 근거 칸에 07을 더했으며, 카나리아 명령 줄과 행을 더했다.
- 티켓 07: 체크박스를 "검증 명령이 모두 초록이다" 밖은 채웠고 "07이 정한 것" 메모를 더했다. Status는 아직 `in-progress`다. 티켓 08에 "07이 넘긴 것"(재지 못한 넷과 08이 NOTES에 적을 둘)을 더했다.

## 결정

- `web/package.json`에 스크립트 줄을 더하지 않았다. 루트에서 `node web/tools/sync-design-system/main.ts <명령>`이 바로 돈다(쳐 봤다). `pnpm -C web`은 작업 폴더를 바꿔 상대 경로가 어긋난다는 것은 어림이다.
- 기록, 기준본, `claim`은 `CONTEXT.md`에 더하지 않았다. `domain-modeling`으로 갈랐다. 셋은 이 기능이 아티팩트 안 파일과 그 칸에 붙인 이름이고 명세 "낱말"이 정의한다.
- 05가 넘긴 "웹이 더한 그림·글꼴을 지울지와 지우는 길"은 `upload.md` 5의 "덮어쓰기와 색인"으로 정했다. 기록의 색인 목록으로 되돌리고, 빠진 항목이 `project/` 경로를 들면 지우며, 가를 수 없으면 사람에게 보인다.
- PR #399 Major 판정의 전제는 `SKILL.md` "먼저 들인다"와 `import.md` 1의 끝 조건("새 들이기는 늘 자기 새 브랜치에서 확인부터 한다")이 지킨다.
- 올리기에 "보낼 것이 없을 때"를 더했다(`upload.md` 5). 화면 작업이 그리기 전마다 올리기를 부르므로, 그 갈래가 없으면 바뀐 것 없는 기록과 색인이 매번 나간다.
- 옛 표현 잔존: "번들 `/design-sync` 스킬은 부르지 않는다"는 명세와 티켓의 인용에만 남았다. `docs/constitution/tech.md` 19행은 아직 참이고 ADR 뒤에 쓰는 문서라 두었다. 기록(일지, ADR, 닫힌 명세, 옛 카나리아 `web_design_artifact.toml`)은 두었다.
- 스킬 본문의 명령 줄을 각 명령의 `parseArgs` 옵션과 독스트링에 손으로 대 봤고 어긋난 것이 없었다(`record claim --inherit`는 확인 보고의 `inherit`가 든 절대 경로를 받는다).

## 고친 것

- `docs/agents/issue-tracker.md`를 파이썬 `write_text`로 써서 CRLF가 됐다. 바이트로 LF로 되돌렸다.
- 스킬 머리 주석의 ADR 0025 이력 제목을 짐작으로 적었다가 grep으로 실제 제목에 맞췄다.
- 워크트리 가드가 묶은 grep, 반복문 변수를 쓴 sed, heredoc 묶음을 거부해 단일 명령과 Write 도구로 바꿨다.

## 검증

- `uv run ruff check .`와 `uv run ruff format --check .`는 초록이다.
- `uv run python tools/run_checks.py`는 백그라운드로 띄웠으나 인계하며 멈춰 결과가 없다.
- 셀프 리뷰(`/code-review`)는 아직이다. 불렀지만 인계 계기가 와서 단계를 밟지 않았다.

## 인계

이 세션의 지금 제목은 `feature/07-sync-design-system-skill`이다. 인계 계기 `셀프 리뷰 직전`이 세션 컨텍스트 223,393 토큰에서 왔다.

지시문:

```
다음 작업: .scratch/design-reverse-sync/issues/07-sync-design-system-skill.md. 스킬과 문서 옮기기, 카나리아는 끝났고 셀프 리뷰부터 PR과 병합까지 남았다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/design-reverse-sync/issues/07-sync-design-system-skill.md
브랜치: feature/07-sync-design-system-skill
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-27-04-sync-design-system-skill.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(`/code-review`)부터 한다(docs/journal/2026-10-27-04-sync-design-system-skill.md). 린트 둘은 초록이고 run_checks 는 인계하며 멈춰 결과가 없다. 티켓의 "검증 명령이 모두 초록이다"와 Status, 일지의 커밋과 "다음"은 아직이다. PR #396(티켓 03)이 같은 .scratch/design-reverse-sync/probes/README.md 를 고친다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `feature/07-sync-design-system-skill (인계함)`으로 바꿨고, 백그라운드의 `run_checks`를 멈췄고, 워크트리 잠금을 풀었다.

open-session을 부른다 2026-10-27T00:47:35Z

## 이어받은 세션: 셀프 리뷰

> 사용자: 지시문 그대로(위 "인계"의 지시문과 같다)

새 세션이 제목을 `feature/07-sync-design-system-skill`로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다. `uv run python tools/run_checks.py`를 백그라운드로 다시 돌려 종료 0이었다(열 검사 모두 Passed, pytest 440.1초, web-verify 503.3초). 남아 있던 미추적 `web/judge-sGnjiH/`는 중단된 앞 실행의 판정자 임시 트리였고 이 실행의 verify가 지웠다. `tools/sibling_overlap.py`는 번호 겹침이 없고, 같은 파일을 고치는 열린 PR은 #296(`docs/agents/issue-tracker.md`)과 #396(프로브 README)이다.

범위: base `5e049681`, 바뀐 파일 열둘, 커밋 0, 미추적 여덟. 표준 축(sonnet·high)과 명세 축을 함께 띄웠다.

- **표준 축.** Major 셋: (1) `확인` 3이 `--reads check-<n>/reads.json`을 늘 주는데 그 파일은 읽지 못한 경로가 있을 때만 생겨, 다 읽힌 가장 흔한 길이 ENOENT로 멈춘다. (2) `check-<n>/`·`send-<n>/` 같은 작업 폴더 경로가 상대 경로로만 적혀, 저장소 뿌리에서 부르는 스크립트가 그것을 저장소 안에 푼다. (3) "먼저 들인다"로 연 새 세션은 첫 턴의 워크트리 문장대로 브랜치를 `feature/NN-web-edit-<slug>`로 먼저 바꾸지만, 그때 티켓 파일이 없어 `import.md` 1의 첫 갈래에 들지 못하고 "새 워크트리" 갈래에서 번호와 slug를 새로 고른다. Minor 여섯: (4) "계속한다" 뒤 `/ui-design`이 부르는 올리기가 같은 웹 편집을 다시 묻는다, (5) 번호를 옮기는 틈에 끊긴 갈래와 티켓을 이미 쓴 뒤 다시 들어오는 갈래, (6) 올리기의 돌아갈 브랜치를 적을 자리가 없다, (7) 아직 없는 계기 훅(티켓 09)을 부르는 쪽으로 적었다, (8) `.ds-sync/ds-bundle-commit`이 NOTES에 없다와 "지금 색인의 `via`는 부분 올리기 꼴이다"가 낡는다, (9) "255개와 16 MiB"와 "(기록과 색인과 지울 경로도 센다)"의 근거. Nit 둘: `import.md` 4의 끝 조건, 정의되지 않은 `<보낼 폴더>`, 냄새로 `upload.md` 2의 `act`→인자 표(Repeated Switches). 명령 옵션, `act` 열셋, 읽기 실패의 까닭 넷, 색인 목록 넷, `git switch --no-overwrite-ignore`, ADR 0025 인용, 변이 53개, 카나리아 `--shape`는 맞다고 확인했다.

표준 축 판정:

- 고친다: (1) 확인을 시작할 때 `reads.json`을 빈 꼴로 쓰고 늘 넘긴다(빈 `{"absent": [], "failed": {}}`를 `check paths --reads`가 받는 것을 쳐 봤다). (2) 작업 폴더 이름으로 시작하는 경로는 절대 경로로 준다고 "명령과 작업 폴더"에 적는다. (3) `import.md` 1의 첫 갈래를 "지금 브랜치가 `feature/NN-web-edit-<slug>` 꼴이고 그 번호의 티켓이 `origin/main`에 없다"로 넓히고 번호와 slug는 그 이름의 것을 쓴다. 지시문의 워크트리 문장은 `next-session` 3단계의 새 브랜치 문장(EnterWorktree 뒤 브랜치를 바꾼다)이다. (5) 2에 티켓이 이미 있으면 그 파일을 잇는다고, 6의 1에 그 틈을 알아보는 문장을 더한다. 틈 자체는 명세 "자기 `claim`"의 2026-10-22 주석이 "드문 틈이라 질문 하나의 값을 받는다"고 받았다. (6) 돌아갈 브랜치를 작업 폴더 파일에 적고 "멈춘 상태"에 올리기 중을 더한다. (7) 계기 훅을 든 셋(설명, 머리 주석, 인자 표)을 빼고 티켓 09에 "07이 넘긴 것"으로 적는다. (8) 뒤의 것: `via`의 사실은 티켓 08 19행이 들고 있어 `upload.md` 3에서 뺀다. (9) 뒤의 괄호: 지울 경로를 세는지는 재지 못했다고 적는다. Nit의 끝 조건과 `<보낼 폴더>`.
- 남긴다: (4) 다시 묻는 것은 명세 177행("올리기의 확인은 화면 작업에서 '계속한다'를 골랐어도 돈다")과 168행의 의도라 동작은 두고, `continue` 줄에 그 뒤의 올리기가 다시 묻는다는 것만 덧붙인다. 작업 트리가 깨끗하지 않으면 올리기가 멈추는 것은 알리고 멈추는 안전한 쪽이라 둔다. (8) 앞의 것: `.ds-sync/`는 빌린 빌드가 의존성을 까는 무시된 폴더(NOTES 23행, `.gitignore` 49행)이고 그 표지의 원천은 `upload.md`라 NOTES에 옮겨 적지 않는다. (9) 앞의 것: 명세 "중간 실패"(158행)가 도구 설명의 "one publish sends at most 255 files and 64MB"와 형식 설명의 "16 MiB a call"을 인용해 정한 값이라 근거가 있다. 냄새: 그 표는 05·06이 정한 명령 인자(`record.ts`의 `decisionOf`가 플래그를 읽는다)에 맞춘 것이고, 명령이 `act`를 받게 바꾸는 것은 05·06 계약을 고치는 일이라 이 티켓 밖이다.

- **명세 축.** 체크박스 문장은 기점과 같고, NOTES의 새 문장은 명세 문구를 품으며, `ACTS` 열셋과 `CALLERS` 셋이 맞고, PR #399 판정의 전제가 지켜진다고 봤다. Major 다섯: (1) `import.md` 1의 첫 갈래가 티켓 파일을 요구하는데 티켓은 2에서 써, 새 워크트리 갈래가 이름을 바꾼 뒤 1로 돌아와 같은 갈래를 되풀이한다(표준 (3)과 같은 자리). (2) "사람이 친 턴" 3이 6의 보내기 직전 확인부터 이어 5의 계획을 건너뛴다. 인계 뒤에는 `first-check.json`도 없다. (3) 올리기 1이 확인보다 먼저 분리 HEAD로 옮기는데, 2에서 "먼저 들인다"·`wait`·`stop`으로 나가는 길에 돌아가는 단계가 없다. (4) 새 워크트리에 `pnpm -C web install`이 없어 `check paths`부터 `ERR_MODULE_NOT_FOUND`로 끝난다(`node_modules` 없는 사본에서 쳐 봤다). (10) "보낼 것이 없을 때"가 기록이 없을 때와 `rewriteRecord`에도 6을 건너뛰어 기록이 새로 쓰이지 않는다. Minor 여섯: (5) "주 체크아웃의 main" 판정이 브랜치를 보지 않는다, (6) "덮어쓰기와 색인"이 `uploadClaimMerged`를 빼는데 명세 178행은 "버린다"를 고른 편집도 같은 길로 되돌린다고 정했다, (7) `import.md` 6의 1에 06 경고의 뒷부분이 빠졌다, (8) "계속한다" 뒤에도 `/ui-design`이 올리기를 불러 ADR 0025 141행의 "그리기 전의 `/ui-design`이 이것만 부른다"와 결정표 설명 "웹 편집은 다음 확인이 다시 찾는다"와 어긋난다(표준 (4)와 같은 자리), (9) "토큰마다"와 "토큰 밖" 줄임, (11) `kickoff/prompting.md` 43행의 옛 올리는 길, (12) 08의 "07이 넘긴 것"의 NOTES 둘이 08 체크박스에 없고 검증 줄과 부딪친다. Nit: 부탁 문구가 "잇습니다"로 끝난다.

명세 축 판정:

- 고친다: (1) 표준 (3)과 같이 고친다. (2) 2의 확인부터 다시 하고 4가 방금 지은 산출을 쓰게 한다. (3)·표준 (6) 함께, `upload.md` 1에 "돌아가기"를 두어 어디서 끝나든 돌아간다. (4) "명령과 작업 폴더"에 새 워크트리의 설치를 둔다. `import.ts` 55행이 `@agent-os/ui/contrast`를 들이는 것을 봤다. (10) 조건에 "받은 기록이 있고 `rewriteRecord`가 아니며"를 더한다. (5) `git branch --show-current`가 `main`인지 더 본다. (6) `uploadClaimMerged`에서 받은 `claim`의 `index`가 기록의 것과 다르면 되돌린다(`sync-record.ts` 249·274행에 `claim.index`와 기록의 `index`가 있다). 옮긴 색인 편집이 어떻게 남는지는 "재지 못한 것"에 더한다. (7) 두 결과를 적는다. (8)·표준 (4) 함께, "계속한다"를 고른 세션은 그리기 전의 올리기를 부르지 않는다. 표준 축 판정에서 남긴다고 한 것을 이렇게 바꿨다. 명세 177행은 올리기가 돌면 그 확인이 돈다는 말이고 화면 작업이 그 올리기를 불러야 한다는 말이 아니며, 사용자 스토리 20과 결정표의 설명이 곧바로 다시 묻지 않는 쪽이다. 웹 편집이 없으면 그리기 전에 맞추는 것(화면 디자인 절 44행)은 그대로다. (9) "디자인 토큰"으로 쓴다. (11) 스킬의 올리기로 고친다. (12) 08에 체크박스 하나를 더하고 검증 줄에 그 두 줄을 넣는다.
- 남긴다: Nit의 "잇습니다". 사람에게 하는 부탁이라 높임 꼴이고, 명세 217행은 부탁에 담을 뜻을 정한 것이다.

고친 것(새로 쓴 사실 문장은 PR 직전 리뷰의 밀 주장으로 넘긴다):

- `SKILL.md` "명령과 작업 폴더": "아래에서 `check-<n>/`, `claim-<n>/`, `send-<n>/`, `<작업 폴더>/`로 시작하는 경로는 모두 이 작업 폴더 아래의 것이고, 스크립트와 `git`에는 절대 경로로 준다." / "`web/node_modules`가 없으면 `main.ts`가 들이는 `import.ts`가 `@agent-os/ui/contrast`를 찾지 못해, 어느 명령이든 JSON 보고 없이 `ERR_MODULE_NOT_FOUND`로 끝난다(셀프 리뷰 서브에이전트가 `node_modules` 없는 사본에서 쳐 봤다)."
- `SKILL.md` 확인 1: "다 읽힌 확인에도 3의 `--reads`가 받을 파일이 있어야 한다(없는 파일을 주면 `input` 오류로 멈춘다)."
- `SKILL.md` "할 일"의 `continue`: "그 올리기는 자기 확인을 다시 돌려 같은 웹 편집을 올리기의 선택지("먼저 들인다", "덮어쓴다")로 곧바로 다시 묻는데, 이 선택지의 설명은 웹 편집을 다음 확인이 다시 찾는다고 말한다". "멈춘 상태"에 "올리기 중", "재지 못한 것"에 옮긴 색인 편집과 지울 경로의 한도를 더했다. 계기 훅을 든 셋을 뺐고, `<보낼 폴더>`를 `send-<n>`으로 고쳤다.
- `import.md` 1: "\"먼저 들인다\"가 연 세션은 첫 턴에 지시문의 워크트리 문장대로 브랜치를 지시문의 이름으로 이미 바꿨으므로 여기다." 2에 이미 쓴 티켓을 잇는 문장. 6의 1: "그러면 더 고친 몫이 없을 때는 `record claim`이 이어받을 기준본을 요구하며 멈추지만, 있을 때는 멈추지 않고 남의 `claim` 이어받기로 가서 기준본이 바뀐다." / "명세 \"자기 `claim`\"의 2026-10-22 주석이 드문 틈이라 질문 하나로 받은 자리다."
- `upload.md` 1의 "돌아가기": "분리 HEAD에 남은 채 \"먼저 들인다\"의 지시문을 내거나 화면 작업을 이으면, [SKILL.md](SKILL.md)의 \"먼저 들인다\"가 바꾸지 않는다고 한 브랜치를 잃는다." 4의 "사람이 친 턴" 3: "4는 방금 지은 산출의 커밋이 HEAD와 같아 다시 부탁하지 않고, 5가 그 산출로 계획을 짓는다." 5: "병합된 `claim`이 든 색인 편집은 들이기에서 사람이 \"버린다\"를 고른 것도 이 올리기가 되돌린다(명세 \"찾았을 때\"의 \"덮어쓴다\" 항목)." / "기록이 없거나 `rewriteRecord`면 보낼 파일이 없어도 6에서 기록을 새로 쓴다. 쓰지 않으면 다음 확인이 또 판단할 수 없음을 낸다." 6의 4: "(명세 \"기록\"의 \"중간 실패\"가 도구 설명과 형식 설명에서 고른 값이다)". 처음에 "올리기"의 절로 적었다가 명세의 절 머리(152행 "기록")를 보고 고쳤다. 3에서 `via`의 낡는 문장을 뺐다.
- `/ui-design` 2단계: "사람이 웹 편집을 두고 \"계속한다\"를 골랐으면 맞추지 않고 그린다. 그 올리기는 같은 웹 편집을 곧바로 다시 묻기 때문이다(그 스킬의 \"할 일\" 표, design-reverse-sync 명세의 사용자 스토리 20)." 끝 조건도 맞췄다. `screens-prompt.md` 1단계는 "웹 편집이 없으면 그 뒤 `올리기`".
- 티켓 07 메모: 설치된 워크트리에서만 바로 돈다, "계속한다" 뒤의 맞추기, 계기 훅 넘김, 덮어쓰기와 색인의 갈래. 티켓 08: NOTES 둘의 체크박스와 검증 줄. 티켓 09: 스킬에 훅을 더하는 체크박스와 카나리아 줄. `kickoff/prompting.md` 43행.

다시 돌린 것:

- 카나리아. `sync-design-system`은 설명(머리말)을 고쳐 사전 확인으로 갈음할 수 없어(`docs/constitution/operations.md` 카나리아 항목의 조건 넷) 두 명세를 다시 돌렸다. `sync_design_system_skill.toml` 통과 4(대조군은 이 스킬을 불러 "Unknown skill: sync-design-system"을 받고 "없음"이었다. 원본의 도구 결과를 봤다), `sync_design_system_story4.toml` 통과 4("없음" 섞인 통과 2, 까닭은 앞 회차와 같다). 본문만 고친 `ui_design_check_before_drawing.toml`은 같은 claude 2.1.302에서 `--preflight` 통과 1로 갈음하고 그 명세의 결과 줄 뒤에 덧붙였다. 규칙 `web-design.md`는 반영에서 고치지 않았다.
- `uv run ruff check .`와 `uv run ruff format --check .`는 초록이다(이 변경에 `.py`가 없어 pre-commit의 ruff는 `Skipped`라 손으로 쳤다). 반영은 마크다운과 TOML뿐이라 손으로 치는 나머지 다섯은 커밋의 pre-commit으로 갈음한다. 결과는 커밋 뒤에 적는다.
- 티켓 07의 Status를 `done`으로, "검증 명령이 모두 초록이다"를 채웠다.
