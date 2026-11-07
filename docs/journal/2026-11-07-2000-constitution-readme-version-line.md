# 2026-11-07 (20:00) 헌법 README에 판 줄만 남기고 이력은 history.md로 옮긴다 (retro-queue-per-item 06)

세션 제목: `feature/06-constitution-readme-version-line`. 브랜치 `feature/06-constitution-readme-version-line`, 워크트리 `.claude/worktrees/06-constitution-readme-version-line`. 모델 Sonnet 5.5 / high.

## 사용자 프롬프트

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. … 인자: .scratch/retro-queue-per-item/issues/06-constitution-readme-version-line.md

지시문의 다음 작업은 "헌법 README에 판 줄만 남기고 이력은 history.md로 옮긴다"이고 구현 단계, 어디서는 새 세션(`tidy-checkouts` 뒤 `EnterWorktree`, name `06-constitution-readme-version-line`), 읽을 것은 `docs/journal/2026-11-07-1400-plan-table-generated.md`의 "봇 첫 회차", 이번 요청 범위는 "PR과 병합까지"였다. 05는 main에 병합돼 이 티켓을 풀었다.

## 한 일

1. **시험을 먼저.** `tests/tools/test_sibling_overlap.py`, `test_check_constitution_version.py`, `test_check_ticket.py`를 새 신호에 맞게 고쳐 옛 도구에서 빨강을 먼저 봤다(판정 시험 6개, 면제 시험 3개).
2. **신호.** 비워 둔 판의 신호가 "이 브랜치가 그 판의 이력 문단을 더했다"에서 "main이 이 브랜치 몫으로 비워 둔 판의 문장을 이 브랜치가 지웠고, 이 브랜치의 판 줄이 main의 판 줄과 같다"로 바뀌었다. `tools/sibling_overlap.py`의 `reserved_version`이 셈을 하고 `HISTORY_HEAD`와 `history_entries`는 없어졌다. `tools/check_constitution_version.py`는 같은 함수를 부르고 막는 글을 새 길(까닭은 ADR 이력이나 일지에, 비워 둔 판을 쓰려면 판 줄은 main의 것 그대로 두고 문장을 지운다)로 바꿨다.
3. **README와 history.md.** `docs/constitution/README.md`는 머리 9줄, 판 줄(`**Version**: 3.0.70`), 비워 둔 문장 하나(3.0.61)만 든다. 옛 한 줄 이력과 2.0.0 문단은 `docs/constitution/history.md`(새 파일, 기록이라 더하지 않는다)로 글자 그대로 옮겼다. 비워 둔 문장 다섯(3.0.61, 3.0.45, 3.0.35, 3.0.25, 3.0.19) 가운데 3.0.61만 이력에 자기 문단이 없어 README에 남겼고, 나머지 넷은 옛 이력 줄과 함께 `history.md`로 갔다.
4. **문서.** `operations.md` 문서 위치 절(`history.md`를 기록으로 들이고 "살아 있는 문서 안의 이력"에서 헌법 README의 버전 이력을 뺐다), `CONTEXT.md`의 헌법 판 용어, `KICKOFF.md`, 프로브 README 두 줄, ADR 0045 이력 항목 하나를 고쳤다. `tools/check_ticket.py`의 헌법 면제에 `docs/constitution/history.md`를 더했다(시험 포함).
5. **변이.** `sibling_overlap_mutations.toml`은 비워 둔 판 열을 새 신호에 맞게 고쳤다. 처음 판에서 더한 "이 브랜치가 지우지 않은 문장도 지운 것으로 센다"는 다른 변이와 같은 함수가 되는 동치 변이라 커밋 검사가 표지를 요구하는 자리에서 가려내 뺐고, 표는 175에서 174가 됐다. 나머지 새 변이 다섯에는 시험의 단언마다 다른 메시지를 달고 그 `AssertionError: …` 줄을 표지로 골랐다. 113~119·121·122를 돌려 아홉 모두 표지까지 맞는 기대대로 빨강이었다. `check_constitution_version_mutations.toml`은 표지 두 개를 새 시험 이름으로 바꿔 열넷 모두 표지까지 맞는 빨강이었다. 변이 로그는 세션 스크래치에 두었다.
6. **판.** 헌법 판을 3.0.69에서 3.0.70으로 올렸다(`operations.md`를 고쳤으므로 판 훅이 본다).

