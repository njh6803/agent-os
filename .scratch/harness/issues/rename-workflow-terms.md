# rename-workflow-terms: 용어집의 작업 규약 쪽 이름 셋을 쉬운 이름으로 바꾼다

**What to build:** 용어집(`CONTEXT.md`)의 이름 가운데 작업 규약을 다루는 셋이 처음 보는 사람에게 낯설다. 사용자가 2026-11-18에 고른 새 이름으로 바꾼다(일지 2026-11-18-1036의 "정해진 이름 바꾸기"). 같은 날 고른 "작업 규약과 화면" 묶음 다섯 가운데 화면 쪽 둘(거꾸로 동기화, 원색 토큰)은 디자인 시스템 아티팩트 올리기가 따라서 다음 PR로 나눴다(일지 2026-11-18-1559의 "다섯을 둘로 나눈 까닭". 이 티켓의 판단이고 사용자가 고른 것은 아니다).

| 옛 이름 | 새 이름 | 가리키는 것 |
|---|---|---|
| 노트 조각 | 릴리스 노트 원고 | 릴리스 노트에 글자 그대로 실릴 글을 담은 파일 하나(기능 단락, 올릴 때 할 일, 소개 글) |
| 되돌려 합치기 | 운영에서 개발로 합치기 | 운영 브랜치(main)에 먼저 올라간 변경을 개발 브랜치(dev)에도 합치는 것 |
| 루트 브랜치 | 주 체크아웃이 따르는 브랜치 | 주 체크아웃이 따라가는 브랜치(`origin/dev`가 있으면 dev, 없으면 main) |

용어집의 영어 이름(Note Fragment, Back-merge, Root Branch)과 파일·식별자 이름(`check_notes.py`, `release-note-fragments`가 든 티켓 이름, `backmerge_diff_check.sh`, 카나리아 명세 이름 `dev_base_tidy_root_branch` 등)과 테스트 함수 이름은 그대로 둔다.

**이름을 바꾸는 범위.** 앞 티켓 `.scratch/harness/issues/rename-small-run-terms.md`가 간 길과 같다. 용어집과, 그 이름이 쓰인 살아 있는 문서(헌법 `operations.md`, `docs/agents/issue-tracker.md`, 스킬, 기능 계획, `.scratch/harness/probes/`, 열린 대기열 항목), 워크플로와 PR 서식, 코드 주석과 독스트링, 오류 문구와 그것을 맞대는 시험에서 바꾼다. 받침이 달라지는 "노트 조각"은 뒤의 조사도 고친다(조각이 → 원고가, 조각을 → 원고를, 조각과 → 원고와). 바꾸지 않는 것은 여섯이다.

- 일지.
- 끝난 기능의 명세·티켓·프로브. release-image는 기능 계획에 `끝` 줄(2026-11-16)이 있고 티켓 열하나가 모두 done이라 그 명세·티켓·프로브는 기록이다. 기능 계획 `.scratch/release-image/plan.md`만 살아 있어 바꾼다. done인 harness 티켓(dev-base-skills-docs, dev-branch-create, dev-branch-transition, dev-release-pr-step, review-pipeline-docs-name-bang-check)도 기록이다.
- ADR의 본문과 제목과 색인. 옛 이름이 본문에 든 ADR 셋(0043, 0056, 0066)에 이력 한 항목씩 단다. 본문이 지난 이력 항목의 제목을 글자 그대로 따온 곳(0043의 포인터 둘, 0056의 포인터 둘)도 그대로 두고 이력 항목에 그렇게 적는다.
- 다른 글이 지난 제목이나 항목 이름을 글자 그대로 따온 곳. ADR 0043 이력 제목 "출시 PR 뒤에도 main을 dev에 되돌려 합친다"를 따온 `tests/tools/test_protection_json.py`의 독스트링, ADR 0056 이력 제목 "릴리스 노트에 세션이 미리 쓴 노트 조각을 싣는다"를 따온 `.scratch/release-image/plan.md`, ADR 0043 결과 절의 항목 이름 "되돌려 합치기"를 가리키는 `next-session` `merge.md`의 한 곳이다.
- 카나리아 명세 머리의 결과 줄(`# 최신 결과:` 줄과 그 뒤에 이어 적은 줄, `# 그 전 결과:` 줄). 살아 있는 문서 안의 이력이다.
- 리뷰 봇 워크플로 `.github/workflows/claude-code-review.yml` 67행의 절 이름 "릴리스 노트 조각". 그 파일을 바꾼 PR은 리뷰 봇이 건너뛰고, 그 워크플로의 가드 스텝(`Fail when Claude left no comment`)이 일지·대기열·티켓·하네스 탐침 밖의 파일을 함께 실은 PR을 실패로 만든다(`docs/constitution/operations.md` 48행과 리뷰 파이프라인 3). 그래서 이 PR에서는 그대로 두고 이 PR을 병합한 뒤 그 한 줄만 따로 PR로 낸다. 받는 쪽은 대기열 항목 `glossary-plain-names-left`의 남은 목록이다. 리뷰 봇은 그 절을 절 이름이 아니라 "느낌표의 기준"이라는 글자로 찾으므로(그 프롬프트의 같은 줄), 두 PR 사이에 절 이름이 어긋나도 찾는 문단은 같다.

