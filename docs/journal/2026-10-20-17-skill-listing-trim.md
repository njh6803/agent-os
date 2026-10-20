# 2026-10-20 (17) 스킬 목록 줄이기: slack만 끄고 계정에서 오는 스킬은 프로젝트 설정으로 끄지 못한다

주 체크아웃에서 시작해 워크트리 `skill-listing-trim`(브랜치 `chore/skill-listing-trim`)으로 들어간 앱 세션 `1d37e692`가
썼다. 셀프 리뷰 직전 경계에서 인계했다(아래 "인계").

## 사용자 프롬프트

> 사용자: 컨텍스트에 매 호출에 실려가는 스킬 목록을 줄일 수 없나? 프로젝트 레벨에서

> 사용자: (다른 세션의 출력 두 덩어리를 붙인 뒤) 위 내용 확인해줘

> 사용자: 그래서 최적화할 수 있어?

> 사용자: slack과 cowork를 끄고, anthropic-skills는 built-in-browser만 남긴 채 끄는 것이 먹히는지 새 세션으로 시험합니다. ADR 0033 이력 초안도 함께 씁니다.

> 사용자: 측정용 앱 세션을 워크트리에서 열어.

> 사용자: (이 세션이 앞서 쓴 "목록 예산을 낮추는 설정(skillListingBudgetFraction): ... diagnosing-bugs처럼 드물게 쓰지만 지침이 쓰라고 정해 둔 스킬의 설명이 먼저 빠질 수 있습니다." 문단을 붙인 뒤) 이것도 적용해보고 어떤 스킬의 설명이 빠지는지 체크해볼 수 없나?

> 사용자: 먹지 않는 설정은 빼고 slack만 끈 채 ADR에 기록해 주세요. 직접 끄는 방법은 없나? mcp 처럼 프로젝트설정에서 안쓰는 mcp를 끌 수 있잖아
> 그리고 예산 0.003은 예산을 0.005 등 수치를 올려가며 테스트해본거야?

## 한 것

- `.claude/settings.json`: `enabledPlugins`에 `"slack@claude-plugins-official": false` 하나만 더했다. 처음에 함께 더한
  `"cowork-plugin-management@synced": false`와 `skillOverrides`의 `anthropic-skills:*` 열여섯 줄은 새 앱 세션에서 먹지
  않아 사용자 지시대로 뺐다.
- ADR 0033 이력 2026-10-20과 본문 31행의 포인터. 처음 초안의 제목·결정("셋을 끈다")을 측정 뒤 "slack만 끄고 데스크톱
  앱이 계정에서 싣는 스킬은 프로젝트 설정으로 끄지 못한다고 적는다"로 고쳐 썼다. 아직 사용자 승인 전이다.
- 프로브 넷(`.scratch/token-usage/probes/`): `skill_listing_entries.py`(기록의 첫 목록), `skill_listing_cli.py`(CLI의
  `skillOverrides`, 측정 아님으로 끝났다), `skill_listing_budget.py`(예산 비율 다섯), `skill_listing_deny.py`(권한 거부
  규칙, 호출 대조 C 포함). README 행 넷. 결과는 그 행들과 ADR 이력의 "잰 것"에 있다.
- 측정용 앱 세션 `5682dc15`는 이 세션이 열지 못해(앱이 `start_session`을 두 턴 연속 "자동 이벤트"로 보고 거절했다)
  사용자가 워크트리 폴더에서 직접 열었다. 그 세션을 위해 잠시 넣은 설정 셋(`grilling` off, `frontend-design` false,
  예산 0.003)은 측정 뒤 되돌렸다.

## 번복하거나 고친 것

- ADR 이력의 결정을 "셋을 끈다"에서 "slack만 끈다"로 바꿨다(측정 결과와 사용자 지시).
- README 기준선의 세션 ID를 `09b52ad2`(다른 세션)에서 `1d37e692`로 고쳤다. 수는 다시 재도 같았다.
- 사용자에게 "예산을 받지 않는 내장 스킬 열둘"이라고 말했다가 다시 세어 열넷으로 고쳤다(ADR 초안도).
- ADR 이력이 든 일지 번호를 `2026-10-20-10`에서 이 파일의 `15`로 고쳤다.
- 세션 안에서 설정을 바꾼 뒤의 목록(03:02 UTC의 `slack`만 빠진 목록)을 처음에 "바로 먹었다"로 읽었다가, 그 뒤 변경에는
  목록이 다시 실리지 않아 근거에서 뺐다.

