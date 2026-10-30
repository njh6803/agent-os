# model-rerun 프로브

다시 풀기(지난 티켓을 갈래마다 다시 푸는 측정)의 프로브다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거", 짓는 규칙은 `.claude/rules/probes.md`다. 근거로 드는 자리는 `.scratch/model-rerun/spec.md`의 "러너가 기대는 `claude -p`의 동작" 결정이다. 설계(`.scratch/model-rerun/design.md`)는 이 동작을 파일럿(8절의 2·3·4·5·7)에서 보겠다고 미뤘다. 결과에 따라 러너의 모양이 달라지므로 명세 단계에서 먼저 쟀다(`to-spec` 3단계). 전용 설정 폴더와 다시 풀기 계정(njh4803. 2026-10-26 njh6803에서 바꿨다)이 드는 확인은 아직 파일럿 몫이다.

본 측정의 사전 등록 절은 아래 "사전 등록(본 측정)"이다. 파일럿과 과제 고르기 뒤, 본 측정의 첫 회차 전에 더하고 내용의 해시로 고정했다(설계 6절 머리). 판정 도구 `tools/rerun_judge.py`가 그 도구의 두 표지(`PREREG_START`·`PREREG_END`) 사이 내용의 SHA-256을 그 도구의 상수 `PREREG_SHA256`과 대 보고, 맞지 않으면 결론을 내지 않는다. 러너도 본 측정 목록의 회차를 열기 전에 같은 대조를 한다. 판정 도구는 이 파일 전체에서 두 표지가 하나씩이고 시작이 앞일 때만 그 사이를 절로 받으므로, 표지는 절의 두 자리에만 쓴다. 그리고 표지는 홀로 한 줄을 차지하게 쓴다. 판정 도구는 줄 안에 섞인 표지도 받아, 한 문장이 표지를 적으면 표지 수가 늘어 절을 받지 못하기 때문이다. 두 약속은 `tests/tools/test_rerun_judge.py`의 `test_이_저장소의_프로브_README가_표지_약속을_지킨다`가 본다. 절의 글을 한 글자라도 바꾸면 해시가 달라지므로, 결과를 본 뒤에는 고치지 않는다.

## 돌리는 법

워크트리 루트에서 친다. 출력 디렉터리는 저장소 밖(세션 스크래치패드)에 둔다. 원본(`<갈래>.jsonl`)에는 세션 셸의 환경 변수 이름과 임시 폴더 경로가 실려 대개 커밋하지 않는다. 커밋한 원본은 `서브-2.jsonl` 하나다. 한 호출에 결과 이벤트가 여럿 나온 유일한 실행이라 그 모양을 남겼다(아래 결과 절의 "한 호출에 결과 이벤트가 여럿일 수 있다"). 그 파일에 실린 로컬 경로는 임시 폴더, 설정 폴더, 셸 실행 파일(`WindowsApps\pwsh.exe`)이고, 명세 PR의 보안 리뷰가 그 파일에서 자격 증명과 이메일 꼴을 찾아 0건이었다(일지 2026-10-22-16 "PR 직전 리뷰").

```sh
uv run python .scratch/model-rerun/probes/headless_flags/headless_flags.py <출력 디렉터리> [--arm <갈래>]
```

저장한 요약만으로 다시 판정하는 길이 둘 있다. `claude`를 띄우지 않는다.

```sh
uv run python .scratch/model-rerun/probes/headless_flags/headless_flags.py --judge .scratch/model-rerun/probes/headless_flags/2026-10-22
uv run python .scratch/model-rerun/probes/headless_flags/headless_flags.py --prices .scratch/model-rerun/probes/headless_flags/2026-10-22
```

`--judge`는 요약마다 그 갈래가 재려던 상황의 표지(아래 표의 "재는 것"마다 하나)가 있는지 보고 `[측정] <이름>`이나 `[측정 아님: <까닭>] <이름>`을 한 줄씩 찍는다. 끝에 회차 셈(`측정 12회차, 측정 아님 0회차`)을 찍고, 하나라도 측정이 아니거나 요약이 없으면 종료 1이다. 회차 셈과 `claude` 출력 읽기는 `tools/probe_kit.py`의 `Rounds`·`LineReader`가 한다(`.claude/rules/probes.md`). `--prices`는 요약의 `modelUsage`마다 `costUSD`가 공식 단가(`docs/model-selection.md` 2절)로 셈한 값과 상대 차이 10억분의 1 안에서 같은지를 캐시 쓰기 배수 둘(5분 1.25배, 1시간 2배)로 보고, 어느 배수와도 맞지 않는 모델이 있거나 견준 칸이 하나도 없으면 종료 1이다.

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `headless_flags/`(프로브 `headless_flags.py`, 2026-10-22 기록 `2026-10-22/`: 갈래 일곱의 요약 열 개, `서브` 갈래를 더 돈 요약 둘 `서브-4`·`서브-5`, `서브`의 둘째 실행 원본 `서브-2.jsonl`) | 다시 풀기 러너가 기대는 `claude -p`의 동작. 결과 이벤트의 비용 칸과 그 셈, `--resume`에서 비용이 누적되는지, `--max-budget-usd`가 구독 로그인에서 멈추는지와 무엇을 세는지, 노력과 모델이 실리는 자리, 서브에이전트의 기록과 결과 이벤트의 수, 저장소의 막는 규칙이 auto 모드에서 막는지(양성 대조는 규칙 없는 같은 저장소), `AskUserQuestion`이 있는지, 한도 이벤트의 칸. 저장한 요약으로는 갈래마다의 측정 표지(`--judge`)와, 비용 칸이 공식 단가의 어느 캐시 쓰기 배수와 맞는지(`--prices`) | `spec.md` "러너가 기대는 `claude -p`의 동작", "회차 기록"의 공식 단가 셈 | `claude` CLI와 로그인. sonnet 세션 일곱, 호출 열. 셋째 실행의 결과 비용을 세션마다 마지막 값으로 더하면 약 $0.30이다. 시간은 재지 않았다. `--judge`와 `--prices`는 커밋한 요약만 읽는다 | Claude Code 2.1.302, 기본 설정 폴더의 njh4803(max), Windows 10 이 PC |
| `deny_shapes/`(프로브 `deny_shapes.py`, 2026-10-26 기록 `2026-10-26/`: 둘째·셋째 실행의 두 갈래 요약 넷. 규칙을 회차 폴더의 파일과 `--settings`로 옮긴 뒤의 2026-10-27 기록 `2026-10-27/`: 두 갈래 요약 둘. 뿌리 규칙의 꼴을 견준 프로브 `root_shape.py`와 그 2026-10-27 기록 `2026-10-27/뿌리-*.summary.json` 셋) | `root_shape.py`: 회차들의 뿌리 바로 아래 쓰기를 막는 꼴 `<뿌리>/*`와 `<뿌리>/*.*`가 뿌리의 확장자 있는 파일, 확장자 없는 파일, 그 아래 회차 폴더의 클론 쓰기를 막는지(양성 대조는 뿌리 규칙 없음). 2026-10-27 결과: `*`는 셋 모두 막았고(클론 쓰기까지), `*.*`는 확장자 있는 파일만 막았으며, 대조는 셋 모두 썼다. 그래서 러너는 `*.*`를 쓴다(조건 판 3). `deny_shapes.py`: 러너의 막는 규칙(`tools/rerun_round.py`의 `deny_rules`) 가운데 `headless_flags`가 재지 않은 꼴, 곧 경로의 쓰기·편집·읽기 규칙과 도구 이름만 쓴 규칙(`WebSearch`, 바깥 상태 도구의 대표 `ListAgents`)이 전용 설정 폴더와 auto 모드에서 막는지와, 서브에이전트의 막힌 호출이 본 세션 결과의 `permission_denials`에 실리는지. 양성 대조는 규칙 없는 같은 저장소다. 주 체크아웃과 홈은 임시 폴더 안의 가짜다 | 티켓 11 "막는 규칙의 새 꼴", `spec.md` "명령과 막는 규칙"의 끝 줄, 티켓 11의 09 메모(서브에이전트의 거부), `spec.md` "러너가 기대는 `claude -p`의 동작"의 2026-10-27 주석(규칙의 새 자리), `tools/rerun_round.py` 독스트링의 못 보는 것 | 전용 설정 폴더의 로그인과 판 고정 복사본. 실행마다 Sonnet 5.5 medium 세션 둘, 셋째 실행의 비용은 둘을 더해 약 $0.23 이고 2026-10-27 실행은 약 $0.27 이다. `root_shape.py`는 갈래 셋에 약 $0.24 다. 시간은 재지 않았다 | Claude Code 2.1.302(복사본 `C:\Users\User\.claude-rerun-bin\2.1.302`), 전용 설정 폴더의 njh4803(max), Windows 10 이 PC |
| `rerun_files_mutations.toml` | 티켓 01(두 계약 파일의 꼴, `tools/rerun_files.py`)의 시험이 무는지. 읽기의 거부(모르는 키, 참거짓·실수 판, 음수, 글 칸마다의 꼴과 유니코드 줄 구분 문자, 무한대와 NaN, float로 담지 못하는 큰 정수, 자릿수 한도를 넘는 정수 리터럴, 깊은 중첩, UTF-8 아닌 파일), 쓰기의 유한하지 않은 수, 칸 사이의 맞음(끝의 종류와 하위 이유, 한도가 아닌 끝의 `resets_at`, 목록의 종류와 파일럿인지, 파일럿의 층, 겹친 id와 차례, 끝남이 아닌 회차와 준비가 실패한 회차의 게이트, 게이트 셋의 차례와 준비 명령, 끝남의 결과 커밋, 결과 커밋과 고른 규칙, 회차 폴더 이름, 숨은 시험의 수와 실패 노드), 두 쓰기의 다시 풀기와 덮어쓰기 거부, 기록 쓰기가 실패할 때 남는 파일, 회차 폴더 이름 풀기와 다음 회차 번호, 노드 ID 자르기와 그 파일 부분의 꼴, 시험 지원 파일 칸의 꼴, 판정 칸의 게이트·숨은 시험, import 경계 | 이 티켓의 시험이 빨강을 본 근거(implement 스킬) | `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/model-rerun/probes/rerun_files_mutations.toml`. pytest 변이만이고 바깥에 닿지 않는다 | — |
| `rerun_hidden_mutations.toml` | 티켓 02(숨은 시험 가르기, `tools/rerun_hidden.py`)의 시험이 무는지. 조건 2의 실패 종류 셋(`AttributeError`·`NameError`·`TypeError`)과 오류 요소, 조건 3의 B 유무, 조건 1의 둘째 실행과 M에서 돌지 않은 바뀐 시험, junit의 같은 노드 둘 가운데 나쁜 쪽, 줄바꿈이 든 문자열 나누기, `git grep`의 `-e`·낱말 경계·`tests/` 빼기, 모음 오류 뒤 이어 돌기와 파일째 넘기기, 걷기 전 링크 끊기, 덮을 자리의 링크(작업 트리 자리 자체 포함)와 덮지 못한 자리, 자식 환경의 `VIRTUAL_ENV`와 저장소 변수, BOM 벗기기, 못 보는 것 둘(junit을 남기지 않은 B의 pytest, 소스 표기와 다른 문자열 값), 티켓 05가 실제 후보 표에서 찾은 NUL 나누기 | 이 티켓의 시험이 빨강을 본 근거(implement 스킬, 티켓의 `tools/mutate.py` 항목) | `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/model-rerun/probes/rerun_hidden_mutations.toml`. pytest 변이만이고 임시 저장소 밖에 닿지 않는다. 임시 저장소에 `sort_candidate`를 부르는 변이는 하나에 수 초에서 수십 초, `git grep` 변이는 약 1초다(2026-10-23 셀프 리뷰 표준 축이 다른 세션이 함께 돌던 때 돌려 앞의 것이 3.3~26.4초였다) | — |
| `rerun_judge_mutations.toml` | 티켓 03(다시 풀기 판정, `tools/rerun_judge.py`)의 시험이 무는지. 후보 조건 셋(경계와 빼기, 셀 수 없는 구간), 결론 없음 셋(T와 S_A의 양쪽 경계, 해시, 끝 표지와 표지의 수), 쓰는 회차(파일럿, 가장 큰 조건 판, 가장 작은 회차 번호, 다른 판과 모르는 판, 회차가 없거나 목록에 없는 과제, 기록 꼴이 아닌 파일), 구간(5% 문턱, C_A가 0인 표본), U가 같은 후보의 차례, 결론 없음의 탐색 머리, 명령 줄 입구(해시 상수 넘기기, 기록 폴더, 꼴 오류, 파일럿 목록, 모듈로 띄우기), 탐색의 거르기(올리기 짝과 D에서 C로 올리는 짝, 빈 토큰 칸, 원래 세션의 레벨) | 이 티켓의 시험이 빨강을 본 근거(implement 스킬) | `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/model-rerun/probes/rerun_judge_mutations.toml`. pytest 변이만이고 바깥에 닿지 않는다 | — |
| `official_cost/compare.py`, `official_cost/2026-10-28.log` | 판 2 기록의 세션·모델마다 세션 기록 파일의 응답 셈과 `modelUsage`의 `costUSD`, 칸마다 모자란 토큰, 그 몫을 같은 단가로 채운 뒤의 남는 차(채운 캐시 쓰기 5분·1시간 두 갈래) | 견준 아홉(Opus 넷, Sonnet 다섯) 모두 채운 쓰기를 5분으로 셈하면 남는 차가 0.0000이다. 응답 셈만으로는 `costUSD`의 0.72~1.00배였다. 모자란 칸은 출력(아홉 가운데 여덟), Opus는 입력·캐시 읽기·캐시 쓰기도였다. 1시간 쓰기 몫이 큰 Opus에서도 맞아 1시간 2배·5분 1.25배는 두 모델에서 같다. 채운 쓰기를 1시간으로 셈한 갈래는 Opus에서 0.0011~0.0287달러가 남아 두 갈래가 갈린다. 모자란 까닭은 재지 않았다. 이 결과로 `tools/rerun_cost.py`가 모자란 칸을 채운다(티켓 11 "공식 단가 셈을 Opus로 대 본다") | 커밋한 기록과 이 PC의 전용 설정 폴더 기록 파일로 다시 돈다. 세션·모델 하나가 회차이고 그 모델의 응답이 기록 파일에 있어 견준 것이 측정이다. 측정 아님(기록 파일이나 응답이 없다)이 있거나 측정이 없으면 종료 1. 2026-10-28 실행은 측정 9, 측정 아님 0이었다 | Claude Code 2.1.302(복사본), 전용 설정 폴더, Windows 10 이 PC |
| `pilot_checks/`(관찰 스크립트 열: `scan_streams.py`, `scan_records.py`, `clone_ledger.py`, `compact_handoff.py`, `extra_sessions_cost.py`, `key_checks.py`, `ratelimit.py`, `start_parts.py`, `handoff_reasons.py`, `result_texts.py`) | 파일럿 회차의 기록, 회차 폴더의 stream-json 원본, 전용 설정 폴더의 세션 기록, 주 체크아웃 사용량 장부에서 설계 8절 확인에 쓸 값(init 칸, 모델 줄 수, 한도 이벤트 칸, 커밋 훅 줄, 클론 장부, 압축과 인계, 하위 세션의 공식 단가, 키 변수 확인, 시작 컨텍스트 크기, 결과 글의 끝)을 찍는다. 단언하지 않는 관찰 스크립트이고, 출력은 손으로 본 근거다. 측정 표지를 세지 않아 `.claude/rules/probes.md` 첫 항목의 프로브가 아니고, 결과 절은 그 수를 측정이 아니라 손으로 본 것으로 적는다. 파일마다 받는 인자는 그 독스트링이다 | "2026-10-27 결과: 파일럿(설계 8절의 확인)", 티켓 11 "설계 8절의 확인" | 회차 뿌리(`--rounds`), 전용 설정 폴더의 `projects`(`--projects`), 장부 폴더(`--ledger`)를 인자로 준다. 모델을 부르지 않는다. `key_checks.py`·`scan_streams.py`·`compact_handoff.py`·`handoff_reasons.py`는 세션의 명령과 글을 앞 120~160자 옮겨 찍어, 세션이 비밀 값을 출력했다면 함께 찍힌다. 출력을 커밋하지 않는다 | Claude Code 2.1.302(복사본), 전용 설정 폴더, Windows 10 이 PC |
| `records/`(러너 `tools/rerun_runner.py`가 쓴 파일럿 회차 기록. 조건 판 1 다섯(회차 번호 1·2), 판 2 여섯(3·4, E 는 2·3)) | 파일럿 회차마다 끝, 비용, 시간, 게이트·숨은 시험, init 도구 목록, 오염 | 일지 2026-10-28-10 "파일럿 첫 실행"·"파일럿 판 2", 티켓 11 "러너로 파일럿 목록을 돈다"의 2026-10-27 주석 | 다시 돌지 않는다. 기록마다 `condition_version`이 판이다 | Claude Code 2.1.302(복사본), 전용 설정 폴더의 njh4803, Opus, Windows 10 이 PC |
| `regate/`(스크립트 `regate.py`, 2026-10-27 출력 `2026-10-27.log`·`2026-10-27-merge.log`) | 판 1 결과 커밋 셋(conversation-02-A-1, end-user-continuation-02-A-1·A-2)에 고친 환경(판 2의 허용 목록과 B 설정의 `env`)으로 게이트와 숨은 시험만 다시 돌 때의 결과. `--merge`면 결과 커밋 대신 그 과제의 M 을 돌아, 숨은 시험이 M 에서 통과하는지(회차의 실패가 시험의 결함이 아닌지) 본다. 모델 세션은 띄우지 않는다. 판정하지 않고 결과를 찍기만 하며, 판 1의 나머지 둘(conversation-02-A-2, E 회차)은 돌지 않았고 `--merge`는 E 의 과제를 돌지 않았다 | 일지 2026-10-28-10 "실행 조건 고침"의 다시 돌기 줄과 "파일럿 판 2"의 M 줄 | `uv run python .scratch/model-rerun/probes/regate/regate.py <저장소> .scratch/model-rerun/probes/pilot.json .scratch/model-rerun/probes/records <옛 회차 뿌리> <새 뿌리> <설정 폴더> [--merge] <기록 이름>...`. 옛 회차 뿌리의 클론이 남아 있어야 한다(`--merge`는 쓰지 않는다). 게이트 하나에 수십 분 | 이 PC(Windows 10, 파이썬 3.12). `2026-10-27.log`는 기준 1bd70d62 의 작업 트리, `2026-10-27-merge.log`는 기준 175fb884 의 작업 트리(`--merge`를 더한 판) |
| `rerun_round_mutations.toml` | 티켓 04(회차의 자리, `tools/rerun_round.py`)의 시험이 무는지. 뿌리와 설정 폴더의 거부(상대 경로와 구분자 둘로 시작하는 장치·UNC 경로, 주 체크아웃과 `~/.claude`의 머리, 링크를 풀기 전과 푼 꼴, 윈도가 쓸 꼴, `realpath`의 장치 접두를 떼어 가운데 조각 끝의 공백·점 둘을 자식과 상관없이 막는 것과 그 경로가 있으면 받는 것, 대소문자, 조각 단위 견줌), 상위의 `.claude/`와 `CLAUDE.md`와 홈 빼기, 주 체크아웃이 worktree 목록의 첫 줄인 것, 표지의 내용과 덮어쓰기 거부, bare 로 B 만 미는 것(태그, M, 원본 설정의 `push.followTags`, 사용자 설정의 원격 이름, 원본의 pre-push 훅), 클론과 bare 의 ref·M 개체 대 보기, git 자식 환경의 저장소 위치 변수, 막는 규칙의 경로 꼴·도구 목록·링크를 푼 꼴, 막는 규칙 파일의 자리(회차 폴더)와 덮어쓰기 거부, 준비의 멈춤·시간 넘김·찾지 못한 명령·위치 변수·벽시계, 세션 환경의 허용 목록과 gh 설정 폴더, 지우기의 표지·이름 꼴·뿌리 바로 아래의 링크·기록·기록의 폴더 이름·표지를 맨 끝에 지우기·글자 그대로의 표지 이름·빈 폴더를 지우지 못할 때 표지 다시 심기·폴더의 읽기 전용 특성·지우기 직전의 링크 재확인·끊지 못한 링크에서 멈추기·링크를 찾다 막힌 폴더만 실패로 알리기·지우다 막힌 까닭·파일인 뿌리·읽지 못한 뿌리, 명령 줄의 없는 뿌리 알림과 UTF-8 출력. 대조군 하나(링크를 먼저 끊지 않아도 이 PC 에서는 바깥 파일이 남는다. 시험이 만드는 링크는 윈도에서 junction, 리눅스에서 심볼릭 링크이고, 이 PC 에서 본 것은 junction 이다). 결과는 아래 변이 절 | 이 티켓의 시험이 빨강을 본 근거(implement 스킬) | `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/model-rerun/probes/rerun_round_mutations.toml`. pytest 변이만이고 임시 폴더의 git 저장소 밖에 닿지 않는다 | 이 PC(Windows 10, 파이썬 3.12) |
| `branches.json` | 과제 고르기(티켓 05)가 원래 브랜치와 PR 앞 비용을 읽는 브랜치 표. 소급 측정의 수집 도구가 쓴 것이고, 칸은 그 도구 README의 `branches.json` 행이 적는다(수와 이름, 첫 사람 트리거 시각과 지시문 줄 값만 있고 프롬프트와 티켓 본문은 없다) | `candidates.md`의 원래 브랜치와 PR 앞 비용 칸, 티켓 05 "실제 후보 표" | `PYTHONUTF8=1 uv run python .scratch/harness/probes/session_cost/collect.py --refresh --out .scratch/model-rerun/probes/branches.json`. 사람의 기본 설정 폴더의 세션 기록과 `gh`를 읽는다. `--out` 없이 치면 소급 측정의 `branches.json`을 덮는다 | 2026-10-24, origin/main 80ff61f1 때, 이 PC(티켓 11 파일럿 앞에서 다시 모았다. 첫 판은 2026-10-23 c3c2cfcf 때). 커밋 전에 이메일·키·사용자 경로 꼴을 grep으로 찾아 0건이었다(손으로 봤다) |
| `branches-2026-10-23.json` | 위 `branches.json`의 첫 판(2026-10-23 c3c2cfcf 때 모은 것)을 그대로 꺼낸 것. 2026-10-23 06:02(UTC)에 데스크톱 앱에서 세션 113개가 지워지며 기록 파일도 지워져, 다시 모은 표의 PR 앞 비용이 줄었다(지움 표지 `<세션 id>.desktop-released.json`의 `"reason": "delete"`와 그 수를 `ls`·`find`로 손으로 봤다. 비용이 준 까닭이 그 지움이라는 것은 크게 준 브랜치가 모두 그 시각 앞에 병합된 것에서 미룬 어림이다). 고르기는 이 표를 `--earlier-branches`로 받아 브랜치마다 PR 앞 비용이 큰 쪽을 쓴다(티켓 11이 사람과 정했다) | `candidates.md`의 PR 앞 비용 칸과 회차 상한, 일지 2026-10-28-10 "기록이 줄어든 까닭" | 다시 모으지 않는다. `git show db3e90db^:.scratch/model-rerun/probes/branches.json`으로 꺼냈다 | 2026-10-23, origin/main c3c2cfcf 때, 이 PC |
| `revive.json` | 바깥 검증 낱말에 부정문·인용·다른 뜻으로 걸린 후보를 되살릴 목록(과제 id → 까닭). 티켓 11이 사람과 정했다. 사람이 고른 일곱 가운데 `-m llm`만으로 걸린 셋(end-user-channel-05·04, conversation-04)은 같은 티켓이 그 낱말을 목록에서 빼 되살리지 않아도 후보로 돌아오므로 뺐다(되살리기는 낱말에 걸린 후보만 받는다) | `candidates.md`의 되살림 표시, 사전 등록 절 | 사람과 다시 정할 때만 고친다 | — |
| `candidates.md` | 티켓 05의 실제 후보 표. main c3c2cfcf의 첫 부모 줄에서 찾은 후보 77개가 한 행씩이고, 남았는지와 빠진 까닭, 맞은 낱말, PR 앞 비용, 크기, 숨은 시험 수와 빠진 노드의 요약, 거슬러 채웠는지, B의 준비·게이트 파일을 든다. 끝 줄은 날짜 안의 남은 후보 수, 거슬러 채워 남은 수, 그 가운데 준비·게이트 파일이 없는 B의 수, 푼 티켓 파일이 둘 이상인 병합 커밋이다 | 티켓 05 "실제 후보 표", 파일럿(티켓 11)이 사람에게 길을 묻는 자리 | `PYTHONUTF8=1 uv run python -m tools.rerun_select table --branches .scratch/model-rerun/probes/branches.json --earlier-branches .scratch/model-rerun/probes/branches-2026-10-23.json --revive .scratch/model-rerun/probes/revive.json --table .scratch/model-rerun/probes/candidates.md --rev 80ff61f1`(티켓 11의 판. 05의 첫 판은 앞의 둘 없이 `--rev c3c2cfcf`). 싼 조건을 지난 후보마다 작업 트리 둘을 꺼내 `uv sync`와 pytest를 돌린다. 2026-10-23에 38개를 가르는 데 2시간 52분 걸렸다(명령을 띄운 시각과 표 파일을 쓴 시각으로 손으로 셌다, 일지 2026-10-23-43) | de5423bd의 `tools/rerun_select.py`·`tools/rerun_hidden.py`(NUL 나누기 전), Windows 10 이 PC. 아래 결과 절의 02 행 |
| `rerun_select_mutations.toml` | 티켓 05(과제 고르기, `tools/rerun_select.py`)의 시험이 무는지. 푼 티켓 찾기(`done` 머리, B의 `done`, B에 없는 티켓 파일, 푼 티켓 파일이 둘 이상인 커밋), 원래 브랜치의 `feature/`, 바깥 검증 낱말의 대소문자와 파일 이름, PR 앞 비용의 문턱과 셈, 되살리기의 거부, 숨은 시험의 문턱과 싼 조건 뒤에만 가르기, 날짜 바닥의 경계, 거슬러 채우기의 차례와 멈춤, 닿지 않은 행의 까닭, 표 칸의 파이프와 준비·게이트 셈, 크기 동률, 겹친 id, 파일럿의 아래 삼분의 일과 씨앗, 본 측정의 파일럿 빼기와 층 씨앗과 큰 층의 나머지, 엇갈린 차례와 갈래 계획의 씨앗, 회차 상한의 바닥, 병합 기록의 첫 부모 줄과 제목 끝 PR 번호와 BOM, 자식 환경의 저장소 변수와 git 시간 제한, 출력 자리와 쓰기 실패, 본 측정 명령, 표 머리의 입력 경로 | 이 티켓의 시험이 빨강을 본 근거(implement 스킬). 구현을 시험보다 먼저 썼다 | `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/model-rerun/probes/rerun_select_mutations.toml`. pytest 변이만이고 임시 저장소 밖에 닿지 않는다 | — |
| `rerun_session_mutations.toml` | 티켓 06(회차의 세션 하나, `tools/rerun_session.py`)의 시험이 무는지. 첫 줄의 틀이 `open_session.ps1`과 같은 것, 지시문의 모델 줄, 명령의 예산을 센트 아래에서 버리기(반올림하지 않기, 이진 부동소수에서 버리지 않기), 끝난 자식의 구동(손자가 출력을 쥐어도 EOF를 마감까지 기다리지 않기, 마감에 닿았을 때 이미 끝난 자식을 끈 호출로 적지 않기, 기록 파일을 열지 못하면 띄운 자식을 끄기), 호출 칸의 종료 코드, 세션 비용이 그 세션 id의 마지막 값인 것, 결과 글의 빈 글과 공백 글 건너뛰기, `type`이 글이 아닌 줄과 깊게 중첩된 줄, 기록 파일 찾기(작업 폴더 이름 아래, 서브에이전트)와 `<synthetic>` 빼기, 기록 줄을 글 안의 U+2028에서 가르지 않기, 결과 커밋의 세 규칙과 main 빼기, git 자식 환경의 저장소 위치 변수, 띄우기 전의 세션 id, 기록의 init 도구와 subtype의 꼴, 세션 환경의 PATH에서 가상 환경 빼기와 상대 조각·루트를 견주지 않기(티켓 04의 `session_env`). 표지는 고른 단언의 값 비교 문구다 | 이 티켓의 시험이 빨강을 본 근거(implement 스킬) | `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/model-rerun/probes/rerun_session_mutations.toml`. pytest 변이만이고 임시 폴더 밖에 닿지 않는다. 가짜 `claude`(`tests/tools/fake_claude.py`)를 띄우는 변이도 그 임시 폴더 안에서 돈다. 손자 갈래의 가짜는 아무것도 쓰지 않고 자는 손자를 파이썬 실행 파일의 폴더에서 띄워 시험 뒤에도 최대 150초 남긴다. "끝난 자식을 보지 않고 EOF 를 기다린다"는 시간 제한 120초까지 기다려 약 2분이 든다(2026-10-23 손으로 한 번 돌려 130.81초) | 이 PC(Windows 10, 파이썬 3.12) |
| `rerun_gates_mutations.toml` | 티켓 07(게이트와 숨은 시험, `tools/rerun_gates.py`)의 시험이 무는지. 결과 커밋만 보기(클론에서 게이트와 숨은 시험을 돌기), 게이트 전의 덮기, 지원 파일 덮기, 게이트 셋을 다 돌기와 함께 쓰는 몫, 시간 넘김으로 적기와 손자까지 끄기, 숨은 시험이 시간을 넘긴 뒤의 xml, 앞선 xml 지우기, 덮을 자리의 링크, 걷기 전 링크 끊기(작업 트리와 클론의 관리 폴더)와 끊지 못할 때 걷지 않기, 작업 트리 자리와 클론의 git 폴더가 링크면 걷지 않기, 작업 트리 자리가 링크면 게이트를 띄우지 않기, 걷기, 자식 환경의 저장소 변수와 `VIRTUAL_ENV`, 결과 커밋의 꼴, 준비가 실패한 뒤 멈추기와 끝난 꼴 옮기기, 게이트가 모두 0일 때만 숨은 시험 돌기, 노드가 없으면 숨은 시험을 띄우지 않기, 겹친 노드를 한 번만 세기, junit 노드의 매개변수 자르기와 같은 노드 둘, 실패·오류·건너뜀·없는 노드·풀리지 않는 xml·UTF-8 이 아닌 xml. 이 티켓이 고친 회차 기록의 끝난 꼴 두 칸(`tools/rerun_files.py`), 04의 `SetupFailed` 불변식, 모은 링크 끊기(`tools/tidy_checkouts.py`의 `cut_links`)와 그 뿌리가 링크인 때와 MAX_PATH 에 걸리는 깊은 폴더와 돌려주는 경로의 잇기(끝 구분자를 뗀 뿌리, 읽지 못한 뿌리), `_Git`이 git 의 시간 넘김과 띄우지 못함을 `GateError`로 바꾸는 것, 게이트가 B 설정의 `env`를 얹는 것과 그 글 값만 고르는 것(티켓 11)도 겨눈다. 결과는 아래 변이 절 | 이 티켓의 시험이 빨강을 본 근거(implement 스킬) | `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/model-rerun/probes/rerun_gates_mutations.toml`. pytest 변이만이고 임시 폴더의 git 저장소 밖에 닿지 않는다. 숨은 시험의 셈을 겨누는 변이는 `-vvv`를 준다(아래 변이 절) | 이 PC(Windows 10, 파이썬 3.12) |
| `rerun_cost_mutations.toml` | 티켓 07(공식 단가, `tools/rerun_cost.py`)의 시험이 무는지. 응답을 가르는 키 셋(message id, uuid, 줄 차례), 같은 id 에서 고르는 usage(첫 것, 마지막 것), 1시간 배수, 남는 몫과 1시간 몫 자르기, Haiku 의 경계·높은 단가·프롬프트에 드는 캐시 쓰기, synthetic, 모델이 없는 응답, 이름의 1m·날짜 꼬리와 `modelUsage` 이름 견줌(모자란 칸 채우기의 견줌은 티켓 12), 대신 셈의 유무·배수·이름과 꼬리만 다른 이름 더하기, subagents, 없는 기록 파일, 기록 줄을 `\n`으로만 가르기, 세션 셈에 대신 셈한 단가 더하기, 회차 합의 대신 셈 더하기와 빈 칸 | 이 티켓의 시험이 빨강을 본 근거(implement 스킬) | `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/model-rerun/probes/rerun_cost_mutations.toml`. pytest 변이만이고 바깥에 닿지 않는다 | — |
| `rerun_continue_mutations.toml` | 티켓 08(이어 가기와 상한 `tools/rerun_continue.py`, 끄기 `tools/rerun_session.py`, 명령 줄 읽기 `tools/proc_command_line.py`)의 시험이 무는지. 물음표 끝(공백만 든 줄, 끝 공백, 전각), 인계 지시문을 옮기는 머리 줄과 끝 줄과 덩이 고르기(뒤의 덩이부터 그 브랜치의 덩이, 그런 덩이가 없을 때), 다음 호출의 종류(같은 브랜치의 지시문, B 뒤 커밋), 호출 앞의 끝(세션·개입 상한의 경계, 남은 예산 $1), 호출 뒤의 끝(시간, 예산, init, 결과 이벤트 없음, 출력을 닫고 멈춰 끈 호출과 끄지 못한 호출, 막는 판정의 차례), 예산에서 이어 부를 세션이 쓴 몫, 개입의 `--resume`과 그 수, 인계의 새 세션 id와 지시문만 넘기기, 첫 줄의 연 저장소와 작업 폴더가 같은 글인 것(06의 표에서 옮겼다), 끝남이 아닌 회차의 물으며 끝남, 지시문 담음, 끄기(명령 줄 확인, 읽지 못함, 나무째, 거두는 기다림의 마감, 거둠의 제한과 시간 넘김, 멈춘 꼴 `Stop`의 끈 것과 남긴 것, 러너가 끊김, 끄지 않은 호출의 호출 칸, 마감에 끈 세션의 표시), 티켓 09가 더한 줄 판정의 끄기(참인 줄에서 읽기 멈추기, 끈 호출 뒤 잇지 않기, 세션의 끈 표시, 남긴 호출의 호출 칸, 멈춘 꼴 `Stop.HALTED_*`), 이어 부르는 명령, 호출 차례, 명령 줄 읽기(PEB 의 자리, proc 의 끝 NUL, 훅에서 옮긴 사본의 함수와 API 원형). 표지는 고른 단언의 값 비교 문구와 단언 메시지다 | 이 티켓의 시험이 빨강을 본 근거(implement 스킬) | `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/model-rerun/probes/rerun_continue_mutations.toml`. pytest 변이만이고 임시 폴더 밖에 닿지 않는다. 가짜 `claude`를 띄우는 변이도 그 임시 폴더 안에서 돈다. "나무째 끄지 않고 그 프로세스만 끈다"는 아무것도 쓰지 않고 자는 가짜의 자식을 시험 뒤에도 최대 600초 남긴다. 그 변이와 "거두는 기다림이 호출의 마감을 넘는다"는 하나에 약 1분이 든다(2026-10-23 표 전체를 두 번 돌린 도구 출력에서 61.08~62.73초). "줄 판정이 참이어도 읽기를 멈추지 않는다"는 그 시험이 마감 30초에 끌 때까지 기다려 약 31초다(2026-10-24 그 변이만 돌린 도구 출력에서 30.88초). 나무째 끄기의 변이는 `taskkill` 줄이라 윈도에서만 뜻이 있고, POSIX 의 그룹 끄기는 리눅스 CI 의 같은 시험이 본다 | 이 PC(Windows 10, 파이썬 3.12) |
| `rerun_checks_mutations.toml` | 티켓 09(측정 아님 가르기, `tools/rerun_checks.py`)의 시험이 무는지. 계정(로그인, 계정 이름, 글자 그대로의 설정 폴더), 설정 폴더의 `env`와 그 끝(기록 없이 멈추지 않고 측정 아님(설정)), init(빈 MCP, 플러그인 `source`, 줄 판정), 모델(별칭, `inherit`, 본 세션의 노력, 서브에이전트의 `<synthetic>`, Agent 입력이 고른 모델과 그 세션 단위, 하네스 모델의 `sonnet`), 셸 명령의 낱말 `gh`(커밋 메시지 떼기, 명령 앞의 셸 예약어, 명령 치환이 든 메시지, heredoc 두 길, 따옴표 없는 구분자의 `$(cat`, `--` 뒤), 경로(조각 경계와 중괄호, 자기 회차, 자기 세션 기록, 링크를 푼 꼴, Git Bash 꼴, `~/.claude`와 홈 아래의 설정 폴더·뿌리를 대신하는 이름, 경로 칸의 상대 경로, 글 칸), 쓰기 내용(`.md`, `tests/`, Git Bash 꼴의 대상), `Monitor`의 웹소켓 입력, 거부된 호출과 그 수, Skill 이름의 접두, 기록의 도구 이름, 한도(시각 하나라도 못 읽음, `bool`), 판정 차례 둘, 사용률의 첫 값. 표지는 고른 단언의 값 비교 문구와 실패한 매개변수 사례의 id 다 | 이 티켓의 시험이 빨강을 본 근거(implement 스킬) | `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/model-rerun/probes/rerun_checks_mutations.toml`. pytest 변이만이고 임시 폴더 밖에 닿지 않는다. 허용 밖 init 에서 끄는 실제 프로세스 시험은 고르지 않는다. 줄 판정을 지우면 가짜가 init 뒤에 멈추는 600초를 기다린 뒤에야 빨개지기 때문이고, 줄 판정이 허용 밖 init 에서 참인지는 이 표의 "줄 판정이 허용 밖 init 에서도 끄라고 하지 않는다"가, 참인 줄에서 읽기를 멈추고 끄는지는 continue 표의 "줄 판정이 참이어도 읽기를 멈추지 않는다"가 본다 | 이 PC(Windows 10, 파이썬 3.12) |
| `rerun_runner_mutations.toml` | 티켓 10(러너 명령, `tools/rerun_runner.py`)의 시험이 무는지. 변이마다 갈래 하나를 되돌리고 그 갈래는 변이의 이름이 적는다. 예를 들면 다시 띄우기의 판정(측정 아님을 끝난 회차로 세기, 판을 보지 않기, 판을 올린 과제를 id 없이 돌기, id 무시, 오염의 셋째), 어림의 남은 회차, 예산의 쓴 것, 과제의 실행 차례, 동시에 셋, 회차 번호의 뿌리 아래 폴더, 한도의 기다림(돌던 동안, 다시 뜬 때)과 시각을 모르는 한도의 멈춤, 돌던 동안 오염의 셋째, 측정 아님의 멈춤, 인계 확인의 판(돌던 동안, 다시 뜬 때), 본 측정의 해시, 결과 이벤트 없는 세션의 비용 대신 넣기, 기록의 게이트 이름, 죽은 회차(돌고 있는 세션, 비용 대신 넣기), 같은 프로젝트 폴더의 다른 세션(티켓 11·12)과 그 비용이 예산 멈춤에 드는 것(티켓 12)이다 | 이 티켓의 시험이 빨강을 본 근거(implement 스킬). 시험을 러너와 함께 써서 러너가 없을 때의 빨강을 보지 못했다(일지 2026-10-24-07) | `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/model-rerun/probes/rerun_runner_mutations.toml`. pytest 변이만이고 임시 폴더 밖에 닿지 않는다. 가짜 `claude`와 임시 저장소로 회차를 끝까지 도는 변이는 하나에 수 초에서 수십 초다 | 이 PC(Windows 10, 파이썬 3.12) |