**함께 고치는 것.**

- 새 이름을 그대로 끼우면 어색해지는 문장은 사실을 그대로 두고 고친다.
  - `tidy-checkouts` 정의 문단: "**루트 브랜치.** 주 체크아웃이 따르는 브랜치다. `git fetch origin` 뒤 …" → "**주 체크아웃이 따르는 브랜치.** `git fetch origin` 뒤 …"(이름이 곧 풀이가 되어 첫 문장을 뺐다).
  - `tidy-checkouts` 설명(머리말): "주 체크아웃을 루트 브랜치(…)로 당기고" → "주 체크아웃을 그 체크아웃이 따르는 브랜치(…)로 당기고".
  - `next-session` `directive.md` 30행: "주 체크아웃이 루트 브랜치(…)가 아니거나" → "주 체크아웃이 자기가 따르는 브랜치(…)에 있지 않거나".
  - `sync-design-system` `import.md` 12행: "**주 체크아웃의 루트 브랜치다**" → "**주 체크아웃이고, 그 체크아웃이 따르는 브랜치에 있다**". `upload.md` 9·70행: "주 체크아웃의 루트 브랜치를/는" → "주 체크아웃이 따르는 브랜치를/는".
  - 동사로 쓴 "main을 dev에 되돌려 합친다" 꼴은 "되돌려"를 떼어 "main을 dev에 합친다"로 쓴다. 방향은 앞의 "main을 dev에"가 이미 말한다. `pr-merge` 67행의 "main을 dev에 되돌려 합치기"도 "main을 dev에 합치기"다.
  - 노트 조각을 줄여 쓴 "조각"도 그 뜻으로 쓰인 곳은 모두 "원고"로 바꾼다. 다른 뜻의 "조각"(코드 조각, 경로 조각, 인용 조각, 세션마다 주는 기록 조각)은 그대로 둔다. 예를 들면 `tools/check_notes.py`의 독스트링·주석과 오류 문구("할 일 조각이 아니다", "조각은 비어 있지 않다", "조각에는 없다". 앞의 것은 그 시험 `tests/tools/test_check_notes.py`의 단언과 함께), 워크플로 주석(`ci.yml`, `pr-title.yml`, `release.yml`), `operations.md`의 두 곳, `implement` 스킬의 "`upgrade/` 조각", 시험이 쓰는 커밋 제목과 주석이다. 시험 함수 이름은 위대로 그대로 둔다.