## 사용자 질문에 한 답 (인계 직전 이 세션의 마지막 메시지)

- 직접 끄는 길: 프로젝트 스킬·사용자 스킬은 `skillOverrides`, 마켓플레이스 플러그인은 `enabledPlugins`로 끈다(잰 대로
  먹는다). 권한 거부 규칙 `Skill(이름)`은 호출만 막고 목록에는 남는다(CLI로 쟀다). 데스크톱 앱이 계정에서 싣는 스킬과
  동기화된 플러그인은 프로젝트 설정으로 끄지 못했고, 문서가 적은 하나씩 끄는 길은 claude.ai 스킬 설정과 앱의
  Customize뿐이다(계정 전체). 재지 않은 후보는 `.claude/settings.local.json`의 `syncClaudeAiSkills: false`다.
- 예산 단계: 앱에서는 0.003 하나만 넣어 봤다. 값은 문맥 창(이 세션 입력이 36만 토큰을 넘었다)으로 어림해 골랐다. 단계를
  올려 본 것은 CLI(haiku, 27개)의 0.05·기본·0.005·0.0025·0.001이다. 문서도 가장 적게 부른 스킬의 설명부터 뺀다고 적는다.

## 셀프 리뷰에 넘길 요구 (명세 축)

요구: 위 프롬프트의 넷째(시험과 ADR 이력 초안), 여섯째(예산을 적용해 빠지는 설명 보기), 일곱째(먹지 않는 설정을 빼고
slack만 끈 채 ADR에 기록, 직접 끄는 길과 예산 단계 질문에 답).

리뷰어 참고(요구가 아니다 — 빠뜨렸다고 내지 마라): 위 "한 것"과 "번복하거나 고친 것".

## 인계

- 인계 경계: 셀프 리뷰 직전. 이 세션은 `/code-review`를 부른 직후 인계 계기를 받아 리뷰 단계를 밟지 않았다.
- 이 세션이 띄운 `tools/run_checks.py`는 인계로 멈춰 결과가 없다. 린트 둘(`ruff check .`, `ruff format --check .`)과
  `tools/check_md_tables.py`, `tools/check_adr_pointers.py`는 통과했다.
- 측정용 세션 `5682dc15`는 더 쓰지 않는다. 사용자가 원하면 보관한다.
- 이 세션의 지금 제목: `프로젝트 레벨 스킬 목록 최적화`(넘기기 전에 `chore/skill-listing-trim (인계함)`으로 바꿨다)
- 워크트리 잠금을 풀었다(`git worktree unlock C:/project/agent/.claude/worktrees/skill-listing-trim`).
- open-session을 부른다 2026-10-20T04:13:20Z

지시문:

다음 작업: 기능 skill-listing-trim. slack만 끄는 설정과 ADR 0033 이력 2026-10-20을 셀프 리뷰하고 승인받아 병합한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: docs/journal/2026-10-20-17-skill-listing-trim.md 의 "사용자 프롬프트" 절이 요청 원문이다. 셀프 리뷰(/code-review)부터 이어 ADR 승인, 커밋, PR, 병합까지 한다
브랜치: chore/skill-listing-trim
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-20-17-skill-listing-trim.md, docs/adr/0033-session-context-is-bounded-by-handoff-and-watched-by-a-ledger.md 의 이력 2026-10-20
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. docs/journal/2026-10-20-17-skill-listing-trim.md. ADR 이력은 셀프 리뷰를 반영한 뒤 사용자에게 보이고 승인받는다(아직 승인 전). run_checks.py는 결과 없이 멈췄다. 셀프 리뷰의 명세 축 요구와 참고는 그 일지의 "셀프 리뷰에 넘길 요구" 절이다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지

## 셀프 리뷰 (이어받은 앱 세션 `976e6e1b`)

> 사용자: docs/journal/2026-10-20-15-skill-listing-trim.md 의 "사용자 프롬프트" 절이 요청 원문이다. 셀프 리뷰(/code-review)부터 이어 ADR 승인, 커밋, PR, 병합까지 한다

