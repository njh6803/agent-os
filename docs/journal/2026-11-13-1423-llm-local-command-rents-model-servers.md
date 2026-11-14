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
- `tools/llm_local_server/main.tf`: 프로바이더 `runpod/runpod` `= 2.0.0`, vLLM 공식 이미지 0.33.0, 구성 둘(`pods`: 모델마다 파드 하나, `shared`: A40 한 장에 서버 둘)이다. 타이머는 90분 뒤 `runpodctl pod delete`로, 없으면 REST DELETE로 파드를 지운다(2026-11-13 구현 시점의 서술이다. 2026-11-14에 이 명령은 동작하지 않는 것으로 드러나 `runpodctl remove pod`만 쓰게 고쳤다. 아래 "타이머를 10분으로 줄여 띄운 한 바퀴" 절). 계정 키는 구성에 싣지 않고 서버 키만 `sensitive` 변수로 받는다. `terraform fmt -check`만 통과했고 `plan`은 돌리지 않았다.
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

(이 절은 2026-11-13 구현 시점의 것이다. 2026-11-14에 클라우드에서 본 것은 아래 "실제로 띄운 것"과 "고친 뒤 `run` 한 바퀴" 절이 이 절의 일부를 갱신한다.)

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

## 실제로 띄운 것 (2026-11-13 밤~2026-11-14, 사용자 승인 아래)

> 사용자: 준비 됐어 / 띄운다 / 다시 띄운다 / 30분마다 다시 시도 / 로그 보며 한 번 더

아래는 Runpod 플러그인의 읽기 도구(`list-pods`, `stream-pod-logs`, `list-pod-billing`)와 `exec-pod`의 출력, 명령의 출력 파일을 이 세션이 손으로 본 것이다. 서버를 띄우고 로그를 읽는 과정은 스크립트로 잰 값이 아니다. 예외가 하나 있다. 도구 호출 확인(아래)은 `.scratch/local-model/probes/live_tool_call.py`가 잰 값이다.

- 첫 실행은 `Unsupported argument`(`image_name`, `gpu_type_ids`, `cloud_type`, `container_disk_in_gb`, `volume_in_gb`)로 끝났다. 프로바이더 스키마와 플러그인의 `create-pod` 설명으로 `main.tf`의 속성 이름을 `image`, `gpu_type_id`, `cloud`, `disk`, `args`로 고쳤다. 파드는 만들어지지 않았다.
- 그 뒤 열네 번 띄웠다(상태 폴더의 회차 파일이 15개다). 아홉 번은 후보마다 400(재고 없음)으로 끝났다. 그 가운데 한 번은 A40 두 장 후보에서 파드 하나가 만들어진 뒤 둘째가 400이라 apply가 실패했고, 만들어진 파드는 명령이 지웠다. 나머지 여덟 번은 파드가 만들어지지 않았다. 다섯 번은 앞 후보가 모두 재고 부족이고 마지막 후보 `shared / A40 x 1`이 만들어졌다. 앞 넷은 서버가 준비 상한 30분 안에 응답하지 않아 명령이 파드를 지웠고(종료 코드 2), 다섯째가 이번 실행이다.
- 30분마다 다시 치는 재시도 스크립트(스크래치패드)가 판정을 출력 전체에 재고 없음 문구(영문 `no longer any instances`)가 있는지로 했다. 마지막 후보가 파드를 만들고 준비 상한을 넘겨 실패한 시도도 앞 후보의 재고 부족 문구에 걸려 재고 부족으로 읽혔다. 다른 종류의 실패면 멈추겠다고 사용자에게 알린 약속과 어긋났고, 같은 구성을 네 번 반복했다. 판정은 마지막 후보의 결과만 봐야 한다.
- Runpod 청구(`list-pod-billing`, 11월 12~13일 UTC 하루 단위, 파드 여덟): 합계 $0.947(GPU $0.934, 디스크 $0.0125). 30분가량 돈 파드 셋이 각각 약 $0.30이다. 11월 14일 UTC의 이번 실행은 이 합계에 없다.

서버가 준비되지 않은 원인은 둘이었고, 둘 다 코드의 결함이다.

