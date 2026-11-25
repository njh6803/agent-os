# 2026-11-26 (01:31) admin-login 티켓 02: 계정 표와 시스템 관리자 명령

브랜치 `feature/02-account-tables-and-system-admin-command`, 워크트리 `.claude/worktrees/02-account-tables-and-system-admin-command`. 모델 Sonnet 5.5(지시문의 high). 기준은 `origin/dev`의 티켓 01 병합(PR 645) 뒤다. 세션은 새 세션이고 나란히 도는 세 세션 가운데 하나다. 중간에 컨텍스트가 한 번 압축됐다. 이 일지는 사용자에게 로컬 모델 시험의 비용을 묻고 답을 받은 직후에 만들었다.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/admin-login/issues/02-account-tables-and-system-admin-command.md

이어지는 줄(다음 작업, 다음 단계, 어디서, 시작 프롬프트, 브랜치, 모델, 읽을 것, 이어받을 상태, 확인할 선행 조건)은 컨텍스트 압축 뒤라 원문 대신 요약으로만 가지고 있다. 줄여 적으면 이렇다. 브랜치 `feature/02-account-tables-and-system-admin-command`, 모델 Sonnet 5.5 / high, "이번 요청 범위: PR과 병합까지"다. 원문은 이 세션의 기록 파일(`C:\Users\User\.claude\projects\C--project-agent--claude-worktrees-02-account-tables-and-system-admin-command\c11bf447-8969-48ef-a570-2ed33e20957e.jsonl`)에 있다.

## 한 일(셀프 리뷰 직전까지)

근거의 종류를 함께 적는다. 코드를 읽은 것, 명령이 출력한 것, 이 세션이 고른 설계다.

- 마이그레이션 `0002`(`src/agent_os/adapters/postgres/migrations/versions/0002_operator_accounts.py`)가 표 여섯과 시스템 관리자에만 거는 부분 유일 색인을 만든다. `upgrade`만 있고 시각 칸에 기본값이 없다. 시험 `tests/test_operator_accounts_migration.py`가 표 여섯, 유일 색인, 서명 키 표가 먼저 있을 때 `migrate`가 "already exists"로 멈추고 판이 `0001`에 남는 것을 단언한다(이 세션이 돌려 통과를 봤다).
- 규칙 함수는 `src/agent_os/http/passwords.py`(NFKC, 코드 포인트 수, 종류, 제어 문자와 서로게이트 거절, Argon2id m=19456 t=2 p=1)와 `src/agent_os/http/accounts.py`(이름 규칙, 포트 `AccountStore`)다. 의존성 `argon2-cffi>=25.1,<26`을 `pyproject.toml`·`uv.lock`·`docs/constitution/tech.md`에 더했다.
- 어댑터는 `src/agent_os/adapters/postgres/accounts.py`·`account_tables.py`·`errors.py`다. 이름 충돌은 SAVEPOINT 안에서 넣고 23505만 `"taken"`으로 돌려준다. 데이터베이스 예외는 `AccountStoreError`로 바꿔 `except` 밖에서 던져 원인과 문맥을 잇지 않는다. 변이로 두 가지(원인 잇기를 되살림, SAVEPOINT를 뺌)가 시험에서 빨개지는 것을 이 세션이 봤고 둘 다 되돌렸다.
- 명령은 `src/agent_os/channel/cli/operator.py`와 `main.py`의 조립이다. 비밀번호는 인자로 받지 않고 터미널이면 두 번, 아니면 첫 줄 하나를 받는다. `main`은 stdin도 UTF-8로 맞춘다(파이프로 넣은 한글 비밀번호의 해시가 달라지지 않게 하려는 설계다).
- 규칙 문서: `.claude/rules/core.md`의 포트 문장 둘을 "core의 포트"로 좁히고 계정 저장소 포트가 `http`에 있다고 적었다. `.claude/rules/adapters.md`에 계정 저장소 항목을 더했다. 올리기 조각은 `docs/release-notes/upgrade/operator-accounts.md`다.
- `tests/fake_database.py`의 `FakeDatabase`에는 `accounts()`를 주지 않았다. 계정을 쓰는 곳은 `system-admin` 명령 하나이고 그 길은 진짜 데이터베이스로만 시험한다. `create_app`은 그대로이고 `serve`는 아직 계정을 쓰지 않는다(03이 들인다). 티켓이 "가짜 데이터베이스가 그 메서드를 어떻게 내는지 이 티켓이 정한다"고 했고 이것이 그 결정이다.
- `.scratch/admin-login/probes/` 아래 옛 프로브 파일 아홉 개(`git diff --stat`로 센 값이다)의 import 순서를 `ruff check --fix --select I`로 정렬했다. 새 모듈 `agent_os.adapters.postgres.accounts`가 생겨 ruff가 그 import를 자기 패키지로 읽게 되면서 정렬 오류가 났기 때문이다(이 세션이 `ruff check .`의 출력으로 봤다). 프로브의 내용은 바꾸지 않았다.

