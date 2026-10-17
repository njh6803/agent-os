"""토큰 사용량 장부와 보고서(ADR 0033, `.scratch/token-usage/spec.md`의 "사용량 장부와 보고서
도구").

토큰과 비용을 재는 기본 길은 이 도구다. 세션 기록을 장부로 옮기고, 장부의 토큰에 단가표를 곱해
환산 비용을 낸다. 같은 세션 기록이 폴더 둘(주 폴더와 워크트리 폴더)에 겹치거나 포크한 세션에 앞
세션의 응답이 복사되어 있어도 응답 ID로 한 번만 센다. 글자 수에 근사 가중치를 곱해 토큰을
어림하지 않는다. 설계 인터뷰의 셈이 그렇게 틀렸다(대기열 273).

사용:
    uv run --no-project python tools/token_report.py daily [--projects 폴더] [--out 폴더]
        [--tz +09:00] [--today YYYY-MM-DD] [--repo 폴더 이름]
명령은 셋이다. `ingest`는 세션 기록을 읽어 장부를 갱신하고(`--full`은 `state.json`을 무시하고 남은
기록을 모두 다시 읽는다. 계정 기록은 건드리지 않는다), `report`는 장부에서 일간·주간·4주 보고서와
요약 파일을 만들고 보관 수를 넘은 일간·주간 보고서를 지우며, `daily`는 둘을 차례로 한다. 표준
라이브러리만 써서 저장소의 가상 환경 없이 돈다(작업 스케줄러가 그렇게 부른다).

인자의 기본값: 세션 기록 폴더는 `~/.claude/projects/`, 출력 폴더는 주 체크아웃(git 공용 디렉터리의
부모)의 `.scratch/token-report/`, 시간대는 이 PC의 지금 오프셋, 오늘은 그 시간대의 오늘, 이
저장소의 기록 폴더 이름(`--repo`, 9절이 쓴다)은 주 체크아웃의 경로에서 만든 것이다. 시간대는
`+09:00` 같은 고정 오프셋이다. 이 PC의 파이썬에는 IANA 시간대 자료가 없다.

한 파일에 둔다. 장부를 쌓는 쪽(`ingest`)과 보고서를 만드는 쪽(`report`)을 모듈 둘로 가르지 않는다.
명세와 작업 스케줄러 티켓(08)은 이 파일을 경로(`tools/token_report.py daily`)로 부른다. 스크립트로
불린 파일은 `tools/`가 경로의 머리에 서서 `from tools import …`가 풀리지 않는다. 가르려면 저장소
루트를 작업 폴더로 두고 `python -m tools.token_report`로 불러야 한다. 그러면 부르는 꼴이 명세와
08의 것과 달라지고, `tools`가 패키지 파일 없는 이름공간이라 가상 환경 없이 띄운 파이썬에 같은 이름의
패키지가 깔려 있으면 그쪽이 먼저 잡힌다. 그래서 가르지 않고, 파일 안을 차례가 고정된 구역(단가표,
장부의 행, 세션 기록 읽기, ingest, 계정, 보고서의 계획·읽기·날짜로 가르기·집계·경보·글·명령)으로
나누며, `report`는 그 구역의 함수를 차례로 부르기만 한다. 파일이 더 자라면 `-m`으로 바꿔 가르는 것을
다시 본다.

출력 폴더:
- `ledger/YYYY-MM.jsonl`: 그 달(지역 시간대)의 장부 행. 행은 셋이고 모두 형식 판 칸 `v`(지금 1)와
  종류 칸 `kind`를 든다. `call`은 모델 응답 하나(응답 ID, UTC 시각, 세션 ID, 서브에이전트 ID와
  유형, 기록 폴더, 브랜치, 모델, 노력, 토큰 다섯, 세션 컨텍스트, 같은 기록 파일의 직전 호출과의 초
  간격), `unreadable`은 읽지 못한 기록 줄 하나(그 앞 기록의 시각에 귀속한다)다. `session`은 메인
  세션 하나이고, 세션 ID와 첫 기록의 시각에 그 기록에서 셈한 칸 일곱을 더 든다. `handoff`(첫 사람
  입력이 `이어받을 상태: 인계:` 줄을 든 지시문인가), `human`(첫 사람 입력 기록의 `origin.kind`가
  `human`인가, 곧 헤드리스가 아니라 사람이나 앱이 연 세션인가), `start_parts`(첫 모델 호출 전 첨부의
  글자 수. 출처별 스킬 목록, 지연 도구 목록, 지침 파일, 그 밖), `large`(문턱을 넘은 도구 결과의
  도구·글자·대상·그 뒤 실려 간 호출 수), `reads`(Read 결과마다 경로·글자·다시 읽기 후보인지),
  `compactions`(압축 경계의 시각·자동인지·직전의 세션 컨텍스트), `prs`(그 세션이 연 PR의 시각과
  브랜치)다. 시각은 모두 UTC다. 일곱이 없는 옛 행은 보고서가 "모름"으로 센다(`ingest --full`로 다시
  쌓는다). 환산 비용은 적지 않는다. 단가표를 고치면 지난 보고서도 같은 셈으로 다시 만들어지게 하기
  위해서다. 칸을 더하는 것은 판을 올리지 않고, 있던 칸의 뜻이나 형을 바꾸면 판을 올리고 옛 판을 읽는
  길을 둔다. 읽는 쪽은 모르는 칸을 무시한다.
- `ledger/accounts.jsonl`: 세션 시작 훅이 덧붙이는 계정 기록(명세 "계정 기록의 줄"). 이 도구는
  읽기만 한다. 세션의 계정은 그 세션 ID의 줄 가운데 `account_uuid`가 `null`이 아닌 마지막 줄의
  이메일이고, 서브에이전트는 부모 세션의 계정이며, 줄이 없으면 "계정 모름"이다.
- `daily/YYYY-MM-DD.md`: `--today`의 전날까지 최근 7일의 일간 보고서.
- `weekly/YYYY-Www.md`: 월요일에서 일요일까지 ISO 주 하나. 끝난 주 가운데 최근 넷이다.
- `four-weeks/YYYY-Www-Www.md`: ISO 주 1~4, 5~8, …, 49~52의 묶음 하나. 53주가 있는 해는 마지막
  묶음(49~53)에 넣는다. 가장 최근에 끝난 묶음이다.
- `report`는 돌 때마다 위 보고서를 모두 다시 만든다. 그래서 빠진 날과 지운 폴더가 같은 바이트로
  다시 생긴다. 일간·주간은 그 이름 모양의 보통 파일 가운데 보고할 것보다 이른 것만 지우고(더 뒤의
  `--today`로 만든 것은 남는다), 4주 요약과 장부는 지우지 않는다. 링크와 폴더, 이름이 다른 파일은
  그대로 두고, 세 보고서 폴더 가운데 하나라도 링크면 아무것도 하지 않고 2로 끝난다.
- `summary.txt`: 최근 일간 보고서의 요약, 여덟 줄 이하. 첫 줄은 글자 그대로 `보고서 날짜:
  YYYY-MM-DD`이고 세션 시작 훅이 이 줄을 읽는다.
- `state.json`: 마지막 `ingest`의 시작 시각. `ingest.lock`: 명령이 도는 동안의 잠금 파일. 잠금이
  있으면 둘째 실행은 기다리지 않고 알린 뒤 3으로 끝난다.

증분과 멱등: `ingest`는 지난 실행의 한 시간 전보다 뒤에 바뀐 기록 파일만 다시 읽고, 그 기록 파일의
행을 새로 읽은 행으로 갈아 끼운다. 새로 읽은 사본에 없는 응답의 옛 행은 남긴다(긴 사본이 지워져
짧은 사본을 읽은 때). 겹친 사본은 가장 긴 것을 읽는다. 같은 응답 ID가 여러 세션에 있으면 먼저
시작한 세션의 행만 남긴다. 시작 시각을 모르는 세션(부모 기록이 없는 서브에이전트)이 직전 장부에서
그 응답을 가졌으면 그대로 갖는다. 다시 읽은 기록의 가장 이른 달의 전달부터 장부를 읽어 견준다.
다시 읽지 않은 행은 읽어 온 달 파일에 그대로 두고 새로 읽은 행만 지금 시간대로 달을 가르며,
`report`는 보고할 날의 앞뒤 하루까지 달 파일을 읽는다. 그래서 실행마다 시간대 인자가 달라도 행이
겹치거나 빠지지 않는다. 기록 파일이 지워져도 그 행은 남는다. 세션 기록 폴더가 없으면 장부와
`state.json`을 건드리지 않고 2로 끝난다(`state.json`을 올리면 그 앞의 기록을 건너뛴다). 달 파일과
보고서와 요약 파일은 임시 파일에 써서 `os.replace`로 바꿔 넣는다. 줄바꿈 없이 잘린 마지막 줄은
세션이 쓰는 도중이라 읽지도 경보에 세지도 않는다. 모델이 `<synthetic>`인 기록은 모델 호출이 아니라
들이지 않는다.

지표: 일간 보고서는 1~12절이다. 주간과 4주 요약은 같은 절을 그 기간 전체로 셈하고, 1절에 날마다의
경보를 모으며, 13절에 날짜별(주간)·주별(4주) 추이를 더한다. 1~6절은 02의 것이다.
- 7절: 메인 세션 컨텍스트가 40만을 넘은 세션의 수와 압축의 자동·수동 수, 자동 압축 직전의 세션
  컨텍스트(기록의 `preTokens`, 없으면 그 압축 경계 앞 마지막 모델 호출의 것)의 최소·중앙값·최대.
- 8절: 직전 호출과 60분 넘게 떨어진 메인 세션 호출 가운데 캐시 쓰기가 세션 컨텍스트의 절반
  이상인 것의 수와, 그 호출의 캐시 쓰기만의 환산 비용과 몫.
- 9절: 이 저장소(`--repo` 폴더와 그 워크트리 폴더)에서 사람이 연 세션(`human`) 가운데 그 기간에 첫
  메인 세션 호출이 있는 것의 그 호출의 세션 컨텍스트 중앙값과, 첫 호출 전 첨부의 구성별 글자 수
  중앙값. 헤드리스 세션은 그 수와 중앙값을 한 줄로 따로 적는다. 하루 수백 개의 시험 세션(카나리아,
  프로브)이 스킬 목록이 짧아 중앙값을 차지하면, 플러그인을 끈 효과와 지침이 늘어난 것을 보지 못하기
  때문이다. 장부가 응답 ID마다 주인 하나만 남겨 포크한 세션의 복사된 응답은 첫 호출이 되지 않는다.
  스킬 목록은 줄 머리(`- 플러그인:스킬`)로 출처를 가르고, 이어지는 줄은 앞 항목의 출처다. 지연 도구
  목록은 이름 줄, 지침 파일은 파일 본문, 그 밖은 나머지 첨부의 JSON 글자 수다.
- 10절: 브랜치(호출의 `gitBranch`)마다 비용 상위 열. 세션은 그 브랜치에 호출이 있는 세션이고 인계는
  그 가운데 인계로 열린 세션이다. PR 앞·뒤는 읽은 모든 세션 행에서 그 브랜치의 가장 이른 PR 시각으로
  그 브랜치 비용을 가른 몫이다. PR의 브랜치는 `gh pr create`의 `--head`(MCP는 `head`)이고, 없으면 그
  호출 기록의 `gitBranch`다. 주 체크아웃(main)에서 다른 브랜치의 PR을 연 것을 main으로 세지 않기
  위해서다.
- 11절: 메인 세션의 호출당 평균 세션 컨텍스트와 캐시 읽기의 몫(캐시 읽기 / 입력·캐시 읽기·캐시
  쓰기의 합).
- 12절: 큰 도구 결과는 범위(`offset`·`limit`) 없는 Read가 2만 자, Bash·PowerShell이 1만 자를 넘은
  결과다(`LARGE`, 큰 결과 알림 훅과 같은 문턱. 범위는 그 훅처럼 키가 있으면 준 것이다). 글자는
  기록의 `tool_result` 본문 글자 수다. 모델이 받은 글이라 Read는 줄 번호가 붙은 글이고, 글이 아닌
  결과(그림)는 0이다. 대상은 Read면 파일
  경로이고 Bash·PowerShell이면 프로그램 이름(`program_of`)뿐이다. 명령 속 비밀이 지우지 않는 장부에
  남지 않게 하기 위해서다. 상위 다섯은 무게(글자 × 그 뒤 실려 간 호출 수, 다음 압축 경계에서
  끊는다) 순이다. 셋 이상의 세션이 읽은 파일은 워크트리 접두를 벗긴 경로(`file_key_of`)로 묶는다.
  다시 읽기 후보는 같은 세션에서 같은 경로를 같은 범위로(또는 전체를 이미 읽고) 다시 읽은 Read다. 그
  사이에 그 파일을 Edit·Write·NotebookEdit·MultiEdit로 고쳤거나, 압축이 있었거나, 작업 트리를
  바꾸는 git 명령(`GIT_MUTATION`)이 돌았으면 세지 않는다. 낭비라는 판정이 아니다. 긴 세션
  컨텍스트에서 앞의 내용을 정확히 짚으려고 다시 읽는 것도 든다.
- 경보는 넷이다. 하루 비용이 지난 7일 가운데 호출이 있던 날의 일간 비용 중앙값의 1.5배를 넘는다.
  세션 컨텍스트가 40만을 넘은 메인 세션이 있다. 시작 컨텍스트 중앙값(9절의 것)이 지난 7일 가운데
  사람이 연 세션이 시작한 날의 일간 중앙값들의 중앙값보다 10% 넘게 크다. 단가표에 없는 모델의
  호출이나 읽지 못한 기록 줄이 있다. 비교하는 두 경보는 견줄 날이 넷보다 적으면 비교하지 않고
  그렇다고 적는다.

옮긴 코드: 호출 모으기(응답 ID마다 출력 토큰이 가장 큰 usage), 메인 세션·서브에이전트·모델·노력·
유형으로 가르기, 서브에이전트 유형 잇기는 `.scratch/harness/probes/token_usage/measure.py`의
`calls`·`split`·`agent_types`에서 옮겼다(티켓 02). 유형은 서브에이전트 기록 옆의
`agent-<ID>.meta.json`의 `agentType`을 먼저 보고, 없으면 부모 기록의 Agent 호출과 그 결과의
`agentId`로 잇는다. 같은 프로브의 `idle`(8절), `reads`·`rereads`(12절), `plugins`의 스킬 목록(9절),
`compactions`(7절)도 옮기며 고쳤다(티켓 03). 무게는 받은 목록을 비우고 받은 사전에 더하던 `_flush`
대신 실려 간 호출 수를 돌려주는 `carried_of`가, 압축은 경계 한 건을 값으로 만드는 `compaction_of`와
글을 만드는 `_context_lines`가 맡는다. 프로브는 하위 명령마다 파일을 고르고 겹침을 걸렀는데,
여기서는 `gather_copies`와 `longest`가 한 번 고른 사본을 `read_stream`이 한 번 읽어 호출 행과 세션
행을 함께 낸다. 프로브의 `REPO_PREFIX`는 `folder_name_of`와 `--repo`가 대신한다. 압축 지점
시뮬레이션(`_simulate`)은 보고서 지표가 아니라 옮기지 않았고, 그 프로브는 ADR 0033의 근거로 남는다.
옮기며 판정이 프로브와 달라진 것: `idle`은 명세의 글자대로 간격이 60분을 넘고(프로브는 60분 이상)
캐시 쓰기가 절반 이상이며(프로브는 절반 초과) 세션 컨텍스트 5만 초과 조건이 없고, 몫의 분모가 메인
세션 비용이 아니라 그 기간의 전체 비용이다. `rereads`는 실패한 Read를 읽기로 세지 않고, 노트북 편집
(`notebook_path`)을 고친 것으로 보며, 작업 트리를 바꾸는 git 명령을 더 본다(`GIT_MUTATION`).
`plugins`는 가장 큰 목록 하나가 아니라 세션마다의 구성을 중앙값으로 내고, 설명 없는
`- 플러그인:스킬` 줄과 이어지는 줄의 출처를 고쳤다. 무게는 세션 컨텍스트가 절반 아래로 준 자리가
아니라 압축 경계에서 끊고, 끊는 호출과 기록 끝의 다음 호출을 더 세지 않는다. 압축은 임시 폴더의 시험
세션을 따로 빼지 않는다.

못 보는 것:
- 세션 기록에 남지 않는 호출(웹 검색 요금, Claude Code 밖의 API 호출, 압축의 요약 요청)과
  청구액·한도의 남은 양. 압축의 요약 요청은 압축 경계 앞뒤 기록에 usage가 없었다(이 PC의 세션
  기록 여럿을 손으로 봤다, 일지 2026-10-17-04).
  시스템 지침과 도구 정의는 기록에 없어 시작 컨텍스트의 구성에 들지 않는다.
- 기록 파일이 첫 `ingest` 전에 지워졌으면 그 호출은 장부에 없다.
- 계정 기록이 없는 세션(세션 시작 훅을 들이기 전, 다른 프로젝트)은 계정을 가르지 못한다.
- 시작 시각을 모르는 세션끼리 응답 ID가 겹치면 어느 쪽이 먼저 시작했는지 모른다. 직전 장부의 주인이
  남고, 둘 다 처음 들면 세션 ID 순이다.
- 끊긴 실행이 남긴 잠금 파일은 사람이 지울 때까지 남아, 그동안 모든 실행이 3으로 끝나고 요약이
  낡는다.
- 서브에이전트의 도구 결과·읽기·압축은 세지 않는다. 세션 행은 메인 세션의 것이다.
- 포크한 세션에 복사된 도구 결과·읽기·압축은 도구 호출 ID와 압축 경계 ID로 한 번만 센다. 복사된
  기록의 시각이 원본과 다르면 그 세션의 시작 날짜가 갈릴 수 있다.
- PR은 Bash·PowerShell 명령의 조각(인용 밖의 `;`·`&`·`|`·줄바꿈으로 가른 것)마다 환경 대입을 벗긴
  첫 낱말 셋이 `gh pr create`이고(`--help`·`-h`·`--dry-run`이 없을 때) 오류 없이 끝난 것과, MCP의
  `create_pull_request`가 오류 없이 끝난 것이다. 따옴표 안의 글(훅 시험의 페이로드)은 세지 않는다.
  그 첫 낱말이 아닌 자리, 곧 명령 치환 안(`$(gh pr create …)`), 괄호·중괄호 묶음(`(gh pr create)`),
  `if …; then`·`!`·`time`·래퍼(`uv run`, `env`) 뒤, 별칭과 스크립트 안에서 연 PR은 놓친다. heredoc
  본문의 줄 머리에 적힌 `gh pr create`는 센다. `--body '-h'`처럼 값이 `-h`·`--help`·`--dry-run`인
  PR은 놓친다. 장부의 세션 행에 없는 PR(사람이 웹에서 연 것, 장부에 들기 전에 지워진 기록, 다른
  PC)의 브랜치는 "PR 시각 모름"이다. `--head` 없이 기본 브랜치에서 연 PR은 그 기본 브랜치로 센다.
  머리는 `--head 값`, `--head=값`, `-H 값`만 읽고 붙여 쓴 `-H값`은 놓친다. 붙여 쓴 꼴을 받으면 다른
  옵션의 값(`--title "-Hotfix: x"`)을 머리로 읽어 지우지 않는 장부에 틀린 브랜치를 남긴다.
- 사람이 연 세션인지는 기록의 `origin` 칸 하나로 가른다. 터미널의 대화형 `claude`가 그 칸에 무엇을
  남기는지는 보지 않았다(이 PC의 세션은 데스크톱 앱과 헤드리스뿐이었다).
- 다시 읽기 후보를 가르는 git 명령(`GIT_MUTATION`)은 흔한 것만 본다. `read-tree`, `git.exe`, 별칭,
  스크립트 안의 git, 공백이 든 인용 경로를 준 `-C`(`git -C 'a b' pull`), 값을 띄어 쓴 긴 앞
  옵션(`git --git-dir x pull`)으로 바뀐 파일과 git 밖의 Bash(sed, 스크립트)로 바뀐 파일은 보지 못해
  후보를 많게 센다. 반대로 커밋 메시지 안의 `git merge` 같은 글자도 걸려 그 뒤의 후보를 적게 센다.
- 프로그램 이름은 명령 앞의 대입만 벗긴다. 래퍼(`env`, `sudo`, `uv run`)는 벗기지 않아 그 이름이
  남는다.
- 셋 이상의 세션이 읽은 파일과 다시 읽기의 파일은 소문자로 바꾼 경로(`file_key_of`)로 적는다.
- 4주 요약은 가장 최근에 끝난 묶음 하나만 돌 때마다 다시 만든다. 작업이 한 묶음 넘게 돌지 않았으면
  그 사이의 묶음은 생기지 않는다.
"""