1. 명령의 준비 확인이 파드에 닿지 못했다. 파이썬 `urllib`의 기본 `User-Agent`는 Runpod 프록시에서 403(`error code: 1010`)이고, 다른 값을 붙이면 200이었다(같은 주소에 `curl`로 `/health` 200). 서버가 떠 있어도 `fetch_models`가 늘 `None`을 받았고, 파드 쪽 접근 로그에 `/v1/models` 요청이 한 줄도 없었다. 이 거절은 첫 네 번의 30분에도 있었을 것으로 읽지만, 그때는 파드 로그를 보지 못해 그 네 번 서버가 떠 있었는지는 모른다. 시험 세계가 `fetch_models`를 통째로 바꿔 끼워 이 거절을 가렸다.
2. 한 GPU에 서버 둘을 `--gpu-memory-utilization 0.45`로 띄우면 A.X가 시작에 실패했다. 서버 둘을 동시에 시작하면 A.X 엔진이 `Available KV cache memory: -10.5 GiB`와 `No available memory for the cache blocks`로 죽었다(gpt-oss가 같은 시각에 메모리를 올리고 있었다). gpt-oss만 남은 뒤 A.X를 따로 시작해 보니 `Free memory on device (10.56/44.42 GiB) on startup is less than desired GPU memory utilization (0.45, 19.99 GiB)`로 다시 실패했다. gpt-oss 하나가 GPU 메모리를 약 34 GiB 쓰고 있었다(로그가 적은 가중치 약 13.8, KV 캐시 18.19, 활성화 1.56, CUDA 그래프 0.26 GiB를 더한 값이 약 33.8이다). `--kv-cache-memory=4294967296`(서버마다 KV 캐시 4 GiB)를 더해 gpt-oss를 먼저, 응답하면 A.X를 시작하니 둘 다 떴고(`nvidia-smi` 38.8 GiB) 시작 로그는 gpt-oss 02:06:58, A.X 02:07:40(UTC)이다. 이 확인은 같은 파드 안에서 `exec-pod`로 서버를 손으로 다시 띄운 것이라 `main.tf`로 띄운 구성의 확인이 아니다.

고친 것(이 커밋 앞): `tools/llm_local.py`의 `fetch_models`가 `User-Agent: agent-os-llm-local`을 보낸다. `main.tf`의 `shared`는 서버마다 `--kv-cache-memory=${var.shared_kv_cache_bytes}`(4 GiB)를 주고 서버를 차례로 띄우되 앞 서버의 `/health`가 응답한 뒤에 다음을 시작한다. `pods`는 바뀌지 않았다. 시험 셋(`test_llm_local_state.py`의 새 시험 둘과 기본값 단언)을 먼저 쓰고 빨강을 본 뒤 고쳤다(User-Agent 시험은 빨강 출력을 봤다. KV 캐시 시험은 상수가 없어 pyright가 먼저 빨갛게 알렸다). 같은 시험 세 파일 70개 통과, ruff·pyright 초록, `terraform fmt -check`와 `validate`(상태 폴더의 `.tfdata`로) 통과다.

이 실행이 확인한 티켓 칸:

- 프로바이더 `runpod/runpod` 2.0.0과 `args`(JSON 객체로 `entrypoint` `/bin/bash -c`와 `cmd`)는 서고, 공식 이미지가 그 시작 명령으로 `vllm serve` 둘과 타이머 줄을 실행했다(파드 로그와 `list-pods`의 `entrypoint`·`cmd`).
- 프록시 주소의 꼴은 `https://<파드id>-<포트>.proxy.runpod.net/v1`이고 8000과 8001 모두 `/health` 200이었다.
- Terraform `cost`와 `list-pods`의 `cost`가 둘 다 0.59(A40, Secure)로 단가 표 0.59와 같다.
- 준비까지의 시간: 파드 생성 02:02:13Z, gpt-oss 단독 시작 02:02:14Z부터 `Application startup complete` 02:04:07Z까지 약 113초(이미지는 내려받지 않았다, `Status: Image is up to date`). 위의 순차 시작은 앞 서버 종료 15초를 포함한다. 서버 둘이 서는 데 gpt-oss 02:06:58에서 A.X 02:07:40까지 42초가 더 걸렸다.
- 두 모델이 도구 요청에 답한다: `exec-pod`로 손으로 띄운 두 서버(`main.tf`가 띄운 것이 아니다)에 `.scratch/local-model/probes/live_tool_call.py`를 돌려 둘 다 `finish_reason: tool_calls`와 `get_weather` 호출 하나(도시 인자 있음)가 나왔다. 응답의 `model`은 요청과 같다. 걸린 시간 A.X 2.0초, gpt-oss 2.9초는 그 프로브가 잰 값이고, 두 회차 모두 서버가 200으로 JSON을 냈다는 표지를 본 측정이었다(표지 없는 회차는 없었다). 이 돌림은 상태 파일에서 키를 읽는 스크래치 스크립트가 서버 둘의 주소와 키를 환경 변수로 넘겼다.

명령은 준비 상한(1838.2초)을 넘겨 종료 코드 2로 끝났고(회차 파일 `round-0015-20261114T023227Z.json`, 연달은 무효 회차 15번) 파드를 지웠다. 끝난 뒤 `list-pods`는 빈 목록이었고, 상태 폴더(`terraform.tfstate`와 백업은 없고 `records/`만 남았다)에서 서버 키 꼴(`sk-local-`)이 든 파일은 0개였다(`grep -rl`로 센 수, 값은 찍지 않았다). 이 회차의 `terraform_output_masked`는 참이었다. 이 실행이 확인하지 못한 티켓 칸: 구성 1(`pods`, 파드 둘)이 서는지(재고가 없었다. A40 두 장 후보에서 한 번은 파드 하나만 만들어지고 둘째가 400이라 apply가 실패했고 만들어진 파드가 지워졌다), 90분 타이머가 Runpod가 주입한 키로 실제로 파드를 지우는지(모든 파드를 명령이 먼저 지웠다), 고친 `main.tf`(KV 고정과 순차 시작)가 `run`으로 서는지, 시작 순서가 A.X 먼저 gpt-oss 나중일 때의 메모리(손으로 본 순서는 gpt-oss 먼저)다. 프로바이더가 `Reading the deprecated pod attributes from the GraphQL API failed`(401) 경고를 냈다.

