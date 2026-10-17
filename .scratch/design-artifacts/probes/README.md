# design-artifacts 프로브

ADR 0025의 2026-10-16 이력이 근거로 드는 측정이다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거"이고 짓는 규칙은 `.claude/rules/probes.md`다.

아티팩트를 읽고 쓰는 일은 Claude Code의 Artifact 도구로만 되고 스크립트가 부를 수 없다. 그래서 도구가 낸 값(판 id, 바이트 수, sha256)을 `artifact_reads.json`에 옮겨 적고, 그 기록을 저장소 사본과 맞대는 몫을 스크립트로 둔다. 공식 안내 문서는 원문을 저장소 밖 작업 폴더에 내려받아 스크립트로 문장과 표를 대 본다.

저장소 루트에서 돈다.

```sh
node .scratch/design-artifacts/probes/hash_match.mjs [--record <기록 파일>] [--saved <받은 파일 폴더>]
node .scratch/design-artifacts/probes/pricing_rows.mjs <작업 폴더>/pricing.html "Project sharing and collaboration" "Claude Design"
node .scratch/design-artifacts/probes/find_sentences.mjs <작업 폴더>/<문서>.html "구절" ...
```

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `hash_match.mjs`, `artifact_reads.json`, `published/design-system.json` | 디자인 시스템 아티팩트에서 읽은 파일마다 도구가 낸 sha256과 저장소 사본의 sha256이 같은지. 저장소 쪽은 줄의 `commit`에서 꺼내(없으면 작업 트리) 나중에 저장소가 바뀌어도 결과가 그대로다. 같은 판이어야 하는 짝 여섯(양성)과 달라야 하는 짝 둘(음성 대조)을 둔다. `--saved`로 받은 파일 폴더를 주면 받은 바이트의 sha256이 도구가 낸 값과 같은지도 본다. 다른 기능은 자기 기록 파일을 `--record`로 준다. 모르는 인자, 값 없는 옵션, `--옵션=값` 꼴은 2로 끝나고, `commit`이 16진수 7~40자가 아니면 측정 아님으로 센다(`git show`가 옵션으로 읽을 값을 막는다) | ADR 0025 이력 2026-10-16의 첫째 항목(빌드의 경로와 아티팩트의 경로가 같다)과 둘째 항목(편집자 쓰기), `docs/agents/issue-tracker.md` 화면 디자인 절의 판 맞대기 | 아티팩트를 다시 읽어(`read`의 `paths`, `out_dir`) 기록에 줄을 더하고 받은 폴더를 `--saved`로 준다 | 아티팩트 판 `1792113436-f9ea`(옮긴 그대로)와 `1792115455-aa71`(쓰기 탐침 뒤), 저장소 `df705c17`, Node 24 |
| `pricing_rows.mjs` | 요금제 비교표의 행(프로젝트 공유와 협업, Claude Design)이 요금제마다 무엇인지 | 같은 이력의 맺음 문단(개인 요금제에는 프로젝트 공유와 협업이 없다), `docs/agents/issue-tracker.md` 화면 디자인 절의 계정 항목 | 원문을 다시 받는다. 고른 행을 못 찾거나 읽지 못한 칸이 있으면 1로 끝난다 | 2026-10-16에 받은 claude.com/pricing |
| `canary/web_design_artifact.toml` | `.claude/rules/web-design.md` 머리 문단에서 고친 문장(판단 기준 파일이 디자인 시스템의 guidelines로 담겨 아티팩트에 올라간다)이 `paths` 안의 파일을 Read로 열 때 새 `claude -p` 세션에 실리는지. `tools/canary.py`로 돈다 | `CLAUDE.md` 작업 규약 3(바꾼 rules를 새 세션에서 불러 본다) | 최신 결과는 명세의 머리 주석이다 | 명세의 머리 주석 |
| `find_sentences.mjs` | 공식 안내 문서에서 근거 문장이 원문에 있는지 | 같은 이력의 단독 Claude Design 종료일, 프로젝트는 단독 쪽에 남는다는 것, 다시 옮기기의 건너뛰기, 이메일 초대와 초대할 수 있는 사람, 개인 계정 사이에 옮기지 않는다는 것, Team의 업무용 이메일. 주인을 옮기는 방법이 없다는 것은 없음을 찾는 말이라 이 스크립트로 재지 못한다(손으로 읽었다) | 원문을 다시 받는다. 구절이 하나라도 없으면 1로 끝난다 | 2026-10-16에 받은 support.claude.com 17440474·9547008·9267247, support.anthropic.com 9450526 |

## 2026-10-16 결과