- 절 제목 둘이 바뀐다. `operations.md`의 `## 릴리스 노트 조각` → `## 릴리스 노트 원고`, `next-session` `merge.md`의 `## 되돌려 합치기` → `## 운영에서 개발로 합치기`. 그 절을 이름으로 가리키는 글(PR 서식, `docs/agents/issue-tracker.md`, `implement` 스킬, `next-session` 결정표의 시작 프롬프트 칸, `pr-merge` 스킬, 프로브 README와 `backmerge_diff_check.sh`)도 같이 바꾼다. 리뷰 봇 프롬프트는 위 "바꾸지 않는 것"의 마지막 항목대로 따로 낸다.
- 카나리아 명세 가운데 물음이나 기대 문구나 머리 설명에 옛 이름이 든 아홉은 원천과 같은 규칙으로 바꾼다. `dev_base_tidy_root_branch`는 원천의 첫 문장이 빠져 물음을 "그 문단을 여는 굵은 글씨 부분"으로, 기대 문구를 "주 체크아웃이 따르는 브랜치."로 바꾼다. `dev_base_sync_design_system_import`의 물음은 바뀐 항목 머리를 따른다.
- 대기열 항목 `glossary-plain-names-left`의 "반영한 것"에 이 셋을 옮기고, 남은 목록의 "작업 규약과 화면"을 "화면" 둘로 줄인다.

**카나리아.** 이 티켓이 고친 스킬 파일 아홉(`implement`, `next-session`의 `SKILL.md`·`directive.md`·`merge.md`, `open-session`, `pr-merge`, `sync-design-system`의 `import.md`·`upload.md`, `tidy-checkouts`)을 원천으로 든 명세는 60개다. 사용자가 고른 대로(일지 2026-11-18-1559의 "사용자에게 물은 것") 그 가운데 열만 새 세션으로 돌린다. 이름이 바뀐 문장을 묻는 아홉과 `upload.md`를 확인할 `dev_base_sync_design_system_upload`다. 대조군은 각 명세의 머리 주석이 적은 바뀌기 전 커밋이다. 나머지 50개의 `# 최신 결과:` 줄은 고치지 않는다. dev에서 이미 원천과 어긋난 셋(`next_session_fable_cut_row`, `next_session_model_line`, `tidy_skill_cwd_owner`)은 이 티켓이 고치지 않고 이 단계 일지(`docs/journal/2026-11-18-1559-rename-workflow-terms.md`)의 "다음" 절에 남긴다.

로컬 모델 시험은 돌리지 않는다. 이 티켓이 고치는 파일에 병합 조건의 범위(`docs/constitution/operations.md` LLM 테스트)에 드는 경로가 없다.

**대기열:** glossary-plain-names-left

**Status:** done

## 수용 기준

- [x] `CONTEXT.md`의 이름 셋이 새 이름이고, 풀이마다 피할 말에 옛 이름이 바꾼 날짜와 함께 들어 있다. 풀이의 사실은 그대로다
- [x] 살아 있는 문서와 코드 주석, 오류 문구의 옛 이름이 새 이름이다. 남은 것은 이름을 바꿨다는 기록과 바꾸기 전의 글을 따온 자리뿐이다(용어집의 피할 말 줄 셋, 새로 단 ADR 이력 셋, 대기열 항목이 옛 이름으로 적은 반영 기록과 남은 일, `dev_base_tidy_root_branch` 머리 설명이 옛 굵은 머리를 밝힌 한 곳, 위 "바꾸지 않는 것"). 줄바꿈으로 갈린 꼴로도 훑었다
- [x] 옛 이름이 본문에 든 ADR 셋(0043, 0056, 0066)에 이력 한 항목씩 달았다. 본문과 제목과 색인은 그대로다
- [x] 고른 카나리아 열이 새 세션에서 통과했고 그 명세의 `# 최신 결과:` 줄을 고쳤다. 통과한 뒤 원천을 고친 명세는 다시 돌리거나 사전 확인으로 갈음했다(`docs/constitution/operations.md` 카나리아 항목의 조건 넷)
- [x] 대기열 항목 `glossary-plain-names-left`의 "반영한 것"에 셋이 있고, 남은 목록에서 빠졌다. 상태는 열림이다
- [x] 검증 명령이 모두 초록이다
