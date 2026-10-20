# 2026-10-20 (20) 최종 사용자 면이 404로 덮는 것을 주인을 확인하기 전의 손상으로 좁힌다

end-user-continuation 티켓 05(`.scratch/end-user-continuation/issues/05-only-pre-owner-damage-is-404.md`)의 구현이다. 나란히
여는 넷(02·03·05·06) 가운데 셋째 세션이고, 워크트리 `05-only-pre-owner-damage-is-404`에서 브랜치
`feature/05-only-pre-owner-damage-is-404`로 했다(기준 `911babc0`).

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/end-user-continuation/issues/05-only-pre-owner-damage-is-404.md"

첫 메시지는 위 문장 뒤에 지시문을 붙인 것이다(아래 원문).

```
다음 작업: .scratch/end-user-continuation/issues/05-only-pre-owner-damage-is-404.md. 최종 사용자 면이 404로 덮는 것은 주인을 확인하기 전의 손상뿐이고, 운영자의 구성 실수는 500이다
다음 단계: 구현
어디서: 새 세션. 나란히 여는 4 중 3. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
시작 프롬프트: /implement .scratch/end-user-continuation/issues/05-only-pre-owner-damage-is-404.md
브랜치: feature/05-only-pre-owner-damage-is-404
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: 나란히 도는 나머지 티켓 .scratch/end-user-continuation/issues/02-runtime-names-the-failure-cause.md, .scratch/end-user-continuation/issues/03-shortcuts-walk-only-that-agent.md, .scratch/end-user-continuation/issues/06-admin-shows-cause-and-shortcut-links.md
이어받을 상태: 없음
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. tidy-checkouts는 묶음의 첫 세션이 돈다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

## 시작

- 묶음의 첫 세션이 `tidy-checkouts`를 돌므로 이 세션은 돌지 않았다. 주 체크아웃에서 브랜치를 따지 않고
  `EnterWorktree`(name `05-only-pre-owner-damage-is-404`)로 들어와 브랜치를 바꿨다(기준 `911babc0`).
- 티켓 05, 명세의 "최종 사용자 면의 404 덮기" 절, ADR 0023의 2026-10-16 이력과 ADR 0014의 2026-09-26 이력, 형제 티켓
  02·03·06을 읽었다. 형제와 함께 고칠 파일은 `core.md`, `run.py`, `continuation.py`, `test_run.py`,
  `test_end_user.py`, probes README다(`tools/sibling_overlap.py`의 함께 고친 파일). 병합할 때 글자 충돌 후보다.

## 구현

- **core.** `PluginError`의 하위 타입 `TraceDamagedBeforePrincipal`을 `core/ports.py`에 더했다. 이름은 용어집의 "주체"와
  "트레이스"에 기댔다. 던지는 자리는 `continuation.py`의 컨텍스트 매니저 `before_principal` 하나가 감싸는 두 읽기다.
  이어 가기의 앞 실행 읽기(`gather_continued`의 `read_link`)와 자기 실행 읽기(`run._own_link`의 `trace.read`, 그리고
  `link_of`·`check_record_rules`)다. `_own_link`는 `trace.read`와 `link_of` 사이의 `None` 판정(`Absent`)을 감싸지
  않으려고 두 번 연다. 같은 `read_link`가 고리를 따라갈 때(`_walk`·`_next_link`)와 재개가 앞 실행을 읽을
  때(`resumed_conversation`)는 감싸지 않아 기반 타입이다.
- **표와 면.** `http/errors.py`의 `failure_for`에 새 하위 타입의 갈래를 기반 `PluginError` 갈래 앞에 두었다. 운영자 면은
  500 원문, 최종 사용자 면은 404 고정 문구다. 기반 `PluginError`는 최종 사용자 면 어디서나 500
  `INTERNAL_MESSAGE`다. 면의 열거 `Surface`를 운영자·최종 사용자 둘로 줄이고, `EndUserPaths`에서 시작 경로를 지웠으며
  `end_user.py`의 `END_USER_START_PATH`와 `server.py`가 그것을 넘기던 자리를 지웠다.
- **기록 한 줄.** 모양(`원래 상태 <코드> <타입 이름>: …`)은 그대로이고, 덮인 손상의 타입 이름이 이제
  `TraceDamagedBeforePrincipal`이다.
- **지침과 독스트링.** `core.md`·`http.md`·`channel.md`, `ports.py`의 `PluginError`·`NotResumable`·`DifferentPrincipal`
  독스트링, `run.py`의 모듈 독스트링과 `read_own_run`, `errors.py`의 `Surface`·`EndUserPaths`·`failure_for`,
  `end_user.py`의 모듈 독스트링과 결정·이어 가기 주석을 고쳤다. 01이 살아 있는 문서에 쓴 덮기 문장은 모두 다시 썼다.
  티켓 01 파일은 기록이라 두었다.
- **plan.md.** end-user-channel 행과 end-user-continuation 행에 티켓 05가 덮는 몫을 좁혔다는 말을 더했다.

## 테스트 먼저

- core: 새 하위 타입을 import하고 정확한 타입(`type(...) is PluginError`, `type(...) is TraceDamagedBeforePrincipal`)으로
  단언하게 바꾼 뒤 16개가 빨갰고(구현 전이라 모두 기반 타입이었다), 구현 뒤 `tests/core/test_run.py` 245개가 초록이었다.
  `read()`가 `PluginError`를 던지는 가짜 `LockedTrace`를 더해 어댑터가 감싼 읽기 실패를 쟀다(명세 검토의 요구).
  깨진 것의 단언은 `not isinstance(…, _SUBTYPES)` 모양에서 정확한 타입으로 바꿨다.
- HTTP: 결정의 구성 오류 넷(진입점, 없는 mcp, 기록이 가리키는 에이전트의 부재, 깨진 고리)과 이어 가기의 셋(진입점,
  없는 mcp, 깨진 고리)이 500 고정 문구이고 원인이 서버 기록에 남는 테스트를 더했다. 구현 전 셋이 `404 != 500`으로
  빨갰고 구현 뒤 초록이었다. 관련 묶음(`test_end_user`, `test_server`, `test_router`, `tests/core`)은 598 passed였다.
- 구현 전부터 초록이던 테스트(자기 실행 손상의 404, 운영자 면의 500, 고리와 재개의 앞 실행이 기반 타입)는 변이 표
  `.scratch/end-user-continuation/probes/pre_owner_damage_mutations.toml`의 일곱 변이로 이빨을 봤다. 모두 기대대로
  빨갰고 약 40초였다.

## 카나리아

바꾼 규칙 셋(`core.md`, `http.md`, `channel.md`)을 원천으로 든 명세를 이 브랜치가 고치지 않아
`tools/sibling_overlap.py`가 1로 끝났다. 기존 명세 셋은 티켓 01의 문장을 묻는 것이라 두고, 티켓 05의 문장을 묻는 명세
셋을 새로 썼다(`.scratch/end-user-continuation/probes/canary/{http,core,channel}_rule_pre_owner_damage.toml`).
claude 2.1.302에서 http와 channel은 통과 4였다. core의 첫 판은 통과 3·실패 1이었다. 실패한 회차도 규칙이 실려
하위 타입 이름을 옮겼는데, 질문 (2)("어디서 던지는지 말한 문장")에 자리를 나열한 다음 문장을 옮겼다. 묻는 문장을
"던지는 자리가 몇 곳인지와 그 자리를 감싸는 함수의 이름을 함께 말한 문장 하나"로 좁혀 다시 돌려 통과 4였다.

## 셀프 리뷰

범위: base `911babc0`, 커밋 0, 고친 파일 13, 미추적 2(변이 표, 이 일지). 리뷰 도중 카나리아 명세 셋이 더 생겼다.
표준 축은 sonnet·high, 명세 축은 본 세션의 모델로 나란히 띄웠다.

### 표준 축

- **Major.** `.scratch/end-user-channel/probes/contract_mutations.toml`의 변이 둘("주체를 손상보다 먼저", "실행을 가리키는
  경로의 깨진 기록을 500 으로")의 원문이 이 변경으로 0번이 된다. pre-commit의 `mutate.py --staged`가 막을 자리다. 같은
  표의 `end_user.py` 원문 넷은 그 전부터 썩어 있었다.
- **Minor.** 티켓 01이 05를 가리켜 미래형으로 쓴 문장(12·51·91행)이 그대로다. 티켓 05가 다듬으라고 한 것이다.
- **Minor.** probes README 행이 일지의 변이 결과를 가리키는데 일지에 그 결과가 없다.
- **Minor.** `core.md`의 깨진 것의 단언은 정확한 타입으로 한다는 그때 문장이 실제보다 넓다. `test_run.py` 1818행(재개할 때 에이전트
  부재)은 `not isinstance(caught.value, Absent)`만 보고, 1605~1673·1745·1757행의 `pytest.raises(PluginError, match=…)`는
  타입을 고정하지 않는다.
- **Minor.** `ports.py`의 `NotResumable`("손상된 트레이스는 … `TraceDamagedBeforePrincipal` 이다")과
  `DifferentPrincipal`("손상이 이것보다 먼저")의 보편 주장에 반례가 있다(재개의 고리 손상, 이어 가기에서 앞 실행 자신의
  기록 규칙).
- **Nit.** `failure_for` 독스트링의 "마지막 갈래만 문구를 덮는다"는 이 변경 전부터 거짓이다.
- **Nit.** 고친 독스트링의 줄바꿈이 어색하다.
- **판단 항목.** `before_principal`의 `except PluginError`가 하위 타입까지 잡는다. `failure_for`의 `if operator` 모양
  반복은 표가 한 곳이라는 표준이 승인한 것이라 내지 않았다.
- 주장 검증에서 참으로 닫은 것: 시작 경로에서 하위 타입이 날 길이 없다, 기반 타입으로 남는 자리, 어댑터가 감싸는 실패,
  변이 표 일곱의 원문과 표지, ADR 0023 이력, 잔존 grep.

### 명세 축

- 수용 기준은 모두 구현됐고 범위를 넘은 것은 없다고 했다.
- **Nit.** 남의 손상된 실행의 404 테스트(`test_end_user.py` 778·1017행)가 `Origin` 없이 보내 봉투와 CORS를 단언하지
  않는다. 티켓은 "모두 JSON 봉투이고 CORS 헤더가 붙는다"이다.
- **Minor.** 명세 265행과 티켓 05의 25행은 기록 한 줄이 `원래 상태 500 PluginError: …` 그대로라고 하는데, 지금은
  `TraceDamagedBeforePrincipal`로 찍힌다(`_detail_of`가 `type(error).__name__`을 쓴다). 틀은 같다.
- **Minor.** `channel.md`와 `end_user.py`의 그때 문장(404는 앞 실행이 없거나 남의 것이거나 손상된 것)에 반례가 있다. 자기 앞
  실행이 자기 기록 규칙을 어기면(`previous="../etc"`) 이제 500이다. 서브에이전트가 스크래치 프로브로 불러 봤다.
- **Nit.** `before_principal` 독스트링의 "여는 자리는 둘이다"는 `with`가 셋이라 어긋난다.
- **Nit.** probes README의 `canary/*.toml` 행이 티켓 01의 것만 든다.
- 참으로 닫은 것: `core.md`의 던지는 자리와 두 타입의 목록(스크래치 프로브와 core 테스트 21개), 시작 경로에서 읽기가
  한 번도 일어나지 않는다(`reads=[]`), 운영자 면의 응답, HTTP 사례, 잔존 grep, `_SUBTYPES` 단언 열둘이 0, 카나리아
  `expect`의 글자.

### 판정

- 문서 위치 규약을 다시 읽으니 진행 중인 기능의 명세·티켓은 살아 있는 문서다(`operations.md` 문서 위치). 구현 때 티켓
  01 파일을 기록으로 보고 둔 판단이 틀렸다. 그래서 티켓 01의 세 문장과 명세 265행을 고친다.
- **고친 것.**
  - 변이 표(Major). `contract_mutations.toml`의 썩은 원문 여섯을 지금 코드에 맞췄다. 이 변경이 깬 둘("주체를 손상보다
    먼저", "실행을 가리키는 경로의 깨진 기록을 500 으로")과 그 전부터 썩은 넷("결정 응답의 첫 인덱스", "도는 실행에
    붙지 않는다", "끝내지 못함의 id", "구독의 한 걸음 사이에 await")이다. 둘째는 하위 타입 갈래의 404를 500
    `INTERNAL_MESSAGE`로 바꾸는 변이로 다시 지었다. `--check` 31개가 통과했고 고친 여섯만 돌려 모두 기대대로 빨갰다.
    그 README 행에 이 일지를 적었다.
  - 티켓 01의 12·51·91행을 지난 일로 다듬었다(표준 축 Minor). 명세 265행과 티켓 05의 25행에 기록 줄의 타입 이름
    주석을 달았다(명세 축 Minor).
  - 테스트의 단언(표준 축 Minor). 다른 실행의 이벤트가 섞인 트레이스, 결정 쓰기 거부, 모르는 종류, 빈 트레이스, 재개할
    때 에이전트 부재의 다섯 자리를 `as caught`와 정확한 타입 단언으로 바꿨다. `core.md`의 문장은 그 범위로 좁혔다.
  - `ports.py`의 `NotResumable`·`DifferentPrincipal`, `failure_for`, `before_principal`의 독스트링(표준 축 Minor·Nit,
    명세 축 Nit)과 `channel.md`·`end_user.py`의 이어 가기 404 문장(명세 축 Minor)을 고쳤다.
  - 남의 손상된 실행의 404 테스트 둘(778·1017행)이 `Origin`을 보내 JSON 봉투와 CORS 헤더를 단언한다(명세 축 Nit).
  - probes README의 `canary/*.toml` 행에 05의 명세 셋을 넣었다(명세 축 Nit).
  - PR 직전 리뷰에 밀 주장으로 넘기는, 반영하며 새로 쓴 사실 문장의 원문:
    - `core.md`: "깨진 것을 하위 타입과 가르는 단언은 `not isinstance(…)`로 빼는 모양이 아니라 정확한
      타입(`type(...) is PluginError`)으로 한다."
    - `ports.py` `NotResumable`: "재개할 실행의 트레이스가 손상됐으면 이것이 아니다. 실행의 상태가 아니라 기록이 깨진
      것이고, 그 주체와 견주기 전에 만난 것이라 `TraceDamagedBeforePrincipal` 이다. 거슬러 읽는 고리에서 만난 손상은
      주체를 확인한 뒤라 기반 타입 그대로다."
    - `ports.py` `DifferentPrincipal`: "손상된 트레이스의 주체는 믿을 수 없으므로 그 실행을 읽다 만난
      손상(`TraceDamagedBeforePrincipal`)이 이것보다 먼저다. 이어 가기에서 앞 실행 자신의 기록 규칙은 이것과 끝나지
      않음 뒤라 기반 타입이다."
    - `errors.py` `failure_for`: "주인을 확인하기 전의 손상(`TraceDamagedBeforePrincipal`)도 깨진 것이라 운영자
      면에서는 500 원문이다. 운영자 면에서는 마지막 갈래만 문구를 덮는다"
    - `continuation.py` `before_principal`: "여는 함수는 둘이다. 이어 가기의 앞 실행 읽기(`gather_continued`)와 자기
      실행 읽기의 단건 읽기·기록 규칙(`run._own_link`. 없음의 판정을 사이에 두고 두 번 연다)이다."
    - `channel.md`: "404는 앞 실행이 없거나 남의 것이거나 그 주체와 견주기 전에 읽다 손상을 만난 것, 요청한 에이전트가
      없거나 열 에이전트 밖인 것이고 고정 문구 하나다. 앞 실행 자신의 기록 규칙, 깨진 고리, 요청한 에이전트의 구성
      오류는 주체를 확인한 뒤의 고장이라 표가 덮지 않고 500 고정 문구다"
    - `end_user.py` 모듈 독스트링: "남의 실행, 그 주체와 견주기 전에 읽다 손상을 만난 실행, 없는 실행, 열 에이전트
      밖의 실행은 모두 같은 404 고정 문구이고, 주체를 확인한 뒤의 구성이나 기록의 고장은 어느 경로에서나 500 고정
      문구다"
    - 명세 265행과 티켓 05 25행: "틀(`원래 상태 <코드> <타입 이름>: …`)은 그대로이고, 타입 이름은 예외의 것이라 덮인
      손상은 `원래 상태 500 TraceDamagedBeforePrincipal: …`로 찍힌다. 운영자 면의 줄도
      `status=500 TraceDamagedBeforePrincipal: …`다"
    - 티켓 05 31행: "모양은 정확한 타입(`type(caught.value) is PluginError`, 주인을 확인하기 전의 손상이면
      `TraceDamagedBeforePrincipal`)이다. 빼는 모양을 쓰던 자리와 손상을 단언하던 자리를 모두 바꿨다."
- **남긴 것.**
  - 고친 독스트링의 줄바꿈(표준 축 Nit). `tools/rewrap_comments.py`가 감은 결과라 손으로 다시 감지 않았다.
    `end_user.py`의 이어 가기 주석만 도구가 다시 감지 않는 짧은 줄이 남아 손으로 감았다.
  - `before_principal`의 `except PluginError`가 하위 타입까지 잡는다(표준 축 판단 항목). 감싸는 두 자리 안에서는
    단건 읽기·`link_of`·기록 규칙만 돌아 기반 타입만 난다(`Absent` 판정은 두 `with` 사이다). 좁히면 기반 타입만 잡는
    `type(...) is` 갈래가 필요해 오히려 읽기 어렵다.
  - 티켓 03의 31행("05가 먼저 병합됐으면 05가 넓힌 모양(새 하위 타입도 아님)을 따른다")은 뜻이 맞아 고치지 않았다.
    03의 파일을 이 브랜치가 고치면 그 브랜치와 글자 충돌 후보가 하나 는다. 받는 쪽은 `test_run.py`의 `_SUBTYPES`
    주석과 `core.md`가 정확한 타입을 적는다.
- **다시 돌린 것.** 위 반영 뒤 `tests/channel/http/test_end_user.py`와 `tests/core/test_run.py`는 323 passed였고 `ruff
  check`가 통과했다. 카나리아는 원천의 본문을 고친 `core.md`와 `channel.md`의 명세를 `--preflight`로 갈음했고(같은
  claude 2.1.302, 머리말과 `expect`는 그대로, 사전 확인 통과 3) 두 명세의 `# 최신 결과:` 줄 뒤에 덧붙였다.
  `http.md`는 카나리아를 돌린 뒤 고치지 않았다. 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다.
- **첫 커밋이 막혔다.** pre-commit의 `mutate.py --staged`가 다른 기능의 표 `.scratch/conversation/probes/continuation_mutations.toml`에서
  이 변경이 깬 원문 둘("요청이 댄 앞 실행의 패턴을 거르지 않는다", "재개가 자기 요약의 자리를 보지 않는다")을 잡았다.
  셀프 리뷰에서 `contract_mutations.toml`만 보고 이 표는 보지 않았다. 둘을 `with before_principal():` 꼴로 고치고 그
  둘만 돌려 기대대로 빨갰다. 그 밖의 검사(pytest 809초, web-verify 503초 등)는 그 회차에 모두 통과했다.
- **둘째 커밋도 막혔다.** 표가 커밋에 들자 `--staged`가 표의 원문 전부를 봐서 부모 판에서 이미 썩어 있던 다섯이
  걸렸다. 다섯도 지금 코드에 맞추고 돌려 모두 기대대로 빨갰다. 그 README에 결과를 적었다. 그 밖의 검사(pytest 650초,
  web-verify 647초 등)는 그 회차에도 모두 통과했다.
- **셋째 커밋 `60ea4c7c`.** 커밋 전에 `uv run python tools/mutate.py --staged`를 손으로 쳐서 문제 0을 본 뒤 커밋했다.
  pre-commit이 모두 통과했다(pyright 53초, run-hooks 330초, web-verify 546초, pytest 611초, 변이 표, 카나리아 모양,
  인용 대조는 경고 셋). 인용 경고 셋은 이 일지의 따옴표였고, 커밋 뒤 일지에서 원문대로 고치거나 따옴표를 뗐다.

## 검사

- **`-m llm`.** 셀프 리뷰 전의 판에서 7 passed(733.89초). 토큰 합계 58,240(입력 57,162, 출력 1,078), 트레이스 10, 모델
  호출 23. 셀프 리뷰가 고친 것은 독스트링·주석·테스트 단언·변이 표·문서라 다시 돌리지 않았다.
- **`run_checks`.** 셀프 리뷰 전에 pyright만 빨갰고(`@contextmanager`의 `Iterator` 반환이 reportDeprecated) `Generator[None]`
  으로 고쳤다. 커밋 `60ea4c7c`의 pre-commit이 손으로 치는 다섯을 갈음한다(위).
- **카나리아.** 새 명세 셋이 claude 2.1.302에서 통과 4. `core.md`와 `channel.md`는 셀프 리뷰가 본문을 고쳐 사전 확인으로
  갈음했다(위 판정).
- **변이.** `pre_owner_damage_mutations.toml` 일곱, `contract_mutations.toml`에서 고친 여섯, conversation의
  `continuation_mutations.toml`에서 고친 일곱이 모두 기대대로 빨갰다. 셀프 리뷰가 테스트를 고친 뒤
  `pre_owner_damage_mutations.toml` 전체는 다시 돌리지 않았다. PR 직전 리뷰를 반영한 뒤(이어받은 세션)
  그 표 전체(가드 항목을 더해 여덟)를 돌려 모두 기대대로 빨갰다.
- **e2e(진단 중).** 전체 e2e(`pnpm -C web/apps/admin exec playwright test`)에서 `e2e/decision.e2e.ts:12`("멈춘 실행을
  허가하면 재개 스트림이 조각으로 붙고 …")가 두 번 실패했다. 첫 번은 LLM 테스트와 카나리아가 함께 돌던 때, 둘째는
  셀프 리뷰 반영 뒤다. 증상은 둘 다 39행 `expect(events).toContainText("run_finished")`가 5초 안에 서지 않은 것이고,
  화면의 이벤트는 `run_started`와 `run_paused`뿐이었다. 나머지 여섯은 통과했다. 단독으로 한 번 돌리면 통과했고(셋 모두),
  `e2e/admin-token.e2e.ts`와 그 시험 둘만 돌려도 통과했다. CLAUDE.md 작업 규약 6대로 diagnosing-bugs를 열어 1단계
  루프를 지었다. `pnpm -C web/apps/admin exec playwright test e2e/decision.e2e.ts:12 --repeat-each=6`이 이 브랜치에서
  2/6 실패했다(셋째·여섯째, 같은 증상, 실패한 회차는 9.3·9.6초이고 통과한 회차는 7.3~8.0초). 이 PC에서 형제 세션
  셋이 함께 돌고 있었다. 이 브랜치는 `web/`과 `openapi.json`을 고치지 않았다(`git diff --stat 911babc0 -- web
  openapi.json`으로 다시 본다).
- **e2e(진단 끝, 이어받은 세션).** 이 브랜치와 무관한 부하·시간 의존이다. 같은 루프(`--repeat-each=8`)를 이 브랜치의
  `src/agent_os`로 한 번, `git checkout 911babc0 -- src/agent_os`로 기준 판을 잠시 들인 채 한 번 돌렸다(뒤에
  `git checkout HEAD -- src/agent_os`로 되돌렸다). 두 판 모두 8/8 실패했고 증상은 앞과 같다(39행, 화면의 이벤트는
  `run_started`와 `run_paused`뿐). 다른 세션 넷(형제 `02`·`04`, `skill-listing-trim`, 아침 보고서)이 함께 돌던 때다.
  `serve.log`에는 여덟 회차 모두 허가(`POST …/approval`)와 도구 호출 뒤에 화면의 다시 읽기(`GET /traces/<id>`)가
  없었고, 지우다 남은 임시 폴더의 트레이스에는 `run_finished`가 모두 있었다(teardown의 `rmSync`가 EPERM으로 폴더를
  남겼다. 진단 뒤 지웠다). 그래서 실행은 서버에서 끝났고 테스트의 창이 먼저 닫혔다. 트레이스의 시각으로 잰 간격(초,
  세션 스크래치의 `gaps.py`, `approval_granted`가 있는 회차만 셌고 빠진 회차는 없었다):

  | 판 | 시작→일시정지 | 허가→재개 | 허가→끝남 |
  |---|---|---|---|
  | 이 브랜치(8) | 3.01~5.02, 평균 4.16 | 3.34~5.02(7회), 평균 4.46 | 5.36~7.04(7회) |
  | 기준 판(8) | 3.23~4.41, 평균 3.70 | 2.75~4.53, 평균 3.66 | 4.76~6.60 |

  이 브랜치의 마지막 회차는 끝나기 전에 teardown이 `serve`를 거둬 재개와 끝남이 없다. 허가와 재개 사이는 재개가
  MCP 픽스처 서버를 자식 프로세스로 띄워 연결하는 자리다(`core/run.py`의 `self._tools.connect`. `serve.log`의
  `ListToolsRequest`가 그때 찍힌다). 테스트는 `approval_granted`가 보인 뒤 기본 5초 안에 `run_finished`를 기다리는데,
  그 창에 프로세스 기동, 픽스처가 도구 뒤에 쉬는 2초, 중계를 지나는 다시 읽기가 모두 든다. 기동이 3초를 넘으면 창이
  닫힌다. 두 판의 차이(평균 약 0.8초)는 이 브랜치의 코드를 지나지 않는 시작→일시정지(운영자 `/runs`의 새 실행.
  `gather_continued`도 `_own_link`도 지나지 않는다)에서도 비슷하게 나서 돌린 차례의 부하 차이로 읽는다. 이 브랜치가
  재개 길에 더한 것은 `trace.read`를 감싸는 컨텍스트 매니저 하나다. 같은 시험이 CI의 `e2e` 잡에서는 형제 PR #319에서
  통과했다. 이 테스트의 창을 넓히거나 픽스처를 미리 띄우는 고침은 이 티켓 밖이라 대기열 후보로 넘긴다(아래 "다음").

## 인계

이 세션의 제목은 `feature/05-only-pre-owner-damage-is-404`였다. 세션 컨텍스트가 문턱(20만)을 넘은 채 `커밋 뒤`에 와서
next-session의 인계 줄로 넘긴다. 이 세션이 번복한 것은 하나다. 구현 때 티켓 01 파일을 기록으로 보고 두었다가, 셀프
리뷰 판정에서 문서 위치 규약대로 진행 중인 기능의 티켓은 살아 있는 문서라 고쳤다(위 판정).

남은 단계:

1. e2e 진단을 잇는다. 위 루프를 기준 판의 `src/agent_os`로 돌려 이 브랜치의 2/6과 견준다. 기준 판에서도 같은 비율로
   실패하면 이 브랜치와 무관한 부하·시간 의존이라 대기열 후보로 넘기고(같은 실패의 회차), 기준 판에서 통과만 하면
   이 브랜치의 변경을 의심해 diagnosing-bugs 3단계로 간다.
2. PR 직전 리뷰(`docs/constitution/operations.md` 리뷰 파이프라인 2). 밀 주장은 위 판정의 "고친 것" 원문 목록이다.
3. `/git-pr`로 PR을 연다. 본문에 e2e 진단의 결론을 적는다.
4. 병합 직전에 `git fetch` 뒤 `origin/main`의 형제 티켓 02·03·04·06의 `Status:`를 본다. 이 세션이 본 때는 모두
   ready-for-agent였다. 모두 done이면 `plan.md` 행과 프론티어를 고친다. 03이 먼저 병합됐으면 그 검증 사례의 단언도
   정확한 타입으로 넓힌다(티켓 05의 31행). 티켓 05의 마지막 두 체크박스(43·44행)는 아직 비어 있다.
5. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다.

지시문:

```
다음 작업: .scratch/end-user-continuation/issues/05-only-pre-owner-damage-is-404.md. 최종 사용자 면이 404로 덮는 것은 주인을 확인하기 전의 손상뿐이고, 운영자의 구성 실수는 500이다
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리를 잇는다. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/end-user-continuation/issues/05-only-pre-owner-damage-is-404.md
브랜치: feature/05-only-pre-owner-damage-is-404
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-20-20-only-pre-owner-damage-is-404.md 의 "판정", "검사", "인계" 절
이어받을 상태: 인계: 커밋 뒤. 구현·셀프 리뷰 반영·커밋(60ea4c7c)까지 마쳤고 푸시와 PR은 아직이다. 커밋하지 않은 변경은 일지뿐이다. 남은 단계는 e2e decision.e2e.ts:12 의 진단(이 브랜치에서 --repeat-each=6 이 2/6 실패, 기준 판 911babc0 의 src 로 같은 루프를 돌려 견주기), PR 직전 리뷰, PR, 병합 직전 형제 티켓 확인, 병합이다. docs/journal/2026-10-20-20-only-pre-owner-damage-is-404.md
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

제목을 `feature/05-only-pre-owner-damage-is-404 (인계함)`으로 바꿨고, 멈출 백그라운드 작업은 없었으며, 워크트리 잠금을
풀었다.

open-session을 부른다 2026-10-20T04:16:20Z

## 이어받은 세션

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/end-user-continuation/issues/05-only-pre-owner-damage-is-404.md"

첫 메시지는 위 문장 뒤에 위 "인계"의 지시문을 붙인 것이다.

- **시작.** 제목을 `feature/05-only-pre-owner-damage-is-404`로 바꾸고, 주 체크아웃 세션인 채 `tidy-checkouts`를 돌았다.
  루트는 main이고 이미 `origin/main`(`2d460f6b`)과 같아 당기지 않았다. 판정은 지울 것이 없었고, 사람에게 넘길
  넷이 있었다. 분리 HEAD인데 그 커밋이 `origin/main`에 없는 워크트리 둘(`confident-wright-2d3ebf`,
  `elegant-dijkstra-aaddb9`), 병합된 PR의 머리와 브랜치 끝이 다른 `skill-check-and-retro-section`, 등록 없이 `.git`이
  있는 폴더 `04-exchange-count-read-cap-and-thread`다. 그 뒤 `EnterWorktree(path)`로 이 워크트리에 들어왔다.
- **형제 상태.** `origin/main`에서 03·06은 `done`, 02·04는 `ready-for-agent`다. 이 PR은 기능을 닫지 않는다(티켓 44행).
  03이 먼저 병합됐으므로 그 검증 사례의 단언을 정확한 타입으로 넓힌다(티켓 31행).
- **e2e 진단.** 위 "검사"의 e2e 항목. 이 브랜치와 무관한 부하·시간 의존이다.
- **main 합치기.** `git merge origin/main`(03 #318, 06 #319, 문서 둘). 코드와 테스트는 저절로 합쳐졌고 글자 충돌은
  넷이었다. 길어서 손 편집 대신 치환마다 한 번 맞는지 단언하는 스크래치 스크립트로 풀었다.
  - `core.md`: 이어 가기 항목은 이 브랜치가 고치지 않아 main 판(03의 바로가기)을 썼다. 실패 정책 항목은 두 쪽이 다른
    문장을 고쳐(이 브랜치는 하위 타입 문장, 03은 고리 목록의 바로가기 문장) 이 브랜치 판에 03의 고리 문장을 심었다.
  - conversation의 `continuation_mutations.toml`: 06이 이 브랜치와 같은 썩은 다섯을 먼저 고쳐 두었다. 둘("에이전트가 낸
    요약 이벤트를 통과시킨다", "표에서 새 하위 타입 둘을 빼면 500 이 된다")은 글이 달라 06의 판을 골랐고(그 원문이 합친
    코드에 그대로 있는 것을 Grep으로 봤다), 셋은 같은 글이라 저절로 합쳐졌다. 그 README는 06 문단을 앞에 두고 이 브랜치
    문단에 그 결과를 더했다.
  - end-user-continuation probes README: 표의 행을 합쳤다(03·06의 행, 이 브랜치의 행, 05의 명세 셋을 든 `canary` 행).
  - 합친 뒤 고친 것: 03의 바로가기 검증 사례(`test_바로가기가_어긋나면_…`)의 빼는 모양을 `type(caught.value) is
    PluginError`로(티켓 31행), `before_principal` 독스트링과 `core.md`의 고리를 따라갈 때를 말한 문장에 바로가기를
    더했다. 티켓 31행에서 이 PR을 열 때 03이 병합되지 않았다고 적은 문장을 지금 사실로 고쳤다.
  - 확인: `tests/core/test_run.py`, `tests/channel/http/test_end_user.py`·`test_router.py`, `tests/test_server.py`가
    618 passed. `mutate.py --staged` 문제 0. conversation 표의 이 브랜치 변이 둘(`--since origin/main`)이 합친 코드에서
    모두 기대대로 빨갰다. `core.md`를 원천으로 든 카나리아 둘(05의 `core_rule_pre_owner_damage.toml`, 03의
    `core_rule_shortcuts.toml`)은 사전 확인 통과 2로 갈음했다.
  - `tools/sibling_overlap.py`가 이 일지가 main의 최신 일지(`-16`)보다 이름순으로 앞이라 알려 `--move`로 `-13`에서
    `-20`으로 옮겼다(인용도 함께).
- **PR 직전 리뷰.** CodeRabbit CLI는 좌석이 없어 대체 둘을 돌렸다(`docs/constitution/operations.md` 리뷰 파이프라인).
  - 보안: 내장 `/security-review`를 커밋하고 main을 합친 뒤(`785575f8`) 돌렸다. 발견 없음. 존재·소유 오라클(주체
    비교 전에 기반 타입이 새는 자리), 최종 사용자 응답의 원문 누출, 면을 줄인 뒤 최종 사용자 경로가 운영자 면으로
    읽히는 길을 경로마다 따라가 모두 닫았다.
  - 버그·성능: `bug-perf-review` 서브에이전트. 유효 셋이 모두 Nit이고 오탐 둘이다. 밀 주장 일곱은 코드와 시험에
    대어 모두 참으로 닫았고, `before_principal` 한 번의 비용은 약 1.1µs라 트레이스 읽기(ms)에 견줘 무시된다. e2e
    진단의 빈틈도 찾지 못했다.
    - Nit 1(고쳤다): `before_principal`이 `PluginError` 전부를 잡아, 감싼 안에 `Absent`·`DifferentPrincipal`을
      던지는 줄이 들어오면 그 갈래가 조용히 손상(최종 사용자 면 404, 운영자 면 500)으로 바뀐다. 지금은 닿는 길이
      없다. 기반 타입만 바꾸고 하위 타입은 그대로 올리게 했다. 시험(`test_주인을_확인하기_전의_자리는_하위_타입을_…`,
      네 사례)이 구현 전에 넷 모두 빨갰고, 변이 표에 "감싸는 자리가 하위 타입도 손상으로 바꾼다"를 더했다.
    - Nit 2(고쳤다): `failure_for` 독스트링의 나열에 새 하위 타입이 없었고, 그 둘레와 `read_own_run` 독스트링에
      짧게 끊긴 줄이 있었다.
    - Nit 3(회고로 넘김): 최종 사용자 면이 덮은 404의 원인은 서버 기록에서만 찾는데, JSONL 어댑터의 단건 읽기
      실패는 메시지가 두 줄이라(`트레이스를 읽을 수 없다: {path}` 다음 줄에 오류 종류) 추적 식별자로 grep하면
      오류 종류가 든 둘째 줄을 놓친다. 이 브랜치가 만든 형식이 아니다(아래 "회고").
  - 확인: `tests/core/test_run.py` 272 passed, 고친 네 파일 `ruff check` 통과, `pre_owner_damage_mutations.toml`
    여덟이 모두 기대대로, 세 변이 표의 원문 확인(`mutate.py --check`) 통과.
- **티켓.** 43행(검증 명령)은 로컬 e2e의 흔들림을 괄호로 달아 닫았다. 44행(기능 닫기)은 `git fetch` 뒤
  `origin/main`(`2d460f6b`)의 02·04가 `ready-for-agent`라 닫지 않는다고 적었다. 병합 직전에 다시 본다.
- **커밋·PR.** 리뷰 반영과 티켓·일지·회고를 `0d2cff19`로 커밋했고(pre-commit 통과), 푸시해 PR #321을 열었다. 열 때
  고친 것이 둘이다. 제목이 74자라 72자 안으로 줄였고, 본문에서 견줘 보지 않은 대안을 든 문장을 지워 사실로 바꿨다.
  리뷰 줄의 좌석 문구는 `coderabbit auth status`를 실제로 친 뒤에 적었다.

## 인계 (PR 연 뒤)

이 세션(이어받은 세션)의 제목은 `feature/05-only-pre-owner-damage-is-404`였다. 세션 컨텍스트가 문턱(20만)을 넘은 채
`PR 연 뒤`에 와서 next-session의 인계 줄로 다시 넘긴다. 받은 경계(`커밋 뒤`)와 다른 경계이고, 요청 범위가 병합까지이며,
곁 세션이 아니라(`get_session`의 `self`에 `parentSessionId`가 없다) 인계하지 않는 때가 아니다. 주 체크아웃은 main이고
`origin/main`(`2d460f6b`)과 같아 선행 조건에 적지 않았다.

남은 단계는 next-session 순서 1의 2(봇 회차)부터다. 첫 `@coderabbitai review` 코멘트도 새 세션이 남긴다. 병합 직전에
`git fetch` 뒤 `origin/main`의 02·04 `Status:`를 다시 본다(티켓 44행). 둘 다 done이면 이 PR이 기능의 마지막 잎이라
티켓 44행과 `plan.md`, 아래 "다음"(지시문을 내지 않는다는 문장)을 고쳐 기능을 닫는다. 이 절과 위 "커밋·PR" 줄은
커밋하지 않았다.

지시문:

```
다음 작업: .scratch/end-user-continuation/issues/05-only-pre-owner-damage-is-404.md. 최종 사용자 면이 404로 덮는 것은 주인을 확인하기 전의 손상뿐이고, 운영자의 구성 실수는 500이다
다음 단계: PR 반영·병합
어디서: 새 세션. 같은 브랜치·워크트리를 잇는다. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/end-user-continuation/issues/05-only-pre-owner-damage-is-404.md
브랜치: feature/05-only-pre-owner-damage-is-404
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-20-20-only-pre-owner-damage-is-404.md 의 "이어받은 세션", "인계 (PR 연 뒤)", "다음" 절
이어받을 상태: 인계: PR 연 뒤. PR #321 을 열었고 봇 회차는 아직이다(@coderabbitai review 코멘트도 남기지 않았다). next-session 순서 1의 2부터 한다. 커밋하지 않은 변경은 일지의 "인계 (PR 연 뒤)" 절과 "커밋·PR" 줄뿐이다. 병합 직전에 형제 02·04의 Status를 다시 보고, 둘 다 done이면 이 PR이 기능을 닫는다(티켓 44행, 일지 "다음"을 고친다). docs/journal/2026-10-20-20-only-pre-owner-damage-is-404.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `feature/05-only-pre-owner-damage-is-404 (인계함)`으로 바꿨고, 멈출 백그라운드 작업은 없었다. 워크트리 잠금은
`is not locked`로 이미 풀려 있었다(이 세션은 `EnterWorktree(path)`로 들어왔다).

open-session을 부른다 2026-10-20T06:00:56Z

## 이어받은 세션 (PR 연 뒤)

> 사용자: "`.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/end-user-continuation/issues/05-only-pre-owner-damage-is-404.md"

첫 메시지는 위 문장 뒤에 위 "인계 (PR 연 뒤)"의 지시문을 붙인 것이다.

- **시작.** 제목을 `feature/05-only-pre-owner-damage-is-404`로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다.
  지시문의 선행 조건이 없음이라 `tidy-checkouts`는 돌지 않았다.
- **봇 회차.** `@coderabbitai review`를 남기고 `tools/wait_ci.py 321`을 기다렸다. 헤드 `0d2cff19`에서 검사는 모두
  통과했고 CodeRabbit은 `Review rate limited`라 리뷰가 없다. 회차로 세지 않고, 보안·버그 축은 PR 본문 체크리스트에
  적은 PR 직전 리뷰 둘이 대체한다(`docs/constitution/operations.md` 초록 착시 목록). claude-review의 첫 회차는
  Critical·Major·Minor 없이 Nit 하나였다. 같은 근거(주체 확인 전의 손상은 남의 존재를 드러낸다)를
  `TraceDamagedBeforePrincipal`, `before_principal`, `failure_for`의 독스트링이 세 번 되풀이한다는 것이다. 일지를
  어차피 푸시해야 해서 같은 커밋에 고쳤다. 원천은 `TraceDamagedBeforePrincipal`에 두고, 나머지 둘은 그 독스트링을
  가리키게 줄였다.
- **형제 상태.** `git fetch` 뒤 `origin/main`의 02·04가 `ready-for-agent`다. 이 PR은 기능을 닫지 않는다(티켓 44행과
  아래 "다음"은 그대로).
- **반영.** `/git-pr-feedback`대로 인라인 코멘트와 리뷰 요약을 보니 둘 다 없었고, 반영할 것은 위 Nit 하나다. 고친
  두 파일은 `tools/rewrap_comments.py`로 감았고 `ruff check`와 `ruff format --check`가 통과했다.

## 인계 (셀프 리뷰 직전)

이 세션(PR 연 뒤를 이어받은 세션)의 제목은 `feature/05-only-pre-owner-damage-is-404`였다. 반영 커밋 전의 셀프
리뷰(`/code-review`)를 부른 순간 세션 컨텍스트가 문턱(20만)을 넘어 `셀프 리뷰 직전`에 왔다. 받은 경계(`PR 연
뒤`)와 다르고, 요청 범위가 병합까지이며, 곁 세션이 아니다(`get_session`의 `self`에 `parentSessionId`가 없다).
그래서 셀프 리뷰의 단계를 밟지 않고 넘긴다. 이 세션이 번복한 것은 없다.

커밋하지 않은 변경은 셋이다. `src/agent_os/core/continuation.py`의 `before_principal` 독스트링과
`src/agent_os/http/errors.py`의 `failure_for` 독스트링(claude-review Nit 반영), 그리고 이 일지의 "이어받은 세션
(PR 연 뒤)" 절과 이 절이다. 남은 단계는 셀프 리뷰(base는 `HEAD`, 범위는 그 셋), 커밋, 푸시,
`@coderabbitai review`와 대기(claude-review는 둘째 회차라 Critical·Major만 고친다), 병합 직전 형제 02·04의
`Status:` 재확인, 워크트리에서 병합이다.

지시문:

```
다음 작업: .scratch/end-user-continuation/issues/05-only-pre-owner-damage-is-404.md. 최종 사용자 면이 404로 덮는 것은 주인을 확인하기 전의 손상뿐이고, 운영자의 구성 실수는 500이다
다음 단계: PR 반영·병합
어디서: 새 세션. 같은 브랜치·워크트리를 잇는다. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/end-user-continuation/issues/05-only-pre-owner-damage-is-404.md
브랜치: feature/05-only-pre-owner-damage-is-404
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-20-20-only-pre-owner-damage-is-404.md 의 "이어받은 세션 (PR 연 뒤)", "인계 (셀프 리뷰 직전)", "다음" 절
이어받을 상태: 인계: 셀프 리뷰 직전. PR #321 의 claude-review 첫 회차 Nit(같은 근거가 독스트링 세 곳에 되풀이)을 반영한 before_principal·failure_for 독스트링과 일지 두 절이 커밋되지 않은 채 워크트리에 있고, 셀프 리뷰(/code-review, base HEAD)부터 한다. 그 뒤 커밋, 푸시, @coderabbitai review 와 tools/wait_ci.py 대기(헤드 0d2cff19 의 CodeRabbit 은 rate limited 라 회차로 세지 않았다. claude-review 는 다음이 둘째 회차라 Critical·Major 만 고친다), 병합 직전 형제 02·04 Status 재확인(둘 다 done 이면 이 PR 이 기능을 닫는다, 티켓 44행), 워크트리에서 병합이다. docs/journal/2026-10-20-20-only-pre-owner-damage-is-404.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `feature/05-only-pre-owner-damage-is-404 (인계함)`으로 바꿨고, 멈출 백그라운드 작업은 없었다(`wait_ci.py`
대기는 이미 끝났다). 워크트리 잠금은 `is not locked`로 이미 풀려 있었다.

open-session을 부른다 2026-10-20T06:08:00Z

## 이어받은 세션 (셀프 리뷰 직전)

> 사용자: "`.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/end-user-continuation/issues/05-only-pre-owner-damage-is-404.md"

첫 메시지는 위 문장 뒤에 위 "인계 (셀프 리뷰 직전)"의 지시문을 붙인 것이다.

- **시작.** 제목을 `feature/05-only-pre-owner-damage-is-404`로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다.
  지시문의 선행 조건이 없음이라 `tidy-checkouts`는 돌지 않았다.
- **셀프 리뷰.** 범위: base `0d2cff19`, 커밋 0, 고친 파일 3(`continuation.py`, `errors.py`, 이 일지), 미추적 0. 명세는
  claude-review 첫 회차의 Nit 원문이고 티켓 05는 참고로 넘겼다. 표준 축은 sonnet·high, 명세 축은 본 세션의 모델로
  나란히 띄웠다.
  - 표준 축: 하드 위반 없음, Minor 둘(판단 항목), Nit 둘.
    - Minor: `before_principal`이 원천이라 가리킨 `TraceDamagedBeforePrincipal` 독스트링에 "바로가기"가 없다. main을
      합칠 때(위 "main 합치기") 바로가기를 `before_principal`과 `core.md`에만 더했다.
    - Minor: `gather_continued`와 `_own_link`의 독스트링이 이유를 `before_principal`에서 찾게 해, 이 diff 뒤로 포인터가
      두 단이 됐다.
    - Nit: `core.md`·`http.md`도 같은 근거를 길게 적는다.
    - Nit: 위 인계 절의 "Critical·Major 만 고친다"가 `operations.md` 리뷰 파이프라인 4의 줄임과 어긋난다.
  - 명세 축: Critical·Major 없음, Minor 둘, Nit 하나. 사라진 정보는 바로가기 말고 없고, ADR이 아니라 원천
    독스트링을 가리키게 한 것이 요구의 뜻(고칠 곳 하나)에 더 맞다고 판정했다.
    - Minor: 바로가기(표준 축과 같다).
    - Minor: 위 "인계 (셀프 리뷰 직전)"가 커밋하지 않은 일지 변경을 두 절로 셌는데, "커밋·PR" 줄과 "인계 (PR 연
      뒤)" 절도 커밋되지 않았다. 파일 수 셋은 맞다.
    - Nit: 위 "같은 커밋에 고쳤다"가 커밋 전에 과거형이다.
  - 두 축이 참으로 닫은 것: `before_principal`을 여는 자리 셋(`continuation.py`의 하나, `run.py`의 둘), 그 안에서
    하위 타입을 던지는 줄이 없음, 하위 타입을 그대로 올림(명세 축이 스크래치 스크립트로 불러 봤고 `-k
    주인을_확인하기_전` 16 passed), 지운 문장의 내용이 원천에 남음, `failure_for`의 500 고정 문구, 일지의 `gh`
    사실(헤드 `0d2cff19`의 검사 모두 통과, CodeRabbit의 rate limited, claude-review의 Nit 하나, 인라인 코멘트와 리뷰
    0, 02·04의 `ready-for-agent`), 위 절의 `> 사용자:` 인용. PR 제목이 처음에 74자였다는 말은 지금 대 볼 수 없다(지금
    68자).
- **판정.**
  - 고친 것:
    - 바로가기(두 축의 Minor). `TraceDamagedBeforePrincipal` 독스트링의 이유 문단에 깨진 바로가기를 더했다. 마지막
      문단은 "주체를 확인한 뒤에 읽는 것은 기반 타입 그대로다"를 일반 조항으로 세우고 고리·바로가기, 재개의 앞 실행,
      앞 실행 자신의 기록 규칙을 그 예로 두었다(code-review 6단계 1).
    - 두 단 포인터(표준 축의 Minor). `gather_continued`와 `_own_link`가 이유를 `TraceDamagedBeforePrincipal`에서 찾게
      했다. `_own_link`에는 감싸는 것이 `before_principal`이라는 말을 남겼다. `run.py` 모듈 독스트링이
      `before_principal`과 ADR 0023의 2026-10-16 이력을 괄호로 드는 문장은 이유가 아니라 장치와 결정을 드는 것이라
      두었다.
  - 남긴 것:
    - `core.md`·`http.md`의 근거 반복(표준 축의 Nit). 지침은 그 경로의 파일을 열 때 실리는 에이전트용 문서라,
      독스트링을 가리키게 줄이면 읽는 쪽이 한 번 더 열어야 한다. 봇의 Nit도 독스트링 셋만 들었다.
    - "Critical·Major 만 고친다"(표준 축의 Nit). 회차 세기의 원천인 `next-session` 1단계의 줄임이다. 그 원문은
      "둘째 회차부터는 Critical·Major만 고치고, 나머지는 지적마다 보류 이유를 PR 코멘트에 남긴 뒤 병합한다"이고,
      보류 코멘트는 이번 회차에 그대로 따른다.
    - 인계 절의 셈(명세 축의 Minor). 지난 세션의 인계 기록이라 고치지 않고 여기 적는다. 커밋하지 않은 일지 변경은
      "커밋·PR" 줄과 "인계 (PR 연 뒤)", "이어받은 세션 (PR 연 뒤)", "인계 (셀프 리뷰 직전)"의 세 절이었다.
    - "같은 커밋에 고쳤다"(명세 축의 Nit). 이 커밋으로 참이 된다.
  - 다음 층(PR 봇의 둘째 회차)이 겨눌, 반영하며 새로 쓴 문장의 원문:
    - `ports.py` `TraceDamagedBeforePrincipal`: "주체를 확인한 뒤의 고장(깨진 고리와 깨진 바로가기, 기록이 가리키는
      에이전트의 부재, 구성 오류)은 요청한 사람 자신의 실행과 대화에 관한 것이라 드러나는 남의 것이 없어 기반 타입
      그대로다", "같은 읽기라도 주체를 확인한 뒤에 읽는 것은 기반 타입 그대로다. 고리나 바로가기를 따라갈 때, 재개가
      앞 실행을 다시 읽을 때, 이어 가기에서 주체·끝남 뒤에 보는 앞 실행 자신의 기록 규칙이 그렇다"
    - `continuation.py` `gather_continued`: "손상이 하위 타입인 이유는 `TraceDamagedBeforePrincipal` 의 독스트링이다"
    - `run.py` `_own_link`: "손상은 주인을 확인하기 전의 것이라 하위 타입이고(이유는 `TraceDamagedBeforePrincipal`,
      감싸는 것은 `before_principal`), 없음은 손상이 아니라 그 사이에 선다"
  - 다시 돌린 것: 고친 네 파일(`ports.py`, `continuation.py`, `run.py`, `errors.py`)의 `ruff check`와
    `ruff format --check`가 통과했다. 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다.

## 회고

두 세션(구현한 세션과 이어받은 세션)을 함께 본다. 낸 후보는 일곱이고 승인 0, 기각 6, 넘김 0, 일지에만 남기는 것 1이다.
대기열에 더한 행과 회차는 없다. 만료할 행은 이 브랜치와 `origin/main` 두 출력 모두 없었다(`tools/queue_open_rows.py`).

1. **일지에만: e2e `decision.e2e.ts:12`가 이 PC의 부하에서 흔들렸다**(위 "검사"의 e2e 항목). 진단에 루프 둘(각 8회)이
   들었다. 허가 뒤 기본 5초 창에 MCP 픽스처 기동과 픽스처의 2초 휴지가 함께 드는 시간 시험이라, 대기열 306이 받아들여
   닫은 종류(부하에서만 빨간 시간 시험, ADR 0036)의 새 사례다. retro 5단계대로 306을 잇지도 새 행을 쓰지도 않는다. 다시
   열지는 사람이 정한다. 고친다면 그 단언에 픽스처 기동을 넣은 기한을 주는 한 줄이다.
2. **기각: 첫 커밋이 다른 기능의 변이 표에서 막혔다**(위 "판정"의 첫 커밋). 셀프 리뷰가 `contract_mutations.toml`만 보고
   conversation의 `continuation_mutations.toml`은 보지 않았다. pre-commit의 `mutate.py --staged`가 그 자리에서 막았다.
   이미 있는 검사가 막은 것이다.
3. **기각: 둘째 커밋이 그 표의 옛 찌꺼기 다섯에서 막혔고, 같은 다섯을 06도 나란히 고쳐 main을 합칠 때 글자 충돌을
   풀었다.** `--staged`는 이 커밋이 새로 깬 원문과 커밋에 든 표의 원문 전부를 보는 설계라(대기열 312), 표를 고치는 쪽이
   그 표의 옛 찌꺼기를 치운다. 막은 것은 설계대로이고, 표를 건드리지 않는 커밋까지 막게 하거나 찌꺼기를 봐주게 하는 것은
   게이트를 바꾸는 일이라 이 비용으로는 내지 않는다. 사실 하나를 남긴다. 2026-10-20에 표 95개 가운데 19개에 옛 찌꺼기가
   있었다(세션 스크래치의 `check_all_tables.py`가 표마다 `mutate.py --check`를 불렀다). 이 브랜치가 고친 `run.py`를
   가리키는 `.scratch/web-admin/probes/pause_index_mutations.toml`의 여덟도 그중이고, 그 표를 고치지 않은 커밋은
   막히지 않았다.
4. **기각: `before_principal`의 `except PluginError`가 하위 타입까지 잡았다.** 셀프 리뷰 표준 축이 판단 항목으로 냈고
   구현 세션이 남겼다가, PR 직전 `bug-perf-review`가 Nit으로 다시 내 두 줄로 고쳤다. 리뷰가 잡도록 둔 판단이라 리뷰가 제
   몫을 했다.
5. **기각: 최종 사용자 면이 덮은 404의 원인이 서버 기록에서 두 줄이다**(PR 직전 리뷰 Nit 3). 이 브랜치가 만든 형식이
   아니고 실제로 놓친 사건이 없다. 하네스가 아니라 제품의 기록 형식이라 PR 본문의 남긴 위험에 적는다.
6. **기각: 워크트리 가드가 명령 둘을 거부했다**(이어받은 세션의 `S=…; git show …` 복합 명령, `xargs -a`). 앱 가드가 그
   자리에서 막았고 `CLAUDE.md` 환경 함정이 이미 적는다. 둘 다 스크래치의 파이썬 스크립트로 옮겼다.
7. **기각: 훅이 세 번 알렸다**(중간 문장이 한국어가 아님, 판정 명령을 파이프에 넣음, 큰 결과 1만 자). 이미 있는 훅이 그
   자리에서 알린 것이다.

## 다음

이 PR은 워크트리에서 병합하고 주 체크아웃을 당기지 않는다. 주 체크아웃 미갱신: 루트는 main.

이 PR은 end-user-continuation을 닫지 않는다. 남은 잎 02·04는 각자 세션이 맡는다(02는
`feature/02-runtime-names-the-failure-cause` 세션, 04는 06이 연 `feature/04-exchange-count-read-cap-and-thread` 세션).
그래서 이 세션은 지시문을 내지 않는다. 뒤에 병합되는 잎이 기능을 닫고 다음 지시문을 낸다.
