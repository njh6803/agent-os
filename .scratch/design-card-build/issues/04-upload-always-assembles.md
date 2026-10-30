# 04: 올리기가 늘 짓기 명령으로 보내고, `.design-sync/`와 `/design-sync`를 드는 글이 사라진다

**What to build:** `/sync-design-system 올리기`가 더는 사람에게 `/design-sync`를 쳐 달라고 부탁하지 않는다. 확인과 결정, 커밋 맞대기 뒤 늘 `assemble`을 돌려 산출 전체를 맞추고, 03의 계획 보고(첫 정식 올리기, 몫, `libraries`·`upgraded`)대로 보낸다. 거꾸로 동기화 뒤의 올리기가 사람 손 없이 한 세션에서 끝난다. 올리기가 계속 읽는 원본 셋(README 원본, 기초 카드 원본, 지난 산출 목록)은 올리기 도구 폴더(`web/tools/sync-design-system/`) 아래로 옮기고 `.design-sync/`는 지운다. 옛 절차를 가리키던 규칙·문서·주석·`.gitignore`·정리 도구의 글을 같은 PR에서 고쳐, 살아 있는 문서에 두 절차가 함께 남지 않는다.

이 티켓이 병합되면 다음 올리기가 첫 정식 올리기가 된다. 05가 그 올리기를 하려 하지만, 화면 작업이 그리기 전마다 올리기를 부르므로(`upload.md`의 "보낼 것이 없을 때") 다른 세션의 올리기가 먼저 할 수도 있다. 그래서 첫 정식 올리기를 보낸 뒤의 확인은 05가 아니라 절차에 둔다(아래 "올리기 전환"의 "보낸 뒤" 줄). 이 티켓은 아티팩트에 보내지 않는다.

전환과 지우기를 한 티켓에 둔 것은 결정을 바꾸는 변경이 그 결정을 가리키는 글을 함께 고치는 `CLAUDE.md` 작업 규약 4 때문이다(명세 "티켓의 차례"의 주석, 사용자가 고른 것).

근거는 `.scratch/design-card-build/spec.md`의 "올리기"("늘 짓는다", "`via`", "지난 산출 목록", "옛 별칭 지우기"의 `_ds_sync.json` 줄, "보낸 뒤"), "디자인 시스템 README와 나머지 파일"("README 원본", "옮기며 고칠 글", "옮기기 절", "기초 카드와 지침"), "`.design-sync/`와 함께 고치는 것"(표, "`.gitignore`", "정리 도구", "그 밖의 자리"), "티켓의 차례", 스토리 28과 그 자리들의 2026-10-29 명세 검토 주석이다. 결정은 ADR 0025 2026-10-28 이력의 "함께 고치는 것"과 "옮겨 가는 동안"이다.

**Blocked by:** 02, 03

**Status:** done

### 시작 전

- [x] 스킬과 규칙을 고치므로 Skill 도구로 `writing-for-agents`를 부른다(`.claude/rules/agent-docs.md`)

### 올리기 전환

