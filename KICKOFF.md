# 새 프로젝트 첫날 킥오프 런북

원본은 이 파일(`C:/project/agent/KICKOFF.md`, 원격 `github.com/njh6803/agent-os`)이다. 새 프로젝트는 그 저장소를 clone해 두고 이 파일과 `kickoff/`(템플릿·부록)와 7단계의 복사 목록을 상대 경로로 가져와 시작하고, 런북을 고칠 일이 생기면 여기를 고친 뒤 복사본에 반영한다. 아래에서 "런북 저장소"는 그 clone이다. **이 판을 처음부터 끝까지 실행한 것은 첫 프로젝트(agent-os, 2026-09-19) 한 번이고 그 뒤의 수정은 실행으로 검증되지 않았다.** 두 번째 프로젝트의 실행이 이 판의 검증이다. 어긋나면 내 실수로 읽지 말고 이 원본을 고친다.

결정 기준일 2026-09-19, 마지막 갱신 2026-09-28. 결정: mattpocock 스킬 유지, superpowers 비활성, 교정 루프는 retro 스킬의 계기 자동 회고(10단계), 지침은 한국어. 스킬(`.claude/skills/`)과 교정 루프 문단(`CLAUDE.md`)은 모두 프로젝트 레벨에 둔다. 전역에는 프로젝트와 무관한 개인 워크플로 스킬(git-*, jira-*)만 남기고, 프로젝트가 관리하는 스킬의 전역 사본은 두지 않는다.

전제 셋. 무엇을 만들지 안다(모르면 `/grill-me`로 브레인스토밍부터 하고 이 런북은 그 뒤에 시작한다). 원격은 GitHub이고 `gh`가 있다(GitLab이면 1·8·9단계의 `gh` 명령, `tools/hook_pr_next_session.py`의 정규식과 MCP 도구 이름, 전역 `git-pr*` 스킬, Claude Code Review 워크플로를 대체해야 한다 — 이 런북은 그 길을 적지 않는다). 하네스 런타임은 파이썬이다(훅·검사·pre-commit·변이 도구가 파이썬 스크립트다. 파이썬 프로젝트가 아니어도 개발 도구로 파이썬 하나와 uv를 두면 그대로 돈다. 7단계).

## 순서의 원칙: 되돌리기 비용이 큰 것부터

세팅 순서를 정하는 기준은 중요도가 아니라 나중에 바꿀 때 드는 비용이다(ai-agent-platform 세팅 플레이북).

| 결정 | 나중에 바꾸면 | 그래서 |
|---|---|---|
| 아키텍처 스타일, 핵심 원칙 | 전부 다시 쓴다 | 첫날(5단계) |
| 저장소·워크스페이스 구조 | 설정 파일 전부 | 첫날(7단계) |
| 계약 형식(디스크 형식, 식별자, 에러 봉투) | 소비자 전부의 타입 | 첫 기능 전 |
| 개발 파이프라인 | 습관을 다시 들인다 | 기능 하나로 검증한 뒤 |
| 기능 | 그 기능만 | 언제든 |

되돌리기 비용은 무엇이 첫날인지를 정하고, 첫날 안의 순서는 도구 의존이 정한다 — setup 스킬이 CLAUDE.md를 고치니 3단계가 4단계 앞이고, `@` 임포트 대상은 5단계가, 검증 명령과 훅 등록은 7단계가 만드니 3단계는 그 둘을 기다린다.

세팅이 끝났다는 신호는 리듬이 생기는 것이다. 티켓 → 명세 → 구현 → 리뷰 → 병합 → 회고가 매 기능마다 같은 모양으로 반복되면 끝난 것이다.

## 어디에 무엇이 사는가

| 위치 | 내용 | 이유 |
|---|---|---|
| `~/.claude/CLAUDE.md` (전역. Windows는 `C:/Users/<user>/.claude/CLAUDE.md`) | 비워 둔다 | 교정 루프 문단은 `CODING_STANDARDS.md`와 `/retro`를 가리키므로, 그것들이 없는 다른 프로젝트에 새면 안 된다 |
| `~/.claude/skills/` (전역) | 프로젝트와 무관한 개인 워크플로 스킬만(git-*, jira-*). 프로젝트가 안 쓰는 것은 그 프로젝트의 `skillOverrides`로 끈다 | 전역은 같은 이름의 프로젝트 스킬을 이기므로, 프로젝트가 관리하는 스킬(grilling 등)의 전역 사본을 두면 `npx skills update` 뒤 낡은 전역이 조용히 이긴다 |
| `.claude/skills/` (프로젝트) | mattpocock 엔지니어링 스킬 전부 + grill-me | git에 커밋, 프로젝트마다 버전 고정. `skills-lock.json`이 출처와 해시를 기록 |
| `.claude/settings.json` (프로젝트) | `enabledPlugins`(LSP 등 프로젝트 플러그인), `skillOverrides`(이 프로젝트가 안 쓰는 전역 스킬을 `"off"`), `hooks`(훅의 등록. 훅 파일만 복사하면 아무것도 발동하지 않는다), `permissions.deny`(`.env`의 Read·Edit 거부) | 저장소와 함께 간다 |
| `CLAUDE.md` (프로젝트) | 다른 파일을 가리키는 포인터, 검증 명령, 교정 루프 문단 | 규칙은 여기 쓰지 않는다. 교정 루프는 규칙이 아니라 규칙을 만드는 절차다 |
| `docs/constitution/` | 헌법. `principles.md`(원칙·거버넌스, 임포트), `tech.md`(스택), `operations.md`(검증·운영). 디렉터리별 규칙은 `.claude/rules/*.md`+`paths` | 프로젝트당 한 번 |
| `CODING_STANDARDS.md` | 검사로 못 잡는 판단 기준 | code-review 스킬이 읽음 |
| `CONTEXT.md`, `docs/adr/` | 용어집, 결정 기록 | domain-modeling이 씀 |
| `docs/agents/` | 이슈 트래커 규칙, 도메인 문서 위치 | setup 스킬이 씀 |
| `.github/` | PR 템플릿, CI 워크플로, Claude Code Review 워크플로 | 첫날. 런북 저장소에서 복사해 검증 명령만 바꾼다 |
| `.coderabbit.yaml` | CodeRabbit 설정. 층별 path_instructions, 린터 끔, 제외는 생성물·락파일·남이 쓴 스킬 사본만 | PR 봇과 로컬 CLI가 같은 파일을 읽는다. PR 자동 리뷰는 공개 저장소나 유료일 때만 켠다(2026-09-20 실측) |
| `.claude/agents/` | 프로젝트 서브에이전트. coderabbit-review(CLI 실행과 트리아지), spec-reviewer(명세 검토). 둘 다 Edit·Write 없음 | 스킬은 절차, 서브에이전트는 격리된 컨텍스트에서 도구를 돌리고 보고만 한다 |
| `tools/` | 배포되지 않는 저장소 유틸. 훅(`hook_*.py`)과 그 실행 래퍼(`launch_hook.py`), 검사(`check_*.py`), 훅 러너(`run_hooks.py`와 페이로드 표), 변이 도구, Actions 실행 요약 | 훅과 CI, 그리고 리뷰 봇 판정이 부른다. 규약은 `.claude/rules/tools.md` |
| `docs/journal/` | 진행 일지. 단계별 사실, 사용자 프롬프트 원문, 갈린 곳과 번복 | 세션을 넘어 이어가고 `/retro`의 입력 |
| `.scratch/` | 로컬 이슈 트래커(명세, 티켓, 프로브)와 회고 대기열(`retro-queue.md`) | 원격 트래커를 쓰지 않는 프로젝트의 작업 기록. 커밋한다 |

주의: 같은 이름의 스킬이 전역과 프로젝트에 둘 다 있으면 전역이 이긴다(공식 문서: enterprise > personal > project). 그래서 프로젝트가 관리하는 스킬의 전역 사본은 두지 않는다. 전역 스킬을 `skillOverrides`로 끄면 같은 이름의 프로젝트 스킬이 살아나는지는 문서에 없으므로, 중복은 끄지 말고 옮긴다.

## 이 런북을 실행하는 에이전트에게