범위: base `911babc0`, 추적 파일 셋, 커밋 0개, 미추적 다섯(프로브 넷과 이 일지). 표준 축은 `sonnet`·`high`, 명세 축은 메인
세션의 모델을 물려받았다. 두 브리프에 공식 문서 원문 발췌(2026-10-20에 `https://code.claude.com/docs/en/<쪽>.md`로 받은
plugins/loading, skills, settings, settings-reference, desktop, permissions)를 실었다.

### 표준 축 보고 (요지)

- [Major] ADR "고르지 않은 것" 첫 항목: settings-reference는 `.trash`로 옮기는 것을 "In user or managed settings"로
  한정한다. `.claude/settings.local.json`의 `false`가 다른 프로젝트에 닿는다는 결론이 서지 않는다.
- [Minor] "하나씩 끄는 길은 claude.ai 스킬 설정과 Customize뿐": 같은 문서의 "Manage those through `/plugin` instead"와
  관리형 키 `disableSideloadFlags`가 반례다.
- [Minor] `names` 57개, 19/38, 타임스탬프, `skillUsage` 횟수(354·294·6, 지금은 296·7)가 프로브 결과처럼 적혔다.
  `skill_listing_entries.py`는 `names`를 읽지 않는다. 기록의 목록 첨부는 넷이고 03:47에 다시 실렸다.
- [Minor] 소제목 "권한 거부 규칙도 목록에서 빼지 못한다"가 CLI의 프로젝트 스킬 둘로 잰 것을 앱과 동기화된 스킬까지 넓힌다.
- [Minor] 기점이 날짜다: 끄는 변경 PR #268은 2026-10-16 05:03:37 UTC 병합이라 10-16 보고서에 앞뒤가 섞인다.
- [Minor] 프로브 독스트링이 낡았다: `skill_listing_entries.py`가 뺀 설정을 있는 것처럼 쓰고, `skill_listing_cli.py`의
  기본 `--settings`는 이제 끄는 키를 0개 읽어 처음 실행을 재현하지 못한다.
- [Minor] "Workflow 도구가 함께 사라진다"는 원문에 없다.
- [Nit] 포인터가 거짓이 된 30행 `slack` 문장이 아니라 31행 뒤에 달렸다. 동기화 폴더는 셋이고 폴더마다 13개다. 이력 제목이
  cowork를 덮지 못한다. 인용이 줄바꿈으로 끊겼다.
- [냄새, 판단] 프로브 사이의 중복(`run_variant`, `start_entries`/`first_listing`, `claude --version`), `a, b` 이름.
- 맞다고 잰 것: 26,462자, 3,712자(14.0%), 13,793자(52.1%), 약 2%·약 6%, 일간 보고서의 세 중앙값, 17·13·4, 내장 열넷,
  예산 프로브의 11·13·27, 두 세션의 `skill_listing_entries.py` 출력.

### 명세 축 보고 (요지)

- 빠진 요구 없음, 요청하지 않은 변경 없음. 설정에 먹지 않은 키가 남지 않았고 수와 인용이 기록과 같다.
- [Major] 표준 축 첫 항목과 같은 지적. 요구 (다) "직접 끄는 방법은 없나?"의 답의 핵심이고, 일지의 "재지 않은 후보"와
  ADR의 결론을 하나로 맞춰야 한다.
- [Minor] "더 높은 출처가 켠 것은 아니다"는 `settings.local.json`만 뺐다. 앱이 동기화된 플러그인을 스스로 넘기는 길이
  남는다. 같은 까닭으로 "넷을 끄는 길은 문서에 없다"도 닫히지 않는다.
- [Minor] "Manage those through `/plugin` instead"의 길을 재지 않았다고 적지 않았다.
- [Minor] 살아 있는 독스트링에 뺀 설정이 남았다(표준 축과 같다). 끈 목록이 비었을 때 측정이 아니라고 세는 표지가 없다.
- [Nit] "Workflow 도구가 함께 사라진다"에 어림 표시가 없다. `skill_listing_budget.py` 3행의 인용 "목록 예산 낮추기"가 ADR
  항목 제목과 글자가 다르다.

