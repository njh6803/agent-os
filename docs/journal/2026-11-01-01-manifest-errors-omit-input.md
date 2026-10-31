# 2026-11-01 (01) 매니페스트를 읽지 못한 문구가 잘못 적은 값을 되울리지 않게 한다 (model-plugin 02)

세션 제목: `feature/02-manifest-errors-omit-input`. 지시문으로 연 새 세션이고 티켓은 `.scratch/model-plugin/issues/02-manifest-errors-omit-input.md`다. 컨텍스트가 인계 문턱을 넘어 커밋 뒤에 인계했다(`handoff.md`).

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/model-plugin/issues/02-manifest-errors-omit-input.md. 다음 작업: 매니페스트를 읽지 못한 문구가 잘못 적은 값(입력값)을 되울리지 않게 한다(어댑터 `_parse` 한 곳). 이번 요청 범위: PR과 병합까지

## 한 것

- 브랜치 `feature/02-manifest-errors-omit-input`를 새 워크트리에 만들고(워크트리 이름은 지시문대로 `02-manifest-errors-omit-input`, `worktree-` 머리의 임시 브랜치를 `git branch -m`으로 바꿨다) 티켓을 `in-progress`로 바꿔 첫 편집에 실었다.
- 빨강: `tests/adapters/test_filesystem.py`의 새 시험이 심은 `sk-ant-…` 값이 `input_value`로 문구에 있다며 실패했다(agent·mcp 둘).
- 고침: `src/agent_os/adapters/filesystem.py`의 `_parse`가 `_describe`(오류 종류, 칸 위치, 문구만. `jsonl.py`의 것과 같은 모양)를 쓴다.
- 문서: `.claude/rules/adapters.md`의 JSONL 항목 곁에 매니페스트 문장을 더했다.
- 카나리아: `adapters.md`를 고쳐 카나리아 명세 둘(`adapters_rule_new_optional_fields.toml`, `adapters_rule_boundary_exceptions.toml`)을 `claude -p`로 돌려 각각 통과 4·실패 0이었고 `# 최신 결과:` 줄을 고쳤다.
- 커밋 `6a64891b`(pre-commit 통과). 커밋 전 전체 러너(`tools/run_checks.py`)도 통과했으나 그 판은 셀프 리뷰 반영 전 파일이다. 반영 뒤 판은 pre-commit이 다시 돌렸다.

## 손으로 본 것 (PR 본문에 적는다)

티켓 어댑터 둘째 항목이 요구한 손으로 보기다. 값 `sk-ant-PROBE-SECRET`을 심은 임시 폴더로 `read_manifest`를 불러 `PluginError` 문구를 봤다(스크래치 스크립트로, 커밋한 프로브가 아니다).

- UTF-8이 아닌 파일: `'utf-8' codec can't decode byte 0xff in position 32: invalid start byte`. 값을 싣지 않았다.
- TOML 문법 오류(`api_key = sk-ant-…`): `Invalid value (at line 1, column 11)`. 값을 싣지 않았다.
- 키 중복(`a = …`, `a = …`): `Cannot overwrite a value (at line 2, column 8)`. 값을 싣지 않았다.
- 셀프 리뷰 표준 축이 `uv run python -I`로 더 본 것: 표를 두 번 선언한 TOML 문법 오류는 표 이름(키)을 싣는다(`Cannot declare ('sk-ant-SECRET',) twice`). 칸 이름 자체(`extra_forbidden (sk-ant-…)`)도 위치로 나온다. 값이 아니라 키에 비밀을 적은 경우는 막지 않는다. 운영자가 어느 칸이 틀렸는지 알아야 해서이고 독스트링과 `adapters.md`에 적었다. 열기 실패(`OSError`)는 기존 시험이 문구에 "권한"이 든 것만 본다.

## 셀프 리뷰 (`/code-review`, base `bf6c1f26`, 파일 4개, 커밋 0, 미추적 0)

