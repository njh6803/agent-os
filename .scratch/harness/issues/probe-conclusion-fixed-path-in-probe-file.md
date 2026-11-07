# probe-conclusion-fixed-path-in-probe-file: 프로브 결론 훅이 프로브 파일에 적은 "고친 길" 문장도 짚는다

**What to build:** `tools/hook_probe_conclusion.py`는 프로브 README(`.scratch/**/probes/**/README.md`)를 Write·Edit로 쓰거나 고칠 때만 알린다. 그런데 고친 길의 표지를 단정한 문장은 README 밖에도 적힌다. 대기열 535의 사례는 프로브 스크립트 `.scratch/harness/probes/widget_char_count/repeat.mjs`의 머리 주석이 고친 길의 표지(`lateEffect`, 카드 직후 포커스가 제목이 아닌 회차)를 "고치기 전 판에서는 빨갰다"고 단정한 것이다. 효과가 시험의 포커스보다 먼저 돌면 고치기 전 판도 초록이라, 그 표지는 `.claude/rules/probes.md` 첫 항목의 고친 길 꼴(고치기 전 판이라면 실패했을 회차에서만 나는 관찰)을 어겼다. 이 훅의 독스트링이 "못 보는 것"으로 적은 README 밖의 결론이 그대로 난 것이다. 셀프 리뷰는 지나가고 PR 직전 리뷰의 대체 읽기가 잡았다. 367부터 센 5회차라 지침(`probes.md` 첫 항목)을 적은 뒤에도 어겨진 것으로 보고 계기 훅으로 올린다(CLAUDE.md 교정 루프). 막는 훅이 아니다.

바꿀 것:

- **발동 조건을 더한다.** 도구가 Write·Edit이고 `file_path`가 `.scratch` 뒤에 `probes` 토막이 있는 경로의 README가 아닌 파일이며, 더한 글(Write의 `content`, Edit의 `new_string`)에 "고친 길"이 들면 알린다. 지우는 쪽 글(`old_string`)에만 든 편집과, 더한 글에 낱말이 없는 편집에는 알리지 않는다. README는 지금 판정 그대로 두고 이 조건을 적용하지 않는다(README는 더한 글에 그 낱말이 없어도 알린다).
- **문장은 따로 짓는다.** 프로브 README의 문장(셋째 항목과 근거의 종류)을 그대로 쓰지 않고 고친 길의 표지를 짚는다. `probes.md` 첫 항목을 가리키며, 그 표지가 고치기 전 판이라면 실패했을 회차에서만 나는 관찰인지, 고치기 전 판도 같은 관찰을 냈을 길(효과가 시험의 포커스보다 먼저 돌 때 등)은 없는지 묻는다. 확인하지 않았으면 그 문장을 단정하지 않고 어림이라고 적게 한다.
- **표지(한 번만 알리는 파일)는 README 알림과 따로 둔다.** 같은 표지를 쓰면 세션이 프로브 파일의 알림을 먼저 받은 뒤 README의 결론에는 알림이 오지 않고, 반대도 같다. 판정마다 표지 이름이 다르게 한다. 기존 README 표지 이름은 바꾸지 않는다.
- **같은 파일을 고치는 문서를 맞춘다.** 훅 독스트링의 머리와 판정과 못 보는 것(README 밖에 적은 결론이 전부 지나간다는 줄을 이 몫만큼 고친다. 프로브 파일의 다른 낱말, 주석 밖의 변수 이름, Bash로 쓴 파일은 여전히 못 본다), `.claude/rules/tools.md`의 Write·Edit 시간 항목 중 이 훅의 줄(경로 문자열과 더한 글을 본다), `docs/agents/issue-tracker.md`의 프로브 절에서 이 훅을 설명한 문장.

판정할 입력(읽는 것은 페이로드의 경로와 더한 글뿐이고 파일은 열지 않는다):