## 측정

- **바이트 대조.** `git show origin/main:docs/constitution/README.md`에서 판 줄 머리(`**Version**: 3.0.69 | … `)를 뗀 나머지 38,291바이트가 `history.md`에 글자 그대로 들어 있다(스크래치 스크립트로 손으로 돌렸다). 옛 README의 비워 둔 문장은 5개, 새 README는 1개다. origin/main은 이 브랜치를 딴 뒤 움직이지 않았다(`git fetch` 뒤 merge-base와 같다).
- **잔존 grep.** `HISTORY_HEAD`, `history_entries`, `이력 문단`, `버전 이력`, `README 이력`을 일지·`history.md`·대기열 밖의 저장소 전체에서 찾았다. 남은 것은 기록(ADR 0045 본문과 이력, 명세, 티켓, 변이 표의 옛 이름 설명)과 새 문장 속의 "이력 문단이 없다"뿐이다. 살아 있는 문서의 잔존은 0이다.

## 결정·번복·확인

- **신호의 조건 둘.** 판 줄이 main과 같다는 조건이 없으면, main을 아직 합치지 않고 문장만 지운 브랜치가 그 판을 가져간 것으로 센다. 그래서 둘 다 요구한다. 판 줄을 비워 둔 판으로 내려 쓰는 길은 열지 않았다. 결정 5의 처음 신호(이 브랜치의 판 줄이 비워 둔 판과 같다)가 형제를 병합할 때 main의 판을 내리는 문제를 ADR 0045 이력 2026-11-06 "비워 둔 판의 신호는 비워 둔 문장을 지운 것이다"가 이미 짚어 신호를 지금 모양으로 정했다.
- **고쳐 쓴 문장도 지운 것으로 센다.** 신호는 꼴이 맞는 문장이 main에는 있고 이 브랜치에는 없다는 것이라, 까닭을 보지 못한다. 도구 독스트링의 "못 보는 것"에 적고 시험으로 고정했다.
- **3.0.61 문장은 뒤따르는 문장과 한 줄이다.** 옛 줄에서 "그 브랜치는 3.0.62 뒤에 병합되어 3.0.63으로 올렸다."가 바로 이어져 함께 두었다. 이 문장은 옛 줄에도 글자 그대로 있다.
- **ADR 0045 본문의 옛 이력 줄 수.** 본문 결정 5는 선택지 설명의 87개와, `N.N.N은/는` 꼴로 세면 84개라고 적었다. 옛 판 줄에서 그 꼴의 머리를 다시 세면 87개이고 2.0.0 문단까지 더하면 88개다(스크래치 `count_heads.py`로 손으로 셌다). 처음 이 일지와 ADR 이력에 "88개"라고 적었다가 명세 축이 짚어 87개와 88개를 가르도록 고쳤다. 84개는 다시 세지 않았다. 결정은 바뀌지 않았다.
- **열린 항목 550.** 읽었다(1회차, 문턱 다섯 번째에 못 미친다). 항목이 겨눈 문제(판을 건너뛴 형제가 비워 둔 문장을 남기지 않는 것)는 그대로 남아 있다. 바뀐 것은 그 문장을 적는 자리가 이력에서 판 줄 곁으로 옮긴 것뿐이라, 항목의 머리·어디로·본문의 낡은 말("헌법 README 이력", 독스트링의 줄 번호)만 새 자리에 맞게 고쳤고 상태는 열림으로 두었다.

## 셀프 리뷰

