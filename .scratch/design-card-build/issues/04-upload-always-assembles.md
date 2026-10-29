# 04: 올리기가 늘 짓기 명령으로 보내고, `.design-sync/`와 `/design-sync`를 드는 글이 사라진다

**What to build:** `/sync-design-system 올리기`가 더는 사람에게 `/design-sync`를 쳐 달라고 부탁하지 않는다. 확인과 결정, 커밋 맞대기 뒤 늘 `assemble`을 돌려 산출 전체를 맞추고, 03의 계획 보고(첫 정식 올리기, 몫, `libraries`·`upgraded`)대로 보낸다. 거꾸로 동기화 뒤의 올리기가 사람 손 없이 한 세션에서 끝난다. 올리기가 계속 읽는 원본 셋(README 원본, 기초 카드 원본, 지난 산출 목록)은 올리기 도구 폴더(`web/tools/sync-design-system/`) 아래로 옮기고 `.design-sync/`는 지운다. 옛 절차를 가리키던 규칙·문서·주석·`.gitignore`·정리 도구의 글을 같은 PR에서 고쳐, 살아 있는 문서에 두 절차가 함께 남지 않는다.

이 티켓이 병합되면 다음 올리기가 첫 정식 올리기가 된다. 05가 그 올리기를 하려 하지만, 화면 작업이 그리기 전마다 올리기를 부르므로(`upload.md`의 "보낼 것이 없을 때") 다른 세션의 올리기가 먼저 할 수도 있다. 그래서 첫 정식 올리기를 보낸 뒤의 확인은 05가 아니라 절차에 둔다(아래 "올리기 전환"의 "보낸 뒤" 줄). 이 티켓은 아티팩트에 보내지 않는다.

전환과 지우기를 한 티켓에 둔 것은 결정을 바꾸는 변경이 그 결정을 가리키는 글을 함께 고치는 `CLAUDE.md` 작업 규약 4 때문이다(명세 "티켓의 차례"의 주석, 사용자가 고른 것).

근거는 `.scratch/design-card-build/spec.md`의 "올리기"("늘 짓는다", "`via`", "지난 산출 목록", "옛 별칭 지우기"의 `_ds_sync.json` 줄, "보낸 뒤"), "디자인 시스템 README와 나머지 파일"("README 원본", "옮기며 고칠 글", "옮기기 절", "기초 카드와 지침"), "`.design-sync/`와 함께 고치는 것"(표, "`.gitignore`", "정리 도구", "그 밖의 자리"), "티켓의 차례", 스토리 28과 그 자리들의 2026-10-29 명세 검토 주석이다. 결정은 ADR 0025 2026-10-28 이력의 "함께 고치는 것"과 "옮겨 가는 동안"이다.

**Blocked by:** 02, 03

**Status:** ready-for-agent

### 시작 전

- [ ] 스킬과 규칙을 고치므로 Skill 도구로 `writing-for-agents`를 부른다(`.claude/rules/agent-docs.md`)

### 올리기 전환