표준 축 8건(확정 0, 판단 8), 명세 축 4건.

- 고친 것: ① 독스트링의 "TOMLDecodeError는 위치만 담는다"가 거짓이었다(표 이름을 싣는다). 값이 아니라 위치와 키 이름이라는 한계를 독스트링과 `adapters.md`에 적었다. ② 독스트링의 "어댑터끼리 import 하지 않아 따로 둔다"는 근거가 문서에 없었다(pyproject 계약은 패키지 단위 형제 독립이다). "선례가 없어 따로 두었다"로 고쳤다. ③ 시험의 `"planted" in message`는 경로에 이미 있는 글자라 빈 단언이었다. 파일 경로 전체를 단언하게 했다. ④ 시험이 model 종류를 덮지 않았다. 매개변수를 agent·mcp·model로 늘리고 헬퍼가 매개변수의 종류 하나만 쓰게 했으며 값이 실제로 심겼는지 단언을 더했다. ⑤ `adapters.md`의 "시작 진단"은 아직 없는 출구(티켓 05)를 현재형으로 적어 뺐다.
- 남긴 것: 운영자 파일 `disabled.toml`의 `_parse_operator_file`(`filesystem.py`)이 `{error}`를 그대로 실어, 검증 오류면 `input_value`를 되울린다(`api_key = "sk-ant-…"`나 `agent = ["sk-ant-…"]`를 적은 `disabled.toml`로 `read_disabled()`를 부르면 나온다. 서브에이전트가 재현했다). 이 티켓은 매니페스트 문구만 닫는 범위라 닫지 않았고 `adapters.md`에 범위 밖이라고 적었다. 병합 뒤 다음 후보다(아래 "다음").
- 다시 돌린 것: 린트 둘과 `tests/adapters/test_filesystem.py` 55개와 `tools/check_instructions.py`를 반영 뒤에 쳤다. 전체 러너는 반영 전 파일로 한 번 통과했고 반영 뒤 판은 pre-commit이 갈음했다.

## 번복·결정

- 번복 없음. 공용 `_describe`로 빼지 않고 어댑터 안에 같은 모양을 따로 뒀다(티켓: "고칠 자리는 `_parse` 한 곳"). 같은 모양이 셋째 자리에 나오면 공유 모듈로 뺄 때다.

## PR 직전 리뷰 (인계받은 세션)

CodeRabbit CLI는 좌석이 배정되지 않아(`coderabbit auth status`: Seat not assigned) 돌지 못했다. 대체로 내장 `/security-review`와 `bug-perf-review` 서브에이전트를 돌렸다.

- `/security-review`: 신뢰도 8 이상의 지적 없음(diff를 읽은 판정이고 서브에이전트나 재현은 돌리지 않았다). `sdk/manifest.py`의 검증기 문구가 싣는 것은 이미 검증된 `kind`뿐이고 입력값을 되울리는 자리가 없다(`Grep`으로 `raise ValueError` 자리를 읽은 것이고 손으로 돌려 본 것은 아니다). 칸 이름(키)에 비밀을 적은 경우와 운영자 파일 문구는 이 PR이 새로 낸 것이 아니라 이미 알려진 범위 밖이다.

- `bug-perf-review` 서브에이전트: 유효한 지적은 Nit 하나. `_describe` 독스트링의 "표를 두 번 선언한 TOML 문법 오류만 표 이름을 싣는다"가 좁다는 지적이다(서브에이전트가 `tomllib.loads`를 직접 불러 `x=[1]\n[[x]]`가 `Cannot mutate immutable namespace ('x',)`를 내는 것을 확인했다고 보고했고, 이 세션이 재현하지는 않았다). 문구는 모두 키 이름이지 값이 아니라 새 누출은 아니다. "표나 키 경로를 선언·변경하다 난 TOML 문법 오류(표를 두 번 선언함 등)"로 독스트링을 고쳤다. 같은 서브에이전트가 `_describe`를 12개 입력으로 불러 값이 새지 않음을 봤다고 보고했다(그 보고를 옮긴 것이다).