비밀: 서버 키(이 실행만의 임시 키)가 `list-pods`의 `args`에 평문으로 실려 이 세션의 도구 출력에 보였다. 파드의 `args`와 상태 파일에 서버 키가 들어가는 설계의 결과이고, 키는 파드가 지워지면 쓸모가 없다.

## 고친 뒤 `run` 한 바퀴 (2026-11-14, 커밋 `483ad85ec`)

> 사용자: 비용 보여 줘 / 승인

`--yes` 없이 친 출력으로 후보별 예상 비용(시간당·어림 30분·최악 90분)을 사용자에게 보이고 승인을 받은 뒤, `uv run --env-file ../../../.env python tools/llm_local.py run --yes -- uv run python .scratch/local-model/probes/live_tool_call.py`를 한 번만 쳤다. 재시도 스크립트는 쓰지 않았다. 아래는 명령의 출력과 회차 파일(`round-0016-20261114T040055Z.json`), Runpod 플러그인의 `list-pods`·`list-pod-billing`을 이 세션이 손으로 본 것이다. 도구 호출 응답은 프로브가 잰 값이다.

- 종료 코드 0. 후보는 둘을 거쳤다. `pods / RTX A5000 x 2`는 파드 둘을 만들다 하나(`6qjw1mpjutgm99`)만 만들어지고 다른 하나가 400(재고 없음)이라 `terraform apply`가 종료 코드 1로 실패했다. 명령은 다음 후보 `pods / RTX 3090 x 2`로 넘어갔고, 끝난 뒤 `list-pods`가 빈 목록이었으므로 A5000의 파드 하나는 지워진 것이다. 일부만 만든 `apply`의 파드를 명령이 지우는 것은 코드(`_launch_and_test`가 상태에 자원이 남았으면 `destroy_folder`를 부른다)를 읽은 해석이고, 앞 실행(A40 두 장 후보)에서도 본 것이라 이번에 새로 확인한 것은 아니다.
- 3090 두 장 구성에서 파드 둘이 서고 두 모델이 모두 도구 요청에 `tool_calls`로 답했다. A.X 1.8초, gpt-oss 2.7초이고 응답의 `model`은 요청과 같다. 프로브는 `측정 2회차, 측정 아님 0회차`로 끝났다. 이것이 구성 1(`pods`)이 서는 첫 확인이고, `run`이 끝까지 돈 첫 한 바퀴다. 같은 모델 둘이 이번에는 `main.tf`가 띄운 서버에서 답했다(앞의 확인은 `exec-pod`로 손으로 띄운 서버였다).
- `elapsed_seconds` 472.4초는 비용 표를 찍고 `--yes`로 상태를 만든 때(`_run`의 `Round(...)` 줄)부터 기록을 쓸 때까지다. 코드를 열어 보니 `_launch_and_test`가 시험 뒤 `destroy_folder`를 마치고 `_finish`를 부르므로 A5000 후보의 실패, 3090의 준비 대기, 프로브(두 응답 합 약 4.5초), 지우기를 모두 포함한다. 준비까지의 시간만은 이 실행에서 따로 재지 않았다.
- 기록 묶음(`_finish`가 찍은 것): 커밋 `483ad85ec`, 엔진 vLLM 0.33.0(`vllm/vllm-openai:v0.33.0`), GPU `RTX 3090`, 구성 `pods`, 가격 표 날짜 2026-11-13, `cost_per_hour` 1.0, 시험 명령 종료 코드 0, 이유 `시험이 끝났다`, 명령 종료 코드 0이다. 서버 옵션은 키 없이 실렸고(`--host 0.0.0.0 --port 8000 --enable-auto-tool-choice`와 파서 `hermes`·`openai`) `terraform_output_masked`는 참이다. `shared`가 아니라 `pods`이므로 KV 캐시 고정은 이 실행에 쓰이지 않았다.
- `cost_per_hour` 1.0은 가격 표의 값이 아니라 `parse_outputs`가 Terraform 출력(`cost_per_hr`)의 파드별 값을 합한 것이다(`state.hourly`). 명령은 이 값이 후보의 예상(0.50 × 2)을 넘으면 회차를 무효로 치는데 이번에는 넘지 않았다. 그래서 3090 두 장의 Terraform `cost`가 단가 표 시간당 $1.00과 같은 것을 봤다. A5000은 파드 하나가 만들어지다 실패해 출력이 없다.
- 끝난 뒤 `list-pods`는 빈 목록이었다. 상태 폴더(`.agent-os-llm-local`, `.tfdata`, `records/`)에서 서버 키 꼴(`sk-local-`)이 든 파일은 0개였다(`grep -rl`로 센 수).
- 비용: 3090 두 장은 시간당 $1.00이라 472초(A5000의 실패와 지우기까지 든 시간이라 3090 파드의 가동 시간보다 길다)를 곱하면 $0.13 안쪽이다. 이것은 곱셈으로 어림한 상한이고 청구서의 값이 아니다. 이 실행 직후 `list-pod-billing`(일 단위, 마지막 2일)에는 이 실행의 A5000 파드 `6qjw1mpjutgm99`가 없었다(3090 파드의 ID는 보지 않았다). 청구가 늦게 오르는지는 모른다. 그때 보이던 11월 13~14일 청구 합계는 $1.509이고 이 실행의 값이 든 것으로 볼 근거가 없다.
- A5000 후보의 `apply` 출력에서만 프로바이더가 `Reading the deprecated pod attributes from the GraphQL API failed`(401) 경고를 냈다. 3090 후보 구간의 출력에는 경고가 없었다.