## 검증(이 세션이 돌린 것)

- `uv run ruff check .`와 `uv run ruff format --check .`가 통과했다(명령 시험 파일의 서식 하나를 `ruff format`으로 고친 뒤).
- `uv run python tools/run_checks.py`가 종료 0으로 끝났다. 출력의 단계는 check-ticket, zizmor, check-notes, lint-imports, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest(1216.7초), web-verify가 모두 `Passed`다.
- `uv run --env-file ../../../.env pytest -m llm -q`가 24개 통과, 8393개 선택 제외로 927초에 끝났다(출력에서 읽음). 출력의 토큰 합계는 262,005(입력 256,450, 출력 5,555)이고 트레이스 30개, 모델 호출 62건이다. 트레이스를 남기지 않은 LLM 테스트 2개는 세지 못했다고 출력이 적었다.
- 로컬 모델 시험 `uv run --env-file ../../../.env python tools/llm_local.py run --yes`가 통과 4, 종료 코드 0으로 끝났다(출력에서 읽음). 기록 묶음은 GPU A40, 배치 `shared`(파드 1대, 시간당 $0.59), 걸린 시간 606초다. 토큰은 입력 6,191·출력 106·호출 4건·트레이스 2개다. 회차 파일은 `C:\Users\User\.agent-os\llm-local\feature%2F02-account-tables-and-system-admin-command\records\round-0001-20261125T164206Z.json`이다. 시험 명령은 출력의 `test_command`(`uv run pytest -m llm_local`)다. 파드는 타이머가 지운다고 도구가 적었으나 실제로 지워졌는지는 이 세션이 확인하지 못했다.
- e2e(관리 화면, 위젯, 위젯 테스트 페이지, 단독 배포)와 사진 비교는 이 세션이 돌리지 않았다. `main.py`와 어댑터를 고쳤지만 `deploy/`, 서버 시작 인자, 위젯·관리 화면 코드는 건드리지 않았다. CI가 돈다.

## 인계

이 세션의 컨텍스트가 인계 문턱(20만 토큰)을 넘은 채 `셀프 리뷰 직전` 경계에 왔다. 인계하지 않는 다섯 경우에는 들지 않는다(`get_session`의 `self`에 `parentSessionId`가 없다, 요청 범위는 "PR과 병합까지", 이어받을 상태는 `인계:`로 시작하지 않는다, `인계 못함` 줄 없음). 다만 인계 절차의 "대기 멈추기"가 이 세션이 띄운 백그라운드 작업을 끊는데, 그때 돌던 `-m llm`과 사용자가 비용을 승인한 로컬 모델 시험(유료 파드)을 도중에 끊으면 안 된다고 판단해, 두 시험이 끝나 결과를 위 "검증" 절에 옮긴 뒤에 인계한다. 두 시험은 끝났고 도는 백그라운드 작업은 없다.

이 세션의 제목은 `feature/02-account-tables-and-system-admin-command`였고 인계하며 `feature/02-account-tables-and-system-admin-command (인계함)`으로 바꾼다. 워크트리 잠금은 `git worktree unlock`으로 푼다.

넘기는 지시문(원문):

