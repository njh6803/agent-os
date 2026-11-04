# 2026-11-04 (02) skill-plugin 티켓

## 시작

> 사용자: .claude/skills/to-tickets/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가
> 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/skill-plugin/spec.md
> / 다음 작업: 기능 skill-plugin. PR #459(agent-os-direction)가 병합됐다. 프론티어인 skill-plugin의 명세를 검토하고 티켓으로
> 쪼갠다 / 다음 단계: 티켓 / 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게
> 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은
> skill-plugin-tickets)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 시작 프롬프트: /to-tickets
> .scratch/skill-plugin/spec.md / 브랜치: docs/skill-plugin-tickets / 모델: Opus 5.5 / xhigh / 읽을 것:
> docs/journal/2026-11-04-01-agent-os-direction-design.md의 "## 다음"(프론티어와 이어받을 것),
> docs/journal/2026-11-03-03-skill-plugin-spec.md의 "## 다음"(구현 티켓이 이어받을 것 셋) / 이어받을 상태: /to-tickets 직전에
> spec-reviewer 서브에이전트로 .scratch/skill-plugin/spec.md를 먼저 검토한다(체크리스트 일곱과 질문 둘. 아직 검토하지 않았다).
> 병합 PR에서 원격 브랜치 남음: docs/agent-os-direction (git push origin --delete가 첫 시도는 GitHub 500으로 실패했고 둘째는
> 자동 모드 분류기가 거부했다). 이 PR이 정한 ADR 0042·0043과 plan.md 슬라이스 7~11의 행 열일곱은 skill-plugin 뒤에 차례로 가고
> 각 행은 설계 인터뷰부터다. ADR 0043의 전환(dev 브랜치)은 harness 티켓이고 언제 여는지는 사용자가 정한다 / 확인할 선행 조건: 주
> 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를
> Read로 열어 따른다. 실행 중 세션과는 견주지 않았다(결정표의 이 줄은 대기열 행을 고르지 않는다) / 이번 요청 범위: 티켓까지

## 분할 (사용자가 골랐다)

명세의 묶음 A(계약과 읽기)가 커서 둘로 나눈 다섯 장을 추천했다. 01 매니페스트가 스킬을 고른다(계약), 02 스킬 문서를 읽는다, 03 실행 준비가 스킬을 읽어 넘긴다(01·02 뒤), 04 관리 화면이 사실대로 말한다(03 뒤), 05 calc가 예시 스킬을 쓴다(03 뒤)다. 병합 사이의 틈 둘(01~03 사이 `skills`를 적어도 효과가 없다, 03~04 사이 화면이 효과를 낮춰 말한다)을 함께 적었다. 선택 화면의 설명에 적은 사실은 훅이 짚어 대 봤다. 화면 리터럴 파일 여섯(13곳)은 grep으로 맞았고, 첫 판에 적은 "시험 사례 마흔 개 남짓"은 잰 수가 아니어서 프로브 회차(26, 28)와 "시험으로 옮길 수는 세지 않았다"로 고쳤다. 사진이 실제로 바뀌는지는 돌려 보지 않은 어림이라고 설명에 적었다.

> 질문: skill-plugin 티켓을 어떻게 나눌까요?
>
> 사용자: 다섯 장으로 나눈다 (Recommended) — 매니페스트 칸, 스킬 문서 읽기, 런타임, 관리 화면, 예시 스킬을 PR 하나씩으로 냅니다. 1·2를 함께 시작하고 3 뒤에 4·5를 함께 돌립니다. 계약 PR이 작아 칸의 모양을 따로 리뷰할 수 있고, 머리말 읽기 시험과 화면 파일 수정이 한 세션에 섞이지 않습니다. 근거 프로브의 회차는 26과 28인데, 그중 시험으로 옮길 수는 세지 않았습니다. PR이 하나 더 늘어나는 것이 값입니다.

고르지 않은 것은 "넉 장, 명세의 묶음 그대로"였다.

## 체크아웃 정리

지시문대로 워크트리에 들어가기 전에 `tidy-checkouts`를 돌았다. 루트를 `b490a852`에서 `f5c944b8`로 당겼다. 지운 것은 `morning-empty-median`, `next-feature-design`, `skill-plugin-spec` 워크트리와 그 브랜치다. `05-default-model-required-and-checked`는 `remove`가 종료 1로 멈췄다(이름 바꾸기 WinError 5, `agent-os.exe`와 `python.exe` 둘이 모듈을 올렸다). `03-default-model-plugin-and-explicit-flag`·`06-round-drive-record`는 바뀐 파일이 있고, `admin-style-spec`·`admin-style-to-spec`·`mcp-shutdown-spec`·`web-widget-spec`은 병합된 PR이 없으며, `agent-os-direction`은 도는 세션이 쥐고, `confident-wright-2d3ebf`·`elegant-dijkstra-aaddb9`는 앱 표지가 있어 남겼다. 휴지통 줄은 없었다.

## 명세 검토

`spec-reviewer`가 체크리스트 일곱과 질문 둘로 봤다. 막는 문제는 없었고, 고칠 것은 이렇게 받았다. 보고의 문장은 그대로 옮기지 않고 아래 "손으로 본 것"과 코드 읽기로 대 본 뒤에 명세에 적었다.

