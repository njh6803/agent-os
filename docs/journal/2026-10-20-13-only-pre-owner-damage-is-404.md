# 2026-10-20 (13) 최종 사용자 면이 404로 덮는 것을 주인을 확인하기 전의 손상으로 좁힌다

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
"자리가 몇 곳인지와 감싸는 함수의 이름을 함께 말한 문장"으로 좁혀 다시 돌려 통과 4였다.

## 셀프 리뷰

범위: base `911babc0`, 커밋 0, 고친 파일 13, 미추적 2(변이 표, 이 일지). 리뷰 도중 카나리아 명세 셋이 더 생겼다.
표준 축은 sonnet·high, 명세 축은 본 세션의 모델로 나란히 띄웠다.

### 표준 축

- **Major.** `.scratch/end-user-channel/probes/contract_mutations.toml`의 변이 둘("주체를 손상보다 먼저", "실행을 가리키는
  경로의 깨진 기록을 500 으로")의 원문이 이 변경으로 0번이 된다. pre-commit의 `mutate.py --staged`가 막을 자리다. 같은
  표의 `end_user.py` 원문 넷은 그 전부터 썩어 있었다.
- **Minor.** 티켓 01이 05를 가리켜 미래형으로 쓴 문장(12·51·91행)이 그대로다. 티켓 05가 다듬으라고 한 것이다.
- **Minor.** probes README 행이 일지의 변이 결과를 가리키는데 일지에 그 결과가 없다.
- **Minor.** `core.md`의 "깨진 것의 단언은 정확한 타입으로 한다"가 실제보다 넓다. `test_run.py` 1818행(재개할 때 에이전트
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
- **Minor.** `channel.md`와 `end_user.py`의 "404는 앞 실행이 없거나 남의 것이거나 손상된 것"에 반례가 있다. 자기 앞
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
