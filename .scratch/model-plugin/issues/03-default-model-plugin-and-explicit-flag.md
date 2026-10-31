# 03: 저장소와 시험 환경이 기본 모델 플러그인 `claude-opus-5`를 두고 `--model`로 명시해 넘긴다

**What to build:** 저장소에 모델 플러그인 `plugins/models/claude-opus-5/plugin.toml`이 생겨 관리 화면 목록에 모델 행으로 뜬다. 운영자 문서가 기본 모델의 이름을 명시해 넘기는 길을 보인다. `.env.example`에 `AGENT_OS_MODEL=claude-opus-5` 줄이 들고, README의 `serve` 줄이 `--model claude-opus-5`를 적는다. 실제 `serve`나 CLI를 격리된 플러그인 루트로 띄우는 시험과 두 e2e 스택은 그 루트에 같은 이름의 모델 매니페스트를 두고 `--model claude-opus-5`를 명시해 넘긴다. 그래서 개발자 셸의 `AGENT_OS_MODEL`에 기대지 않는다.

**동작은 바뀌지 않는 준비 티켓이다.** 지금 코드에서 `claude-opus-5`는 코드의 기본 모델 이름과 같다. 이 티켓이 깐 자리 덕분에 04가 모델 파일을 읽기 시작하고 05가 코드의 기본값을 걷어도 이 시험들과 스택이 초록으로 남는다. 명세는 이것을 런타임 뒤의 "가장자리 묶음"으로 두었는데, 명세 검토가 방향이 반대라고 보였다. 런타임이 먼저 들어오면 기본 모델 매니페스트가 없는 격리 루트와 두 e2e 스택이 빨갛고, 이 준비는 지금 코드에서도 초록이다(명세 Further Notes 마지막 불릿의 2026-10-31 명세 검토 주석). 코드의 기본값이나 모델 생성 함수에 기대는 시험(`DEFAULT_MODEL`을 import하거나 `anthropic_chat_model`을 가로채는 것, 이름을 푸는 순서를 재는 것)은 여기서 고치지 않는다. 그것을 걷는 04와 05가 함께 고친다.

근거는 `.scratch/model-plugin/spec.md`의 "저장소의 기본 모델 플러그인과 격리 루트" 절과 그 2026-10-31 명세 검토 주석, "고칠 자리"의 2026-10-31 주석, Testing Decisions의 "저장소 상태"·"두 e2e 스택"이다. 거부한 안 셋(격리 루트의 기본 모델을 다른 이름으로, 스택이 환경변수로 넘기기, `sonnet` 픽스처를 지우기)은 그 절에 있다.

**Blocked by:** 01(지금 sdk는 모델 종류의 `provider`·`model_id`를 모르는 칸으로 거부해, 01 전에 이 파일을 두면 목록에서 표지 행이고 읽히지 않는다)

**Status:** done

### 저장소와 운영자 문서

- [x] **`plugins/models/claude-opus-5/plugin.toml`을 둔다.** 공통 넷(`version = "0.1.0"`)에 `provider = "anthropic"`, `model_id = "claude-opus-5"`, `max_tokens = 16000`이고 `temperature`는 적지 않는다(지금의 동작 그대로). 저장소의 이 파일을 실제 파일시스템 어댑터로 읽어 종류·제공사·모델 id·`max_tokens`·없는 `temperature`를 보는 시험을 둔다. 선례는 저장소의 플러그인을 실제 어댑터로 읽는 `tests/test_calc_plugin.py`다(명세의 "저장소 상태" 선례는 2026-10-31 명세 검토 주석대로 이것이다)
- [x] **`.env.example`에 `AGENT_OS_MODEL=claude-opus-5` 줄이 든다.** 둘레의 주석 모양을 따른다
- [x] **README의 `serve` 줄이 `--model claude-opus-5`를 적는다**(명세 검토가 둘 가운데 하나를 고르라고 했고 to-tickets가 명시하는 쪽을 골랐다. 스택·시험과 같은 길이다). `disabled.toml` 줄의 "skill과 model은 로더가 생길 때" 문장은 켜고 끄기가 실제로 듣게 된 뒤인 06이 고친다

### 격리 루트의 시험