범위: base `29165af3`(origin/main), 추적 파일 변경 16개, 미추적 2개(`history.md`와 이 일지), 커밋 0개. 표준 축(sonnet·high)과 명세 축(본 세션 모델)을 서브에이전트로 나란히 돌렸다. 두 축을 합치거나 순위를 매기지 않고 적는다. 아래는 서브에이전트가 읽거나 돌린 결과를 이 세션이 받은 것이고, "직접"이라 적은 것만 이 세션이 돌려 본 것이다.

**표준 축.** Critical·Major 없음, Minor 셋, Nit 셋.
- Minor 1. `tools/sibling_overlap.py` `Survey.reserved` 주석이 옛 모델("main의 헌법 이력이 … 비워 둔 판으로 채웠으면")이었다. 잔존 grep에서 "이력 문단"만 찾아 이 주석을 놓쳤다. 직접 고쳤다.
- Minor 2·3. "README에는 판 줄과 비워 둔 문장만 남는다"가 `operations.md`, `CONTEXT.md`, `history.md`, README 머리, ADR에 거의 같은 글로 있고, README에는 제목과 안내 문단도 남아 정밀하지 않다.
- Nit. 모듈 독스트링의 "판 줄이 main과 달라지기 전의 브랜치(main을 합치기 전)"는 앞뒤가 어긋났다. 직접 고쳤다. 남은 3.0.61 문장은 이미 병합된 브랜치의 것이라 지울 브랜치가 없다. `VERSION.search`가 세 자리에서 쓰인다.
- 서브에이전트가 `reserved_version`을 13개 입력으로 불러 독스트링과 맞는 것을 봤고, 새 README 대 옛 README의 바이트 대조(38,291바이트)도 맞았다.

**명세 축.** Critical·Major 없음, Minor 둘, Nit 셋. 시험 세 파일 250개 통과(403초), `check_md_tables`·`check_line_separators`·`check_type_escapes` 0.
- Minor. README 머리 소개 문단에 설명이 붙었다(티켓은 "판 줄과 비워 둔 문장만"). `CONTEXT.md` 수정은 명세의 문서 목록 밖이다.
- Nit. ADR 0045 새 항목의 "88개"는 반쪽이다. 직접 세어 옛 판 줄 안의 머리가 87, 2.0.0 문단까지 88이었다. 직접 고쳤다. 새 막는 글을 겨눈 변이가 없다(티켓은 둘을 맞추라고만 했다). 3.0.61 문장은 아무도 지우지 않는다(명세가 문단 없는 것만 남기라고 했다).

### 고친 것과 남긴 것

- 고침: 주석과 독스트링 오기 둘, ADR 이력과 이 일지의 87·88 문장. 고친 뒤 `uv run ruff check tools/sibling_overlap.py`와 `ruff format --check`가 통과했다(직접).
- 남김(Minor 2·3과 README 머리 문단): "판 줄과 문장만 남는다"는 티켓과 ADR 결정 5가 쓴 표현이고, README 머리는 판을 올리는 세션이 읽는 자리라 까닭을 적을 곳(ADR 이력·일지)과 이 파일이 기록이라는 것을 알리려 둔 문장이다. 같은 사실을 다섯 곳에서 되풀이한 것은 원천이 `operations.md` 하나이고 나머지는 가리키는 쪽이 낫다는 판단 항목이라 이 PR에서 줄이지 않는다.
- 남김(Nit): 남은 3.0.61 문장은 지울 브랜치가 없어도 티켓이 남기라 했다. 새 막는 글을 겨눈 변이는 후속 후보다.

### 다시 돌린 명령

- 전체 `uv run python tools/run_checks.py`는 주석 고침 전에 모두 통과했다(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest 371초, web-verify 529초). 이후 바뀐 것은 문구뿐이라 커밋의 pre-commit이 다시 돌고, 그 결과는 커밋 뒤에 적는다.
- `uv run ruff check .`와 `uv run ruff format --check .`는 통과했다. `uv run python tools/sibling_overlap.py`는 번호 겹침 없음(헌법 3.0.70)이다.