- `hash_match.mjs`(받은 파일 폴더와 함께): 측정 15, 측정 아님 0, 기대와 다름 0. `df705c17`의 `.claude/rules/web-design.md`와 `.design-sync/foundations/` 아래 네 파일이 아티팩트의 `project/guidelines/web-design.md`, `project/foundations/<이름>/index.html`과 바이트까지 같다. 이 다섯은 빌드가 `ds-bundle/`로 그대로 옮기는 원본이라, 빌드의 `ds-bundle/<경로>`가 아티팩트에서는 `project/<같은 경로>`다(빌드 산출 자체는 맞대지 않았다). 이 브랜치가 뒤에 `web-design.md`의 머리 문장을 고쳐 지금 저장소의 그 파일은 아티팩트와 다르고, 병합 뒤 올린다. 음성 대조 둘(다른 파일, 쓰기 전의 색인)은 다르다고 나왔다. 쓰기 탐침이 올린 색인(`published/design-system.json`)은 다시 받은 판 `1792115455-aa71`의 파일과 같다. 받은 바이트 일곱의 sha256이 모두 도구가 낸 값과 같다.
- `pricing_rows.mjs`: 표 0(Free, Pro, Max 5x, Max 20x)의 "Project sharing and collaboration"은 넷 다 no, 표 4(Team, Enterprise 둘)는 셋 다 yes. "Claude Design"은 모두 yes.
- `find_sentences.mjs`: 원문에서 다음 구절을 찾았다(문서 넷, 구절 열하나, 없음 0). 이전 안내의 "will close on December 14, 2026", "Your projects stay in the standalone version", "On individual plans, nothing is shared", "Not all at once"(프로젝트는 하나씩 내려받는다), "Changed in Claude since it was migrated"와 "left as they are"(다시 옮기기는 Claude에서 바뀐 디자인 시스템을 건너뛴다). 공유 안내의 "To give specific people access, invite them by email", "Available in beta on Pro, Max, Team, and Enterprise plans", "Who can invite: The artifact's owner". 내보내기 안내의 "we don't support migrating data between personal accounts". Team 안내의 "The account creator must use a business email address". 웹 요약이 "On later runs, systems changed in Claude are skipped"라고 옮긴 문장은 원문에 그 글자로는 없고, 위 두 구절이 같은 뜻이다.

## 손으로 본 것 (2026-10-16)

스크립트로 다시 낼 수 없는 도구와 브라우저 조작이다.

- **옮기기.** njh4803으로 로그인한 내장 브라우저에서 claude.ai의 Artifacts 화면 "팀 디자인 시스템 마이그레이션"을 눌렀다. 따로 확인 창 없이 돌았고 "완료. 디자인 시스템 1개 중 1개가 claude.ai에 있습니다"가 떴다. 결과는 https://claude.ai/artifact/8ttLDZQqchfD2ao1XG56GH 이고 파일 874개다. 색인은 `editing: "off"`와 `source`(단독 프로젝트 `0a8386b7…`)를 들고, `tokens.json`은 없으며, 화면에 "Finish the migration" 배너가 뜬다. 옮김 보고(`project/assets/notes/MIGRATION-REPORT.md`)는 "every file of the project ← itself, with its bytes unchanged"라고 적는다.
- **초대와 수락.** 공유 창에서 njh6803 계정의 이메일을 "편집자"로 초대했다. 수락하기 전에는 Claude Code(njh6803, `claude auth status`로 봤다)의 `read`가 "artifact not found"를 냈고 njh6803의 브라우저에서도 열리지 않았다. 사용자가 수락을 누른 뒤 `read`가 "shared with you from another organization (writer…)"로 읽었다. 수락한 뒤에도 njh4803 쪽 공유 창에는 한동안 "초대됨"이 남아 있었다.
- **쓰기.** njh6803의 Claude Code가 색인(`project/design-system.json`)에 `lastChange` 하나만 더해 `publish`했다. 판 6(`1792115455-aa71`)이 되었고, njh4803의 브라우저에서 아티팩트가 그대로 열렸다.
- **디자인 시스템 목록.** 수락한 뒤 Claude Code의 `quickstart`(intent design)가 "the account lists no design systems"를 냈고, `list`(scope shared)는 "Artifacts shared from another organization are not listed here yet"라고 적었다. 다른 조직이 공유한 디자인 시스템은 Claude Code의 목록에 나오지 않는다.
- **주인.** 공유 창에서 소유자 칸은 고를 수 없게 흐리게 나왔다. 주인을 옮기는 메뉴는 보이지 않았다.

## 재지 못한 것

- njh4803이 Design 아티팩트를 비워서 만들 수 있는지(claude.ai 화면의 "디자인"은 프롬프트로 시작한다), 그것에 이 디자인 시스템을 붙인 채 njh6803의 Claude Code가 편집자로 화면을 그릴 수 있는지. admin-style이 처음 그릴 때 잰다.
- 이 세션의 쓰기 뒤에 "다시 마이그레이션"이 이 디자인 시스템을 실제로 건너뛰는지. 문서의 문장만 봤다.
- `/design-sync` 빌드의 산출 전체(`_ds_bundle.*`, `_preview/*`, `components/**`)가 지금 아티팩트와 바이트까지 같은지. 위 다섯 파일은 저장소에 커밋된 원본이 있어 맞댔고, 나머지는 빌드를 돌려야 나온다.