```
다음 작업: .scratch/admin-login/issues/02-account-tables-and-system-admin-command.md. 계정 표 여섯과 시스템 관리자 명령을 짓는 두 번째 티켓(티켓 03이 이 티켓을 기다린다)
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/admin-login/issues/02-account-tables-and-system-admin-command.md
브랜치: feature/02-account-tables-and-system-admin-command
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: 일지 docs/journal/2026-11-26-0131-admin-login-ticket-02.md (이 세션이 한 일, 검증 결과, 남은 일)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. 일지 docs/journal/2026-11-26-0131-admin-login-ticket-02.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

남은 일: 셀프 리뷰(`/code-review`) 반영, 티켓 02 상태를 `done`으로 바꾸고 `uv run python tools/plan_table.py`, `uv run python tools/sibling_overlap.py`, 이 일지의 `## 다음`과 회고, 커밋(`feat!:`), 푸시, PR, 병합(워크트리 사본의 `merge.md` "워크트리에서 병합할 때"). 로컬 모델 시험의 비용은 사용자가 확인했고 이미 돌았으므로 다시 묻지 않는다.

## 셀프 리뷰(`/code-review`, 이어받은 세션이 돌렸다)

범위: base `11343375b`(origin/dev와 같다), 수정 파일 안 `.scratch` 프로브 아홉 개와 `uv.lock`을 뺀 일곱, 미추적 열세 개, 커밋 없음. 표준 축(sonnet·high)과 명세 축(세션 모델)을 병렬로 돌렸다. Critical은 없었다.

판정과 반영(근거는 코드를 열어 본 것이고, 고친 문장의 사실은 그 자리에서 다시 읽거나 돌려 확인했다).

- **고침 1(두 축이 함께 냈다): 표준 입력이 UTF-8이 아니면 역추적이 난다.** `printf`로 `\xff\xfe…`를 넣은 `password_hash_of`가 `UnicodeDecodeError`로 끝나는 것을 직접 재현했다. 예외 글에 읽던 바이트와 위치가 실려 비밀번호의 일부가 새고 높임말 문구도 없었다. `_read_password`가 그 예외를 받아 `NOT_UTF8_TEXT`로 거절하게 했고 시험 `test_표준_입력이_UTF8이_아니면_역추적_없이_받아들이지_않는다`를 더했다.
- **고침 2: 새 시험 둘의 빨강을 변이로 봤다.** `main`이 stdin을 UTF-8로 맞추는 줄을 뺀 변이에서 `test_표준_입력이_cp949로_열려_있어도…`가 1로 빨개졌고, `ACCOUNT_FAILURES`의 타입을 `BigInteger`로 바꾼 변이에서 칸 타입 대조 시험이 `bigint != integer`로 빨개졌다. 둘 다 되돌렸다. 이 셋째 시험(`_use_utf8` 시험)은 명세 축이 "stdin 추가는 검증된 바 없다"고 낸 것을 닫는다.
- **고침 3: 표 정의 대조 시험이 칸 타입을 보지 않았다(두 축).** `information_schema`의 `data_type`을 같이 견주게 했고 `adapters.md`의 문장은 "이름·타입·비어도 됨, 키와 색인은 견주지 않는다"로 맞췄다.
- **고침 4: `_decide`의 재시도 갈래에 명령 단위 시험이 없었다.** 가짜 작업 객체(포트 타입으로 적은 픽스처)로 "taken 뒤 이긴 쪽이 다른 이름이면 1로 멈춘다"와 "두 번 다 막히면 `RuntimeError`"를 더했다.
- **고침 5: 틀리거나 낡은 문장.** `account_tables.py`의 "지금 쓰는 칸만 든다"(표 셋의 칸은 전부 들었다), `accounts.py` 어댑터의 "같은 이름을 동시에 넣는 경합은 재지 못했다"(프로브는 못 쟀으나 시험이 있다. 그 한계를 둘로 갈랐다), `passwords.py`의 "기본 매개변수는 저장과 견줌의 시간이 다른 값이다"(프로브 `.scratch/admin-login/probes/hash_load/`의 README 요약 6이 적은 +274ms 문장으로 바꿨다. 그 요약은 그 프로브가 다시 낸다고 적은 값이다), `http/accounts.py`의 `end_logins` 독스트링, `main._use_utf8`의 독스트링(stdin 추가), `core.md`의 "그것을 쓰는 층(`http`)이 선언한다"(채널과 관리가 함께 쓰는 `http`로). 이 문장들은 PR 직전 리뷰에 밀 주장으로 넘긴다. 칸 타입 대조의 범위("키와 색인은 견주지 않는다"), "프로브 결과 6이 +274ms를 쟀다", "`end_logins`는 아직 끊기지 않은 로그인 전부를 끊는다"(시험 `test_로그인을_끊으면…`이 본다), "같은 이름을 동시에 넣는 경합은 시험이 본다"(`test_같은_이름을_동시에_넣으면…`).
- **고침 6: 잔존 문장.** `.claude/agents/spec-reviewer.md`와 `CODING_STANDARDS.md`의 "포트 다섯 밖의"를 "core의 포트 다섯 밖의"로 좁혔다. `.github/PULL_REQUEST_TEMPLATE.md`의 같은 구절은 `src/agent_os/core/` 항목 아래라 이미 core로 한정돼 둔다.
- **고침 7: 시험의 군더더기.** 값이 하나뿐인 `parametrize("value", [None])`를 풀었다.
- **고침 8: 일지의 "열 곳"**은 아홉 개가 맞아 위에서 고쳤다.
- **고침 9: 업그레이드 노트의 단독 배포 꼴(명세 축 (c)3).** 단독 배포의 운영자는 서버 안으로 들어가지 않고 `docker compose exec serve agent-os operator system-admin <계정 이름>`으로 친다(명세 "서버 명령"과 티켓 14의 배포 안내가 같은 꼴을 쓴다). `docs/release-notes/upgrade/operator-accounts.md`의 3번 항목에 그 꼴을 더했다. 서비스 이름 `serve`는 `deploy/standalone/compose.yaml`의 서비스 이름과 같다(파일에서 읽음). 이 세션이 `docker compose exec`로 돌려 보지는 않았다(그 실행은 티켓 14의 단독 배포 e2e 몫이다).
- **헌법 판과 카나리아.** `tech.md`를 고쳤으므로 판을 3.1.8로 올렸다(`sibling_overlap`이 알렸다). 하네스 파일 셋(`adapters.md`, `core.md`, `spec-reviewer.md`)이 바뀌어 `sibling_overlap`이 카나리아 명세 열여섯을 알렸다. 새로 더한 `adapters.md` 항목을 겨냥한 명세 `.scratch/admin-login/probes/canary/adapters_rule_account_store.toml`을 새로 썼고 아래 "검증"에 결과를 적는다.

