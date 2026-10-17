# 2026-10-17 (02) 디자인 시스템과 화면을 Claude 아티팩트로 옮기는 탐침과 설계

next-session 지시문으로 연 admin-style 명세 세션이다. 주 체크아웃에서 브랜치를 따지 않고 워크트리
`.claude/worktrees/admin-style-spec`에 들어가 브랜치를 `docs/admin-style-spec`으로 바꿨다. 선행 조건(화면을 그려 고르기)이
채워지지 않아 이 세션이 내장 브라우저로 Claude Design에서 그리려다 계정이 엇갈린 것을 보았고, 사용자의 질문을 따라가다
같은 세션에서 design-artifacts를 했다. 브랜치는 `docs/design-artifacts`로 바꿨다(워크트리 폴더 이름은 그대로다).
admin-style의 명세는 쓰지 않았다. 산출물은 다음과 같다.

- ADR 0025의 2026-10-16 이력 "디자인 시스템과 화면은 Claude 아티팩트에 두고, Claude Code가 편집자로 저장소에서 올린다"와
  본문 포인터 둘, ADR 0026의 포인터 둘
- `.scratch/design-artifacts/probes/`(해시 대조, 요금제 비교표, 공식 안내 원문의 구절, `web-design.md` 카나리아)
- `docs/agents/issue-tracker.md` 화면 디자인 절, `.design-sync/NOTES.md`, `kickoff/prompting.md`, `.claude/rules/web-design.md`,
  `README.md`, 헌법 `tech.md` 웹 행(3.0.38)
- `.scratch/admin-style/design/screens-prompt.md`의 하는 법과 고른 뒤, 패턴 참조를 모양으로 고친 것
- `plan.md`의 design-artifacts 행, admin-style·web-widget 행, 프론티어 문단
- Claude 쪽: 디자인 시스템 아티팩트 https://claude.ai/artifact/8ttLDZQqchfD2ao1XG56GH (주인 njh4803, 편집자 njh6803)

> 사용자: ".claude/skills/to-spec/SKILL.md 를 읽어 그대로 따른다. … 다음 작업: 기능 admin-style. 관리 화면을 새 디자인
> 시스템으로 그리고 명세를 세운다 … 확인할 선행 조건: 명세 전에 사람이 /design-sync로 디자인 시스템을 다시 맞추고
> screens-prompt.md로 Claude Design에서 화면을 그려 골라야 한다(plan.md admin-style 행) 이번 요청 범위: PR과 병합까지"

## 선행 조건과 그리기 시도

`packages/ui`는 2026-10-14 동기화 뒤로 바뀌지 않았고(마지막 변경 `e7ca8193`), 화면은 그려지지 않았다(`C:\project`에
관리 화면 ZIP이 없고 지시문에 프로젝트 링크가 없다). 선택 화면으로 물었다.

> 사용자(질문에 답): "제가 브라우저로 그림 (추천)"

내장 브라우저로 claude.ai/design을 열었고 사용자가 로그인했다. Wireframe 템플릿을 골랐다. 프롬프트를 넣기 전에, 프롬프트가
"디자인 시스템 문서의 패턴 03.x"를 가리키는데 Claude Design의 디자인 시스템 프로젝트에는 컴포넌트 카드·기초 카드·판단
기준만 오르고 패턴은 없다는 것과 그 번호가 옛 v3 파일의 것이라는 것을 찾았다. 재탐색 디자인 파일 3절의 규칙에서 관리
화면의 결정과 어긋나는 것(거르기 지우기, 트레이스로 가는 링크)을 빼고 모양으로 옮겼고, 부품 목록의 "표면"을 "카드"로
고쳤다. 입력창의 글(2,715자, 21줄)이 파일의 글과 같다는 것을 FNV 해시로 대 봤다. 보내기 전에 사용자가 멈췄다.

> 사용자: "일단 여기까지 하고 멈추자"

## 계정

