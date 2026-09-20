# 새 프로젝트 첫날 킥오프 런북

원본은 이 파일(`C:/project/agent/KICKOFF.md`)이다. 새 프로젝트는 이 파일을 복사해서 시작하고, 런북을 고칠 일이 생기면 여기를 고친 뒤 복사본에 반영한다.

기준일 2026-09-19. 결정: mattpocock 스킬 유지, superpowers 비활성, 교정 루프는 retro 스킬의 계기 자동 회고(10단계), 지침은 한국어. 스킬(`.claude/skills/`)과 교정 루프 문단(`CLAUDE.md`)은 모두 프로젝트 레벨에 둔다. 전역에는 프로젝트와 무관한 개인 워크플로 스킬(git-*, jira-*)만 남기고, 프로젝트가 관리하는 스킬의 전역 사본은 두지 않는다.

전제: 무엇을 만들지 안다. 모르면 `/grill-me`로 브레인스토밍부터 하고 이 런북은 그 뒤에 시작한다.

## 순서의 원칙: 되돌리기 비용이 큰 것부터

세팅 순서를 정하는 기준은 중요도가 아니라 나중에 바꿀 때 드는 비용이다(ai-agent-platform 세팅 플레이북).

| 결정 | 나중에 바꾸면 | 그래서 |
|---|---|---|
| 아키텍처 스타일, 핵심 원칙 | 전부 다시 쓴다 | 첫날(5단계) |
| 저장소·워크스페이스 구조 | 설정 파일 전부 | 첫날(7단계) |
| 계약 형식(디스크 형식, 식별자, 에러 봉투) | 소비자 전부의 타입 | 첫 기능 전 |
| 개발 파이프라인 | 습관을 다시 들인다 | 기능 하나로 검증한 뒤 |
| 기능 | 그 기능만 | 언제든 |

세팅이 끝났다는 신호는 리듬이 생기는 것이다. 티켓 → 명세 → 구현 → 리뷰 → 병합 → 회고가 매 기능마다 같은 모양으로 반복되면 끝난 것이다.

## 어디에 무엇이 사는가

| 위치 | 내용 | 이유 |
|---|---|---|
| `~/.claude/CLAUDE.md` (전역. Windows는 `C:/Users/<user>/.claude/CLAUDE.md`) | 비워 둔다 | 교정 루프 문단은 `CODING_STANDARDS.md`와 `/retro`를 가리키므로, 그것들이 없는 다른 프로젝트에 새면 안 된다 |
| `~/.claude/skills/` (전역) | 프로젝트와 무관한 개인 워크플로 스킬만(git-*, jira-*). 프로젝트가 안 쓰는 것은 그 프로젝트의 `skillOverrides`로 끈다 | 전역은 같은 이름의 프로젝트 스킬을 이기므로, 프로젝트가 관리하는 스킬(grilling 등)의 전역 사본을 두면 `npx skills update` 뒤 낡은 전역이 조용히 이긴다 |
| `.claude/skills/` (프로젝트) | mattpocock 엔지니어링 스킬 전부 + grill-me | git에 커밋, 프로젝트마다 버전 고정. `skills-lock.json`이 출처와 해시를 기록 |
| `.claude/settings.json` (프로젝트) | `enabledPlugins`(LSP 등 프로젝트 플러그인), `skillOverrides`(이 프로젝트가 안 쓰는 전역 스킬을 `"off"`) | 저장소와 함께 간다 |
| `CLAUDE.md` (프로젝트) | 다른 파일을 가리키는 포인터, 검증 명령, 교정 루프 문단 | 규칙은 여기 쓰지 않는다. 교정 루프는 규칙이 아니라 규칙을 만드는 절차다 |
| `docs/constitution/` | 헌법. `principles.md`(원칙·거버넌스, 임포트), `tech.md`(스택), `operations.md`(검증·운영). 디렉터리별 규칙은 `.claude/rules/*.md`+`paths` | 프로젝트당 한 번 |
| `CODING_STANDARDS.md` | 검사로 못 잡는 판단 기준 | code-review 스킬이 읽음 |
| `CONTEXT.md`, `docs/adr/` | 용어집, 결정 기록 | domain-modeling이 씀 |
| `docs/agents/` | 이슈 트래커 규칙, 도메인 문서 위치 | setup 스킬이 씀 |
| `.github/` | PR 템플릿, CI 워크플로, Claude Code Review 워크플로 | 첫날. 런북 저장소에서 복사해 검증 명령만 바꾼다 |
| `.coderabbit.yaml` | CodeRabbit CLI 설정. 층별 path_instructions, 린터 끔, 제외는 생성물·락파일만, PR 자동 리뷰 끔 | 로컬 CLI가 읽는다. PR 리뷰는 공개 저장소나 유료일 때만 값을 한다 |
| `.claude/agents/` | 프로젝트 서브에이전트. coderabbit-review(CLI 실행과 트리아지, 수정 없음) | 스킬은 절차, 서브에이전트는 격리된 컨텍스트에서 도구를 돌리고 보고만 한다 |
| `tools/` | 배포되지 않는 저장소 유틸. 지침 검사, 커밋 메시지 검사, Actions 실행 요약 | 훅과 CI, 그리고 리뷰 봇 판정이 부른다 |
| `docs/journal/` | 진행 일지. 단계별 사실, 사용자 프롬프트 원문, 갈린 곳과 번복 | 세션을 넘어 이어가고 `/retro`의 입력 |
| `.scratch/` | 로컬 이슈 트래커(명세, 티켓) | 원격 없는 프로젝트의 유일한 작업 기록. 커밋한다 |

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

