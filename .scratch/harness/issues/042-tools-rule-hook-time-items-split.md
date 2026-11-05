# 042: `tools.md`의 훅별 시간 항목을 이벤트·도구마다 하위 항목으로 나눈다

**What to build:** `.claude/rules/tools.md`의 훅별 시간 항목은 한 줄이다(이 티켓을 시작할 때 9,638자. 대기열 516이 적은 9,030자는 그 뒤로 훅이 더해져 자랐다). 그 줄에는 이벤트와 도구가 다른 훅 스무 남짓이 문장으로 이어져 있다. 이 PR과 main이 각자 훅을 더하면 그 줄 전체가 한 덩어리로 충돌했고, Write·Edit의 PostToolUse 훅을 첫째부터 열째까지 서수로 부르는 문장은 훅이 하나 더해질 때마다 서수가 밀렸다. 서수를 물은 카나리아도 병합 뒤 물음을 고쳐 다시 돌려야 했다(`tools_rule_measure_word_hook.toml`의 머리 주석에 두 번 기록). 이 티켓은 그 줄을 이벤트·도구마다 하위 항목으로 나누고(Write·Edit는 훅마다 한 항목), 서수로 부르던 자리를 훅 이름으로 바꾼다. 서수로 묻던 카나리아는 훅 이름으로 묻게 고친다. 훅 이름, 시간 범위, 근거 문구, 프로브 경로는 한 글자도 바꾸지 않고 옮긴다. 시간을 새로 재거나 훅을 더하고 빼지 않는다.

**대기열:** 516

**Status:** done

## 수용 기준

- [x] 시간 항목이 한 줄이 아니라, 이벤트·도구마다 하위 항목이고 Write·Edit의 PostToolUse 훅은 훅마다 하위 항목이다. 시간 항목 안의 어느 줄도 1,000자를 넘지 않는다(옮긴 뒤 최장 725자)
- [x] 옮긴 몫이 같다. 옛 줄과 새 항목에서 `\d+~\d+ms`·`\d+ms`·`.scratch/…` 경로·대기열·티켓 번호·날짜의 다중집합이 같고, `hook_*` 이름은 서수가 있던 자리에 더한 열둘과, 인계 훅 항목을 가리키는 문장에 더한 `hook_handoff`·`hook_handoff_notice` 둘이 늘었을 뿐이다(셀프 리뷰가 독립 스크립트로 다시 셌다. 일지 2026-11-05-05에 결과)
- [x] 시간 항목에 서수로 훅을 부르는 문장(`첫째가`·`넷째는`·`열째까지`·`일곱 다` 등)이 남지 않는다. 카나리아 머리 주석의 옛 서수는 그 명세가 겪은 일을 적은 기록이라 두었다
- [x] 서수로 훅을 묻던 카나리아 여섯(`.scratch/harness/probes/canary/tools_rule_{measure_word,ui_design,scratch_probe,probe_conclusion,journal_evidence}_hook.toml`과 `.scratch/design-reverse-sync/probes/canary/tools_rule_web_edit_hook.toml`)이 훅 이름으로 묻고, 바꾼 명세는 실제로 돌려 통과 4다(결과는 각 명세의 `# 최신 결과:` 줄). 물음을 바꾸지 않은 `source = ".claude/rules/tools.md"` 명세는 `--preflight`가 통과한다
- [x] 회고 반영: 516의 고침, 일지 2026-10-28-07-measure-word-hook.md·2026-10-28-08-bug-perf-review-batch.md. 대기열 516에 닫힘 표지를 단다
- [x] 검증 명령이 모두 초록이다
