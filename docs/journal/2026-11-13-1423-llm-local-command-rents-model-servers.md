# 2026-11-13 모델 서버를 띄우는 명령의 클라우드 없이 도는 몫 (local-model 03)

세션 제목: `feature/03-llm-local-command-rents-model-servers` (인계하면 `<브랜치> (인계함)`으로 바뀐다)

## 사용자 프롬프트 원문

> 사용자: 다음 작업: .scratch/local-model/issues/03-llm-local-command-rents-model-servers.md. 모델 서버를 띄우는 명령 `tools/llm_local.py run`이 비용을 확인받고 Runpod에 모델 서버 둘을 띄워 시험을 돌린 뒤 지운다
> 다음 단계: 구현
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고 그 뒤 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/local-model/issues/03-llm-local-command-rents-model-servers.md
> 브랜치: feature/03-llm-local-command-rents-model-servers
> 모델: Sonnet 5.5 / high
> 읽을 것: docs/journal/2026-11-12-2214-local-model-tickets.md의 "다음"(사용자에게 다시 물을 것 셋 가운데 (1)이 이 티켓의 셋째 구성이다)
> 이어받을 상태: 02는 PR 554로 dev에 병합됐다. 이 티켓의 첫 수락은 사용자의 준비 넷이라 모자라면 티켓 본문대로 클라우드 없이 도는 몫만 커밋하고 in-progress로 둔다
> 이번 요청 범위: 구현·리뷰·커밋까지

## 한 것

- 티켓의 첫 수락(사용자의 준비 넷)을 먼저 봤다. `--env-file ../../../.env`를 넘긴 환경에 `RUNPOD_API_KEY`의 이름이 없었고(값은 읽지 않았다), Terraform은 1.5.5라 1.6 이상이 아니었다. 그래서 티켓 본문대로 클라우드 없이 도는 몫만 만들었다. 티켓은 `in-progress`로 두었고 "띄워 확인하는 것"의 칸은 모두 비어 있다.
- `tools/llm_local.py`(`run`, `sweep`): 환경 검사, 상태 폴더(`~/.agent-os/llm-local/<브랜치>/`), 잠금(`<이름>.lock`과 `<이름>.guard`의 OS 파일 잠금), 남은 자원 지우기, 예상 비용, 서버 키, 띄우기(재고가 없으면 다음 후보), 준비 기다리기(상한 30분), 시험 자식, 지우기, 기록 묶음, 종료 코드 0~4다. 외부 명령은 `execute` 한 함수를 지나고 출력은 파이프가 아니라 임시 파일로 받는다.
- `tools/llm_local_server/main.tf`: 프로바이더 `runpod/runpod` `= 2.0.0`, vLLM 공식 이미지 0.33.0, 구성 둘(`pods`: 모델마다 파드 하나, `shared`: A40 한 장에 서버 둘)이다. 타이머는 90분 뒤 `runpodctl pod delete`로, 없으면 REST DELETE로 파드를 지운다. 계정 키는 구성에 싣지 않고 서버 키만 `sensitive` 변수로 받는다. `terraform fmt -check`만 통과했고 `plan`은 돌리지 않았다.
- 단가 표는 Runpod 가격 페이지를 2026-11-13에 WebFetch로 다시 받아 옮겼다(Secure Cloud, RTX A5000 0.27, RTX 3090 0.50, A40 0.59 달러/시). WebFetch는 원문이 아니라 웹 요약을 주므로 값은 요약에서 읽은 것이고, 띄워 본 `cost`와 견주는 일은 티켓의 "띄워 확인하는 것"에 남아 있다. 값은 코드의 `GPUS`, 날짜는 `PRICE_TABLE_DATE`다.
- 시험 네 파일: `tests/tools/llm_local_world.py`(가짜 세계), `test_llm_local.py`(이름, 비용 표, 걸음 1~5, 한 바퀴), `test_llm_local_rounds.py`(종료 코드 갈래, 비밀 가리기, 기록 묶음, 연달은 무효 회차), `test_llm_local_state.py`(잠금 동시성, `sweep` 반박, 구성 읽기, 실제 pytest 자식, 긴 경로). 클라우드가 없어도 돌고 윈도 junction과 리눅스 심볼릭 링크를 모두 만든다.
- `docs/constitution/tech.md`의 시험용 모델 서버 행을 고치고 헌법 판을 3.0.95로 올렸다. 마커 `llm_local`과 로컬 모델 시험은 05가 더한다.
- 변이 표 `.scratch/local-model/probes/llm_local_mutations.toml`(12건).