from __future__ import annotations

import argparse
import bisect
import io
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, timedelta, timezone
from itertools import dropwhile
from pathlib import Path

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None

FORMAT = 1
# 시작 시각을 모르는 행의 순위 칸. 시각끼리 견주는 자리에 None 대신 둔다.
_NO_TIME = datetime.min.replace(tzinfo=UTC)
KEEP_DAILY = 7
KEEP_WEEKLY = 4
ALARM_DAYS = 7
SPIKE = 1.5
START_SPIKE = 1.1
MIN_DAYS = 4
OVER_CONTEXT = 400_000
IDLE_S = 3600
# 큰 도구 결과의 문턱(글자). 큰 결과 알림 훅(`tools/hook_large_result.py`의 `READ_LIMIT`·
# `SHELL_LIMIT`)과 같은 값이고, 같은 크기의 결과로 두 쪽의 판정을 견주는 시험이 있다.
LARGE = {"Read": 20_000, "Bash": 10_000, "PowerShell": 10_000}
TOP = 5
TOP_BRANCHES = 10
MANY_SESSIONS = 3
UNKNOWN_ACCOUNT = "계정 모름"
OTHER_SKILLS = "(프로젝트·내장)"
DAILY, WEEKLY, FOUR_WEEKS = "daily", "weekly", "four-weeks"
LOCK = "ingest.lock"
DAILY_NAME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\.md")
WEEKLY_NAME = re.compile(r"[0-9]{4}-W[0-9]{2}\.md")
MONTH_NAME = re.compile(r"([0-9]{4}-[0-9]{2})\.jsonl")
HANDOFF = re.compile(r"^이어받을 상태: 인계:", re.MULTILINE)
# 작업 트리를 바꾸는 git 하위 명령 가운데 흔한 것(프로브에서 옮겨 `revert`·`clean`·`apply`·`rm`·
# `mv`와 `--no-pager` 같은 앞 옵션을 더했다). `merge-base`, `worktree list`, 커밋 메시지 속 맨
# 낱말(`merge`, `reset`)은 걸리지 않는다. 못 보는 것은 모듈 독스트링에 있다.
GIT_MUTATION = re.compile(
    r"(?<![\w-])git(?:\s+(?:-[cC]\s+\S+|--[\w-]+(?:=\S+)?))*\s+(?:pull|merge|checkout|switch"
    r"|rebase|reset|restore|stash(?!\s+(?:list|show)\b)|cherry-pick|am|revert|clean|apply|rm|mv"
    r"|worktree\s+(?:add|remove|move|prune))(?![\w-])"
)
NOT_RUN = frozenset({"--help", "-h", "--dry-run"})
EDITS = frozenset({"Edit", "Write", "NotebookEdit", "MultiEdit"})
SHELLS = frozenset({"Bash", "PowerShell"})
_SKILL_SOURCE = re.compile(r"- ([\w.-]+):[\w.-]+(?::|$)")
_ENV_ASSIGNMENT = re.compile(r"[A-Za-z_]\w*=")
_UNSAFE_ASSIGNMENT = re.compile(r"[$`\\()]")
_UNSAFE_PS = re.compile(r"@['\"{]|`")
_LINE_CONTINUATION = re.compile(r"[\\`]\r?\n")
_PROGRAM = re.compile(r"[\w./\\:+-]+")
_WORKTREE = re.compile(r"/\.claude/worktrees/[^/]+/")
GIT_TIMEOUT = 10


# 단가표


@dataclass(frozen=True)
class Price:
    input: float
    output: float
    cache_read: float


# 달러/백만 토큰. `.scratch/harness/probes/session_cost/costs.py`의 표를 2026-10-16에 옮겼다. 출처는
# 그 독스트링이다. 입력·출력은 claude-api 스킬(Claude Code 2.1.295 번들, 모델 표는 2026-10-06
# 캐시), 캐시 읽기는 같은 번들의 `shared/prompt-caching.md` 배수이고, 캐시 쓰기는 5분이 입력의
# 1.25배, 1시간이 2배다. `claude-sonnet-5-5`의 캐시 읽기는 공식 가격표(2026-10-13)의 0.05배가
# 아니라 Claude Code가 셈한 0.1배다(그 프로브의 README "2026-10-13 캐시 읽기 단가 대조").
# `claude-haiku-5-5`는 프롬프트 10만 토큰 이하의 단가다. 웹 검색 요금은 표에 없다.
PRICES: dict[str, Price] = {
    "claude-opus-5-5": Price(4.0, 20.0, 0.20),
    "claude-fable-5-1": Price(10.0, 50.0, 0.25),
    "claude-sonnet-5-5": Price(2.0, 10.0, 0.20),
    "claude-haiku-5-5": Price(0.10, 0.50, 0.01),
    "claude-opus-5": Price(5.0, 25.0, 0.50),
    "claude-opus-4-8": Price(5.0, 25.0, 0.50),
    "claude-opus-4-7": Price(5.0, 25.0, 0.50),
    "claude-sonnet-5": Price(2.0, 10.0, 0.20),
    "claude-haiku-4-5": Price(1.0, 5.0, 0.10),
}


def price_of(model: str) -> Price | None:
    """날짜가 붙은 이름(`claude-haiku-4-5-20251001`)은 날짜를 떼고 찾는다."""
    head, _, tail = model.rpartition("-")
    return PRICES.get(head if tail.isdigit() and len(tail) == 8 else model)


# JSON 읽기


def _obj(v: Json) -> dict[str, Json]:
    return v if isinstance(v, dict) else {}


def _list(v: Json) -> list[Json]:
    return v if isinstance(v, list) else []


def _str(v: Json) -> str | None:
    return v if isinstance(v, str) else None


def _int(v: Json) -> int:
    return v if isinstance(v, int) and not isinstance(v, bool) else 0


def _opt_int(v: Json) -> int | None:
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def _parse_json(text: str) -> Json:
    # `json.loads`의 반환형은 Any라, 여기서 `Json`으로 받아 뒤의 좁히기가 타입 검사를 지나게 한다.
    return json.loads(text)


def _time(v: Json) -> datetime | None:
    """UTC 시각. 읽지 못하거나 시간대가 없으면 None이다."""
    s = _str(v)
    if s is None:
        return None
    try:
        t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t.astimezone(UTC) if t.tzinfo is not None else None


def _iso(t: datetime) -> str:
    base = t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S")
    ms = t.microsecond // 1000
    return f"{base}.{ms:03d}Z" if ms else f"{base}Z"


