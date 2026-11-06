# 2026-11-06 (11) 문서 검색 서버의 저장소 이름 rag-engine(제안서 둘째 판 반영)

## 사용자 프롬프트

> 사용자: @"C:\Users\User\Downloads\agent-os-rag-baseline-plan (1).md"
> 첨부한 agent-os-rag-baseline-plan.md는 다음 기능 계획의 제안서다. 그대로 붙여 넣지 말고 저장소 절차대로 반영해 줘.
>
> 1. 기준 커밋 403c9e9 이후 main이 바뀌었으면 1절의 사실부터 다시 확인한다.
> 2. 6절의 PRD 개정안을 보여 주고 승인을 받는다.
> 3. 7~9절의 ADR 0044, 0045, 0046 초안을 셀프 리뷰한 뒤 하나씩 승인을 받는다. 번호는 저장소의 다음 번호에 맞춘다.
> 4. 승인이 끝나면 3절과 4절대로 .scratch/plan.md를 고친다. Blocked by에 rag-engine:<slug>로 적힌 것은 다른 저장소의 행이므로 이 저장소에 만들지 않는다.
> 5. 10~13절은 각 행의 설계 인터뷰 입력으로 쓴다. 저장소 어디에 둘지는 문서 위치 규약대로 정한다.
>
> 계획과 저장소의 현재 상태가 맞지 않는 곳이 있으면 고치기 전에 먼저 알려 줘.

(제안서는 저장소 밖의 파일이라 커밋하지 않는다. 일지 2026-11-06-02가 반영한 앞 판은 `Downloads/agent-os-rag-baseline-plan.md`(00:09)이고, 이번에 받은 것은 같은 폴더의 `agent-os-rag-baseline-plan (1).md`(14:47)다. 아래에서 앞 판, 둘째 판으로 부른다.)

## 대조(고치기 전)

