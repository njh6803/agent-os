# 2026-11-04 (03) 계약: 에이전트 매니페스트의 skills 칸

## 시작

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가
> 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자:
> .scratch/skill-plugin/issues/01-contract-agent-manifest-skills-field.md
> / 다음 작업: .scratch/skill-plugin/issues/01-contract-agent-manifest-skills-field.md. 에이전트 매니페스트에 `skills` 칸을 더하는
> 계약 티켓 / 다음 단계: 구현 / 어디서: 새 세션. 나란히 여는 2 중 1. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고
> (그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은
> 01-contract-agent-manifest-skills-field)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 시작 프롬프트: /implement
> .scratch/skill-plugin/issues/01-contract-agent-manifest-skills-field.md / 브랜치: feature/01-contract-agent-manifest-skills-field /
> 모델: Sonnet 5.5 / high / 읽을 것: .scratch/skill-plugin/issues/02-read-skill-document-into-sdk-value.md(나란히 도는 티켓.
> `.claude/rules/sdk.md`와 `tests/test_server.py`를 줄이 다르게 함께 고치므로 뒤에 병합되는 쪽이 앞의 것을 합친다),
> docs/journal/2026-11-04-02-skill-plugin-tickets.md의 "## 다음" / 이어받을 상태: 없음 / 확인할 선행 조건: 주 체크아웃 미갱신:
> 루트는 main. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다 /
> 이번 요청 범위: PR과 병합까지

이 세션의 제목은 `feature/01-contract-agent-manifest-skills-field`이다.

## 체크아웃 정리

`tidy-checkouts`를 돌았다. 루트는 이미 `origin/main`(`c81f7973`)과 같아 당길 것이 없었다. 지운 것은 `docs/agent-os-direction`, `docs/skill-plugin-tickets`의 워크트리와 브랜치, 그리고 로컬 브랜치 `worktree-skill-plugin-tickets`다. `05-default-model-required-and-checked`는 `remove`가 종료 1로 멈췄다(이름 바꾸기 WinError 5, `agent-os.exe`와 `python.exe` 둘이 모듈을 올렸다). `03`·`06`은 바뀐 파일이 있고 `02`는 실행 중인 세션의 것이며, `admin-style-spec`·`admin-style-to-spec`·`mcp-shutdown-spec`·`web-widget-spec`은 병합된 PR이 없고, `confident-wright-2d3ebf`·`elegant-dijkstra-aaddb9`는 앱 표지가 있어 남겼다.

## 한 것

티켓을 `in-progress`로 바꾸고 실패하는 시험을 먼저 썼다. `tests/sdk/test_manifest.py`의 `skills` 시험이 첫 빨강이었고(지금 `--collect-only -k skills`로 세면 함수 8개, 매개변수 사례까지 10개다. 사례마다 빨강의 까닭이 같았는지는 첫 실행의 출력을 남기지 않아 모른다), `pnpm -C web typecheck`는 티켓이 말한 대로 리터럴 13곳에서 `skills` 누락으로 빨갰다.