- 어긋난 사실 넷. `yaml` 계약이 간접 사슬로 서지 못하는 것, `skills`의 패턴이 `PluginName`만으로는 걸리지 않는 것, `read_skill`이 `_parse`를 따르면 값이 `__cause__`에 남는 것, 결정 칸의 꼴이 mcp가 아니라 모델인 것.
- 묶음의 순서 하나. 관리 화면은 런타임 뒤다. 먼저 들어가면 결정 칸이 런타임이 받아 줄 재개를 막는다.
- 빠진 것. 사진 비교(01·04), `_SchemaOnlyPlugins`를 포함한 가짜 소스 자리, 옛 셈의 자리, 어댑터와 core의 스토리 3·4·9·16 시험, D에서 낡는 글, 변이 표의 선택자.

## 측정 (프로브 `answer_format_llm.py`)

명세가 어림으로 둔 것, 곧 예시 스킬이 calc의 답을 바꾸지 않는다는 것을 티켓 전에 쟀다. 티켓 05가 본문을 정해야 하는데, 본문이 값이나 도구 호출을 바꾸면 스킬을 고칠지 시험을 고칠지가 그 티켓에서 터지기 때문이다. 커밋한 프로브 `.scratch/skill-plugin/probes/answer_format_llm.py`이고 표는 그 `README.md`다.

- 대조(블록 없음)와 블록 갈래 모두 새 실행 5회가 값 4·도구 있음, 이어 가기 3회가 `20`이었다. 16회차 토큰 합계 180153이다.
- 양성 대조인 도구금지 갈래(같은 자리에 도구를 쓰지 말라는 글)는 2회 모두 출력 `4`에 도구 호출이 없었다. 그 자리의 글이 실제 모델의 행동을 바꿀 수 있다는 것을 보인다. 합계 6690이다.
- 측정 아님 0. 회차가 적어 드문 흔들림은 잡지 못한다. calc 코드가 엮는 실제 경로와 요약을 지나는 `-m llm` 시험은 재지 않았다.

첫 판은 ruff E501로 걸렸고(`tools/rewrap_comments.py`로 풀었다), 도구금지 갈래가 없는 첫 설계는 양성 대조가 없어 더했다.

## 손으로 본 것 (커밋하지 않은 스크래치 스크립트)

명세에 적은 "손으로 봤다"가 이것이다. 스크립트는 세션 스크래치패드의 `il_recheck.py`와 `manifest_pattern.py`이고 저장소에 없다.

- `uv run python <스크래치패드>/il_recheck.py`. 서브에이전트 사본의 `adapters/filesystem.py`에 양성 대조로 심긴 `import yaml`이 첫 판을 오염시켜(`indirect` 갈래가 BROKEN이었다) 그 줄을 뺀 깨끗한 사본으로 다시 나눠 쳤다. `yaml`을 import하는 파일이 `sdk/skill.py` 하나인 사본에서, 키 없는 `forbidden`은 일곱 층 모두 BROKEN, `allow_indirect_imports = true`는 KEPT, 거기에 `adapters/clock.py`의 직접 `import yaml`을 더하면 BROKEN이다.
- `uv run python <스크래치패드>/manifest_pattern.py`. `parse_manifest`의 `mcp`가 `../../evil`, `UPPER`, 한 글자를 그대로 받는다. `tuple[PluginName, ...]` 시제품도 받고 스키마에 패턴이 없다. `tuple[Annotated[PluginName, Field(pattern=PLUGIN_NAME_PATTERN)], ...]`은 `string_pattern_mismatch`로 거부하고 스키마에 패턴이 실린다.
- `uv run python tools/mutate.py --check <표>`. `prepare_mutations.toml` 3개와 `continuation_mutations.toml` 30개는 원문이 모두 있다.

`uv.lock`의 변경과 사진 정답의 변경은 돌려 보지 않아 어림이고 티켓에 그렇게 적었다.

## 고친 문서

- 명세. 서두 한 문단을 포함해 `(2026-11-04 명세 검토…)` 주석 열일곱이다(`grep -o`로 셌다). 표시 글자 수는 `거부한 안:` 29, `명세가 정했다` 14, `넘겨받았다` 1, `사용자가 골랐다` 2 그대로다(`grep -o`로 셌다).
- ADR 0041. 이력 2026-11-04 "명세 검토가 쓰지 않는 칸의 뜻과 칸의 패턴, 결정 칸의 꼴, 티켓의 순서를 바로잡았다"와 본문 포인터 넷이다. 사용자 승인은 아래 "ADR 승인"이다.
- `.scratch/plan.md`. skill-plugin 행, claude-code-compat 행(명세가 범위 밖에 둔 셋을 넘겼다), 프론티어 문단이다. 기능 상태는 첫 티켓이 병합될 때까지 `todo`다.

## 티켓

`.scratch/skill-plugin/issues/`에 다섯 장을 썼다. 01 계약(None), 02 읽기(None), 03 런타임(01·02), 04 관리 화면(03), 05 예시(03)다. 나란히 도는 둘의 함께 고치는 파일을 티켓마다 적었다. 01·02는 `.claude/rules/sdk.md` 하나이고 줄이 다르다. 04·05는 없다(티켓의 고칠 자리로 대 봤다).

넘긴 것의 받는 쪽과 Blocked by를 대 봤다(`to-tickets` 5단계).

| 넘긴 것 | 받는 쪽 | 받는 쪽이 넘기는 쪽 뒤에 서나 |
|---|---|---|
| 일지 2026-11-03-03의 셋(`Any` 좁히기, 비ASCII 이름, 어댑터 경로의 `\r`) | 02의 같은 이름 절 | 넘기는 쪽이 이미 병합된 명세다 |
| 런타임이 읽는다는 말(`sdk.md`) | 03 | 03이 01·02에 막힌다 |
| 안내 줄 걷기 | 04 | 04가 03을 거쳐 01에 막힌다 |
| 실제 스킬 경로의 `-m llm_widget` | 05 | 05가 03에 막힌다 |
| 범위 밖 셋(이름 규칙, 유니코드, 1024자) | `plan.md` claude-code-compat 행 | 그 행은 skill-plugin 뒤의 슬라이스 9다 |

