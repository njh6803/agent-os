# 004: 매개변수와 반환의 `bool | None` 주석을 잡는 검사를 더한다

**What to build:** 세 값(`True`·`False`·`None`)으로 출력을 고르는 꼴을 기계로 잡는다. 매개변수(위치·키워드 전용·`*args`·`**kwargs`)와 반환의 주석이 `bool | None`·`None | bool`·`Optional[bool]`(`typing.Optional`, 문자열로 쓴 주해 포함)인 자리를 AST로 찾는다. ruff FBT는 키워드 전용 매개변수를 보지 않아 `tools/hook_choice_facts.py`의 `output_for(..., first: bool | None)`이 리뷰까지 지나갔다. 판정은 기존 지침 검사(`tools/check_instructions.py`)에 함수 하나로 더한다. 새 `tools/check_*.py`로 두면 pre-commit·CI·러너 등록과 게이트 수를 든 문서까지 바뀌는데, 같은 파일에 `tools/`의 코드 모양을 AST로 보는 선례(`calls_without_timeout`)가 있다. 훑는 범위는 `src`·`tools`·`tests`이고 `.scratch/**/probes/`는 보지 않는다(pyright와 타입 우회 검사도 보지 않는 자리다). `CODING_STANDARDS.md`의 불리언 플래그 줄에 이 검사가 막는 범위를 적는다.

**대기열:** 423

**Status:** done

## 수용 기준

- [x] 시험을 먼저 써서 빨간 것을 본다. 발동(세 모양, 키워드 전용, 반환, 문자열 주해, `typing.Optional`)과 침묵(`bool`, `int | None`, `bool | int | None`, `Literal`, 변수 주석)을 단언한다
- [x] 독스트링에 잡는 것과 못 보는 것을 적고, 못 보는 것마다 지나간다는 시험 하나로 고정한다
- [x] `src`·`tools`·`tests`에서 잡히는 곳이 0이고, 들일 때 `.scratch/**/probes/`의 수를 일지에 적는다
- [x] 변이(`tools/mutate.py`)로 판정의 빨강을 본다
- [x] `CODING_STANDARDS.md`의 불리언 플래그 줄이 이 검사를 가리킨다
- [x] 대기열 423을 닫는다
- [x] 검증 명령이 모두 초록이다