이 실행으로 새로 확인한 티켓 칸: 구성 1(`pods`, 3090 두 장)이 서고 두 모델이 `main.tf`가 띄운 서버에서 답한다, 고친 `main.tf`와 `User-Agent` 고침이 `run`으로 끝까지 돈다, 3090 두 장의 Terraform `cost`가 단가 표와 같다(위 `cost_per_hour`). 확인하지 못한 칸: 90분 타이머가 Runpod가 주입한 키로 실제로 파드를 지우는지(앞의 열다섯 회차와 이번 회차 모두 명령이 먼저 지웠다), 타이머가 지운 뒤의 `terraform destroy`, A5000의 Terraform `cost`, 준비까지의 시간, `shared`가 `main.tf`의 순서(A.X 먼저)로 서는지(이번에는 `pods`가 서서 `shared`까지 가지 않았다).

## 셀프 리뷰 (2026-11-14, 클라우드 실행 뒤의 고침과 글)

범위는 `origin/dev` 기준 작업 트리 전체(수정 여섯 파일, 미추적 `live_tool_call.py`와 `.terraform.lock.hcl`)다. 표준 축과 명세 축을 나란히 돌렸다. 서브에이전트의 보고는 모델이 쓴 글이라 지적마다 파일을 열어 확인한 뒤 판정했다.

고친 것:
- 프로브 `README.md`의 도입부가 "실제 모델 서버는 쓰지 않는다"로 새 프로브 `live_tool_call.py`와 어긋나, 그 프로브만 예외라고 적었다. 프로브 독스트링의 "표준 라이브러리만 쓴다"는 `tools/probe_kit.py`를 가져다 쓰는 것과 어긋나 고쳤다.
- 근거 문장의 종류를 바로잡았다. 코드·시험·프로브 주석의 "실측"은 "손으로 봤다"로 바꿨고, `llm_local.py` 독스트링의 "못 보는 것"에 지금 본 것과 못 본 것(`pods`, 90분 타이머)을 나눠 적었다.
- 명세·티켓의 "클라우드에서 돌려 보지 않았다"를 2026-11-14에 본 만큼으로 좁히고, 구성 2는 `main.tf`가 아니라 `exec-pod`로 손으로 띄운 서버에서 본 것이며 `main.tf`의 모양(A.X 먼저, 고정 KV 캐시, 순차 시작)은 띄워 보지 않았다고 적었다.
- 이 일지의 "실제로 띄운 것": 프로브가 잰 값과 손으로 본 값을 가르고, 열네 번 가운데 파드가 하나 만들어졌다 지워진 한 번을 따로 적고, 34 GiB의 합산을 더했다.
- 회차 수를 열세 번에서 열네 번으로 고쳤다(회차 파일 열다섯 개에서 첫 실행의 속성 오류 하나를 뺀 수).
- `main.tf`의 시험 앞 서버가 죽으면 대기 루프가 끝나지 않는다는 것을 주석으로 적었다(명령의 준비 상한과 90분 타이머가 파드를 지운다).

남긴 것과 이유:
- 4 GiB 값이 `llm_local.py`와 `main.tf`에 두 번 적혀 있다. 시험이 같음을 단언해 어긋나면 빨개진다. 하나로 줄이려면 `main.tf`의 기본값을 없애고 늘 명령이 넘기게 해야 하는데, 그러면 `terraform` 단독 실행이 막혀 이번에는 두었다.
- 프로브와 `llm_local.py`가 같은 `USER_AGENT` 문자열을 따로 적었다. 프로브는 `tools` 밖의 일회용이라 import하지 않았다.
- `.terraform.lock.hcl`에 한 플랫폼의 `h1:` 해시와 `zh:` 해시가 든다. 다른 플랫폼(CI의 리눅스)에서 `terraform init`이 해시를 더 쓰려 하면 고쳐야 한다. 이 명령은 사용자의 PC(윈도)에서만 돌리는 도구라 지금은 두었고, CI에서 `terraform init`을 돌리는지는 확인하지 않았다.