- [x] 빌드 판정(`needsBuild`, `record needs-build`)과 그 시험을 걷어 낸다
- [x] 올리기 절차(`.claude/skills/sync-design-system/`의 `SKILL.md`, `upload.md`)가 커밋 맞대기(기준 커밋과 조상 확인) 뒤 늘 `assemble`을 돌린다. 앞 시도의 산출 폴더는 지우고 친다. 짓기가 실패하면 보내지 않고 `upload.md` 1의 "돌아가기"대로 돌아간 뒤 멈춘다. "돌아가기"가 드는 멈춤 가운데 "4의 산출 스크립트로 멈출 때"는 "짓기가 실패할 때"로 바꾼다. 분리 HEAD에 남은 채 멈추면 화면 작업이 돌아갈 브랜치를 잃는다(그 절의 마지막 문장). "빌드가 필요한지", "빌드가 필요 없다"·"빌드가 필요하다"의 갈래, 사람에게 `/design-sync`를 부탁하는 문구, "사람이 친 턴" 절을 걷어 낸다. 그 갈래를 가리키는 다른 절의 문장도 고친다. 예를 들어 "보낼 것이 없을 때"의 "3의 "빌드가 필요한지"가 필요 없다고 내어 이 갱신에 닿지 않는다"는 늘 지으면 거짓이 된다. 같은 HEAD에서 다시 들어도 짓고 계획해 그 갱신에 닿는다
- [x] 계획에는 늘 지난 산출 목록(옮긴 자리)을 준다. 호출 몫은 03의 계획 보고대로 나누고, 손으로 나누던 문장과 `_ds_sync.json`을 마지막 호출에 싣는 규칙을 걷어 낸다
- [x] 색인의 `lastChange.via`는 늘 `agent-os main@<짧은 SHA>`다. 부분 올리기의 꼴(`agent-os 부분 main@…`)은 기준 커밋을 읽을 때만 옛 기록을 위해 안다. `libraries`와 `upgraded`는 03이 지은 값을 쓴다
- [x] "README의 옮기기 절"의 물음 설명에 셋을 적는다. 그 절이 이번 올리기가 지우는 파일을 가리킨다는 것, 캔버스의 복사 목록은 새 README 본문이 든다는 것, 절을 두는 길은 받은 옛 README를 그대로 두어 새 본문을 버리므로 README가 이번 올리기가 지우는 `.prompt.md`를 계속 가리키고 다음 올리기마다 같은 물음이 나온다는 것이다
- [x] "보낸 뒤"의 확인이 `clean`이고 보낸 파일에 `components/` 아래 경로나 `_ds_bundle.*`가 들었으면, 올린 세션이 앱 안 브라우저로 Components 절을 한 번 열어 카드가 모두 그려지고 칸 아래가 잘리지 않았는지 본다. 깨진 카드를 보면 되돌리지 않고 사람에게 알리며, 고칠 일을 `docs/agents/issue-tracker.md`의 규약대로 티켓으로 쓴다. 계획이 첫 정식 올리기로 본 올리기였으면, 보낸 뒤 파일 목록(`list`의 `scope: "files"`)에 옛 별칭(`components/<무리>/<이름>/…`, `_preview/`, `_vendor/`, `_ds_sync.json`)이 남지 않았는지도 보고, 남았으면 같은 길로 사람에게 알리고 티켓으로 쓴다. 05 전에 다른 세션의 올리기가 첫 정식 올리기를 해도 이 확인은 그 올리기에서 돈다
- [x] 다 보낸 뒤 지난 산출 목록을 그 올리기에서 `--paths`가 쓴 목록으로 바꿔 커밋한다는 문장이 옮긴 자리를 가리킨다
- [x] 스토리 28의 주석대로, 옛 `/design-sync`가 다시 올린 파일 가운데 확인이 찾는 것은 기록에 든 마크다운(README와 `guidelines/`의 둘)뿐이고 나머지는 찾지 못한다는 것을 절차의 못 보는 것에 적는다

### 옮기기

- [x] `.design-sync/conventions.md`를 올리기 도구 폴더 아래로 옮긴다. 이름은 이 티켓이 정한다. `.design-sync/foundations/` 아래 넷과 `.design-sync/upload-output.json`도 옮긴다. 옮긴 파일의 바이트는 그대로다(README 원본은 아래 고칠 글 셋만 바뀐다)
- [x] 짓기 명령이 README 원본과 기초 카드 원본을 옮긴 자리에서 읽는다
- [x] 옮긴 README 원본과 기초 카드 원본을 `web/.prettierignore`에 까닭(올라가는 바이트 그대로 둔다)과 함께 더한다. 지난 산출 목록은 지금 꼴(들여쓰기 두 칸, 한 줄 한 경로, 끝 줄바꿈)로 Prettier를 지나는지 `pnpm -C web verify`로 본다
- [x] README 원본의 글 셋을 고친다. 목업 설치가 복사할 파일 넷(`styles.css`, `fonts/fonts.css`, `_ds_bundle.css`, `_ds_bundle.js`)을 본문이 이름으로 든다. "어디를 읽나"의 `components/<group>/<Name>/<Name>.prompt.md`를 `components/<이름>/README.md`(쓰임)와 Components 절의 카드로 바꾼다. `.d.ts`를 드는 글은 뺀다. 고친 뒤에도 02의 파일 검사가 초록이다
- [x] `.design-sync/NOTES.md`의 내용을 명세의 표대로 옮긴다. 지난 산출 목록의 뜻과 "빌드가 짓지 않는 파일"은 그 목록을 읽는 계획 함수의 독스트링으로, "기초 카드" 절의 규칙과 카드 이름이 `index`로 보이는 열린 문제는 옮긴 기초 카드 원본 곁의 글로, "사용 규약" 절의 요지는 파일 검사의 독스트링으로, Re-sync risks의 README 옮기기 절 항목은 사실만 `upload.md`의 "README의 옮기기 절"로 옮긴다. 나머지(돌리는 법, driver, 카드 스토리, 고친 것, 포크, 채점, Alert 항목, 계정 항목)는 옮기지 않는다
- [x] `.design-sync/`의 추적 파일 14개가 모두 옮겨지거나 지워지고 폴더가 없다

