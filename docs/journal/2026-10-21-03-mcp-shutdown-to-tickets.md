# 2026-10-21 (03) mcp-shutdown 명세 검토와 티켓

next-session 지시문으로 연 새 세션이다. 제목을 브랜치 이름으로 바꾸고, 주 체크아웃이 미갱신이라 `tidy-checkouts`를 먼저 돌았다. 그 뒤 주 체크아웃에서 브랜치를 따지 않고 워크트리 `.claude/worktrees/mcp-shutdown-to-tickets`에 들어가 브랜치를 `docs/mcp-shutdown-to-tickets`로 바꿨다. `to-tickets` 스킬을 따랐다. 산출물은 다음과 같다.

- 명세 검토(spec-reviewer)와 그 결과를 닫는 명세의 주석 `(2026-10-21 명세 검토: …)`
- 티켓 셋 `.scratch/mcp-shutdown/issues/01~03`
- ADR 0034의 2026-10-21 이력 "CLI는 첫 Ctrl+C를 실행을 감싼 취소 범위로 전해, 서버를 닫는 도중에 눌러도 한 번이면 끝난다"와 본문 포인터 하나
- 프로브 `close_paths.py`의 사례 `cli_ctrl_c_closing`과 처리기 `--cli-handler scope`, 그 README의 결과
- `plan.md`의 mcp-shutdown 행 끝 괄호와 프론티어 문장

> 사용자: "`.claude/skills/to-tickets/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/mcp-shutdown/spec.md … 다음 작업: 기능 mcp-shutdown. 명세(`.scratch/mcp-shutdown/spec.md`)가 병합됐고(#331) 티켓이 없다 / 다음 단계: 티켓 … 이어받을 상태: 명세 검토(spec-reviewer)는 아직 돌지 않았다. … 이번 요청 범위: 티켓까지"

## 체크아웃 정리

루트를 `83f09401`에서 `6501d4a4`로 당겼다. 병합된 브랜치 `worktree-admin-style-spec`을 지웠고, 쉬는 세션만 쥐던 `tidy-idle-sessions`는 그 세션을 끝낸 뒤 워크트리와 브랜치 `chore/tidy-idle-sessions`를 지웠다. 휴지통의 `node_modules` 셋을 비웠다. 남긴 것은 병합되지 않은 PR의 워크트리(admin-style-spec, bug-perf-review-batch, mcp-shutdown-spec, measure-word-hook, model-rerun-design, morning-report-format, ticket-for-every-pr-design, web-widget-spec), 앱의 표지가 있는 둘(confident-wright-2d3ebf, elegant-dijkstra-aaddb9), 프로세스가 쥔 것(mcp-shutdown-to-spec 등)이다. `mcp-shutdown-spec`은 이 기능의 첫 세션이 남긴 커밋하지 않은 원본을 쥐고 있어 지울지는 사람이 정한다(지시문). `%TEMP%`의 `mcp-full-stack-*` 사본 열 개(약 2.8GB)는 대기열 392의 몫으로 두었다.

## 명세 검토