### 판정

- 고친다: 두 축의 Major(휴지통 이동의 범위), 닫힌 주장 "뿐"·"문서에 없다"·"더 높은 출처"(일반 조항으로), 권한 거부의
  범위, 손으로 본 것의 표기와 `skillUsage`의 날짜, 03:47의 재첨부, 기점(PR #268), 프로브 독스트링과 `skill_listing_cli.py`의
  재현, Workflow 문장, 포인터 자리, 동기화 폴더 수, 끊긴 인용, `skill_listing_budget.py`의 인용.
- 고친 것: ADR 포인터를 30행 `slack` 문장 바로 뒤로 옮겼다. `skill_listing_entries.py`가 `names` 수, 설명·이름만 항목,
  첫 호출 뒤 첨부의 시각·글자 수·`names` 수를 세게 고쳐 두 기록을 다시 읽었다(앞의 수는 그대로, 새 수는 문서와 같다).
  `skill_listing_cli.py`의 기본 끄는 키를 측정 때 기록에서 꺼낸 열여섯(`MEASURED_OFF`)으로 두고 빈 목록을 측정 아님으로
  세게 고쳐 다시 돌렸다(같은 결과, 종료 1). `skill_listing_budget.py`의 인용, 두 독스트링, README 행 셋, ADR 이력의
  항목들을 고쳤다.
- PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 사실 문장, 원문 그대로):
  - ADR: "개인 파일(`.claude/settings.local.json`)의 `false`는 받아들여져, 이미 받은 동기화 스킬을 싣지 않고 새로
    내려받지도 않는다. 받은 스킬을 `~/.claude/skills/.trash/`로 옮긴다고 문서가 적은 것은 사용자 설정과 관리형 설정의
    `false`다(원문, settings-reference). 그래서 개인 파일에 두면 이 프로젝트 폴더의 세션에서만 빠질 것으로 본다(어림)."
  - ADR: "남은 해석은 앱이 이 플러그인을 스스로 넘기는 길이다. 문서는 데스크톱 앱이 claude.ai에서 동기화된 플러그인을
    스스로 관리한다고 적지만(원문, ... `disableSideloadFlags`), 어떤 플러그인 ID로 넘기는지는 적지 않았고 확인하지 못했다."
  - ADR: "문서가 적은 다른 끄는 길은 이 저장소가 커밋하는 프로젝트 설정으로 쓸 수 없거나, 재지 않았다." 와 그 뒤 `/plugin`,
    `"<이름>@inline": false`, `disableSideloadFlags`, Customize를 든 두 문장.
  - ADR: "`~/.claude/skills/synced/` 아래 폴더 셋에 같은 이름으로 13개씩"
  - ADR: "설정을 바꾼 세션(`1d37e692`)의 기록에는 첫 목록 뒤에 목록이 세 번 더 실렸다 ... 03:47에 다시 실린 목록도 같은
    22,749자, `names` 59개였다."
  - ADR: "플러그인 넷을 끄는 변경(PR #268, 2026-10-16 05:03 UTC 병합)의 앞뒤가 섞인 일간 보고서 2026-10-16(지역 시간대
    +09:00의 날짜)"
  - ADR: "`bug-perf-review`가 보안 축을 넘기는 내장 `/security-review`도 모델에게서 사라진다. 원문은 번들 스킬은 지우고
    `/init` 같은 내장 명령은 모델에게 숨긴다고 적는다."
  - ADR: "아래에서 "원문"이라 적은 공식 문서의 문장은 2026-10-20에 ...를 내려받아 손으로 대 봤다."
  - 프로브 독스트링: `skill_listing_entries.py`의 "두 수가 같으면 예산이 항목을 통째로 빼지 않은 것이라, 목록에 없는 항목은
    설정이 뺀 것으로 읽는다(공식 skills 문서는 목록이 늘 모든 스킬의 이름을 담는다고 적는다)."
- ADR 승인: 반영한 이력을 쉬운 말로 요약해 보이고 물었다("ADR 0033 이력 2026-10-20(slack만 끄고, 계정에서 오는 스킬은
  프로젝트 설정으로 끄지 못한다고 기록)을 이대로 승인할까요?").

  > 사용자: 승인 (Recommended) — 이력 끝에 '이 이력은 2026-10-20에 사용자가 승인했다'를 더하고 커밋·PR·병합까지 진행합니다. 새 세션부터 스킬 목록에서 slack:* 13개가 빠집니다.

