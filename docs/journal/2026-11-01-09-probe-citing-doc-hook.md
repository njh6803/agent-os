# 2026-11-01 (09) 프로브를 근거로 드는 명세·ADR·서브에이전트 정의를 고칠 때도 근거의 범위를 짚는다 (harness 035)

세션 제목: `chore/035-probe-citing-doc-hook`. 지시문으로 연 새 세션이고 티켓은 `.scratch/harness/issues/035-probe-citing-doc-hook.md`다. 나란히 여는 다섯 중 둘째다(형제 034·036·037·038).

## 사용자 프롬프트

> 사용자: 대기열 540을 티켓 .scratch/harness/issues/035-probe-citing-doc-hook.md로 쓰고 한다. … 다음 작업: 프로브를 근거로 드는 문장(명세, ADR, 서브에이전트 정의)을 고칠 때도 probes.md 셋째 항목을 짚는 계기 훅(대기열 540). 이번 요청 범위: PR과 병합까지

## 한 것

- 워크트리 `035-probe-citing-doc-hook`에 들어가 임시 브랜치 `worktree-035-probe-citing-doc-hook`를 `chore/035-probe-citing-doc-hook`로 바꿨다. 티켓 파일을 쓰고 `tools/sibling_overlap.py`를 다시 쳐 번호 겹침이 없음을 봤다.
- 훅 `tools/hook_probe_citing_doc.py`(PostToolUse `Write|Edit`, 계기)를 더했다. 고친 파일이 명세(`.scratch/<slug>/spec.md`), ADR(`docs/adr/*.md`, 색인 `README.md` 제외), 서브에이전트 정의(`.claude/agents/*.md`)이고 더한 글(Edit의 `new_string`, Write의 `content`)에 `probes/`·`프로브`·`탐침`이 있을 때만 세션·에이전트마다 한 번 알린다. 낱말을 요구한 까닭은 표지가 세션·에이전트마다 하나라 프로브와 상관없는 명세 편집이 그 한 번을 쓰면 뒤의 편집에 알리지 못해서다.
- 시험 `tests/tools/test_hook_probe_citing_doc.py` 30건(먼저 썼다), `.claude/settings.json` 등록(첫 `Write|Edit` 묶음), `tools/hook_payloads.toml` 사례 셋, 변이 표 `.scratch/harness/probes/probe_citing_doc_hook_mutations.toml`과 그 README 행, `.claude/rules/tools.md` 시간 항목에 열째 훅, `.claude/rules/probes.md` 끝에 짧은 항목 하나, `docs/agents/issue-tracker.md`의 훅 언급 한 문장.

## 손으로 본 것

- `uv run pytest -q tests/tools/test_hook_probe_citing_doc.py`: 30 passed.
- `uv run python tools/run_hooks.py`(래퍼를 거친 실제 실행): `훅 페이로드 172건, 어긋남 0건`. 새 훅의 사례 셋이 기대대로(발동 하나, 침묵 둘)였다.
- `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/probe_citing_doc_hook_mutations.toml`: 도구가 `변이 14 모두 기대대로`를 찍었다.

## 카나리아 (규칙 파일을 고쳤다)

`probes.md`와 `tools.md`를 고쳤으므로 `claude -p`로 규칙이 실리는지 봤다. 러너의 stream-json에는 실린 규칙 본문이 없어(`tools.md` 훅 항목) 아래는 모델의 답을 읽은 것이다.

- 새 카나리아 `.scratch/harness/probes/canary/probes_rule_citing_doc_hook.toml`. 첫 판은 더한 문장이 `probes.md` 셋째 항목(긴 한 줄) 한가운데에 있었고 실험군 셋 가운데 둘만 통과했다(하나는 "없음"). 질문이 묻는 자리를 좁힌 둘째 판도 같은 2/3였다. 규칙이 실리지 않은 것인지 긴 항목에서 문장을 놓친 것인지는 가르지 못했다. 결과를 본 뒤 문장을 짧은 독립 항목(파일 끝)으로 옮기고 질문을 그 항목에 맞췄다. 그 셋째 판이 통과 4(실험군 셋 모두 통과, 대조군 "없음")였다. 바꾼 기준과 까닭은 그 명세의 머리 주석에도 적었다.
- 기존 명세 `tools_rule_measure_word_hook.toml`: 열째 훅을 같은 괄호에 더해 시간의 말이 "여섯 다"에서 "일곱 다"로 바뀌어 사전 확인이 실패했다. 물음 2와 카나리아 둘째 조각을 맞추고 다시 돌려 통과 4였다.
- 사전 확인 통과: `probes_rule_conclusion_hook.toml`(대조군 커밋 77ecd319), `tools_rule_probe_conclusion_hook.toml`. 이 둘은 문구를 건드리지 않아 실제로 다시 돌리지는 않았다.