## 회고

후보 3, 승인 0, 넘김 0, 기각 3. 대기열 만료 점검(`uv run python tools/queue_open_rows.py --ref origin/main`)은 만료할 행이 없었다.

- 기각 1: 독스트링과 규칙 문장의 "~만 싣는다" 같은 전칭 단정이 두 번 틀렸다. 셀프 리뷰가 "TOMLDecodeError는 위치만 담는다"를, PR 직전 `bug-perf-review`가 "표를 두 번 선언한 오류만 키를 싣는다"를 잡았다. 리뷰가 잡도록 둔 기준(주장 검증)을 어겨 리뷰가 잡은 사건이라 리뷰가 제 몫을 한 것이고 회차로 세지 않는다(대기열 20의 닫힌 수 주장과 같은 갈래).
- 기각 2: 이 워크트리에서 `cat >> 파일 <<EOF`로 일지를 이으려다 앱의 워크트리 가드가 "너무 복잡해 검증할 수 없다"며 거부했다. `CLAUDE.md` 환경 함정이 이미 적은 모양이고 가드가 그 자리에서 막았다. Edit으로 바꿔 한 호출만 낭비했다.
- 기각 3: CodeRabbit CLI 좌석이 없었다(`coderabbit auth status`: Seat not assigned). 대기열 136(닫힘)이 정한 대체(`/security-review` + `bug-perf-review`)를 그대로 밟았다.

## 다음

- 이 일지의 PR을 병합한 뒤 `model-plugin`의 다음 티켓은 `03-default-model-plugin-and-explicit-flag`다. 01(`01-contract-model-manifest-fields`)이 막고 있어 01이 병합된 뒤에 연다. 01은 형제 워크트리 `01-contract-model-manifest-fields`가 하고 있고, 02와 01이 같은 `tests/adapters/test_filesystem.py`를 고치므로 뒤에 병합되는 쪽이 앞의 것을 합친다. 04는 01·02·03이 모두 병합된 뒤다.
- 티켓 후보(범위 밖으로 넘긴 일): 운영자 파일 `disabled.toml`의 `_parse_operator_file`(`src/agent_os/adapters/filesystem.py`)이 `{error}`를 그대로 실어 검증 오류면 `input_value`를 되울린다. `api_key = "sk-ant-…"`나 `agent = ["sk-ant-…"]`를 적은 `disabled.toml`로 `read_disabled()`를 부르면 나온다(셀프 리뷰의 서브에이전트가 재현했다고 보고했다). 관리 면의 켜고 끄기 길이 이 문구를 내므로 02와 같은 `_describe`를 쓰는 작은 티켓 하나다. 04가 모든 실행에서 모델 파일을 읽기 전에 필요하지는 않지만 06(관리 화면의 모델 켜고 끄기) 전에는 닫는다.
- PR 병합 뒤 `주 체크아웃 미갱신` 한 줄과 원격 브랜치 정리는 `merge.md` 워크트리 절 3·4대로 보고에 남긴다.

## 인계 메모 (이 절은 단계를 닫는 "다음"이 아니다)

- 인계했다. 새 세션이 같은 브랜치에서 푸시하고 PR을 열고 병합까지 한다. 그 세션이 이 일지에 "다음"을 쓰고 회고를 돈다.
- 병합 뒤 후보: 운영자 파일 손상 문구(`_parse_operator_file`)의 `input_value` 되울림. 티켓 후보이고 이 일지의 "남긴 것"이 근거다.
- 01과 02는 둘 다 `tests/adapters/test_filesystem.py`를 고친다. 뒤에 병합되는 쪽이 앞의 것을 합친다.
- 인계 순서: 일지, 제목(`(인계함)`), 잠금 풀기(`git worktree unlock`)를 마쳤다. 백그라운드 작업은 모두 끝나 멈출 것이 없었다.
- open-session을 부른다 2026-10-31T17:05Z
