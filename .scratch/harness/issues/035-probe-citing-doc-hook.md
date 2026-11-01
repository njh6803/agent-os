# 035: 프로브를 근거로 드는 명세·ADR·서브에이전트 정의를 고칠 때도 근거의 범위를 짚는 계기 훅

**What to build:** `.claude/rules/probes.md` 셋째 항목(해석은 양성 대조와 다른 해석을 가르는 갈래를 둔 뒤에 일반화한다)은 프로브 README를 고칠 때만 `tools/hook_probe_conclusion.py`가 짚는다. 그런데 어긴 문장은 README 밖에서 났다. 대기열 540의 두 사례는 둘 다 명세나 코드 독스트링에 있었다. design-card-build 명세는 프로브가 pnpm을 거쳐 견준 것을 "셸 없이 띄우는 길로 묶음·장면·빌드 CSS·글꼴이 모두 같았다"로 넓혀 적었고, model-plugin 티켓 04의 `_prepare` 독스트링과 `core.md`는 프로브가 키와 네트워크가 필요 없다는 것까지만 쟀는데 "만들기는 실패할 길이 없다"고 적었다. 둘 다 셀프 리뷰 두 축이 잡았다. 506의 처방(셋째 항목)은 섰고, 506이 넘긴 계기 훅 후보가 이 티켓이다(세 번째 반복).

그래서 훅 `tools/hook_probe_citing_doc.py`를 더한다. PostToolUse `Write|Edit`에서, 고친 파일이 명세(`.scratch/<slug>/spec.md`), ADR(`docs/adr/` 아래 마크다운), 서브에이전트 정의(`.claude/agents/` 아래 마크다운) 가운데 하나이고, 더한 글(Edit의 `new_string`, Write의 `content`)에 프로브를 가리키는 낱말(`probes/`, `프로브`, `탐침`)이 있을 때만 세션·에이전트마다 한 번 알린다. 알림은 근거 문장을 프로브가 잰 상황과 대 보라고 한다. 프로브 README 행이 적은 실행 위치·입력·판·길 밖으로 넓힌 문장(한 길에서 잰 것을 모든 길로, 잰 부분 집합에서 "모두"·"~할 길이 없다"로)이 없는지 보고, 있으면 잰 범위로 좁히거나 갈래를 더해 다시 재거나 어림이라고 적으라고 한다. 가리키는 절은 `.claude/rules/probes.md` 셋째 항목과 `docs/agents/issue-tracker.md` 프로브와 근거 절이다. 막지 않는다.

등록은 `.claude/settings.json`의 첫 `Write|Edit` 묶음, 시험은 `tests/tools/test_hook_probe_citing_doc.py`, 페이로드 표 사례 셋(발동 하나, 침묵 둘), 변이 표 `.scratch/harness/probes/probe_citing_doc_hook_mutations.toml`과 그 README 행이다. `.claude/rules/tools.md` 시간 항목의 Write·Edit 훅 나열과 `docs/agents/issue-tracker.md`의 훅 언급을 맞춘다. 대기열 540은 반영을 닫는다.

**대기열:** 540

**Status:** done

## 수용 기준

- [x] 훅이 명세·ADR·서브에이전트 정의를 고치면서 프로브 낱말을 더한 편집에서만 알리고, 그 밖의 편집(프로브 낱말이 없는 명세 편집, 다른 경로, 다른 도구)에는 지나간다
- [x] 알림이 셋째 항목과 근거 절을 가리키고, 가리키는 절이 문서에 있다는 시험이 있다
- [x] 세션·에이전트마다 한 번이고 표지를 못 쓰면 호출마다 알린다
- [x] 독스트링에 못 보는 것을 적고 그 항목마다 시험으로 고정했다
- [x] 등록, 페이로드 표, 변이 표, `tools.md`와 `issue-tracker.md`의 언급을 맞췄다
- [x] 검증 명령이 모두 초록이다
