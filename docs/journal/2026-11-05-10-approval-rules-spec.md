# 2026-11-05 (10) approval-rules 명세

## 사용자 프롬프트

> 사용자: `.claude/skills/to-spec/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: approval-rules / 다음 작업: 기능 approval-rules. 운영자의 승인 규칙 파일(후보 6)의 명세를 쓴다 / 다음 단계: 명세 / 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 approval-rules-spec)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 시작 프롬프트: /to-spec approval-rules / 브랜치: docs/approval-rules-spec / 모델: Fable 5.1 / xhigh / 읽을 것: docs/journal/2026-11-05-08-approval-rules-design.md의 "다음" 절, docs/adr/0044-… / 이어받을 상태: ADR 0044는 accepted이고 PR 469로 병합됐으며 설계 인터뷰는 끝났다. 명세가 대 볼 것 넷과 구현 티켓의 완료 조건 둘(core.md 재개 항목, sdk.md 선택 필드 항목)이 일지 "다음"에 있다. 사용자가 정할 것 셋(서버에 묶인 단일 도구 꼴, 승인 결정을 서버에 묶을지, deny 오타 사실을 바로잡은 뒤 모양만 보는 결정을 다시 볼지)도 그 절에 있고 명세 전에 사용자에게 물어 정한다. / 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session merge.md의 "워크트리에서 병합할 때"를 Read로 열어 따른다 / 이번 요청 범위: 명세까지

## 사용자가 정한 것(명세 전, AskUserQuestion 한 화면)

지시문이 "명세 전에 사용자에게 물어 정한다"고 한 셋과 to-spec의 이음매 확인을 한 화면에 물었다. 넷 모두 추천안을 골랐다. 고른 라벨과 설명은 아래 글자 그대로다.

> 사용자: (규칙 파일의 줄에 서버에 묶인 단일 도구 꼴 `everything:add`를 더할까, 더하면 allow에는 서버를 꼭 붙이게 할까?) "더하고 allow는 서버 필수 (Recommended)" — 설명: `everything:add` 꼴을 받습니다. 열어 주는 allow 줄은 `서버:도구`나 `서버:*`만 받고 맨 이름(`add`)이 있으면 파일이 깨진 것으로 거부합니다. 막는 deny와 묻는 ask는 맨 이름도 받습니다(넓게 맞아도 안전한 쪽이라서). ADR 0044는 꼴이 둘뿐이라고 적었으므로(20행) 이력으로 남깁니다.

> 사용자: (승인 결정을 서버에 묶을까? 멈춘 사이 서버 목록이 바뀌어 같은 이름 `add`가 다른 서버에서 오면 그 다른 도구에 승인이 적용된다. PR 리뷰 봇이 Major로 짚었다.) "서버까지 묶는다 (Recommended)" — 설명: 멈춤 기록에 서버 이름이 남고, 재개할 때 서버가 다르면 재개 불일치(`resume_mismatch`)로 실패합니다. 서버 칸이 없는 옛 트레이스는 지금처럼 이름과 인자만 봅니다. ADR 0044 64행이 "이 ADR이 정하지 않는다, 사용자가 정할 물음"으로 남긴 자리입니다.

> 사용자: (deny 오타가 같은 도구를 덮는 allow가 있으면 묻지 않고 돈다는 사실 위에서, 모양만 보는 결정을 그대로 둘까?) "에이전트 표만 연결과 대 본다 (Recommended)" — 설명: 에이전트 표(표 이름은 명세가 짓습니다)에 적힌 도구 이름이 그 에이전트의 연결 목록에 없거나 서버 이름이 매니페스트의 서버 목록에 없으면 연결 직후 `run_failed`(도구 연결)입니다. 공통 표는 여러 에이전트에 걸치므로 모양만 봅니다. 인터뷰에서 "뜻밖에 허락되는 일은 없다"는 설명 아래 거부했던 안(ADR 0044 Considered Options 74행)을 바로잡은 사실 위에서 다시 묻는 것이고, 고르면 ADR 0044 이력으로 남깁니다.

> 사용자: (시험을 어디에 둘까?) "core 주 이음매 + 실제 모델 하나 (Recommended)" — 설명: 게이트의 집행, 적용 규칙 칸, 재개와 서버 대조, 모두 deny인 재개는 core에서 가짜 포트로 시험합니다. 파일 읽기와 깨짐은 파일시스템 어댑터 시험, 같은 이름 검사는 MCP 어댑터 시험(같은 픽스처 stdio 서버를 두 플러그인 이름으로 띄워 같은 이름을 만듭니다), 투영은 HTTP 항목 시험에 둡니다. 그리고 예시 규칙 파일을 둔 calc를 실제 모델로 돌려 모두 deny인 재개가 어떻게 끝나는지 보는 `-m llm` 시험 하나를 둡니다.

## tidy-checkouts(워크트리에 들어가기 전, 주 체크아웃에서)

지시문대로 Skill 도구로 `tidy-checkouts`를 먼저 돌았다. 루트는 main이고 깨끗해 `origin/main`의 b77f158f(PR 469)로 당겼다. 지운 것은 워크트리 `041-mutate-check-marker-quality`와 로컬 브랜치 `chore/043-plan-skill-plugin-done`·`worktree-044-plan-status-matches-tickets-test`이고, 휴지통에 남아 있던 042의 `web/node_modules` 잔재를 비웠다. 남긴 것과 이유는 다음과 같다. `03-default-model-plugin-and-explicit-flag`·`06-round-drive-record`는 바뀐 파일이 있다. `044-plan-status-matches-tickets-test`·`admin-style-spec`·`admin-style-to-spec`·`mcp-shutdown-spec`·`web-widget-spec`은 그때 병합된 PR이 없었다. `05-default-model-required-and-checked`는 agent-os.exe(pid 7960)와 python.exe(pid 26204·38052)가 쥐고 있다. `approval-rules-design`은 claude.exe·pwsh.exe가 쥐고 있다(그 세션이 아직 떠 있다). `confident-wright-2d3ebf`·`elegant-dijkstra-aaddb9`는 앱의 표지가 있어 앱의 정리에 맡긴다. 사람에게 넘긴 것은 없고 답을 기다리지 않았다. 그 뒤 `EnterWorktree`(approval-rules-spec)로 들어가 `docs/approval-rules-spec`을 땄고, 명세를 쓰기 전에 `origin/main`(57316a5d, PR 470)을 합쳤다.

## 측정: 모두 deny인 재개의 모델 호출

ADR 0044 "치르는 값"의 어림(도구 호출 블록이 든 대화를 도구 정의 없이 보내면 API가 거부해 원인 `model_call`의 `run_failed`가 된다)은 결과에 따라 명세의 처리가 갈리므로, to-spec 3대로 명세가 받는 자리에서 쟀다. 프로브는 `.scratch/approval-rules/probes/all_deny_resume_call.py`이고, 저장소의 모델 플러그인 `claude-opus-5`를 실제 어댑터로 만들어 루프와 같은 `model_caller`로 묶고, 멈춘 호출을 거부로 기록한 직후의 메시지 열을 손으로 지어 세 갈래(도구없음, 양성 대조 도구있음, `tool_choice` none의 선택없음)로 두 회차씩 보냈다. 판정은 돌리기 전에 독스트링에 적었다. 측정 6회차, 측정 아님 0회차, 종료 코드 0. 여섯 회차 모두 수락이고 도구 호출이 없었다. 어림은 서지 않았고 사전 판정대로 명세는 모두 deny인 재개에 처리를 따로 두지 않는다. 실제 재개 길이 `run_finished`로 끝나는 것은 재지 않았고 구현 티켓의 `-m llm` 시험이 잰다. 해석과 갈래가 가른 것, 재지 않은 것은 그 폴더의 `README.md`다. LLM 토큰 합계: 입력 2214 출력 920.

## 명세

`.scratch/approval-rules/spec.md`(Status: ready-for-agent). 서두의 수는 넘겨받은 것 열둘, 사용자가 고른 것 넷, 명세가 정한 것 열여덟, 이력 다섯, 거부한 안 마흔다섯이다. 이름과 문구는 이렇게 정했다. 파일은 `rules.toml`, 표는 `[common]`과 `[agents.<에이전트 이름>]`, 규칙 줄은 세 꼴(`add`, `everything:*`, `everything:add`)이고 allow는 서버를 붙인 두 꼴만 받는다. 핵심은 불변 값 `Rules`를 `PluginSource.read_rules()`(인자 없는 동기 메서드)로 받고 규칙 값은 core에 둔다. 적용 규칙 칸은 `rule`(값 `deny`·`requires_approval`·`ask`·`allow`·`default`, sdk의 닫힌 목록 `AppliedRule`), 서버 칸은 `run_paused`의 `server`이고 둘 다 런타임만 쓴다. 거부 문구는 `운영자가 거부했다: <서버>:<도구>`, 연결 목록에 없는 이름은 게이트 앞에서 `도구가 없다: <이름>`으로 거부한다. 같은 이름 검사는 MCP 어댑터가 연결을 열며 한다. 그 에이전트의 표는 연결 직후 승인 요구 검사 바로 뒤에 대 본다. 설계가 묻지 않은 자리 하나를 코드를 읽어 찾았다. 마스킹할 인자가 있는 도구가 운영자의 ask나 적힌 규칙 없음으로 멈추면 승인 뒤 마스킹된 값이 도구에 가므로, 준비 단계에서 `PluginError`로 거부한다(저자의 승인 요구와 마스킹이 겹칠 때의 지금 자리와 같다). 고칠 자리는 묶음 A(계약과 sdk, 관리 화면의 필드 이름 표)·B(포트와 어댑터)·C(core 집행과 재개)·D(예시와 바깥 증거)로 나눴고 시험은 사용자가 고른 이음매대로 core 주 이음매와 어댑터 시험, HTTP 항목 시험, 실제 모델 시험 하나다.

## ADR 이력과 plan.md

`.claude/rules/adr.md`대로 Skill 도구로 `domain-modeling`을 먼저 불렀다. ADR 0044에 `## 이력`을 열고 2026-11-05 이력 넷을 썼다. "규칙 줄에 서버에 묶인 도구 하나의 꼴이 늘고 allow는 서버를 붙인다", "승인 결정은 서버에도 묶인다", "그 에이전트의 표는 연결 뒤 대 본다", "명세가 정한 것과 잰 것". 앞의 셋은 사용자가 고른 것이고 넷째는 명세가 채운 이름·문구·자리와 측정 결과다. 본문에서 거짓이 되거나 범위가 바뀐 문장 뒤에 포인터를 달았다. 모양 절의 두 꼴과 모양만 본다와 맨 이름 규칙, 기록 절의 선택 칸 하나, 범위 밖의 필드 이름 표 항목 하나와 서버 묶음, Considered Options의 거부한 안, Consequences의 계약 줄과 치르는 값(allow의 범위, deny 오타, `<서버>:<도구>`, 모두 deny인 재개)이다. ADR 0009에는 2026-11-05 둘째 이력 "재개의 일치 검사는 서버도 본다"를 썼다. 그 ADR의 2026-09-22 이력 문장("도구 이름과 마스킹된 인자에 묶인다")에는 포인터를 달지 않았다. 지난 이력 항목은 기록이고 포인터 검사가 이력 절 안의 포인터를 거부한다(처음에 달았다가 검사가 빨개져 뺐다). `uv run python tools/check_adr_pointers.py`는 초록이다. `CONTEXT.md`는 고치지 않았다. 규칙 파일·승인 요구·적용 규칙 항목이 셋째 꼴과 서버 묶음 뒤에도 글자 그대로 참이고, 새 용어는 나오지 않았다. `.scratch/plan.md`의 approval-rules 행과 프론티어 문단에 명세가 선 것과 사용자가 더 고른 셋, 다음이 명세 검토와 티켓인 것을 적었다. 행의 상태는 티켓이 없어 todo 그대로다(`tests/test_plan_status.py`가 티켓 상태와 대 본다).

