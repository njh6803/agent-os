# 05: 예시 — calc가 `answer-format` 스킬을 쓰고, 실제 모델 시험이 스킬 경로를 끝까지 지난다

**What to build:** 저장소에 예시 스킬 `plugins/skills/answer-format/`이 서고 calc가 매니페스트의 `skills`로 그것을 고른다. calc 코드는 스킬마다 `지침 <이름>: <본문>` 블록을 프롬프트에 엮는다. 그래서 실제 CLI와 실제 모델로 calc를 돌리면 스킬 문서의 본문이 모델에 간 것이 트레이스의 첫 `llm_called.prompt`에 남고(스토리 23), 스킬 문서를 고치면 서버를 다시 띄우지 않아도 다음 실행의 프롬프트가 바뀌며, 관리 화면에서 이 스킬을 끄면 calc의 다음 실행이 409다. 관리 목록에 스킬 행이 하나 는다.

저장소에서 스킬 경로가 실제로 도는 첫 티켓이다(ADR 0041 "저장소가 예시 스킬 하나를 두고 calc가 고른다"). 04와 나란히 돈다. 함께 고치는 파일은 없다. 04보다 먼저 들어가면 이 행에 옛 안내 줄이 잠시 남는다.

근거는 `.scratch/skill-plugin/spec.md`의 "예시 스킬"(사용자가 골랐다)과 그 2026-11-04 명세 검토 주석, "고칠 자리의 묶음"의 D와 그 주석, "실제 모델 호출 하나", Testing Decisions의 "calc"와 그 주석·"저장소 상태"다. 앞선 결정은 ADR 0041과 그 2026-11-03 이력이다. **본문이 값과 도구 호출을 바꾸지 않는지는 프로브 `.scratch/skill-plugin/probes/answer_format_llm.py`가 아래 글 그대로 쟀다.** 블록을 글로 넣은 calc 사본에서 새 실행 5회가 값 4와 도구 호출을, 이어 가기 3회가 `20`을 냈고, 대조 갈래도 같았다(README). 회차가 적어 드문 흔들림은 잡지 못하고, calc 코드가 엮는 실제 경로와 요약을 지나는 `-m llm` 시험은 지나지 않았다. **본문을 바꾸면 이 결과는 그 본문의 것이 아니므로 프로브를 다시 돈다.**

**Blocked by:** 03(런타임이 고른 스킬을 읽어 `ctx.skills`로 넘긴다)

**Status:** done

### 스킬 폴더

- [x] **`plugins/skills/answer-format/plugin.toml`은 공통 넷(`schema_version = "1"`, `kind = "skill"`, `name = "answer-format"`, `version = "0.1.0"`)뿐이다.** `plugins/skills/.gitkeep`은 지우지 않는다(`plugins/models/.gitkeep`이 모델을 둔 뒤에도 남아 있다)
- [x] **`SKILL.md`의 머리말은 `name: answer-format`과 한 줄의 `description`(계산 답을 적는 형식. 최종 답만 내는 에이전트가 답을 쓸 때 쓴다)이고, 본문은 프로브가 잰 글 그대로다.** "답은 값 하나만 쓴다. 단위·설명·계산 과정을 붙이지 않는다. 계산할 수 없으면 왜 할 수 없는지 한 문장으로 답한다."
- [x] **저장소 상태 시험이 `plugins/skills/answer-format/`을 실제 어댑터로 읽어 `Skill`이 되는 것을 본다.** 저장소의 플러그인을 실제 어댑터로 읽는 선례는 `tests/test_calc_plugin.py`다

### calc