- [ ] 빌드 판정(`needsBuild`, `record needs-build`)과 그 시험을 걷어 낸다
- [ ] 올리기 절차(`.claude/skills/sync-design-system/`의 `SKILL.md`, `upload.md`)가 커밋 맞대기(기준 커밋과 조상 확인) 뒤 늘 `assemble`을 돌린다. 앞 시도의 산출 폴더는 지우고 친다. 짓기가 실패하면 보내지 않고 멈춘다. "빌드가 필요한지", "빌드가 필요 없다"·"빌드가 필요하다"의 갈래, 사람에게 `/design-sync`를 부탁하는 문구, "사람이 친 턴" 절을 걷어 낸다. 그 갈래를 가리키는 다른 절의 문장도 고친다. 예를 들어 "보낼 것이 없을 때"의 "3의 "빌드가 필요한지"가 필요 없다고 내어 이 갱신에 닿지 않는다"는 늘 지으면 거짓이 된다. 같은 HEAD에서 다시 들어도 짓고 계획해 그 갱신에 닿는다
- [ ] 계획에는 늘 지난 산출 목록(옮긴 자리)을 준다. 호출 몫은 03의 계획 보고대로 나누고, 손으로 나누던 문장과 `_ds_sync.json`을 마지막 호출에 싣는 규칙을 걷어 낸다
- [ ] 색인의 `lastChange.via`는 늘 `agent-os main@<짧은 SHA>`다. 부분 올리기의 꼴(`agent-os 부분 main@…`)은 기준 커밋을 읽을 때만 옛 기록을 위해 안다. `libraries`와 `upgraded`는 03이 지은 값을 쓴다
- [ ] "README의 옮기기 절"의 물음 설명에 셋을 적는다. 그 절이 이번 올리기가 지우는 파일을 가리킨다는 것, 캔버스의 복사 목록은 새 README 본문이 든다는 것, 절을 두는 길은 받은 옛 README를 그대로 두어 새 본문을 버리므로 README가 이번 올리기가 지우는 `.prompt.md`를 계속 가리키고 다음 올리기마다 같은 물음이 나온다는 것이다
- [ ] "보낸 뒤"의 확인이 `clean`이고 보낸 파일에 `components/` 아래 경로나 `_ds_bundle.*`가 들었으면, 올린 세션이 앱 안 브라우저로 Components 절을 한 번 열어 카드가 모두 그려지고 칸 아래가 잘리지 않았는지 본다. 깨진 카드를 보면 되돌리지 않고 사람에게 알리며, 고칠 일을 `docs/agents/issue-tracker.md`의 규약대로 티켓으로 쓴다. 계획이 첫 정식 올리기로 본 올리기였으면, 보낸 뒤 파일 목록(`list`의 `scope: "files"`)에 옛 별칭(`components/<무리>/<이름>/…`, `_preview/`, `_vendor/`, `_ds_sync.json`)이 남지 않았는지도 보고, 남았으면 같은 길로 사람에게 알리고 티켓으로 쓴다. 05 전에 다른 세션의 올리기가 첫 정식 올리기를 해도 이 확인은 그 올리기에서 돈다
- [ ] 다 보낸 뒤 지난 산출 목록을 그 올리기에서 `--paths`가 쓴 목록으로 바꿔 커밋한다는 문장이 옮긴 자리를 가리킨다
- [ ] 스토리 28의 주석대로, 옛 `/design-sync`가 다시 올린 파일 가운데 확인이 찾는 것은 기록에 든 마크다운(README와 `guidelines/`의 둘)뿐이고 나머지는 찾지 못한다는 것을 절차의 못 보는 것에 적는다

### 옮기기

- [ ] `.design-sync/conventions.md`를 올리기 도구 폴더 아래로 옮긴다. 이름은 이 티켓이 정한다. `.design-sync/foundations/` 아래 넷과 `.design-sync/upload-output.json`도 옮긴다. 옮긴 파일의 바이트는 그대로다(README 원본은 아래 고칠 글 셋만 바뀐다)
- [ ] 짓기 명령이 README 원본과 기초 카드 원본을 옮긴 자리에서 읽는다
- [ ] 옮긴 README 원본과 기초 카드 원본을 `web/.prettierignore`에 까닭(올라가는 바이트 그대로 둔다)과 함께 더한다. 지난 산출 목록은 지금 꼴(들여쓰기 두 칸, 한 줄 한 경로, 끝 줄바꿈)로 Prettier를 지나는지 `pnpm -C web verify`로 본다
- [ ] README 원본의 글 셋을 고친다. 목업 설치가 복사할 파일 넷(`styles.css`, `fonts/fonts.css`, `_ds_bundle.css`, `_ds_bundle.js`)을 본문이 이름으로 든다. "어디를 읽나"의 `components/<group>/<Name>/<Name>.prompt.md`를 `components/<이름>/README.md`(쓰임)와 Components 절의 카드로 바꾼다. `.d.ts`를 드는 글은 뺀다. 고친 뒤에도 02의 파일 검사가 초록이다
- [ ] `.design-sync/NOTES.md`의 내용을 명세의 표대로 옮긴다. 지난 산출 목록의 뜻과 "빌드가 짓지 않는 파일"은 그 목록을 읽는 계획 함수의 독스트링으로, "기초 카드" 절의 규칙과 카드 이름이 `index`로 보이는 열린 문제는 옮긴 기초 카드 원본 곁의 글로, "사용 규약" 절의 요지는 파일 검사의 독스트링으로, Re-sync risks의 README 옮기기 절 항목은 사실만 `upload.md`의 "README의 옮기기 절"로 옮긴다. 나머지(돌리는 법, driver, 카드 스토리, 고친 것, 포크, 채점, Alert 항목, 계정 항목)는 옮기지 않는다
- [ ] `.design-sync/`의 추적 파일 14개가 모두 옮겨지거나 지워지고 폴더가 없다

### 함께 고치는 글