- 큰 어긋남. 앞 판은 PR #473으로 이미 반영되어 병합되었다(일지 2026-11-06-02). PRD 개정은 승인받았고, 제안서의 ADR 셋은 0046·0047·0048로 accepted이며(0044는 approval-rules, 0045는 retro-queue-per-item이 가졌다), plan.md에 새 행이 들어갔고, 제안서 11~13절은 그 일지의 "설계 인터뷰 입력" 절에 있다.
- 두 판을 `git diff --no-index --word-diff`로 견줬다. PRD 개정안(6절), 위젯 ADR 초안(8절), 10~13절은 같다. 달라진 것은 둘이다. (1) 문서 검색 서버 저장소의 이름이 `rag-engine`으로 정해지고 그 행이 다시 나뉘었다(rag-mcp → core, rag-admin → source-sync와 admin, rag-ops → release-image와 backup-upgrade와 diag-bundle, 1.0에 db-source와 change-log). (2) 5절 접점 표에 "구조화 데이터"(Text-to-SQL은 기준선과 1.0 범위 밖) 줄이 더해졌다. 행 이름은 같은 폴더의 `rag-engine-plan.md` 6절 "행" 표와 맞는다(앞 세션이 읽은 판에서는 165~177줄이었고, 15:04 판에서는 "## 6. 행"이 179줄, 표 머리가 183줄, 행 열둘이 185~196줄이다. PR 직전 버그 축이 `grep -n "^## "`로, 이어받은 세션이 같은 명령과 `sed -n '183,196p'`로 봤다).
- 둘째 판도 앞 판의 전제를 들고 있어 그대로 따르지 않는 곳: approval-rules를 슬라이스 10·pilot-release 뒤로 미루는 것(어제 "지금 자리에서 계속"을 골랐고 지금 `in-progress`, 티켓 01 #475·02 #476 병합), ADR 번호 0044~0046, install-package(→ deploy-package), "주소 모양 MCP 서버"(→ 원격 MCP 서버), doc-qa-agent의 Blocked by(approval-rules가 든다), pilot-release 알려진 한계의 "운영자 승인 규칙 없음"(빠졌다).
- 1절의 사실. `403c9e9` 뒤로 origin/main은 `e9bbfcc`이고, 일지 2026-11-06-02가 대 본 `83a66cd` 뒤의 코드 변경은 approval-rules 01·02뿐이다(`git diff --stat 83a66cd..origin/main -- src plugins uv.lock pyproject.toml openapi.json`). 걸리는 사실을 다시 봤다. `ModelProvider`는 `ANTHROPIC` 하나, `run.py` 1009줄의 `self._tools.connect`, `RunFinished`는 `output` 하나, `uv.lock`의 mcp 2.3.0, Dockerfile 없음. `C:\project`에 rag-engine 저장소는 없다.
- `rag-server:`가 든 살아 있는 문서: `.scratch/plan.md` 32·35·38·43·59줄(33·34줄은 접두사 없는 옛 행 이름 `rag-ops`만 든다. 처음에는 일곱 줄 모두 `rag-server:`가 든다고 적었고, 이어받은 세션의 셀프 리뷰 두 축이 `git grep`으로 다시 세어 고쳤다), ADR 0046 29줄, ADR 0048 19줄, `CONTEXT.md` 177줄(`git grep`, 일지 제외). ADR 0046 47줄은 첫 판의 행 이름 다섯(bootstrap, rag-mcp, rag-admin, search-eval, rag-ops)을 들고 있는데 `rag-server`로만 grep해 놓쳤고, 같은 셀프 리뷰가 잡았다(아래 "셀프 리뷰"). `tests/test_plan_status.py`는 Blocked by 칸을 보지 않는다(21줄 독스트링).

## 사용자가 정한 것

> 사용자: (이번 판에서 새로 바뀐 것(저장소 이름 rag-engine과 그 행 이름)만 저장소에 반영할까요?) "이름 바뀐 곳만 고친다 (Recommended)" — 설명: plan.md에서 Blocked by 셋(answer-eval, deploy-package, stale-warning), 내용 칸 셋(ops-backup-upgrade, diag-bundle, principal-propagation), 프론티어 문단의 접두사를 rag-engine:으로 바꿉니다. ADR 0048에는 저장소 이름을 정한 이력 하나를 더해 보여 드리고 승인을 받습니다. ADR 0046 29줄과 용어집 177줄의 rag-server: 표기도 함께 고칩니다. approval-rules의 자리와 deploy-package라는 이름처럼 어제 정한 것은 그대로 둡니다.

> 사용자: (새로 들어온 '구조화 데이터(매출·재고 같은 숫자는 Text-to-SQL 도구로 따로 다루고 기준선과 1.0 범위 밖)' 줄을 어디에 둘까요?) "PRD의 미룬 것에 더한다 (Recommended)" — 설명: PRD 24줄의 미룬 것 목록에 '구조화 데이터 질의(Text-to-SQL)'를 더합니다. PRD 개정이므로 더할 문장을 먼저 보여 드리고 승인을 받습니다. 나중에 'DB의 숫자도 답하게 하자'는 요청이 나오면, 그 기능이 범위 밖이라는 근거가 PRD에 남아 있습니다.

## PRD 개정(승인)

화면에 두 곳을 diff로 보였다. 상태 줄의 "2026-11-06 개정 사용자 승인. 개정의 근거는 ADR 0042와 ADR 0046"을 "2026-11-06 개정 두 번 사용자 승인. 개정의 근거는 ADR 0042와 ADR 0046, 일지 2026-11-06-11"로, 미룬 것 목록 끝에 "구조화 데이터 질의(Text-to-SQL)"를 더하고 "돌아오면 …" 뒤에 "구조화 데이터 질의는 매출이나 재고처럼 숫자가 바뀌고 합계를 내야 하는 데이터를 묻는 것이고, 문서 검색 서버는 그런 데이터를 색인하지 않는다."를 넣는다. 제안서의 "SQL 커넥터는 데이터베이스에 든 글만 가져온다"는 그 저장소가 정할 일이라 넣지 않았다고 함께 적었다.

> 사용자: (위 PRD 개정안(상태 줄과 미룬 것의 구조화 데이터 질의)을 이대로 승인하시겠습니까?) "이대로 승인 (Recommended)" — 설명: 적힌 문장 그대로 docs/PRD.md의 3줄과 24줄을 고칩니다. 그다음에는 ADR 0048에 더할 저장소 이름 이력을 써서 셀프 리뷰를 한 뒤 보여 드립니다.

반영: `docs/PRD.md` 3줄과 24줄을 보인 문장 그대로 고쳤다. 고르지 않은 선택지(라벨만): "설명 문장은 빼고 목록에만 더한다".

## 용어(domain-modeling)

`.claude/rules/adr.md`대로 이력을 쓰기 전에 `domain-modeling`을 불렀다. `rag-engine`은 개념이 아니라 문서 검색 서버를 담은 저장소의 이름이다. 그래서 글에서 서버를 이를 때는 지금처럼 "문서 검색 서버"를 쓰고, `rag-engine`은 그 저장소를 이를 때와 `plan.md` 행의 접두사에만 쓴다. `CONTEXT.md` 문서 검색 서버 항목의 _Avoid_를 그렇게 고쳤다. 첫 질문의 설명은 "ADR 0046 29줄과 용어집 177줄의 rag-server: 표기도 함께 고칩니다"였지만, `.claude/rules/adr.md`가 본문의 다른 글자를 고치지 않게 하므로 ADR 0046과 0048의 본문은 글자를 바꾸지 않고 포인터를 단다.

## ADR 초안(셀프 리뷰 전)

ADR 0048에 `## 이력`과 `### 2026-11-06 문서 검색 서버의 저장소 이름을 rag-engine으로 정한다`를 더하고, 19줄 끝과 ADR 0046 29줄 끝에 포인터를 달았다. `CONTEXT.md` 문서 검색 서버의 _Avoid_를 위 용어 절대로 고쳤다. `uv run python tools/check_adr_pointers.py`가 0으로 끝났다(손으로 쳤다). 색인(`docs/adr/README.md`)의 0046·0048 행은 제목·상태·날짜만 들어 바꾸지 않았다.

## 인계 전 상태(셀프 리뷰 직전)

세션 컨텍스트가 인계 문턱을 넘어 `셀프 리뷰 직전` 경계에서 넘긴다. 이 세션의 제목은 `docs/rag-engine-name`이었다. 커밋하지 않은 변경이 워크트리 `C:/project/agent/.claude/worktrees/rag-engine-name`에 있다(PRD, ADR 0046, ADR 0048, `CONTEXT.md`, 이 일지).

남은 일(사용자 요청 3~4의 나머지):

1. `/code-review` 셀프 리뷰. 기준점 origin/main(이 세션에서는 `e9bbfcc`). 명세 축의 원천은 이 일지의 사용자 프롬프트, "사용자가 정한 것", "PRD 개정(승인)", 제안서 둘째 판 2~5절이다. plan.md는 아직 고치지 않았다.
2. 반영한 뒤 ADR 0048 이력과 두 포인터를 보이고 승인받는다.
3. 승인 뒤 `.scratch/plan.md`를 고친다. Blocked by 셋: answer-eval의 `rag-server:rag-mcp` → `rag-engine:core`, deploy-package의 `rag-server:rag-ops` → `rag-engine:release-image, rag-engine:backup-upgrade, rag-engine:diag-bundle`, stale-warning의 `rag-server:doc-freshness` → `rag-engine:doc-freshness`. 내용 칸 셋: ops-backup-upgrade(33줄)의 "그 저장소의 rag-ops가"는 backup-upgrade로, diag-bundle(34줄)의 "rag-ops가"는 그 저장소의 diag-bundle로, principal-propagation(38줄)의 `rag-server:<slug>`는 `rag-engine:<slug>`로 바꾼다(제안서 둘째 판 5절이 그 저장소의 문서 권한 행을 doc-permission으로 든다. Blocked by에 넣을지는 그 행의 설계 인터뷰 몫이고 제안서 4절도 바꾸지 않았다). 프론티어 문단(59줄)의 `rag-server:<slug>` 문장과, 끝에 저장소 이름이 정해졌다는 한 문장. approval-rules의 자리, deploy-package라는 이름, doc-qa-agent의 Blocked by는 그대로 둔다. 다른 저장소의 행은 이 저장소에 만들지 않는다(사용자 요청 4).
4. 둘째 셀프 리뷰(plan.md), 검증 명령, 커밋(`docs/rag-engine-name`, 면제 PR), PR, 병합, 이 일지의 "다음", retro.

주의: 열린 PR #477(approval-rules 03)이 있다. 이 세션의 `tools/sibling_overlap.py`는 함께 고친 파일이 없다고 냈지만, 커밋 전에 다시 친다.

## 인계 지시문

```
다음 작업: 기능 rag-engine-name. 제안서 둘째 판이 정한 문서 검색 서버 저장소 이름(rag-engine)을 저장소 절차대로 반영한다(셀프 리뷰, ADR 0048 이력 승인, plan.md, PR)
다음 단계: 설계 인터뷰
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: docs/journal/2026-11-06-11-rag-engine-name.md의 "사용자 프롬프트" 절의 요청을 "인계 전 상태"의 남은 일 1부터 잇는다. 제안서는 C:\Users\User\Downloads\agent-os-rag-baseline-plan (1).md
브랜치: docs/rag-engine-name
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-06-11-rag-engine-name.md 전체, 제안서 둘째 판 2~5절
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. PRD 개정은 승인받아 반영했고 ADR 0048 이력은 승인 전 초안이다. docs/journal/2026-11-06-11-rag-engine-name.md
확인할 선행 조건: rag-engine 저장소가 원격(GitHub)에 있는지 보지 않았다. ADR 0048 이력 초안은 이 PC의 C:\project만 보고 "아직 없다"고 적었다
이번 요청 범위: PR과 병합까지(ADR 0048 이력은 사용자 승인)
```

제목을 `docs/rag-engine-name (인계함)`으로 바꿨다. 이 세션이 띄운 백그라운드 작업은 없다. `git worktree unlock C:/project/agent/.claude/worktrees/rag-engine-name`이 출력 없이 끝났다.

open-session을 부른다 2026-11-06T06:04:09Z

## 이어받은 세션(셀프 리뷰부터)

인계 지시문대로 새 세션이 제목을 `docs/rag-engine-name`으로 바꾸고 워크트리 `C:/project/agent/.claude/worktrees/rag-engine-name`에 들어갔다(`git worktree list`에서 그 브랜치가 체크아웃된 자리를 손으로 찾았다).

- 제안서 파일. 지시문의 `agent-os-rag-baseline-plan (1).md`는 `Downloads`에 없고, 같은 폴더에 `agent-os-rag-baseline-plan.md`(15:04, 68,116바이트)와 `rag-engine-plan.md`(15:04)만 있다(`ls -la --time-style=long-iso`로 봤다). 앞의 것이 둘째 판이다. 2절 "저장소 둘" 표에 `rag-engine(RAG 서버)` 행이 있고 5절 접점 표 끝에 "구조화 데이터" 줄이 있다(`sed -n '39,197p'`로 읽었다). 첫 판(00:09)은 폴더에 남아 있지 않아 "달라진 것은 둘이다"는 다시 견주지 못했다.
- origin/main. 이 세션이 들어온 뒤 origin/main은 PR #477(approval-rules 03, `d0f5a195`)만큼 앞섰고 plan.md는 그 변경에 들지 않았다(`git diff --stat e9bbfcc9..origin/main`로 봤다). 이 브랜치에 커밋이 없어 `git merge origin/main --no-edit`은 fast-forward로 끝났고 커밋하지 않은 변경은 그대로다(`git status --short`로 봤다).
- 선행 조건. GitHub의 njh6803 계정에 `rag-engine` 저장소는 없다. `gh repo view njh6803/rag-engine --json name`이 "Could not resolve to a Repository"로 종료 1이고, `gh repo list njh6803 --limit 100`의 목록에도 없다(2026-11-06에 손으로 봤다). ADR 0048 이력의 "원격은 보지 않았다"를 이 두 명령으로 봤다고 고쳤다.

## 셀프 리뷰(기준 d0f5a195)

범위: base `d0f5a1951852ab878fffc3e23d62514c4f977ed5`(origin/main = HEAD), 바뀐 파일 넷(`CONTEXT.md`, `docs/PRD.md`, ADR 0046, ADR 0048), 커밋 0, 미추적 1(이 일지). 명세는 이 일지의 "사용자 프롬프트"·"사용자가 정한 것"·"PRD 개정(승인)"·"용어"와 제안서 둘째 판 2~5절 발췌, 인계 지시문의 범위를 요구로, plan.md를 아직 고치지 않은 것과 앞 판에서 정한 것을 리뷰어 참고로 넘겼다. 표준 축은 sonnet·high, 명세 축은 본 세션 모델(ADR 0033).

### Standards

1. Major — ADR 0046 47줄. 본문이 첫 판의 행 이름 다섯(bootstrap, rag-mcp, rag-admin, search-eval, rag-ops)을 드는데 둘째 판이 그 행을 일곱으로 다시 나눴고, 포인터가 없다(`.claude/rules/adr.md`의 "이력이 본문의 문장을 거짓으로 만들거나 … 같은 편집에서 … 포인터를 단다"). ADR 0048 이력도 옛 이름에서 새 이름으로의 대응을 적지 않았다.
2. Minor(판단) — PRD 3줄 "2026-11-06 개정 두 번 사용자 승인". 같은 날 PRD를 고친 커밋은 #473과 이번 것 둘이라 개정 두 번은 맞지만, 일지 2026-11-06-02가 승인을 두 번 적어 "두 번"이 개정 수인지 승인 수인지 갈리고 앞 항목의 모양("날짜 개정 사용자 승인")에서 벗어난다.
3. Minor(판단) — PRD 24줄 "문서 검색 서버는 그런 데이터를 색인하지 않는다". 저장소 안에 반례는 없지만(`git grep`), `rag-engine-plan.md`가 1.0에 db-source(SQL 질의 결과를 문서로 색인)를 두어, 바로 앞의 정의("숫자가 바뀌고 합계를 내야 하는 데이터")에 기대 참이다.
4. Minor(과도기) — `CONTEXT.md` 177줄과 ADR 이력이 plan.md 접두사를 `rag-engine:`으로 현재형으로 적는데 plan.md는 아직 `rag-server:`다. plan.md 수정이 같은 PR에 들어가야 한다.
5. Nit — `CONTEXT.md` 177줄 _Avoid_의 괄호가 길다(267줄에 비슷한 선례).
6. Nit — 이 일지 "대조" 절의 줄 번호 32·33·34·…가 부정확하다. `rag-server`가 든 줄은 32·35·38·43·59이고 33·34는 맨 `rag-ops`다.

Smell: Shotgun Surgery 가능성(이름 하나가 CONTEXT, ADR 둘, plan.md에 흩어짐). 포인터 규약이 의도한 구조. 그 밖은 해당 없음. 주장 검증: 저장소 없음(맞음, `gh repo view`·`gh repo list`·`ls`), 행 이름 다섯의 대응(맞음), 포인터 모양(맞음, `check_adr_pointers.py` 종료 0), PRD 개정 두 번(일부 어긋남, 2), PRD 24줄 보편 주장(판단, 3), 일지 줄 번호(어긋남, 6), `test_plan_status.py` 21줄(맞음), 일지 1절의 코드 사실 넷(맞음), 두 판 견줌(대조 불가. 첫 판이 없다), 열린 PR #477(지금은 병합됨. 기록이라 어긋남 아님).

### Spec

(a) 1. Major — ADR 0046 47줄에 포인터가 없다(R2 "이름 바뀐 곳만 고친다", R5 "본문은 글자를 바꾸지 않고 포인터를 단다"). 앞 세션이 `rag-server`만 grep해 옛 행 이름(`rag-mcp`·`rag-ops`)으로는 찾지 않았다. (b) 범위 넘침 없음. (c) 2. Minor — ADR 0048 이력 "agent-os의 세 행이 기다리는 행도 바뀌었다". stale-warning이 기다리는 행은 doc-freshness 그대로이고 접두사만 바뀌었다. 재분할로 바뀐 것은 answer-eval·deploy-package 둘이다. 3. Minor — 이 일지 "대조" 절 줄 번호 어긋남(표준 6과 같다). 남은 일 3의 고칠 목록은 plan.md의 실제 글과 맞고 빠진 줄도 없다(plan.md의 `rag-` 전수가 그 일곱 줄). 4. Nit — 인계 지시문의 제안서 경로가 지금 없다(기록). 앞 판이 사라져 "달라진 것은 둘이다"는 대조 불가. 주장 검증: 행 대응 다섯(맞음, 제안서와 글자 그대로), "이 저장소에는 만들지 않는다"(맞음), "결정은 바뀌지 않았다"(맞음), 저장소 없음(맞음, 같은 명령), PRD 3·24줄(승인 문장과 글자 그대로), CONTEXT 177(맞음), 포인터 둘과 ADR README 행(맞음), 일지 1절 재확인(모두 맞음).

요약: 표준 6(Major 1), 명세 4(Major 1). 두 축의 Major는 같은 자리다.

고친 것: (1) ADR 0046 47줄의 행 이름 문장 뒤에 `(바뀜: ADR 0048 이력 2026-11-06 "문서 검색 서버의 저장소 이름을 rag-engine으로 정한다")`를 달았다. (2) ADR 0048 이력에 첫 판의 행 다섯이 새 행 일곱으로 어떻게 대응되는지(rag-mcp→core, rag-admin→source-sync·admin, rag-ops→release-image·backup-upgrade·diag-bundle, bootstrap은 빠짐. 새 저장소는 킥오프 런북으로 시작해 뼈대 행을 두지 않는다. 1.0 열에 db-source와 change-log)를 적고, "세 행"을 "두 행"으로 고쳐 answer-eval과 deploy-package만 들고, stale-warning은 접두사만 바뀐 것으로 적었다. 대응의 원천은 이 일지 "대조" 절(앞 세션의 word-diff)과 제안서 둘째 판 9절 293줄("RAG 서버(rag-engine)의 행(core, source-sync, admin, search-eval, release-image, backup-upgrade, diag-bundle)은 그 저장소의 계획에 있다. 그 저장소는 agent-os의 킥오프 런북(`KICKOFF.md`)으로 시작한다"), `rag-engine-plan.md` 9줄("저장소의 뼈대를 따로 만드는 행은 두지 않고")이다(둘 다 `grep -n`과 `sed -n`으로 읽었다). (3) 이 일지 "대조" 절의 줄 번호를 고쳤다. PR 직전 리뷰에 밀 주장으로 넘길 새 문장: "rag-mcp는 core로, rag-admin은 source-sync와 admin으로, rag-ops는 release-image와 backup-upgrade와 diag-bundle로 나뉘었고, bootstrap은 빠졌다", "새 저장소는 agent-os의 킥오프 런북(`KICKOFF.md`)으로 시작하므로 뼈대를 만드는 행을 따로 두지 않는다", "1.0 열에는 db-source와 change-log가 더해졌다", "stale-warning이 기다리는 `rag-engine:doc-freshness`는 접두사만 바뀌었다".

남긴 것: 표준 2·3은 사용자가 "이대로 승인"한 PRD 문장이라 바꾸지 않는다(바꾸면 재승인이다). 3은 정의에 기대 참이고 제안서의 한정 문장을 넣지 않기로 한 것도 승인에 들었다. 표준 4는 남은 일 3(승인 뒤 plan.md)으로 같은 PR에 든다. 표준 5는 267줄의 선례가 있어 둔다. 명세 4는 기록이라 두고, 위 "이어받은 세션"에 지금의 파일 상태를 적었다. Smell은 포인터 규약이 의도한 구조다.

다시 돌린 명령: `uv run python tools/check_adr_pointers.py` 종료 0(고친 뒤 손으로 쳤다). 나머지 다섯은 커밋의 pre-commit으로 갈음한다(결과는 커밋 뒤에 적는다).

## ADR 0048 이력 승인

화면에 이력 한 절의 전문과 포인터 셋(ADR 0046 29·47줄, ADR 0048 19줄)을 보였다. 47줄의 포인터는 셀프 리뷰가 더한 것이라고 함께 적었다.

> 사용자: (위 ADR 0048 이력 한 절과 포인터 셋을 이대로 승인하시겠습니까?) "이대로 승인 (Recommended)" — 설명: ADR 0048 끝에 위 이력이 그대로 들어가고, ADR 0046 29·47줄과 ADR 0048 19줄에 포인터 셋이 붙습니다(지금 디스코의 줄 번호를 grep으로 대 봤습니다). 그다음 plan.md의 일곱 줄(32·35·43줄의 Blocked by, 33·34줄의 rag-ops, 38줄의 principal-propagation, 59줄의 프론티어 문단)을 rag-engine 이름으로 고치고 둘째 셀프 리뷰를 거쳐 PR을 열어 병합합니다.

("디스코"는 "디스크"의 오타다. 화면에 보인 글자 그대로 옮겼다.) 고르지 않은 선택지(라벨만): "문장을 고쳐서 다시 본다". 승인으로 ADR 0048 이력은 초안에서 확정이 됐고, 본문 글자는 바꾸지 않았다.

## plan.md 반영(남은 일 3)

"인계 전 상태"의 남은 일 3 목록 그대로 일곱 줄을 고쳤다. 32줄 answer-eval의 Blocked by `rag-server:rag-mcp` → `rag-engine:core`, 33줄 "그 저장소의 rag-ops가" → "그 저장소의 backup-upgrade가", 34줄 "rag-ops가" → "그 저장소의 diag-bundle이", 35줄 deploy-package의 Blocked by `rag-server:rag-ops` → `rag-engine:release-image, rag-engine:backup-upgrade, rag-engine:diag-bundle`, 38줄 principal-propagation의 `rag-server:<slug>` → `rag-engine:<slug>`, 43줄 stale-warning의 Blocked by `rag-server:doc-freshness` → `rag-engine:doc-freshness`, 59줄 프론티어 문단의 "`rag-server:<slug>` 로 가리키며" → "`rag-engine:<slug>` 로 가리키며"와 끝에 저장소 이름이 정해졌다는 문장 하나. 행을 더하거나 지우지 않았다. 고친 뒤 `git grep -n "rag-server\|rag-ops\|rag-mcp\|rag-admin" -- ':!docs/journal'`은 다섯 자리를 냈고 모두 의도한 자리다(포인터가 달린 ADR 본문 셋, 옛 이름에서 새 이름으로의 대응을 적은 ADR 0048 이력과 59줄). 린트 둘(`uv run ruff check .`, `uv run ruff format --check .`)은 손으로 쳐서 둘 다 0이었다(`.py`가 없는 커밋이라 pre-commit에서 Skipped가 된다).

## 둘째 셀프 리뷰(plan.md, 기준 d0f5a195)

범위는 첫 회차 뒤에 바뀐 것: plan.md 일곱 줄, 첫 회차 뒤 고친 ADR 문장, 일지의 새 절. 첫 회차에서 판정된 지적은 다시 내지 않게 했다.

### Standards

Critical·Major·Minor 없음. Nit 둘(판단). (1) plan.md 33·34줄의 "그 저장소의 backup-upgrade가"·"그 저장소의 diag-bundle이"에 접두사가 없고, 35줄 Blocked by는 `diag-bundle`과 `rag-engine:diag-bundle`을 함께 든다. 34줄은 diag-bundle 행 자체라 "그 저장소의"가 구분을 맡고 뜻은 통한다. (2) ADR 0048 48줄 이력 문단이 길다. 같은 ADR의 다른 이력과 모양이 같다. 도구: `check_md_tables.py`·`check_adr_pointers.py` 출력 없음, `pytest -q tests/test_plan_status.py` 12 passed. 주장 검증: 잔존 모두 의도된 자리(맞음. 보고는 "네 곳"이라 썼지만 든 자리는 plan.md 59줄, ADR 0046 29·47줄, ADR 0048 19·48줄의 다섯이다. 둘째 명세 축이 그 어긋남을 잡았다), 프론티어 불변(맞음, 32·35·43줄의 막힘이 풀리거나 더해지지 않았다), 59줄 새 문장의 행 이름(32·35줄과 글자 그대로), ADR 0048 이력의 행 다섯(ADR 0046 47줄과 글자 그대로)과 행 일곱(`rag-engine-plan.md` 6절 표와 같다), `KICKOFF.md`(루트에 있다), 1.0 열의 db-source·change-log(일부 대조 불가. 첫 판이 없어 "더해졌다"는 앞 세션의 word-diff에 기댄다), 일지 "이어받은 세션"의 명령 결과(읽기 명령으로 다시 쳐서 맞음), 일지가 인용한 adr.md 문장(원문 12줄의 낱말 순서와 맞음), 포인터 제목(`###` 줄과 글자 그대로).

남긴 것: Nit (1)은 용어 결정(`rag-engine`은 저장소를 이를 때와 행의 접두사에만 쓴다. "용어" 절)과 남은 일 3의 목록 그대로라 둔다. 내용 칸에서는 "그 저장소"가 문서 검색 서버의 저장소를 가리킨다. Nit (2)는 선례와 같은 모양이라 둔다.

### Spec

(a) 없음. 일곱 줄이 모두 고쳐졌고 approval-rules의 자리와 deploy-package라는 이름은 그대로다(diff가 그 일곱 줄 밖을 건드리지 않았다). (b) Nit(판단) — plan.md 59줄. 남은 일 3은 "한 문장"인데 세 문장이 더해졌다(이름 결정·접두사·행 이름, "그 저장소의 행은 이 표에 만들지 않는다", "이 변경은 프론티어를 바꾸지 않는다"). 셋 다 참이고 승인 이력과 맞다. (c) Nit 둘 — 이 일지 "plan.md 반영" 절의 "정해졋다" 오타, 같은 절의 "다섯 자리"와 Standards 전사의 "네 곳"이 어긋남(잔존은 다섯이다. `rag-server` 셋인 plan.md 59줄·ADR 0046 29줄·ADR 0048 19줄과, 옛 행 이름 둘인 ADR 0046 47줄·ADR 0048 48줄). 주장 검증: 32·35·43줄 Blocked by(P2·P3·P4와 쉼표·공백·순서까지 글자 그대로), 33·34줄(P2와 맞음. 34줄의 "그 저장소의"는 앞의 "문서 검색 서버 쪽 진단"이 선행사), 38줄(문장만 바뀌고 Blocked by는 mcp-trust 그대로), 59줄 새 문장(바뀐 세 행과 남은 막힘이 모두 todo라 풀린 행도 새로 막힌 행도 없다), 다른 저장소의 행을 만들지 않음(표 행 52→52, 줄 82→82), ADR 0048 48줄의 행 일곱과 1.0 열(제안서 2절과 `rag-engine-plan.md` 표와 같다. 옛 다섯에서 새 일곱으로의 대응과 "더해졌다"는 첫 판이 없어 대조 불가), 일지의 사실들(모두 맞음), 포인터 모양(adr.md 13줄 형식과 같다). 다시 친 도구: `check_adr_pointers.py` 0, `pytest tests/test_plan_status.py` 12 passed, `check_md_tables.py` 출력 없음.

요약: 표준 Nit 2, 명세 Nit 3. Critical·Major·Minor 없음.

고친 것: 이 일지의 오타와 수(명세 Nit 둘). 남긴 것: 59줄의 세 문장은 셋 다 참이라 둔다. 다시 돌린 명령: 일지만 고쳐 다시 돌릴 검사가 없고, 커밋의 pre-commit으로 갈음한다.

## 검증

plan.md를 고친 뒤 `uv run python tools/run_checks.py`를 워크트리에서 백그라운드로 돌렸다. 열 단계(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest 460.5s, web-verify 697.3s)가 모두 Passed이고 Skipped는 없었으며 종료 0이었다(로그를 `tail`로 읽었다). 린트 둘은 위 "plan.md 반영" 절대로 손으로 쳐서 0이었다. `-m llm`·`-m llm_widget`·e2e·사진 비교는 돌리지 않았다. 문서만 바뀐 변경이라 그 테스트가 지나는 코드에 닿지 않는다.

## PR 직전 리뷰(CodeRabbit CLI)

`coderabbit-review` 서브에이전트를 커밋과 나란히 돌렸다. CLI 0.7.5, 로그인 njh6803이고, `coderabbit auth status`에 `Seat         : not assigned`와 `Plan: Free`가 보여(2026-11-03에는 그 줄이 없었다) 정의의 1단계대로 리뷰를 돌리지 않고 끝냈다. 한도는 쓰지 않았다. 이 세션이 앞서 친 같은 명령은 `head -12`로 잘라 `Review access`까지만 봤고 그 아래의 `Seat` 줄을 보지 못했다. CLI 축이 비었으므로 대체 둘(`/security-review`는 커밋 뒤 origin/main을 합친 상태에서, `bug-perf-review` 서브에이전트)을 PR 전에 돌린다.

## 커밋

첫 커밋(`git commit -F`)은 pre-commit의 검사를 모두 지나고(열 단계와 인용 대조·헌법 판 검사. 헌법 판은 `(no files to check)Skipped`) commit-msg 훅에서 "제목 79자 > 72자"로 막혔다(로그를 `tail`로 읽었다). 제목을 67자로 줄였다. 인용 대조 경고 10건은 하나씩 봤다. 둘(42줄의 선택지 설명 인용에서 "과 용어집 177줄의"가 빠진 것, 109줄의 "두 행(answer-eval, deploy-package)"이 ADR 글과 다른 풀어 쓴 말인 것)을 고쳤고, 나머지 여덟은 바뀌기 전의 옛 글(PRD 상태 줄, ADR 0048 초안의 두 문구, plan.md 59줄의 옛 접두사 문장)과 저장소 밖 문서(제안서 둘째 판 293줄, `rag-engine-plan.md` 9줄, 제안서 5절의 SQL 커넥터 문장, `gh`의 오류 문구)를 글자 그대로 옮긴 것이라 둔다. 그 커밋 명령 뒤에 인계 계기(`hook_handoff`, 컨텍스트 328,990 토큰, 경계 `커밋 뒤`)가 왔지만 계기를 낸 명령이 실패해 `handoff.md` 1의 첫 줄(인계하지 않는 때)대로 넘기지 않고 이었다. 이 세션은 곁 세션이 아니다(`get_session`의 `self`에 `parentSessionId`가 없다).

## 인계(커밋 뒤)

세션 컨텍스트가 인계 문턱을 넘어(계기 문장은 363,435 토큰) `커밋 뒤` 경계에서 넘긴다. 둘째 시도에서 들어간 커밋 `0a0f3bba`(제목 67자. 첫 시도는 commit-msg 훅에 막혀 커밋이 만들어지지 않았으므로 이 브랜치의 커밋은 이 하나다)는 pre-commit을 모두 지났다. 열 단계와 인용 대조·변이 표 검사는 Passed이고, ruff 둘과 카나리아 명세·헌법 판 검사는 `(no files to check)`로 Skipped다(`.py`와 명세·헌법 파일이 커밋에 없다. ruff 둘은 "검증" 절대로 손으로 쳐 0이었다). 인용 대조는 경고 9건을 냈고 막지 않았다. 첫 커밋의 10건에서 둘을 고쳤고, 고친 것을 적은 "커밋" 절의 155줄이 바뀌기 전 문구를 따옴표로 인용해 하나가 늘었다. 아홉 모두 바뀌기 전의 옛 글(PRD 상태 줄, ADR 0048 초안의 두 문구, plan.md 59줄의 옛 접두사 문장, 이 일지가 고친 옛 문구)과 저장소 밖 문서·`gh` 오류 문구를 글자 그대로 옮긴 것이라 둔다. 작업 트리는 깨끗하고(`git status --short`가 비었다) 푸시하지 않았으며 이 브랜치에 열린 PR은 없다(`gh pr view docs/rag-engine-name --json state`가 PR이 없다고 답했다). 이 세션의 제목은 `docs/rag-engine-name`이었다. 이 세션은 곁 세션이 아니다(`get_session`의 `self`에 `parentSessionId`가 없다). `handoff.md` 1의 다섯에 들지 않아 넘긴다. 이 세션이 띄운 백그라운드 작업은 없다. 남은 단계는 아래 지시문의 "이어받을 상태"에 있다.

### 인계 지시문

```
다음 작업: 기능 rag-engine-name. 제안서 둘째 판이 정한 문서 검색 서버 저장소 이름(rag-engine)을 저장소 절차대로 반영한다(셀프 리뷰, ADR 0048 이력 승인, plan.md, PR)
다음 단계: 설계 인터뷰
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: docs/journal/2026-11-06-11-rag-engine-name.md의 "사용자 프롬프트" 절의 요청을 "인계 전 상태"의 남은 일 1부터 잇는다. 제안서는 C:\Users\User\Downloads\agent-os-rag-baseline-plan (1).md
브랜치: docs/rag-engine-name
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-06-11-rag-engine-name.md 전체. "인계 전 상태"의 남은 일 1~3과 4의 둘째 셀프 리뷰·검증·커밋은 끝났고, "이어받은 세션"부터 "인계(커밋 뒤)"까지가 이 세션의 기록이다. 제안서 둘째 판은 지금 C:\Users\User\Downloads\agent-os-rag-baseline-plan.md(15:04)이고 "(1)" 파일은 없다
이어받을 상태: 인계: 커밋 뒤. docs/journal/2026-11-06-11-rag-engine-name.md. 커밋 0a0f3bba(docs: 문서 검색 서버 저장소 이름을 ADR 0048 이력과 plan.md에 반영한다 (rag-engine-name))까지 했고 푸시하지 않았으며 열린 PR은 없다. 남은 단계: PR 직전 리뷰의 대체 둘(CodeRabbit CLI는 `Seat: not assigned`라 돌지 못했다. `/security-review`는 커밋 뒤 origin/main을 합친 상태에서, `bug-perf-review` 서브에이전트는 나란히. 두 보고를 일지에 옮기고 Critical·Major를 고친 뒤 커밋), 푸시, PR(docs/<slug> 면제 PR. 템플릿의 체크리스트에 CLI가 돌지 못한 것과 대체 둘의 결과를 적는다), `@coderabbitai review` 코멘트, merge.md 2~4의 "워크트리에서 병합할 때", 일지 "다음", retro, next-session. `tools/sibling_overlap.py`가 커밋 전에 알린 것 둘: 형제 워크트리 04-runtime-enforces-rules-per-tool-call에 일지 2026-11-06-09가 있어 그쪽이 먼저 병합되면 이 일지의 번호를 옮긴다(병합 직전에 다시 친다), 워크트리 mcp-shutdown-spec도 .scratch/plan.md를 고쳐 나중에 병합하는 쪽에 글자 충돌 후보다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지(ADR 0048 이력은 사용자 승인을 받았다)
```

제목을 `docs/rag-engine-name (인계함)`으로 바꿨다(바꾸기 전 제목은 `docs/rag-engine-name`). 이 세션이 띄운 백그라운드 작업은 없어 멈출 것이 없다. `git worktree unlock C:/project/agent/.claude/worktrees/rag-engine-name`은 `is not locked`로 끝나 `handoff.md` 4대로 넘어갔다. 이 문장을 `printf`로 바로 일지에 더하려 하자 워크트리 가드가 명령 글자 속의 `git worktree unlock`을 보고 거부해, 파일로 써서 `cat`으로 붙였다.

open-session을 부른다 2026-11-06T07:18:27Z

## 이어받은 세션(PR 직전 리뷰부터)

인계 지시문대로 새 세션이 제목을 `docs/rag-engine-name`으로 바꾸고 워크트리 `C:/project/agent/.claude/worktrees/rag-engine-name`에 들어갔다(`git worktree list`에서 그 브랜치가 체크아웃된 자리를 찾았다).

- 상태. HEAD는 `0a0f3bba`이고 origin/main은 `d0f5a195` 그대로라(`git fetch origin main` 뒤 `git log --oneline -3 origin/main`으로 봤다) 이 브랜치는 origin/main 바로 위의 커밋 하나다. 합칠 것이 없어 `/security-review`의 전제(커밋 뒤 origin/main을 합친 상태)는 이미 차 있다. 작업 트리에는 앞 세션이 커밋하지 않은 이 일지의 "인계(커밋 뒤)" 절이 있다(`git status --short`). 제안서 둘째 판은 지시문대로 `Downloads/agent-os-rag-baseline-plan.md`(15:04)이고 "(1)" 파일은 없다(`ls -la`).
- 좌석. `coderabbit auth status`를 다시 쳤다. `Plan: Free`, `Seat: not assigned` 그대로라 CLI 축은 비었고 대체 둘로 간다.
- 형제. `uv run python tools/sibling_overlap.py`는 `번호 겹침 없음`이고, 다음 빈 번호는 일지 `2026-11-06-10`·대기열 581·티켓 045(아직 어디에도 없는 번호라 코드 스팬에 넣었다. 그 도구가 그렇게 안내했다), 이름순으로 앞서는 형제는 워크트리 04-runtime-enforces-rules-per-tool-call의 일지 2026-11-06-09 하나, 함께 고친 파일은 워크트리 mcp-shutdown-spec의 `.scratch/plan.md`였다. 열린 PR은 없다(`gh pr list --state open`이 빈 목록을 냈다).

## PR 직전 리뷰(대체 둘)

`bug-perf-review` 서브에이전트(기준 d0f5a195, 밀 주장 여섯)와 내장 `/security-review`를 나란히 돌렸다.

### /security-review

내장 명령의 1단계(취약점 식별 서브태스크)에 저장소 규약(PR 템플릿 체크리스트의 "설계 문서의 침묵이 곧 구현의 침묵")을 함께 넘겨, 지시의 HARD EXCLUSIONS 가운데 "Insecure documentation"은 글투와 설명 부족에만 적용하고, 설계 문서의 결정·Blocked by·신뢰 경계가 그대로 구현되면 CWE가 되는 자리는 보게 했다. 결과는 찾은 것 없음(No findings)이고, 식별이 0건이라 2·3단계(거짓 양성 거르기와 신뢰도 8 미만 제외)는 돌 것이 없었다. 서브태스크가 따라가 본 것: 바뀐 파일 여섯과 작업 트리의 일지 추가분을 ADR 0046·0048 본문, `CONTEXT.md`의 신뢰 수준·도구 결과·주체·사이트 항목, plan.md의 바뀌지 않은 행(approval-rules, local-model, mcp-http, doc-qa-agent, mcp-trust, value-masking)과 대 봤다. Blocked by 셋의 대응(answer-eval은 1:1, deploy-package는 ADR 0048 이력의 분할 셋과 글자 그대로, stale-warning은 접두사만)에서 agent-os 쪽 선행 행은 하나도 빠지지 않았고, 보안 결정이 든 내용 칸(검색 도구를 허락하는 규칙 파일, 토큰은 환경 변수, 443 하나, 진단 묶음에 비밀 값 없음, 문서 속 지시를 데이터로)의 글자는 바뀌지 않았다. 신뢰 경계 문장(검색 결과는 최종 사용자 입력과 같은 신뢰 수준, MCP로 읽기 도구만, `_meta` 주체의 범용 형식)은 이 diff가 건드리지 않았고, 포인터 셋은 옛 문장을 이력으로 넘기기만 해 옛 결정과 새 결정 사이에 구현자가 더 약한 쪽을 고를 어긋남이 없다. PRD의 구조화 데이터 질의 미룸과 ADR 0048 이력의 1.0 db-source(다른 저장소의 행) 사이의 긴장은 범위 서술이라 CWE 경로로 이어지지 않는다고 판정했다(신뢰도 0.7 미만, 보고하지 않음). 일지와 이력에 실린 값은 경로·계정 이름·`Seat`·`Plan` 줄·토큰 수뿐이고 비밀 값은 없다(원칙 V). 고칠 것 없음.

### bug-perf-review

기준 d0f5a195, 범위 파일 여섯(전부 문서, 여섯 모두 따라갔다), 도구 호출 37, 백그라운드 작업 없음. Critical·Major 없음, Minor 셋(유효 둘, 보류 하나), 오탐 넷.

- 유효 Minor — 이 일지 21줄. `rag-engine-plan.md` 표를 "165~177줄"로 적었는데 지금 파일(15:04)에서는 "## 6. 행"이 179줄, 표 머리가 183줄, 행 열둘이 185~196줄이다(리뷰가 `grep -n "^## "`로 봤고, 이 세션이 같은 명령과 `sed -n '183,196p'`로 다시 봤다. 165~177줄은 5절 끝 근처다). 앞 세션이 읽은 판은 지금과 달랐을 수 있다(두 파일 모두 15:04에 다시 저장되었다). 고침: 절 이름으로 가리키고 두 판의 줄 번호를 함께 적었다.
- 유효 Minor — 이 일지 159줄(커밋되지 않았던 "인계(커밋 뒤)" 절). "둘째 커밋 `0a0f3bba`"라고 썼지만 이 브랜치의 커밋은 그 하나다(`git log --oneline origin/main..HEAD`가 한 줄을 냈다). 첫 시도는 commit-msg 훅에 막혀 커밋이 만들어지지 않았다(155줄). 이어받는 세션이 "첫 커밋"을 찾거나 둘을 합치려 들 수 있다. 고침: "둘째 시도에서 들어간 커밋"으로 고치고 커밋이 하나라고 덧붙였다.
- 보류 Minor — `.scratch/plan.md` 32줄. answer-eval이 `rag-engine:core`만 기다리는데 수락 문장은 "실제 문서 검색 서버 이미지에 공개 문서 묶음을 넣고 돌린 평가 세트"를 요구하고, 그 저장소에서 이미지를 만드는 행은 release-image(슬라이스 2)이며 core는 HTTP 서버다(`sed -n '32p'`로 수락 문장을, `rag-engine-plan.md` 6절 표로 행을 봤다). 제안서 둘째 판 143줄도 같은 Blocked by와 같은 수락 문장이라 이번 변경이 만든 문제가 아니라 제안서를 그대로 옮긴 것이고, 첫 판의 `rag-mcp`가 어디까지 맡았는지는 남아 있지 않아 이번 이름 바꿈이 뜻을 바꿨는지는 가릴 수 없다. 사용자가 "이름 바뀐 곳만 고친다"를 골랐으므로 이 PR에서는 두고, answer-eval의 설계 인터뷰가 먼저 볼 것으로 이 일지 "다음"과 PR 남긴 위험에 적는다.

요청받은 확인은 모두 맞았다. Blocked by의 행 이름 다섯(core, release-image, backup-upgrade, diag-bundle, doc-freshness)이 `rag-engine-plan.md` 6절 표에 있다. `tests/test_plan_status.py`는 Blocked by 칸을 보지 않고 `.py` 가운데 그 칸을 읽는 곳도 없다. `uv run python tools/check_adr_pointers.py`는 출력 없이 끝났고 포인터 셋은 `.claude/rules/adr.md` 13줄 모양이며 제목이 ADR 0048의 `###` 줄과 글자 그대로 같다. `git diff --check`도 깨끗하다. `CONTEXT.md` 177줄 _Avoid_는 지금 plan.md와 맞는다. 살아 있는 문서의 옛 이름은 plan.md 59줄, ADR 0046 29·47줄, ADR 0048 19·48줄 다섯 자리뿐이고 모두 포인터나 대응 설명이 붙은 자리다. plan.md의 일곱 줄 변경(7행 추가·7행 삭제)은 행을 더하거나 지우지 않았다.

밀 주장 여섯의 대조. (1) 행 대응 가운데 rag-ops의 분할 셋은 옛 plan.md 글(33·34줄이 백업과 진단을, deploy-package가 rag-ops를 기다린 것)과, rag-mcp→core는 answer-eval의 옛 Blocked by와, bootstrap 빠짐은 제안서 293줄의 일곱 행 목록과 맞았다. rag-admin→source-sync·admin은 첫 판이 저장소에도 Downloads에도 없어 대 보지 못했다(앞 세션의 word-diff에 기댄다. 커밋 메시지의 남긴 위험과 같다). (2) 킥오프 런북은 `rag-engine-plan.md` 9줄과 제안서 293줄이 들고 `KICKOFF.md`는 루트에 추적되어 있다. (3) 1.0 열은 제안서 2절 표의 rag-engine 1.0 칸이 "hwp-binary, doc-permission, doc-freshness, db-source, change-log"라 둘이 들어 있는 것까지 확인했고, "더해졌다"는 변화는 첫 판이 없어 대 보지 못했다. ADR 0046에도 그 저장소의 1.0 행 목록이 없다. (4) stale-warning은 43줄 diff가 접두사만 바뀐 것이다. (5) 59줄 세 문장은 맞고, 프론티어는 approval-rules·local-model·mcp-http·pilot-portal 넷 그대로이며 바뀐 Blocked by 행 셋은 모두 다른 선행 행도 기다리는 todo라 풀리거나 새로 막힌 행이 없다. (6) "이어받은 세션"의 명령 결과는 `git diff --name-only e9bbfcc9 d0f5a195`에 plan.md가 없고 origin/main이 d0f5a195이며 두 파일이 15:04인 것으로 맞았다(`gh`는 다시 치지 않았다).

오탐 넷은 리뷰가 근거를 적어 닫았다. PRD 24줄의 "그런 데이터를 색인하지 않는다"는 `rag-engine-plan.md` 126~128줄이 SQL 커넥터를 "데이터베이스에 든 글"로 한정해 db-source와 모순되지 않는다. 인계 지시문이 첫 지시문의 "시작 프롬프트"·"다음 단계"를 되풀이한 것은 `handoff.md` 38줄의 모양이다. PRD 상태 줄의 "개정 두 번"은 앞선 셀프 리뷰가 다룬 해석 문제이고 사용자가 승인한 문장이다. 일지 23줄의 "코드 변경은 approval-rules 01·02뿐"은 그때의 origin/main(e9bbfcc)을 서술한 기록이다.

다시 돌린 명령: 일지만 고쳐 다시 돌릴 검사가 없고, 커밋의 pre-commit으로 갈음한다. PR 직전 리뷰를 반영하며 새로 쓴 문장은 이 일지 21줄의 두 판 줄 번호와 159줄의 "둘째 시도에서 들어간 커밋"이고, PR 리뷰어 참고에 적는다.

## 커밋 뒤의 인계 계기(넘기지 않음)

커밋 명령(`git commit -F`)을 백그라운드로 띄운 직후 인계 계기(`hook_handoff`, 컨텍스트 270,395 토큰, 경계 `커밋 뒤`)가 왔다. `handoff.md`를 Read로 열어 1의 다섯을 봤다. 이 세션을 연 지시문의 "이어받을 상태"가 `인계: 커밋 뒤`로 시작해 셋째(인계로 연 세션이 넘겨받은 경계에 다시 왔다)에 들어 넘기지 않고 이었다. 커밋이 도는 동안은 편집 훅(`hook_edit_during_commit`)이 막으므로 이 판단은 커밋이 끝난 뒤에 적었다.

## 커밋(이 세션의 것)과 PR

커밋 `ccfbd2c9`(docs: PR 직전 리뷰 대체 둘의 보고를 일지에 옮기고 Minor 둘을 고친다)는 pre-commit을 모두 지났다(백그라운드 출력 파일을 `tail -45`로 읽었다). 열 단계 Passed(pytest 403.8s, web-verify 583.3s, 러너 584.16s), 마크다운 표·줄 구분 문자·변이 표·커밋 메시지 검사 Passed, ruff 둘과 카나리아 명세·헌법 판 검사는 `(no files to check)`로 Skipped다(일지만 든 커밋이라 대상 파일이 없다). 인용 대조 경고 1건은 206줄의 "hwp-binary, doc-permission, doc-freshness, db-source, change-log"로, 제안서 둘째 판 2절 표의 rag-engine 1.0 칸을 글자 그대로 옮긴 것이라 둔다. 커밋 전에 친 `uv run python tools/sibling_overlap.py`는 처음 1로 끝났다. 이 일지가 적은 "다음 빈 번호 일지 2026-11-06-10"이 어디에도 없는 일지 번호를 가리켜서였고, 그 출력의 안내대로 코드 스팬에 넣고 다시 쳐 `번호 겹침 없음`으로 0이었다. `git branch --show-current`는 `docs/rag-engine-name`이었다. 커밋 뒤 `git status --short`는 비었다.

`git push -u origin docs/rag-engine-name`으로 커밋 둘(`0a0f3bba`, `ccfbd2c9`)을 푸시하고, `gh pr create --base main --head docs/rag-engine-name --title … --body-file …`로 PR #479(https://github.com/njh6803/agent-os/pull/479)를 열었다(docs/<slug> 면제 PR, 티켓 없음. 제목은 첫 커밋의 제목 그대로이고, 본문은 PR #473을 본보기로 템플릿을 채웠으며 체크리스트의 PR 직전 리뷰 줄은 위 "PR 직전 리뷰(대체 둘)" 절의 결과다. 따옴표가 든 `--title`을 워크트리 가드가 거부하지 않았다).

## 인계(PR 연 뒤)

PR을 연 명령 직후 인계 계기(`hook_handoff`, 컨텍스트 283,907 토큰, 경계 `PR 연 뒤`)와 next-session 계기(`hook_pr_next_session`)가 함께 왔다. `handoff.md`대로 앞의 것이 이기고 Skill 도구로 next-session을 부르지 않는다. 1의 다섯을 봤다. PR은 열렸고(명령 성공), 요청 범위는 PR과 병합까지라 이 경계에서 끝나지 않고, 이 세션의 지시문의 "이어받을 상태"는 `인계: 커밋 뒤`로 시작해 지금 경계(`PR 연 뒤`)와 다르며, 이 일지에 이 세션이 쓴 `인계 못함` 줄이 없고, 곁 세션이 아니다(`get_session`의 `self`에 `parentSessionId`가 없다). 다섯에 들지 않아 넘긴다. `@coderabbitai review` 코멘트는 남기지 않았다(`handoff.md` 3의 `PR 연 뒤` 줄대로 새 세션이 남긴다). 앱의 PR 바는 #479를 스스로 묶었다(`get_status`: bound, 열 때 검사 pending 6·passing 1·skipped 1, `MERGEABLE`·`BLOCKED`). 자동 고침(auto_fix)은 켜지 않았다. 새 세션이 자기 대기(`tools/wait_ci.py`)를 띄우기 때문이다(`handoff.md` 6). 이 세션이 띄운 백그라운드 작업은 없다(커밋은 끝났고 서브에이전트 둘은 보고를 냈다). 이 세션의 제목은 `docs/rag-engine-name`이었다. 커밋하지 않은 변경은 이 일지의 "커밋 뒤의 인계 계기(넘기지 않음)" 절부터 이 절까지이고, 새 세션이 이어 쓰고 커밋한다.

### 인계 지시문

```
다음 작업: 기능 rag-engine-name. 제안서 둘째 판이 정한 문서 검색 서버 저장소 이름(rag-engine)을 저장소 절차대로 반영한다(셀프 리뷰, ADR 0048 이력 승인, plan.md, PR)
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: docs/journal/2026-11-06-11-rag-engine-name.md의 "사용자 프롬프트" 절의 요청을 "인계 전 상태"의 남은 일 1부터 잇는다. 제안서는 C:\Users\User\Downloads\agent-os-rag-baseline-plan (1).md
브랜치: docs/rag-engine-name
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-06-11-rag-engine-name.md 전체. "이어받은 세션(PR 직전 리뷰부터)"부터 "인계(PR 연 뒤)"까지가 이 세션의 기록이다. PR 본문은 `gh pr view 479 --json body`로 읽는다. 제안서 둘째 판은 지금 C:\Users\User\Downloads\agent-os-rag-baseline-plan.md(15:04)이고 "(1)" 파일은 없다
이어받을 상태: 인계: PR 연 뒤. docs/journal/2026-11-06-11-rag-engine-name.md. PR #479(docs/rag-engine-name)를 열었고 `@coderabbitai review` 코멘트는 아직 남기지 않았다. 남은 단계: merge.md 2(봇 회차)부터. 첫 `@coderabbitai review` 코멘트를 남기고 `uv run python tools/wait_ci.py 479`를 백그라운드로 띄워 기다린다. 봇 지적을 반영한다(첫 회차의 Minor·Nit은 지적마다 판단). 이 일지의 "다음"과 retro를 마친 일지를 커밋해 푸시한다. "다음"에 적을 것 하나: answer-eval(plan.md 32줄)의 Blocked by가 rag-engine:core만인데 수락은 실제 문서 검색 서버 이미지를 요구하고 이미지는 그 저장소의 release-image가 만든다. 제안서가 그대로라 이 PR에서는 두었고 answer-eval의 설계 인터뷰가 먼저 본다(PR 직전 버그 축의 보류). 그 뒤 merge.md "워크트리에서 병합할 때" 1~4(--match-head-commit, --delete-branch 금지, 원격 정리, 주 체크아웃 미갱신 한 줄)와 next-session. 커밋하지 않은 변경은 이 일지의 인계 절들이고 새 세션이 이어 쓰고 커밋한다. 병합 직전 tools/sibling_overlap.py를 다시 친다. 형제 워크트리 04-runtime-enforces-rules-per-tool-call의 일지 2026-11-06-09가 먼저 병합되면 이 일지의 번호를 옮기고 PR 본문의 일지 이름도 `gh pr edit 479 --body-file`로 고친다. 워크트리 mcp-shutdown-spec도 .scratch/plan.md를 고쳐 나중에 병합하는 쪽에 글자 충돌 후보다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지(ADR 0048 이력은 사용자 승인을 받았다)
```

제목을 `docs/rag-engine-name (인계함)`으로 바꿨다(바꾸기 전 제목은 `docs/rag-engine-name`. 세션이 스스로 붙인 제목이라 앱이 묻지 않고 바꿨다). 이 세션이 띄운 백그라운드 작업은 없어 멈출 것이 없다. `git worktree unlock C:/project/agent/.claude/worktrees/rag-engine-name`(경로는 `git rev-parse --show-toplevel`의 출력 그대로)은 `is not locked`로 끝나 `handoff.md` 4대로 넘어갔다. 이 턴에서는 가드가 Bash의 `git worktree unlock`을 거부하지 않았다.

open-session을 부른다 2026-11-06T07:49:24Z

## 이어받은 세션(PR 반영·병합부터)

인계 지시문대로 새 세션이 제목을 `docs/rag-engine-name`으로 바꾸고 워크트리에 들어갔다(HEAD `ccfbd2c9`가 PR #479의 `headRefOid`와 같다). `@coderabbitai review` 코멘트를 남기고 `uv run python tools/wait_ci.py 479`를 백그라운드로 띄웠다.

### CI 실패: 러너의 ripgrep이 14에서 15로 올랐다

대기 명령이 `python`과 `verify` 실패로 끝났다(`CodeRabbit NEUTRAL`, 나머지 초록). `python` 잡의 실패는 `tests/tools/test_hook_env_read_rg.py::test_Grep_도구의_glob_에서_훅이_rg_보다_넓게_막는_자리[{{.env}}]` 한 건이다(`1 failed, 6441 passed`). 이 PR은 문서만 바꿔 원인이 아니다. 원인은 러너다. main의 마지막 초록 실행(`42172283644`, 06:05 UTC)은 `ubuntu-24.04`(이미지 `20261101.360.1`)에서 ripgrep 14.1.0-1을 깔았고, 이 PR의 실패 실행(`42183052219`, 07:46 UTC)은 `ubuntu-26.04`(이미지 `20261101.186.1`)에서 ripgrep 15.1.0-1ubuntu1을 깔았다(두 잡 로그의 `Image:`와 `Setting up ripgrep` 줄을 `gh run view --log --job`으로 봤다). `ci.yml`이 `ubuntu-latest`를 쓰고 `rg`를 까는 잡은 `python` 하나다(`grep -n`, 59줄). 테스트의 `_GREP_TOOL_STRICTER` 주석(117줄)이 "rg 14.1.1 은 겹친 묶음을 풀지 못해 오류로 끝난다"고 적은 그 동작이 15.1.0에서 달라졌을 것으로 보이나 15를 직접 재지는 않았다. 열린 PR은 #478(04)도 같은 잡을 돌린다. 세션 카드(`start_session` own_initiative)는 훅이 막았다(ADR 0037 "세션 카드").

> 사용자: (PR #479가 문서와 무관한 CI 실패로 병합되지 않습니다. CI 서버의 운영체제 이미지가 최근에 새 판(ubuntu-26.04)으로 바뀌어 검색 도구 ripgrep이 14.1.0에서 15.1.0으로 올라갔고, 14 판의 동작을 가정한 훅 테스트 한 건이 깨졌습니다. 어떻게 풀까요?) "러너를 24.04로 고정" — 설명: 이 워크트리에서 새 브랜치를 따서 ci.yml의 python 잡(ripgrep을 까는 유일한 잡)만 ubuntu-24.04로 고정합니다. main의 마지막 초록 실행(06:05 UTC)이 그 이미지였고, 이 PR의 실패 실행(07:46 UTC)이 26.04였습니다. 그 PR을 먼저 병합하고 #479에 main을 합쳐 다시 돌립니다. CI 한 바퀴가 이번 실행 기준 9분 32초라 그만큼 걸립니다. ripgrep 15에서 훅이 어떻게 다른지는 재 보지 않은 채 일지 '다음'에 별도 일로 적습니다.

고르지 않은 선택지(라벨만): "테스트를 ripgrep 15도 아는 쪽으로 고침", "고치지 않고 멈춤".

이 세션은 거기서 러너 고정을 새 브랜치 `chore/045-ci-python-runner-pin`으로 옮겨 PR #480으로 열었다. 일지는 `docs/journal/2026-11-06-10-ci-python-runner-pin.md`다.

## 이어받은 세션(러너 고정 병합 뒤 PR #479로 돌아옴)

PR #480(`chore/045-ci-python-runner-pin`)을 먼저 병합했다. 병합 커밋은 `6f205c0e`이고 `gh pr view 480 --json state,mergeCommit`이 `MERGED`를 냈다. 그 실행의 `python` 잡은 `Image: ubuntu-24.04`와 `Setting up ripgrep (14.1.0-1)`에서 `6442 passed`로 초록이었다(`gh run view --log --job`을 받아 `grep`으로 손으로 봤다). 원격 브랜치는 `git fetch --prune origin` 뒤 `git ls-remote --exit-code --heads origin refs/heads/chore/045-ci-python-runner-pin`이 종료 2로 끝나 없다. 주 체크아웃 미갱신: 루트는 main(`d0f5a195`, `git worktree list --porcelain`으로 봤다).

이 워크트리로 돌아와 보니 HEAD는 `ccfbd2c9`이고 작업 트리의 변경은 이 일지뿐이었다(`git status --short`). 아래 "회고"와 "다음"을 쓰고 이 일지를 커밋한 뒤 `git merge origin/main`으로 러너 고정을 합쳐 다시 돌린다.

번호 옮김. 러너 고정의 일지 2026-11-06-10이 먼저 main에 들어 이 일지의 번호(08)가 이름순으로 뒤처졌다(`uv run python tools/sibling_overlap.py`가 "다음 세션이 이름순 최신 일지의 '다음'을 읽어 이 일지를 지나친다"고 알리고 11로 옮기라고 했다). `--move`로 11로 옮기고, 합친 main에 든 티켓 045와 일지 2026-11-06-10의 살아 있는 가리킴(티켓 5줄, 일지 5·11줄)도 11로 고쳤다. 그 일지의 기록(인용한 옛 문구, 당시 지시문의 경로)은 쓰인 그대로 두었다.

## 회고

후보 3, 승인 1(회차로 세는 것), 기각 2, 넘김 0. 넘긴 것이 없어 사용자에게 묻지 않았다. 일지는 이 일지 하나와 PR #480의 일지(2026-11-06-10)를 읽었다. 이 PR이 연 CI 실패(ripgrep 14→15)는 2026-11-06-10의 회고가 대기열 500의 2회차로 이미 셌다.

1. **승인(회차로 센다).** 문서 검색 서버의 저장소 이름을 바꾸며 앞 세션이 옛 이름 `rag-server`로만 `grep`해, 옛 행 이름 `rag-mcp`·`rag-ops`가 든 ADR 0046 47줄을 놓쳤고 셀프 리뷰 두 축이 같은 자리를 Major로 잡았다(이 일지 "셀프 리뷰" 절 Standards 1·Spec 1). `CLAUDE.md` 작업 규약 4(결정이 바뀌면 옛 표현을 저장소 전체에서 grep해 잔존이 0인지 본다)가 이미 정한 것을 어긴 사건이다. 열린 대기열 420("결정이나 측정이 바뀐 뒤 옛 표현이 살아 있는 문서 셋에 남아 셀프 리뷰가 잡았다", 10회차)과 같은 가족이고, 이번에는 이름 바꿈에서 새 이름의 옛 표기 하나만 찾은 것이 달랐다. 420에 11회차를 더했다(`자체 승인 2026-11-06, 11회차`). 420은 3회차를 훨씬 넘겨 지침이 아닌 검사(옮긴 이름을 낱말로 받아 살아 있는 문서의 잔존을 세는 도구)를 고르는 행이라 이 PR에서 반영하지 않는다. 넘김이 아니다(가드레일을 느슨하게 하지 않는다). 문턱: 사건은 이 일지, 층은 420이 고르는 검사, 되돌림은 PR 하나다. 이 사건에서 드러난 모양(새 이름 하나로 grep하면 옛 이름이 둘 이상일 때 놓친다)은 그 행의 도구 설계가 받는다.
2. **기각.** 첫 커밋이 commit-msg 훅의 "제목 79자 > 72자"에 막혔다(이 일지 "커밋" 절). 이미 있는 훅이 그 자리에서 막은 것이다.
3. **기각.** `coderabbit auth status`를 `head -12`로 잘라 `Seat` 줄을 못 봤다(이 일지 "PR 직전 리뷰(CodeRabbit CLI)" 절). `CLAUDE.md` 환경 함정의 "검사 도구가 내가 생각하는 것을 실제로 봤는지 먼저 확인한다"가 이미 있고, 그 세션이 스스로 알아차려 비용이 호출 하나였다.

만료할 행: `uv run python tools/queue_open_rows.py --ref origin/main`이 없다고 냈다. 회차 3 이상의 열린 행이 이미 여럿 있어 chore 계기는 그쪽이 낸다.

## 다음

- answer-eval(`.scratch/plan.md` 32줄)의 Blocked by가 `rag-engine:core`만인데 수락 문장은 실제 문서 검색 서버 이미지를 요구하고, 그 이미지는 `rag-engine:release-image`가 만든다. 제안서 둘째 판 143줄이 그대로여서 이 PR은 이름만 바꾸고 두었다. answer-eval의 설계 인터뷰가 먼저 본다(PR 직전 버그 축의 보류).
- `rag-engine` 저장소는 아직 없다(2026-11-06에 `gh repo view`·`gh repo list`로 봤다). 만들 때 `KICKOFF.md`를 복사해 시작하고, `plan.md`의 `rag-engine:<slug>` 행이 닫혔는지는 그 저장소를 본 뒤 확인한다(ADR 0048).
- principal-propagation의 Blocked by에 그 저장소의 문서 권한 행(doc-permission)을 넣을지는 그 행의 설계 인터뷰가 정한다.
- ripgrep 15에서 훅과 `rg`의 동작 차이를 재서 `tests/tools/test_hook_env_read_rg.py`가 두 판을 모두 아는 쪽으로 고치고 러너 고정을 풀지 정하는 harness 티켓과, ADR 0038 이력·12줄 포인터(사용자 승인)는 일지 2026-11-06-10 "다음"에 적혀 있다. 새 harness 티켓으로 쓴다.