## 사전 등록(본 측정)

<!-- 사전 등록 시작 -->

이 절이 본 측정의 판정 정의 전부다. 결과를 보기 전(본 측정의 첫 회차 전)에 쓰고, 내용(두 표지 사이 글의 UTF-8)의 SHA-256을
판정 도구 `tools/rerun_judge.py`의 `PREREG_SHA256`으로 고정했다. 그 해시가 다르면 러너는 본 측정 회차를 열지 않고 판정은
결론 없음이다. 원천은 설계(`.scratch/model-rerun/design.md`) 3~6절과 그것을 고친 명세(`.scratch/model-rerun/spec.md`)이고,
둘이 다르면 명세를, 글과 코드가 다르면 실제로 도는 코드를 적었다. 괄호의 절 이름은 출처다. 아래 "코드 상수" 줄의 값은
`tests/tools/test_rerun_prereg.py`가 모듈마다의 `PREREG_VALUES`와 대 보고, "과제 목록"과 "되살릴 목록"의 JSON은 같은 시험이
`main.json`·`revive.json`과 대 본다. 명령 줄로 받는 값(본 측정 예산 상한 $1,600, 계정 이름 njh4803, `claude` 복사본 경로)은
코드 상수가 아니라 그 시험이 잡지 못한다. 이 절이 `<모듈>.<이름>`으로 상수를 부르는 이름은 그 모듈 `PREREG_VALUES`
표의 키다(함수를 부를 때는 함수 이름 그대로다). 모듈 속성 이름과 같거나, 앞 밑줄을 뗀 이름이거나(`rerun_checks.GH`는 `_GH`), 여러 상수를 묶은 이름이다
(`rerun_select.SEEDS`, `rerun_gates.LIMITS`, `rerun_checks.LIMIT_MARKERS`). 정규식은 글과 켠 플래그를 함께 싣는다
(`rerun_files.prereg_pattern`).

### 모집단(과제 고르기와 숨은 시험)

- 후보는 main의 첫 부모 줄에서 부모가 하나인 squash 병합 커밋 M이다. B는 M의 부모다(설계 3절, 명세 "과제 고르기").
- 푼 티켓: M이 바꾼 티켓 파일(`rerun_select.TICKET_PATH`) 가운데 B의 `Status:` 값이 `done`(`rerun_select.DONE`)으로 시작하지 않고 M의 값이 그것으로 시작하는 파일. 값은 줄 머리가 `Status:`나 `**Status:**`인 첫 줄의 첫 낱말이고, B에 없는 파일은 값이 없다. 그런 파일이 정확히 하나인 M만 후보다(명세 "후보를 찾는 자리").
- 아래를 모두 맞아야 후보로 남는다(명세 "과제 고르기", 설계 3절 "과제의 조건").
  - B에 그 티켓 파일이 있다.
  - M 제목 끝에 PR 번호 `(#NNN)`가 있고, 브랜치 표에서 `prs`에 그 번호가 든 행이 정확히 하나이며 그 `branch`가 `feature/`(`rerun_select.BRANCH_PREFIX`)로 시작한다. 그 이름이 원래 브랜치다.
  - 브랜치 표는 `.scratch/model-rerun/probes/branches.json`이고, 옛 표 `branches-2026-10-23.json`을 함께 받아 브랜치마다 PR 앞 비용이 큰 쪽의 행을 쓴다. 표에 없는 브랜치는 빠진다.
  - 원래 세션의 PR 앞 비용(그 행의 `cost` − `cost_post_pr`)이 $70(`rerun_select.COST_LIMIT_USD`) 이하다.
  - 티켓 파일 이름에 `human-verification`(`rerun_select.EXTERNAL_NAME`)이 들지 않는다. 되살릴 수 없다.
  - B의 티켓 글에 바깥 검증 낱말(`rerun_select.EXTERNAL_TERMS`)이 대소문자를 가리지 않고 하나도 없다. 이 낱말로만 빠진 후보는 되살릴 목록(아래 표)에 든 것만 되살린다.
  - 파이썬 숨은 시험이 셋(`rerun_select.MIN_HIDDEN`) 이상이다. 가르기가 실패한 후보는 빠진다.
- 날짜: B의 커밋 시각이 2026-10-12T00:00+09:00(`rerun_select.DATE_FLOOR`) 이후인 후보를 먼저 본다. 남은 후보가 열둘(`rerun_select.MIN_CANDIDATES`)보다 적으면 그 앞의 후보를 M의 커밋 시각이 늦은 것부터 하나씩 더하고, 더한 후보도 위 조건을 모두 지나야 남는다(명세 "층과 수").
- 숨은 시험(명세 "숨은 시험 가르기"). 파이썬(pytest) 시험만 쓴다. 단위는 pytest의 노드 ID이고 매개변수화한 경우는 따로 센다.
  - 바뀐 시험: M과 B의 `tests/` 아래 시험 파일에서 모듈 수준 `test_*`와 `Test*` 클래스의 `test_*` 메서드 가운데, M에 새로 생겼거나 함수 정의(데코레이터 포함)의 AST 덤프가 다른 것.
  - 시험 파일은 `tests/` 아래 `test_*.py`, 시험 지원 파일은 `conftest.py`와 `tests/` 아래 시험 파일이 아닌 `.py`다.
  - B와 M을 각각 꺼낸 작업 트리에서 그 작업 트리의 환경으로 준비(`rerun_hidden.SETUP_COMMANDS`)하고 `rerun_hidden.PYTEST_COMMAND`로 돌린다.
  - 조건 1: M에서 두 번 돌려 두 번 다 통과한 노드만 남는다.
  - 조건 2: B에 M의 시험 파일과 M이 바꾼 지원 파일을 덮고 돌린 junit xml에서 `error` 요소인 노드, `failure`의 `message`가 `rerun_hidden.NAME_ERRORS`의 이름으로 시작하는 노드, 통과하거나 건너뛴 노드, 결과가 없는 노드는 빠진다. 나머지 `failure`는 남는다.
  - 조건 3: 시험 함수 본문의 이름(`Name`의 id, `Attribute`의 attr)과 길이 둘 이상의 문자열 상수(줄바꿈과 NUL에서 나눈 조각마다) 가운데 하나라도 M의 `tests/` 밖 추적 파일에 있고 B의 추적 파일 어디에도 없으면 그 함수의 노드가 모두 빠진다. 이름은 `git grep -w -F`, 문자열은 `git grep -F`로 찾는다.
- 크기 지표: B의 티켓 글에서 `rerun_select.BACKTICK_PATH`에 맞는 서로 다른 파일 경로의 수.
- 층과 고르기(명세 "층과 수", "씨앗", "실행 차례").
  - 남은 후보 n개를 크기 지표로 정렬한다. 동률은 M의 커밋 해시 순이다.
  - 파일럿: 아래 ⌊n/3⌋개를 `random.Random(1)`로 섞어 앞의 셋. 갈래 계획은 `rerun_select.PILOT_PLANS`.
  - 본 측정: 커밋한 파일럿 목록의 과제를 뺀 m개를 아래 ⌊m/3⌋개(작은), 가운데 ⌊m/3⌋개(중간), 나머지(큰)로 자르고 층마다 씨앗 2·3·4로 섞어 앞에서 셋·셋·둘(`rerun_select.MAIN_COUNTS`)을 고른다. 파일럿 셋은 다시 고르지 않는다. 씨앗 목록은 `rerun_select.SEEDS`.
  - 실행 차례는 작은 1, 중간 1, 큰 1, 작은 2, 중간 2, 큰 2, 작은 3, 중간 3이다. 차례 i(0부터)의 갈래 계획은 다섯 갈래를 `random.Random(100 + i)`로 섞은 것이다.
  - 회차 상한은 과제마다 PR 앞 비용의 3배(`rerun_select.CAP_MULTIPLIER`)와 $40(`rerun_select.CAP_FLOOR_USD`) 가운데 큰 값이다.
  - 후보 표에는 B마다 `rerun_select.SETUP_FILES`가 있는지 적는다.
- 고르기 도구는 회차의 결과를 읽지 않는다.
- 과제 목록(과제 id, B, M, 원래 브랜치, 층, 크기 지표, 실행 차례, 갈래 계획, PR 앞 비용, 회차 상한, 숨은 시험 ID, 시험 지원 파일, 원래 세션의 모델과 레벨)은 아래 표다. 되살릴 목록과 그 까닭도 아래 표다.

### 갈래

- 다섯 갈래(`rerun_files.ARMS`, 설계 4절).
  - A(기준): `claude-opus-5-5` / `xhigh`
  - B: `claude-opus-5-5` / `high`
  - C: `claude-opus-5-5` / `medium`
  - D: `claude-sonnet-5-5` / `high`
  - E: `claude-sonnet-5-5` / `medium`
- 기준 갈래는 A(`rerun_judge.BASE_ARM`)이고, 후보가 없을 때 두는 칸은 `Opus 5.5 / xhigh`다.
- 갈래 사이에 다른 것은 `--model`, `--effort`, 지시문의 `모델:` 줄뿐이다.

### 회차의 조건

- **체크아웃.** 회차마다 사람이 명령 줄로 준 뿌리 아래 새 회차 폴더 `<과제 id>-<갈래>-<회차 번호>-<짧은 난수>`를 짓는다. 뿌리와 전용 설정 폴더는 주 체크아웃과 `~/.claude`를 경로 조각 단위로 머리로 갖지 않고, 회차 폴더의 상위(홈은 뺀다)에 `.claude/`가 없어야 한다(명세 "클론과 설정 폴더").
  - 주 저장소에서 B만 bare 저장소의 `main`으로 밀고 그것을 클론한다. 클론의 모든 ref가 B를 가리키고 `git rev-list --all`에 M이 없어야 세션을 연다. `origin`은 그 bare 저장소다.
  - 준비 `rerun_files.SETUP_COMMANDS`를 세션 전에 클론에서 돌고(명령마다 `rerun_round.SETUP_TIMEOUT`초), 비용과 시간에 넣지 않는다. 하나라도 0이 아니면 측정 아님(준비)이고 러너가 멈춘다.
- **설정 폴더와 계정.** 전용 `CLAUDE_CONFIG_DIR`를 쓴다. 회차를 열기 전에 그 폴더로 친 `claude auth status --json`의 `loggedIn`이 참이고, `email`의 `@` 앞이 명령 줄의 계정 이름(njh4803)이며, `configDirectory`가 넘긴 문자열과 글자 그대로 같아야 한다. 아니면 회차를 열지 않고 멈춘다(기록 없음).
  - 그 폴더의 `settings.json`에 `env` 키가 있으면(JSON 객체가 아니거나 읽지 못해도) 러너는 측정 아님(설정)으로 멈춘다. 다른 키는 보지 않는다. 사람이 로그인하며 옮긴 키는 `autoCompactWindow`(400,000), 출력 스타일, 언어다.
  - 모든 호출의 init 이벤트에서 `mcp_servers`가 빈 목록이고 `plugins`의 항목마다 출처가 허용 모임 안이다. 허용 모임은 `rerun_checks.BUILTIN_PLUGINS`(`@builtin`), `rerun_checks.SYNCED_PLUGINS`(`@synced`), 클론의 `.claude/settings.json` `enabledPlugins`에서 값이 참인 키다. 어기면 그 호출을 끄고 측정 아님(설정)이며 러너가 멈춘다.
  - `claude` 실행 파일은 2.1.302의 복사본(`C:\Users\User\.claude-rerun-bin\2.1.302`)을 명령 줄로 준다. 회차마다 `claude --version`을 적는다.
  - 전용 설정 폴더에서 클론의 프로젝트 설정이 켠 `pyright-lsp`가 실리지 않고 사람의 플러그인 스킬이 없는 것은 실제 세션과의 차이로 두고 고치지 않는다(명세 "설정 폴더의 설정"의 2026-10-27 주석).
