# 2026-10-31 (08) 모델 플러그인 티켓

## 시작

> 사용자: .claude/skills/to-tickets/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가
> 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/model-plugin/spec.md
> / 다음 작업: 기능 model-plugin. 모델 플러그인을 런타임이 읽게 하는 설계(ADR 0040)의 명세를 검토하고 티켓으로 쪼갠다 / 다음
> 단계: 티켓 / 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은
> 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 model-plugin-tickets)로 새
> 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 시작 프롬프트: /to-tickets .scratch/model-plugin/spec.md / 브랜치:
> docs/model-plugin-tickets / 모델: Opus 5.5 / xhigh / 읽을 것: docs/journal/2026-10-31-07-model-plugin-spec.md의 "다음" 절 /
> 이어받을 상태: 없음. 명세 검토(spec-reviewer 서브에이전트)를 /to-tickets 전에 먼저 돌린다. to-tickets가 받을 일 둘(매니페스트
> PluginError 문구의 input_value, ModelSource가 모델 아닌 종류를 거르는 자리)은 위 일지 "다음"에 있다. / 확인할 선행 조건: 주
> 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를
> Read로 열어 따른다 / 이번 요청 범위: 티켓까지

첫 턴 훅이 짚은 차례대로 세션 제목을 `docs/model-plugin-tickets`로 바꾸고, `tidy-checkouts`를 돌고, `EnterWorktree(name=model-plugin-tickets)`로 들어가 `docs/model-plugin-tickets`를 땄다.

## tidy-checkouts 보고

- 루트: main을 `d5e2f1ec`에서 `d4221552`(origin/main)로 당겼다.
- 지운 것: 없다.
- 남긴 것: `08-admin-decision-column`(`remove`가 종료 1. 이름 바꾸기가 WinError 5로 거부됐고 읽을 수 있는 프로세스에서 쥔 것을 찾지 못했다), `next-feature-grill`(쉬는 세션 넷의 프로세스를 `end-holders`로 끝냈는데 다시 친 `judge`에서 그중 `local_e1ae186c…` 세션이 새 pid로 다시 떠서 쥐고 있었다), `wireframe-optional`(쉬는 세션 셋의 `claude.exe`와 `pwsh.exe`가 쥠), `model-plugin-spec`(도는 세션 `docs/model-plugin-spec`), `06-round-drive-record`(바뀐 파일), `admin-style-spec`·`admin-style-to-spec`·`mcp-shutdown-spec`·`web-widget-spec`(병합된 PR 없음), `confident-wright-2d3ebf`·`elegant-dijkstra-aaddb9`(앱 표지).
- 사람에게 넘길 것 없음. 휴지통 줄 없음.

## 명세 검토

`spec-reviewer` 서브에이전트에 명세 경로와 특히 볼 자리 넷(계약 티켓이 혼자 초록인가, 런타임과 가장자리가 나란히 도는가, 매니페스트 `PluginError` 문구의 `input_value`, `ModelSource`가 모델 아닌 종류를 거르는 자리)을 넘겼다. 결과는 blocker 2 · should-fix 8 · nit 6이다. 근거는 대부분 서브에이전트의 코드 읽기이고, 값이 새는 것 하나는 서브에이전트가 임시 스크립트(세션 스크래치패드의 `review/echo_secret.py`)로 손으로 봤다고 보고했다. 그 스크립트를 커밋하지 않았으니 프로브의 측정이 아니다.

blocker 둘의 근거 가운데 넷은 이 세션이 파일을 열어 다시 봤다. `tests/test_server.py:154`의 `SONNET = parse_manifest(…)`가 모듈 수준이고, `tests/test_main.py:43`이 `DEFAULT_MODEL`을 import하며, `adapters/filesystem.py`의 `_parse`가 `ValidationError` 전문을 문구에 싣고, 관리 화면 `RunDecision.tsx`의 `disabledFor`가 에이전트와 `manifest.mcp`만 본다. 관리 API의 계약(`openapi.json`)에 기본 모델의 이름을 내는 자리가 없는 것도 grep으로 봤다(`"model"` 칸은 이벤트 둘의 것뿐이다).

- [blocker] 명세의 계약 묶음이 포트 모양과 `default_model`을 들어 혼자 초록일 수 없다. 포트가 바뀌는 순간 core는 모델 매니페스트를 읽어야 모델을 얻고, 그러면 런타임 전체가 끌려온다. 반대로 공통 넷만 적은 `sonnet` 픽스처 둘이 가장자리 묶음에 있어 sdk만 바뀌어도 `tests/test_server.py`가 수집 오류다. `PluginName`을 만드는 쪽(계약)과 `is_plugin_name`으로 거르는 쪽(런타임)도 갈렸다.
- [blocker] 런타임과 가장자리는 나란히 돌 수 없고 의존 방향이 명세의 Further Notes와 반대다. 런타임이 코드의 기본값을 걷으면 기본 모델 매니페스트가 없는 격리 루트의 시험과 두 e2e 스택이 빨갛고, 가장자리 준비(매니페스트를 두고 `--model claude-opus-5`를 명시)는 지금 코드에서도 초록이다(그 이름이 지금 기본값과 같다).
- should-fix 여덟: `serve` 시작 진단과 CLI가 어댑터 문구를 그대로 내면 잘못 적은 키 값이 stderr로 나간다(스토리 10), 어댑터의 좁힘 갈래를 하나로(core는 거르지도 시험하지도 않는다), 실제 모델 시험의 `llm_called.model == model_id` 단언은 플러그인 이름과 `model_id`와 옛 기본값이 모두 같아 어떤 구현에서도 초록이다, 모델 상세 사진 정답 여덟 장, 안내 줄을 걷는 일과 켜고 끄기가 듣는 일이 다른 티켓에 갈린 것과 그 vitest(`HomePage.test.tsx`), 결정 칸의 꺼짐 미리 알림이 모델을 모르는 것(ADR 0019), 포트 메서드가 동기인지와 이름(재개의 첫 걸음에 `await`가 없다는 불변식), 스토리 8·20을 덮는 시험이 없는 것.
- nit 여섯: 생성 타입이 리터럴을 깨는 것은 어림이 아니라 지금 코드(`conversation_limit: number | null`)로 닫힌다, README `serve` 줄의 "적거나 … 안내하며", 고칠 자리에 빠진 규칙·독스트링 문장, 변이 표 둘의 원문, 모델 리터럴에 `provider: null`을 적지 않는다, 선례 파일 둘(`HomePage.test.tsx`, `tests/test_calc_plugin.py`).

## 분할 (사용자가 골랐다)

blocker 둘은 명세가 묶음을 나눈 자리에 있어 티켓을 나누는 것으로 닫는다고 보고 여섯 장의 분할을 보였다. 01 계약(sdk·`openapi.json`·생성 타입·리터럴·사진 정답·`sonnet` 픽스처 둘), 02 거부 문구가 값을 되울리지 않는다, 03 저장소와 격리 루트가 기본 모델 매니페스트를 두고 `--model`을 명시한다(01에 막힌다), 04 런타임(01·02·03에 막힌다. 코드의 기본값은 남긴다), 05 기본 모델의 코드 기본값을 걷고 시작 때 확인(04에 막힌다), 06 관리 화면이 켜고 끄기의 효과를 말한다(04에 막힌다)다. 병합 사이의 틈 둘(01~04 사이 `model` 칸이 받아들여지되 무시된다, 04~06 사이 화면이 효과가 없다고 말한다)과 결정 칸의 미리 알림이 무엇인지를 함께 적었다. 선택 화면의 설명에 적은 사실은 훅이 짚어 지금 코드에 대 봤다(`openapi.json`, `RunDecision.tsx`의 `noticeOf` 독스트링).

> 질문: 티켓을 위의 여섯 장으로 나누는 것이 괜찮은가요?
>
> 사용자: 여섯 장 그대로 (Recommended) — 01·02를 함께 시작하고 03 → 04 → 05·06 순서로 갑니다. 티켓마다 새 세션과 PR이 하나씩입니다.

고르지 않은 둘은 "02를 01에 합친다"와 "03을 01에 합친다"였다.

> 질문: 모델이 꺼져서 재개할 수 없는 실행을 관리 화면의 결정 칸이 미리 알리게 할까요?
>
> 사용자: 에이전트가 고른 모델만 (Recommended) — 에이전트 파일에 model을 적었고 그 모델이 꺼져 있으면, 버튼을 막고 '모델 X가 꺼져 있다'를 보입니다. 기본 모델은 관리 API가 그 이름을 내지 않아 화면이 모르므로, 누른 뒤 409 문구로 알립니다. 06에서 ADR 0019 이력 한 줄을 승인받습니다.

고르지 않은 것은 "지금처럼 409 문구에 맡김"이었다.