## 번복·결정

- 한 훅에 합치지 않고 따로 등록했다(`hook_probe_conclusion`의 "왜 따로 등록하는가"와 같은 까닭: 판정과 표지가 다르다).
- 알림 문장의 첫 판 위치를 `probes.md` 셋째 항목 안에서 파일 끝의 독립 항목으로 옮겼다(위 카나리아). 훅 알림이 가리키는 "셋째 항목"은 그대로다.

## 셀프 리뷰 (새 세션이 이어서 돌았다)

`/code-review`를 base `544381ea`, 추적 파일 7개, 미추적 6개, 커밋 0개로 돌렸다. 표준 축(sonnet·high)과 명세 축을 나란히 띄웠다. 두 서브에이전트가 낸 것은 모델의 읽기이고, 시험 30건 통과는 명세 축이 직접 돌려 본 것이다.

고친 것:
- 카나리아 `tools_rule_measure_word_hook.toml` 4행 머리 주석이 "넷째부터 아홉째까지"로 남아 있었다(표준 축, 계약 변경 잔존). "열째까지"로 맞췄다.
- 독스트링 두 곳이 대기열 540 행의 요약을 명세 원문처럼 따옴표로 인용했다(표준 축). 요약이라고 밝히고 따옴표를 뺐다.
- `probes.md` 새 항목의 "모든 길로 적었고"가 사례(셸 없이 띄우는 한 길)보다 넓었다(표준 축). "pnpm을 거쳐 견준 것을 명세가 셸 없이 띄우는 길에서도 같았다고 적었고"로 좁혔다.
- 독스트링의 못 보는 것에 "안 바뀐 기존 낱말"이 빠져 있었다(표준 축, `tools.md` 규칙). 항목을 더하고 시험 `test_못_보는_것_안_바뀐_기존_낱말에도_알린다`로 고정했다.
- 세션 ID가 없을 때 `main`을 직접 돌리는 시험이 없었다(명세 축). `test_main_은_세션을_모르면_표지_없이_호출마다_알린다`를 더했다.
- `probes.md`가 프로브 폴더 파일을 열 때만 실려 명세를 고치는 컨텍스트에는 없는데, 알림은 "셋째 항목"만 가리켰다(표준 축). 알림에 "실려 있지 않을 수 있다, 필요하면 Read로 연다"를 더하고 시험을 붙였다. 첫 문구에 "셋째 항목"을 또 넣었다가 변이 12(알림에서 셋째 항목 빼기)가 초록이 되는 것을 변이 표가 잡아, 문구에서 그 말을 뺐다.
- 티켓 본문의 "페이로드 표 두 사례"를 실제와 같은 "사례 셋(발동 하나, 침묵 둘)"으로 고쳤다(둘 다).
- 대기열 540 행을 취소선과 `**닫힘 (티켓 경로, …)**`로 닫았다(명세 축, 티켓이 요구한 "반영을 닫는다").