## 인계(셀프 리뷰 직전)

code-review 스킬을 부른 직후 인계 계기(`hook_handoff`)가 왔다. 세션 컨텍스트 201,465 토큰(문턱 200,000), 경계 "셀프 리뷰 직전". `handoff.md`를 Read로 열어 따랐다. 인계하지 않는 때 다섯에 들지 않는다. 계기를 낸 명령은 실패하지 않았고, 요청 범위(명세까지. 지시문의 선행 조건 줄이 병합까지를 이 세션의 일로 적었다)는 이 경계에서 끝나지 않으며, 이 세션의 지시문은 인계로 연 것이 아니고, `인계 못함` 줄이 없고, 곁 세션이 아니다(`get_session`의 `self`에 `parentSessionId`가 없다). 셀프 리뷰는 밟지 않고 새 세션이 한다.

- 이 세션의 제목은 `docs/approval-rules-spec`(이 세션이 첫 턴에 붙였다)이고 `docs/approval-rules-spec (인계함)`으로 바꾼다.
- 커밋하지 않은 변경(`git status --porcelain`): 고친 것 `.scratch/plan.md`, `docs/adr/0009-resume-by-replaying-the-trace.md`, `docs/adr/0044-rules-file-is-enforced-per-call-and-operator-deny-beats-the-decision.md`. 새 것 `.scratch/approval-rules/`(`spec.md`, `probes/README.md`, `probes/all_deny_resume_call.py`), 이 일지. 내용은 위 "측정"·"명세"·"ADR 이력과 plan.md" 절이다. 커밋도 푸시도 없고 PR도 없다(`gh pr view docs/approval-rules-spec`이 없다고 했다). 브랜치 머리는 `origin/main`(57316a5d)과 같다.
- 이 세션이 번복하거나 고친 것: ADR 0009의 2026-09-22 이력 문장에 달았던 포인터를 뺐다(`check_adr_pointers.py`가 이력 절 안의 포인터를 거부했다. 지난 이력은 기록). 명세 서두의 수 둘을 다시 세어 고쳤다(명세가 정한 것 열여섯 → 열여덟, 거부한 안 서른넷 → 마흔다섯. 절 제목의 "명세가 정했다"와 "거부한 안:" 줄의 굵은 글씨를 셌다). 명세 "모두 deny인 재개"의 `run_finished` 끝맺음을 측정이 아니라 어림으로 고쳐 적었다(측정은 API 수락과 글 응답까지다). ADR 0044 이력 제목의 띄어쓰기(`allow 는` → `allow는`)를 본문 표기에 맞췄고, 포인터도 함께 고쳤다. 그 밖에 번복한 결정은 없다.
- 백그라운드 작업은 없다(프로브는 끝났고 `run_checks.py`는 아직 띄우지 않았다). 워크트리 잠금은 풀고 넘긴다.
- 주 체크아웃은 이 세션이 시작할 때 b77f158f로 당겼으나 그 뒤 origin/main이 57316a5d(PR 470)로 앞섰다(`git worktree list` 첫 줄과 `git rev-parse --short origin/main`으로 봤다). 새 세션의 지시문에 미갱신으로 적는다.
- 넘기는 단계(새 세션이 이 차례로 한다. "다음" 절은 단계를 닫는 세션이 쓴다): `/code-review`(기점 origin/main) 셀프 리뷰와 Critical·Major 반영 → 서두의 수 다시 세기(to-spec 3) → ADR 0044 이력 넷과 ADR 0009 이력 하나의 승인을 AskUserQuestion 한 화면으로 받는다(작업 규약 5. 초안은 디스크에 있다) → 검증(문서와 프로브만 바뀌어 손으로 치는 다섯은 pre-commit 결과로 갈음하되 마크다운 표·줄 구분 문자 검사는 pytest 저장소 상태 테스트가 보고, 프로브 `.py`는 ruff가 본다) → `git branch --show-current` 확인과 `uv run python tools/sibling_overlap.py`(일지 10의 번호 대조) 뒤 커밋(메시지는 heredoc이나 파일) → `git-pr`로 PR(docs/ 면제 PR, 티켓 없음) → PR 직전 리뷰와 봇 회차 → 병합은 `next-session` `merge.md`의 "워크트리에서 병합할 때"를 Read로 열어 따른다 → next-session 지시문(다음은 명세 검토와 `/to-tickets approval-rules`, 사용자가 부른다) → retro.

지시문:

```
다음 작업: 기능 approval-rules. 운영자의 승인 규칙 파일(후보 6) 명세의 산출물(spec.md, 프로브와 README, ADR 0044 이력 넷과 ADR 0009 이력 하나, plan.md 두 자리, 일지)을 셀프 리뷰부터 수 세기·이력 승인·커밋·PR·병합까지 마친다
다음 단계: 명세
어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec approval-rules
브랜치: docs/approval-rules-spec
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-05-10-approval-rules-spec.md의 "인계(셀프 리뷰 직전)" 절(커밋하지 않은 변경과 넘기는 단계)과 "사용자가 정한 것" 절, .scratch/approval-rules/spec.md, docs/adr/0044-rules-file-is-enforced-per-call-and-operator-deny-beats-the-decision.md의 2026-11-05 이력 넷, docs/adr/0009-resume-by-replaying-the-trace.md의 2026-11-05 둘째 이력
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리 approval-rules-spec에 있고 셀프 리뷰(/code-review, 기점 origin/main)부터 한다. 일지 docs/journal/2026-11-05-10-approval-rules-spec.md. 사용자가 정할 것 셋은 물어 정했고(일지 "사용자가 정한 것") 다시 묻지 않는다. 명세·프로브·ADR 이력 다섯·plan.md는 모두 쓰였고, 이력은 초안이라 셀프 리뷰 반영 뒤 AskUserQuestion으로 승인을 받는다(작업 규약 5). 서두의 수(열둘·넷·열여덟·다섯·마흔다섯)는 반영마다 다시 센다. 측정은 끝났고 다시 돌리지 않는다. 일지의 "다음" 절은 아직 없다
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main(origin/main보다 뒤). 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: 명세까지
```

제목을 `docs/approval-rules-spec (인계함)`으로 바꿨다(앱이 묻지 않고 바꿨다). 같은 제목으로 도는 다른 세션은 없고 이 세션을 뺀 도는 세션은 0이다(`list_sessions` limit 50). 멈출 백그라운드 작업은 없다.
`git worktree unlock`으로 이 워크트리의 잠금을 풀었다(오류 없음, 종료 코드 0).

open-session을 부른다 2026-11-05T12:08:22Z

## 새 세션(셀프 리뷰부터)