## PR 직전 리뷰

CodeRabbit 좌석이 없어 CLI 대신 대체 둘을 돈다.

- 내장 `/security-review`: 지적 없음. 이 변경은 `tools/`의 정규식 문자열 대조와 문서 이동뿐이고, 새 서브프로세스·역직렬화·경로 조립·네트워크 호출이 없다. 읽는 입력은 `git`이 낸 README 본문과 브랜치 이름이고 둘 다 정규식 대조에만 쓴다. diff에서 `subprocess`·`eval`·`open(`·`Path(`를 더한 줄을 grep해 0건을 확인했다.

- `bug-perf-review`(기준 커밋 29165af3, 18개 파일): 유효·보류 지적 0건이다. `reserved_version`의 경계 입력(같은 글, 문장 삭제, 판 줄 상승, 공백 없는 두 문장, CRLF, 판 줄 둘, 3.0.9와 3.0.10 비교, 빈 글, branch=None, 백틱이 든 이름)은 모두 바르게 처리했다. `exempt()`는 정확한 경로에서만 면제한다(`.bak`, 하위 폴더, 다른 폴더, 대소문자는 거부). 변이 표 `--check`는 "174 모두 한 번씩 있다"로 끝났다. `history.md`는 옛 README의 이력과 2.0.0 문단을 문자열 포함으로 대 봤고 바이트 비교는 내가 따로 했다. 변이를 넣어 돌리는 것과 변이 113~119·121·122의 짝 대조는 하지 않았다고 보고했다. Nit: README의 3.0.61 문장 뒤 "3.0.62 뒤에 병합되어 3.0.63"이 남는데 명세대로 남긴 것이라 두었다.

## 다음

- 커밋 `4f4c73d4`까지 마쳤고(pre-commit 전부 통과, `Skipped`는 카나리아 명세 모양뿐이다. 이 커밋이 카나리아 명세를 건드리지 않았다) 푸시하지 않았다. 컨텍스트가 인계 문턱을 넘은 채 `커밋 뒤` 경계에 와서 새 세션에 넘긴다. 새 세션은 푸시, PR(`git-pr`), `merge.md` 2의 봇 회차, 회고(`retro`, 이 일지에 `## 회고` 절을 더한다), 병합을 한다. 이 세션은 `retro`를 아직 돌지 않았다. PR을 열기 전에 `uv run python tools/sibling_overlap.py`를 한 번 더 친다(지금은 번호 겹침 없음, 헌법 3.0.70). 병합 직전에 `git fetch origin` 뒤 main이 움직였으면 합치고 `docs/constitution/README.md`의 판 줄과 `history.md`가 다른 브랜치의 변경과 부딪히지 않았는지 본다. 다른 브랜치가 옛 한 줄 이력에 문단을 더했으면 충돌 해결 때 그 문단이 사라지지 않게 `history.md`에 옮긴다.
- PR 본문에 적을 것: `05-default-model-required-and-checked` 워크트리를 `tidy-checkouts`가 지우지 못한 것, 옛 이력과 `history.md`의 바이트 대조, 열린 항목 550 판단, `CONTEXT.md`를 고친 것, 후속 후보(`tests/test_plan_status.py`의 `len(rows) - 1`이 `plan-head.md`에 표 줄이 없다는 가정에 기댄다. 이 티켓과 무관하면 후속).

open-session을 부른다 2026-11-07T11:34:10Z

인계 못함 커밋 뒤: open-session의 열기 스크립트(tools/open_session.ps1)를 자동 모드 분류기가 거부했다. 제목을 되돌리고 이 세션에서 푸시와 PR부터 잇는다(2026-11-07, 워크트리 잠금은 이미 풀었고 다시 잠그지 않는다).
