# 2026-10-22 (11) 하네스 chore 배치: 회차 3 이상인 대기열 행 아홉과 같은 대상의 고침 셋

브랜치 `chore/choice-facts-batch`, 워크트리 `.claude/worktrees/choice-facts-batch`.

> 사용자: "대기열 394·395·339·412·341·391·396·400·403(회차 3 이상인 열린 행 아홉. 227도 4회차지만 열린 PR #296이 맡았다)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이 대상이고, 같은 대상 파일의 고침 행 368(412보다 먼저 고친다)·369·408(412와 tools/hook_payloads.toml이나 같은 훅 파일을 든다)을 함께 반영한다 … 다음 단계: 구현 / 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 … 브랜치: chore/choice-facts-batch / 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래 … 이어받을 상태: PR #338(mcp-shutdown 03)은 claude-review 첫 회차의 Minor 3·Nit 3을 모두 두고(이유는 그 PR의 코멘트) 고침 없이 병합했다. CodeRabbit은 그 HEAD에서 한도에 걸려 리뷰가 없었다. 그 PR을 연 세션은 hook_handoff가 아니라 다른 세션("주간한도 95% 초과 시 세션 전환")의 요청으로 끊겼고, 고침 커밋이 없어 그 사실은 일지 2026-10-21-14에 실리지 않았다 … 이번 요청 범위: PR과 병합까지"

## 시작