위 지시문으로 연 새 세션이다(사용자 프롬프트는 그 지시문 그대로이고 open-session이 보냈다). 제목을 `docs/approval-rules-spec`으로 바꿨다(앱이 묻지 않고 바꿨다). 주 체크아웃에서 Skill 도구로 `tidy-checkouts`를 먼저 돌았다. 루트는 main이고 깨끗해 b77f158f에서 `origin/main`의 57316a5d(PR 470)로 당겼다. 지운 것은 워크트리 `044-plan-status-matches-tickets-test`와 브랜치 `chore/044-plan-status-matches-tickets-test`(쉬는 세션 셋의 `claude.exe`가 쥐고 있어 `end-holders`로 끝낸 뒤 `judge`를 다시 쳐 지웠다), 로컬 브랜치 `worktree-approval-rules-spec`(커밋이 모두 `origin/main`에 있다)이다. 남긴 것과 이유는 다음과 같다. `05-default-model-required-and-checked`는 `judge`가 지운다로 냈으나 `remove`가 종료 1로 멈췄다(agent-os.exe pid 7960, python.exe pid 26204·38052가 모듈을 올려 두어 이름 바꾸기가 막혔다. 망가뜨린 것은 없다). `approval-rules-design`은 claude.exe 다섯(쉬는 세션들)과 pwsh.exe 둘(pid 34312·31564)이 작업 디렉터리로 쥐고 있다. `03-default-model-plugin-and-explicit-flag`·`06-round-drive-record`는 바뀐 파일이 있다. `admin-style-spec`·`admin-style-to-spec`·`mcp-shutdown-spec`·`web-widget-spec`·`approval-rules-spec`은 병합된 PR이 없다. `confident-wright-2d3ebf`·`elegant-dijkstra-aaddb9`는 앱의 표지가 있어 앱의 정리에 맡긴다. 휴지통에 남은 것은 없었다. 사람에게 넘긴 것은 없고 답을 기다리지 않았다. 그 뒤 `EnterWorktree(path)`로 이 워크트리에 들어왔다. 브랜치는 `docs/approval-rules-spec`, 머리는 57316a5d(`origin/main`과 같다)이고 커밋하지 않은 변경은 위 "인계" 절의 목록 그대로다.

code-review를 부른 직후 인계 계기(`hook_handoff`, 세션 컨텍스트 217,328 토큰, 경계 "셀프 리뷰 직전")가 다시 왔다. `handoff.md`를 Read로 열어 봤다. 인계하지 않는 때 셋째("이어받을 상태"가 `인계: 셀프 리뷰 직전`로 시작한다. 인계로 연 세션이 넘겨받은 경계에 다시 왔다)에 들어 넘기지 않고 code-review를 그대로 밟는다. 자동 압축이 받는다.

## 셀프 리뷰

`/code-review`(기점 `origin/main`)를 돌았다. 범위는 base 57316a5d(HEAD와 같다), 고친 파일 셋(`.scratch/plan.md`, ADR 0009, ADR 0044), 커밋 0, 미추적 넷(`spec.md`, `probes/README.md`, `probes/all_deny_resume_call.py`, 이 일지)이다. 표준 축(sonnet·high)과 명세 축(본 세션의 모델)을 나란히 돌렸고 두 브리프에 주장 검증 목록과 밀 주장을 줬다. 명세 축의 명세 출처는 지시문의 산출물, to-spec 스킬, ADR 0044 "명세로 넘긴 것", 설계 일지 "다음", 사용자의 답 넷(위 "사용자가 정한 것" 원문), adr·probes 규칙이고, 리뷰어 참고로 인계 사실과 이력이 초안인 것을 가렀다.

### 표준 축 보고(요지)

- Major 1. 명세 "깨짐과 읽기 실패의 문구"가 검증 오류를 pydantic 문구에서 입력 값을 벗긴 것이라 적고 `_describe`를 선례로 들었는데, `.claude/rules/adapters.md`는 "운영자 파일(`disabled.toml`)의 손상 문구는 이 보호 밖이고 검증 오류 전문을 싣는다"고 적고 코드(`_parse_operator_file`)도 `{error}`를 그대로 싣는다. "값은 들지 않는다"와 거부한 안 "값을 싣는다"의 근거도 거짓이다.
- Minor. 서두의 수 가운데 거부한 안이 마흔다섯이 아니라 47이다(`거부했다.`도 47번). 나머지 넷(열둘·넷·열여덟·다섯)은 맞다.
- Minor. 인용 다섯이 원문과 다르다. ADR 0044에 "도구 이름은 서버가 정한 원문 그대로"가 없다. 용어집은 "도구 호출 하나를 막을지"다. ADR 0042는 "운영자 파일은 둘이 는다. 규칙 파일과 서버 파일"이다. 다른 호출을 `run_failed`로 끝내는 규칙은 ADR 0014가 아니라 ADR 0009의 2026-09-22 이력이다. Out of Scope가 든 "PR 직전 보안 리뷰 판단"은 allow 권고 문장이다.
- Minor. Out of Scope가 mcp-trust에 넘긴 `tool_called`의 서버 칸이 plan.md의 mcp-trust 행에 없다.
- Minor. `_call_safely`는 `_describe`를 써 지금 내용은 `LookupError: 도구가 없다: add`라 명세의 "같은 내용"이 아니다.
- 포인터 Minor 둘. ADR 0044 21행·83행의 포인터가 문장 가운데에 있다. 91행 "프로브는 없다"가 거짓인데 포인터가 없다. Nit. 56행 "sdk는 두 이벤트의 선택 칸 말고는 바뀌지 않는다"는 `AppliedRule`로 포인터 후보다.
- 프로브 Minor 둘. README가 "블록이 모델에 갔다"를 되울림과 토큰 크기로만 읽고 코드가 단언하는 표지(응답의 모델 이름)는 블록이 드롭된 해석에서도 난다. 명세의 "두 회차 되울림"은 README(도구없음 둘째 회차만)보다 강하다. 프로브의 거부 문구와 명세의 문구가 다른 것을 README가 밝히지 않는다.
- Nit. 일지 "명세" 절의 묶음 D 서술이 명세와 다르다. plan.md 프론티어 문단에 낡은 서술이 남아 있다. baseline smell은 없다.
- 확인된 것. `check_adr_pointers.py` 초록, 프로브 ruff 초록, `uv.lock`의 두 판이 README와 같다, 명세가 든 식별자 모두 실재, 지금 문구 넷 일치, ADR 0009 이력이 인용한 2026-09-22 문구 둘 글자 그대로, 일지의 20·64·74행 맞다, 입력 토큰 합 2214는 123×2+492×4와 맞다.
- 요약: 하드 위반 5건(Major 1, Minor 4), 판단 항목 7건(Minor 5, Nit 2). Critical 없음.

### 명세 축 보고(요지)

- (a) a1 Minor. 위 plan.md mcp-trust 행과 같다(Blocked by는 approval-rules를 포함한다).
- (b) b1 Major. 명세 151행(고치기 전)이 서버가 다르거나 지금 그 이름의 도구가 없으면 재개 불일치라고 적은 것은 사용자의 둘째 답("서버가 다르면 재개 불일치")에 없는 확장인데 "사용자가 골랐다"로 두고 ADR 0044·0009 이력이 사용자 결정으로 적는다. 또 106행 3단계(없는 이름은 게이트 앞 거부, 결정 소비)와 같은 상황을 서버 칸의 유무로 `run_failed`와 계속으로 갈라 끝낸다. 지금 코드는 `_require_paused_call`이 연결을 보지 않고 통과하고 승인 뒤 `_call_safely`가 `ok=false` `LookupError: 도구가 없다: …`로 계속한다(탐침으로 불렀다).
- (c) c1 Major(표준 축 Major 1과 같다. 탐침이 `input_value='../SECRETVALUEXYZ'`가 든 문구를 봤다). c2 Major. 명세 185·207행과 US 19가 `-m llm` 시험이 `plugins/`를 복사해 `rules.toml`이 따라간다고 적는데 `_copy_repo_plugins`는 `agents/calc`·`mcp/everything`·`skills/answer-format`·`models/<기본>` 네 폴더만 복사한다. 고치지 않으면 `-m llm` 전부가 기본 묻는다에서 멈춘다. c3 Major. "도구 이름은 서버가 정한 원문 그대로" 인용 없음. c4~c9 Minor. 용어집 인용, ADR 0042 인용, `LookupError:` 접두, 되울림 회차, ADR 0014, `tests/sdk/`에 `cause`·`shortcuts` 시험이 없다(`tests/adapters/test_jsonl.py`·`tests/core/test_run.py`에 있다). c10~c12 Nit. 일지의 포인터 목록 "결정 줄의 선택 칸 하나"는 ADR 0044 8행에 없고 35행에만 있다. 일지 묶음 D. "모델을 부를 때마다"는 `ctx.llm()` 한 번에 한 번이다.
- 확인된 것. 집행의 차례 1~8이 `_Context._call`의 흐름과 맞고 "그대로다" 단계가 모두 실재한다. `_reject_runtime_only`·`_bind`·`routes[route.tool.name]`·`approval_conflicts`·`items.py` 투영을 코드로 확인했다. `FailureCause`에 네 원인이 실재한다. "명세로 넘긴 것" 12항목이 모두 짝이 있고 완료 조건 둘이 넘겨받은 것 12와 묶음 A·C에 있다. 사용자 답 넷이 일지와 글자 같다. 마스킹·묻기 충돌의 자리와 `secret_args` 전제가 맞다. 프로브가 표지·사전 판정·양성 대조·README 표를 갖추고 `run_finished`는 어림으로 적었다. `<서버>:<도구>` 꼴의 에이전트 표 검사는 설명의 두 조건을 합친 자연스러운 범위다.
- 요약: (a) 1, (b) 1, (c) 12. Major 4(b1·c1·c2·c3), Minor 7, Nit 3.

