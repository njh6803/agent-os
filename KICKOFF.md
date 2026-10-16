# 새 프로젝트 첫날 킥오프 런북

원본은 이 파일(`C:/project/agent/KICKOFF.md`, 원격 `github.com/njh6803/agent-os`)이다. 새 프로젝트는 그 저장소를 clone해 두고 이 파일과 `kickoff/`(템플릿·부록)와 7단계의 복사 목록을 상대 경로로 가져와 시작하고, 런북을 고칠 일이 생기면 여기를 고친 뒤 복사본에 반영한다. 아래에서 "런북 저장소"는 그 clone이다. **이 판을 처음부터 끝까지 실행한 것은 첫 프로젝트(agent-os, 2026-09-19) 한 번이고 그 뒤의 수정은 실행으로 검증되지 않았다.** 두 번째 프로젝트의 실행이 이 판의 검증이다. 어긋나면 내 실수로 읽지 말고 이 원본을 고친다.

**시작.** 처음 쓰는 기계면 이 런북 저장소를 clone한다. 새 프로젝트 폴더를 만들어 그 폴더에서 Claude Code 세션을 열고, 아래 한 줄의 `<clone>`을 그 clone의 절대 경로(슬래시. agent-os의 기계면 `C:/project/agent`)로 바꿔 붙여 넣는다. 세션이 진행 규율 `kickoff/runner.md`를 읽고, 사용자 레벨 스킬 `/kickoff`를 만들 허락을 물은 뒤 같은 세션에서 `/kickoff`를 치게 한다. 그 뒤로는(이미 `/kickoff`가 있는 기계면 처음부터) 새 프로젝트 폴더의 세션에서 한 줄 대신 `/kickoff`로 시작하고, 끊기거나 압축된 뒤에도 `/kickoff`로 잇는다. 진행은 그 폴더의 `.scratch/kickoff.md`에 남는다.

```text
`<clone>/kickoff/runner.md`를 Read 도구로 읽고 그대로 따른다.
```

결정 기준일 2026-09-19, 마지막 갱신 2026-10-13. 결정: mattpocock 스킬 유지, superpowers 비활성, 교정 루프는 retro 스킬의 계기 자동 회고(10단계), 지침은 한국어. 스킬(`.claude/skills/`)과 교정 루프 문단(`CLAUDE.md`)은 모두 프로젝트 레벨에 둔다. 전역에는 프로젝트와 무관한 개인 워크플로 스킬(git-*, jira-*)과 킥오프 진행 스킬 `kickoff`만 남기고, 프로젝트가 관리하는 스킬의 전역 사본은 두지 않는다.

전제 셋. 무엇을 만들지 안다(준비가 처음에 묻고, 모르면 거기서 브레인스토밍부터 한다). 원격은 GitHub이고 `gh`가 있다(GitLab이면 1·8·9단계의 `gh` 명령, `tools/hook_pr_next_session.py`의 정규식과 MCP 도구 이름, 전역 `git-pr*` 스킬, Claude Code Review 워크플로를 대체해야 한다 — 이 런북은 그 길을 적지 않는다). 하네스 런타임은 파이썬이다(훅·검사·pre-commit·변이 도구가 파이썬 스크립트다. 파이썬 프로젝트가 아니어도 개발 도구로 파이썬 하나와 uv를 두면 그대로 돈다. 7단계).

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
| `~/.claude/skills/` (전역) | 프로젝트와 무관한 개인 워크플로 스킬(git-*, jira-*)과 `kickoff`(런북 clone의 진행 규율 `kickoff/runner.md`를 가리키는 짧은 스킬. 진행 규율의 시작 확인이 만든다)만. 프로젝트가 안 쓰는 것은 그 프로젝트의 `skillOverrides`로 끈다 | 전역은 같은 이름의 프로젝트 스킬을 이기므로, 프로젝트가 관리하는 스킬(grilling 등)의 전역 사본을 두면 `npx skills update` 뒤 낡은 전역이 조용히 이긴다 |
| `.claude/skills/` (프로젝트) | mattpocock 엔지니어링 스킬 전부 + grill-me | git에 커밋, 프로젝트마다 버전 고정. `skills-lock.json`이 출처와 해시를 기록 |
| `.claude/settings.json` (프로젝트) | `enabledPlugins`(LSP 등 프로젝트 플러그인), `skillOverrides`(이 프로젝트가 안 쓰는 전역 스킬을 `"off"`), `hooks`(훅의 등록. 훅 파일만 복사하면 아무것도 발동하지 않는다), `permissions.deny`(`.env`의 Read·Edit 거부) | 저장소와 함께 간다 |
| `CLAUDE.md` (프로젝트) | 다른 파일을 가리키는 포인터, 검증 명령, 교정 루프 문단 | 규칙은 여기 쓰지 않는다. 교정 루프는 규칙이 아니라 규칙을 만드는 절차다 |
| `docs/constitution/` | 헌법. `principles.md`(원칙·거버넌스, 임포트), `tech.md`(스택), `operations.md`(검증·운영). 디렉터리별 규칙은 `.claude/rules/*.md`+`paths` | 프로젝트당 한 번 |
| `CODING_STANDARDS.md` | 검사로 못 잡는 판단 기준 | code-review 스킬이 읽음 |
| `CONTEXT.md`, `docs/adr/` | 용어집, 결정 기록 | domain-modeling이 씀 |
| `docs/agents/` | 이슈 트래커 규칙, 도메인 문서 위치 | setup 스킬이 씀 |
| `.github/` | PR 템플릿, CI 워크플로, Claude Code Review 워크플로 | 첫날. 런북 저장소에서 복사해 검증 명령만 바꾼다 |
| `.coderabbit.yaml` | CodeRabbit 설정. 층별 path_instructions, 린터 끔, 제외는 생성물·락파일·남이 쓴 스킬 사본만 | PR 봇과 로컬 CLI가 같은 파일을 읽는다. PR 자동 리뷰는 공개 저장소나 유료일 때만 켠다(2026-09-20 실측) |
| `.claude/agents/` | 프로젝트 서브에이전트. coderabbit-review(CLI 실행과 트리아지), bug-perf-review(CLI가 못 돌 때 버그·성능 리뷰), spec-reviewer(명세 검토). 모두 Edit·Write 없음 | 스킬은 절차, 서브에이전트는 격리된 컨텍스트에서 도구를 돌리고 보고만 한다 |
| `tools/` | 배포되지 않는 저장소 유틸. 훅(`hook_*.py`)과 그 실행 래퍼(`launch_hook.py`), 검사(`check_*.py`), 검사 러너(`run_checks.py`), 훅 러너(`run_hooks.py`와 페이로드 표), 변이 도구, Actions 실행 요약 | 훅과 CI, 그리고 리뷰 봇 판정이 부른다. 규약은 `.claude/rules/tools.md` |
| `docs/journal/` | 진행 일지. 단계별 사실, 사용자 프롬프트 원문, 갈린 곳과 번복 | 세션을 넘어 이어가고 `/retro`의 입력 |
| `.scratch/` | 로컬 이슈 트래커(명세, 티켓, 프로브)와 회고 대기열(`retro-queue.md`) | 원격 트래커를 쓰지 않는 프로젝트의 작업 기록. 커밋한다 |

주의: 같은 이름의 스킬이 전역과 프로젝트에 둘 다 있으면 전역이 이긴다(공식 문서: enterprise > personal > project). 그래서 프로젝트가 관리하는 스킬의 전역 사본은 두지 않는다. 전역 스킬을 `skillOverrides`로 끄면 같은 이름의 프로젝트 스킬이 살아나는지는 문서에 없으므로, 중복은 끄지 말고 옮긴다.

## 이 런북을 실행하는 에이전트에게

첫 프로젝트(agent, 2026-09-19~20)에서 에이전트가 실제로 저지른 것에서 나온 규칙이다. 1~6은 세팅 중, 7~9는 원격과 봇을 붙일 때.

