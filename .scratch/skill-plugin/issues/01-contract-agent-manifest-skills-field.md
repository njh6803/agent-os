# 01: 계약 — 에이전트 매니페스트가 `skills`로 스킬을 고른다

**What to build:** 에이전트 개발자가 `plugin.toml`에 `skills = ["<스킬 이름>", …]`을 적으면 그 매니페스트가 읽히고, 관리 API의 목록(`GET /plugins`)과 상세가 그 칸을 적은 순서 그대로 싣는다. 적지 않으면 빈 목록이다. 플러그인 이름 패턴을 어긴 이름(대문자, 한 글자, `../../evil`), 같은 이름을 두 번 적은 것, 에이전트가 아닌 종류가 적은 `skills`는 읽는 단계에서 거부된다. 거부된 파일은 목록에서 그 행만 표지 행이고 상세는 500이다. 관리 화면은 새 칸을 아는 생성 타입으로 컴파일되고, 상세는 새 칸을 매니페스트 JSON 그대로 보인다.

이 기능의 계약 티켓이고 03을 막는다(04·05는 03을 거쳐 막힌다). 02와 나란히 돈다. 수용 기준의 고칠 자리로 대 본 겹침은 줄이 다른 두 파일이다. `.claude/rules/sdk.md`(이 티켓은 종류별 칸의 불릿, 02는 스킬 줄)와 `tests/test_server.py`(이 티켓은 표지 행 시험, 02는 가짜 소스의 `read_skill`)다. 구현하며 겹치는 파일이 더 나와도 같다. 어느 파일이든 뒤에 병합되는 쪽이 앞의 것을 합친다. 계약은 sdk의 칸, `openapi.json`, 생성 타입이다. 끌고 오는 것은 생성 타입을 단 관리 화면의 리터럴과 매니페스트 JSON을 그리는 상세의 사진 정답, `.claude/rules/sdk.md`의 불릿 하나다. **`Skill`, `parse_skill`, `read_skill`, `AgentContext.skills`는 여기 들지 않는다.** 모두 `openapi.json`에 실리지 않아 02가 맡는다. 리뷰의 질문은 "동작하나"가 아니라 이 칸 이름과 모양으로 오래 살 수 있느냐다.

**병합 뒤에 틈이 있다(to-tickets에서 사용자가 분할을 골랐다).** 런타임은 아직 `skills`를 보지 않는다. 그래서 받아들여지되 효과가 없고, 가리키는 스킬이 없어도 그 에이전트가 돈다. to-tickets 시점(main `f5c944b8`)에 저장소에 `skills`를 적은 에이전트는 없고 05까지 없다. 03이 이 틈을 닫는다. 이 티켓이 쓰는 문장(독스트링, 주석, rules)은 틈 동안에도 참이어야 한다. 런타임이 무엇을 하는지가 아니라 계약이 무엇을 약속하는지를 말한다(model-plugin 01과 같은 규칙).

근거는 `.scratch/skill-plugin/spec.md`의 "스킬 폴더와 매니페스트"와 그 2026-11-04 명세 검토 주석, "매니페스트 `skills`의 중복", "고칠 자리의 묶음"의 A와 그 주석, Testing Decisions의 "sdk 매니페스트"·"HTTP 두 면"·"관리 화면"이다. 앞선 결정은 ADR 0041과 그 2026-11-04 이력, ADR 0008의 2026-11-03 이력(`schema_version` "1" 유지), ADR 0010의 2026-09-23 이력(늘 실리는 칸을 required로 내보낸다)이다.

**Blocked by:** None (can start immediately)

**Status:** done

### sdk — `skills` 칸

- [ ] **칸은 원소마다 플러그인 이름 패턴을 드는 목록이고 선택이며 기본은 빈 목록이다.** 적은 순서를 지킨다. **`mcp` 칸의 타입을 그대로 쓰면 안 된다.** `PluginName`은 패턴을 들지 않는 `NewType`이라 `mcp` 칸은 `../../evil`을 받는다(명세 검토 세션이 `parse_manifest`를 불러 손으로 봤다). 원소에 패턴을 든 타입이어야 거부되고 `openapi.json`의 `items`에 `pattern`이 실린다. 어댑터의 `_ValidName`과 같은 꼴이다. `mcp` 칸의 빈틈은 이 티켓이 고치지 않는다
- [ ] **이름 패턴을 어긴 원소를 거부 사례로 단언한다.** `UPPER`, 한 글자, `../../evil`이고 표지는 `string_pattern_mismatch`다. 문자열이 아닌 원소도 거부한다. 실패를 기대하는 시험은 pydantic 오류의 `type`이나 검증자의 문구로 까닭을 단언한다(`CODING_STANDARDS.md`). 받는 사례(칸을 생략, 적은 순서가 그대로)도 같은 자리에서 본다. 선례는 `tests/sdk/test_manifest.py`의 `test_에이전트는_model을_안_적으면_없음이다`, `test_에이전트의_model이_이름_패턴을_어기면_읽는_단계에서_거부한다`다
- [ ] **같은 이름이 두 번 있으면 읽는 단계에서 거부하고 문구는 `agent 플러그인의 skills 에 같은 이름이 두 번 있다: <이름>`이다.** 문구에 드는 이름은 패턴을 지난 값이라 그대로 실어도 된다. 이 검증이 패턴 검증 뒤에 도는지 사례(패턴을 어긴 이름을 두 번 적은 것)로 본다. 어긴 값이 이 문구에 실리면 안 된다
- [ ] **에이전트가 아닌 종류(`mcp`, `skill`, `model`)가 `skills`를 적으면 `requires_approval`처럼 거부한다.** 선례는 `test_에이전트가_아니면_model을_갖지_못한다`다
- [ ] **`schema_version`은 "1" 그대로다.** 가리키는 스킬 플러그인이 실재하는지는 여기서 보지 않는다. 매니페스트만으로는 알 수 없어 03의 실행 준비가 본다
- [ ] **계약에 실리는 모델의 독스트링은 한 줄이고 논증은 `#` 주석에 둔다**(`.claude/rules/sdk.md`, `.claude/rules/http.md`의 "계약에 박히는 것 둘")
- [ ] **`src/agent_os/sdk/manifest.py`의 `PluginKind` 위 주석 "skill은 첫 슬라이스에서 디렉터리와 값만 예약한다"를 지금 사실로 고친다**(ADR 0041 "구현 티켓이 고칠 곳")