PR 직전 `bug-perf-review`에 밀 주장(이 고침으로 새로 쓴 사실 문장):
- 공식 이미지가 `args`로 `vllm serve`를 실행한다는 것(`main.tf` 머리 주석. 파드 로그로 봤다).
- 서버 둘을 동시에 시작하면 A.X가 KV 캐시 `-10.5 GiB`로 죽고 순차로 시작하면 둘 다 뜬다는 것(손으로 띄운 서버에서만 봤고 `main.tf`로는 안 봤다).
- Runpod 프록시가 파이썬 `urllib`의 기본 `User-Agent`를 403으로 거절한다는 것(손으로 `curl`과 대 봤고 시험은 지어낸 서버로 같은 모양을 만든다).
- 앞 서버가 죽으면 대기 루프가 끝나지 않고 명령의 준비 상한과 90분 타이머가 파드를 지운다는 것(타이머가 지우는 것은 아직 못 봤다).

다시 돌린 명령(고친 뒤): 시험 세 파일 70개 통과, `ruff check`·`ruff format --check` 초록, `pyright` 0 오류, `terraform fmt -check` 통과.

첫 커밋 시도의 pre-commit(21분 24초): pytest 7303개 가운데 `tests/tools/test_rerun_runner.py`의 `test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다` 하나가 `assert board.run() == 0`에서 1로 실패했고(그 시험은 `hang=3.0`초를 쓰는 시간 시험이다), 나머지 훅은 통과했다. 같은 시험을 홀로 돌리니 15.41초에 통과했다. 이 브랜치는 그 시험이 읽는 파일을 건드리지 않았고, 부하에서만 빨개지는 시간 시험이라고 읽는다(대기열 306의 종류). 이 사례는 일지에만 적고 시험은 고치지 않는다. 같은 시험이 두 번 연속 빨가면 추측하지 않고 `diagnosing-bugs`로 넘어간다.

## 셀프 리뷰 (2026-11-14, `run` 결과를 적은 문서 변경)

범위는 `git diff HEAD`의 문서 셋(티켓, 명세, 이 일지)이다. 표준 축과 명세 축을 나란히 돌렸고, 두 보고가 모델이 쓴 글이라 지적마다 코드(`tools/llm_local.py`)와 출력 파일을 열어 확인한 뒤 판정했다.

고친 것(확인해 보니 맞았다):
- 3090의 Terraform `cost`를 "보지 않았다"고 쓴 것이 틀렸다. 기록의 `cost_per_hour`는 `parse_outputs`가 Terraform 출력의 `cost_per_hr`를 합한 값이고(753·967행), 이번에 통과한 상한 검사(968~971행)에 쓰였다. 확인한 칸으로 옮기고 A5000만 미확인으로 남겼다.
- `elapsed_seconds`를 지우기 포함 여부를 모른다고 쓴 것이 틀렸다. 코드를 열어 보니 지우기(931~932행) 뒤에 `_finish`(1069행)가 재므로 지우기까지 든다. 포함 항목을 바로잡았다.
- A5000 파드의 청구를 $0.0016이라 쓴 것은 근거가 없었다. 그 청구 행의 파드 ID는 이 실행의 A5000 파드(`6qjw1mpjutgm99`)와 달랐다. 청구 서술을 지금 보인 것(그 ID가 청구 목록에 없었다, 합계 $1.509)으로 다시 쓰고 `$0.13`은 상한이라고 밝혔다.
- 프로바이더의 401 경고는 A5000 후보 구간에만 있었다.
- "두 번의 `run` 모두 명령이 먼저 지웠다"를 앞의 열다섯 회차와 이번 회차로 고쳤다. 일부만 만든 `apply`의 파드를 명령이 지우는 것은 새로 확인한 것이 아니라 코드를 읽은 해석이고 앞 실행에서도 본 것이라고 고쳤다.
- 타이머 시간을 밖에서 받는지를 코드를 열기 전에 모른다고 쓴 것을 고쳤다(`TIMER_MINUTES = 90`을 `TF_VAR_timer_minutes`로 고정해 넘긴다).
- 명세 구성 1에 날짜 주석을 더했고, 프로브 README의 `live_tool_call.py` 줄에 이번 판(RTX 3090, 명령의 자식으로 돈 것)을 더했고, 옛 시점 문구에 시점 표시를 달았고, 기록 묶음의 필드를 일지에 옮겼다.

남긴 것과 이유: 일지 "확인하지 못한 것" 절 셋째 항목 이하의 옛 문장은 2026-11-13 구현 시점의 기록이라 지우지 않고 절 머리에 시점 표시를 달았다. 이번 결과의 $ 값은 청구서에서 읽은 것이 아니고, 청구가 늦게 오르는지는 모른다. 청구서가 올라온 뒤 그 값을 적는 일은 다음 확인 때 한다.

다시 돌린 명령: 문서만 바뀌었다. 커밋이 부르는 pre-commit(인용 대조, 표, 줄 구분 문자 검사 포함)에 맡긴다.

## 타이머를 10분으로 줄여 띄운 한 바퀴 (2026-11-14, 커밋 `bc9e19b17` 위의 임시 변경)

> 사용자: 비용 보여 줘 / 승인