- [ ] `.claude/rules/web-design.md`에서 변형 스토리를 `.design-sync/config.json`의 skip에 넣으라는 줄을 showcase 태그가 든 스토리만 카드에 오른다는 뜻으로 고친다. ADR 0025 2026-10-28 이력이 함께 든 머리 문장은 지금 옛 이름을 들지 않고 올리는 길을 `/sync-design-system`의 올리기로 적는다. 그 문장이 짓기 명령으로 바뀐 뒤에도 맞는지 보고, 근거 괄호에 그 이력을 더할지 정해 결과에 적는다
- [ ] `docs/agents/issue-tracker.md` 화면 디자인 절에서 빌드가 필요한지, 빌린 빌드의 세부를 드는 `NOTES.md`, 동기화가 바꾼 `.design-sync/`를 지금 절차로 고친다
- [ ] `README.md`의 `.design-sync/` 줄, 헌법 `docs/constitution/tech.md`의 웹 행, `kickoff/prompting.md`를 고친다. 헌법의 문구를 고치므로 `docs/constitution/README.md`의 판을 patch로 올린다. 판은 `tools/sibling_overlap.py`가 내는 "형제가 쓴 가장 높은 헌법 판"보다 높게 고른다. `sdk/`와 `openapi.json`은 바뀌지 않는다
- [ ] 디자인 시스템 패키지와 올리기 도구 안에서 옛 절차를 드는 주석을 고친다(검토가 찾은 것은 `check.ts`·`check.test.ts`의 "번들 변환기"와 `record.ts`의 `ds-bundle/`이다)
- [ ] `.gitignore`의 디자인 시스템 패키지 빌드 주석에서 "(/design-sync 만 쓴다)"를 패키지 빌드를 무엇이 쓰는지로 고치고 `dist/`·`storybook-static/` 줄은 남긴다. `/design-sync` 산출물 주석 아래의 무시 줄 다섯(`/.ds-sync/`, `/ds-bundle/`, `/.design-sync/sb-reference/`, `/.design-sync/learnings/`, `/.design-sync/.cache/`)은 남기고, 주석만 옛 `/design-sync`가 쓰던 자리이고 버릇대로 쳐도 그 다섯 자리의 산출은 커밋되지 않게 남긴다는 뜻으로 고친다. 지금 주석은 "아래 셋만 무시하고"라고 쓰지만 줄은 다섯이니 함께 바로잡는다. 번들 `/design-sync`를 다시 치면 `.design-sync/`에 설정 파일(config, NOTES)을 새로 만드는지는 재지 않았다(명세 검토의 확인하지 못한 것). 만든다면 그 파일은 다섯 줄에 덮이지 않으니, 주석은 다섯 자리만 말하고 이 사실을 결과에 적는다
- [ ] `tidy-checkouts`가 부르는 정리 도구의 다시 만들 수 있는 자리 가운데 빌린 빌드의 넷(`.ds-sync/`, `ds-bundle/`, `.design-sync/sb-reference/`, `.design-sync/.cache/`)은 남기고, 그 자리를 설명하는 글만 옛 `/design-sync`의 자리로 고친다. 판정은 바꾸지 않으므로 그 자리를 이름으로 드는 시험(ADR 0025 2026-10-28 이력이 든 `tests/tools/test_tidy_checkouts.py`)도 남는다
- [ ] 옛 이름(`/design-sync`, `.design-sync/`, `빌린 빌드`, `ds-bundle`, `.ds-sync`, `번들 변환기`)으로 저장소를 grep해 살아 있는 문서의 잔존이 0인지 본다(`CLAUDE.md` 작업 규약 4). 기록(일지, 대기열, ADR의 지난 이력, 지난 명세와 티켓)과, 위 `.gitignore`와 정리 도구가 옛 자리라고 밝히며 남기는 글은 세지 않는다. 남긴 것마다 까닭을 이 티켓의 결과에 적는다. 셀프 리뷰가 미리 찾은 것은 둘이다. `CONTEXT.md`의 "피할 말" 괄호가 Claude Design용 `/design-sync`를 들고(번들 스킬 자체를 가리키는 말이라 남길 수 있다. 고치면 `CONTEXT.md`를 쓰는 domain-modeling 스킬로 고친다), 위 정리 도구의 시험이 남는 자리를 든다

### 검증

- [ ] 바꾼 스킬(`sync-design-system`)과 규칙(`web-design.md`)은 새 세션에서 불러 새 글이 실리는지 본다(`CLAUDE.md` 작업 규약 3, `docs/constitution/operations.md` 환경 규약 상세)
- [ ] 검증 명령이 모두 초록이다. 모델 경로, 위젯, 관리 화면을 건드리지 않아 `-m llm`·`-m llm_widget`·e2e·사진 비교는 칠 일이 없다