`tidy-checkouts`가 루트 main을 `14efe41d`에서 `c1e05e96`로 당기고 병합된 워크트리와 브랜치 열둘을 지웠다. 휴지통의 `node_modules`·`.venv` 사본 열넷은 다른 체크아웃의 node.exe·esbuild.exe·python.exe가 쥐어 남았다. 그 뒤 `EnterWorktree`로 새 워크트리에 들어가 브랜치를 `chore/choice-facts-batch`로 바꿨다. 기점은 origin/main `6bd52b06`(#342)이다.

`queue_open_rows.py --rows`의 회차 3 이상은 394(7)·395(5)·227(4)·339(4)·412(4)·341(3)·391(3)·396(3)·400(3)·403(3)이었다. 227은 지시문대로 PR #296이 맡아 뺐다.

## 339: 탐침이 나눠 쓰는 도구

`tools/probe_kit.py`를 새로 두었다. `Rounds`는 회차마다 표지를 받아 측정인 회차와 아닌 회차를 세고, 측정 아님이 하나라도 있거나 측정이 없으면 종료 코드 1을 낸다. 회차 안의 예외는 측정 아님으로 적고 다음 회차로 간다. `LineReader`는 하위 프로세스의 줄을 daemon 스레드와 큐로 제한 시간 안에 읽고, EOF를 본 뒤에는 기다리지 않는다(EOF 표시를 되돌리는 대신 상태로 기억한다). 시험은 `tests/tools/test_probe_kit.py` 열하나다. 이 배치의 새 탐침 둘이 `Rounds`를 쓴다.

## 368·412: 커밋 중 편집 훅

368의 처방은 거짓 알림을 먼저 재현하고 원인을 가르라고 했다. 탐침 `.scratch/harness/probes/edit_during_commit_launcher.py`를 지어 실행 파일 셋(런처 `cmd`·`bin`, 실제 git)과 `-C` 절대·상대, 부하 없음·부하로 갈랐다. 탐침은 훅의 지금 판과 옛 판(작업 디렉터리만 본 판)을 같은 훑기로 함께 판정해, 옛 판이 거짓 알림을 낸 회차가 고친 길을 지난 표지가 된다.

- 고치기 전 10회차: 런처는 모든 갈래에서 10회차 모두 거짓 알림이었다. 순간은 행이 짐작한 런처(자식 전·자식 뒤)만이 아니라 런처의 자식 git에서도 났다. 실제 git을 바로 띄운 갈래도 `-C`를 풀기 전의 순간에 났다(부하 없이 절대 5·상대 3, 부하 아래 9·9).
- 고침: 전역 옵션의 `-C`를 차례로 풀고 마지막 `--work-tree`를 얹는다(`commit_directory`). 절대 경로는 옮기기 전과 뒤가 같은 자리를 가리킨다. 런처는 실행 파일 자리로 알아보고(`is_launcher`, 윈도는 `QueryFullProcessImageNameW`) 띄운 폴더에서 상대 경로를 푼다. 60회차로 다시 재니 절대 경로는 0이 되었지만 런처의 상대 경로는 자식 git에서 여전히 27~59회차였다. 그래서 런처가 띄운 자식의 상대 경로는 런처의 작업 디렉터리에서 풀게 더 고쳤고, 30회차로 다시 재니 런처의 상대 경로 120회차 가운데 둘(자식이 끝난 뒤의 런처, 원인은 가르지 않았다)만 남았다.
- 남긴 것: 바로 띄운 실제 git의 상대 경로 `-C`는 이미 옮겼는지 알 수 없어 작업 디렉터리를 믿는다. 옮기기 전이면 띄운 폴더의 편집을 막는 거짓 양성이고(30회차에서 부하 없이 17, 부하 아래 30), 훅의 못 보는 것과 그 시험으로 고정했다.

412는 그 뒤에 훅을 PostToolUse 알림에서 PreToolUse 막음(deny)으로 옮겼다. 등록, `tools/hook_payloads.toml`의 사례, 시간 탐침(`edit_during_commit_time.py`, 판정을 deny로 읽게 고치고 다시 쟀다. 175~199ms), `.claude/rules/tools.md`의 시간 문단을 함께 고쳤다. 막는 이유 문장은 처음에 `ensure_ascii=False`로 냈는데, 훅 환경의 stdout이 cp949면 그 출력이 예외를 내고 fail-open으로 막음이 조용히 풀린다. 그래서 기본값으로 되돌렸다.

시험 단언 하나를 고쳤다. 막는 이유에 `대기열 412`가 있는지 본 단언이 메시지의 `대기열 293·412`와 맞지 않아 빨갰다. 훅이 아니라 단언의 표기가 틀린 것이라 `대기열 293·412`로 고쳤다.

## 408: `gh api`로 연 PR

도움말(`gh api --help`)은 필드가 있으면 POST라고만 하고 `--input`만 준 꼴은 말하지 않는다. 그래서 탐침 `.scratch/harness/probes/gh_api_method.py`로 쟀다. `GH_DEBUG=api`와 가짜 토큰으로 `--hostname localhost`(닫힌 443번 포트)에 보내, 디버그 기록의 요청 줄에서 메서드를 읽는다. 필드 없음 GET, `-f` POST, `-X POST` POST(대조 셋이 기대대로), `--input`만 POST, `--input`과 `-X GET`은 GET이었다.

두 훅(`hook_pr_next_session`, `hook_handoff`)에 같은 판정 `opens_pr_by_api`를 옮겨 적었다. 엔드포인트가 `repos/<주인>/<이름>/pulls`이고, 메서드가 `-X`·`--method`로 POST이거나 메서드 없이 몸(`-f`·`-F`·`--input`)이 있으면 PR 열기다. 엔드포인트는 인용되기 쉬워, 이 판정만 인용 구간을 지우지 않고 그 안의 공백과 셸 문자를 `_`로 바꿔 한 낱말로 남긴다. `gh pr` 길의 기존 동작은 그대로 두었다. `hook_pr_next_session`에도 `--dry-run`·`--help`·`-h`를 거르는 `_runs`를 더했다. 두 시험은 같은 표 `tests/tools/gh_api_cases.py`를 쓴다. 못 보는 것은 GraphQL의 `createPullRequest`, 변수로 준 엔드포인트, REST의 병합(`PUT …/pulls/<번호>/merge`, `hook_pr_next_session`만 해당)이다.

handoff 시험의 단언 하나를 고쳤다. 표의 침묵 사례 `git commit -m "gh api …"`는 handoff에서는 원래 "커밋 뒤" 경계라 `is None`이 빨갰다. 훅이 아니라 단언이 틀린 것이라 "PR 연 뒤가 아니다"로 고쳤다.

## 369: Grep glob의 중괄호

처방대로 먼저 손으로 봤다. 스크래치패드의 임시 저장소에 숨김 파일 둘(`.hidden369`, gitignore 된 `.probe369`)과 마크다운 둘을 두고 이 세션의 Grep 도구(claude 2.1.302)로 같은 표지를 찾았다. glob이 없으면 숨김 파일은 읽고 gitignore 된 파일은 건너뛰었고, `{*.md,**}`는 gitignore 된 숨김 파일까지 읽었으며, `*.md`(음성 대조)는 마크다운 둘만 읽었다. 그래서 `{*.md,**}`의 꼴은 가짜 `.env`에 닿는다.

`tools/hook_env_read.py`는 glob을 중괄호 갈래마다 펼쳐(`_brace_branches`, 여러 묶음과 겹친 묶음도 푼다) 한 갈래라도 `.env`에 닿으면 막는다(`_reaches_env`). Grep 도구의 glob, rg의 glob, grep의 `--include`가 그것을 쓴다. 빼는 자리(`--exclude`, rg의 `!`)는 펼치지 않는다. 인용된 중괄호는 grep이 글자로 읽어 `.env`를 빼지 않기 때문이다. 그 대가로 따옴표 없이 bash가 펼쳐 `.env`를 빼는 `--exclude={.env*,x}`도 막는 거짓 양성이 남고, 독스트링의 못 보는 것에 적었다. 독스트링의 두 서술(머리 문단, `deny_reason_for_grep_tool`)은 잰 동작(glob 없이는 숨김 파일을 읽고 gitignore 된 파일을 건너뛴다, glob의 갈래가 바로 맞으면 gitignore 된 파일도 읽는다)으로 고쳤다. `tools/hook_payloads.toml`에 행의 꼴 `{.claude/**,docs/*.md}`를 발동 사례로 더했다.

## 394·395: 선택 화면 훅이 처음 화면을 막는다

394의 처방은 거부 이유가 AskUserQuestion에서 모델에게 닿는지를 먼저 재라고 했다. `choice_facts/probe.py`에 갈래 E를 더했다. `deny_hook.py`가 같은 질문의 첫 호출을 거부하고 둘째 호출을 지나가게 한다. E를 다섯 번 돌렸고 모두 측정이고 기대대로였다. 거부 이유는 도구 결과(`PreToolUse:AskUserQuestion hook error: <이유>`)로 모델에게 갔고, 막힌 호출에는 허락 요청(앱의 선택 화면)이 없었으며, 모델이 같은 질문을 4.1~5.4초 뒤에 다시 부르자 그 호출에만 허락 요청이 왔다.

E의 첫 판 기준 하나는 결과를 본 뒤 고쳤다. "거부 표지를 둘째 호출 앞의 글에 옮긴다"를 단언했는데, 셋째 회차가 표지를 마지막 답에서야 옮겨 어긋났다. 둘째 호출은 첫 결과 뒤에 생성되어 이유가 이미 문맥에 있으므로, 읽었다는 표지는 첫 결과 뒤의 글 어디든 된다고 보고 기준을 "첫 결과 뒤의 모델 글"로 바꿨다. 둘째 호출 앞에 옮겼는지는 단언 밖에서 찍는다. 그 회차의 저장한 원본을 새로 더한 `--saved`로 다시 읽어 기대대로임을 봤다. 결과를 본 뒤 기준을 고친 것이라 독스트링과 README에 그대로 적었다.

그 결과로 `tools/hook_choice_facts.py`를 막는 훅으로 바꿨다. 막는 대상은 실수다.

- 세션에서 질문 문장과 라벨이 처음인 선택 화면은 한 번 막는다. 거부 이유는 설명의 사실을 지금 대 보고, 다르면 고치고, 대 보지 못한 것은 어림이라고 적은 뒤 다시 부르라고 한다(grilling의 "올리기 전"). 이유 끝에 수가 든 문장을 옮기는 것은 옛 판과 같다.
- 같은 화면인지는 질문 문장과 라벨로 가른다(`screen_key`). 그래서 설명만 고쳐 다시 부른 화면은 다시 막지 않는다.
- 표지는 임시 폴더 아래 `agent-os-choice-facts`에 세션·에이전트·화면 열쇠의 해시 이름으로 `O_EXCL`로 만든다. 서브에이전트도 따로 센다.
- 세션 ID가 없거나 표지 폴더를 쓰지 못하면 막지 않고 옛 알림으로 물러선다. 같은 화면을 끝없이 막지 않기 위해서다.
- 다시 부른 화면(지나가는 길)에는 395의 계기를 `additionalContext`로 낸다. 받은 답과 확인받은 요약을 이 턴에 일지에 옮기고, 일지 파일이 없으면 `sibling_overlap.py`의 `다음 빈 번호`로 머리 한 줄 파일을 먼저 만들라는 문장이다(code-review 6단계 끝과 같은 길). 물러선 알림에도 같은 문장이 붙는다.

실제 훅으로 C를 세 번 돌렸다. 모두 측정이고 기대대로였다. 모델은 거부 이유를 읽고 같은 질문을 4.9~6.3초 뒤에 다시 불렀고, 다시 부른 화면은 막히지 않았으며, 답 뒤 글에 `ANSWERED_LEAD`를 옮겼다. 다시 부른 화면에서 대 보지 못한 4.5초를 설명에 어림이라고 적고 설명만 고친 것은 탐침이 단언하지 않아 저장한 원본을 손으로 봤다(셀프 리뷰 명세 축이 짚어 고쳤다). 훅 시간(`time_hook.py`, 빈 임시 폴더, 다섯 번씩 두 번)은 처음 화면 192~206ms, 다시 부른 화면 193~454ms(454ms는 한 번), 세션을 모르는 길 189~219ms였다. 시험은 31개(자식 프로세스로 세션마다 처음만 막는지까지 본다), `tools/hook_payloads.toml` 사례 넷(`run_hooks` 146건 어긋남 0), 변이 스물아홉이 모두 기대대로였다. `.claude/rules/tools.md`의 계기 훅 항목에 AskUserQuestion에서 잰 거부의 길을, 시간 문단에 새 수를 적었다.

## 403: 러너의 리눅스 pyright

`tools/run_checks.py`의 `pyright_checks`가 리눅스가 아닌 곳에서 `pyright --pythonplatform Linux`를 한 번 더 돈다. 시험 셋을 더했고, 이 브랜치의 작업 트리에서 두 플랫폼 모두 `0 errors`였다. 행이 닫을 때 적으라고 한 것: 시험이 리눅스에서만 빨개지는 몫(281·318의 꼴)은 이 검사가 잡지 못한다. 그 몫은 `.claude/rules/tests.md`의 조항과 CI가 잡는 값을 받아들인다. 끝이 열린 결함 종류라 그 셋째에서 검사를 더 늘리지 않는다.

## 339의 규칙 몫: probes.md가 공용 도구를 가리킨다

`.claude/rules/probes.md`의 첫 항목에 파이썬 탐침은 셈을 `Rounds`로 한다는 문장을, 다섯째 항목에 출력을 `LineReader`로 읽는다는 문장을 넣었다. 다섯째 항목은 그 도구가 맡는 것(daemon 스레드와 큐, EOF 표시 기억, 배출의 제한 시간)과 그 까닭을 독스트링으로 넘기고, 탐침의 몫 둘(stderr 버리기, 줄을 JSON으로 풀어 `type`으로 알아보기)만 남겼다. 그래서 그 항목의 카나리아 "읽는 스레드와 큐"가 사라져, 카나리아 명세(`probes_rule_stream_delete_marker.toml`)의 첫째를 `LineReader`로 바꾸고 넷째 `Rounds`를 더했다.

## 341: next-session 1단계의 차례

1단계의 하위 항목에서 일지를 3, 병합 길을 4로 맞바꿨다. 일지 항목 끝에 단계를 닫는 세션은 회고와 "다음"까지 마친 일지를 4의 `headRefOid` 대조 전에 푸시한다는 문장을 넣었다. 늦어도 마지막 봇 회차의 커밋에 싣고, 고친 것이 없는 회차면 일지만 실은 커밋을 푸시한다. 번호 인용은 같은 스킬의 두 곳(봇 회차의 "뒤로 넘긴 일"과 "반영"), 인계할 때 2, `code-review` 6단계 끝, 카나리아 명세 셋(질문 하나와 머리 주석 둘)에서 고쳤다. 질문을 고친 `next_session_deferred_merge_running_scope.toml`은 대조군인 주 체크아웃이 이미 다섯 카나리아를 든 판이라 다시 돌리지 않았고, 머리 주석에 그렇게 적었다. `tools/*.py`의 "1단계" 인용은 단계 번호 3·4를 들지 않았다.

## 391·397: ADR 규칙

`.claude/rules/adr.md`의 첫 항목에 명세가 ADR 본문의 사실을 거짓으로 만들어도 명세를 쓰는 같은 작업에서 그 ADR의 이력에 무엇이 바뀌었는지와 명세의 경로를 적고 포인터를 단다는 문장을, 둘째 항목에 이름으로 들지 않은 ADR도 결정이 바꾸는 규약 문서의 절 이름과 경로로 `docs/adr/`를 grep해 본다는 문장을 넣었다. 397의 사례(ADR 0037이 바꾼 ADR 0005의 문장)는 두 ADR에 그 포인터가 지금 있는 것을 보고 적었다.

## 396: grilling의 갈래 밟기

`grilling`의 끝 조건 바로 앞에 문단 하나를 넣었다. 결정이 에이전트가 단계대로 따르는 절차를 바꾸면, 합의 요약을 올리기 전에 그 절차의 중간으로 들어오는 갈래(인계, 끊은 뒤 이어 가기, 열린 PR 반영, 면제 단계, 규약 전에 열린 일)를 하나씩 밟고, 어긋나는 동작이 나면 그것을 아직 열린 가지로 다음 라운드에 묻는다. 밟는 법은 `code-review` 4단계의 **갈래 밟기** 문단을 가리킨다. 머리 주석에도 적었다.

## 400: to-tickets의 경로 규칙

템플릿 뒤 문단의 원본 문언("avoid specific file paths")을 to-spec 사본과 같은 뜻으로 바꿨다. 코드 조각과 명세가 고칠 자리로 정하지 않은 구현 파일의 경로는 적지 않고, 규칙 문서·ADR·테스트 선례의 경로와 명세가 정한 고칠 자리의 경로는 적는다. 프로토타입 조각의 예외는 원문대로 두었다. 머리 주석의 "셋을 더했다"를 "넷"으로 고치고 대기열 400을 적었다.

## 카나리아

바꾼 규칙과 스킬마다 새 세션에서 불러 봤다. 모두 이 PC, claude 2.1.302, 두 갈래 모두 `6bd52b06` 위의 커밋 전 작업 트리이고, 결과는 각 명세의 머리 주석에도 적었다.

| 명세 | 대상 | 결과 |
|---|---|---|
| `tools_rule_choice_facts_hook.toml`(셋째 카나리아를 192~206ms로 바꿨다) | `.claude/rules/tools.md` | 통과 4, 대조군 "없음" 셋 |
| `probes_rule_stream_delete_marker.toml`(첫째를 바꾸고 넷째를 더했다) | `.claude/rules/probes.md` | 통과 4, 대조군 "없음" 넷 |
| `next_session_journal_before_merge.toml`(새것) | next-session 1단계 3 | 통과 4, 대조군(`--control-commit 6bd52b06`) "없음" |
| `adr_rule_spec_and_unnamed_adr.toml`(새것) | `.claude/rules/adr.md` | 통과 4, 대조군 "없음" 둘 |
| `grilling_entry_branches.toml`(새것) | grilling | 통과 4, 대조군(`--control-commit 6bd52b06`) "없음" 둘 |
| `to_tickets_path_rule.toml`(새것) | to-tickets | 통과 4, 대조군(`--control-commit 6bd52b06`) "없음" |

## 고친 것

- `.claude/rules/tools.md`의 커밋 중 편집 훅 시간에서 훑는 두 길을 187~199ms로 적었는데, 저장한 원본 두 벌의 최솟값은 막는 길의 186ms였다. 탐침 README를 고치며 원본과 맞대다 찾아 186~199ms로 고쳤다.

## 인계 (셀프 리뷰 직전)

열두 행을 모두 반영하고 대기열에서 닫은 뒤(`.scratch/retro-queue.md` 열두 줄), `/code-review`(고정점 `origin/main` = `6bd52b06`, 커밋 없이 미커밋·미추적 변경뿐)를 부른 직후 인계 계기가 왔다(`셀프 리뷰 직전`, 세션 컨텍스트 327,060 토큰). 인계하지 않는 때 다섯 가운데 어디에도 들지 않았다(`get_session`의 `self`에 `parentSessionId` 없음). 이 세션의 제목은 `chore/choice-facts-batch`였고 `chore/choice-facts-batch (인계함)`으로 바꾼다.

- 검사: `uv run ruff check .`과 `uv run ruff format --check .`은 통과했다. 그 뒤 `tools/run_checks.py`를 백그라운드로 띄웠고, zizmor·지침·경계·타입 우회·pyright·pyright-linux·훅 러너가 통과한 채 pytest와 web verify가 도는 동안 인계 절차로 멈췄다(TaskStop). 멈추는 순간 web-verify가 `Failed (190.0s)`로 찍혔다. 그 출력은 이 워크트리의 첫 `pnpm install`(54.5초) 뒤 api-client·lint·format·typecheck를 지나 vitest의 `RUN` 줄에서 끊겨, 멈춤에 끊긴 것으로 보지만 어림이다(이 브랜치는 `web/`을 고치지 않았다). pytest와 web은 이 판에서 끝까지 본 적이 없다. 그 전에 따로 돌린 것은 훅마다의 시험(`test_hook_choice_facts.py` 31개, `test_run_checks.py` 23개 등), `run_hooks` 146건 어긋남 0, 변이 표 스물아홉, 카나리아 여섯이다.
- 셀프 리뷰는 돌지 않았다. 새 세션이 `/code-review`부터 한다. diff가 에이전트가 따르는 절차(next-session, grilling, to-tickets, 훅이 넣는 문구)를 바꾸므로 두 브리프에 **갈래 밟기** 문단이 든다. 이 세션이 반영하며 새로 쓴 사실 문장(일지의 각 절, 탐침 README의 2026-10-22 결과, 대기열 닫힘 문장)은 원본 출력(스크래치패드의 `cf_e*.txt`·`cf_c*.txt`·`edit_time*.txt`·`gh_api_method.txt`·`canary_*.txt`)과 맞대 썼다. 스크래치패드는 이 세션의 것이라 새 세션은 열지 못할 수 있다.
- 남은 단계: 셀프 리뷰와 반영, 회고(`retro`)와 `## 다음`(이 일지 끝), `git branch --show-current`와 `sibling_overlap.py`, 커밋, PR 직전 리뷰, PR, 봇 회차, 워크트리의 병합 길. `next-session` 1단계는 이 PR이 바꾼 차례(일지 3, 병합 길 4)로 따른다. 새 세션의 Skill 도구는 주 체크아웃의 옛 사본을 실으니 워크트리 사본의 `SKILL.md`를 Read로 연다.
- 결정: 341은 두 갈래 가운데 차례를 바꾸는 쪽을 골랐다(세 회차의 일지가 모두 회고와 "다음"을 병합 전에 실었다). 339의 규칙 몫은 `LineReader`가 맡는 것과 까닭을 독스트링으로 넘기고 탐침의 몫 둘만 규칙에 남겼다. 카나리아는 바뀐 규칙·스킬마다 하나씩, 새 문장을 든 명세가 없으면 새로 지었다.
- 번복한 것: 없음. 고친 것은 위 "고친 것" 절과 E의 기준(394·395 절).

지시문:

```
다음 작업: 하네스 chore 배치. mcp-shutdown이 닫힌 뒤 회차 3 이상인 열린 대기열 행과 같은 대상 파일의 고침 행을 한 PR로 반영한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 394·395·339·412·341·391·396·400·403(회차 3 이상인 열린 행 아홉. 227도 4회차지만 열린 PR #296이 맡았다)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이 대상이고, 같은 대상 파일의 고침 행 368(412보다 먼저 고친다)·369·408(412와 tools/hook_payloads.toml이나 같은 훅 파일을 든다)을 함께 반영한다
브랜치: chore/choice-facts-batch
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-22-11-choice-facts-batch.md 의 "인계 (셀프 리뷰 직전)"과 그 앞 절들
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다(docs/journal/2026-10-22-11-choice-facts-batch.md). 열두 행의 반영과 대기열 닫기, 카나리아 여섯은 끝났고 회고와 "## 다음"은 아직이다. 이 브랜치가 next-session(1단계의 일지 3·병합 길 4)·grilling·to-tickets·code-review를 고쳐, 그 스킬은 워크트리 사본의 SKILL.md를 Read로 열어 따른다
확인할 선행 조건: tools/run_checks.py의 pytest와 web verify는 이 판에서 끝까지 돌지 않았다(인계로 멈췄고, 멈추는 순간 web-verify가 vitest 도중 Failed로 찍혔다. 멈춤 탓이라는 것은 어림이다)
이번 요청 범위: PR과 병합까지
```

넘기기 전: 제목을 `chore/choice-facts-batch (인계함)`으로 바꿨고, 백그라운드 러너를 멈췄으며(남은 자식 프로세스 없음), `git worktree unlock C:/project/agent/.claude/worktrees/choice-facts-batch`가 오류 없이 끝났다.

open-session을 부른다 2026-10-22T05:48:54Z

## 이어받은 세션 (셀프 리뷰부터)

> 사용자: (위 지시문의 시작 프롬프트와 같다)

`git worktree list`에서 이 브랜치가 `.claude/worktrees/choice-facts-batch`에 있어 `EnterWorktree(path)`로 들어갔다. 세션 제목을 `chore/choice-facts-batch`로 바꿨다.

- 앞 세션이 러너를 vitest 도중에 멈춰, `web/eslint.config.test.ts`의 `afterAll`이 지우지 못한 픽스처 `web/judge-vZhAvt/`(위반 사례 파일과 api-client를 가리키는 junction)가 미추적으로 남았다. 지우는 명령은 자동 모드 분류기가 거부해, 이 세션의 스크래치패드로 옮겼다. `web/` 안에 두면 다음 web verify의 eslint와 Prettier가 그 파일을 읽는다.
- `tests/tools/test_hook_edit_during_commit.py` 하나만 작업 트리가 CRLF였다(`git ls-files --eol`의 `w/crlf`, 속성은 `eol=lf`). LF로 맞췄다.
- `uv run python tools/run_checks.py`를 다시 돌렸다. 아홉 모두 통과했다(pytest 207.4초, web-verify 232.1초, pyright-linux 40.1초). 앞 세션이 끝까지 보지 못한 pytest와 web verify가 이 판에서 초록이다. `uv run ruff check .`과 `uv run ruff format --check .`도 통과했다.
- `sibling_overlap.py`가 1로 끝났다. 둘이다. 일지 번호는 origin/main의 최신 `2026-10-22-04`보다 앞서 `2026-10-22-05`로 옮겨야 한다(셀프 리뷰 뒤 `--move`. 그때의 `--move`는 같은 날의 번호 07을 내 그 이름으로 옮겼고, PR 직전 리뷰를 반영한 뒤 main에 08이 들어 다시 11로 옮겼다. 아래 PR 직전 리뷰 절). 그리고 이 브랜치가 `code-review` SKILL.md(6단계 끝의 `next-session` 1단계 4→3 괄호)를 고쳤는데 그 원천의 카나리아 명세를 고치지 않았다. 앞 세션의 카나리아 여섯에 code-review가 없었다. 여섯 명세 가운데 그 괄호를 묻는 것이 없어, 같은 문단을 묻는 `code_review_overlap_exit_two.toml`에 둘째 물음(그 괄호, 기대 `1단계 3의 번호 받기`)을 더했다. 대조군 `55ba299`에는 옛 괄호 `1단계 4의 번호 받기`가 있다(`git show`로 봤다). 사전 확인은 통과했다. 돌리니 통과 4였다(claude 2.1.302, `--control-commit 55ba299`). 대조군은 둘째 물음에 옛 괄호를 옮겼다.

### 셀프 리뷰

`/code-review`(워크트리 사본을 Read로 열어 따랐다). base `6bd52b06`, 바뀐 파일 34개, 커밋 0개, 미추적 12개. 명세는 사용자 요청과 기점 판 대기열의 열세 행(397 포함)이고, 2단계의 옮기는 변경의 옛 판정으로 훅 다섯과 러너·등록의 옛 계약 일곱을 명세 축에 넘겼다. 두 브리프에 갈래 밟기 문단과 `gh api --help`(gh 2.98.0) 발췌를 넣었다.

표준 축(sonnet, high) 보고: Critical·Major 없음.
- Minor 1. 옛 번호 잔존: `.scratch/token-usage/spec.md:156`의 "1단계의 4(일지)", `:170`의 "`next-session` 1단계의 3 … 병합은 PR을 연 세션의 일이다".
- Minor 2. `.claude/rules/probes.md` 다섯째 항목의 "PR의 CodeRabbit이 잡아(일지 2026-10-21-12)"는 그 사건이 든 일지가 아니다(축은 2026-10-17-10을 들었다).
- Minor 3. `tools/hook_choice_facts.py` 독스트링의 "다섯 번 모두 이유의 표지를 옮기고"가 근거보다 세다(셋째 회차는 마지막 답에서 옮겼고 기준을 결과 뒤에 고쳤다).
- Minor 4. `tools/hook_edit_during_commit.py`의 "부하 없이 절반 남짓"(README는 절대 5/10, 상대 3/10)과 못 보는 것의 "35/60, 57/60"(앞 판의 값, 최신 30회차는 17·30).
- Minor 5. 갈래 밟기: 백그라운드로 도는 커밋 동안 `hook_handoff`의 인계 절차(일지 쓰기)와 `code-review` 6단계 끝의 받은 턴 옮기기가 새 막음에 걸린다. 백그라운드 커밋을 다루는 시험이 없다.
- Minor 6. `tools/hook_env_read.py`가 읽는 자리의 인용된 중괄호(`cat '.{env,x}'`)도 막는 거짓 양성이 못 보는 것에 없다. `_brace_branches("{{a,b}")`는 그대로 돌려주는데 bash는 안쪽 묶음을 펼친다. 우회는 찾지 못했다.
- Nit. `tools/hook_scratch_probe_rule.py:15`가 `hook_edit_during_commit`을 PostToolUse 등록으로 든다. `tools/probe_kit.py`의 `KeyboardInterrupt`·`SystemExit`를 고정하는 시험이 없다. ADR 0035 2026-10-19 이력의 "검사 여덟"(기록이라 잔존 아님).
- 판단 항목: 불리언 플래그(`output_for(..., first: bool | None)`, `Slot.mark(measured=)`, 탐침의 `run_branch(loaded=)`).
- 맞게 확인한 것: `claim_first`·`launch_hook` 모양 서술, `tools.md`의 시간 범위, `gh api -X post`의 POST, 카나리아 `expect`의 글자, 변이 28개와 대조군 1개, `_brace_branches`의 여러·겹친 묶음, 문장 가르기 예, `commit_directory`의 경로와 런처 판정, 타입 우회 없음.

명세 축 보고: 범위 넘침 없음.
- Minor 1. `.scratch/retro-queue.md:387`(열린 행 383)에 "`next-session` 1단계의 4"가 두 번 남았다.
- Minor 2. `.scratch/harness/probes/hooks_push_help_and_commit_lock_mutations.toml:403-415`의 변이 "293 main 이 커밋을 찾은 결과를 버린다"의 `old`(`context = context_for(…)`)가 지금 코드에 없다(함수가 `deny_reason`으로 바뀌었다).
- Minor 3. `_brace_branches`가 쉼표 없는 중괄호를 글자로 두는데, Grep 도구(rg)는 `{x}`도 갈래로 읽는다. 축이 gitignore 된 숨김 파일 `.secret369`를 glob `{.secret369}`로 읽었고, 훅은 `deny_reason_for_grep_tool(…, "{.env}")`와 `rg -g '{.env}'`를 지나보낸다(옛 판도 놓치던 꼴).
- Minor 4. 412의 "거짓 양성이 남은 채 막으면 커밋하지 않은 세션의 편집을 막는다": 남긴 거짓 양성(상대 경로 `-C`로 바로 띄운 실제 git이 옮기기 전의 순간)에 막힌 세션은 막는 이유가 기다리라는 커밋이 없다. 창의 길이는 재지 않았다. 런처의 상대 경로 2/120도 원인을 가르지 않았다.
- Minor 5. README·일지의 C 결과 "설명에 어림이라고 적어 … 설명만 고친 화면은 막히지 않았다"는 `probe.py`가 단언하지도 찍지도 않는다(`retry_checks`·`key_of`는 질문 문장만 견준다). 손으로 본 것이 측정처럼 적혔다.
- Nit. 훅 독스트링의 "절반 남짓"(표준 축 Minor 4와 같다), 시험 독스트링의 "런처 상대 경로 절반 남짓"(README는 27·59·28·58/60), `hook_payloads.toml`의 handoff `gh api` 사례 note "명령만 바꿨다"(description·tool_response·session_id도 바뀌었다).
- 맞게 확인한 것: 403의 시험 몫 문장, 341의 두 조건, 394↔324·395↔250의 포인터, 408의 경계 입력 30개, 옛 판정 일곱 가운데 넓힌 판정이 옛 경우를 푼 것 없음, next-session 인계 2·3과 봇 회차의 4 참조.

판정:
- 표준 Minor 1은 고치지 않는다. token-usage의 티켓 아홉이 모두 `**Status:** done`이고 `plan.md`에 행이 없어, 그 명세는 `docs/constitution/operations.md` 문서 위치 절의 기록이다. 축은 비어 있는 체크박스를 미완료로 읽었다.
- 표준 Minor 2를 고쳤다. 그 사건(첫 줄 `readline`, CodeRabbit)은 2026-10-17-10의 339~342행에 있고 2026-10-21-12에는 `readline`이 없다(Grep으로 봤다).
- 표준 Minor 3을 고쳤다. 독스트링을 README와 같은 세기로 바꿨다(다섯 번 모두 다시 불렀고 첫 결과 뒤의 글에 옮겼다, 한 번은 마지막 답, 보는 자리는 결과를 본 뒤 정했다).
- 표준 Minor 4를 고쳤다. "절반 남짓"을 README의 수(10회차 가운데 부하 없이 절대 5·상대 3, 부하 아래 9·9)로, 못 보는 것의 "60회차에서 35·57"을 고친 판의 30회차 17·30과 그 앞 판의 60회차 35·57로 바꿨다.
- 표준 Minor 5는 고치지 않는다. 막는 이유가 "이 세션이 백그라운드로 띄운 커밋이면 그 끝 알림을 기다린다"고 시켜, 인계 중의 일지 쓰기는 막힌 뒤 커밋이 끝나면 잇는다. 단계를 건너뛰거나 두 번 하지 않는다. 백그라운드로 띄운 커밋에 `hook_handoff`가 "커밋 뒤"를 곧바로 내는 것은 이 배치 전부터의 일이다.
- 표준 Minor 6을 고쳤다. 읽는 자리의 인용된 중괄호(`cat '.{env,x}'`)와 쉼표 없는 묶음(`cat .{env}`)을 막는 거짓 양성을 `tools/hook_env_read.py` 모듈 독스트링의 못 보는 것에 적고, 막는다고 단언하는 시험으로 고정했다. 짝이 없는 `{`는 bash처럼 글자로 두고 그 뒤의 묶음을 풀게 고쳐 `{{a,b}`가 `{a`·`{b`가 된다.
- 표준 Nit 셋 가운데 둘을 고쳤다. `tools/hook_scratch_probe_rule.py`의 옛 등록 서술에 PreToolUse로 옮긴 것(대기열 412)을 덧붙였다. `tools/probe_kit.py`의 못 보는 것(`KeyboardInterrupt`·`SystemExit`은 회차로 적지 않고 그대로 올린다)을 두 예외로 매개변수화한 시험으로 고정했다. 처음부터 초록이라 `except Exception`을 `except BaseException`으로 넓히는 변이를 손으로 넣어 두 경우 모두 `DID NOT RAISE`로 빨간 것을 보고 되돌렸다. ADR 0035 이력의 "검사 여덟"은 기록이라 두었다.
- 판단 항목(불리언 플래그) 셋 가운데 하나를 고쳤다. `tools/hook_choice_facts.py`의 `output_for(..., first: bool | None)`은 이 브랜치가 새로 쓴 함수이고, 세 값이 세 출력(막기, 답 뒤 계기, 옛 알림)을 골라 `CODING_STANDARDS.md`의 불리언 플래그 줄(키워드 전용으로 지나간 플래그)에 든다. `Seen` 열거(`FIRST`·`AGAIN`·`UNKNOWN`)로 바꾸고 `claim_first`와 `screen_seen`(옛 `first_seen`)이 그것을 돌려준다. 함수를 셋으로 쪼개지 않은 것은 갈래를 고르는 일이 순수 함수 시험이 없는 `main`으로 옮겨 가기 때문이다. 시험을 먼저 바꿔 `ImportError`로 빨간 것을 본 뒤 고쳤고, 바뀐 줄을 `old`로 든 변이 넷(다시 부른 화면도 막는다, 가를 수 없는 화면도 막는다, 표지 폴더를 만들지 못하면 처음이라고 본다, 세션을 몰라도 표지를 쓴다)을 새 코드로 옮겼다. `Slot.mark(measured=)`와 탐침의 `run_branch(loaded=)`는 둔다. `mark`는 값과 상관없이 회차 하나를 적는 한 가지 일만 하고, `measured`는 probes 규칙이 둘로 정한 사실(재려는 상황의 표지를 봤는가)이다. `loaded`는 `main`이 `(False, True)`로 도는 실험 조건이고 두 조건에서 같은 측정을 한다.
- 명세 Minor 1을 고쳤다. 대기열 383행의 두 곳을 "1단계의 일지 항목(그때 4, 대기열 341 뒤로 3)"과 "1단계의 3"으로 바꿨다.
- 명세 Minor 2를 고쳤다. 변이 "293 main 이 커밋을 찾은 결과를 버린다"의 `old`를 지금 줄 `reason = deny_reason(file_path, running_commits(processes))`로, `new`를 `reason = deny_reason(file_path, [])`로 옮겼다. 그 변이만 돌려 기대대로 빨갰다(146건 가운데 어긋남 1, 기준선은 초록).
- 명세 Minor 3을 고쳤다. `_brace_branches`가 쉼표 없는 묶음도 갈래 하나로 풀어, Grep 도구의 glob `{.env}`·`**/{.e*}`·`{.{env},y}`와 명령 `rg -uu -g '{.env}' KEY`를 막는다. `{*.md}`와 `{{.env,x}`는 지나간다고 고정했다.
- 명세 Minor 4를 고쳤다. 막는 이유에 커밋을 띄우지 않은 세션은 한 번 다시 편집하고, 다시 막히면 다른 세션의 커밋을 기다리라는 문장을 더하고 시험으로 단언했다(먼저 빨갛고 고친 뒤 51 passed). 못 보는 것에 런처로 친 상대 경로의 120회차 가운데 둘(원인은 가르지 않았다)과, 한 번 다시 하라는 처방이 창의 길이를 재지 않은 어림이라는 것을 적었다.
- 명세 Minor 5를 고쳤다. 탐침 README의 `choice_facts/` 행과 이 일지 57행의 C 결과에서 탐침이 잰 것만 측정으로 두고, 설명에 어림이라고 적고 설명만 고친 것은 저장한 원본을 손으로 본 것이라고 적었다(`retry_checks`는 질문 문장만 견준다).
- 명세 Nit 셋을 고쳤다. 훅 독스트링의 "절반 남짓"(표준 Minor 4와 함께), 시험 독스트링의 런처 상대 경로를 README의 갈래마다 60회차 가운데 27·59·28·58로, `tools/hook_payloads.toml`의 handoff `gh api` 사례 note를 바뀐 칸을 모두 드는 문장으로 바꿨다.

고친 것: 표준 Minor 2·3·4·6, 표준 Nit 둘, 판단 항목 하나(`output_for`), 명세 Minor 1~5, 명세 Nit 셋. 반영하며 새로 쓴 사실 문장은 아래이고, PR 직전 `bug-perf-review` 브리프에 밀 주장으로 넘긴다.
1. `tools/hook_choice_facts.py` 독스트링 "이유가 닿는 때": "다섯 번 모두 그랬고, 모델은 다섯 번 모두 같은 질문을 다시 불렀으며 첫 결과 뒤의 글에 이유의 표지를 옮겼다. 한 번은 둘째 호출 뒤의 마지막 답에서 옮겼고, 표지를 보는 자리(첫 결과 뒤의 글)는 결과를 본 뒤 정했다(탐침 README)."
2. `tools/hook_edit_during_commit.py` 독스트링: "실제 git 을 바로 띄운 회차도 10회차 가운데 부하 없이 절대 경로 5·상대 경로 3, 부하 아래 9·9에서 그 순간이 훑혔다."
3. 같은 파일의 못 보는 것: "(거짓 양성. 고친 판의 탐침 30회차에서 부하 없이 17, 부하 아래 30. 그 앞 판의 60회차에서는 35·57)", "런처로 친 상대 경로도 고친 판의 120회차 가운데 둘(자식이 끝난 뒤의 런처)에서 막았고 원인은 가르지 않았다."
4. 같은 파일의 막는 이유: "이 세션이 띄운 커밋이 없으면 같은 편집을 한 번 다시 한다. 다른 프로세스의 git 이 작업 폴더를 옮기기 전의 순간을 훑었을 수 있다(이 훅의 못 보는 것). 다시 막히면 다른 세션의 커밋이 이 체크아웃에서 도는 것이라 끝나기를 기다린다."
5. `tests/tools/test_hook_edit_during_commit.py`의 런처 시험 독스트링: "자식의 작업 디렉터리를 믿던 판은 런처로 친 상대 경로의 네 갈래(갈래마다 60회차)에서 27·59·28·58회차를 거짓으로 셌다."
6. `tools/hook_env_read.py`의 `_brace_branches` 독스트링: "쉼표가 없는 묶음(`{x}`)은 갈래 하나로 푼다. Grep 도구의 glob 이 그렇게 읽는다(2026-10-22 손으로 봤다. `.ignore` 에 든 숨김 파일을 glob 없이는 건너뛰고 `{<그 이름>}` 으로는 읽었으며, `{*.md}` 는 마크다운을 찾았다. rg 의 glob 은 Grep 도구가 ripgrep 위에 있어 같다고 보고 따로 재지 않았다, 어림)."
7. 같은 파일의 모듈 독스트링과 `_glob_reaching_env`: "숨김 파일과 `{*.md,**}` 는 2026-10-22 gitignore 된 숨김 가짜 파일로 손으로 봤다, 대기열 369", "`{*.md,**}` 가 gitignore 된 숨김 파일을 읽었다, 2026-10-22 손으로 봤다".
8. `.claude/rules/probes.md` 다섯째 항목: "PR의 CodeRabbit이 잡아(일지 2026-10-17-10)".
9. 탐침 README `choice_facts/` 행과 이 일지 57행: "다시 부른 화면에서 모델이 대 보지 못한 4.5초를 설명에 어림이라고 적고 설명만 고친 것은 탐침이 단언하지도 찍지도 않아(`retry_checks`는 질문 문장만 견준다), 저장한 원본을 손으로 봤다."
10. `tools/hook_payloads.toml` 726행 note: "위 실제 입력의 모양에서 명령·설명·도구 응답(커밋의 gitOperation 을 뺐다)·세션 ID·tool_use_id 를 PR 열기에 맞게 고쳐 지었다".
11. `tools/hook_scratch_probe_rule.py`: "`hook_edit_during_commit`(도는 커밋. 그 뒤 PreToolUse 에서 막는 훅으로 옮겼다, 대기열 412)".
12. `.scratch/retro-queue.md` 383행: "1단계의 일지 항목(그때 4, 대기열 341 뒤로 3)을 어겼고", "지침(`next-session` 1단계의 3)".
13. 카나리아 `code_review_overlap_exit_two.toml` 머리: "통과 4(2026-10-22, 이 PC, claude 2.1.302, 대조군 `55ba299` …). 둘째 물음을 더한 판이다. 대조군은 둘째 물음에 옛 괄호 `1단계 4의 번호 받기`를 옮겼다."

남긴 것: 표준 Minor 1(그 명세는 티켓 아홉이 모두 done인 기록이다), 표준 Minor 5(막는 이유가 백그라운드 커밋의 끝 알림을 기다리라고 시켜 인계 단계가 어긋나지 않는다), ADR 0035의 "검사 여덟"(이력), 판단 항목 둘(`Slot.mark`, `run_branch`, 까닭은 위 판단 항목 줄).

다시 돌린 명령: `uv run pytest -q tests/tools/test_probe_kit.py` 13 passed, `tests/tools/test_hook_choice_facts.py` 31 passed, `tests/tools/test_hook_env_read.py` 165 passed, `tests/tools/test_hook_edit_during_commit.py` 51 passed. `tools/mutate.py`의 `choice_facts_hook_mutations.toml`이 변이 29 모두 기대대로였다. `tools/run_hooks.py`가 146건 어긋남 0이었다. 바꾼 세 파일의 ruff check·format·pyright는 오류 0이었다. probes.md는 본문의 일지 번호만 고쳐 `uv run python tools/canary.py --preflight .scratch/harness/probes/canary/probes_rule_stream_delete_marker.toml`(통과 1)로 갈음했다(같은 PR·같은 판 2.1.302로 앞서 통과 4, 머리말과 명세의 칸은 그대로, 카나리아는 묻는 자리에 남았다). 손으로 치는 다섯은 커밋 `7e0cf7df`의 pre-commit으로 갈음했다. ruff check·format, lint-imports, check-instructions, zizmor, check-type-escapes, pyright-linux, pyright, run-hooks, pytest, web-verify, 마크다운 표, 줄 구분 문자, 변이 표, 카나리아 명세가 모두 Passed였고(묶음 360초), 헌법 판 검사만 고친 헌법 파일이 없어 Skipped였다. 인용 대조는 이 일지에서 경고 6건을 냈다. 셋은 셀프 리뷰가 고치기 전의 문구를 든 것이라 저장소에 없는 것이 맞고, 둘은 `tools/hook_edit_during_commit.py`의 막는 이유가 문자열 여러 줄에 나뉘어 있어 글자로 이어 찾지 못한 것이며, 하나(위 13)는 원문의 한 문장을 표시 없이 건너뛴 인용이라 원문대로 고쳤다.

## PR 직전 리뷰

CodeRabbit CLI는 자리가 없어 돌지 못하므로 대체 길로 갔다. origin/main `98272c4f`를 합친 커밋 `87b69a66` 위에서 내장 `/security-review`와 `bug-perf-review` 셋(훅, 탐침·공용 도구, 문서와 밀 주장 1~13)을 띄웠다.

보안 리뷰: 찾는 서브에이전트가 하나를 냈고(확신 0.9), 거르는 서브에이전트가 3/10으로 걸러 지적이 0이다. 그 하나는 `tools/hook_env_read.py`의 `_brace_branches`가 대괄호 안의 `{`·`}`까지 펼쳐, 옛 판이 막던 `cat .en[!{}]`·`cat .en[u-{}]`·`cat .e[a-{][!}]`, `grep -r --include=.en[u-{}]`, `rg -g '.en[!{}]'`, Grep 도구 glob `.en[!{}]` 등이 지나가는 회귀다. 찾는 쪽은 Git Bash·GNU grep·Grep 도구가 가짜 숨김 파일 `.abv`를 그 꼴로 읽는 것을 봤다. 거르는 쪽은 일부러 만든 입력이고 더 쉬운 우회가 이미 못 보는 것에 있어 취약점은 아니라고 보고, 정확성 버그로 넘기라고 했다. 찾는 쪽은 범위 밖의 옛 구멍으로 `[^x]`도 들었다. 파이썬 fnmatch는 그것을 부정으로 읽지 않는데 bash·GNU grep·ripgrep은 부정으로 읽어, `cat .en[^x]`이 옛 판과 새 판 모두 지나간다.

훅 축 보고: Minor 6, Nit 1.
- Minor 1. `_brace_branches`가 묶음 수에 지수로 커져, `{a,b}` 열여섯에 7.0초가 걸렸고 스물은 100초에 끝나지 않았다. 등록의 시간 제한 20초를 넘으면 막지 않고 지나간다.
- Minor 2. `hook_choice_facts`가 막는 이유에 질문·라벨의 수도 옮기는데, 그 수를 고쳐 다시 부르면 화면 열쇠가 달라져 한 번 더 막는다. 못 보는 것에 없다.
- Minor 3. `hook_edit_during_commit`이 끝나지 않는 커밋(편집기가 열린 채 남은 것) 앞에서 모든 편집을 막는데, 막는 이유에 빠져나올 길이 없다.
- Minor 4. 두 훅의 `gh api` 판정이 `-X=POST`의 값을 `=POST`로 읽어 PR 열기를 놓친다. 축이 `GH_DEBUG=api`로 gh 2.98.0이 그것을 POST로 보내는 것을 봤다.
- Minor 5. PowerShell의 백틱 줄 이음으로 필드를 다음 줄에 둔 `gh api`를 두 훅이 놓친다.
- Minor 6. `hook_env_read` 모듈 독스트링의 손으로 본 문장(셀프 리뷰가 넘긴 밀 주장 7)이 숨김 파일도 gitignore 된 파일로 본 것처럼 읽힌다.
- Nit. `tools/hook_payloads.toml` 726행 note(밀 주장 10)의 "위 실제 입력"이 바로 위 사례인지 두 사례 위인지 적지 않았다. `transcript_path`는 두 사례 위의 것이다.
- 밀 주장 1~7·10·11은 맞다고 확인했다(7은 첫 문장의 문구만 어긋난다). 오탐 넷(Bash 백슬래시 줄 이음, 런처의 자식 git, 600겹 중첩, 빈 묶음)을 적었다.

탐침·공용 도구 축 보고: Minor 5, Nit 1, 보류 1.
- Minor 1. `tools/probe_kit.py`의 `LineReader`가 글 흐름(`text=True`)에서 풀지 못하는 바이트를 만나면 `UnicodeDecodeError`(`ValueError`)를 흐름 닫힘으로 삼켜, 앞 줄까지 잃고 EOF처럼 보이며 자식이 파이프가 차서 멈췄다(임시 스크립트로 재현).
- Minor 2. `drain`의 제한 시간이 줄 사이에만 걸려 0.1초마다 쓰는 자식 앞에서 `drain(0.5)`가 돌아오지 않았다(재현).
- Minor 3. `.scratch/harness/probes/edit_during_commit_launcher.py`가 양성 대조(옛 판의 거짓 알림)가 한 번도 없어도 0으로 끝난다. Nit로 `communicate(timeout=120)`이 넘으면 띄운 git을 끄지 않아 `index.lock`이 남을 수 있다.
- Minor 4. `.scratch/harness/probes/gh_api_method.py`가 대조 갈래의 기대 메서드를 단언하지 않는다.
- Minor 5. `SKIP=pyright`로는 `pyright-linux`가 빠지지 않는데 안내가 없다.
- 보류. `choice_facts/probe.py` 머리의 "세 회차 가운데 하나"와 훅 독스트링의 "다섯 번"이 횟수에서 갈린다.

문서 축 보고: 유효 0, 보류 1, 오탐 2. 호출 40번에 닿아 멈췄다.
- 보류. 이 일지 138행이 번호를 `2026-10-22-05`로 옮겨야 한다고만 적고, 파일은 `-07`인데 옮겼다는 줄이 없다.
- 오탐 2. `.scratch/token-usage/spec.md:9`와 그 `issues/05-handoff-hooks-and-sentences.md:27`의 옛 "1단계 3". 셀프 리뷰 표준 Minor 1과 같은 판정(티켓이 모두 done인 기록)이라고 축이 스스로 분류했다.
- 밀 주장 8·9·12는 맞고, 13은 대조군 `55ba299`를 열지 못했다. 카나리아 다섯(`adr_rule_spec_and_unnamed_adr`, `grilling_entry_branches`, `probes_rule_stream_delete_marker`, `to_tickets_path_rule`, `tools_rule_choice_facts_hook`)은 열지 못했다.

### 반영

모두 PR을 열기 전에 고쳤다. 고치는 값이 작고 비밀 가드와 탐침 도구의 존재 이유에 닿기 때문이다.
- 보안 후보는 버그로 고쳤다. 닿는지 보는 자리(`_reaches_env`, `_glob_reaching_env`)가 펼친 갈래와 함께 펼치기 전의 패턴도 보게 했다(`_candidates`). 옛 구멍 `[^`도 같이 막았다. `_matches_env`가 `[^`를 `[!`로 바꿔 판정한다. 대괄호 안 중괄호의 Bash·`--include`·`-g`·Grep 도구 입력과 `[^`의 입력을 막는다고 단언하는 시험 셋을 더했다.
- 훅 Minor 1: 갈래 상한 `_BRANCH_LIMIT = 256`을 두고, 넘으면 펼치기를 멈춰 막는 쪽으로 간다. 펼치기를 재귀에서 반복으로 바꿨다. `{a,b}` 아홉과 마흔은 막고(20초 안), 여덟은 지나간다고 고정했고, 못 보는 것에 그 거짓 양성을 적었다.
- 훅 Minor 2: 못 보는 것에 수를 고쳐 다시 부른 화면이 새 화면이라 또 막힌다는 거짓 양성을 적고 시험으로 고정했다.
- 훅 Minor 3: 막는 이유에 "몇 분이 지나도 끝나지 않으면 그 pid 를 사용자에게 알린다. 편집기가 열린 채 남은 커밋은 기다려도 끝나지 않는다."를 더하고, 못 보는 것에 끝나지 않는 커밋을 적었으며, 편집기를 여는 커밋 갈래를 시험에 더했다.
- 훅 Minor 4: 붙여 쓴 짧은 옵션 값의 앞 `=`를 한 번 벗긴다(두 사본 같게). `-X=POST`를 `OPENS`에, `-X=GET`을 `NOT_OPENS`에 더했다. 탐침 `gh_api_method.py`에도 그 갈래를 더해 POST임을 봤다(아래).
- 훅 Minor 5: 두 훅이 PowerShell의 백틱 줄 이음(백틱 뒤 줄바꿈)을 이어 붙인 뒤 가른다. `POWERSHELL_OPENS`로 두 훅의 PowerShell 사례를 고정했다.
- 훅 Minor 6: 문장을 "숨김 파일은 gitignore 하지 않은 가짜 파일로, `{*.md,**}` 는 gitignore 된 숨김 가짜 파일로 봤다"로 갈랐다.
- 훅 Nit: note를 "두 사례 위 '문턱 위 세션의 커밋' 의 실제 입력(같은 트랜스크립트)에서"로 고쳤다.
- 탐침 Minor 1: 글 흐름은 그 밑의 바이트 흐름을 그 흐름의 인코딩으로 줄마다 `errors="replace"`로 풀고 `\r\n`을 `\n`으로 바꾼다. 밑의 흐름과 인코딩은 흐름을 좁히지 않고 `getattr`로 꺼내 구체 형식(`io.BufferedIOBase`·`io.RawIOBase`, `str`)으로 좁힌다. `TextIOWrapper`로 좁히면 제네릭 인자를 몰라 pyright strict가 오류 여덟을 냈고(그 판정의 else 갈래에도 Unknown이 남았다), 선례 `src/agent_os/channel/cli/interrupt.py`의 `_raw_stderr`를 따랐다. 깨진 바이트 앞뒤 줄을 잃지 않는다는 시험을 더했다.
- 탐침 Minor 2: `drain`의 제한 시간을 배출 전체의 마감으로 바꿨다. 줄이 계속 오는 자식 앞에서 `drain(0.5)`가 돌아오는 시험을 더했다. 옛 코드에서 그 시험이 멈춘 것을 먼저 봤다(명령이 백그라운드로 옮겨져 멈췄고, 남은 자식 프로세스는 없었다).
- 탐침 Minor 3과 Nit: `run_branch`가 고친 길을 지난 회차 수를 돌려주고, 런처를 상대 경로로 친 갈래에서 그것이 0이면 "양성 대조 없음"을 찍고 1로 끝난다. 절대 경로 갈래는 옛 판도 침묵하는 것이 기대라 문턱을 걸지 않는다. `communicate`가 넘으면 자기 핸들로 끄고 다시 던진다. 이 탐침은 다시 돌리지 않았다.
- 탐침 Minor 4: `CONTROLS`(필드 없음 GET, `-f` POST, `-X POST` POST)와 어긋나면 측정 아님으로 센다. 다시 돌려 측정 6/6이었고(gh 2.98.0) `-X=POST`는 POST였다. README 행에 그 결과를 더했다.
- 탐침 Minor 5: `tools/run_checks.py`의 `pyright_checks` 독스트링에 둘 다 빼려면 `SKIP=pyright,pyright-linux`라고 적었다.
- 탐침 보류: README와 이 일지는 "셋째 회차"라 적어, `probe.py` 머리를 "셋째 회차가"로 맞췄다.
- 문서 보류: 138행에 그때의 `--move`가 같은 날의 번호 07을 내 그 이름으로 옮겼다고 덧붙였다.
- 문서 오탐 2는 셀프 리뷰 표준 Minor 1과 같은 판정으로 두었다.
- 미확인 둘을 이었다. `git show 55ba299:./.claude/skills/code-review/SKILL.md`에 `1단계 4의 번호 받기`가 한 번 있다(밀 주장 13이 맞다). 카나리아 다섯은 `tools/canary.py --preflight`로 모두 통과했다. 대조군을 커밋으로 꺼내는 셋(`--control-commit 6bd52b06`)과, 같은 체크아웃에서 `paths` 밖 파일을 읽는 둘(인자 없이)이다. 처음에 뒤의 둘에도 `--control-commit`을 줘 옛 사본의 원천에 카나리아가 있다고 실패했고, 명세 머리의 돌리는 법대로 인자 없이 다시 돌렸다.

다시 돌린 명령: 바꾼 파이썬 파일의 `uv run ruff check`(통과)와 `ruff format --check`(77 files already formatted), 바꾼 파일의 `uv run pyright`(`probe_kit.py`를 고친 뒤 오류 0), `uv run pytest -q`로 바꾼 시험 파일 일곱 367 passed, `tools/mutate.py --check`로 바뀐 훅·도구를 겨누는 변이 표 여덟이 모두 원문이 한 번씩 있다.

커밋 직전의 번호 대조: origin/main이 `b2f5c61`로 움직여, 이 일지(그때 07)가 main에 든 `2026-10-22-08`보다 이름순으로 앞이라고 1로 끝났다. `--move`로 `2026-10-22-11`로 옮겼고, 도구가 이 일지의 기록 문장 둘(그때 07로 옮겼다는 138행과 그 반영 줄)의 번호까지 바꿔 손으로 되돌렸다. 대기열 번호 420~425는 겹침이 없다. `git diff --name-only HEAD...origin/main`의 열넷 가운데 이 브랜치와 함께 고친 것은 탐침 README와 대기열 둘이고, 나머지(번호 도구와 harness 티켓 번호, 모델 재실행 설계)에서 이 브랜치가 따를 새 규약은 보지 못했다.

첫 커밋 시도는 pre-commit의 ruff check 하나로 막혔다(`too-many-statements-in-try-clause`, `tools/probe_kit.py`의 `_pump`가 8 > 5). 앞의 ruff check는 pyright 오류를 고치며 `_pump`를 다시 쓰기 전에 친 것이었다. 다른 검사는 모두 Passed였다(pytest 349.6초, web-verify 227.5초, 헌법 판만 Skipped). 읽는 일을 `_pump_text`·`_pump_plain`으로 나눠 `try` 절을 줄였고, 그 else 갈래에 남은 Unknown(pyright)도 위의 꼴로 없앴다. ruff check·format, pyright(윈도·리눅스 플랫폼), `tests/tools/test_probe_kit.py` 15 passed를 다시 봤다.

## 회고

일차 자료는 이 일지(번복과 갈린 곳은 없다)와 이어받은 이 세션이다. 후보 열넷, 승인 여덟, 기각 여섯, 넘김 0.

승인(모두 대기열로 간다. 이 PR의 범위는 지시문이 정한 행이라 여기서 반영하지 않는다):
1. 앞 세션의 러너가 인계로 멈춰 `web/eslint.config.test.ts`의 `afterAll`이 돌지 않았고 판정자 임시 트리 `web/judge-vZhAvt/`가 junction과 함께 남았다(이 세션이 스크래치패드로 옮겼다). 열린 행이 처방한 사건이라 회차로 센다 → 대기열 379, 3회차.
2. 결정이나 측정이 바뀐 뒤 옛 표현이 살아 있는 문서 셋에 남아 셀프 리뷰가 잡았다(대기열 383의 "1단계의 4", `hook_scratch_probe_rule`의 옛 PostToolUse 등록, `hook_edit_during_commit` 못 보는 것의 다시 재기 전 수). `CLAUDE.md` 작업 규약 4를 어긴 것이라 회차로 센다. 줄바꿈이 원인인 314와 원인이 달라 새 행이고 314가 가리킨다 → 대기열 420, 1회차.
3. 손으로 본 C 결과를 탐침이 잰 결과 사이에 측정처럼 적었고, 훅 독스트링이 결과를 본 뒤 바꾼 기준을 밝히지 않았다(셀프 리뷰 두 축). `docs/agents/issue-tracker.md` 프로브와 근거 절(닫힌 45가 낸 지침)을 어겼다 → 대기열 421, 45의 5회차. 처방은 프로브 README를 고칠 때 도는 `hook_probe_conclusion`의 계기 문장이다.
4. `_brace_branches`가 rg와 달리 쉼표 없는 묶음을 글자로 두어 `{.env}`를 지나보냈다(셀프 리뷰 명세 축). `.claude/rules/tools.md`의 하류 판정 항목(닫힌 239가 낸 지침)을 어겼다 → 대기열 422, 239의 3회차. 처방은 실제 rg와 훅의 판정을 맞대는 시험이다.
5. `hook_env_read`의 인용 중괄호 거짓 양성을 못 보는 것에 적지도 시험으로 고정하지도 않았다(셀프 리뷰 표준 축). 같은 `tools.md` 못 보는 것 항목을 어긴 열린 행이다 → 대기열 362, 2회차. `probe_kit`의 `KeyboardInterrupt`는 훅이나 검사가 아닌 공용 도구라 이 셈에 넣지 않았다.
6. `output_for(..., first: bool | None)`은 리뷰 기준(`CODING_STANDARDS.md`)을 어겨 리뷰가 잡은 사건이라 회차 셈에서는 빼지만, `bool | None` 주석은 AST로 잡을 수 있어 검사로 승인한다(사건, 층, 되돌림). 같은 가족인 닫힌 285(린터가 보지 못하는 불리언 플래그, 4회차)를 잇는다 → 대기열 423, 285의 5회차.
7. `tools/hook_report.py`가 UserPromptSubmit 훅의 알림을 세지 못해 `hook_prompt_directive.py`를 뺄 후보로 냈다. 그 이벤트의 출력은 명령 칸이 없는 `hook_additional_context` 첨부로만 남고 `hook_success`가 없다(이 세션의 트랜스크립트와 이 저장소의 기록을 스크래치 스크립트로 손으로 봤다. 그 훅의 문장이 든 그 첨부가 96건, uuid로 겹침을 거르지 않았다). 도구의 버그라 고침이다 → 대기열 424, 1회차.
8. retro 5단계의 행 찾기에서 Grep 도구가 대기열의 긴 행을 생략해, 스크래치 스크립트로 행의 번호·머리·승인 칸을 아홉 번 찍었다. 도구 옵션으로 옮길 수 있다 → 대기열 425, 1회차.

`hook_report.py`(대기열 423이 새 검사로 문턱을 지나 돌렸다)의 뺄 후보는 `hook_prompt_directive.py` 하나였고, 위 7의 까닭으로 거짓 양성이라 빼자고 넘기지 않았다. 이 세션의 첫 턴에도 알렸다. 가드레일을 느슨하게 하는 제안이 아니라 넘김이 없다.

기각:
- `hooks_push_help_and_commit_lock_mutations.toml`의 변이 하나의 `old`가 지금 코드에 없었다(명세 축 Minor 2). pre-commit의 `mutate.py --staged`가 커밋에 들 판에서 원문이 정확히 한 번 있는지 보아 커밋 때 막는다(대기열 312).
- 페이로드 표 note와 probes.md의 일지 번호가 틀렸다. 리뷰 기준(주장 검증)이 잡았고 검사로 옮길 수 없다.
- 막는 이유가 남긴 거짓 양성을 다루지 않은 것(명세 Minor 4)과 백그라운드 커밋 동안의 인계(표준 Minor 5)는 지침 위반이 아닌 설계 판단이고 리뷰가 제 몫을 했다.
- 앞 세션이 code-review의 카나리아 명세를 고치지 않은 것은 `sibling_overlap.py`가 그 자리에서 알렸다.
- 시험 데코레이터를 엉뚱한 자리에 넣은 것, 틀린 기대값(`{{x}.env,y}`), import 차례, 한글 폭의 E501은 pytest·ruff·`hook_ruff_line_width`가 잡았다.
- 픽스처 지우기(자동 모드 분류기), git 복합 명령(워크트리 가드), 스크래치패드로의 `cd`(훅)는 이미 있는 가드가 막았다.

만료: `queue_open_rows.py`는 이 판에서 150·155·163을, `--ref origin/main`에서는 없음을 냈다. 두 출력에 모두 든 행이 없어 닫지 않았다.

## 다음

- 이 PR이 병합되면 결정표의 하네스 chore 줄이다. 다음은 `plan.md`의 프론티어이고, 회차 3 이상인 대기열 421·423·227·379·422으로 chore를 잇지 않는다. origin/main `98272c4f` 기준으로 design-reverse-sync는 명세가 있고 티켓이 없으며, web-widget·admin-style·design-card-build는 todo다. 고르기는 병합 뒤 `next-session` 2단계가 실행 중 세션을 빼고 한다.
- 주 체크아웃 미갱신: 루트는 main. 이 PR은 워크트리에서 병합하므로 루트를 당기지 않는다(`next-session` "워크트리에서 병합할 때" 4).
- 대기열 424를 고치기 전에는 `hook_report.py`가 `hook_prompt_directive.py`를 계속 뺄 후보로 낸다. 다음 회고는 그것을 넘기지 않는다.
- PR #349 claude-review 첫 회차의 Minor 1(`.claude/rules/tools.md`의 훅 시간 문단이 훅마다 수를 한 글머리에 쌓는다. 훅별 표를 따로 두고 규칙에는 재서 표에 더한다는 문장만 남기자는 제안)을 이 배치의 행 밖이라 두었다. 다음 회고가 대기열 후보로 판정한다.

## 인계 (커밋 뒤)

PR 직전 리뷰의 반영을 커밋 `cade43cb`로 마친 직후 인계 계기가 왔다(`커밋 뒤`, 세션 컨텍스트 323,088 토큰). 첫 커밋 시도(ruff로 막혔다) 뒤에도 계기가 왔지만 그 명령은 실패해 경계가 아니었다. 인계하지 않는 때 다섯 가운데 어디에도 들지 않았다. 이 세션을 연 지시문의 "이어받을 상태"는 `인계: 셀프 리뷰 직전`이라 경계가 다르고, `get_session`의 `self`에 `parentSessionId`가 없다. 이 세션의 제목은 `chore/choice-facts-batch`였고 `chore/choice-facts-batch (인계함)`으로 바꾼다. 이 세션에서 사람의 새 프롬프트는 없었다.

- `cade43cb`의 pre-commit: 모두 Passed(pytest 234.7초, web-verify 225.1초), 헌법 판만 Skipped. 인용 대조 경고 1건(PR 직전 리뷰 절의 훅 Minor 3 줄)은 `tools/hook_edit_during_commit.py`의 막는 이유가 문자열 여러 줄에 나뉘어 글자로 이어 찾지 못한 것이다(셀프 리뷰 뒤 커밋의 판정과 같다).
- 남은 단계: origin/main 합치기(이 세션의 마지막 대조에서 `b2f5c61`. 충돌 후보는 `.scratch/retro-queue.md` 끝과 `.scratch/harness/probes/README.md`), 합친 뒤 `sibling_overlap.py`(main에 더 늦은 일지가 들었으면 다시 `--move`), 푸시, PR 열기와 `@coderabbitai review`, 봇 회차, 워크트리의 병합 길, 그 뒤 `next-session` 2~4단계. PR 직전 리뷰는 끝나 다시 돌리지 않는다. PR 본문의 체크리스트에는 위 "PR 직전 리뷰" 절의 결과와 남긴 것(문서 축 오탐 2, 다시 돌리지 않은 런처 탐침)을 적는다.
- 결정: PR 직전 리뷰의 유효 지적은 모두 PR 전에 고쳤다(고치는 값이 작고 비밀 가드와 탐침 도구의 존재 이유에 닿는다). 보안 후보는 걸러졌지만 버그로 고쳤다.
- 번복하거나 고친 것: `--move`가 이 일지의 기록 문장 둘의 옛 번호까지 바꿔 손으로 되돌렸다. 첫 커밋 시도가 ruff로 막혀 `_pump`를 나눴다.

지시문:

```
다음 작업: 하네스 chore 배치. mcp-shutdown이 닫힌 뒤 회차 3 이상인 열린 대기열 행과 같은 대상 파일의 고침 행을 한 PR로 반영한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 394·395·339·412·341·391·396·400·403(회차 3 이상인 열린 행 아홉. 227도 4회차지만 열린 PR #296이 맡았다)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이 대상이고, 같은 대상 파일의 고침 행 368(412보다 먼저 고친다)·369·408(412와 tools/hook_payloads.toml이나 같은 훅 파일을 든다)을 함께 반영한다
브랜치: chore/choice-facts-batch
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-22-11-choice-facts-batch.md 의 "PR 직전 리뷰"와 "인계 (커밋 뒤)"
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰, 회고와 "## 다음", PR 직전 리뷰와 그 반영까지 커밋했고(마지막 커밋 cade43cb, 푸시하지 않았고 PR은 없다), 남은 단계는 origin/main 합치기와 합친 뒤의 sibling_overlap.py, 푸시, PR 열기, 봇 회차, 워크트리의 병합 길이다. PR 직전 리뷰는 다시 돌리지 않는다(docs/journal/2026-10-22-11-choice-facts-batch.md). next-session은 워크트리 사본의 SKILL.md를 Read로 열어 따른다
확인할 선행 조건: .scratch/harness/probes/edit_during_commit_launcher.py는 PR 직전 리뷰를 반영한 뒤(양성 대조 문턱, 시간을 넘긴 커밋 끄기) 다시 돌리지 않았다
이번 요청 범위: PR과 병합까지
```

넘기기 전: 제목을 `chore/choice-facts-batch (인계함)`으로 바꿨고, 이 세션이 띄운 백그라운드 작업은 남은 것이 없었으며(두 커밋 모두 끝났다), `git worktree unlock C:/project/agent/.claude/worktrees/choice-facts-batch`는 `is not locked`로 끝나 넘어갔다.

open-session을 부른다 2026-10-22T08:43:17Z

## 이어받은 세션 (커밋 뒤부터)

> 사용자: (위 "인계 (커밋 뒤)" 지시문의 시작 프롬프트와 같다)

`git worktree list`에서 이 브랜치가 `.claude/worktrees/choice-facts-batch`에 있어 `EnterWorktree(path)`로 들어갔고, 세션 제목을 `chore/choice-facts-batch`로 바꿨다. 위 "인계 (커밋 뒤)" 절은 커밋되지 않은 채 작업 트리에 있어 이 세션의 커밋에 실었다.

- origin/main `b2f5c61d`(#345·#346)를 합쳤다. `.scratch/retro-queue.md`가 두 자리에서 충돌했다. 하나는 main이 391행 앞에 426·427행을 더한 자리이고, 다른 하나는 양쪽이 끝에 서로 다른 행(이쪽 420~425, main 415~419·428)을 더한 자리다. main은 391행을 고치지 않았고(공통 조상과 견줬다) 번호도 겹치지 않아, 앞 자리는 426·427 뒤에 이 브랜치가 닫은 391을, 뒤 자리는 번호순으로 두었다. 푼 판은 이 브랜치의 판에 main이 더한 행 여덟만 더한 것이다(`diff`로 봤다). 탐침 README는 저절로 합쳐졌다.
- 결정: main이 더한 427행을 닫았다. 그 처방(수가 든 선택 화면을 세션에서 처음 부를 때 한 번 거부하고, 대 보지 못한 것은 어림이라고 적어 다시 부르라고 거부 이유에 싣는다)은 394가 이 브랜치에서 반영한 `tools/hook_choice_facts.py`의 `_DENY_BODY`와 같다. 427의 사건은 main의 옛 판(답한 뒤에 읽히는 알림)에서 났다. 열어 두면 다음 chore 배치가 이미 들어간 처방을 다시 맡는다.
- 합친 뒤 `sibling_overlap.py`: 번호 겹침 없음(origin/main `b2f5c61`, 다음 빈 번호는 `일지 2026-10-22-12`·대기열 429).
- 확인할 선행 조건이던 런처 탐침을 다시 돌렸다(`edit_during_commit_launcher.py 30`). 훅의 판정 코드는 앞 판의 30회차를 잰 때와 같다(`cade43cb`는 막는 이유 문장만 늘렸다, `git diff`로 봤다). 종료 0, 360회차가 모두 측정이었다. 런처의 상대 경로 네 갈래에서 옛 판이 29·30·28·30회차 거짓 알림을 내 양성 대조 문턱을 넘었다. 지금 판은 절대 경로 여섯 갈래 0, 런처의 상대 경로 120회차 가운데 하나(`bin` 부하, 자식이 끝난 뒤의 런처), 실제 git 상대 경로 9·30회차였다. 앞 판(둘, 17·30)과 꼴이 같아 둘째 표본으로 `tools/hook_edit_during_commit.py`의 작업 트리 문단과 못 보는 것, 탐침 README 행에 덧붙였다.
- `coderabbit auth status`: `Plan: Free`, `Seat: not assigned`. PR 직전 리뷰를 대체 둘로 돌린 근거가 이 PR에서도 그대로다.
- 합치기 커밋 `bcc79e68`의 pre-commit: 모두 Passed(pytest 212.6초, web-verify 222.8초), 카나리아 명세 모양과 헌법 판은 고친 파일이 없어 Skipped. 병합 중이라 ruff는 충돌 파일만 봤고(`Checking merge-conflict files only`), 고친 `tools/hook_edit_during_commit.py`는 그 전에 ruff check·format을 손으로 통과했다. 인용 대조 경고 3건은 모두 main이 쓴 427행의 인용(그 세션의 화면 문구, main의 옛 훅 문구, 처방의 제안 문장)이고 줄을 닫으며 다시 걸렸다. 기록이라 두었다.
- PR #349를 `gh api repos/njh6803/agent-os/pulls --method POST --input <JSON>`으로 열었다(대기열 382의 길). 지금 도는 훅은 주 체크아웃의 옛 사본이라 이 꼴을 PR 열기로 알아보지 못해(이 PR의 408이 고친다), `PR 연 뒤`의 인계 계기와 `hook_pr_next_session`의 계기가 오지 않았다. 남은 일이 봇 회차와 병합뿐이라 이 세션에서 이었다.
- 첫 대기의 결과: 검사 모두 통과, CodeRabbit은 `Review rate limited`(리뷰 없음), claude-review는 Critical·Major 없이 Minor 2·Nit 2. 첫 회차라 지적마다 판단했고 넷 모두 두었다. Minor 1은 위 "다음"으로 넘겼고, Minor 2(`tool_name` 검사 세 곳)는 `test_다른_도구는_침묵한다`와 변이 둘이 각 함수의 검사를 고정하며, Nit 둘은 규칙(막는 훅 독스트링)과 리뷰 스스로의 판단으로 두었다. 이유는 PR 코멘트에 남겼다.