> 질문: 04와 06 사이에 화면이 '효과가 없다'고 잘못 말하는 틈을 받아들일까요?
>
> 사용자: 받아들이고 06을 따로 둔다 (Recommended) — 04는 파이썬만 고쳐 한 세션에 들어가기 쉽습니다. 06은 04 바로 뒤에 05와 함께 돌아 틈이 짧습니다. 화면이 효과를 실제보다 낮춰 말하는 쪽이라, 끈 줄 알았는데 실행이 도는 일은 생기지 않습니다.

고르지 않은 것은 "06의 화면 고침을 04에 합친다"였다.

## 명세에 단 주석

닫은 자리마다 `(2026-10-31 명세 검토: …)` 꼴의 주석을 달고, 서두의 "이력은 하나다" 뒤에 검토와 분할을 밝히는 주석 하나를 더했다. 주석은 서두가 세는 표시 글자를 쓰지 않는다. 달고 난 뒤 `grep -o`로 세니 `거부한 안:` 14, `명세가 정했다` 12, `넘겨받았다` 6, `사용자가 골랐다` 1로 main의 명세와 같았다. 처음에는 "꺼진 모델"에 단 불릿이 `사용자가 골랐다`를 써서 2였고, `to-tickets에서 사용자가 고른 것`으로 바꿨다.

- blocker 둘은 "고칠 자리"의 마지막 주석에 티켓 여섯의 분할로 닫았다. 계약에서 포트와 `default_model`을 빼 04로 보내고 `sonnet` 픽스처 둘을 01에 넣었다. 가장자리 준비는 03으로 런타임 앞에 두고, 코드의 기본값을 걷는 일은 05로 미뤘다. Further Notes 마지막 불릿에 방향이 반대라는 주석을 달았다.
- should-fix 여덟. 시작 진단의 입력값은 02가 닫고 05가 그 출구를 연다("시작 때의 확인"). 좁힘 갈래는 어댑터의 `match` 앞 하나이고 core는 거르지도 시험하지도 않는다("어댑터의 모양"). 실제 모델 시험은 플러그인 이름과 `model_id`가 다른 복사 루트로 잰다("실제 모델 호출 하나"). PluginDetail 사진 여덟 장은 01("계약"). 안내 줄과 그 vitest는 06("계약"과 Testing). 결정 칸의 미리 알림은 사용자가 골라 06("꺼진 모델"의 새 불릿, 아래 분할). 포트 메서드는 동기이고 이름은 04가 짓는다("포트의 모양"). 스토리 20은 04, 스토리 8은 05가 시험한다(Testing).
- nit 여섯. 생성 타입이 리터럴을 깨는 것은 코드로 닫힌다고 고쳤다("계약"). README `serve` 줄은 `--model claude-opus-5`를 적는다(03). 검토가 더한 자리(호출 자리 넷, 규칙 문장 둘, 독스트링, 변이 표 둘)를 "고칠 자리" 주석에 들었다. 모델 리터럴은 `provider: "anthropic"`을 적는다. 선례 파일 둘(`HomePage.test.tsx`, `tests/test_calc_plugin.py`)을 바로잡았다.
- 검토 지적이 아니라 티켓을 쓰며 더한 것 하나. 06이 결정 칸의 구현 파일을 들 수 있게 "고칠 자리" 주석에 `RunDecision.tsx`와 ADR 0019 이력 한 줄을 더했다. 티켓 템플릿은 명세가 고칠 자리로 정하지 않은 구현 파일의 경로를 적지 않는다.

## 티켓

`issues/`에 여섯을 썼다. 파일 이름의 stem이 구현 브랜치다.

- `01-contract-model-manifest-fields`(막는 것 없음)
- `02-manifest-errors-omit-input`(막는 것 없음)
- `03-default-model-plugin-and-explicit-flag`(01)
- `04-runtime-builds-model-per-run`(01, 02, 03)
- `05-default-model-required-and-checked`(04)
- `06-admin-model-toggle-and-decision-preview`(04)

넘긴 것의 받는 쪽을 대 봤다. 02가 닫는 입력값은 05의 시작 진단이 처음 stderr로 내고, 05는 02를 04를 거쳐 기다린다. 03이 명시한 `--model claude-opus-5` 덕분에 05가 코드의 기본값을 걷어도 격리 루트와 두 e2e 스택이 그대로이고, 05는 03을 04를 거쳐 기다린다. 03이 넘긴 calc 시험의 새 단언(이름 ≠ `model_id`)은 04가 받고, 04는 03을 기다린다. 04가 들인 이름 패턴 위반은 05의 시작 확인이 쓰고, 05는 04를 기다린다. 06의 시험 리터럴은 01이 더한 `model` 칸을 쓰고, 06은 01을 04를 거쳐 기다린다. README `disabled.toml` 줄은 03이 06에 넘겼고 06은 03을 04를 거쳐 기다린다. 05와 06은 함께 고치는 파일이 `README.md` 하나이고 줄이 달라(05는 `serve` 줄, 06은 `disabled.toml` 줄) 나란히 돈다(처음에는 파일이 겹치지 않는다고 적었고 셀프 리뷰가 바로잡았다). 01이 넘긴 `sdk.md`의 런타임 문장은 04가 받는다(셀프 리뷰가 04에 더했다). 01과 02는 둘 다 `tests/adapters/test_filesystem.py`를 고쳐 뒤에 병합되는 쪽이 앞의 것을 합친다.

06을 쓰며 코드를 다시 봤다. 결정 칸의 꺼짐 스토리는 `RunDecision.stories.tsx`가 아니라 `RunDetail.stories.tsx`의 `DisabledPlugins`이고, 관리 화면 e2e의 꺼짐 흐름(`plugin-toggle.e2e.ts`)은 에이전트만 끈다. `PluginList` 스토리에는 모델 행이 없어 안내 줄을 걷어도 사진이 바뀌지 않을 것이다(코드를 읽은 어림). `PluginList.tsx`의 집합 주석이 드는 "스토리 21"은 이 명세가 아니라 앞선 기능의 번호라 티켓에서 번호 대신 주석의 내용으로 가리켰다.

`plan.md`의 model-plugin 행과 프론티어 문단에 티켓 여섯과 다음(01·02)을 적었고 상태는 `todo` 그대로다.

## 검사 (셀프 리뷰 전)

- `tools/check_md_tables.py`, `tools/check_line_separators.py`, `tools/check_adr_pointers.py`는 출력 없이 끝났다. ruff 둘은 `All checks passed!`와 `1202 files already formatted`였다.
- 인용 대조(`tools/check_quotes.py`)에 바뀐 마크다운 아홉을 넘기니 경고 둘이 났다. 02의 `adapters.md` 인용은 원문의 `(도구 결과)`가 빠져 있어 원문대로 고쳤다. 04의 따옴표 둘은 저장소의 글이 아니라 `tools/mutate.py --check`의 출력이라, 그 명령을 다시 돌려 두 표가 변이 11개와 30개 모두 원문을 한 번씩 찾는 것을 보고 따옴표 없는 서술로 바꿨다. 다시 치니 경고가 없었다.
- `tools/run_checks.py`를 백그라운드로 띄웠으나 끝나기 전에 아래 인계 계기가 와서 멈췄다. 결과는 없다.

## 이 세션이 고친 것

- 티켓 06의 결정 칸 스토리를 `RunDecision.stories.tsx`로 적었다가 실제 자리인 `RunDetail.stories.tsx`의 `DisabledPlugins`로 고쳤고, 관리 화면 e2e의 꺼짐 흐름(`plugin-toggle.e2e.ts`)은 vitest로 덮는다는 줄을 더했다.
- 티켓 06이 `PluginList.tsx` 집합 주석을 "스토리 21의 근거"로 가리켰는데, 그 번호는 이 명세의 스토리 21(트레이스의 `llm_called.model`)이 아니라 앞선 기능의 것이라 주석의 내용으로 바꿨다.
- 명세 "꺼진 모델"에 단 불릿이 `사용자가 골랐다`를 써서 서두가 세는 표시가 하나 늘었다. `to-tickets에서 사용자가 고른 것`으로 바꿨다.
- 티켓 템플릿이 명세의 고칠 자리 밖 구현 파일 경로를 막아, 명세 "고칠 자리" 주석에 `RunDecision.tsx`와 ADR 0019 이력 한 줄을 더했다.
- `plan.md`를 파이썬 `write_text`로 고치자 Windows에서 줄 끝이 CRLF가 되어(git이 `CRLF will be replaced by LF` 경고를 냈다) 바이트로 LF로 되돌렸다. diff는 두 줄 바뀜 그대로다.

## 인계 (셀프 리뷰 직전)

`/code-review origin/main`을 부르자 인계 계기(`hook_handoff`. 세션 컨텍스트 210,721 토큰, 경계 `셀프 리뷰 직전`)가 와서 `handoff.md`를 Read로 열었다. 인계하지 않는 때 다섯에 들지 않는다. 계기를 낸 호출은 실패하지 않았고, 요청 범위 "티켓까지"는 커밋·PR·병합까지 이어지며, 이 세션의 지시문의 "이어받을 상태"는 `없음`이고, 이 일지에 `인계 못함` 줄이 없으며, `get_session`의 `self`에 `parentSessionId`가 없다. 그래서 넘긴다. `code-review`의 단계는 밟지 않았다.