> 사용자: "메인 계정인 njh4803 계정의 클로드 디자인에 디자인 시스템이랑 Color and type pairings 있어. 그걸 이 계정의
> 클로드 디자인에 공유하거나 복제할 수 있어?"

브라우저는 그사이 njh4803으로 로그인되어 있었고, 그 계정의 디자인 시스템 ID가 `.design-sync/config.json`의 `projectId`와
같았다. 처음 프롬프트를 넣은 계정에도 "Agent OS 디자인 시스템"(Org default)이 있었는데, 2026-10-12에 다른 계정에 남은 첫
프로젝트일 수 있다(확인하지 않았다). 그 계정에서 보냈으면 옛 디자인으로 그려졌을 수 있다. Share 창의 접근 범위는 "Only you"와
"Your workspace" 둘뿐이었고, 프로젝트 메뉴의 Duplicate는 같은 계정 안의 사본이다. Claude Code는 njh6803으로 로그인되어
있다(`claude auth status`).

> 사용자: "개인 요금제의 워크스페이스에 멤버를 더할 수 있는지는 확인하지 않았습니다. 확인해줘"

njh4803은 맥스 플랜이고 설정에 조직·멤버 탭이 없다. 요금제 비교표 원문을 내려받아 표를 스크립트로 읽었다("Project sharing
and collaboration"이 Free·Pro·Max 모두 no, Team·Enterprise yes). Team 안내 원문은 만드는 사람이 업무용 이메일을 써야 하고
@gmail.com 같은 공개 도메인은 안 되며 두 명 이상이라고 적는다.

> 사용자: "공유할 수 있는 방법이 없을까? 클로드코드 design.md로 라던지 UI 목업이나 와이어프레임도 프로젝트 내에 파일을
> 저장하고 불러와서 동기화 하는 방식으로 버전을 명시해서 동일 버전인지도 확인할 수 있게"

단독 Claude Design이 2026-12-14에 닫히고 Claude 아티팩트로 옮겨 간다는 것, 아티팩트는 Pro·Max에서도 이메일로 편집자를
초대할 수 있다는 것(베타)을 원문으로 대 봤다. 이 세션의 Artifact 도구에 Design과 Design System 형식이 있고, Design System
아티팩트는 `project/` 아래 파일 묶음이라 저장소에서 파일을 올리고 받아 대 볼 수 있다. 전환을 재는 세션을 제안했다.

> 사용자: "현재는 njh6803 으로 시작하고 njh4803으로 추후에 주인으로 바꿀 수 있어?"

주인을 옮기는 기능은 문서에 없고, 개인 계정 사이에 데이터를 옮기는 것도 지원하지 않는다(원문). 처음부터 njh4803을 주인으로
세우는 길을 추천했다.

> 사용자: "njh4803을 주인으로 하고 njh6803을 편집자로 초대하는 길로 가자."
>
> 사용자: "진행"

njh4803의 Artifacts 화면에서 "팀 디자인 시스템 마이그레이션"을 눌렀고(확인 창 없이 돌았다), 옮겨진 아티팩트의 공유 창에서
njh6803을 편집자로 초대했다. Claude Code의 `read`는 "artifact not found"였고 njh6803의 브라우저에서도 열리지 않았다.

> 사용자: "보여 내가 수락을 안눌렀어"

수락한 뒤 `read`가 "shared with you from another organization (writer…)"로 읽었다. 디자인 시스템 계정 구성은 auto-memory에
적었다. 제안 카드를 새 사실로 바꿔 올렸다.

> 사용자: "이 작업을 여기에서 진행해 주세요: "디자인 아티팩트로 옮기는 탐침과 설계""

## 탐침과 결정

브랜치를 `docs/design-artifacts`로 바꿨다. 잰 것은 프로브 README가 원천이다.

- 해시 대조: 아티팩트의 `project/guidelines/web-design.md`와 `project/foundations/<이름>/index.html` 넷이 저장소의
  `.claude/rules/web-design.md`, `.design-sync/foundations/`와 sha256까지 같다. 그래서 빌드의 `ds-bundle/<경로>`가
  아티팩트의 `project/<같은 경로>`다.
- Claude Code의 디자인 시스템 목록(`quickstart`)에는 다른 계정이 공유한 이 디자인 시스템이 나오지 않는다.
- 옮긴 원문을 대 보다가 웹 요약의 "On later runs, systems changed in Claude are skipped"가 원문에 그 글자로 없는 것을
  찾았다. 원문은 "Changed in Claude since it was migrated … left as they are"다.

쓰기 전에, 한 번 쓰면 다시 옮기기가 이 디자인 시스템을 건너뛰어 단독 쪽과 갈라진다는 것을 알리고 물었다.

> 사용자(질문에 답): "Claude Code가 직접 (추천)", "njh4803으로 저장소?프로젝트?를 생성만하고 njh6803을 초대해서
> njh6803으로 작업 진행"

쓰기 탐침: 색인 `project/design-system.json`에 `lastChange` 하나만 더해 올렸다. 판 6(`1792115455-aa71`)이 되었고 다시 받은
파일의 sha256이 올린 것과 같으며, njh4803의 브라우저에서 그대로 열렸다. ADR 0025의 이력 초안을 쓰고, 이 결정을 참조하는
살아 있는 문서를 고쳤다. `web-design.md`의 머리 문장을 고쳐 카나리아를 돌렸다(통과 4, 실험군 3·대조군 1).

## 셀프 리뷰

`/code-review`(기점 `df705c17`, 파일 19, 커밋 0, 미추적 0). 문서·프로브만이라 표준 축은 sonnet이었다.

명세 축은 Critical 1·Major 2·Minor 여럿·Nit 넷, 표준 축은 Major 5·Minor 여럿이었고 겹친 것이 많다. 판정과 반영:

- 고쳤다(두 축의 첫째): `web-design.md` 머리를 고친 뒤 `hash_match.mjs`가 작업 트리를 읽어 종료 코드 1이었다(다시 돌려
  봤다). 기록의 줄마다 대조한 커밋(`df705c17`)을 적고 저장소 쪽을 그 커밋에서 꺼내게 했다. 이제 작업 트리와 무관하게
  측정 15, 기대와 다름 0이다. 아티팩트의 `web-design.md`는 옛 판이라 병합 뒤 이 세션이 올린다.
- 고쳤다: 화면 프롬프트 하는 법 1이 2026-10-14 뒤로 `packages/ui`가 바뀌지 않았으면 올릴 것이 없다고 갈음하던 것. 기점이 날짜였고 입력이
  `packages/ui`만이 아니었다. 화면 디자인 절에 "색인 `via`의 커밋 뒤로 빌드의 입력(`web/packages/ui`, NOTES를 뺀
  `.design-sync/`, `web-design.md`)이 바뀌었는지"를 `git diff --stat`으로 가르는 규칙을 두고 프롬프트는 그것을 가리킨다.
  `hash_match.mjs`는 `--record`로 기록 파일을 받아 다른 기능이 이 기능의 기록을 덮지 않는다.