남긴 것과 이유(Minor·Nit, 근거를 본 뒤 보류).

- 명세 축 (c)2: `PostgresAccounts.transaction()`이 블록 본문의 `OSError`·`SQLAlchemyError`도 `AccountStoreError`로 바꾼다. 블록 본문은 이 티켓에서 `system_admin_command`뿐이고 그 안에서 난 데이터베이스 예외가 바뀌는 것이 의도(원인을 잇지 않는다)라 둔다. 뒤 티켓이 블록 안에서 다른 `OSError`를 낼 길을 더하면 그때 가른다.
- 명세 축 (a)1: 명세 "표와 마이그레이션"은 "값을 싣는 실패를 내지 않는다" 규칙을 postgres-foundation의 마이그레이션 규칙 문서에도 한 줄 더하라고 적었으나, 티켓의 체크박스는 `0002`의 독스트링만 요구하고 그 규칙 문서가 어느 파일인지 `.claude/rules`에서 찾지 못했다. 티켓이 이 일을 구체화한 판이라 독스트링으로 닫고, 뒤 티켓(해시와 키 칸을 건드리는 마이그레이션)이 규칙 문서를 가리키게 할지는 그 티켓이 정한다.
- 명세 축 (a)2·(a)3: 멈춘 올리기 시험은 `result.ok` 거짓까지 보고 종료 코드 1은 `tests/test_migrate_command.py`의 선례가 그 변환을 본다. 명령 시험의 파이프는 `StringIO`로 대신한다(실제 프로세스 파이프는 e2e와 compose 시험의 몫이다. 03 이후 티켓이 같은 줄을 진짜 파이프로 지난다).
- 표준 축 (a)2: `main._system_admin`의 `stderr.write(...); return EXIT_FAILED` 세 번 되풀이. 같은 모양이 `serve`와 `migrate`에도 있어 이 티켓에서 뽑지 않는다.
- 표준 축 냄새: `AccountRow` 일곱 칸 중 명령이 쓰는 것은 `.name` 하나(포트가 뒤 티켓의 읽기도 받치려는 것이라 Speculative Generality가 아니라 포트의 몫), `_NewAccount`의 같은 이름 셋(`http`·어댑터·명령이 서로를 import하지 못하는 층 경계), `password_hash_of`의 이름과 `_decide`의 CQS 혼합은 이름·모양의 취향이라 둔다.