이 세션의 사용자 프롬프트는 위 "시작"의 지시문과 "분할"의 답 셋이다. 이 세션의 제목은 `docs/model-plugin-tickets`이고 지시문을 낸 뒤 `docs/model-plugin-tickets (인계함)`으로 바꾼다. 주 체크아웃은 `git fetch` 뒤 `origin/main`과 같은 `d4221552`였다.

새 세션이 할 일은 셀프 리뷰부터다. 고정점은 `origin/main`이고, 범위에 미추적 파일(티켓 여섯과 이 일지)이 든다. 명세 출처는 `.scratch/model-plugin/spec.md`와 `.scratch/model-plugin/issues/`이고, 요구에 넣을 사용자 답 셋은 위 "분할"에 원문이 있다. 이것은 면제 PR(`docs/`)이라 티켓을 구현하지 않는다. 리뷰를 반영한 뒤 커밋(pre-commit이 손으로 치는 다섯을 갈음한다), 푸시, PR, 봇 회차, `merge.md`의 "워크트리에서 병합할 때", `next-session`(다음은 막힌 것이 없는 티켓 01과 02를 나란히), 회고 순서다. 티켓 06이 쓸 ADR 0019 이력 초안은 06의 일이라 이 PR에서 쓰지 않는다.

지시문:

```
다음 작업: 기능 model-plugin. 모델 플러그인을 런타임이 읽게 하는 설계(ADR 0040)의 명세를 검토하고 티켓으로 쪼갠다(티켓 여섯을 썼고 셀프 리뷰부터)
다음 단계: 티켓
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-tickets .scratch/model-plugin/spec.md
브랜치: docs/model-plugin-tickets
모델: Opus 5.5 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-10-31-08-model-plugin-tickets.md 전부
이어받을 상태: 인계: 셀프 리뷰 직전 docs/journal/2026-10-31-08-model-plugin-tickets.md. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review origin/main, 미추적 파일인 티켓 여섯과 일지 08을 범위에 넣는다)부터 한다. to-tickets는 다시 돌지 않는다. 명세 검토와 분할, 사용자 답 셋, 티켓 여섯, plan.md 행은 끝났다(일지 "분할"·"명세에 단 주석"·"티켓"). 백그라운드 tools/run_checks.py는 인계 때 멈춰 결과가 없다. 리뷰 반영 뒤 커밋(pre-commit 갈음), 푸시, PR(면제 PR, 티켓 없음), 봇 회차, merge.md "워크트리에서 병합할 때", next-session(다음은 티켓 01·02를 나란히), retro가 남았다.
확인할 선행 조건: 없음
이번 요청 범위: 티켓까지
```

open-session을 부른다 2026-10-31T14:21:28Z

## 이어받은 세션 (셀프 리뷰부터)

> 사용자: .claude/skills/to-tickets/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가
> 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/model-plugin/spec.md
> / 다음 작업: 기능 model-plugin. 모델 플러그인을 런타임이 읽게 하는 설계(ADR 0040)의 명세를 검토하고 티켓으로 쪼갠다(티켓
> 여섯을 썼고 셀프 리뷰부터) / 다음 단계: 티켓 / 어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아
> 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다 / 시작 프롬프트: /to-tickets
> .scratch/model-plugin/spec.md / 브랜치: docs/model-plugin-tickets / 모델: Opus 5.5 / xhigh. 2의 잇는 지시문 / 읽을 것:
> docs/journal/2026-10-31-08-model-plugin-tickets.md 전부 / 이어받을 상태: 인계: 셀프 리뷰 직전 (위 "인계" 절의 지시문과 같다)
> / 확인할 선행 조건: 없음 / 이번 요청 범위: 티켓까지

첫 턴 훅대로 세션 제목을 `docs/model-plugin-tickets`로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다. to-tickets는 다시 돌지 않았다. `git fetch` 뒤 `origin/main`은 그대로 `d4221552`였다.

## 셀프 리뷰

`/code-review origin/main`. base `d4221552`, 바뀐 파일 둘(`spec.md`, `plan.md`), 커밋 없음, 미추적 일곱(티켓 여섯과 이 일지). 표준 축은 sonnet·high, 명세 축은 이 세션의 모델로 띄웠다. 명세 축의 요구는 명세를 빠짐없이 덮기, to-tickets 절차, 명세 검토 지적 닫기, 승인한 분할, 사용자 답 셋(위 "분할"의 원문), `plan.md` 행이다.

범위: base `d4221552`, 바뀐 파일 2, 커밋 0, 미추적 7.

### 표준 축 (sonnet·high)

Critical·Major 없음, Minor 2, Nit 4, smell 판단 1. 잰 것(서브에이전트 보고): 명세 표시 글자 수(`거부한 안:` 14 등)가 main과 같다, `check_quotes.py` 인용 24건 경고 없음, 인용한 규칙·README·ADR 0019·독스트링·시험 이름이 원문과 같다, `serve` 35곳, 리터럴 파일 여섯, `SONNET`·`DEFAULT_MODEL` 줄, 사진 정답 여덟 장, `mutate.py --check` 11개·30개, `_parse`가 심은 값을 문구에 싣는다(서브에이전트가 임시 스크립트로 네 종류에 심어 봤다).

- [Minor] 04의 "가짜 모델을 만드는 자리는 98곳"은 `GenericFakeChatModel(`만 셌다. `ToolAwareFakeModel(` 등이 더 있다.
- [Minor] 05와 06은 고치는 파일이 겹치지 않는다는 문장(05, 일지 "티켓")은 틀렸다. 둘 다 `README.md`를 고친다.
- [Nit] to-tickets 경로 규칙: 02의 `_parse`, 04·05의 `_model_problem`, 05의 `_add_model`, 03의 `web/apps/widget/e2e/plugins.ts`가 명세의 고칠 자리에 없다.
- [Nit] 01·06의 사진 어림은 표지가 있어 위반이 아니다.
- [Nit] 명세 "시작 때의 확인" 주석의 "표준 에러에 나간다"가 지금 사실처럼 읽힌다. 지금은 `serve`·CLI가 모델 파일을 읽지 않는다.
- [Nit] 일지의 `check_quotes.py` 근거가 그 도구의 범위(20자 이상 큰따옴표)를 적지 않았다. 위반은 아니다.
- [smell, 판단] Duplicated Code: 틈 설명과 README 줄이 여러 티켓에 되풀이된다.

### 명세 축 (Opus 5.5)

Major 1, Minor 3, Nit 3. 요청 밖 변경 없음. 맞다고 대 본 것(서브에이전트 보고): 시험 이름 11개와 따옴표 인용 전부, Blocked by 사슬과 받는 쪽 대조, 사용자 답 셋의 조건, 일지 07이 넘긴 둘(02·04가 받는다), 검토 지적 2·8·6이 닫힌 것, `plan.md`의 `todo`와 다음 01·02, 04의 요약 이벤트 `model` 시험이 잴 수 있는 것(가짜 모델의 `model_name`을 시험이 정한다).

- [Major] 03이 격리 루트 가운데 `workspace` 픽스처만 든다. `tests/test_main.py`에는 루트를 따로 짓는 시험(실행 전 오류의 매개변수 시험, `--plugins-root`로 `custom` 루트를 쓰는 둘, `_serving`·`_copy_repo_plugins`를 쓰는 `-m llm` 넷)이 있고, 04가 들어오면 "진입점 import 실패" 사례가 `기본 모델 플러그인이 없다`로 바뀌는 식으로 빨개진다. 03에서 실제 `serve` 서브프로세스를 띄우는 시험도 같다고 한 문장이 빼는 쪽으로 읽힌다.
- [Minor] 01이 "런타임이 읽는다는 말은 04가 쓴다"(`sdk.md`)고 넘겼는데 04가 받지 않는다.
- [Minor] 05·06의 README 겹침(표준 축과 같은 지적).
- [Minor] `plan.md` 행의 "첫 티켓은 계약: … core 모델 포트의 모양"이 새 분할(포트는 04)과 어긋난다.
- [Nit] 03의 `run`·`resume` 36곳은 여러 줄로 쓴 호출 하나를 빠뜨렸다.
- [Nit] 02가 코드 조각(`errors(include_url=False, …)`)과 명세에 없는 경로(`_parse`, `http/errors.py`)를 든다.
- [Nit] 명세 "포트의 모양" 주석이 인자 이름을 04가 짓는다고 하나 "기본 모델의 입구"가 `default_model`을 이미 정했다.

### 판정