첫 프로젝트(agent, 2026-09-19~20)에서 에이전트가 실제로 저지른 것에서 나온 규칙이다. 1~6은 세팅 중, 7~9는 원격과 봇을 붙일 때.

1. **사용자가 경험에서 제안한 것은 판단해서 자리에 넣는다.** "그 내용이 어딘가에 있다"는 "행동이 일어나는 자리에 있다"가 아니다. 지침의 값은 로드 시점이 정한다. 3단계의 표로 자리를 정해 넣고, 거부는 이유를 일지에 남긴다. "이미 있음", "나중에"로 넘기지 않는다.
2. **옆 프로젝트의 원재료를 가리키면 원문을 읽는다.** 요약하지 말고 항목별로 채택·수정 채택·거부를 근거와 함께 보고한 뒤, 채택한 것은 그 자리에서 넣는다. 원재료: `ai-agent-platform/docs/setup-playbook.md`, `docs/setup-prompts/01~09`, `AGENTS.md`, `.claude/rules/`.
3. **결정은 사용자 것, 사실 조사는 에이전트 것.** 사용자에게 파일을 열어 확인하라고 하지 않는다. 서브에이전트로 조사하고, 결정만 번호 붙여 묻는다.
4. **일지를 1단계에서 만들고 매 단계 적는다.** 사용자 프롬프트 원문(결정·방향 전환·설계 질문), 벗어난 점, 세션 끝에 "추천과 결정이 갈린 곳"과 "에이전트가 번복하거나 고친 것". 이 두 절이 `/retro`의 입력이다.
5. **하네스를 바꾸면 실행으로 확인하고, 새 검사는 변이로 빨강을 본다.** 파일이 그럴듯한 것은 확인이 아니다. 스크립트를 셸 체인으로 돌릴 때는 실패 시 멈추게 한다(`|| exit 1`). 커밋 전에 `git show --stat`으로 내용을 본다.
6. **한 파일에 모으지 않는다.** 헌법은 처음부터 셋(원칙·스택·운영), 디렉터리 규칙은 `.claude/rules/`+`paths`, 트리는 README, 미래 배치와 범위는 `.scratch/plan.md`. `@` 임포트는 원칙 하나뿐.
7. **옆 프로젝트의 구성을 옮기기 전에 이 계정·플랜에서 실측한다.** CodeRabbit PR 리뷰는 무료 플랜의 비공개 저장소에서 요약만 남기고 초록이었고, 보호 브랜치는 403이었다. 플랜 차이 없이 옮겨 PR 둘(#3·#4)로 되돌렸다. 도구를 켜기 전에 요금·플랜 조건을 보고, 문서에 없으면 작은 PR 하나로 실측한 뒤 채택한다. 일지 "CodeRabbit App".
8. **결정을 바꾸면 옛 표현을 grep해 잔존을 0으로 만든다.** "원격·PR은 첫날부터"로 바꾸고도 `skillOverrides`의 git-pr 셋을 끈 채 두었다. 규약 4가 있는데도 놓쳤다. 옛 낱말(도구 이름, 개수, 담당)을 저장소 전체에서 찾고 셀프 리뷰에도 같은 grep을 시킨다. 규약 4에 넣었다. 일지 "번복".
9. **확인 안 한 사실은 추정이라고 적는다.** "설치하면 14일 체험이 켜진다"를 요금 페이지 문구에서 추정해 사실처럼 썼고 실제는 Free였다. 실측한 것에만 "실측"을 붙인다. 일지 "CodeRabbit App".

## 0단계. 한 번만 하는 전역 준비

프로젝트마다 반복하지 않는다. 기계마다 한 번이다 — agent-os의 기계에서는 2026-09-19에 했고, 새 기계에서만 다시 한다.

1. superpowers 비활성화 (되돌리려면 `enable`).

```bash
claude plugin disable superpowers@claude-plugins-official
```

2. 전역 스킬 정리. grill-with-docs, domain-modeling, grilling, grill-me는 프로젝트 레벨로 옮길 것이므로 전역 복사본을 백업 폴더로 이동한다. git-*, jira-* 같은 개인 워크플로 스킬은 남긴다.

```bash
mkdir -p ~/.claude/skills-backup && mv ~/.claude/skills/grill-with-docs ~/.claude/skills/domain-modeling ~/.claude/skills/grilling ~/.claude/skills/grill-me ~/.claude/skills-backup/
```

전역 `~/.claude/CLAUDE.md`는 비워 둔다. 교정 루프 문단은 3단계에서 프로젝트 `CLAUDE.md`에 넣는다.

## 1단계. 저장소 만들기

```bash
mkdir my-project && cd my-project && git init && mkdir docs
```

`.gitignore`는 스캐폴딩 때 프레임워크가 만들거나 에이전트에게 맡긴다. 이 디렉터리에서 Claude Code를 연다.

원격을 만들기 전에 플랜을 본다. 8단계의 보호 브랜치와 봇 경로가 여기서 갈린다.

```bash
gh api user --jq .plan.name
```

Billing & plans의 Included usage도 본다. Actions 무료 분량은 계정 단위 월 2,000분이라 다른 비공개 저장소가 써 버리면 이 저장소의 잡이 시작조차 안 되고, CI가 게이트라 병합도 막힌다(agent-os PR #10 실측. 주석은 결제 실패를 말하지만 원인은 분량 소진이었다). 공개 저장소는 무제한이다. Claude 리뷰 한 번이 1~10분을 쓴다. `free`이고 비공개로 갈 거면 보호 브랜치와 룰셋은 403이고 CodeRabbit PR 리뷰는 요약만 남는다. 처음부터 `/git-pr-merge`를 게이트로, CodeRabbit은 CLI-only로 간다. 공개 저장소면 둘 다 무료로 풀린다. agent-os는 이것을 PR을 열고 나서 알아 PR 넷을 되돌리는 데 썼다.

`docs/journal/<날짜>-kickoff.md`를 지금 만든다. 머리말에 기록 규칙을 적는다. 결정·방향 전환·설계 질문에 해당하는 사용자 프롬프트는 `> 사용자:` 인용으로 원문 그대로(오타도 고치지 않는다), 단순 조작 지시는 제외, 에이전트의 말은 옮기지 않고 세션 끝에 "추천과 결정이 갈린 곳"과 "에이전트가 번복하거나 고친 것"만 한 줄씩. 병렬 티켓 세션은 `docs/journal/<날짜>-<티켓슬러그>.md`.

## 2단계. 스킬을 프로젝트 레벨로 설치

설치기는 기본이 프로젝트 레벨(`.claude/skills/`)이다. Windows에서는 심링크 대신 복사(`--copy`)를 쓴다. 이름은 공백으로 나열하고, 오류가 나면 `-s`를 스킬마다 반복한다.

```bash
npx skills@latest add mattpocock/skills -a claude-code --copy -y -s grill-me grill-with-docs grilling domain-modeling setup-matt-pocock-skills to-spec to-tickets implement tdd code-review diagnosing-bugs writing-for-agents retro
```

`--copy`는 Windows 전용이다(심링크 대신 복사). 다른 OS는 빼도 된다. `tdd`가 부르는 `codebase-design` 스킬은 이 목록에 없다 — 시임 어휘가 필요하면 함께 설치하고, 아니면 `tdd` 사본에서 그 문장을 지우고 센티널을 붙인다(agent-os는 아직 어느 쪽도 하지 않았다).

| 스킬 | 역할 | 단계 |
|---|---|---|
| setup-matt-pocock-skills | 이슈 트래커, 라벨, 문서 위치 설정 | 4 |
| grill-with-docs, grilling, domain-modeling | 기능 설계 인터뷰 + 용어집/ADR 기록 | 9 |
| to-spec | 대화를 명세로 만들어 트래커에 발행 | 9 |
| to-tickets | 명세를 수직 슬라이스 티켓으로 분해 | 9 |
| implement, tdd | 티켓 구현, 테스트 먼저 | 9 |
| code-review | 표준 축과 명세 축을 병렬 서브에이전트로 리뷰 | 9 |
| diagnosing-bugs | 버그 진단 루프 | 수시 |
| writing-for-agents | 에이전트용 문서 작성 스타일. retro가 호출 | 10 |
| retro | 세션 회고, 하네스 개선 후보 제안 | 10 |

확인과 갱신:

```bash
npx skills ls
```

```bash
npx skills update -p
```

grill-me도 설치기에 있다(`skills/productivity/grill-me`, 2026-04부터). agent-os는 "본인 스킬"로 잘못 알고 백업 폴더에서 복사해 락 밖에 두었고, 그래서 갱신도 센티널 검사도 받지 않는다. 새 프로젝트는 위 목록으로 받는다.

`.claude/skills/`는 git에 커밋한다. 전역에 같은 이름을 남기지 않는다. `agents/openai.yaml`은 Codex용 메타데이터라 Claude Code가 읽지 않는다. 지우면 `npx skills update`가 되살리니 그대로 둔다.

## 3단계. CLAUDE.md 생성

`/init`으로 만든 뒤 `kickoff/claude-md-template.md`의 모양으로 줄인다. setup 스킬이 이 파일에 `## Agent skills` 블록을 추가하므로 setup보다 먼저 만든다. 이 단계는 뒤의 산출물에 기대는 자리가 둘이다 — `@` 임포트 대상은 5단계가 만들고 검증 명령은 7단계가 채운다. 그 전까지 `@` 줄은 주석으로 두고 검증 명령 칸은 비워 둔다. 훅 등록과 빨강 확인은 7단계다(pre-commit이 있어야 한다). 교정 루프 절은 템플릿 그대로 복사한다. 규칙이 아니라 규칙을 만드는 절차이므로 "규칙 없음" 원칙과 충돌하지 않는다.

지침의 자리는 로드 시점이 정한다. 로드 시점은 넷이다 — 항상(CLAUDE.md, `@` 임포트, `paths` 없는 rules, 모델이 부를 수 있는 스킬의 description, 자동 메모리 `MEMORY.md`의 앞부분, 켜 둔 MCP 서버의 도구 이름과 서버 지침), 해당 파일을 Read 도구로 열 때(`paths` 있는 rules와 하위 디렉터리의 `CLAUDE.md`. Bash `cat`·`sed`로 읽으면 안 실린다), 필요하다고 판단할 때(skill 본문. 한 번 부르면 이후 턴 내내 남는다), 사건이 일어날 때(훅의 계기 문장). 마크다운 링크는 로드되지 않는다. 파일을 쪼개도 임포트하면 분량은 같다. 분류 표는 위 템플릿의 교정 루프 절이고, 남길 항목은 "이 줄을 지우면 실수하게 되나"로 거른다. 강제가 필요한 것은 문서가 아니라 훅이다.

- 배치 규칙의 판정자는 `tools/check_instructions.py`다. `paths` 누락(규칙 폴더는 하위까지 본다. `paths`는 목록과 쉼표 문자열 둘 다 받는다), 아무 파일도 가리키지 않는 `paths` glob(규칙이 조용히 안 실린다), 저장소 파일을 상대 경로로 부르는 훅(세션이 루트를 벗어나면 깨지고, PreToolUse면 모든 Bash를 막는다. `${CLAUDE_PROJECT_DIR}`로 쓴다), 200줄 초과, 원칙 외 `@` 임포트(문장 속 `@경로`도 임포트다. rules와 임포트된 파일 안의 `@`도 따라가 실리므로 거기서도 잡는다), 임포트된 파일 안의 형제 상대 경로(백틱 경로는 모델이 루트 기준으로 읽는다. `@` 임포트의 상대 경로는 담은 파일 기준으로 풀린다), 덧댄 스킬 사본의 센티널 소실과 목록 누락, 훅의 텍스트 stdin, 루트 밖의 `CLAUDE.md`·`AGENTS.md`(`node_modules`와 워크트리는 보지 않는다). 7단계에서 복사·등록하고 빨강을 본다.
- 항상 로드 분량은 `/context`를 직접 실행해 실측하고, 재배치했으면 전후 값을 ADR로 남긴다. 줄 수는 대리 지표일 뿐이다 — agent-os는 200줄 검사만 두고 실측을 한 번도 하지 않아, 재배치 커밋(2026-09-20) 뒤 여덟 날 동안 줄은 11% 늘고 글자는 39% 늘었다(2026-09-28 감사). 이 기준은 ai-agent-platform AAPP-15(2026-09-01)에서 한 번 겪었고, agent에서 담지 않아 두 번째로 겪었다.

## 4단계. /setup-matt-pocock-skills

한 번 실행한다. 세 가지를 묻는다.

- 이슈 트래커: GitHub, GitLab, 로컬 마크다운(`.scratch/<feature>/`), 기타. Jira는 "기타"를 고르고 한 단락으로 설명한다. 예: "이슈는 Jira. 티켓 생성은 /jira-create, 착수는 /jira-start(브랜치와 Draft PR), 커밋과 진행 기록은 /jira-commit, 완료는 /jira-complete. 브랜치 이름은 feature/[이슈번호]-[kebab-설명]." 그대로 `docs/agents/issue-tracker.md`에 기록된다.
- 트리아지 라벨: triage 스킬을 안 깔았으므로 건너뛴다.
- 도메인 문서: 단일 컨텍스트 기본(루트 `CONTEXT.md` + `docs/adr/`). 모노레포면 멀티 컨텍스트.

산출물: `docs/agents/issue-tracker.md`, `docs/agents/domain.md`, `CLAUDE.md`의 `## Agent skills` 블록. 쓰기 전에 초안을 보여 주니 한국어로 고쳐서 승인한다.

로컬 마크다운을 골랐으면 `docs/agents/issue-tracker.md`에 두 가지를 더한다. `Status:` 값(`ready-for-agent`, `in-progress`, `done`, `wontfix`)과 "전체 계획" 절(`.scratch/plan.md`가 기능 목록·`Blocked by`·`Status`를 갖고, 프론티어만 병렬, 계약 변경 티켓이 첫 blocker). 그리고 `.scratch/plan.md` 첫 판을 만든다. 슬라이스와 기능(slug), 의존, 상태. 헌법의 "첫 슬라이스와 비목표"는 헌법이 아니라 여기 산다.

## 5단계. 헌법

헌법 전에 제품 의도 한 장(`docs/PRD.md`)을 쓴다. 누구의 어떤 문제를 왜 푸는가, 무엇을 만들고 무엇을 안 만드는가, 성공의 정의, 스펙이 충돌할 때의 우선순위. 40줄 안팎. 설계 문서는 "어떻게"만 담으므로 이것이 없으면 스펙끼리 충돌할 때 기준이 없다(ai-agent-platform은 설계 spec 7개에 PRD 0개였다). 이 시점이 가장 싸다.

Spec Kit 템플릿을 내려받아 채운다. Spec Kit 자체는 설치하지 않는다. Spec Kit의 specify, clarify, plan, tasks, implement, analyze는 2단계에서 설치한 to-spec, to-tickets, implement, code-review와 1:1로 겹쳐서 둘 다 깔면 실행기가 둘이 된다. mattpocock에 없는 것은 헌법뿐이고, 헌법 스킬이 하는 인터뷰는 grill-me가 대신한다. 반대로 Spec Kit 파이프라인을 쓰고 싶으면 to-spec, to-tickets, implement, code-review를 빼고 `specify init --integration claude`로 대체한다. 어느 쪽이든 파이프라인은 한 벌만.

```bash
mkdir -p docs/constitution && curl -L -o docs/constitution/principles.md https://raw.githubusercontent.com/github/spec-kit/main/templates/constitution-template.md
```

PowerShell에서는 `curl`이 별칭이라 `curl.exe`로 쓴다. 이 시점에 3단계 CLAUDE.md의 `@` 줄을 살린다.

채우는 방법: 에이전트에게 "`/grill-me`로 docs/constitution/을 채우자. 한국어로. 다 채울 때까지 물어라"라고 시킨다. 원칙과 거버넌스는 `principles.md`, 스택은 `tech.md`, 검증·운영은 `operations.md`에 쓴다. 이것이 킥오프 인터뷰다. 템플릿 섹션 대응:

| 템플릿 섹션 | 채울 내용 |
|---|---|
| 원칙 1~5 | 타협 불가 원칙. 예: 테스트 먼저, 타입 any 금지, 서비스 간 DB 직접 접근 금지 |
| 자유 섹션 1 | 스택과 구조. 멀티레포/모노레포, 백엔드, 프론트엔드, 패키지 매니저, 디렉터리 규칙 |
| 자유 섹션 2 | 검증과 운영. 테스트 의무, CI 도구, 이슈관리(4단계에서 고른 것), 브랜치와 PR 규칙 |
| 거버넌스 | 개정 절차. 헌법 변경은 ADR을 남긴다 |

빈 칸 없이 채운다. 모르는 항목은 "미정"이 아니라 결정한다. 결정 못 하면 그릴링을 더 한다.

인터뷰에서 나온 결정 중 ADR 요건 셋(되돌리기 어렵다, 코드만 봐선 의아하다, 진짜 대안이 있었다)을 채우는 것은 그 자리에서 ADR로 쓰고 `docs/adr/README.md` 색인을 같이 만든다. 첫날에 보통 둘에서 넷이 나온다(엔진 선택, 진실의 원천, 권한 기본값, 지침 배치).

**처음부터 셋으로 나눈다.** `principles.md`(원칙 다섯과 거버넌스, 30줄 안팎)만 `CLAUDE.md`가 `@`로 임포트하고, `tech.md`와 `operations.md`는 지도에서 "언제 읽나"와 함께 경로로 가리킨다. 디렉터리에만 해당하는 규칙(포트, 어댑터, 플러그인, 테스트)은 헌법이 아니라 `.claude/rules/*.md`에 `paths`를 붙여 둔다. 첫 프로젝트에서 한 파일로 시작해 161줄까지 키운 뒤 통째로 임포트하다 나눴다. 그 비용을 다시 치르지 않는다.

나누는 기준은 주제가 아니라 셋이다. (1) 150줄을 넘거나 에이전트가 규칙을 놓치기 시작할 때. (2) 어떤 절이 다른 절과 다른 주기로 바뀔 때. 구조는 패키지를 추가할 때마다 바뀌고 원칙은 거의 안 바뀐다. (3) 어떤 절이 저장소 일부에만 해당할 때. 이 런북은 그 경로를 `paths`로 든 `.claude/rules/*.md`로 옮기고 중첩 `CLAUDE.md`는 쓰지 않는다. 공식 문서(`large-codebases`)는 둘을 나란히 두고 기준을 이렇게 적는다 — 디렉터리마다 소유자가 제 규약을 유지하면 중첩 `CLAUDE.md`, 규약을 한곳에 모으거나 같은 규칙이 흩어진 경로에 걸리면 `paths` 규칙. 혼자이거나 한 팀이면 후자다. 실리는 때는 둘이 비슷하다(그 경로의 파일을 Read할 때. 중첩 `CLAUDE.md`는 cwd가 그 디렉터리면 시작 시에도). 다른 점은 중첩 `CLAUDE.md` 안의 `@` 임포트까지 따라와 루트 지침에 거는 검사(줄 수, 임포트 허용 목록) 밖에 놓인다는 것이다. 디렉터리마다 소유자가 갈리면 ADR을 남기고 중첩 검사를 거둔다. 도구가 중첩 파일을 만들기도 한다(Next의 `next dev`가 에이전트를 감지하면 앱 폴더에 `AGENTS.md`와 `CLAUDE.md`를 만든다). 지침 검사가 그것을 잡는다. 검증 명령처럼 매 세션 필요하고 자주 바뀌는 것은 헌법이 아니라 `CLAUDE.md`에 둔다.

## 6단계. CODING_STANDARDS.md 뼈대

```markdown
# 코딩 표준

code-review 스킬이 리뷰할 때 읽는 파일. 자동 검사(린트, 타입, 테스트, 훅)로 잡을 수 있는 것은 여기 쓰지 않고 검사를 만든다. 아래 항목은 /retro가 제안하고 사용자가 "규칙으로"라고 승인한 것만 남긴다.

## 심각도
Critical(보안, 데이터 유실, 장애) 병합 차단 / Major(명백한 버그, 잘못된 로직) 병합 전 수정 / Minor(가독성, 중복, 누락 테스트) 후속 허용 / Nit 작성자 재량.

## 리뷰하지 않는 것
포맷, 린트, 타입 오류, 생성물. 도구가 잡는다.

## 판단 기준
(비어 있음)
```

규칙은 강제력이 가장 높은 층에 둔다. 타입 → 린터·훅 → 아키텍처 테스트 → 지침 → 리뷰. 오른쪽으로 갈수록 비용이 자릿수로 커진다. 린터가 잡는 규칙을 지침에 쓰지 않고, 거짓 양성이 많은 규칙을 하드 게이트로 만들지 않는다(`disable`이 관례가 되면 옆의 살아 있는 규칙까지 죽는다). 리뷰 관점은 4개 이하로 둔다. 길어지면 아무도 안 읽는다. 선행 프로젝트에서 검증된 판단 기준 목록이 있으면 첫날 씨앗으로 넣어도 되지만, 그래도 "규칙으로" 승인을 거친다.

## 7단계. 스캐폴딩과 검증 명령

에이전트에게 "헌법대로 골격을 만들어라"라고 시킨다. 프레임워크 생성기(`create-next-app` 같은 것)는 에이전트가 돌린다. 종료 조건은 세 명령이 실제로 통과하는 것이다.

- 테스트 명령 1개 (샘플 테스트 하나 포함)
- 린트 명령 1개
- 타입체크 명령 1개 (해당 언어면)

통과한 명령을 `CLAUDE.md`의 검증 명령 칸에 적는다. 이때 아래 파일들을 런북 저장소에서 복사한다. **파일마다 바꿀 자리가 다르다** — 각 항목 끝의 괄호가 그것이고, "검증 명령과 층 이름만"이 아니다.

하네스 런타임부터 적는다. 훅 열둘과 그 실행 래퍼, 검사 여섯과 훅 러너, 변이 도구, pre-commit은 파이썬이고 훅은 `uv run --project "${CLAUDE_PROJECT_DIR}" --no-sync python "${CLAUDE_PROJECT_DIR}/tools/launch_hook.py" <훅>.py`로 돈다(`--project`가 빠지면 저장소 밖에서 시스템 파이썬으로 돈다). 래퍼 `tools/launch_hook.py`는 훅 파일이 없으면 막지 않고 지나가게 하고, 지나갈 때 사용자와 모델에게 알린다(Stop·SubagentStop은 모델에게 알리면 대화가 이어져 사용자에게만). 훅 경로를 바로 부르면 파일이 없을 때 파이썬이 2로 끝나고, PreToolUse에서 2는 막기라 그 매처의 모든 호출이 막힌다(agent-os, 2026-10-02. 새 훅을 등록한 워크트리 세션이 다시 시작되며 `${CLAUDE_PROJECT_DIR}`이 그 파일이 없는 주 체크아웃을 가리켰다). 파이썬 프로젝트가 아니면 개발 도구로 uv와 파이썬 하나를 두면 그대로 돈다 — uv는 pyproject가 없는 폴더에서도 시스템 파이썬으로 돌았다(2026-09-28 실측). 훅(`hook_*.py`)은 표준 라이브러리만 쓴다. 러너·변이 도구(pydantic)와 OpenAPI 내보내기(앱 의존성)는 프로젝트 venv에서 돈다.

- `.claude/settings.json`의 `hooks` 블록과 `permissions.deny`. **훅 파일만 복사하면 아무것도 발동하지 않는다.** 반대로 등록만 복사하고 래퍼를 빠뜨리면 모든 훅이 2로 끝난다(PreToolUse는 그 매처의 호출을 막는다. 2의 효과는 이벤트마다 다르다, 부록 C). 등록 모양은 위 명령 한 줄이고 매처는 훅마다 다르다(UserPromptSubmit 하나, Stop 하나, PostToolUse `Write|Edit` 둘과 `Bash|PowerShell|<GitHub MCP PR 도구 넷>`(데스크톱 앱의 플러그인 도구 둘과 claude.ai 클라우드 세션의 도구 둘은 이름이 다르다), PreToolUse `Bash` 셋, `Bash|PowerShell` 둘, `Bash|Grep` 하나, 매처 없이(모든 도구) 하나). `permissions.deny`에 `Read(//**/.env)`·`Edit(//**/.env)`(`./`는 세션 cwd 기준이라 워크트리 세션에서는 주 체크아웃의 `.env`에 안 걸린다)와 PowerShell 읽기 모양(`PowerShell(Get-Content *.env*)` 등, Windows면), `env`에 `PYTHONUTF8`(파이썬이면). 에이전트의 저장소 전체 grep 한 번에 API 키가 도구 출력에 실린 적이 있다(agent-os, 2026-09-28). Bash·Grep으로 읽는 길은 `hook_env_read`가 막는다. 두 장치 모두 호출의 모양을 보는 에이전트 층이라 `.NET` 읽기 같은 것은 지나간다(부록 C). 셋째 층은 키 자체다 — `.env`에는 사용 한도를 건 개발용 키만 두고, 도구 출력에 실린 키는 회전한다. (바꿀 곳: GitHub MCP 도구 이름이 다르면 그 매처와 `tools/hook_pr_next_session.py`의 `MCP_TOOLS`를 함께. 두 목록의 대조는 `tests/tools/test_hook_pr_next_session.py`가 한다)
- 훅 열둘과 그 테스트 `tests/tools/test_hook_*.py`. 이유는 각 파일의 독스트링이 원천이다. `hook_prompt_directive`(지시문 계기, 폴더가 다르면 `decision: block`), `hook_journal_retro`(일지의 '다음' 절을 쓰면 retro 계기), `hook_pr_next_session`(PR 열기·병합 뒤 next-session 계기), `hook_ruff_line_width`(파이썬 파일을 쓴 직후 ruff E501을 계기로 — 한글은 폭 2라 글자 수로 가늠하면 넘긴다. ruff 설정을 그대로 따라, 설정이 없거나 E501을 고르지 않은 프로젝트에서는 침묵한다), `hook_bash_heredoc`(40줄 넘는 heredoc deny), `hook_bash_python_stub`(맨 `python` deny — 파이썬 프로젝트에만), `hook_bash_gate_pipe`(게이트가 파이프에 묻히면 경고), `hook_git_main_commit`(main 위 커밋 deny), `hook_stop_korean`(턴을 끝내는 답의 산문이 한국어가 아니면 Stop을 `decision: block`으로 막아 한 번 다시 쓰게 한다, SDK 세션은 뺀다), `hook_midturn_korean`(도구 호출 바로 앞의 중간 문장이 한국어가 아니면 다음 문장부터 한국어로 쓰라고 경고 — 입력에 텍스트가 없어 트랜스크립트에서 자기 `tool_use` 앞을 읽는다, 서브에이전트와 SDK 세션은 뺀다), `hook_env_read`(`.env` 읽기와 `.env`를 빼지 않은 전체 grep deny, Grep 도구의 `.env` 경로도), `hook_pr_head_sync`(`gh pr ready`와 `@coderabbitai review` 코멘트를 PR head가 로컬 HEAD에 못 미칠 때 deny — 푸시 직후 GitHub가 PR head를 갱신하기 전에 부르면 리뷰가 옛 head를 본다). 앞의 넷은 단계를 닫는 순간에 처음부터 붙인 계기 훅, 뒤의 여덟은 지침이 어겨진 뒤 승격된 것(여섯. 그중 `hook_bash_gate_pipe`와 `hook_midturn_korean`은 막지 않고 알리는 계기 훅이다)이거나 실패가 조용해 첫 사건에서 막는 훅으로 간 것(`hook_env_read`, `hook_pr_head_sync`)이라 새 프로젝트는 처음부터 갖는다. (바꿀 곳: `hook_bash_gate_pipe`의 게이트 명령 목록을 그 프로젝트의 검증 명령으로. `hook_stop_korean`과 `hook_midturn_korean`은 답변 언어가 한국어인 프로젝트에만. `hook_pr_head_sync`는 GitHub PR과 `gh`를 쓰는 프로젝트에만)
- `.claude/rules/tools.md`. 훅·검사의 규약(단독 실행, 바이트 stdin, 계기 훅과 막는 훅의 기준, 못 보는 것 절, 식별자 언어). (바꿀 곳 0)
- `.github/PULL_REQUEST_TEMPLATE.md`. 변경 유형, 왜, 남긴 위험, 변경된 영역, 체크리스트, 확인 방법, 관련 티켓. `/git-pr`이 이것을 채운다. (바꿀 곳: 변경된 영역의 층 이름과 검증 명령, 67행 중 약 15행)
- 커밋 메시지 훅 `tools/check_commit_msg.py`와 `tests/tools/test_check_commit_msg.py`. `.pre-commit-config.yaml`에 `stages: [commit-msg]`로 등록하고 `default_install_hook_types: [pre-commit, commit-msg]`를 둔다. 나쁜 메시지로 빨강을 본다. (바꿀 곳 0)
- 지침 검사 `tools/check_instructions.py`와 `tests/tools/test_check_instructions.py`. `.pre-commit-config.yaml`에 `always_run: true`로 등록한다. (바꿀 곳: `PATCHED_SKILLS`·`SENTINEL`·`ALLOWED_IMPORTS` 상수를 **그 프로젝트가 실제로 덧댄 사본**으로. agent-os는 여섯(code-review·grilling·implement·retro·to-spec·to-tickets)을 덧댔고 그대로 복사하면 첫 커밋이 그 여섯의 센티널 부재로 빨강이다. 목록은 양방향으로 검사된다 — 주석이 있는데 목록에 없는 사본도 빨강)
- 타입 우회 검사 `tools/check_type_escapes.py`(파이썬이면. 원칙 III의 판정자, ADR 0013), 변이 도구 `tools/mutate.py`(테스트가 무엇을 재는지 변이로 본다. 바이트 그대로 되돌리고 기대 결과를 받는다. `.pre-commit-config.yaml`에 `files: _mutations\.toml$`로 `--check`를 걸어 커밋에 든 변이 표의 원문을 본다), Actions 실행 요약 `tools/gh_run_summary.py`(리뷰 봇이 코멘트 없이 초록일 때 로그를 읽는다. operations.md가 가리킨다). (바꿀 곳 0. 검사는 `[tool.pyright]`의 `include`를 읽는다)
- 인용 대조 `tools/check_quotes.py`와 `tests/tools/test_check_quotes.py`. 바뀐 .md의 20자 이상 따옴표 인용을 저장소와 글자 그대로 대조해 경고만 낸다(같은 PR에서 고친 문장의 인용 둘이 옛 문구로 남았던 자리). `.pre-commit-config.yaml`에 `files: \.md$`와 `verbose: true`로 두고 CI에는 넣지 않는다. (바꿀 곳 0)
- 마크다운 표 검사 `tools/check_md_tables.py`와 `tests/tools/test_check_md_tables.py`. cmark-gfm(GitHub의 렌더러)의 블록 파싱을 옮겨, 표가 GFM에서 깨지는 자리를 본다 — 행의 칸 수가 머리 행과 다른 것, 표 아래에 빈 줄이 없는 것, 표 안의 구분 행(빈 줄 없이 붙은 표 둘), 표처럼 썼는데 표가 되지 못한 머리 행. agent-os의 plan.md가 두 번 깨졌다 — 칸 안에 넣은 줄바꿈 목록이 표를 끊었고, 코드 스팬 안의 `|`가 칸 구분으로 읽혔다(GFM은 코드 스팬도 파이프를 보호하지 않는다). 줄 두 개만 보는 판정은 목록·인용·HTML 블록 안에서 오탐과 미탐을 함께 냈다(적대 검증). `.pre-commit-config.yaml`에 `types: [markdown]`, `require_serial: true`, `stages: [pre-commit]`. (바꿀 곳 0)
- 줄 구분 문자 검사 `tools/check_line_separators.py`와 `tests/tools/test_check_line_separators.py`. 추적 텍스트 파일의 날것 U+2028·U+2029·U+0085를 잡는다. 편집 도구가 소스의 비 ASCII 이스케이프를 날것 문자로 저장하는 사고가 되풀이됐다(PR #58, 그리고 이 검사를 쓰던 세션에서 파일 다섯). 소스에 그 문자가 필요하면 `chr()`로 만든다. `types: [text]`, `require_serial: true`, `stages: [pre-commit]` — 이것이 없으면 커밋 메시지 파일(text)에도 돈다. (바꿀 곳 0)
- 실행 래퍼 `tools/launch_hook.py`와 `tests/tools/test_launch_hook.py`. (바꿀 곳 0)
- 훅 러너 `tools/run_hooks.py`와 페이로드 표 `tools/hook_payloads.toml`, `tests/tools/test_run_hooks.py`. 러너는 등록 명령이 모두 위 모양인지 대조하고 그 모양으로 훅을 띄운다. 새 훅의 넷 중 "실행 확인"을 pre-commit이 돈다 — 실제 훅 파일을 **손으로 흉내 낸 페이로드**로 돌리는 것이라 Claude Code가 실제로 주는 입력 모양(런타임 입력 계약)은 검증하지 않는다. 워크트리 세션의 훅으로는 바뀐 파일을 확인할 수 없다(주 체크아웃의 파일이 돈다. agent-os, 2026-09-28). (바꿀 곳: 표의 사례를 그 프로젝트의 훅으로. 등록과 표가 한쪽에만 있는 훅은 러너가 잡는다)
- `.github/workflows/ci.yml`. 훅과 같은 검사. LLM 테스트 제외. 경로 필터를 걸면 미매칭은 실패로. (바꿀 곳: 파이썬이면 검사 이름만, 아니면 셋업 스텝 전부)
- 브랜치 보호 본문 `tools/protection.json`. 8단계의 `gh api --input`이 이 파일을 읽으므로 복사하지 않으면 그 명령이 입력을 찾지 못한다(PR #91 리뷰). (바꿀 곳: `required_status_checks.contexts`의 검사 이름이 `verify`가 아니면 그것)
- `.coderabbit.yaml`. 보안·버그·성능만. 린터는 끈다(CI가 돌린다). 제외는 생성물·락파일·남이 쓴 스킬 사본(`.claude/skills/**`)만. 로컬 CLI도 이 파일을 읽으므로 테스트 경로를 빼면 로컬 리뷰도 사라진다. 비공개 저장소에 무료 플랜이면 `auto_review.enabled: false`. PR에서는 요약만 남고 체크가 `pass`로 보인다. (바꿀 곳: `path_instructions` 아홉 블록과 "이 저장소의 특수성" 문단은 그 프로젝트의 층과 원칙으로 **새로 쓴다**. 골격만 복사하고 대부분을 다시 쓴다)
- `.github/workflows/claude-code-review.yml`. 유지보수성(리뷰 관점 넷)과 경계. 플러그인 대신 직접 프롬프트로, 읽을 파일(CLAUDE.md, CODING_STANDARDS.md, 용어집, rules)과 담당 축, 완료 조건(요약 코멘트 하나를 `gh pr comment`로)을 명시한다. 뒤에 "코멘트가 0개면 실패" 스텝을 둔다. `show_full_output: true`. 시크릿은 사람이 넣는다. (바꿀 곳: 경계 축 문장을 그 프로젝트의 원칙으로 새로 쓴다. agent-os 것은 LangGraph·LangChain 타입의 누출이다)
- `.claude/agents/coderabbit-review.md`. CLI 실행, 좌석 확인(`coderabbit auth status`의 `Seat:`), 트리아지. 코드를 고치지 않는다. (바꿀 곳: 오탐 목록을 그 프로젝트의 자동 검사가 잡는 것으로)
- `.claude/agents/spec-reviewer.md`. 명세를 티켓 전에 검토하는 읽기 전용 검토자. 9단계 3번의 체크리스트와 질문의 원천이다. (바꿀 곳: 체크리스트 2와 6의 원칙 항목을 그 프로젝트 헌법으로)
- `.claude/skills/code-review/SKILL.md` 사본. 원본은 `<fixed-point>...HEAD`만 보고 리포트에서 멈춘다. 덧댄 것은 사본 첫머리 주석이 원천이다 — 범위를 미커밋·미추적까지, 보고 뒤 반영 절차, 본 범위 한 줄, 소스 없는 변경은 sonnet, 요구·참고 가름, 두 브리프의 주장 검증 목록, 받는 쪽 확인. 근거 확인은 서브에이전트가 격리된 컨텍스트에서 ADR도 주변 코드도 모른 채 판단한다는 사실에 대한 장치이고, 부록 A의 초록 착시와 한 쌍이다. 문서만 바뀐 변경을 리뷰에서 면제하지 않는다. (바꿀 곳 0)
- 나머지 덧댄 사본 다섯(`grilling`, `implement`, `retro`, `to-spec`, `to-tickets`). 무엇을 덧댔는지는 각 사본 첫머리 주석이 원천이다. 덧댄 사본은 `npx skills update -p`가 조용히 되돌리므로 그 주석을 센티널로 삼아 지침 검사가 본다. 사람이 기억하는 대신 훅이 판정한다. 부록 A의 `disable-model-invocation` 줄과 같은 병이다. (바꿀 곳: 덧댐이 그 프로젝트에 맞지 않으면 사본을 원본으로 두고 `PATCHED_SKILLS`에서 뺀다)
- `.claude/skills/next-session/SKILL.md`. PR을 열거나 병합하면 다음 작업의 지시문(형식은 스킬)을 낸다. PR을 열었으면 그 세션이 반영과 병합까지 마친 뒤다. 세션을 끝내는 것은 그 사건이 아니라 지시문의 "어디서"다. 계기 훅을 위반 확인 전에 두는 이유는 10단계. (바꿀 곳: 결정표의 스킬 이름이 다르면 그것)
- `.claude/skills/open-session/SKILL.md`와 `tools/open_session.ps1`. **Windows 데스크톱 앱 전용이다.** 다른 OS면 이 항목을 건너뛰고 next-session 4단계에 "지시문을 낸 뒤 사람이 새 세션에 붙여 넣는다"는 대체 줄을 둔다. 지시문의 "어디서"가 새 세션이면 그 세션을 연다. 앱 딥링크(`claude://code/new?q=…`. 폴더를 실으면 신뢰 대화상자 뒤 폴더가 떨어진다)로 지시문이 채워진 세션 화면을 열고, 접근성 트리로 보내기와 분할 보기를 누른다. 첫 줄이 슬래시 명령이면 앱이 그 `/`를 전각 `／`로 바꿔 넣어 명령이 되지 못한다. 그래서 스크립트가 쏘기 전에 이 저장소의 스킬 명령을 그 스킬 파일을 읽어 따르라는 한 줄로 옮겨 사람 손 없이 보내고, 옮기지 못한 슬래시 명령만 보내기 전에 멈춰 사람이 첫 글자를 고쳐 보낸다. 제목은 여는 쪽이 아니라 새 세션이 스스로 브랜치명으로 바꾼다. 딥링크 URL은 윈도 명령줄로 넘어가 잘리므로 8000자 안이어야 한다. 앱이 업데이트를 위한 끝내기를 시작하고 끝내지 못하면 딥링크를 로그 없이 버려, 스크립트가 쏘기 전에 앱의 로그에서 그 표지를 찾고 멈춘다(`quitting=`, 부록 C). 칩·`claude --bg`·스케줄 실행을 버린 이유는 일지 2026-09-21 open-session. (바꿀 곳: 스킬 21행의 `-Folder` 경로)
- `.scratch/retro-queue.md`. 회고가 낸 후보 중 승인했으나 반영하지 않은 것의 표. 규약 셋 — 승인분만, 닫으면 취소선, 번호는 영구 식별자. 없으면 승인된 회고가 일지 산문에만 남아 다음 세션이 파일 열여섯 개를 센다(agent-os 2026-09-22). (바꿀 곳: 머리말만 두고 표는 비운다)
- `docs/constitution/operations.md`의 리뷰 파이프라인 절. 커밋 전 셀프 리뷰, PR 직전 CLI, PR 봇(공개·유료면 둘, 아니면 Claude 하나), 초록 착시. (바꿀 곳: 절 구조만 복사하고 실측 항목(PR 번호, 좌석, 별 수)은 첫 PR 뒤에 그 프로젝트의 것으로 채운다)
- `README.md`의 원천 표. 사실 하나에 원천 하나. 두 곳이 다르면 원천이 맞고 나머지가 버그다. (바꿀 곳: 행 전부를 그 프로젝트의 문서로)

새 검사는 일부러 깨뜨려 빨강을 보고 원복한다. 통과만 보고 넣은 검사는 무엇이든 잡는다는 증거가 없다(선행 저장소는 이것 때문에 '실패해야 할 것이 성공으로 보이던' 문제를 다섯 번 겪었다). 복사한 검사는 `tests/tools/`의 테스트가 빨강의 증거라 `uv run pytest tests/tools`가 그 확인이고, 손 변이는 테스트가 없는 새 검사에만 한다. 최소 가드레일도 이때 건다. pre-commit 훅이든 CI 잡이든 린트와 테스트가 자동으로 도는 곳 하나. retro 기준으로 가드레일 없는 저장소는 그 자체가 결함이다.

디렉터리별 규칙 파일을 `.claude/rules/<dir>.md`로 만든다. 헌법 인터뷰에서 나온 디렉터리 한정 결정이 내용이고 `paths` 프론트매터가 필수다. 각 파일 첫머리에 원천(코드·테스트 또는 ADR·명세)을 적고 "코드와 다르면 코드를 고치거나 ADR을 남긴다"를 둔다. 코드 독스트링과 같은 문장을 되풀이하지 않는다 — 결정과 ADR 번호는 rules에, 논증은 코드에(agent-os는 다섯 쌍이 글자 그대로 중복되어 있었다). 린터가 판정하는 것(import 경계)은 도구 설정을 가리키기만 한다.

선택: 스택이 정해졌으면 LSP 플러그인을 프로젝트 스코프로 설치한다. `.claude/settings.json`의 `enabledPlugins`에 기록되어 저장소와 함께 간다. 같은 파일의 `skillOverrides`에 이 프로젝트가 안 쓰는 전역 스킬(jira-* 등. git-pr*는 PR 흐름이 쓰므로 끄지 않는다)을 `"off"`로 적어 매 세션 컨텍스트와 오트리거를 줄인다. 이름이 같은 플러그인 스킬(`coderabbit:code-review` 등)은 `skillOverrides`로 끌 수 없으니(부록 C) 안 쓰면 `/plugin`으로 플러그인째 끈다. 안 쓰는 MCP 서버와 같은 서버 두 벌도 `/mcp`로 끈다. 끈 전후는 `/context`로 잰다. 언어 서버 바이너리는 따로 설치해야 한다.

```bash
claude plugin install typescript-lsp@claude-plugins-official --scope project
```

## 8단계. 첫 커밋

```bash
git add -A && git commit -m "chore: 하네스 킥오프 (헌법, CLAUDE.md, 코딩 표준, 스킬)"
```

포함: `.claude/skills/`, `.claude/settings.json`(있으면), `CLAUDE.md`, `CODING_STANDARDS.md`, `docs/`, `.github/`, `tools/`, 골격.

첫 커밋 뒤 원격을 만들고 푸시한다. 그다음부터는 브랜치 → `/git-pr` → CI 초록 → `/git-pr-merge`(squash)다.

```bash
gh repo create <owner>/<repo> --private --source=. --push
```

main을 보호한다. 필수 상태 검사 `verify`(CI 잡 이름), strict, 선형 이력, 강제 푸시·삭제 금지. PR 필수는 두지 않는다 — main에 닿는 커밋을 거르는 것은 필수 검사다. 혼자면 관리자 우회를 허용해 두고 팀원이 생기면 끈다. 관리자 우회는 사람의 토큰으로 도는 에이전트에게도 열려 있고(`gh pr merge --admin`, main 직접 푸시), 로컬 훅은 커밋만 막는다(GitHub 문서상의 동작이고 agent-os는 재지 않았다). 그래서 병합은 체크를 먼저 보는 `/git-pr-merge`로만 한다. 팀이면 리뷰 승인 필수와 CODEOWNERS를 첫날에 더한다. 요청 본문은 7단계에서 복사한 `tools/protection.json`이다(agent-os의 실제 설정을 2026-09-28에 `gh api repos/<owner>/<repo>/branches/main/protection`으로 내보낸 것. 원격이 바뀌면 같은 명령으로 다시 뽑는다).

```bash
gh api -X PUT repos/<owner>/<repo>/branches/main/protection --input tools/protection.json
```

1단계 갈림길이 `free`+비공개였으면 이 절은 생략하고 `/git-pr-merge`가 게이트다. 고른 것을 `operations.md` 가드레일 절에 적는다. 나중에 공개로 바꾸면 그날 보호를 건다(agent-os는 셋째 날 공개 전환 뒤 걸었다). 상세는 `kickoff/pitfalls.md`·`kickoff/facts.md`.

봇 리뷰의 전제 둘은 사람이 한다. 에이전트는 토큰과 시크릿을 다루지 않는다.

1. `claude setup-token`으로 만든 토큰을 저장소 시크릿 `CLAUDE_CODE_OAUTH_TOKEN`에 넣는다. 에이전트는 `gh secret list`로 이름과 시각만 확인한다.
2. 로컬에서 `coderabbit auth login`. `coderabbit auth status`의 `Seat:`를 본다. `not assigned`면 유료 구독 없이는 CLI 축이 비어 있다(agent-os 2026-09-23 실측. 좌석 배정에는 활성 유료 구독이 필요하다). `coderabbit --usage`는 청구 주기 누적만 보여주고 시간당 잔량을 보여주지 않는다.

CodeRabbit GitHub App은 공개 저장소이거나 CodeRabbit 유료 플랜일 때만 설치한다. 공개라도 별이 10개 미만이면 자동 리뷰가 없고 PR마다 `@coderabbitai review`로 부른다(agent-os PR #12·#43 실측, 2026-09-21·22. OSS PR 리뷰 상한은 별 수에 따라 시간당 1~10회이고 별이 적으면 하한 쪽이다). 비공개 저장소에 무료 플랜이면 설치해도 Walkthrough 요약만 남고 체크는 `pass`다(agent-os PR #2 실측, 2026-09-20). 플랜·요금 사실의 확인일은 `kickoff/facts.md`에 모아 둔다. 설치 여부는 PR의 `coderabbitai[bot]` 코멘트로만 확인할 수 있고 설치 목록 API는 앱 토큰이 필요해 `gh`로는 403이다. 체험은 자동으로 켜지지 않고 시트는 대시보드 team-management에서 사람이 할당한다.

첫 PR에서 Claude Code Review가 실제로 코멘트를 남기는지 본다. 코멘트 없는 초록은 전제가 빠진 것이다. Claude Code Review는 지적이 없을 때 코멘트를 안 남기고 초록이 되기도 하므로(agent-os 실측, 4턴 실행) 워크플로에 `show_full_output: true`를 켜 두고 로그로 실행 내용을 확인한다.

## 9단계. 첫 기능

기능마다 이 순서. 원천은 복사 목록의 `to-tickets` 사본 1단계이고 여기는 첫날을 위한 요지다. 건너뛸지의 기준은 "몇 개를 건드리나"가 아니라 "건드리는 곳마다 새로 정할 것이 있나"다. 같은 패턴의 N번째 반복은 여러 모듈을 관통해도 새 결정이 없으므로 설계 인터뷰 없이 바로 시킨다.

첫 기능 전에 공통 규약을 정한다. 식별자 형식, 에러 봉투, 시간대, 디스크 형식의 버전. 도메인마다 다시 정하면 어긋난다. 미루는 것은 괜찮지만 미룬 자리에 판정 장치(드리프트 검사 테스트)는 둔다. 원천 → 생성물 방향을 하나로 고정하고 생성물은 커밋하며 드리프트 검사는 CI가 아니라 테스트에 둔다.

리뷰에서 보류한 지적은 그 자리에서 다 고치지 않고 별도 티켓으로 뺀다. 계획이나 명세는 사후에 실제 구현대로 고쳐 쓰지 않는다. 어긋난 지점이 기록이다. 살아남은 결정만 ADR로 승격한다.

각 단계의 절차는 그 스킬·서브에이전트 파일이 원천이다. 여기는 순서와 새 프로젝트가 바꿀 자리만 적는다.

1. `/grill-with-docs` 로 설계 인터뷰. 용어는 `CONTEXT.md`, 결정은 `docs/adr/`에 쌓인다.
2. `/to-spec` 으로 대화를 명세로.
3. 읽기 전용 서브에이전트 `spec-reviewer`(복사 목록)가 명세를 검토한다. 체크리스트 일곱과 질문 둘은 그 파일에 있고, 새 프로젝트는 체크리스트 2와 6의 원칙 항목을 그 프로젝트 헌법으로 바꾼다. agent-os는 첫 기능에서 일회성 호출로 시작해 두 번째 기능(http-channel)에서 파일로 굳혔다.
4. `/to-tickets` 로 수직 슬라이스 티켓. 원격 트래커면 4단계에서 적은 흐름대로 발행한다.
5. `/implement` 로 구현. tdd 스킬이 테스트 먼저를 강제한다. 이 티켓의 몫만 쓴다.
6. 커밋 전 `/code-review`. 범위(미커밋·미추적까지)와 반영 규칙(Critical·Major는 커밋 전에, 근거를 먼저, 보류는 티켓이나 회고 후보로)은 사본 6단계가 원천이다.
7. PR 직전 `coderabbit-review` 서브에이전트. 좌석이 있을 때만이다(8단계).
8. `/git-pr`로 PR. 별이 10개 미만인 공개 저장소는 `gh pr comment <번호> --body "@coderabbitai review"`로 부른다. 봇 둘과 CI의 역할 분담, 코멘트 0개인 초록을 읽는 법은 `operations.md` 리뷰 파이프라인이 원천이다. `/git-pr-feedback`으로 반영하고 `/git-pr-merge`로 squash 병합한다. 반영과 병합은 PR을 연 세션이 하고, 병합 뒤는 10단계다.

## 10단계. 세션 마감

단계를 닫는 순간의 지침은 어겨진다. 그래서 마감의 셋은 스킬과 훅이 들고 이 절은 그것들을 가리킨다.

- **회고**는 `retro` 스킬이 계기에 스스로 돈다. 계기는 스킬 description에 적되 "세션이 끝나면" 같은 관찰 불가능한 것이 아니라 관찰 가능한 사건(일지의 "다음" 갱신, 마무리 발화)으로, 지침이 어겨진 뒤 훅으로 옮겼다(`tools/hook_journal_retro.py`, 복사 목록). 후보를 심각도 순으로 내놓으면 승인한 것만 반영하고, 승인했으나 이 세션에서 반영하지 않는 것은 `.scratch/retro-queue.md`에 짧은 행으로 적는다. 원본 스킬의 플래그를 왜 빼는지는 `kickoff/pitfalls.md`.
- **다음 작업**은 `next-session` 스킬이 지시문으로 낸다. PR을 열거나 병합하면 훅(`tools/hook_pr_next_session.py`)이 계기를 넣고, 결정표가 "어디서"를 정한다. 결정표에 "회차 3 이상이면 chore 배치" 줄을 처음부터 둔다 — 대기열은 유입에만 계기가 있으면 자란다(agent-os는 그 줄 없이 아홉 날 동안 승인 행 서른여덟 중 둘만 닫았다, 2026-09-28 아침 감사 시점). 진행 상태는 메모리에 적지 않는다. 저장소(일지의 "다음", `plan.md`, 대기열)가 원천이고, 메모리에 둔 스냅숏은 하루 만에 두 곳이 틀렸다(agent-os 2026-09-22).
- **승격 사다리**는 `.claude/rules/tools.md`와 `CLAUDE.md` 교정 루프가 원천이다. 기계적 위반은 린터 규칙이나 훅으로, 판단 기준만 `CODING_STANDARDS.md`로. 같은 주의를 세 번 되풀이하면 지침 후보, 지침으로 적은 뒤에도 어겨지면 훅 후보. 막는 훅은 어겨진 것이 확인된 뒤에만 더하되 실패가 조용하고 패턴이 고정된 것은 첫 사건에서 간다. 계기만 넣는 훅은 단계를 닫는 지침에 처음부터 붙인다 — 거짓 양성의 비용이 문장 하나라 게이트의 사다리를 타지 않는다. 지침이 길어졌으면 잘라낸다. `/context`로 항상 로드 분량을 실측해 늘었으면 3단계의 배치 기준으로 다시 나눈다.

## 첫날 종료 체크리스트

각 항목 끝의 괄호는 산출 단계다.

- [ ] superpowers 비활성, 전역 CLAUDE.md 비어 있음, 프로젝트가 관리하는 스킬의 전역 사본 없음, 안 쓰는 전역 스킬은 `skillOverrides`로, 안 쓰는 플러그인과 MCP 서버는 `/plugin`·`/mcp`로 꺼짐 (0·7)
- [ ] `npx skills ls`의 목록이 2단계 설치 목록 + 7단계에서 더한 스킬(next-session, open-session)과 같다 (2·7)
- [ ] `CLAUDE.md`: 레이어 역할, 지도(언제 읽나), 검증 명령, 작업 규약, 교정 루프와 로드 시점 표, 환경 함정. `@` 임포트는 principles.md 하나 (3)
- [ ] `docs/agents/issue-tracker.md`에 4단계에서 고른 트래커의 흐름 기록 (4)
- [ ] `docs/PRD.md` 한 장, `docs/constitution/` 세 파일 빈 칸 없음, 한국어, `docs/adr/README.md` 색인 (5)
- [ ] `CODING_STANDARDS.md` 존재, 판단 기준 비어 있음 (6)
- [ ] 테스트, 린트, 타입체크 명령 통과. 가드레일 하나 이상 (7)
- [ ] `.claude/settings.json`에 훅 등록과 `permissions.deny`(`.env`). 훅마다 `tools/hook_payloads.toml`에 발동·침묵 사례가 있고 `uv run python tools/run_hooks.py`와 `uv run pytest tests/tools`가 초록 (7)
- [ ] PR 템플릿, commit-msg 훅(빨강 확인), 지침 검사(상수를 이 프로젝트에 맞춤), CI 워크플로, `.coderabbit.yaml`, Claude Code Review 워크플로, 서브에이전트 둘, `.claude/rules/` 디렉터리별 규칙과 `tools.md`, `.scratch/retro-queue.md`, README의 원천 표 (7)
- [ ] 첫 커밋 완료. 원격 생성과 푸시, 첫 PR이 CI를 통과. main 보호를 걸었거나(`tools/protection.json`) free+비공개라 `/git-pr-merge` 게이트를 `operations.md`에 적었다 (8)
- [ ] 봇 전제 둘(`CLAUDE_CODE_OAUTH_TOKEN` 시크릿, CLI 로그인과 `Seat:` 확인). 첫 PR에서 Claude 코멘트 확인. CodeRabbit App은 공개 저장소나 유료일 때만 (8)
- [ ] `docs/journal/` 첫 파일과 기록 규칙, `.scratch/plan.md` 첫 판 (1·4)
- [ ] `/context` 실측값을 일지나 ADR에 기록 (10)

## 부록

런북 저장소의 `kickoff/` 아래에 있다. 새 프로젝트도 clone 한 런북 저장소에서 상대 경로로 읽는다.

- `kickoff/claude-md-template.md` — 3단계 CLAUDE.md 템플릿.
- `kickoff/pitfalls.md` — 부록 A. 세팅 중 실제로 걸린 함정. 조용히 통과하는 것을 시끄럽게 만든 기록.
- `kickoff/prompting.md` — 부록 B. 세팅 프롬프트와 스킬·서브에이전트를 쓸 때.
- `kickoff/facts.md` — 부록 C. 플랜·요금·플랫폼 사실과 확인일. 날짜가 없는 값은 추정으로 읽는다.

## 세 번째 프로젝트가 끝나면

이 런북을 세 번 돌린 뒤 매번 같은 곳을 손봤다면 그 부분만 본인 스킬로 만든다. 그 전에는 도구를 만들지 않는다. 다만 7단계의 복사 목록이 첫 주에 다섯 번 늘었으므로, 두 번째 프로젝트에서 그 목록을 매니페스트 파일(경로 | 바꿀 자리 | 확인법)로 굳히는 것은 도구가 아니라 목록이라 이 규칙과 충돌하지 않는다.