타이머만 보려고 `tools/llm_local.py`의 `TIMER_MINUTES`를 90에서 10으로 임시로 바꾸고(커밋하지 않았고 끝난 뒤 `git checkout`으로 되돌렸다), 명령의 `--` 뒤 자식으로 서버가 준비된 뒤 720초 자는 스크래치 스크립트(`sleep_child.py`, 서버는 쓰지 않는다)를 넣어 한 번 띄웠다. 아래는 명령의 출력, 회차 파일(`round-0017-20261114T045104Z.json`), Runpod 플러그인의 `list-pods`·`stream-pod-logs`·`exec-pod` 출력을 이 세션이 손으로 본 것이다. 측정 스크립트로 잰 값은 없다.

- 후보는 넷을 거쳤다. RTX A5000 두 장과 A40 두 장은 파드 둘 가운데 하나만 만들어지고 다른 하나가 재고 없음(400)이라 `apply`가 실패했다(`list-pods`로 파드 하나씩 남은 것을 봤고, 명령이 다음 후보로 넘어가며 지웠다). RTX 3090 두 장도 같았다(명령 출력에 파드 `eadc7jm3u1glup`이 만들어진 뒤 다른 하나가 400이라는 줄이 있다. 그 파드가 `list-pods`에 남았는지는 보지 못했고, 다음 후보로 넘어갔다). 마지막 `shared / A40 x 1`이 섰다.
- `shared`가 `main.tf`의 새 순서(A.X 먼저, 고정 KV 캐시 4 GiB, 앞 서버의 `/health` 뒤에 다음 서버)로 섰다. 명령의 준비 확인이 통과해 자식이 시작됐다. 파드 생성 04:36:06Z에서 자식 시작 04:39:01Z까지 약 175초다. 이것이 A.X 먼저일 때의 메모리가 서는지에 대한 답이다. 이 실행의 자식은 잠만 자서 도구 호출 응답은 이번에 `shared`로 보지 않았다(손으로 띄운 서버에서는 앞서 봤다).
- 타이머는 파드를 지우지 못했다. 파드 생성 10분 2초 뒤(04:46:08Z)에 타이머가 실행됐지만 컨테이너 로그에 `Error: unknown command "pod" for "runpodctl"`가 남았고 파드는 계속 `RUNNING`이었다(04:47:51Z `list-pods`. 04:48:03Z에 `exec-pod`로 친 `ps`가 시작 명령의 경과 시간을 714초로 찍었다). 이미지의 `runpodctl`은 `1.14.15-dac76ad`이고 `pod` 하위 명령이 없다(도움말에 `remove`, `stop` 등이 있다). 구성이 `runpodctl`이 있으면 `curl` 갈래로 넘어가지 않게 짜서, 그 한 번의 실패로 타이머가 끝났다. 앞 회차들은 같은 이미지 태그(`vllm/vllm-openai:v0.33.0`)를 썼으므로 90분 타이머도 같은 이유로 파드를 지우지 못했을 것으로 미루어 읽는다. 그 회차들은 명령이 먼저 지워 타이머가 도는 것을 보지 못했다.
- `curl` 갈래도 동작하지 않았다. 파드 안에서 주입된 키로 `DELETE https://rest.runpod.io/v2/pods/<파드 ID>`를 치니 HTTP 301이었고 이동 위치는 `https://docs.runpod.io/api-reference-v2/overview`였다. 같은 키로 `GET /v1/pods/<파드 ID>`는 403, `GET /v2/pods/<파드 ID>`는 301이었다.
- 파드 안에서 `runpodctl remove pod "$RUNPOD_POD_ID"`를 치니 `pod "ac64ykj9aq0gso" removed`로 끝났고 이어 `list-pods`가 빈 목록이었다. 곧 주입된 키로 이 명령이 파드를 한 번 지운 것을 봤다(04:48:52Z. 이 한 번은 이 세션이 타이머를 대신해 `exec-pod`로 친 것이다).
- 그 뒤 명령은 자식이 끝나는 04:51:01Z까지 기다린 뒤 종료 코드 0으로 끝났고 이유는 `시험이 끝났다`였다(`지우기 실패`가 아니다). 이미 지워진 파드가 있는 상태에서 명령의 지우기(`destroy_folder`)가 끝난 것은 회차 파일에서 읽었다. 다만 `destroy_folder`는 첫 `terraform destroy`가 실패하면 `apply -refresh-only`로 상태를 맞춘 뒤 다시 `destroy`하고 그것이 성공하면 참을 돌려주므로, 첫 `destroy`가 성공했는지 재시도 뒤에 성공했는지는 모른다(명령의 `destroy` 출력 줄은 보지 않았다). 끝난 뒤 `list-pods`는 빈 목록이었고 상태 폴더에서 서버 키 꼴(`sk-local-`)이 든 파일은 0개였다.
- 비용: `shared`의 A40(Terraform이 돌려준 `cost` 0.59, 회차 파일의 `cost_per_hour`)은 04:36:06Z부터 04:48:52Z까지 766초 떠 있어 약 $0.13이다. 일부만 만들어진 파드 셋은 각각 몇 초 떠 있었다(청구는 보지 않았다). 곱셈으로 어림한 값이고 청구서의 값이 아니다.