def _iso_of(v: Json) -> str:
    """기록의 시각을 장부의 글로. 읽지 못하면 빈 글이고, 그 행은 어느 날에도 들지 않는다."""
    t = _time(v)
    return _iso(t) if t is not None else ""


def _text_len(content: Json) -> int:
    """도구 결과 본문의 글자 수. 글 블록만 세고 그림은 0이다."""
    if isinstance(content, str):
        return len(content)
    return sum(
        len(_str(b.get("text")) or "")
        for b in (_obj(x) for x in _list(content))
        if b.get("type") == "text"
    )


# 장부의 행


@dataclass(frozen=True)
class Call:
    id: str
    at: str
    session: str
    agent: str | None
    agent_type: str | None
    project: str
    branch: str | None
    model: str
    effort: str | None
    input: int
    cache_read: int
    cache_write_5m: int
    cache_write_1h: int
    output: int
    context: int
    gap_s: float | None

    def row(self) -> dict[str, Json]:
        return {
            "v": FORMAT,
            "kind": "call",
            "id": self.id,
            "at": self.at,
            "session": self.session,
            "agent": self.agent,
            "agent_type": self.agent_type,
            "project": self.project,
            "branch": self.branch,
            "model": self.model,
            "effort": self.effort,
            "input": self.input,
            "cache_read": self.cache_read,
            "cache_write_5m": self.cache_write_5m,
            "cache_write_1h": self.cache_write_1h,
            "output": self.output,
            "context": self.context,
            "gap_s": self.gap_s,
        }

    @staticmethod
    def of(r: dict[str, Json]) -> Call:
        gap = r.get("gap_s")
        return Call(
            id=_str(r.get("id")) or "",
            at=_str(r.get("at")) or "",
            session=_str(r.get("session")) or "",
            agent=_str(r.get("agent")),
            agent_type=_str(r.get("agent_type")),
            project=_str(r.get("project")) or "",
            branch=_str(r.get("branch")),
            model=_str(r.get("model")) or "",
            effort=_str(r.get("effort")),
            input=_int(r.get("input")),
            cache_read=_int(r.get("cache_read")),
            cache_write_5m=_int(r.get("cache_write_5m")),
            cache_write_1h=_int(r.get("cache_write_1h")),
            output=_int(r.get("output")),
            context=_int(r.get("context")),
            gap_s=float(gap)
            if isinstance(gap, int | float) and not isinstance(gap, bool)
            else None,
        )

    def cost(self) -> float | None:
        """달러. 단가표에 없는 모델이면 None이다."""
        p = price_of(self.model)
        if p is None:
            return None
        return (
            self.input * p.input
            + self.output * p.output
            + self.cache_read * p.cache_read
            + self.cache_write_5m * p.input * 1.25
            + self.cache_write_1h * p.input * 2.0
        ) / 1e6

    def write_cost(self) -> float | None:
        """캐시 쓰기 몫만의 달러. 단가표에 없는 모델이면 None이다."""
        p = price_of(self.model)
        if p is None:
            return None
        return (self.cache_write_5m * 1.25 + self.cache_write_1h * 2.0) * p.input / 1e6


@dataclass(frozen=True)
class Large:
    """문턱을 넘은 도구 결과 하나. 대상은 Read면 경로, 셸이면 프로그램 이름이고 남기지 않았으면
    None이다. `carried`는 그 결과가 들어온 뒤 다음 압축 경계나 기록 끝까지의 모델 호출 수다."""

    id: str
    at: str
    tool: str
    chars: int
    target: str | None
    carried: int

    def row(self) -> dict[str, Json]:
        return {
            "id": self.id,
            "at": self.at,
            "tool": self.tool,
            "chars": self.chars,
            "target": self.target,
            "carried": self.carried,
        }

    @staticmethod
    def of(r: dict[str, Json]) -> Large:
        return Large(
            _str(r.get("id")) or "",
            _str(r.get("at")) or "",
            _str(r.get("tool")) or "",
            _int(r.get("chars")),
            _str(r.get("target")),
            _int(r.get("carried")),
        )


@dataclass(frozen=True)
class FileRead:
    """Read 결과 하나. `again`은 다시 읽기 후보인지다."""

    id: str
    at: str
    path: str
    chars: int
    again: bool

    def row(self) -> dict[str, Json]:
        return {
            "id": self.id,
            "at": self.at,
            "path": self.path,
            "chars": self.chars,
            "again": self.again,
        }

    @staticmethod
    def of(r: dict[str, Json]) -> FileRead:
        return FileRead(
            _str(r.get("id")) or "",
            _str(r.get("at")) or "",
            _str(r.get("path")) or "",
            _int(r.get("chars")),
            r.get("again") is True,
        )


@dataclass(frozen=True)
class Compaction:
    """압축 경계 하나. `context`는 압축 직전의 세션 컨텍스트이고 모르면 None이다."""

    id: str
    at: str
    trigger: str
    context: int | None

    def row(self) -> dict[str, Json]:
        return {"id": self.id, "at": self.at, "trigger": self.trigger, "context": self.context}

    @staticmethod
    def of(r: dict[str, Json]) -> Compaction:
        return Compaction(
            _str(r.get("id")) or "",
            _str(r.get("at")) or "",
            _str(r.get("trigger")) or "",
            _opt_int(r.get("context")),
        )


@dataclass(frozen=True)
class PrOpen:
    at: str
    branch: str | None

    def row(self) -> dict[str, Json]:
        return {"at": self.at, "branch": self.branch}

    @staticmethod
    def of(r: dict[str, Json]) -> PrOpen:
        return PrOpen(_str(r.get("at")) or "", _str(r.get("branch")))


@dataclass(frozen=True)
class StartParts:
    """첫 모델 호출 전 첨부의 글자 수. 스킬 목록은 출처마다다."""

    skills: dict[str, int]
    deferred_tools: int
    instructions: int
    other: int

    def row(self) -> dict[str, Json]:
        skills: dict[str, Json] = {k: v for k, v in self.skills.items()}
        return {
            "skills": skills,
            "deferred_tools": self.deferred_tools,
            "instructions": self.instructions,
            "other": self.other,
        }

    @staticmethod
    def of(r: dict[str, Json]) -> StartParts:
        return StartParts(
            {k: _int(v) for k, v in _obj(r.get("skills")).items()},
            _int(r.get("deferred_tools")),
            _int(r.get("instructions")),
            _int(r.get("other")),
        )


@dataclass(frozen=True)
class SessionFacts:
    """세션 행이 02 뒤에 더한 칸 일곱."""

    handoff: bool
    human: bool
    start_parts: StartParts
    large: tuple[Large, ...]
    reads: tuple[FileRead, ...]
    compactions: tuple[Compaction, ...]
    prs: tuple[PrOpen, ...]

    def row(self) -> dict[str, Json]:
        return {
            "handoff": self.handoff,
            "human": self.human,
            "start_parts": self.start_parts.row(),
            "large": [x.row() for x in self.large],
            "reads": [x.row() for x in self.reads],
            "compactions": [x.row() for x in self.compactions],
            "prs": [x.row() for x in self.prs],
        }

    @staticmethod
    def of(r: dict[str, Json]) -> SessionFacts:
        def rows(key: str) -> list[dict[str, Json]]:
            return [_obj(x) for x in _list(r.get(key))]

        return SessionFacts(
            r.get("handoff") is True,
            r.get("human") is True,
            StartParts.of(_obj(r.get("start_parts"))),
            tuple(Large.of(x) for x in rows("large")),
            tuple(FileRead.of(x) for x in rows("reads")),
            tuple(Compaction.of(x) for x in rows("compactions")),
            tuple(PrOpen.of(x) for x in rows("prs")),
        )


@dataclass(frozen=True)
class SessionRow:
    """메인 세션 하나. `facts`가 None이면 칸 일곱이 없는 옛 행이다."""

    session: str
    start: str
    facts: SessionFacts | None = None

    def row(self) -> dict[str, Json]:
        out: dict[str, Json] = {
            "v": FORMAT,
            "kind": "session",
            "session": self.session,
            "start": self.start,
        }
        if self.facts is not None:
            out.update(self.facts.row())
        return out

    @staticmethod
    def of(r: dict[str, Json]) -> SessionRow:
        facts = SessionFacts.of(r) if "handoff" in r else None
        return SessionRow(_str(r.get("session")) or "", _str(r.get("start")) or "", facts)


@dataclass(frozen=True)
class Unreadable:
    session: str
    agent: str | None
    file: str
    line: int
    at: str

    def row(self) -> dict[str, Json]:
        return {
            "v": FORMAT,
            "kind": "unreadable",
            "session": self.session,
            "agent": self.agent,
            "file": self.file,
            "line": self.line,
            "at": self.at,
        }


@dataclass
class Ledger:
    calls: list[Call] = field(default_factory=list[Call])
    sessions: list[SessionRow] = field(default_factory=list[SessionRow])
    unreadable: list[Unreadable] = field(default_factory=list[Unreadable])

    def extend(self, other: Ledger) -> None:
        self.calls.extend(other.calls)
        self.sessions.extend(other.sessions)
        self.unreadable.extend(other.unreadable)

    def rows(self) -> list[Call | SessionRow | Unreadable]:
        return [*self.calls, *self.sessions, *self.unreadable]


type StreamKey = tuple[str, str | None]


def _stream_of(r: Call | SessionRow | Unreadable) -> StreamKey:
    return (r.session, None) if isinstance(r, SessionRow) else (r.session, r.agent)


def read_ledger_file(path: Path) -> Ledger:
    """달 파일 하나. 줄은 `\\n`으로만 가른다. `json.dumps(ensure_ascii=False)`는 U+2028 같은 줄 구분
    문자를 그대로 쓰는데(Read 경로에 들 수 있다) `splitlines()`는 거기서도 갈라 행이 깨진다."""
    out = Ledger()
    for line in path.read_text(encoding="utf-8").split("\n"):
        if not line.strip():
            continue
        r = _obj(_parse_json(line))
        kind = r.get("kind")
        if kind == "call":
            out.calls.append(Call.of(r))
        elif kind == "session":
            out.sessions.append(SessionRow.of(r))
        elif kind == "unreadable":
            out.unreadable.append(
                Unreadable(
                    _str(r.get("session")) or "",
                    _str(r.get("agent")),
                    _str(r.get("file")) or "",
                    _int(r.get("line")),
                    _str(r.get("at")) or "",
                )
            )
    return out


# 세션 기록 읽기


@dataclass(frozen=True)
class Copy:
    path: Path
    folder: str
    size: int
    mtime: float


def gather_copies(projects: Path) -> dict[StreamKey, list[Copy]]:
    """기록 파일을 (세션 ID, 서브에이전트 ID)마다 모은다. 겹친 사본은 같은 열쇠에 든다."""
    found: dict[StreamKey, list[Copy]] = defaultdict(list)
    if not projects.is_dir():
        return found
    for folder in sorted(projects.iterdir()):
        if not folder.is_dir():
            continue
        paths: list[tuple[StreamKey, Path]] = [((p.stem, None), p) for p in folder.glob("*.jsonl")]
        paths += [
            ((p.parent.parent.name, p.stem.removeprefix("agent-")), p)
            for p in folder.glob("*/subagents/agent-*.jsonl")
        ]
        for key, p in paths:
            try:
                st = p.stat()
            except FileNotFoundError:
                continue
            found[key].append(Copy(p, folder.name, st.st_size, st.st_mtime))
    return found


def longest(copies: list[Copy]) -> Copy:
    return max(copies, key=lambda c: (c.size, c.folder))


@dataclass(frozen=True)
class Record:
    line: int
    data: dict[str, Json]