## 셀프 리뷰 반영 뒤의 검증(이어받은 세션이 돌렸다)

- `uv run ruff check .`와 `uv run ruff format --check .`가 통과했다(출력에서 읽음. 반영 중 `ruff format`이 파일 하나를 고쳤다).
- `uv run python tools/run_checks.py`가 종료 0으로 끝났다. check-notes, check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright-linux, pyright, run-hooks, pytest(823.4초), web-verify(910.8초)가 모두 `Passed`다(출력에서 읽음).
- 카나리아(`claude` 2.1.325, 러너 출력에서 읽음). 새 명세 `adapters_rule_account_store.toml`(`.claude/rules/adapters.md`의 계정 저장소 항목)이 통과 4였다. 실험군 셋이 두 구절을 글자 그대로 옮겼고 대조군은 "없음"이었다. 바뀐 `spec-reviewer.md`의 명세 둘은 대조군 커밋을 `--control-commit`으로 주어 돌렸다. `spec_reviewer_agent.toml`은 통과 4였고 `spec_reviewer_evidence_kinds.toml`은 첫 판이 통과 3·실패 1이었다. 실패 한 회차에서 모델이 카나리아 구절의 `<slug>`를 `&lt;slug&gt;`로 바꿔 적어 글자가 맞지 않았다. 같은 명령을 다시 돌려 통과 4였고, 바뀐 정의의 문장이 실리지 않은 것이 아니라 모델이 옮기며 낸 글자 차이로 본다(어림. 원인을 더 재지 않았다). 나머지 명세 열넷은 `--preflight`만 통과했고 새로 쓴 세 명세의 `--shape`도 통과했다. 세 명세의 `# 최신 결과:` 줄을 고쳤다. 고친 `adapters.md`와 `core.md`의 문장(포트 목록 단서, 표 대조 범위)을 겨냥한 기존 명세는 없었다. `core.md`는 새 명세 `.scratch/admin-login/probes/canary/core_rule_unknown_domain_port.toml`(core가 모르는 영역의 포트는 `http`가 선언한다는 문장)을 써서 돌렸고 통과 4였다. 실험군 셋이 그 문장을 글자 그대로 옮겼고 대조군은 "없음"이었다("없음" 섞임 0). 그래서 `sibling_overlap`의 `core.md` 알림(기존 명세 여덟)은 그 여덟이 이번에 고친 문장을 겨냥하지 않아 사전 확인만 한 채 남아 있다. 알림은 파일 단위로 뜨고 그 줄을 지우는 길이 없어, 이 알림이 남은 채 커밋한다(알림 안내가 허용한 길).
- `-m llm`과 로컬 모델 시험은 반영 뒤에 다시 돌리지 않았다. 앞서 돌린 뒤 `src/`의 변경은 `operator.py`의 UTF-8 거절 갈래(`channel/cli`)와 `adapters/`·`main.py`의 독스트링뿐이고, 호출 길이나 모델 호출은 바뀌지 않았다(코드를 읽은 판단이다).
- e2e와 사진 비교는 이 세션이 돌리지 않았다(위와 같은 이유로 CI가 돈다).

## 사용자에게 물은 것: 로컬 모델 시험 비용

`tools/llm_local.py run`을 `--yes` 없이 쳐 예상 비용을 받았다(Runpod 단가는 2026-11-13에 웹 요약에서 읽은 값이라 원문과 대조하지 않은 어림이다). 후보는 RTX A5000(파드 2대, 어림 30분 $0.27, 최악 90분 $0.81), RTX 3090($0.50, $1.50), A40 파드 2대($0.59, $1.77), A40 공유 서버(파드 1대, $0.29, $0.88)다. 선택 화면은 훅이 한 번 막아 설명의 수를 출력과 대 본 뒤 다시 불렀다.