옮긴 시험을 지금 이음매로 잴 수 있는지 코드로 봤다. 두 `run()` 사이의 본문 바꾸기는 `FakePlugins`의 공개 속성 선례(`tests/core/test_run.py`의 `model_manifests`), 프롬프트 동일성은 `ToolAwareFakeModel.received`, 목록의 보통 행은 core의 가짜 `list_manifests`가 `NotImplementedError`라 어댑터 자리, `_run_calc`는 저장소 루트 고정이라 임시 루트를 받게 고치는 것까지 수용 기준에 들었다. `PluginList.stories.tsx`의 그 줄은 첫 판에 스토리의 설명으로 적었는데 grep으로 play 단언임을 보고 고쳤다.

## 인계 (셀프 리뷰 직전)

이 세션의 제목은 `docs/skill-plugin-tickets`였다. 세션 컨텍스트가 인계 문턱을 넘은 채 `/code-review`를 부르자 `hook_handoff`의 계기가 왔다(`handoff.md`). 인계하지 않는 때 다섯에 들지 않는다(`get_session`의 `self`에 `parentSessionId`가 없다). 그래서 셀프 리뷰를 밟지 않고 넘긴다. 아무것도 커밋하지 않았다. 사용자가 고치거나 되돌린 것은 없고, 이 세션이 스스로 고친 것은 위 절마다 적었다.

새 세션이 이어받을 것은 이렇다.