### 반영

지적마다 근거를 코드와 문서에서 먼저 봤다(`adapters.md` 18행, `filesystem.py` 234행, `run.py`의 `_require_paused_call` 1281~1287행과 `_call_safely` 1567~1572행과 `_describe` 1594행, `tests/test_main.py` 2802~2815행, `CONTEXT.md` 392행, ADR 0042 42행, ADR 0044 20행, ADR 0009 141행). 고친 것은 다음이다. 새로 쓴 사실 문장은 PR 직전 리뷰의 밀 주장으로 원문을 둔다.

1. 깨짐 문구(명세 "깨짐과 읽기 실패의 문구", Testing의 좋은 시험·시험할 모듈). 값을 벗긴다를 전문을 싣는다로 바꿨다. 새 문장: "검증 오류는 pydantic 문구의 전문이고 입력 값이 든다. 운영자 파일의 손상 문구는 매니페스트 문구가 값을 벗기는 보호의 밖이다", "문구에 어느 배열의 몇째 줄인지(`agents.calc.allow.0`)와 그 줄의 값이 든다". 거부한 안을 "검증 오류에서 값을 벗긴다(매니페스트 문구처럼)"로 바꿨다(수는 같다).
2. 재개의 없는 이름(명세 "집행의 차례" 2·3, "서버 칸과 재개의 대조", ADR 0044 이력 "승인 결정은 서버에도 묶인다", ADR 0009 이력). 사용자의 답대로 서버가 다를 때만 불일치로 좁히고, 지금 연결에 그 이름의 도구가 없으면 3의 거부(결정 소비)로 통일했다. 절 제목에 "없는 이름의 처리는 명세가 정했다"를 더하고 거부한 안 "지금 그 이름의 도구가 없으면 재개 불일치로 끝낸다"를 더했다. 새 문장: "지금 연결에 그 이름의 도구가 없으면(멈춘 사이 그 서버가 매니페스트에서 빠졌다) 서버를 대 보지 않고, 재개가 아닐 때와 같이 게이트 앞에서 `도구가 없다: <이름>`으로 거부하며 결정은 소비된다", "지금 코드는 이름과 인자만 대 보고 없는 이름을 `_call_safely`의 실패 결과로 넘긴다(코드를 읽었다)".
3. `-m llm` 도우미(명세 "예시 규칙 파일과 시험 자리의 규칙 파일", 묶음 D, "실제 모델 시험 하나"). 새 문장: "`-m llm` 시험은 저장소 `plugins/`에서 calc와 그것이 쓰는 플러그인 폴더 넷만 임시 루트에 복사하므로(`tests/test_main.py`의 `_copy_repo_plugins`, 코드를 읽었다) 루트의 `rules.toml`은 따라가지 않는다. 그 도우미가 `rules.toml`도 복사하게 고친다(묶음 D)".
4. 인용 다섯. ADR 0044 "도구 이름 그대로", 용어집 "도구 호출 하나를 막을지, 멈출지, 그냥 부를지를 정한 규칙의 출처", ADR 0042 "운영자 파일은 둘이 는다. 규칙 파일과 서버 파일", ADR 0009의 2026-09-22 이력 "결정은 정책이 아니라 멈춘 호출에 묶인다", Out of Scope의 근거를 사용자의 첫째 답으로.
5. `도구가 없다` 문구(명세 "집행의 차례" 3). 새 문장: "지금은 이 호출이 어댑터의 `LookupError`를 `_call_safely`가 바꾼 `LookupError: 도구가 없다: <이름>`의 실패 결과가 되는데(코드를 읽었다) … 내용은 예외 타입의 접두 없이 어댑터의 문구만 싣는다".
6. 되울림(명세 "모두 deny인 재개"). README대로 둘째 회차만으로 좁혔다.
7. sdk 시험의 선례를 `tests/adapters/test_jsonl.py`의 `test_실패_원인과_바로가기가_왕복하고_헤더는_3_그대로다`와 `test_새_필드_둘의_키가_없는_옛_줄은_원인과_바로가기가_없음으로_읽힌다`로 바꿨다.
8. ADR 0044 포인터. 21행·83행의 포인터를 문장 끝으로 옮겼다(21행은 맨 이름 규칙 문장과 allow 권고 문장을 한 묶음으로 보고 뒤에 하나). 91행 "프로브는 없다. 이 결정에 수치 근거가 없기 때문이다." 뒤에 "명세가 정한 것과 잰 것" 포인터를 달았다.
9. plan.md의 mcp-trust 행에 넘긴 것 둘(`tool_called`의 서버 칸, 서버 파일의 이름)을 적었다. Blocked by는 approval-rules다.
10. README "재지 않은 것"에 프로브의 거부 문구 `운영자 규칙이 거부했다: add`가 명세의 문구와 다른 것과, 그 차이가 수락 여부에 들지 않는다고 보는 것은 어림이라 적었다.
11. 이 일지의 "명세" 절 묶음 D 서술과 "ADR 이력과 plan.md" 절의 포인터 목록을 고쳤다.
12. 서두의 수. 거부한 안 마흔다섯을 마흔여덟으로(47에 2의 하나를 더했다). 나머지 넷은 그대로다.

남긴 것과 이유.

- ADR 0044 56행 "sdk는 두 이벤트의 선택 칸 말고는 바뀌지 않는다"(Nit). `AppliedRule`은 그 칸의 값 타입이라 칸의 일부로 보고 문장을 참으로 뒀다. 포인터를 달지 않았다.
- README의 표지(응답의 모델 이름이 블록 드롭 해석에서도 난다, Minor). 프로브가 재는 것은 API의 수락이고, "블록이 모델에 갔다"는 README가 관찰과 어림으로 가른 둘째 물음이다. 명세의 처리("따로 두지 않는다")는 수락만 기대하므로 표지를 바꾸지 않았다.
- "모델을 부를 때마다"(Nit). `ctx.llm()` 한 번이 모델 호출 한 번이라 같은 뜻으로 뒀다.
- plan.md 프론티어 문단의 낡은 서술(Nit). 그 문단은 시간순 기록이라 옛 문장을 지우지 않는 관행이다.
- ADR 이력을 고치며 `domain-modeling`을 다시 부르지 않았다. 앞 세션이 이 기능의 이력 다섯을 쓰며 불렀고(위 "ADR 이력과 plan.md"), 이 세션의 고침은 그 초안 하나의 범위를 사용자의 답으로 좁히고 포인터 자리를 옮긴 것이라 새 용어가 없다.

다시 돌린 명령과 결과(손으로 쳤다). `uv run python tools/check_adr_pointers.py` 출력 없이 종료 0. `uv run ruff check .scratch/approval-rules/probes/all_deny_resume_call.py` "All checks passed!". `uv run python tools/check_md_tables.py`와 `uv run python tools/check_line_separators.py`에 고친 마크다운 여섯(명세, 프로브 README, plan.md, 이 일지, ADR 0044, ADR 0009)을 주어 둘 다 출력 없이 종료 0. 서두의 수는 Grep으로 다시 셌다. `^### .*명세가 정했다` 18줄, `거부했다.` 48번, "사용자가 골랐다" 절 제목 다섯은 결정 넷(시험 자리의 둘은 한 결정)이고, 넘겨받은 것 (1)~(12)와 이력 다섯은 그대로다. 나머지 손으로 치는 검증은 커밋의 pre-commit 결과로 갈음한다(결과는 커밋 뒤에 적는다).

## ADR 이력 승인

셀프 리뷰를 반영한 뒤 이력 다섯의 요지(위 1~5 반영 뒤의 본문)를 보이고 AskUserQuestion 한 화면으로 물었다. 사용자가 고른 라벨과 설명은 아래 글자 그대로다.

> 사용자: (위 요지의 ADR 0044 이력 넷과 ADR 0009 이력 하나를 이대로 승인할까요? 승인하면 명세와 같은 커밋으로 들어가고, 이력에 적힌 결정이 구현 티켓의 전제가 됩니다) "다섯 모두 승인 (Recommended)" — 설명: 이력 다섯을 지금 디스크의 초안 그대로 확정합니다. 다음 단계(검증·커밋·PR·병합)로 바로 갑니다.

고르지 않은 다른 선택지는 멈춘 도구가 사라진 경우만 다시 정하는 것(2의 재개에서 도구가 연결에서 사라진 경우를 `run_failed`로 끝내는 쪽으로 바꾸고 명세와 이력 둘을 고친 뒤 다시 본다)였다. 그래서 ADR 0044의 2026-11-05 이력 넷과 ADR 0009의 2026-11-05 둘째 이력은 승인됐고, 셋째 꼴과 allow의 서버, 서버 묶음과 없는 이름의 처리, 에이전트 표 검사, 명세가 정한 이름·문구·자리와 측정 결과가 구현 티켓의 전제다.

## 커밋과 PR 직전 리뷰

