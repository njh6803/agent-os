# 2026-11-06 (08) 문서 검색 서버의 저장소 이름 rag-engine(제안서 둘째 판 반영)

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
- 두 판을 `git diff --no-index --word-diff`로 견줬다. PRD 개정안(6절), 위젯 ADR 초안(8절), 10~13절은 같다. 달라진 것은 둘이다. (1) 문서 검색 서버 저장소의 이름이 `rag-engine`으로 정해지고 그 행이 다시 나뉘었다(rag-mcp → core, rag-admin → source-sync와 admin, rag-ops → release-image와 backup-upgrade와 diag-bundle, 1.0에 db-source와 change-log). (2) 5절 접점 표에 "구조화 데이터"(Text-to-SQL은 기준선과 1.0 범위 밖) 줄이 더해졌다. 행 이름은 같은 폴더의 `rag-engine-plan.md` 표(165~177줄)와 맞는다.
- 둘째 판도 앞 판의 전제를 들고 있어 그대로 따르지 않는 곳: approval-rules를 슬라이스 10·pilot-release 뒤로 미루는 것(어제 "지금 자리에서 계속"을 골랐고 지금 `in-progress`, 티켓 01 #475·02 #476 병합), ADR 번호 0044~0046, install-package(→ deploy-package), "주소 모양 MCP 서버"(→ 원격 MCP 서버), doc-qa-agent의 Blocked by(approval-rules가 든다), pilot-release 알려진 한계의 "운영자 승인 규칙 없음"(빠졌다).
- 1절의 사실. `403c9e9` 뒤로 origin/main은 `e9bbfcc`이고, 일지 2026-11-06-02가 대 본 `83a66cd` 뒤의 코드 변경은 approval-rules 01·02뿐이다(`git diff --stat 83a66cd..origin/main -- src plugins uv.lock pyproject.toml openapi.json`). 걸리는 사실을 다시 봤다. `ModelProvider`는 `ANTHROPIC` 하나, `run.py` 1009줄의 `self._tools.connect`, `RunFinished`는 `output` 하나, `uv.lock`의 mcp 2.3.0, Dockerfile 없음. `C:\project`에 rag-engine 저장소는 없다.
- `rag-server:`가 든 살아 있는 문서: `.scratch/plan.md` 32·35·38·43·59줄(33·34줄은 접두사 없는 옛 행 이름 `rag-ops`만 든다. 처음에는 일곱 줄 모두 `rag-server:`가 든다고 적었고, 이어받은 세션의 셀프 리뷰 두 축이 `git grep`으로 다시 세어 고쳤다), ADR 0046 29줄, ADR 0048 19줄, `CONTEXT.md` 177줄(`git grep`, 일지 제외). ADR 0046 47줄은 첫 판의 행 이름 다섯(bootstrap, rag-mcp, rag-admin, search-eval, rag-ops)을 들고 있는데 `rag-server`로만 grep해 놓쳤고, 같은 셀프 리뷰가 잡았다(아래 "셀프 리뷰"). `tests/test_plan_status.py`는 Blocked by 칸을 보지 않는다(21줄 독스트링).

## 사용자가 정한 것

> 사용자: (이번 판에서 새로 바뀐 것(저장소 이름 rag-engine과 그 행 이름)만 저장소에 반영할까요?) "이름 바뀐 곳만 고친다 (Recommended)" — 설명: plan.md에서 Blocked by 셋(answer-eval, deploy-package, stale-warning), 내용 칸 셋(ops-backup-upgrade, diag-bundle, principal-propagation), 프론티어 문단의 접두사를 rag-engine:으로 바꿉니다. ADR 0048에는 저장소 이름을 정한 이력 하나를 더해 보여 드리고 승인을 받습니다. ADR 0046 29줄과 용어집 177줄의 rag-server: 표기도 함께 고칩니다. approval-rules의 자리와 deploy-package라는 이름처럼 어제 정한 것은 그대로 둡니다.

> 사용자: (새로 들어온 '구조화 데이터(매출·재고 같은 숫자는 Text-to-SQL 도구로 따로 다루고 기준선과 1.0 범위 밖)' 줄을 어디에 둘까요?) "PRD의 미룬 것에 더한다 (Recommended)" — 설명: PRD 24줄의 미룬 것 목록에 '구조화 데이터 질의(Text-to-SQL)'를 더합니다. PRD 개정이므로 더할 문장을 먼저 보여 드리고 승인을 받습니다. 나중에 'DB의 숫자도 답하게 하자'는 요청이 나오면, 그 기능이 범위 밖이라는 근거가 PRD에 남아 있습니다.

## PRD 개정(승인)

화면에 두 곳을 diff로 보였다. 상태 줄의 "2026-11-06 개정 사용자 승인. 개정의 근거는 ADR 0042와 ADR 0046"을 "2026-11-06 개정 두 번 사용자 승인. 개정의 근거는 ADR 0042와 ADR 0046, 일지 2026-11-06-08"로, 미룬 것 목록 끝에 "구조화 데이터 질의(Text-to-SQL)"를 더하고 "돌아오면 …" 뒤에 "구조화 데이터 질의는 매출이나 재고처럼 숫자가 바뀌고 합계를 내야 하는 데이터를 묻는 것이고, 문서 검색 서버는 그런 데이터를 색인하지 않는다."를 넣는다. 제안서의 "SQL 커넥터는 데이터베이스에 든 글만 가져온다"는 그 저장소가 정할 일이라 넣지 않았다고 함께 적었다.

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
시작 프롬프트: docs/journal/2026-11-06-08-rag-engine-name.md의 "사용자 프롬프트" 절의 요청을 "인계 전 상태"의 남은 일 1부터 잇는다. 제안서는 C:\Users\User\Downloads\agent-os-rag-baseline-plan (1).md
브랜치: docs/rag-engine-name
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-06-08-rag-engine-name.md 전체, 제안서 둘째 판 2~5절
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. PRD 개정은 승인받아 반영했고 ADR 0048 이력은 승인 전 초안이다. docs/journal/2026-11-06-08-rag-engine-name.md
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