- 알린다: 프로브 `.py`·`.mjs`·`.sh`·`.toml` 파일의 Write·Edit에서 더한 글에 "고친 길"이 있다.
- 지나간다: 같은 경로의 편집에서 더한 글에 낱말이 없다, 낱말이 `old_string`에만 있다, 프로브 폴더 밖의 파일(`tools/`, `.scratch/<기능>/spec.md`)이다, Bash로 쓴 파일이다.
- 한 번만 알린다: 프로브 파일의 알림과 README의 알림이 서로의 표지를 쓰지 않는다. 세션·에이전트마다 각각 한 번이다.

못 보는 것(독스트링에 적고 시험 하나로 고정한다): 낱말 "고친 길"이 없는 표현("수정한 경로", "고친 판이 지났다"), 프로브 폴더 밖에 옮겨 적은 같은 문장(명세·ADR은 `hook_probe_citing_doc`의 몫이다), 낱말이 있어도 고친 길의 표지 문장이 아닌 경우(거짓 양성. 값이 작다).

**대기열:** 535

**Status:** done

## 수용 기준

- [x] 시험을 먼저 썼다(`tests/tools/test_hook_probe_conclusion.py`). 알림 발동, 낱말이 `old_string`에만 있을 때 지나감, 낱말 없는 편집이 지나감, 프로브 폴더 밖의 파일이 지나감, README 알림과 표지가 서로 독립, 문장이 `probes.md` 첫 항목을 가리킴. 시험을 쓴 뒤 훅을 고치기 전에 시험을 돌려 빨강을 보지는 않았다(새 이름을 import하는 시험이라 훅을 고치기 전에는 import 오류였을 것이다. 어림이다)
- [x] 위 입력대로 `hook_probe_conclusion.py`가 동작하고, 기존 README 시험(표지 이름 포함)이 그대로 초록이다(시험 39개)
- [x] 못 보는 것 항목마다 시험 하나가 있다(`.claude/rules/tools.md` "못 보는 것" 규칙)
- [x] `tools/hook_payloads.toml`에 발동 하나와 발동하지 말아야 할 실제 입력 하나를 더했다. 래퍼를 거친 실행 확인은 pre-commit 러너가 한다(워크트리 세션의 훅은 주 체크아웃 파일이 돌기 때문)
- [x] 훅 독스트링, `.claude/rules/tools.md`의 시간 항목 줄, `docs/agents/issue-tracker.md`의 설명 문장이 새 판정과 맞다. 옛 표현("프로브 README일 때만")은 카나리아 명세가 글자 그대로 기대하는 문장이라 그대로 두고 새 몫을 이어 적었다
- [x] 대기열 항목 `.scratch/retro-queue/0535.md`의 상태를 `닫힘 (…)`으로 고쳤다
- [x] 변이 표 `probe_conclusion_hook_mutations.toml`을 새 코드에 맞췄다(어긋난 둘을 고치고 새 동작을 깨는 셋을 더했다). 서른하나 모두 기대대로였다
- [x] 규칙 파일 `.claude/rules/tools.md`를 고쳤으므로 카나리아 `tools_rule_probe_conclusion_hook.toml`을 새 `claude -p` 세션으로 돌렸다. 통과 4, 실패 0이고 명세의 `# 최신 결과:` 줄을 고쳤다
- [x] 검증 명령이 모두 초록이다(셀프 리뷰 뒤 ruff 둘은 손으로 쳐 통과, 나머지 손으로 치는 다섯은 커밋의 pre-commit 결과로 갈음한다. 시험은 거짓 양성 몫을 더해 40개다. 원 문구: 손으로 치는 명령 전부와 `uv run python tools/run_checks.py`. 커밋 직전의 pre-commit이 갈음하는 것은 그 결과로 갈음한다). `uv run python tools/plan_table.py`로 전체 계획 표를 돌려 필요하면 같은 커밋에 싣는다