- 승인 뒤 커밋 직전에 사용자가 예산을 고르지 않은 이유를 다시 물었다.

  > 사용자: (요약의 "고르지 않은 것: 목록 예산을 낮추면 ... 설명이 먼저 빠져서 고르지 않았습니다" 문단을 붙인 뒤) 근데 이거 알아서 조정되지않아? 안쓰는애들 위주로 빠지도록

  > 사용자: 근데 tdd, retro나 스킬안에 다른 스킬을 부르게 명시 되어있고 지침으로써 워크플로우가 정해져있는데

  0.003에서 설명이 빠진 스킬마다 이름을 부르는 자리를 `CLAUDE.md`, `.claude/skills`, `.claude/agents`, `.claude/rules`,
  `tools/hook_*.py`, `docs/constitution/operations.md`에서 스크래치 스크립트로 찾아 손으로 봤다. `diagnosing-bugs`(작업
  규약 6), `tdd`(`implement`), `domain-modeling`(`grill-with-docs`), `writing-for-agents`(`retro` 1단계)는 이름으로
  불린다. `grill-with-docs`는 `next-session`의 시작 프롬프트에, `retro`는 `hook_journal_retro`의 계기에 이름이 든다.
  `git-*`는 프로젝트가 아니라 사용자 레벨 스킬(`~/.claude/skills`)이고, `git-commit`을 뺀 넷은 `next-session`과 운영
  문서가 슬래시 명령으로 든다. 그래서 ADR의 이유("`diagnosing-bugs`
  처럼 `CLAUDE.md`가 부르라고 정한 스킬의 설명을 잃는다")가 틀렸다. 잃는 것은 설명에만 적힌 계기(사용자의 말에서
  시작하는 계기, `retro` 밖의 `writing-for-agents`, `built-in-browser`의 먼저 읽기)다.

  > 사용자: 이번 PR은 slack만 끄는 그대로 두고, ADR의 '고르지 않은 것' 이유를 설명에만 있는 계기로 좁혀 고친 뒤 다시 보여 줘. 중간 예산값 측정과 채택은 병합 뒤 별도 세션에서 하자.

  ADR 이력의 "스킬 목록 예산을 낮춘다" 항목에서 틀린 이유를 빼고, 이름으로 불리는 길과 설명에만 적힌 계기를 갈라
  적었다. 이 문장들도 PR 직전 리뷰에 밀 주장이다. 그 대조에서 `git-*`가 사용자 레벨 스킬인 것이 나와,
  `skill_listing_entries.py`가 접두 없는 항목을 "프로젝트·내장"으로 부르던 이름을 "프로젝트·사용자·내장"으로 고치고
  ADR 이력 머리의 출처별 수와 프로브 README 행도 맞췄다. 고친 문단을 보여 주고 다시 물었다.

  > 사용자: 승인 (Recommended) — 이 문단으로 ADR 이력을 확정합니다. 이어서 커밋, PR 직전 리뷰, PR, 병합까지 진행합니다.

  ADR 끝의 승인 줄("이 이력은 2026-10-20에 사용자가 승인했다.")은 같은 날의 재승인이라 그대로 둔다.
- 남긴다: 이력 제목(cowork도 데스크톱 앱이 계정에서 싣는 플러그인이라 제목이 덮는다고 본다. 바꾸면 포인터와 함께 바뀌어
  얻는 것이 없다). 프로브 사이의 중복과 `a, b` 이름(한 번 쓰고 남기는 프로브라, 공통 모듈을 두면 한 프로브를 고칠 때 다른
  프로브의 옛 결과를 재현하는 길까지 함께 바뀐다. 판단이다).

## 커밋과 PR 직전 리뷰

