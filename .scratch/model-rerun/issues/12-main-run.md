# 12: 본 측정 — 러너의 남은 시험을 고정해 병합하고, 병합된 main 에서 다시 풀기 본 측정을 끝까지 돌려 판정한다

**What to build:** 티켓 11(`.scratch/model-rerun/issues/11-pilot-and-prereg.md`)이 고정한 사전 등록대로 본 측정(과제 8개, 다섯 갈래, 상한 $1,600)을 돌고 판정한다. 본 측정 첫 회차 전에, 예산 멈춤과 판정이 읽는 비용에 드는 러너의 갈래를 시험으로 고정해 병합한다. 그 PR 이 병합된 main 의 체크아웃에서 러너를 띄우고, 끝나면 `rerun_judge`로 판정해 일지와 `docs/model-selection.md`에 적는다. 칸을 바꿀 판정이면 ADR 0029 이력 초안을 써서 사람의 승인을 받는다.

근거는 일지 `docs/journal/2026-10-28-10-pilot-and-prereg.md`의 "사전 등록 절과 해시"(본 측정 지시문 재료)와 "다음", 티켓 11, `docs/model-selection.md` 4절 "준비 중인 다시 풀기"다. 기능 model-rerun 의 티켓 11 이 병합된 뒤 그 일을 잇는 티켓이라 같은 디렉터리의 다음 번호다(`docs/agents/issue-tracker.md`).

**Blocked by:** 없음(11 은 done)

**Status:** done

### 시험 고정 (본 측정 첫 회차 전, 동작은 바꾸지 않는다)

- [x] `tools/rerun_runner.py`의 `other_transcripts`: 회차 세션의 기록 파일(인계로 세션이 여럿이어도 모두)은 빼고, 같은 프로젝트 폴더의 다른 세션만 센다. 다른 프로젝트 폴더의 기록과 `.jsonl`이 아닌 파일, 하위 폴더(회차 세션의 `subagents/`)는 세지 않는다. 새 시험 `test_다른_세션은_회차_세션의_프로젝트_폴더_바로_아래_기록만_센다`
- [x] 그 비용(`other_usd`)이 예산 멈춤(`spent + estimate > cap_usd`)의 `spent`에 든다. 새 시험 `test_다른_세션의_비용도_예산_멈춤의_쓴_것에_든다`
- [x] `tools/rerun_continue.py`의 `arm_model_line`: PR #408 안에서 이미 시험이 들어가 갈음한다(`test_모델_줄이_없으면_브랜치_줄_뒤에_넣고_둘이면_하나로_줄인다`). 일지 "다음"은 그보다 앞서 적혔다
- [x] `tools/rerun_cost.py`의 `_gaps` 꼬리: 같은 까닭으로 갈음한다(`test_꼬리만_다른_modelUsage_두_이름은_더한_뒤_기록과_견준다`). 그 시험을 겨누는 변이는 앞의 표에 없어 `rerun_cost_mutations.toml` 31 을 더했다
- [x] 판정 몫의 셈: 갈음한다(`test_같은_프로젝트_폴더에_남은_다른_세션의_공식_단가를_회차_비용에_더한다`가 `judge_view`의 두 비용을 본다. 판정 보기가 다른 세션의 비용을 더하는지는 `rerun_files_mutations.toml`의 "판정 보기가 다른 세션의 비용을 더하지 않는다"가 `test_rerun_files.py`의 시험으로 본다)
- [x] 새 시험마다 `tools/mutate.py`로 그 갈래를 깨는 변이가 빨갛다(`rerun_runner_mutations.toml` 33~38, 프로브 README 변이 절). 목록의 차례(`sorted`)는 결과가 하나라 시험 밖이다. `Path`의 차례가 운영 체제마다 달라 둘 이상의 이름으로 고정하면 리눅스 CI 와 이 PC 가 갈린다

### 고를 것