> 질문: 이번 변경이 로컬 모델 시험(Runpod 유료 파드)의 병합 조건 범위에 듭니다. 어림 $0.27~$0.59(30분), 최악 $0.81~$1.77(90분)로 돌려도 될까요?
> 선택지: 돌린다(`--yes`로 실행합니다. 파드는 타이머가 90분 뒤 지웁니다. 단가는 웹 요약 값이라 원문과 다를 수 있습니다) / 이번에는 건너뛴다(시험 없이 진행하고 PR 본문에 돌리지 않았다고 적습니다)
> 사용자: 돌린다 (Recommended)

## PR 직전 리뷰(CodeRabbit CLI, `coderabbit-review` 서브에이전트)

CLI 0.7.5가 `review_completed`로 끝까지 돌았다(`Seat: not assigned`, `Plan: Free`에서도 돌았다. 서브에이전트 보고에서 읽음). 범위는 `--committed --base origin/dev`, 파일 48개. 지적 3건 모두 유효, 오탐 0. 판정은 서브에이전트가 내고 본 세션이 코드를 열어 다시 확인한 뒤 고쳤다.

- **고침 10(Major): `_decide`가 이름 조회가 돌려준 줄의 `tier`를 보지 않았다.** `lock_system_admin()`이 비었다는 이유만으로 그 뒤 줄을 모두 관리자 단계로 거절했다(`operator.py`). READ COMMITTED에서 두 조회 사이에 같은 이름의 시스템 관리자가 커밋되면 재설정해야 하는데 1로 끝난다(데이터는 상하지 않고 같은 명령을 다시 치면 풀린다). `existing.tier == "admin"`일 때만 `_AdminTier`로 끝내고 아니면 다음 바퀴로 돌게 했다. 시험 `test_두_조회_사이에_시스템_관리자가_생기면_다시_읽어_재설정한다`를 더했다. `_RacingWork.lock`이 늘 `None`을 돌려주던 픽스처가 이 갈래를 건드리지 못했던 것이 빈틈이었다(`existing` 인자를 더했다). 변이로 `tier` 검사를 시스템 관리자까지 거절하게 바꾸면 `assert 1 == 0`으로 빨개지는 것을 봤다.
- **고침 11(Minor, CLI는 Major): 터미널이 글자를 숨기지 못하면 `getpass`가 경고만 내고 보이는 입력으로 받는다.** 서브에이전트가 이 저장소의 파이썬 3.12.10 `getpass.unix_getpass` 소스를 열어 `termios.error`가 `fallback_getpass`(경고 `GetPassWarning` 뒤 에코가 켜진 입력)로 가는 것을 확인했다. 드문 환경(`stdin.isatty()`는 참인데 termios 제어가 실패하는 pty)이고 화면을 보는 사람에게만 보이지만 고치는 값이 작아 고쳤다. 두 `ask`를 `warnings.catch_warnings()` 안에서 `simplefilter("error", GetPassWarning)`로 감싸고, 경고가 오류가 되면 `CANNOT_HIDE_TEXT`로 입력을 받기 전에 멈춘다. 시험은 `warnings.warn(..., GetPassWarning)`을 진짜로 내는 가짜 `ask`를 써서 필터가 경고를 오류로 바꾸는 길까지 본다. 필터를 `"ignore"`로 바꾼 변이에서 해시가 나와 빨개지는 것을 봤다.
- **고침 12(Minor, CLI는 Major): 업그레이드 노트 1번에 판 번호를 바꾸라는 말이 없었다.** `deploy/standalone/compose.yaml`의 이미지가 `${AGENT_OS_VERSION}`으로 정해져(파일에서 읽음) `.env`의 그 줄을 바꾸지 않으면 새 판이 뜨지 않는다. `standalone-postgres.md` 3번처럼 "`.env`의 `AGENT_OS_VERSION`을 새 판 번호로 바꾸고 …"로 고쳤다.

남긴 것과 이유(서브에이전트가 코드를 읽고 더한 보류 둘, 본 세션이 명세와 대 봤다).