코드로 다시 본 것: `grep -o`로 `tests/core/test_run.py`의 가짜 모델 생성을 셌다(`GenericFakeChatModel` 98, `ToolAwareFakeModel` 65, `SleepyModel` 6, `UnbindableModel` 1. 클래스 정의를 뺀 수). `tests/test_main.py`의 `workspace` 밖 루트 시험(303행의 매개변수 시험, 2238·2254행의 `custom` 루트, `_serving`과 `_copy_repo_plugins`)과 `main(` 호출(한 줄로 쓴 `serve` 35, `run`·`resume` 36, 여러 줄 하나, 인자를 변수로 짓는 호출 열둘)을 열어 봤다. `main`을 쓰는 시험 파일은 `tests/test_main.py` 하나다(grep). 명세에 든 구현 이름은 `grep -c -F`로 셌다.

- 고친다: Major(03 격리 루트를 일반 조항으로), Minor 넷(04의 수, README 겹침, 04가 `sdk.md` 문장을 받기, `plan.md` 행), Nit 넷(03의 호출 수, 경로 규칙과 02의 코드 조각, 명세 "표준 에러" 주석의 시제, 인자 이름 주석).
- 남긴다: 사진 어림 Nit(표지가 있다고 축 스스로 말했다), `check_quotes.py` 범위 Nit(인용은 표준 축이 grep으로 다시 맞췄고 도구의 범위는 그 독스트링이 원천이다), Duplicated Code 판단(티켓 세션은 자기 티켓과 명세만 읽으므로 틈과 README 몫이 티켓마다 있어야 한다).

### 반영

고친 것. 반영으로 새로 쓴 문장은 아래 `>` 줄에 티켓·명세·`plan.md`의 원문 그대로 옮긴다(PR 직전 리뷰에 밀 주장이다).

- 03: 격리 루트 불릿을 일반 조항으로 바꾸고, 예시로 실행 전 오류의 매개변수 시험, `custom` 루트 시험 둘, `_serving`·`_copy_repo_plugins`의 `-m llm` 시험을 들었다. 실제 `serve` 서브프로세스를 띄우는 시험을 빼는 쪽으로 읽히던 문장은 명시하는 불릿으로 옮겼다. 셋째 `>` 문장은 명세 "실행 준비의 순서"와 303행 시험을 읽은 어림이고, 넷째는 명세 "저장소의 기본 모델 플러그인과 격리 루트"의 위젯 스택 문장에서 옮겼다. 호출 수는 grep으로 셌다.

  > `tests/test_main.py`에서 실제 파일시스템 어댑터가 플러그인을 읽는 루트는 모두 `models/claude-opus-5/plugin.toml`을 함께 둔다.
  >
  > 빠뜨린 루트는 04가 모델 파일을 읽기 시작하는 순간 빨개진다.
  >
  > 명세의 준비 순서대로면 실행 전 오류 시험의 "진입점 import 실패" 사례는 import보다 앞선 `기본 모델 플러그인이 없다`로 바뀐다.
  >
  > 실제 모델을 부르는 `-m llm` 시험의 루트는 저장소의 `plugins/models/claude-opus-5`를 복사하거나 같은 `model_id`를 적는다. 04부터 그 `model_id`가 제공사에 가기 때문이다(아래 위젯 스택과 같은 까닭)
  >
  > to-tickets 시점에 그 파일의 `main(` 호출은 한 줄로 쓴 `main(["serve"…` 35곳과 `main(["run"…`·`main(["resume"…` 36곳에, 여러 줄로 쓴 호출 하나와 인자 목록을 변수로 짓는 호출 열둘이 더 있다(grep으로 셌다).

- 04: 가짜 모델의 수를 고치고, 인자 이름을 누가 짓는지 가르고, 01이 넘긴 `sdk.md` 문장을 받는 불릿을 더했다.

  > to-tickets 시점에 그 파일에서 가짜 모델을 만드는 호출은 170곳이다(`GenericFakeChatModel` 98, 그것을 상속한 `ToolAwareFakeModel` 65, 그 하위 클래스 `SleepyModel` 6과 `UnbindableModel` 1. 클래스 정의를 빼고 `grep -o`로 셌다).
  >
  > 메서드의 이름과 모델 소스를 받는 인자의 이름은 이 티켓이 짓되 `ToolSource`·`PluginSource`와 같은 꼴이다. 기본 모델의 인자 `default_model`은 명세의 "기본 모델의 입구"가 정했다
  >
  > `.claude/rules/sdk.md`에 런타임이 실행을 준비할 때마다 모델 매니페스트를 읽어 그 칸으로 모델을 만든다는 말을 더한다.

- 05·06: README 96행(`serve` 줄)과 39행(`disabled.toml` 줄)을 grep으로 보고 고쳤다. 일지 "티켓" 절의 같은 문장도 바로잡았다.

  > 06과 나란히 돈다. 둘이 함께 고치는 파일은 `README.md` 하나이고 줄이 다르다(이 티켓은 `serve` 줄의 주석, 06은 `disabled.toml` 줄).

- 02: 코드 조각을 산문으로 바꾸고, `http/errors.py` 경로를 걷었다.

  > 모양은 `jsonl.py`의 `_describe`처럼 오류마다 위치와 종류와 문구만 남기고 입력값·문맥·URL을 뺀다.
  >
  > 운영자 면의 500 봉투와 서버 기록 한 줄은 오류 문구 그대로이고 최종 사용자 면은 고정 문구다.

- 명세: "포트의 모양" 주석과 "시작 때의 확인" 주석을 고치고, "고칠 자리" 주석에 셀프 리뷰가 더한 구현 자리 넷을 적었다. 넷의 역할은 함수 정의와 독스트링을 grep으로 봤다. 서두가 세는 표시 글자는 그대로다(`grep -o`로 `거부한 안:` 14, `명세가 정했다` 12, `넘겨받았다` 6, `사용자가 골랐다` 1).

  > 기본 모델의 인자 `default_model`은 아래 "기본 모델의 입구"가 정했다
  >
  > `extra_forbidden` 거부 문구에 실리므로, 이 절의 확인이 들어서면 그 값이 표준 에러에 나간다.
  >
  > 매니페스트를 읽지 못한 문구를 짓는 `adapters/filesystem.py`의 `_parse`, 빈 모델 지정을 진단하는 `main.py`의 `_model_problem`, `--model` 도움말을 다는 `channel/cli/main.py`의 `_add_model`, 위젯 e2e의 픽스처를 쓰는 `web/apps/widget/e2e/plugins.ts`다.

- `plan.md`: 포트가 04로 간 것을 적었다. 리뷰가 내지 않은 같은 행의 닫힌 주장(관리 화면은 모델 행의 안내 줄만 걷는다)도 06의 결정 칸 미리 알림과 어긋나 고쳤다.

  > 트레이스는 바뀌지 않고 관리 화면은 모델 행의 안내 줄을 걷고 결정 칸이 에이전트가 고른 꺼진 모델을 미리 알린다. 첫 티켓은 계약: 매니페스트의 칸과 `openapi.json`(ADR 0040. 명세는 core 모델 포트의 모양도 계약에 두었으나 명세 검토가 런타임 티켓 04 로 옮겼다).

남긴 것: 위 "판정"의 셋(사진 어림 Nit, `check_quotes.py` 범위 Nit, Duplicated Code 판단).

PR 직전 리뷰에 밀 주장: 위 `>` 줄 전부. 특히 03의 "진입점 import 실패" 사례가 바뀐다는 어림과 `-m llm` 루트의 `model_id` 문장, 04의 170곳, 05·06의 README 줄 가름이다.

## 커밋

`30e54b56` "docs: 모델 플러그인 명세를 검토하고 티켓 여섯으로 쪼갠다". pre-commit의 `tools/run_checks.py` 묶음이 모두 Passed였다(check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest 395.7s, web-verify 443.8s. 묶음 444.05s). 마크다운 표, 줄 구분 문자, 변이 표(`mutate.py --staged`), 인용 대조(경고 없음), 커밋 메시지도 Passed였다. ruff 둘은 `.py`가 없어 Skipped라 커밋 전에 손으로 쳤다(`uv run ruff check .`는 `All checks passed!`, `uv run ruff format --check .`는 `1202 files already formatted`). 카나리아 명세와 헌법 판은 대상 파일이 없어 Skipped다. `-m llm`·e2e·사진 비교는 이 변경(문서만)이 닿지 않아 치지 않았다. 커밋 전 `tools/sibling_overlap.py`는 번호 겹침 없음이었고, `.scratch/plan.md`를 `mcp-shutdown-spec` 워크트리도 고쳐 나중에 병합하는 쪽의 글자 충돌 후보로 나왔다.

## 인계 (커밋 뒤)

