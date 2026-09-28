# plugin-toggle 프로브

명세·ADR·코드 주석이 근거로 든 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`. 2026-09-28에
세션 스크래치패드에서 옮겼고(대기열 29), 바꾼 것은 ruff를 지나게 한 형식과
`probe_bool.py`의 부수 효과 import(`verbatim` 변환기 등록)에 단 `noqa` 주석이다. 옮기기 전의 근거는
프로브를 날짜나 "명세 검토의 프로브" 같은 말로 가리킨다. 이 표가 그 말을 파일로 잇는다.

돌리는 법은 저장소 루트에서 `PYTHONUTF8=1 uv run python .scratch/plugin-toggle/probes/<파일>`이다.
교체와 경합을 재는 다섯(표에서 "윈도"라고 적은 것)은 윈도의 파일 공유 의미를 잰다. 다른 OS에서는 다른 값이 나온다.

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 |
|---|---|---|---|
| `probe_toggle.py` | 요청 본문의 기본 `bool`이 `"false"`·`0`·`"no"`를 받는지와 `StrictBool`의 422, 동기 `def` 라우트와 `async def` 라우트가 도는 스레드, `{name:path}`에서 PUT `…/enabled`가 닿는 라우트 | 명세 Implementation Decisions "관리 API"의 "2026-09-26 프로브" 셋, Further Notes "이 명세의 프로브" | 그대로 |
| `probe_bool.py` | 위의 불린과 스레드를 실제 `verbatim` 변환기와 이름 패턴으로 다시 재고, 계약 스키마와 PUT `…/calc/enabled%0A`의 맞춤을 본다 | 명세 "관리 API"(설치본으로 다시 잰 것, `%0A`), 티켓 01의 경로 맞춤 수용 기준, `tests/test_server.py`의 꼬리 개행 경로 테스트 독스트링 | 저장소 venv |
| `probe_replace.py` | 다른 스레드나 다른 프로세스가 연 파일을 `os.replace`로 바꾸면 무엇이 나는지 | ADR 0017의 2026-09-27 첫 이력 "운영자 파일을 열거나 교체하다 막히면 짧게 동기로 다시 시도한다" | 윈도. 임시 디렉터리를 지우지 않는다 |
| `probe_race.py` | 교체 2000번과 쉬지 않는 읽기가 같은 프로세스의 두 스레드에서 부딪힐 때 각자 겪는 것 | ADR 0017의 같은 이력 | 윈도. 임시 디렉터리를 지우지 않는다 |
| `probe_race_proc.py` | 읽는 쪽이 다른 프로세스일 때 같은 경합 | ADR 0017의 같은 이력 | 윈도. 자식 프로세스를 띄운다 |
| `probe_retry.py` | 1·2·4·8·16ms 재시도를 넣으면 경합이 사라지는지, 핸들을 오래 쥐면 재시도가 다한 뒤 옛 파일이 남는지. 재시도 간격을 스크립트 안에 따로 두어 어댑터는 재지 않는다 | ADR 0017의 같은 이력, 티켓 01의 상한 수용 기준, `adapters/filesystem.py`의 `_RETRY_DELAYS` 주석 | 윈도 |
| `probe_retry_cap.py` | 실제 `FilesystemPlugins`의 `read_disabled`와 `write_enabled`를 두 스레드로 부딪혀 성공·실패와 재시도 깊이 분포를 센다. 인자는 초와 간격 목록(`none`이면 재시도 없음) | ADR 0017의 같은 이력(티켓 01이 실제 어댑터로 다시 잰 수치), `adapters/filesystem.py`의 `_RETRY_DELAYS` 주석 | 윈도. 비공개 `_RETRY_DELAYS`와 `time.sleep`을 바꿔 끼운다 |