def read_records(path: Path) -> tuple[list[Record], list[int]]:
    """줄마다 JSON 객체를 낸다. 읽지 못한 줄은 번호로 따로 낸다. 줄바꿈 없는 마지막 줄은 버린다."""
    parts = path.read_bytes().split(b"\n")
    parts.pop()
    records: list[Record] = []
    bad: list[int] = []
    for i, raw in enumerate(parts, 1):
        if not raw.strip():
            continue
        try:
            data = _parse_json(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            bad.append(i)
            continue
        if isinstance(data, dict):
            records.append(Record(i, data))
        else:
            bad.append(i)
    return records, bad


def _blocks(d: dict[str, Json]) -> list[dict[str, Json]]:
    return [b for b in _list(_obj(d.get("message")).get("content")) if isinstance(b, dict)]


def _usage_of(d: dict[str, Json]) -> dict[str, Json] | None:
    """모델 호출 기록(usage가 든 assistant 기록, `<synthetic>` 빼고)의 usage."""
    if d.get("type") != "assistant":
        return None
    m = _obj(d.get("message"))
    u = m.get("usage")
    if not isinstance(u, dict) or _str(m.get("model")) == "<synthetic>":
        return None
    return u


def _context_of(u: dict[str, Json]) -> int:
    return (
        _int(u.get("input_tokens"))
        + _int(u.get("cache_read_input_tokens"))
        + _int(u.get("cache_creation_input_tokens"))
    )


def agent_types_of(records: list[Record]) -> dict[str, str]:
    """부모 기록의 Agent 호출과 그 결과의 `agentId`로 잇는다. 유형을 생략한 호출은 결과의
    `agentType`을 괄호로 단다."""
    uses: dict[str, str | None] = {}
    out: dict[str, str] = {}
    for rec in records:
        d = rec.data
        if d.get("type") == "assistant":
            for b in _blocks(d):
                if b.get("type") == "tool_use" and b.get("name") == "Agent":
                    uses[_str(b.get("id")) or ""] = _str(_obj(b.get("input")).get("subagent_type"))
        result = _obj(d.get("toolUseResult"))
        agent_id = _str(result.get("agentId"))
        if d.get("type") != "user" or agent_id is None:
            continue
        for b in _blocks(d):
            tid = _str(b.get("tool_use_id"))
            if tid is not None and tid in uses:
                named = uses[tid]
                out[agent_id] = named or f"(생략→{_str(result.get('agentType')) or '?'})"
    return out


def read_meta_type(sub_path: Path) -> str | None:
    meta = sub_path.with_name(sub_path.stem + ".meta.json")
    try:
        data = _parse_json(meta.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return _str(_obj(data).get("agentType"))


@dataclass
class _Response:
    """응답 하나의 줄들. 첫 줄의 기록, 출력 토큰이 가장 큰 usage, 첫 줄 번호, 시각이 있는 첫 줄의
    시각."""

    first: dict[str, Json]
    usage: dict[str, Json]
    line: int
    at: datetime | None


def _cache_writes(u: dict[str, Json]) -> tuple[int, int]:
    """TTL 갈래가 없거나 합이 맞지 않으면 남는 쓰기를 5분으로 본다(싼 쪽)."""
    total = _int(u.get("cache_creation_input_tokens"))
    cc = _obj(u.get("cache_creation"))
    w5 = _int(cc.get("ephemeral_5m_input_tokens"))
    w1 = _int(cc.get("ephemeral_1h_input_tokens"))
    if w5 + w1 != total:
        w1 = min(w1, total)
        w5 = total - w1
    return w5, w1


def read_stream(key: StreamKey, copy: Copy, agent_type: str | None) -> Ledger:
    """기록 파일 하나를 장부 행으로 옮긴다. 메인 세션이면 세션 행의 칸도 같은 기록에서 셈한다."""
    session, agent = key
    records, bad = read_records(copy.path)
    out = Ledger()
    order: list[str] = []
    responses: dict[str, _Response] = {}
    stamps: list[tuple[int, datetime]] = []
    for rec in records:
        d = rec.data
        t = _time(d.get("timestamp"))
        if t is not None:
            stamps.append((rec.line, t))
        u = _usage_of(d)
        if u is None:
            continue
        m = _obj(d.get("message"))
        mid = _str(m.get("id")) or _str(d.get("uuid")) or f"{copy.path.name}:{rec.line}"
        seen = responses.get(mid)
        if seen is None:
            order.append(mid)
            responses[mid] = _Response(d, u, rec.line, t)
            continue
        if seen.at is None:
            seen.at = t
        if _int(u.get("output_tokens")) > _int(seen.usage.get("output_tokens")):
            seen.usage = u
    prev: datetime | None = None
    for mid in order:
        r = responses[mid]
        d, u, t = r.first, r.usage, r.at
        m = _obj(d.get("message"))
        if t is None:
            # 어느 줄에도 시각이 없는 응답은 날에 귀속하지 못해 읽지 못한 줄로 센다.
            bad.append(r.line)
            continue
        w5, w1 = _cache_writes(u)
        inp = _int(u.get("input_tokens"))
        read = _int(u.get("cache_read_input_tokens"))
        out.calls.append(
            Call(
                id=mid,
                at=_iso(t),
                session=session,
                agent=agent,
                agent_type=agent_type,
                project=copy.folder,
                branch=_str(d.get("gitBranch")),
                model=_str(m.get("model")) or "(모름)",
                effort=_str(d.get("effort")),
                input=inp,
                cache_read=read,
                cache_write_5m=w5,
                cache_write_1h=w1,
                output=_int(u.get("output_tokens")),
                context=inp + read + w5 + w1,
                gap_s=None if prev is None else round((t - prev).total_seconds(), 3),
            )
        )
        prev = t
    if agent is None and stamps:
        start = _iso(min(stamps, key=lambda s: s[0])[1])
        out.sessions.append(SessionRow(session, start, facts_of(records)))
    fallback = datetime.fromtimestamp(copy.mtime, UTC)
    lines = [n for n, _ in stamps]
    for line in sorted(set(bad)):
        i = bisect.bisect_left(lines, line)
        at = stamps[i - 1][1] if i else (stamps[i][1] if stamps else fallback)
        out.unreadable.append(Unreadable(session, agent, copy.path.name, line, _iso(at)))
    return out


# 세션 행의 칸


def facts_of(records: list[Record]) -> SessionFacts:
    """메인 세션 기록 하나에서 세션 행의 칸 일곱을 셈한다."""
    scan = _ToolScan()
    for rec in records:
        scan.add(rec)
    prompt = first_prompt_of(records)
    return SessionFacts(
        handoff=handoff_of(prompt),
        human=human_of(prompt),
        start_parts=start_parts_of(records),
        large=scan.large(),
        reads=tuple(scan.reads),
        compactions=tuple(scan.compactions),
        prs=tuple(scan.prs),
    )


@dataclass(frozen=True)
class Prompt:
    """첫 사람 입력의 기록과 글."""

    record: dict[str, Json]
    text: str


def first_prompt_of(records: list[Record]) -> Prompt | None:
    """첫 사람 입력. 도구 결과, `isMeta`, 압축 요약의 user 기록은 사람 입력이 아니다."""
    for rec in records:
        d = rec.data
        if d.get("type") != "user" or d.get("isMeta") is True or d.get("isCompactSummary") is True:
            continue
        content = _obj(d.get("message")).get("content")
        if isinstance(content, str):
            return Prompt(d, content)
        blocks = [_obj(b) for b in _list(content)]
        if any(b.get("type") == "tool_result" for b in blocks):
            continue
        texts = [_str(b.get("text")) or "" for b in blocks if b.get("type") == "text"]
        if texts:
            return Prompt(d, "\n".join(texts))
    return None


def handoff_of(prompt: Prompt | None) -> bool:
    """인계로 열린 세션인가. 첫 사람 입력이 `이어받을 상태: 인계:` 줄을 든 지시문이다."""
    return prompt is not None and HANDOFF.search(prompt.text) is not None


def human_of(prompt: Prompt | None) -> bool:
    """사람이 연 세션인가. 첫 사람 입력 기록의 `origin.kind`가 `human`이다. 2026-10-16 이 저장소의
    지난 48시간 메인 세션 기록에서 그 칸의 값과 `entrypoint`·`promptSource`, 첫 스킬 목록의 크기만
    커밋하지 않은 스크래치 스크립트로 셌다. 데스크톱 앱에서 사람이나 `open-session`이 연 세션은
    `human`이었고, 헤드리스 `claude -p`와 SDK 세션(카나리아, 프로브)은 `origin`이 없었다.
    `entrypoint`는 헤드리스 세션도 `claude-desktop`인 것이 많아(물려받는다) 가르지 못했다. 지난
    7일로 넓혀 판(`version`)과 함께 세니 `human`은 앱이 싣는 판(2.1.286, 2.1.295)에만 있었고, PATH의
    `claude -p`로 보이는 판(2.1.292, 2.1.296, 2.1.300)과 SDK(2.1.237)에는 없었다. 앱 판인데
    `origin`이 없던 둘은 첫 입력이 `<system-reminder>`로 시작하는 앱의 자동 세션이었다."""
    return prompt is not None and _obj(prompt.record.get("origin")).get("kind") == "human"


def skill_sources_of(listing: str) -> dict[str, int]:
    """스킬 목록 첨부의 출처별 글자 수(줄마다 줄바꿈 하나를 더한다). `- 플러그인:스킬` 줄은 그
    플러그인, 다른 `- ` 줄은 프로젝트·내장이고, `- `로 시작하지 않는 줄은 앞 항목의 출처다."""
    out: dict[str, int] = {}
    source = OTHER_SKILLS
    for line in listing.splitlines():
        if line.startswith("- "):
            m = _SKILL_SOURCE.match(line)
            source = m.group(1) if m else OTHER_SKILLS
        out[source] = out.get(source, 0) + len(line) + 1
    return out


def start_parts_of(records: list[Record]) -> StartParts:
    """첫 모델 호출 전 첨부의 글자 수. `prompt_snapshot`은 모델로 가지 않는 진단 기록이라 뺀다."""
    skills: dict[str, int] = {}
    deferred = instructions = other = 0
    for rec in records:
        if _usage_of(rec.data) is not None:
            break
        if rec.data.get("type") != "attachment":
            continue
        a = _obj(rec.data.get("attachment"))
        kind = a.get("type")
        if kind == "skill_listing":
            for source, n in skill_sources_of(_str(a.get("content")) or "").items():
                skills[source] = skills.get(source, 0) + n
        elif kind == "deferred_tools_delta":
            deferred += sum(len(_str(x) or "") + 1 for x in _list(a.get("addedLines")))
        elif kind == "instructions":
            files = (_obj(f) for f in _list(a.get("files")))
            instructions += sum(len(_str(f.get("content")) or "") for f in files)
        elif kind != "prompt_snapshot":
            other += len(json.dumps(a, ensure_ascii=False))
    return StartParts(skills, deferred, instructions, other)


def _raw_segments(command: str) -> list[list[str]]:
    """인용 밖의 `;`·`&`·`|`·줄바꿈으로 가른 조각마다 인용 밖 공백으로 가른 낱말. 인용 부호는 낱말에
    남긴다. 줄 이음(bash의 `\\`, PowerShell의 백틱 뒤 줄바꿈)은 공백으로 이어, 이어진 줄의
    옵션(`--head`, `--dry-run`)이 같은 조각에 든다. 인용 안의 줄 이음도 잇는데, 인용 안의 글은
    남기지 않으므로 상관없다."""
    segments: list[list[str]] = [[]]
    word: list[str] = []
    quote: str | None = None
    for char in _LINE_CONTINUATION.sub(" ", command):
        if quote is not None:
            word.append(char)
            if char == quote:
                quote = None
        elif char in "'\"":
            quote = char
            word.append(char)
        elif char in ";&|\n" or char.isspace():
            if word:
                segments[-1].append("".join(word))
            word = []
            if char in ";&|\n":
                segments.append([])
        else:
            word.append(char)
    if word:
        segments[-1].append("".join(word))
    return [s for s in segments if s]


def _unquote(word: str) -> str:
    """낱말의 인용 부호를 벗긴다. 인용 안의 다른 부호는 글자다."""
    out: list[str] = []
    quote: str | None = None
    for char in word:
        if quote is None and char in "'\"":
            quote = char
        elif char == quote:
            quote = None
        else:
            out.append(char)
    return "".join(out)


def _segments(command: str) -> list[list[str]]:
    """`_raw_segments`의 낱말에서 인용 부호를 벗긴 것."""
    return [[_unquote(w) for w in s] for s in _raw_segments(command)]


def _is_ps_assignment(words: list[str]) -> bool:
    """PowerShell의 변수 대입 조각(`$x = …`, `$env:K='…'`, `$n += 1`)."""
    head = words[0]
    return head.startswith("$") and ("=" in head or (len(words) > 1 and words[1].endswith("=")))


def program_of(command: str) -> str | None:
    """명령의 프로그램 이름. 명령 앞의 환경 대입(`이름=값`)과 PowerShell의 변수 대입 조각을 벗긴 첫
    낱말이다. 벗기는 선례는 `tools/hook_user_settings_read.py`의 `_strip_prefix`다. 이 장부는 지우지
    않으므로 남길 수 없으면 None으로 둔다. 벗긴 대입에 `$`·백틱·백슬래시·괄호가 있으면(따옴표 없는
    명령 치환 `X=$(echo 비밀) curl`, 이스케이프한 공백 `X=a\\ 비밀 curl`) 낱말 경계를 믿을 수 없어
    None이다. 건너뛰는 PowerShell 대입 조각에 here-string 머리(`@'`, `@"`), 해시테이블 머리(`@{`),
    백틱이 있어도 None이다. here-string 안의 따옴표는 인용을 열고 닫지 않아, 안에 따옴표가 홀수 개면
    그 뒤 줄(비밀이 홀로 든 줄)을 조각으로 잘못 가르고(PR 직전 보안 리뷰가 함수를 불러 봤다),
    여러 줄 해시테이블은 다음 줄의 키(`Authorization = …`)를 프로그램으로 읽는다. 남기는 낱말은 인용
    부호를 벗기기 전의 것이 단어 문자(`\\w`, 한글도 든다)와 `._-/\\:+`로만 되어야 한다. 따옴표에서
    온 글은 값일 수 있다(`'비밀' | gh auth login --with-token`)."""
    for words in _raw_segments(command):
        rest = list(dropwhile(_ENV_ASSIGNMENT.match, words))
        if any(_UNSAFE_ASSIGNMENT.search(w) for w in words[: len(words) - len(rest)]):
            return None
        if rest and _is_ps_assignment(rest) and _UNSAFE_PS.search(" ".join(rest)):
            return None
        if not rest or _is_ps_assignment(rest):
            continue
        return rest[0] if _PROGRAM.fullmatch(rest[0]) else None
    return None


def _branch_of_head(head: str) -> str | None:
    """PR 머리 값에서 브랜치. 따옴표와 포크의 `소유자:` 접두를 벗긴다."""
    return head.strip("'\"").rpartition(":")[2] or None


def pr_create_of(command: str) -> list[str] | None:
    """명령 위치의 `gh pr create` 조각의 낱말(명령 앞의 환경 대입을 벗겼다). 그런 조각이 없거나
    `--help`·`-h`·`--dry-run`이 있어 PR을 만들지 않는 조각이면 None이다. 따옴표 안의 글은 낱말
    하나라 걸리지 않는다."""
    for words in _segments(command):
        rest = list(dropwhile(_ENV_ASSIGNMENT.match, words))
        if rest[:3] == ["gh", "pr", "create"]:
            return None if NOT_RUN & set(rest) else rest
    return None


def pr_head_of(words: list[str]) -> str | None:
    """`gh pr create` 낱말의 `--head`·`-H` 값. 없으면 None이고, 그때 PR의 브랜치는 기록의
    `gitBranch`다."""
    for i, word in enumerate(words):
        if word.startswith("--head="):
            return _branch_of_head(word.removeprefix("--head="))
        if word in ("--head", "-H") and i + 1 < len(words):
            return _branch_of_head(words[i + 1])
    return None


def _path_key(inp: dict[str, Json]) -> str:
    """한 세션 안에서 같은 파일인지 가르는 열쇠. 윈도 경로라 대소문자를 가리지 않는다.
    `NotebookEdit`는 경로를 `notebook_path`로 받는다."""
    path = _str(inp.get("file_path")) or _str(inp.get("notebook_path")) or ""
    return path.replace("\\", "/").lower()


def file_key_of(path: str) -> str:
    """세션을 건너 같은 파일인지 가르는 열쇠. 워크트리 접두(`/.claude/worktrees/<이름>/`)를
    벗긴다."""
    return _WORKTREE.sub("/", path.replace("\\", "/").lower(), count=1)


def _range_of(inp: dict[str, Json]) -> tuple[int | None, int | None]:
    return _opt_int(inp.get("offset")), _opt_int(inp.get("limit"))


def _ranged(inp: dict[str, Json]) -> bool:
    """Read에 범위를 줬는가. 큰 결과 알림 훅과 같이 `offset`·`limit` 키가 있으면 값이 정수가
    아니어도 준 것으로 본다."""
    return "offset" in inp or "limit" in inp


def carried_of(
    entered: Sequence[tuple[int, int]], cuts: Sequence[tuple[int, int]], end: int
) -> list[int]:
    """들어온 자리(기록의 줄, 그때까지의 모델 호출 수)마다 그 뒤 실려 간 호출 수. 들어온 뒤 처음
    오는 압축 경계(줄, 그때까지의 호출 수)에서 끊고, 없으면 기록 끝(`end`, 모든 호출 수)까지다."""
    lines = [line for line, _ in cuts]
    out: list[int] = []
    for line, calls in entered:
        i = bisect.bisect_right(lines, line)
        stop = cuts[i][1] if i < len(cuts) else end
        out.append(stop - calls)
    return out


def compaction_of(d: dict[str, Json], last_context: int | None) -> Compaction:
    """압축 경계 기록 하나. 압축 직전의 세션 컨텍스트는 기록의 `preTokens`(Claude Code가 압축할 때
    센 값)이고, 없으면 그 앞 마지막 모델 호출의 것이다. `preTokens`는 마지막 호출 뒤에 든 도구
    결과까지 들어 자동 압축 창과 견줄 값이다. 2026-10-16 셀프 리뷰의 명세 축이 이 PC의 모든
    프로젝트에서 자동 압축 19건을 스크래치 스크립트로 견주니, 둘의 차이는 중앙값 4,374이고 가장 큰
    것은 393,461이었다(이 저장소 밖의 폴더). PR 직전 리뷰가 이 저장소 폴더의 20건만 보니
    `preTokens`가 언제나 컸고 차이의 중앙값은 4,491, 가장 큰 것은 47,045였다."""
    meta = _obj(d.get("compactMetadata"))
    pre = _opt_int(meta.get("preTokens"))
    context = pre if pre is not None else last_context
    return Compaction(
        _str(d.get("uuid")) or "",
        _iso_of(d.get("timestamp")),
        _str(meta.get("trigger")) or "(모름)",
        context,
    )


@dataclass(frozen=True)
class _Use:
    """결과를 기다리는 도구 호출 하나."""

    name: str
    input: dict[str, Json]
    branch: str | None
    again: bool


class _ToolScan:
    """메인 세션 기록 하나를 차례대로 훑어 도구 결과, 읽기, 압축 경계, 연 PR을 모은다. 다시 읽기
    후보의 판정은 `cmd_rereads`(프로브)의 것이다."""

    def __init__(self) -> None:
        self.calls = 0
        self.last_context: int | None = None
        self.ids: set[str] = set()
        self.uses: dict[str, _Use] = {}
        self.seen: dict[str, set[tuple[int | None, int | None]]] = {}
        self.cuts: list[tuple[int, int]] = []
        self.pending: list[tuple[int, int, Large]] = []
        self.reads: list[FileRead] = []
        self.compactions: list[Compaction] = []
        self.prs: list[PrOpen] = []

    def add(self, rec: Record) -> None:
        d = rec.data
        if d.get("type") == "system" and d.get("subtype") == "compact_boundary":
            self.seen.clear()
            self.cuts.append((rec.line, self.calls))
            self.compactions.append(compaction_of(d, self.last_context))
            return
        u = _usage_of(d)
        if u is not None:
            m = _obj(d.get("message"))
            mid = _str(m.get("id")) or _str(d.get("uuid")) or str(rec.line)
            if mid not in self.ids:
                self.ids.add(mid)
                self.calls += 1
            self.last_context = _context_of(u)
        for b in _blocks(d):
            if d.get("type") == "assistant" and b.get("type") == "tool_use":
                self._use(b, _str(d.get("gitBranch")))
            elif d.get("type") == "user" and b.get("type") == "tool_result":
                self._result(rec, b)

    def _use(self, b: dict[str, Json], branch: str | None) -> None:
        tid = _str(b.get("id"))
        name = _str(b.get("name")) or ""
        inp = _obj(b.get("input"))
        if tid is None:
            return
        key = _path_key(inp)
        if name in EDITS:
            self.seen.pop(key, None)
        elif name in SHELLS and GIT_MUTATION.search(_str(inp.get("command")) or ""):
            self.seen.clear()
        ranges = self.seen.get(key, set())
        again = name == "Read" and (_range_of(inp) in ranges or (None, None) in ranges)
        self.uses[tid] = _Use(name, inp, branch, again)

    def _result(self, rec: Record, b: dict[str, Json]) -> None:
        tid = _str(b.get("tool_use_id")) or ""
        use = self.uses.pop(tid, None)
        if use is None:
            return
        at = _iso_of(rec.data.get("timestamp"))
        chars = _text_len(b.get("content"))
        ok = b.get("is_error") is not True
        command = _str(use.input.get("command")) or ""
        if use.name == "Read" and not ok:
            # 실패한 읽기(파일이 없다, 너무 크다)는 파일을 싣지 않았다. 기억하면 뒤이은 범위 읽기를
            # 다시 읽기 후보로 잘못 센다.
            return
        if use.name == "Read":
            path = (_str(use.input.get("file_path")) or "").replace("\\", "/")
            self.reads.append(FileRead(tid, at, path, chars, use.again))
            self.seen.setdefault(_path_key(use.input), set()).add(_range_of(use.input))
            if not _ranged(use.input) and chars > LARGE["Read"]:
                self.pending.append((rec.line, self.calls, Large(tid, at, "Read", chars, path, 0)))
        elif use.name in SHELLS:
            if chars > LARGE[use.name]:
                large = Large(tid, at, use.name, chars, program_of(command), 0)
                self.pending.append((rec.line, self.calls, large))
            words = pr_create_of(command)
            if ok and words is not None:
                self.prs.append(PrOpen(at, pr_head_of(words) or use.branch))
        elif ok and use.name.endswith("create_pull_request"):
            head = _str(use.input.get("head"))
            self.prs.append(PrOpen(at, _branch_of_head(head) if head else use.branch))

    def large(self) -> tuple[Large, ...]:
        carried = carried_of([(line, n) for line, n, _ in self.pending], self.cuts, self.calls)
        return tuple(
            replace(x, carried=c) for (_, _, x), c in zip(self.pending, carried, strict=True)
        )


# 시간대와 달


def tz_of(text: str) -> timezone:
    m = re.fullmatch(r"([+-])(\d{2}):(\d{2})", text)
    if m is None:
        raise argparse.ArgumentTypeError(f"시간대는 +09:00 같은 고정 오프셋이다: {text}")
    delta = timedelta(hours=int(m.group(2)), minutes=int(m.group(3)))
    return timezone(-delta if m.group(1) == "-" else delta)


def local_date(at: str, tz: timezone) -> date:
    t = _time(at)
    return t.astimezone(tz).date() if t is not None else date.min


def month_of(at: str, tz: timezone) -> str:
    return local_date(at, tz).strftime("%Y-%m")


def _row_time(r: Call | SessionRow | Unreadable) -> str:
    return r.start if isinstance(r, SessionRow) else r.at


def _prev_month(month: str) -> str:
    y, m = (int(x) for x in month.split("-"))
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02}"


def _dates(first: date, last: date) -> list[date]:
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]