커밋 뒤에 인계 계기(`hook_handoff`. 세션 컨텍스트 292,121 토큰, 경계 `커밋 뒤`)가 와서 `handoff.md`를 Read로 열었다. 인계하지 않는 때 다섯에 들지 않는다. 커밋은 성공했고, 요청 범위 "티켓까지"는 PR과 병합까지 이어지며, 이 세션의 지시문의 "이어받을 상태"는 `인계: 셀프 리뷰 직전`이라 경계가 다르고, 이 일지에 `인계 못함` 줄이 없으며, `get_session`의 `self`에 `parentSessionId`가 없다. 그래서 넘긴다. 열린 PR은 없다(`gh pr view docs/model-plugin-tickets`가 `no pull requests found`).

이 세션의 사용자 프롬프트는 위 "이어받은 세션"의 지시문 하나다. 이 세션이 번복하거나 고친 것은 위 "반영"과 그 "판정"이다. 이 세션의 제목은 `docs/model-plugin-tickets`이고 지시문을 낸 뒤 `docs/model-plugin-tickets (인계함)`으로 바꾼다. 백그라운드 작업은 없다(커밋은 끝났고 서브에이전트 둘도 끝났다).

새 세션이 할 일은 푸시부터다. 그 뒤 PR 직전 리뷰(`docs/constitution/operations.md` 리뷰 파이프라인 2. 밀 주장은 위 "반영"의 `>` 줄), PR(면제 PR, 티켓 없음), 봇 회차, `merge.md`의 "워크트리에서 병합할 때", `next-session`(다음은 막힌 것이 없는 티켓 01과 02를 나란히), 회고 순서다. 남긴 셀프 리뷰 지적 셋은 위 "판정"에 있다.

지시문:

```
다음 작업: 기능 model-plugin. 모델 플러그인을 런타임이 읽게 하는 설계(ADR 0040)의 명세를 검토하고 티켓으로 쪼갠다(티켓 여섯을 커밋했고 푸시부터)
다음 단계: 티켓
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-tickets .scratch/model-plugin/spec.md
브랜치: docs/model-plugin-tickets
모델: Opus 5.5 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-10-31-08-model-plugin-tickets.md의 "이어받은 세션 (셀프 리뷰부터)" 절부터 끝까지
이어받을 상태: 인계: 커밋 뒤 docs/journal/2026-10-31-08-model-plugin-tickets.md. 셀프 리뷰와 반영을 마치고 커밋했다(pre-commit 통과, 결과는 일지 "커밋"). 푸시하지 않았고 PR이 없다. to-tickets와 셀프 리뷰는 다시 돌지 않는다. 남은 단계는 푸시, PR 직전 리뷰(밀 주장은 일지 "반영"의 > 줄), PR(면제 PR, 티켓 없음), 봇 회차, merge.md "워크트리에서 병합할 때", next-session(다음은 티켓 01·02를 나란히), retro다. 일지의 이 인계 절은 커밋하지 않았다.
확인할 선행 조건: 없음
이번 요청 범위: 티켓까지
```

open-session을 부른다 2026-10-31T14:50:54Z

## 이어받은 세션 (푸시부터)

> 사용자: .claude/skills/to-tickets/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가
> 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/model-plugin/spec.md
> / 다음 작업: 기능 model-plugin. 모델 플러그인을 런타임이 읽게 하는 설계(ADR 0040)의 명세를 검토하고 티켓으로 쪼갠다(티켓
> 여섯을 커밋했고 푸시부터) / 다음 단계: 티켓 / 어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아
> 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다 / 시작 프롬프트: /to-tickets
> .scratch/model-plugin/spec.md / 브랜치: docs/model-plugin-tickets / 모델: Opus 5.5 / xhigh. 2의 잇는 지시문 / 읽을 것:
> docs/journal/2026-10-31-08-model-plugin-tickets.md의 "이어받은 세션 (셀프 리뷰부터)" 절부터 끝까지 / 이어받을 상태: 인계: 커밋
> 뒤 (위 "인계 (커밋 뒤)" 절의 지시문과 같다) / 확인할 선행 조건: 없음 / 이번 요청 범위: 티켓까지

첫 턴 훅대로 세션 제목을 `docs/model-plugin-tickets`로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다. to-tickets와 셀프 리뷰는 다시 돌지 않았다. `git fetch origin main` 뒤 `origin/main`은 그대로 `d4221552`라 합칠 것이 없었다(`git rev-parse origin/main`, 손으로 봤다). `30e54b56`을 `git push -u origin docs/model-plugin-tickets`로 푸시했다.

## PR 직전 리뷰

CodeRabbit 좌석은 없다(`coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`. 손으로 봤다). 그래서 리뷰 파이프라인 2의 대체 둘(`/security-review`, `bug-perf-review` 서브에이전트)을 나란히 돌렸다. 돌리기 전에 친 `uv run python tools/sibling_overlap.py`는 번호 겹침 없음(종료 코드 0, 손으로 봤다)이고, 글자 충돌 후보는 커밋 때와 같은 `mcp-shutdown-spec` 워크트리의 `.scratch/plan.md` 하나다. 버그·성능 축에는 위 "반영"의 `>` 줄을 열 주장으로 나눠 근거와 대 보게 했다.

**보안 축(`/security-review`).** 식별 서브태스크가 티켓 여섯 전문과 명세·`plan.md`의 바뀐 줄을 읽고, 티켓을 다음 PR에 취약점을 심을 설계 지시로 읽어 지금 코드와 대 봤다. HIGH·MEDIUM 0건이라 거짓 양성을 거르는 서브태스크는 띄울 것이 없었다. 판정의 근거는 서브태스크의 코드 읽기다. 02는 지금 있는 노출(`adapters/filesystem.py`의 매니페스트 `_parse`가 `ValidationError` 전문을 문구에 싣는다)을 닫는 지시이고, 노출을 늘리는 04·05가 02에 막혀 있어 순서도 맞다. 봤지만 뺀 것(확신 1~2/10): 02가 검증 오류가 아닌 실패(TOML 문법, `UnicodeDecodeError`, `OSError`)의 문구를 그대로 두는 것, 운영자 면 409·500이 이름과 `PluginError` 원문을 싣는 것(토큰 뒤이고 최종 사용자 면은 `http/errors.py`의 `failure_for`가 고정 문구로 덮는다), 05의 시작 진단(02 뒤에 오고 값을 심은 시험을 요구한다), 에이전트 `model`과 CLI 이름으로 짓는 경로(`PLUGIN_NAME_PATTERN`이 `..`·`/`를 막는다), 매니페스트가 요청을 정하는 것(`provider`는 닫힌 열거이고 `base_url` 같은 칸이 없다), 관리 화면이 모델 이름을 그리는 것(React 텍스트, 막는 것은 서버 409), diff의 비밀처럼 생긴 문자열(grep 0건). 이 PR이 낸 것이 아닌 참고 하나: 운영자 파일 `_parse_operator_file`도 `{error}` 전문을 싣고 02의 범위 밖이나, `disabled.toml`에는 플러그인 이름만 들어 영향이 낮다. 이 세션이 `filesystem.py`의 두 자리를 열어 문구에 `{error}`를 싣는 것을 다시 봤다. 고칠 것은 없다.

**버그·성능 축(`bug-perf-review` 서브에이전트).** 기준 `d4221552`, 범위 9파일, 마지막 호출 41(예산 40을 한 번 넘겼다). 유효 1, 보류 2, 오탐 0으로 보고했다. 밀 주장 열의 판정은 맞다 여덟(2·3·4·5·8·10, 6은 대체로, 9는 시제), 틀림 하나(1), 확인 못함 하나(7의 뒤 절. 서버 기록 한 줄이 문구 그대로인지 열지 못했다)다. 근거는 서브에이전트의 코드 읽기와 grep이고, 4·5의 수는 그 서브에이전트가 다시 셌다.

- [Minor, 유효] 03의 격리 루트 열거가 `tests/test_main.py` 793행의 `-m llm` 시험(`test_멈춘_실행은_그_프로세스가_끝난_뒤_다른_프로세스가_재개해_끝까지_간다`)을 빠뜨렸다. `tmp_path`에 루트를 짓고 서브프로세스 `_cli`로 돌아 `main(` grep에도 `_serving`·`_copy_repo_plugins`에도 걸리지 않는다. 04부터 `-m llm`에서야 빨개진다.
- [Major 후보, 보류] 05가 코드의 기본값을 걷으면 멈춘 `run`이 찍는 재개 안내 줄에 `--model`이 없어, `--model`로 돌린 실행의 줄을 그대로 친 재개가 `AGENT_OS_MODEL` 없이는 이름 없음으로 끝난다. 05가 이 길을 다루지 않는다.
- [Minor 후보, 성능, 보류] 실행마다 새 `ChatAnthropic`이 서면 httpx 클라이언트를 인스턴스 사이에 공유하지 않을 경우 실행마다 TLS 핸드셰이크를 새로 한다. 프로브는 만들기만 쟀다.
- [Nit, 주장 9] 모델 파일의 문구가 표준 에러로 처음 나가는 때는 05의 시작 확인이 아니라 04의 CLI 실행 준비다. 명세 "시작 때의 확인" 주석의 문장만 05를 말한다.