커밋 d13dd2fe `docs: approval-rules 명세를 쓰고 ADR 0044·0009 이력 다섯에 고른 셋과 정한 것을 남긴다`(파일 일곱, +609/-12). 첫 시도는 제목이 87자라 Bash의 PreToolUse 훅이 commit-msg 판정(72자)을 미리 짚어 막았고, 제목을 64자로 줄여 다시 쳤다. pre-commit은 ruff check, ruff format, parallel-checks(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest 355.9초, web-verify 509.6초. 합 509.88초), markdown tables, line separators, mutation tables, quotes, commit message가 모두 Passed다. canary specs와 constitution version은 해당 파일이 없어 Skipped이고 이 커밋에 그 종류의 파일이 없으니 손으로 칠 것이 없다. 이것으로 손으로 치는 다섯을 갈음한다. 인용 대조 훅(경고만)이 넷을 냈다. 이 일지 92행(명세 축 보고가 옮긴, 고치기 전 명세 151행의 문장), 이 일지 130행(고르지 않은 선택지의 라벨), 명세 159행(포트 독스트링에 적을 제안 문장), 명세 180행(deny를 도구 목록에서 뺀다는 인용이 ADR 0042 43행·ADR 0044 28행 어느 문장과도 글자 그대로 같지 않다). 판정과 고침은 아래 반영에 적는다.