def _month_names(first: date, last: date) -> list[str]:
    out: list[str] = []
    y, m = first.year, first.month
    while (y, m) <= (last.year, last.month):
        out.append(f"{y}-{m:02}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


# 파일 쓰기


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def is_link(p: Path) -> bool:
    return p.is_symlink() or p.is_junction()


class LockedError(Exception):
    pass


class Lock:
    """출력 폴더의 잠금 파일. 이미 있으면 기다리지 않고 `LockedError`를 낸다."""

    def __init__(self, out: Path) -> None:
        self.path = out / LOCK

    def __enter__(self) -> Lock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as e:
            raise LockedError(str(self.path)) from e
        os.close(fd)
        return self

    def __exit__(self, *_: object) -> None:
        self.path.unlink(missing_ok=True)


# ingest


def _owner_rank(
    c: Call, starts: dict[str, str], held: dict[str, StreamKey]
) -> tuple[int, datetime, str, str]:
    """같은 응답 ID의 행 가운데 남길 것의 순위(작을수록 앞). 시작 모를 세션이 직전 장부에서 그
    응답을 가졌으면 그대로 갖고, 시작을 아는 세션끼리는 이른 쪽이 이기며, 나머지 시작 모를 세션은
    진다."""
    start = _time(starts.get(c.session))
    if start is not None:
        return (1, start, c.session, c.agent or "")
    rank = 0 if held.get(c.id) == _stream_of(c) else 2
    return (rank, _NO_TIME, c.session, c.agent or "")


def _sorted_rows(rows: Iterable[Call | SessionRow | Unreadable]) -> list[dict[str, Json]]:
    def key(r: Call | SessionRow | Unreadable) -> tuple[str, str, str, str, str]:
        if isinstance(r, SessionRow):
            return ("0", r.start, r.session, "", "")
        if isinstance(r, Call):
            return ("1", r.at, r.session, r.agent or "", r.id)
        return ("2", r.at, r.session, r.agent or "", f"{r.line:09d}")

    return [r.row() for r in sorted(rows, key=key)]


type Row = Call | SessionRow | Unreadable
type Placed = tuple[str, Row]


def read_changed_since(out: Path) -> float | None:
    """지난 `ingest`의 한 시간 전(유닉스 시각). `state.json`이 없거나 읽지 못하면 None이다."""
    state_path = out / "state.json"
    if not state_path.is_file():
        return None
    last = _time(_obj(_parse_json(state_path.read_text(encoding="utf-8"))).get("last_ingest"))
    return None if last is None else last.timestamp() - 3600


def _read_agent_type(
    key: StreamKey,
    copy: Copy,
    streams: dict[StreamKey, list[Copy]],
    parents: dict[str, dict[str, str]],
) -> str | None:
    """서브에이전트 유형. `meta.json`을 먼저 보고, 없으면 부모 기록의 Agent 호출로 잇는다."""
    session, agent = key
    if agent is None:
        return None
    found = read_meta_type(copy.path)
    if found is not None or (session, None) not in streams:
        return found
    if session not in parents:
        parents[session] = agent_types_of(read_records(longest(streams[(session, None)]).path)[0])
    return parents[session].get(agent)


def _read_changed(
    streams: dict[StreamKey, list[Copy]], changed: list[StreamKey]
) -> tuple[Ledger, set[StreamKey]]:
    """바뀐 기록을 읽는다. 훑은 뒤 지워진 기록은 건너뛰어 그 기록의 옛 행이 남는다."""
    parents: dict[str, dict[str, str]] = {}
    fresh = Ledger()
    keys: set[StreamKey] = set()
    for key in changed:
        copy = longest(streams[key])
        try:
            rows = read_stream(key, copy, _read_agent_type(key, copy, streams, parents))
        except FileNotFoundError:
            continue
        fresh.extend(rows)
        keys.add(key)
    return fresh, keys


def _placed_of(
    old_months: dict[str, Ledger], fresh: Ledger, fresh_keys: set[StreamKey], tz: timezone
) -> tuple[list[Placed], dict[str, StreamKey]]:
    """달 파일에 둘 행과 직전 장부의 응답 주인. 다시 읽은 기록의 옛 행은 새 행으로 갈아 끼우되,
    새로 읽은 사본에 없는 응답(긴 사본이 지워져 짧은 사본을 읽었을 때)의 옛 행은 남긴다. 다시 읽지
    않은 행은 읽어 온 달 파일에 그대로 둔다. 시간대 인자가 바뀌어도 읽지 않은 달 파일로 옮겨 그
    파일을 덮지 않게 하기 위해서다. 새로 읽은 행만 지금 시간대로 달을 가른다."""
    fresh_ids = {(_stream_of(c), c.id) for c in fresh.calls}
    placed: list[Placed] = []
    held: dict[str, StreamKey] = {}
    for month, old in old_months.items():
        held.update((c.id, _stream_of(c)) for c in old.calls)
        placed += [(month, c) for c in old.calls if (_stream_of(c), c.id) not in fresh_ids]
        placed += [(month, s) for s in old.sessions if _stream_of(s) not in fresh_keys]
        placed += [(month, u) for u in old.unreadable if _stream_of(u) not in fresh_keys]
    placed += [(month_of(_row_time(r), tz), r) for r in fresh.rows()]
    return placed, held


def read_months(ledger_dir: Path) -> list[str]:
    """장부 폴더에 있는 달 파일의 달(`YYYY-MM`), 이른 것부터. 폴더가 없으면 빈 목록이다."""
    names = os.listdir(ledger_dir) if ledger_dir.is_dir() else []
    return sorted(m.group(1) for name in names if (m := MONTH_NAME.fullmatch(name)))


def owned_rows_of(placed: list[Placed], held: dict[str, StreamKey]) -> list[Placed]:
    """응답 ID마다 한 행만 남긴다(`_owner_rank`). 호출 행이 아닌 행은 그대로 둔다."""
    starts = {r.session: r.start for _, r in placed if isinstance(r, SessionRow)}
    owner: dict[str, tuple[str, Call]] = {}
    for month, r in placed:
        if not isinstance(r, Call):
            continue
        prev = owner.get(r.id)
        if prev is None or _owner_rank(r, starts, held) < _owner_rank(prev[1], starts, held):
            owner[r.id] = (month, r)
    return [*owner.values(), *((m, r) for m, r in placed if not isinstance(r, Call))]


def ingest(projects: Path, out: Path, tz: timezone, since: float | None) -> None:
    """`since`(유닉스 시각)보다 뒤에 바뀐 기록을 다시 읽어 장부를 갱신한다. None이면 남은 기록을
    모두 다시 읽고 모든 달 파일과 견준다."""
    if not projects.is_dir():
        # state를 올리면 다음 실행이 그 앞의 기록을 건너뛴다.
        raise ToolError(f"세션 기록 폴더가 없다: {projects}. 장부와 state.json을 그대로 둔다")
    started = time.time()
    ledger_dir = out / "ledger"
    streams = gather_copies(projects)
    changed = [
        k
        for k, copies in sorted(streams.items(), key=lambda kv: (kv[0][0], kv[0][1] or ""))
        if since is None or any(c.mtime > since for c in copies)
    ]
    fresh, fresh_keys = _read_changed(streams, changed)
    existing = read_months(ledger_dir)
    fresh_rows = fresh.rows()
    load: list[str] = []
    if fresh_rows:
        first = min(month_of(_row_time(r), tz) for r in fresh_rows)
        load = existing if since is None else [m for m in existing if m >= _prev_month(first)]
    old_months = {m: read_ledger_file(ledger_dir / f"{m}.jsonl") for m in load}
    placed, held = _placed_of(old_months, fresh, fresh_keys, tz)
    by_month: dict[str, list[Row]] = {m: [] for m in load}
    for month, r in owned_rows_of(placed, held):
        by_month.setdefault(month, []).append(r)
    for month, rows in sorted(by_month.items()):
        body = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in _sorted_rows(rows))
        write_atomic(ledger_dir / f"{month}.jsonl", body)
    state: dict[str, Json] = {
        "v": FORMAT,
        "last_ingest": _iso(datetime.fromtimestamp(started, UTC)),
    }
    write_atomic(out / "state.json", json.dumps(state) + "\n")
    print(f"기록 파일 {len(changed)}개를 다시 읽고 달 파일 {len(by_month)}개를 썼다: {ledger_dir}")