- [x] `PREREG_VALUES`를 둔 모듈의 대문자 상수가 모두 표에 들거나 제외 목록에 드는지 보는 시험: **하지 않는다.** 2026-10-29 에 AST 로 세어 보니 표 밖의 모듈 수준 대문자 상수가 열한 모듈에 102개였다(앞 밑줄이 없는 이름만, 튜플 대입 `PREREG_START, PREREG_END`는 빼고 센 수다. 앞 밑줄 이름까지 넣으면 176개다). 대부분 이름표(`END_DONE`, `REASON_*`), 경로·환경 변수 이름, 시간 제한, 또는 값이 이미 다른 표 항목이나 `main.json`에 든 별칭(`OPUS`·`SONNET`은 갈래 표에, 고르기 시드 `SEED_*`는 표의 `SEEDS` 한 항목에)이다. 102개마다 까닭을 적는 일이 크고, 그 가운데 하나라도 표로 옮기면 사전 등록 절과 `PREREG_SHA256`을 다시 지어야 해 본 측정 직전의 판을 흔든다. 본 측정 뒤 러너 손질로 넘긴다

### 본 측정

2026-10-29: 아래 항목은 티켓 13 으로 넘긴다. CI 의 커밋 검사(`tools/check_ticket.py`, ADR 0037)가 PR 을 열 때 이 티켓이 done 이기를 요구하는데, 아래는 이 PR 이 병합된 뒤에야 할 수 있다. 측정의 결과와 판정은 그 기록을 싣는 다음 PR 에 들고, 그 PR 의 티켓이 같은 디렉터리의 다음 번호 13 이다. 계정은 사람이 njh6803 으로 바꿨다(일지 `docs/journal/2026-10-29-10-main-run.md`).

- [ ] 시험 고정 PR 을 병합한다
- [ ] 선행 조건을 본다: 계정 njh4803 의 주간 한도가 본 측정을 담을 만큼 남았는지. 앱의 `get_usage`는 앱에 로그인한 계정의 값이라 njh4803 의 것이 아닐 수 있어, 사람에게 묻는다, 판 고정 복사본 `C:\Users\User\.claude-rerun-bin\2.1.302`와 전용 설정 폴더 `C:\Users\User\.claude-rerun`의 로그인이 사는지
- [ ] 병합된 main 의 체크아웃에서 러너를 백그라운드로 띄우고 끝 알림을 기다린다. 명령 줄은 일지 "사전 등록 절과 해시"의 재료 그대로다: `uv run python -m tools.rerun_runner .scratch/model-rerun/probes/main.json --root C:/Users/User/rerun-rounds --config-dir C:/Users/User/.claude-rerun --account njh4803 --claude C:/Users/User/.claude-rerun-bin/2.1.302 --cap 1600`. 러너가 첫 회차 전에 사전 등록 절의 해시를 대 본다
- [ ] 끝나면 판정(`rerun_judge`)을 돌려 결과를 일지와 `docs/model-selection.md`에 적는다
- [ ] 칸을 바꿀 판정이면 ADR 0029 이력 초안을 써서 보이고 승인을 받는다

### 미루는 것 (본 측정 뒤, 측정 판을 흔들지 않게)

- 일지 "다음" 넷째·다섯째 줄의 러너 손질(`plan_task`의 `rerun`과 `_check_end`의 `timed_out` 불리언 인자, `gates_green`·`hidden_passed`의 열거, `rerun_files.py` 나누기, `test_구간은_5와_95_백분위다`의 자리, `root_shape.py`의 갈래별 기대 결과, `_with_costs`·`_interrupted`의 같은 차례, `ALLOWED_ENV`의 윈도 기본값 튜플, `ROOT_SHAPE`의 점 없는 회차 폴더 단언)
- PR #408 셋째 회차: `tools/rerun_round.py` `_round`에서 게이트 묶음 고르기가 `try` 안에 있는 것
- 위 "고를 것"의 대문자 상수 시험
