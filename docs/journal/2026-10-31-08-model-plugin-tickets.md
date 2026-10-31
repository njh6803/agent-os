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