PR 직전 리뷰. `coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 CLI 축이 비어(`docs/constitution/operations.md` 리뷰 파이프라인 2) 대체 둘을 돌렸다. 버그·성능은 `bug-perf-review` 서브에이전트(기준 57316a5d, 셀프 리뷰 반영에서 새로 쓴 밀 주장 여덟을 브리프에 나열), 보안은 커밋 뒤 `/security-review`다(`git fetch origin` 뒤 origin/main이 57316a5d 그대로라 합칠 것은 없었다).

### 버그·성능 축 보고(요지)

- 범위 파일 7, 호출 40에서 멈췄다. Minor 5(유효 4, 보류 1), Critical·Major 없음, 오탐 0.
- 유효 1. 명세 60행의 ADR 0042 인용(운영자 파일은 둘이 는다, 규칙 파일과 서버 파일)이 리터럴 Grep 0건이고 42행에 두 조각이 따로 있다(이음 글자는 열지 못했다).
- 유효 2. 명세 185행과 묶음 D(201행)가 `-m llm` 시험 전부가 기본 묻는다에서 멈춘다고 적은 것이 코드와 어긋난다. `_copy_repo_plugins`를 부르는 시험은 2867행 하나이고, 551행 시험은 `plugins/` 통째를 복사하며(새 `rules.toml`이 따라간다), 2836행 시험은 `cwd=REPO_ROOT`, 1024·2442행의 gatedcalc 시험 둘은 `_write_plugin`·`_write_mcp_plugin`으로 손수 쓴 `tmp_path` 루트라 `rules.toml`이 없다(`add`는 `requires_approval`이라 첫 멈춤은 같되 모델이 다른 도구를 부르면 기본에서 멈춘다), 2527행 시험은 도구가 없다. 같은 절의 나머지 시험이 예시 규칙 파일로 그대로 지나간다는 문장도 손수 쓴 루트 둘에는 맞지 않는다.
- 유효 3. 프로브 59~67행의 모듈 수준 `ToolSpec(...)`은 묶음 B가 `server`를 필수로 더하면 `TypeError`로 시작도 못 한다(코드를 읽었다. 프로브는 게이트 밖이라 아무것도 빨개지지 않는다).
- 유효 4. 프로브 97~103행이 어떤 400이든 측정 "거부"로 센다. 이번 여섯 회차는 모두 수락이라 결론에 영향은 없고, 다시 돌리는 판에서 거짓 거부가 근거가 될 수 있다(`.claude/rules/probes.md` 첫 항목. `tools/probe_kit.py`의 `Rounds.round`가 예외를 삼켜 측정 아님으로 세므로 400 아닌 오류는 안전하다).
- 보류 5. 명세 "집행의 차례" 3(없는 이름의 거부)과 5(deny의 거부)가 재개한 실행에서 `run_resumed`를 언제 쓰는지 침묵한다. 지금 `_Context._call`은 결정을 꺼낸 뒤 `_resume()`(`RunResumed` 기록)을 부르고 멈춤·거부·호출로 간다. 구현이 3을 `_resume()` 앞의 조기 반환으로 지으면 `run_resumed` 없이 `tool_called(ok=false)`가 이어진다. `check_record_rules`와 ADR 0009의 `run_resumed` 위치 규칙을 읽어 판정한다.
- 밀 주장 여덟 가운데 여섯 일치. 깨진 운영자 파일의 문구에 자리(`agent.0`)와 `input_value`가 드는 것을 `_parse_operator_file`에 깨진 입력 둘을 넣어 봤고 작은 pydantic 모델로 `agents.calc.allow.1`·`agents.calc.deny.0`이 `input_value`와 함께 나오는 것을 봤다. `_require_paused_call`(1281~1287)과 `_call_safely`(558~599), `McpConnection({})`에 없는 이름으로 `call`을 부르면 `LookupError`의 문구가 `도구가 없다: nope`이고 `_call_safely`를 거치면 content가 `LookupError: 도구가 없다: nope`인 것, `tests/adapters/test_jsonl.py` 880·922행의 시험 이름 둘, 프로브 68행의 문구와 명세 123행, README 표와 입력 토큰 합 2214. 4번은 반만(폴더 넷은 맞고 전부가 틀림), 6번 인용 다섯은 ADR 0044 20행·`CONTEXT.md` 392행·ADR 0009 128행·`adapters.md` 18행이 일치하고 ADR 0042만 유효 1이다. 나열 밖에서 서두의 열여덟·마흔여덟, 프로브의 `ROOT`(`parents[3]`)와 `--env-file ../../../.env`도 맞았다.
- 따라가지 못한 것. plan.md·ADR 0044·ADR 0009의 diff(출력이 잘렸다), `tests/core/test_run.py`의 시험 이름 셋, `tests/adapters/test_mcp.py`의 시험 하나, `web/apps/widget/e2e/plugins.ts`, `EventItem.tsx`의 필드 이름 표, 프로브 독스트링의 `chat_models.py` 인용과 README의 라이브러리 판 번호. 일지는 기록 문서라 보지 않았다. 남긴 백그라운드 작업은 없다. 따라가지 못한 것 가운데 식별자의 실재와 `uv.lock`의 판 번호는 셀프 리뷰 표준 축이 이미 확인했다(위 "표준 축 보고" 확인된 것).

### 반영(버그·성능 축과 인용 경고)

지적마다 근거를 먼저 봤다. ADR 0042 42행, `tests/test_main.py`의 `-m llm` 시험 여섯(551·1024·2442·2527·2835·2854행)의 루트 만드는 줄과 `_write_plugin`(214행)·`_write_mcp_plugin`(224행)·`_copy_repo_plugins`(2802행), `src/agent_os/core/run.py`의 `_call`(558~599행. `_require_paused_call` → `_take_verdict` → `_resume` → 게이트 차례)과 `_resume`(617~622행), `check_record_rules`(`core/continuation.py` 377행. 요약 이벤트의 자리를 보는 규칙이라 `run_resumed`는 판정하지 않는다), 프로브 59~68행과 92~116행, `.claude/rules/probes.md` 첫 항목. 고친 것은 다음이고 새로 쓴 사실 문장은 원문으로 둔다.

1. 유효 1(ADR 0042 인용). 원문 42행은 굵은 머리 문장 뒤에 규칙 파일과 서버 파일이고로 이어져, 명세의 인용은 굵은 표시와 끝 조각만 달랐고 인용 대조 훅도 지나갔다. 그래도 굵은 머리 문장 "운영자 파일은 둘이 는다"만 인용하고 나머지는 괄호로 뺐다.
2. 유효 2(`-m llm` 시험). 전부를 하나로 좁히고 여섯의 루트를 가른 문장으로 바꿨다. 새 문장: "`_copy_repo_plugins`로 임시 루트를 만드는 하나(한도를 작게 적은 calc의 요약 시험)는 그 도우미가 저장소 `plugins/`에서 calc와 그것이 쓰는 플러그인 폴더 넷만 복사하므로 루트의 `rules.toml`이 따라가지 않는다", "`plugins/` 통째를 복사하는 하나(모델 이름을 바꾸는 시험)와 저장소 루트에서 바로 도는 하나(calc 이어 가기)는 저장소의 예시 파일을 쓰고, 도구 없는 에이전트(asker)의 하나는 게이트에 들지 않는다", "`gatedcalc`와 가짜 서버 `fixture`를 `_write_plugin`·`_write_mcp_plugin`으로 손수 쓰는 둘(CLI 재개, HTTP 승인)은 규칙 파일이 없어 `add`의 승인 요구에서 지금처럼 멈추되 모델이 다른 도구를 부르면 기본에서 멈추므로, 아래 채널·서버 테스트와 같은 꼴의 파일을 그 루트에도 둔다(묶음 D)". 묶음 D에 그 루트 둘의 규칙 파일을 더했다.
3. 유효 3(프로브의 `ToolSpec`). README 표의 다시 돌 때 칸에 묶음 B 뒤에는 `ADD`에 `server=`가 필요하다고 적고, 명세 "표와 키" 절의 `ToolSpec.server` 항목에 프로브의 `ADD`도 그 칸을 채운다고 적었다.
4. 유효 4(400 판정). 프로브의 except 갈래를 본문에 `tool`이 있을 때만 측정 거부로, 아니면 측정 아님으로 세게 고치고, 독스트링의 표지 문단과 README("측정 뒤 고친 것")에 측정 뒤의 고침이고 기록된 여섯 회차에 400이 없어 결과는 그대로라고 적었다. 다시 돌리지 않았다.
5. 보류 5(`run_resumed`). 지금 코드가 대조 뒤에 소비와 `run_resumed` 기록을 하고 그 뒤에 게이트로 가므로 명세 3에 그 차례를 적어 보류를 닫았다. 새 문장: "소비는 지금처럼 `run_resumed` 기록과 함께 2 바로 뒤이고, 이 거부와 5의 거부는 그 뒤에 온다(`_Context._call`의 `_take_verdict`와 `_resume`의 차례. 코드를 읽었다)".
6. 인용 경고 넷. 이 일지 92행은 고치기 전 문장을 옮긴 것이라 따옴표를 떼고 고치기 전이라 적었다. 이 일지 130행은 선택지 라벨이라 따옴표를 뗐다. 명세 159행은 포트 독스트링에 적을 제안 문장이라 따옴표를 뗐다. 명세 180행은 ADR 0044 28행의 문장 "deny인 도구는 모델에 붙이는 도구 목록에서 뺀다"로 바꿨다.

남긴 것은 없다. 서두의 수는 바뀌지 않았다(거부한 안을 더하거나 빼지 않았고 "명세가 정했다" 절도 그대로다).

### 보안 축 보고(`/security-review`)

내장 `/security-review`를 커밋 d13dd2fe 뒤에 돌렸다(origin/main이 57316a5d 그대로라 합치지 않았다. 그 명령이 모은 diff는 177.5KB라 파일로 저장됐다). 1단계 식별 서브태스크(general-purpose)가 바뀐 파일 일곱을 전문으로 읽고 명세가 인용한 지금 코드(`run.py`의 `_Context._call`·`_mask`·`_reject_masked_args`·`_require_paused_call`·`_call_safely`·`_describe`·`_reject_runtime_only`·`_reject_unknown_declarations`, `filesystem.py`의 `_parse_operator_file`·`_describe`, `adapters/anthropic.py`, `channel/http/items.py`의 `project`, `tools/probe_kit.py`)와 대 봤으며, `.scratch/approval-rules/` 아래를 비밀 패턴(`sk-ant`, `api_key=`, `token=`, `password`)으로 grep해 0건이고 `.env`가 `.gitignore`에 드는 것을 확인했다. 결과는 **No findings**다. 신뢰도 0.7 이상의 취약점이 없어 2단계(오탐 거르기 서브태스크)는 띄울 것이 없었다. 보고가 확인한 것: 프로브는 키 값을 읽거나 찍지 않고(`uv run --env-file`이 환경에만 넣고 `ChatAnthropic`이 스스로 읽는다) 출력은 400 본문 앞 300자·모델 이름·토큰 수·응답 글 80자뿐이며 `subprocess`·`eval`·파일 삭제·역직렬화가 없다. 명세의 집행은 fail-closed(기본 묻는다, deny → requires_approval → ask → allow, 재개에서 deny가 결정을 이김, allow는 서버를 붙인 두 꼴만)이고, 에이전트가 `rule`·`server`를 채운 이벤트를 내면 `run_failed(agent_code)`라 운영자 규칙 기록을 에이전트 코드가 위조할 수 없으며, `items.py`의 투영이 `run_failed`를 고정 문구로, `tool_called`를 이름·ok만 옮겨 거부 문구와 검사 문구에 든 서버·도구 이름이 위젯에 가지 않는다. 문턱 아래 참고 셋: 깨진 `rules.toml`의 500 문구가 pydantic 전문을 싣는 것은 `disabled.toml`과 같은 규약이라 새 노출이 아니다, 공통 표의 deny 오타가 `<서버>:*` allow 뒤에 숨는 길은 ADR 0044가 받아들인 잔여 위험이고 이 명세의 에이전트 표 검사가 그 길을 좁혔다, 예시 `plugins/rules.toml`의 `[agents.calc] allow = ["everything:*"]`는 지금 calc가 everything의 도구를 묻지 않고 도는 상태를 그대로 두는 것이라 새 공격면이 아니다. 고친 것은 없다.

### 둘째 커밋

반영 넷(명세, 프로브, 프로브 README, 이 일지)을 커밋 706f1c29 `docs: approval-rules 명세의 PR 직전 리뷰 지적 다섯과 인용 경고 넷을 반영한다`(파일 넷, +55/-14)로 넣었다. 커밋 전 손으로 친 것: 프로브에 `uv run ruff check`("All checks passed!")와 `uv run ruff format --check`("1 file already formatted"), 고친 마크다운 셋에 `tools/check_md_tables.py`와 `tools/check_line_separators.py`(둘 다 출력 없이 종료 0), `git branch --show-current`(`docs/approval-rules-spec`), `uv run python tools/sibling_overlap.py`("번호 겹침 없음". 함께 고친 파일: mcp-shutdown-spec 워크트리의 `.scratch/plan.md`). 프로브 독스트링의 넘친 줄(25행, 폭 101)은 PostToolUse 훅이 짚어 `tools/rewrap_comments.py`로 감았다. pre-commit은 첫 커밋과 같은 검사가 모두 Passed(parallel-checks 478.36초, pytest 339.0초, web-verify 478.0초)이고 canary specs·constitution version은 해당 파일이 없어 Skipped, 인용 대조는 파일 셋의 인용 아홉에 경고 없음이다.

## 인계(커밋 뒤)

둘째 커밋을 치자 인계 계기(`hook_handoff`, 세션 컨텍스트 295,712 토큰, 경계 "커밋 뒤")가 왔다. `handoff.md`를 Read로 열어 인계하지 않는 때 다섯을 대 봤다. 계기를 낸 명령은 성공했다(706f1c29). 이 세션의 범위는 병합까지라 커밋에서 끝나지 않는다. 이 세션을 연 지시문의 "이어받을 상태"는 `인계: 셀프 리뷰 직전`이라 지금의 경계와 다르다. 이 일지에 `인계 못함` 줄이 없다. `get_session`의 `self`에 `parentSessionId`가 없어 곁 세션이 아니다. 다섯 모두 아니라 넘긴다. 이 세션의 제목은 바꾸기 전 `docs/approval-rules-spec`이다. 멈출 백그라운드 작업은 없다(커밋 둘과 서브에이전트 둘은 끝났다). 주 체크아웃은 main이고 origin/main(57316a5d)과 같아 미갱신이 아니다.

넘기는 상태. 커밋 둘(d13dd2fe 명세, 706f1c29 PR 직전 리뷰 반영)이 로컬 브랜치에만 있고 푸시하지 않았으며 PR은 없다. 셀프 리뷰 반영, 사용자의 ADR 이력 다섯 승인, PR 직전 리뷰 둘은 끝났고 위 절들에 있다. `git-pr` 스킬은 이 세션이 Skill 도구로 실었으나 밟지 않았다(3단계 푸시 전). 남은 단계는 아래 지시문의 "이어받을 상태"에 있다. 이 절은 커밋하지 않은 채 넘기고 새 세션이 이어 쓰고 커밋한다.

```
다음 작업: 기능 approval-rules. 운영자의 승인 규칙 파일(후보 6) 명세의 산출물이 커밋 둘(d13dd2fe 명세, 706f1c29 PR 직전 리뷰 반영)로 워크트리 approval-rules-spec의 브랜치에 있다. 푸시·PR·봇 회차·병합과 일지 "다음"·다음 지시문·회고를 마친다
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec approval-rules
브랜치: docs/approval-rules-spec
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-05-10-approval-rules-spec.md의 "커밋과 PR 직전 리뷰" 절과 "인계(커밋 뒤)" 절(PR 본문의 체크리스트와 리뷰어 참고는 그 두 절로 채운다), .scratch/approval-rules/spec.md
이어받을 상태: 인계: 커밋 뒤. docs/journal/2026-11-05-10-approval-rules-spec.md. 커밋 둘이 로컬 브랜치에만 있고 아직 푸시하지 않았으며 PR은 없다(gh pr list --head docs/approval-rules-spec가 비었다). 셀프 리뷰 반영, 사용자의 ADR 이력 다섯 승인, PR 직전 리뷰 둘(bug-perf-review의 Minor 다섯 반영, /security-review는 No findings)은 끝났고 일지에 있다. 남은 단계는 차례로 git-pr 스킬로 푸시와 PR(docs/ 면제 PR, 티켓 없음. 사용자에게 묻지 않는다) → PR 연 직후 @coderabbitai review 코멘트와 merge.md 2(봇 회차) → 병합은 이 워크트리 사본의 next-session merge.md "워크트리에서 병합할 때"를 Read로 열어 따른다(.scratch/plan.md를 mcp-shutdown-spec 워크트리도 고쳐 글자 충돌 후보다) → 일지 "## 다음" 절과 next-session 지시문(다음은 명세 검토와 /to-tickets approval-rules, 사용자가 부른다) → retro. 측정은 끝났고 다시 돌리지 않는다. 사용자가 정할 것은 모두 정했고 다시 묻지 않는다. 일지의 "인계(커밋 뒤)" 절은 커밋하지 않은 채 넘긴다
확인할 선행 조건: 없음
이번 요청 범위: 명세까지
```

제목을 `docs/approval-rules-spec (인계함)`으로 바꿨다. 잠금 풀기(`git worktree unlock`)는 `is not locked`라 넘어갔다. open-session을 부른다 2026-11-05T13:32:43Z

## 새 세션(푸시부터)

위 지시문으로 연 새 세션이다(사용자 프롬프트는 그 지시문 그대로이고 open-session이 보냈다. 원문은 위 "인계(커밋 뒤)" 절의 코드 블록). 제목을 `docs/approval-rules-spec`으로 바꿨다(앱이 묻지 않고 바꿨다). 지시문의 선행 조건이 없음이라 tidy-checkouts는 돌지 않았고, `git worktree list`에서 브랜치가 체크아웃된 자리를 찾아 `EnterWorktree(path)`로 이 워크트리에 들어왔다. 브랜치는 `docs/approval-rules-spec`, 머리는 706f1c29이고 커밋하지 않은 변경은 이 일지뿐이다(위 "인계(커밋 뒤)" 절). `git fetch origin` 뒤 origin/main은 57316a5d 그대로라 합칠 것이 없었다.

git-pr 스킬을 Skill 도구로 실었다. 지시문대로 스킬의 확인 단계(6단계)는 밟지 않았다. `git push -u origin docs/approval-rules-spec`으로 커밋 둘(d13dd2fe, 706f1c29)을 푸시했고, PR #471 `docs: approval-rules 명세를 쓰고 ADR 0044·0009 이력 다섯에 고른 셋과 정한 것을 남긴다`를 열었다(docs/ 면제 PR, 티켓 없음. 본문은 PR #469의 본문을 본보기로 템플릿을 채웠고, 체크리스트와 리뷰어 참고는 이 일지의 "커밋과 PR 직전 리뷰"·"인계(커밋 뒤)" 절로 채웠다. 본문은 파일로 써서 `--body-file`로 넘겼다). 앱의 PR 바가 #471을 스스로 묶었다(`get_status`: bound, 열 때 검사 pending 6·passing 1·skipped 1, `MERGEABLE`·`BLOCKED`). `@coderabbitai review` 코멘트는 남기지 않았다(아래 인계. handoff.md 3의 `PR 연 뒤` 줄대로 새 세션이 남긴다).

## 인계(PR 연 뒤)

PR을 열자 인계 계기(`hook_handoff`, 세션 컨텍스트 228,112 토큰, 경계 "PR 연 뒤")가 왔고 `hook_pr_next_session`의 계기도 함께 왔다. `handoff.md`를 Read로 열어 인계하지 않는 때 다섯을 대 봤다. 계기를 낸 명령은 성공했다(#471). 이 세션의 범위는 병합까지라 PR 연 뒤에서 끝나지 않는다. 이 세션을 연 지시문의 "이어받을 상태"는 `인계: 커밋 뒤`라 지금의 경계와 다르다. 이 일지에 `인계 못함` 줄이 없다. `get_session`의 `self`에 `parentSessionId`가 없어 곁 세션이 아니다. 다섯 모두 아니라 넘긴다. 이 세션의 제목은 바꾸기 전 `docs/approval-rules-spec`이다. 멈출 백그라운드 작업은 없다(`wait_ci.py`는 띄우지 않았다). 주 체크아웃은 main이고 origin/main(57316a5d)과 같아 미갱신이 아니다. 이 세션이 번복하거나 고친 결정은 없다.

넘기는 상태. PR #471이 열려 있고 HEAD 706f1c29가 PR head와 같다. 봇 회차(`merge.md` 2)는 시작하지 않았다. 이 일지의 "인계(커밋 뒤)" 절부터는 커밋하지 않았고 새 세션이 이어 쓰고 커밋한다.

```
다음 작업: 기능 approval-rules. 운영자의 승인 규칙 파일(후보 6) 명세의 PR #471(브랜치 docs/approval-rules-spec, 커밋 d13dd2fe 명세·706f1c29 PR 직전 리뷰 반영)이 열려 있다. 봇 회차·병합과 일지 "다음"·다음 지시문·회고를 마친다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec approval-rules
브랜치: docs/approval-rules-spec
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-05-10-approval-rules-spec.md의 "인계(PR 연 뒤)" 절과 "커밋과 PR 직전 리뷰" 절, PR #471 본문(gh pr view 471), .scratch/approval-rules/spec.md(봇 지적을 반영하면 서두의 수를 다시 센다, to-spec 3)
이어받을 상태: 인계: PR 연 뒤. docs/journal/2026-11-05-10-approval-rules-spec.md. merge.md 2(봇 회차)부터 한다. 첫 @coderabbitai review 코멘트도 새 세션이 남긴다. PR #471은 docs/ 면제 PR(티켓 없음)이고 열 때 검사는 pending이었으며 앱의 PR 바가 묶었다. 일지의 "인계(커밋 뒤)" 절부터는 커밋하지 않았다. 새 세션이 이어 쓰고 봇 회차 뒤 "## 다음" 절과 회고까지 마친 일지를 커밋해 병합 전에 푸시한다(merge.md 3. 그 푸시로 도는 리뷰도 회차로 센다). 셀프 리뷰 반영, 사용자의 ADR 이력 다섯 승인, PR 직전 리뷰 둘은 끝났고 PR 본문 체크리스트와 일지에 있다. 병합은 이 워크트리 사본의 next-session merge.md "워크트리에서 병합할 때"를 Read로 열어 따른다(.scratch/plan.md를 mcp-shutdown-spec 워크트리도 고쳐 글자 충돌 후보다). 다음 지시문은 명세 검토(spec-reviewer)와 /to-tickets approval-rules(사용자가 부른다). 측정은 끝났고 다시 돌리지 않는다. 사용자가 정할 것은 모두 정했고 다시 묻지 않는다
확인할 선행 조건: 없음
이번 요청 범위: 명세까지
```

제목을 `docs/approval-rules-spec (인계함)`으로 바꿨다(앱이 묻지 않고 바꿨다). 잠금 풀기(`git worktree unlock`)는 `is not locked`라 넘어갔다. open-session을 부른다 2026-11-05T13:42:53Z

## 새 세션(봇 회차·병합)

위 지시문으로 연 세션이다(사용자 프롬프트는 그 지시문 그대로이고 open-session이 보냈다. 원문은 위 "인계(PR 연 뒤)" 절의 코드 블록). 제목을 `docs/approval-rules-spec`으로 바꿨고(앱이 묻지 않고 바꿨다) `git worktree list`에서 브랜치가 체크아웃된 자리를 찾아 `EnterWorktree(path)`로 이 워크트리에 들어왔다. 지시문의 선행 조건이 없음이라 tidy-checkouts는 돌지 않았다. 브랜치는 `docs/approval-rules-spec`, 머리는 706f1c29이고 PR 471은 OPEN, `MERGEABLE`이었다. 시작 프롬프트 `/to-spec approval-rules`는 명세가 이미 서 있어 스킬을 다시 돌지 않았다. 지시문대로 봇 회차부터 했다.

## 봇 회차

헤드 706f1c29에서 `@coderabbitai review` 코멘트를 남기고 상태를 한 번 읽으니 검사 넷이 pending이라 `tools/wait_ci.py 471`을 백그라운드로 띄웠다. 끝 줄은 모두 통과였다(CodeRabbit, claude-review, e2e, e2e-widget, python, ticket, verify, visual, web).

- **claude-review.** 지적 없음. 읽은 코멘트는 한 건이고 선택 칸 세 개가 형식 3 그대로라는 서술과 `read_rules()`가 포트 다섯을 늘리지 않는다는 서술을 `sdk.md`·`disabled.toml` 선례와 맞춰 확인했다고 적었다.
- **CodeRabbit 첫 회차(인라인 일곱, Major 1과 Minor 6).** 첫 회차라 지적마다 판단했다. 근거는 명세와 ADR 0044, 코드(`adapters/mcp.py`의 `connect`)를 읽은 것이다(코드를 읽었다).
  - 명세 집행의 차례 7 Major: 반영했다. 7번이 allow면 그냥 부른다로만 적어, 멈춘 사이 ask가 allow로 바뀐 재개에서 승인자의 거부가 무시되는 길이 있었다. 명세 "결정이 적용된 호출의 적용 규칙"(ask가 allow로 바뀌어도 결정을 그대로 적용하고 칸은 멈춘 까닭)과 ADR 0044의 재개 항목(그 밖의 변화는 지금 규칙대로 결정을 적용한다)에 어긋난 진짜 모순이었다. 7번을 결정이 없을 때만 그냥 부르고 있으면 6과 같이 적용하는 문장으로 고쳤다.
  - 명세 에이전트 표 이름 거부한 안(76행 아래) Minor: 반영했다. 이름이 틀린 표는 어느 실행에도 걸리지 않아 해가 없다는 문장이 deny에는 거짓이었다. allow의 오타는 기본이 묻는다 덕에 뜻밖에 묻는 데서 그치고, deny의 오타는 조용히 효력이 없어 같은 도구에 맞는 공통 allow가 있으면 묻지 않고 돈다. 에이전트 표 검사도 그 에이전트가 돌 때만 돌아 표 이름의 오타는 닫지 못한다. 결정은 바꾸지 않았고 거짓이던 근거 문장만 ADR 0044 "모양"의 잔여 위험과 맞췄다.
  - 명세 같은 이름 검사(158행) Minor: 반영했다. 모으기를 둘째 겹침에서 멈추면서 서버가 셋 이상이면 모두 나열한다는 두 문장이 어긋났다. 코드는 서버를 매니페스트 순서로 하나씩 열며 모으므로 겹친 서버 뒤의 서버는 열리지 않는다. 문구를 처음 겹친 두 서버만 싣는 쪽으로 맞추고, 끝까지 모아 던지는 쪽은 실패할 연결을 모든 서버까지 여는 값을 치른다고 적었다. 봇이 고르라 한 두 길 가운데 코드가 이미 가는 쪽이다.
  - 명세 묶음 C·D 순서(201행) Minor: 반영했다. C가 기본이 묻는다를 집행하면 규칙 파일이 없는 기존 시험이 멈추는데, 규칙 파일은 D에 있어 묶음마다 혼자 초록이라는 명세 자신의 조건과 어긋났다. 봇은 `-m llm`만 말했지만 위젯 e2e와 파일시스템 루트를 만드는 테스트도 같은 모양이다. 어느 시험이 멈추는지는 PR 본문이 이미 구현 티켓이 센다고 적었으므로, C 티켓이 멈추는 시험의 규칙 파일을 같은 티켓에서 두고 D는 나머지를 맡는다고 묶음 절에 적었다. 티켓을 어떻게 쪼갤지의 결정이 아니라 명세의 조건을 지키게 하는 문장이다.
  - 프로브 독스트링(31행) Minor: 반영했다. 프로브가 판정을 돌리기 전에 적었다고 밝히면서 `.claude/rules/probes.md`가 요구하는 고정 절과 내용 해시 대조를 두지 않았다. 판정 정의(모집단, 결과 변수, 측정인 회차, 판정, 판정하지 않는 것)를 `DEFINITION` 한 절로 모으고 `DEFINITION_SHA256`을 고정해 돌릴 때 대조하게 했다(`ast`로 값을 뽑아 해시를 계산했고 고정값과 같다). 해시는 400 조건을 좁힌 뒤의 현재 판이라 돌리기 전의 원래 글자와 같지 않다는 것, 해시는 앞으로의 몰래 바꿈만 막는다는 것을 프로브 README의 "판정 정의의 고정"에 적었다. 프로브를 다시 돌리지 않았다.
  - 프로브 400 문구(105행) Minor: 보류했다. 도구 문구(`tool`)가 다른 도구 관련 400에도 나 표지가 못 된다는 지적은 맞다. 다만 도구 정의 없음의 실제 거부 본문을 한 번도 관찰하지 못해(여섯 회차 모두 수락) 더 좁은 문구를 고를 근거가 없다. 문구를 짐작으로 좁히면 거짓 표지가 된다. 판정 절에 잠정 표지라 적고 400이 나면 본문을 사람이 읽고 가른다고 못 박았다. 400이 나는 판에서 본문을 보고 고른다.
  - 프로브 수락 회차의 요청 본문(110행) Minor: 보류했다. 수락 표지가 응답의 모델 이름뿐이라 블록이 드롭된 요청도 측정으로 센다는 지적이다. 셀프 리뷰 표준 축이 같은 지적을 냈고 그때 보류한 이유 그대로다. 프로브가 재는 것은 API의 수락이고 명세의 처리(모두 deny인 재개에 처리를 따로 두지 않는다)는 수락만 기대한다. 블록이 모델에 갔는지는 README가 되울림과 토큰 크기로 가른 둘째 물음이다. 요청 본문을 가로채는 일은 langchain 내부 호출을 건드려 크고, 실제 재개 길의 `run_finished`는 구현 티켓의 `-m llm` 시험이 잰다.
- 보류한 일 가운데 뒤의 작업으로 넘기는 것은 없다. 위 둘은 구현 티켓의 `-m llm` 시험이 실제 재개 길로 다시 재는 일의 안에 있고 PR 본문의 남긴 위험에 이미 적혀 있다.
- 반영 뒤 손으로 친 것: 프로브 `uv run ruff check`(All checks passed!)와 `uv run ruff format --check`(1 file already formatted), 명세와 README에 `tools/check_md_tables.py`·`tools/check_line_separators.py`(둘 다 출력 없이 종료 0). 서두의 수를 Grep으로 다시 셌다. `^### .*명세가 정했다` 18줄, `거부했다.` 48번이고 이번 반영은 문장 안을 고쳤을 뿐 표시를 더하거나 빼지 않아 열여덟·마흔여덟 그대로다(넘겨받은 것 열둘, 사용자가 고른 것 넷, 이력 다섯도 그대로).
- PR 본문의 남긴 위험 두 자리(프로브 해시, 묶음 C가 멈추는 시험의 규칙 파일을 가져가는 것)를 푸시 전에 `gh pr edit`으로 고쳤다. 푸시 뒤에 보류 둘의 이유를 PR 코멘트로 남긴다.