# 계정


def read_accounts(path: Path) -> dict[str, str]:
    """세션 ID -> 계정 이름(이메일, 없으면 계정 ID). `account_uuid`가 null인 줄은 앞을 덮지
    않는다."""
    accounts: dict[str, str] = {}
    if not path.is_file():
        return accounts
    for line in path.read_text(encoding="utf-8").split("\n"):
        try:
            r = _obj(_parse_json(line))
        except json.JSONDecodeError:
            continue
        sid = _str(r.get("session_id"))
        uuid = _str(r.get("account_uuid"))
        if sid is not None and uuid is not None:
            accounts[sid] = _str(r.get("email")) or uuid
    return accounts


# 보고서: 계획


def week_name_of(monday: date) -> str:
    year, week, _ = monday.isocalendar()
    return f"{year}-W{week:02}"


def weeks_in(year: int) -> int:
    """ISO 해의 주 수(52나 53). 12월 28일은 언제나 그 해의 마지막 주에 든다."""
    return date(year, 12, 28).isocalendar().week


@dataclass(frozen=True)
class Group:
    """ISO 해 하나의 4주 묶음(첫 주에서 끝 주까지)."""

    year: int
    first: int
    last: int

    def name(self) -> str:
        return f"{self.year}-W{self.first:02}-W{self.last:02}"

    def mondays(self) -> list[date]:
        return [date.fromisocalendar(self.year, w, 1) for w in range(self.first, self.last + 1)]

    def dates(self) -> list[date]:
        return _dates(self.mondays()[0], date.fromisocalendar(self.year, self.last, 7))