1. **사용자가 경험에서 제안한 것은 판단해서 자리에 넣는다.** "그 내용이 어딘가에 있다"는 "행동이 일어나는 자리에 있다"가 아니다. 지침의 값은 로드 시점이 정한다. 3단계의 표로 자리를 정해 넣고, 거부는 이유를 일지에 남긴다. "이미 있음", "나중에"로 넘기지 않는다.
2. **옆 프로젝트의 원재료를 가리키면 원문을 읽는다.** 요약하지 말고 항목별로 채택·수정 채택·거부를 근거와 함께 보고한 뒤, 채택한 것은 그 자리에서 넣는다. 원재료: `ai-agent-platform/docs/setup-playbook.md`, `docs/setup-prompts/01~09`, `AGENTS.md`, `.claude/rules/`.
3. **결정은 사용자 것, 사실 조사는 에이전트 것.** 사용자에게 파일을 열어 확인하라고 하지 않는다. 서브에이전트로 조사하고, 결정만 추천을 맨 앞에 둔 선택 화면(Claude Code는 `AskUserQuestion`)으로 묻는다.
4. **일지를 준비에서 만들고 매 단계 적는다.** 사용자 프롬프트 원문(결정·방향 전환·설계 질문), 벗어난 점, 세션 끝에 "추천과 결정이 갈린 곳"과 "에이전트가 번복하거나 고친 것". 이 두 절이 `/retro`의 입력이다.
5. **하네스를 바꾸면 실행으로 확인하고, 새 검사는 변이로 빨강을 본다.** 파일이 그럴듯한 것은 확인이 아니다. 스크립트를 셸 체인으로 돌릴 때는 실패 시 멈추게 한다(`|| exit 1`). 커밋 전에 `git show --stat`으로 내용을 본다.
6. **한 파일에 모으지 않는다.** 헌법은 처음부터 셋(원칙·스택·운영), 디렉터리 규칙은 `.claude/rules/`+`paths`, 트리는 README, 미래 배치와 범위는 `.scratch/plan.md`. `@` 임포트는 원칙 하나뿐.
7. **옆 프로젝트의 구성을 옮기기 전에 이 계정·플랜에서 실측한다.** CodeRabbit PR 리뷰는 무료 플랜의 비공개 저장소에서 요약만 남기고 초록이었고, 보호 브랜치는 403이었다. 플랜 차이 없이 옮겨 PR 둘(#3·#4)로 되돌렸다. 도구를 켜기 전에 요금·플랜 조건을 보고, 문서에 없으면 작은 PR 하나로 실측한 뒤 채택한다. 일지 "CodeRabbit App".
8. **결정을 바꾸면 옛 표현을 grep해 잔존을 0으로 만든다.** "원격·PR은 첫날부터"로 바꾸고도 `skillOverrides`의 git-pr 셋을 끈 채 두었다. 규약 4가 있는데도 놓쳤다. 옛 낱말(도구 이름, 개수, 담당)을 저장소 전체에서 찾고 셀프 리뷰에도 같은 grep을 시킨다. 규약 4에 넣었다. 일지 "번복".
9. **확인 안 한 사실은 추정이라고 적는다.** "설치하면 14일 체험이 켜진다"를 요금 페이지 문구에서 추정해 사실처럼 썼고 실제는 Free였다. 실측한 것에만 "실측"을 붙인다. 일지 "CodeRabbit App".

## 준비

새 프로젝트 폴더를 만들고 그 폴더에서 Claude Code 세션을 연다. 준비는 그 세션에서 시작한다. 원격에 기대지 않는 사람 몫(무엇을 만드나, 도구와 `gh` 로그인, 저장소의 주인과 이름, 공개 여부, CodeRabbit CLI 로그인)을 여기서 먼저 모은다. 8단계까지 가서 흩어진 자리마다 사람을 불러내지 않기 위해서다. 공개 여부는 7단계의 `.coderabbit.yaml`과 8단계의 보호 브랜치가 기대므로 0단계 전에 정한다(agent-os ADR 0028).

**진행 파일.** 첫 일로 `kickoff/progress-template.md`에서 새 프로젝트의 진행 파일 `.scratch/kickoff.md`를 만든다. `.scratch/`도 이때 생긴다. 단계마다의 상태와 사람 몫의 대기·끝남·건너뜀이 여기 남고, `/kickoff`가 이 파일의 첫 미완 단계부터 잇는다. 칸과 상태의 뜻은 그 템플릿이, 채우는 법은 진행 규율(`kickoff/runner.md`)이 원천이다.

**일지.** 이어서 `docs/journal/<날짜>-01-kickoff.md`(agent-os의 첫 일지 `2026-09-19-kickoff.md`는 이 규칙 전의 이름이다)를 만든다. `docs/`도 이때 생긴다. 준비의 결정부터 적을 곳이 있게 하기 위해서다. 머리말에 기록 규칙을 적는다. 결정·방향 전환·설계 질문에 해당하는 사용자 프롬프트는 `> 사용자:` 인용으로 원문 그대로(오타도 고치지 않는다), 선택 화면에서 고른 것은 질문과 고른 선택지의 설명을 같은 인용으로, 단순 조작 지시는 제외, 에이전트의 말은 옮기지 않고 세션 끝에 "추천과 결정이 갈린 곳"과 "에이전트가 번복하거나 고친 것"만 한 줄씩. 뒤의 일지도 `docs/journal/<날짜>-<NN>-<슬러그>.md`이고 `NN`은 그날의 순번이다. 같은 날 세션 둘이 쓰면 순번이 갈라 준다.

**무엇을 만드나.** 만들 것을 한두 문장으로 정한다.

사람 몫(결정): 무엇을 만드나. 이 세션의 선택 화면에서 한두 문장으로 답하거나, 아직 모르면 브레인스토밍부터 한다고 고른다.

브레인스토밍을 고르면 세션은 런북 저장소의 `.claude/skills/grilling/SKILL.md`를 Read로 읽어 따르고, 그 사본이 가리키는 agent-os 고유의 참조(그 저장소의 `CLAUDE.md`, 이슈 트래커, 대기열)는 따르지 않는다. 이 시점에는 새 프로젝트의 스킬이 아직 없고, 0단계를 마친 기계에는 전역 grilling도 없다(0단계가 백업 폴더로 옮긴다).

**도구.** 세션이 `git`, `gh`, `uv`, `npx`, `coderabbit`의 `--version`을 친다. 2단계가 `npx`를, 7단계가 `uv`와 파이썬을 쓰므로 그 단계에서 막히기 전에 본다. CodeRabbit CLI를 설치하는 단계는 이 런북에 없어 여기서 본다. 설치 길은 OS마다 달라 이 런북이 갖지 않는다.

사람 몫(사람만): `--version`이 실패한 도구를 이 기계에 설치한다(없는 도구가 있을 때만). 확인: 그 도구의 `--version`

**`gh` 로그인과 `user` 범위.** 세션이 `gh auth status`를 본다. 로그인한 활성 계정이 있고, 그 계정의 `Token scopes` 줄에 따옴표로 싼 낱말 `'user'`가 있으면 된 것이다. 글자 `user`만 찾으면 `'read:user'`나 `'user:email'`도 맞고, 계정이 여럿이면 활성 계정이 아닌 줄에서 맞을 수 있다. `user` 범위는 아래 Actions 사용량을 읽는 데 든다. `gh auth login`의 브라우저 흐름은 `user`를 청하지 않으므로(`kickoff/facts.md`) 로그인할 때 `-s user`로 함께 받는다. 그러면 브라우저 승인이 한 번으로 끝난다.

사람 몫(사람만): 터미널에서, 로그인이 안 돼 있으면 `gh auth login -s user`를, 로그인했는데 범위에 `user`가 없으면 `gh auth refresh -h github.com -s user`를 친다(둘 가운데 하나일 때만). `user`는 프로필 쓰기까지 주는 넓은 범위이고, 나중에 `gh auth refresh -h github.com -r user`로 뺄 수 있다. 확인: `gh auth status`의 활성 계정과, 그 계정의 `Token scopes`에 따옴표로 싼 낱말 `'user'`

**주인과 이름.** 세션이 `gh api user --jq .login`과 `gh api user/orgs --jq '.[].login'`으로 후보를 보인다. 개인 계정의 `<login>`은 git의 사용자 이름과 다를 수 있다. 선택 화면의 선택지는 넷까지라, 후보가 넷을 넘으면 개인 계정과 조직 셋을 보이고 나머지는 직접 입력으로 받는다.

사람 몫(결정): 저장소의 주인(개인 계정이나 조직)과 저장소 이름.

**플랜과 Actions 사용량.** 공개 여부를 묻기 전에 세션이 읽어 선택 화면의 설명에 넣는다. Actions 무료 분량은 계정 단위라 다른 비공개 저장소가 써 버리면 이 저장소의 잡이 시작조차 안 되고, CI가 게이트라 병합도 막힌다(agent-os PR #10 실측. 주석은 결제 실패를 말하지만 원인은 분량 소진이었다). 공개 저장소는 무제한이다. Claude 리뷰 한 번이 1~10분을 쓴다.

- 플랜: 개인이면 `gh api user --jq .plan.name`, 조직이면 `gh api orgs/<org> --jq .plan.name`이다. 조직의 전체 정보는 조직 소유자이고 classic 토큰에 `admin:org`가 있어야 보인다(GitHub REST orgs 문서). 킥오프는 그 범위를 받지 않는다. 조직 전체를 관리하는 범위라 플랜 하나를 읽는 값으로는 너무 크다. 그래서 조직의 플랜은 대개 빌 것이다(어림. 문서는 전체 정보를 말하고 `plan` 필드를 지목하지 않는다). 비면 플랜을 모르는 채로 묻는다.
- 사용량: 개인이면 `gh api "users/<login>/settings/billing/usage?year=<UTC 연>&month=<UTC 월>"`, 조직이면 같은 쿼리로 `organizations/<org>/settings/billing/usage`다. 조직의 길은 그 조직의 관리자만 부를 수 있다. 경로와 범위의 확인일은 `kickoff/facts.md`다.
- 거르기: 항목에서 `product`가 `actions`이고 `unitType`이 `Minutes`인 것만 고른다. `repositoryName`은 주인 없이 이름만 오므로, `gh repo list <주인> --json name,visibility --limit 1000` 한 번으로 받은 목록과 이름으로 맞춘다. 저장소마다 부르면 그 수만큼 하위 프로세스가 돈다. `PRIVATE`인 저장소의 `quantity`만 `sku`(`Actions Linux`, `Actions Windows` 등)마다 더해 보인다. Windows와 macOS의 배수를 재지 않았으므로 `sku`끼리는 더하지 않는다. 목록에 없는 이름(지운 저장소 등)은 "알 수 없음"으로 따로 보인다. 무료 분량(월 2,000분)은 `kickoff/facts.md`의 값을 함께 보인다.
- 읽지 못하면(조직의 관리자가 아니다, 다른 종류의 토큰이다) 사용량 없이 공개 여부를 묻고, 설명에 읽지 못한 이유를 적는다.

**커밋되는 billing 값.** 진행 파일과 일지는 8단계의 첫 커밋으로 원격에 올라가고, 새 저장소는 공개를 추천받는다. 그래서 두 파일에는 플랜, 공개 여부, 비공개 저장소 Actions 분의 `sku`마다 합계만 적는다. 진행 파일에서는 "준비에서 정한 것" 표가 그 값을 받는다. 다른 저장소의 이름과 금액은 적지 않는다. 일지의 `> 사용자:` 인용이 선택 화면의 설명을 옮길 때도 저장소 이름은 "저장소 N개"로 바꿔 적는다.

**공개 여부.** 선택 화면의 설명에 플랜, 위의 비공개 사용량, 그리고 이 갈림을 넣는다. 무료(`free`)이고 비공개면 보호 브랜치와 룰셋이 403이고 CodeRabbit PR 리뷰는 요약만 남는다. 그러면 처음부터 `/git-pr-merge`가 게이트이고 CodeRabbit은 CLI만 쓴다. 공개면 Actions가 무제한이고 둘 다 무료로 풀린다. agent-os는 이것을 PR을 열고 나서 알아 PR 넷을 되돌리는 데 썼다. 추천은 무료 플랜이면 공개다. 유료이거나 플랜을 모르면 추천 없이 두 갈래를 모두 설명한다. 조직의 플랜은 대개 비어 모르는 쪽이 되고, 조직 저장소의 공개는 그 조직의 코드 공개 결정이라 세션이 추천할 근거도 없다.

사람 몫(결정): 저장소를 공개로 둘지 비공개로 둘지. 이 답이 7단계의 `.coderabbit.yaml`, 8단계의 `gh repo create`와 main 보호를 가른다.

사람 몫(사람만): github.com에서 그 조직의 Billing 화면을 보거나 조직 소유자에게 물어, 이번 달 남은 Actions 분량을 이 세션에 알린다(주인이 조직이고, 위에서 사용량을 읽지 못했고, 비공개를 골랐을 때만). 확인: 없음 — 화면의 값은 사람이 알린다

**CodeRabbit.** 세션이 `coderabbit auth status`를 본다. 출력에 `Seat` 줄이 있으면 로그인한 것으로 보고, 그 값을 진행 파일의 "준비에서 정한 것"과 일지에 적는다. 로그인한 출력의 모양은 agent-os의 명세가 손으로 봤고(CLI 0.7.5, `User info`와 `Review access` 두 절이고 `Seat` 줄은 뒤의 절에 있다) 로그인하지 않은 출력은 보지 못했다. 그래서 이 판단은 그 모양에 기댄다. 그 줄은 `Seat`과 콜론 사이에 공백이 여럿이라(`Seat         : not assigned`) 글자 그대로의 `Seat:`이 아니라 줄 머리의 `Seat`, 공백, 콜론, 값의 모양으로 찾는다. `not assigned`는 실패가 아니다. `not assigned`면 유료 구독 없이는 CLI 축이 비어 있다(agent-os 2026-09-23 실측. 좌석 배정에는 활성 유료 구독이 필요하다, `kickoff/facts.md`). 그러면 PR 직전 리뷰가 대체 경로로 간다(9단계 7). `coderabbit --usage`는 청구 주기 누적만 보여주고 시간당 잔량을 보여주지 않는다.

사람 몫(사람만): 터미널에서 `coderabbit auth login`을 친다(로그인이 안 돼 있을 때만). 확인: `coderabbit auth status`에 `Seat` 줄

## 0단계. 한 번만 하는 전역 준비

프로젝트마다 반복하지 않는다. 기계마다 한 번이다 — agent-os의 기계에서는 2026-09-19에 했고, 새 기계에서만 다시 한다. 이 단계의 일은 모두 저장소 밖(이 기계의 Claude Code 전체)에 닿아 하기 전에 허락을 받는다.

1. superpowers 비활성화 (되돌리려면 `enable`).

사람 몫(허락): 이 기계의 전역 플러그인 superpowers를 `claude plugin disable superpowers@claude-plugins-official`로 끈다(켜져 있을 때만).

```bash
claude plugin disable superpowers@claude-plugins-official
```

2. 전역 스킬 정리. grill-with-docs, domain-modeling, grilling, grill-me는 프로젝트 레벨로 옮길 것이므로 전역 복사본을 백업 폴더로 이동한다. git-*, jira-* 같은 개인 워크플로 스킬은 남긴다.

사람 몫(허락): 이 기계의 전역 스킬 넷을 아래 명령 `mkdir -p ~/.claude/skills-backup && mv ~/.claude/skills/grill-with-docs ~/.claude/skills/domain-modeling ~/.claude/skills/grilling ~/.claude/skills/grill-me ~/.claude/skills-backup/`로 백업 폴더에 옮긴다. `~/.claude/skills/`에 없는 것은 명령에서 뺀다(넷 가운데 하나라도 있을 때만).

```bash
mkdir -p ~/.claude/skills-backup && mv ~/.claude/skills/grill-with-docs ~/.claude/skills/domain-modeling ~/.claude/skills/grilling ~/.claude/skills/grill-me ~/.claude/skills-backup/
```

3. 사용자 레벨 진행 스킬 `~/.claude/skills/kickoff/SKILL.md`. `/kickoff`가 런북 clone의 진행 규율을 읽게 하는 짧은 스킬이고 원문은 `kickoff/skill-template.md`다. 진행 규율의 시작 확인이 허락을 받아 이미 만들었으므로 여기서는 묻지 않고, 진행 파일 사람 몫 표의 `시작` 행을 0단계 행의 메모에 옮긴다. 이 clone을 가리키면 끝남이고, 시작에서 만들기를 건너뛰었거나 다른 clone을 가리킨 채 두었으면 건너뜀과 그 이유다. 건너뛴 것은 8단계 끝에서 다시 묻는다. 진행 규율 없이 이 런북을 사람이 몰아 돌리면 진행 파일도 이 스킬도 없으니, 쓰려면 여기서 그 원문의 `<clone>`을 이 clone의 절대 경로(슬래시)로 바꿔 그 자리에 만든다.

전역 `~/.claude/CLAUDE.md`는 비워 둔다. 교정 루프 문단은 3단계에서 프로젝트 `CLAUDE.md`에 넣는다.

사람 몫(허락): 이 기계의 전역 `~/.claude/CLAUDE.md`를 `cp ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.bak && : > ~/.claude/CLAUDE.md`로 사본을 남기고 비운다. 허락을 묻는 설명에 지금 내용을 보인다(비어 있지 않을 때만).

## 1단계. 저장소 만들기

```bash
git init -b main
```

`-b main`은 기본 브랜치 설정이 없는 기계에서도 main으로 시작하게 한다. 8단계의 보호와 이 런북 전체가 main을 가정한다. 폴더와 세션은 준비에서 열었고 `docs/`는 일지와 함께 생겼다.

사람 몫(결정): 이 프로젝트에서 워크트리를 쓸지. 아래 `.gitignore`와 7단계에서 복사하는 `tidy-checkouts`가 이 답을 쓴다.

`.gitignore`는 스캐폴딩 때 프레임워크가 만들거나 에이전트에게 맡긴다. 워크트리를 쓸 것이면 `/.claude/worktrees/`를 처음부터 넣는다(클론마다 다른 `.git/info/exclude`에만 있으면 새 클론에서 사본이 검사와 `git add -A`에 섞인다).

원격의 공개 여부는 준비에서 정했다. 8단계의 보호 브랜치와 봇 경로가 그 답으로 갈린다(준비의 "공개 여부").

## 2단계. 스킬을 프로젝트 레벨로 설치

설치기는 기본이 프로젝트 레벨(`.claude/skills/`)이다. Windows에서는 심링크 대신 복사(`--copy`)를 쓴다. 이름은 공백으로 나열하고, 오류가 나면 `-s`를 스킬마다 반복한다.

`tdd`가 부르는 `codebase-design` 스킬은 아래 목록에 없다 — 시임 어휘가 필요하면 목록에 더해 함께 설치하고, 아니면 설치한 뒤 `tdd` 사본에서 그 문장을 지우고 센티널을 붙인다(agent-os는 아직 어느 쪽도 하지 않았다).

사람 몫(결정): `codebase-design`을 함께 설치할지, 설치하지 않고 `tdd` 사본에서 그 문장을 지우고 센티널을 붙일지.

```bash
npx skills@latest add mattpocock/skills -a claude-code --copy -y -s grill-me grill-with-docs grilling domain-modeling setup-matt-pocock-skills to-spec to-tickets implement tdd code-review diagnosing-bugs writing-for-agents retro
```

`--copy`는 Windows 전용이다(심링크 대신 복사). 다른 OS는 빼도 된다.

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
| retro | 세션 회고, 하네스 개선 후보의 판정 | 10 |

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

사람 몫: 없음

`/init`으로 만든 뒤 `kickoff/claude-md-template.md`의 모양으로 줄인다. setup 스킬이 이 파일에 `## Agent skills` 블록을 추가하므로 setup보다 먼저 만든다. 이 단계는 뒤의 산출물에 기대는 자리가 둘이다 — `@` 임포트 대상은 5단계가 만들고 검증 명령은 7단계가 채운다. 그 전까지 `@` 줄은 주석으로 두고 검증 명령 칸은 비워 둔다. 훅 등록과 빨강 확인은 7단계다(pre-commit이 있어야 한다). 교정 루프 절은 템플릿 그대로 복사한다. 규칙이 아니라 규칙을 만드는 절차이므로 "규칙 없음" 원칙과 충돌하지 않는다.

지침의 자리는 로드 시점이 정한다. 로드 시점은 넷이다 — 항상(CLAUDE.md, `@` 임포트, `paths` 없는 rules, 모델이 부를 수 있는 스킬의 description, 자동 메모리 `MEMORY.md`의 앞부분, 켜 둔 MCP 서버의 도구 이름과 서버 지침), 해당 파일을 Read 도구로 열 때(`paths` 있는 rules와 하위 디렉터리의 `CLAUDE.md`. Bash `cat`·`sed`로 읽으면 안 실린다), 필요하다고 판단할 때(skill 본문. 한 번 부르면 이후 턴 내내 남는다), 사건이 일어날 때(훅의 계기 문장). 마크다운 링크는 로드되지 않는다. 파일을 쪼개도 임포트하면 분량은 같다. 분류 표는 위 템플릿의 교정 루프 절이고, 남길 항목은 "이 줄을 지우면 실수하게 되나"로 거른다. 강제가 필요한 것은 문서가 아니라 훅이다.

- 배치 규칙의 판정자는 `tools/check_instructions.py`다. `paths` 누락(규칙 폴더는 하위까지 본다. `paths`는 목록과 쉼표 문자열 둘 다 받는다), 아무 파일도 가리키지 않는 `paths` glob(규칙이 조용히 안 실린다), 저장소 파일을 상대 경로로 부르는 훅(세션이 루트를 벗어나면 깨지고, PreToolUse면 모든 Bash를 막는다. `${CLAUDE_PROJECT_DIR}`로 쓴다), 200줄 초과, 원칙 외 `@` 임포트(문장 속 `@경로`도 임포트다. rules와 임포트된 파일 안의 `@`도 따라가 실리므로 거기서도 잡는다), 임포트된 파일 안의 형제 상대 경로(백틱 경로는 모델이 루트 기준으로 읽는다. `@` 임포트의 상대 경로는 담은 파일 기준으로 풀린다), 덧댄 스킬 사본의 센티널 소실과 목록 누락, 훅의 텍스트 stdin, 루트 밖의 `CLAUDE.md`·`AGENTS.md`(`node_modules`와 워크트리는 보지 않는다), `settings.local.json`의 가드(deny·ask·hooks. local은 추적하지 않아 워크트리에 없으니 가드는 `settings.json`에만). 7단계에서 복사·등록하고 빨강을 본다.
- 항상 로드 분량은 `/context`를 직접 실행해 실측하고, 재배치했으면 전후 값을 ADR로 남긴다. 줄 수는 대리 지표일 뿐이다 — agent-os는 200줄 검사만 두고 실측을 한 번도 하지 않아, 재배치 커밋(2026-09-20) 뒤 여덟 날 동안 줄은 11% 늘고 글자는 39% 늘었다(2026-09-28 감사). 이 기준은 ai-agent-platform AAPP-15(2026-09-01)에서 한 번 겪었고, agent에서 담지 않아 두 번째로 겪었다.

## 4단계. /setup-matt-pocock-skills

한 번 실행한다. 세 가지를 묻는다.

- 이슈 트래커: GitHub, GitLab, 로컬 마크다운(`.scratch/<feature>/`), 기타. Jira는 "기타"를 고르고 한 단락으로 설명한다. 예: "이슈는 Jira. 티켓 생성은 /jira-create, 착수는 /jira-start(브랜치와 Draft PR), 커밋과 진행 기록은 /jira-commit, 완료는 /jira-complete. 브랜치 이름은 feature/[이슈번호]-[kebab-설명]." 그대로 `docs/agents/issue-tracker.md`에 기록된다.
- 트리아지 라벨: triage 스킬을 안 깔았으므로 건너뛴다.
- 도메인 문서: 단일 컨텍스트 기본(루트 `CONTEXT.md` + `docs/adr/`). 모노레포면 멀티 컨텍스트.

산출물: `docs/agents/issue-tracker.md`, `docs/agents/domain.md`, `CLAUDE.md`의 `## Agent skills` 블록. 쓰기 전에 초안을 보여 주니 한국어로 고쳐서 승인한다.

사람 몫(결정): 위의 이슈 트래커와 도메인 문서의 모양, 그리고 산출물 초안의 승인. setup 스킬이 글로 물어도 이 세션의 선택 화면으로 묻는다.

로컬 마크다운을 골랐으면 `docs/agents/issue-tracker.md`에 두 가지를 더한다. `Status:` 값(`ready-for-agent`, `in-progress`, `done`, `wontfix`)과 "전체 계획" 절(`.scratch/plan.md`가 기능 목록·`Blocked by`·`Status`를 갖고, 프론티어만 병렬, 계약 변경 티켓이 첫 blocker). 그리고 `.scratch/plan.md` 첫 판을 만든다. 슬라이스와 기능(slug), 의존, 상태. 헌법의 "첫 슬라이스와 비목표"는 헌법이 아니라 여기 산다.

## 5단계. 헌법

헌법 전에 제품 의도 한 장(`docs/PRD.md`)을 쓴다. 누구의 어떤 문제를 왜 푸는가, 무엇을 만들고 무엇을 안 만드는가, 성공의 정의, 스펙이 충돌할 때의 우선순위. 40줄 안팎. 설계 문서는 "어떻게"만 담으므로 이것이 없으면 스펙끼리 충돌할 때 기준이 없다(ai-agent-platform은 설계 spec 7개에 PRD 0개였다). 이 시점이 가장 싸다.

사람 몫(결정): PRD의 내용과 이 단계 헌법 인터뷰의 결정들, 그리고 인터뷰에서 나온 ADR 초안의 승인. grill-me가 글로 물어도 이 세션의 선택 화면으로 묻는다.

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

code-review 스킬이 리뷰할 때 읽는 파일. 자동 검사(린트, 타입, 테스트, 훅)로 잡을 수 있는 것은 여기 쓰지 않고 검사를 만든다. 아래 항목은 첫날의 씨앗 목록에 회고에서 승인된 줄만 더한다(판정은 retro 스킬 4단계).

## 심각도
Critical(보안, 데이터 유실, 장애) 병합 차단 / Major(명백한 버그, 잘못된 로직) 병합 전 수정 / Minor(가독성, 중복, 누락 테스트) 후속 허용 / Nit 작성자 재량.

## 리뷰하지 않는 것
포맷, 린트, 타입 오류, 생성물. 도구가 잡는다.

## 판단 기준
(비어 있음)
```

규칙은 강제력이 가장 높은 층에 둔다. 타입 → 린터·훅 → 아키텍처 테스트 → 지침 → 리뷰. 오른쪽으로 갈수록 비용이 자릿수로 커진다. 린터가 잡는 규칙을 지침에 쓰지 않고, 거짓 양성이 많은 규칙을 하드 게이트로 만들지 않는다(`disable`이 관례가 되면 옆의 살아 있는 규칙까지 죽는다). 리뷰 관점은 4개 이하로 둔다. 길어지면 아무도 안 읽는다. 선행 프로젝트에서 검증된 판단 기준 목록이 있으면 첫날 씨앗으로 넣어도 되지만, 그 목록은 사람이 고른다. 씨앗은 새 프로젝트의 회고 후보가 아니라서 retro의 판정을 거치지 않는다.

사람 몫(결정): 선행 프로젝트의 판단 기준을 첫날 씨앗으로 넣을지와, 넣으면 어느 항목을 넣을지(그 목록이 있을 때만).

## 7단계. 스캐폴딩과 검증 명령

에이전트에게 "헌법대로 골격을 만들어라"라고 시킨다. 프레임워크 생성기(`create-next-app` 같은 것)는 에이전트가 돌린다. 종료 조건은 세 명령이 실제로 통과하는 것이다.

- 테스트 명령 1개 (샘플 테스트 하나 포함)
- 린트 명령 1개
- 타입체크 명령 1개 (해당 언어면)

통과한 명령을 `CLAUDE.md`의 검증 명령 칸에 적는다. 이때 아래 파일들을 런북 저장소에서 복사한다. **파일마다 바꿀 자리가 다르다** — 각 항목 끝의 괄호가 그것이고, "검증 명령과 층 이름만"이 아니다.

사람 몫(결정): 복사 목록의 조건부 항목. 답변 언어가 한국어인가(`hook_stop_korean`, `hook_midturn_korean`), claude.ai 클라우드 세션을 쓰는가(`hook_session_web_deps`). OS와 원격은 세션이 스스로 안다.

하네스 런타임부터 적는다. 훅과 그 실행 래퍼, 검사와 훅 러너, 변이 도구, pre-commit은 파이썬이고 훅은 `uv run --project "${CLAUDE_PROJECT_DIR}" --no-sync python "${CLAUDE_PROJECT_DIR}/tools/launch_hook.py" <훅>.py`로 돈다(`--project`가 빠지면 저장소 밖에서 시스템 파이썬으로 돈다). 래퍼 `tools/launch_hook.py`는 훅 파일이 없으면 막지 않고 지나가게 하고, 지나갈 때 사용자와 모델에게 알린다(Stop·SubagentStop은 모델에게 알리면 대화가 이어져 사용자에게만). 알림은 세션·에이전트·이벤트·훅마다 처음 한 번만 낸다 — 호출마다 내자 다시 연 워크트리 세션에서 같은 문단이 Write·Edit마다 약 마흔 번 컨텍스트에 쌓였다(agent-os, 2026-10-12). 훅 경로를 바로 부르면 파일이 없을 때 파이썬이 2로 끝나고, PreToolUse에서 2는 막기라 그 매처의 모든 호출이 막힌다(agent-os, 2026-10-02. 새 훅을 등록한 워크트리 세션이 다시 시작되며 `${CLAUDE_PROJECT_DIR}`이 그 파일이 없는 주 체크아웃을 가리켰다). 파이썬 프로젝트가 아니면 개발 도구로 uv와 파이썬 하나를 두면 그대로 돈다 — uv는 pyproject가 없는 폴더에서도 시스템 파이썬으로 돌았다(2026-09-28 실측). 훅(`hook_*.py`)은 표준 라이브러리만 쓴다. 러너·변이 도구(pydantic)와 OpenAPI 내보내기(앱 의존성)는 프로젝트 venv에서 돈다.

- `.claude/settings.json`의 `hooks` 블록과 `permissions.deny`. **훅 파일만 복사하면 아무것도 발동하지 않는다.** 반대로 등록만 복사하고 래퍼를 빠뜨리면 모든 훅이 2로 끝난다(PreToolUse는 그 매처의 호출을 막는다. 2의 효과는 이벤트마다 다르다, 부록 C). 등록 모양은 위 명령 한 줄이고 매처는 훅마다 다르다(UserPromptSubmit과 Stop은 매처 없이, SessionStart는 `startup|resume`, PostToolUse는 `Write|Edit`와 `Bash|PowerShell|<GitHub MCP PR 도구 넷>`(데스크톱 앱의 플러그인 도구 둘과 claude.ai 클라우드 세션의 도구 둘은 이름이 다르다)와 `WebFetch`와 `Grep`, PreToolUse는 `Bash`, `Bash|PowerShell`, `Bash|Grep`, `Skill`, 매처 없이(모든 도구)). 어느 훅이 어느 매처에 드는지는 `.claude/settings.json`이 원천이다. 다만 인계 훅 둘의 등록(PostToolUse `Bash|PowerShell|Skill|<GitHub MCP PR 만들기 도구 둘>`의 `hook_handoff`, Stop의 `hook_handoff_notice`)은 새 프로젝트에 복사하지 않는다. 그 비용의 거의 전부가 agent-os였고(ADR 0033), 훅 파일 없이 등록만 실리면 래퍼가 알림을 낸다. 위 매처 목록에는 그 둘의 매처를 넣지 않았다. `hook_session_usage`(SessionStart `startup|resume|clear|compact|fork`)도 등록, 훅 파일, 그 시험(`tests/tools/test_hook_session_usage.py`. 보고서 도구를 import한다) 모두 복사하지 않는다. 그 훅이 쓰고 읽는 사용량 장부와 보고서 도구(`tools/token_report.py`)를 새 프로젝트에 복사하지 않아(agent-os 토큰 사용 명세 Out of Scope), 등록만 옮기면 같은 알림이 나고, 아래 항목의 `tests/tools/test_hook_*.py`를 통째로 옮기면 그 시험이 import에서 깨진다. 위 SessionStart 매처(`startup|resume`)는 복사하는 `hook_session_web_deps`의 것이다. `permissions.deny`에 `Read(//**/.env)`·`Edit(//**/.env)`(`./`는 세션 cwd 기준이라 워크트리 세션에서는 주 체크아웃의 `.env`에 안 걸린다)와 PowerShell 읽기 모양(`PowerShell(Get-Content *.env*)` 등, Windows면), `env`에 `PYTHONUTF8`(파이썬이면). 에이전트의 저장소 전체 grep 한 번에 API 키가 도구 출력에 실린 적이 있다(agent-os, 2026-09-28). Bash·Grep으로 읽는 길은 `hook_env_read`가 막는다. 두 장치 모두 호출의 모양을 보는 에이전트 층이라 `.NET` 읽기 같은 것은 지나간다(부록 C). 셋째 층은 키 자체다 — `.env`에는 사용 한도를 건 개발용 키만 두고, 도구 출력에 실린 키는 회전한다. (바꿀 곳: GitHub MCP 도구 이름이 다르면 그 매처와 `tools/hook_pr_next_session.py`의 `MCP_TOOLS`를 함께. 두 목록의 대조는 `tests/tools/test_hook_pr_next_session.py`가 한다)
- 훅과 그 테스트 `tests/tools/test_hook_*.py`. 이유는 각 파일의 독스트링이 원천이다. `hook_prompt_directive`(지시문 계기, 폴더가 다르면 `decision: block`), `hook_journal_retro`(일지의 '다음' 절을 쓰면 retro 계기. 새 일지 파일을 만든 Write 에는 `tools/sibling_overlap.py`를 자식으로 돌려 순번이 다음 빈 번호와 다르면 그 번호를 계기로 — `ls`로 고른 번호가 형제와 겹쳐 커밋 직전에 번호와 인용을 옮겼다. 그 도구가 없는 프로젝트는 순번 대조를 뺀다), `hook_pr_next_session`(PR 열기·병합 뒤 next-session 계기), `hook_grill_design_check`(모델이 `grill-with-docs`를 Skill 도구로 부르려 하면 설계 인터뷰가 맞는지 확인하라는 계기. 이 훅을 복사하면 아래 "나머지 덧댄 사본" 항목의 `grill-with-docs` 사본과 짝이다), `hook_webfetch_summary`(WebFetch가 페이지 본문 대신 작은 모델의 답인 웹 요약을 돌려주면 받은 바이트와 답의 글자 수를 들어, 그 수와 인용을 근거로 쓰거나 원문 확인이라 말하기 전에 본문을 내려받아 대 보라는 계기 — 요약이 기능이 들어온 판을 틀리게 준 일이 있었고, 요약을 원문처럼 근거로 쓴 일이 세 번이었으며 그중 둘은 근거 규약을 적은 뒤였다. 2xx가 아니면 받은 본문이 없고, 결과의 UTF-8 바이트 수가 받은 바이트와 같으면 본문을 그대로 돌려준 것이라 둘 다 침묵한다), `hook_grep_omitted`(Grep 도구가 500자를 넘는 일치 줄을 `[Omitted long matching line]`으로만 내면 그 수와 자리를 들어, 잔존을 세는 중이면 그 줄을 따로 열라는 계기 — 잔존 grep이 그 표지 뒤의 행을 놓쳤다. 생략된 문맥 줄은 일치를 숨기지 않아 세지 않는다), `hook_ruff_line_width`(파이썬 파일을 쓴 직후 ruff E501을 계기로 — 한글은 폭 2라 글자 수로 가늠하면 넘긴다. ruff 설정을 그대로 따라, 설정이 없거나 E501을 고르지 않은 프로젝트에서는 침묵한다. 안내에 아래 감기 도구의 명령을 싣는다), `hook_line_separators`(쓴 파일에 아래 줄 구분 문자 검사가 잡는 문자가 있으면 그 자리를 계기로 — 편집 도구가 이스케이프를 날것 문자로 저장해도 보이지 않아, 그 검사가 커밋을 막을 때에야 알았다), `hook_bash_heredoc`(40줄 넘는 heredoc deny), `hook_bash_python_stub`(맨 `python` deny — 파이썬 프로젝트에만), `hook_bash_gate_pipe`(게이트가 파이프에 묻히면 경고), `hook_bash_msys_pathconv`(Git Bash가 git의 인자를 경로 목록으로 바꿀 모양이면 `MSYS_NO_PATHCONV=1`을 들어 경고 — 대개 첫 콜론 왼쪽에 `/`가 있고 오른쪽이 `.`·`/`로 시작하면 바뀌어(`:./`·`//` 등 예외는 훅 독스트링) `origin/main:.scratch/x.md`가 `origin\main;.scratch\x.md`로 가 실패한다. 윈도이거나 `MSYSTEM`이 있을 때만 알린다), `hook_git_main_commit`(커밋이 있는 저장소의 main 위 커밋 deny — 커밋이 하나도 없는 저장소의 첫 커밋은 지나간다(8단계)), `hook_push_behind_main`(origin/main보다 뒤처진 브랜치의 `git push` deny — 필수 검사가 최신 main 위에서 돌아야 병합되는 보호(strict)라 뒤처진 채 푸시한 CI는 병합 전에 한 번 더 돈다. 지우는 푸시와 `PUSH_BEHIND_OK`가 든 명령은 지나간다. 원격·기본 브랜치가 origin·main이 아니면 바꿀 곳), `hook_bash_cd_outside`(셸의 작업 폴더를 지금 체크아웃 밖이나 그 체크아웃의 하위 폴더로 옮기는 `cd` deny — Bash의 작업 폴더는 다음 호출로 이어져, 워크트리 세션이 주 체크아웃으로 들어가자 그 뒤 모든 명령을 앱의 가드가 거부했다. 가드가 없는 주 체크아웃 세션에서는 옮긴 뒤의 git이 다른 체크아웃에 조용히 닿아 그 세션에도 건다. 체크아웃은 `.git`이 있는 조상이거나 `.claude/worktrees/<이름>`이다. 하위 폴더로 옮기는 `cd`는 처음에 알리기만 했는데, 다음 호출의 상대 경로가 그 하위 폴더에서 풀린 일이 세 번이었고 알린 뒤에도 되풀이돼 막는다. 폴더를 인자로 주거나(`pnpm -C <폴더>`) 서브셸로 가두는 대안을 안내한다), `hook_bash_commit_msg`(`git commit -F <파일>`의 메시지를 커밋하는 저장소의 commit-msg 판정 스크립트로 먼저 대 보고 걸리면 deny — 그 단계가 pre-commit 검사 뒤라 제목 하나 때문에 약 7~8분의 게이트를 한 번 더 돈 일이 세 번이었다. 알림은 명령이 돈 뒤에야 모델에게 닿아 막는다. 그 파일이 그대로 메시지가 되고 commit-msg 판정이 돌 커밋만 본다(`-e`·`--squash`·`--no-verify`, 같은 명령에서 쓰는 파일 등은 보지 않는다)는 것은 훅 독스트링. 판정 스크립트는 이 훅의 저장소(주 체크아웃과 등록된 워크트리)의 것만 띄운다 — 훅은 권한 확인 전에 돌아, 밖의 저장소에 커밋을 시도만 해도 그 저장소의 스크립트가 돌았다), `hook_stop_korean`(턴을 끝내는 답의 산문이 한국어가 아니면 Stop을 `decision: block`으로 막아 한 번 다시 쓰게 한다, SDK 세션은 뺀다), `hook_midturn_korean`(도구 호출 바로 앞의 중간 문장이 한국어가 아니면 다음 문장부터 한국어로 쓰라고 경고 — 입력에 텍스트가 없어 트랜스크립트에서 자기 `tool_use` 앞을 읽는다, 서브에이전트와 SDK 세션은 뺀다), `hook_env_read`(`.env` 읽기와 `.env`를 빼지 않은 전체 grep deny, Grep 도구의 `.env` 경로도. 명령 앞의 래퍼는 옵션과 그 값까지 벗겨 본다), `hook_user_settings_read`(사용자 설정 파일 둘(`~/.claude/settings.json`, `~/.claude.json`)을 Read·Grep·Bash·PowerShell로 출력하면 deny하고 값 없이 키 이름만 내는 명령을 안내한다 — 설정의 한 갈래를 통째로 출력해 비밀이 세션 기록에 남았다. 프로젝트의 `.claude/settings.json`은 지나간다), `hook_push_delete_open_pr`(열린 PR의 머리 브랜치를 원격에서 지우는 `git push` deny — 병합과 지우기를 한 번에 보내, 병합이 실패했는데 지우기가 나가 PR이 닫혔다. 열린 PR은 `gh api`의 REST로, 쓰지 못하면 `git ls-remote`의 merge ref로 가린다. 원격은 이름으로 준 것만 묻는다. 명령 글의 URL로 접속하면 권한 판정 전에 요청이 나간다), `hook_pr_head_sync`(`gh pr ready`와 `@coderabbitai review` 코멘트를 PR head가 로컬 HEAD에 못 미칠 때 deny — 푸시 직후 GitHub가 PR head를 갱신하기 전에 부르면 리뷰가 옛 head를 본다), `hook_session_web_deps`(클라우드 세션이 시작되거나 이어질 때 루트에서 `uv run pre-commit install`을, 이어 `pnpm -C web install --frozen-lockfile`을 친다 — 클라우드 세션은 새 클론이라 git 훅도 `web/node_modules`도 없다. 실패하면 손으로 칠 명령과 함께 알리고 0으로 끝난다). 계기 훅은 `hook_prompt_directive`(폴더가 다를 때만 막는다)·`hook_journal_retro`·`hook_pr_next_session`·`hook_grill_design_check`·`hook_webfetch_summary`·`hook_grep_omitted`·`hook_ruff_line_width`·`hook_line_separators`·`hook_bash_gate_pipe`·`hook_bash_msys_pathconv`·`hook_midturn_korean`·`hook_session_web_deps`(설치가 실패할 때만 알린다)이고, 나머지는 막는 훅이다. 단계를 닫는 순간에 처음부터 붙인 것은 `hook_pr_next_session`이고, 실패가 조용해 첫 사건에서 막는 훅으로 간 것은 `hook_env_read`와 `hook_pr_head_sync`와 `hook_user_settings_read`이고, 계기로는 때를 맞출 수 없어 사용자가 막기를 고른 것은 `hook_pr_head_sync`와 `hook_push_behind_main`이며, 나머지는 지침이 어겨지거나 사건이 난 뒤에 붙였다. 모두 겪고 나서 생긴 것이라 새 프로젝트는 처음부터 갖는다. (바꿀 곳: `hook_bash_gate_pipe`의 게이트 명령 목록을 그 프로젝트의 검증 명령으로. `hook_webfetch_summary`의 안내가 가리키는 근거 규약(`docs/agents/issue-tracker.md` 프로브와 근거)을 그 프로젝트의 자리로. `hook_stop_korean`과 `hook_midturn_korean`은 답변 언어가 한국어인 프로젝트에만. `hook_pr_head_sync`와 `hook_push_delete_open_pr`는 GitHub PR과 `gh`를 쓰는 프로젝트에만. `hook_bash_commit_msg`는 commit-msg 단계의 판정 스크립트(`tools/check_commit_msg.py`)가 있는 프로젝트에만. `hook_session_web_deps`는 claude.ai 클라우드 세션을 쓰는 프로젝트에만. 루트에 pre-commit 설정이 있으면 uv로 git 훅을, pnpm 워크스페이스가 있으면 그 의존성을 까니, 그 경로와 명령을 그 프로젝트의 것으로)
- `.claude/rules/tools.md`. 훅·검사의 규약(단독 실행, 바이트 stdin, 계기 훅과 막는 훅의 기준, 못 보는 것 절, 식별자 언어). (바꿀 곳 0)
- `.github/PULL_REQUEST_TEMPLATE.md`. 변경 유형, 왜, 남긴 위험, 계약 영향, 변경된 영역, 체크리스트, 확인 방법, 관련 티켓, 리뷰어 참고. `/git-pr`이 이것을 채운다. 계약 영향 칸은 PR마다 계약에 닿았는지를 "없음"까지 적게 한다 — 계약을 지침(`CLAUDE.md` 작업 규약)에만 정의해 두는 동안 템플릿의 변경된 영역에는 HTTP 계약(`openapi.json`)의 줄이 없어, 그 파일을 바꾼 PR 열하나가 체크할 칸 없이 병합됐다(agent-os, 2026-10-15에 템플릿을 살피다 찾았다). (바꿀 곳: 계약 영향 칸이 가리키는 계약의 정의와 함께 바꿀 것의 예, 변경된 영역의 층 이름과 검증 명령, 약 20행)
- 커밋 메시지 훅 `tools/check_commit_msg.py`와 `tests/tools/test_check_commit_msg.py`. `.pre-commit-config.yaml`에 `stages: [commit-msg]`로 등록하고 `default_install_hook_types: [pre-commit, commit-msg]`와 `default_stages: [pre-commit]`을 둔다. 기본 단계를 두지 않으면 단계를 적지 않은 `always_run` 훅이 commit-msg 단계에서 한 번 더 돈다(agent-os, 대기열 118 — pyright·pytest까지 커밋마다 두 번이었다). 나쁜 메시지로 빨강을 본다. (바꿀 곳 0)
- 지침 검사 `tools/check_instructions.py`와 `tests/tools/test_check_instructions.py`. 아래 검사 러너의 `CHECKS`에 넣는다. (바꿀 곳: `PATCHED_SKILLS`·`SENTINEL`·`ALLOWED_IMPORTS` 상수를 **그 프로젝트가 실제로 덧댄 사본**으로. agent-os는 일곱(code-review·grill-with-docs·grilling·implement·retro·to-spec·to-tickets)을 덧댔고 그대로 복사하면 첫 커밋이 그 일곱의 센티널 부재로 빨강이다. 목록은 양방향으로 검사된다 — 주석이 있는데 목록에 없는 사본도 빨강)
- 타입 우회 검사 `tools/check_type_escapes.py`(파이썬이면. 원칙 III의 판정자, ADR 0013), 변이 도구 `tools/mutate.py`(테스트가 무엇을 재는지 변이로 본다. 바이트 그대로 되돌리고 기대 결과를 받는다. 변이마다 시간 제한을 두어 넘기면 띄운 프로세스까지 끝내고, 따옴표 인자 없이 번호나 `--since <커밋>`으로 고른다. `.pre-commit-config.yaml`에 `files: _mutations\.toml$`로 `--check`를 걸어 커밋에 든 변이 표의 원문을 본다), Actions 실행 요약 `tools/gh_run_summary.py`(리뷰 봇이 코멘트 없이 초록일 때 로그를 읽는다. operations.md가 가리킨다), 형제 번호 대조 `tools/sibling_overlap.py`(커밋 직전에 origin/main, 열린 PR의 head, 형제 워크트리와 일지 순번·ADR·대기열 행·헌법 판을 대조한다. 열린 PR은 `gh api`로, 쓰지 못하면 merge ref로 읽는다. 다음 빈 일지·대기열 번호와 형제가 쓴 가장 높은 헌법 판을 늘 찍고, 새 일지가 없으면 받은 번호로 바로 일지 파일을 만들라고 안내한다. 새 일지가 main의 최신 일지보다 이름순으로 앞이거나, 헌법 파일을 고치고 판을 올리지 않았거나, 바꾼 스킬 본문·규칙·서브에이전트를 원천으로 든 카나리아 명세를 이 브랜치가 하나도 고치지 않았거나, 이 브랜치가 더한 줄의 `일지 YYYY-MM-DD-NN` 인용이 main·형제·이 브랜치 어디에도 없는 번호를 가리키면(인용 블록, 코드 스팬, 펜스 안은 빼고) 겹침처럼 1로 끝난다. main의 헌법 이력이 이 브랜치 몫으로 비워 둔 판에 이 브랜치가 이력 문단을 더했으면 판을 올린 것으로 센다. `--move`는 옮길 번호대로 일지·ADR의 파일 이름과 일지 머리 줄, 이 브랜치의 변경과 미추적 파일 안의 인용을 옮기고 다시 대조한다. 2로 끝나면 stderr에 할 일(번호를 손으로 고르지 않는다)을 싣는다. HEAD가 닫힌 PR의 head인 형제 워크트리는 커밋하지 않은 변경만 견주고 형제 줄에서 접는다. agent-os는 `CLAUDE.md` 환경 함정의 커밋 전 줄과 `next-session` 1단계의 일지 줄이 가리킨다), PR 검사 대기 `tools/wait_ci.py`(검사가 pending이면 `next-session` 1단계가 Bash 도구의 `run_in_background`로 띄워, 검사와 리뷰 봇이 끝날 때 세션이 깨어난다. 사람이 "CI 끝났어"로 깨우던 자리다). (바꿀 곳: 검사는 `[tool.pyright]`의 `include`를 읽는다. `sibling_overlap.py`는 번호의 자리가 다르면 경로 상수 넷과 판을 올려야 하는 헌법 파일 목록 `CONSTITUTION_TEXTS`, 원격과 기본 브랜치가 다르면 `REMOTE`·`BRANCH`, 카나리아 명세나 불러 보는 하네스 파일의 자리가 다르면 `CANARY_SPECS`·`HARNESS`, 일지 인용의 꼴, 헌법 이력의 문단 머리, 판을 비워 두는 문장이 다르면 `JOURNAL_CITE`·`HISTORY_HEAD`·`RESERVED`. `wait_ci.py`는 필수 검사와 리뷰 봇의 이름이 다르면 `EXPECTED`, 리뷰 봇이 CodeRabbit이 아니면 `UNREQUESTED_PREFIX`와 요청 문구. 템플릿의 환경 함정은 빈 자리라, 커밋 전에 그 명령을 치는 줄을 그 프로젝트의 `CLAUDE.md`에 더한다)
- 인용 대조 `tools/check_quotes.py`와 `tests/tools/test_check_quotes.py`. 바뀐 .md의 20자 이상 따옴표 인용을 저장소와 글자 그대로 대조해 경고만 낸다(같은 PR에서 고친 문장의 인용 둘이 옛 문구로 남았던 자리). `.pre-commit-config.yaml`에 `files: \.md$`와 `verbose: true`로 두고 CI에는 넣지 않는다. (바꿀 곳 0)
- 마크다운 표 검사 `tools/check_md_tables.py`와 `tests/tools/test_check_md_tables.py`. cmark-gfm(GitHub의 렌더러)의 블록 파싱을 옮겨, 표가 GFM에서 깨지는 자리를 본다 — 행의 칸 수가 머리 행과 다른 것, 표 아래에 빈 줄이 없는 것, 표 안의 구분 행(빈 줄 없이 붙은 표 둘), 표처럼 썼는데 표가 되지 못한 머리 행. agent-os의 plan.md가 두 번 깨졌다 — 칸 안에 넣은 줄바꿈 목록이 표를 끊었고, 코드 스팬 안의 `|`가 칸 구분으로 읽혔다(GFM은 코드 스팬도 파이프를 보호하지 않는다). 줄 두 개만 보는 판정은 목록·인용·HTML 블록 안에서 오탐과 미탐을 함께 냈다(적대 검증). `.pre-commit-config.yaml`에 `types: [markdown]`, `require_serial: true`. (바꿀 곳 0)
- 줄 구분 문자 검사 `tools/check_line_separators.py`와 `tests/tools/test_check_line_separators.py`. 추적 텍스트 파일의 날것 U+2028·U+2029·U+0085와 뒤에 LF가 없는 CR을 잡고, `.py`에서는 ASCII 밖의 유니코드 일반 범주 Zs·Cf(줄바꿈 없는 공백, 전각 공백, 폭 없는 공백, 방향 제어 문자, 파일 머리 뒤의 BOM 등)도 잡는다. 편집 도구가 소스의 비 ASCII 이스케이프와 역슬래시-r을 날것 문자로 저장하는 사고가 되풀이됐다(PR #58, 그리고 이 검사를 쓰던 세션에서 파일 다섯, 그 뒤 `.md` 표의 CR). 보이지 않는 공백을 `.py`에만 거는 것은 한국어 문서의 전각 공백이 정당할 수 있어서다. 소스에 그 문자가 필요하면 `chr()`로 만든다. `types: [text]`, `require_serial: true`. 최상위 `default_stages: [pre-commit]`이 없으면 커밋 메시지 파일(text)에도 돈다. (바꿀 곳 0)
- 주석·독스트링 감기 도구 `tools/rewrap_comments.py`와 `tests/tools/test_rewrap_comments.py`. 넘친 줄의 꼬리 어절을 다음 줄 앞으로 넘기고 짧은 줄은 끌어올리지 않는다. 세션마다 스크래치에 감기 스크립트를 새로 지었고, 그것들이 줄 끝을 CRLF로 바꾸고 빈 줄·닫는 따옴표·혼자 선 줄을 문단에 붙이고 코드 스팬을 갈랐다. 폭과 넘친 줄의 판정은 ruff의 E501을 따르고(한글 2, 조합형 자모 0, 줄 끝 지시 주석 빼기) 프로브 `rewrap_width.py`가 저장소의 줄로 대조한다. (바꿀 곳 0. 줄 길이는 파일마다 가장 가까운 ruff 설정에서 읽는다)
- ADR 포인터 규약 `.claude/rules/adr.md`(`paths: docs/adr/**`)와 그 검사 `tools/check_adr_pointers.py`, `tests/tools/test_check_adr_pointers.py`. 개정을 이력에 쌓으면 본문에 옛 문장이 남아 리뷰가 그것을 지금의 결정으로 읽는다(agent-os, 리뷰 둘이 한 문장을 잔존으로 읽었다). 이력이 바꾼 본문 문장 뒤에 `(바뀜: 이력 날짜 "제목")`을 달고, 검사가 그 모양과 제목을 이력 제목과 대조한다. pre-commit 훅이나 CI 단계를 따로 두지 않고 pytest의 저장소 상태 테스트로 돈다. (바꿀 곳: ADR 디렉터리가 `docs/adr`가 아니면 rules의 `paths`와 검사의 `ADR_DIR`, 이력 절의 제목이 `## 이력`이 아니면 검사의 `HISTORY_HEADING`. 디렉터리를 잘못 가리키면 ADR 0개라 검사가 빨갛다)
- 실행 래퍼 `tools/launch_hook.py`와 `tests/tools/test_launch_hook.py`. 한 번만 알린 표지는 임시 디렉터리의 `agent-os-launch-hook`에 둔다. (바꿀 곳 0. 두 프로젝트가 그 디렉터리를 나눠 써도 열쇠에 세션 ID가 들어 섞이지 않는다)
- 훅 러너 `tools/run_hooks.py`와 페이로드 표 `tools/hook_payloads.toml`, `tests/tools/test_run_hooks.py`. 러너는 등록 명령이 모두 위 모양인지 대조하고 그 모양으로 훅을 띄운다. 새 훅의 넷 중 "실행 확인"을 pre-commit이 돈다 — 실제 훅 파일을 **손으로 흉내 낸 페이로드**로 돌리는 것이라 Claude Code가 실제로 주는 입력 모양(런타임 입력 계약)은 검증하지 않는다. 워크트리 세션의 훅으로는 바뀐 파일을 확인할 수 없다(주 체크아웃의 파일이 돈다. agent-os, 2026-09-28). (바꿀 곳: 표의 사례를 그 프로젝트의 훅으로. 등록과 표가 한쪽에만 있는 훅은 러너가 잡는다)
- 검사 러너 `tools/run_checks.py`와 `tests/tools/test_run_checks.py`. pre-commit은 훅을 하나씩 돌므로, 파일을 고치지 않는 `always_run` 검사(타입체크, import 경계, 테스트, 지침 검사, 타입 우회 검사, 훅 러너, web verify)를 이 러너 하나가 함께 띄우고 끝난 차례로 결과를 찍는다. `.pre-commit-config.yaml`에는 파일을 고치는 ruff 둘 뒤에 훅 하나로 `always_run: true`, `pass_filenames: false`, `verbose: true`를 두고, 건너뛰기는 검사 id로 `SKIP=pytest`처럼 한다. agent-os에서는 함께 띄워 Linux와 Windows 모두 4할 남짓 줄었다(잰 시간은 ADR 0005의 2026-10-07 이력). Windows에서 `pnpm`은 `pnpm.cmd`라 러너는 명령을 `shutil.which`로 찾는다. 같은 검사를 러너와 훅에 함께 두면 커밋마다 두 번 돌아 테스트가 그것을 본다. (바꿀 곳: `CHECKS`를 그 프로젝트의 검사 명령으로)
- `.github/workflows/ci.yml`. 훅과 같은 검사. LLM 테스트 제외. 경로 필터를 걸면 미매칭은 실패로. (바꿀 곳: 파이썬이면 검사 이름만, 아니면 셋업 스텝 전부)
- 브랜치 보호 본문 `tools/protection.json`. 8단계의 `gh api --input`이 이 파일을 읽으므로 복사하지 않으면 그 명령이 입력을 찾지 못한다(PR #91 리뷰). (바꿀 곳: `required_status_checks.contexts`의 검사 이름이 `verify`가 아니면 그것)
- `.coderabbit.yaml`. 보안·버그·성능만. 린터는 끈다(CI가 돌린다). 제외는 생성물·락파일·남이 쓴 스킬 사본(`.claude/skills/**`)만. 로컬 CLI도 이 파일을 읽으므로 테스트 경로를 빼면 로컬 리뷰도 사라진다. 비공개 저장소에 무료 플랜이면 `auto_review.enabled: false`. PR에서는 요약만 남고 체크가 `pass`로 보인다. (바꿀 곳: `path_instructions` 아홉 블록과 "이 저장소의 특수성" 문단은 그 프로젝트의 층과 원칙으로 **새로 쓴다**. 골격만 복사하고 대부분을 다시 쓴다)
- `.github/workflows/claude-code-review.yml`. 유지보수성(리뷰 관점 넷)과 경계. 플러그인 대신 직접 프롬프트로, 읽을 파일(CLAUDE.md, CODING_STANDARDS.md, 용어집, rules)과 담당 축, 완료 조건(요약 코멘트 하나를 `gh pr comment`로)을 명시한다. 뒤에 "코멘트가 0개면 실패" 스텝을 둔다. `show_full_output: true`. 시크릿은 사람이 넣는다. (바꿀 곳: 경계 축 문장을 그 프로젝트의 원칙으로 새로 쓴다. agent-os 것은 LangGraph·LangChain 타입의 누출이다)
- `.claude/agents/coderabbit-review.md`. CLI 실행, 좌석 확인(`coderabbit auth status`의 `Seat:`), 트리아지. 코드를 고치지 않는다. (바꿀 곳: 오탐 목록을 그 프로젝트의 자동 검사가 잡는 것으로)
- `.claude/agents/bug-perf-review.md`. CLI가 못 돌 때(미설치, 로그인·좌석 없음, 한도 초과) 버그·성능 축을 같은 트리아지(유효·오탐·보류)로 본다. 보안 축은 내장 `/security-review`가 맡는다(agent-os ADR 0006의 2026-10-07 이력). (바꿀 곳: 성능 항목의 훅 시간 포인터를 그 프로젝트의 것으로)
- `.claude/agents/spec-reviewer.md`. 명세를 티켓 전에 검토하는 읽기 전용 검토자. 9단계 3번의 체크리스트와 질문의 원천이다. (바꿀 곳: 체크리스트 2와 6의 원칙 항목을 그 프로젝트 헌법으로)
- `.claude/skills/code-review/SKILL.md` 사본. 원본은 `<fixed-point>...HEAD`만 보고 리포트에서 멈춘다. 덧댄 것은 사본 첫머리 주석이 원천이다 — 범위를 미커밋·미추적까지, 보고 뒤 반영 절차, 본 범위 한 줄, 표준 축은 언제나 sonnet·high(agent-os ADR 0033), 요구·참고 가름, 두 브리프의 주장 검증 목록, 받는 쪽 확인. 근거 확인은 서브에이전트가 격리된 컨텍스트에서 ADR도 주변 코드도 모른 채 판단한다는 사실에 대한 장치이고, 부록 A의 초록 착시와 한 쌍이다. 문서만 바뀐 변경을 리뷰에서 면제하지 않는다. (바꿀 곳 0)
- 나머지 덧댄 사본 여섯(`grill-with-docs`, `grilling`, `implement`, `retro`, `to-spec`, `to-tickets`). 무엇을 덧댔는지는 각 사본 첫머리 주석이 원천이다. `grill-with-docs` 사본은 모델이 부르는 스킬이라 `tools/hook_grill_design_check.py`와 그 테스트, 등록(PreToolUse 매처 `Skill`), 페이로드 표의 두 건을 함께 복사한다. 훅을 복사하지 않는 프로젝트는 사본 첫머리 주석의 훅 문장을 뺀다. 덧댄 사본은 `npx skills update -p`가 조용히 되돌리므로 그 주석을 센티널로 삼아 지침 검사가 본다. 사람이 기억하는 대신 훅이 판정한다. 부록 A의 `disable-model-invocation` 줄과 같은 병이다. (바꿀 곳: 덧댐이 그 프로젝트에 맞지 않으면 사본을 원본으로 두고 `PATCHED_SKILLS`에서 뺀다)
- `.claude/skills/next-session/SKILL.md`. PR을 열거나 병합하면 다음 작업의 지시문(형식은 스킬)을 낸다. PR을 열었으면 그 세션이 반영과 병합까지 마친 뒤다. 인계 계기(`hook_handoff`)가 오면 결정표의 인계 줄로 새 세션에 넘기고 그 세션이 마친다. 인계 훅은 복사하지 않으므로(위 `.claude/settings.json` 항목) 새 프로젝트에서는 그 줄이 쓰이지 않는다. 세션을 끝내는 것은 그 사건이 아니라 지시문의 "어디서"다. 계기 훅을 위반 확인 전에 두는 이유는 10단계. (바꿀 곳: 결정표의 스킬 이름이 다르면 그것)
- `.claude/skills/open-session/SKILL.md`와 `tools/open_session.ps1`. **Windows 데스크톱 앱 전용이다.** 다른 OS면 이 항목을 건너뛰고 next-session 4단계에 "지시문을 낸 뒤 사람이 새 세션에 붙여 넣는다"는 대체 줄을 둔다. 지시문의 "어디서"가 새 세션이면 그 세션을 연다. 막힌 것이 없는 티켓이 둘 이상이면 next-session이 티켓마다 지시문을 내고 이 스킬이 차례로 전부 열며, 새 세션들은 지시문대로 각자 워크트리를 판다(딥링크가 폴더를 싣지 못해 여는 쪽이 워크트리를 고르지 못한다). 앱 딥링크(`claude://code/new?q=…`. 폴더를 실으면 신뢰 대화상자 뒤 폴더가 떨어진다)로 지시문이 채워진 세션 화면을 열고, 접근성 트리로 보내기와 분할 보기를 누른다. 첫 줄이 슬래시 명령이면 앱이 그 `/`를 전각 `／`로 바꿔 넣어 명령이 되지 못한다. 그래서 스크립트가 쏘기 전에 이 저장소의 스킬 명령을 그 스킬 파일을 읽어 따르라는 한 줄로 옮겨 사람 손 없이 보내고, 옮기지 못한 슬래시 명령만 보내기 전에 멈춰 사람이 첫 글자를 고쳐 보낸다. 제목은 여는 쪽이 아니라 새 세션이 스스로 브랜치명으로 바꾼다. 딥링크 URL은 윈도 명령줄로 넘어가 잘리므로 8000자 안이어야 한다. 앱이 업데이트를 위한 끝내기를 시작하고 끝내지 못하면 딥링크를 로그 없이 버려, 스크립트가 쏘기 전에 앱의 로그에서 그 표지를 찾고 멈춘다(`quitting=`, 부록 C). 칩·`claude --bg`·스케줄 실행을 버린 이유는 일지 2026-09-21 open-session. (바꿀 곳: 스킬 21행의 `-Folder` 경로)
- `.claude/skills/tidy-checkouts/SKILL.md`. 병합 뒤 주 체크아웃을 `origin/main`으로 당기고, 병합된 워크트리와 로컬 브랜치를 지운다. 주 체크아웃 세션에서만 돈다 — 워크트리 세션에서는 데스크톱 앱의 가드가 Bash 도구의 `git -C <루트> pull`을 거부했다. 주 체크아웃에서 병합하면 next-session이 부르고, 워크트리에서 병합하면 그 세션이 연 새 세션이 첫 턴에 워크트리에 들어가기 전에 부른다 — 지시문 "어디서" 줄의 워크트리 문장이 그것으로 시작하고, 나란히 여는 묶음이면 첫 세션만이다(이유는 next-session 3단계). 정리 절차가 없을 때 agent-os에는 병합된 워크트리 열여섯이 쌓였다(2026-10-05 워크트리 감사, 일지 2026-10-05-05). 지우는 판정은 병합된 PR의 머리와 HEAD가 같고, 깨끗하고, 그 워크트리에서 도는 세션이 없는 것이다. (바꿀 곳: 워크트리를 쓰지 않는 프로젝트면 건너뛴다. 세션 목록 도구(`list_sessions`)가 없는 환경이면 판정 3을 기계로 볼 수 없으니, 지우기 전에 목록을 사람에게 보이고 확인받는다)
- `.scratch/retro-queue.md`. 회고가 낸 후보 중 승인했으나 반영하지 않은 것의 표. 규약 셋 — 승인한 것만(승인은 retro가 판정한다), 닫으면 취소선, 번호는 영구 식별자. 없으면 승인된 회고가 일지 산문에만 남아 다음 세션이 파일 열여섯 개를 센다(agent-os 2026-09-22). (바꿀 곳: 머리말만 두고 표는 비운다)
- `docs/constitution/operations.md`의 리뷰 파이프라인 절. 커밋 전 셀프 리뷰, PR 직전 CLI, PR 봇(공개·유료면 둘, 아니면 Claude 하나), 초록 착시. (바꿀 곳: 절 구조만 복사하고 실측 항목(PR 번호, 좌석, 별 수)은 첫 PR 뒤에 그 프로젝트의 것으로 채운다)
- `README.md`의 원천 표. 사실 하나에 원천 하나. 두 곳이 다르면 원천이 맞고 나머지가 버그다. (바꿀 곳: 행 전부를 그 프로젝트의 문서로)

새 검사는 일부러 깨뜨려 빨강을 보고 원복한다. 통과만 보고 넣은 검사는 무엇이든 잡는다는 증거가 없다(선행 저장소는 이것 때문에 '실패해야 할 것이 성공으로 보이던' 문제를 다섯 번 겪었다). 복사한 검사는 `tests/tools/`의 테스트가 빨강의 증거라 `uv run pytest tests/tools`가 그 확인이고, 손 변이는 테스트가 없는 새 검사에만 한다. 최소 가드레일도 이때 건다. pre-commit 훅이든 CI 잡이든 린트와 테스트가 자동으로 도는 곳 하나. retro 기준으로 가드레일 없는 저장소는 그 자체가 결함이다.

디렉터리별 규칙 파일을 `.claude/rules/<dir>.md`로 만든다. 헌법 인터뷰에서 나온 디렉터리 한정 결정이 내용이고 `paths` 프론트매터가 필수다. 각 파일 첫머리에 원천(코드·테스트 또는 ADR·명세)을 적고 "코드와 다르면 코드를 고치거나 ADR을 남긴다"를 둔다. 코드 독스트링과 같은 문장을 되풀이하지 않는다 — 결정과 ADR 번호는 rules에, 논증은 코드에(agent-os는 다섯 쌍이 글자 그대로 중복되어 있었다). 린터가 판정하는 것(import 경계)은 도구 설정을 가리키기만 한다.

선택: 스택이 정해졌으면 LSP 플러그인을 프로젝트 스코프로 설치한다. `.claude/settings.json`의 `enabledPlugins`에 기록되어 저장소와 함께 간다. `--scope project`여도 플러그인 캐시는 사용자 폴더에 있어 저장소 밖에 닿는다.

사람 몫(허락): 그 언어의 LSP 플러그인을 `claude plugin install typescript-lsp@claude-plugins-official --scope project`로 설치한다. 플러그인 이름은 그 프로젝트의 언어로 바꾼다(스택이 정해졌을 때만).

```bash
claude plugin install typescript-lsp@claude-plugins-official --scope project
```

언어 서버 바이너리는 따로 설치해야 한다. 설치 길은 OS와 언어마다 달라 이 런북이 갖지 않는다.

사람 몫(사람만): 그 플러그인이 부르는 언어 서버 바이너리를 이 기계에 설치한다(LSP 플러그인을 설치했을 때만). 확인: 그 바이너리의 `--version`

안 쓰는 전역 스킬, 플러그인, MCP 서버를 꺼서 매 세션 컨텍스트와 오트리거를 줄인다. 끈 전후는 `/context`로 잰다. `/context`, `/plugin`, `/mcp`는 대화형 화면과 내장 명령이라 사람이 친다.

사람 몫(사람만): 끄기 전에 이 세션의 입력창에 `/context`를 친다(아래에서 끌 전역 스킬, 플러그인, MCP 서버가 있을 때만). 확인: 세션이 대화에 들어온 출력을 읽어 일지에 적는다

`.claude/settings.json`의 `skillOverrides`에 이 프로젝트가 안 쓰는 전역 스킬(jira-* 등. git-pr*는 PR 흐름이 쓰므로 끄지 않는다)을 `"off"`로 적는다. `kickoff`도 끄지 않는다. 끄면 이 프로젝트에서 `/kickoff`로 이을 수 없다. 이름이 같은 플러그인 스킬(`coderabbit:code-review` 등)은 `skillOverrides`로 끌 수 없으니(부록 C) 안 쓰면 `/plugin`으로 플러그인째 끈다. 안 쓰는 MCP 서버와 같은 서버 두 벌도 `/mcp`로 끈다.

사람 몫(사람만): 안 쓰는 플러그인과 MCP 서버를 이 세션의 `/plugin`·`/mcp` 화면에서 끈다(끌 것이 있을 때만). 확인: 없음 — 대화형 화면이다

사람 몫(사람만): 끈 뒤에 다시 `/context`를 친다(끈 것이 있을 때만). 확인: 세션이 대화에 들어온 출력을 읽어 일지에 적는다

## 8단계. 첫 커밋과 첫 PR

첫 커밋은 main 위에서 한다. 7단계가 등록한 `hook_git_main_commit`은 커밋이 하나도 없는 저장소의 첫 커밋을 지나가게 한다. 진행 파일과 일지도 이 커밋에 든다.

```bash
git add -A && git commit -m "chore: 하네스 킥오프 (헌법, CLAUDE.md, 코딩 표준, 스킬)"
```

포함: `.claude/skills/`, `.claude/settings.json`(있으면), `CLAUDE.md`, `CODING_STANDARDS.md`, `docs/`(일지), `.scratch/`(진행 파일, `plan.md`, 대기열), `.github/`, `tools/`, 골격.

첫 커밋 뒤에는 main 위의 커밋을 그 훅이 막는다. 그래서 그 뒤에 바뀐 진행 파일과 일지는 `chore/kickoff` 브랜치의 첫 PR이 싣는다. 차례는 아래 1~6이다. 그다음 기능부터는 브랜치 → `/git-pr` → CI 초록 → `/git-pr-merge`(squash)다.

**1. 원격과 보호, 봇의 전제.** 첫 커밋 뒤 원격을 만들고 푸시한다. 주인과 이름, 공개 여부(`--public`이나 `--private`)는 준비에서 정한 것이다.

사람 몫(허락): GitHub에 저장소를 만들고 첫 커밋을 푸시한다. 칠 명령은 `gh repo create <owner>/<repo> --<공개 여부> --source=. --push`이고, 자리표시자는 준비에서 정한 주인과 이름, `public`이나 `private`로 채운다.

```bash
gh repo create <owner>/<repo> --<공개 여부> --source=. --push
```

main을 보호한다. 필수 상태 검사 `verify`(CI 잡 이름), strict, 선형 이력, 강제 푸시·삭제 금지. PR 필수는 두지 않는다 — main에 닿는 커밋을 거르는 것은 필수 검사다. 혼자면 관리자 우회를 허용해 두고 팀원이 생기면 끈다. 관리자 우회는 사람의 토큰으로 도는 에이전트에게도 열려 있고(`gh pr merge --admin`, main 직접 푸시), 로컬 훅은 커밋만 막는다(GitHub 문서상의 동작이고 agent-os는 재지 않았다). 그래서 병합은 체크를 먼저 보는 `/git-pr-merge`로만 한다(워크트리에서는 그 스킬이 main을 가로채므로, 같은 체크를 본 뒤 `--delete-branch` 없이 병합하는 next-session "워크트리에서 병합할 때"의 길로). 팀이면 리뷰 승인 필수와 CODEOWNERS를 첫날에 더한다. 요청 본문은 7단계에서 복사한 `tools/protection.json`이다(agent-os의 실제 설정을 2026-09-28에 `gh api repos/<owner>/<repo>/branches/main/protection`으로 내보낸 것. 원격이 바뀌면 같은 명령으로 다시 뽑는다).

사람 몫(결정): 혼자인지 팀인지. 팀이면 리뷰 승인 필수와 CODEOWNERS를 첫날에 더하고 관리자 우회를 끈다.

사람 몫(허락): `gh api -X PUT repos/<owner>/<repo>/branches/main/protection --input tools/protection.json`으로 main을 보호한다(공개 저장소이거나 유료 플랜일 때만. 무료 플랜의 비공개 저장소는 403이다).

```bash
gh api -X PUT repos/<owner>/<repo>/branches/main/protection --input tools/protection.json
```

준비에서 무료 플랜에 비공개를 골랐으면 이 보호는 생략하고 `/git-pr-merge`가 게이트다. 고른 것을 `operations.md` 가드레일 절에 적는다. 나중에 공개로 바꾸면 그날 보호를 건다(agent-os는 셋째 날 공개 전환 뒤 걸었다). 상세는 `kickoff/pitfalls.md`·`kickoff/facts.md`.

봇 리뷰의 전제 둘은 사람이 한다. 에이전트는 토큰과 시크릿을 다루지 않는다. 하나는 저장소 시크릿이다. 다른 하나인 CodeRabbit CLI 로그인과 좌석 확인은 원격에 기대지 않아 준비에서 했다(준비의 "CodeRabbit").

사람 몫(사람만): `claude setup-token`으로 토큰을 만들어 이 저장소의 시크릿 `CLAUDE_CODE_OAUTH_TOKEN`으로 넣는다. 자리는 GitHub 저장소의 Settings → Secrets and variables → Actions이거나, 터미널의 `gh secret set CLAUDE_CODE_OAUTH_TOKEN`이다. 확인: `gh secret list`에 그 이름과 넣은 시각. 에이전트는 이름과 시각만 본다

CodeRabbit GitHub App은 공개 저장소이거나 CodeRabbit 유료 플랜일 때만 설치한다. 공개라도 별이 10개 미만이면 자동 리뷰가 없고 PR마다 `@coderabbitai review`로 부른다(agent-os PR #12·#43 실측, 2026-09-21·22. OSS PR 리뷰 상한은 별 수에 따라 시간당 1~10회이고 별이 적으면 하한 쪽이다). 비공개 저장소에 무료 플랜이면 설치해도 Walkthrough 요약만 남고 체크는 `pass`다(agent-os PR #2 실측, 2026-09-20). 플랜·요금 사실의 확인일은 `kickoff/facts.md`에 모아 둔다. 설치 여부는 PR의 `coderabbitai[bot]` 코멘트로만 확인할 수 있고 설치 목록 API는 앱 토큰이 필요해 `gh`로는 403이다. 체험은 자동으로 켜지지 않고 시트는 대시보드 team-management에서 사람이 할당한다.

사람 몫(사람만): 브라우저에서 CodeRabbit에 GitHub 계정으로 로그인하고, 이 저장소에 CodeRabbit GitHub App을 설치한다(공개 저장소이거나 CodeRabbit 유료 플랜일 때만). 확인: 없음 — 설치 여부는 PR의 `coderabbitai[bot]` 코멘트로만 보이고 이 자리에는 PR이 아직 없다. 첫 PR을 연 뒤 그 코멘트로 대 본다

**2. 첫 PR.** `git switch -c chore/kickoff`로 브랜치를 따서, 첫 커밋 뒤에 바뀐 진행 파일과 일지를 커밋한다.

사람 몫(허락): 첫 PR을 연다. `chore/kickoff` 브랜치를 `git push -u origin chore/kickoff`로 푸시하고 `/git-pr`로 연다. 이 허락은 병합까지 그 브랜치에 다시 푸시하는 것도 덮는다.

PR을 열면 7단계가 복사한 `hook_pr_next_session`이 next-session을 지금 돌리라는 계기를 넣는다. 그 스킬의 1단계는 병합까지 가므로 첫 PR에서는 따르지 않는다. next-session은 아래 6의 병합 뒤에 읽는다.

**3. CI와 봇.** CI와 Claude Code Review를 본다. Claude Code Review가 실제로 코멘트를 남기는지 본다. 코멘트 없는 초록은 전제가 빠진 것이다. Claude Code Review는 지적이 없을 때 코멘트를 안 남기고 초록이 되기도 하므로(agent-os 실측, 4턴 실행) 워크플로에 `show_full_output: true`를 켜 두고 로그로 실행 내용을 확인한다. CI가 빨가면 고쳐 같은 브랜치에 푸시한다.

사람 몫(허락): 첫 PR에 `gh pr comment <번호> --body "@coderabbitai review"`로 CodeRabbit 리뷰를 부른다(App을 설치했고, 공개 저장소이고, 별이 10개 미만일 때만).

1의 App 줄에서 "했다"를 골랐으면 여기서 PR의 `coderabbitai[bot]` 코멘트로 대 본다. CI와 Claude Code Review가 끝나고 CodeRabbit을 불렀으면 그 리뷰까지 끝났는데 그 코멘트가 없으면, 무엇이 없는지 보이고 App 줄을 다시 묻는다(설치를 다시 본다 / 건너뛴다).

**4. 마무리 확인.** 하네스가 다 깔린 이 자리에서 항상 로드 분량을 잰다. 줄 수는 대리 지표일 뿐이다(3단계).

사람 몫(사람만): 이 세션의 입력창에 `/context`를 친다. 확인: 세션이 대화에 들어온 출력을 읽어 일지에 적는다

준비부터 여기까지 건너뛴 사람 몫을 진행 파일에서 모아 보인다.

사람 몫(결정): 건너뛴 사람 몫을 지금 할지. "지금 한다"를 고르면 그 줄마다 갈래대로 다시 묻는다(건너뛴 것이 있을 때만).

그 뒤 아래 첫날 종료 체크리스트를 진행 파일과 대조해 보인다.

**5. 회고.** 일지의 `## 다음`을 9단계 1(`/grill-with-docs`로 첫 기능의 설계 인터뷰)로 적고, 새 프로젝트의 `retro` 스킬 파일(`.claude/skills/retro/SKILL.md`)을 Read로 읽어 따른다(10단계). 회고가 끝나면 진행 파일의 8단계를 끝남으로 적고, 회고가 바꾼 일지와 대기열과 함께 커밋해 같은 브랜치에 푸시한다. 끝남을 회고 뒤에 적는 것은 회고 도중에 끊겨도 다음 `/kickoff`가 회고로 돌아오게 하기 위해서다. 병합 뒤에는 main에 커밋할 수 없으므로 회고는 여기서 끝낸다.

**6. 병합.** 회고까지 실은 첫 PR을 병합한다.

사람 몫(허락): 첫 PR을 `/git-pr-merge`(`gh pr merge --squash --delete-branch`)로 병합한다. 그 스킬이 CI를 먼저 보고, 빨가면 병합하지 않고 그 실패를 고친다.

병합 뒤 새 프로젝트의 `next-session` 스킬 파일을 Read로 읽어 따라 9단계 1의 지시문을 낸다. Windows 데스크톱 앱이면 `open-session`이 새 세션을 열고, 다른 OS면 사람이 그 지시문을 새 세션에 붙여 넣는다.

## 9단계. 첫 기능

기능마다 이 순서. 원천은 복사 목록의 `to-tickets` 사본 1단계이고 여기는 첫날을 위한 요지다. 건너뛸지의 기준은 "몇 개를 건드리나"가 아니라 "건드리는 곳마다 새로 정할 것이 있나"다. 같은 패턴의 N번째 반복은 여러 모듈을 관통해도 새 결정이 없으므로 설계 인터뷰 없이 바로 시킨다.

첫 기능 전에 공통 규약을 정한다. 식별자 형식, 에러 봉투, 시간대, 디스크 형식의 버전. 도메인마다 다시 정하면 어긋난다. 미루는 것은 괜찮지만 미룬 자리에 판정 장치(드리프트 검사 테스트)는 둔다. 원천 → 생성물 방향을 하나로 고정하고 생성물은 커밋하며 드리프트 검사는 CI가 아니라 테스트에 둔다.

리뷰에서 보류한 지적은 그 자리에서 다 고치지 않고 별도 티켓으로 뺀다. 계획이나 명세는 사후에 실제 구현대로 고쳐 쓰지 않는다. 어긋난 지점이 기록이다. 살아남은 결정만 ADR로 승격한다.

각 단계의 절차는 그 스킬·서브에이전트 파일이 원천이다. 여기는 순서와 새 프로젝트가 바꿀 자리만 적는다.

1. `/grill-with-docs` 로 설계 인터뷰. 용어는 `CONTEXT.md`, 결정은 `docs/adr/`에 쌓인다. 화면이 있는 기능의 인터뷰는 반응형을 묻는다. 무엇의 폭에 반응하는지(창인지 자기 자리인지. 남의 페이지 안의 한 자리에 들어가는 것은 대개 자기 자리의 폭이다), 어느 폭까지 대응하는지(모바일, 접근성 목표의 리플로 폭), 기준 폭을 어떤 단위의 토큰으로 두는지다. agent-os는 디자인 시스템 인터뷰가 이것을 빠뜨려, ADR이 병합된 뒤 사용자가 묻고서야 정했다(ADR 0026의 첫째 2026-10-06 이력). 디자인 도구(agent-os는 Claude Design)에서 그리는 단계가 있으면, 그리기 전에 에이전트가 붙여 넣을 시작 프롬프트를 써서 `.scratch/<slug>/design/`에 둔다. 그런 단계는 디자인 시스템의 방향 탐색(색과 글꼴, 한 번)과 기능마다 명세 전에 그리는 화면이다. 프롬프트를 쓰기 전에 참고 디자인을 정한다. 사람에게 참고할 디자인이 있는지 먼저 묻고, 있으면 그것에서 규칙을 뽑고, 없거나 셋보다 적으면 세션이 찾아 채운다. 디자인 시스템을 도구에 올릴 때는 겉모습(보여 주기용 미리보기, 기초 카드, 목록 타일)도 함께 올린다. 차례는 `kickoff/prompting.md`의 "참고 디자인 조사" 절이다. agent-os는 처음 탐색에 참고 없이 위젯과 관리 화면을 한꺼번에 넣었고, 올린 디자인 시스템을 본 사용자가 디자인이 예쁘지 않다며 관리 화면에 맞게 다시 디자인해 달라고 했다(2026-10-12). 프롬프트는 근거 문서(ADR, 계획의 기능 행, 명세)가 정한 제약, 그릴 것, 화면 문구에 쓸 용어집의 말을 담고, 결정이 아닌 가정은 따로 밝힌다. 디자인 시스템의 방향 탐색 프롬프트가 받아 올 항목, 프롬프트를 나누는 자리(사람이 고르는 자리에서만), 사람과 세션의 일을 가르는 법은 `kickoff/prompting.md`의 "디자인 탐색 프롬프트가 담을 것" 절이다. 도구의 템플릿이 긴 글 대신 질문 양식을 띄우면 프롬프트를 양식 칸마다의 짧은 답으로 쓴다(agent-os는 Claude Design의 Color + type pairing 템플릿이 칸마다 400자인 양식을 띄웠고, 붙인 긴 글은 잘렸다). 도구 안의 조작(새 프로젝트, 템플릿, 양식 채우기, 프롬프트 붙여 넣기)과 결과를 내려받아 정해진 자리(저장소의 바로 위 폴더)에 두는 일은 기본으로 세션이 내장 브라우저로 한다. 사람은 로그인하고, 세션이 채운 화면을 보인 뒤 보내기와 내려받기마다 허락하고, 나온 안을 고른다(agent-os는 2026-10-12 사용자가 직접 만들어 줄 수 없느냐고 물어 그렇게 바꿨다). 고르기는 추천을 맨 앞에 둔 선택 화면으로 묻고, 테마가 여럿이면 이름도 그렇게 고른다. 차례와 기준은 `kickoff/prompting.md`의 "디자인 탐색 프롬프트가 담을 것" 끝과 "테마 이름 짓기"다. 사람이 원하거나 내장 브라우저가 없는 환경(데스크톱 앱 밖)이면 사람이 붙여 넣고 그 자리에 저장한다. 차례와 막히는 곳은 `kickoff/prompting.md`의 "디자인 탐색 프롬프트가 담을 것" 절 끝이다. agent-os에서는 프롬프트 없이 탐색을 넘기자 사람이 무엇을 하는 단계인지부터 되물었다(2026-10-06, `.scratch/design-system/design/exploration-prompt.md`).
2. `/to-spec` 으로 대화를 명세로.
3. 읽기 전용 서브에이전트 `spec-reviewer`(복사 목록)가 명세를 검토한다. 체크리스트 일곱과 질문 둘은 그 파일에 있고, 새 프로젝트는 체크리스트 2와 6의 원칙 항목을 그 프로젝트 헌법으로 바꾼다. agent-os는 첫 기능에서 일회성 호출로 시작해 두 번째 기능(http-channel)에서 파일로 굳혔다.
4. `/to-tickets` 로 수직 슬라이스 티켓. 원격 트래커면 4단계에서 적은 흐름대로 발행한다.
5. `/implement` 로 구현. tdd 스킬이 테스트 먼저를 강제한다. 이 티켓의 몫만 쓴다.
6. 커밋 전 `/code-review`. 범위(미커밋·미추적까지)와 반영 규칙(Critical·Major는 커밋 전에, 근거를 먼저, 보류는 티켓이나 회고 후보로)은 사본 6단계가 원천이다.
7. PR 직전 `coderabbit-review` 서브에이전트. 좌석이 있을 때만이다(준비). CLI가 못 돌면(미설치, 로그인·좌석 없음, 한도 초과) 내장 `/security-review`(보안)와 `bug-perf-review` 서브에이전트(버그·성능)를 나란히 돌린다.
8. `/git-pr`로 PR. 별이 10개 미만인 공개 저장소는 `gh pr comment <번호> --body "@coderabbitai review"`로 부른다. 봇 둘과 CI의 역할 분담, 코멘트 0개인 초록을 읽는 법은 `operations.md` 리뷰 파이프라인이 원천이다. `/git-pr-feedback`으로 반영하고 `/git-pr-merge`로 squash 병합한다. 반영과 병합은 PR을 연 세션이 하고(인계 훅을 들인 프로젝트에서 인계 계기가 오면 인계로 연 세션이 한다), 병합 뒤는 10단계다.

## 10단계. 세션 마감

단계를 닫는 순간의 지침은 어겨진다. 그래서 마감의 셋은 스킬과 훅이 들고 이 절은 그것들을 가리킨다.

- **회고**는 `retro` 스킬이 계기에 스스로 돈다. 계기는 스킬 description에 적되 "세션이 끝나면" 같은 관찰 불가능한 것이 아니라 관찰 가능한 사건(일지의 "다음" 갱신, 마무리 발화)으로, 지침이 어겨진 뒤 훅으로 옮겼다(`tools/hook_journal_retro.py`, 복사 목록). 후보마다 승인·기각·넘김을 스스로 판정해 심각도 순으로 보이고, 사람에게 넘긴 것만 묻는다. 무엇을 넘기고 무엇을 스스로 승인하는지는 retro 사본 4단계가 원천이다. agent-os는 회고마다 사람의 답을 기다리다가 2026-10-12에 사용자 요청으로 이렇게 바꿨다. 승인했으나 이 세션에서 반영하지 않는 것은 `.scratch/retro-queue.md`에 짧은 행으로 적는다. 원본 스킬의 플래그를 왜 빼는지는 `kickoff/pitfalls.md`.
- **다음 작업**은 `next-session` 스킬이 지시문으로 낸다. PR을 열거나 병합하면 훅(`tools/hook_pr_next_session.py`)이 계기를 넣고, 결정표가 "어디서"를 정한다. 결정표에 "회차 3 이상이면 chore 배치" 줄을 처음부터 둔다 — 대기열은 유입에만 계기가 있으면 자란다(agent-os는 그 줄 없이 아홉 날 동안 승인 행 서른여덟 중 둘만 닫았다, 2026-09-28 아침 감사 시점). 진행 상태는 메모리에 적지 않는다. 저장소(일지의 "다음", `plan.md`, 대기열)가 원천이고, 메모리에 둔 스냅숏은 하루 만에 두 곳이 틀렸다(agent-os 2026-09-22).
- **승격 사다리**는 `.claude/rules/tools.md`와 `CLAUDE.md` 교정 루프가 원천이다. 기계적 위반은 린터 규칙이나 훅으로, 판단 기준만 `CODING_STANDARDS.md`로. 같은 실수가 세 번 반복되면 규칙(`CODING_STANDARDS.md`의 줄) 후보, 지침으로 적은 뒤에도 어겨지면 훅 후보. 막는 훅은 어겨진 것이 확인된 뒤에만 더하되 실패가 조용하고 패턴이 고정된 것은 첫 사건에서 가고, 계기로는 때를 맞출 수 없어 사용자가 막기를 고른 것도 간다. 계기만 넣는 훅은 단계를 닫는 지침에 처음부터 붙인다 — 거짓 양성의 비용이 문장 하나라 게이트의 사다리를 타지 않는다. 지침이 길어졌으면 잘라낸다. `/context`로 항상 로드 분량을 실측해 늘었으면 3단계의 배치 기준으로 다시 나눈다.

## 첫날 종료 체크리스트

각 항목 끝의 괄호는 산출 단계다.

- [ ] superpowers 비활성, 전역 CLAUDE.md 비어 있음, 프로젝트가 관리하는 스킬의 전역 사본 없음, 사용자 레벨 진행 스킬 `~/.claude/skills/kickoff/SKILL.md`가 이 런북 clone을 가리킴, 안 쓰는 전역 스킬은 `skillOverrides`로, 안 쓰는 플러그인과 MCP 서버는 `/plugin`·`/mcp`로 꺼짐 (0·7)
- [ ] `npx skills ls`의 목록이 2단계 설치 목록 + 7단계에서 더한 스킬(next-session, open-session, tidy-checkouts)과 같다 (2·7)
- [ ] `CLAUDE.md`: 레이어 역할, 지도(언제 읽나), 검증 명령, 작업 규약, 교정 루프와 로드 시점 표, 환경 함정. `@` 임포트는 principles.md 하나 (3)
- [ ] `docs/agents/issue-tracker.md`에 4단계에서 고른 트래커의 흐름 기록 (4)
- [ ] `docs/PRD.md` 한 장, `docs/constitution/` 세 파일 빈 칸 없음, 한국어, `docs/adr/README.md` 색인 (5)
- [ ] `CODING_STANDARDS.md` 존재, 판단 기준 비어 있음 (6)
- [ ] 테스트, 린트, 타입체크 명령 통과. 가드레일 하나 이상 (7)
- [ ] `.claude/settings.json`에 훅 등록과 `permissions.deny`(`.env`). 훅마다 `tools/hook_payloads.toml`에 발동·침묵 사례가 있고 `uv run python tools/run_hooks.py`와 `uv run pytest tests/tools`가 초록 (7)
- [ ] PR 템플릿, commit-msg 훅(빨강 확인), 지침 검사(상수를 이 프로젝트에 맞춤), CI 워크플로, `.coderabbit.yaml`, Claude Code Review 워크플로, 서브에이전트 셋, `.claude/rules/` 디렉터리별 규칙과 `tools.md`, `.scratch/retro-queue.md`, README의 원천 표 (7)
- [ ] 첫 커밋 완료. 원격 생성과 푸시, 첫 PR이 CI를 통과. main 보호를 걸었거나(`tools/protection.json`) free+비공개라 `/git-pr-merge` 게이트를 `operations.md`에 적었다 (8)
- [ ] 봇 전제 둘(`CLAUDE_CODE_OAUTH_TOKEN` 시크릿, CLI 로그인과 `Seat:` 확인). 첫 PR에서 Claude 코멘트 확인. CodeRabbit App은 공개 저장소나 유료일 때만 (준비·8)
- [ ] `docs/journal/` 첫 파일과 기록 규칙, `.scratch/plan.md` 첫 판 (준비·4)
- [ ] `/context` 실측값을 일지나 ADR에 기록 (8)

## 부록

런북 저장소의 `kickoff/` 아래에 있다. 새 프로젝트도 clone 한 런북 저장소에서 상대 경로로 읽는다.

- `kickoff/runner.md` — 진행 규율. `/kickoff`와 머리의 첫 시작 한 줄이 이것을 읽게 하고, 세션이 이대로 준비부터 8단계까지 차례로 진행하며 사람 몫 줄에서 멈춘다. 순서, 멈출 자리, 선택 화면, 진행 기록만 갖는다.
- `kickoff/skill-template.md` — 사용자 레벨 스킬 `kickoff`의 원문. 진행 규율의 시작 확인이 자리표시자 `<clone>`을 그 기계의 clone 경로로 바꿔 `~/.claude/skills/kickoff/SKILL.md`로 만든다.
- `kickoff/progress-template.md` — 진행 파일 `.scratch/kickoff.md`의 모양. 준비의 첫 일로 복사한다.
- `kickoff/claude-md-template.md` — 3단계 CLAUDE.md 템플릿.
- `kickoff/pitfalls.md` — 부록 A. 세팅 중 실제로 걸린 함정. 조용히 통과하는 것을 시끄럽게 만든 기록.
- `kickoff/prompting.md` — 부록 B. 세팅 프롬프트와 스킬·서브에이전트를 쓸 때. 디자인 탐색 프롬프트가 담을 것과 참고 디자인 조사도 여기다.
- `kickoff/facts.md` — 부록 C. 플랜·요금·플랫폼 사실과 확인일. 날짜가 없는 값은 추정으로 읽는다.

## 세 번째 프로젝트가 끝나면

이 런북을 세 번 돌린 뒤 매번 같은 곳을 손봤다면 그 부분만 본인 스킬로 만든다. 그 전에는 도구를 만들지 않는다. 다만 7단계의 복사 목록이 첫 주에 다섯 번 늘었으므로, 두 번째 프로젝트에서 그 목록을 매니페스트 파일(경로 | 바꿀 자리 | 확인법)로 굳히는 것은 도구가 아니라 목록이라 이 규칙과 충돌하지 않는다. 킥오프를 순서대로 진행하는 얇은 진행 스킬도 이 규칙의 예외다. 단계의 내용은 이 런북에 두고 스킬은 순서, 멈출 자리, 선택 화면, 진행 기록만 갖는다(agent-os ADR 0028, 진행 규율은 `kickoff/runner.md`).