- 고쳤다: `via`에 커밋을 적은 적이 없고 동기화한 커밋의 원천이 둘이었다. `via`를 `agent-os main@<짧은 SHA>`로 정하고
  올리기는 그 파일을 담은 PR이 병합된 뒤로 정했다(squash로 사라질 브랜치 커밋을 남기지 않는다). README 표의 동기화한
  커밋은 그 `via`의 커밋이다.
- 고쳤다: 올리기 절차의 빈칸. 호출의 모양(`url`, `root`, 절대 경로 `file_path`, `files`), 빌드에서 빠진 경로의 지우기와
  지우지 않을 파일, `lastChange` 넷을 모두 새로 적기, 거절됐을 때의 다시 읽기, 올릴 경로를 아티팩트의 파일 목록과 맞대기.
  업로드 없이 빌드만 하는 driver 명령과 올리지 않을 빌드 부산물은 이 세션이 알지 못해 다음 동기화가 NOTES에 적는다고
  `plan.md`의 design-artifacts 행에 넘겼다.
- 고쳤다: ADR 0026의 포인터 둘(요약 문단 끝, 디자인 문서 문단의 `guidelinesGlob`). 단독 원본 프로젝트를 언제 내려놓을지
  (지우지 않고 2026-12-14에 함께 닫히게 둔다). 재지 못한 것을 받는 쪽에(디자인 시스템을 Design 아티팩트에 붙일 수
  있는지는 admin-style 행과 design-artifacts 행, 다시 옮기기가 실제로 건너뛰는지는 ADR). "첫 쓰기로 갈라졌다"는
  "공식 안내대로라면"으로 낮췄다.