def group_of(year: int, week: int) -> Group:
    """그 주가 든 4주 묶음. 53주는 마지막 묶음(49~53)에 든다."""
    g = min((week - 1) // 4, 12)
    return Group(year, 4 * g + 1, 4 * g + 4 if g < 12 else weeks_in(year))


def finished_group(last: date) -> Group:
    """`last`까지 끝난 가장 최근의 4주 묶음."""
    year, week, _ = last.isocalendar()
    g = group_of(year, week)
    if g.dates()[-1] <= last:
        return g
    if g.first == 1:
        return group_of(year - 1, weeks_in(year - 1))
    return group_of(year, g.first - 1)


@dataclass(frozen=True)
class Plan:
    """한 번의 `report`가 만들 보고서. 일간 7일, 끝난 주 넷(월요일), 끝난 4주 묶음 하나."""

    days: list[date]
    weeks: list[date]
    group: Group

    def dates(self) -> list[date]:
        weekly = [d for w in self.weeks for d in _dates(w, w + timedelta(days=6))]
        return sorted({*self.days, *weekly, *self.group.dates()})


def plan_reports(today: date) -> Plan:
    last = today - timedelta(days=1)
    days = [last - timedelta(days=i) for i in range(KEEP_DAILY - 1, -1, -1)]
    sunday = last - timedelta(days=last.isoweekday() % 7)
    weeks = [sunday - timedelta(days=6 + 7 * i) for i in range(KEEP_WEEKLY - 1, -1, -1)]
    return Plan(days, weeks, finished_group(last))


# 보고서: 장부 읽기


@dataclass(frozen=True)
class Book:
    """보고할 날들의 호출 행과 읽지 못한 줄, 읽은 모든 달의 세션 행, 계정."""

    calls: list[Call]
    unreadable: list[Unreadable]
    sessions: dict[str, SessionRow]
    accounts: dict[str, str]


def read_session_rows(path: Path) -> list[SessionRow]:
    """달 파일의 세션 행. 세션 행이 파일 머리에 모여 있어(`_sorted_rows`) 다른 행에서 멈춘다."""
    rows: list[SessionRow] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            r = _obj(_parse_json(line))
            if r.get("kind") != "session":
                break
            rows.append(SessionRow.of(r))
    return rows


def gather_book(ledger_dir: Path, first: date, last: date) -> Book:
    """`first`의 하루 앞부터 `last`의 하루 뒤까지의 달 파일을 읽는다. 시간대 인자가 실행마다 다르면
    행이 이웃 달 파일에 들 수 있어서다. 그보다 앞선 달 파일은 세션 행만 읽는다. 앞선 달에 시작한
    세션의 행이 그 달 파일에 있다."""
    wanted = _month_names(first - timedelta(days=1), last + timedelta(days=1))
    ledger = Ledger()
    sessions: dict[str, SessionRow] = {}
    for month in read_months(ledger_dir):
        path = ledger_dir / f"{month}.jsonl"
        if month in wanted:
            ledger.extend(read_ledger_file(path))
        elif month < wanted[0]:
            sessions.update((s.session, s) for s in read_session_rows(path))
    sessions.update((s.session, s) for s in ledger.sessions)
    accounts = read_accounts(ledger_dir / "accounts.jsonl")
    return Book(ledger.calls, ledger.unreadable, sessions, accounts)


# 보고서: 날짜로 가르기


@dataclass(frozen=True)
class Start:
    """이 저장소 메인 세션의 첫 호출. 구성을 모르면(옛 세션 행) `parts`가 None이고, `human`은
    사람이 연 세션인지다(옛 세션 행은 거짓)."""

    session: str
    context: int
    parts: StartParts | None
    human: bool


@dataclass(frozen=True)
class Daybook:
    """지역 날짜로 가른 장부. 기간의 집계는 여기서 그 기간의 날짜만 꺼낸다."""

    calls: dict[date, list[Call]]
    unreadable: dict[date, int]
    large: dict[date, list[tuple[str, Large]]]
    reads: dict[date, list[tuple[str, FileRead]]]
    compactions: dict[date, list[Compaction]]
    starts: dict[date, list[Start]]
    sessions: dict[str, SessionRow]
    pr_at: dict[str, datetime]
    accounts: dict[str, str]


def is_repo_folder(name: str, repo: str) -> bool:
    """이 저장소와 그 워크트리의 기록 폴더. 이름이 같은 접두로 시작하는 다른 저장소는 뺀다."""
    return name == repo or name.startswith(repo + "--")


def _session_events(
    rows: list[SessionRow], tz: timezone
) -> tuple[
    dict[date, list[tuple[str, Large]]],
    dict[date, list[tuple[str, FileRead]]],
    dict[date, list[Compaction]],
]:
    """세션 행의 도구 결과·읽기·압축을 날짜로 가른다. 포크한 세션에 복사된 것은 ID로 걸러 먼저
    시작한 세션의 것만 남긴다."""
    large: dict[date, list[tuple[str, Large]]] = defaultdict(list)
    reads: dict[date, list[tuple[str, FileRead]]] = defaultdict(list)
    compactions: dict[date, list[Compaction]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for s in sorted(rows, key=lambda s: (_time(s.start) or _NO_TIME, s.session)):
        if s.facts is None:
            continue
        for x in s.facts.large:
            if ("large", x.id) not in seen:
                seen.add(("large", x.id))
                large[local_date(x.at, tz)].append((s.session, x))
        for r in s.facts.reads:
            if ("read", r.id) not in seen:
                seen.add(("read", r.id))
                reads[local_date(r.at, tz)].append((s.session, r))
        for c in s.facts.compactions:
            if ("compaction", c.id) not in seen:
                seen.add(("compaction", c.id))
                compactions[local_date(c.at, tz)].append(c)
    return large, reads, compactions


def _first_prs(rows: Iterable[SessionRow]) -> dict[str, datetime]:
    """브랜치마다 가장 이른 PR 시각."""
    out: dict[str, datetime] = {}
    for s in rows:
        for pr in s.facts.prs if s.facts is not None else ():
            t = _time(pr.at)
            if (
                t is not None
                and pr.branch is not None
                and (pr.branch not in out or t < out[pr.branch])
            ):
                out[pr.branch] = t
    return out


def _starts(book: Book, tz: timezone, since: date, repo: str) -> dict[date, list[Start]]:
    """이 저장소 메인 세션의 첫 호출을 그 날짜로 가른다. 세션 행의 시작이 `since`(읽은 첫 날)보다
    앞이면 그 앞의 호출을 읽지 않아 첫 호출인지 몰라 뺀다."""
    first: dict[str, Call] = {}
    for c in sorted(book.calls, key=lambda c: (c.at, c.id)):
        if c.agent is None and c.session not in first:
            first[c.session] = c
    out: dict[date, list[Start]] = defaultdict(list)
    for sid, c in sorted(first.items()):
        s = book.sessions.get(sid)
        if s is None or local_date(s.start, tz) < since or not is_repo_folder(c.project, repo):
            continue
        parts = s.facts.start_parts if s.facts is not None else None
        human = s.facts is not None and s.facts.human
        out[local_date(c.at, tz)].append(Start(sid, c.context, parts, human))
    return out


def daybook_of(book: Book, tz: timezone, since: date, repo: str) -> Daybook:
    calls: dict[date, list[Call]] = defaultdict(list)
    for c in book.calls:
        calls[local_date(c.at, tz)].append(c)
    unreadable: dict[date, int] = defaultdict(int)
    for u in book.unreadable:
        unreadable[local_date(u.at, tz)] += 1
    large, reads, compactions = _session_events(list(book.sessions.values()), tz)
    return Daybook(
        calls,
        unreadable,
        large,
        reads,
        compactions,
        _starts(book, tz, since, repo),
        book.sessions,
        _first_prs(book.sessions.values()),
        book.accounts,
    )


# 보고서: 집계


@dataclass
class Tally:
    cost: float = 0.0
    calls: int = 0

    def add(self, cost: float | None) -> None:
        self.cost += cost or 0.0
        self.calls += 1


@dataclass
class SessionTally:
    tally: Tally = field(default_factory=Tally)
    max_context: int = 0
    project: str = ""
    branch: str | None = None
    last_main: str = ""


@dataclass
class BranchTally:
    tally: Tally = field(default_factory=Tally)
    sessions: set[str] = field(default_factory=set[str])
    before: float = 0.0


@dataclass
class Period:
    """하루, 한 주, 4주 묶음 하나의 집계."""

    dates: list[date]
    unreadable: int = 0
    total: Tally = field(default_factory=Tally)
    accounts: dict[str, Tally] = field(default_factory=dict[str, Tally])
    kinds: dict[str, Tally] = field(
        default_factory=lambda: {"메인 세션": Tally(), "서브에이전트": Tally()}
    )
    models: dict[tuple[str, str, str], Tally] = field(
        default_factory=dict[tuple[str, str, str], Tally]
    )
    types: dict[str, Tally] = field(default_factory=dict[str, Tally])
    sessions: dict[str, SessionTally] = field(default_factory=dict[str, SessionTally])
    unknown_models: dict[str, int] = field(default_factory=dict[str, int])
    over: set[str] = field(default_factory=set[str])
    idle: Tally = field(default_factory=Tally)
    main_context: int = 0
    cache_read: int = 0
    branches: dict[str | None, BranchTally] = field(default_factory=dict[str | None, BranchTally])
    compactions: list[Compaction] = field(default_factory=list[Compaction])
    starts: list[Start] = field(default_factory=list[Start])
    large: list[tuple[str, Large]] = field(default_factory=list[tuple[str, Large]])
    reads: list[tuple[str, FileRead]] = field(default_factory=list[tuple[str, FileRead]])

    def add(self, c: Call, accounts: dict[str, str], pr_at: dict[str, datetime]) -> None:
        cost = c.cost()
        if cost is None:
            self.unknown_models[c.model] = self.unknown_models.get(c.model, 0) + 1
        kind = "메인 세션" if c.agent is None else "서브에이전트"
        model = c.model.removeprefix("claude-")
        self.total.add(cost)
        self.accounts.setdefault(accounts.get(c.session, UNKNOWN_ACCOUNT), Tally()).add(cost)
        self.kinds[kind].add(cost)
        self.models.setdefault((kind, model, c.effort or "(없음)"), Tally()).add(cost)
        if c.agent is not None:
            self.types.setdefault(c.agent_type or "(미상)", Tally()).add(cost)
        s = self.sessions.setdefault(c.session, SessionTally())
        s.tally.add(cost)
        if c.agent is None:
            s.max_context = max(s.max_context, c.context)
            s.project, s.branch, s.last_main = c.project, c.branch, c.at
            self._add_main(c)
        elif not s.project:
            s.project = c.project
        b = self.branches.setdefault(c.branch, BranchTally())
        b.tally.add(cost)
        b.sessions.add(c.session)
        pr = pr_at.get(c.branch) if c.branch is not None else None
        t = _time(c.at)
        if pr is not None and t is not None and t < pr:
            b.before += cost or 0.0

    def _add_main(self, c: Call) -> None:
        if c.context > OVER_CONTEXT:
            self.over.add(c.session)
        self.main_context += c.context
        self.cache_read += c.cache_read
        rewrite = (c.cache_write_5m + c.cache_write_1h) * 2 >= c.context > 0
        if c.gap_s is not None and c.gap_s > IDLE_S and rewrite:
            self.idle.add(c.write_cost())


def _on[T](by_date: dict[date, list[T]], dates: list[date]) -> list[T]:
    """날짜로 가른 목록에서 그 날짜들의 것을 날짜 차례로 잇는다."""
    return [x for d in dates for x in by_date.get(d, [])]


def period_of(dates: list[date], days: Daybook) -> Period:
    p = Period(dates)
    calls = sorted(_on(days.calls, dates), key=lambda c: (c.at, c.session, c.agent or "", c.id))
    for c in calls:
        p.add(c, days.accounts, days.pr_at)
    p.unreadable = sum(days.unreadable.get(d, 0) for d in dates)
    p.compactions = _on(days.compactions, dates)
    p.starts = _on(days.starts, dates)
    p.large = _on(days.large, dates)
    p.reads = _on(days.reads, dates)
    return p


def start_median(p: Period) -> float | None:
    """사람이 연 세션의 시작 컨텍스트 중앙값. 그런 세션이 없으면 None이다."""
    values = [s.context for s in p.starts if s.human]
    return statistics.median(values) if values else None


# 보고서: 경보


@dataclass(frozen=True)
class Alarms:
    alarms: list[str]
    notes: list[str]


def alarms_of(day: Period, previous: list[Period]) -> Alarms:
    """하루의 경보. `previous`는 그 앞 7일이다."""
    alarms: list[str] = []
    notes: list[str] = []
    busy = [p.total.cost for p in previous if p.total.calls]
    if len(busy) < MIN_DAYS:
        notes.append(
            f"비용 급증은 비교하지 않았다: 지난 7일 가운데 호출이 있던 날이 {len(busy)}일로"
            " 넷보다 적다"
        )
    else:
        median = statistics.median(busy)
        if day.total.cost > median * SPIKE:
            alarms.append(
                f"경보: 환산 비용 ${_money(day.total.cost)}이 지난 7일 가운데 호출이 있던"
                f" {len(busy)}일의 중앙값 ${_money(median)}의 {SPIKE}배를 넘는다"
            )
    if day.over:
        alarms.append(f"경보: 세션 컨텍스트가 40만을 넘은 세션 {len(day.over)}개")
    today = start_median(day)
    started = [m for p in previous if (m := start_median(p)) is not None]
    if today is not None and len(started) < MIN_DAYS:
        notes.append(
            "시작 컨텍스트는 비교하지 않았다: 지난 7일 가운데 시작한 세션이 있던 날이"
            f" {len(started)}일로 넷보다 적다"
        )
    elif today is not None and today > statistics.median(started) * START_SPIKE:
        alarms.append(
            f"경보: 시작 컨텍스트 중앙값 {today:,.0f}이 지난 7일 가운데 시작한 세션이 있던"
            f" {len(started)}일의 중앙값 {statistics.median(started):,.0f}보다 10% 넘게 크다"
        )
    parts: list[str] = []
    if day.unknown_models:
        n = sum(day.unknown_models.values())
        parts.append(f"단가표에 없는 모델의 호출 {n}회({', '.join(sorted(day.unknown_models))})")
    if day.unreadable:
        parts.append(f"읽지 못한 기록 줄 {day.unreadable}개")
    if parts:
        alarms.append("경보: " + ", ".join(parts))
    return Alarms(alarms, notes)


# 보고서: 글


def _money(v: float) -> str:
    return f"{v:,.2f}"


def _share(part: float, total: float) -> str:
    return f"{part / total:.1%}" if total > 0 else "해당 없음"


def _table(head: list[str], align: str, rows: list[list[str]]) -> list[str]:
    if not rows:
        return ["해당 없음"]
    return [
        "| " + " | ".join(head) + " |",
        "|" + "|".join("--:" if a == "r" else "---" for a in align) + "|",
        *("| " + " | ".join(r) + " |" for r in rows),
    ]


def _section(n: int, title: str) -> list[str]:
    return ["", f"## {n}. {title}", ""]


def _by_cost[K](items: dict[K, Tally]) -> list[tuple[K, Tally]]:
    return sorted(items.items(), key=lambda kv: (-kv[1].cost, -kv[1].calls, str(kv[0])))


def _tz_text(tz: timezone) -> str:
    off = tz.utcoffset(None)
    sign = "-" if off < timedelta(0) else "+"
    minutes = abs(int(off.total_seconds())) // 60
    return f"{sign}{minutes // 60:02}:{minutes % 60:02}"


def _local_text(at: str | None, tz: timezone) -> str:
    t = _time(at)
    return t.astimezone(tz).strftime("%Y-%m-%d %H:%M") if t is not None else "(모름)"


def _spread(values: list[int]) -> str:
    if not values:
        return "해당 없음"
    return f"최소 {min(values):,}, 중앙값 {statistics.median(values):,.0f}, 최대 {max(values):,}"


@dataclass(frozen=True)
class Page:
    """보고서 파일 하나. 일간은 추이가 없다."""

    title: str
    period: Period
    alarms: list[str]
    notes: list[str]
    trend_title: str = ""
    trend: list[tuple[str, Period]] = field(default_factory=list[tuple[str, Period]])


def _head_lines(page: Page, days: Daybook, tz: timezone) -> list[str]:
    p = page.period
    lines = [
        f"# {page.title}",
        "",
        f"지역 시간대 {_tz_text(tz)}의 날짜다. 비용은 장부의 토큰에 단가표"
        "(`tools/token_report.py`의 `PRICES`)를 곱한 API 환산 달러다. 구독 한도에서 무엇이 "
        "차감됐는지는 `/usage`의 플랜 사용량 내역(이 기계의 기록으로 어림한 값)을 본다.",
        "",
    ]
    if not p.total.calls:
        lines += ["호출 없음", ""]
    old = sorted(s for s in p.sessions if (r := days.sessions.get(s)) and r.facts is None)
    if old:
        lines += [
            f"새 칸이 없는 옛 세션 행 {len(old)}개는 7·9·10·12절에서 모름이다"
            "(`ingest --full`로 다시 쌓는다).",
            "",
        ]
    lines += ["## 1. 경보", ""]
    lines += [f"- {x}" for x in page.alarms] or ["- 없음"]
    lines += [f"- {x}" for x in page.notes]
    return lines


def _cost_lines(p: Period, days: Daybook, tz: timezone) -> list[str]:
    """2~6절."""
    total = p.total.cost
    money = ["환산 비용($)", "몫", "호출"]

    def cells(v: Tally) -> list[str]:
        return [_money(v.cost), _share(v.cost, total), str(v.calls)]

    lines = [
        *_section(2, "합계와 계정별"),
        f"모델 호출 {p.total.calls}회, 환산 비용 ${_money(total)}",
        "",
    ]
    lines += _table(["계정", *money], "lrrr", [[k, *cells(v)] for k, v in _by_cost(p.accounts)])
    lines += _section(3, "메인 세션과 서브에이전트")
    kinds = [[k, *cells(v)] for k, v in p.kinds.items()] if p.total.calls else []
    lines += _table(["구분", *money], "lrrr", kinds)
    lines += _section(4, "모델·노력별")
    lines += _table(
        ["구분", "모델", "노력", *money],
        "lllrrr",
        [[*k, *cells(v)] for k, v in _by_cost(p.models)],
    )
    lines += [*_section(5, "서브에이전트 유형별"), "몫은 전체 비용에 대한 것이다.", ""]
    lines += _table(["유형", *money], "lrrr", [[k, *cells(v)] for k, v in _by_cost(p.types)])
    lines += [
        *_section(6, "상위 세션 다섯"),
        "비용과 호출은 메인 세션과 그 서브에이전트를 합친 것이고,"
        " 세션 컨텍스트는 메인 세션의 것이다.",
        "",
    ]
    top = sorted(p.sessions.items(), key=lambda kv: (-kv[1].tally.cost, -kv[1].tally.calls, kv[0]))
    lines += _table(
        ["세션", "기록 폴더", "브랜치", "시작", "환산 비용($)", "최대 세션 컨텍스트", "호출"],
        "llllrrr",
        [
            [
                sid[:8],
                s.project,
                s.branch or "(모름)",
                _local_text(r.start if (r := days.sessions.get(sid)) else None, tz),
                _money(s.tally.cost),
                f"{s.max_context:,}",
                str(s.tally.calls),
            ]
            for sid, s in top[:TOP]
        ],
    )
    return lines


def _context_lines(p: Period) -> list[str]:
    """7절."""
    auto = [c for c in p.compactions if c.trigger == "auto"]
    before = [c.context for c in auto if c.context is not None]
    return [
        *_section(7, "세션 컨텍스트 40만과 압축"),
        f"- 세션 컨텍스트가 40만을 넘은 메인 세션 {len(p.over)}개",
        f"- 압축 자동 {len(auto)}회, 수동 {len(p.compactions) - len(auto)}회",
        f"- 자동 압축 직전의 세션 컨텍스트: {_spread(before)}",
    ]


def _idle_lines(p: Period) -> list[str]:
    """8절."""
    return [
        *_section(8, "쉰 뒤의 캐시 재작성"),
        "직전 호출과 60분 넘게 떨어진 메인 세션 호출 가운데 세션 컨텍스트 절반 이상을 캐시에 다시"
        f" 쓴 것 {p.idle.calls}회, 캐시 쓰기 환산 비용 ${_money(p.idle.cost)}"
        f"(전체 비용의 {_share(p.idle.cost, p.total.cost)})",
    ]


def _start_lines(p: Period) -> list[str]:
    """9절."""
    lines = _section(9, "시작 컨텍스트")
    others = [s.context for s in p.starts if not s.human]
    if others:
        lines += [
            "사람이 연 세션이 아닌 것(헤드리스 `claude -p`, SDK, 칸이 없는 옛 행)"
            f" {len(others)}개는 아래 중앙값에 넣지 않았다. 그 첫 호출 세션 컨텍스트 중앙값은"
            f" {statistics.median(others):,.0f}이다.",
            "",
        ]
    median = start_median(p)
    if median is None:
        return [*lines, "이 기간에 첫 호출이 있는, 사람이 연 이 저장소의 메인 세션이 없다."]
    human = [s for s in p.starts if s.human]
    known = [s.parts for s in human if s.parts is not None]
    lines += [
        f"사람이 연 이 저장소의 메인 세션 {len(human)}개의 첫 호출 세션 컨텍스트 중앙값"
        f" {median:,.0f}. 구성은 첫 호출 전 첨부의 글자 수이고, 구성을 아는 세션 {len(known)}개의"
        " 중앙값이다.",
        "",
    ]
    if not known:
        return [*lines, "해당 없음"]

    def mid(values: Iterable[int]) -> str:
        return f"{statistics.median(values):,.0f}"

    sources = {k for x in known for k in x.skills}
    by_source = sorted(
        ((k, statistics.median(x.skills.get(k, 0) for x in known)) for k in sources),
        key=lambda kv: (-kv[1], kv[0]),
    )
    rows = [["스킬 목록 합", mid(sum(x.skills.values()) for x in known)]]
    rows += [[f"스킬 목록: {k}", f"{v:,.0f}"] for k, v in by_source]
    rows += [
        ["지연 도구 목록", mid(x.deferred_tools for x in known)],
        ["지침 파일", mid(x.instructions for x in known)],
        ["그 밖", mid(x.other for x in known)],
    ]
    return [*lines, *_table(["구성", "중앙값(자)"], "lr", rows)]


def _branch_lines(p: Period, days: Daybook) -> list[str]:
    """10절."""
    lines = [
        *_section(10, "브랜치별"),
        "환산 비용 상위 열. 인계는 그 브랜치에 호출이 있는 세션 가운데 인계로 열린 세션의 수다. PR"
        " 앞·뒤는 그 브랜치의 비용을 장부에서 가장 이른 PR 연 시각으로 가른 몫이다.",
        "",
    ]
    rows: list[list[str]] = []
    top = sorted(
        p.branches.items(), key=lambda kv: (-kv[1].tally.cost, -kv[1].tally.calls, str(kv[0]))
    )
    for branch, b in top[:TOP_BRANCHES]:
        handoffs = sum(
            1
            for sid in b.sessions
            if (r := days.sessions.get(sid)) is not None and r.facts is not None and r.facts.handoff
        )
        cost = b.tally.cost
        if branch is not None and branch in days.pr_at:
            split = f"{_share(b.before, cost)} · {_share(cost - b.before, cost)}"
        else:
            split = "PR 시각 모름"
        rows.append(
            [
                branch or "(모름)",
                _money(cost),
                _share(cost, p.total.cost),
                str(len(b.sessions)),
                str(handoffs),
                split,
            ]
        )
    head = ["브랜치", "환산 비용($)", "몫", "세션", "인계", "PR 앞·뒤"]
    return [*lines, *_table(head, "lrrrrl", rows)]


def _cache_lines(p: Period) -> list[str]:
    """11절."""
    n = p.kinds["메인 세션"].calls
    average = f"{p.main_context / n:,.0f}" if n else "해당 없음"
    return [
        *_section(11, "캐시 효율"),
        f"메인 세션 호출 {n}회, 호출당 평균 세션 컨텍스트 {average},"
        f" 캐시 읽기의 몫 {_share(p.cache_read, p.main_context)}",
    ]


def _target_text(x: Large) -> str:
    if x.target is None:
        return "(남기지 않음)"
    return file_key_of(x.target) if x.tool == "Read" else x.target


def _file_rows(reads: list[tuple[str, FileRead]]) -> list[list[str]]:
    """셋 이상의 세션이 읽은 파일의 상위 다섯(세션 수, Read 수, 글자 순)."""
    sessions: dict[str, set[str]] = defaultdict(set)
    count: dict[str, int] = defaultdict(int)
    chars: dict[str, int] = defaultdict(int)
    for sid, r in reads:
        key = file_key_of(r.path)
        sessions[key].add(sid)
        count[key] += 1
        chars[key] += r.chars
    many = [k for k, v in sessions.items() if len(v) >= MANY_SESSIONS]
    many.sort(key=lambda k: (-len(sessions[k]), -count[k], -chars[k], k))
    return [[k, str(len(sessions[k])), str(count[k]), f"{chars[k]:,}"] for k in many[:TOP]]


def _reread_line(reads: list[tuple[str, FileRead]]) -> str:
    total = sum(r.chars for _, r in reads)
    again = [r for _, r in reads if r.again]
    chars = sum(r.chars for r in again)
    line = f"다시 읽기 후보 {len(again)}회 {chars:,}자(Read 글자의 {_share(chars, total)})"
    if not again:
        return line
    by: dict[str, int] = defaultdict(int)
    for r in again:
        by[file_key_of(r.path)] += r.chars
    key, n = min(by.items(), key=lambda kv: (-kv[1], kv[0]))
    return f"{line}, 가장 많은 파일 {key} {n:,}자"


def _tool_lines(p: Period) -> list[str]:
    """12절."""
    top = sorted(
        p.large, key=lambda sx: (-sx[1].chars * sx[1].carried, -sx[1].chars, sx[1].at, sx[1].id)
    )
    return [
        *_section(12, "큰 도구 결과와 반복 Read"),
        f"문턱을 넘은 결과 {len(p.large)}개(범위 없는 Read {LARGE['Read']:,}자, Bash·PowerShell"
        f" {LARGE['Bash']:,}자). 상위 다섯은 무게(글자 × 그 뒤 실려 간 호출 수) 순이다.",
        "",
        *_table(
            ["도구", "글자", "실려 간 호출", "대상", "세션"],
            "lrrll",
            [
                [x.tool, f"{x.chars:,}", f"{x.carried:,}", _target_text(x), sid[:8]]
                for sid, x in top[:TOP]
            ],
        ),
        "",
        "셋 이상의 세션이 읽은 파일(워크트리 접두를 벗긴 경로):",
        "",
        *_table(["파일", "세션", "Read", "글자"], "lrrr", _file_rows(p.reads)),
        "",
        _reread_line(p.reads),
    ]


def _trend_lines(page: Page) -> list[str]:
    """13절. 주간은 날짜별, 4주 요약은 주별이다."""
    rows = [
        [
            label,
            str(q.total.calls),
            _money(q.total.cost),
            _share(q.kinds["메인 세션"].cost, q.total.cost),
            f"{m:,.0f}" if (m := start_median(q)) is not None else "해당 없음",
            str(len(q.over)),
        ]
        for label, q in page.trend
    ]
    head = [
        "기간",
        "모델 호출",
        "환산 비용($)",
        "메인 세션 몫",
        "시작 컨텍스트 중앙값",
        "40만 넘은 세션",
    ]
    return [*_section(13, page.trend_title), *_table(head, "lrrrrr", rows)]


def page_text_of(page: Page, days: Daybook, tz: timezone) -> str:
    p = page.period
    lines = [
        *_head_lines(page, days, tz),
        *_cost_lines(p, days, tz),
        *_context_lines(p),
        *_idle_lines(p),
        *_start_lines(p),
        *_branch_lines(p, days),
        *_cache_lines(p),
        *_tool_lines(p),
    ]
    if page.trend:
        lines += _trend_lines(page)
    return "\n".join(lines) + "\n"


def summary_text_of(d: Period, a: Alarms, report: Path) -> str:
    head = f"환산 비용 ${_money(d.total.cost)}"
    if d.total.calls:
        head += " (" + ", ".join(f"{k} ${_money(v.cost)}" for k, v in _by_cost(d.accounts)) + ")"
    lines = [f"보고서 날짜: {d.dates[0].isoformat()}", head, *(a.alarms or ["경보 없음"])]
    lines.append(f"보고서: {report}")
    return "\n".join(lines) + "\n"


def _span_text(dates: list[date]) -> str:
    return f"{dates[0].isoformat()} ~ {dates[-1].isoformat()}"


def pages_of(
    plan: Plan, periods: dict[date, Period], alarms: dict[date, Alarms], days: Daybook
) -> dict[str, Page]:
    """출력 폴더 아래 경로마다 보고서."""

    def dated(dates: list[date]) -> list[str]:
        """주간·4주 요약의 1절. 날마다의 경보에 날짜를 단다."""
        return [f"{d.isoformat()}: {x}" for d in dates for x in alarms[d].alarms]

    pages: dict[str, Page] = {}
    for d in plan.days:
        a = alarms[d]
        title = f"토큰 사용 일간 보고서: {d.isoformat()}"
        pages[f"{DAILY}/{d.isoformat()}.md"] = Page(title, periods[d], a.alarms, a.notes)
    for monday in plan.weeks:
        dates = _dates(monday, monday + timedelta(days=6))
        name = week_name_of(monday)
        pages[f"{WEEKLY}/{name}.md"] = Page(
            f"토큰 사용 주간 보고서: {name}({_span_text(dates)})",
            period_of(dates, days),
            dated(dates),
            [],
            "날짜별 추이",
            [(d.isoformat(), periods[d]) for d in dates],
        )
    g = plan.group
    dates = g.dates()
    weeks = [(week_name_of(m), _dates(m, m + timedelta(days=6))) for m in g.mondays()]
    pages[f"{FOUR_WEEKS}/{g.name()}.md"] = Page(
        f"토큰 사용 4주 요약: {g.year}-W{g.first:02}~W{g.last:02}({_span_text(dates)})",
        period_of(dates, days),
        dated(dates),
        [],
        "주별 추이",
        [(name, period_of(ws, days)) for name, ws in weeks],
    )
    return pages


def stale_reports(folder: Path, keep_from: str, name: re.Pattern[str]) -> list[Path]:
    """그 이름 모양의 보통 파일 가운데 보고할 첫 파일 이름(`keep_from`)보다 이른 것. 링크·폴더,
    그보다 뒤의 것(다른 `--today`로 만든 것)은 들지 않는다."""
    if not folder.is_dir():
        return []
    return sorted(
        p
        for p in folder.iterdir()
        if name.fullmatch(p.name) and p.name < keep_from and not is_link(p) and p.is_file()
    )


# 보고서: 명령


def report(out: Path, tz: timezone, today: date, repo: str) -> None:
    linked = [f for f in (out / DAILY, out / WEEKLY, out / FOUR_WEEKS) if is_link(f)]
    if linked:
        raise ToolError(f"보고서 폴더가 링크라 쓰지도 지우지도 않는다: {linked[0]}")
    plan = plan_reports(today)
    dates = plan.dates()
    first = dates[0] - timedelta(days=ALARM_DAYS)
    book = gather_book(out / "ledger", first, dates[-1])
    days = daybook_of(book, tz, first - timedelta(days=1), repo)
    periods = {d: period_of([d], days) for d in _dates(first, dates[-1])}
    previous = range(1, ALARM_DAYS + 1)
    alarms = {
        d: alarms_of(periods[d], [periods[d - timedelta(days=i)] for i in previous]) for d in dates
    }
    pages = pages_of(plan, periods, alarms, days)
    for path, page in pages.items():
        write_atomic(out / path, page_text_of(page, days, tz))
    last = plan.days[-1]
    daily = out / DAILY / f"{last.isoformat()}.md"
    write_atomic(out / "summary.txt", summary_text_of(periods[last], alarms[last], daily))
    gone = [
        *stale_reports(out / DAILY, f"{plan.days[0].isoformat()}.md", DAILY_NAME),
        *stale_reports(out / WEEKLY, f"{week_name_of(plan.weeks[0])}.md", WEEKLY_NAME),
    ]
    for p in gone:
        p.unlink(missing_ok=True)
    print(f"보고서 {len(pages)}개를 쓰고 {len(gone)}개를 지웠다: {out}")


class ToolError(Exception):
    pass


# 경로


def folder_name_of(checkout: Path) -> str:
    """Claude Code가 그 체크아웃의 세션 기록을 두는 폴더 이름. 영문자와 숫자 밖의 글자를 `-`로
    바꾼다(`C:\\project\\agent`는 `C--project-agent`, 2026-10-16 폴더 목록으로 손으로 봤다)."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(checkout))


def main_checkout() -> Path:
    """이 파일이 든 저장소의 git 공용 디렉터리의 부모."""
    done = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=Path(__file__).resolve().parent,
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        check=True,
    )
    return Path(done.stdout.strip()).parent


def _date_of(text: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"날짜는 YYYY-MM-DD다: {text}") from e


def _parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--projects", type=Path, help="세션 기록 폴더(기본 ~/.claude/projects)")
    common.add_argument(
        "--out", type=Path, help="출력 폴더(기본 주 체크아웃의 .scratch/token-report)"
    )
    common.add_argument("--tz", type=tz_of, help="지역 시간대, +09:00 같은 고정 오프셋")
    common.add_argument(
        "--today", type=_date_of, help="오늘 날짜 YYYY-MM-DD(기본 지역 시간대의 오늘)"
    )
    common.add_argument(
        "--repo", help="이 저장소의 기록 폴더 이름(기본 주 체크아웃의 경로에서 만든 것)"
    )
    parser = argparse.ArgumentParser(
        prog="token_report.py", description="토큰 사용량 장부와 보고서. 자세한 것은 독스트링."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    ing = sub.add_parser("ingest", parents=[common], help="세션 기록을 읽어 장부를 갱신한다")
    ing.add_argument("--full", action="store_true", help="state.json을 무시하고 모두 다시 읽는다")
    sub.add_parser("report", parents=[common], help="장부에서 보고서와 요약을 만든다")
    sub.add_parser("daily", parents=[common], help="ingest와 report를 차례로 한다")
    return parser


def main(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    command: str = args.command
    projects: Path = args.projects or Path.home() / ".claude" / "projects"
    tz: timezone = args.tz or tz_of(_tz_text(_local_tz()))
    today: date = args.today or datetime.now(tz).date()
    try:
        out: Path = args.out or main_checkout() / ".scratch" / "token-report"
        # 이 저장소의 폴더 이름은 보고서(9절)만 쓴다. `ingest`는 git 없이도 돈다.
        repo: str | None = None
        if command != "ingest":
            repo = args.repo or folder_name_of(main_checkout())
    except (OSError, subprocess.SubprocessError) as e:
        print(f"주 체크아웃을 찾지 못했다. --out과 --repo를 준다: {e}", file=sys.stderr)
        return 2
    try:
        with Lock(out):
            if command != "report":
                since = None if getattr(args, "full", False) else read_changed_since(out)
                ingest(projects, out, tz, since)
            if repo is not None:
                report(out, tz, today, repo)
    except LockedError as e:
        print(f"다른 실행이 도는 중이라 멈춘다. 잠금 파일: {e}", file=sys.stderr)
        print("멈춘 실행이 남긴 잠금이면 그 파일을 지우고 다시 돌린다.", file=sys.stderr)
        return 3
    except ToolError as e:
        print(str(e), file=sys.stderr)
        return 2
    return 0


def _local_tz() -> timezone:
    off = datetime.now().astimezone().utcoffset() or timedelta(0)
    return timezone(off)


if __name__ == "__main__":
    # 윈도의 파이프는 PYTHONUTF8이 없으면 cp949다. 한글 출력이 깨지지 않게 고정한다.
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv[1:]))
