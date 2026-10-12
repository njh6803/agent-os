# 2026-10-12 (18) 버그·성능 리뷰가 남긴 백그라운드 작업을 멈추고, PR 직전 리뷰의 유효 지적을 고치는 값으로 가른다

next-session 지시문으로 연 새 세션의 하네스 chore다. 대기열 188·190을 닫는다. 세션은 주 체크아웃에서 열렸고,
지시문대로 `tidy-checkouts`를 먼저 돈 뒤 `EnterWorktree(name=perf-review-background-and-triage)`로 들어가
`origin/main`(`0661d72`)에서 `chore/perf-review-background-and-triage`를 땄다. 순번은 18이다. PR #186이 13을,
PR #187이 16을, 형제 워크트리 `canary-precheck`가 커밋하지 않은 17을 쥐고 있었다(그 워크트리의 `docs/journal/`을
읽었다).

## 계기

> 사용자: "대기열 188·190을 한 chore PR로 반영한다. 둘 다 PR 직전 버그·성능 축이고 190은 2회차다"

## 첫 턴의 tidy-checkouts

- **루트.** main이고 깨끗했다. `a76107e`에서 `0661d72`(PR #184)로 당겼다. 당긴 커밋이 이 스킬 파일(3의 판정 3
  요약)을 바꿔, 스킬 지시대로 새 사본을 Read로 열고 3부터 그 판을 따랐다.