- [x] **`plugins/agents/calc/plugin.toml`에 `skills = ["answer-format"]`이 든다**
- [x] **calc 코드는 스킬마다 `지침 <이름>: <본문>` 블록을 머리 문장("계산 요청이다. …") 뒤, 앞 대화 블록 앞에 두고, 머리 문장과 블록 사이, 블록 사이, 블록 뒤는 모두 빈 줄 하나다.** 본문은 앞뒤 공백을 다듬어 엮는다. 스킬이 없으면 블록이 없어 그 전과 같은 모양이다. 앞 대화 블록이 데이터라고 밝히는 것과 달리 스킬 블록은 지시다(ADR 0041 "컨텍스트의 멤버"). 플러그인은 sdk만 import한다
- [x] **낡는 글을 고친다.** `plugins/agents/calc/agent.py`의 독스트링("그 전과 글자 그대로 같다"), `tests/test_calc_plugin.py`의 머리 독스트링과 `FRESH_PROMPT` 주석과 시험 이름(`test_이어_가지_않은_실행의_프롬프트는_이_티켓_전과_글자_그대로_같다`), `tests/test_main.py`의 `_copy_repo_plugins` 독스트링이다
- [x] **시험 이름을 바꾸면 변이 표 `.scratch/conversation/probes/continuation_mutations.toml`의 선택자(`-k 글자_그대로_같다`)를 함께 고친다.** 그 표는 calc 코드의 원문(`if not lines:`, `conversation.summary`, `exchange`의 줄)도 든다. 바꾼 뒤 `uv run python tools/mutate.py --check .scratch/conversation/probes/continuation_mutations.toml`이 모두 원문을 찾는지 본다

### 시험

- [x] **`tests/test_calc_plugin.py`의 `FRESH_PROMPT`가 머리 문장 뒤에 블록이 든 새 글이다.** 첫 빨강이다
- [x] **스킬이 둘이면 매니페스트 순서로 블록 둘이다.** 임시 플러그인 루트에 저장소 `plugins/`를 복사하고 시험만 아는 본문의 둘째 스킬을 더해 calc의 `skills`에 적는다. 그 본문이 프롬프트에 드는 것이 파일에서 읽힌 글이 프롬프트에 닿는 증거다. 본문을 코드에 베낀 calc는 이 시험을 지나지 못하고, `FRESH_PROMPT`와 실제 모델 단언은 베낀 calc도 지난다(PR 봇 CodeRabbit이 짚었다). 실행 도우미 `_run_calc`가 저장소 루트로 고정이라 임시 루트를 받게 한다
- [x] **`skills`를 지운 calc 사본의 프롬프트가 블록 없는 옛 글이다**(스토리 3)
- [x] **이어 간 실행에서 스킬 블록이 앞 대화 블록 앞에 선다.** 선례는 `tests/test_calc_plugin.py`의 세 시험이다
- [x] **`tests/test_main.py`의 calc `-m llm` 시험에 단언 하나를 더한다.** 트레이스의 첫 `llm_called.prompt`에 저장소의 `plugins/skills/answer-format/SKILL.md` 본문(시험이 그 파일을 읽어 다듬은 글)이 들어 있다. 새 시험을 더하지 않는다. 이 단언은 런타임 전의 코드에서는 초록일 수 없다
- [x] **`tests/test_main.py`의 `_copy_repo_plugins`가 calc가 고른 스킬 폴더도 복사한다.** `-m llm`의 한도 시험이 그 루트로 실제 CLI를 돌린다(ADR 0041 "구현 티켓이 고칠 곳")
- [x] **`-m llm` 시험이 값이나 도구 호출의 단언에서 깨지면 시험을 고치지 않고 멈춰 보고한다**(원칙 II). 프로브의 대조 갈래와 견줘 본문 때문인지 흔들림인지 가른다

### 문서

- [x] **옛 표현을 저장소 전체에서 grep해 살아 있는 문서에 잔존이 0인지 본다**(`CLAUDE.md` 작업 규약 4). "calc의 프롬프트가 그 전과 같다"처럼 스킬이 없다고 읽히는 문장이다. 기록은 고치지 않는다

### 검증

- [x] **빨강을 먼저 본다**(헌법 원칙 II). 첫 빨강은 `FRESH_PROMPT`다
- [x] **검증 명령이 모두 초록이다.** 손으로 치는 다섯, `-m llm`, `-m llm_widget`(위젯 스택이 저장소 `plugins/`를 통째로 옮겨 calc를 부른다)을 친다
