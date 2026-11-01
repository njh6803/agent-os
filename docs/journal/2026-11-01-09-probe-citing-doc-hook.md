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

## 인계 메모 (이 절은 단계를 닫는 "다음"이 아니다)

- 컨텍스트가 인계 문턱(20만 토큰)을 넘은 채 셀프 리뷰 직전(`/code-review` 호출 직후)에 왔다. 새 세션이 같은 브랜치·워크트리에서 셀프 리뷰부터 이어 커밋, PR, 병합, 회고까지 하고 이 일지에 "다음"을 쓴다.
- 커밋하지 않은 변경이 워크트리에 있다: 훅·시험·등록·페이로드 표·변이 표와 README 행·카나리아 명세 둘·규칙 둘(`probes.md`, `tools.md`)·`issue-tracker.md` 한 문장·티켓·이 일지. 티켓 `035`는 아직 `in-progress`이고 수용 기준 상자는 모두 비어 있다. 셀프 리뷰를 반영하고 전체 검증을 마친 뒤 `done`과 상자를 채운다.
- 전체 러너 `uv run python tools/run_checks.py`는 이 세션이 한 번 띄웠으나 일지 번호를 `--move`로 옮기기 전에 시작했고, 인계하며 멈췄다. 읽은 부분은 check-ticket, zizmor, lint-imports, check-type-escapes, check-instructions, pyright, pyright-linux가 Passed였고 pytest와 web 단계의 결과는 보지 못했다(출력 파일을 읽은 것이다). 새 세션이 다시 돌린다. 린트 둘(`ruff check .`, `ruff format --check .`)은 러너에 없어 따로 치고, 포맷 한 건을 `ruff format`으로 고친 뒤 다시 치지는 않았다.
- 일지 번호는 형제 `037`과 겹쳐 `2026-11-01-07`에서 `-09`로 옮겼다(`sibling_overlap.py --move`). 이 일지의 옛 번호 인용도 도구가 옮겼다.
- 카나리아 보고: 새 `probes_rule_citing_doc_hook.toml`(통과 4)과 고친 `tools_rule_measure_word_hook.toml`(통과 4)은 위 "카나리아" 절의 결과다. `probes_rule_conclusion_hook.toml`·`tools_rule_probe_conclusion_hook.toml`은 사전 확인만 통과했다.
- 형제 `034`(`034-deletion-tool-adversarial-input-hook`)도 `.claude/settings.json`·`.claude/rules/tools.md`·`tools/hook_payloads.toml`·`.scratch/harness/probes/README.md`를 고친다(`sibling_overlap.py`의 함께 고친 파일). 뒤에 병합되는 쪽이 main을 합친다.
- 세션 제목: 인계하며 `chore/035-probe-citing-doc-hook (인계함)`으로 바꿨다. 백그라운드 작업(전체 러너와 그 대기)은 TaskStop으로 멈췄고, 잠금은 `git worktree unlock`으로 풀었다.
- open-session을 부른다 2026-11-01T05:57Z
