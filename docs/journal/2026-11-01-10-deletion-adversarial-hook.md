# 2026-11-01 (10) 지우는 호출 편집에 반박 입력을 짚는 계기 훅

세션 제목: `chore/034-deletion-tool-adversarial-input-hook`. 브랜치 `chore/034-deletion-tool-adversarial-input-hook`, 워크트리 `.claude/worktrees/034-deletion-tool-adversarial-input-hook`. 티켓 `.scratch/harness/issues/034-deletion-tool-adversarial-input-hook.md`(대기열 442).

## 사용자 프롬프트

> 사용자: 대기열 442을 티켓 .scratch/harness/issues/034-deletion-tool-adversarial-input-hook.md로 쓰고 한다

지시문의 이번 요청 범위는 "PR과 병합까지"다. 모델은 Sonnet 5.5 / high, 어디서는 새 세션이고 주 체크아웃이 미갱신이라 `tidy-checkouts`를 먼저 돌고 `EnterWorktree`로 들어간 뒤 브랜치를 바꾼다.

## 한 일

- `tidy-checkouts`: 루트 `54c79da9`를 `544381ea`(origin/main)로 당겼다. 쉬는 세션이 쥔 `wireframe-optional` 워크트리와 브랜치 `chore/033-wireframe-optional-and-option-count`를 지웠다. 나머지 워크트리는 실행 중인 세션, 프로세스 점유, 바뀐 파일, 병합된 PR 없음, 앱 표지 가운데 하나로 남겼다.
- `EnterWorktree`가 만든 브랜치 `worktree-034-…`를 `chore/034-deletion-tool-adversarial-input-hook`으로 바꿨다.
- 티켓 034를 썼다. 대기열 442의 처방: `tools/`·`web/tools/` 아래 도구 코드에 지우는 호출 줄을 더하는 Write·Edit에, 커밋 전에 판정을 깨는 입력으로 반박하라는 계기를 세션·에이전트마다 한 번 넣는다. 막는 훅이 아니라 계기 훅이다(`.claude/rules/tools.md`의 가름: 지우는 대상이 자기가 만든 임시 폴더인지 사람 폴더인지는 모델이 가른다).
- `tools/hook_deletion_adversarial.py`와 `tests/tools/test_hook_deletion_adversarial.py`(66건), `.claude/settings.json` 등록(첫 `Write|Edit` 묶음 끝), `tools/hook_payloads.toml`의 발동·침묵 사례, `.claude/rules/tools.md` 훅별 시간 항목의 새 문장, 변이 표 `.scratch/harness/probes/deletion_adversarial_hook_mutations.toml`(변이 33과 대조군 1)과 프로브 `README.md` 행, 카나리아 명세 `.scratch/harness/probes/canary/tools_rule_deletion_adversarial_hook.toml`을 더했다. 모두 아직 커밋하지 않았다.
- 훅 설계 결정: 대상은 폴더 이름이 `tools`인 토막 아래의 코드 파일이고 바로 앞 토막이 `tests`이거나 시험 파일 꼴이면 뺀다. 지우는 호출은 더한 줄에서만 보고(`added_lines`), 주석 줄은 거르며, 꼴은 `shutil.rmtree`·`os.remove`·`unlink`·`rmSync`·`rm(`·`git worktree remove`·`git clean`·`branch -D`·`Remove-Item`·`rm -rf`와 git을 리스트 인자로 부르는 꼴이다. 알림은 `hook_scratch_probe_rule`의 표지 모양으로 세션·에이전트마다 한 번이다. 다섯 입력은 `.claude/rules/tools.md`의 지우거나 덮어쓰는 도구 항목과 대기열 442 행에서 가져왔다.

## 결과

근거의 종류: 아래는 모두 이 세션이 워크트리에서 손으로 친 명령의 출력이다. 변이 표와 카나리아의 판정은 커밋한 도구(`tools/mutate.py`, `tools/canary.py`)가 찍은 줄이고, 커밋 전이라 pre-commit과 `tools/run_checks.py`의 전체 한 바퀴는 아직 돌리지 않았다.

