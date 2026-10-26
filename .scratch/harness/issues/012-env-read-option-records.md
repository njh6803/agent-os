# 012: 환경 읽기 훅의 옵션 읽기를 명령마다 레코드 하나와 getopt 읽기 함수 하나로 합친다

**What to build:** `tools/hook_env_read.py`는 명령의 옵션을 여러 표(`_VALUE_OPTIONS`, `_FILE_OPTIONS`, `_PATTERN_LONG_OPTIONS`, `_NO_ABBREVIATION`, `_WRAPPERS`)와 여러 읽기 함수(`_positionals`, `_option_width`, `_short_value_option`, `_getopt_values`, `_pattern_given_by_option`, `_abbreviates_pattern_option`, `_option_values`, `_SHORT_CLUSTER`로 센 묶음)로 읽는다. 자리마다 읽는 법이 조금씩 달라, 하류(GNU grep·sed·gawk, rg, ag, ack, 래퍼)와 다르게 읽는 사례가 PR #366의 푸시마다 새 자리에서 나왔다. 이것을 명령마다 레코드 하나(값 옵션, 파일 옵션, 패턴 옵션, 긴 옵션 줄임을 받는지)와 (옵션, 값) 쌍과 위치 인자를 내는 getopt 읽기 함수 하나로 합친다. 판정(파일 읽기, grep·rg 훑기, 래퍼 벗기기)은 모두 그 쌍만 본다. 줄임을 받는 명령에서 이름이 표와 그대로 같지 않은 긴 옵션은 하류가 어떻게 읽을지 훅이 다 알 수 없으므로, 값 옵션의 줄임으로 읽은 글과 값 없는 플래그로 읽은 글을 모두 판정해 어느 쪽에서든 걸리면 막는다(`.claude/rules/tools.md`의 "다르게 읽은 글을 모두 본다" 항목). 대기열 448에 남은 사례(`diff --from-file=.env`, `sort --files0-from=.env`, gawk `-i`·`-E`, `grep -- --file .env`, `rg -uueKEY_X`, `grep -rn --max-c 5 KEY`)는 레코드에 옵션을 적거나 읽기 함수가 `--`를 따르는 것으로 닫는다. 실제 도구와 맞대는 시험을 grep·sed·gawk로 넓히는 일은 이 티켓에 넣지 않는다(넓히면 ADR 0038의 이력 초안이 든다).

**대기열:** 448

**Status:** done

- [x] 옵션 표와 읽기 함수가 명령마다 레코드 하나(`OptionSpec`)와 읽기 함수 하나(`_read_options`)로 합쳐졌고, 옛 표와 함수(`_VALUE_OPTIONS`, `_FILE_OPTIONS`, `_PATTERN_LONG_OPTIONS`, `_NO_ABBREVIATION`, `_SHORT_CLUSTER`, `_option_width`, `_short_value_option`, `_getopt_values`, `_abbreviates_pattern_option`, `_option_values`)가 남지 않는다
- [x] 대기열 448의 남은 사례 여섯이 막힌다고 단언하는 시험이 있다. `grep -rn --max-c 5 KEY`와 `sudo --us root cat .env`는 독스트링의 못 보는 것에서 빠지고 막는 시험으로 옮겨졌다
- [x] 기존 시험(`tests/tools/test_hook_env_read.py`, `tests/tools/test_hook_env_read_rg.py`)이 고치지 않고 초록이다. 못 보는 것 시험에서 잡게 된 것은 독스트링과 함께 옮겼다
- [x] 두 글(줄임으로 읽은 글, 플래그로 읽은 글)을 모두 보는 데서 생기는 거짓 양성이 독스트링의 못 보는 것에 적혀 있고 시험으로 고정됐다
- [x] 검증 명령이 모두 초록이다

## Comments

- 2026-10-26 셀프 리뷰 반영: "두 글"(모든 긴 옵션을 플래그로 읽은 글, 모두 줄임으로 읽은 글)은 표에 없는 플래그와 진짜 줄임이 섞인 `ack .env --color --mat X`를 지나보냈다(명세 축). 그래서 모호한 긴 옵션마다 플래그로 읽을지 줄임으로 읽을지의 조합을 모두 본다(`_every_choice`, 상한 여덟을 넘으면 막는다). 수용 기준 넷째의 "두 글"은 그 조합 가운데 둘이다. 표준 축이 짚은 손으로 짠 읽기 셋(셸 `-c`, git 전역 옵션, grep `-d recurse`)도 레코드로 옮겼다.
- 2026-10-26 PR #391 claude-review 첫 회차 반영: 막는다고 기대하는 시험 둘이 막는 까닭의 표지(`저장소 전체를 훑으며`, `다 판정하지 못한다`)까지 단언한다. 셸 `-c` 의 명령 글은 레코드로 읽은 글과 옛 읽기(옵션 낱말에 `c` 가 든 첫 짧은 옵션 다음 낱말)를 모두 본다. `+o posix` 같은 `+` 옵션을 `_read_options` 가 읽지 못해서이고, 수용 기준 첫째가 든 옛 표와 함수에는 들지 않는 예외다(`_shell_c_arguments` 독스트링). `_Choices` 를 불변 값으로 바꾸자는 Minor 와 독스트링의 이력을 줄이자는 Nit 은 고치지 않았고 까닭은 PR 코멘트에 있다.