### 계약 파일과 생성 타입

- [ ] **`openapi.json`을 `uv run python tools/export_openapi.py`로 다시 뽑는다.** `PluginManifest`에 `skills`가 들고 직렬화 스키마에서 `required`이며 `null`을 허락하지 않고 `items`에 `pattern`이 있다. 선례는 `test_직렬화_스키마에서_새_다섯_칸은_모두_required이고_null을_허락한다`다. 최신성 시험이 파일을 판정한다
- [ ] **생성 타입을 다시 만든다.** `skills`가 필수로 들어 옛 리터럴이 타입 검사에서 깨지는 것이 첫 빨강이다(스토리 21)
- [ ] **관리 화면의 매니페스트 리터럴에 `skills: []`를 적는다.** to-tickets 시점에 `conversation_limit: null`을 적은 파일은 여섯, 13곳이다(`organisms/PluginDetail.stories.tsx` 2, `organisms/PluginList.stories.tsx` 1, `organisms/RunDetail.stories.tsx` 2, `pages/RunPage.decision.test.tsx` 3, `pages/HomePage.test.tsx` 4, `pages/PluginPage.test.tsx` 1, 모두 `web/apps/admin/components/` 아래). 매니페스트를 펼친 문자열 픽스처가 있으면 타입 검사가 아니라 vitest에서 빨개지니 함께 본다
- [ ] **플러그인 상세의 사진 정답이 바뀌면 다시 만든다.** 상세가 매니페스트 JSON을 그려 리터럴에 칸이 들면 `web/apps/admin/visual/snapshots/organisms-plugindetail--{enabled,disabled}-{1280,320}-{light,dark}.png` 여덟 장이 바뀔 것이다(코드를 읽은 어림, 돌리지 않았다). `pnpm -C web visual:admin`으로 빨강을 보고 `pnpm -C web visual:admin:update`로 정답을 컨테이너 안에서 다시 만든 뒤 바뀐 사진을 PR 본문에 적는다(`.claude/rules/web-design.md`). 다른 사진이 바뀌면 그것도 적는다
- [ ] **관리 API의 경로는 늘지 않는다.** 스킬의 설명과 본문은 관리 API에 나오지 않는다. 스킬 행의 안내 줄("로더가 생기기 전에는 효과가 없다")은 이 티켓에서 걷지 않는다. 걷는 것은 켜고 끄기가 실제로 듣게 된 뒤인 04다

### 관리 API

- [ ] **`GET /plugins`의 에이전트 행이 `skills`를 함께 낸다.** 적지 않은 에이전트는 빈 목록이다
- [ ] **이름 패턴을 어긴 `skills`를 적은 에이전트 파일은 그 행만 표지 행(`reason`에 거부 까닭)이고 단건 상세는 500이다.** 목록 전체가 500이 되지 않는다. 선례는 `tests/test_server.py`의 `_admin_app`과 `test_읽을_수_없는_매니페스트는_목록에서는_표지이고_단건으로는_500이다`다

### 문서

- [ ] **`.claude/rules/sdk.md`의 종류별 칸 불릿(12행)에 `agent`의 선택 칸 `skills`를 더한다.** 원소마다 패턴을 보고, 같은 이름은 거부하며, 다른 종류가 적으면 거부한다는 것까지다. 틈 동안에도 참인 문장이어야 하므로 런타임이 읽는다는 말은 03이 쓴다. 고치기 전에 Skill 도구로 `writing-for-agents`를 부른다(`.claude/rules/agent-docs.md`)
- [ ] **옛 표현을 저장소 전체에서 grep해 살아 있는 문서에 잔존이 0인지 본다**(`CLAUDE.md` 작업 규약 4). "디렉터리와 값만 예약한다", 스킬 종류에 칸이 없다고 읽히는 문장이다. 기록(일지, 대기열, ADR 이력)은 고치지 않는다

### 검증

- [ ] **빨강을 먼저 본다**(헌법 원칙 II). 첫 빨강은 sdk의 받기·거부 시험, 리터럴이 타입 검사에서 깨지는 것, `openapi.json` 최신성 시험이다
- [ ] **검증 명령이 모두 초록이다.** 손으로 치는 다섯에 더해 관리 화면 e2e(`pnpm -C web/apps/admin exec playwright test`. api-client가 바뀐다)와 사진 비교 `pnpm -C web visual:admin`을 친다. 위젯과 `-m llm`은 이 티켓이 닿지 않는다