- **지운 것.** 없다. `지운다` 판정이 하나도 나오지 않았다.
- **남긴 것.** 잠금 pid가 살아 있는 여덟, 작업 디렉터리로 쥔 `claude.exe`가 있는 둘(`review-workflow-guards` pid
  61148, `rewrap-and-separator-hook` pid 60020. PR #184가 판정 3에 들인 갈래다), 병합된 PR이 없는 넷,
  다시 만들 수 없는 `grep.exe.stackdump`가 든 `canary-spec-pipeline-followup`, 병합된 PR이 없는 로컬 브랜치
  스물.
- **사람에게 넘긴 것.** prunable 하나(`05-admin-hides-decision-for-end-user`), 분리 HEAD 셋, PR 머리가 다른
  `skill-check-and-retro-section`, 등록 없는 폴더 여섯, 실행 중인 세션 `docs/admin-style-spec`의 제목이 체크아웃된
  어느 브랜치와도 맞지 않아 보류된 `spec-pipeline-and-pytest-ids`. 지시문대로 답을 기다리지 않았다.

## 188: 무엇이 남았나

행은 "`bug-perf-review`가 띄운 백그라운드 재현"이라 적었다. 일지 15 세션의 서브에이전트 기록
(`agent-a99e8d7e4edecc6e0.jsonl`, meta의 `agentType`이 `bug-perf-review`)을 스크래치 스크립트로 읽었다.

- 리뷰어는 `run_in_background`를 한 번도 쓰지 않았다. 도구 호출 51번 가운데 Bash가 34번이었다.
- 압력 시험 `uv run python …/p3.py`를 `timeout: 300000`으로 쳤고, 결과는 "Command did not complete within its 300s
  timeout and was moved to the background (ID: bq0cfb3rc)"였다. Bash 도구는 시간 제한을 넘긴 명령을 죽이지 않고
  백그라운드로 옮긴다.
- 리뷰어는 그 출력 파일을 한 번 읽고 다른 프로브로 넘어갔고, 보고를 낸 뒤 "stopped by main session" 알림을 받았다.
- 정의의 도구는 Bash, Read, Grep, Glob이라 `TaskStop`이 없었다. "멈춘다" 한 줄만 더하면 작업 ID로 멈출 도구가
  없는 지시가 된다(Bash로 프로세스를 찾아 죽이는 길은 재지 않았다).

그래서 보고 형식 절에 문단 하나를 더하고 `tools`에 `TaskStop`을 더했다. 문단은 `run_in_background`를 쓰지
않았어도 남는다는 것을 적는다. 사건의 리뷰어가 그 경우였다.

## 188을 잰 것

카나리아 러너의 agent 판정은 서브에이전트가 도구를 쓰면 실패로 보므로(`tools/canary.py` 독스트링), 멈추는
행동은 재지 못한다. 프로브 `.scratch/harness/probes/subagent_task_stop.py`를 새로 지었다. 실험군은 이
워크트리(새 정의), 대조군은 주 체크아웃(`0661d72`의 옛 정의)이고, 두 갈래 모두 본 세션의 `--tools`가
`Agent,Bash,Read,Grep,Glob,TaskStop`이라 다른 것은 정의뿐이다. 서브에이전트에게는 120초 걸리는 명령을 시간 제한
3초로 한 번 치고 보고하게 했다. claude 2.1.296.

- **첫 실행.** 네 회차 모두 Bash가 "This command requires approval"로 막혀 명령이 돌지 않았다. `-p`에는 승인할
  사람이 없고 프로젝트 설정에 허용 규칙이 없다. 측정은 아니었지만, 실험군 셋만 답에서 `TaskStop`과 "Bash가
  백그라운드로 옮긴 작업"을 말하고 대조군은 말하지 않아 새 정의가 실린 것은 보였다. 그 판의 프로브는 이 회차들을
  측정 아님으로 거르지 못하고 0으로 끝났다(셀프 리뷰가 잡았다, 아래).
- **둘째 실행.** 그 명령 하나를 `--allowed-tools`로 허용했다. 네 회차 모두 Bash가 "did not complete within its 3s
  timeout and was moved to the background"를 냈다. 실험군 셋은 모두 그 ID로 `TaskStop`을 불러 "Successfully stopped
  task"를 받았다. 대조군은 멈추지 않고 보고했다. 일지 15의 사건이 대조군에서 그대로 났다. 다만 질문이 "보고
  형식 절대로"와 "보고 전에 한 일을 적는다"로 서브에이전트를 이끌었다(두 리뷰 축이 짚었다).
- **셋째 실행(지금 판).** 그 두 구절을 빼고 "그다음 보고하라"만 남겼다. 회차는 서브에이전트의 Bash 결과에 "moved to
  the background"가 있어야 측정으로 센다. 네 회차 모두 측정이었고, 실험군 셋은 모두 `TaskStop`을 불렀고 대조군은
  부르지 않았다. 대조군은 문단과 도구가 함께 달라 무엇이 멈추게 했는지는 가르지 못한다.
- 169의 카나리아 명세 `bug_perf_review_budget.toml`은 러너의 `agent_problems`가 실험군 정의의 `tools`와
  `agent_tools`가 같은 집합인지 보므로 `TaskStop`을 더했다. 대조군인 주 체크아웃에 169 문단이 이미 병합되어 있어
  그대로는 다시 돌릴 수 없다. 그래서 `agent_problems`만 불러 고친 명세는 문제 0, 고치기 전 명세는 "정의의 tools …
  가 agent_tools … 와 다르다"인 것을 봤다.

## 190

리뷰 파이프라인 2의 "트리아지(유효·오탐·보류)만 하고 수정은 본 세션이 한다" 바로 뒤에 두었다. 행의 "어디로"는
"2(대체 둘)의 트리아지"였지만, CLI의 `coderabbit-review`와 대체 둘이 같은 트리아지를 쓰므로 2의 본문에 두면
양쪽에 걸린다. 일지 08의 사례는 PR 직전 리뷰가 `보류`로 판정한 Nit였으므로 `보류` 판정도 넣었다(명세 축이
짚었다). 두는 지적은 판정과 고치는 값을 PR 체크리스트의 그 줄에 적는다. 비용은 일지 14만 푸시·CI·변이를 적었고
08의 회차는 다른 Minor도 함께 고친 푸시라 가를 수 없어, "PR을 연 뒤에 고치면 푸시와 CI가 한 바퀴 더 돈다"는 구조의
사실로 좁혔다. 헌법 문구 수정이라 patch다. 3.0.25로 올렸다가 `tools/sibling_overlap.py`가 형제 워크트리
`canary-precheck`(커밋 `620b80d`)의 3.0.25와 겹친다고 알려 3.0.26으로 비켰다. 처음 돌린 그 도구는 버전을 올리기
전이라 "이 브랜치의 새 번호 없음"만 냈다.

## 바꾼 것

- `.claude/agents/bug-perf-review.md`(188): `tools`에 `TaskStop`, 보고 형식 절의 둘째 문단.
- `docs/constitution/operations.md`(190): 리뷰 파이프라인 2의 문장 넷. `docs/constitution/README.md` 3.0.26.
- `.scratch/harness/probes/subagent_task_stop.py`(새로)와 프로브 README의 행, 카나리아 명세
  `bug_perf_review_budget.toml`의 `agent_tools`와 머리 주석, `tools/canary.py`의 `tools_for` 독스트링(부분집합
  구성을 이 프로브의 대조군이 봤다).
- `.scratch/retro-queue.md`: 188·190을 닫았다.

## 잔존 grep

`도구 넷`, `Bash, Read, Grep, Glob`, `"Bash", "Read", "Grep", "Glob"]`를 `.claude/`·헌법·`tools/`·프로브·`KICKOFF.md`에서
찾았다. 남은 것은 `coderabbit-review`의 `tools` 줄, `KICKOFF.md`의 GitHub MCP PR 도구 넷, `operations.md` 환경 규약
상세와 `tools/canary.py`의 `tools_for`가 적은 2026-10-12-02의 측정(그때의 구성)이라 고치지 않았다. `KICKOFF.md`와
`README.md`의 "모두 Edit·Write 없음", "모두 수정 없음"은 `TaskStop`을 더해도 참이다.

## 셀프 리뷰

`/code-review`, 기준 `0661d72`, 바뀐 파일 여섯과 미추적 하나(프로브), 커밋 0. 소스 파일이 없어 두 축 모두
sonnet으로 돌렸다. 명세는 사용자 요청과 대기열 두 행이고, 이 세션이 한 것(도구 추가, 프로브, 카나리아 명세,
3.0.26)은 리뷰어 참고로 갈라 넘겼다. 표준 축은 Minor 6·Nit 4, 명세 축은 Minor 2·Nit 5였고 Critical·Major는
없었다. 고치는 값이 모두 작아 판단 항목까지 거의 다 고쳤다(190의 문장대로다).

- **고친 것.**
  - [명세 Minor] 프로브 독스트링이 "앞쪽 실행의 stream-json은 서브에이전트의 도구 호출을 싣지 않는다"며 디스크
    기록을 읽었다. 틀렸다. 저장한 원본에 서브에이전트의 `TaskStop` 호출이 `parent_tool_use_id`와 함께 있었다(grep으로
    봤다). 앞쪽 실행에서 빠지는 것은 마지막 글이다(일지 02가 좁힌 문장). 프로브를 stream-json만 읽게 다시 썼고,
    앞 실행 둘의 원본에 대 보니 디스크 기록과 같은 결과였다.
  - [표준 Minor] 프로브가 전제("moved to the background")를 단언하지 않아, 승인 거부로 헛돈 첫 실행이 0으로 끝났다.
    셋(답, `bug-perf-review` 호출, 전제)이 맞는 회차만 측정으로 센다. 앞 실행 원본에 대 보니 첫 실행 넷은 측정 아님,
    둘째 실행 넷은 측정이었다. 인자 오용의 종료 2도 독스트링에 적었다.
  - [표준 Minor, 명세 Nit] 질문의 유도 두 구절을 빼고 셋째 실행을 돌렸다(위). 문단과 도구를 가르지 못하는 것, 실제
    리뷰 중에 지키는지, 기본 시간 제한과 다른 OS는 "못 보는 것"에 적었다.
  - [표준 Minor, 명세 Minor] 리뷰 파이프라인 2의 "두려면(보류하거나 한계로 적으면) 그 값을 든다"는 `보류`를 판정과
    미룸의 두 뜻으로 썼고, 어느 값을 어디에 적는지 없었다(위 190).
  - [표준 Minor, 명세 Nit] 169 카나리아 명세의 머리 주석이 "옛 정의의 tools 줄은 새 판과 같아"와 그것을 뒤집는 덧붙임을
    함께 담았다. 다시 썼다.
  - [표준 Minor, 명세 Nit] 188 닫힘 메모의 "옛 도구에는 멈출 길이 없었다"는 보편 부정이다. "`TaskStop`이 없어 작업
    ID로 멈출 수 없었다"로 좁히고 "리뷰어가 `run_in_background`로 띄운 것이 아니라"로 고쳤다. 일지와 프로브도.
  - [표준 Minor] `tools/canary.py`의 `tools_for`가 "부분집합은 재지 않았다"고 적었는데 이 프로브의 대조군이 그 구성이었다.
  - [표준 Nit] 정의 문단이 근거 프로브를 파일 이름으로 가리키지 않았고(`docs/agents/issue-tracker.md` 프로브와 근거),
    "본 세션이 그 작업을 멈춰야 했다"는 기록("stopped by main session")보다 컸다.
  - [표준 Nit] 프로브의 이름(`tools`가 정의의 모든 줄, `calls`가 system 부분형과 도구 이름을 섞음)은 다시 쓰며 걷었다.
  - [명세 Nit] 사건 기록의 위치(세션 ID와 서브에이전트 기록 파일)를 프로브 독스트링에 적었다.
- **남긴 것.**
  - [표준 Nit] `clean_env`·`run`·`TIMEOUT`이 `claude_md_parent.py`와 겹친다. 프로브는 근거를 다시 내는 단독
    스크립트라 공용 모듈에 묶지 않는다. `ARMS`의 튜플도 프로브 하나의 상수라 두었다.
  - [표준 Nit] `coderabbit-review`도 Bash로 긴 CLI를 치는데 `TaskStop`이 없다. 그 CLI는 좌석이 없어 돌지 않고 행의 범위
    밖이라 두었다.
  - [명세, 범위] `TaskStop`은 이 리뷰가 띄우지 않은 작업 ID도 멈출 수 있고, "이 리뷰가 남긴 것"이라는 제한은 문장뿐이다.
    PR 직전 보안 축(`/security-review`)에 넘긴다.
- **다시 돌린 것.** 프로브 셋째 실행, 고친 파서를 앞 실행 원본 둘에 대 본 것, 고친 카나리아 명세의 `agent_problems`
  (문제 0, 고치기 전 명세는 tools 불일치). 검증 명령 다섯은 커밋의 pre-commit으로 갈음한다.