- 커밋 `89240c4d`. pre-commit이 모두 통과했다(검사 러너 523초: pytest 522.8초, web-verify 291.2초, run-hooks
  133.6초, pyright 35.2초. ruff 둘, 표, 줄 구분 문자, 변이 표, 커밋 메시지 통과. 카나리아 명세와 헌법 판은 대상 파일이
  없어 Skipped). 인용 대조 경고 6건은 모두 저장소 밖 원문이나 기록이다. ADR 227행은 프로브 출력(표지
  `blocked by permission rules`가 그 일부), 283행은 `~/.claude/skills/synced/*/built-in-browser/SKILL.md` 셋에 글자 그대로
  있고(Grep), 일지 넷은 옛 문장과 리뷰 보고를 옮긴 기록이다.
- `git fetch origin` 뒤 `git merge origin/main`(병합 커밋 `a3a8864f`, 충돌 없음). main이 새로 바꾼 파일과 이 브랜치의
  파일은 겹치지 않았다.
- CodeRabbit CLI는 `coderabbit auth status`가 `Seat: not assigned`라 대체 둘을 나란히 돌렸다.
- `/security-review`: 신뢰도 8 이상 0건. 식별 서브태스크가 낸 후보가 없어 거짓 양성 거르기는 돌지 않았다.
- `bug-perf-review`: 유효 4(Minor 3, Nit 1), 보류 6, 오탐 5. 도구 호출 40에서 멈춰 보류 일부를 닫지 못했다.
  - 고친 것:
    - `skill_listing_entries.py`가 첫 첨부의 `names` 없음을 `names 0개`로 합쳐 0으로 끝나던 것을, `names 없는 첨부 N개`로
      찍고 측정 아님으로 세게 했다. 가짜 기록 넷(목록, 키 없음, 문자열, 둘 가운데 하나만 없음)으로 rc 0·1·1·1을 손으로
      봤고, 5682dc15 기록의 출력은 그대로였다.
    - `skill_listing_cli.py`가 A에 `CONTROL`이 없으면 B의 대조를 건너뛰던 것을 측정 아님으로 세게 했다. `run_variant`와
      `shutil.which`를 가짜로 바꿔 네 갈래(둘 다 있음, A에 없음, B에서 빠짐, A에 출처 없음)로 rc 0·1·1·1을 손으로 봤다.
      고치기 전에는 둘째가 0이었다.
    - `skill_listing_entries.py` 독스트링에 첫 목록은 줄마다 줄바꿈을 더한 값(`token_report`와 같다)이고 뒤 첨부는 본문
      길이 그대로라 1자 적게 찍힌다고 적었다(Nit).
    - ADR "스킬 목록 예산을 낮춘다" 항목에 `skillOverrides`의 `"name-only"` 길을 더했다(문서 침묵).
    - 프로브 README의 두 행(entries, cli)에 새 측정 아님 조건을 맞췄다.
  - 보류를 본 세션이 닫은 것: 이름으로 부르는 자리(위 대조와 같은 grep으로 줄을 봤다), `built-in-browser` 인용 끝말(Grep
    3건), 압축 03:08(기록의 `compact_boundary`가 `2026-10-20T03:08:13Z`), 일간 보고서의 중앙값 셋(주 체크아웃
    `.scratch/token-report/daily/2026-10-16·17·19.md`의 "9. 시작 컨텍스트" 표, 사람이 연 세션만), 프로브 독스트링의
    skills 문서 문장(skills.md "Skill descriptions are cut short" 절의 "The listing always contains every skill name"),
    프로브가 남긴 haiku 세션(같은 보고서가 헤드리스 세션을 중앙값에서 뺀다).
  - PR 봇에 밀 주장(이번 반영으로 새로 쓴 문장, 원문 그대로):
    - ADR: "예산을 낮추는 대신 고른 항목만 `skillOverrides`의 `"name-only"`로 설명 없이 싣는 길도 문서에 있다(원문, skills).
      `anthropic-skills:*`에는 같은 키의 `"off"`가 먹지 않아 `"name-only"`도 먹지 않을 것으로 보고(어림) 재지 않았다."
    - ADR: "프로젝트·사용자 스킬 몇을 `"name-only"`로 두는 길도 그 측정에서 함께 견준다."
    - 프로브 독스트링: "첫 목록의 글자 수는 `token_report`처럼 줄마다 줄바꿈 하나를 더한 값이고, 뒤 첨부의 글자 수는 본문
      길이 그대로라 같은 목록이 1자 적게 찍힌다."
