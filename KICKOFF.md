# 새 프로젝트 첫날 킥오프 런북

원본은 이 파일(`C:/project/agent/KICKOFF.md`)이다. 새 프로젝트는 이 파일을 복사해서 시작하고, 런북을 고칠 일이 생기면 여기를 고친 뒤 복사본에 반영한다.

기준일 2026-09-19. 결정: mattpocock 스킬 유지, superpowers 비활성, 교정 루프는 `/retro` 수동 회고, 지침은 한국어. 스킬(`.claude/skills/`)과 교정 루프 문단(`CLAUDE.md`)은 모두 프로젝트 레벨에 둔다. 전역에는 프로젝트와 무관한 개인 워크플로 스킬(git-*, jira-*)만 남기고, 프로젝트가 관리하는 스킬의 전역 사본은 두지 않는다.

전제: 무엇을 만들지 안다. 모르면 `/grill-me`로 브레인스토밍부터 하고 이 런북은 그 뒤에 시작한다.

## 어디에 무엇이 사는가

| 위치 | 내용 | 이유 |
|---|---|---|
| `~/.claude/CLAUDE.md` (전역. Windows는 `C:/Users/<user>/.claude/CLAUDE.md`) | 비워 둔다 | 교정 루프 문단은 `CODING_STANDARDS.md`와 `/retro`를 가리키므로, 그것들이 없는 다른 프로젝트에 새면 안 된다 |
| `~/.claude/skills/` (전역) | 프로젝트와 무관한 개인 워크플로 스킬만(git-*, jira-*). 프로젝트가 안 쓰는 것은 그 프로젝트의 `skillOverrides`로 끈다 | 전역은 같은 이름의 프로젝트 스킬을 이기므로, 프로젝트가 관리하는 스킬(grilling 등)의 전역 사본을 두면 `npx skills update` 뒤 낡은 전역이 조용히 이긴다 |
| `.claude/skills/` (프로젝트) | mattpocock 엔지니어링 스킬 전부 + grill-me | git에 커밋, 프로젝트마다 버전 고정. `skills-lock.json`이 출처와 해시를 기록 |
| `.claude/settings.json` (프로젝트) | `enabledPlugins`(LSP 등 프로젝트 플러그인), `skillOverrides`(이 프로젝트가 안 쓰는 전역 스킬을 `"off"`) | 저장소와 함께 간다 |
| `CLAUDE.md` (프로젝트) | 다른 파일을 가리키는 포인터, 검증 명령, 교정 루프 문단 | 규칙은 여기 쓰지 않는다. 교정 루프는 규칙이 아니라 규칙을 만드는 절차다 |
| `docs/constitution.md` | 헌법. 원칙, 스택, 저장소 구조, 검증 의무, CI, 이슈관리 | 프로젝트당 한 번 |
| `CODING_STANDARDS.md` | 검사로 못 잡는 판단 기준 | code-review 스킬이 읽음 |
| `CONTEXT.md`, `docs/adr/` | 용어집, 결정 기록 | domain-modeling이 씀 |
| `docs/agents/` | 이슈 트래커 규칙, 도메인 문서 위치 | setup 스킬이 씀 |
| `docs/journal/` | 진행 일지. 단계별 사실, 사용자 프롬프트 원문, 갈린 곳과 번복 | 세션을 넘어 이어가고 `/retro`의 입력 |
| `.scratch/` | 로컬 이슈 트래커(명세, 티켓) | 원격 없는 프로젝트의 유일한 작업 기록. 커밋한다 |

주의: 같은 이름의 스킬이 전역과 프로젝트에 둘 다 있으면 전역이 이긴다(공식 문서: enterprise > personal > project). 그래서 프로젝트가 관리하는 스킬의 전역 사본은 두지 않는다. 전역 스킬을 `skillOverrides`로 끄면 같은 이름의 프로젝트 스킬이 살아나는지는 문서에 없으므로, 중복은 끄지 말고 옮긴다.

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

## 지도
- 헌법(타협 불가 원칙, 스택, 저장소 구조, 검증 의무): docs/constitution.md
- 코딩 표준(리뷰 시 적용): CODING_STANDARDS.md
- 용어집: CONTEXT.md, 결정 기록: docs/adr/

## 검증 명령
- 테스트:
- 린트:
- 타입체크:

## 교정 루프
- 내가 네 결과를 고치거나 되돌리면, 먼저 그 실수를 테스트·린트·훅 같은 자동 검사로 잡을 수 있는지 판단하고 검사를 제안한다.
- 자동 검사로 잡을 수 없는 판단 기준만 CODING_STANDARDS.md에 한 줄로 제안한다. 내가 "규칙으로"라고 말하기 전에는 추가하지 않는다.
- 이 파일에는 규칙을 쓰지 않는다. 다른 파일을 가리키는 포인터만 둔다.
- 의미 있는 세션이 끝나면 /retro를 권한다.

## 원칙
- 답변과 문서는 한국어로 쓴다.
```

## 4단계. /setup-matt-pocock-skills

한 번 실행한다. 세 가지를 묻는다.

- 이슈 트래커: GitHub, GitLab, 로컬 마크다운(`.scratch/<feature>/`), 기타. Jira는 "기타"를 고르고 한 단락으로 설명한다. 예: "이슈는 Jira. 티켓 생성은 /jira-create, 착수는 /jira-start(브랜치와 Draft PR), 커밋과 진행 기록은 /jira-commit, 완료는 /jira-complete. 브랜치 이름은 feature/[이슈번호]-[kebab-설명]." 그대로 `docs/agents/issue-tracker.md`에 기록된다.
- 트리아지 라벨: triage 스킬을 안 깔았으므로 건너뛴다.
- 도메인 문서: 단일 컨텍스트 기본(루트 `CONTEXT.md` + `docs/adr/`). 모노레포면 멀티 컨텍스트.

산출물: `docs/agents/issue-tracker.md`, `docs/agents/domain.md`, `CLAUDE.md`의 `## Agent skills` 블록. 쓰기 전에 초안을 보여 주니 한국어로 고쳐서 승인한다.

## 5단계. 헌법

Spec Kit 템플릿을 내려받아 채운다. Spec Kit 자체는 설치하지 않는다. Spec Kit의 specify, clarify, plan, tasks, implement, analyze는 2단계에서 설치한 to-spec, to-tickets, implement, code-review와 1:1로 겹쳐서 둘 다 깔면 실행기가 둘이 된다. mattpocock에 없는 것은 헌법뿐이고, 헌법 스킬이 하는 인터뷰는 grill-me가 대신한다. 반대로 Spec Kit 파이프라인을 쓰고 싶으면 to-spec, to-tickets, implement, code-review를 빼고 `specify init --integration claude`로 대체한다. 어느 쪽이든 파이프라인은 한 벌만.

```bash
curl.exe -L -o docs/constitution.md https://raw.githubusercontent.com/github/spec-kit/main/templates/constitution-template.md
```

채우는 방법: 에이전트에게 "`/grill-me`로 docs/constitution.md를 채우자. 한국어로. 다 채울 때까지 물어라"라고 시킨다. 이것이 킥오프 인터뷰다. 템플릿 섹션 대응:

| 템플릿 섹션 | 채울 내용 |
|---|---|
| 원칙 1~5 | 타협 불가 원칙. 예: 테스트 먼저, 타입 any 금지, 서비스 간 DB 직접 접근 금지 |
| 자유 섹션 1 | 스택과 구조. 멀티레포/모노레포, 백엔드, 프론트엔드, 패키지 매니저, 디렉터리 규칙 |
| 자유 섹션 2 | 검증과 운영. 테스트 의무, CI 도구, 이슈관리(Jira), 브랜치와 PR 규칙 |
| 거버넌스 | 개정 절차. 헌법 변경은 ADR을 남긴다 |

빈 칸 없이 채운다. 모르는 항목은 "미정"이 아니라 결정한다. 결정 못 하면 그릴링을 더 한다.

**한 파일로 시작한다.** 첫날 분량은 100줄 안팎이라 나눌 이유가 없고, 버전과 개정일이 한 곳에 있어 개정 관리가 쉽다. 이 파일은 `CLAUDE.md`가 가리키기만 하고 매 세션 자동으로 읽히지는 않는다. 항상 읽혀야 하는 것은 원칙 5개뿐이므로, 파일이 작을 때는 `CLAUDE.md`에 `@docs/constitution.md`로 임포트해도 되고, 커지면 원칙만 `docs/constitution/principles.md`로 떼어 임포트하고 나머지(`tech.md`, `structure.md`)는 포인터로 둔다.

나누는 기준은 주제가 아니라 셋이다. (1) 150줄을 넘거나 에이전트가 규칙을 놓치기 시작할 때. (2) 어떤 절이 다른 절과 다른 주기로 바뀔 때. 구조는 패키지를 추가할 때마다 바뀌고 원칙은 거의 안 바뀐다. (3) 어떤 절이 저장소 일부에만 해당할 때. 이 경우는 파일을 나누는 게 아니라 그 디렉터리의 `CLAUDE.md`로 옮긴다(중첩 지원). 모노레포는 루트 헌법 하나에 패키지별 중첩 `CLAUDE.md`가 기본형이다. 검증 명령처럼 매 세션 필요하고 자주 바뀌는 것은 헌법이 아니라 `CLAUDE.md`에 둔다.