- `uv run pytest -q tests/tools/test_hook_deletion_adversarial.py`: 66 통과.
- `uv run python tools/run_hooks.py`(페이로드 표 전체): 훅 페이로드 171건, 어긋남 0건, 표의 빈자리 0건.
- 변이 표: 도구가 `변이 34 모두 기대대로`를 찍었다.
- `uv run ruff check .`와 `uv run ruff format --check .` 통과. `uv run pyright`(새 파일 둘)은 0 오류. `tools/check_type_escapes.py`는 0으로 끝났다.
- 카나리아: 첫 판은 통과 3, 실패 1이었다. 실험군 세 답이 모두 새 문장을 인용해 규칙은 실렸지만, 한 답이 물음의 "괄호 안에 적은 두 번째 설명"을 시간 설명의 괄호로 읽어 카나리아를 옮기지 못했다. 카나리아 문구(expect)는 그대로 두고 물음만 고쳐 다시 돌렸고 통과 4, 실패 0이었다. 바꾼 것은 물음 문구뿐이고 까닭은 명세 머리에 적었다.

## 고친 것과 번복한 것

- 변이 표를 쓰며 서식 출력을 주 체크아웃 루트 쪽 경로로 잘못 리다이렉트해 `C:\project\agent\.scratch_unused.log`를 만들었다. 내가 만든 파일이라 바로 지웠고 그 뒤 주 체크아웃에 남은 것이 없음을 `ls`로 확인했다.
- `.scratch/..` 꼴이 섞인 경로로 변이 표를 썼는데 워크트리 안에 만들어졌음을 `ls`와 `git status --short`로 확인했다.
- 효과가 없을 변이 하나("빈 세션 ID")를 빼고, clean·branch -D의 리스트 인자 꼴 변이 둘을 더했다.

## 인계

경계 `셀프 리뷰 직전`. 세션 제목을 `chore/034-deletion-tool-adversarial-input-hook (인계함)`으로 바꿨고 워크트리 잠금을 풀었다.
open-session을 부른다 2026-11-01T05:58:20Z

## 셀프 리뷰 (`/code-review`, 이어받은 세션)

범위: base `544381eafbeee5d1aacf709ff1cbb5870ac761f2`(= HEAD), 추적 파일 4, 미추적 7(훅·시험·변이 표·카나리아·티켓·일지·이 파일), 커밋 0. 표준 축은 sonnet·high, 명세 축은 기본 모델 서브에이전트가 맡았다.

- 표준 축: 확정 8(줄 집합의 차 거짓 음성이 못 보는 것에 없음, 들여쓰기가 바뀌면 알리는 서술 불일치, 호출 목록 밖의 거짓 음성, 독스트링에 없는 거짓 양성, 시험 파일 꼴 이름의 거짓 음성, `web/tools/**`가 규칙의 `paths`에 없음, 대기열 번호 인용 오류, 훅 목록의 "도는 변이"), smell 3(중복은 훅 규약이 허용, 접미사 목록, 이름 `_before_after`).
- 명세 축: 부분 구현 3(변이 표가 시험 파일 꼴 넷과 표지 쪽 분기를 깨지 않음, 못 보는 것 둘의 시험 없음, Edit 조각 갈래의 시험 없음), 어긋남 2(줄 집합의 차, 호출 꼴), 범위 2(`tools` 토막이 든 모든 자리, 티켓이 든 것 밖의 호출 꼴과 확장자).
- 두 축이 낸 함수 동작 주장은 이 세션이 `uv run python -I`로 스크래치 탐침을 쳐 다시 봤다(손으로 봤다. 같은 글자 줄 복제는 침묵, 꼬리 주석과 블록 주석과 `def rmtree(`는 알림, `web/apps/admin/tools/`와 `node_modules/pkg/tools/`는 대상).