- [x] **`tests/test_main.py`에서 실제 파일시스템 어댑터가 플러그인을 읽는 루트는 모두 `models/claude-opus-5/plugin.toml`을 함께 둔다.** `workspace` 픽스처만이 아니다. to-tickets 시점(main `d4221552`)에 그 파일에는 `tmp_path`에 루트를 따로 짓는 실행 전 오류의 매개변수 시험, `--plugins-root`로 `custom` 아래 루트를 쓰는 시험 둘, 실제 `serve` 프로세스를 띄우는 `_serving`이나 저장소의 calc를 복사하는 `_copy_repo_plugins`를 쓰는 `-m llm` 시험, `tmp_path`에 루트를 짓고 실제 CLI 프로세스(`_cli`)로 멈춘 실행을 다른 프로세스가 재개하는 `-m llm` 시험이 있다(셀프 리뷰와 PR 직전 리뷰가 파일을 열어 봤다). 빠뜨린 루트는 04가 모델 파일을 읽기 시작하는 순간 빨개진다. 명세의 준비 순서대로면 실행 전 오류 시험의 "진입점 import 실패" 사례는 import보다 앞선 `기본 모델 플러그인이 없다`로 바뀐다. 그래서 `main(`을 부르거나 CLI·`serve` 프로세스를 띄우는 자리(`_cli`와 그것을 쓰는 `_cli_run`, `_serving`)를 grep해 그 자리가 쓰는 루트마다 대 보고, 루트를 짓는 도우미가 함께 쓰게 해도 된다. 내용은 받아들여지는 모델 매니페스트면 되지만, 실제 모델을 부르는 `-m llm` 시험의 루트는 저장소의 `plugins/models/claude-opus-5`를 복사하거나 같은 `model_id`를 적는다. 04부터 그 `model_id`가 제공사에 가기 때문이다(아래 위젯 스택과 같은 까닭)
- [x] **그 루트로 `serve`·`run`·`resume`을 부르는 시험이 `--model claude-opus-5`를 명시해 넘긴다.** 실제 `serve` 프로세스를 띄우는 시험(`_serving`)도 같다. to-tickets 시점에 그 파일의 `main(` 호출은 한 줄로 쓴 `main(["serve"…` 35곳과 `main(["run"…`·`main(["resume"…` 36곳에, 여러 줄로 쓴 호출 하나와 인자 목록을 변수로 짓는 호출 열둘이 더 있다(grep으로 셌다). 호출이 많으니 그 시험 파일 안의 도우미 하나가 붙여도 된다. 멈춘 실행의 안내 줄을 그대로 먹이는 재개(`_guidance`를 쓰는 자리)에는 덧붙이지 않는다. 그 줄이 `--model`을 싣게 하는 것은 05이고, 그 전에는 코드의 기본값이 같은 이름이라 초록이다. 빼는 것은 이름을 푸는 규칙 자체를 재는 시험(빈 이름, 플래그·환경변수·기본값의 순서)이고 그것은 04·05가 고친다
- [x] **`-m llm` 시험 가운데 저장소 루트에서 실제 CLI를 돌리는 것도 `--model claude-opus-5`를 명시한다**(명세 "저장소의 기본 모델 플러그인과 격리 루트"). 저장소의 플러그인 파일이 그 이름을 받친다. 시험의 수는 늘지 않는다. calc 시험의 새 단언(플러그인 이름과 `model_id`를 다르게 둔 것)은 모델 파일을 읽는 04가 더한다. 지금 코드에서는 플러그인 이름이 그대로 제공사에 가서 실패하기 때문이다
- [x] **저장소 루트를 쓰는 `tests/test_calc_plugin.py`가 새 모델 행과 함께 초록인지 본다.** 목록의 모델 행 수를 단언하는 시험이 있으면 고친다

### 두 e2e 스택

- [x] **관리 화면 e2e 스택(`web/apps/admin/e2e/stack.ts`)이 `models/claude-opus-5`를 쓰고 `serve`에 `--model claude-opus-5`를 넘긴다.** `models/sonnet`은 01이 고친 그대로 남는다. 모델 행 수를 세는 단언은 to-tickets 시점에 없지만(`admin-token.e2e.ts`는 행을 이름으로 찾는다) 시작할 때 다시 본다
- [x] **위젯 e2e 스택(`web/apps/widget/e2e/stack.ts`와 픽스처를 쓰는 `e2e/plugins.ts`)이 `models/claude-opus-5`를 쓰고 `serve`에 `--model claude-opus-5`를 넘긴다.** 픽스처의 `model_id`는 저장소 파일과 같은 `claude-opus-5`다. 실제 모델 모드는 저장소의 플러그인을 복사한 뒤(`copyRepoPlugins`) 같은 루트에 픽스처를 쓰므로(`writeFixturePlugins`), 다른 id를 적으면 복사해 온 저장소 파일이 그 픽스처로 덮여 `-m llm_widget`이 가짜 id를 제공사에 보낸다(명세가 코드를 읽은 시나리오이고 돌리지 않았다)

### 검증

- [x] **빨강을 먼저 본다.** 저장소의 모델 플러그인을 읽는 시험이 파일이 없어 실패하는 것이 첫 빨강이다. 나머지는 지금 코드에서 이미 초록인 자리를 명시로 바꾸는 것이라, 바꾼 뒤에도 초록인지 본다
- [x] **검증 명령이 모두 초록이다.** 손으로 치는 다섯에 더해 관리 화면 e2e(`pnpm -C web/apps/admin exec playwright test`)와 위젯 e2e(`pnpm -C web/apps/widget exec playwright test`), 그리고 `-m llm`(CLI 시험의 인자를 바꿨다)과 `-m llm_widget`(위젯 스택을 바꿨다)을 친다. `.env` 경로는 `docs/constitution/operations.md`의 LLM 테스트 절이다