## 회고

후보 넷, 승인 2, 기각 2, 넘김 0.

- **승인: 새 프로브가 판정을 돌리기 전에 적었다고 하면서 `probes.md`의 사전 등록 항목(판정 정의 전부를 해시로 고정한 절에 두고 판정 스크립트가 대 본다)을 어겼다.** 사건: 첫 커밋의 프로브 독스트링이 판정을 해시 절 없이 산문으로 적었고, 셀프 리뷰 두 축과 PR 직전 리뷰 둘이 지나갔으며 PR 봇이 처음 짚었다. 층: 이 항목을 `tools/hook_scratch_probe_rule.py`의 훅으로 올리는 처방이 대기열 426에 이미 열려 있어 그 행을 잇는다. 되돌림: 행에 회차를 더하는 것은 PR 하나로 되돌린다. 간 자리: 대기열 426에 3회차를 더했다(336의 3회차). 426은 이제 회차 3 이상이고, 같은 훅을 고치는 430(9회차)이 이미 chore 계기다. 이 사건은 `.scratch/approval-rules/probes/`의 저장소 프로브라 훅이 지금 보는 세션 스크래치패드 스크립트 밖이라는 점이 새 정보다. 426의 처방이 사전 등록 절을 쓰는 문서에도 그 항목이 닿게 할지 함께 보도록 이미 적혀 있어, 반영 때 저장소 프로브의 독스트링도 대상에 넣는다.
- **승인: CodeRabbit 인라인 코멘트가 한 건마다 분석 스크립트 출력과 AI 프롬프트 블록을 달고 와서 일곱 건을 읽는 데 약 24K자가 컨텍스트에 실렸다.** 사건: `gh api`로 읽은 본문 전체가 10.6K자, 걸러도 본문 3200자씩 13.7K자였다. 판단에는 심각도, 파일:줄, 첫 단락, 제안 diff면 충분했다. 층: 도구(요약 출력기)다. 되돌림: 새 도구 하나라 PR 하나로 되돌린다. 간 자리: 대기열 573(새 행, 1회차). 새 도구라 문턱은 세 번째 반복이고 그 전에는 회차를 센다. 찾기는 `queue_open_rows.py --search coderabbit --search 인라인.코멘트 --search Script.executed`로 했고 같은 일을 다룬 행이 없었다.
- **기각: 명세 안의 모순(집행의 차례 7번과 138행)을 셀프 리뷰 두 축과 PR 직전 리뷰가 놓치고 PR 봇이 짚었다.** 같은 모양의 사건이 이 저장소에서 쌓인 행이 없고 명세 모순은 명세마다 자리가 달라 검사로 옮길 층이 없다. 판단 기준으로 올릴 사건 수도 못 채웠다. 다음 단계가 명세 검토(`spec-reviewer`)라 같은 종류의 결함을 한 번 더 거른다.
- **기각: DEFINITION 문자열의 줄이 ruff의 폭 100을 넘었다.** 편집 직후 훅이 그 자리에서 네 줄을 알렸고 바로 감았다.
- 만료: `tools/queue_open_rows.py`가 만료할 행 없음을 냈다. 워크트리에서는 `--ref origin/main`을 한 번 더 돌고 두 출력에 모두 든 행만 닫는다고 정해 두었으나, 첫 출력에 없으니 둘의 교집합도 비어 둘째를 돌리지 않았다.