고친 것(이 일지를 싣는 커밋): `tools/llm_local_server/main.tf`의 타이머가 `runpodctl remove pod "$RUNPOD_POD_ID"`만 쓴다(`curl` 갈래를 뺐다). 시험 `test_구성의_타이머는_이미지의_runpodctl_명령으로_파드를_멈추지_않고_지운다`가 먼저 빨갛게 실패하는 것(`runpodctl remove pod`가 없다)을 본 뒤 고쳤다. 같은 시험 세 파일 70개 통과, `ruff`, `terraform fmt -check`, `terraform validate`(상태 폴더의 `.tfdata`로) 통과다. 이 고침이 타이머에서 실제로 파드를 지우는지는 아직 띄워 보지 않았다. 파드 안에서 손으로 친 같은 명령이 지운 것까지만 봤다. 타이머의 하위 셸이 환경 변수 `RUNPOD_API_KEY`와 `RUNPOD_POD_ID`를 갖는지는 보지 못했다(실패 로그의 오류는 인증보다 앞서 나므로 근거가 되지 못한다). `exec-pod`로 친 환경에는 둘 다 있었다(`key-set`, `podid-set`).

## 셀프 리뷰 (2026-11-14, 타이머 고침과 그 결과를 적은 글)

범위는 `git diff HEAD`(`main.tf`, 시험, 일지, 명세, 티켓)다. 표준 축과 명세 축을 나란히 돌렸고, 두 보고가 모델이 쓴 글이라 지적마다 코드와 출력 파일을 열어 확인한 뒤 판정했다.

고친 것(확인해 보니 맞았다):
- 앞 회차들의 90분 타이머도 같은 이유로 실패했을 것이라는 서술을 미루어 읽은 것이라고 밝혔다. 그 회차들은 명령이 먼저 지워 타이머가 도는 것을 보지 못했다.
- 명령의 `destroy_folder`가 종료 0으로 끝난 것을 첫 `terraform destroy`의 성공으로 읽은 서술을 고쳤다. 첫 `destroy`가 실패하면 `apply -refresh-only` 뒤 다시 지우므로 어느 길이었는지는 모른다.
- 명세 207·209·218·253행과 `tools/llm_local.py` 독스트링의 "못 보는 것", 티켓 7행에 남아 있던 옛 문장(자식까지 돈 회차가 없다, `pods`를 보지 못했다, 타이머를 아직 못 봤다)을 지금 사실로 고쳤다. 지금 사실은 `pods`와 `shared`가 서고, 첫 타이머가 결함으로 드러나 고쳤으며, 고친 타이머가 스스로 지우는 것은 보지 못했다는 것이다.
- 새 `main.tf` 주석이 시험이 금지하는 문구(`pod delete`)를 그대로 적어 시험이 빨갛게 되던 것을 문구를 바꿔 고쳤다.

남긴 것과 이유:
- 시험 `test_구성의_타이머는_이미지의_runpodctl_명령으로_파드를_멈추지_않고_지운다`는 문자열만 본다. 그 문구가 주석에도 있어 주석만 남고 명령이 빠져도 지나갈 수 있고, 타이머가 서버보다 먼저 걸리는지와 `sleep`이 `timer_minutes`에서 오는지도 보지 않는다. `timer = join(...)` 블록을 뽑아 보게 하는 강화는 이 커밋에 싣지 않았다. 이 시험이 막으려는 것은 이미지에 없는 하위 명령으로 되돌아가는 일이고, 실제 방어는 다시 띄워 타이머가 파드를 지우는 것을 보는 일이다.
- 고친 타이머가 스스로 파드를 지우는 것, A5000 두 장의 Terraform `cost`, `shared`로 두 모델이 `tool_calls`로 답하는 것, 청구서의 값은 아직 보지 못했다. 다음 확인 때 타이머를 몇 분으로 줄인 한 바퀴로 본다.

다시 돌린 명령(손으로): `uv run pytest -q`로 `test_llm_local_state.py`·`test_llm_local.py`·`test_llm_local_rounds.py` 70개 통과, `ruff check`와 `ruff format --check`와 `pyright`가 변경한 두 파이썬 파일에서 0건, `terraform fmt -check` 출력 없음, 이 브랜치 확인(`feature/03-llm-local-command-rents-model-servers`), `sibling_overlap` 번호 겹침 없음. 나머지 게이트는 커밋이 부르는 pre-commit의 결과로 갈음한다. 이 커밋은 `.scratch/local-model/probes/README.md`를 건드리지 않아, `origin/dev`가 함께 고친 그 파일과는 글자 충돌 후보가 아니다.