- `src/agent_os/sdk/manifest.py`: `skills: tuple[Annotated[PluginName, Field(pattern=PLUGIN_NAME_PATTERN)], ...] = ()`. 원소마다 패턴을 거는 타입이라 `UPPER`, 한 글자, `../../evil`이 `string_pattern_mismatch`로 거부된다. 중복 거부는 `model_validator`가 패턴 검증 뒤에 돈다(어긴 이름을 두 번 적어도 중복 문구는 나지 않고 패턴 거부만 난다). 에이전트가 아닌 종류가 적으면 `<종류> 플러그인은 skills 를 갖지 않는다`로 거부한다. `PluginKind` 위 주석의 "디렉터리와 값만 예약한다"를 "skill은 공통 넷만 가지고 종류별 칸이 없다. 에이전트가 `skills`로 이름을 골라 쓴다"로 고쳤다.
- `openapi.json`을 `tools/export_openapi.py`로 다시 뽑고(`skills`가 `required`이고 `items.pattern`이 실렸다), `pnpm -C web generate:api-client`로 생성 타입을 다시 만들었다. 직렬화 스키마의 `skills`는 `anyOf` 없이 배열이라 `null`을 허락하지 않는다.
- 관리 화면의 리터럴 여섯 파일 13곳에 `skills: []`를 `model: null,` 바로 뒤에 더하고(서버 직렬화 순서), `PluginPage.test.tsx`의 JSON 문자열 픽스처에도 `"skills": []`를 같은 자리에 더했다.
- 시험: `tests/adapters/test_filesystem.py`에 실제 폴더로 `skills`의 순서와 표지 행(문구에 어긴 값이 없다)과 단건 `PluginError`를 보는 시험 하나, `tests/test_server.py`에 `GET /plugins`와 단건이 `skills`를 싣는 시험과 표지 행·500 시험을 더했다.
- `.claude/rules/sdk.md`의 종류별 칸 불릿에 `agent`의 선택 칸 `skills`를 더했다. 런타임이 읽는다는 말은 쓰지 않았다(03의 몫). 고치기 전에 `writing-for-agents`를 불렀다. 옛 표현 "디렉터리와 값만 예약" 잔존을 grep했고 살아 있는 문서에는 없다(남은 곳은 일지와 ADR과 옛 명세, 이 티켓이다).

디자인 시스템 확인(`sync-design-system 확인`)은 화면 코드를 처음 고쳤을 때 돌았고 결과가 `clean`(웹 편집 없음)이어서 `continue`였다.

## 검증 결과

- `uv run ruff check . && uv run ruff format --check .`: 통과.
- `uv run python tools/run_checks.py`: 전부 통과(`pytest` 461.7초, `web-verify` 560.4초).
- `pnpm -C web visual:admin`: 첫 판은 빨강이었다. `organisms-plugindetail--enabled`와 `--disabled`의 1280·320 시험 넷이 실패했다(예: 320 폭 `disabled`는 기대 776px, 실제 796px). `visual:admin:update`로 정답을 다시 만들었고 바뀐 사진은 정확히 티켓이 어림한 여덟 장이다(`organisms-plugindetail--{enabled,disabled}-{1280,320}-{light,dark}.png`). 1280 `enabled` 라이트를 눈으로 열어 `"skills": [],`가 `"model": null,` 다음 줄에 그려진 것을 봤다. 다른 사진은 바뀌지 않았고 다시 돌린 72개가 통과했다.
- `pnpm -C web/apps/admin exec playwright test`(관리 화면 e2e): 9개 통과.

근거의 종류. 위 검증 결과의 통과와 실패는 모두 이 세션이 그 명령을 쳐서 본 출력이다(`run_checks.py`는 백그라운드 출력 파일의 끝 줄 `exited with code 0`을 읽었고 단계별 초는 그 파일의 값이다). 사진의 "정확히 여덟 장"은 `git status --short`의 목록이고, 모양은 사진 한 장(1280 `enabled` 라이트)만 손으로 열어 봤다. 나머지 일곱 장은 열어 보지 않았다. `openapi.json`의 `skills`가 `anyOf` 없는 배열이라는 말은 `git diff openapi.json`을 읽은 것이다. `pre-commit`은 아직 돌지 않았다(커밋 전이다). 옛 표현 잔존 0은 `Grep`으로 살아 있는 문서(`README.md`, `CONTEXT.md`, `CLAUDE.md`, `src`)를 훑은 결과이고, 기록은 세지 않았다.

## 셀프 리뷰 (이어받은 세션)

`/code-review`를 base `c81f7973`로 돌렸다. 범위는 미커밋 변경 파일 14개(사진 여덟 장 제외)와 미추적 일지 하나, 커밋 0개다. 표준 축은 sonnet·high, 명세 축은 본 세션 모델로 돌렸다. 둘 다 서브에이전트 보고이고, 아래 "맞다"는 `parse_manifest`를 서브에이전트가 `uv run python`으로 불러 본 것(표준 축·명세 축 보고)과 이 세션이 `openapi.ts`와 `--collect-only`를 열어 본 것이다.