## 다음

- 명세 검토(`spec-reviewer`)와 `/to-tickets approval-rules`(둘 다 사용자가 부른다). 명세는 ready-for-agent이고 PR 471로 병합되며, 서두의 수는 열둘·넷·열여덟·다섯·마흔여덟이다. 티켓을 쪼갤 때 묶음 A → C, B → C, C → D의 의존을 따르고, C 티켓은 기본이 묻는다가 서면 멈추는 기존 시험(`-m llm`의 calc 시험, 위젯 e2e 꾸러미, 파일시스템 루트를 만드는 테스트)의 규칙 파일을 같은 티켓에서 둔다(명세 묶음 절, 봇 첫 회차 뒤에 더했다).
- 구현 티켓이 `.claude/rules/core.md` 재개 항목, `.claude/rules/sdk.md` 선택 필드 항목, 포트 표 두 행과 `adapters.md`의 운영자 파일·MCP 항목을 코드와 같은 티켓에서 고친다(명세 묶음 A·B·C).
- 실제 재개 길이 `run_finished`로 끝나는지는 재지 않았다. 구현 티켓의 `-m llm` 시험이 잰다(PR 본문 남긴 위험).
- 프로브를 다시 돌린다면 400이 나는 판에서 본문 앞 300자를 사람이 읽고 도구 문구 표지를 다듬는다(프로브 README).
- 대기열 426(3회차)과 430(9회차)은 같은 훅을 고치는 chore 계기다. 저장소 프로브의 사전 등록 독스트링도 그 처방 대상에 넣는다.
- 병합 뒤 상태(주 체크아웃 미갱신 한 줄, 원격 브랜치 정리 결과)는 병합한 세션의 보고와 다음 지시문의 이어받을 상태에 있다.

