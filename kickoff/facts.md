# 부록 C. 플랜·요금·플랫폼 사실과 확인일

바뀌는 사실이다. 날짜가 없는 값은 추정으로 읽고, 다른 프로젝트에서 쓸 때 공급자 페이지에서 다시 확인해 날짜를 갱신한다.

| 사실 | 확인일 | 어디서 |
|---|---|---|
| GitHub Actions 무료 분량은 계정 단위 월 2,000분. 다른 비공개 저장소가 써 버리면 잡이 시작조차 안 된다 | 2026-09-20 | agent-os PR #10, ADR 0005 |
| 무료 플랜 비공개 저장소는 보호 브랜치·룰셋이 403 | 2026-09-20 | agent-os, ADR 0005 |
| CodeRabbit CLI 상한은 개발자당 시간당 3회 롤링 윈도. `--usage`는 시간당 잔량을 보여주지 않는다 | 2026-09-21 | 공식 요금제 문서 rate limits 표 |
| CodeRabbit OSS PR 리뷰는 별 수에 따라 시간당 1~10회. 별 10개 미만이면 자동 리뷰 없음, `@coderabbitai review`로 부른다 | 2026-09-21·22 | agent-os PR #12·#43 |
| CodeRabbit CLI 좌석 배정에는 활성 유료 구독이 필요하다. 무료면 `Seat: not assigned`로 연결 단계에서 끝난다 | 2026-09-23 | 공식 문서 management/seat-assignment, agent-os 실측 |
| Claude Code Review 액션은 자기 워크플로 파일이 기본 브랜치와 다르면 건너뛴다. 다른 워크플로 파일은 무관 | 2026-09-20, 정정 2026-09-28 | agent-os PR #3·#6(건너뜀)·#43(돌았다) |
| Claude Code 스킬 우선순위는 enterprise > personal > project | 2026-09-19 | 공식 문서 |
| Claude Code의 `@` 임포트는 CLAUDE.md 어디에서든 임포트다. 코드 스팬과 펜스는 제외 | 2026-09-28 | 공식 문서 memory 페이지 |
| 앱 딥링크가 첫 줄의 슬래시를 전각으로 바꾼다. 딥링크 URL은 8000자 안 | 2026-09-24 | agent-os PR #50·#65 |
| `paths` 있는 rules와 하위 디렉터리의 CLAUDE.md는 Read 도구로 그 경로의 파일을 읽을 때 실린다. Bash(`cat`·`sed`)·Grep·Glob·Write(새 파일)로는 안 실린다. cwd가 그 디렉터리면 하위 CLAUDE.md는 시작 시 실린다. `paths` glob은 cwd가 아니라 프로젝트 루트 기준이다 | 2026-09-29 | 공식 memory 문서, agent-os `claude -p` 2.1.281 실측(InstructionsLoaded 훅 로그, `.scratch/harness/probes/instruction_loading/`)과 주 세션 재현, anthropics/claude-code #90450(auto mode의 Bash 우선 지침이 이것을 조용히 끈다, 열림) |
| `@` 임포트는 줄 머리나 공백 뒤의 경로이고, 굵게·링크 글자·인라인 태그의 머리(`**@x.md**`)에 붙은 것도 실렸다. 괄호로 감싸거나 조사·끝 마침표가 붙은 것은 안 실렸다. `#` 뒤는 잘리고, 한글 이름의 파일은 실렸다. 펜스·코드 스팬·들여쓴 코드 블록·`<div>` 같은 HTML 블록 안과, 닫힌 HTML 주석 안의 것은 블록이든 문단 속이든 안 실렸다(블록 주석은 루트 CLAUDE.md·rules·임포트된 파일에서, 나머지는 임포트된 파일에서 쟀다). 상대 경로는 임포트를 담은 파일 기준이고 최대 네 단계 재귀다. rules 파일과 하위 CLAUDE.md 안의 `@`도 따라간다 | 2026-09-29 | 공식 memory 문서, agent-os 실측(`.scratch/harness/probes/instruction_loading/`, `import_comments/`) |
| `.claude/rules/`는 하위 폴더까지 재귀로 찾는다. `paths`는 YAML 목록이나 쉼표로 가른 문자열이다. 공식 문서는 YAML이 깨지면 `paths` 없이 매 세션 싣는다고 하지만, 2.1.281에서 닫히지 않은 흐름 목록·따옴표와 `paths: sub/**: x: y`는 시작 때도 그 경로를 Read할 때도 안 실렸다(조용히 죽는다). 다른 키만 깨진 것, 탭 들여쓰기, 겹친 키(뒤의 값)는 실렸다 | 2026-09-29 | 공식 memory 문서, agent-os 실측(`.scratch/harness/probes/import_comments/`) |
| 하위 디렉터리에서 띄운 세션은 조상의 CLAUDE.md와 rules는 싣지만 조상의 `.claude/settings.json`(훅·권한)은 읽지 않는다 | 2026-09-29 | 공식 large-codebases 문서, agent-os 실측 |
| AGENTS.md는 2.1.277부터 직접 읽힌다. 단 작업 디렉터리나 조상에 CLAUDE.md·CLAUDE.local.md가 있으면 읽히지 않는다(설정으로 바꾼다). 실린 CLAUDE.md와 rules는 `/context`의 Memory files로 보고(`/memory`는 위치 목록이라 없는 파일도 나열한다), 직접 읽힌 AGENTS.md는 `/memory`로 본다 | 2026-09-29 | 공식 memory 문서, agent-os 실측 |
| 권한 규칙은 Claude가 쓴 호출의 모양만 맞춘다(보안 경계가 아니다). `./`는 세션 cwd 기준, `//`는 파일시스템 루트 기준이다. Read deny는 PowerShell 도구에 걸리지 않아(Read 규칙만 두고 `Get-Content`가 읽혔다) `PowerShell(Get-Content *.env*)` 같은 모양 규칙이 따로 든다. 별칭(`gc`·`cat`·`type`·`sls`)은 정규화되어 같은 규칙에 걸린다. `[IO.File]` 같은 읽기는 그래도 지나간다 | 2026-09-29 | 공식 permissions·large-codebases 문서, agent-os 실측(`.scratch/harness/probes/env_deny_probe.md`) |
| PreToolUse 훅의 종료 코드 2는 그 호출을 막는다. 그 밖의 비0과 `timeout` 초과는 지나간다(fail-open). 효과는 이벤트마다 다르다(PostToolUse는 2로도 이미 실행된 호출을 되돌리지 못한다). `python <없는 경로>` 꼴 등록은 파이썬이 2로 끝나 그 매처의 모든 호출을 막는다 | 2026-09-29 | 공식 hooks 문서, agent-os 실측 |
| 플러그인 스킬은 `skillOverrides`로 끌 수 없다(`/plugin`으로). 스킬 description은 한 항목 1,536자에서 잘린다. MCP 도구 스키마는 지연 로딩이 기본이라 매 세션 도구 이름과 서버 지침만 실린다. `MEMORY.md`는 앞 200줄 또는 25KB가 시작 시 실린다. `/context`는 2.1.283부터 MCP 서버 지침을 센다(그 전 판의 값은 그만큼 적다) | 2026-09-29 | 공식 skills·costs·memory 문서, CHANGELOG 2.1.283, agent-os `/context` 실측(MCP 지연분 125.3k는 맥락 밖) |
| 샌드박스(OS 수준 격리)는 macOS·Linux·WSL2에서만 된다. 네이티브 Windows는 지원하지 않는다 | 2026-09-29 | 공식 sandboxing 문서 |