spec-reviewer가 `6501d4a4`의 명세를 체크리스트 일곱과 질문 둘로 봤다. blocker 1, should-fix 12, nit 3이었다. 검토는 저장소 밖 임시 스크립트(세션 스크래치패드의 `close_press\`)로 넷을 손으로 봤다. 닫는 도중의 첫 Ctrl+C, 쓰기 실패의 종료 코드, 우두머리가 아닌 런처, 범위 취소의 변형이다.

- **B1.** mcp 2.3.0에서 서버를 닫는 2초 사이에 온 첫 Ctrl+C는 시제품 처리기로도 `asyncio.run` 그대로로도 CLI를 끝내지 못했다. 명세의 처리기 테스트는 도구 호출 도중에만 눌러 그것을 보지 못한다. ADR 0034의 2026-10-17 이력("그 취소를 받은 뒤의 보호된 닫기는 끝까지 간다")은 취소가 닫기 전에 들어온 경우에만 맞았다. CLI는 결말을 받자마자 답을 찍고 core는 그 뒤에 닫으므로, 답이 보인 뒤 2초 안에 누르면 이 경우다.
- should-fix 열둘은 티켓 경계(처리기는 2.3.0과 같은 티켓, 사례 2·5와 명령 찾아보기는 런처 티켓), 상류 이슈 초안의 자리와 승인, `tech.md`와 헌법 판, 중단 한 줄의 조건, 쓰기 실패 테스트의 단언, LLM 테스트, 포트 독스트링, 덮이지 않은 스토리, 런처만 죽는 한계, README의 자리, 문서와 코드를 같은 티켓에 두는 것이었다. nit 셋은 POSIX와 macOS, `-I`의 문구, 재지 않은 까닭이다.

## 다시 잰 것

B1은 검토의 임시 스크립트로만 보인 것이라, 명세와 ADR이 근거로 들 수 있게 `close_paths.py`에 사례 `cli_ctrl_c_closing`(닫기 시작 0.5초 뒤 한 번, 10초 뒤 살아 있으면 한 번 더)과 처리기 `scope`(`_run_with_scope_cancel`. 첫 SIGINT를 주 코루틴을 감싼 anyio 취소 범위의 `cancel`로 전한다)를 더해 두 OS에서 돌렸다. Windows는 2.3.0만, Linux는 Docker의 네 갈래다. 측정 아닌 두 회차를 뺀 모든 회차의 표지가 섰다. 측정 아닌 둘은 Windows `asyncio.run` 그대로의 두 번 사례와 Linux 1.30.0 `scope`의 두 번 사례이고, 앞의 것은 2026-10-17과 같이 끝나지 않았고 뒤의 것은 첫 SIGINT에 끝나 둘째를 보내지 못했다.

- 네이티브 취소는 닫는 도중의 첫 SIGINT 뒤 10초 안에 끝나지 않았고 이어 보낸 SIGINT에 끝났다(2.3.0. `asyncio.run` 그대로는 Windows에서, `force`는 두 OS에서). `scope`는 누른 뒤 1.48~1.56초에 닫기 끝을 찍고 끝났고 서버가 내려갔다.
- `scope`는 1.30.0 위에서 누른 뒤 0.008초에 끝나며 서버를 남겼다(Linux). 1.30.0은 닫기를 보호하지 않아 범위 취소가 닫기를 끊은 것으로 본다(어림). 그래서 처리기가 2.3.0 앞에 설 수 없다는 검토의 지적(S1)에 근거가 하나 더 섰다.
- 2.3.0에서 도구 호출 도중의 한 번과 두 번은 `scope`도 `force`와 같은 모양이었다. 1.30.0의 한 번은 위와 같이 달랐다.

## 사용자가 고른 것

> 사용자(질문에 답): "언제 눌러도 한 번이면 끝나게 (추천)" — 설명: 첫 Ctrl+C를 실행 타임아웃과 같은 길(anyio 취소 범위)로 전합니다. 닫기를 보호하는 장치가 그대로 지켜져, 닫는 도중에 눌러도 남은 시간(검토가 잰 바로 누른 뒤 약 1.5초)만 마저 닫고 끝납니다. 대신 처리기 코드가 시제품과 달라지므로, 01 티켓이 '닫기 시작 뒤 한 번' 테스트를 더하고 빨강부터 확인합니다.

> 사용자(질문에 답): "셋, 02·03 나란히 (추천)" — 설명: 위 초안 그대로입니다. 01이 병합되면 02(예외)와 03(런처)를 두 세션에서 동시에 돌리고, 뒤에 병합하는 쪽이 어댑터 모듈의 충돌을 풉니다. 가장 빨리 끝납니다.

두 질문은 한 화면이었다. 거부한 안은 앞의 것이 "지금 방식을 두고 한계로 적기", 뒤의 것이 "셋, 02 다음 03 차례로"와 "둘로 합치기"다. 앞의 것은 ADR 0034의 2026-10-21 이력이 적는다.

## to-tickets가 정한 것

명세의 주석에 "(to-tickets가 정했다)"로 적었다. 요지는 다음과 같다.

- 중단의 한 줄은 트레이스의 상태를 말하지 않는다. 결말을 쓴 뒤 닫는 동안 누르면 "결말 없이 남는다"가 거짓이 되는데 처리기는 결말을 봤는지 모른다. 끝나는 꼴은 그때도 중단(130)이다(S5)
- 처리기 테스트는 넷이다(한 번, 두 번, 닫기를 시작한 뒤의 한 번, 쓰기 실패). 셋째가 결말 뒤의 누름도 대신한다(B1, S6)
- 닫기 사례 2·5와 명령 찾아보기는 런처 티켓 03이 들고 draft의 실험 커밋으로 Linux CI의 빨강을 먼저 보인다. 서버 기동 실패 테스트는 02와 03의 병합 순서와 무관하게 초록이다(S2)
- 상류 이슈 초안은 03이 `.scratch/mcp-shutdown/` 아래에 쓰고 사용자가 승인한 뒤에만 올린다(S3)
- `tech.md`를 고치는 01이 헌법 patch 판을 올리고, 헌법에 닿아 02·03을 막는다(S4)
- LLM 테스트와 전체 검사, 포트 독스트링, 스토리의 받는 자리, 런처만 죽는 한계, README의 자리, 문서와 티켓의 짝(S7~S12)과 nit 셋

## 이 세션이 고친 것

- ADR 0034 2026-10-21 이력 초안이 네이티브 취소를 "두 OS"에서 쟀다고 적었다. `asyncio.run` 그대로는 Windows에서만, 2026-10-17 이력의 처리기 시제품(`force`)은 두 OS에서 쟀으므로 그렇게 고쳤다.
- 티켓 01의 사례 1을 1.30.0 위에서 빨강부터 보이라고 적었는데, 시제품의 가짜 서버는 2.x의 `MCPServer`를 써 1.30.0에서 뜨지 않는다. `fakes.py`처럼 임시로 `FastMCP`로 대신하라는 문장을 더했다.
- 티켓 03이 부모가 죽은 뒤 서버가 "0.2초 안팎"에 내려간다고 적었는데, 측정은 3초 뒤에 모두 내려간 것만 봤다. "런처는 0.2초마다 부모를 보고, 측정은 3초 뒤에 모두 내려간 것을 봤다"로 고쳤다.

## 인계

셀프 리뷰 직전에 인계 계기가 왔다(세션 컨텍스트 362,596 토큰, 문턱 200,000). next-session "인계할 때" 1의 인계하지 않는 다섯에 들지 않는다. 계기를 낸 `code-review` 호출은 성공했고, 요청 범위는 "티켓까지"이며, 지시문의 "이어받을 상태"는 `인계:`로 시작하지 않고, `인계 못함` 줄이 없으며, `get_session`의 `self`에 `parentSessionId`가 없다. 열린 PR이 없어 다음 단계는 지시문의 "티켓" 그대로다. `tools/model_sweep.py`는 `스윕 밖`이었다. 셀프 리뷰, 검사, 커밋, PR, 병합과 `## 다음`은 새 세션이 한다. 이 세션이 띄운 백그라운드 작업은 없다.

- 이 세션의 제목: `docs/mcp-shutdown-to-tickets`에서 `docs/mcp-shutdown-to-tickets (인계함)`으로 바꾼다.
- 명세 검토 보고 원문은 이 세션의 스크래치패드 `C:\Users\User\AppData\Local\Temp\claude\C--project-agent\62056b38-248d-4338-97c3-a576534efea2\scratchpad\review.txt`에 있다. 저장소에 남기지 않는다(일지 2026-10-05-04의 기각).

지시문:

```
다음 작업: 기능 mcp-shutdown. 명세 검토를 닫는 명세 주석, 티켓 셋(01~03), ADR 0034의 2026-10-21 이력 초안, 프로브 사례를 워크트리에 썼고 커밋하지 않았다
다음 단계: 티켓
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-tickets .scratch/mcp-shutdown/spec.md
브랜치: docs/mcp-shutdown-to-tickets
모델: Opus 5.5 / xhigh
읽을 것: docs/journal/2026-10-21-03-mcp-shutdown-to-tickets.md, .scratch/plan.md 의 mcp-shutdown 행
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(`/code-review`)부터 한다. 일지는 docs/journal/2026-10-21-03-mcp-shutdown-to-tickets.md. 명세 검토(spec-reviewer)는 돌았고 앞 세션은 지적 열여섯(blocker 1, should-fix 12, nit 3)을 모두 명세의 `(2026-10-21 명세 검토: …)` 주석과 티켓 수용 기준으로 닫았다고 본다. 그 보고 원문은 앞 세션의 스크래치패드 C:\Users\User\AppData\Local\Temp\claude\C--project-agent\62056b38-248d-4338-97c3-a576534efea2\scratchpad\review.txt 에 있다(저장소에 남기지 않는다). 셀프 리뷰의 명세 축에는 to-tickets 스킬, 명세, 사용자 답 둘(일지 "사용자가 고른 것"의 라벨과 설명 원문), 그 보고 원문을 요구로 넘긴다. ADR 0034의 2026-10-21 이력 초안은 아직 사용자에게 보이지 않았다. 셀프 리뷰를 반영한 뒤 보여 승인을 받는다(작업 규약 5). 일지의 `## 다음`은 아직 없다. 앞 지시문이 넘긴 둘은 그대로다. 워크트리 mcp-shutdown-spec(커밋하지 않은 원본)은 지울지를 사람이 정하고, %TEMP%의 mcp-full-stack-* 사본은 대기열 392의 몫이다
확인할 선행 조건: 없음
이번 요청 범위: 티켓까지
```

제목을 바꿨고 워크트리 잠금을 풀었다.

open-session을 부른다 2026-10-21T00:31:55Z

## 이어받은 세션

위 지시문으로 연 새 세션이 제목을 `docs/mcp-shutdown-to-tickets`로 바꾸고 `git worktree list`에서 그 브랜치의 워크트리를 찾아 `EnterWorktree(path)`로 들어왔다. 커밋하지 않은 변경 다섯과 미추적 파일 넷이 그대로 있었다.

> 사용자: "`.claude/skills/to-tickets/SKILL.md` 를 읽어 그대로 따른다. … 인자: .scratch/mcp-shutdown/spec.md … 이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(`/code-review`)부터 한다. … 이번 요청 범위: 티켓까지"

## 셀프 리뷰

`/code-review`를 기준 `6501d4a4`(origin/main과의 merge-base)로 돌렸다. 범위는 수정 파일 다섯, 미추적 넷, 커밋 없음이다. 명세 축에는 to-tickets 스킬, 명세, 사용자 답 둘(질문과 선택지 원문은 앞 세션 스크래치패드의 `ask.txt`에서 옮겼다), 명세 검토 보고 원문을 요구로 넘겼다. 보고 원문은 그 파일을 읽지 못할 수 있어 브리프에 전문을 실었다. 두 브리프에 mcp 2.3.0 `stdio_client`의 닫기 발췌를 실었다.

### 표준 축

Critical·Major 없음. 프로브는 다시 돌리지 않았고(mcp 2.3.0 환경을 새로 받아야 해서), 병합 순서 세 상태는 코드를 읽어 따졌다.

- Minor 1. 티켓 03 "두 프로브는 … 런처의 폴더를 주면 홀로 돈다": `stale_parent.py`는 폴더 인자가 없고 런처를 `src/agent_os/adapters/mcp_launcher.py`라는 고정 경로로 찾는다. 티켓은 런처 파일 이름을 정하지 않고, 둘째 프로브는 아직 없다.
- Minor 2. ADR 2026-10-21 이력(과 명세 주석, 티켓)의 "1.30.0은 닫기를 보호하지 않아 범위의 취소가 닫기를 곧바로 끊었다"가 근거 표시 없이 단정이다. README는 같은 문장을 어림으로 적었고, 측정으로 선 것은 0.008초에 끝나며 서버가 남은 것뿐이다.
- Minor 3. 일지 "다시 잰 것"의 "모든 회차의 표지가 섰다(측정 아닌 둘은 …)"가 표지가 서지 않은 회차를 괄호에 넣은 모순이다.
- Minor 4. 티켓 01 처리기에 첫 Ctrl+C가 범위를 잡기 전에 오거나 루프가 닫힌 뒤에 오는 틈의 기대가 없다. 시제품 `_run_with_scope_cancel`은 범위가 없으면 첫 SIGINT를 곧바로 두 번째 꼴로 보내고, 루프가 닫힌 뒤의 `call_soon_threadsafe`는 `RuntimeError`를 낼 수 있다.
- Nit: 거부한 안의 따옴표 문구가 ADR과 명세에서 글자가 다르다. 일지의 "네이티브 취소(`asyncio.run` 그대로, `force`) … (2.3.0, 두 OS)"와 "`scope`도 `force`와 같은 모양"의 범위가 흐리다. README의 "2.3.0의 닫기가 끝나지 않았다"는 잰 것(자식이 10초 안에 끝나지 않음)보다 넓다. ADR의 "네이티브 취소는 한 번 나고 다시 오지 않았다"에 근거 표시가 없다. 티켓이 파일 경로를 많이 든다(저장소 선례가 같아 지적만). `close_paths.py`의 판단 항목 smell(두 처리기 골격의 중복, 사례 분기의 흩어짐, 늘 함께 다니는 인자 셋).
- 어긋남 없이 대 본 것: README 표와 ADR·명세의 수, 종료 코드, `TraceStore.write`가 동기이고 `_emit`이 await 없이 쓰는 것, 기한 판정이 `deadline.cancelled_caught`라 바깥 범위의 취소가 시간 초과로 읽히지 않는 것, CLI가 `RunFinished`에서 곧바로 쓰는 것, main 보호의 `strict`, `cancel-in-progress`, 헌법 판 선례, draft 실험 커밋 선례, 프로브의 `--expect` 인자들, `fakes.py`의 `FastMCP` 갈래, ADR 포인터 제목, 티켓 01의 잔존 목록, 병합 순서 세 상태의 서버 기동 실패 테스트.

### 명세 축

범위 넘침 없음. 검토 지적 열여섯 가운데 열넷이 닫혔고 S4(명세 Solution의 "계약 티켓이 없다"에 주석이 없다)와 S12(아래 2)가 일부다. 검토가 확인하지 못한 넷 가운데 U2는 닫혔고, U3은 일부(아래 4), U1(serve 강제 종료 뒤 asyncio의 네이티브 취소가 이미 닫는 중인 실행에 닿는 길)과 U4(처리기의 `signal.signal`은 주 스레드에서만 된다)는 받는 자리가 없다. U4는 위험이 낮다고 봤다(설치된 xdist 3.8.0이 `main_thread_only`로 돌고 `tests/test_main.py`가 in-process로 부르는 `main([...])` 68회도 주 스레드다).

- Major 1. 02·03의 기능 닫기 판정: strict는 코드를 묶지 판정의 때를 묶지 않는다. 02 판정 → 03 판정 → 02 병합 → 03이 main을 들인 뒤 다시 판정하지 않고 병합하면 아무도 기능을 닫지 않는다. 선례 end-user-continuation 02에는 "다시 본다"가 있다. 티켓 01에는 첫 병합 때 기능을 `in-progress`로 바꾸는 줄이 없다(`docs/agents/issue-tracker.md`, 선례 end-user-continuation 01).
- Minor 2. 티켓 01이 처리기 독스트링에 "POSIX는 03의 런처가 거둔다"를 쓰게 해, 01과 03 사이의 main에서 거짓이다(명세 "문서와 독스트링은 그것을 참으로 만드는 코드와 같은 티켓에 든다"와 어긋난다).
- Minor 3. 티켓 01 셋째 사례의 표지가 "누름이 닫기 시작 표지 뒤"뿐이다. 프로브는 닫기 끝보다 앞인지도 봤다. 부하로 누름이 늦으면 재려는 상황 없이 초록이 될 수 있다.
- Minor 4. 티켓 01 "범위의 취소가 기다림마다 다시 들어와도 결말이 바뀌지 않는다"를 재는 테스트가 없다(자식은 core를 거치지 않고 `-m llm`은 Ctrl+C를 누르지 않는다). 근거 문장으로 낮추거나 core를 거치는 사례를 더한다.
- Minor 5. 스토리 14·23·30을 받는 자리가 명세와 다르다. 명세는 런처 독스트링과 `adapters.md` 둘 다라고 했는데 티켓 03의 `adapters.md` 항목에 14·30이, 독스트링에 23이 없다.
- Minor 6. 표준 축 Minor 1과 같다. `stale_parent.py`는 런처 경로(39행)와 거부 문구 "이미 끝나"(40행)를 코드에 박았고 티켓은 둘 다 정하지 않는다.
- Minor 7. ADR 이력의 "(신호 처리기는 루프 밖에서 돈다)"와 `close_paths.py`의 "이벤트 루프의 스레드에서 불러야 해서"가 틀렸다. Windows에서 손으로 보니 처리기는 주 스레드에서, 루프가 select에서 기다리는 도중에 돌았다. `call_soon_threadsafe`가 필요한 까닭은 select를 깨우는 데 있다.
- Minor 8. U1을 받는 자리가 없다. 알려진 한계로 적거나 티켓 03의 상류 초안에 넣는다.
- Nit 9. 티켓 01은 의존성 교체를 사례 1의 1.30.0 빨강보다 위에 둬, 위에서부터 따르면 락을 되돌려야 한다. 02와 03이 모두 병합된 상태에서 명령 찾아보기가 `ConnectionError`로 감싸는 범위 안에 있어야 하는데 티켓 02의 목록에 없다.
- Nit 10. 명세의 Solution "계약 티켓이 없다", Testing Decisions "시간"의 "열두 개(… CLI 처리기 둘)", Implementation Decisions 머리의 `_run_with_force_exit`가 주석 없이 남았다. 일지의 "모든 회차의 표지가 섰다(측정 아닌 둘은 …)". ADR과 명세가 거부한 안을 따옴표로 "반응이 없고"라 옮겼는데 선택지 원문은 "효과가 없고"다.
- 밀어 보고 맞은 것(명세 축): 수와 출처, `cli_ctrl_c_closing`이 닫기 시작 0.5초 뒤의 누름을 만드는 것, 2.3.0의 `missing_command`가 두 OS에서 `FileNotFoundError`인 것, 병합 순서 세 상태, `RunFinished`가 연결 안에서 나오는 것, 선례들, 시제품의 `os.write(2)`, 사용자 답 둘의 인용, `check_adr_pointers.py`가 0으로 끝난 것.

### 반영

고친 것(두 축의 지적을 근거로 확인한 뒤 고쳤다. 새로 쓴 사실 문장은 고치기 전에 손으로 봤다: 저장소 `.venv`의 anyio 4.15.1·Python 3.12.10에서 취소를 받은 뒤 세 번 기다리면 범위 취소는 세 번 모두 다시 들어오고 네이티브 취소는 첫 번만 났다. 다른 스레드의 `signal.signal`은 `ValueError: signal only works in main thread of the main interpreter`였다. 닫힌 루프의 `call_soon_threadsafe`는 `RuntimeError: Event loop is closed`였다. Python 3.12.10 `asyncio.runners.Runner._on_sigint`의 소스를 열어 첫 SIGINT 뒤 "wakeup loop if it is blocked by select()" 주석과 함께 `call_soon_threadsafe(lambda: None)`을 부르는 것을 봤다).

- 명세 축 Major 1: 티켓 02·03의 닫기 판정을 "main을 마지막으로 들인 뒤, 병합 바로 앞에 판정한다"로 고치고 "판정 뒤에 main을 다시 들였으면 다시 판정한다"를 더했다. 티켓 01에 첫 병합이라 mcp-shutdown 행을 `in-progress`로 바꾸는 줄을 더했다.
- 명세 축 Minor 2: 티켓 01이 처리기 독스트링에 그 main에서 참인 것(Windows는 Job Object가 거두고 POSIX에서는 남을 수 있다)만 적고, 03이 POSIX의 런처를 더하게 했다. 명세 "고칠 자리"의 2026-10-21 주석에도 적었다.
- 명세 축 Minor 3: 티켓 01 셋째 사례와 명세 Testing Decisions 주석의 표지에 누름이 닫기 끝보다 앞인지 보는 조건(닫기 끝이 없으면 앞으로 센다)을 더했다.
- 명세 축 Minor 4: 티켓 01의 "결말이 바뀌지 않는다" 체크 항목을 지우고 처리기 절 머리의 근거 문단(재는 테스트를 두지 않는 까닭 포함)으로 낮췄다.
- 명세 축 Minor 5: 티켓 03의 `adapters.md` 항목에 스토리 14·30을, 런처 독스트링에 스토리 23을 더했다.
- 두 축의 Minor(프로브 문구): 티켓 03이 `stale_parent.py`의 박힌 상수 셋(런처 경로, "이미 끝나", "런처:")과 저장소 루트에서 돌리는 것, 구현과 다르면 상수를 맞추는 것을 적게 고쳤다.
- 명세 축 Minor 7: ADR 이력의 "(신호 처리기는 루프 밖에서 돈다)"와 `close_paths.py` 독스트링의 "이벤트 루프의 스레드에서 불러야 해서"를, 처리기가 select 도중에도 끼어들어 돌고 루프를 깨우지 않아 `call_soon_threadsafe`로 깨운다는 문장으로 바꿨다.
- 명세 축 Minor 8: U1을 명세 "serve 종료"의 "Ctrl+C 두 번"에 재지 않은 갈래(코드를 읽은 어림)로 적고 Out of Scope의 "serve의 신호 처리"가 받게 했다.
- 명세 축 Nit 9: 티켓 01의 의존성 절 머리에 사례 1의 빨강을 먼저 본다는 순서를 적었다. 티켓 02의 감싸는 목록에 "03이 먼저 병합되었으면 그 앞의 명령 찾아보기도"를 더했다.
- 명세 축 Nit 10: 명세 Solution의 "계약 티켓이 없다", Implementation Decisions 머리의 시제품 이름, Testing Decisions "시간"의 수에 2026-10-21 주석을 달았다. ADR과 명세의 거부한 안 인용을 선택지 설명 원문("닫는 2초 사이의 첫 Ctrl+C는 효과가 없고, 한 번 더 누르면 곧바로 끝난다")으로 바꿨다.
- 표준 축 Minor 2: ADR 이력과 명세 주석의 1.30.0 원인 문장을, 잰 것은 0.008초에 끝나며 서버가 남은 것이고 원인은 어림이라는 문장으로 고쳤다. ADR에서는 1.30.0이 닫기를 취소된 범위 안에서 돌린다는 Context를 근거로 들었다.
- 표준 축 Minor 3과 Nit: 일지 "다시 잰 것"의 표지 문장, 네이티브 취소의 OS 범위, `scope`와 `force`가 같은 모양인 판(2.3.0)을 고쳤다.
- 표준 축 Minor 4와 U4: 티켓 01에 첫 SIGINT가 범위를 잡기 전이나 루프가 닫힌 뒤에 와도 중단의 꼴로 끝나고 추적을 찍지 않는다는 항목과, 처리기는 주 스레드에서만 달 수 있다는 항목을 더했다.
- 표준 축 Nit: README의 "2.3.0의 닫기가 끝나지 않았다"를 "자식이 10초 안에 끝나지 않았다"로 좁히고 `closed` 표지로는 가르지 않는 까닭(연결을 나선 뒤에 찍는다, 코드를 읽었다)을 적었다. 같은 뜻의 명세 "상류에 알린다" 주석과 티켓 03의 초안 항목도 고쳤다. ADR의 "네이티브 취소는 한 번 나고 다시 오지 않았다"에 손으로 본 근거를 달았다. ADR의 도구 호출 도중 수에 "mcp 2.3.0에서"를 더했다.

남긴 것:

- 표준 축 Nit "티켓이 파일 경로를 많이 든다": to-tickets 스킬은 경로를 피하라고 하지만, 이 저장소의 티켓은 경로를 들어 왔고(admin-api 01 등) 명세의 "고칠 자리"가 경로로 정해져 있다. 표준 축도 저장소 선례가 이긴다고 판정했다.
- 표준 축 Nit `close_paths.py`의 smell 셋: 판단 항목이고, 프로브가 두 처리기와 사례를 한 파일에서 가르는 모양이라 그대로 둔다.

PR 직전 리뷰에 밀 주장으로 넘길 새 문장(원문):

- ADR 0034 2026-10-21 이력: "신호 처리기는 루프가 select에서 기다리는 도중에도 주 스레드에 끼어들어 돌고 루프를 깨우지 않으므로, 그 호출로 루프를 깨워 취소를 루프의 콜백으로 돌린다(Python 3.12의 `asyncio.runners`도 첫 SIGINT 뒤 같은 호출로 루프를 깨운다. 코드를 읽었다. 처리기가 select 도중에 도는 것은 셀프 리뷰가 Windows에서 손으로 봤다)"
- ADR 0034 2026-10-21 이력: "범위의 취소는 범위를 나갈 때까지 기다림마다 다시 들어오고, 네이티브 취소는 한 번 나고 다시 오지 않는다(anyio 4.15.1과 Python 3.12.10에서 취소를 받은 뒤 세 번 기다려 손으로 봤다)"
- ADR 0034 2026-10-21 이력: "1.30.0은 닫기 절차를 취소된 범위 안에서 돌리므로(위 Context) 범위의 취소가 닫기를 곧바로 끊은 것으로 본다(어림, 가르지 않았다)"
- 프로브 README: "닫기 끝의 표지(`closed`)는 연결을 나선 뒤에 찍어, 네이티브 취소가 그 자리 앞에서 밖으로 올라가면 닫기가 끝났어도 찍히지 않는다(코드를 읽었다)"
- 명세 "Ctrl+C 두 번" 주석: "둘째 SIGINT 뒤 asyncio가 남은 태스크를 네이티브로 취소할 때 그 실행이 이미 서버를 닫는 중이면, … serve가 셋째 SIGINT까지 끝나지 않을 수 있다(코드를 읽은 어림, 재지 않았다)"
- 티켓 01: "시제품(`_run_with_scope_cancel`)은 범위를 잡기 전의 첫 SIGINT를 둘째처럼 다루고, 루프가 닫힌 뒤의 `loop.call_soon_threadsafe`는 `RuntimeError: Event loop is closed`를 낸다(손으로 봤다)", "`signal.signal`은 다른 스레드에서 `ValueError`를 낸다(손으로 봤다)"
- 티켓 01: "core는 기한을 자기 범위의 `cancelled_caught`로 가려 바깥 범위의 취소를 시간 초과로 읽지 않는다(코드를 읽었다. 서버 여럿으로는 재지 않았다)"
- 티켓 03: "`stale_parent.py`는 … 지금 폴더 아래 `src/agent_os/adapters/mcp_launcher.py`를 런처로 띄우며 런처의 표준 에러에서 "이미 끝나"와 "런처:"를 찾는다(셋 다 그 프로브 코드의 상수다)"
- 티켓 02·03: "strict는 코드를 묶을 뿐 판정한 때를 묶지 않는다"

다시 돌린 명령: 커밋이 부르는 pre-commit으로 갈음했다. 커밋 `c5f09a32`의 pre-commit이 모두 통과했다(ruff 둘, 러너의 zizmor·지침 검사·lint-imports·타입 우회 검사·pyright·훅 러너·pytest·web verify, 러너 314.77초, 마크다운 표, 줄 구분 문자, 변이 표, 커밋 메시지). 카나리아 명세와 헌법 판 검사는 해당 파일이 없어 `Skipped`였다. 인용 대조가 경고 열 건을 냈다. 넷(97·98·101·111행)은 리뷰가 짚은 고치기 전의 문장이라 저장소에 없는 것이 맞다. 122행은 Python 3.12.10의 `Runner._on_sigint` 소스와 글자가 같다(그 함수의 소스를 찍어 봤다). 나머지 다섯(프로브 README 1, 이 일지 4)은 요약을 따옴표로 감싼 것이라 원문으로 바꾸거나 따옴표를 뗐다.

## ADR 승인

셀프 리뷰를 반영한 뒤 ADR 0034의 2026-10-21 이력 초안을 쉬운 말로 요약해 보이고 물었다(작업 규약 5). 화면의 수(1.48~1.56초, 2.02~2.24초, 10초, 약 2초)는 이력 본문에서 옮겼다.

> 사용자: (선택) 승인 (Recommended) — 이 문안 그대로 커밋합니다. 이어서 PR 직전 리뷰를 돌리고, PR을 열어 병합한 뒤, 다음 세션(티켓 01)의 지시문까지 만듭니다.

## 커밋과 main 들이기

커밋 직전 `sibling_overlap.py`가 1로 끝났다. 그사이 main에 병합된 일지 2026-10-21-02(ticket-for-every-pr 설계)가 이 브랜치의 일지 `2026-10-21-01`보다 이름순으로 뒤라, `--move`로 이 일지를 2026-10-21-03으로 옮겼다(파일 이름과 `plan.md`·이 일지의 인용). origin/main이 `6501d4a4`에서 `561b37cb`로 움직여 `git diff --name-only HEAD...origin/main`을 이 브랜치의 파일과 대 보니 겹치는 것이 없었다. 새로 선 규약은 ADR 0037(main에 들어가는 PR은 모두 티켓 하나를 가리킨다)인데, 기능의 설계·명세·티켓을 쓰는 PR은 그 경계의 면제라 이 PR에 닿지 않는다. 커밋 `c5f09a32` 뒤 origin/main을 합쳤다(`a2f1ae6f`).

## PR 직전 리뷰

`coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 리뷰 파이프라인 2의 대체 둘을 돌렸다. 기준은 `561b37cb`(main을 합친 뒤의 merge-base), 범위는 이 브랜치의 파일 아홉이다.

### 보안 축(`/security-review`)

지적 없음. 코드 파일은 프로브 `close_paths.py` 하나이고, 자식 프로세스를 인자 목록으로 띄우며(`shell=True` 없음), config의 값은 프로브가 지은 것(mkdtemp 경로, 고정 명령, argparse `choices`)뿐이고, 신호는 제 프로세스에만 보낸다. 문서는 사용자 승인 뒤에만 상류에 이슈를 올리게 하고 Docker는 판을 고정한 이미지에 저장소를 읽기 전용으로 붙인다. 1단계가 후보를 내지 않아 오탐 거르기는 돌리지 않았다.

### 버그·성능 축(`bug-perf-review`)

Critical·Major 없음. 보류 Minor 셋, 오탐 넷. 밀 주장 아홉은 모두 맞거나 어림으로 적혀 있다고 판정했다(2는 저장소 `.venv`에서 다시 재현했고, 4는 `close_paths.py`의 `closed`가 `async with stdio_client` 블록 밖에 찍히는 것을, 7은 `run.py`의 `move_on_after`와 `cancelled_caught`를, 8은 `stale_parent.py`의 상수 셋을 열었다). 오탐은 02·03에 자기 `Status:`를 `done`으로 바꾸는 항목이 없다는 것(end-user-continuation의 티켓 여섯도 같은 모양이고 모두 `done`이다), draft PR에는 CI가 돌지 않는다는 것(`ci.yml`이 기본 types의 `pull_request:`라 돈다), 02·03의 서버 기동 실패 테스트 문장, 2.3.0 발췌와의 충돌이다. 예산에 닿아 따라가지 못한 것(락 변화 문장, `pyproject.toml` 주석 줄 수, `write_failure.py`의 옵션, 1.30.0의 저수준 `Server`, 일지 1~120행, README 51행 뒤, 시제품)은 셀프 리뷰 두 축이 본 범위다.

- 보류 1. 범위 취소의 재진입이 끊는 정리로 트레이스 쓰기와 서버 닫기만 들고 에이전트의 `finally`의 기다림을 빠뜨렸다(ADR 이력의 대가 첫 항목, 티켓 01 처리기 절 머리).
- 보류 2. 01이 병합돼도 `plan.md` 프론티어 문단의 "다음은 티켓 01 이다"를 고치는 단계가 없다.
- 보류 3. 티켓 01의 쪽 나눔 테스트 둘에 빨강을 먼저 보는 단계가 없다(원칙 II).

### 반영

- 보류 1을 고쳤다. 실행 타임아웃의 기한도 같은 범위 취소이고, `run()`이 기한 범위 안에서 `events()` → `_drive` → `_connected` → `_attend` → `_relay` → `_closing(agent.run(...))`로 에이전트의 제너레이터를 닫으므로 지금도 기한에서 그 기다림은 끊긴다(코드를 읽었다). 저장소의 플러그인 에이전트에는 `finally`가 없다(`plugins/`에서 grep). 티켓 01 처리기 절 머리의 근거 문단에 이것을 더했다. ADR 이력은 고치지 않았다. 대가 첫 항목의 "취소된 실행이 범위 안에서 보호 없이 기다리는 정리는 곧바로 끊긴다"가 이미 이 경우를 덮고, 승인받은 글을 고치지 않는다.
- 보류 3을 고쳤다. 티켓 01의 쪽 나눔 항목에, 커서가 `None`이 아닌 동안 따르기만 하는 어댑터(시제품의 첫 판)로 두 테스트가 기한의 `TimeoutError`로 빨간 것을 먼저 본 뒤 빈 글의 끝과 1000쪽 상한을 더한다는 순서를 적었다(명세 218행의 고치기 전 빨강과 같은 모양).
- 보류 2는 남긴다. 프론티어 문단은 날짜를 단 기록이고, design-system과 end-user-continuation의 "다음은 티켓 01 이다"도 그 기능이 진행되고 닫힌 뒤 그대로다. end-user-continuation의 첫 티켓(`89b560de`)은 `plan.md`에서 행의 상태만 `todo`에서 `in-progress`로 바꿨다(`git show --word-diff`로 봤다). 진행의 원천은 행의 상태 칸, 티켓의 `Status:`, 일지의 "다음"이다.

이 반영으로 새로 쓴 문장(원문):

- 티켓 01: "실행 타임아웃의 기한(`move_on_after`)도 같은 범위 취소이고 core는 그 범위 안에서 에이전트의 제너레이터를 닫으므로(`core/run.py`의 기한 범위와 `_closing`, 코드를 읽었다) 첫 Ctrl+C는 기한과 같은 꼴이 될 뿐이다. 저장소의 플러그인 에이전트에는 `finally`가 없다(`plugins/`에서 grep했다)"
- 티켓 01: "커서가 `None`이 아닌 동안 따르기만 하는 어댑터(시제품의 첫 판, 빈 글을 끝으로 보지 않고 쪽 상한이 없다)로 둘 다 기한의 `TimeoutError`로 빨간 것을 본 뒤"

이 둘은 PR 봇이 다음 층이다. 다시 돌린 명령은 이 반영의 커밋이 부르는 pre-commit으로 갈음했다. 커밋 `3bad1f43`의 pre-commit이 모두 통과했다(러너 229.22초, 인용 대조 경고 없음). ruff 둘은 스테이지된 `.py`가 없어 `Skipped`였고, 마지막 `.py` 변경(`close_paths.py`)은 `c5f09a32`에서 ruff를 지났다. 카나리아 명세와 헌법 판 검사는 해당 파일이 없어 `Skipped`였다.

## 인계 (커밋 뒤)

`3bad1f43` 커밋 뒤 인계 계기(`커밋 뒤`, 세션 컨텍스트 약 26만 토큰)가 왔다. 인계하지 않는 때 다섯에 들지 않는다. 커밋은 성공했고, 요청 범위("티켓까지")는 PR과 병합까지라 커밋에서 끝나지 않으며, 이 세션이 넘겨받은 경계는 `셀프 리뷰 직전`이라 이번 경계와 다르고, `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다. 이 세션의 지금 제목은 `docs/mcp-shutdown-to-tickets`이고 넘기기 전에 `docs/mcp-shutdown-to-tickets (인계함)`으로 바꾼다. `tools/model_sweep.py docs/mcp-shutdown-to-tickets`는 `스윕 밖`이고 열린 PR이 없어 모델은 결정표의 인계 줄대로 `Opus 5.5 / xhigh`다.

지시문:

다음 작업: 기능 mcp-shutdown. 티켓 셋(01~03), 명세 주석, ADR 0034의 2026-10-21 이력(사용자 승인), 프로브 사례를 커밋했고 PR을 열어 병합하는 것이 남았다
다음 단계: 티켓
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-tickets .scratch/mcp-shutdown/spec.md
브랜치: docs/mcp-shutdown-to-tickets
모델: Opus 5.5 / xhigh
읽을 것: 일지 docs/journal/2026-10-21-03-mcp-shutdown-to-tickets.md의 "셀프 리뷰"부터 끝까지
이어받을 상태: 인계: 커밋 뒤. `c5f09a32`(티켓 셋과 명세·ADR·프로브·일지), origin/main `561b37cb`를 합친 `a2f1ae6f`, PR 직전 리뷰를 반영한 `3bad1f43`까지 커밋했고 푸시하지 않았다(PR 없음). 셀프 리뷰, ADR 0034 이력의 사용자 승인, PR 직전 리뷰(CodeRabbit 좌석 없음이라 `/security-review`는 지적 없음, `bug-perf-review`는 보류 Minor 셋 가운데 둘을 고치고 프론티어 문단 하나를 선례로 남겼다)를 마쳤다. 남은 단계는 이 일지의 커밋하지 않은 인계 절을 커밋하고, 푸시하고, PR을 열고(체크리스트에 두 리뷰의 결과와 남긴 지적의 이유. 계약 영향은 이 PR이 헌법을 고치지 않고 티켓 01이 `tech.md`를 고친다는 것과 ADR 0034 이력의 승인), 순서 1의 2(봇 회차)와 병합을 거쳐, 일지에 `## 다음`(다음은 티켓 01)을 쓰고 next-session을 부르는 것이다. docs/journal/2026-10-21-03-mcp-shutdown-to-tickets.md
  워크트리 mcp-shutdown-spec(커밋하지 않은 원본)은 지울지를 사람이 정한다. %TEMP%의 mcp-full-stack-* 사본은 대기열 392의 몫이다.
확인할 선행 조건: 없음
이번 요청 범위: 티켓까지

제목을 `docs/mcp-shutdown-to-tickets (인계함)`으로 바꿨다. `git worktree unlock`은 `is not locked`였다(넘어간다).

open-session을 부른다 2026-10-21T03:16:24Z

## 이어받은 세션 (커밋 뒤)

위 지시문으로 연 새 세션이 제목을 `docs/mcp-shutdown-to-tickets`로 바꾸고 `git worktree list`에서 그 브랜치의 워크트리를 찾아 `EnterWorktree(path)`로 들어왔다. HEAD는 `3bad1f43`이었고 커밋하지 않은 변경은 이 일지 하나였다.

> 사용자: "`.claude/skills/to-tickets/SKILL.md` 를 읽어 그대로 따른다. … 인자: .scratch/mcp-shutdown/spec.md … 이어받을 상태: 인계: 커밋 뒤. … 남은 단계는 이 일지의 커밋하지 않은 인계 절을 커밋하고, 푸시하고, PR을 열고(체크리스트에 두 리뷰의 결과와 남긴 지적의 이유. 계약 영향은 이 PR이 헌법을 고치지 않고 티켓 01이 `tech.md`를 고친다는 것과 ADR 0034 이력의 승인), 순서 1의 2(봇 회차)와 병합을 거쳐, 일지에 `## 다음`(다음은 티켓 01)을 쓰고 next-session을 부르는 것이다. … 이번 요청 범위: 티켓까지"