- **환경 변수.** 세션은 물려받은 환경이 아니라 `rerun_round.ALLOWED_ENV`의 이름 가운데 부모 환경에 있는 것과, 러너가 값을 짓는 `rerun_round.RUNNER_SET_ENV`(설정 폴더, `DISABLE_AUTOUPDATER=1`, 회차 폴더의 빈 `GH_CONFIG_DIR`)로 띄운다. `PATH`에서는 가상 환경의 실행 폴더(부모 폴더에 `pyvenv.cfg`가 있는 폴더)를 뺀다. 기록에는 넘긴 이름만 적는다(명세 "환경 변수").
- **명령.** `claude` `rerun_session.SESSION_FLAGS` `--model <갈래의 전체 이름>` `--effort <갈래의 레벨>` `--settings <회차 폴더의 deny-settings.json>` `--max-budget-usd <남은 값>`이고, 첫 호출에 `--session-id <러너가 지은 uuid>`, 개입 호출에 `--resume <세션 id>`를 붙인다. `--fallback-model`은 주지 않는다. 첫 메시지는 표준 입력으로 넣는다(명세 "명령과 막는 규칙").
- **막는 규칙.** 회차 폴더(클론 밖)의 `deny-settings.json`의 `permissions.deny`다(명세 "명령과 막는 규칙"의 2026-10-27 주석).
  - `rerun_round.FIXED_DENY_RULES` 그대로.
  - `rerun_round.BLOCKED_TOOLS`의 도구 이름만 쓴 규칙.
  - 주 체크아웃과 사용자의 `~/.claude`에 거는 `rerun_round.PATH_TOOLS`의 경로 규칙(링크를 풀지 않은 꼴과 푼 꼴).
  - 뿌리 바로 아래 `rerun_round.ROOT_SHAPE`에 거는 `rerun_round.ROOT_TOOLS`의 경로 규칙.
- **지시문.** 첫 메시지는 첫 줄, 빈 줄 하나, 지시문 전문이다(명세 "지시문과 첫 메시지").
  - 첫 줄은 `rerun_session.START_LINE`에 스킬 파일 `.claude/skills/implement/SKILL.md`(`rerun_session.START_SKILL`), 연 저장소 = 클론의 경로, 인자 = 티켓 경로를 넣은 것이다.
  - 지시문은 아래 열 줄이다. 워크트리 문장은 없다.
    - `다음 작업: <티켓 경로>. <티켓 첫 제목 줄에서 "# NN:"·"# " 머리를 뗀 글>`
    - `다음 단계: 구현`
    - `어디서: 새 세션`
    - `시작 프롬프트: /implement <티켓 경로>`
    - `브랜치: <원래 브랜치>`
    - `모델: <Opus 5.5 또는 Sonnet 5.5> / <갈래의 레벨>`
    - `읽을 것: 없음`
    - `이어받을 상태: 없음`
    - `확인할 선행 조건: 없음`
    - `이번 요청 범위: 구현·리뷰·커밋까지`
- **이어 가기.** 호출이 끝날 때마다 결과 글(글이 빈 것을 뺀 마지막 결과 이벤트의 `result`)과 클론을 보고 셋 가운데 하나로 간다(설계 5절, 명세 "이어 가기와 끝").
  1. 결과 글에 줄 머리 `어디서: 새 세션`이 있고 줄 머리 `브랜치:`의 값이 이 회차의 원래 브랜치다(`tools/hook_prompt_directive.py`의 `directive_branch`). 그 브랜치의 마지막 지시문 덩이를 옮기되 `모델:` 줄을 갈래의 값 한 줄로 바꿔, 같은 갈래·같은 클론의 새 세션을 위 첫 메시지 모양으로 연다. 인계로 세고 개입으로 세지 않는다.
  2. 1이 아니고 결과 커밋이 B 뒤에 있다. 끝남이다. 결과 글에서 공백만 든 줄을 뺀 마지막 줄이 끝 공백을 뗀 뒤 `?`나 `？`로 끝나면 물으며 끝남으로 적는다.
  3. 그 밖. `--resume`으로 `rerun_continue.INTERVENTION_MESSAGE` 한 줄을 넣고 개입 하나로 센다. 모델이 백그라운드 작업을 기다리며 차례를 끝낸 것도 여기다.
  - 결과 이벤트 없이 끝난 호출(러너가 끈 것과 한도 표지가 든 것은 뺀다)은 셋 어디로도 가지 않고 측정 아님(호출)이며 러너가 멈춘다.
  - 본 측정에서 인계가 난 회차가 끝나면, 명령 줄의 확인 인자가 러너의 조건 판과 같지 않은 한 새 회차를 열지 않고 멈춘다.
- **끝.** 이어 가기 2로 끝나면 끝남이다. 판정할 결과 커밋은 지시문 `브랜치:` 이름의 로컬 브랜치의 끝, 그 브랜치가 없으면 main이 아닌 로컬 브랜치 가운데 B 뒤에 커밋이 있는 것이 하나뿐일 때 그 끝이고, 둘 이상이거나 없으면 결과 커밋이 없다(`rerun_files.RULES`). 커밋하지 않은 변경은 쓰지 않는다. 끝의 종류와 하위 이유는 `rerun_files.END_REASONS`다.
- **상한.** 상한으로 끊긴 회차는 풀지 못한 것이다(설계 5절, 명세 "상한과 끄기").
  - 호출마다 넘기는 예산은 회차 상한에서 그 호출 전까지 회차가 쓴 것(세션마다 마지막 `total_cost_usd`의 합, 이어 부를 세션의 몫과 `other_usd` 포함)을 뺀 값이다. 남은 값이 $1(`rerun_continue.MIN_BUDGET_USD`) 미만이거나 결과 `subtype`이 `error_max_budget_usd`면 상한으로 끊김(예산).
  - 개입이 셋째가 되거나(`rerun_continue.MAX_INTERVENTIONS` = 2) 세션이 다섯째가 되면(`rerun_continue.MAX_SESSIONS` = 4) 상한으로 끊김(개입·세션).
  - 회차의 벽시계가 4시간(`rerun_continue.WALL_CLOCK_SECONDS` = 14,400초)을 넘으면, 그 pid의 명령 줄에 그 호출의 세션 id가 있는지 본 뒤 프로세스 트리를 끈다. 상한으로 끊김(시간). 결과 이벤트가 없는 세션의 비용 칸에는 그 세션 기록 파일의 공식 단가 셈을 대신 넣고 표시한다.