첫 커밋 시도에서 pre-commit의 pytest가 7303개 가운데 하나(`tests/tools/test_rerun_gates.py`의 `test_게이트_몫의_시간을_넘기면_그_게이트는_시간_넘김이고_남은_게이트는_돌지_않는다`)에서 실패했다. 손자까지 끈 뒤 `notes`가 비어야 하는데 `게이트 작업 트리를 다 걷지 못했다`가 하나 들어 있었다. 이 변경은 그 시험이 쓰는 코드를 건드리지 않았고, 같은 파일을 혼자 돌리면 49개가 통과했다(183초). 같은 러너가 web-verify(1196초)와 겹쳐 1038초 도는 부하에서만 난 것으로 읽지만, 원인을 부하로 가려 재지는 않았다. 시험은 고치지 않았고, 부하에서 갈리는 시험의 앞선 사례(`test_rerun_runner.py`)와 같은 종류라 이 일지에만 적는다.

두 번째 커밋 시도에서는 다른 시험(`tests/tools/test_probe_kit.py`의 `test_배출은_줄이_계속_와도_제한_시간에_끝난다`)이 7303개 가운데 하나로 실패했다(`assert lines`에서 빈 목록, 러너 749초). 자식 파이썬이 시작하기 전에 0.5초짜리 배출 창이 닫힌 것으로 읽지만 시작 시간을 재 보지는 않았다. 같은 파일을 혼자 돌리면 15개가 4.38초에 통과했다. 이 변경이 닿지 않는 코드다. 이 세션에서 부하로만 갈린 시험이 이로써 서로 다른 셋(`test_rerun_runner.py`, `test_rerun_gates.py`, `test_probe_kit.py`)이다. 사례를 하나씩 고치는 것이 아니라 종류 전체를 다루는 일이 필요하다는 근거로 일지에 남기고, 이 커밋에서는 시험을 건드리지 않는다.

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

1. 고침(`fetch_models`의 `User-Agent`, `shared`의 KV 캐시 고정과 순차 시작)과 일지·티켓·명세의 글은 커밋 `483ad85ec`에 들었다(pre-commit 통과. 첫 시도는 부하에서만 빨개지는 `test_rerun_runner.py`의 시간 시험 하나로 막혔고 홀로 돌리면 통과했다). `bc9e19b17`은 그 `run` 결과(RTX 3090 두 장)를 적은 것이고, 타이머를 10분으로 줄여 띄운 결과와 타이머 고침(`runpodctl remove pod`)은 이 일지를 커밋하는 커밋이 싣는다.
2. 아직 비어 있는 칸을 채운다. 고친 타이머가 스스로 파드를 지우는지(옛 타이머는 `runpodctl`에 `pod` 하위 명령이 없어 실패했다. 파드 안에서 손으로 친 `runpodctl remove pod`만 지우는 것을 봤다), A5000의 Terraform `cost`, 준비까지의 시간(`shared`는 파드 생성에서 자식 시작까지 약 175초로 어림했다), `shared`가 도구 호출에 답하는지(이번 `shared`는 서버가 서는 것까지만 봤다)다. 타이머는 `tools/llm_local.py`의 `TIMER_MINUTES = 90`이 `TF_VAR_timer_minutes`로 고정해 넘기므로, 이번처럼 이 상수를 임시로 10분으로 바꿔 돌리는 길뿐이다. 그 판을 커밋하지 않는 조건으로 비용을 사용자에게 보이고 확인을 받은 뒤 띄운다. 이번 회차는 앞의 세 후보(A5000, 3090, A40 두 장)가 모두 파드 하나를 만들다 실패했고(직전 회차는 A5000만 그랬다), 그 파드들의 비용(후보당 몇 초)도 청구서가 올라오면 본다. 재고가 없으면 재시도 스크립트를 쓰더라도 판정은 마지막 후보의 결과만 보게 짓고, 다른 종류의 실패(준비 상한 초과 포함)면 멈춘다. 결과가 명세와 다르면 명세에 날짜를 단 주석으로 적고, ADR 0058 본문이 거짓이 되면 이력 초안을 쓰고 승인을 받는다. 준비 상한 30분은 본 준비 시간으로 다시 맞춘다.
3. 그 확인이 끝난 뒤 상태를 `done`으로 바꾸고 PR을 연다. 그 전에는 PR을 열지 않는다(확인 칸이 빈 채 `done`이 되면 05가 풀린다). PR 직전 리뷰(`bug-perf-review`)에는 위 "밀 주장" 넷과, 이 일지의 "고친 뒤 `run` 한 바퀴" 절이 새로 쓴 두 주장(`elapsed_seconds`가 지우기까지 포함한다는 것, `cost_per_hour`가 Terraform 출력의 합이라 3090 두 장이 단가 표와 같다는 것), "타이머를 10분으로 줄여 띄운 한 바퀴" 절이 새로 쓴 주장(이미지의 `runpodctl` 1.14.15에 `pod` 하위 명령이 없다는 것, 주입된 키로 `runpodctl remove pod`가 파드를 지운다는 것, 이미 지워진 파드가 있어도 명령의 지우기가 끝난다는 것. 첫 `destroy`가 성공했는지 `apply -refresh-only` 뒤 재시도로 성공했는지는 모른다)을 넘긴다.
4. 05가 `tech.md`의 같은 행을 마커까지 든 사실로 다시 고친다.