- Critical·Major: 없다. 수용 기준의 누락과 범위 넘침도 명세 축이 못 찾았다.
- 고친 것: ① `manifest.py` 주석의 "생성 클라이언트가 같은 규칙을 안다"는 거짓이었다. `openapi.ts`는 `skills: string[]`이라 패턴이 TS 타입에 실리지 않는다(이 세션이 Grep으로 봤다). "계약이 같은 규칙을 드러낸다"로 좁혔다. ② `sdk.md`와 `test_manifest.py` 독스트링의 "같은 값"을 `../../evil` 같은 값으로 바꾸고, `mcp` 칸의 빈틈을 이 기능이 고치지 않는다는 말(ADR 0041 이력 64행)을 `sdk.md`에 더했다. ③ `test_패턴을_어긴_이름을_두_번_적어도_패턴_거부만_나고_중복_문구는_나지_않는다`로 시험 이름을 단언에 맞췄다. ④ 위 "한 것"의 시험 개수를 `--collect-only` 값으로 고쳤다.
- 남긴 것과 이유: `Field(pattern=PLUGIN_NAME_PATTERN)`가 세 칸에 붙는 중복과 `_fields_belong_to_their_kind`의 종류별 줄 반복은 판단 항목(Minor)이고 이 티켓의 계약 범위 밖이라 두었다. `tests/test_server.py`의 표지 행 시험은 가짜 소스가 문구를 만들어 서버 쪽 배관만 보지만, 티켓이 서버 면의 표지 행·500 단언을 요구하고 실제 거부는 어댑터 시험이 덮는다. `.scratch/first-slice/spec.md:241`의 "디렉터리와 종류 값만 예약한다"는 닫힌 첫 슬라이스 명세, 곧 기록이라 고치지 않는다.

## 카나리아와 재검증

`uv run python tools/canary.py`로 `sdk_rule_failure_cause.toml`과 `sdk_rule_shortcut_patterns.toml`을 새 `claude -p`(2.1.318)로 돌렸다. 둘 다 통과 4, 실패 0, "없음" 섞임 0이다(도구 집계 줄을 읽었다). 갈래의 체크아웃 커밋은 `c81f7973`이고 `sdk.md`의 변경은 커밋 전이라 그 커밋에 없다. 도구가 못 보는 것으로 적은 "커밋하지 않은 변경" 몫이며, 실험군이 읽은 사본에 이 세션의 `sdk.md` 변경이 실렸는지는 이 출력으로 재지 못했다. 두 명세의 카나리아는 이 티켓이 더한 불릿과 다른 항목이라 이 실행은 규칙이 여전히 `paths`로 실린다는 것까지 보인다. 리뷰 반영 뒤 `ruff check`·`ruff format --check` 통과, 건드린 시험 파일 셋의 `-k "skills or manifest or plugin"` 109개 통과를 직접 쳤다.

## 남은 일 (이 세션이 인계한다)

- 셀프 리뷰(`/code-review`)를 아직 하지 않았다. 변경은 커밋하지 않은 워크트리에 있다. 인계 계기가 `셀프 리뷰 직전`에서 왔다.
- 리뷰 뒤 Critical·Major를 고치고 티켓 `Status`를 `done`으로 바꿔 커밋한 다음 PR과 병합까지 간다. PR 본문에 바뀐 사진 여덟 장을 적는다.
- `.claude/rules/sdk.md`를 고쳐서 카나리아 명세 `sdk_rule_failure_cause.toml`, `sdk_rule_shortcut_patterns.toml`을 새 `claude -p` 세션에서 불러 보고(`tools/canary.py`) 그 명세의 `# 최신 결과:` 줄을 고쳐야 한다(`tools/sibling_overlap.py`의 알림). 계정 한도로 돌리지 못하면 그 절의 계정 한도 항목대로 사전 확인만 돌린다.
- `uv run python tools/sibling_overlap.py`가 02 워크트리와 `.claude/rules/sdk.md`, `tests/adapters/test_filesystem.py`, `tests/test_server.py`를 함께 고친 파일로 알렸다. 줄이 다르므로 뒤에 병합되는 쪽이 합친다.

open-session을 부른다 2026-11-04T13:52:00Z