### 함께 고치는 글

- [x] `.claude/rules/web-design.md`에서 변형 스토리를 `.design-sync/config.json`의 skip에 넣으라는 줄을 showcase 태그가 든 스토리만 카드에 오른다는 뜻으로 고친다. ADR 0025 2026-10-28 이력이 함께 든 머리 문장은 지금 옛 이름을 들지 않고 올리는 길을 `/sync-design-system`의 올리기로 적는다. 그 문장이 짓기 명령으로 바뀐 뒤에도 맞는지 보고, 근거 괄호에 그 이력을 더할지 정해 결과에 적는다
- [x] `docs/agents/issue-tracker.md` 화면 디자인 절에서 빌드가 필요한지, 빌린 빌드의 세부를 드는 `NOTES.md`, 동기화가 바꾼 `.design-sync/`를 지금 절차로 고친다
- [x] `README.md`의 `.design-sync/` 줄, 헌법 `docs/constitution/tech.md`의 웹 행, `kickoff/prompting.md`를 고친다. 헌법의 문구를 고치므로 `docs/constitution/README.md`의 판을 patch로 올린다. 판은 `tools/sibling_overlap.py`가 내는 "형제가 쓴 가장 높은 헌법 판"보다 높게 고른다. `sdk/`와 `openapi.json`은 바뀌지 않는다
- [x] 디자인 시스템 패키지와 올리기 도구 안에서 옛 절차를 드는 주석을 고친다(검토가 찾은 것은 `check.ts`·`check.test.ts`의 "번들 변환기"와 `record.ts`의 `ds-bundle/`이다)
- [x] `.gitignore`의 디자인 시스템 패키지 빌드 주석에서 "(/design-sync 만 쓴다)"를 패키지 빌드를 무엇이 쓰는지로 고치고 `dist/`·`storybook-static/` 줄은 남긴다. `/design-sync` 산출물 주석 아래의 무시 줄 다섯(`/.ds-sync/`, `/ds-bundle/`, `/.design-sync/sb-reference/`, `/.design-sync/learnings/`, `/.design-sync/.cache/`)은 남기고, 주석만 옛 `/design-sync`가 쓰던 자리이고 버릇대로 쳐도 그 다섯 자리의 산출은 커밋되지 않게 남긴다는 뜻으로 고친다. 지금 주석은 "아래 셋만 무시하고"라고 쓰지만 줄은 다섯이니 함께 바로잡는다. 번들 `/design-sync`를 다시 치면 `.design-sync/`에 설정 파일(config, NOTES)을 새로 만드는지는 재지 않았다(명세 검토의 확인하지 못한 것). 만든다면 그 파일은 다섯 줄에 덮이지 않으니, 주석은 다섯 자리만 말하고 이 사실을 결과에 적는다
- [x] `tidy-checkouts`가 부르는 정리 도구의 다시 만들 수 있는 자리 가운데 빌린 빌드의 넷(`.ds-sync/`, `ds-bundle/`, `.design-sync/sb-reference/`, `.design-sync/.cache/`)은 남기고, 그 자리를 설명하는 글만 옛 `/design-sync`의 자리로 고친다. 판정은 바꾸지 않으므로 그 자리를 이름으로 드는 시험(ADR 0025 2026-10-28 이력이 고칠 자리로 든 `tests/tools/test_tidy_checkouts.py`)도 남는다
- [x] 옛 이름(`/design-sync`, `.design-sync/`, `빌린 빌드`, `ds-bundle`, `.ds-sync`, `번들 변환기`)으로 저장소를 grep해 살아 있는 문서의 잔존이 0인지 본다(`CLAUDE.md` 작업 규약 4). 기록(일지, 대기열, ADR의 지난 이력, 끝난 기능의 명세·티켓·프로브)과, 위 `.gitignore`와 정리 도구가 옛 자리라고 밝히며 남기는 글은 세지 않는다. 남긴 것마다 까닭을 이 티켓의 결과에 적는다. 셀프 리뷰가 미리 찾은 것은 둘이다. `CONTEXT.md`의 "피할 말" 괄호가 Claude Design용 `/design-sync`를 들고(번들 스킬 자체를 가리키는 말이라 남길 수 있다. 고치면 `CONTEXT.md`를 쓰는 domain-modeling 스킬로 고친다), 위 정리 도구의 시험이 남는 자리를 든다
- [x] 끝난 기능의 변이 표 둘은 위 grep에서 세지 않는 기록이지만, 이 티켓의 커밋이 그 표가 겨누는 파일을 바꾸므로 pre-commit의 변이 표 원문 검사(`tools/mutate.py --staged`)가 "부모 판에서 맞던 원문을 이 커밋이 깼다"로 막는다(그 독스트링과 `staged`를 읽었다. 돌려 보지는 않았다). `.scratch/design-reverse-sync/probes/record_check_mutations.toml`은 `upload.ts`의 `needsBuild` 본문을 겨누는 변이를 들고(설정 폴더를 빌드로 보는 변이 등), `.scratch/design-refresh/probes/checker_mutations.toml`은 `check-conventions.mjs`를 돌리며 `.design-sync/` 아래 파일을 바꾼다. 걷어 내거나 지운 코드를 겨누는 변이는 표에서 빼고(표 전체가 그렇다면 표를 지운다), 옮긴 코드를 겨누는 변이는 원문을 옮긴 자리로 고친다. 뺀 것과 그 까닭은 그 프로브 README의 줄에 적는다. 끝난 기능의 표를 지금 코드에 맞춘 선례는 일지 2026-10-28-04의 "변이 표 원문 검사" 줄이다