고친 것:
- 독스트링의 사실 셋: "`web/tools/**` 는 규칙의 `paths` 에 없어 `web/tools/judge-trees.ts` 를 열어도 실리지 않는다"(`.claude/rules/tools.md` 머리의 `paths`가 `tools/**`, `tests/tools/**`, `.claude/settings.json`, `.pre-commit-config.yaml`뿐임을 열어 봤다), 정션과 MAX_PATH 사건의 출처를 "대기열 361"에서 "대기열 442 행의 3회차와 2회차"로(442 행 본문을 열어 봤다), Write·Edit PostToolUse 훅 목록에서 "도는 변이" 삭제(`hook_edit_during_mutate`는 `Write|Edit|NotebookEdit` 별도 묶음이고 `tools.md` 시간 항목의 아홉 훅에 없다).
- 못 보는 것에 적은 항목과 각각의 시험 하나: 같은 글자 줄 또 더하기(지나감), 보호문으로 둘러 들여쓰기가 바뀌면 알림, 호출 목록 밖의 지우기 아홉 꼴(지나감)과 확장자 `.bat`·`.cmd`·`.psm1`(지나감), 지우지 않는 줄도 알림 여섯 꼴, 시험 파일 꼴 이름의 도구 파일(지나감), `tools` 토막이 든 다른 자리(대상), Edit의 원래 글이 없을 때 조각 둘로 보기.
- 변이 표: 시험 파일 꼴 변이 넷(접두, 접미, `.test-d.`, `.spec.`), 표지 쪽 변이 넷(폴더·파일을 못 만들 때, 임시 폴더가 없을 때, 빈 세션 ID)을 더했다. 전체 한 바퀴에서 빈 세션 ID 변이가 초록(`어긋남`)이라 시험 `test_main_은_세션을_모르면_호출마다_알린다`에 빈 문자열 세션 갈래를 더했고, 그 번호만 다시 돌려 빨강을 봤다.
- 이 반영으로 새로 쓴 사실 문장(PR 직전 리뷰에 밀 주장): 위 독스트링의 사실 셋, 프로브 `README.md` 행의 "변이 마흔하나(…)와 대조군 하나"와 "`변이 42 모두 기대대로`", 훅 독스트링 못 보는 것의 호출 꼴 열거(아홉 꼴이 지나가고 여섯 꼴이 알린다는 것).

남긴 것과 이유:
- 호출 목록을 넓히지 않았다(리스트 인자 `rm`, `rimraf.sync`, `.Delete(` 등): 티켓은 "등"으로 열어 두었고, 줄 단위 패턴을 넓힐수록 거짓 양성이 늘며 꼴마다 변이를 더해야 한다. 지나간다고 독스트링과 시험에 고정했다.
- 대상 경로를 `tools/`·`web/tools/`로 좁히지 않았다: 거짓 양성의 값이 알림 한 번이다. 넓다고 독스트링과 시험에 적었다.
- Nit 둘(`_before_after`·`texts` 이름, `.cts`·`.mts` 같은 확장자 근거)은 고치지 않았다: 호출 꼴과 상관없는 이름이고 확장자는 이 저장소에서 쓰는 TS 도구 확장자다.
- `tool_name`·`file_path` 꼴 가드의 변이는 더하지 않았다: 그 가드를 빼도 다음 줄(`content`·`old_string` 꼴)이 같은 입력을 걸러, 같은 결과를 내는 변이라 빨갛게 만들 수 없다.

다시 돌린 명령(이 세션이 워크트리에서 쳤다): `uv run pytest -q tests/tools/test_hook_deletion_adversarial.py` 87 통과, `uv run python tools/mutate.py --check <표>`가 `변이 42 모두 원문이 한 번씩 있다`, 전체 한 바퀴는 42 가운데 41이 기대대로이고 빈 세션 ID 하나가 어긋났다가 시험을 고친 뒤 그 번호만 다시 돌려 기대대로. `uv run python tools/run_checks.py`는 종료 0이고 열 단계(check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright-linux, pyright, run-hooks, pytest, web-verify)가 모두 Passed였다(937.9초와 1339.3초는 pytest와 web-verify, 다른 세션이 도는 때였다). `uv run ruff check .`는 `All checks passed!`, `uv run ruff format --check .`는 `1214 files already formatted`. 커밋의 pre-commit 결과는 커밋 뒤 아래에 적는다. `-m llm`·e2e·사진 비교는 이 변경이 닿지 않아 돌리지 않았다.

## 남은 일

- 검증 명령 전부(`tools/run_checks.py`), 티켓을 done으로 바꾸고 체크박스 채우기, pre-commit이 도는 커밋, 푸시, PR, 봇 회차, 병합(`merge.md`의 워크트리 길), 회고. 이 PR은 `.claude/settings.json`과 `.claude/rules/tools.md`를 형제 035가 함께 고치므로 뒤에 병합되는 쪽이 main을 합친다. 형제 035는 `.claude/rules/tools.md`, `.claude/settings.json`, 프로브 `README.md`, `tools/hook_payloads.toml`을, 형제 036은 프로브 `README.md`를 함께 고친다.