- **한도.** `rate_limit_event`의 `status`가 `rejected`이거나 결과의 `api_error`가 `usage_limit_reached`(`rerun_checks.LIMIT_MARKERS`)면 측정 아님(한도)이다. `resetsAt` 뒤까지 새 회차를 열지 않고 그 회차를 새 클론으로 처음부터 다시 돈다. 풀리는 시각을 모르면 멈춘다. `allowed_warning`은 기록만 한다(명세 "한도").
- **오염.** 도구 입력은 assistant 이벤트의 `tool_use`이고 서브에이전트의 것도 든다. 결과 이벤트들의 `permission_denials`에 든 호출은 오염으로 세지 않고 거부 수로 센다. 꼴의 이름은 `rerun_checks.PATTERN_NAMES`다(명세 "오염 검사").
  - 셸 명령의 명령 전체에서 `rerun_checks.ADDRESSES`와 `rerun_checks.SESSION_OPENERS`를, `git commit`의 메시지(`-m`·`--message`의 인자, `-F -`의 heredoc 본문)를 뗀 명령에서 낱말 `gh`(`rerun_checks.GH`)를 찾는다.
  - 웹 도구(`rerun_checks.WEB_TOOLS`)의 입력은 모든 글에서 그 여섯 꼴을 찾는다.
  - 셸 명령은 `rerun_checks.SHELL_TOOLS`(Bash, PowerShell, Monitor)의 명령이다. `Monitor`가 웹소켓을 여는 입력(`ws`)은 웹 도구처럼 모든 글에서 찾는다.
  - 쓰기 도구(`rerun_checks.CONTENT_TOOLS`)의 내용은 대상이 `.md`가 아니고 클론의 `tests/` 밖일 때만 `rerun_checks.ADDRESSES`를 찾는다.
  - 모든 도구 입력의 경로 값과 셸 명령에서 주 체크아웃, 사용자의 `~/.claude`, 같은 뿌리 아래 다른 회차 폴더(뿌리 자체와 뿌리 바로 아래 파일 포함), 전용 설정 폴더를 찾는다. 자기 회차 폴더와 자기 세션 기록 폴더는 뺀다. 견주기는 `\`→`/`, 대소문자 접기, Git Bash의 `/c/` 꼴, 홈·설정 폴더의 별칭(`rerun_checks.HOME_ALIASES`, `rerun_checks.CONFIG_ALIASES`)을 쓰고 경로 조각 경계에서만 걸린다. 글 칸(`rerun_checks.FREE_TEXT_KEYS`)과 Grep의 `pattern`은 경로로 보지 않는다.
  - 막은 도구의 이름과 Skill 입력의 `open-session`을 찾는다.
  - 걸리면 측정 아님(오염)이고 한 번 다시 돈다. 같은 과제·갈래·조건 판에서 두 번째로 걸리면 그 과제를 그 판의 모든 갈래에서 뺀다.
- **모델 확인.** 다르면 측정 아님(모델)이고 러너가 멈춘다(명세 "모델 확인").
  - 본 세션 기록 파일의 assistant 줄 가운데 모델이 `<synthetic>`인 것을 뺀 줄이 모두 갈래의 모델과 노력이다.
  - 서브에이전트 기록의 assistant 줄은 모델만 보고, 허용 모임은 갈래의 모델, 하네스 모델(클론의 `.claude/agents/*.md` 머리말 `model`과 `code-review` 표준 축의 `sonnet`(`rerun_checks.CODE_REVIEW_MODEL`)), 그 세션이 Agent 입력의 `model`로 고른 모델의 합이다. 별칭은 `rerun_checks.MODEL_ALIASES`로 풀고 `inherit`·빈 값·없는 값은 갈래의 모델이다. 서브에이전트의 노력은 보지 않는다.
- **측정 아님을 다루는 법.** 한도는 위대로 다시 돈다. 오염은 위대로다. 설정·준비·호출·모델과 계정 불일치는 처음 났을 때 새 회차를 열지 않고 멈추고, 사람이 다시 띄우면 그 회차를 다시 돈다. 죽은 러너가 남긴 회차는 측정 아님(중단)으로 적고 다시 돈다. 멈출 때 함께 돌던 회차는 끝까지 둔다(명세 "차례, 동시성, 예산").
- **차례와 예산.** 과제는 과제 목록의 실행 차례대로, 한 과제의 갈래 계획을 마친 뒤 다음 과제로 간다. 동시에 둘(`rerun_runner.MAX_PARALLEL`)까지 돈다. 다음 과제를 시작하기 전에 쓴 것(모든 회차 기록의 비용 합. 파일럿과 측정 아님 포함)과 그 과제의 어림(PR 앞 비용 × 남은 회차 갈래의 `rerun_runner.ARM_RATIOS` 합)의 합이 명령 줄의 상한($1,600, 2026-10-28 사람이 $900에서 올렸다)을 넘으면 멈춘다. 조건 판은 `rerun_runner.CONDITION_VERSION`이고, 본 측정 목록의 회차를 열기 전에 이 절의 해시를 판정 도구의 상수와 대 보아 다르면 열지 않는다. 시간은 판정에 쓰지 않는다.

### 회차마다의 결과 변수

- **풀었다**: 끝이 끝남이고, 게이트가 모두 종료 0이며 시간을 넘긴 게이트가 없고, 숨은 시험이 하나 이상 돌아 모두 통과했다(설계 6절, `rerun_files.judge_view`).
- **게이트**: 결과 커밋을 클론에서 새 작업 트리로 꺼내 `rerun_files.SETUP_COMMANDS`로 준비한 뒤 게이트 묶음을 차례로 모두 돈다. 과제의 B에 `tools/run_checks.py`가 있으면 `rerun_files.GATE_COMMANDS`, 없으면 `rerun_files.OLD_GATE_COMMANDS`다. 환경은 세션의 허용 목록 환경에 B의 `.claude/settings.json` `env` 값을 얹은 것이다. 시간 제한은 `rerun_gates.LIMITS`(준비 1,800초씩, 게이트 묶음 전체 1,800초, 숨은 시험 600초, git 300초)이고 넘기면 그 몫이 실패다. 결과 작업 트리의 준비가 실패하면 게이트와 숨은 시험을 돌지 않고 풀지 못한 것이다. 게이트는 끝남인 회차에서만 돈다(명세 "게이트와 숨은 시험").
- **숨은 시험**: 게이트가 모두 종료 0인 회차에서만, 같은 작업 트리에 M의 숨은 시험 파일과 시험 지원 파일을 덮고 숨은 시험의 노드 ID만 `rerun_gates.PYTEST_ARGV`로 돌려 junit xml로 센다. 덮을 자리가 링크를 지나거나 쓰지 못하면 모든 노드가 실패다.
- **비용**(Claude Code 셈): 회차의 세션마다 마지막 결과 이벤트의 `total_cost_usd`를 더하고 `other_usd`를 더한다. 결과 이벤트가 없는 세션은 공식 단가 셈을 대신 넣는다(명세 "러너가 기대는 `claude -p`의 동작", "회차 기록", `rerun_files.judge_view`).
- **비용**(공식 단가 셈): 세션 기록 파일(본 세션과 `subagents/`)의 assistant 응답을 message id로 한 번씩 `rerun_cost.PRICES`로 셈하고(캐시 쓰기는 5분 몫 `rerun_cost.WRITE_5M`배, 1시간 몫 `rerun_cost.WRITE_1H`배, Haiku는 프롬프트가 `rerun_cost.HAIKU_LONG_PROMPT`토큰을 넘으면 `rerun_cost.HAIKU_LONG_PRICE`), 모델마다 마지막 `modelUsage`보다 모자란 토큰을 같은 단가로 채운다(채운 캐시 쓰기는 5분 배수). 여기에 `other_usd`를 더한다.
- **`other_usd`**: 회차 세션의 기록 파일이 든 프로젝트 폴더에 남은 회차 세션이 아닌 세션 기록(과제의 시험이 띄운 하위 `claude -p`)의 공식 단가 셈의 합. 회차 기록 꼴 판 1(`rerun_files.RECORD_SHAPE_VERSION` 앞)은 0으로 읽는다.
- **개입**: 이어 가기 3의 호출 수. 인계는 세지 않는다.
- **물으며 끝남**: 이어 가기 2에서 결과 글의 끝 줄이 물음표로 끝났는지.
- 판정이 읽는 그 밖의 칸: 과제 id, 갈래, 회차 번호, 파일럿인지, 조건 판, `claude --version`, 끝의 종류.

### 갈래마다의 지표와 후보 조건

- T는 판정에 쓰는 과제의 모임이다(아래 "쓰는 회차").
- 갈래 k마다 S_k(T에서 푼 과제 수), C_k(T의 Claude Code 셈 비용의 합), U_k = C_k / S_k(S_k가 0이면 없음), R_k = U_k / U_A를 낸다.
- R_k의 90% 구간: 2,000회(`rerun_judge.RESAMPLES`) 부트스트랩. 갈래마다 `random.Random(0)`(`rerun_judge.SEED`)을 새로 만들고, 회마다 T에서 |T|개 과제를 복원 추출해 갈래 k와 A에 함께 쓴다. 그 표본에서 S_k, S_A, C_A 가운데 하나라도 0이면 세지 않는다. 세지 않은 표본이 5%(`rerun_judge.UNCOUNTABLE_SHARE`, 100회)를 넘으면 그 갈래의 구간은 셀 수 없음이다. 구간은 `tools/model_sweep_judge.py`의 `percentile_ci`(5·95 백분위)다.
- 갈래 k(B~E)는 아래 셋을 모두 맞으면 후보다. A는 후보가 아니다.
  1. S_k ≥ S_A − 1(`rerun_judge.SOLVED_SLACK`).
  2. 개입 수가 A보다 많은 과제가 둘(`rerun_judge.MORE_INTERVENTIONS_MAX`) 이하.
  3. R_k의 구간 위 끝이 1(`rerun_judge.RATIO_UPPER_MAX`)보다 작다. 셀 수 없음이면 맞지 못한다.

### 결론

- 후보 가운데 U_k가 가장 작은 갈래가 구현 칸의 새 값이다. U_k가 같으면 A~E 차례의 앞이다.
- 후보가 없으면 칸을 `Opus 5.5 / xhigh`로 둔다.
- 결과는 ADR 0029 이력 초안의 재료이고, 사용자가 승인한다(설계 6절).
- 출력은 갈래마다 S, C, U, R과 구간, 개입이 A보다 많은 과제 수, 물으며 끝남, 상한으로 끊김의 표와 결론 한 줄이다. 끈 호출의 비용을 대신 넣은 회차, 결과 작업 트리의 준비가 실패한 회차, 공식 단가 셈에 `modelUsage` 대신 셈이 든 회차의 수를 갈래마다 함께 적는다.

### 되풀이

- 판정을 바꾸지 않고 두 번 더 셈한다(명세 "판정"의 되풀이 둘).
  - 단가: 비용을 모든 모델의 공식 단가 셈으로 바꾼 판정.
  - 숨은 시험: "풀었다"를 끝남과 게이트만으로 센 판정.
- 되풀이로 고른 갈래가 본 판정과 다르면 결론에 "<단가 / 숨은 시험>에 따라 갈린다"를 붙인다. 고른 갈래만 견주고, 결론 없음이면 붙이지 않는다.

### 판정하지 않는 조건

- 아래 가운데 하나라도 맞으면 결론 없음이고 칸을 `Opus 5.5 / xhigh`로 둔다. 표는 "탐색(판정이 아니다)"로 낸다(설계 6절).
  - T가 여섯(`rerun_judge.MIN_TASKS`)보다 적다.
  - S_A × 2 < |T|.
  - README에 이 절의 시작과 끝 표지가 하나씩 차례대로 있지 않거나, 절 내용의 UTF-8 SHA-256이 판정 도구의 상수와 다르다.

### 쓰는 회차

- 본 측정 과제 목록만 판정한다. 파일럿 목록은 거부하고, 파일럿 표시가 있는 회차는 세지 않는다(명세 "판정").
- 과제마다 측정 아님까지 센 본 측정 회차에서 가장 큰 조건 판 V를 잡고, V에서 갈래마다 측정 아님이 아닌 회차 가운데 회차 번호가 가장 작은 것을 쓴다.
- 아래 과제는 T에서 빼고 까닭을 적는다.
  - 본 측정 회차가 하나도 없다.
  - V에 측정인 회차가 없는 갈래가 있다.
  - 쓰는 회차 가운데 `claude --version`이 빈 값인 것이 있다.
  - 쓰는 회차 사이에 `claude --version`이 다르다.
- 오염으로 그 판에서 뺀 과제는 그 갈래에 측정인 회차가 없어 빠진다.

### 탐색(판정이 아니다)

- 크기 층별: 층마다 T의 과제 수, 갈래의 푼 수, 층 안의 U_k / U_A. 문턱은 정하지 않는다.
- 실패하면 올리기: 갈래 짝 (x, y)마다 과제의 비용을 x가 풀었으면 C_x, 아니면 C_x + C_y로, 푼 수를 x나 y가 푼 과제 수로 셈해 푼 수와 푼 과제 하나의 비용을 낸다. 짝은 본 판정의 C가 x < y인 것이고, D에서 C로 올리는 짝(`rerun_judge.PASTED_ESCALATION`)은 C와 상관없이 든다.
- 갈래마다 회차 벽시계 초의 중앙값, 토큰 합(입력, 출력, 캐시 읽기, 캐시 쓰기, 생각. 빈 칸이 든 회차가 있으면 빈 값), 생각 토큰 / 출력 토큰, 물으며 끝남의 수(`AskUserQuestion`을 부른 수를 갈음), 상한으로 끊긴 수, 막는 규칙이 거부한 호출 수.
- A의 비용과 원래 세션의 PR 앞 비용의 비: 과제 목록의 원래 세션 모델과 레벨의 `/` 뒤가 `xhigh`(`rerun_judge.ORIGINAL_EFFORT`)인 T의 과제로만 낸다.
- D·E(`rerun_judge.PASTED_ARMS`)의 R과 구간을 붙여 넣은 글의 "Opus 비용의 55~60%"와 견준다.
- 한도 사용률: 갈래와 창(`unifiedWindows`, 없으면 `rateLimitType`)마다 회차의 끝 사용률 − 첫 사용률의 중앙값.

### 코드 상수

```text
rerun_files.SHAPE_VERSION = 1
rerun_files.RECORD_SHAPE_VERSION = 2
rerun_files.ARMS = [["A", "claude-opus-5-5", "xhigh"], ["B", "claude-opus-5-5", "high"], ["C", "claude-opus-5-5", "medium"], ["D", "claude-sonnet-5-5", "high"], ["E", "claude-sonnet-5-5", "medium"]]
rerun_files.END_REASONS = {"끝남": [], "상한으로 끊김": ["개입", "세션", "예산", "시간"], "측정 아님": ["한도", "오염", "모델", "설정", "준비", "호출", "중단"]}
rerun_files.RULES = ["지시문 브랜치", "하나뿐인 브랜치", "없음"]
rerun_files.GATE_COMMANDS = ["uv run ruff check .", "uv run ruff format --check .", "uv run python tools/run_checks.py"]
rerun_files.OLD_GATE_COMMANDS = ["uv run ruff check .", "uv run ruff format --check .", "uv run pytest -q", "uv run pyright", "uv run lint-imports", "pnpm -C web verify"]
rerun_files.SETUP_COMMANDS = ["uv sync", "pnpm -C web install --frozen-lockfile", "uv run pre-commit install"]
rerun_files.MODEL_LABELS = {"claude-opus-5-5": "Opus 5.5", "claude-sonnet-5-5": "Sonnet 5.5"}
rerun_files.TEST_FILE = {"pattern": "tests/(?:[A-Za-z0-9_][A-Za-z0-9_.-]*/)*test_[A-Za-z0-9_.-]*\\.py", "flags": []}
rerun_files.TESTS_PY = {"pattern": "tests/(?:[A-Za-z0-9_][A-Za-z0-9_.-]*/)*[A-Za-z0-9_][A-Za-z0-9_.-]*\\.py", "flags": []}
rerun_files.CONFTEST = {"pattern": "(?:[A-Za-z0-9_][A-Za-z0-9_.-]*/)*conftest\\.py", "flags": []}
rerun_select.DATE_FLOOR = "2026-10-12T00:00:00+09:00"
rerun_select.MIN_CANDIDATES = 12
rerun_select.MIN_HIDDEN = 3
rerun_select.COST_LIMIT_USD = 70.0
rerun_select.EXTERNAL_TERMS = ["playwright", "pnpm -C web visual", "사진 비교", "Claude Design", "사람이 확인"]
rerun_select.EXTERNAL_NAME = "human-verification"
rerun_select.BRANCH_PREFIX = "feature/"
rerun_select.BACKTICK_PATH = {"pattern": "`([^`\\s]+\\.[A-Za-z][A-Za-z0-9]{0,4})`", "flags": []}
rerun_select.SEEDS = [1, 2, 3, 4, 100]
rerun_select.PILOT_PLANS = [["A", "A"], ["A", "A"], ["E"]]
rerun_select.MAIN_COUNTS = [3, 3, 2]
rerun_select.CAP_MULTIPLIER = 3.0
rerun_select.CAP_FLOOR_USD = 40.0
rerun_select.SETUP_FILES = ["web/package.json", "tools/run_checks.py"]
rerun_select.TICKET_PATH = {"pattern": "\\.scratch/([^/]+)/issues/([0-9]{2})-[^/]*\\.md", "flags": []}
rerun_select.PR_SUFFIX = {"pattern": "\\(#([0-9]+)\\)$", "flags": []}
rerun_select.DONE = "done"
rerun_hidden.SETUP_COMMANDS = [["uv", "sync"]]
rerun_hidden.PYTEST_COMMAND = ["uv", "run", "pytest"]
rerun_hidden.NAME_ERRORS = ["AttributeError", "NameError", "TypeError"]
rerun_hidden.SEVERITY = {"통과": 0, "건너뜀": 1, "실패": 2, "오류": 3}
rerun_round.FIXED_DENY_RULES = ["Bash(gh:*)", "Bash(git push:*)", "Skill(open-session)", "Bash(*open_session.ps1*)", "Bash(*claude://*)"]
rerun_round.BLOCKED_TOOLS = ["WebFetch", "WebSearch", "SendMessage", "ListAgents", "RemoteTrigger", "PushNotification", "DesignSync", "CronCreate", "ScheduleWakeup"]
rerun_round.PATH_TOOLS = ["Read", "Edit", "Write"]
rerun_round.ROOT_TOOLS = ["Edit", "Write"]
rerun_round.ROOT_SHAPE = "*.*"
rerun_round.ALLOWED_ENV = ["USERNAME", "USERDOMAIN", "COMPUTERNAME", "NUMBER_OF_PROCESSORS", "OS", "PROCESSOR_ARCHITECTURE", "PROCESSOR_IDENTIFIER", "PROCESSOR_LEVEL", "PROCESSOR_REVISION", "ALLUSERSPROFILE", "PUBLIC", "CommonProgramFiles", "CommonProgramFiles(x86)", "CommonProgramW6432", "ProgramW6432", "PSModulePath", "PATH", "PATHEXT", "SYSTEMROOT", "SystemDrive", "WINDIR", "COMSPEC", "USERPROFILE", "HOME", "HOMEDRIVE", "HOMEPATH", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA", "ProgramFiles", "ProgramFiles(x86)", "TEMP", "TMP", "UV_CACHE_DIR", "UV_PYTHON_INSTALL_DIR", "PNPM_HOME", "XDG_CACHE_HOME", "CLAUDE_CONFIG_DIR", "DISABLE_AUTOUPDATER"]
rerun_round.RUNNER_SET_ENV = ["CLAUDE_CONFIG_DIR", "DISABLE_AUTOUPDATER", "GH_CONFIG_DIR"]
rerun_round.AUTOUPDATER_OFF = "1"
rerun_round.SETUP_TIMEOUT = 1800
rerun_session.START_SKILL = "implement"
rerun_session.START_LINE = "{skill} 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `{root}`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: {rest}"
rerun_session.SESSION_FLAGS = ["-p", "--permission-mode", "auto", "--setting-sources", "user,project,local", "--strict-mcp-config", "--output-format", "stream-json", "--verbose"]
rerun_session.TITLE_HEAD = {"pattern": "#\\s+(?:[0-9]+:\\s*)?", "flags": []}
rerun_session.SYNTHETIC = "<synthetic>"
rerun_continue.INTERVENTION_MESSAGE = "지시문의 이번 요청 범위를 끝까지 마친다"
rerun_continue.MAX_INTERVENTIONS = 2
rerun_continue.MAX_SESSIONS = 4
rerun_continue.MIN_BUDGET_USD = 1.0
rerun_continue.WALL_CLOCK_SECONDS = 14400
rerun_continue.BUDGET_SUBTYPE = "error_max_budget_usd"
rerun_continue.DIRECTIVE_HEAD = "다음 작업:"
rerun_continue.DIRECTIVE_TAIL = "이번 요청 범위:"
rerun_continue.MODEL_HEAD = "모델:"
rerun_continue.BRANCH_HEAD = "브랜치:"
rerun_continue.QUESTION_MARKS = ["?", "？"]
rerun_checks.BUILTIN_PLUGINS = ["cc-plugin-agents-md", "cc-plugin-telemetry", "cc-plugin-plugin-authoring"]
rerun_checks.SYNCED_PLUGINS = ["frontend-design", "cowork-plugin-management"]
rerun_checks.MODEL_ALIASES = {"sonnet": "claude-sonnet-5-5", "haiku": "claude-haiku-5-5", "opus": "claude-opus-5-5"}
rerun_checks.CODE_REVIEW_MODEL = "sonnet"
rerun_checks.LIMIT_MARKERS = ["rejected", "usage_limit_reached"]
rerun_checks.PATTERN_NAMES = ["github-주소", "githubusercontent-주소", "저장소-이름", "낱말-gh", "open-session-스크립트", "claude-링크", "주-체크아웃", "사용자-claude", "다른-회차", "설정-폴더", "막은-도구", "open-session-스킬"]
rerun_checks.ADDRESSES = {"github-주소": {"pattern": "github\\.com", "flags": ["IGNORECASE"]}, "githubusercontent-주소": {"pattern": "githubusercontent\\.com", "flags": ["IGNORECASE"]}, "저장소-이름": {"pattern": "njh6803/agent-os", "flags": ["IGNORECASE"]}}
rerun_checks.GH = {"pattern": "(?<!\\w)gh(?!\\w)", "flags": ["IGNORECASE"]}
rerun_checks.SESSION_OPENERS = {"open-session-스크립트": {"pattern": "open_session\\.ps1", "flags": ["IGNORECASE"]}, "claude-링크": {"pattern": "claude://", "flags": ["IGNORECASE"]}}
rerun_checks.SOCKET_KEY = "ws"
rerun_checks.OPEN_SESSION = "open-session"
rerun_checks.FREE_TEXT_BY_TOOL = {"Grep": ["pattern"]}
rerun_checks.INHERIT = ["", "inherit"]
rerun_checks.FRONT_MATTER = {"pattern": "\\A---[ \\t]*\\r?\\n(.*?)\\r?\\n---[ \\t]*(?:\\r?\\n|\\Z)", "flags": ["DOTALL"]}
rerun_checks.MODEL_LINE = {"pattern": "^model:[ \\t]*(.*?)[ \\t]*$", "flags": ["MULTILINE"]}
rerun_checks.BOUNDARY = "\t\n\u000b\f\r \"&'()*,/:;<>?`{|}"
rerun_checks.SHELL_TOOLS = ["Bash", "PowerShell", "Monitor"]
rerun_checks.WEB_TOOLS = ["WebFetch", "WebSearch"]
rerun_checks.CONTENT_TOOLS = {"Write": ["file_path", "content"], "Edit": ["file_path", "new_string"], "NotebookEdit": ["notebook_path", "new_source"]}
rerun_checks.AGENT_TOOLS = ["Agent", "Task"]
rerun_checks.FREE_TEXT_KEYS = ["content", "description", "message", "new_source", "new_string", "old_string", "prompt"]
rerun_checks.PATH_KEYS = ["file_path", "notebook_path", "path"]
rerun_checks.KNOWN_TOOLS = ["Agent", "Bash", "CronCreate", "DesignSync", "Edit", "Glob", "Grep", "ListAgents", "Monitor", "NotebookEdit", "PowerShell", "PushNotification", "Read", "RemoteTrigger", "ScheduleWakeup", "SendMessage", "Skill", "SubagentHandback", "Task", "WebFetch", "WebSearch", "Write"]
rerun_checks.HOME_ALIASES = ["~", "$home", "${home}", "$userprofile", "${userprofile}", "$env:home", "${env:home}", "$env:userprofile", "${env:userprofile}", "%userprofile%"]
rerun_checks.CONFIG_ALIASES = ["$CLAUDE_CONFIG_DIR", "${CLAUDE_CONFIG_DIR}", "$env:CLAUDE_CONFIG_DIR", "${env:CLAUDE_CONFIG_DIR}", "%CLAUDE_CONFIG_DIR%"]
rerun_gates.LIMITS = {"setup": 1800, "gates": 1800.0, "hidden": 600.0, "git": 300}
rerun_gates.PYTEST_ARGV = ["uv", "run", "pytest"]
rerun_gates.BAD_CHILDREN = ["error", "failure", "skipped"]
rerun_cost.PRICES = {"claude-fable-5-1": {"input": 10.0, "output": 50.0, "cache_read": 0.25}, "claude-opus-5-5": {"input": 4.0, "output": 20.0, "cache_read": 0.2}, "claude-sonnet-5-5": {"input": 2.0, "output": 10.0, "cache_read": 0.1}, "claude-haiku-5-5": {"input": 0.1, "output": 0.5, "cache_read": 0.01}}
rerun_cost.HAIKU_LONG_PRICE = {"input": 0.5, "output": 2.5, "cache_read": 0.05}
rerun_cost.HAIKU_LONG_PROMPT = 100000
rerun_cost.WRITE_5M = 1.25
rerun_cost.WRITE_1H = 2.0
rerun_runner.CONDITION_VERSION = 4
rerun_runner.MAX_PARALLEL = 2
rerun_runner.ARM_RATIOS = {"A": 1.0, "B": 0.8, "C": 0.7, "D": 0.9, "E": 0.7}
rerun_judge.BASE_ARM = "A"
rerun_judge.MIN_TASKS = 6
rerun_judge.SOLVED_SLACK = 1
rerun_judge.MORE_INTERVENTIONS_MAX = 2
rerun_judge.RATIO_UPPER_MAX = 1.0
rerun_judge.SEED = 0
rerun_judge.RESAMPLES = 2000
rerun_judge.UNCOUNTABLE_SHARE = 0.05
rerun_judge.ORIGINAL_EFFORT = "xhigh"
rerun_judge.PASTED_ARMS = ["D", "E"]
rerun_judge.PASTED_ESCALATION = ["D", "C"]
rerun_judge.KEEP_CELL = "Opus 5.5 / xhigh"
rerun_judge.PASTED_CLAIM = "Opus 비용의 55~60%"
```

### 과제 목록(`main.json`)

```json
{
  "shape_version": 1,
  "kind": "본 측정",
  "tasks": [
    {
      "task_id": "mcp-shutdown-02",
      "ticket": ".scratch/mcp-shutdown/issues/02-boundary-exceptions.md",
      "base": "303e8fb5751b2c7ca36c0de4fea40e958a996529",
      "merge": "f1e6516b8075bade8f1b9b779218845be8635a10",
      "branch": "feature/02-boundary-exceptions",
      "tier": "작은",
      "size": 7,
      "order": 0,
      "pilot": false,
      "pr_cost_usd": 19.9878,
      "round_cap_usd": 59.9634,
      "hidden_tests": [
        "tests/adapters/test_mcp.py::test_서버_기동_실패는_서버_이름과_명령을_든_연결_오류다",
        "tests/adapters/test_mcp.py::test_둘째_서버가_열리지_않아도_연결_오류_하나다",
        "tests/adapters/test_mcp.py::test_뜨자마자_끝나는_서버는_서버_이름을_든_연결_오류_하나다",
        "tests/adapters/test_mcp.py::test_연결_안에서_던진_예외_그룹은_그_그룹_그대로_나온다",
        "tests/adapters/test_mcp.py::test_연결_안의_yield_에_멈춘_제너레이터는_예외_없이_닫힌다",
        "tests/adapters/test_mcp.py::test_끝나지_않는_도구_목록은_쪽_수의_상한에서_서버를_든_연결_오류다",
        "tests/adapters/test_mcp.py::test_연결_안에서_난_예외는_감싸이지_않고_나오며_서버가_내려간다"
      ],
      "support_files": [],
      "original_model_effort": "claude-opus-5-5/medium",
      "arm_plan": [
        "C",
        "A",
        "E",
        "D",
        "B"
      ]
    },
    {
      "task_id": "web-widget-01",
      "ticket": ".scratch/web-widget/issues/01-contract-calling-item-and-limit-kind.md",
      "base": "07c890c58ff7d9a1f24c4959104650f74f8b6083",
      "merge": "96d3e1df21e35ec50a2b9310eaac0d64103ab469",
      "branch": "feature/01-contract-calling-item-and-limit-kind",
      "tier": "중간",
      "size": 11,
      "order": 1,
      "pilot": false,
      "pr_cost_usd": 65.4854,
      "round_cap_usd": 196.4562,
      "hidden_tests": [
        "tests/channel/http/test_end_user.py::test_도구를_요청한_모델_호출은_그_도구_이름을_차례대로_든_calling_항목이다",
        "tests/channel/http/test_end_user.py::test_주체별_시간당_실행은_미끄러지는_창이고_Retry_After_는_남은_초다",
        "tests/channel/http/test_end_user.py::test_이어_가기의_에러도_JSON_봉투이고_허용_출처에_CORS_헤더가_붙는다"
      ],
      "support_files": [],
      "original_model_effort": "claude-opus-5-5/xhigh",
      "arm_plan": [
        "A",
        "D",
        "C",
        "B",
        "E"
      ]
    },
    {
      "task_id": "model-rerun-10",
      "ticket": ".scratch/model-rerun/issues/10-schedule-and-budget.md",
      "base": "f1ed4be75da341b4c1dfafa0f5196f1642876ca2",
      "merge": "80ff61f1d83176ff8c2a590e71a0958d8cdf148c",
      "branch": "feature/10-schedule-and-budget",
      "tier": "큰",
      "size": 27,
      "order": 2,
      "pilot": false,
      "pr_cost_usd": 30.0483,
      "round_cap_usd": 90.1449,
      "hidden_tests": [
        "tests/tools/test_rerun_session.py::test_예산은_유한한_값만_받는다[nan]",
        "tests/tools/test_rerun_session.py::test_예산은_유한한_값만_받는다[inf]",
        "tests/tools/test_rerun_session.py::test_예산은_유한한_값만_받는다[-inf]"
      ],
      "support_files": [
        "tests/tools/fake_claude.py"
      ],
      "original_model_effort": "claude-opus-5-5/medium",
      "arm_plan": [
        "E",
        "D",
        "A",
        "C",
        "B"
      ]
    },
    {
      "task_id": "end-user-continuation-05",
      "ticket": ".scratch/end-user-continuation/issues/05-only-pre-owner-damage-is-404.md",
      "base": "0a6e0b0d75291f4616fe4595353be5c73de8b97f",
      "merge": "ed11175312d00c7269060c17adf3e0ff437fd8e8",
      "branch": "feature/05-only-pre-owner-damage-is-404",
      "tier": "작은",
      "size": 8,
      "order": 3,
      "pilot": false,
      "pr_cost_usd": 67.3266,
      "round_cap_usd": 201.9798,
      "hidden_tests": [
        "tests/channel/http/test_end_user.py::test_손상된_남의_실행에_운영자_채널은_500_원문이고_최종_사용자_면은_404_고정이다",
        "tests/channel/http/test_end_user.py::test_결정에서_주인을_확인한_뒤의_고장은_고정_문구의_500이다",
        "tests/channel/http/test_end_user.py::test_이어_가기의_구성_오류와_깨진_고리는_고정_문구의_500이다",
        "tests/channel/http/test_end_user.py::test_자기_실행의_손상도_남의_손상처럼_404이고_기록에는_하위_타입이_남는다",
        "tests/channel/http/test_end_user.py::test_이어_가기의_에러도_JSON_봉투이고_허용_출처에_CORS_헤더가_붙는다"
      ],
      "support_files": [],
      "original_model_effort": "claude-opus-5-5/xhigh",
      "arm_plan": [
        "E",
        "A",
        "C",
        "B",
        "D"
      ]
    },
    {
      "task_id": "web-widget-02",
      "ticket": ".scratch/web-widget/issues/02-runtime-relays-call-events-live.md",
      "base": "51a0417e6106afaaeca5ba7bf77f663d4a33f28b",
      "merge": "eec99a5170e58572d5e6b6d79df788c2fa6f7b6a",
      "branch": "feature/02-runtime-relays-call-events-live",
      "tier": "중간",
      "size": 16,
      "order": 4,
      "pilot": false,
      "pr_cost_usd": 27.298,
      "round_cap_usd": 81.894,
      "hidden_tests": [
        "tests/channel/http/test_end_user.py::test_모델이_요청한_도구가_끝나기_전에_부르기_시작함_항목이_도착한다",
        "tests/channel/http/test_router.py::test_모델이_요청한_도구가_끝나기_전에_그_모델_호출의_프레임이_도착한다",
        "tests/core/test_run.py::test_모델이_요청한_도구가_불릴_때_소비자는_이미_그_모델_호출의_이벤트를_받았다",
        "tests/core/test_run.py::test_모델_호출의_이벤트를_쓰지_못하면_그_모델이_요청한_도구는_불리지_않는다"
      ],
      "support_files": [],
      "original_model_effort": "claude-opus-5-5/medium",
      "arm_plan": [
        "D",
        "E",
        "C",
        "B",
        "A"
      ]
    },
    {
      "task_id": "ticket-for-every-pr-03",
      "ticket": ".scratch/ticket-for-every-pr/issues/03-commit-check-blocks-ticketless.md",
      "base": "96fbe2419f08938b293976438552f36f8d9339d2",
      "merge": "e62eb0524abe70a59392824300ead161bdba7447",
      "branch": "feature/03-commit-check-blocks-ticketless",
      "tier": "큰",
      "size": 20,
      "order": 5,
      "pilot": false,
      "pr_cost_usd": 22.5991,
      "round_cap_usd": 67.7973,
      "hidden_tests": [
        "tests/tools/test_check_ticket.py::test_바로_치면_지금_색인으로_판정한다",
        "tests/tools/test_check_ticket.py::test_저장소가_아닌_폴더에서는_git_실패로_2를_낸다",
        "tests/tools/test_check_ticket.py::test_바로_치면_전환의_한_줄이_보인다"
      ],
      "support_files": [],
      "original_model_effort": "claude-opus-5-5/medium",
      "arm_plan": [
        "B",
        "A",
        "D",
        "C",
        "E"
      ]
    },
    {
      "task_id": "end-user-channel-04",
      "ticket": ".scratch/end-user-channel/issues/04-cors-on-prefix.md",
      "base": "8a4274fed2676a250a702c57ace49a517b686876",
      "merge": "5a3710824aad6aee5d239a7d11ef26b7e275812a",
      "branch": "feature/04-cors-on-prefix",
      "tier": "작은",
      "size": 4,
      "order": 6,
      "pilot": false,
      "pr_cost_usd": 20.4797,
      "round_cap_usd": 61.4391,
      "hidden_tests": [
        "tests/channel/http/test_end_user.py::test_허용_출처의_요청은_200과_에러_응답_모두에_CORS_헤더_셋을_받는다",
        "tests/test_server.py::test_최종_사용자_면의_예기치_않은_500도_봉투이고_CORS_헤더와_추적_식별자를_든다",
        "tests/test_server.py::test_CORS_분기는_인증과_같은_경로로_면을_가른다"
      ],
      "support_files": [],
      "original_model_effort": "claude-opus-5-5/xhigh",
      "arm_plan": [
        "E",
        "B",
        "C",
        "A",
        "D"
      ]
    },
    {
      "task_id": "conversation-01",
      "ticket": ".scratch/conversation/issues/01-contract-continue-run-and-own-exchanges.md",
      "base": "300b5f03fd01afc30acebff9acab263fdcb1a82f",
      "merge": "4112d2b854fcd881aff5548950acbb1b0ae2c9a5",
      "branch": "feature/01-contract-continue-run-and-own-exchanges",
      "tier": "중간",
      "size": 10,
      "order": 7,
      "pilot": false,
      "pr_cost_usd": 49.4847,
      "round_cap_usd": 148.4541,
      "hidden_tests": [
        "tests/channel/http/test_router.py::test_스트림_항목이_이름_있는_Event_이고_TraceEvent_와_같은_멤버를_가리킨다",
        "tests/channel/http/test_router.py::test_409_는_채널_라우트에만_있다",
        "tests/channel/http/test_router.py::test_없는_앞_실행과_없는_에이전트는_404_봉투이고_메시지가_가른다",
        "tests/channel/http/test_router.py::test_다른_주체와_끝나지_않음과_꺼짐은_409_봉투이고_트레이스가_생기지_않는다[\\ub2e4\\ub978 \\uc8fc\\uccb4]",
        "tests/channel/http/test_router.py::test_다른_주체와_끝나지_않음과_꺼짐은_409_봉투이고_트레이스가_생기지_않는다[\\ub05d\\ub098\\uc9c0 \\uc54a\\uc74c]",
        "tests/channel/http/test_router.py::test_다른_주체와_끝나지_않음과_꺼짐은_409_봉투이고_트레이스가_생기지_않는다[\\uaebc\\uc9d0]",
        "tests/channel/http/test_router.py::test_고리가_깨지면_500_봉투이고_message_가_그_PluginError_의_문구다",
        "tests/channel/http/test_router.py::test_패턴을_어기는_앞_실행은_422이고_트레이스_포트가_불리지_않는다",
        "tests/channel/http/test_router.py::test_이어_가기_본문에_추가_필드를_실으면_무시하지_않고_422다[principal]",
        "tests/channel/http/test_router.py::test_이어_가기_본문에_추가_필드를_실으면_무시하지_않고_422다[model]",
        "tests/channel/http/test_router.py::test_이어_가기_본문에_추가_필드를_실으면_무시하지_않고_422다[previous_run]",
        "tests/channel/http/test_router.py::test_이어_가기_경로와_결정_경로는_서로_가로채지_않는다",
        "tests/channel/http/test_router.py::test_공유_409_설명은_세_채널_라우트에서_같고_상태와_주체를_함께_말한다"
      ],
      "support_files": [],
      "original_model_effort": "claude-fable-5-1/high",
      "arm_plan": [
        "A",
        "C",
        "E",
        "D",
        "B"
      ]
    }
  ]
}
```

### 되살릴 목록(`revive.json`)

```json
{
  "model-rerun-10": "'사람이 확인'은 러너의 명령 줄 인자 이야기다(\"사람이 확인 인자를 주면 잇는다\"). 사람이 결과를 확인하는 체크박스가 아니다",
  "model-rerun-05": "낱말 다섯은 거르기 낱말 목록 자체를 수용 기준에 인용한 것이다",
  "end-user-continuation-06": "'사진 비교'는 \"packages/ui를 건드리지 않으면 사진 비교도 CI에 맡긴다\", 곧 로컬에서 치지 않는다는 문장이다",
  "web-admin-01": "'playwright'는 게이트 훅이 잡을 명령 모양의 예(\"예: Playwright 실행\")다. 세션이 Playwright 를 돌리는 체크박스가 아니다"
}
```
<!-- 사전 등록 끝 -->

## 2026-10-22 결과: headless 동작

측정이었다. 갈래를 더해 가며 갈래마다 두 번에서 네 번 돌렸고(`서브`만 넷), 기록마다 init과 result 이벤트가 있었으며 한도에 막힌 회차가 없었다(프로브의 종료 코드 0). 그때의 프로브는 갈래마다의 표지를 보지 않았다. 갈래마다의 표지를 더한 판의 `--judge`로 커밋한 요약 열둘을 다시 판정하니 열둘 모두 측정이었다(종료 0). 그 뒤 프로브의 회차 셈과 읽기를 `tools/probe_kit.py`로 옮겼다. 옮긴 판은 `claude`를 다시 띄우지 않았다. 커밋한 요약의 `--judge`가 `측정 12회차, 측정 아님 0회차`로 종료 0, `--prices`가 종료 0이었고, 세션 스크래치에 둔 요약 다섯(표지를 지운 넷과 그대로 둔 하나, 커밋하지 않았다)의 `--judge`는 넷을 측정 아님으로 세어 종료 1이었다. 읽기와 회차 셈은 세션 스크래치의 가짜 시험으로 손으로 봤다. 가짜 자식 프로세스로 읽기 넷(보통 끝, 풀 수 없는 바이트, 제한 시간을 넘겨 매달려 64초 뒤 꺼짐, 손자가 stdout을 쥔 채 남아 14초 뒤 돌아옴), 가짜 `drive`로 회차 셈 둘(첫 호출이 예외로 끝나면 이어 부르기가 돌지 않고 측정 아님, 첫 호출이 끝나면 이어 부르기가 돈다)이 모두 기대대로였다. 커밋한 요약은 일곱 갈래를 한 번에 돈 실행(아래에서 셋째 실행)의 판과 그 뒤에 더 돈 `서브-4`·`서브-5`다. 그 판이 요약에 init의 `tools`, 한도 이벤트의 칸, 결과 이벤트 전부를 남긴다. 아래의 수는 그 요약의 것이다. 첫째와 둘째 실행(그 앞의 여섯 갈래를 한 번에 돈 실행과 그 뒤에 따로 돈 `서브`)은 `서브-2.jsonl` 밖의 원본을 커밋하지 않았다. 아래에서 그 실행을 드는 자리마다 무엇으로 봤는지 적는다.

- **결과 이벤트에 비용 칸이 있다.** 결과 이벤트에 `total_cost_usd`와 모델별 `modelUsage`(토큰, `costUSD`, `costBasis: "list"`)가 있다. init의 `apiKeySource`는 `none`이었다(구독 로그인, `서브-2.jsonl`).
- **비용 칸은 공식 단가로 셈한 값과 같고, 캐시 쓰기의 배수는 그 모델의 응답이 쓴 캐시 수명과 함께 갈렸다.** `--prices`로 커밋한 요약 열둘의 `modelUsage` 열여섯 칸을 공식 단가(`docs/model-selection.md` 2절. 캐시 읽기는 Sonnet $0.10, Haiku $0.01)로 셈해 대니 열여섯 모두 한 배수와 맞았다(종료 0). `claude-sonnet-5-5` 열둘은 모두 1시간(입력의 2배), `서브`·`서브-4`·`서브-5`의 서브에이전트 `claude-haiku-5-5` 셋은 모두 5분(1.25배)이었고, `거부대조`의 Haiku는 캐시 쓰기가 0이라 두 배수가 함께 맞았다. `서브`의 세션 기록(본 세션 파일과 그 아래 `subagents/`)을 응답마다 보니 Sonnet 응답의 `cache_creation`은 모두 `ephemeral_1h_input_tokens`에, Haiku 응답은 모두 `ephemeral_5m_input_tokens`에 실렸다(요약의 세션 id로 기본 설정 폴더의 기록 파일을 열어 손으로 봤다). 이 기록에서는 모델과 수명이 함께 갈려, "배수는 모델이 정한다"는 해석과 "응답의 캐시 수명이 정한다"는 해석을 가르지 못한다. 뒤의 것은 공식 문서의 배수(사용량 장부 `tools/token_report.py`의 단가표 주석과 `_cache_writes`)에 기댄다. 이 기록에서는 응답마다 수명으로 나눠 셈해도 모델마다 한 배수로 셈해도 같은 값이 나오고, 다른 모델(Opus)에서 두 셈이 갈리는지는 보지 않았다. 캐시 읽기를 `docs/model-selection.md` 3절과 장부 단가표의 Sonnet $0.20으로 셈하면 캐시 읽기가 있는 Sonnet 열둘이 모두 맞지 않는다(캐시 읽기 토큰 × $0.10만큼 커진다).
- **`--resume`의 비용과 토큰은 세션 누적이다.** `모양`(도구 호출 넷, 다섯 차례)이 $0.04218, 같은 세션을 이어 부른 `이어가기`(도구 없는 한 줄 답)가 $0.04503이었고, `modelUsage`의 출력 토큰도 355에서 373으로, 캐시 읽기가 108,182에서 131,538로 늘었다. 그 호출의 몫이었다면 출력 토큰은 한 줄 답의 몫(373 − 355 = 18)에 가까웠을 것이다. `누적이어가기`도 같다($0.02538에서 $0.04858로, 출력 5에서 188로). `num_turns`는 호출의 몫이다(`이어가기` 1). 그래서 회차의 비용은 세션마다 마지막 결과 이벤트의 `total_cost_usd`이고, 결과 이벤트마다 더하면 이어 부른 몫을 두 번 센다.
- **`--max-budget-usd`는 구독 로그인에서 멈춘다.** `예산`(`모양`과 같은 질문, 예산 $0.01)은 첫 응답 뒤에 결과 `error_max_budget_usd`, `terminal_reason: budget_exhausted`, 종료 코드 1로 끝났다. 비용은 $0.02670으로 예산을 넘었다. 예산은 응답이 끝난 뒤에 재고, 넘긴 응답이 낸 도구 호출(Bash)은 결과 없이 돌지 않았다. 양성 대조는 같은 질문을 예산 없이 마친 `모양`이다.
- **예산은 세션 누적이 아니라 그 호출의 몫을 센다.** `누적`이 새 세션을 $0.02538에 열고, `누적이어가기`가 그 세션을 예산 $0.02로 이어 불렀다. 시작할 때 이미 누적이 예산을 넘었는데도 첫 응답의 Bash가 돌았고, 둘째 응답 뒤에 `budget_exhausted`로 멈췄다(`num_turns` 2, 둘째 응답의 Read는 돌지 않았다). 그 호출의 몫은 $0.04858 − $0.02538 = $0.02320이다. 누적을 셌다면 첫 응답 뒤에 멈춰 그 응답의 Bash도 돌지 않았을 것이다(`예산`에서 예산을 넘긴 응답의 도구는 돌지 않았다). `예산이어가기`(같은 예산 $0.01로 도구 없는 한 줄 답)도 멈추지 않고 끝났지만, 다음 응답이 없어 멈출 자리가 없었다는 해석과 가르지 못해 `누적`을 더했다.
- **노력은 stream-json에 없고 세션 기록 파일에 있다.** 커밋한 요약 열둘 모두 이벤트에 `effort` 키가 없었다(이벤트의 키를 모두 훑는 `effort_keys_in_events`가 빈다). 원본을 커밋하지 않은 세 실행의 `.jsonl`을 모두 훑어도 큰따옴표로 싼 문자열 가운데 이름에 effort가 든 것은 `effort`와 `per_turn_effort_active`(init의 칸, 값 `true`) 둘뿐이었고, 앞의 것은 init의 슬래시 명령 목록에 든 명령 이름이었다(세션 스크래치 스크립트 `init_tools.py`로 세고, 셋째 실행 `질문`의 원본을 `grep -o`로 앞뒤까지 봤다. 셋째 실행 `모양`의 원본에서 `grep -c '"effort":'`는 0이었다. 손으로 봤다). 세션 기록 파일(`<설정 폴더>/projects/<작업 폴더 slug>/<세션 id>.jsonl`)의 assistant 줄에 `effort`(`low`)와 `message.model`이 있다. 모델이 `<synthetic>`이고 `effort`가 없는 줄은 `예산이어가기`의 기록에만 있었다(요약의 `transcript.model`이 `예산` `claude-sonnet-5-5` 1, `누적이어가기` 3, `예산이어가기` 3과 `<synthetic>` 1). 예산에 끊긴 세션(`예산`)을 이어 부른 기록이고, 끊긴 뒤 이어 부르지 않은 `누적이어가기`에는 없었다. 무엇이 그 줄을 만드는지는 가르지 않았다. 기록 파일의 폴더 이름은 작업 폴더의 경로에서 나온다.
- **서브에이전트의 기록은 본 세션 기록 옆의 폴더에 따로 있다.** `서브`는 Task 도구로 `model: haiku`인 서브에이전트를 띄웠다. 서브에이전트의 응답은 stream-json에 `parent_tool_use_id`가 붙은 assistant 이벤트로 `claude-haiku-5-5`였고, 세션 기록은 `<세션 id>/subagents/agent-<id>.jsonl`에 `effort: low`, `claude-haiku-5-5`로 있었다. 본 세션 기록 파일의 assistant 줄은 모두 `claude-sonnet-5-5`였다. 세 요약(`서브`, `서브-4`, `서브-5`)이 모두 그랬다. 서브에이전트에 준 노력은 없었는데 본 세션과 같은 `low`가 실렸다. 모든 본 세션이 `low`였으므로, 그 값이 본 세션에서 물려받은 것인지 서브에이전트의 기본값인지는 가르지 않았다.
- **한 호출에 결과 이벤트가 여럿일 수 있다.** 네 번 돈 `서브` 가운데 둘째 실행 한 번(`서브-2.jsonl`)에서 Task 도구가 서브에이전트를 백그라운드로 띄웠다(`Async agent launched successfully`). 본 세션이 "아직 실행 중"이라는 답으로 차례를 끝낸 뒤, 서브에이전트가 끝나자 init이 다시 오고 본 세션이 낱말을 답했다. 프로세스는 서브에이전트가 끝날 때까지 기다렸다. 결과 이벤트는 셋이었고(`result_index` 0·1·2), 글은 차례로 "아직 실행 중" 답, 낱말, 빈 글(`num_turns` 0)이었으며, 셋 모두 같은 `total_cost_usd`(세션 누적)를 실었다. 나머지 세 번은 서브에이전트의 보고가 그 차례 안에 돌아와 결과 이벤트가 하나였다. 그래서 마지막 결과 이벤트의 글이 빌 수 있다.
- **저장소의 막는 규칙이 auto 모드에서 막는다.** `거부`는 저장소의 `.claude/settings.local.json`에 `Bash(gh:*)`, `Bash(git push:*)`, `Bash(*open_session.ps1*)`, 저장소 밖 폴더의 `Read(//c/…/outside/**)`(드라이브 문자는 소문자, 콜론 없음), `Skill(probe-open)`, `WebFetch(domain:github.com)`을 두었다. 여섯 행동이 모두 결과의 `permission_denials`에 들었고, 도구 결과가 오류(`Permission to use Bash with command … has been denied.`, `File is in a directory that is denied by your permission settings.`, `Skill execution blocked by permission rules`, `WebFetch denied access to domain:github.com.`)였으며, 스크립트가 쓰는 표지 파일(`opened.txt`)이 생기지 않았고, 답에 바깥 파일의 표지 낱말이 없었다. 양성 대조 `거부대조`(규칙 없는 같은 저장소)에서는 여섯이 모두 돌았다. `gh --version`이 판을 찍었고, `git push origin main`이 로컬 bare 원격에 `Everything up-to-date`를 냈고, 표지 파일이 생겼고, 바깥 파일과 스킬을 읽었고, WebFetch가 페이지 제목을 냈다. 그래서 auto 모드의 분류기는 이 여섯 가운데 아무것도 스스로 막지 않았고, 막은 것은 규칙이다.
- **막는 규칙을 둔 세션에는 PowerShell 도구가 없었다.** `거부`의 init `tools`는 27개로, 다른 갈래의 28개에서 `PowerShell`만 빠졌다. 커밋한 요약 열둘 가운데 `PowerShell`이 없는 것은 `거부` 하나다. 원본을 커밋하지 않은 세 실행에서도 그랬다(세 실행의 원본마다 첫 init의 도구 수와 `PowerShell` 유무를 세션 스크래치 스크립트 `init_tools.py`로 찍어 손으로 봤다. `거부`만 27개이고 `PowerShell`이 없었다). 규칙이 Bash 규칙이어서인지 `settings.local.json`이 있어서인지는 가르지 않았다.
- **`modelUsage`에 갈래 밖의 모델이 실린다.** `거부대조`의 `modelUsage`에 `claude-haiku-5-5`(출력 287토큰, $0.00093)가 있었다. 서브에이전트가 없었고 assistant 줄과 세션 기록의 모델은 모두 `claude-sonnet-5-5`였다. 그 갈래에만 있던 것은 WebFetch의 실행과 auto 모드가 위험할 수 있는 명령(푸시, 스크립트)을 판정한 일이고, 둘 가운데 무엇이 Haiku를 불렀는지는 가르지 않았다. 그래서 `modelUsage`의 모델 목록은 갈래의 모델과 서브에이전트의 모델만이 아니다.
- **`-p`에는 `AskUserQuestion`이 없다.** 모든 갈래의 init `tools`에 그 도구가 없었다. `질문`에서 모델이 `ToolSearch`로 `select:AskUserQuestion`을 찾았고 결과가 `No matching deferred tools found`였으며, 답은 그 도구를 쓸 수 없다고 했다. init `tools`에는 스키마를 늦게 싣는 도구도 든다. `WebFetch`가 목록에 있으면서 `거부`·`거부대조`에서 `ToolSearch`로 실린 뒤 불렸다.
- **바깥에 닿는 도구가 init에 있다.** `--strict-mcp-config`로 `mcp_servers`는 비었고, 플러그인은 내장 셋(`cc-plugin-agents-md`, `cc-plugin-telemetry`, `cc-plugin-plugin-authoring`)이었다. 도구 목록에는 `SendMessage`, `ListAgents`, `RemoteTrigger`, `PushNotification`, `DesignSync`, `CronCreate`, `ScheduleWakeup`, `Workflow`, `Monitor`, `EnterWorktree`, `WebSearch`가 있었다. 이 도구들을 막는 규칙은 재지 않았다.
- **허용 목록 환경으로 로그인이 된다.** 프로브는 `claude`를 허용 목록(요약의 `env_names`)으로 지은 환경으로 띄웠고 모든 갈래가 구독 로그인으로 돌았다. 세션 셸에는 허용 목록 밖의 이름이 더 있었다(`CLAUDECODE`, `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_MESSAGING_SOCKET`, `CLAUDE_EFFORT`, `MSYSTEM` 등. Claude Code와 Git Bash가 넣는 이름이다). 허용 목록이 토큰을 거르는지는 이 프로브로 보이지 못한다. 프로브를 띄운 셸에 `GH_TOKEN`·`GITHUB_TOKEN`이 처음부터 없었다(이름의 수만 세어 손으로 봤다, 0). 거르는 것은 러너가 허용 목록으로 환경을 짓는 코드의 시험이 본다.
- **한도 이벤트에 사용률이 있다.** `rate_limit_event`의 `rate_limit_info`에 `status`, `rateLimitType`, `utilization`, `unifiedWindows`(`five_hour`, `seven_day`마다 `utilization`과 `resetsAt`)가 있었다. 그때 njh4803은 `seven_day` 0.97, `status: allowed_warning`이었다. `예산`처럼 첫 응답 뒤에 멈춘 호출에는 그 이벤트가 없었다.

못 본 것.

- 전용 `CLAUDE_CONFIG_DIR`와 다시 풀기 계정(njh4803). 기록이 그 폴더 아래에만 생기는지, 그 폴더의 로그인으로 도는지는 파일럿(설계 8절 1)이 본다.
- 러너의 `--setting-sources user,project,local`. 이 프로브는 사람의 기본 설정 폴더로 돌아, 사람의 사용자 설정(허용 규칙, 훅, 출력 스타일)이 섞이지 않게 `project,local`로 `user`를 뺐다(요약의 `args`). 러너의 `user`는 전용 설정 폴더의 설정이다. 그 설정이 위 동작을 바꾸지 않는지도 파일럿이 본다.
- 막는 규칙을 다른 꼴의 명령으로 비켜 가는 길(따옴표, 다른 셸, 경로를 바꾼 읽기). 다시 풀기는 오염 검사가 도구 입력을 훑어 그 몫을 받는다.
- 갈래의 모델과 노력 바꾸기. 이 프로브는 본 세션을 `claude-sonnet-5-5`·`low` 하나로만 돈다. Opus와 다른 노력에서 기록 파일의 `effort` 값이 `--effort`와 같은지, Opus의 `costUSD`가 공식 단가와 같은지는 파일럿(설계 8절 2·4)이 본다.
- 서브에이전트가 백그라운드로 뜨는 때를 가르는 것. 네 번 가운데 한 번이었고 무엇이 갈랐는지 보지 않았다.
- 데스크톱 앱 세션. 이 동작은 `claude -p`의 것이다.

## 2026-10-23 결과: 후보 표

`candidates.md`는 위 표의 명령이 쓴 그대로다(머리의 "되살릴 목록은 없음다"도 그 판 도구의 문구이고, 그 뒤 "없다"로 고쳤다). 아래의 수는 그 표의 끝 줄과 행이다.

- **문턱 12개에 8개다.** B가 2026-10-12 이후인 남은 후보는 1개(ticket-for-every-pr-03, 숨은 시험 3개)였다. 그래서 거슬러 채우기가 날짜 앞의 후보를 끝까지 내려가 7개를 더했다(http-channel-04·03, admin-api-06·04, interrupts-05·04·03). 이 수는 사용자 결정("실제 후보 수를 본 뒤 정한다", 일지 2026-10-23-02)이 기다린 것이고, 길은 파일럿(티켓 11)이 사람에게 묻는다. 그 일지의 정적 어림은 날짜 안이 넷쯤이고 9월의 B에는 두 파일이 없다는 것이었다. 날짜 안은 그보다 적었고, 거슬러 채워 남은 7개(B가 2026-09-21~26)의 B에는 두 파일이 어림대로 없었다.
- **거슬러 채워 남은 7개는 모두 B에 준비·게이트 파일이 없다.** `web/package.json`과 `tools/run_checks.py`가 둘 다 없다(표의 두 칸).
- **후보가 빠진 까닭은 바깥 검증 낱말이, 노드가 빠진 까닭은 조건 2의 "결과 없음(모음 실패)"이 가장 흔하다.** 빠진 69개 가운데 빠진 까닭 칸에 바깥 검증 낱말이 든 행이 34개, 숨은 시험이 셋보다 적은 행이 29개다. 숨은 시험 가르기까지 간 38개 가운데 빠진 노드가 있는 행은 30개이고, 그 가운데 23개 행(노드 705개)에 모음 실패가 들며 다음으로 흔한 조건 2 통과는 10개 행이다. 모음 실패가 든 23개 가운데 4개는 남은 후보다(두 칸을 세션 스크래치 스크립트 `row_reasons.py`·`node_reasons.py`로 까닭의 머리말마다 셌다). 모음 실패가 흔한 것은 새 모듈을 짓고 그 모듈의 시험을 새로 쓰는 티켓이면 B에 덮은 시험 파일이 import에서 실패해, 그 파일의 노드가 모두 결과 없이 빠지기 때문이라는 해석이다. 이 해석은 행을 읽은 어림이고 후보마다 모음 오류의 문구를 보지는 않았다.
- **model-rerun-02 행은 도구의 결함이다.** 그 행의 까닭 `git grep -q 를 띄우지 못했다: embedded null character`는 02의 시험 본문에 든 NUL 문자열을 조건 3이 `git grep`의 인자로 넘기다 난 것이다. 이 표를 지은 뒤 `tools/rerun_hidden.py`가 문자열을 NUL에서도 나누게 고쳤다. 고친 도구로 그 후보 하나를 다시 가르니 숨은 시험 0개, 빠진 노드 99개(조건 2 결과 없음(모음 실패) 98, 조건 3 문자열 1)였다(세션 스크래치 스크립트로 `sort_candidate(".", "d0e696c9", "c3c2cfcf")`를 불러 손으로 봤다). 그래서 다시 지어도 그 행은 숨은 시험이 셋보다 적어 빠진다. 다른 행이 같은 입력이면 같게 나온다는 것은 다시 짓지 않은 어림이라, 끝 줄의 수가 그대로라는 것도 어림이다. 표는 다시 짓지 않았다(사용자 결정, 일지 2026-10-23-43). 파일럿 명령은 표를 처음부터 다시 지어 고친 도구가 쓴다.

## 2026-10-26 결과: 막는 규칙의 새 꼴

`deny_shapes.py`를 세 번 돌았다. 첫 실행은 이름만 쓴 규칙의 두 도구를 부르지 못하고 `ToolSearch`에서 끝나 그 두 행동이 "시도 없음"이었다. 그래서 둘째 판부터 그 이름을 찾은 `ToolSearch`도 시도로 세고 init의 `tools`를 적게 바꿨다(결과를 본 뒤 바꾼 표지다. 첫 실행의 요약은 둘째 실행이 같은 출력 폴더에 덮어 남지 않았다). 둘째 실행의 `규칙`은 모델이 Edit 앞의 Read가 막히자 Edit을 부르지 않아 측정이 아니었고, 지시문에 "Read 가 막혀도 Edit 은 꼭 한 번 부른다"를 넣은 셋째 실행은 두 갈래 모두 측정이었다. 둘째·셋째 실행의 요약은 `2026-10-26/`에 `<갈래>-<실행 차례>.summary.json`으로 손으로 옮겨 커밋했다. 그때의 판은 행동을 시도했는지만 봤고, 셀프 리뷰가 짚어 갈래마다의 기대 표지(규칙 갈래의 거부 문구와 `permission_denials`, 대조 갈래의 성공)를 더한 뒤 `--rejudge`로 저장한 넷을 다시 판정했다. 셋째 실행의 두 갈래와 둘째 실행의 `대조`가 측정이고 `규칙-2`는 Edit 미시도로 측정 아님이다(종료 1). 넷의 갈래를 맞바꾼 사본은 두 갈래 모두 여섯 행동이 표지 없음으로 걸려, 표지가 갈래를 가르는 것을 봤다(세션 스크래치 스크립트로 사본을 지었다). 아래 결론은 셋째 실행에서 낸다.

- **경로 규칙은 쓰기·편집·읽기를 막는다.** 셋째 실행의 `규칙`에서 가짜 주 체크아웃의 Write와 Edit, 가짜 `~/.claude`의 Read가 모두 결과의 `permission_denials`에 들었고, 도구 결과는 `File is in a directory that is denied by your permission settings.`였으며, 파일은 생기거나 바뀌지 않았다. 대조에서는 같은 Write가 파일을 만들었고 Read가 표지 낱말을 돌려주었다. 대조의 Edit은 둘째 실행에서 파일을 고쳤고(먼저 Read 했다), 셋째 실행에서는 Read 없이 불러 `File has not been read yet`으로 실패했다. 규칙 갈래의 Edit 거부는 그 문구가 아니라 위의 거부 문구라 규칙이 막은 것이다.
- **도구 이름만 쓴 규칙은 그 도구를 세션에서 뺀다.** `규칙`의 init `tools`는 18개이고 `WebSearch`·`ListAgents`가 없었다. 모델이 `ToolSearch`(`select:WebSearch,ListAgents`)로 찾으니 `No matching deferred tools found`였다. 대조의 init `tools`는 28개이고 둘이 있었으며, 둘 다 불려 결과를 돌려주었다(검색 결과, 다른 세션이 없다는 글). 대조에만 있던 열 개는 `BLOCKED_TOOLS` 아홉 모두와 `PowerShell`이었다(`--rejudge`가 찍는 init `tools`의 차. 둘째 실행도 같다). `PowerShell`이 빠지는 것은 `spec.md`의 "막는 규칙을 둔 세션에는 PowerShell 도구가 없다"와 같다.
- **서브에이전트의 막힌 호출은 본 세션 결과의 `permission_denials`에 실린다.** `규칙`에서 서브에이전트(Agent, `model: haiku`)가 부른 가짜 주 체크아웃의 Write(`parent_tool_use_id`가 붙은 `tool_use`)가 막혔고 그 id가 본 세션 결과의 `permission_denials`에 있었다. 대조에서는 같은 Write가 파일을 만들었다. `tools/rerun_checks.py`의 오염 검사는 `permission_denials`의 id 에 든 호출을 보지 않으므로(그 독스트링의 "오염"), 이 꼴의 서브에이전트 거부를 오염으로 세지 않는다고 본다(코드 읽기. 티켓 11의 09 메모가 남긴 물음). 셋째 실행의 서브에이전트는 두 갈래 모두 백그라운드로 떴다(`Async agent launched successfully`). 둘째 실행의 `대조`는 서브에이전트 보고가 Agent 결과로 바로 돌아왔다.
- **init 의 `mcp_servers`는 비었고 `plugins`는 내장 셋과 계정 동기화 둘이었다.** 두 갈래 모두 같다. 동기화 둘은 이 티켓이 허용 모임에 더했다(`SYNCED_PLUGINS`).

못 본 것: 한 꼴마다 갈래 하나에 측정 회차 하나(셋째 실행)이고, Opus와 다른 노력은 재지 않았다. 같은 규칙을 다른 길(Bash로 쓰기, 상대 경로)로 비켜 가는 것은 재지 않았고 오염 검사가 받친다. 바깥 상태 도구 일곱 가운데 `ListAgents`만 불렀다. 나머지 여섯은 init 목록에서 빠진 것만 봤다. 규칙 갈래의 서브에이전트는 두 실행 모두 백그라운드로 떠, 앞쪽으로 뜬 서브에이전트의 거부가 `permission_denials`에 실리는지는 재지 않았다.

## 2026-10-27 결과: 막는 규칙의 새 자리

파일럿 첫 실행 뒤 러너가 막는 규칙을 클론의 `.claude/settings.local.json`에서 회차 폴더의 `deny-settings.json`으로 옮기고 세션 명령에 `--settings <그 파일>`을 붙였다(`spec.md` "러너가 기대는 `claude -p`의 동작"의 2026-10-27 주석). 같은 프로브를 새 자리로 한 번 돌았다. 두 갈래 모두 임시 폴더(클론 밖)의 규칙 파일을 `--settings`로 받고, 대조는 빈 목록이라 두 갈래의 차이는 규칙의 내용뿐이다. 두 갈래 모두 측정이었다(종료 0, `2026-10-27/`의 두 요약).

- **새 자리의 규칙도 막는다.** `규칙`에서 Write·Edit·Read와 서브에이전트의 Write가 모두 `File is in a directory that is denied by your permission settings.`로 막혔고, 파일 표지(새 파일이 생기지 않았다, 고친 파일이 그대로다, 답에 홈 표지 낱말이 없다)가 맞았다. 이름만 쓴 규칙의 두 도구는 init `tools`에 없고 `ToolSearch`가 `No matching deferred tools found`였다. 대조에서는 Write와 서브에이전트의 Write가 파일을 만들었고 Read가 표지 낱말을 돌려주었으며, `WebSearch`·`ListAgents`가 불려 결과를 돌려주었다(대조의 Edit은 Read 없이 불러 `File has not been read yet`이었다).
- **init `tools`의 차는 옛 자리와 같다.** `--rejudge`가 찍은 차(대조에만 있는 열 개: `BLOCKED_TOOLS` 아홉과 `PowerShell`)가 2026-10-26 실행의 `규칙-2`·`규칙-3`과 글자까지 같았다. 그래서 자리를 옮겨도 규칙이 세션에서 빼는 도구는 같다고 본다(두 자리 모두 한 회차씩).

못 본 것: 한 갈래 한 회차이고 Sonnet medium 이다. 파일럿의 실제 회차(Opus, B 의 프로젝트 설정이 있는 클론)에서 새 자리가 막는지는 다음 파일럿 실행의 오염 검사와 `denied_calls`가 본다. 파일럿 첫 실행의 실제 회차는 옛 자리의 규칙으로도 init `tools`에 `PowerShell`이 있었다(회차 기록의 `init_tools`). 그 차이는 가르지 않았다.

## 2026-10-27 결과: 파일럿(설계 8절의 확인)

조건 판 2의 여섯 회차(`records/`의 회차 번호 3·4, E 는 2·3)를 주로 보고, 판 1의 다섯 회차는 판 1 결함(허용 목록의 `USERNAME`, 게이트의 B 설정 `env`, 클론에 쓴 막는 규칙)과 무관한 항목에서만 보탠다. 자료는 회차 기록, 회차 폴더의 stream-json 원본(판 1·2 합쳐 17파일)과 로그, 전용 설정 폴더의 세션 기록이다. 모델은 새로 부르지 않았다. 아래 수는 측정이 아니라 손으로 본 것이다. 친 스크립트는 `pilot_checks/`에 커밋했지만 값을 찍기만 하고 측정 표지를 세지 않으며(`.claude/rules/probes.md` 첫 항목의 프로브가 아니다), 출력은 세션의 명령과 글을 옮겨 찍을 수 있어 커밋하지 않았다. 그래서 수는 그 스크립트를 다시 쳐야 다시 나온다. 항목마다 근거를 "기록에서 셌다", "스크립트 출력을 봤다(스크립트 이름)", "손으로 봤다(본 것)", "코드를 읽었다", "어림"으로 적는다. 비용 수치는 따로 적지 않으면 기록의 `official_usd`이고, 채우기(`official_cost/`) 전의 옛 셈이다. 9의 web 시험 판정은 없어졌고, 명세 프로브(`headless_flags/`, 기본 설정 폴더·Sonnet low)가 본 2·3·4·5·7은 전용 설정 폴더와 Opus xhigh·Sonnet medium에서 같은지만 본다.

- **1. 기록이 전용 설정 폴더 아래에만 생긴다: 맞다.** 러너가 띄운 본 세션 id 열둘이 모두 전용 설정 폴더의 `projects/C--Users-User-rerun-rounds-<회차>-clone/<id>.jsonl`에 하나씩 있고, `~/.claude/projects/`에는 0개였다(파일 이름만 봤다). 주 체크아웃 사용량 장부의 네 파일에서 그 id와 낱말 `rerun-rounds`가 0건이었다. init 의 `memory_paths`는 모두 전용 폴더 아래였고 `apiKeySource`는 `none`, 기록의 `account`는 열하나 모두 njh4803이다. 설계 5절이 미룬 어림대로 `hook_session_usage`가 end-user-continuation 클론에 계정 장부를 썼다. 주 체크아웃 장부의 마지막 `ingest`는 대부분의 회차보다 앞이지만, `ingest`의 기본 기록 폴더가 `~/.claude/projects`라 다음 `ingest`에도 들지 않는다고 본다(코드를 읽은 어림). 근거: 클론 장부는 `clone_ledger.py`의 출력을 봤다. `~/.claude/projects/`는 `find`로 파일 이름만, 주 체크아웃 장부는 `grep`으로 id와 낱말을 손으로 봤다.
- **2. 기록 파일의 모델·노력이 갈래와 같다: 맞다.** 판 2 본 세션 일곱의 `main_lines`가 모두 갈래의 (모델, 노력) 한 줄이고(A 넷 Opus xhigh 434·503·704·659줄, E 셋 Sonnet medium 116·85·116줄), 그 수가 stream-json의 본 세션 assistant 이벤트 수와 세션마다 같았다. 06의 셈과 러너가 같은 틀린 꼴로 맞는 순환은 다른 출처의 수와 맞으므로 깨졌다고 본다. `model_mismatch`는 열하나 모두 비었다. 서브에이전트는 A가 Opus xhigh(물려받은 것)와 Sonnet high(B 의 code-review 표준 축), E가 Sonnet medium과 Sonnet high였다. 근거: 기록, `scan_streams.py`, `scan_records.py`.
- **3. 구독 로그인에서 `--max-budget-usd`가 멈춘다: 볼 수 없었다.** 러너는 호출마다 예산을 넘겼지만 회차 비용이 상한의 절반에도 닿지 않아 결과 이벤트가 모두 `success`였다. 명세 프로브(Sonnet low)의 결과에 기댄다. 근거: 기록, `scan_streams.py`.
- **4. 결과 이벤트의 비용 칸과 한도 이벤트의 사용률: 맞다(사용률은 꼴 하나가 다르다).** 결과 이벤트 모두에 `total_cost_usd`와 비지 않은 `modelUsage`가 있었다. 한도 이벤트 195개 모두 `unifiedWindows`의 `five_hour`·`seven_day`에 `utilization`이 있었고, 맨 위 `utilization`은 `status: allowed_warning`인 116개에만 있었다. 러너는 `unifiedWindows`를 읽어 열하나 모두 찼다. 기록의 두 비용(Claude Code 셈과 공식 단가)이 달랐던 것은 "2026-10-27 결과" 표의 `official_cost/` 행이 가렸다(세션 기록 파일의 토큰이 모자랐다). 근거: `scan_streams.py`, `ratelimit.py`.
- **5-1. 막는 규칙이 auto 모드에서 막는다(Opus): 볼 수 없었다.** 판 2 회차 모두 규칙 파일을 `--settings`로 받았지만 모델이 그 대상을 부르지 않았다. 판 2 stream에서 러너의 경로 규칙이 내는 거부 문구(`File is in a directory that is denied by your permission settings.`)는 0건이었다. 판 2 stream에 있는 `blocked by a deny rule`은 클론 프로젝트 설정의 `Read(//**/.env)`가 `.env` 읽기를 막은 것이고 러너의 규칙이 아니다. 규칙 꼴은 `deny_shapes/`(Sonnet medium)만 봤고, 본 측정의 기록(`permission_denials`)에 맡긴다. 근거: 기록, `scan_streams.py`.
- **5-2. 클론 커밋에서 pre-commit과 commit-msg 훅이 돈다: 맞다.** 준비 로그에 두 훅의 설치 줄이 있고, 커밋한 판 2 회차 모두의 `git commit` 도구 결과에 commit-msg 훅과 pre-commit 훅(`ruff check`, `run_checks.py`, `pytest`)의 줄이 있었다. 근거: `scan_streams.py`, 회차 폴더의 `setup.log`와 클론의 `.git/hooks/`를 손으로 봤다(conversation-02-A-3, end-user-continuation-02-A-3).
- **5-3. init 의 플러그인과 MCP: 다르다.** `mcp_servers`는 모두 `[]`이고 `plugins`는 계정 동기화 둘과 내장 셋이었다. B 가 켠 `pyright-lsp`는 init 에 없고 init `tools`에 `LSP`도 없다. 전용 설정 폴더의 `installed_plugins.json`이 비어, 켰지만 깔지 않은 플러그인이 빠진 것으로 본다(어림). GitHub 에 닿는 플러그인·MCP는 없었다. 마켓 플러그인의 init 꼴(09의 메모)은 실리지 않아 보지 못했다. 근거: `scan_streams.py`, 클론의 `.claude/settings.json`과 전용 설정 폴더의 `plugins/installed_plugins.json`·`plugins/marketplaces/`를 손으로 봤다.
- **5-4. 세션 셸에서 허용 목록 밖의 이름이 비어 있다: 맞다(`GH_TOKEN` 자체는 볼 수 없었다).** 기록의 `env_names`에 `GH_TOKEN`·`GITHUB_TOKEN`·`ANTHROPIC_API_KEY`가 없고, 도구 결과에 앞의 둘의 글자가 0건이었다. 모델이 `-m llm` 전에 `ANTHROPIC_API_KEY`를 본 회차 여섯 모두 비어 있었다. 러너를 띄운 셸에 `GH_TOKEN`이 있었는지는 보지 않아 거르기를 보인 것은 아니다. 근거: 기록, `key_checks.py`(값은 찍지 않는다).
- **6. 인계 지시문의 붙여 넣기와 `--resume`: 맞다(둘 다 실제로 났다).** end-user-continuation-03-E-2에서 `hook_handoff`의 계기(셀프 리뷰 직전), 지시문으로 끝난 결과 글, 기록의 `인계` 호출, 인계 뒤 세션의 결과 커밋이 모두 있었다. 그 회차는 첫 세션의 뿌리 쓰기로 측정 아님(오염)이다. 지시문의 `모델:` 줄이 갈래와 달랐고(`Opus 5.5 / medium 레벨 스윕의 갈래`) 러너가 그대로 붙였다. 조건 판 4부터 러너가 갈래 값으로 바꿔 붙인다. `--resume`은 end-user-continuation-02-A-4에서 같은 세션 id 의 개입 호출 둘과 개입 문장 두 번으로 봤다. 개입의 까닭은 모델이 백그라운드 리뷰어를 기다리겠다며 차례를 끝낸 것이고, 개입 둘이 Claude Code 셈으로 $11.54를 더했다. 근거: 기록, `compact_handoff.py`, `handoff_reasons.py`, `result_texts.py`.
- **7. `-p`에서 `AskUserQuestion`: 맞다.** 열하나 모두 init `tools`에 없고 부르거나 찾은 호출이 없었다. 판 2 회차는 모두 `asked_at_end: false`다. 근거: 기록, `scan_streams.py`.
- **8. 시작 컨텍스트를 실제 지시문 세션과 견준다: 다르다.** `tools/token_report.py`의 `start_parts_of`와 같은 셈으로 낸 글자 수가 같은 과제의 실제 세션의 약 52~63%였다(conversation-02 34,066/65,533, end-user-continuation-02 37,393/59,810~63,699). 빠진 것은 지연 도구 목록(약 6천~1만 자), 플러그인 스킬(실제 장부의 `coderabbit`, `claude-hud` 등), 지침 파일 887자(사용자 수준 지침이나 메모리로 본다, 어림), 그 밖 약 1만 자(가르지 않았다)다. 근거: `start_parts.py`, 실제 쪽은 장부 행을 그대로 읽었다.
- **9. 숨은 시험의 덮어쓰기와 게이트가 A 의 결과에서 돈다: 맞다.** 판 2의 끝남 다섯 모두 게이트 종료 코드가 0으로 실렸고, 숨은 시험 통과 수(9/10, 9/10, 63/65, 63/65, 15/15)의 전체 수가 `pilot.json`의 숨은 시험 수와 같다. 옛 게이트 묶음 여섯은 두 회차 모두 시간을 넘기지 않았고, 파일 시각으로 약 4분 반이었다. 근거: 기록, 파일 시각, 코드를 읽었다.
- **10. 같은 과제의 A 두 번의 비용 차: 값을 냈다.** 기록의 `official_usd`(옛 셈)로 conversation-02 판 2가 $19.69·$23.76(판 1까지 넷의 변동계수 약 8%), end-user-continuation-02 판 2가 $32.67·$37.10(약 7%)이다. 채운 셈은 Claude Code 셈과 같아 $21.34·$25.82, $34.87·$40.46이다(변동계수는 옛 셈으로만 냈다). end-user-continuation-02의 A 회차마다 과제의 카나리아 시험이 띄운 하위 `claude -p` 세션 4~8개가 같은 프로젝트 폴더에 기록을 남겼고, 응답 셈으로 판 1·2 넷 합 약 $2.39(판 2 둘은 약 $0.87, A 비용의 1~3%)가 기록에 들지 않았다. 조건 판 4부터 러너가 그 셈을 `other_usd`로 더한다. 근거: 기록, `extra_sessions_cost.py`(셈은 고치기 전의 `rerun_cost`와 같은 단가표). 표준편차는 손셈이다.
- **11. 셋째 과제의 E 한 번: 맞다.** E-3이 끝남이었고 모델 확인이 비었으며, 게이트 셋 모두 0, 숨은 시험 15/15, 기록의 공식 단가 $2.65(옛 셈. 채운 셈과 Claude Code 셈은 $2.79)였다. 공식 문서가 적은 Sonnet medium의 확인을 구하며 멈춤은 판 2의 E 두 회차에서 나지 않았다. 작은 과제 하나의 두 회차라 갈래의 성질로 일반화하지 않는다.

정한 것(일지 2026-10-28-10 "설계 8절 확인과 사람 결정"). 사람이 넷을 정했다. 하위 세션의 비용은 회차 비용에 더하고(10), 인계 지시문의 모델 줄은 갈래 값으로 바꾼다(6). 이 둘과 공식 단가 셈의 채우기로 조건 판이 4로 올랐다. `pyright-lsp`와 플러그인 스킬이 빠진 것(5-3, 8)은 설계가 뺀 MCP와 같은 한계로 명세에 적었다. 서브에이전트의 허용 모임은 지금 규칙대로 고정한다(2). 세션이 정한 기본값은 다섯이다. 백그라운드를 기다리다 끝난 것도 개입으로 센다(모든 갈래에 같은 규칙). 근거 스크립트는 `pilot_checks/`에 커밋한다. 예산 멈춤과 Opus 막기(3, 5-1)는 따로 재지 않는다. 사용률은 `unifiedWindows` 기준이다(4). 본 측정의 첫 인계 뒤 멈춤은 설계대로 둔다(6).

못 본 것: 러너의 막는 규칙이 Opus에서 실제 호출을 막는 것(5-1)과 예산 멈춤(3), 세션 셸의 `GH_TOKEN` 그 자체(5-4), 실제 지시문 세션에 `pyright-lsp`가 실리는지(사용자 설정을 읽지 않았다), 시작 컨텍스트 그 밖 약 1만 자의 정체, 서브에이전트가 앞쪽으로 뜬 때의 거부(이 파일럿에 막힌 서브에이전트 호출이 없었다). 하위 `claude -p` 세션의 도구 입력도 보지 않았다. 오염 검사는 본 세션 stream-json만 훑고(코드를 읽었다), 그 세션이 러너의 `--settings` 막는 규칙을 받았는지는 그 명령 줄을 보지 못해 모른다(어림).

## 2026-10-31 결과: 본 측정 1차

조건 판 4, 과제 8개(`main.json`), 갈래 다섯으로 돌았다. 판정 출력은 `judge-main.md`(`uv run python -m tools.rerun_judge --tasks .scratch/model-rerun/probes/main.json`의 출력)이고, 도구가 찍은 결론은 "결론 없음: S_A가 T의 절반보다
적다(S_A 2, T 7)"이다. 회차 기록은 `records/`의 본 측정 회차이고, 경위와 읽은 것은 일지 2026-10-31-02, 결정은 ADR 0029 이력
2026-10-31이다.

## 변이

`rerun_files_mutations.toml`(2026-10-23, 티켓 01의 셀프 리뷰 전, 커밋하지 않은 작업 트리에서 기준 9999e83e). 이 티켓의 시험은 구현 전에 모듈이 없어 수집 오류로만 빨갰다. 변이 21 모두 기대대로 빨갰다(각 1 failed. 거부를 기대한 열다섯은 `DID NOT RAISE` 표지까지 맞았다). 셀프 리뷰를 반영한 뒤(같은 날, 커밋하지 않은 작업 트리, 기준 9999e83e) 글 칸의 꼴, 게이트의 수와 차례, 준비 명령, 실패 노드, 끝남의 결과 커밋, 회차 폴더 경로, 유한한 수, 깊은 중첩과 UTF-8 아닌 파일, 과제 목록 쓰기의 다시 풀기를 더하고 옛 변이 셋(참거짓 판, 이름 칸, 쓰기의 다시 풀기)을 고친 코드에 맞췄다. 처음 돌린 39 가운데 다섯이 표지가 어긋났다. 넷은 다른 거부가 먼저 걸려 그 갈림을 재지 못한 시험이었고(끝의 하위 이유, 파일럿의 층, 준비 명령, 숨은 시험의 수를 고르는 `-k`), 하나는 표의 정규식 이스케이프였다. 시험과 표를 고친 뒤 변이 39 모두 기대대로 빨갰다(표지를 단 서른셋은 `DID NOT RAISE` 서른하나, `RecursionError`·`UnicodeDecodeError` 하나씩이 맞았고, 표지 없는 여섯은 빨강만 본다). PR 직전 `bug-perf-review`를 반영한 뒤(같은 날, 커밋하지 않은 작업 트리, 기준 04edfe96에 origin/main 975bf04c를 합친 cac5e3e5) float로 담지 못하는 큰 정수, 자릿수 한도를 넘는 정수 리터럴, 쓰기의 유한하지 않은 수, 회차 폴더 경로와 실패 노드가 받던 유니코드 줄 구분 문자 셋(U+0085·U+2028·U+2029)을 거부하는 사례를 더하고 옛 변이 넷(회차 폴더 경로와 실패 노드의 꼴, 무한대와 NaN, 깊은 중첩)을 고친 코드에 맞췄다. 더한 시험 사례 여섯은 고치기 전에 빨간 것을 봤고, 변이 44 모두 기대대로 빨갰다(표지를 단 서른여덟은 `DID NOT RAISE` 서른셋, `RecursionError`·`UnicodeDecodeError`·`OverflowError`·`Exceeds the limit`·`Out of range float` 하나씩이 맞았고, 표지 없는 여섯은 빨강만 본다). 셀프 리뷰를 반영한 뒤(같은 날, 커밋하지 않은 작업 트리, 기준 cac5e3e5) 두 칸의 줄 구분 문자 사례를 `str.splitlines`가 줄을 끊는 문자를 코드 포인트 전부에서 센 매개변수 시험으로 바꾸고, 줄 구분 문자 변이 둘을 셋을 함께 지우던 것에서 그때까지 시험이 없던 문자 하나(회차 폴더의 U+2029, 실패 노드의 U+0085)만 지우는 것으로 바꿨다. 변이 44 모두 기대대로 빨갰고, 바꾼 두 변이는 그 문자의 매개변수 사례에서 빨갰다(표지 내역은 앞과 같다). PR #361의 봇 회차를 반영한 뒤(같은 날, 커밋하지 않은 작업 트리, 기준 d1d5a7ed) 회차 기록의 회차 폴더 칸을 뿌리를 뺀 이름(`round_dir_name`)으로 좁혀 회차 폴더 경로의 정규식과 그것을 겨누던 변이 둘(아무 글이나 받는다, U+2029)을 뺐고, `write_record`를 임시 파일과 하드 링크로 고쳐 덮어쓰기 변이를 `os.replace`로 바꾸고 쓰기 실패를 겨누는 변이 둘(기록 파일에 바로 쓴다, 임시 파일을 지우지 않는다)을 더했다. 표지 없던 여섯은 변이를 손으로 넣어 실패 출력을 본 뒤 고른 단언에서만 나오는 문구(값까지 든 `assert` 줄, `).gates_green`·`).hidden_passed`, `Extra items in the left set`과 `'subprocess'`)를 표지로 달았다. 더한 시험은 고치기 전에 반쯤 쓴 기록 파일이 남아 빨간 것을 봤고, 변이 44 모두 기대대로 빨갰다(이제 마흔넷 모두 표지가 있다). 봇 반영분의 셀프 리뷰를 반영한 뒤(같은 날, 같은 기준) 임시 파일 이름에 난수를 붙이고 `"x"`로 열게 고쳐 덮어쓰기 변이의 원문을 맞추고, 변이 둘(임시 파일 이름이 pid만 쓰고 그 이름을 덮어 연다, os의 하위 프로세스 길을 쓴다)을 더했다. 둘 다 손으로 넣어 실패 출력을 본 뒤 표지를 골랐고, 앞의 것은 둘째 쓰기가 같은 기록이면 같은 바이트로 다시 채워져 초록이어서 시험이 다른 기록을 쓰게 고친 뒤에 빨갰다. 변이 46 모두 기대대로 빨갰다(마흔여섯 모두 표지가 있다). 티켓 02가 숨은 시험 노드 ID의 파일 부분과 시험 지원 파일 칸을 허용 목록 꼴로 좁힌 뒤(2026-10-23, 커밋하지 않은 작업 트리, 기준 d0e696c9) 노드 ID를 마지막 `::`에서 자르는 변이가 값을 돌려주지 않고 거부되어 표지를 그 거부 문구로 바꿨고, 두 칸의 꼴을 겨누는 변이 둘(파일 부분을 아무 글이나 받는다, 지원 파일 칸을 아무 글이나 받는다)을 더했다. 바꾼 하나와 더한 둘을 골라 돌려 셋 모두 표지까지 기대대로 빨갰다. 나머지 마흔다섯은 원문 확인(`--check`)만 했다.

`rerun_hidden_mutations.toml`(2026-10-23, 티켓 02의 셀프 리뷰 전, 커밋하지 않은 작업 트리에서 기준 d0e696c9). 이 티켓의 시험은 구현 전에 모듈이 없어 수집 오류로만 빨갰다. 처음 돌린 변이 17 가운데 열다섯은 표지까지 기대대로 빨갰고, 둘(자식 환경에 `VIRTUAL_ENV`를 남긴다, 저장소 변수를 남긴다)은 빨갰지만 표지가 어긋났다. 표에 두 변이의 고친 줄을 서로 바꿔 적은 것이었고, 맞바꾼 뒤 그 둘을 다시 돌려 표지까지 기대대로 빨갰다. 셀프 리뷰 표준 축이 그 판의 표지 셋(낱말 경계, `tests/` 빼기, 같은 노드 둘)이 시험 소스의 조각이라 다른 단언이 빨개져도 출력에 실린다고 짚었다. 단언에 메시지를 붙이거나 손으로 변이를 넣어 본 실패 출력의 diff 줄로 바꾸고, 덮을 자리의 링크와 저장소 변수 변이의 표지도 `AssertionError:` 줄로 좁혔다. 같은 리뷰의 두 축이 짚은 두 결함(M에서 돌지 않은 바뀐 시험이 까닭 없이 사라진다, 덮지 못한 `OSError`가 실패 갈래가 되지 않는다)을 고치며 변이 둘을 더했고, 고친 뒤 열아홉 모두 표지까지 기대대로 빨갰다. PR 직전 `bug-perf-review`가 짚은 BOM 결함을 고치고 못 보는 것 둘을 시험으로 고정하며 변이 셋을 더했고, 그 셋만 담은 표를 커밋하지 않은 작업 트리(기준 fbcd6239)에서 돌려 모두 표지까지 기대대로 빨갰다. PR #363의 CodeRabbit Minor(M의 풀리지 않는 시험 파일)를 반영하며 변이 하나(M 의 풀리지 않는 파일을 시험이 없는 것으로 본다)를, 그 반영분의 셀프 리뷰 명세 축을 반영하며 하나(M 의 풀리지 않는 파일이 있어도 후보가 성공으로 끝난다)를 더했다(일지 2026-10-23-18의 봇 회차와 그 셀프 리뷰). 티켓 07의 셀프 리뷰를 반영한 뒤(2026-10-23, 커밋하지 않은 작업 트리, 기준 c2c03eae) 변이 24 전부를 돌려 모두 기대대로였다. 그 리뷰가 짚은 작업 트리 자리 자체의 링크를 `overlay_target`이 보게 고치며 변이 하나(작업 트리 자리 자체의 링크를 보지 않는다)를 더했고, 그 변이도 고른 표지까지 기대대로 빨갰다. 스물다섯 모두 표지가 있다. 티켓 05가 실제 후보 표에서 02 자신이 NUL 문자열로 실패 갈래인 것을 찾아 문자열을 NUL에서도 나누게 고치며(2026-10-23, 커밋하지 않은 작업 트리, 기준 de5423bd) 원문이 바뀐 23번을 맞추고 NUL 나누기 변이(9번)를 더했다. 원문 확인은 25 모두 한 번씩이었고, 8·9·23번을 골라 돌려 모두 표지까지 기대대로 빨갰다(9번은 표지를 비운 첫 실행의 출력에서 골랐다). 고친 줄을 겨누는 시험 둘은 고치기 전에 빨간 것을 봤다. 셀프 리뷰를 반영하며(같은 날, 같은 기준) 9번이 느린 `sort_candidate` 시험까지 고르던 `-k`를 값 층 시험 하나(`NUL_이_든_문자열은_그_자리에서도`)로 좁혔고, 다시 돌려 표지까지 기대대로 빨갰다(1 failed, 0.90초). 07과 05를 합친 표(2026-10-23, 티켓 07이 origin/main 062e9734를 합친 작업 트리)는 원문 확인에서 26 모두 한 번씩이었다.

`rerun_select_mutations.toml`(2026-10-23, 티켓 05의 셀프 리뷰 전, 커밋하지 않은 작업 트리에서 기준 c3c2cfcf). 구현을 시험보다 먼저 써 시험은 빨강을 본 적이 없었다. 처음 판 27은 표지를 비워(`표지-미정`) 실패 출력을 받았고, 26이 빨갰다. 23번(중간 층을 작은 층의 씨앗으로 섞는다)은 시험의 층이 셋이라 고를 것이 다 들고 차례만 바뀌어 초록이었고, 21번(본 측정이 파일럿이 아닌 목록을 받는다)은 종류 검사가 아니라 층 부족으로 빨개 그 갈림을 재지 못했다. 본 측정 시험을 후보 21개로, 종류 시험을 파일럿 목록의 종류만 바꾼 입력으로 고친 뒤 21~24번이 모두 빨갰고, 출력에서 고른 표지를 단 27이 모두 기대대로였다. 셀프 리뷰를 반영한 뒤(같은 날, 같은 기준) 원문이 바뀐 다섯(5·6·7·12·13)을 맞추고 새 갈림 열하나(28~38)를 더했다. 그 다섯과 겨누는 시험에 사례가 더해진 둘(9번의 되살리기 오류 시험에 파일 이름 사례가, 27번의 병합 기록 시험에 꼬리·제목 중간의 PR 번호·티켓 없는 PR·BOM·곁가지 커밋 사례가 더해졌다), 새 열하나를 골라 돌려 모두 표지까지 기대대로 빨갰다. 새 열하나는 표지를 비운 첫 실행의 출력에서 표지를 골랐고, 36번의 `PermissionError: [Errno 13] Permission denied`는 이 PC(윈도)의 문구다. 그 사이 같은 변이 실행을 두 번 띄워 두 프로세스가 같은 모듈에 변이를 넣은 일이 있었다. 둘 다 끄고 원문 확인으로 원문이 제자리인 것을 본 뒤 한 번만 다시 돌렸고, 겹친 실행의 결과는 쓰지 않았다. PR 직전 `bug-perf-review`를 반영하며(같은 날, 커밋하지 않은 작업 트리, 기준 5b1efeca) 브랜치 표의 비용 범위, 출력 자리가 폴더이거나 쓸 수 없는 파일인지, 알림의 git 이름을 고쳤다. 그 시험 아홉은 고치기 전에 빨간 것을 봐 변이를 더하지 않았다. 36번이 겨누는 쓰기 실패 시험은 넓힌 앞선 검사에 먼저 걸리지 않게, 검사 뒤 가르기를 지을 때 그 자리에 폴더를 만들도록 바꿨다. 원문 확인은 38 모두 한 번씩이었고, 35·36번을 골라 돌려 둘 다 표지까지 기대대로 빨갰다. PR #371의 CodeRabbit 첫 회차를 반영하며(같은 날, 커밋하지 않은 작업 트리, 기준 a5726119) 과제 목록을 쓸 때의 `ShapeError`도 2로 끝내고 빈 `top_model_effort`를 가르기 전에 거부했다. 그 시험 둘은 고치기 전에 빨간 것을 봐 변이를 더하지 않았다. 36번의 원문을 새 `except` 줄로, 바꿀 글을 `except ShapeError`(`OSError`를 뺀다)로 맞췄고, 원문 확인은 38 모두 한 번씩, 36번을 골라 돌려 표지까지 기대대로 빨갰다. 이어 셀프 리뷰 명세 축이 인코딩 실패(브랜치 표의 홀로 선 서로게이트)도 `_write`를 벗어나 트레이스백과 빈 목록 파일을 남기는 것을 짚어(같은 날, 같은 기준), 글을 다 짓고 UTF-8 바이트로 바꾼 뒤에 열고 `ValueError`를 받게 고쳤다. 그 시험은 고치기 전에 `UnicodeEncodeError`로 빨간 것을 봤다. 36번의 원문과 바꿀 글(`except ValueError`)을 다시 맞추고 새 갈림 둘(39번 바이트로 바꾸기 전에 연다, 40번 인코딩 실패를 2로 바꾸지 않는다)을 더했다. 원문 확인은 40 모두 한 번씩이었고, 36번은 표지까지 기대대로 빨갰으며, 39·40번은 표지를 비운 첫 실행의 출력에서 표지를 골라 다시 돌려 둘 다 기대대로 빨갰다.

`rerun_judge_mutations.toml`(2026-10-23, 티켓 03의 셀프 리뷰 전, 커밋하지 않은 작업 트리에서 기준 d0e696c9). 판정과 탐색의 시험은 조각마다 구현 전에 빨간 것을 봤지만 탐색 일곱은 `explore` 칸이 없다는 오류로, 명령 줄 넷은 `main`을 import하지 못하는 오류로 한꺼번에 빨갰고, 파일럿 빼기 시험은 구현 전에 우연히 초록이었다. 후보 조건과 결론 없음의 갈림 하나하나는 빨강을 본 적이 없었다. 모르는 판, C_A가 0인 표본, U가 같은 후보의 차례, 결론 없음의 탐색 머리는 시험보다 구현이 먼저였다. 모르는 판의 첫 시험은 다섯 갈래 가운데 하나만 판이 비어 판이 갈래 사이에 다른지 보는 검사에도 걸려 모르는 판의 검사를 지워도 초록일 것이라, 표를 짓기 전에 모든 갈래의 판이 빈 과제를 더하고 까닭 문구를 "claude 판을 모르는 갈래"로 나눴다(고친 시험이 구현 전에 빨간 것을 봤다). 변이 28 모두 빨갰고 처음 돌린 판에서 셋이 표지가 어긋났다. 셋 다 pytest가 긴 값을 줄여 찍어 예상한 `assert` 줄이 출력에 그대로 실리지 않은 것이라, 출력에 찍힌 diff 줄(`Left contains one more item: …`, `Right contains one more item: …`, `At index 0 diff: 3 != 2`)로 바꿨다. 처음 고른 셀 수 없음 문턱의 표지 `is None`은 실패 줄 위에 보이는 시험 코드에도 실려 다른 단언이 빨개져도 맞을 수 있어, 그 변이를 넣어 실패 출력을 본 뒤 값까지 든 머리(`AssertionError: assert (0.2, 0.6) is None`)로 바꿨다. 고친 넷을 다시 돌려 모두 기대대로 빨갰다(스물여덟 모두 표지가 있고, 각 1 failed다). 셀프 리뷰를 반영한 뒤(같은 날, 커밋하지 않은 작업 트리, 기준 d0e696c9) 변이 일곱(표지가 둘 이상인 README, 회차가 없는 과제, 목록에 없는 과제, 기록 꼴이 아닌 파일, 모듈로 띄울 때 출력 다시 열기와 입구, D에서 C로 올리는 짝)을 더하고, 옛 변이 둘(끝 표지, 올리기 짝)을 고친 코드와 바뀐 시험 이름에 맞췄다. 더한 시험 가운데 표지 둘·저장소의 README·회차가 없는 과제·D→C 짝·UTF-8 아닌 README는 고치기 전에 빨간 것을 봤고, 처음부터 초록이던 셋(목록에 없는 과제, 기록 꼴이 아닌 파일, 모듈로 띄우기)은 변이로 빨강을 봤다. 바꾼 아홉(12·13·19·20·21·30·31·32·33번)을 `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/model-rerun/probes/rerun_judge_mutations.toml <번호>`로 골라 돌렸다. 32번은 첫 실행에서 기대대로였고, 나머지 여덟은 첫 실행에 임시 표지를 달아 실패 출력을 본 뒤 고른 단언에서만 나오는 문구로 표지를 바꿨고 다시 돌려 모두 기대대로 빨갰다. 그 가운데 둘(20·21번)의 표지는 셈이 고른 단언까지 가지 못하고 터진 자리의 문구(`KeyError: 'model-rerun-09'`, `회차 기록: JSON이 아니다`)이고, 30번은 출력을 다시 열지 않으면 cp949가 `−`(U+2212)를 쓰지 못해 자식이 죽는 문구(`illegal multibyte sequence`)다. 표 전체 35는 시험을 고쳤으므로 PR 직전 리뷰를 반영해 커밋한 뒤 다시 돈다(`tools/mutate.py` 독스트링의 언제 전체를 돌리나). PR 직전 리뷰를 반영해 커밋한 7310bcf4를 `git worktree add --detach`로 꺼낸 임시 워크트리에서 `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/model-rerun/probes/rerun_judge_mutations.toml`로 전체를 돌려(2026-10-23), 기준선 35 모두 초록이고 변이 35 모두 기대대로 빨갰다(각 1 failed, 도구의 끝 줄 `변이 35 모두 기대대로`). 그 반영은 저장소 README 시험의 검사를 도우미로 빼고 시험 둘을 더했을 뿐, 표가 겨누는 시험은 고치지 않았다. origin/main(c3c2cfcf, 티켓 02가 숨은 시험 노드 ID의 파일 부분을 좁혔다)을 합치며 시험이 지은 과제 목록의 노드 ID 고정 값을 `tests/t.py`에서 `tests/test_t.py`로 바꿨고, 그 병합 커밋 300d000f를 같은 절차로 꺼내 전체를 다시 돌려(2026-10-23) 기준선 모두 초록이고 변이 35 모두 기대대로 빨갰다(도구의 끝 줄 `변이 35 모두 기대대로`).

`rerun_round_mutations.toml`(2026-10-23, 티켓 04, 커밋하지 않은 작업 트리에서 기준 d0e696c9). 이 티켓의 시험은 구현 전에 모듈이 없어 수집 오류로만 빨갰다. 처음 돌린 39 가운데 넷이 어긋났다. 끝의 점과 대소문자의 변이 둘이 초록이었다. 윈도의 `realpath`가 있는 폴더의 이름을 실제 이름으로 바꿔 주기 때문이라, 시험에 아직 없는 머리를 더해 빨강을 봤고 링크를 풀기 전 꼴의 변이와 그 시험을 더했다. 링크 끊기의 변이는 링크를 먼저 끊지 않아도 이 PC 에서 바깥 파일이 남아 기대를 빨강에서 대조군(초록)으로 바꿨다. 저장소 위치 변수의 변이는 고른 표지(`AssertionError`)가 아니라 `git init`의 실패로 빨개져 표지를 그 실패로 바꿨고, 넓은 표지(`AssertionError`)는 실패한 단언 줄(pytest 가 `>`로 가리키는 줄)로 좁혔다. 고친 뒤 변이 40 모두 기대대로였다. 커밋 전 반박 검증을 반영한 뒤(같은 날, 같은 기준) 옛 변이 둘(상대 경로 뿌리, 구분자 둘로 시작하는 장치와 UNC 경로)을 고친 코드에 맞추고, 다섯(표지를 글자 그대로의 이름으로 찾기, 빈 폴더를 지우지 못할 때 표지 다시 심기, 폴더의 읽기 전용 특성, 지우기 직전의 링크 재확인, 파일인 뿌리)을 더했다. 바꾸거나 더한 일곱은 기대대로 빨갰다. 셀프 리뷰를 반영한 뒤(같은 날, 같은 기준) 옛 변이 다섯(표지에 이름 쓰기, 이미 있는 회차 폴더 덮기, 준비가 실패한 뒤의 남은 명령, 시간 넘김, 표지 다시 심기)을 고친 코드에 맞추고, 일곱(찾지 못한 준비 명령, 끊지 못한 링크, `push.followTags`, 클론의 원격 이름, 원본의 pre-push 훅, 읽지 못한 뿌리, 가운데 조각 끝의 공백과 점)을 더했다. 바꾸거나 더한 열둘은 고른 표지까지 기대대로 빨갰다. 그 뒤 변이 52 전부를 돌리자 쉰하나가 기대대로였고, "뿌리 바로 아래의 링크를 회차 폴더로 받는다" 하나가 빨갰지만 표지가 어긋났다. 반박 검증이 더한 지우기 직전의 링크 재확인이 그 링크를 지우지 않고 실패로 돌려, 첫 판정을 빼도 `removed`는 빈 채이고 `not_round`에서 이름이 빠진 단언이 빨개진다. 표지를 그 단언 줄(`assert report.not_round == [target.name]`)로 바꿔 그 변이만 다시 돌렸고 기대대로 빨갰다. 쉰둘 가운데 쉰하나가 표지를 달고 하나는 대조군이었다. PR 직전 리뷰를 반영한 뒤(같은 날, 커밋하지 않은 작업 트리, 기준 8d72b6b2) 고친 줄을 원문으로 쓰던 셋(링크를 푼 꼴, 링크를 풀기 전 꼴, 윈도가 쓸 꼴)을 맞추고, "가운데 조각 끝의 공백과 점을 모두 뗀다"를 "realpath 의 장치 접두를 떼지 않는다"로 바꿨다. 옛 변이는 접두를 뗀 `realpath`가 같은 입력을 늘 막게 되어 결과가 원본과 같아졌다(그 변이만 든 커밋하지 않은 스크래치 변이 표를 `tools/mutate.py`로 고친 코드에 돌려, 그 시험이 초록인 것을 손으로 봤다). 둘(없는 뿌리를 알리지 않는다, 명령 줄의 출력을 UTF-8로 고정하지 않는다)을 더했다. 바꾸거나 더한 여섯은 고른 표지까지 기대대로 빨갰고, 변이 54 전부를 다시 돌려 모두 기대대로인 것을 봤다. 쉰넷 가운데 쉰셋이 표지를 달고 하나는 대조군이었다. 반영분의 셀프 리뷰를 반영한 뒤(같은 날, 커밋하지 않은 작업 트리, 기준 8d72b6b2) `remove_round_dirs`가 없는 뿌리를 `None`으로 알리게 고치며 시험의 호출을 도우미 `_지우기`로 옮겼다. 그 호출 줄을 표지로 쓰던 "폴더의 읽기 전용 특성을 풀지 않는다"의 표지와, 원문의 들여쓰기가 바뀐 "없는 뿌리를 알리지 않는다"의 원문을 맞췄다. 옛 "가운데 조각 끝의 공백과 점을 모두 뗀다"는 그 경로가 있으면 받는다는 새 시험에 겨눠 되살렸다. 그 시험만 구현 전부터 초록이었고, 나머지 새 시험 셋은 고치기 전에 빨간 것을 봤다. 바꾸거나 더한 셋은 고른 표지까지 기대대로 빨갰고, 변이 55 전부를 다시 돌려 모두 기대대로인 것을 봤다. 쉰다섯 가운데 쉰넷이 표지를 달고 하나는 대조군이었다. PR 봇 claude-review의 첫 회차를 반영한 뒤(같은 날, 커밋하지 않은 작업 트리) `_remove`가 실패를 예외로 알리게 고쳐, 그 자리를 원문으로 쓰던 둘(지우기 직전의 링크 재확인, 끊지 못한 링크)을 맞췄고, 고친 자리를 겨누는 넷을 돌려 고른 표지까지 기대대로 빨간 것을 봤다(일지 2026-10-23-32의 봇 첫 회차). 그 반영분을 셀프 리뷰한 뒤(같은 날, 커밋하지 않은 작업 트리, 기준 368a0b4f) 예외 이름을 바꿔 그 둘을 다시 맞추고, 원문이 `try` 안으로 들어간 대조군의 원문을 맞췄으며, 둘(링크를 찾다 막힌 것을 그 폴더의 실패로 바꾸지 않는다, 지우다 막힌 까닭을 알리지 않는다)을 더했다. 새 시험 하나(링크를 찾다 막힌 폴더)는 고치기 전에 빨간 것을 봤고, 까닭의 단언은 있던 시험에 더해 구현 전부터 초록이었다. 고친 셋과 더한 둘, 더한 단언을 지나는 "표지를 맨 끝에 지우지 않는다"까지 여섯을 돌려 대조군은 초록, 다섯은 고른 표지까지 기대대로 빨갰다. 쉰일곱 가운데 쉰여섯이 표지를 달고 하나는 대조군이다. 티켓 07이 링크 끊기를 `tools/tidy_checkouts.py`의 `cut_links`로 모으며(2026-10-23) 그 자리를 원문으로 쓰던 변이의 원문을 `_cut_links(`에서 `cut_links(`로 맞췄고, 원문 확인(`--check`)만 했다. `rerun_hidden_mutations.toml`의 걷기 전 링크 끊기 변이도 같다. 티켓 07의 셀프 리뷰를 반영한 뒤(같은 날, 커밋하지 않은 작업 트리, 기준 c2c03eae) 변이 57 전부를 돌리자 쉰다섯이 기대대로였고 둘이 어긋났다. "찾지 못한 준비 명령을 종료로 적는다"는 빨갰지만 표지가 어긋났다. 07이 `SetupFailed`에 끝난 꼴과 종료 코드의 짝을 보는 불변식을 더해, 그 변이가 단언에 닿기 전에 그 불변식의 `ValueError`로 빨개졌다(출력에 찍혔다). 표지를 그 문구로 바꿨다. "지우기 직전에 링크인지 다시 보지 않는다"는 초록이었다. 07이 모은 `cut_links`가 뿌리가 링크면 끊지 않고 그 뿌리를 돌려줘, 직전 확인을 빼도 같은 폴더가 실패에 든다. 시험에 실패의 까닭이 직전 확인의 문구인지 보는 단언을 더했다. 그 변이에 일부러 없는 표지를 단 커밋하지 않은 사본 표를 돌려, 까닭이 직전 확인의 문구가 아니라 "끊지 못한 링크나 읽지 못한 폴더 1개(첫째 …\\model-rerun-04-A-1-w3)"인 것을 손으로 봤다. 표지를 더한 단언으로 바꿔 그 둘을 다시 돌렸고 고른 표지까지 기대대로 빨갰다. 쉰일곱 가운데 쉰여섯이 표지를 달고 하나는 대조군이다.

`rerun_gates_mutations.toml`(2026-10-23, 티켓 07의 셀프 리뷰 전, 커밋하지 않은 작업 트리에서 기준 c2c03eae). 이 티켓의 게이트 시험은 구현 전에 모듈이 없어 수집 오류로만 빨갰고, 갈림 하나하나는 빨강을 본 적이 없다. 변이 34 모두 빨갰고, 처음 돌린 판에서 열여섯이 표지가 어긋났다. 열하나는 숨은 시험의 셈(`Hidden`)을 견주는 단언이었다. 변이 도구의 출력 끝에서 pytest 가 그 비교를 줄여 찍고(`Full output truncated`) 펼친 줄(`passed: 0 != 5`)만 보여, 예상한 `assert Hidden(...)` 줄이 출력에 그대로 실리지 않은 것이다. 펼친 줄은 변이 도구가 판정 낱말뿐인 표지라고 받지 않았다. 그 변이에 `-vv`를 주고 다시 돌려도 출력은 줄여 찍혔다(변이 도구의 pytest 러너가 `-q`를 붙여 상쇄한다고 어림한다). `-vvv`를 주자 값까지 든 `assert Hidden(passed=0, total=5,` 꼴의 줄이 실려 그 줄을 표지로 썼다. 둘(띄우지 못한 준비, 회차 기록의 시간 넘김 칸)은 펼친 줄(`timed_out: True != False`)로, 끊지 못한 링크의 하나는 diff 줄(`Right contains one more item:`)과 그 값의 끝(`stuck'`)으로 바꿨다. 어긋나지 않은 읽지 못한 폴더의 변이도 표지(`assert [] == [`)가 같은 시험의 끊지 못한 링크 단언에도 실릴 수 있어 같은 꼴(`없음'`)로 좁혔다. 덮을 자리의 링크 변이는 바깥에 썼는지 보는 단언보다 숨은 시험의 셈이 먼저 빨개져, 시험에서 바깥을 보는 단언을 앞으로 옮기고 diff 줄(`At index 0 diff: 'conftest.py' != 'keep.txt'`)을 표지로 썼다. 걷지 않는 변이는 도우미 `_걷혔다`의 두 단언에 메시지를 붙여 그 메시지를 표지로 썼다. 고친 열일곱을 두 번에 나눠 다시 돌려 모두 고른 표지까지 기대대로 빨갰다. 서른넷 모두 표지가 있다. 커밋 전 반박 검증을 반영한 뒤(같은 날, 같은 기준) 원문이 바뀐 셋(걷기 전에 링크를 끊지 않는다, 끊지 못한 링크가 남아도 걷는다, 작업 트리를 걷지 않는다)을 맞추고, 넷(클론의 관리 폴더 안의 링크를 끊지 않는다, 작업 트리 자리가 링크인지 보지 않는다, 클론의 git 폴더가 링크인지 보지 않는다, 링크 끊기가 뿌리 링크를 따라간다)을 더했다. 새 시험 셋(관리 폴더 안의 링크, 링크로 바뀐 작업 트리 자리, 뿌리가 링크인 링크 끊기)은 고치기 전에 빨간 것을 봤다. 링크로 바뀐 클론의 git 폴더 갈래는 구현 뒤에 매개변수로 더해 변이로 빨강을 봤다. 바꾸거나 더한 일곱은 고른 표지까지 기대대로 빨갰다. 서른여덟 모두 표지가 있다. 손자를 남기는 변이는 표의 주석대로 윈도에서만 빨갛다고 어림한다(리눅스에서는 돌리지 않았다). 셀프 리뷰를 반영한 뒤(같은 날, 커밋하지 않은 작업 트리, 같은 기준) 원문이 바뀐 넷을 `--check`로 찾아 맞추고 변이 38 전부를 돌리자, 서른여섯이 기대대로였고 둘이 빨갰지만 표지가 어긋났다. "게이트 전에 숨은 시험 파일을 덮는다"는 리뷰가 `_overlay`의 인자를 줄여, 변이가 넣은 옛 호출이 `TypeError`로 빨개진 것이다. 변이의 호출과 들여쓰기를 맞췄다. "작업 트리 자리가 링크인지 보지 않는다"는 리뷰가 더한 시험(준비 뒤에 작업 트리 자리가 링크로 바뀐다)이 같은 `-k`에 걸려 먼저 빨개진 것이다. 기준선이 그 `-k`(`링크로_바뀌면 and gate`)에서 시험 셋을 골랐고, 모듈 이름에 `gate`가 들어 `and gate`가 모듈의 모든 시험에 맞는다고 어림한다. 그 변이와 이웃 변이(클론의 git 폴더)의 `-k`를 옛 시험의 이름으로 좁혔다. 리뷰가 더한 갈림 셋을 겨누는 변이(작업 트리 자리가 링크여도 게이트를 띄운다, 게이트가 0이 아니어도 숨은 시험을 돈다, UTF-8 이 아닌 junit xml 에서 멈춘다)를 더하고, 임시 표지로 한 번 돌려 실패 출력을 본 뒤 표지를 골랐다. 고친 둘과 좁힌 이웃 하나, 더한 셋을 다시 돌려 모두 고른 표지까지 기대대로 빨갰다. 마흔하나 모두 표지가 있다. PR 직전 `bug-perf-review`를 반영한 뒤(같은 날, 커밋하지 않은 작업 트리, 기준 90f9f675) 링크 끊기의 원문이 바뀐 셋(뿌리 링크를 따라간다, 끊지 못한 링크를 알리지 않는다, 읽지 못한 폴더를 알리지 않는다)을 맞추고, 셋(링크 끊기가 긴 경로를 평범한 경로로 훑는다, 숨은 시험 노드가 없어도 pytest 를 띄운다, 겹친 노드를 겹친 채 센다)을 더했다. 더한 셋이 겨누는 시험은 고치기 전에 빨간 것을 봤다. 더한 셋의 표지는 실패 출력을 보기 전에 실패한 단언에서만 나오는 꼴(diff 줄, 단언의 메시지, 값까지 든 `assert` 줄)로 달았다. 그 가운데 긴 경로의 표지는 반영분의 셀프 리뷰 표준 축이 스크래치 사본에 변이를 넣어 출력에 실리는 것을 봤고(서브에이전트가 손으로 봤다), 나머지 둘은 그 리뷰 뒤에 더해 아래 실행의 결과만 있다. 바꾸거나 더한 여섯과 같은 함수의 "링크 끊기가 링크를 끊지 않는다"를 번호(18, 39~44)로 골라 돌려 일곱 모두 고른 표지까지 기대대로 빨갰다. 마흔넷 모두 표지가 있고, 나머지 서른일곱은 원문 확인(`--check`)만 했다. PR #372의 claude-review 첫 회차를 반영한 뒤(같은 날, 커밋하지 않은 작업 트리, 기준 d5db123e) `cut_links`가 돌려주는 경로의 잇기를 겨누는 둘(링크 끊기가 끝 구분자를 뗀 뿌리에 그대로 이어 붙인다, 링크 끊기가 읽지 못한 뿌리에도 구분자를 붙인다)을 더했다. 앞의 것이 겨누는 새 시험(끝 구분자가 붙은 경로)은 고치기 전에 빨간 것을 봤다. 둘을 임시 표지로 한 번 돌려 실패 출력을 본 뒤 표지를 골랐고, 다시 돌려(43, 44) 둘 모두 고른 표지까지 기대대로 빨갰다. 같은 반영이 `_Git`의 예외 변환을 한 메서드로 모았지만 원문이 바뀐 변이는 없었다(`--check`). 마흔여섯 모두 표지가 있다. 그 반영분의 셀프 리뷰(같은 날, 기준 d5db123e)를 반영하며 `_Git._call`의 두 변환을 고정하는 새 시험(git 이 시간을 넘기거나 뜨지 못하면 `GateError`다)과 그것을 겨누는 둘(git 의 시간 넘김을 GateError 로 바꾸지 않는다, git 을 띄우지 못한 것을 GateError 로 바꾸지 않는다)을 더했다. 그 시험은 구현 뒤에 썼으니 빨강은 이 둘로 봤다. 둘을 임시 표지로 한 번 돌려 실패 출력(변환되지 않은 `TimeoutExpired`와 `OSError`가 그대로 오른다)을 본 뒤 표지를 골랐다. 같은 반영이 링크 끊기 시험 셋의 준비를 도우미로 모아, 그 시험을 쓰는 다섯(40~44)과 새 둘(47, 48)을 다시 돌려 모두 고른 표지까지 기대대로 빨갰다. 마흔여덟 모두 표지가 있다. 회고 반영(같은 날, 지우는 두 함수의 홈 가드)이 `cut_links`의 뿌리 링크 조건을 여러 줄로 바꿔 18(링크 끊기가 뿌리 링크를 따라간다)의 원문이 0번이 되었고, 그 반영분의 셀프 리뷰 뒤 `--check`가 알렸다. 홈 가드는 남기고 링크 조건만 빼는 원문으로 고쳐 다시 돌려 고른 표지까지 기대대로 빨갰다.

`rerun_cost_mutations.toml`(2026-10-23, 티켓 07의 셀프 리뷰 전, 커밋하지 않은 작업 트리에서 기준 c2c03eae). 공식 단가 시험은 구현 전에 모듈이 없어 수집 오류로만 빨갰고, 대신 셈 이름의 정규화만 시험을 먼저 고쳐 빨강을 봤다. `isclose`를 셋 단언하는 시험(나눈 캐시 쓰기)과 같은 id 의 응답 시험을 겨누는 변이는 변이가 낼 값을 표의 셈과 같은 식으로 미리 셈해(커밋하지 않은 한 줄 스크립트로 손으로 셈했다) 그 값의 머리(`isclose>(0.0024` 등)를 표지에 넣었다. 변이 23 모두 빨갰고, 처음 돌린 판에서 둘(응답이 있는 모델도 대신 셈한다, 대신 셈의 이름을 떼지 않는다)이 표지가 어긋났다. 둘 다 diff 의 방향을 거꾸로 짐작한 것이라 출력에 찍힌 `Left contains one more item:` 줄로 바꿨고, 그 둘을 다시 돌려 기대대로 빨갰다. 스물셋 모두 표지가 있다. 셀프 리뷰를 반영한 뒤(같은 날, 커밋하지 않은 작업 트리, 같은 기준) 원문이 바뀐 하나(synthetic 응답을 센다)를 맞추고 변이 23 전부를 돌려 모두 기대대로였다. 리뷰가 고친 모델이 없는 응답의 갈림을 겨누는 변이 하나(모델이 없는 응답을 빼고 센다)를 더했고, 그 변이도 고른 표지까지 기대대로 빨갰다. 스물넷 모두 표지가 있다. PR 직전 `bug-perf-review`를 반영한 뒤(같은 날, 커밋하지 않은 작업 트리, 기준 90f9f675) 원문이 바뀐 둘(대신 셈의 이름을 떼지 않고 적는다, 본 세션 기록 파일이 없으면 건너뛴다)을 맞추고, 둘(대신 셈에서 같은 모델을 더하지 않고 덮는다, 기록 줄을 splitlines 로 가른다)을 더했다. 더한 둘이 겨누는 시험은 고치기 전에 빨간 것을 봤다. 더한 둘과 맞춘 이름 변이의 표지는 실패 출력을 보기 전에 실패한 단언에서만 나오는 꼴로 달았다. 덮는 변이와 이름 변이의 표지는 반영분의 셀프 리뷰 표준 축이 스크래치 사본에 변이를 넣어 출력에 실리는 것을 봤고(서브에이전트가 손으로 봤다), splitlines 변이는 그 리뷰 뒤에 더했다. 변이 26 전부를 돌려 모두 고른 표지까지 기대대로 빨갰다(도구의 끝 줄 `변이 26 모두 기대대로`). 스물여섯 모두 표지가 있다. PR #372의 claude-review 첫 회차를 반영한 뒤(같은 날, 커밋하지 않은 작업 트리, 기준 d5db123e) 대신 셈을 `_substitutes`와 `_merged`로 뽑아 원문이 바뀐 셋(대신 셈의 이름을 떼지 않고 적는다, 대신 셈에서 같은 모델을 더하지 않고 덮는다, 회차 합의 것은 이름을 "회차 합에서 대신 셈한 같은 모델을 합치지 않는다"로 바꿨다)을 맞추고 표지는 그대로 두었다. 뽑으며 생긴 더하기를 겨누는 하나(세션 셈에 대신 셈한 단가를 더하지 않는다)를 더했다. 변이 27 전부를 돌려 스물여섯이 고른 표지까지 기대대로였고, 임시 표지로 단 더한 하나는 빨갰지만 표지가 없었다. 그 실패 출력의 `isclose` 값으로 표지를 고르고 다시 돌려 기대대로 빨갰다. 스물일곱 모두 표지가 있다. 그 반영분의 셀프 리뷰(같은 날, 기준 d5db123e)가 그 뽑기로 부동소수점 더하기의 차례가 바뀐 것(응답 셈의 합에 대신 셈의 합을 따로 더했다)을 짚어, 대신 셈의 금액을 같은 누산기에 차례로 더하게 `_substitute_usd`(금액), `_substitute`(항목), `Substitute`를 그대로 받는 `_merge_substitutes`로 다시 나눴다. 원문이 바뀐 여덟(modelUsage 의 이름을 떼지 않고 응답의 모델과 견준다, 기록에 응답이 없는 모델을 대신 셈하지 않는다, 기록에 응답이 있는 모델도 대신 셈한다, 대신 셈의 캐시 쓰기를 1시간 배수로 셈한다, 대신 셈의 이름을 떼지 않고 적는다, 대신 셈에서 같은 모델을 더하지 않고 덮는다, 세션 셈에 대신 셈한 단가를 더하지 않는다, 회차 합에서 대신 셈한 같은 모델을 합치지 않는다)을 맞췄다. 변이 27 전부를 돌려 스물여섯이 고른 표지까지 기대대로였고, "modelUsage 의 이름을 떼지 않고 응답의 모델과 견준다"는 빨갰지만 표지가 없었다. 대신 셈의 금액을 셀 때 이름을 따로 떼어 단가 오류가 나지 않고, 그 사용량을 응답이 없는 모델로 세어 대신 셈 항목이 하나 더 생긴다. 그 실패 출력의 `Left contains one more item` 줄로 표지를 바꾸고 다시 돌려(16) 기대대로 빨갰다. 스물일곱 모두 표지가 있다.

`rerun_session_mutations.toml`(2026-10-23, 티켓 08의 셀프 리뷰 전, 커밋하지 않은 작업 트리에서 기준 893e0fe8). 08이 `launch`가 호출 차례를 `RoundDir.append_session_id`에서 받게 하고 `drive`의 예외 갈래를 명령 줄을 본 뒤 끄게 고쳐, 두 변이(세션 id 를 띄운 뒤에 적는다, 예외가 나도 띄운 자식을 끄지 않는다)의 원문을 고친 코드에 맞췄다. 첫 줄의 연 저장소 변이는 첫 메시지를 짓는 자리가 `tools/rerun_continue.py`로 옮겨 가 continue 표로 옮겼다. 표 전체 27을 돌려 스물여섯은 표지까지 기대대로 빨갰고, "마감에 닿으면 끝난 자식도 끈 호출로 적는다" 하나는 노린 단언에서 빨갰지만 표지가 어긋났다. 08이 그 단언을 `killed`·`kill_skipped`까지 보게 넓혀 실패 머리가 `assert not True`에서 `assert (not True)`로 바뀐 것이라, 표지를 그 머리와 `).timed_out`으로 바꿔 그 변이만 다시 돌렸고 기대대로 빨갰다(스물일곱 모두 표지가 있다). 셀프 리뷰를 반영한 뒤(같은 날, 커밋하지 않은 작업 트리, 기준 893e0fe8) `Drove`의 불리언 칸이 `Stop` 하나가 되고 차례 세기가 `RoundDir.call_count`로 나뉘고 `drive`의 예외 갈래가 끝난 자식의 명령 줄을 읽지 않게 되어, 원문 둘(세션 id 를 띄운 뒤에 적는다, 예외가 나도 띄운 자식을 끄지 않는다)과 표지 하나(마감에 닿으면 끝난 자식도 끈 호출로 적는다)를 맞췄다. 표지는 고친 단언(`got.stop is Stop.EXITED`)의 꼴에서 `<Stop.DEADLINE_LEFT: 'deadline_left'> is <Stop.EXITED: 'exited'>`로 고른 뒤 돌려 봤다. `--since origin/main`이 고른 셋을 돌려 모두 고른 표지까지 기대대로 빨갰다(도구의 끝 줄 `변이 3 모두 기대대로`). PR 직전 리뷰를 반영해 커밋한 33785252(같은 날, 그 리뷰가 고친 것은 독스트링과 문서뿐이다)에서 표 전체를 돌려 기준선 모두 초록이고 변이 27 모두 고른 표지까지 기대대로 빨갰다(도구의 끝 줄 `변이 27 모두 기대대로`).

`rerun_continue_mutations.toml`(2026-10-23, 티켓 08의 셀프 리뷰 전, 커밋하지 않은 작업 트리에서 기준 893e0fe8). 표지를 없는 문구(`표지-미정`)로 둔 판을 먼저 돌려 변이 35 모두 빨간 것과 변이마다의 실패 출력을 보고, 고른 단언에서만 나오는 값 비교 문구로 표지를 골랐다. 그 출력에서 "인계에 새 세션 id 를 받지 않는다"는 노린 단언(둘째 호출의 `--session-id`)보다 앞의 끝 단언에서 빨갰다. 같은 id 로 다시 연 호출에서 가짜의 그 세션 각본이 바닥나 회차가 측정 아님으로 끝난 것이라(가짜의 `_pick`을 읽어 봤다), 시험에서 세션 id 단언을 앞으로 옮겼다. 표지를 단 판을 돌리니 서른둘이 표지까지 기대대로였고, 셋은 노린 단언에서 빨갰지만 표지가 어긋났다. 셋 다 pytest 가 긴 값을 줄여 찍어 `assert X == Y` 머리가 적은 모양으로 실리지 않은 것이다. 둘은 출력에 찍힌 줄(드릴다운 줄, diff 줄)로 바꿨다. "시간을 넘긴 호출을 상한으로 끊지 않는다"는 같은 시험의 다른 단언도 같은 드릴다운 줄을 낼 수 있어, 그 단언에 메시지를 붙여 표지로 썼다. 그 셋만 다시 돌려 모두 기대대로 빨갰다(서른다섯 모두 표지가 있다). 셀프 리뷰를 반영한 뒤(같은 날, 커밋하지 않은 작업 트리, 기준 893e0fe8) 원문이 어긋난 열셋을 고친 코드(`Stop`, `Opening`, `_ours`, 덩이 고르기)에 맞추고, 단언이 `Stop`을 보게 바뀐 거두는 기다림의 둘은 표지만 맞추고, 열(덩이 고르기 셋, 끄지 못한 호출 뒤 잇기, 멈춰 끈 호출을 시간으로 보기, 끄지 않은 멈춘 호출을 끈 것으로 적기, 러너가 끊김, 세션의 끈 표시 둘, 멈춰 남긴 호출의 호출 칸)을 더해 마흔다섯이 됐다. 바꾸거나 더한 변이의 표지는 고른 단언의 메시지나 값 비교의 꼴에서 고른 뒤 돌려 봤다. 첫 판처럼 표지를 없는 문구로 둔 판을 먼저 돌리지는 않았다. 바꾸거나 더한 스물다섯(4·6·7·8·14·16~19·22·24·25·29·30·32~42번)을 번호로 골라 돌려 모두 고른 표지까지 기대대로 빨갰다(도구의 끝 줄 `변이 25 모두 기대대로`). 그 실행 동안 이 PC 는 다른 세션들로 CPU 가 100%였고(`Get-Counter`로 두 번 잰 값, 손으로 봤다) 기준선 하나(`그_밖이면_resume`)가 151.66초였다. PR 직전 리뷰를 반영해 커밋한 33785252(같은 날, 그 리뷰가 고친 것은 독스트링과 문서뿐이다)에서 표 전체를 돌려 기준선 모두 초록이고 변이 45 모두 고른 표지까지 기대대로 빨갰다(도구의 끝 줄 `변이 45 모두 기대대로`). PR #374 claude-review 첫 회차의 Nit(훅의 명령 줄 읽기와 그 사본이 같은지 견주는 시험이 없다)을 받아 시험 `test_훅에서_옮긴_명령_줄_읽기가_훅의_것과_같다`와 변이 둘(46·47번, 사본의 함수가 갈린다, 사본의 API 원형이 훅에 없는 문장을 든다)을 더했다(같은 날, 커밋하지 않은 작업 트리, 기준 3c4623c8). 표지는 그 시험의 단언 메시지에서 고른 뒤 돌려 봤고, 없는 문구로 둔 판을 먼저 돌리지는 않았다. 그 둘을 이름으로 골라 돌려 기준선이 초록이고 둘 다 고른 표지까지 기대대로 빨갰다(도구의 끝 줄 `변이 2 모두 기대대로`). 티켓 09가 줄 판정(`watch`)과 `Stop.HALTED_*`를 더하고 08 메모대로 `run_sessions`에서 호출 하나(`_call`)와 다음 메시지(`_opening`)를 뽑아(같은 날, 티켓 09의 셀프 리뷰 전, 커밋하지 않은 작업 트리, 기준 07c890c5), 원문이 어긋난 아홉(`call_end`의 조건, `_opening`으로 옮긴 인계의 첫 메시지, `runner_killed`, `LEFT_RUNNING`을 쓰는 자리)을 고친 코드에 맞추고 줄 판정의 변이 넷(19·41·44·45번)을 더해 쉰하나가 됐다. 더한 넷의 표지는 고른 단언의 메시지와 값 비교의 꼴에서 고른 뒤 돌려 봤고, 없는 문구로 둔 판을 먼저 돌리지는 않았다. 바꾸거나 더한 열셋(16~19·25·26·38~41·43~45번)을 번호로 골라 돌려 기준선이 초록이고 모두 고른 표지까지 기대대로 빨갰다(도구의 끝 줄 `변이 13 모두 기대대로`). `--check`로 쉰하나 모두 원문이 한 번씩 있는 것도 봤다. 티켓 09의 셀프 리뷰 명세 축이 checks 표의 "끄기 자체는 continue 표의 줄 판정 변이가 본다"와 달리 `drive`의 `if watch(line):`를 없애는 변이가 없다고 짚어(2026-10-24, 커밋하지 않은 작업 트리, 같은 기준), 그 갈림을 고정하는 시험 `test_줄_판정이_참이면_마감_전에_그_줄에서_끈다`와 그것을 겨누는 "줄 판정이 참이어도 읽기를 멈추지 않는다"(46번)를 더해 쉰둘이 됐다. 그 시험은 구현 뒤에 썼으니 빨강은 이 변이로 봤다. 표지는 그 시험의 단언 메시지에서 고른 뒤 돌려 봤다. 그 변이를 번호로 골라 돌려 기준선이 초록이고 고른 표지까지 기대대로 빨갰다(도구의 끝 줄 `변이 1 모두 기대대로`, 30.88초).

`rerun_checks_mutations.toml`(2026-10-23, 티켓 09의 셀프 리뷰 전, 커밋하지 않은 작업 트리에서 기준 07c890c5). 표지를 없는 문구(`표지-고르기-전`)로 둔 판을 먼저 돌려 변이마다의 실패 출력을 봤다. 서른넷은 빨갰고 셋은 초록이었다. "서브에이전트의 synthetic 줄도 센다"는 시험의 서브에이전트 기록에 `<synthetic>` 줄이 없었고, "-- 뒤의 경로도 메시지 옵션으로 읽는다"는 `--` 뒤에 `-m`을 둔 사례가 없었고, "플러그인 접두가 붙은 Skill 이름을 알아보지 못한다"는 `:`가 든 Skill 이름 사례가 없었다. 셋 다 그 길을 밟는 사례를 시험에 더했다(서브에이전트 기록의 `<synthetic>` 다섯 줄, `git commit -- -m gh`, 새 시험 `test_Skill_이름은_앞의_슬래시와_콜론_앞을_떼고_견준다`). 서른넷의 표지는 그 출력에서 고른 단언에서만 나오는 값 비교 문구와 실패한 사례의 id 로 골랐고, 셋은 더한 사례의 꼴(값 비교의 꼴과 사례 id)에서 골랐다. 그 뒤 표 전체를 돌려 기준선 모두 초록이고 변이 37 모두 고른 표지까지 기대대로 빨갰다(도구의 끝 줄 `변이 37 모두 기대대로`). 그 실행에서 가짜 `claude`를 띄우는 기준선 하나(`env_키가`)가 58.33초였다. 첫 판에서는 0.49초였고 같은 시험을 고른 변이 4는 0.79초였다. 원인은 재지 않았다. 셀프 리뷰를 반영한 뒤(2026-10-24, 커밋하지 않은 작업 트리, 같은 기준) `--check`가 원문이 어긋났다고 알린 여덟(본 세션의 노력을 보지 않는다, 서브에이전트의 synthetic 줄도 센다, Agent 입력이 고른 모델을 허용하지 않는다, 커밋 메시지를 떼지 않고 gh 를 찾는다, 표준 입력으로 받는 커밋 메시지의 heredoc 본문을 떼지 않는다, 메시지 옵션 뒤 $(cat heredoc 본문을 떼지 않는다, ~/.claude 를 대신하는 이름을 보지 않는다, 한도를 설정보다 먼저 본다)을 고친 코드에 맞췄다. "설정 폴더의 env 키를 보지 않는다"는 시험이 매개변수 시험으로 바뀌어 `-k`와 표지를 맞췄다. 리뷰가 고친 갈림을 겨누는 아홉(설정 폴더의 잘못을 계정처럼 기록 없이 멈춘다, Agent 입력이 고른 모델을 회차의 모든 세션에 허용한다, 명령 앞의 셸 예약어를 지나지 않는다, 따옴표 없는 구분자의 $(cat heredoc 본문은 치환이 없어도 떼지 않는다, 홈 아래의 설정 폴더와 뿌리를 홈을 대신하는 이름으로 적은 꼴을 보지 않는 둘, 경로 뒤의 중괄호를 조각 경계로 보지 않는다, 쓰기 대상의 Git Bash 꼴을 클론 밖으로 본다, Monitor 의 웹소켓 입력을 보지 않는다)을 더해 마흔여섯이 됐다. 더한 아홉의 표지는 고른 단언의 값 비교 꼴과 사례 id 에서 고른 뒤 돌려 봤고, 없는 문구로 둔 판을 먼저 돌리지는 않았다. 표 전체를 돌려 기준선 모두 초록이고, 마흔셋은 고른 표지까지 기대대로 빨갰고 셋은 빨갰지만 표지가 어긋났다. 둘(자기 회차 폴더도 다른 회차로 센다, 자기 세션 기록 폴더도 설정 폴더로 센다)은 리뷰가 같은 매개변수 시험의 앞쪽에 경계 글자 사례 셋(중괄호 둘, 대괄호 하나)을 더해 사례 id 의 번호가 셋씩 밀린 것이라(`--collect-only`로 id 를 봤다) 같은 입력의 새 id 로 바꿨다. "Monitor 의 웹소켓 입력을 보지 않는다"는 pytest 가 긴 값을 줄여 찍어 고른 `assert` 줄이 실리지 않은 것이라, 출력에 찍힌 diff 줄(`Right contains 6 more items, first extra item: Hit(pattern='github-주소', tool='Monitor')`)로 바꿨다. 그 시험의 단언은 하나뿐이다. 셋을 번호로 골라 다시 돌려 모두 기대대로 빨갰다(도구의 끝 줄 `변이 3 모두 기대대로`). 마흔여섯 모두 표지가 있다.

`rerun_runner_mutations.toml`(2026-10-24, 티켓 10의 셀프 리뷰 전, 커밋하지 않은 작업 트리에서 기준 7496a830). 표지를 없는 문구(`표지-미정`)로 둔 판을 먼저 돌려 변이 22 모두 빨간지와 변이마다의 실패 출력을 봤다. 셋이 초록이었다. "동시에 셋까지 연다"는 자리 판정만 넓혀 일꾼 수(`ThreadPoolExecutor(MAX_PARALLEL)`)가 둘을 지켰고, 일꾼 수까지 넓히게 고쳤다. "풀리는 시각을 모르는 한도에서 멈추지 않는다"의 `halt = None or (`는 halt가 비었을 때 원문과 같은 동치 변이라 `halt and (`로 고쳤다. "인계 확인을 판과 견주지 않는다(돌던 동안)"는 다른 판의 확인을 쥐고 도는 시험이 없어 `test_다른_판의_확인을_쥐고_돌던_동안에도_첫_인계에서_멈춘다`를 더했다. 그 뒤 고른 단언에서만 나오는 값 비교 문구로 표지를 골라 전체를 다시 돌리니 스물하나가 표지까지 기대대로였다. 어긋난 하나(16번)는 변이 판에서 각본 없는 C 회차가 열려 다른 까닭으로 멈춰, 실패한 단언이 종료 코드가 아니라 안내 문구 단언이었다. 표지를 그 단언의 실패 문구로 바꿔 그 번호만 다시 돌려 기대대로 빨갰다. 셀프 리뷰를 반영하며(같은 날, 같은 기준) 판을 내린 러너의 id 갈래, 게이트를 돌지 못한 회차의 멈춤, 끄지 못한 호출 뒤의 멈춤을 겨누는 셋(23~25번)을 더해 스물다섯이 됐다. 그 셋의 시험은 구현 뒤에 썼으니 빨강은 이 변이로 봤다. 번호로 골라 돌려 기준선이 초록이고 셋 다 고른 표지까지 기대대로 빨갰다(도구의 끝 줄 `변이 3 모두 기대대로`). `where 0 = run()`·`where 1 = run()`을 표지로 쓴 변이(10·12·14·15·17·18·20·21번)는 그 시험의 종료 코드 단언에서만 나오는 문구라 고른 단언은 가리지만, 종료 코드가 어떤 까닭으로 바뀌었는지는 가리지 않는다.

티켓 11(2026-10-26, 옛 게이트 묶음, 커밋하지 않은 작업 트리에서 기준 d5ab0c15)이 더한 변이는 일곱이다. `rerun_files_mutations.toml`의 49, `rerun_gates_mutations.toml`의 49·50, `rerun_runner_mutations.toml`의 26~29다. 셋째 세션이 표지를 없는 문구로 둔 판을 먼저 돌려 여섯(러너 26~28까지)의 실패 출력을 본 뒤 표지를 골랐다. 넷째 세션의 셀프 리뷰가 코드를 고치며 원문이 어긋난 여섯(기록 29, 게이트 4·49, 러너 20·26·27. 기록 29는 셋째 세션이 원문과 시험 이름을 바꾸고 표를 맞추지 않은 것이다)을 맞추고 러너 29를 더해, 그 일곱을 번호로 돌려 모두 기대대로였다. 러너 27·29의 표지(`where 1 = run()`)는 러너가 멈췄다는 것만 가리킨다. 거부 문구는 러너의 출력 줄로 가고 pytest 출력에는 실리지 않는다.

티켓 11의 조건 판 2(2026-10-27, 커밋하지 않은 작업 트리에서 기준 1bd70d62)가 막는 규칙을 회차 폴더로 옮겨 `rerun_round_mutations.toml`의 settings.local 변이 둘(26·27)의 원문과 시험이 사라졌다. 셀프 리뷰 두 축이 잡아 새 자리의 변이로 바꿨고(26 "막는 규칙을 클론의 settings.local 에 쓴다", 27 "이미 있는 규칙 파일을 견주지 않는다"), 둘을 번호로 돌려 고른 표지까지 기대대로 빨갰다. 같은 판이 더한 `settings_env`가 B 해시 검사를 베껴 `rerun_gates_mutations.toml` 50의 원문이 두 번 있던 것은 그 검사를 `_blob_in_base`로 모아 풀었고, 게이트 변이 둘(51 "게이트가 B 설정의 env 를 얹지 않는다", 52 "B 설정의 env 에서 글이 아닌 값도 낸다")을 더했다. 50·52는 고른 표지로 빨갰고, 51은 빨갰지만 게이트보다 앞선 준비 명령에서 먼저 빨개져 표지(`assert 7 == 0`)가 어긋났다. 출력의 준비 실패 단언 줄로 표지를 바꿔 다시 돌렸고 기대대로였다. 두 표 모두 `--check`로 원문이 한 번씩 있는 것을 봤다.

티켓 11의 조건 판 4(2026-10-27~28, 커밋하지 않은 작업 트리에서 기준 47aa107b)는 변이 아홉을 더했다. `rerun_files_mutations.toml`의 50~52(판정 보기의 다른 세션 비용, 회차 기록의 판 1 읽기 둘), `rerun_cost_mutations.toml`의 28~30(모자란 칸 채우기), `rerun_runner_mutations.toml`의 31·32(같은 프로젝트 폴더의 다른 세션), `rerun_continue_mutations.toml`의 53(인계 지시문의 모델 줄)이다. 코드가 바뀌어 원문이 어긋난 기록 2와 이어 가기 26은 원문을 맞췄다. 기록 51은 처음 표지를 pytest 의 실패 줄로 두었다가 셀프 리뷰가 짚어 `회차 기록.spend: 빠진 키 ['other_usd']`로 바꿨다. 더한 아홉과 맞춘 둘을 2026-10-28에 번호로 다시 돌려 모두 기대대로였고, 여섯 표 모두 `--check`로 원문이 한 번씩 있는 것을 봤다.

티켓 11의 조건 판 3(2026-10-27, 커밋하지 않은 작업 트리에서 기준 175fb884)은 뿌리 규칙의 변이 셋을 더했다. `rerun_round_mutations.toml`의 58 "뿌리 규칙을 쓰지 않는다"와 59 "뿌리 규칙을 회차 폴더에도 맞는 꼴로 쓴다", `rerun_runner_mutations.toml`의 30 "러너가 뿌리를 막는 규칙에 넘기지 않는다"다. 셋 모두 빨갰고, 58은 처음 고른 표지(`assert [] == [...]`)가 pytest 의 줄인 출력에 없어 어긋나 실패 줄의 `Right contains 2 more items` 문구로 바꿔 다시 돌렸고 기대대로였다.

티켓 12(2026-10-29, 커밋하지 않은 작업 트리에서 기준 84542f52)는 본 측정 첫 회차 전에 `rerun_runner_mutations.toml`의 33~36을 더했다. 33 "다른 세션을 프로젝트 폴더 아래까지 훑는다", 34 "인계한 세션은 다른 세션에서 빼지 않는다", 35 "다른 프로젝트 폴더의 기록도 다른 세션으로 센다", 36 "예산 멈춤의 쓴 것에 다른 세션의 비용을 넣지 않는다"다. 셀프 리뷰가 짚어 같은 표의 37 "다른 세션에 .jsonl 이 아닌 파일도 센다"와 38 "회차 세션의 기록 파일이 없으면 모든 프로젝트 폴더를 훑는다", `rerun_cost_mutations.toml`의 31 "모자란 칸을 셀 때 modelUsage 의 이름 꼬리를 떼지 않는다"를 더했다(앞의 표에는 `_gaps`의 꼬리를 겨누는 변이가 없었다). 38 의 표지를 얻으려고 시험의 둘째 단언에 메시지를 달았다. 일곱 모두 빨갰고 표지(단언 메시지에 실은 정렬한 기록 이름, 멈춘 줄의 쓴 것 금액)가 출력에 있었다. 표지는 시험 원문에 글자 그대로 나오지 않는 꼴로 골랐고, `--check`로 두 표의 원문(러너 38, 비용 31)이 한 번씩 있는 것도 봤다.