## 돌려서 본 것

- 시험 세 파일: 통과. 가짜 세계의 가짜 terraform이 `init`에서 `-state`를 요구하던 것이 시험 쪽 버그였고 `apply`와 `destroy`에서만 요구하도록 고쳤다.
- 원칙 III: 시험에 `# pyright: ignore`와 `# type: ignore`를 썼다가 가짜 세계가 기록하는 `terraform_envs`와 `server_options(record)` 헬퍼로 바꿨다. `check_type_escapes.py`는 초록이다.
- `uv run ruff check .`, `ruff format --check .`, `pyright`, `pyright --pythonplatform Linux`, `lint-imports`, `tools/check_instructions.py`(시간 제한 없는 호출과 지우는 호출 훅 포함), `tools/check_type_escapes.py`: 모두 초록이다. 줄 길이 지적은 독스트링 문단을 `tools/rewrap_comments.py`로 다시 감아 고쳤다.
- 손으로 한 반박(`.claude/rules/tools.md`): 표지 없는 폴더, 뿌리 밖을 가리키는 링크, 폴더 안의 링크, 살아 있는 잠금은 시험이 단언한다. 이 밖에 윈도에서 `uv run python -c`로 260자를 넘는 경로(417자, `\\?\` 접두로 만들었다)를 `delete_tree`로 지워 봤더니(손으로 봤다) `FileNotFoundError`로 폴더가 남았다. `scrub_state`는 같은 입력에서 예외를 그대로 던졌다. `long_path`(`\\?\` 접두, 정규화하지 않는다)로 고치고 `scrub_state`가 훑기에 실패하면 알리고 끝나게 했다. 시험 둘과 변이 하나로 고정했다.
- 변이(`tools/mutate.py`) 12건: 첫 실행에서 둘(잠금의 명령 줄 판정에서 하위 명령을 보지 않기, 키를 모를 때 상태 백업을 남기기)이 초록으로 남았다. 앞의 것은 시험에 `llm_local.py --help` 사례가 없었고 뒤의 것은 키를 아는 훑기가 백업까지 지워 가려졌다. 사례와 시험을 더해 다시 돌렸더니 12건 모두 기대대로 빨강이다(변이 7은 시험 선택을 바꿨다. 결과를 본 뒤 바꾼 기준이다). 첫 판의 변이 1은 표지(`precious.txt`)가 시험 원문에 글자 그대로 있어 변이 도구가 막았고 `FileNotFoundError`로 고쳤다.
- 가짜 세계 밖에서 확인하지 못한 것은 아래 "확인하지 못한 것"이다.

## 확인하지 못한 것

- 클라우드에서 돌려 보지 않았다. 구성의 자원 속성 이름(`args`, `cost_per_hr` 등), 프로바이더 2.0.0의 `args` 동작, REST 주소(`https://rest.runpod.io/v2/pods/$RUNPOD_POD_ID`)는 명세의 원문 인용에서 옮겼고 확인하지 않았다.
- 타이머는 첫째 방법(공식 이미지의 시작 명령을 셸로 바꿔 지우는 명령을 백그라운드로 건다)만 구성에 들었다. 둘째 방법(셸로 시작하는 기본 이미지에 vLLM을 설치)은 짓지 않았다. Runpod가 주입한 키로 파드가 지워지는지는 띄워 보지 않았다.
- `shared` 배치는 서버마다 포트가 다르다(8000, 8001). 티켓은 포트 하나만 연다고 적었다. 그 편차는 둘째 구성에 한해서고 확인하지 않았다.
- 시간 제한 값(`READY_LIMIT_SECONDS=1800`, 자식 3000초)은 어림이다. 준비 상한은 잰 준비 시간으로 다시 맞춘다(티켓).
- 헌법 판(3.0.95)은 형제 브랜치와 겹칠 수 있다. 커밋 직전에 `tools/sibling_overlap.py`로 본다.

## 인계 (셀프 리뷰 직전)

- 이 세션의 컨텍스트가 인계 문턱을 넘어 셀프 리뷰 직전에 넘긴다. 커밋하지 않았다. 지금 워크트리에 있는 것은 위 "한 것"의 파일 전부다(`tools/llm_local.py`, `tools/llm_local_server/`, `tests/tools/` 새 파일 넷, 변이 표와 프로브 README의 줄, `tech.md`와 헌법 판 3.0.95, 티켓 칸, 이 일지).
- `tools/run_checks.py` 전체 실행을 백그라운드로 띄웠다가 인계하며 멈췄다. 결과를 보지 못했다. 커밋의 pre-commit이 같은 검사를 돈다(`CLAUDE.md` 검증 명령 절).
- `code-review`는 불렀지만 서브에이전트를 띄우기 전에 넘겼다. 새 세션이 base SHA부터 다시 시작한다.
- 이 일지의 아래 "남은 일"은 닫는 세션이 retro에서 "다음"으로 옮긴다(2026-11-13 회고에서 옮겼다. 이 일지 끝의 "다음").
- open-session을 부른다 2026-11-13T05:28:05Z

## 셀프 리뷰 (인계받은 세션, base e5c709c96, 추적 4·미추적 8개 파일, 커밋 0)

두 축 보고를 받은 턴에 판정을 적는다. 고친 것과 다시 돌린 명령의 결과는 고친 뒤 이 절 아래에 덧붙인다.

고친다(근거를 코드에서 확인했다):

- 명세 1: `terraform_step`이 실패한 단계의 출력만 `OUT`에 넘겨 성공한 apply·destroy가 키를 되울려도 `terraform_output_masked`가 거짓이었다. 성공한 단계도 훑는다. 시험 자식 출력에서 가린 것이 이 칸을 참으로 만들던 것도 갈라 Terraform 몫만 센다.
- 명세 2: 앞 회차의 `junit.xml`과 `basetemp`를 시험 자식 전에 지우지 않아, 자식이 pytest가 아니면 앞 회차의 통과 수와 토큰이 이번 기록에 실렸다. 자식 전에 지운다.
- 명세 3: `launched`를 `terraform init` 앞에서 달아 init 중 Ctrl-C가 2로 나갔다. 명세는 띄우기(apply)를 시작하기 전에 끊기면 4다. apply 직전에 달고, 그 전에 끊기면 4로 끝낸다.
- 명세 5: `consecutive_invalid_rounds`를 시험만 불렀다. 무효 회차로 끝날 때 그 수를 찍고 둘 이상이면 세션이 멈춰 보고하라고 적는다.
- 표준 위험 둘째(코드를 읽은 판단): apply가 시간 제한에 걸려 죽으면 상태 파일이 없어도 다음 GPU 후보로 가서 파드를 더 띄운다. 그 자리에서 멈추고 3으로 끝내며 Runpod 콘솔 확인을 알린다.
- 표준 위험 첫째(코드를 읽은 판단): `execute`의 시간 제한과 Ctrl-C는 직계 자식만 죽인다. 윈도에서 `uv run pytest`는 pytest를 손자로 띄운다. 프로세스 트리를 끊는다.
- 명세 7·표준 1: `shared` 구성은 포트 둘을 연다(티켓은 하나). 일지가 이미 적은 편차다. 시험 이름과 단언을 사실대로 고치고, `main.tf`와 `llm_local.py`의 이미지·옵션·타이머·0.45가 어긋나지 않는지 보는 시험을 더한다.
- 명세 8: `main.tf` 머리 주석이 속성 이름을 명세의 원문 인용에서 옮겼다고 적은 것은 거짓이다(`cost_per_hr`·`gpu_type_ids` 등은 명세에 없다). 확인하지 않은 추정이라고 고친다.
- 명세 9·표준 4: 단가 표는 웹 요약에서 읽은 값이다. 독스트링과 출력에 그렇게 적고, 근거가 없는 Community Cloud가 더 싸다는 문장을 지운다.
- 표준 2: `sweep`은 산 잠금이나 표지 없는 폴더를 건드리지 않고도 0이다. 독스트링을 맞춘다.
- 표준 3: "(재고 없음)"은 init·apply의 어떤 실패에도 붙는다. 문구를 "재고 없음이나 다른 실패"로 고친다.
- 표준 5: probes README의 변이 표 행이 "시간은 재지 않았다"면서 519초를 적는다. 맞춘다.

남긴다:

- 명세 4(`lock_is_live`가 `sweep`도 산 잠금으로 본다): `sweep`이 같은 잠금을 쓰므로 필요하다. 독스트링에 적혀 있다. 티켓 문장("명령줄이 `run`일 때만")과의 차이는 이 일지가 적는다.
- 명세 6의 나머지(`terraform.tfstate`가 없는 폴더를 `sweep`이 지운다): apply가 죽어 상태가 안 쓰인 고아 파드는 상태로 알 수 없다. 위 apply 시간 제한 고침과 90분 타이머가 받친다.
- 표준 스멜 Duplicated Code(`tools/tidy_checkouts.py`의 `delete_path`·`long_path`와 같은 모양): 이 파일의 지우기는 12건의 변이와 긴 경로 반박(417자)으로 고정돼 있고 `delete_path`는 홈 가드와 `str` 경로의 다른 계약이다. 합치는 일은 이 티켓의 몫이 아니라 회고 후보다.
- 표준 스멜 Divergent Change(1055줄 한 파일), Data Clumps(`(url, model_id, key)` 삼중쌍), Primitive Obsession(`invalid_reason` 문자열): 판단 호출이고 명세가 한 파일을 정했다. 05가 환경 변수 상수를 import하는 모양을 바꾸지 않는다.
- 표준 코드 위험 셋째(옛 서버 키를 모르는 `destroy_folder(…, None)`의 출력): 변수가 `sensitive`라 화면에서 가려진다. 시험이 없다. 띄워 확인할 때 본다.

고친 뒤(같은 세션):

- 위 "고친다" 열한 줄을 모두 반영했다. 코드는 `tools/llm_local.py`(`execute`의 프로세스 트리 종료, `Reporter.watch_terraform`, `clear_results`, 첫 apply 앞에서 `launched`, 시간 제한에 걸린 apply 뒤 3으로 멈춤, 무효 회차 연속 수 출력, 문구)와 `tools/llm_local_server/main.tf` 머리 주석, 시험은 `tests/tools/`의 새 시험 아홉(월드에 `interrupt_on_init`·`apply_times_out`·`child_echoes_key`를 더했다), 변이 표 13~17, probes README 두 행과 티켓의 편차 두 줄이다.
- 다시 돌린 명령(출력을 이 세션이 봤다): `uv run ruff check .`와 `ruff format --check .`, `uv run pyright`와 `--pythonplatform Linux`, `uv run lint-imports`, `tools/check_instructions.py`, `tools/check_type_escapes.py`는 모두 초록, `terraform fmt -check`는 출력 없이 끝났다, 시험 세 파일 68개 통과, 변이 13~17은 모두 기대대로 빨강이다(`PYTHONUTF8=1 uv run python tools/mutate.py .scratch/local-model/probes/llm_local_mutations.toml 13 14 15 16 17`). 변이 1~12는 코드를 옮겼으므로 `--check`로 원문부터 봤다(17건 모두 원문이 한 번씩 있다).
- 첫 커밋 시도는 pre-commit의 변이 표 검사(`tools/mutate.py --staged`)가 빨강을 기대한 변이 열일곱 모두에 `expect_output`이 없다고 막았다(나머지 게이트는 그 시도에서 통과했다. pytest 893초, web-verify 1165초). 임시 표지로 한 바퀴 돌려 실패 머리를 보고(탐침이 찍은 것), 표지를 열여섯에 더했다(1번은 있었다). 시험 원문에 있는 문구는 표지가 못 되어, 시험 아홉에 단언 메시지(제품이 만든 값이 실린다)를 더하고 표지를 골랐다. 그 뒤 변이 표 한 바퀴가 "변이 17 모두 기대대로"로 끝났다(탐침이 찍은 것).
- 모르는 것: 윈도의 `taskkill /T`와 `start_new_session`·`killpg` 길은 이 PC(윈도 10)에서만 시험이 단언했다. 리눅스 길은 pyright만 통과했고 CI의 리눅스에서 처음 돈다(코드를 읽은 것).
- 밀 주장(PR 직전 `bug-perf-review`가 겨눌 문장): (1) `execute`는 시간 제한과 Ctrl-C 모두에서 프로세스 트리를 끊는다, (2) 성공한 terraform 단계의 출력도 `terraform_output_masked`를 센다, (3) 첫 `apply` 앞에서 끊기면 4, 그 뒤면 2다, (4) apply가 시간 제한에 걸려 상태 파일에 자원이 없으면 다음 후보로 가지 않고 3이다.
- 표지를 더한 뒤의 재시도가 커밋 `d2a4403`이 되어 pre-commit 게이트를 모두 통과했다. 티켓은 `in-progress`이고 PR은 열지 않았다.

## 회고

후보 일곱, 승인 하나, 기각 여섯, 사용자에게 넘긴 것 없음. 만료할 항목은 없었다(`uv run python tools/queue_open_rows.py`).

- **승인** 변이 표를 짓는 때 `expect_output`을 정하지 않아, 표지 없는 빨강 열일곱이 약 20분짜리 커밋 시도를 한 바퀴 돈 끝에서야 `mutate.py --staged`에 막혔다. 사건과 층(지침 한 줄이나 검사 앞의 순서), 되돌림(PR 하나)은 서지만 더하는 것이라 문턱 앞이다. 대기열 `mutation-table-checked-late`에 1회차로 새로 썼다(0350은 검사를 들이며 닫혔고 이 사건은 그 검사가 있는 채로 난 것이라 잇지 않았다. 표지 고르기의 질은 0579가 센다). pre-commit은 훅을 모두 돌고 `fail_fast`가 없어, `check-mutations`를 앞으로 옮겨도 한 바퀴가 줄지 않는다는 것을 설정과 `operations.md`로 확인했다.
- **기각** 표지 17번을 시험 원문과 호출 꼴 규칙에 걸리는 문구로 골랐던 것: 이미 있는 `--check`가 그 자리에서 알렸다(0579는 검사가 알리지 못한 것을 세는 항목이라 회차를 더하지 않는다).
- **기각** 단언 메시지 없이 쓴 시험 아홉에 표지를 달기 위해 메시지를 더한 것: 위 승인과 같은 사건이다.
- **기각** `tools/tidy_checkouts.py`의 `delete_path`·`long_path`와 같은 모양이 `tools/llm_local.py`에 또 있는 것(Duplicated Code): 아직 한쪽만 틀어진 사건이 없다. 한쪽의 지우기 결함이 다른 쪽에 없는 것으로 드러나면 그 사건으로 합친다.
- **기각** 윈도에서만 시험한 `killpg` 길: `tests/tools/`의 시험은 CI의 리눅스에서도 돌고(`.claude/rules/tests.md`), 그 길은 CI가 처음 잰다.
- **기각** 첫 스크래치 스크립트 쓰기를 `hook_scratch_probe_reread`가, 40줄 넘는 heredoc과 맨 `python3`를 훅이, 81자 커밋 제목을 커밋 검사가 막은 것: 모두 이미 있는 훅과 검사가 그 자리에서 막았다.
- **기각** 컨텍스트가 인계 문턱을 넘어 셀프 리뷰 직전에 넘긴 것: 인계 훅이 설계대로 돈 것이다.

## 다음

1. 사용자가 준비를 마쳐야 한다. 주 체크아웃의 `.env`에 `RUNPOD_API_KEY`(Runpod 계정과 크레딧, 자동 충전은 켜지 않는다)와 Terraform 1.6 이상이 있어야 한다. 이 PC는 Terraform이 1.5.5다. 모자라면 사용자에게 알리고 멈춘다.
2. 준비가 되면 `--yes` 없이 `uv run --env-file ../../../.env python tools/llm_local.py run`을 쳐 비용을 사용자에게 보이고 확인을 받은 뒤 `--yes`와 `--` 뒤의 도구 호출 프로브로 띄운다. 티켓의 "띄워 확인하는 것" 칸을 채운다. 결과가 명세와 다르면 명세에 날짜를 단 주석으로 적고, ADR 0058 본문이 거짓이 되면 이력 초안을 쓰고 승인을 받는다. 처음 띄우는 길에서 볼 것은 이 일지의 "남긴다" 셋째(옛 서버 키를 모르는 `destroy_folder`의 출력이 키를 가리는지), `main.tf`의 속성 이름과 공식 이미지의 시작 명령이 `args`를 삼키는지다.
3. 그 확인이 끝난 뒤 상태를 `done`으로 바꾸고 PR을 연다. 그 전에는 PR을 열지 않는다(확인 칸이 빈 채 `done`이 되면 05가 풀린다). PR 직전 리뷰(`bug-perf-review`)에는 위 "밀 주장" 넷을 넘긴다.
4. 05가 `tech.md`의 같은 행을 마커까지 든 사실로 다시 고친다.