프로젝트마다 반복하지 않는다.

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

Billing & plans의 결제 수단과 Actions 지출 한도도 본다. 결제가 막히면 잡이 시작조차 안 되고 CI가 게이트라 병합도 막힌다(agent-os PR #10 실측). `free`이고 비공개로 갈 거면 보호 브랜치와 룰셋은 403이고 CodeRabbit PR 리뷰는 요약만 남는다. 처음부터 `/git-pr-merge`를 게이트로, CodeRabbit은 CLI-only로 간다. 공개 저장소면 둘 다 무료로 풀린다. agent-os는 이것을 PR을 열고 나서 알아 PR 넷을 되돌리는 데 썼다.

`docs/journal/<날짜>-kickoff.md`를 지금 만든다. 머리말에 기록 규칙을 적는다. 결정·방향 전환·설계 질문에 해당하는 사용자 프롬프트는 `> 사용자:` 인용으로 원문 그대로(오타도 고치지 않는다), 단순 조작 지시는 제외, 에이전트의 말은 옮기지 않고 세션 끝에 "추천과 결정이 갈린 곳"과 "에이전트가 번복하거나 고친 것"만 한 줄씩. 병렬 티켓 세션은 `docs/journal/<날짜>-<티켓슬러그>.md`.

## 2단계. 스킬을 프로젝트 레벨로 설치

설치기는 기본이 프로젝트 레벨(`.claude/skills/`)이다. Windows에서는 심링크 대신 복사(`--copy`)를 쓴다. 이름은 공백으로 나열하고, 오류가 나면 `-s`를 스킬마다 반복한다.

```bash
npx skills@latest add mattpocock/skills -a claude-code --copy -y -s grill-with-docs grilling domain-modeling setup-matt-pocock-skills to-spec to-tickets implement tdd code-review diagnosing-bugs writing-for-agents retro
```

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

grill-me는 본인 스킬이라 설치기에 없다. 백업에서 복사한다.

```bash
cp -r ~/.claude/skills-backup/grill-me .claude/skills/
```

`.claude/skills/`는 git에 커밋한다. 전역에 같은 이름을 남기지 않는다.

## 3단계. CLAUDE.md 생성

`/init`으로 만든 뒤 아래 모양으로 줄인다. setup 스킬이 이 파일에 `## Agent skills` 블록을 추가하므로 setup보다 먼저 만든다. 검증 명령은 7단계에서 채운다. 교정 루프 문단은 아래 그대로 복사한다. 규칙이 아니라 규칙을 만드는 절차이므로 "규칙 없음" 원칙과 충돌하지 않는다.

```markdown
# <프로젝트명>

<한 줄 소개>. 원칙만 아래에서 임포트하고 나머지는 경로로 읽는다. 200줄 이하.

@docs/constitution/principles.md

## 레이어
- <디렉터리>: <역할 한 줄> (3~6줄. 트리 전체는 README)

## 지도
| 문서 | 읽는 때 | 쓰는 때 |
|---|---|---|
| docs/constitution/tech.md, operations.md | 스택·운영을 만질 때 | ADR 뒤 |
| CONTEXT.md, docs/adr/ | 용어를 쓰거나 결정을 바꾸기 전 | domain-modeling, 승인 뒤 |
| CODING_STANDARDS.md | 리뷰 때 | "규칙으로" 뒤 |
| .scratch/plan.md, .scratch/<slug>/ | 이어서 할 때, 티켓 시작 전 | to-spec, to-tickets |
| docs/journal/ | 이어서 할 때 끝의 "다음" | 단계를 마칠 때 |

## 검증 명령
- 테스트: / 린트: / 타입체크:

## 작업 규약
1. 작업 전 명세·티켓·해당 ADR을 읽는다. 결정을 바꾸기 전에는 반드시.
2. 고칠 파일과 영향을 세 줄로 적고 시작한다.
3. 끝나면 검증 명령을 돌린다. 하네스를 바꿨으면 실제 실행으로 확인한다.
4. 결정이 바뀌면 그것을 참조하는 스킬·훅·rules·워크플로·명세를 같이 고치고, 옛 표현을 grep해 잔존이 0인지 본 뒤 3을 다시 돈다.
5. 아키텍처 결정은 ADR 초안을 보여주고 승인받는다.

## 교정 루프
- (런북 원문 네 줄) + 지침 추가 시 로드 시점 표(도구 설정 / rules+paths / skills / docs+링크 / 이 파일)

## 환경 함정
- 명령을 치기 전에 알아야 하는 것만 (PYTHONUTF8 등)

## 원칙
- 답변과 문서는 한국어로 쓴다.
```

지침을 어디에 두느냐는 로드 시점이 정한다. `paths` 누락, 200줄 초과, 원칙 외 `@` 임포트는 pre-commit 훅(`tools/check_instructions.py`)이 막는다. 스크립트는 런북 저장소(`C:/project/agent/tools/check_instructions.py`)에서 복사하고 `.pre-commit-config.yaml`에 `always_run: true`로 등록한 뒤, `paths` 없는 rules 파일을 하나 만들어 빨강을 보고 지운다. 규칙을 쓰는 시점에 걸리는 것과 나중에 전부 재배치하는 것은 비용이 다르다. 셋이다. 항상(CLAUDE.md, `@` 임포트, `paths` 없는 rules), 해당 파일을 열 때(`paths` 있는 rules), 필요하다고 판단할 때(skill). 마크다운 링크는 로드되지 않는다. 파일을 쪼개도 임포트하면 분량은 같다. 분류 표는 위 템플릿의 교정 루프 절에 있고, 남길 항목은 "이 줄을 지우면 실수하게 되나"로 거른다. 강제가 필요한 것은 문서가 아니라 훅이다. 항상 로드 분량은 `/context`를 직접 실행해 실측하고, 재배치했으면 전후 값을 ADR로 남긴다. 줄 수는 대리 지표일 뿐이다. 이 기준은 ai-agent-platform AAPP-15(2026-09-01)에서 한 번 겪었고, agent에서 담지 않아 두 번째로 겪었다.

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
mkdir -p docs/constitution && curl.exe -L -o docs/constitution/principles.md https://raw.githubusercontent.com/github/spec-kit/main/templates/constitution-template.md
```

채우는 방법: 에이전트에게 "`/grill-me`로 docs/constitution/을 채우자. 한국어로. 다 채울 때까지 물어라"라고 시킨다. 원칙과 거버넌스는 `principles.md`, 스택은 `tech.md`, 검증·운영은 `operations.md`에 쓴다. 이것이 킥오프 인터뷰다. 템플릿 섹션 대응:

| 템플릿 섹션 | 채울 내용 |
|---|---|
| 원칙 1~5 | 타협 불가 원칙. 예: 테스트 먼저, 타입 any 금지, 서비스 간 DB 직접 접근 금지 |
| 자유 섹션 1 | 스택과 구조. 멀티레포/모노레포, 백엔드, 프론트엔드, 패키지 매니저, 디렉터리 규칙 |
| 자유 섹션 2 | 검증과 운영. 테스트 의무, CI 도구, 이슈관리(Jira), 브랜치와 PR 규칙 |
| 거버넌스 | 개정 절차. 헌법 변경은 ADR을 남긴다 |

빈 칸 없이 채운다. 모르는 항목은 "미정"이 아니라 결정한다. 결정 못 하면 그릴링을 더 한다.

인터뷰에서 나온 결정 중 ADR 요건 셋(되돌리기 어렵다, 코드만 봐선 의아하다, 진짜 대안이 있었다)을 채우는 것은 그 자리에서 ADR로 쓰고 `docs/adr/README.md` 색인을 같이 만든다. 첫날에 보통 둘에서 넷이 나온다(엔진 선택, 진실의 원천, 권한 기본값, 지침 배치).

**처음부터 셋으로 나눈다.** `principles.md`(원칙 다섯과 거버넌스, 30줄 안팎)만 `CLAUDE.md`가 `@`로 임포트하고, `tech.md`와 `operations.md`는 지도에서 "언제 읽나"와 함께 경로로 가리킨다. 디렉터리에만 해당하는 규칙(포트, 어댑터, 플러그인, 테스트)은 헌법이 아니라 `.claude/rules/*.md`에 `paths`를 붙여 둔다. 첫 프로젝트에서 한 파일로 시작해 161줄까지 키운 뒤 통째로 임포트하다 나눴다. 그 비용을 다시 치르지 않는다.

나누는 기준은 주제가 아니라 셋이다. (1) 150줄을 넘거나 에이전트가 규칙을 놓치기 시작할 때. (2) 어떤 절이 다른 절과 다른 주기로 바뀔 때. 구조는 패키지를 추가할 때마다 바뀌고 원칙은 거의 안 바뀐다. (3) 어떤 절이 저장소 일부에만 해당할 때. 이 경우는 파일을 나누는 게 아니라 그 디렉터리의 `CLAUDE.md`로 옮긴다(중첩 지원). 모노레포는 루트 헌법 하나에 패키지별 중첩 `CLAUDE.md`가 기본형이다. 검증 명령처럼 매 세션 필요하고 자주 바뀌는 것은 헌법이 아니라 `CLAUDE.md`에 둔다.

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

통과한 명령을 `CLAUDE.md`의 검증 명령 칸에 적는다. 이때 파일 여섯과 절 하나를 같이 만든다. 런북 저장소(`C:/project/agent`)에서 복사해 검증 명령과 층 이름만 바꾼다.

- `.github/PULL_REQUEST_TEMPLATE.md`. 변경 유형, 왜, 남긴 위험, 변경된 영역(그 프로젝트의 층), 체크리스트(검증 명령), 확인 방법, 관련 티켓. `/git-pr`이 이것을 채운다.
- 커밋 메시지 훅 `tools/check_commit_msg.py`. `.pre-commit-config.yaml`에 `stages: [commit-msg]`로 등록하고 `default_install_hook_types: [pre-commit, commit-msg]`를 둔다. 나쁜 메시지로 빨강을 본다.
- `.github/workflows/ci.yml`. 훅과 같은 검사. LLM 테스트 제외. 경로 필터를 걸면 미매칭은 실패로.
- `.coderabbit.yaml`. 보안·버그·성능만. 린터는 끈다(CI가 돌린다). path_instructions는 그 프로젝트의 층으로. 제외는 생성물·락파일만. 로컬 CLI도 이 파일을 읽으므로 테스트 경로를 빼면 로컬 리뷰도 사라진다. 비공개 저장소에 무료 플랜이면 `auto_review.enabled: false`. PR에서는 요약만 남고 체크가 `pass`로 보인다.
- `.github/workflows/claude-code-review.yml`. 유지보수성(리뷰 관점 넷)과 경계. 플러그인 대신 직접 프롬프트로, 읽을 파일(CLAUDE.md, CODING_STANDARDS.md, 용어집, rules)과 담당 축, 완료 조건(요약 코멘트 하나를 `gh pr comment`로)을 명시한다. 뒤에 "코멘트가 0개면 실패" 스텝을 둔다. `show_full_output: true`. 시크릿은 사람이 넣는다.
- `.claude/agents/coderabbit-review.md`. CLI 실행, 남은 횟수 확인, 트리아지. 코드를 고치지 않는다. 오탐 목록은 그 프로젝트의 자동 검사가 잡는 것으로.
- `docs/constitution/operations.md`의 리뷰 파이프라인 절. 커밋 전 셀프 리뷰, PR 직전 CLI, PR 봇 하나, 초록 착시.

새 검사는 일부러 깨뜨려 빨강을 보고 원복한다. 통과만 보고 넣은 검사는 무엇이든 잡는다는 증거가 없다(선행 저장소는 이것 때문에 '실패해야 할 것이 성공으로 보이던' 문제를 다섯 번 겪었다). 최소 가드레일도 이때 건다. pre-commit 훅이든 CI 잡이든 린트와 테스트가 자동으로 도는 곳 하나. retro 기준으로 가드레일 없는 저장소는 그 자체가 결함이다.

디렉터리별 규칙 파일을 `.claude/rules/<dir>.md`로 만든다. 헌법 인터뷰에서 나온 디렉터리 한정 결정(포트 목록, 어댑터 규칙, 플러그인 모델, 테스트 규약)이 내용이고 `paths` 프론트매터가 필수다. 각 파일 첫 줄에 "원천은 코드와 테스트, 여기는 결정만"을 적어 규칙이 코드를 앞지를 때 조용히 고쳐지지 않게 한다.

선택: 스택이 정해졌으면 LSP 플러그인을 프로젝트 스코프로 설치한다. `.claude/settings.json`의 `enabledPlugins`에 기록되어 저장소와 함께 간다. 같은 파일의 `skillOverrides`에 이 프로젝트가 안 쓰는 전역 스킬(jira-* 등. git-pr*는 PR 흐름이 쓰므로 끄지 않는다)을 `"off"`로 적어 매 세션 컨텍스트와 오트리거를 줄인다. 언어 서버 바이너리는 따로 설치해야 한다.

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

main을 보호한다. 필수 상태 검사 `ci / verify`, 직접 푸시 금지. 혼자면 관리자 우회를 허용해 두고 팀원이 생기면 끈다.

```bash
gh api -X PUT repos/<owner>/<repo>/branches/main/protection --input protection.json
```

1단계 갈림길이 `free`+비공개였으면 이 절은 생략하고 `/git-pr-merge`가 게이트다. 고른 것을 `operations.md` 가드레일 절에 적는다. 상세는 부록 A.

봇 리뷰의 전제 둘은 사람이 한다. 에이전트는 토큰과 시크릿을 다루지 않는다.

1. `claude setup-token`으로 만든 토큰을 저장소 시크릿 `CLAUDE_CODE_OAUTH_TOKEN`에 넣는다. 에이전트는 `gh secret list`로 이름과 시각만 확인한다.
2. 로컬에서 `coderabbit auth login`. `coderabbit --usage`로 남은 횟수를 본다.

CodeRabbit GitHub App은 공개 저장소이거나 유료일 때만 설치한다. 비공개 저장소에 무료 플랜이면 설치해도 Walkthrough 요약만 남고 체크는 `pass`다(agent-os 실측). 설치 여부는 PR의 `coderabbitai[bot]` 코멘트로만 확인할 수 있고 설치 목록 API는 앱 토큰이 필요해 `gh`로는 403이다. 체험은 자동으로 켜지지 않고 시트는 대시보드 team-management에서 사람이 할당한다.

첫 PR에서 Claude Code Review가 실제로 코멘트를 남기는지 본다. 코멘트 없는 초록은 전제가 빠진 것이다. Claude Code Review는 지적이 없을 때 코멘트를 안 남기고 초록이 되기도 하므로(agent-os 실측, 4턴 실행) 워크플로에 `show_full_output: true`를 켜 두고 로그로 실행 내용을 확인한다.

## 9단계. 첫 기능

기능마다 이 순서. 건너뛸지의 기준은 "몇 개를 건드리나"가 아니라 "건드리는 곳마다 새로 정할 것이 있나"다. 같은 패턴의 N번째 반복은 여러 모듈을 관통해도 새 결정이 없으므로 설계 인터뷰 없이 바로 시킨다.

첫 기능 전에 공통 규약을 정한다. 식별자 형식, 에러 봉투, 시간대, 디스크 형식의 버전. 도메인마다 다시 정하면 어긋난다. 미루는 것은 괜찮지만 미룬 자리에 판정 장치(드리프트 검사 테스트)는 둔다. 원천 → 생성물 방향을 하나로 고정하고 생성물은 커밋하며 드리프트 검사는 CI가 아니라 테스트에 둔다.

리뷰에서 보류한 지적은 그 자리에서 다 고치지 않고 별도 티켓으로 뺀다. 계획이나 명세는 사후에 실제 구현대로 고쳐 쓰지 않는다. 어긋난 지점이 기록이다. 살아남은 결정만 ADR로 승격한다.

1. `/grill-with-docs` 로 설계 인터뷰. 용어는 `CONTEXT.md`, 결정은 `docs/adr/`에 쌓인다.
2. `/to-spec` 으로 대화를 명세로.
3. 명세를 읽기 전용 서브에이전트가 체크리스트로 검토한다. 첫 기능은 체크리스트를 프롬프트에 넣은 일회성 호출이고, 두 번째 기능에서도 같은 검토를 하면 `.claude/agents/spec-reviewer.md`로 굳힌다. 체크리스트 일곱: 계약 영향과 스키마 버전 처리가 적혔는가 / 원칙 위반이 없는가, 특히 새 포트와 core의 프로바이더 import / accepted ADR과 충돌하는가 / 언급한 경로가 실재하는가 / 비목표를 침범하는가 / 수용 기준마다 덮는 테스트가 있고 LLM 테스트가 포함되는가 / 자리표시자 문장이 없는가. 분류는 blocker·should-fix·nit, "blocker 없음은 정상 결과", 근거 없는 "~일 수 있다" 금지, 편집 도구 없음.
4. `/to-tickets` 로 수직 슬라이스 티켓. Jira면 4단계에서 적은 흐름대로 `/jira-create`.
5. `/implement` 로 구현. tdd 스킬이 테스트 먼저를 강제한다.
6. 커밋 전 `/code-review`로 표준 축과 명세 축 셀프 리뷰. Critical·Major는 커밋 전에 고친다. 건너뛰지 않는다. 보류한 지적은 별도 티켓.
7. PR 직전 `coderabbit-review` 서브에이전트로 보안·성능 축. 무료 CLI는 주기당 3회라 PR마다 한 번.
8. `/git-pr`로 PR. Claude Code Review가 유지보수성·경계, CI가 자동 검사. `/git-pr-feedback`으로 반영. 둘이 초록이고 코멘트가 실제로 있었는지 본 뒤 `/git-pr-merge`로 squash 병합. main 이력은 PR 단위다.

## 10단계. 세션 마감

`/retro`. 사람이 치지 않아도 에이전트가 계기에 돌린다. 계기는 스킬 description에 적는다("세션이 끝나면" 같은 관찰 불가능한 것이 아니라 일지의 "다음" 갱신, 마무리 발화). 원본 스킬의 플래그는 부록 A. 후보를 심각도 순으로 내놓으면 승인한 것만 반영한다. 기계적 위반은 린터 규칙이나 훅으로, 판단 기준만 `CODING_STANDARDS.md`로, 지침이 길어졌으면 잘라낸다. `/context`로 항상 로드 분량을 실측해 늘었으면 3단계의 배치 기준으로 다시 나눈다. 승격 사다리는 이렇다. 같은 주의를 세 번 손으로 되풀이하면 지침 후보, 지침으로 적은 뒤에도 어겨지면 훅 후보. 훅은 실제로 안 지켜지는 것이 확인된 뒤에만 더한다. 세션 끝에 메모리에 일지 위치, 다음 할 일, 기한을 한 줄로 남긴다. 다음 세션이 일지부터 읽게 하는 장치다.

## 첫날 종료 체크리스트

- [ ] superpowers 비활성, 전역 CLAUDE.md 비어 있음, 프로젝트가 관리하는 스킬의 전역 사본 없음, 안 쓰는 전역 스킬은 `skillOverrides`로 꺼짐
- [ ] `.claude/skills/`에 12개 스킬, `npx skills ls`로 확인
- [ ] `CLAUDE.md` 200줄 이하. 레이어 역할, 지도(언제 읽나), 검증 명령, 작업 규약, 교정 루프와 로드 시점 표, 환경 함정. `@` 임포트는 principles.md 하나
- [ ] `docs/agents/issue-tracker.md`에 Jira 흐름 기록
- [ ] `docs/constitution/` 세 파일 빈 칸 없음, 한국어. 디렉터리별 규칙은 `.claude/rules/`
- [ ] `CODING_STANDARDS.md` 존재, 판단 기준 비어 있음
- [ ] 테스트, 린트, 타입체크 명령 통과, 가드레일 하나 이상
- [ ] 첫 커밋 완료. 원격 생성과 푸시, main 보호, 첫 PR이 CI를 통과
- [ ] PR 템플릿, commit-msg 훅(빨강 확인), CI 워크플로, `.coderabbit.yaml`, Claude Code Review 워크플로, coderabbit-review 서브에이전트
- [ ] 봇 전제 둘(`CLAUDE_CODE_OAUTH_TOKEN` 시크릿, CLI 로그인). 첫 PR에서 Claude 코멘트 확인. CodeRabbit App은 공개 저장소나 유료일 때만
- [ ] `/context` 실측값을 일지나 ADR에 기록
- [ ] `docs/PRD.md` 한 장, `docs/adr/README.md` 색인, 지침 검사 훅
- [ ] `docs/journal/` 첫 파일과 기록 규칙, `.scratch/plan.md` 첫 판, `.claude/rules/` 디렉터리별 규칙, README의 원천 표

## 부록 A. 세팅 중 실제로 걸린 함정

문서를 읽어서는 알 수 없고 겪어야 아는 것. ai-agent-platform과 agent 두 저장소의 실측이다. 원칙 하나로 요약하면 **조용히 통과하는 것을 시끄럽게 만든다.**

| 함정 | 증상 | 대응 |
|---|---|---|
| PowerShell here-string | `@`가 커밋 메시지에 새어 들어감 | 여러 줄은 파일로. 지침만으로는 새 세션에서 2/3 위반이라 훅이 거부 |
| 큰 heredoc | Bash 도구의 파서가 깨져 아무것도 실행되지 않음 | 긴 스크립트는 파일로 쓰고 셸에는 경로만 |
| `PYTHONUTF8=1` 누락 | 한글 출력이 cp949로 깨지고 일부 검사가 통째로 안 돎 | 명령 앞에 항상. pytest는 conftest에서 stdout 재설정 |
| Git Bash의 `python` | Windows 스토어 스텁이라 아무것도 안 함 | `uv run python` 또는 `py` |
| 파이프 뒤의 `&&` | 파이프 마지막 명령의 종료 코드만 봄 | 판정 명령은 파이프 없이 |
| Windows CRLF가 훅 경로를 오염 | 포매터가 엉뚱한 경로를 받음 | 훅에서 `tr -d '\r'`, `.gitattributes`로 LF 고정 |
| Git Bash `echo`가 백슬래시를 먹음 | JSON 페이로드가 안 파싱돼 훅 시험이 조용히 헛돎 | 페이로드도 파일로 |
| 추적 파일 0개에서 `pre-commit run --all-files` | 훅 전부 "no files to check"로 exit 0 | 스테이징 뒤 다시 돌리고 `always_run` |
| CI 경로 필터 미매칭 | 필터 구멍이 조용히 job을 skip | 미매칭을 실패로 승격 |
| 환경 부재로 skip된 테스트 | 초록으로 보임 | CI에서는 에러. LLM 테스트는 키 없으면 실패 |
| 전역 스킬이 프로젝트 스킬을 이김 | `npx skills update` 뒤 낡은 전역이 조용히 이김 | 프로젝트가 관리하는 스킬의 전역 사본을 두지 않는다 |
| 스킬의 `disable-model-invocation` | 지침에 "자동으로 돌린다"고 써도 에이전트가 그 스킬을 못 부름 | 프로젝트 사본에서 플래그를 빼고, 계기를 지침에 적는다. `npx skills update`가 되돌리므로 갱신 뒤 확인 |
| ini 계열 파일의 한글 | 환경변수로도 인코딩을 못 바꿔 죽음 | ASCII만 |
| 셸 체인이 앞 명령의 실패를 무시 | 스크립트가 문법 오류로 안 돌았는데 뒤의 커밋이 그대로 실행돼 메시지가 내용을 앞지름 | 판정 명령 뒤에 `\|\| exit 1`. 커밋 전에 `git show --stat`으로 내용을 본다 |
| 봇 리뷰의 초록 착시 | 시트 미할당·무료 플랜이면 CodeRabbit이 Walkthrough만 남기고 `pass`, 시간당 한도를 넘어도 `pass`. Claude Code Review 플러그인은 지적이 없으면 코멘트 없이 `pass`가 되곤 했고, 워크플로를 바꾼 PR에서는 파일이 기본 브랜치와 다르다는 검증에 걸려 건너뛰며 `pass`다 | 비공개+무료면 CodeRabbit PR 리뷰를 끄고 CLI만. Claude는 플러그인 대신 직접 프롬프트로 요약 코멘트를 완료 조건에 걸고 "코멘트 0개면 실패" 스텝을 둔다. `show_full_output`으로 로그를 남긴다. 워크플로 변경은 별도 PR 먼저 |
| CodeRabbit CLI 무료 한도 | 주기당 3회. 커밋마다 돌리면 첫날에 소진 | PR마다 한 번. `coderabbit --usage`로 남은 횟수 확인 뒤 실행 |
| `.coderabbit.yaml`의 제외 목록을 로컬 CLI도 읽음 | 테스트 경로를 빼면 로컬에서도 리뷰를 못 받음 | 제외는 생성물·락파일만 |
| 무료 플랜 비공개 저장소의 보호 브랜치 | `gh api .../branches/main/protection`이 403 "Upgrade to GitHub Pro". 룰셋도 같다 | 공개 전환이나 Pro. 아니면 `/git-pr-merge`의 `gh pr checks`가 유일한 게이트라 직접 `gh pr merge`를 치지 않는다 |

## 부록 B. 세팅 프롬프트와 스킬·서브에이전트를 쓸 때

하네스를 한 번에 여러 개 만드는 작업은 프롬프트 설계가 결과를 좌우한다. ai-agent-platform AAPP-48에서 효과가 확인된 기법.

1. Phase 0에 "파일 생성 금지, 조사 결과 보고, 승인 대기"를 명시한다. 확인 못 한 항목은 "미확인"으로 두고 추측으로 채우지 않는다. 없으면 존재하지 않는 경로가 스킬에 박힌다.
2. "만들지 않는 것" 절을 이유와 함께 쓴다. 미룬 이유가 곧 나중의 착수 조건이다.
3. 읽기 전용 서브에이전트에는 이유를 적는다. "수정 권한이 있으면 판단이 '이게 맞나'에서 '통과시키자'로 기운다."
4. 검토 에이전트에 "blocker 없음은 정상적이고 흔한 결과다. 지적할 것을 만들어내지 마라"를 명시한다.
5. 훅·API처럼 버전에 따라 바뀌는 것은 기억이 아니라 문서를 확인하라고 지시한다.
6. 외부 자료는 "참고하되 복사 금지"로, 가져오지 않을 부분까지 적는다. 참고 대상만 주면 전제째로 복사된다.
7. 기존 파일은 "덮어쓰지 말고 병합, 충돌하면 멈추고 보고"로 고정한다.
8. 헷갈리는 용어는 프롬프트 안에서 정의한다.

## 세 번째 프로젝트가 끝나면

이 런북을 세 번 돌린 뒤 매번 같은 곳을 손봤다면 그 부분만 본인 스킬로 만든다. 그 전에는 도구를 만들지 않는다.