남긴 것:
- 알림 문장의 "세션·에이전트마다 한 번이다"는 세션을 모르거나 표지를 못 쓰면 매번 간다는 것과 어긋난다(둘 다 낮음). 훅 독스트링 "한 번" 절이 그 갈래를 적고 있어 두었다.
- 상수 `README`의 값이 `"readme.md"`(표준 축 Mysterious Name)와 `ToolInput.old_string`의 선언만 있는 필드(Speculative Generality)는 판단 항목이고 시험과 변이 표가 이름을 쓴다. 두었다.
- `tools/hook_probe_conclusion.py` 45~46행이 "명세·ADR에는 알리지 않는다"고 적은 것은 그 훅만의 일이라 참이다(명세 축). 교차 언급은 더하지 않았다.
- 컨텍스트 압축 뒤 표지가 남아 알림이 사라지는 한계는 독스트링이 이미 적었다(둘 다). 되살리는 길은 `hook_probe_conclusion`과 같아 두었다.
- NFD 한글 낱말과 역슬래시 낱말 `probes\`는 못 잡는다(표준·명세 축이 서브에이전트가 `-I`로 불러 봤다). 이 PC의 Write·Edit 입력에서 낱말이 그 꼴로 오는지는 재지 않았다. 독스트링에 적지 않았고 시험도 없다.

다시 돌린 것: `uv run python tools/run_checks.py` 모든 단계 통과(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright-linux, pyright, run-hooks, pytest, web-verify. 반영 뒤에 쳤고, 그 뒤 알림 문장 한 군데를 더 고쳤다). `uv run ruff check .`와 `ruff format --check .` 통과. 변이 표는 알림 문장을 마지막으로 고친 뒤 `변이 14 모두 기대대로`를 도구가 찍었다. 카나리아는 `probes.md` 새 항목의 둘째 문장 한 군데와 `tools_rule_measure_word_hook.toml`의 머리 주석만 고쳐 다시 돌리지 않았다(기대 문구는 첫 문장과 `tools.md`에 있다).

## PR 직전 리뷰 (세 번째 세션)

`coderabbit auth status`가 `Seat: not assigned`(Plan: Free)라 CLI 축은 비어 있고, 규약의 대체 둘(`operations.md` 리뷰 파이프라인 2)을 나란히 돌렸다. 아래는 모델의 읽기이고, 판정은 이 세션이 코드와 직접 돌린 결과로 했다.

- 내장 `/security-review`: 지적 없음. 훅이 입력을 문자열 견줌에만 쓰고, 표지 파일 이름이 `sha256` 16진이라 경로를 벗어날 수 없고, 출력이 입력을 되풀이하지 않는다. 임시 폴더에 같은 이름을 미리 만들어 알림을 끄는 길은 방어 심층이고 알림이 막는 장치가 아니어서 보고하지 않았다.
- `bug-perf-review` 서브에이전트: 유효 1(Minor), 보류 1, 오탐 6.
  - 유효: `is_citing_doc`이 이름이 `spec.md`이면 `.scratch`가 아닐 때도 곧바로 거짓을 돌려줘서 `docs/adr/spec.md`와 `.claude/agents/spec.md`를 놓쳤다(서브에이전트가 `-c`로 직접 불렀다). 고치는 값이 코드 두 줄이라 PR 전에 고쳤다. 시험 `test_이름이_spec_md_인_ADR_과_서브에이전트_정의도_본다`를 더했고, 변이 표에 그 회귀를 깨는 변이를 더하고 기존 변이 1의 원문을 새 코드에 맞췄다. 도구가 `변이 15 모두 기대대로`를 찍었다.
  - 보류: `MultiEdit`로 고친 글. 이 세션의 도구 목록에 `MultiEdit`가 없고, 같은 매처 `Write|Edit`를 쓰는 다른 훅도 같은 한계라 독스트링에는 적지 않았다. 있다고 재지 않은 것을 못 보는 것으로 적으면 규칙(`tools.md` "못 본다고 적은 주장도 잰다")과 어긋난다. 도구가 생기면 `tools.md`의 매처 항목을 함께 고칠 일이다.
  - 오탐: 깨진 입력의 종료 코드 1(fail-open), 표지 경쟁 조건(`O_EXCL`), 표지가 쌓임(래퍼와 같은 한계), cp949 출력(ASCII 출력), 짝 없는 서로게이트 세션 ID(`surrogatepass`), `tools.md`의 "열째"(맞다).

## 인계 메모 (이 절은 단계를 닫는 "다음"이 아니다)

- 두 번째 인계다. 첫 인계는 셀프 리뷰 직전이었고, 이 세션이 셀프 리뷰를 돌려 반영하고 전체 검증을 마친 뒤 커밋(`b38d473b`)까지 했다. 컨텍스트가 인계 문턱(20만 토큰)을 넘어 `커밋 뒤` 경계에서 넘긴다.
- 사용자 프롬프트는 위 "사용자 프롬프트" 절의 것 그대로다. 이 세션이 새로 받은 사용자 말은 없다. 요청 범위는 PR과 병합까지다.
- 한 것: 셀프 리뷰 반영(위 "셀프 리뷰" 절), 대기열 540 닫기, 티켓 `done`과 수용 기준 상자 채우기, 전체 러너 통과, 린트 둘 통과, 변이 표 `변이 14 모두 기대대로`, 커밋 한 건. pre-commit은 통과했다(커밋이 600초를 넘겨 백그라운드로 넘어갔다가 종료 코드 0으로 끝났다).
- 남은 일: 푸시, PR 열기, `merge.md`의 봇 회차(`@coderabbitai review` 코멘트와 CI 대기), 병합, 병합 뒤 이 일지에 `## 다음`을 쓰고 회고(`retro`). PR은 아직 열지 않았다.
- 푸시하기 전에 `git fetch origin` 뒤 `origin/main`이 움직였는지 본다. 형제 `034`(`034-deletion-tool-adversarial-input-hook`)도 `.claude/settings.json`·`.claude/rules/tools.md`·`tools/hook_payloads.toml`·`.scratch/harness/probes/README.md`를 고친다. 먼저 병합되는 쪽이 있으면 뒤에 병합되는 쪽이 main을 합친다. `tools.md` 시간 항목의 서수("열째", "일곱 다")와 카나리아 `tools_rule_measure_word_hook.toml`의 물음 2·`expect`가 034의 훅 등록과 겹쳐 어긋날 수 있다. 합친 뒤 서수와 그 카나리아를 다시 맞춘다.
- 일지 번호 `2026-11-01-09`보다 이름순으로 뒤인 형제 일지(`-10`, `-11`)가 있어 겹치지 않는다. 형제가 먼저 병합되고 같은 번호를 쓰면 `sibling_overlap.py --move`로 옮긴다.
- 카나리아 `probes_rule_citing_doc_hook.toml`과 고친 `tools_rule_measure_word_hook.toml`은 셀프 리뷰 반영 전에 돌려 통과 4였다. 반영 뒤에는 `probes.md` 새 항목의 둘째 문장과 머리 주석만 고쳐 다시 돌리지 않았다.
- 세션 제목: 인계하며 `chore/035-probe-citing-doc-hook (인계함)`으로 바꾼다.
- open-session을 부른다 2026-11-01T06:47Z