### 검증

- [x] 바꾼 스킬(`sync-design-system`)과 규칙(`web-design.md`)은 새 세션에서 불러 새 글이 실리는지 본다(`CLAUDE.md` 작업 규약 3, `docs/constitution/operations.md` 환경 규약 상세)
- [x] 회고 반영: `tools/check_commit_msg.py`가 제목을 git처럼 첫 문단으로 읽고, 줄이 여럿이면 제목 줄 뒤에 빈 줄이 없다고 잡는다(시험이 임시 저장소의 실제 git `%s`와 견준다. 앞의 `#` 줄을 늘 건너뛰어 `-F` 메시지를 git과 다르게 읽는 것은 못 보는 것으로 고정했다), 일지 2026-10-30-10-upload-always-assembles.md
- [x] 검증 명령이 모두 초록이다. 모델 경로, 위젯, 관리 화면을 건드리지 않아 `-m llm`·`-m llm_widget`·e2e·사진 비교는 칠 일이 없다

### 결과

1. **자리.** 이 티켓이 정한 이름이다. README 원본은 `web/tools/sync-design-system/artifact-source/README.md`, 기초 카드 원본 넷은 그 곁의 `artifact-source/foundations/`, 지난 산출 목록은 `web/tools/sync-design-system/previous-output.json`이다. 기초 카드 원본 곁의 글은 `artifact-source/foundations.md`로 두었다. `foundations/` 안에 두면 짓기 명령이 그 폴더를 통째로 산출에 옮겨 올라가기 때문이다(`assemble.ts`의 기초 카드 몫을 읽었다). 옮긴 바이트는 README 원본의 글 셋 말고는 그대로다(`git status`가 `R`로 보였다. README 원본만 `RM`).
2. **NOTES의 내용이 간 곳.** 지난 산출 목록의 뜻과 "빌드가 짓지 않는 파일"은 `upload.ts` 머리 독스트링으로(그 목록을 읽는 함수는 `planUpload`이고, 독스트링이 그 함수의 머리 몫이다), "기초 카드" 절의 규칙과 카드 이름이 `index`로 보인 열린 문제는 `artifact-source/foundations.md`로, "사용 규약" 절의 요지는 짓기 시험의 머리 주석으로(README 원본이 든 이름을 시험이 다시 맞대고, 문장 모양이 바뀌면 시험도 고친다), Re-sync risks의 README 옮기기 절 항목은 사실만 `upload.md`의 "README의 옮기기 절"로 옮겼다. 나머지는 옮기지 않았다.
3. **걷어 낸 코드.** `needsBuild`와 그 상수, `record needs-build`, 그 시험 셋(바뀐 경로 줄 목록, 따옴표 줄, `describe("빌드가 필요한지")`)을 지웠다. `record needs-build`가 모르는 하위 명령으로 거부되는 사례는 명령을 지우기 전에 시험에 넣어 빨강을 봤다. `splitCalls`의 `_ds_sync.json`을 마지막 몫에 싣는 규칙도 코드에서 걷었다. 늘 짓는 산출에는 그 파일이 없어 그 규칙이 닿을 일이 없고, 첫 정식 올리기에서는 그 파일이 지울 경로다. 그 시험도 지웠다. `record plan`의 `--previous-output`은 필수로 바꾸지 않았다. 절차가 늘 주고(`upload.md` 5), 필수로 바꾸면 `record-check.test.ts`가 `record plan`을 부르는 열일곱 자리(그 파일에 `previous-output`이 한 번도 없다. `grep -c`로 셌다)를 고쳐야 해 이 티켓의 범위를 넘는다. 목록 없는 계획의 뜻(산출이 전체가 아닐 수 있다)은 `upload.ts` 머리 독스트링에 남겼다.
4. **`.claude/rules/web-design.md` 머리 문장.** 짓기 명령 뒤에도 맞다. 같은 파일이 `guidelines/web-design.md`로 오르고(짓기 명령이 바이트 그대로 둔다, `assemble.ts`를 읽었다) 올리는 길은 `/sync-design-system`의 올리기다. 근거 괄호에 ADR 0025 2026-10-28 이력은 더하지 않았다. 그 문장은 오르는 자리와 길만 말하고, 2026-10-28 이력은 카드와 묶음을 저장소가 짓는다는 결정이라 그 문장의 근거가 아니다. 카드에 오르는 스토리의 줄은 showcase 태그로 고르는 지금 뜻으로 고쳤다.
5. **SKILL.md 설명.** "번들 `/design-sync`의 업로드와는 다른 스킬이다"를 걷었다. 절차가 그 스킬을 더 부르지 않고 사람에게 쳐 달라고도 하지 않아, 매 세션 실리는 설명에서 그 이름이 할 일이 없다. 스킬 이름 없이 말해도 이 스킬이 불리는지는 story4 카나리아로 다시 쟀다(아래 9).
6. **`.gitignore`.** 무시 줄 다섯은 남기고 주석만 옛 `/design-sync`가 쓰던 자리라고 고쳤다. 옛 주석의 "아래 셋만"도 함께 사라졌다. 번들 `/design-sync`를 다시 치면 `.design-sync/`에 설정 파일(config, NOTES)을 새로 만드는지는 재지 않았다. 만든다면 그 파일은 다섯 줄에 덮이지 않는다. 패키지 빌드 주석은 그 빌드를 패키지의 `build` 스크립트를 손으로 칠 때만 쓴다고 고쳤다(`web/package.json`과 CI 워크플로에서 그 스크립트를 부르는 자리가 없는 것을 grep으로 봤다).
7. **옛 이름의 잔존.** `git grep -I -E`로 옛 이름 여섯과 `needs-build`·`needsBuild`·`upload-output`·`_ds_sync`·`conventions.md`·`thumbnail.html`·`check-conventions`를 `.scratch`·`docs/journal`·`docs/adr` 밖에서 셌다. 이 grep이 찾아 더 고친 것은 `web/packages/ui/.storybook/main.ts`의 머리 주석이다. 셀프 리뷰가 찾아 더 고친 것은 `web/packages/ui/src/styles/theme.css` 12행과 `DesignTokens.stories.tsx` 428~429행의 주석이다. ADR 0025 2026-10-28 이력이 `web/packages/ui` 아래 `/design-sync`를 드는 주석을 고칠 자리로 들어, 첫 올리기의 CSS에 변수가 빠진 사실은 남기고 옛 절차의 이름만 걷었다. 남긴 것과 그 까닭은 이렇다.
   - `.gitignore`의 다섯 줄과 그 주석, `tools/tidy_checkouts.py`의 넷과 그 주석, `tests/tools/test_tidy_checkouts.py`의 그 자리: 이 티켓이 옛 자리라고 밝히며 남긴다.
   - `CONTEXT.md` 275행 "피할 말"의 괄호: Claude Code에 남은 번들 스킬 자체를 가리키는 말이라, "동기화"가 섞이는 상대로 드는 것이 지금도 맞다. 고치지 않았으므로 domain-modeling 스킬은 부르지 않았다.
   - `docs/constitution/README.md`의 옛 판 설명: 판 이력이다.
   - `tests/tools/test_mutate.py` 2386행: 이 티켓이 지운 변이 표가 `ds-bundle/`을 가리켰다는 기록이다.
   - `@ds-bundle`(`assemble.ts`, `assemble.test.ts`): 컴포넌트 묶음 형식의 머리 이름이라 옛 절차의 이름이 아니다.
   - `_ds_sync.json`(`upload.md`, `upload.test.ts`, `previous-output.json`): 첫 정식 올리기가 지울 옛 별칭 파일의 이름이다.
   - `record-check.test.ts`의 `["record", "needs-build"]`: 걷어 낸 하위 명령이 모르는 하위 명령으로 거부되는지 보는 사례다.
   - `kickoff/prompting.md`의 `thumbnail.html`: Claude Design이 목록 타일을 그리는 길을 본 관찰이라 옛 절차가 아니다.
   - 이 기능 자신의 것: 기능이 진행 중이라 명세와 티켓은 살아 있는 문서다(`docs/constitution/operations.md` 문서 위치). 명세의 옛 이름은 이 기능이 걷어 낼 대상과 그 까닭을 적은 결정이다. 끝난 티켓 01~03의 옛 이름은 그 티켓이 병합될 때의 절차를 적은 수용 기준과 결과이고, 병합된 티켓은 다시 열지 않는다(`docs/agents/issue-tracker.md` 규약). 프로브(`card_build.mjs`는 커밋 `35028cba`의 지난 산출 목록을 읽는다)는 그 커밋의 사실을 잰다. `.scratch/plan.md`의 design-card-build 행과 프론티어 문단은 날짜를 단 누적 서술이라 옛 문장을 고치지 않고, 04 병합의 한 문장을 PR 번호를 받은 뒤의 커밋에 더한다(02가 PR #434에서 그렇게 했다). 대기열은 기록이다. 남은 티켓 05에는 옛 이름이 없다.
8. **변이 표.** 이 커밋이 겨누는 파일을 바꾼 표 넷을 지금 코드에 맞췄다. 수와 문구는 `tools/mutate.py`가 찍은 줄이고, 실행은 모두 `fcf808fa` 위의 작업 트리다.
   - `.scratch/design-card-build/probes/assemble_mutations.toml`: 원본을 겨누는 열일곱의 `file`만 옮긴 자리로 바꿨다. `--check` "변이 64 모두 원문이 한 번씩 있다", 열일곱만 돌려 "변이 17 모두 기대대로"(기준선 일곱 초록).
   - `.scratch/design-card-build/probes/upload_plan_mutations.toml`: `_ds_sync.json`의 자리 변이(옛 14)를 뺐다. 원문이 바뀐 13과 사례 이름·좁히기가 바뀐 3·22를 돌려 "변이 3 모두 기대대로"(기준선 셋 초록), `--check` "변이 25 모두 원문이 한 번씩 있다".
   - `.scratch/design-reverse-sync/probes/record_check_mutations.toml`: 빌드 판정과 따옴표 줄을 겨누던 넷(옛 21·22·23·39)을 뺐고, 시험 이름이 바뀐 두 변이(지금 44·46)를 돌려 "변이 2 모두 기대대로", `--check` "변이 49 모두 원문이 한 번씩 있다".
   - `.scratch/design-refresh/probes/checker_mutations.toml`과 `checker_mutations.mjs`: 표 전체가 지운 `check-conventions.mjs`와 `.design-sync/` 아래 파일을 겨눠 표째 지웠다(지운 판은 `git show fcf808fa:<경로>`).
   - 뺀 것과 당겨진 번호는 각 프로브 README의 2026-10-30 절과 표의 줄에 적었다.
9. **검증.**
   - 새 세션 확인(작업 규약 3): 카나리아 여섯을 claude 2.1.312로 돌려 모두 통과했다. 새 명세 둘(`.scratch/design-card-build/probes/canary/`의 올리기 절차와 낱말), 이 스킬의 설명을 고쳐 사전 확인으로 갈음할 수 없는 기존 셋(design-reverse-sync의 `sync_design_system_skill`·`sync_design_system_web_edit_hook`·`sync_design_system_story4`), 고친 규칙의 `web_design_showcase`(design-refresh, 둘째 물음과 기대를 새 문장에 맞췄다)다. 회차마다의 결과는 각 명세 머리의 `# 최신 결과:` 줄이다. 낱말 명세의 첫 회(통과 3·실패 1)는 실험군 한 회차가 문장 끝을 바꿔 옮긴 것이라 기대에서 끝의 "다"를 빼고 다시 돌렸고(그 명세의 "결과를 본 뒤 바꾼 것"), story4의 첫 회(통과 3·실패 1)는 한 회차가 다른 줄을 옮긴 것이라 그대로 다시 돌렸다. 대조군은 모두 옛 문장이나 "없음"으로 답했다.
   - 웹 편집 확인: 화면 코드 폴더의 주석을 고치자 계기 훅이 알려 `/sync-design-system 확인`을 돌렸고 `clean`(결정 `continue`)이었다(판 `1793259788-d3cd`). 셀프 리뷰를 반영하며 `theme.css`·`DesignTokens.stories.tsx`를 고친 새 세션에서도 다시 돌려 같은 판에서 `clean`(결정 `continue`)이었다.
   - README 원본을 고친 뒤의 02 파일 검사: 셀프 리뷰 명세 축이 짓기·올리기·기록 시험 세 파일(110개)을 따로 돌려 초록이라고 냈다. 커밋의 pre-commit `web-verify`(Vitest)가 다시 돈다.
   - 검증 명령: 셀프 리뷰와 회고 반영 뒤의 작업 트리에서 `uv run ruff check .`와 `uv run ruff format --check .`가 지났다(명령 출력을 손으로 봤다). pyright·lint-imports·pytest와 나머지 검사(`web-verify` 포함)는 이 티켓을 싣는 커밋의 pre-commit이 돌았고, 그 결과는 일지 2026-10-30-10의 "커밋" 절이다. 사진 비교는 `packages/ui`에서 주석만 바꿔 로컬에서 치지 않고 CI의 visual 잡에 맡긴다.
10. **셀프 리뷰가 고친 절차.** `upload.md` 6의 6의 마지막 항목을 "목록 갱신과 돌아가기"로 다시 썼다. 지난 산출 목록은 커밋 검사의 면제 모양이 아니라 티켓을 가리키는 브랜치에만 실리므로, 돌아갈 브랜치가 티켓 모양이면 거기 싣고, 명세 브랜치(`docs/<slug>`)이거나 새로 든 워크트리면 돌아가기 전에 harness 티켓 하나의 `chore/<NNN>-<slug>` 브랜치를 딴다(옛 글은 새 워크트리에서 `chore/<이름>`을 따게 해 커밋 검사의 판정 7에 막혔다). 5의 "보낼 것이 없을 때"는 목록이 달라 갱신하는 때 6의 6의 카드와 옛 별칭 확인을 조건 없이 한다. 첫 정식 올리기가 마지막 호출 뒤 그 확인 전에 끊기면, 다시 든 올리기는 기록이 이미 정식 배치라 `firstCanonical`이 false여서 그 확인에 닿지 않았다. `docs/agents/issue-tracker.md` 화면 디자인 절의 같은 문장도 맞췄다.