- **셀프 리뷰.** `/code-review origin/main`부터다. 변경은 명세 주석, 티켓 다섯, 프로브 하나와 README, ADR 0041 이력, `plan.md`, 이 일지이고 코드는 없다. 미추적 파일이 있어 범위에 넣는다. 위 "손으로 본 것"의 스크립트는 이 세션의 스크래치패드(`C:\Users\User\AppData\Local\Temp\claude\C--project-agent\068141f0-3384-4f44-b55c-0dee9c813f41\scratchpad\`)에 있고 저장소에는 없다. 리뷰어가 대 보려면 그 폴더를 읽거나 같은 모양을 다시 친다.
- **ADR 0041 승인.** 2026-11-04 이력과 포인터 넷은 초안이고 아직 승인받지 않았다. 셀프 리뷰를 반영한 뒤에 사용자에게 보이고 승인을 받는다(`CLAUDE.md` 작업 규약 5). 병합은 묻지 않는다.
- **사용자에게 알릴 것.** 아직 알리지 않았다. 위 "체크아웃 정리"의 보고, 원격에 남은 브랜치 `docs/agent-os-direction`(이 세션에 지울 지시가 없어 그대로 두었다), ADR 0042의 차이다. 일지 2026-11-03-04의 선택지 설명은 모델·도구·스킬 접근이라 적었고 ADR 0042의 굵은 글은 모델·도구 호출을 중재·강제·기록한다고 적었으며, 스킬 읽기는 호출이 아니라 실행 준비의 읽기이고 준비 단계의 거부에는 트레이스가 남지 않는다. 이 세션의 판단은 승인된 ADR의 문장이 모델·도구 호출이라 어긋나지 않는다는 것이고, 그 판단을 사용자에게 보인다.
- **후속 후보 둘.** 명세가 이 기능 밖에 둔 것이다. `mcp` 칸에 패턴이 없어 `../../evil`을 받는 것, 매니페스트 `_parse`의 `from error`가 `ValidationError`를 `__cause__`에 남기는 것이다. 받는 곳은 아직 없다. 일감 카드나 대기열 후보로 낸다.

낸 지시문은 이렇다.

```
다음 작업: 기능 skill-plugin. 명세 검토와 티켓 다섯까지 쓴 변경이 커밋되지 않은 채 워크트리에 있다. 셀프 리뷰부터 이어 병합과 다음 지시문까지 간다
다음 단계: 티켓
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-tickets .scratch/skill-plugin/spec.md
브랜치: docs/skill-plugin-tickets
모델: Opus 5.5 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-04-02-skill-plugin-tickets.md의 "## 인계 (셀프 리뷰 직전)"
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. docs/journal/2026-11-04-02-skill-plugin-tickets.md. 사용자가 다섯 장 분할을 골랐으니 다시 묻지 않는다. ADR 0041의 2026-11-04 이력은 셀프 리뷰를 반영한 뒤에 보이고 승인받는다
확인할 선행 조건: 없음
이번 요청 범위: 티켓까지
```

open-session을 부른다 2026-11-04T11:42:04Z

## 이어받음과 셀프 리뷰

새 세션이 위 지시문을 받아 이 워크트리에 들어와 `/code-review origin/main`부터 이었다. 범위는 base `f5c944b8`, 수정 파일 4개, 커밋 0개, 미추적 7개다. 사양은 명세·사용자의 답(위 "분할" 절의 인용 그대로)·`to-tickets` 규칙·일지 2026-11-03-03이 넘긴 셋이고, 일지의 "이어받을 것"은 요구가 아니라 참고로 넘겼다.

### 표준 축 (Critical·Major 없음, Minor 셋, Nit 둘)

지적마다 판정이다. 근거는 이 세션이 코드와 grep으로 다시 봤다.

- Minor: 티켓 04의 사진 넉 장은 더 많다. `PluginList.stories.tsx`의 `SwitchFailed`도 메타의 `data: ROWS`를 물려받아 스킬 행이 있으니 `switch-failed-*` 넉 장도 바뀔 것이다(코드를 읽은 어림). 고친다.
- Minor: 01·02의 "함께 고치는 파일은 `.claude/rules/sdk.md` 하나"는 닫힌 주장의 반례가 있다. 02가 `tests/test_server.py`의 가짜 소스(225·242행 근처)에 `read_skill`을 더하고, 01이 같은 파일의 `_admin_app` 선례 옆에 표지 행 시험을 더한다. 고친다.
- Minor: 프로브의 표지. 셋으로 나눠 봤다. 대조 갈래의 `BODY not in prompts[0]`는 보류한다. 재려는 상황이 "블록이 없는 실행"이고 사본이 오염되면 거짓이 되어 가른다. 도구금지 갈래의 `도구=False`가 종료 코드에 들지 않는 것도 보류한다. README가 적은 규약이 "종료 코드 0은 측정으로 섰다는 뜻이고 결론은 결과 줄로 읽는다"이고 `Rounds`가 그렇다. 이어 가기 회차가 둘째 프롬프트의 앞 대화 블록을 보지 않는 것은 사실이다. 표지를 더하면 대조와 블록 갈래를 다시 돌아야 해(약 18만 토큰) 표지를 바꾸지 않고, 못 보는 것으로 독스트링과 README에 적는다.
- Nit: 명세 17행과 187행의 "프로브 셋"은 그대로 둔다. 19행의 주석이 넷째를 적고, 명세는 옛 문장을 지우지 않고 표시 주석을 더하는 방식으로 왔다.
- Nit: 티켓 02의 "두 대역" 가운데 `_DisabledReader`는 Protocol이고 대역은 `_FailingReader` 하나다(`tests/adapters/test_filesystem.py` 1005·1040행). 고친다.

표준 축이 실행으로 맞다고 낸 것은 `check_adr_pointers.py` 종료 0, `mutate.py --check`의 변이 3개와 30개, `parse_manifest`의 `mcp`·`model` 경계, 시험 이름 19개, 리터럴 13곳, 토큰 합계와 주석 수다. README의 회차별 토큰은 원본 출력이 커밋되지 않아 다시 내지 못했고 합계의 산술만 맞다고 보고했다.

### 명세 축 (Critical·Major 없음, 빠진 스토리 번호와 범위 넘침 없음, Minor 셋, Nit 둘)

명세 축은 티켓 다섯을 차례로 구현하면 명세가 정한 것이 빠짐없이 구현된다고 냈고, 01·02와 04·05는 병합 순서와 무관하며 틈에서 깨지는 시험을 찾지 못했다고 냈다(코드 읽기). 사진 비교, e2e, LLM은 지시대로 돌리지 않았다.

- Minor: 03의 HTTP 선례 가운데 `tests/test_server.py`의 둘은 `_route_that_raises`로 표만 밀어 구현과 무관하게 초록이다(이 세션이 코드를 읽었다, 1304행과 그 지렛대 독스트링). 실제 자리인 `tests/channel/http/test_end_user.py`의 `FakePlugins`는 mcp와 모델만 종류로 가르고 나머지를 에이전트 표에서 찾아 "매니페스트 있음, 문서 없음"을 흉내 내지 못한다. 고친다.
- Minor: 03이 `-m llm_widget`을 05로 미룬 것은 `CLAUDE.md` 검증 명령과 어긋난다. 그 줄은 서버의 최종 사용자 경로를 건드리면 친다고 적었고 예외가 없다. 예외를 적지 않고 03도 치게 고친다.
- Minor: 표준 축과 같은 둘(사진, 함께 고치는 파일)이다. 위에서 판정했다.
- Nit: ADR 0041 36행 "같은 셈을 적은 코드 셋"에 명세 146행의 주석이 "실제보다 적다"고 적었는데 포인터가 없다. 그대로 둔다. `.claude/rules/adr.md`가 달지 않는 것으로 적은 "그때의 셈"이고, 그 문단 끝이 묶음은 명세, 티켓은 to-tickets에 넘겼으며, 티켓 03이 늘린 목록을 든다.
- Nit: 05의 "블록 사이와 블록 뒤"에 머리 문장과 블록 사이가 없다. 고친다. 지금 `PROMPT`(`plugins/agents/calc/agent.py`를 읽었다)와 프로브의 글이 빈 줄 하나다.

### 고친 것

아래는 새로 쓴 사실 문장의 원문이다. PR 직전 리뷰의 밀 주장으로 넘긴다.

- 티켓 04: "`List`와 `SwitchFailed` 두 스토리가 같은 `ROWS`를 그려 스킬 행이 있으므로, 안내 줄이 없어지며 `web/apps/admin/visual/snapshots/organisms-pluginlist--{list,switch-failed}-*` 여덟 장이 바뀔 것이다(코드를 읽은 어림, 돌리지 않았다)."
- 티켓 01·02: "수용 기준의 고칠 자리로 대 본 겹침은 줄이 다른 두 파일이다." 뒤에 `.claude/rules/sdk.md`와 `tests/test_server.py`를 들고 "구현하며 겹치는 파일이 더 나와도 같다. 어느 파일이든 뒤에 병합되는 쪽이 앞의 것을 합친다." 닫힌 주장의 반례만 덧붙이지 않고 일반 조항으로 적었다.
- 티켓 02와 명세 145행: "Protocol `_DisabledReader`와 대역 `_FailingReader`는 `read_disabled`만 보아 해당하지 않는다."
- 티켓 03: "시험의 자리는 실제 라우트와 준비를 지나는 `tests/channel/http/test_end_user.py`"이고 "`_route_that_raises`로 예외를 상태 코드로 옮기는 표만 밀어 구현과 무관하게 초록이므로 이 시험의 선례가 아니다". 새 수용 기준 "`FakePlugins`를 넓힌다"는 "지금은 mcp와 모델만 종류로 가르고 나머지를 에이전트 표에서 찾아, 스킬 매니페스트와 스킬 문서를 따로 들 자리가 없다". core 시험의 가짜는 경로를 밝혔다.
- 티켓 03의 검증: "최종 사용자 경로의 실행 준비가 바뀌어 `CLAUDE.md`의 검증 명령이 뒤의 둘을 요구한다. 저장소의 매니페스트가 아직 `skills`를 적지 않아 이 두 시험은 스킬 경로를 지나지 않고, 옛 경로가 깨지지 않았는지를 본다." 위 "티켓" 절 표의 "실제 스킬 경로의 `-m llm_widget`은 05"는 그대로 맞다.
- 티켓 05: "머리 문장과 블록 사이, 블록 사이, 블록 뒤는 모두 빈 줄 하나다."
- 명세 173행에 표시 주석 하나를 더했다. 그래서 위 "고친 문서"의 주석 열일곱은 지금 열여덟이다(`(2026-11-04 명세 검토`를 Grep의 count로 셌다).
- 프로브 독스트링과 README: "이어 가기 회차의 표지는 두 실행이 0으로 끝나고 둘째가 첫째의 식별자를 `--continuation`으로 받은 것까지이고, 둘째 프롬프트에 앞 대화 블록이 든 것은 보지 않는다. 앞 값 없이는 `20`이 나오기 어렵다는 것은 어림이다." 표지와 결과는 바꾸지 않았고 다시 돌리지 않았다. 독스트링은 `tools/rewrap_comments.py`로 다시 감았다.
- 위 "티켓" 절의 "01·02는 `.claude/rules/sdk.md` 하나이고 줄이 다르다"는 그때의 판단이고, 지금은 위 티켓 01·02의 문장이다.

### 남긴 것

- 프로브 대조 갈래의 표지와 도구금지 갈래의 종료 코드: 위 표준 축 판정대로 규약에 맞아 고치지 않았다.
- 명세 17행과 187행의 "프로브 셋", ADR 0041 36행의 "코드 셋": 위 판정의 까닭으로 고치지 않았다.

### 다시 돌린 명령

- `uv run ruff check .scratch/skill-plugin/probes/answer_format_llm.py` 통과(손으로 쳤다), `uv run python tools/check_adr_pointers.py` 출력 없이 끝났다(손으로 쳤다). 손으로 치는 다섯은 커밋의 pre-commit으로 갈음하고 결과는 커밋 뒤에 적는다.

## ADR 승인

셀프 리뷰를 반영한 뒤 ADR 0041의 2026-11-04 이력 여섯 항목과 본문 표시 네 곳을 표로 풀어 보였다(27행, 28행, 33행 두 곳을 Grep으로 셌다). 이력의 글자는 셀프 리뷰가 바꾸지 않았다.

> 질문: ADR 0041의 2026-11-04 이력과 본문 표시 네 곳을 이대로 승인할까요?
>
> 사용자: 이대로 승인 (Recommended) — 이력 여섯 항목과 본문 표시 네 곳을 그대로 커밋합니다. 그 뒤 PR을 열어 병합하고 다음 작업 지시문을 냅니다. 구현 티켓은 바로잡은 내용(이름 규칙 검사, 읽지 못한 스킬을 꺼짐으로 세지 않기 등)을 따릅니다.

같은 메시지에서 넘어온 알림 셋을 사용자에게 보였다. 체크아웃 정리의 보고, 원격에 남은 `docs/agent-os-direction`(`git ls-remote`로 `e0885d8a`를 손으로 봤다), ADR 0042의 차이(일지 2026-11-03-04 68행의 "모델·도구·스킬 접근"과 ADR 0042 6행·8행의 "모델·도구 호출"을 읽었다)와 어긋나지 않는다는 판단이다. 사용자는 승인 화면에서 이 알림에 답을 더하지 않았다.

## 커밋

`02f99147`(파일 11개)이다. pre-commit은 ruff 둘, 묶음 검사 열(`check-ticket`, `lint-imports`, `zizmor`, `check-instructions`, `check-type-escapes`, `pyright-linux`, `pyright`, `run-hooks`, `pytest`, `web-verify`), 마크다운 표, 줄 구분 문자, 변이 표, 커밋 메시지가 Passed다(백그라운드 출력을 읽었다). 카나리아 명세와 헌법 판은 해당 파일이 없어 Skipped다. 인용 대조 경고 5건은 막지 않는 경고이고 원문을 옮긴 것이 아니라 낼 일이 없다. 티켓 05의 스킬 본문(아직 없는 글), 프로브 README의 해석 문장, 이 일지가 지적을 줄여 옮긴 셋이다. 사진 비교와 e2e와 `-m llm`은 코드와 화면이 바뀌지 않아 돌리지 않았다.

## 인계 (커밋 뒤)

이 세션의 제목은 `docs/skill-plugin-tickets`였다. 커밋 직후 `hook_handoff`의 계기가 왔다(세션 컨텍스트 312,201 토큰, 문턱 200,000). 인계하지 않는 때 다섯에 들지 않는다. 명령은 성공했고, 요청 범위 "티켓까지"는 병합까지이며, 이 세션의 지시문은 다른 경계(`인계: 셀프 리뷰 직전`)이고, `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다. 사용자가 고치거나 되돌린 것은 없다. 아직 PR이 없다.

새 세션이 이어받을 것은 이렇다.

- **PR 직전 리뷰.** `coderabbit-review`부터다. 돌지 못하면 `/security-review`와 `bug-perf-review`다(`docs/constitution/operations.md` 리뷰 파이프라인 2). `bug-perf-review`로 가면 위 "고친 것"의 문장을 브리프에 밀 주장으로 나열한다.
- **PR과 병합.** PR을 열고 `.claude/skills/next-session/merge.md`를 Read로 열어 따른다. ADR 0041은 위 "ADR 승인"대로 승인받았으니 병합은 묻지 않는다.
- **후속 후보 둘.** 위 앞 세션 인계의 것이고 아직 내지 않았다. `mcp` 칸에 패턴이 없어 `../../evil`을 받는 것, 매니페스트 `_parse`의 `from error`가 `ValidationError`를 `__cause__`에 남기는 것이다. 받는 곳이 없다. 일감 카드나 대기열 후보로 낸다.
- **원격 브랜치 `docs/agent-os-direction`.** 사용자에게 알렸고 지우라는 답은 없었다. 그대로 둔다.
- **이 절 뒤의 일지는 커밋되지 않았다.** 새 세션이 이어 쓰고 다음 커밋에 싣는다. 회고와 `## 다음`은 단계를 닫는 그 세션이 한다.

낸 지시문은 이렇다.

```
다음 작업: 기능 skill-plugin. 셀프 리뷰 반영과 ADR 0041 승인, 커밋까지 마쳤다. PR 직전 리뷰부터 이어 병합과 다음 지시문까지 간다
다음 단계: 티켓
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-tickets .scratch/skill-plugin/spec.md
브랜치: docs/skill-plugin-tickets
모델: Opus 5.5 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-04-02-skill-plugin-tickets.md의 "## 인계 (커밋 뒤)"
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰 반영과 ADR 0041 승인, 커밋까지 했고 PR은 아직 없다. 남은 단계는 PR 직전 리뷰, PR 열기, merge.md 2(봇 회차)부터의 병합, 회고와 일지의 "다음", 다음 지시문이다. 일지의 인계 절은 커밋되지 않은 채 워크트리에 있다. docs/journal/2026-11-04-02-skill-plugin-tickets.md
확인할 선행 조건: 없음
이번 요청 범위: 티켓까지
```

`git worktree unlock`은 `is not locked`로 끝났다. 띄운 백그라운드 작업은 모두 끝나 멈출 것이 없었다.

open-session을 부른다 2026-11-04T12:17:51Z

## 이어받음과 PR 직전 리뷰

새 세션이 위 지시문을 받아 이 워크트리에 들어와 PR 직전 리뷰부터 이었다. `git fetch origin` 뒤 `origin/main`과 merge-base가 모두 `f5c944b8`이라 합칠 것이 없었다. `sibling_overlap.py`는 번호 겹침 없음이고, `.scratch/plan.md`를 `mcp-shutdown-spec` 워크트리도 고쳤다고 냈다.

### CodeRabbit CLI

돌지 못했다. `coderabbit-review`가 1단계에서 끝냈고, 이 세션이 `coderabbit auth status`를 다시 쳐 `Plan: Free`, `Seat: not assigned`를 봤다. CLI는 0.7.5다. `docs/constitution/operations.md` 리뷰 파이프라인 2의 2026-11-03 기록은 같은 0.7.5에 `Plan`·`Seat` 줄이 없고 리뷰가 돌았다고 적었다. 그래서 판이 달라서 생긴 차이는 아니다. 리뷰를 실제로 돌려 보지는 않았다(그 정의가 `not assigned`면 멈춘다). 대체 둘로 갔다.

### `/security-review`

보고는 이렇다. 찾은 취약점은 없다. 서브태스크가 지적을 내지 않아 거르는 단계는 돌 것이 없었다. 서브태스크가 전문을 읽은 코드는 프로브 `answer_format_llm.py` 하나다. `subprocess.run`은 목록 인자이고 `shell=True`가 없으며, `ANTHROPIC_API_KEY`는 있는지만 보고, 쓰는 곳은 임시 폴더뿐이다. 이 셋은 이 세션도 프로브를 읽어 맞다고 봤다. 마크다운은 지시의 제외 규칙으로 판정하지 않았고 비밀값 패턴만 Grep했다(일치한 줄은 키 이름과 경로뿐이고 실제 값은 없었다는 보고다). 티켓 01·04·05와 명세, ADR 0041의 나머지 줄은 줄마다 읽지 않았다는 보고다. MCP 어댑터가 키를 자식에 넘기지 않는다는 것은 코드를 읽은 결론이고 돌려 보지 않았다는 보고다.

### `bug-perf-review`

기준 `f5c944b8`, 파일 11개, 호출 40에서 멈췄다는 보고다. 유효 0, 보류 1, 오탐 4이고, 위 "고친 것"에서 넘긴 밀 주장 아홉은 모두 반례가 없었다는 보고다. 프로브는 돌리지 않았다(실제 모델을 부른다).

- 보류 Minor: 티켓 02의 가짜 목록에 `.scratch` 프로브의 가짜 셋(`mcp-shutdown/probes/write_failure.py`, `web-widget/probes/event_timing.py`, `harness/probes/precommit_xdist/filesystem_read_retry.py`)이 없어, `read_skill`이 늘면 pyright가 빨개질 수 있다는 지적이다. **오탐으로 닫았다.** `pyproject.toml`의 `[tool.pyright]` `include`가 `src`, `tests`, `tools`뿐이라(이 세션이 Grep으로 읽었다) `.scratch`는 범위 밖이다. 티켓을 고치지 않았다. 앞의 둘이 `PluginSource` 자리에 넘어가는 것은 Grep으로 봤고, 지난 측정의 기록이라 지금 포트에 맞추지 않는다.
- 오탐 넷은 티켓 03의 "넷을 본다"(읽는 대상의 넷째가 기존 `model_reads`로 읽힌다), 일지의 인계 지시문, 티켓 01의 "13곳"이 `conversation_limit: null`만 센 수인 것, 프로브의 표지와 종료 코드다(위 "남긴 것"의 판정 그대로).
- 보고가 대지 못했다고 적은 것은 `.scratch/plan.md`의 diff, 명세 주석 하나하나의 본문, ADR 0008·0010·0012·0017·0019의 본문, 티켓 05 본문과 프로브 `BODY`의 코드포인트 일치 등이다.

리뷰를 반영해 고친 파일은 없다. PR 체크리스트에 CLI가 돌지 못한 것과 대체 둘의 결과를 적는다.

### 커밋과 PR

`fb06dc86`(이 일지 하나)이다. pre-commit은 묶음 검사 열(`lint-imports`, `zizmor`, `check-ticket`, `check-instructions`, `check-type-escapes`, `pyright`, `pyright-linux`, `run-hooks`, `pytest`, `web-verify`), 마크다운 표, 줄 구분 문자, 변이 표, 인용 대조, 커밋 메시지가 Passed다(백그라운드 출력을 읽었다). ruff 둘과 카나리아 명세, 헌법 판은 해당 파일이 없어 Skipped다. ruff는 앞 `02f99147`의 pre-commit에서 Passed라고 위 "커밋" 절이 적었다. 푸시 전에 `git fetch origin` 뒤 `git log --oneline HEAD..origin/main`이 비어 합칠 것이 없었다. [PR 460](https://github.com/njh6803/agent-os/pull/460)을 열었다. 커밋 뒤 계기는 이 세션의 지시문이 이미 `인계: 커밋 뒤`여서 `handoff.md` 1대로 넘기지 않았다.

## 인계 (PR 연 뒤)

이 세션의 제목은 `docs/skill-plugin-tickets`였다. PR을 연 직후 `hook_handoff`의 계기가 왔다(세션 컨텍스트 232,739 토큰, 문턱 200,000). 인계하지 않는 때 다섯에 들지 않는다. 명령은 성공했고(`gh pr view`가 `OPEN`), 요청 범위 "티켓까지"는 병합까지이며, 이 세션의 지시문은 다른 경계(`인계: 커밋 뒤`)이고, `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다. 이 세션의 사용자 메시지는 첫 메시지 하나이고 위 "인계 (커밋 뒤)"의 지시문과 같은 글이다. 사용자가 고치거나 되돌린 것은 없다.

새 세션이 이어받을 것은 이렇다.

- **봇 회차와 병합.** `.claude/skills/next-session/merge.md`를 Read로 열어 2(봇 회차)부터 한다. `@coderabbitai review`를 아직 남기지 않았고 `tools/wait_ci.py` 대기도 띄우지 않았다. ADR 0041은 위 "ADR 승인"대로 승인받았으니 병합은 묻지 않는다.
- **회고와 `## 다음`.** 단계를 닫는 그 세션이 이 일지까지 읽고 돈다. `merge.md` 3대로 병합 대조 전에 푸시한다.
- **회고 후보 하나.** CodeRabbit의 `auth status`가 2026-11-03에는 0.7.5에서 `Plan`·`Seat` 줄 없이 보였고 리뷰가 돌았다고 `docs/constitution/operations.md` 리뷰 파이프라인 2가 적었는데, 2026-11-04에는 같은 0.7.5에서 `Plan: Free`, `Seat: not assigned`가 보였다(위 "CodeRabbit CLI"). 그 문단이 가르지 못했다고 적은 "CLI 판인지"의 근거이고(대기열 557), `coderabbit-review` 정의가 `not assigned`에서 멈춰 리뷰가 실제로 거절되는지는 이 세션이 보지 못했다.
- **후속 후보 둘.** 위 인계들이 넘긴 것이고 아직 내지 않았다. `mcp` 칸에 패턴이 없어 `../../evil`을 받는 것, 매니페스트 `_parse`의 `from error`가 `ValidationError`를 `__cause__`에 남기는 것이다. 받는 곳이 없다. 일감 카드나 대기열 후보로 낸다.
- **원격 브랜치 `docs/agent-os-direction`.** 위 "ADR 승인"의 알림대로 사용자의 답이 없어 그대로 둔다.
- **이 절 뒤의 일지는 커밋되지 않았다.** 새 세션이 이어 쓰고 다음 커밋에 싣는다. 그 커밋을 푸시하면 봇이 다시 돌므로 `merge.md` 2의 회차 세기를 따른다.

낸 지시문은 이렇다.

```
다음 작업: 기능 skill-plugin. PR 직전 리뷰와 PR 열기까지 마쳤다. 봇 회차부터 이어 병합과 다음 지시문까지 간다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-tickets .scratch/skill-plugin/spec.md
브랜치: docs/skill-plugin-tickets
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-04-02-skill-plugin-tickets.md의 "## 인계 (PR 연 뒤)"
이어받을 상태: 인계: PR 연 뒤. PR 460이 열려 있고 merge.md 2(봇 회차)부터 한다. 첫 @coderabbitai review 코멘트도 새 세션이 남긴다. 회고와 일지의 "다음", 병합, 다음 지시문이 남았고 일지의 인계 절은 커밋되지 않은 채 워크트리에 있다. docs/journal/2026-11-04-02-skill-plugin-tickets.md
확인할 선행 조건: 없음
이번 요청 범위: 티켓까지
```

`git worktree unlock`은 `is not locked`로 끝났다. 띄운 백그라운드 작업은 모두 끝나 멈출 것이 없었다.

open-session을 부른다 2026-11-04T12:41:53Z

## 이어받음과 봇 회차

새 세션이 위 지시문을 받아 이 워크트리에 들어와 `merge.md` 2(봇 회차)부터 이었다. 지시문의 첫 줄 "시작 프롬프트"는 `/to-tickets`였지만 "다음 단계: PR 반영·병합"과 "이어받을 상태"가 병합까지를 가리켜 티켓을 다시 나누지 않았다(`next-session` 결정표의 "같은 시작 프롬프트" 줄대로다). 제목은 `docs/skill-plugin-tickets`로 바꿨다.

- 마지막 푸시 뒤(`fb06dc86`)에 `@coderabbitai review`를 남기고 `tools/wait_ci.py 460`을 백그라운드로 띄웠다. 끝 줄은 `모두 통과`였다(CodeRabbit, claude-review, e2e, e2e-widget, python, ticket, verify, visual, web 모두 SUCCESS).
- claude-review는 이 PR의 첫 리뷰에서 지적이 없었다. CodeRabbit은 첫 회차에서 Minor 하나를 냈다(`answer_format_llm.py` 158행, `'4' in output`이 `14`도 참으로 세는 것. 같은 꼴의 `'20' in output`도 같다).
- 판정은 보류다. 지적은 사실이지만 결과 문구의 `값=` 표지에만 닿는다. README 표의 출력 열("5회 모두 출력 `4`" 등)은 회차마다 찍는 `출력=` 줄(`print`, 155·169행)의 표준 출력이라 결론이 달라지지 않는다(프로브 코드를 읽은 결론이다. 회차의 원본 출력은 커밋되지 않았고 이 세션은 프로브를 다시 돌리지 않았다). 표지를 고치면 프로브 본문이 바뀌어 실제 모델로 대조와 블록 두 갈래(약 18만 토큰)를 다시 돌아야 한다. 그래서 코드는 그대로 두고 README에 한계 한 문장을 적었다.
- 이 보류는 일을 뒤의 작업으로 넘기는 것이 아니다. 그래서 일지 "다음"에는 넣지 않고 PR 코멘트에만 남긴다. 같은 꼴이 되풀이되는지는 대기열 571이 센다.

## 회고

후보 셋: 승인 하나, 기각 둘. 넘긴 것은 없다.

- 승인(대기열 571, 1회차): 프로브가 결과 문구에 적는 값 표지를 부분 문자열로 센 것을 PR 봇이 짚었다. 사건은 위 "이어받음과 봇 회차"의 CodeRabbit Minor이고, 층은 검사로 옮기기 어려워(값 표지는 프로브마다 다르다) 판단 기준이며, PR 하나로 되돌릴 수 있다. 더하는 것의 문턱(세 번째)에 닿지 않아 `CODING_STANDARDS.md`에는 더하지 않고 회차를 세는 행으로 두었다. 대기열에서 이 꼴을 찾았으나 같은 행이 없었다(`--search answer_format`, `부분.문자열.검사`, `숫자.경계`).
- 기각: 이 PR 직전 리뷰에서 CodeRabbit CLI가 `Seat: not assigned`로 돌지 못한 것. 사람 몫인 대기열 570이 이미 같은 일(좌석 배정까지는 `operations.md` 리뷰 파이프라인 2의 대체 둘)을 덮고, 사람 몫 행은 다시 보아도 회차를 더하지 않는다.
- 기각: 지시문의 "시작 프롬프트"가 세 지시문 내내 `/to-tickets`로 남은 것. `next-session` 결정표의 "작업을 마치지 못한 채 끊는다" 줄이 "같은 시작 프롬프트"로 정한 설계이고, 세 세션 모두 "다음 단계"와 "이어받을 상태"로 바로 이었다. 실수가 난 사건이 없다.
- 만료할 행: 없음(`uv run python tools/queue_open_rows.py`).

## 다음

- PR 460 병합 뒤 `.scratch/plan.md`의 skill-plugin 행이 가리키는 구현 티켓을 시작한다. 01(매니페스트가 스킬을 고른다, 계약)과 02(스킬 문서를 읽는다)는 서로 막지 않아 나란히 열 수 있다. 같은 파일 `.claude/rules/sdk.md`와 `tests/test_server.py`를 줄이 다르게 고치므로 뒤에 병합되는 쪽이 앞의 것을 합친다(두 티켓 본문에 적었다). 03(실행 준비)은 01·02 뒤, 04(관리 화면)·05(예시 스킬)는 03 뒤다. 각 티켓은 `/implement .scratch/skill-plugin/issues/<파일>`로 시작한다.
- 후속 후보 둘은 받는 곳이 아직 없다. `mcp` 칸에 이름 패턴이 없어 `../../evil`을 받는 것, 매니페스트 `_parse`의 `from error`가 `ValidationError`를 `__cause__`에 남기는 것이다. 사용자가 일감 카드나 대기열 후보로 낼지 정한다.
- 원격 브랜치 `docs/agent-os-direction`이 남아 있다(위 "ADR 승인"의 알림에 사용자의 답이 없었다).
- 대기열 571: 프로브의 값 표지가 부분 문자열로 센 사건이 두 번 더 나오면 `CODING_STANDARDS.md`에 더한다. 대기열 570은 사람 몫이다(CodeRabbit 좌석 배정).
- `.scratch/plan.md`를 `mcp-shutdown-spec` 워크트리도 고쳤다(`sibling_overlap.py`). 그 PR이 먼저 병합되면 이쪽이 합친다.