**판정.** 코드로 다시 본 것: `tests/test_main.py` 788~820행(793행 시험이 `_write_mcp_plugin`·`_write_plugin`으로 `tmp_path`에 루트를 짓고 `_cli`로 돌며 `_cli(_guidance(paused.stdout))`로 재개한다), `_cli`·`_python`·`_cli_run`·`_copy_repo_plugins`의 몸통, `_guidance`를 부르는 자리 열(567, 585, 636, 649, 695, 698, 719, 813, 2264, 2399행. grep), `channel/cli/main.py`의 `_approval_request`와 `_inherited_options`(안내 줄은 기본값에서 벗어난 `--traces`·`--plugins-root`만 물려주고 `--model`은 싣지 않는다. 독스트링이 "안내가 작동하지 않으면 안내가 아니다"라고 적는다), `.venv`의 langchain-anthropic `_client_utils.py`(`_get_default_httpx_client`·`_get_default_async_httpx_client`에 `@lru_cache`가 붙어 `base_url`·`timeout`·프록시가 같으면 같은 httpx 클라이언트를 돌려준다)와 `chat_models.py`의 `_client`·`_async_client`(`cached_property`가 그 함수를 부른다).

- 고친다: Minor(03의 열거에 793행 시험을 더하고 grep 처방을 `_cli`·`_cli_run`·`_serving`까지 넓혔다). 보류로 온 재개 안내 줄은 유효로 올려 Major로 보고 고친다. 구현 세션이 시험을 환경변수로 덮으면 운영자의 안내 줄이 깨진 채 남기 때문이다. 05의 "기본값을 걷는다"에 안내 줄이 그 실행의 기본 모델 이름을 `--model`로 싣는다는 불릿을 더하고, 03에 안내 줄을 먹이는 재개에는 `--model`을 덧붙이지 않는다는 문장을, 명세 "시작 때의 확인"의 CLI 불릿에 2026-11-01 주석을 더했다. 싣는 쪽을 고른 근거는 안내 줄을 짓는 함수의 독스트링이 이미 정한 원칙이고, 계약(`sdk/`, `openapi.json`, 헌법)이 아니어서 to-tickets가 고른다(README `serve` 줄을 고른 것과 같다).
- 오탐: 성능. 위 `@lru_cache`로 인스턴스가 달라도 httpx 클라이언트와 연결 풀을 공유한다(코드를 읽었다. 돌리지 않았다).
- 남긴다: 주장 9의 Nit. 같은 주석의 다음 문장이 02가 닫는 출구 다섯(목록·상세·실행 500·`serve`·CLI)을 들고, 티켓 02가 "04부터 모든 실행이 모델 파일을 읽는다"고 적어 구현 순서는 맞다.

명세 주석을 단 뒤 서두의 표시 글자를 다시 셌다(`grep -o`로 `거부한 안:` 14, `명세가 정했다` 12, `넘겨받았다` 6, `사용자가 골랐다` 1. main과 같다).

서브에이전트가 확인하지 못한 주장 7의 뒤 절(서버 기록 한 줄이 오류 문구 그대로다)은 `http/errors.py`의 모듈 독스트링이 "서버 기록은 덮기 전의 것을 남긴다"고 적는 것을 grep으로 봤다(코드를 읽었다. 돌리지 않았다).

## 커밋 (PR 직전 리뷰 반영)

`4ebcbade` "docs: PR 직전 리뷰를 반영해 03의 격리 루트와 05의 재개 안내 줄을 고친다". pre-commit의 `tools/run_checks.py` 묶음이 모두 Passed였다(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest 350.9s, web-verify 444.1s). 마크다운 표, 줄 구분 문자, 변이 표, 인용 대조, 커밋 메시지도 Passed였다. ruff 둘은 `.py`가 없어 Skipped라 커밋하는 동안 손으로 쳤다(`uv run ruff check .`는 `All checks passed!`, `uv run ruff format --check .`는 `1202 files already formatted`). 카나리아 명세와 헌법 판은 대상 파일이 없어 Skipped다. 커밋 전 `tools/sibling_overlap.py`는 번호 겹침 없음이었다.

커밋을 띄운 뒤 인계 계기(`hook_handoff`. 세션 컨텍스트 247,537 토큰, 경계 `커밋 뒤`)가 와서 `handoff.md`를 Read로 열었다. 이 세션의 지시문의 "이어받을 상태"가 `인계: 커밋 뒤`로 시작해 인계하지 않는 때 셋째에 들어 넘기지 않고 잇는다.

## 인계 (PR 연 뒤)

`4ebcbade`를 푸시하고 PR #444(https://github.com/njh6803/agent-os/pull/444)를 열었다. 본문은 저장소 템플릿을 채웠다(면제 PR, 티켓 없음. PR 직전 리뷰의 결과와 05의 안내 줄을 to-tickets가 고른 것을 체크리스트와 "남긴 위험"에 적었다). `/git-pr`을 부르지 않고 `gh pr create --body-file`로 열었고, 사용자에게 묻지 않은 것은 메모리의 "병합은 승인 없이 진행"을 따랐다. 앱의 `get_status`가 PR #444를 묶었다고 보였고 검사 일곱이 대기 중이었다.

PR이 서자 인계 계기(`hook_handoff`. 세션 컨텍스트 264,941 토큰, 경계 `PR 연 뒤`)가 와서 `handoff.md`를 Read로 열었다. 인계하지 않는 때 다섯에 들지 않는다. PR 만들기는 성공했고, 요청 범위 "티켓까지"는 병합까지 이어지며, 이 세션의 지시문의 "이어받을 상태"는 `인계: 커밋 뒤`라 경계가 다르고, 이 일지에 `인계 못함` 줄이 없으며, `get_session`의 `self`에 `parentSessionId`가 없다. 그래서 넘긴다. 함께 온 `hook_pr_next_session` 계기는 인계 줄이 이겨 따르지 않았다. `@coderabbitai review` 코멘트는 남기지 않았다(`PR 연 뒤` 인계는 새 세션이 남긴다). 백그라운드 작업은 없다(커밋과 서브에이전트 셋이 끝났다).

이 세션의 사용자 프롬프트는 위 "이어받은 세션 (푸시부터)"의 지시문 하나다. 이 세션이 고친 것은 위 "PR 직전 리뷰"의 "판정"이다(03의 격리 루트 열거와 grep 처방, 05의 재개 안내 줄 불릿, 03의 안내 줄 문장, 명세 "시작 때의 확인" 주석). 이 세션의 제목은 `docs/model-plugin-tickets`이고 지시문을 낸 뒤 `docs/model-plugin-tickets (인계함)`으로 바꾼다.

새 세션이 할 일은 `merge.md` 2(봇 회차)부터다. 첫 `@coderabbitai review` 코멘트와 `wait_ci`, 반영, 3(일지. 이 PR이 티켓 단계를 닫으므로 `retro`와 "다음" 절까지 마친 일지를 마지막 봇 회차의 커밋에 싣는다. "다음"은 막힌 것이 없는 티켓 01과 02를 나란히), 4(워크트리에서 병합할 때), 그 뒤 `next-session`이다. 이 절과 위 "커밋 (PR 직전 리뷰 반영)" 절은 커밋하지 않았으니 다음 커밋에 싣는다.

지시문:

```
다음 작업: 기능 model-plugin. 모델 플러그인을 런타임이 읽게 하는 설계(ADR 0040)의 명세를 검토하고 티켓으로 쪼갠다(PR #444를 열었고 봇 회차부터)
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-tickets .scratch/model-plugin/spec.md
브랜치: docs/model-plugin-tickets
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: docs/journal/2026-10-31-08-model-plugin-tickets.md의 "이어받은 세션 (푸시부터)" 절부터 끝까지
이어받을 상태: 인계: PR 연 뒤 docs/journal/2026-10-31-08-model-plugin-tickets.md. PR #444(면제 PR, 티켓 없음)를 열었고 커밋 둘(30e54b56, 4ebcbade)이 푸시됐다. @coderabbitai review 코멘트는 아직 남기지 않았다. 일지의 "커밋 (PR 직전 리뷰 반영)" 절과 "인계 (PR 연 뒤)" 절은 커밋하지 않았으니 다음 커밋(봇 회차 반영이나 "다음"을 실은 커밋)에 싣는다. 남은 것: merge.md 2(봇 회차. 첫 @coderabbitai review 코멘트와 wait_ci), 3(일지. 이 PR이 티켓 단계를 닫으므로 retro와 "다음" 절까지 마친 일지를 마지막 봇 회차의 커밋에 싣는다. "다음"은 막힌 것이 없는 티켓 01·02를 나란히), 4(워크트리에서 병합할 때), 그 뒤 next-session(다음은 티켓 01·02를 나란히). to-tickets와 셀프 리뷰, PR 직전 리뷰는 다시 돌지 않는다.
확인할 선행 조건: 없음
이번 요청 범위: 티켓까지
```