## 6단계. CODING_STANDARDS.md 뼈대

```markdown
# 코딩 표준

code-review 스킬이 리뷰할 때 읽는 파일. 자동 검사(린트, 타입, 테스트, 훅)로 잡을 수 있는 것은 여기 쓰지 않고 검사를 만든다. 아래 항목은 /retro가 제안하고 사용자가 "규칙으로"라고 승인한 것만 남긴다.

## 판단 기준
(비어 있음)
```

## 7단계. 스캐폴딩과 검증 명령

에이전트에게 "헌법대로 골격을 만들어라"라고 시킨다. 프레임워크 생성기(`create-next-app` 같은 것)는 에이전트가 돌린다. 종료 조건은 세 명령이 실제로 통과하는 것이다.

- 테스트 명령 1개 (샘플 테스트 하나 포함)
- 린트 명령 1개
- 타입체크 명령 1개 (해당 언어면)

통과한 명령을 `CLAUDE.md`의 검증 명령 칸에 적는다. 최소 가드레일도 이때 건다. pre-commit 훅이든 CI 잡이든 린트와 테스트가 자동으로 도는 곳 하나. retro 기준으로 가드레일 없는 저장소는 그 자체가 결함이다.

선택: 스택이 정해졌으면 LSP 플러그인을 프로젝트 스코프로 설치한다. `.claude/settings.json`의 `enabledPlugins`에 기록되어 저장소와 함께 간다. 같은 파일의 `skillOverrides`에 이 프로젝트가 안 쓰는 전역 스킬(jira-*, git-pr* 등)을 `"off"`로 적어 매 세션 컨텍스트와 오트리거를 줄인다. 언어 서버 바이너리는 따로 설치해야 한다.

```bash
claude plugin install typescript-lsp@claude-plugins-official --scope project
```

## 8단계. 첫 커밋

```bash
git add -A && git commit -m "chore: 하네스 킥오프 (헌법, CLAUDE.md, 코딩 표준, 스킬)"
```

포함: `.claude/skills/`, `.claude/settings.json`(있으면), `CLAUDE.md`, `CODING_STANDARDS.md`, `docs/`, 골격.

## 9단계. 첫 기능

기능마다 이 순서. 30분 미만이거나 파일 3개 미만이면 전부 건너뛰고 바로 시킨다.

1. `/grill-with-docs` 로 설계 인터뷰. 용어는 `CONTEXT.md`, 결정은 `docs/adr/`에 쌓인다.
2. `/to-spec` 으로 대화를 명세로.
3. `/to-tickets` 로 수직 슬라이스 티켓. Jira면 4단계에서 적은 흐름대로 `/jira-create`.
4. `/implement` 로 구현. tdd 스킬이 테스트 먼저를 강제한다.
5. `/code-review main` 으로 표준 축과 명세 축 리뷰.

## 10단계. 세션 마감

`/retro`. 후보를 심각도 순으로 내놓으면 승인한 것만 반영한다. 기계적 위반은 린터 규칙이나 훅으로, 판단 기준만 `CODING_STANDARDS.md`로, 지침이 길어졌으면 잘라낸다.

## 첫날 종료 체크리스트

- [ ] superpowers 비활성, 전역 CLAUDE.md 비어 있음, 프로젝트가 관리하는 스킬의 전역 사본 없음, 안 쓰는 전역 스킬은 `skillOverrides`로 꺼짐
- [ ] `.claude/skills/`에 12개 스킬, `npx skills ls`로 확인
- [ ] `CLAUDE.md` 30줄 이내, 규칙 없음, 포인터·검증 명령·교정 루프 문단만
- [ ] `docs/agents/issue-tracker.md`에 Jira 흐름 기록
- [ ] `docs/constitution.md` 빈 칸 없음, 한국어
- [ ] `CODING_STANDARDS.md` 존재, 판단 기준 비어 있음
- [ ] 테스트, 린트, 타입체크 명령 통과, 가드레일 하나 이상
- [ ] 첫 커밋 완료

## 세 번째 프로젝트가 끝나면

이 런북을 세 번 돌린 뒤 매번 같은 곳을 손봤다면 그 부분만 본인 스킬로 만든다. 그 전에는 도구를 만들지 않는다.