- 계정 이름이 소문자인지 보는 CHECK를 `0002`에 넣지 않았다. 이름 규칙의 소문자 접기는 명세가 `http`의 함수(`fold_account_name`)에 두라고 적었고(`spec.md` "계정 이름"), 03 티켓이 대문자로 넣은 이름(`Kim.Dev`)의 로그인을 따로 시험한다(03의 수용 기준). 표의 칸 정의는 명세가 정한 것이라 이 티켓이 제약을 더하지 않고, 03이 접기를 빼먹으면 그 시험이 빨개진다.
- 파이프로 넣은 비밀번호 앞에 UTF-8 BOM이 붙어 오면 `U+FEFF`가 비밀번호에 든다. BOM을 붙이는 쓰는 쪽이 있는지 확인하지 못했고(윈도 PowerShell 5.1의 파이프가 후보이나 재 보지 않았다), 규칙을 바꾸는 일은 명세가 정할 몫이라 이 티켓에서 고치지 않는다. 단독 배포 e2e(티켓 14)는 노드가 글을 직접 파이프에 쓰므로 BOM이 붙지 않을 것으로 본다(어림이고 재 보지 않았다).

## 회고

낸 후보 셋: 승인 0, 기각 3, 넘김 0. 대기열 만료는 이 회고가 닫은 열 항목(`562`, `external-ref-moved-while-citing`, `glob-slash-pattern-narrowed-path`, `grep-glob-slash-pattern`, `harness-work-invisible-in-plan`, `measure-subagent-stopped-by-usage-limit`, `open-session-stale-main-copy`, `option-description-implied-omission`, `plugins-outside-type-judges`, `ui-design-web-edit-read-path-prefix`)이다. 기본 출력과 `--ref origin/dev` 출력이 같은 열을 냈다.

- **카나리아 알림이 기존 명세 여덟을 주는데 그 여덟이 이번 문장을 겨냥하지 않았다(탐색).** 알림 문구는 "원천으로 든 명세가 없으면 새로 쓴다"인데 `core.md`에는 명세가 이미 여덟이라 어느 쪽인지 읽어 가려야 했다. 한 번 난 일이고 사건의 손해는 새 명세 하나를 쓴 몫이다. 기각(더하는 것의 다섯 번째가 아니고 손상도 없다).
- **`spec_reviewer_evidence_kinds`의 첫 판이 모델이 `<slug>`를 `&lt;slug&gt;`로 옮겨 빨갰다(자동 검사).** 다시 돌려 통과했고 정의의 문장은 실려 있었다. 모델의 옮기기 차이라 검사를 느슨하게 하는 쪽(넘김)으로 갈 일이고, 한 번이라 기각. 명세 머리와 위 "검증"에 적었다.
- **셀프 리뷰가 잡은 낡은 문장 다섯(독스트링과 규칙 문장)과 UTF-8 거절 누락(표준 규칙).** 리뷰가 잡도록 둔 기준을 어겨 리뷰가 잡은 사건이라 회차로 세지 않는다(회고 4단계). 새 판단 기준도 아니라 기각.

다음 회고가 이어 세어야 할 것은 없다.

## 다음

- **지금 단계: PR과 병합.** 이 일지의 변경과 위 고침을 한 커밋(`feat!:`)으로 싣는다. PR 제목에 `!`가 붙고 본문에 "올리기 전에 데이터베이스를 백업한다"를 적는다(업그레이드 노트 `docs/release-notes/upgrade/operator-accounts.md`가 같은 말을 한다).
- **PR 직전 리뷰.** `coderabbit-review`(CLI가 돌지 못하면 `bug-perf-review`)를 돌려 트리아지한다. 위 "고침 5"의 문장(칸 타입 대조 범위, +274ms, `end_logins`, 동시 삽입 시험)은 밀 주장으로 넘긴다.
- **병합 뒤.** 티켓 03(`.scratch/admin-login/issues/03-login-logout-me-and-setup-beside-shared-tokens.md`)이 풀린다. 이 티켓이 계정 표 여섯과 `AccountStore` 포트를 짓고 시스템 관리자 명령을 세웠으므로 03이 로그인 경로를 그 위에 얹는다.
- **돌리지 못한 것.** e2e와 사진 비교는 CI가 돈다. `-m llm`과 로컬 모델 시험은 반영 뒤에 다시 돌리지 않았다(이유는 위 "검증").

open-session을 부른다 2026-11-25T16:46:00Z