## 검증 (세 번째 세션, PR 직전 리뷰 반영 뒤)

- 훅 시험: `uv run pytest -q tests/tools/test_hook_probe_citing_doc.py`가 34건 통과(변이 도구의 기준선이 찍은 `34 passed in 0.71s`).
- 변이 표: `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/probe_citing_doc_hook_mutations.toml`이 `변이 15 모두 기대대로`를 찍었다. 변이 11(표지를 보지 않고 늘 알린다)과 12(등록의 매처와 도구 목록이 갈린다)는 각각 114초·107초가 걸렸다. 원인(실패 출력, 부하, 다른 세션의 `uv`)은 가르지 못했다.
- 린트 둘: `uv run ruff check .`와 `uv run ruff format --check .`가 통과했다.
- 전체 러너 `uv run python tools/run_checks.py`: lint-imports, check-ticket, zizmor, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, web-verify가 Passed였고 pytest만 `2 failed, 6055 passed in 739.60s`였다. 실패 둘은 `tests/channel/cli/test_interrupt.py`의 `test_닫는_도중에_한_번_더_누르면_닫기를_기다리지_않고_끝난다`와 `test_서버를_닫기_시작한_뒤에_한_번_누르면_닫기를_마치고_중단으로_끝난다`이고 둘 다 `Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다`였다. 그 파일만 홀로 돌리니 `6 passed in 42.14s`였다(이 PC에서 손으로 쳤다). 이 브랜치는 그 시험과 코드를 건드리지 않았다.
- 둘째 커밋(`c73ed050`)의 pre-commit이 종료 코드 0으로 끝났다(백그라운드로 돌려 알림으로 받았다).
- PR #452를 열었다. 열기 전 `coderabbit auth status`가 `Seat: not assigned`였다.

