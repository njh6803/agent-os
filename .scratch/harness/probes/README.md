# 하네스 프로브

하네스(`tools/`, `.claude/`)의 코드 주석이 근거로 든 측정 스크립트다. 기능이 아니라 slug 자리에
`harness`를 쓴다. 규약은 `docs/agents/issue-tracker.md`. 2026-09-28에 세션 스크래치패드에서
옮겼다(대기열 29). 옮기기 전의 근거는 프로브를 "실측"으로 가리킨다. 이 표가 그 말을 파일로 잇는다.

`probe_*.ps1` 둘은 Claude 데스크톱 창의 접근성 트리를 읽기만 하고 아무것도 누르지 않는다. 창이 하나 떠 있어야 한다.
`probe_tree.ps1`은 화면의 글이 곧 측정 대상이라 대화 원문의 앞부분을 찍는다. 출력을 옮기기 전에 비밀이
없는지 본다. `probe_send.ps1`은 입력창 값의 길이만 찍는다(PR #89 CodeRabbit, CWE-532).
돌리는 법은 `pwsh -File .scratch/harness/probes/<파일>`이다.

`md_tables_vs_cmark.py`는 저장소 루트에서 `PYTHONUTF8=1 uv run --with cmarkgfm python .scratch/harness/probes/md_tables_vs_cmark.py`로 돈다.
cmarkgfm은 uv의 일회용 환경에만 들어가고 프로젝트 의존성이 아니다. 처음 한 번은 내려받는다.

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 |
|---|---|---|---|
| `probe_send.ps1` | 이름이 "보내기"/"Send"인 요소의 개수·종류·활성 여부·패턴, 그리고 입력창 값의 길이 | `tools/open_session.ps1`의 보내기 버튼 고르기 주석("(2026-09-22 실측,") | Claude 창 하나 |
| `probe_tree.ps1` | 창의 Text·Button·Edit·Document 요소를 훑어 지시문이 화면에 어떻게 보이는지 | `tools/open_session.ps1`의 진단 주석과 슬래시 명령 주석("(2026-09-23 실측)", "(2026-09-23 실측,") | Claude 창 하나 |
| `md_checks_mutations.toml` | `tools/check_md_tables.py`·`tools/check_line_separators.py`의 규칙 하나씩을 뺀 변이 21. 돌리는 법은 `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/md_checks_mutations.toml` | 일지 2026-09-28-07의 변이 줄 | 검사나 그 테스트를 고칠 때. 원문이 한 번 있어야 하므로 코드가 바뀌면 변이도 고친다 |
| `md_tables_vs_cmark.py` | `tools/check_md_tables.py`와 cmark-gfm의 표 모양(끝 줄, 본문 행)과 한 줄의 칸 수. 저장소 마크다운 전부와 무작위 문서 | `tools/check_md_tables.py` 독스트링의 차분 대조 문단과 코드 주석("차분 대조가 찾았다") | 검사를 고칠 때. 어긋나면 줄인 문서를 찍는다 |
