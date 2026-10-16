# 04: 세션 시작 훅 — 계정을 장부에 남기고 새 요약을 한 번 보인다

**What to build:** 이 저장소에서 세션이 시작되거나 이어지거나 갈라질 때마다, 새 훅 `hook_session_usage`가 그 세션의 계정(계정 ID와 이메일)을 사용량 장부의 계정 기록에 한 줄 남긴다. 그래서 보고서가 합계와 함께 계정별 내역을 낸다. 새 일간 보고서가 생긴 뒤 사람이 처음 세션을 열면 `summary.txt`의 요약 몇 줄이 사람에게만 보인다. 같은 보고서로는 다시 보이지 않고, 보고서가 36시간 넘게 갱신되지 않았으면 그 사실이 맨 앞에 붙어 하루 한 번 보인다. 카나리아 같은 헤드리스 세션은 요약의 몫을 가져가지 않는다.

근거는 `.scratch/token-usage/spec.md`의 "세션 시작 훅"(훅, 계정 기록, 요약, 헤드리스 세션, 자리, 못 보는 것), "사용량 장부와 보고서 도구"의 계정 기록의 줄, Testing Decisions의 훅 항목이다. 요약을 보이는 때는 ADR 0033 이력 2026-10-16 "요약은 새 보고서 뒤 처음 시작한 세션에 보이고 클라우드 세션은 인계하지 않는다"다.

**Blocked by:** 01(러너가 `notice`를 받는다), 02(장부의 자리와 `summary.txt`, 계정 기록을 읽는 쪽)

**Status:** ready-for-agent

### 훅

- [ ] SessionStart에 매처 `startup|resume|clear|compact|fork`로 래퍼 모양 등록을 더한다(`tools/run_hooks.py`의 `REGISTRATION`)
- [ ] 매번 계정 기록(`ledger/accounts.jsonl`)에 명세 "계정 기록의 줄"의 모양 그대로 한 줄을 덧붙인다. 계정은 `~/.claude.json`의 `oauthAccount.accountUuid`와 `oauthAccount.emailAddress`이고, 읽지 못하면 두 칸이 `null`이다. 그 파일의 다른 키는 출력하지도 장부에 남기지도 않는다(대기열 272)
- [ ] 출력 폴더는 `CLAUDE_PROJECT_DIR`의 git 공용 디렉터리의 부모(주 체크아웃) 아래다. 워크트리에서 시작한 세션도 같은 곳에 쓴다
- [ ] 요약은 `source`가 `startup`이고 요약의 보고서 날짜를 이름으로 한 표지 파일을 `O_EXCL`로 처음 만들었을 때만 `systemMessage`로 보인다. 보고서 날짜는 `summary.txt`의 첫 줄 `보고서 날짜: YYYY-MM-DD`에서 읽는다(명세 "요약 파일". 쓰는 쪽은 02다). 그 줄을 읽지 못하면 요약을 보이지 않는다. `summary.txt`의 수정 시각이 36시간보다 오래됐으면 앞줄을 붙이고 표지 이름에 지역 날짜를 더한다. `summary.txt`가 없으면 침묵이다. 판정은 지금 시각을 인자로 받는 순수 함수다
- [ ] 헤드리스 세션을 가른다. 먼저 실제 대화형 세션과 `claude -p` 세션의 SessionStart 페이로드를 저장해 가를 칸이 있는지 본다(저장한 원본은 `.scratch/token-usage/probes/`에 커밋한다, `.claude/rules/probes.md`). 칸이 없으면 `tools/canary.py`가 띄우는 세션의 환경에 표지 변수를 주고, 훅은 그 변수가 있으면 요약의 표지를 만들지 않고 계정만 기록한다. 카나리아 밖의 `claude -p`는 못 보는 것이다
- [ ] 독스트링에 무엇을 보고 무엇을 못 보는지 적고, 못 보는 것마다 시험으로 고정한다(`.claude/rules/tools.md`). 세션 도중의 계정 바꾸기, 이 저장소 밖에서 연 세션, 카나리아 밖의 헤드리스 세션이다

### 시험과 실행 확인

- [ ] 명세 Testing Decisions의 세션 시작 훅 항목을 시험으로 고정한다. 줄의 모양, `fork`의 계정, 같은 보고서 날짜의 둘째 `startup`은 침묵, 05:00 전에 연 세션이 있었어도 새 요약 뒤의 다음 `startup`은 보임, 낡은 요약의 앞줄과 하루 한 번, 요약 파일이 없으면 침묵, 헤드리스 표지, 두 키 밖을 출력하지 않음이다. 선례는 `tests/tools/test_hook_session_web_deps.py`다
- [ ] 끝에서 끝까지 하나를 둔다. 훅이 쓴 줄을 `tools/token_report.py`가 읽어 그 세션의 비용이 계정별 절에 그 이메일로 든다
- [ ] `tools/hook_payloads.toml`에 발동(`notice`) 하나와 침묵 하나를 실제 입력으로 더한다. 사례는 `CLAUDE_PROJECT_DIR`을 임시 저장소 자리표시자로, 홈(`USERPROFILE`·`HOME`)을 `.claude.json`을 둔 임시 폴더로 줘 실제 장부와 표지에 닿지 않게 한다. 필요한 자리표시자를 러너에 더하고, 러너 독스트링의 자리표시자 목록과 수를 고친다(선례 `${BROKEN_WEB}`)
- [ ] `tools/mutate.py`로 표지 판정과 계정 고르기를 바꾸면 시험이 빨개지는지 본다
- [ ] SessionStart에서 훅이 쓰는 시간을 재서 `.claude/rules/tools.md`의 시간 목록에 더한다. 그 rules를 고치면 그것을 원천으로 든 카나리아 가운데 바뀐 문장에 닿는 것을 돌려 결과 줄을 고친다(`tools/sibling_overlap.py`가 본다)
- [ ] `KICKOFF.md` 7단계의 `.claude/settings.json` 항목에 이 등록은 새 프로젝트에 복사하지 않는다고 적고, 그 항목이 늘어놓은 SessionStart 매처를 맞춘다(명세 Out of Scope)
- [ ] `CLAUDE.md`의 검증 명령이 모두 초록이다

### 받는 쪽

- [ ] 계정을 바꾸면 `~/.claude.json`이 바로 바뀌는지와 `systemMessage`가 세션 컨텍스트에 들지 않는지는 이 훅이 주 체크아웃에서 돌고 새 요약이 생겨야 잴 수 있어 09가 본다(명세 "적용 뒤 확인")

### 이 티켓이 정할 것

1. 헤드리스 세션을 가르는 길(페이로드의 칸인지 카나리아의 표지 변수인지)과 그 근거
2. 표지 파일의 이름과 자리