제목을 `docs/model-plugin-tickets (인계함)`으로 바꿨다. 워크트리 잠금 풀기는 `is not locked`로 끝나 넘어갔다.

open-session을 부른다 2026-10-31T15:13:04Z

## 이어받은 세션 (봇 회차부터)

> 사용자: .claude/skills/to-tickets/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/model-plugin/spec.md / 다음 작업: 기능 model-plugin. 모델 플러그인을 런타임이 읽게 하는 설계(ADR 0040)의 명세를 검토하고 티켓으로 쪼갠다(PR #444를 열었고 봇 회차부터) / 다음 단계: PR 반영·병합 / 브랜치: docs/model-plugin-tickets / 모델: Sonnet 5.5 / high. 2의 잇는 지시문 / 이번 요청 범위: 티켓까지

첫 턴 훅대로 세션 제목을 `docs/model-plugin-tickets`로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다. `git rev-parse HEAD`와 PR의 `headRefOid`가 `4ebcbade`로 같았다. to-tickets와 셀프 리뷰, PR 직전 리뷰는 다시 돌지 않았다.

## 봇 회차

`@coderabbitai review`를 PR #444에 남기고 `gh pr checks`를 한 번 읽으니 `python`·`web`·`visual`이 pending이라 `tools/wait_ci.py 444`를 백그라운드로 띄웠다. 30분 뒤 종료 코드 3(`끝: 시간 초과 30분. 남은 것 CodeRabbit(나타나지 않음)`)으로 끝났다. 나머지 검사 여덟(claude-review, e2e, e2e-widget, python, ticket, verify, visual, web)은 모두 SUCCESS였다.

CodeRabbit은 이 PR에서 아무 흔적도 남기지 않았다. 이슈 코멘트(`gh api repos/njh6803/agent-os/issues/444/comments`)에는 claude[bot]의 코멘트 하나와 내가 남긴 `@coderabbitai review`뿐이고, 인라인 리뷰와 리뷰 본문은 없으며(`gh api repos/njh6803/agent-os/pulls/444/comments`와 `…/pulls/444/reviews`가 모두 길이 0), 헤드의 check-runs(`gh api …/commits/4ebcbade…/check-runs`)에도 CodeRabbit 항목이 없다. 모두 이 세션이 명령을 쳐서 손으로 본 것이다. 앞선 PR #443의 일지(일지 2026-10-31-07 "이어받음 (PR 연 뒤)"에서 읽었다)는 같은 저장소에서 첫 요청에 "리뷰를 받지 않는다"는 안내만 달렸다가 한 번 더 요청해 인라인 리뷰를 받았다고 적는데, 이번에는 두 번째 요청을 하지 않았다. 왜 나타나지 않았는지는 재지 않았다. 별 10개 미만 안내가 이번에는 달리지 않은 것이 그 일지와 다르다.

claude-review는 이 PR에 낸 첫 리뷰(15:12Z 코멘트)에서 "지적 없음"이었다. 그래서 봇 회차에서 고칠 지적이 없다. CodeRabbit이 첫 회차를 내지 않았으므로 다음 푸시에서도 CodeRabbit의 회차는 첫 회차로 센다. 이 푸시(일지만 실은 커밋)로 도는 claude-review는 둘째 회차라 Critical·Major만 고친다.

뒤로 넘긴 봇 지적은 없다.

### 둘째 푸시의 봇 회차

`a3219b41`(일지와 대기열만 실은 커밋)을 푸시하고 `@coderabbitai review`를 다시 남겨 `wait_ci`를 띄우니 "끝: 모두 통과"(CodeRabbit SUCCESS 포함)였다. 이번에는 CodeRabbit이 요약 코멘트와 인라인 리뷰 하나를 달았고(`gh api …/issues/444/comments`와 `…/pulls/444/comments`가 길이 1을 냈다. 손으로 봤다), claude-review도 코멘트를 달았다. 앞의 "봇 회차"에서 CodeRabbit이 나타나지 않던 것은 두 번째 요청 뒤에야 풀렸다(#443과 같은 모양이다).

**회차.** CodeRabbit은 이 PR에 낸 첫 리뷰라 첫 회차이고 지적마다 고칠지를 판단한다. claude-review는 15:12Z 코멘트가 첫 회차(지적 없음), 이 코멘트가 둘째 회차라 Critical·Major만 고친다.

**고친 것.**
- [Minor, CodeRabbit] 티켓 06의 결정 칸 미리 알림이 모델 행의 `kind`·`name`·`enabled`만 보면 01이 읽지 못한 모델을 낼 때 쓰는 `manifest` 없는 표지 행을 꺼진 모델로 판정한다. `RunDecision.tsx`의 `disabledFor`(66~81행)를 읽어 보니 에이전트 행은 `"manifest" in row`를 거치지만 mcp 검사는 `enabled`만 본다. 모델 검사는 `manifest`가 있는 행만 대상으로 삼고 표지 행은 미리 알 수 없다고 적었다. 시험은 같은 파일의 기존 둘(목록 재조회 실패 803행, 에이전트 행이 표지 845행. `grep`으로 이름을 봤다)이 다른 갈래를 덮고 모델 행이 표지인 경우만 새로 필요하다고 적었다.

**보류한 것.** 셋 모두 둘째 회차의 claude-review 지적이라 PR 코멘트에 이유를 남긴다.
- [Minor] 티켓 04가 너무 크다(포트·인자·이름 검증·어댑터·실행마다 만들기·가짜 모델 170곳). 사용자가 여섯 장 분할을 골랐고(위 "분할"), 가짜 모델 정리는 포트가 바뀌는 04에서 함께 고치는 것으로 정했다(위 "셀프 리뷰"의 04 고침과 "티켓" 절, 이 세션은 04 본문을 다시 열어 대 보지 않았다. 어림이다). 일을 뒤로 넘기는 보류가 아니다.
- [Nit] 틈 설명이 여러 티켓에 되풀이된다. 티켓 세션이 자기 티켓과 명세만 읽으므로 티켓마다 있어야 한다는 판단(위 "셀프 리뷰"의 Duplicated Code 판단)을 그대로 둔다.
- [Nit] 티켓에 박은 수(03의 `main(` 호출 수, 04의 가짜 모델 170곳)를 다시 세게 한다는 문장. 두 티켓이 이미 "to-tickets 시점에"라고 시점을 박았다.

## 회고

후보 둘, 승인 1(대기열 555에 새 행), 기각 1, 넘김 0. 대기열 만료 2(192·340).

- **승인 (대기열 555, 1회차).** 티켓이 "모두"로 가리키는 대상을 grep으로 센 열거 하나로 닫아 그 grep에 걸리지 않는 모양을 놓쳤다. 사건은 이 일지의 "셀프 리뷰" Major(03이 `workspace` 픽스처만 들고 `tests/test_main.py`의 다른 루트 시험 넷을 빠뜨렸다)와 "PR 직전 리뷰" Minor(고친 열거가 `main(`·`_serving`·`_copy_repo_plugins`에 걸리지 않는 서브프로세스 시험 793행을 또 빠뜨렸다)다. 층은 판단 기준이다. 검사로 옮길 수 있는 모양이 아니라(어느 부류가 "모두"인지는 티켓마다 다르다) `CODING_STANDARDS.md`로 간다. 두 번 다 리뷰가 제 몫을 했으므로 4단계의 회차 셈에서는 빼고, "더하는 것"의 문턱(세 번째)을 지나기 전이라 반영하지 않고 회차를 세는 행으로 둔다. 되돌림은 PR 하나다. 행 찾기는 `uv run python tools/queue_open_rows.py --search to-tickets --search 열거 --search grep.*셌`로 했고, 출력에 머리가 보인 to-tickets 행(399·400·429·493)과 견주었다. 같은 to-tickets에서 난 열린 493은 티켓이 한 동작을 빼면서 남는 자리를 적지 않은 것이라 다른 처방이다. 대상 파일 목록에 같이 든 `CODING_STANDARDS.md`의 다른 열린 행 가운데 402·405·500·548·551은 머리 260자를 파이썬 한 줄로 찍어 읽었고(손으로 봤다) 모두 다른 일이다(부동소수 견줌, SIGINT 처리기, 도구 판에 기댄 시험, 판정 시험의 거르기, 체크박스 닫기). 552는 열지 않았다(대기열 머리의 요약으로는 조회 범위를 좁힌 일이다).
- **기각.** CodeRabbit이 나타나지 않아 `tools/wait_ci.py`가 30분을 기다린 일. 이미 있는 도구가 그 자리에서 `끝: 시간 초과 30분 … (나타나지 않음)`으로 알렸고, 이 세션은 그 줄대로 PR 코멘트·리뷰·check-runs를 직접 읽어 갈랐다. 더 일찍 포기하게 하는 것은 리뷰를 기다리는 시간을 줄이는 쪽이라 가드레일을 느슨하게 하는 넘김에 들고, 사건이 하나(손상 없음)라 올리지 않는다. 같은 파일의 열린 행 372·374·441·499는 모두 CodeRabbit이 흔적을 남긴 뒤의 판정이라 이 일과 다르다. 이 일이 되풀이되면 `tools/wait_ci.py`에 CodeRabbit의 부재를 부르는 끝 줄을 세는 행으로 올린다.
- **만료.** 192(`tools/run_checks.py`가 실패하면 곧바로 멈출지, 승인 2026-10-12·2026-10-17 메모)와 340(프로브 결과의 내용 해시 대조, 승인 2026-10-17)을 취소선과 `만료 2026-11-01`로 닫았다. 승인 칸의 가장 늦은 날짜가 14일을 넘었고 사람 몫도 회차 3 이상도 아니며, 이 워크트리와 `origin/main` 두 출력(`uv run python tools/queue_open_rows.py`와 `--ref origin/main`)에 모두 들었다.

## 다음

기능 model-plugin은 티켓 여섯이 `.scratch/model-plugin/issues/`에 있고 PR #444가 병합되면 `todo`로 시작한다. `next-session` 결정표로는 막힌 것이 없는 티켓 01과 02가 나란히 시작할 수 있다. 사용자가 고른 순서는 01·02를 함께 시작하고 03 → 04 → 05·06으로 가는 것이며 티켓마다 새 세션과 PR 하나씩이다.

- 01 `01-contract-model-manifest-fields`: sdk 매니페스트의 모델 칸, `openapi.json`, 생성 타입, 리터럴, 사진 정답, `sonnet` 픽스처 둘.
- 02 `02-manifest-errors-omit-input`: 매니페스트 거부 문구가 입력값을 되울리지 않는다. 01과 둘 다 `tests/adapters/test_filesystem.py`를 고치므로 뒤에 병합되는 쪽이 앞의 것을 합친다.
- 03은 01에, 04는 01·02·03에, 05와 06은 04에 막힌다. 05와 06은 `README.md`를 함께 고치지만 줄이 달라(05는 `serve` 줄, 06은 `disabled.toml` 줄) 나란히 돈다.
- 06은 ADR 0019 이력 한 줄을 사용자에게 승인받는다(사용자가 고른 답, "분할" 절).
- 워크트리에서 병합하므로 주 체크아웃은 당기지 않는다. 새 세션을 열면 `directive.md`대로 "확인할 선행 조건"에 `주 체크아웃 미갱신`을 적고, 그 세션이 워크트리에 들어가기 전에 `tidy-checkouts`로 당긴다.
- CodeRabbit이 이 PR에서 흔적을 남기지 않았다(위 "봇 회차"). 다음 PR에서 되풀이되는지 본다.

## 인계 (커밋 뒤, 둘째 봇 회차 반영)

커밋 `77ba4f14`(티켓 06 한 파일과 이 일지. 16줄 더함·2줄 지움)가 pre-commit을 지나 섰다(`checks` 묶음 모두 Passed. pytest 347.6s, web-verify 443.5s. 마크다운 표, 줄 구분 문자, 변이 표, 인용 대조(경고 없음), 커밋 메시지도 Passed이고 ruff 둘은 `.py`가 없어 Skipped다. 출력 파일을 읽었다). 이 커밋은 푸시하지 않았다. 앞 커밋 `a3219b41`은 푸시했고 그 푸시의 `wait_ci`는 "끝: 모두 통과"였다.

인계 계기(`hook_handoff`. 세션 컨텍스트 210,024 토큰, 경계 `커밋 뒤`)가 와서 `handoff.md`를 Read로 열었다. 인계하지 않는 때 다섯에 들지 않는다. 커밋은 성공했고, 요청 범위 "티켓까지"는 병합까지 이어지며, 이 세션의 지시문의 "이어받을 상태"는 `인계: PR 연 뒤`라 경계가 다르고, 이 일지에 `인계 못함` 줄이 없으며, `get_session`의 `self`에 `parentSessionId`가 없다. 그래서 넘긴다.

이 세션의 사용자 프롬프트는 위 "이어받은 세션 (봇 회차부터)"의 지시문 하나다. 이 세션이 번복하거나 고친 것은 위 "둘째 푸시의 봇 회차"의 고친 것(티켓 06의 표지 행)과 일지 안의 주장 근거 보강 둘(대기열 행 찾기를 열어 본 범위, 가짜 모델 정리의 근거를 어림으로 낮춘 것)이다. 이 세션의 제목은 `docs/model-plugin-tickets`이고 지시문을 낸 뒤 `docs/model-plugin-tickets (인계함)`으로 바꾼다. 백그라운드 작업은 없다(대기와 커밋이 끝났다).

새 세션이 할 일은 `77ba4f14`를 푸시하는 것부터다. 이 절은 커밋하지 않았으니 푸시 전에 일지만 한 커밋으로 싣는다(또는 푸시 뒤 다음 커밋에 싣는다). 푸시한 뒤 `@coderabbitai review` 코멘트와 `wait_ci`로 봇 회차를 잇는다. CodeRabbit은 이 푸시 뒤가 둘째 회차, claude-review는 셋째 회차라 둘 다 Critical·Major만 고친다. 둘째 푸시의 claude-review가 낸 보류 셋(티켓 04의 크기 Minor, 틈 설명 되풀이 Nit, 박은 수를 다시 세게 하는 문장 Nit)의 이유는 일지 "둘째 푸시의 봇 회차"에 적었으나 PR 코멘트에는 아직 남기지 않았다. 병합 전에 `gh pr comment`로 남긴다. 그 뒤 일지 3(회고와 "다음"은 끝났다. 위 "회고"와 "다음")과 `merge.md` 4(워크트리에서 병합할 때), 이어서 `next-session`이다. 다음 단계는 막힌 것이 없는 티켓 01과 02를 나란히 여는 것이다(구현, Sonnet 5.5 / high, 나란히 여는 2). 병합 보고에 CodeRabbit이 첫 요청에는 나타나지 않고 둘째 요청 뒤에 리뷰를 냈다는 한 줄을 넣는다.

지시문:

```
다음 작업: 기능 model-plugin. 모델 플러그인을 런타임이 읽게 하는 설계(ADR 0040)의 명세를 검토하고 티켓으로 쪼갠다(PR #444의 둘째 봇 회차 반영을 커밋했고 푸시부터)
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-tickets .scratch/model-plugin/spec.md
브랜치: docs/model-plugin-tickets
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: docs/journal/2026-10-31-08-model-plugin-tickets.md의 "이어받은 세션 (봇 회차부터)" 절부터 끝까지
이어받을 상태: 인계: 커밋 뒤 docs/journal/2026-10-31-08-model-plugin-tickets.md. PR #444(면제 PR, 티켓 없음)가 열려 있고 푸시된 헤드는 a3219b41이다. 로컬 커밋 77ba4f14(CodeRabbit 첫 회차의 Minor를 티켓 06에 반영)는 아직 푸시하지 않았고, 일지의 "인계 (커밋 뒤, 둘째 봇 회차 반영)" 절은 커밋하지 않았다. 남은 것: 푸시, @coderabbitai review 코멘트, wait_ci(CodeRabbit 둘째 회차·claude-review 셋째 회차라 Critical·Major만), 둘째 푸시의 claude-review 보류 셋을 이유와 함께 PR 코멘트로 남기기, merge.md 4(워크트리에서 병합), 그 뒤 next-session(다음은 티켓 01·02를 나란히, 구현). 회고와 "다음" 절은 일지에 끝나 있다. to-tickets와 셀프 리뷰, PR 직전 리뷰는 다시 돌지 않는다.
확인할 선행 조건: 없음
이번 요청 범위: 티켓까지
```

open-session을 부른다 2026-10-31T16:18:23Z

## 이어받은 세션 (푸시부터)

> 사용자: .claude/skills/to-tickets/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/model-plugin/spec.md / 다음 작업: 기능 model-plugin. … (PR #444의 둘째 봇 회차 반영을 커밋했고 푸시부터) / 다음 단계: PR 반영·병합 / 브랜치: docs/model-plugin-tickets / 모델: Sonnet 5.5 / high. 2의 잇는 지시문 / 이번 요청 범위: 티켓까지

첫 턴 훅대로 세션 제목을 `docs/model-plugin-tickets`로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다. `git worktree list`에서 이 브랜치가 `.claude/worktrees/model-plugin-tickets`에 체크아웃된 것을 보았고, HEAD는 `77ba4f14`다. to-tickets와 셀프 리뷰, PR 직전 리뷰는 다시 돌지 않았다. 앞 세션이 커밋하지 않고 둔 일지 수정(위 "봇 회차"와 "인계" 절)을 한 커밋으로 실어 `77ba4f14`와 함께 푸시한다.