## 회고

후보 4, 승인 0, 기각 4, 넘김 0. 사용자에게 묻지 않았다.

1. **경로 판정의 이름 분기가 `.scratch` 밖의 `spec.md`를 놓친 것(기각).** PR 직전 `bug-perf-review`가 Minor로 잡았고 PR 전에 고쳤다. 손상은 없었고 시험 하나와 변이 하나로 고정했다. 리뷰가 제 몫을 한 사건이라 승인의 회차로 세지 않고, 경로 판정의 논리 허점이라 검사로 옮길 일반 규칙도 없다. 근거: 서브에이전트 보고와 이 세션이 변이 표로 돌린 결과(`변이 15 모두 기대대로`).
2. **부하에서만 빨간 Ctrl+C 시간 시험 둘(기각, 일지에만).** 같은 종류를 대기열 306이 받아들이고 닫았고, 그 결정은 새 사례를 회차에 더하지 않고 일지에만 적는다(retro 5단계). 같은 파일의 열린 행 531은 `assert 끝.pressed[0] < 끝.cancelled`의 다른 단언이라 이 사건과 다른 일이다(`tools/queue_open_rows.py --ref origin/main --search test_interrupt --search Ctrl.C`로 찾았다). 근거: 러너 출력과 홀로 돌린 `6 passed`(위 검증 절). 일지만 바꾼 셋째 커밋의 pre-commit에서도 같은 종류가 한 번 더 났다. `tests/tools/test_rerun_runner.py::test_같은_갈래가_두_번_든_파일럿의_두_회차가_함께_돌아도_번호가_다르다`가 `assert max(...) == 2`에서 `1 == 2`로 빨갰고(`1 failed, 6056 passed in 836.12s`), 그 파일을 홀로 돌리니 `63 passed in 431.39s`였다(손으로 쳤다). 두 번 모두 pytest가 10분을 넘긴 러너였다.
3. **CodeRabbit 좌석 미배정으로 CLI 축이 비어 있던 것(기각).** `operations.md` 리뷰 파이프라인 2가 이미 그 증상과 대체 둘을 적고 있고, 이 세션은 그대로 따랐다. 이미 있는 지침이 맡은 일이다.
4. **변이 11·12가 각 1분 49초·1분 47초 걸린 것(기각).** 사건은 있으나 원인을 재지 않았다(위 검증 절). 가른 뒤에 다시 본다. 같은 시험을 홀로 돌리면 0.71초라 시험 몫은 아닌 듯하나 어림이다.

만료할 행은 없었다(`uv run python tools/queue_open_rows.py --ref origin/main`의 "만료할 행" 줄이 `(없음)`).

## 다음

모델 플러그인 기능이 닫힌 뒤 하네스 chore 묶음(034~038)으로 열린 다섯 가운데 035가 이 PR(#452)이다. 병합하면 티켓 035는 `done`으로 main에 든다. 형제 034·036·037·038은 이미 각자 워크트리에서 돌고 있고(`git worktree list`), 그 가운데 034가 `.claude/settings.json`·`.claude/rules/tools.md`·`tools/hook_payloads.toml`·프로브 README를 같이 고치므로 먼저 병합되는 쪽의 뒤에 병합되는 쪽이 main을 합치고, 합칠 때 `tools.md` 시간 항목의 서수(열째, 일곱 다)와 카나리아 `tools_rule_measure_word_hook.toml`의 물음 2와 `expect`를 다시 맞춘다.

`next-session` 결정표로는 프론티어를 고를 차례인데 `plan.md`의 프론티어에 남은 기능이 없다(model-plugin이 2026-11-01에 닫혔다). 그래서 이 세션은 다음 기능의 지시문을 내지 않는다. PRD 범위에서 다음 기능을 고르는 설계 인터뷰(`/grill-with-docs`)는 사용자가 기능을 정한 뒤에 연다. 대기열은 회차 3 이상 행이 여럿 남았지만 하네스 chore PR 뒤에는 chore를 잇지 않는 규칙(ADR 0036)이라 이어 열지 않는다.