- 고쳤다(근거와 인용): `ds-bundle/`이 바이트까지 같았다고 적은 것은 잰 것이 저장소 원본이라 그대로 적었다. "주인은 옮길 수 없다"는
  문서에 없다는 것을 단정으로 올린 문장이라 네 곳에서 "방법이 안내에 없다"로 낮췄고, `find_sentences`로는 없음을 재지
  못한다고 README에 적었다. "프로젝트는 옮겨지지 않는다"는 원문 구절 "Your projects stay in the standalone version"을
  더해 대 봤다(구절 열하나). "워크스페이스에 멤버를 못 둔다"는 요금제 행과 설정 화면(손으로 봤다)으로 나눠 적었다.
  프로브 README가 만든 인용 둘과 근거 자리의 엇갈림, ADR이 줄여 옮긴 거부 안의 이름, 킥오프의 초대 범위(Pro·Max·Team·
  Enterprise, 베타), NOTES 머리의 현재형, `thumbnail.html`이 없다는 것의 출처(파일 목록을 손으로 봤다), 화면 디자인 절의
  섞인 시제, "같은 판"이 파일 단위라는 것, ADR의 "함께 고치는 것"이 실제 변경보다 적던 것.
- 고쳤다(프로브): `pricing_rows.mjs`가 읽지 못한 칸(`?`)을 측정으로 세던 것, `hash_match.mjs`가 `expect`의 오타를
  differ로 읽던 것. 둘 다 측정 아님으로 세고 1로 끝난다.
- 뺐다: 하는 법 3에 더한 입력 대조 단계(요구에 없었고 `kickoff/prompting.md`에 같은 요령이 있다), 하는 법 머리가 잘못
  가리킨 킥오프의 "넷" 문단 인용.
- 남겼다: 표준 축의 Duplicated Code(아티팩트 주소와 계정 문장이 여러 문서에 있다). `plan.md`의 행이 넘긴 것을 행마다
  적는 규약(`docs/agents/issue-tracker.md` 전체 계획 절)이라 판단 항목으로 둔다. `web-design.md`의 "Claude Design의
  컴포넌트 카드"는 Claude Design이 Claude 안에서 이어지는 제품 이름이라("Claude Design now lives in Claude") 잔존으로
  보지 않았다. 화면 프롬프트 본문의 "내보내 쓴다"는 그리는 쪽에 주는 글이라 그대로 둔다.
- 다시 돌린 것: `hash_match.mjs --saved`(측정 15, 기대와 다름 0, 종료 0), `pricing_rows.mjs`(읽지 못한 칸 0, 종료 0),
  새 구절 대조(종료 0). 검증 명령 다섯은 커밋의 pre-commit으로 갈음한다.

## ADR 승인

셀프 리뷰를 반영한 뒤 ADR 0025 이력 초안의 요지(결정, 거부한 안 다섯, 넘긴 것)를 보이고 물었다.

> 사용자: "ADR 0025의 2026-10-16 이력을 승인한다. 커밋하고 PR과 병합까지 진행해."

## 다음

(병합 뒤 마무리한다)
