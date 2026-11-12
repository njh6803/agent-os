# 2026-11-12 (02:48) local-model 명세

세션 제목 `docs/local-model-spec`. 브랜치 `docs/local-model-spec`, 워크트리 `.claude/worktrees/local-model-spec`. 모델 Fable 5.2 / xhigh(지시문은 "Fable 5.1"로 적었다)로 시작했고, 명세를 쓰던 도중에 사용자가 `/model claude-opus-5-5`로 Opus 5.5 / xhigh로 바꾼 뒤 "다시 시도해 주세요"라고 했다(바꾼 까닭은 듣지 않았다). 주 체크아웃(main `3a07ba979`)에서 시작해 `tidy-checkouts`를 돈 뒤 `EnterWorktree`로 들어왔고, 도구가 만든 브랜치에서 `git switch -c`로 지시문의 브랜치를 땄다. 기준은 `origin/main` `c475168d9`다.

## 사용자 프롬프트

> 사용자: `.claude/skills/to-spec/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: 다음 작업: 기능 local-model. ADR 0057·0058 설계를 바탕으로 명세 작성
> 다음 단계: 명세
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 local-model-spec)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /to-spec
> 브랜치: docs/local-model-spec
> 모델: Fable 5.1 / xhigh
> 읽을 것: docs/journal/2026-11-11-1534-local-model-design.md의 "다음" 절과 "domain-modeling" 절
> 이어받을 상태: 설계 PR(#530)이 병합됐다. 병합 때 셋째 claude-review의 Minor 하나를 PR 코멘트로만 보류했고 일지 "다음"에는 없다. CONTEXT.md의 모델 서버 항목은 피할 말에 "로컬 모델"(서버가 아닌 모델을 이를 때만 허용)과 "엔드포인트"를 올렸는데, ADR 0057·0058과 기능 계획은 "호환 서버", "OpenAI 호환 엔드포인트", "로컬 모델 시험"을 그대로 쓴다. 명세가 마커·모듈·테스트 이름을 정하기 전에 어느 쪽으로 맞출지 정한다. 이 세션들이 연 PR의 CI가 11일 14시~17시(UTC)에 Canonical의 DNS 장애로 apt 단계에서 모두 실패했다가 복구됐다(actions/runner-images 이슈 15296). 같은 문구로 실패하면 코드가 아니라 그 장애를 먼저 의심한다
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

## tidy-checkouts

주 체크아웃을 `3a07ba979`에서 `c475168d9`로 당겼다. 워크트리 `base-agent-tickets`와 브랜치 `docs/base-agent-tickets`를 지웠다. 둘은 도구가 1로 끝나 그대로 두고 넘어갔다. `end-holders`는 `release-image-design` 워크트리를 받은 세션 밖의 프로세스(`sleep.exe`, pid 31244)가 쥐고 있어 아무것도 끄지 않았고, `empty-trash`는 휴지통의 `base-agent-tickets`와 `doc-permission-verdict`의 `web/node_modules`를 다른 프로세스(esbuild.exe, node.exe)가 쥐고 있어 비우지 못했다. 다음 정리가 다시 본다.

## 사용자에게 물은 것 셋

명세를 쓰기 전에 선택 화면 하나로 셋을 물었다. 묻기 전에 화면의 사실을 대 봤다(손으로 봤다, Grep). "호환 서버"는 ADR 0057의 4줄과 ADR 0058의 6줄에 있고 기능 계획에는 없다. "엔드포인트"는 기능 계획 본문과 ADR 0057의 1줄에 있다. `CONTEXT.md`의 **모델 서버** 항목은 피할 말에 "엔드포인트, 추론 서버, LLM 서버, 로컬 모델(서버가 아니라 그 서버가 내는 모델을 이를 때만 쓴다), vLLM"을 든다.

1. **용어.** 질문: "명세에서 '모델을 내주는 서버'를 부르는 말을 어느 쪽에 맞출까요? 용어집(CONTEXT.md)은 '모델 서버'를 쓰라고 하는데, ADR 0057·0058과 기능 계획은 '호환 서버', '엔드포인트'라고 적었습니다."

   > 사용자: 용어집을 따른다 (Recommended)

   그 선택지의 설명: "명세와 새로 짓는 이름(시험용 '가짜 모델 서버', 모듈, 테스트 이름)은 '모델 서버'로 씁니다. 이미 승인된 이름인 제공사 값 openai-compatible, 마커 llm_local, '로컬 모델 시험'은 그대로 둡니다. ADR 본문은 고치지 않고, 명세 첫머리에 'ADR의 호환 서버는 용어집의 모델 서버다'라는 한 줄을 적습니다." 고르지 않은 안은 용어집의 모델 서버 항목에 "호환 서버"를 같은 뜻의 말로 올리는 것이었다.

2. **GPU 실측.** 질문: "빌린 GPU 서버(Runpod 파드)를 실제로 띄워 구성을 확인하는 일을 언제 할까요? 문서만으로는 '파드가 정해진 시간 뒤 스스로 지워지는 타이머'를 vLLM 이미지에 걸 수 있는지 확정되지 않았습니다."

   > 사용자: 구현 티켓에서 띄운다 (Recommended)

   그 선택지의 설명: "ADR 0058이 정한 그대로입니다. 명세는 첫째 구성(모델마다 24GB 파드 하나씩 나란히)과, 그것이 되지 않을 때 차례로 시도할 다음 구성을 미리 적습니다. 지금은 비용과 준비가 들지 않습니다. 미리 적은 구성이 모두 되지 않으면 그때 다시 여쭙니다." 고르지 않은 안은 명세 단계에서 지금 띄워 확인하는 것이었고, 사용자의 준비(Runpod 계정과 크레딧, 주 체크아웃 `.env`의 `RUNPOD_API_KEY`, Terraform 1.6 이상)와 GPU 요금(몇 달러, 어림)이 먼저 들었다. to-spec의 측정 규칙(설계 ADR이 넘긴 측정도 명세가 받는 자리에서 잰다, 대기열 38·61)을 이 측정에는 쓰지 않는 까닭이 이 답이다. 재려면 사용자의 준비와 과금이 먼저 있어야 하고, ADR 0058이 그 측정을 "서버를 띄우는 파일을 들이는 티켓"에 두었다.

3. **시험 이음매.** 질문: "테스트가 제품과 만나는 자리(시험 이음매)를 이렇게 잡아도 될까요? 평소 테스트는 실제 CLI를 띄우고 모델 자리에만 '가짜 모델 서버'(이 PC 안에서 뜨는 작은 HTTP 서버)를 끼웁니다. GPU를 빌려 도는 시험(-m llm_local)은 같은 테스트를 진짜 모델 둘로 돌립니다."

   > 사용자: 이대로 진행 (Recommended)

   그 선택지의 설명: "가짜는 모델 서버 한 곳에만 둡니다. calc 예시가 실제 MCP 도구를 써서 답하고 기록(트레이스)이 남는 것까지 평소 테스트와 CI가 매번 확인합니다. 어댑터의 세부(키가 없을 때, 깨진 도구 호출, 되울린 키 가리기)는 같은 가짜 서버로 어댑터만 따로 봅니다." 고르지 않은 안은 실제 CLI를 띄우는 테스트를 `-m llm_local`에만 두는 것이었다.

## 묻기 전에 원문에서 본 것

설계 세션이 스크래치패드에 받아 둔 원문을 다시 읽었다(읽었다. 클라우드는 부르지 않았고 아래의 구성은 돌려 보지 않았다).

- Terraform 프로바이더의 `runpod_pod` 문서는 `args`를 "Arguments passed to the container entrypoint"로 적고, `docker_entrypoint`와 `docker_start_cmd`를 읽기 전용("as the API decodes it from args", "Set the command through args")으로 적는다. `args`가 이미지의 시작 명령을 바꿀 수 있는지는 이 글만으로 가르지 못했다.
- vLLM의 Docker 문서는 공식 이미지 뒤에 엔진 인자를 붙여 쓰라고 적는다("You can add any other engine-args you need after the image tag"). 셸로 들어가려면 `--entrypoint /bin/bash`로 바꾸는 예시를 싣는다. 그래서 파드 안에서 타이머를 돌리거나 한 파드에 서버 둘을 띄우려면 시작 명령을 셸로 바꿀 수 있어야 한다.
- vLLM의 gpt-oss 안내는 H100·H200·B200을 들고 "Ampere, Ada Lovelace, RTX 5090"은 작업 중이라고 적으면서, 같은 글의 A100 절은 "GPT-OSS works on Ampere devices by default"라고 적는다. 도구 호출은 `--tool-call-parser openai --enable-auto-tool-choice`로 켠다. A.X 4.0 Light의 모델 카드는 `--enable-auto-tool-choice --tool-call-parser hermes`를 적는다.
- Runpod 가격 페이지의 24GB급은 RTX A5000 $0.27, RTX 3090 $0.5, L4 $0.59, RTX 4090 $0.89이고 48GB의 A40은 $0.59다(시간당. Community와 Secure 가운데 어느 값인지는 가르지 못했다).

## 프로브

측정은 `.scratch/local-model/probes/`이고 결과와 결과를 본 뒤 바꾼 것은 그 `README.md`의 "2026-11-12 결과"가 원천이다. `openai_compat.py`의 마지막 전체 실행은 104 사례가 모두 측정이었고 종료 코드 0이었다(쟀다, `.scratch/local-model/probes/openai_compat.py`). 프로브를 돈 환경(`make_env.py`가 만든 것)과 출력 파일은 이 세션의 스크래치패드에 있어 커밋하지 않았고 다른 세션에 넘기지 않는다. 다시 돌리려면 그 README의 "돌리는 법"대로 환경을 새로 만든다.

## 명세를 쓰며 정한 것

명세 `.scratch/local-model/spec.md`의 서두가 수를 센다. 셀프 리뷰 전의 셈은 넘겨받은 것 스물여섯, 사용자가 고른 것 셋, 명세가 정한 것 스물넷, 이력 둘, 거부한 안 스물아홉이다(거부한 안은 `거부한 안:` 표시를 grep으로 셌다). 결정마다의 근거와 거부한 안은 명세의 각 절에 있다. 설계가 묻지 않은 자리를 명세가 재어 찾은 것은 넷이다.

- 라이브러리가 주소별로 나눠 쓰는 HTTP 클라이언트는 한 프로세스의 둘째 이벤트 루프에서 `Event loop is closed`로 실패한다. 그래서 모델마다 쉬는 연결을 두지 않는 클라이언트를 준다(명세 "HTTP 클라이언트").
- 도구 호출의 인자가 JSON이지만 객체가 아니면 pydantic의 검증 예외가 그 인자를 글에 싣는다. 그래서 어댑터는 그 예외에서 틀린 자리만 싣는다(명세 "실패 문구와 되울린 키").
- 쿼리가 든 `base_url`은 요청 경로가 쿼리 뒤에 붙어 깨진다. 그래서 모델 파일을 읽는 단계에서 거부한다(명세 "매니페스트").
- 모델 이름이 `o`와 숫자로 시작하거나 `gpt-5`로 시작하면 라이브러리가 요청을 바꾼다. 알려진 한계로 둔다(명세 "요청").

## ADR 0057의 이력 초안 둘

뒤의 두 결정이 ADR 0057의 본문 문장을 거짓으로 만들어, 파일 끝의 "## 이력"에 2026-11-12 이력 둘("모델 파일의 주소에 쿼리 문자열이 있으면 읽는 단계에서 거부한다", "모델 이름의 머리에 따라 라이브러리가 요청을 바꾸는 것을 알려진 한계로 둔다")을 쓰고 포인터 셋을 달았다. 결정 "주소는 비밀이 아닌 것으로 본다"와 Consequences "주소의 쿼리"에는 앞의 것을, 결정 "요청"에는 뒤의 것을 달았다. 이력을 쓰기 전에 `domain-modeling`을 불렀다. 사용자의 승인은 아직 받지 않았다. 셀프 리뷰를 반영한 뒤에 묻는다(작업 규약 5).

## 받는 쪽에 넘긴 것

명세의 "다른 기능에 넘기는 것"이 원천이다. `.scratch/deploy-package/plan.md` 5행 끝에 쿼리 거부와 배포 안내가 더할 넷(환경의 헤더 변수 넷, `OPENAI_PROXY`를 듣지 않는 것, 모델 이름의 머리, `/v1`까지 적는 것), 호출마다 드는 TLS 악수를 적었다. `.scratch/answer-eval/plan.md` 5행 끝에는 로컬 모델의 지연을 잴 때 호출마다 새 연결과 TLS 악수의 몫을 갈라 적으라는 문장을 적었다.

## 이 세션이 고친 것

- 훅 `hook_probe_citing_doc.py`가 ADR 0057 이력의 세 줄을 짚었다. 측정 낱말("쟀다")이 있는데 프로브 경로가 없었다. 각 괄호에 `.scratch/local-model/probes/openai_compat.py`를 적었다.
- 명세에서 `아래 "다른 문서"`라고 가리킨 자리 둘이 실제 절 이름과 달라 "다른 기능에 넘기는 것"으로 고쳤다.
- 매니페스트 절에 처음 쓴 "쿼리가 든 주소는 어느 모델 서버에도 붙지 않는다"는 어림이 섞여 "Chat Completions의 경로에 닿지 않는다"로 고쳤다. 같은 뜻의 문장이 서두 11행("쿼리가 든 주소는 요청 경로가 깨져 어느 서버에도 붙지 않는다")에 남아 있다. 인계 직전에 grep으로 봤고 고치지 않았다(셀프 리뷰가 다룬다).
- "MCP url은 쿼리로도 붙는다"고 처음 쓴 문장은 재지 않은 말이라 "재지 않았고 범위 밖"으로 고쳤다.
- ADR 0049의 파일 이름을 추측했다가 틀려 Glob으로 다시 찾았다.

검사 셋(`tools/check_adr_pointers.py`, `tools/check_md_tables.py`, `tools/check_line_separators.py`)은 출력 없이 끝났다. 검증 명령 전체와 셀프 리뷰는 아직 돌리지 않았다.

## 인계

셀프 리뷰를 부르기 직전에 세션 컨텍스트가 360,378 토큰으로 인계 문턱 20만을 넘어 훅(`hook_handoff`)이 인계 계기(`셀프 리뷰 직전`)를 냈고, 그 뒤 자동 압축이 왔다. `handoff.md`의 인계하지 않는 때 다섯에는 들지 않았다(`get_session`의 `self`에 `parentSessionId`가 없다). 넘기기 전 이 세션의 제목은 `docs/local-model-spec`이다.

낸 지시문:

```text
다음 작업: 기능 local-model. ADR 0057·0058 설계를 바탕으로 명세 작성
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec
브랜치: docs/local-model-spec
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-12-0248-local-model-spec.md 전체(이 세션이 쓰다 넘긴 일지. 새 세션이 이어 쓰고 커밋한다)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. 일지는 docs/journal/2026-11-12-0248-local-model-spec.md. 명세 본문, ADR 0057의 2026-11-12 이력 초안 둘과 포인터 셋, 받는 기능 계획 둘(deploy-package, answer-eval)의 문장, 프로브와 그 README는 다 썼다. 리뷰의 기준점은 origin/main이고 미추적 셋(.scratch/local-model/spec.md, .scratch/local-model/probes/, 위 일지)을 포함하며, 원천 명세는 ADR 0057·0058과 설계 일지 docs/journal/2026-11-11-1534-local-model-design.md다. 반영 뒤 명세 서두의 수 다섯을 다시 세고, ADR 0057 이력 둘의 승인을 쉬운 말로 묻는다(아직 묻지 않았다). 서두 11행에 어림이 섞인 문장 하나가 남은 것을 알고 넘긴다(일지 "이 세션이 고친 것")
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `docs/local-model-spec (인계함)`으로 바꿨다. 이 세션이 띄운 백그라운드 작업은 없었다. `git worktree unlock C:/project/agent/.claude/worktrees/local-model-spec`이 출력 없이 끝났다.

open-session을 부른다 2026-11-11T20:06:52Z

## 이어받은 세션 (2026-11-12 18:00)

위 인계 지시문을 받은 새 세션이 이 절부터 쓴다. 모델은 Fable 5.2 / xhigh다(받은 지시문의 모델 줄이 그렇게 적혀 있었다). 세션 제목을 `docs/local-model-spec`으로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다. `ListAgents`와 `list_sessions`(보관된 것 포함 15개)에 이 브랜치를 제목으로 한 다른 세션은 없었다(손으로 봤다).

> 사용자: `.claude/skills/to-spec/SKILL.md` 를 읽어 그대로 따른다. (…) 인자: 다음 작업: 기능 local-model. ADR 0057·0058 설계를 바탕으로 명세 작성 (…) 이어받을 상태: 인계: 셀프 리뷰 직전. (…) 이번 요청 범위: PR과 병합까지

지시문의 나머지 줄은 위 "인계"의 "낸 지시문"과 같고 모델 줄만 `Fable 5.2 / xhigh.`다.

### 기준 브랜치가 dev로 바뀌어 있었다

이 브랜치는 커밋 없이 `9d6295f38`에 있었다(`git reflog`에 2026-11-12 09:55의 `merge origin/main: Fast-forward`가 있다. 위 세션이 인계 직전에 친 것으로 보이나 이 일지에는 적혀 있지 않다). 그 뒤 저장소의 기준 브랜치가 dev로 바뀌었다(`docs/constitution/operations.md` "브랜치와 병합", `git branch -r`의 `origin/HEAD -> origin/dev`). `docs/*` 브랜치의 기준 브랜치는 `origin/dev`이므로 `git merge --ff-only origin/dev`로 `fba36f78a`까지 올렸다. 커밋하지 않은 변경과 겹치는 파일이 없어 빨리 감기로 끝났다. 그래서 인계 지시문이 적은 "리뷰의 기준점은 origin/main"은 `origin/dev`의 `fba36f78a`로 바꿔 읽었다.

명세가 "코드를 읽었다"고 적은 커밋 `c475168d9`와 `fba36f78a` 사이에 명세가 기대는 파일이 바뀌었다(손으로 봤다, `git diff --stat c475168d9 HEAD -- src tests plugins …`). `sdk/manifest.py`(에이전트 칸 `max_turns`·`max_tool_calls`, ADR 0052), `core/run.py`, `core/loop.py`, `.claude/rules/core.md`·`sdk.md`, `tests/test_calc_plugin.py`, `plugins/`(assistant, doc-search, cite-sources)다. `uv.lock`과 `pyproject.toml`은 그대로였다. 그 문장들을 지금의 코드로 다시 대 보는 것을 셀프 리뷰의 밀 주장에 넣었다.

### 프로브를 새 환경에서 다시 돌렸다

위 세션의 환경은 그 세션의 스크래치패드에 있어 넘겨받지 못했다. README의 "돌리는 법"대로 이 세션의 스크래치패드에 환경을 새로 만들었다. `make_env.py`의 출력은 설치 61개, 새 패키지 넷(`langchain-openai` 1.6.2, `openai` 3.49.0, `regex` 2026.11.9, `tiktoken` 0.14.0), 락과 달라진 판 없음으로 README와 같았다(쟀다, `.scratch/local-model/probes/make_env.py`). `openai_compat.py` 전체는 측정 104회차, 측정 아님 0회차, 종료 코드 0이었다(쟀다, `.scratch/local-model/probes/openai_compat.py`. 셀프 리뷰를 반영하기 전의 판이다). 환경과 출력 파일은 스크래치패드에 있고 커밋하지 않는다.

검사 넷(`tools/check_adr_pointers.py`, `tools/check_md_tables.py`, `tools/check_line_separators.py`, `tools/plan_table.py --check`)은 출력 없이 0으로 끝났다. `tools/sibling_overlap.py`는 "이 브랜치의 새 번호 없음", "번호 겹침 없음", "함께 고친 파일 없음"이었다.

### 셀프 리뷰 (`/code-review`)

스킬은 dev를 합치며 바뀌어 디스크의 `.claude/skills/code-review/SKILL.md`를 Read로 열어 따랐다. 본 범위: base `fba36f78a`, 추적 파일 3개의 미커밋 변경, 커밋 0개, 미추적 셋(`.scratch/local-model/spec.md`, `.scratch/local-model/probes/`의 17개, 이 일지). 표준 축은 sonnet·high, 명세 축은 본 세션의 모델로 나란히 띄웠다. 두 브리프에 주장 검증 목록 열과 밀 주장(서두의 수, 이력이 빠진 자리, 그 사이 바뀐 코드, 기준 브랜치 전환, 받는 쪽, 명세 안의 모순, 프로브와 명세의 대응)을 넣었고, 프로브의 개별 사례를 다시 돌릴 수 있게 위 환경의 인터프리터 경로를 줬다.

**명세 축의 보고(받은 그대로 줄였다). Critical 0, Major 2, Minor 10, Nit 2.**

- Major 1 (c). 명세 "실패 문구와 되울린 키"의 `<서버>`가 스킴·호스트·포트뿐이라 경로를 싣지 않는다. ADR 0057 결정 "주소는 비밀이 아닌 것으로 본다"의 "실패 문구에 그대로 실린다"와 이력 초안의 "주소의 나머지가 … 실패 문구에 실리는 것은 그대로다"가 거짓이 되는데 이력도 포인터도 없다. 서두의 "본문의 문장을 거짓으로 만들지 않아"의 반례다.
- Major 2 (a). 깨진 JSON 인자의 도구 호출을 가짜 모델 서버로 보는 사례가 없다. ADR 0057 "평소의 시험"과 사용자의 셋째 답("깨진 도구 호출 …은 같은 가짜 서버로 어댑터만 따로")이 요구하는데, B는 `FakeModels`로만 보고 D는 "객체가 아닌 도구 인자"뿐이다.
- Minor 3 (c). "ADR 0057이 출발점으로 적은 꼴"이라는 인용이 ADR 0057에 없다.
- Minor 4 (c). 로컬 모델 시험이 "더하는 둘" 가운데 스킬 문서 본문의 단언은 `tests/test_main.py`의 calc 시험에 이미 있다.
- Minor 5 (c). "실행 하나의 모델 호출은 루프 상한(10턴)과 대화 요약 한 번을 넘지 않는다"는 틀렸다. 끝은 `ctx.llm()` 한 번마다다.
- Minor 6 (c). "`--yes` 없이 … terraform을 부르지 않고"가 걸음 1(판 확인)·4(destroy)와 어긋난다. 종료 코드가 겹칠 때(2와 3, 통과 뒤 지우기 실패, 걸음 4 실패, 모든 후보의 재고 없음)의 가름이 없다.
- Minor 7 (c)(a). `main`을 병합 대상으로 적은 문장 넷. "규약 문서" 절이 ADR 0058 "브랜치 전략과의 관계"와 "제품 판을 내기 전에도 한 번"을 받지 않았다.
- Minor 8 (a). "HTTP 클라이언트"의 재지 않은 셋(취소·실패한 호출의 연결, 여러 번 부를 때, Linux)을 D로 넘겼다. 결과가 포트의 닫기(ADR)를 낳을 수 있다.
- Minor 9 (c). "고칠 자리의 묶음"의 D "위 규약 문서 전부"와 B의 `core.md` 한 줄이 "규약 문서" 절의 묶음 배정과 어긋난다.
- Minor 10 (c). 서두 "그 가운데 넷" 가운데 둘은 스물넷이 아니라 이력이다. 같은 행의 "어느 서버에도 붙지 않는다"는 어림이다.
- Minor 11 (c). `.scratch/deploy-package/plan.md`에 더한 문장이 넷 뒤에 TLS 악수를 다섯째로 싣는다. "`HTTPS_PROXY`, `NO_PROXY`만"은 잰 것이 `HTTP_PROXY`뿐이다.
- Minor 12 (a). answer-eval의 `**Blocked by:**`에 local-model이 없는데 그 확인을 명세에 적지 않았다.
- Nit. 프로브 네 곳의 "호환 서버". "재시도의 시도마다"는 README가 "본다"로 적은 것이다.
- 맞다고 본 것: 수 26·3·24·29와 묶음 8·6·4·7, 명세가 든 사례 이름이 모두 `--list`에 있는 것, 이력 둘의 다섯 사례 재실행, `^o\d`·`gpt-5` 조건, 네 칸, 조립 자리 셋, `temperature` 10·5줄, README의 수치.
- 대조 불가: 저장소 밖 원문(Terraform, vLLM, Runpod 가격).

**표준 축의 보고(받은 그대로 줄였다). Critical 0, Major 2, Minor 6, 판단 4.**

- Major 1 (hard). 기준 브랜치 전환 뒤 거짓이 된 문장. 명세 스토리 20 "변경이 main에 들어오지 않는다", "계약 묶음만 병합된 main" 세 자리, 서두 "이 브랜치의 기준 커밋 `c475168d9`". 그 사이 바뀐 파일을 HEAD에서 다시 대 본 결과 `_ask`·`_describe`·`blamed("model_call")`·`model_caller`, 검사 네 칸 목록, 조립 자리 셋, 예시 모델 하나는 그대로였다고 보고했다.
- Major 2 (hard). `probes/outside_worktree.py` 둘째 회차의 표지 `ANTHROPIC_API_KEY in os.environ`이 "`--env-file`이 넘겼다"와 "세션 환경에 원래 있었다"를 가르지 못한다. `--env-file` 없이 돈 회차에서 그 변수가 없다는 음성 대조가 없다(`.claude/rules/probes.md` 첫째·셋째 항목). 명세의 "`.env`를 넘긴 환경에 `RUNPOD_API_KEY`는 없었다"가 그 위에 서 있다.
- Minor 3. 명세 "HTTP 클라이언트"의 "실행 하나의 모델 호출은 루프 상한(10턴)과 대화 요약 한 번을 넘지 않는다"(명세 축 Minor 5와 같다).
- Minor 4. 서두의 "어느 서버에도 붙지 않는다"와, 매니페스트 절·ADR 이력의 "경로에 닿지 않는다"가 받은 요청 줄에서 끌어낸 추론인데 "쟀다"가 붙어 있다.
- Minor 5. `.scratch/deploy-package/plan.md`의 "표준 프록시 변수(`HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`)만 듣는다"는 `HTTP_PROXY`만 잰 것의 일반화다(명세 축 Minor 11의 뒤 절반과 같다).
- Minor 6. `cases_response.py`의 `_tool_case`와 `_usage_case`가 요청이 1건 이상이고 메시지가 있으면 측정으로 센다. 예외를 기대하는 사례도 까닭(`ValidationError`와 `loc`)을 표지로 보지 않는다.
- Minor 7. 서두 (4)의 "예외 모양은 구현 티켓이 확인한다"가 낡았다. 명세의 "키" 절이 그 모양을 이미 적는다(`.scratch/local-model/probes/openai_compat.py`의 `key_function_raises`).
- Minor 8. answer-eval의 `**Blocked by:**`(명세 축 Minor 12와 같다).
- 판단. 용어집(프로브 README의 "가짜 OpenAI 호환 서버"·"실제 로컬 모델 서버"·"로컬 서버", `cases_response.py`, `fake_server.py`, 명세의 "가짜 서버"·"로컬 모델의 지연"). 명세의 구현 파일 경로 19건(hard 위반은 아니라고 봤다). 명세 "요청"의 `o1` 갈래 "재지 않았다"와 `gpt-5` 온도 조건의 `reasoning_effort` 예외. `adapter_candidate.py`의 `_generate`·`_agenerate` 중복.
- 맞다고 본 것: 사례 이름 104개와 명세가 든 이름, 서두의 수 넷, ADR 포인터 셋과 이력 제목의 글자 일치, 프로브 17개의 README 줄, 일지의 이름 규약과 `> 사용자:` 인용.

### 리뷰 반영 (2026-11-12 19:08까지)

판정은 근거를 먼저 본 뒤에 냈다. Major 넷은 모두 맞다고 보고 고쳤고, Minor는 하나(Linux 측정)만 이유와 함께 남겼다.

**Major.**

- 명세 축 Major 1(실패 문구의 주소). 맞다. ADR 0057 결정 "주소는 비밀이 아닌 것으로 본다"가 주소는 실패 문구에 그대로 실린다고 적고, 명세의 `<서버>`(스킴·호스트·포트)가 그 문장을 거짓으로 만든다. 이력을 하나 더 쓰는 대신 명세를 승인된 결정에 맞췄다. 문구는 `base_url`을 글자 그대로 싣고 찍히지 않는 글자만 이스케이프한다(MCP 어댑터의 `_where`와 같은 방식이다. `adapters/mcp.py`를 읽었다). 앞의 안은 "거부한 안"으로 남겼다. 후보 어댑터도 같이 고쳤다(`_server`를 지우고 `_address`). 승인된 결정 안으로 돌아간 것이라 사용자에게 따로 묻지 않았다.
- 명세 축 Major 2(깨진 도구 호출을 가짜 모델 서버로 보는 사례). 맞다. D에 둘을 더했다. 어댑터 시험의 "응답"에 인자가 깨진 JSON인 호출이 예외 없이 `invalid_tool_calls`에 든다는 사례를, CLI 시험에 calc의 평소 시험과 같은 모양으로 가짜 모델 서버가 깨진 인자의 `add` 호출을 내는 사례를 뒀다.
- 표준 축 Major 1(기준 브랜치 전환). 맞다. 스토리 20, "계약 묶음만 병합된 main" 세 자리, 서두의 기준 커밋 문장을 고쳤다.
- 표준 축 Major 2(`outside_worktree.py`의 음성 대조). 맞다. `--env-file` 없는 실행에 "그 변수가 없다"를 보는 회차를 더하고 두 명령을 다시 쳤다. 첫째 명령은 "env-file 없이 환경에 ANTHROPIC_API_KEY: 없다", 둘째 명령은 "환경에 ANTHROPIC_API_KEY: 있다", "환경에 RUNPOD_API_KEY: 없다"였고 명령마다 측정 2회차, 측정 아님 0회차였다(쟀다, `.scratch/local-model/probes/outside_worktree.py`).

**Minor와 판단, 고친 것.** 명세 축 3(인용을 "이 명세가 프로브를 짓기 전에 세운 첫째 안"으로), 4(로컬 모델 시험의 단언. `tests/test_main.py`의 그 시험을 읽어 같은 것과 다른 둘로 다시 적었다), 5(모델 호출 수의 끝), 6(`terraform apply`와 종료 코드의 차례), 7(규약 문서가 받는 ADR 0058의 두 대목), 9(묶음 배정), 10(서두의 "넷"), 11(배포 기능 계획의 다섯과 프록시 변수), 12(answer-eval의 `**Blocked by:**`), Nit 둘. 표준 축 4(쿼리 주소의 "닿지 않는다"를 잰 것과 어림으로 갈랐다. 명세 서두와 매니페스트 절, ADR 0057 이력 초안), 6(응답 사례의 표지를 요청 1건과 "응답을 읽는 데까지 갔다"로 좁혔다), 7, 판단의 용어("가짜 모델 서버", "실제 모델 서버")와 `o1`·`gpt-5` 조건이다. 명세 축 8의 셋 가운데 둘은 그 자리에서 프로브에 사례를 더해 봤다(`.scratch/local-model/probes/openai_compat.py`, 아래 "새로 잰 것").

**남긴 것과 이유.**

- 명세 축 8의 Linux. 재지 않았다. 리눅스 컨테이너에 환경을 다시 만들어야 하고, 같은 연결 셈을 D의 어댑터 시험이 CI의 리눅스 러너에서 본다(명세 "사례"의 수명과 취소에 적었다). 결과가 결정을 바꿀 자리가 그 시험이 빨개지는 자리와 같다고 봤다. 쉬는 연결을 두지 않는 것이 루프의 종류에 덜 기댄다는 것은 어림이다.
- 판단의 "로컬 모델의 지연". 그대로 뒀다. 용어집은 "로컬 모델"을 서버가 아니라 그 서버가 내는 모델을 이를 때 쓰라고 하고, 그 문장은 모델의 지연을 말한다.
- 판단의 구현 파일 경로 19건. 그대로 뒀다. 이 저장소의 명세가 고칠 자리를 경로로 적는 것은 관행이고 리뷰도 hard 위반이 아니라고 봤다.
- 판단의 `_generate`·`_agenerate` 중복. 그대로 뒀다. 후보는 측정용이고 구현 티켓이 옮기지 않고 새로 짓는다.

**새로 잰 것(쟀다, `.scratch/local-model/probes/openai_compat.py`).** 마지막 전체 실행은 측정 108회차, 측정 아님 0회차, 종료 코드 0이다. 더한 사례는 넷이다.

- `candidate_connections_after_failures`. 후보의 401은 연결 3개 가운데 3개, 재시도가 든 500은 9개 가운데 9개, 200의 JSON 아닌 본문은 3개 가운데 3개, 기한에 끊긴 호출은 3개 가운데 3개가 닫혔고, 기본값 클라이언트의 대조(401)는 3개 가운데 0개였다.
- `calls_on_one_model`. 후보는 네 번 불러 연결 4개를 맺고 넷째 호출이 끝난 시점에 4개가 닫혀 있었다. 대조는 연결 1개를 다시 썼고 닫힌 것이 0개였다.
- `build_rejects_address`. 아래 "리뷰가 묻지 않은 발견".
- `guard_candidate_odd_url_401`. 경로에 공백, 한글, 줄 구분 문자(U+2028)가 든 주소가 예외 글에 글자 그대로 실리고 줄 구분 문자만 이스케이프한 꼴이었다.

104 사례 실행과 견주면 겹치는 104 사례 가운데 `guard_candidate_userinfo_401` 하나만 결과가 달랐다("암호 없음"에서 "암호 글에 있음"으로. 주소를 글자 그대로 싣게 된 결과다. 스크래치패드의 견줌 스크립트로 손으로 봤다). `check_adapter_types.py`는 측정 5회차, 측정 아님 0회차였다(쟀다, `.scratch/local-model/probes/check_adapter_types.py`).

**리뷰가 묻지 않은 발견: 읽는 단계를 지난 주소가 모델을 만들다 거부된다.** 주소를 글자 그대로 싣게 고친 뒤 개행이 든 주소의 예외 글을 보려던 사례가 따로 돌린 실행에서 측정 아님으로 끝났다(종료 코드 1). 호출이 아니라 모델을 만드는 순간 `httpx2.InvalidURL`이 났다. 꼴이 이상한 주소 열을 sdk의 `HttpServer`와 후보의 만들기에 차례로 넣는 사례로 다시 짜니, 검사를 지나고 만들다 실패한 것이 넷(개행, 탭, 숫자가 아닌 포트, 경로 7만 자)이었다. CLI는 `PluginError`만 실행 전 오류로 받는다(`channel/cli/main.py`를 읽었다). 그래서 명세의 "모델 소스와 모듈"에 결정 하나를 더했다. 모델 서버 모듈이 만들기에서 난 예외를 `PluginError`로 바꾸고 문구는 플러그인 이름과 예외 종류의 이름만 든다. 읽는 단계의 검사에 규칙을 더하는 안은 거부했다(판정자가 라이브러리의 주소 해석이고, 원격 MCP 서버의 `url`과 나눠 쓰는 규칙이라 그 칸의 계약이 함께 바뀐다). 계약도 ADR 본문도 바꾸지 않는 결정이라 사용자에게 묻지 않았다. ADR 0057 결정 "키"의 "모델을 만드는 것이 키도 네트워크도 요구하지 않는다"는 그대로 참이다.

**고치며 새로 쓴 사실 문장(PR 직전 리뷰의 밀 주장으로 넘긴다).** 명세의 원문이다.

1. "개행이 든 주소, 탭이 든 주소, 포트가 숫자가 아닌 주소, 경로가 7만 자인 주소가 `httpx2.InvalidURL`로 끝났다"
2. "실행을 준비하는 길은 `PluginError`를 실행 전 구성 오류로 받아 트레이스 없이 진단만 적으므로(`channel/cli/main.py`를 읽었다), 라이브러리의 예외가 그대로 올라오면 그 길을 비켜 간다."
3. "만드는 때에는 키를 읽지 않아(아래 "키") 이 예외에 키가 실릴 길이 없다."
4. "`<주소>`는 모델 파일의 `base_url`을 글자 그대로 실은 것이고 찍히지 않는 글자만 이스케이프한다."
5. "사용자 정보가 든 주소가 어댑터까지 오면 키 대신 Basic 인증이 가고, 그 주소의 암호 글자와 서버가 되울린 Basic 값이 둘 다 문구에 실린다"
6. "실패하거나 취소된 호출도 연결을 남기지 않았다. (…) 그래서 포트에 닫기를 두지 않는다."
7. "호출의 수는 `ctx.llm()` 한 번마다 턴 상한(에이전트 매니페스트의 `max_turns`, 없으면 10. ADR 0052)까지이고, 에이전트가 `ctx.llm()`을 여러 번 부를 수 있어 실행 전체의 상한은 없다"
8. "단언은 `-m llm`의 calc 시험과 같고 두 군데만 다르다"와 그 뒤의 두 차이
9. "`o1-local`에 `temperature=None`을 이름으로 넘긴 요청의 본문에는 `temperature`가 없었다"
10. 종료 코드가 겹칠 때의 차례(3, 2, 1)와 "4는 걸음 1·3·5에서 아무것도 띄우지도 지우지도 않고 끝난 때에만 낸다"
11. "그 기능 계획의 `**Blocked by:**`에는 local-model이 없다. 그 기능의 첫 보고서는 Anthropic API의 모델로 내고, 오픈 모델의 지연은 local-model이 닫힌 뒤 다시 재서 pilot-release의 보고서로 내기 때문이다"
12. "그 시험은 CI의 리눅스 러너에서도 돈다."

**서두의 수 다섯(본문의 표시로 다시 셌다).** 넘겨받은 것 26(그대로), 사용자가 고른 것 3(그대로), 명세가 정한 것 24에서 25(모델을 만들다 거부되는 주소의 처리), 이력 2(그대로), 거부한 안 29에서 32(읽는 단계에 규칙을 더한다, 바꾸지 않고 둔다, 스킴과 호스트와 포트만 싣는다. Grep `거부한 안:`이 33건이고 서두 자신의 언급 하나를 뺀다).

`domain-modeling`은 ADR 0057 이력 초안을 고치기 전에 Skill 도구로 불렀다. 새 용어도 새 ADR도 없다고 봤다.

### ADR 0057 이력 둘의 승인 (2026-11-12 19:21)

셀프 리뷰를 반영한 뒤에 선택 화면 하나로 둘을 물었다(작업 규약 5). 화면에 적은 사실은 올리기 전에 대 봤다. 라이브러리의 조건은 프로브 환경의 `langchain_openai/chat_models/base.py`(1.6.2)의 1301~1306행과 3721행에서 읽었고, 요청 줄과 이름별 결과는 108 사례 실행의 저장한 출력에서 `path_with_query`와 `model_name_quirks`의 줄을 손으로 봤다(Grep과 Read). 그 줄에서 가짜 모델 서버는 깨진 요청 줄에도 답을 돌려줬다(`"text": "pong"`). 가짜 서버가 경로를 가리지 않기 때문이고, 그래서 화면에는 실제 모델 서버에서 실패할 것이라는 말을 어림으로 적었다. 관리 화면 응답에 쿼리가 실린다는 것은 잰 것이 아니라 ADR 0057의 결정에서 따라 나오는 것이라 첫 판의 질문 문장("관리 화면 응답과 실패 문구와 로그에 그대로 남았습니다")을 고쳐 다시 올렸다.

1. **주소의 쿼리.** 질문: "모델 파일의 모델 서버 주소에 `?token=abc` 같은 쿼리 문자열(물음표 뒤의 부가 값)이 적혀 있으면 어떻게 처리할까요? 가짜 모델 서버로 재어 보니 그런 주소는 요청이 깨진 주소로 전송되었고, 물음표 뒤의 값이 실패 문구와 INFO 수준의 로그에 그대로 실렸습니다."

   > 사용자: 파일을 읽을 때 거부한다 (Recommended)

   그 선택지의 설명: "운영자가 주소에 `?`를 적으면 실행이 시작되기 전에 "base_url 에 쿼리 문자열을 적을 수 없다"라는 문구가 표시됩니다(구현은 다음 단계의 티켓이 합니다). 물음표 뒤에 적은 비밀이 실패 문구나 로그나 관리 화면 응답으로 새어 나갈 경로가 사라집니다. 대신 주소의 쿼리가 꼭 필요한 모델 서버에는 접속할 수 없는데, 재어 본 대로라면 막지 않아도 요청이 깨진 주소로 전송되므로 실제로 잃는 것은 없을 것으로 보입니다(어림)." 고르지 않은 안은 원래 결정대로 막지 않는 것이었다.

2. **모델 이름.** 질문: "모델 이름이 `o1…`·`o3…`처럼 `o`와 숫자로 시작하면 지시문이 다른 역할로 전송되고, `gpt-5…`로 시작하면 모델 파일의 온도 값이 빠지는 라이브러리의 동작을 어떻게 다룰까요? 사내 모델 서버가 그런 이름의 모델을 제공할 때에만 발생합니다."

   > 사용자: 알려진 한계로 적어 둔다 (Recommended)

   그 선택지의 설명: "런타임은 아무것도 막지 않고 수정하지도 않습니다. ADR 0057의 이력에 이 동작을 기재하고 배포 기능의 계획에도 넘겨 두어서, 나중에 작성될 배포 안내 문서가 이 동작을 설명하게 합니다. 코드가 라이브러리의 내부 구현에 의존하지 않습니다." 고르지 않은 안은 둘이었다. 어댑터가 라이브러리의 내부 메서드를 재정의해 되돌리는 것과, 그런 이름의 모델 파일을 읽는 단계에서 거부하는 것이다.

둘 다 초안 그대로 승인됐다. 이력에는 사용자가 승인했다는 말과 이 절의 자리만 첫 문장에 덧붙였고, 명세 서두의 "승인을 받는다"를 "받았다"로 고쳤다.

## 인계 뒤의 open-session (위 세션이 적었다)

첫 열기는 새 세션 화면을 열고 폴더(`C:\project\agent`)를 맞춘 뒤 "5초 안에 모델 메뉴의 'Fable 5.1' 을(를) 찾지 못했다."로 멈췄다(`restore=필요`, 원래 값은 Opus 5.5 / xhigh). 지시문은 보내지 않은 채 화면에 남았다. 사용자가 "다시 시도해줘"라고 했다. 다시 열기 전에 이 세션 트랜스크립트에서, 사용자가 이 세션을 Fable 5.2에서 Opus 5.5로 바꾸기 직전의 응답이 429(`model_requires_usage_credits`, `seven_day_overage_included`, 기업 단위로 초과 사용이 꺼져 있다)였던 것을 찾았다. 그래서 Fable 5.2로 고쳐도 새 세션의 첫 턴이 같은 429로 멈춘다고 보고, 모델 줄만 `모델: Opus 5.5 / xhigh`로 고친 지시문을 새 파일로 다시 쐈다(같은 파일로 두 번 돌리지 않는다는 open-session 규칙 때문이다). 그 밖의 줄은 위 지시문과 같다. `list_sessions`에 이 브랜치를 제목으로 한 다른 세션이 없는 것을 보고 쐈다. 2의 잇는 지시문 값(Fable 5.1)이 앱의 모델 메뉴와 어긋나는 것은 회고 후보로 넘긴다. 이 세션도 같은 값의 지시문으로 열렸는데 Fable 5.2로 돌았다(일지 머리 줄). 그때 연 쪽이 어떻게 그 값을 골랐는지는 보지 않았다.

## 이어받은 세션의 인계 (커밋 뒤, 2026-11-12 19:38)

"이어받은 세션" 절을 쓴 세션이 적는다. 승인 뒤 커밋했다. 커밋은 `cfa62b318`(파일 22개)이고 pre-commit이 787초 걸려 Bash의 600초 제한을 넘겨 백그라운드로 넘어갔다가 종료 코드 0으로 끝났다. 그 출력에서 ruff 둘, check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest(613.5초), web-verify(786.9초), 마크다운 표, 줄 구분 문자, 변이 표, 커밋 메시지 검사가 Passed였고 canary specs와 constitution version은 대상 파일이 없어 Skipped였다(손으로 봤다, 그 출력을 Read로). 커밋 전에 따로 친 `uv run ruff check .`, `uv run ruff format --check .`, `tools/check_adr_pointers.py`, `tools/check_md_tables.py`, `tools/check_line_separators.py`, `tools/plan_table.py --check`도 걸린 것이 없었고, `git branch --show-current`는 `docs/local-model-spec`, `tools/sibling_overlap.py`는 번호 겹침과 함께 고친 파일이 없다고 냈다.

**인용 대조의 경고(막지 않는 검사).** 명세 83행의 ADR 0057 인용 "쿼리에 비밀을 적는 것은 막지 않는다"가 ADR에 글자 그대로 없다는 한 건을 커밋 뒤에 고쳤다. ADR 0057 22행의 글자 "주소의 쿼리 문자열에 비밀을 적는 것은 막지 않고"로 바꿨고 이 변경은 커밋하지 않았다. 이 일지의 인용 31건도 저장소에 글자 그대로 없다고 나왔다. 선택 화면의 질문과 설명, 바깥 문서의 문장, 리뷰 보고가 든 고치기 전의 문장, 프로브의 출력, 가운데를 줄인 명세 인용이라고 갈래로만 봤고 하나씩 원문과 대 보지는 않았다.

**인계의 계기.** 커밋 명령이 백그라운드로 넘어간 직후 훅(`hook_handoff`)이 세션 컨텍스트 205,073 토큰으로 인계 계기(`커밋 뒤`)를 냈다. 커밋이 끝나기를 기다려 성공을 본 뒤에 `handoff.md`를 따랐다. 인계하지 않는 때 다섯에는 들지 않았다. 커밋이 성공했고, 요청 범위가 PR과 병합까지이고, 이 세션을 연 지시문의 이어받을 상태는 `인계: 셀프 리뷰 직전`이라 같은 경계가 아니고, 이 세션이 쓴 인계 실패 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다. 넘기기 전 이 세션의 제목은 `docs/local-model-spec`이다. 이 브랜치에 열린 PR은 없다(`gh pr view docs/local-model-spec --json state`가 no pull requests found를 냈다).

낸 지시문:

```text
다음 작업: 기능 local-model. ADR 0057·0058 설계를 바탕으로 명세 작성
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec
브랜치: docs/local-model-spec
모델: Fable 5.2 / xhigh. 2의 잇는 지시문. 그 값 Fable 5.1은 앱의 모델 메뉴에 없어(일지 "인계 뒤의 open-session") 이 세션을 연 지시문의 값을 적는다
읽을 것: docs/journal/2026-11-12-0248-local-model-spec.md 전체(앞의 두 세션이 쓰다 넘긴 일지. 새 세션이 이어 쓰고 커밋한다)
이어받을 상태: 인계: 커밋 뒤. 일지는 docs/journal/2026-11-12-0248-local-model-spec.md. 셀프 리뷰 두 축의 반영, 명세 서두의 수 다섯 세기(26·3·25·2·32), ADR 0057 이력 둘의 사용자 승인까지 마치고 커밋 하나로 묶었다. 푸시하지 않았고 PR도 없다. 그 커밋 뒤에 고친 둘이 커밋하지 않은 변경으로 남아 있다. 일지의 마지막 절 "이어받은 세션의 인계 (커밋 뒤)"와, pre-commit의 인용 대조가 경고한 명세 "매니페스트" 절의 ADR 0057 인용 한 자리다. 남은 단계는 PR 직전 리뷰(일지 "리뷰 반영"의 "고치며 새로 쓴 사실 문장" 열둘을 bug-perf-review 브리프의 밀 주장으로 넘긴다), 푸시와 PR(base는 dev), 봇 회차 반영, 병합, 일지 "다음"과 회고다. 본문을 고치는 반영마다 명세 서두의 수를 다시 세고, 승인받은 ADR 0057 이력 둘의 결정을 바꾸는 반영은 사용자에게 다시 묻는다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

모델 줄은 `directive.md` 2의 잇는 지시문(명세면 Fable 5.1 / xhigh)을 글자 그대로 따르지 않았다. 그 이름이 앱의 모델 메뉴에 없어 앞 세션의 첫 열기가 멈췄고(위 절), 이 세션은 `Fable 5.2 / xhigh.`로 적힌 지시문으로 열려 그 모델로 돌았다(`get_session`의 `self`가 `claude-fable-5-2`와 `xhigh`를 보였다). `directive.md`의 그 값을 고치는 것은 회고 후보로 넘긴다(위 절이 이미 넘겼다).

제목을 `docs/local-model-spec (인계함)`으로 바꿨다. 이 세션이 띄운 백그라운드 작업은 남아 있지 않았다(커밋 명령 하나가 백그라운드로 넘어갔다가 끝났다). `git worktree unlock C:/project/agent/.claude/worktrees/local-model-spec`은 `is not locked`로 끝나 넘어갔다.

open-session을 부른다 2026-11-12T10:39:11Z

## 셋째 세션 (2026-11-12 19:47)

위 "이어받은 세션의 인계 (커밋 뒤)"의 지시문을 받은 새 세션이 이 절부터 쓴다. 모델은 Fable 5.2 / xhigh다. 세션 제목을 `docs/local-model-spec`으로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다. `ListAgents`에서 이 브랜치의 이름을 쓰는 다른 세션은 넘긴 세션 `docs/local-model-spec (인계함)` 하나였고, `list_sessions`에서 그 세션은 `isRunning`이 false였다(손으로 봤다). 제목이 이 브랜치인 도는 세션은 없었다.

> 사용자: `.claude/skills/to-spec/SKILL.md` 를 읽어 그대로 따른다. (…) 인자: 다음 작업: 기능 local-model. ADR 0057·0058 설계를 바탕으로 명세 작성 (…) 이어받을 상태: 인계: 커밋 뒤. (…) 이번 요청 범위: PR과 병합까지

지시문의 나머지 줄은 위 절의 "낸 지시문"과 같다.

### 시작할 때 본 것

`git fetch origin` 뒤 `git rev-parse origin/dev`는 `fba36f78a`로 이 브랜치의 기준과 같았다. 워크트리에는 커밋 `cfa62b318` 위에 커밋하지 않은 변경 둘(명세 83행의 ADR 0057 인용, 이 일지의 위 절)이 있었다. `tools/sibling_overlap.py`는 "이 브랜치의 새 번호 없음", "번호 겹침 없음", "함께 고친 파일 없음"이었고, `tools/check_adr_pointers.py`와 `tools/plan_table.py --check`는 출력 없이 끝났다. 명세의 `거부한 안:` 표시는 33건이고 서두 자신의 언급 하나를 빼면 서두의 서른둘과 같았다(손으로 봤다, Grep).

### 프로브를 새 환경에서 다시 돌렸다

앞 세션의 환경은 그 세션의 스크래치패드에 있어 넘겨받지 못했다. README의 "돌리는 법"대로 이 세션의 스크래치패드에 환경을 새로 만들었다. `make_env.py`의 출력은 설치 61개, 새 패키지 넷(`langchain-openai` 1.6.2, `openai` 3.49.0, `regex` 2026.11.9, `tiktoken` 0.14.0), 락과 달라진 판 없음이었다(쟀다, `.scratch/local-model/probes/make_env.py`). `openai_compat.py` 전체는 측정 108회차, 측정 아님 0회차였다(쟀다, `.scratch/local-model/probes/openai_compat.py`. 커밋 `cfa62b318`의 판이다). 환경과 출력 파일은 스크래치패드에 있고 커밋하지 않는다.

### PR 직전 리뷰

`coderabbit auth status`는 `Plan: Free`, `Seat: not assigned`였다(손으로 봤다). 리뷰 파이프라인 2대로 `coderabbit-review` 서브에이전트를 띄웠고, 기준 브랜치가 dev로 바뀐 뒤라 브리프에 `--base origin/dev`를 붙이라고 적었다. 앞 세션이 넘긴 "고치며 새로 쓴 사실 문장" 열둘은 CLI에 넘길 길이 없어(`code-review` 6단계) `bug-perf-review` 서브에이전트를 함께 띄워 밀 주장으로 넘겼다. 커밋하지 않은 변경인 명세 83행의 인용을 열셋째로 더했다. 그 브리프에 위 환경의 인터프리터 경로와 108 사례 실행의 출력 파일 경로를 줬다.

**`coderabbit-review`의 보고(받은 그대로 줄였다).** CLI 0.7.5, `Plan: Free`, `Seat: not assigned`. `coderabbit review --agent --include-untracked --base origin/dev`가 약 8분 뒤 종료 코드 0과 `review_completed`로 끝났고 파일 22개를 봤다고 보고했다. 지적 13건, 서브에이전트의 트리아지는 유효 5, 유효이나 이미 적힌 한계 1(두 자리), 보류 6, 오탐 0이다.

- Major `cases_request.py:269`·`329`(보류). `env_key_used_when_omitted`와 `env_gateway_used_when_omitted`가 실제 Authorization 값을 보지 않는다.
- Major `cases_logs.py:70`(유효). `query=True` 사례가 쿼리가 요청 경로에 실렸는지 보지 않는다.
- Minor `cases_logs.py:70-73`(유효). `logs_401_*`가 401을, 성공 사례가 호출 결과를 표지로 보지 않는다.
- Major `cases_response.py:46`(보류). `_read_the_reply`가 `openai.OpenAIError` 전체를 제외해, 응답 본문을 읽다 난 그 계열의 예외까지 측정 밖으로 뺀다.
- Critical(서브에이전트는 Minor로 봤다) `adapter_candidate.py:88-89`, 명세 153행(유효, 이미 적힌 한계). `masked`가 지금 환경의 키 값만 가려, 요청 뒤 변수가 바뀌면 되울린 옛 키가 문구에 남는다.
- Critical 명세 178행(보류). 응답 헤더 값이 DEBUG 로그에 찍힌다고 적으면서, 서버가 키를 응답 헤더로 되울리는 갈래가 수락 시험에 없다.
- Major `make_env.py:72`(유효). 인자로 저장소 루트를 주면 저장소의 `.venv`에 설치한다.
- Minor `outside_worktree.py:55`(유효). 체크아웃이 홈 아래에 있으면 `outside`가 거짓이 된다.
- Minor `cases_failure.py:113`(보류). 가짜 서버가 응답을 보내지 못해도 측정으로 센다.
- Minor `cases_guard.py:510`(보류). 요청이 닿은 뒤 기한 전에 다른 오류가 나도 측정으로 센다.
- Minor `cases_guard.py:334`(보류). 잘못된 키 값의 거부와 "환경 변수 없음"의 거부를 가르지 않는다.
- Minor 명세 238행(유효). 걸음 4가 죽은 잠금 아래 자원을 지운 뒤 걸음 5에서 `--yes` 없이 끝나는 길이 종료 코드 0~4 어디에도 맞지 않는다.

**`bug-perf-review`의 보고(받은 그대로 줄였다).** 기준 `fba36f78a`, 범위 22개 파일, 도구 호출 26번이라고 보고했다(작업 알림의 `tool_uses`는 41이었다). 밀 주장 열셋 가운데 열하나는 근거와 맞았다고 했고 둘을 지적으로 냈다. Minor 2, 오탐 2다.

- Minor 명세 238행(밀 주장 10, 유효). "4는 걸음 1·3·5에서 아무것도 띄우지도 지우지도 않고 끝난 때에만 낸다"가 걸음 4·5와 맞지 않는다. 죽은 잠금이 남은 채 `--yes` 없이 치면 걸음 4가 지우고 걸음 5에서 끝나, 0~4 어디에도 맞지 않는다(CodeRabbit의 마지막 지적과 같다). 같은 대목의 빈칸 둘도 짚었다. Ctrl-C로 끊긴 회차와, 걸음 9의 시험이 시간 제한에 걸린 회차의 종료 코드가 없다.
- Minor 명세 132행(밀 주장 6, 유효). 넷째 호출이 끝난 시점에 연결 4개가 닫혀 있었다는 고치기 전의 문장은 측정보다 세다. `calls_on_one_model`은 호출 넷 뒤 1초(`SETTLE_SECONDS`)를 기다리고 읽는다. 결론("포트에 닫기를 두지 않는다")은 놓은 뒤의 값과 대조 갈래가 받친다고 봤다.
- 근거와 맞았다고 본 밀 주장: 1(`build_rejects_address`의 출력), 2(`channel/cli/main.py`가 `PluginError`를 받아 진단만 적는다), 3, 4(`_address`의 `isprintable` 판정과 `guard_candidate_odd_url_401`의 출력), 5, 7(`core/loop.py`와 `core/run.py`), 8(`tests/test_main.py`의 단언과 두 차이), 9(`model_name_quirks`의 출력), 11(`.scratch/answer-eval/plan.md`의 `**Blocked by:**`와 본문. pilot-release 쪽 기능 계획은 열지 않았다고 했다), 12(`.github/workflows/ci.yml`의 `ubuntu-24.04`), 13(ADR 0057 22행에 글자 그대로 있다).
- 프로브 표지. `candidate_connections_after_failures`의 `status_500` 갈래에는 재시도가 실제로 들었다는 표지가 없다(`requests >= 3`만 본다. 이번 출력은 9건이다). `_read_the_reply`가 `OpenAIError`를 모두 빼는 것은 CodeRabbit이 올린 것과 같아 새 지적으로 세지 않았다.
- 오탐 둘. `outside_worktree.py`의 음성 대조가 둘째 실행 안에 없다는 것(명세가 두 실행으로 갈라 적었다), 명세의 "CI의 리눅스 러너에서도 돈다"(시험이 들어오면 돈다는 서술이다).
- 따라가지 못했다고 적은 파일: `cases_request.py`, `cases_logs.py`, `cases_failure.py`, `cases_key.py`, `fake_server.py`, `support.py`, `make_env.py`, `versions.py`, 프로브 `README.md`, `.scratch/deploy-package/plan.md`, 명세의 나머지 줄.

CLI가 `review_completed`로 끝났으므로 대체 리뷰(`/security-review`)는 돌리지 않았다.

**판정과 반영 (2026-11-12 20:09까지).** 판정은 근거를 먼저 본 뒤에 냈다. CodeRabbit CLI의 지적 13건(위 목록의 열두 줄이고 첫 줄이 두 자리다) 가운데 하나를 오탐으로 보고 남겼고 열둘을 고쳤다. `bug-perf-review`의 Minor 둘과 표지 하나도 고쳤다. 서브에이전트가 "보류"로 둔 여섯은 그 코드를 읽어 다시 판정했다.

- `cases_request.py:269`(`env_key_used_when_omitted`). 오탐으로 봤다. 결과 갈래가 서버가 받은 인증 헤더를 심은 키와 견줘 "환경의 키가 갔다"와 "다른 값이 갔다"로 이미 가른다(그 함수를 읽었다). 고치지 않았다.
- `cases_request.py:329`(`env_gateway_used_when_omitted`). 맞다. 결과 갈래가 주소만 실었고 간 키는 `data`에만 있었다. 간 인증 헤더가 게이트웨이 키인지를 결과에 싣게 고쳤다.
- `cases_logs.py:70`과 `70-73`. 맞다. 측정 여부의 조건에 둘을 더했다. 호출이 고른 갈래대로 끝났다(성공 갈래는 메시지가 돌아왔고, 상태 코드 갈래는 예외의 글이 그 코드를 든다). 쿼리 갈래는 서버가 받은 요청 줄에 그 쿼리가 있다.
- `cases_response.py:46`(`_read_the_reply`). 맞다. `openai` 계열의 예외 전체를 빼던 것을 전송·상태의 실패 둘(`openai.APIConnectionError`, `openai.APIStatusError`)만 빼게 고쳤다. 앞 세션의 셀프 리뷰가 좁힌 표지가 재려는 상황(응답 본문을 읽다 나는 그 계열의 예외)까지 측정 밖으로 뺐다.
- `adapter_candidate.py:88-89`와 명세 "실패 문구와 되울린 키". 맞다. CLI는 Critical로, 서브에이전트는 이미 적힌 한계로 봤다. 명세가 한계로 적은 것은 "서버가 값을 바꿔 되울린다"였고 "호출 도중에 환경의 값이 바뀐다"는 아니어서 새 틈으로 봤다. 후보와 명세를 두 값을 찾아 가리게 고쳤다(호출을 시작하며 읽어 둔 값과 예외를 바꾸는 때의 환경 값). 앞의 안은 "거부한 안"으로 남겼다. ADR 0057 결정 "되울린 키"의 "환경에서 읽은 값을 글자 그대로 찾아 가린다"는 그대로 참이라 이력을 쓰지 않았고 사용자에게 묻지 않았다. 프로브 사례는 더하지 않았다. 요청을 받은 뒤 환경의 키 값을 바꾸고 받은 키를 되울리는 가짜 모델 서버의 사례를 D의 어댑터 시험에 뒀고(명세 "사례"의 실패), 명세와 README에 이 갈래를 재지 않았다고 적었다.
- 명세 "로그"의 응답 헤더. 맞다. 다만 고칠 것은 수락 시험이 아니라 한계의 기록이라고 봤다. 응답 헤더의 값이 DEBUG 로그에 찍히는 것은 라이브러리(`httpcore2`)의 동작이고, 막는 장치를 두지 않기로 한 명세에서 "헤더로 되울린 키가 로그에 없다"는 통과할 수 없는 시험이 된다. 받아들인 한계로 적고 배포 안내에 넘겼다(명세 "다른 기능에 넘기는 것"의 deploy-package가 다섯에서 여섯이 됐고 `.scratch/deploy-package/plan.md`에 여섯째를 적었다). 그런 서버로 재지는 않았다. ADR 0057 Consequences "로그"가 수락에 건 문장은 그대로이고 그 시험의 가짜 모델 서버는 키를 본문으로 되울린다. 로그 필터를 두는 안의 거부 이유에는 응답 헤더의 값 가운데 어느 것이 비밀인지 어댑터가 알지 못한다는 것을 더했다.
- `make_env.py:72`. 맞다. 인자가 이 저장소 안이거나 `pyproject.toml`이 있는 디렉터리면 아무것도 깔지 않고 2로 끝나게 고쳤다. 가드를 다시 읽은 뒤 워크트리 루트 `.`과 주 체크아웃의 루트를 넣었고 둘 다 거부 문구와 종료 코드 2로 끝났다(손으로 봤다, `uv run python .scratch/local-model/probes/make_env.py .`과 같은 명령에 주 체크아웃의 경로).
- `outside_worktree.py:55`. 맞다. "작업 폴더 밖"의 판정에서 "작업 폴더가 홈 아래에 있지 않다"는 조건을 뺐다. 체크아웃이 홈 아래에 있으면 밖에 쓰고도 거짓이었다. 이 PC의 체크아웃은 홈 밖이라 결과는 그대로다.
- `cases_failure.py:113`(`_odd_body`), `cases_guard.py:334`(`_candidate_bad_key`와 `guard_candidate_missing_key`), `cases_guard.py:510`(`guard_candidate_cancelled`). 맞다. 표지를 좁혔다. 요청이 정확히 한 건이다, 예외의 글이 변수 이름만이 아니라 그 거부의 문구를 든다, 기한이 실제로 호출을 끊으려 했다(`cancel_called`).
- `candidate_connections_after_failures`의 `status_500` 갈래(`bug-perf-review`). 맞다. 서버가 받은 요청이 호출 수보다 많다는 조건(재시도가 들었다)을 측정 여부에 더했다.
- 명세 "HTTP 클라이언트"의 "넷째 호출이 끝난 시점"(`bug-perf-review`). 맞다. "넷째 호출이 끝나고 1초를 기다린 시점"으로 고치고, 두 사례의 셈이 호출 뒤 1초 이상을 기다린 값이며 호출이 끝난 그 순간의 값은 재지 않았다고 적었다. README의 같은 문장도 고쳤다.
- 명세의 종료 코드 문단(두 리뷰가 같은 자리를 짚었다). 맞다. 넷을 정했다. 첫째, 4는 띄우기를 시작하기 전에 끝난 때다. 걸음 4가 앞 세션이 남긴 것을 지운 뒤 걸음 5에서 `--yes` 없이 끝난 때도 4이고 지운 것은 출력에 남긴다. 둘째, 걸음 9의 시험이 시간 제한에 걸리면 실패한 시험으로 보고 걸음 10의 확인을 거쳐 1이나 2다. 셋째, Ctrl-C로 끊긴 회차는 띄우기를 시작한 뒤면 지운 뒤 2이고(지우지 못하면 3) 그 전이면 4다. 넷째, 무효 회차가 둘에서 셋이 됐다(띄운 뒤 시험이 판정을 내기 전에 끊긴 회차). 걸음 4의 지우기를 `--yes` 뒤로 미루는 안은 거부했다(확인을 기다리는 동안 남은 서버의 요금이 나간다). C 묶음의 시험이 보는 것에 그 가름을 더했다. ADR 0058이 명세로 넘긴 자리(남은 서버를 먼저 지우는지, 서버 쪽 사정의 회차를 실패로 셀지)를 채운 것이라 ADR 본문은 그대로다.

**다시 잰 것.** 고친 뒤 `openai_compat.py` 전체는 측정 108회차, 측정 아님 0회차였다(쟀다, `.scratch/local-model/probes/openai_compat.py`). 고치기 전의 실행(위 "프로브를 새 환경에서 다시 돌렸다")과 견주면 108 사례 가운데 결과 갈래가 달라진 것은 `env_gateway_used_when_omitted` 하나였다(스크래치패드의 견줌 스크립트로 손으로 봤다). `outside_worktree.py`의 두 명령은 명령마다 측정 2회차, 측정 아님 0회차였고 결과는 앞 세션과 같았다(쟀다, `.scratch/local-model/probes/outside_worktree.py`. 첫째는 "env-file 없이 환경에 ANTHROPIC_API_KEY: 없다", 둘째는 "환경에 ANTHROPIC_API_KEY: 있다"와 "환경에 RUNPOD_API_KEY: 없다"). 그 뒤 후보의 `masked` 독스트링 한 문장("두 번 넘게 바뀌면 놓친다"를 "두 번 이상 바뀌면 놓칠 수 있다"로. 두 번 바뀌어도 가운데 값이 생긴다)을 고쳤고, 그 판으로 `check_adapter_types.py`를 다시 돌려 측정 5회차, 측정 아님 0회차, 후보의 진단 0개와 타입 우회 0개를 봤다(쟀다, `.scratch/local-model/probes/check_adapter_types.py`). `openai_compat.py` 전체는 그 독스트링을 고친 뒤 다시 돌리지 않았다.

**고치며 새로 쓴 사실 문장(PR 봇이 겨냥할 자리).** 명세의 원문이다.

1. "모델 하나를 놓지 않고 네 번 불렀을 때도 넷째 호출이 끝나고 1초를 기다린 시점(모델을 아직 쥐고 있을 때)에 연결 4개가 모두 닫혀 있었다"
2. "찾는 값은 둘이다. 감싼 메서드가 라이브러리를 부르기 전에 먼저 읽어 둔 값(위 "키")과, 예외를 바꾸는 때의 환경 값이다"
3. "도중에 한 번 바뀌면 보낸 값은 그 둘 가운데 하나이고, 한 호출 안에서 두 번 이상 바뀌면 가운데 값을 놓칠 수 있다. 이 갈래는 프로브로 재지 않았다."
4. "`httpcore2`의 DEBUG 줄이 응답 헤더의 값을 찍으므로(위 첫 항목), 모델 서버나 그 앞의 게이트웨이가 응답 헤더에 비밀을 실으면 그 값이 DEBUG 로그에 남는다."
5. "4는 띄우기를 시작하기 전에 끝난 때에만 낸다. 걸음 1·3·5에서 끝난 때와 걸음 7 전에 Ctrl-C로 끊긴 때다."와 그 뒤의 시간 제한과 Ctrl-C의 문장들
6. "무효 회차는 셋이다."

**서두의 수 다섯(본문의 표시로 다시 셌다).** 넘겨받은 것 26(그대로), 사용자가 고른 것 3(그대로), 명세가 정한 것 25(그대로. 고친 것은 모두 이미 센 자리 안이다. 실패 문구의 모양과 감싸는 자리, 로그 시험의 모양, 걸음, 무효 회차), 이력 2(그대로), 거부한 안 32에서 34(예외를 바꾸는 때의 환경 값만 가린다, 걸음 4의 지우기를 `--yes` 뒤로 미룬다. Grep `거부한 안:`이 35건이고 서두 자신의 언급 하나를 뺀다). `uv run python tools/plan_table.py`는 `.scratch/plan.md`를 바꾸지 않았다.

### 커밋과 PR (2026-11-12 20:28까지)

리뷰 반영을 커밋 하나로 묶었다. 커밋은 `0c26ca6e3`(파일 13개)이고 pre-commit이 746초 걸려 백그라운드로 돌렸으며 종료 코드 0으로 끝났다. 그 출력에서 ruff 둘, check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest(591.6초), web-verify(745.9초), 마크다운 표, 줄 구분 문자, 변이 표, 커밋 메시지 검사가 Passed였고 canary specs와 constitution version은 대상 파일이 없어 Skipped였다(손으로 봤다, 그 출력을 Read로). 커밋 전에 따로 친 `uv run ruff check .`, `uv run ruff format --check .`, `tools/check_adr_pointers.py`, `tools/check_md_tables.py`, `tools/check_line_separators.py`, `tools/plan_table.py --check`도 걸린 것이 없었고, `git branch --show-current`는 `docs/local-model-spec`, `tools/sibling_overlap.py`는 번호 겹침과 함께 고친 파일이 없다고 냈다. `git fetch origin` 뒤의 `origin/dev`는 `fba36f78a` 그대로였다. 반영 커밋 앞에 `/code-review` 전체를 다시 돌리지는 않았다(그 스킬의 6단계가 고친 뒤에는 검증 명령만 다시 돌리라고 한다).

**인용 대조의 경고(막지 않는 검사).** 이 일지에서 세 건이 났다. 앞 세션이 고치기 전의 인용을 일부러 적어 둔 한 건(위 "이어받은 세션의 인계"의 인용 대조 문단)은 그대로 뒀다. 이 세션이 쓴 두 건은 따옴표를 뗐다. 리뷰 보고가 든 고치기 전의 명세 문장과, 명세의 문장을 줄여 옮긴 것이다. 이 고침은 커밋하지 않았다.

**커밋 뒤의 인계 계기.** 커밋 명령을 백그라운드로 띄운 직후 훅(`hook_handoff`)이 세션 컨텍스트 261,071 토큰으로 인계 계기(`커밋 뒤`)를 냈다. `handoff.md` 1의 셋째에 들어 넘기지 않았다. 이 세션을 연 지시문의 이어받을 상태가 `인계: 커밋 뒤`로 시작한다.

**푸시와 PR.** `git push -u origin docs/local-model-spec` 뒤 `gh pr create --base dev`로 PR 547을 열었다(`https://github.com/njh6803/agent-os/pull/547`). 제목은 첫 커밋의 제목이고 본문은 `.github/PULL_REQUEST_TEMPLATE.md`를 채웠다. 체크리스트의 PR 직전 리뷰 줄에 CLI와 `bug-perf-review`의 결과, 둔 지적 하나(`env_key_used_when_omitted`, 오탐)의 판정을 적었다. `gh pr view 547 --json headRefOid`의 값은 로컬 HEAD(`0c26ca6e3`)와 같았다. `@coderabbitai review` 코멘트는 남기지 않았다(아래 인계).

## 셋째 세션의 인계 (PR 연 뒤, 2026-11-12 20:28)

**인계의 계기.** PR을 연 명령 직후 훅(`hook_handoff`)이 세션 컨텍스트 304,647 토큰으로 인계 계기(`PR 연 뒤`)를 냈다. 함께 온 `hook_pr_next_session`의 계기보다 이것을 따랐다. 인계하지 않는 때 다섯에는 들지 않았다. PR이 열렸고, 요청 범위가 PR과 병합까지이고, 이 세션을 연 지시문의 이어받을 상태는 `인계: 커밋 뒤`라 같은 경계가 아니고, 이 세션이 쓴 인계 실패 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다. 넘기기 전 이 세션의 제목은 `docs/local-model-spec`이다.

낸 지시문:

```text
다음 작업: 기능 local-model. 명세 PR 547의 봇 회차를 반영하고 병합
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec
브랜치: docs/local-model-spec
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-12-0248-local-model-spec.md 전체(앞의 세 세션이 쓰다 넘긴 일지. 새 세션이 이어 쓰고 커밋한다)
이어받을 상태: 인계: PR 연 뒤. 일지는 docs/journal/2026-11-12-0248-local-model-spec.md. PR 직전 리뷰(CodeRabbit CLI와 bug-perf-review)의 반영을 둘째 커밋으로 묶어 푸시하고 PR 547(base는 dev)을 열었다. next-session merge.md 2(봇 회차)부터 한다. 첫 @coderabbitai review 코멘트도 새 세션이 남긴다. 커밋하지 않은 변경은 일지 하나다(절 "커밋과 PR"과 "셋째 세션의 인계", 인용의 따옴표 둘). 봇 회차의 커밋에 싣는다. 남은 단계는 봇 회차 반영, 일지 "다음"과 회고, 병합(merge.md "워크트리에서 병합할 때")이다. 봇이 겨냥할 자리는 일지 "고치며 새로 쓴 사실 문장(PR 봇이 겨냥할 자리)"의 여섯이고, PR 체크리스트에 둔 지적 하나(env_key_used_when_omitted, 오탐)의 판정은 일지 "판정과 반영"에 있다. 본문을 고치는 반영마다 명세 서두의 수 다섯(지금 26·3·25·2·34)을 다시 세고, 승인받은 ADR 0057 이력 둘의 결정을 바꾸는 반영은 사용자에게 다시 묻는다. 프로브를 다시 돌리려면 환경을 새로 만든다(프로브 README "돌리는 법". 앞 세션의 환경은 그 세션의 스크래치패드에 있다)
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

모델 줄은 `directive.md` 2의 잇는 지시문(`PR 반영·병합`이면 Sonnet 5.5 / high)을 그대로 따랐다. 이 세션은 막히지 않았다.

제목을 `docs/local-model-spec (인계함)`으로 바꿨다. 이 세션이 띄운 백그라운드 작업은 남아 있지 않았다(커밋 명령 하나와 리뷰 서브에이전트 둘이 모두 끝났다). `git worktree unlock C:/project/agent/.claude/worktrees/local-model-spec`은 `is not locked`로 끝나 넘어갔다.

open-session을 부른다 2026-11-12T11:29:00Z

## 넷째 세션 (2026-11-12 20:40)

위 "셋째 세션의 인계 (PR 연 뒤)"의 지시문을 받은 새 세션이 이 절부터 쓴다. 모델은 Sonnet 5.5 / high다(받은 지시문의 모델 줄 그대로). 세션 제목을 `docs/local-model-spec`으로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다.

> 사용자: `.claude/skills/to-spec/SKILL.md` 를 읽어 그대로 따른다. (…) 인자: 다음 작업: 기능 local-model. 명세 PR 547의 봇 회차를 반영하고 병합 (…) 이어받을 상태: 인계: PR 연 뒤. (…) 이번 요청 범위: PR과 병합까지

지시문의 나머지 줄은 위 "낸 지시문"과 같다. 첫 줄이 명세 스킬을 가리키지만 지시문의 다음 작업은 PR 반영·병합이라, 이 세션은 `to-spec`을 읽기만 하고(명세는 이미 썼다) `merge.md` 2(봇 회차)대로 했다.

### 봇 회차

PR 547의 머리는 `0c26ca6e3` 그대로였다(`gh pr view 547 --json headRefOid`). 첫 `@coderabbitai review` 코멘트를 남기고 `tools/wait_ci.py 547`을 백그라운드로 기다렸다. 결과는 CodeRabbit Finished, claude-review SUCCESS, 나머지 검사도 모두 SUCCESS(llm은 SKIPPED)였다. claude-review는 "지적 없음"이었다. CodeRabbit은 이 PR에 낸 첫 리뷰라 첫 회차이고, 지적 7건(Critical 1, Minor 6)을 지적마다 판단했다(Minor도 고칠지를 판단하는 회차다).

**판정과 반영.**

- `cases_guard.py` `guard_candidate_key_rotation`(Minor, 맞다). 지운 뒤의 세 번째 호출이 키를 계속 보내도 표지가 섰다. 표지를 요청이 정확히 2건이고 지운 뒤의 예외 글에 변수 이름과 키 없음 문구가 든 것으로 좁혔다.
- `cases_guard.py` `guard_candidate_success`(Minor, 맞다). 둘째 호출의 결과를 버렸다. 둘째 호출도 도구 호출 하나를 돌려받은 것을 표지에 더했다.
- `cases_lifetime.py` `_failing_runs`(Minor, 맞다). 예외가 났다는 것만 세어 연결이 끊긴 실패도 기대한 실패로 셌다. 갈래마다 예외 글에 들어야 할 원인(`(HTTP 401)`, `(HTTP 500)`, `(ValueError)`와 "Unexpected response type")을 정했고, 이 글은 갈래마다 예외를 한 번 찍어 보고 정했다(손으로 봤다, 스크래치패드의 한 번 쓴 스크립트). 봇이 함께 제안한 응답 전송 카운터(`FakeServer`에 두는 것)는 더하지 않았다. 상태 코드나 본문을 읽다 난 예외 글이 서버가 답을 보낸 뒤의 실패라는 표지를 이미 하기 때문이다.
- `check_adapter_types.py` `stray`(Minor, 맞다). 줄 번호만 비교해 같은 줄의 다른 규칙 진단을 버렸다. (줄, 규칙) 쌍 전체를 비교하게 고쳤다.
- `check_adapter_types.py` 환경 루트(Minor, 맞다). `make_env.py`와 같은 가드를 더했다. 인자로 워크트리 루트 `.`을 주니 거부 문구와 종료 코드 2로 끝났다(손으로 봤다).
- `make_env.py` 표지 파일(Minor, 맞다). 앞 세션의 가드는 저장소 안과 `pyproject.toml`이 있는 자리만 막았다. 이 프로브가 만들며 심은 표지 파일이 없는 `.venv`에는 얹지 않고 2로 끝나게 했다. 표지가 없는 앞 환경에 다시 치니 거부 문구와 2였고, 새 폴더에는 표지가 심기고 설치가 0으로 끝났다(손으로 봤다).
- `docs/journal`의 응답 헤더 DEBUG 로그(Critical 표시, 판정은 둔다). 아래 따로 적는다.

**다시 잰 것.** 환경은 앞 세션의 것을 넘겨받지 못해 이 세션의 스크래치패드에 `make_env.py`로 새로 만들었다(설치 61개, 새 패키지 넷, 락과 달라진 판 없음). 고친 뒤 `openai_compat.py` 전체는 측정 108회차, 측정 아님 0회차였고 세 사례의 결과 문구는 좁히기 전과 같았다(쟀다, `.scratch/local-model/probes/openai_compat.py`). `check_adapter_types.py`는 측정 5회차, 측정 아님 0회차이고 기대한 오류 8개가 모두 났고 기대 밖 진단은 없었다(쟀다, `.scratch/local-model/probes/check_adapter_types.py`). 좁힌 표지 셋과 두 프로브 가드는 프로브 README에 적었다.

**둔 Critical: 응답 헤더 값이 DEBUG 로그에 남는다.** 봇은 명세 스토리 18(루트 로거를 DEBUG로 켜도 키 값이 남지 않기를 바란다)과 어긋난다며, 어댑터가 `httpcore2`의 DEBUG 기록을 `mcp.py`처럼 필터로 버리고 수락 시험에 헤더 되울림 갈래를 넣으라고 했다. 앞 세션이 같은 지적을 CLI 리뷰에서 받아 이미 받아들인 한계로 판정했다(위 "셋째 세션"의 판정과 반영). 이번에 새로 확인한 것은 `adapters/mcp.py`를 읽은 것이다(읽었다). 그 필터는 `mcp.client.streamable_http`가 도구 호출의 인자를 DEBUG로 찍어 막을 것이 있었기 때문에 있고, 거기서는 헤더 값이 `mcp`·`httpx2`·`httpcore2`의 DEBUG에 실리지 않는다고 그 독스트링이 적는다. 여기서 `httpcore2`의 DEBUG를 통째로 버리면 응답 헤더와 함께 접속 단계의 기록도 사라진다(명세가 위 측정에서 적었다). 그래서 결정은 그대로 두고 명세 스토리 18에 한계를 덧붙이고(`받아들인 한계다(아래 "로그")`), 로그 절의 필터 거부 이유에 위 두 사실을 더했다. 새 `거부한 안:` 표시는 없고, 이 한계는 이미 deploy-package의 배포 안내로 넘어가 있다(명세 "다른 기능에 넘기는 것"). 이 판정은 사용자가 고른 것도 승인한 이력도 바꾸지 않는다. 사용자가 헤더 값까지 막기를 원하면 명세 "로그"의 결정 하나(필터를 둔다)를 바꾸는 일이라 그때 다시 묻는다.

**서두의 수 다섯(본문의 표시로 다시 셌다).** 넘겨받은 것 26, 사용자가 고른 것 3, 명세가 정한 것 25, 이력 2, 거부한 안 34. 그대로다. 고친 것은 이미 센 자리 안의 문장 둘이다(스토리 18의 덧붙임, 필터 거부 이유의 보강). Grep `거부한 안:`이 35건이고 서두 자신의 언급 하나를 뺀다(손으로 봤다, `grep -o`).

## 회고

후보 하나, 승인 하나(회차로 세는 것), 기각과 넘김 0이다. 승인한 것은 이 세션에서 반영하지 않고 대기열의 열린 항목에 회차만 더했다.

- **프로브 표지가 있었으나 재려는 상황을 다 보지 못했다(승인, 11회차).** 사건: 이 PR의 프로브에서 CodeRabbit이 Minor로 표지 셋을 짚었다. 키를 지운 뒤의 호출이 키 없음 거부로 끝났는지, 둘째 호출이 응답을 읽는 데까지 갔는지, 401·500·JSON 아님 갈래의 예외가 그 갈래의 원인인지를 보지 않았다. 셀프 리뷰 두 축과 PR 직전 리뷰(CLI와 `bug-perf-review`)가 같은 꼴을 이미 여럿 잡았는데도 이 셋이 남았다. `.claude/rules/probes.md` 첫 항목을 어긴 사건이고 그 규칙이 구현 때 실리는 규칙이라 회차로 센다. 간 자리: `.scratch/retro-queue/probe-round-marked-measured-unconditionally.md`에 11회차를 더했다(0430의 10회차). 층의 조건은 그 항목의 `어디로:`가 정했다. 그 처방(조건 없는 `mark(measured=True`를 짚는 계기 훅)은 이번 꼴, 곧 조건은 있으나 재려는 상황을 다 보지 못한 표지를 잡지 못하므로, 판단 기준을 가진 리뷰가 잡을 몫으로 남는다.
- 본 것 가운데 기각한 후보는 없고 새 사건도 없다. 만료할 항목은 `tools/queue_open_rows.py`와 `--ref origin/dev` 둘 모두 없음이었다.

## 다음

병합 뒤 단계는 기능 local-model의 티켓 나누기다(`next-session` 결정표의 "`spec.md`는 있고 `issues/`가 없다" 줄). 사용자만 부르는 `/to-tickets`로 가기 전에 명세 검토(`spec-reviewer` 서브에이전트)가 먼저다. 이 일지에는 그 검토가 돈 기록이 없다. 명세 서두의 수 다섯은 26·3·25·2·34이고, 티켓을 나눌 때 묶음 여덟(명세 "고칠 자리의 묶음")과 그 사이 막힘을 명세 그대로 따른다. 사용자에게 미리 물을 일은 없다. 다만 명세 "로그"의 응답 헤더 한계(받아들인 한계)를 사용자가 막는 쪽으로 바꾸자고 하면, 필터를 둘지 정하는 그 결정을 다시 묻는다.


## 넷째 세션의 인계 (커밋 뒤, 2026-11-12 21:10)

**인계의 계기.** 봇 회차의 반영을 커밋한 직후 훅(`hook_handoff`)이 세션 컨텍스트 311,545 토큰으로 인계 계기(`커밋 뒤`)를 냈다. 인계하지 않는 때 다섯에는 들지 않았다. 커밋 명령이 종료 코드 0으로 끝났고(pre-commit이 길어 백그라운드로 돌렸다), 요청 범위는 PR과 병합까지이고, 이 세션을 연 지시문의 이어받을 상태는 `인계: PR 연 뒤`라 같은 경계가 아니고, 이 세션이 쓴 인계 실패 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다. 넘기기 전 이 세션의 제목은 `docs/local-model-spec`이다.

커밋은 `b28b7cf57`(파일 8개)이다. 푸시하지 않았다. 앞 절 "넷째 세션"의 회고와 다음은 이 커밋에 이미 실려 있다. 커밋하지 않은 변경은 이 절 하나뿐이다.

낸 지시문:

```text
다음 작업: 기능 local-model. 명세 PR 547의 봇 회차 반영 커밋을 푸시하고 병합
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec
브랜치: docs/local-model-spec
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-12-0248-local-model-spec.md 전체(앞의 네 세션이 쓰다 넘긴 일지. 새 세션이 이어 쓰고 커밋한다). 병합 뒤 다음 단계는 일지 "다음"이다
이어받을 상태: 인계: 커밋 뒤. 일지는 docs/journal/2026-11-12-0248-local-model-spec.md. PR 547의 CodeRabbit 첫 회차(지적 7건)를 판정하고 반영한 커밋 b28b7cf57을 만들었고 푸시하지 않았다. 일지 "넷째 세션"에 판정, 다시 잰 것, 서두의 수(26·3·25·2·34, 그대로), 회고, 다음이 이미 있고 이 커밋에 실려 있다. 커밋하지 않은 변경은 일지 하나다(절 "넷째 세션의 인계"). 푸시한 뒤 merge.md 2(봇 회차)부터 한다. 푸시마다 대기를 새로 띄운다. 이 PR에는 `@coderabbitai review` 코멘트를 이미 남겼고 CodeRabbit은 시간당 포함 리뷰 한 번이라 이 푸시에는 한도로 리뷰가 없을 수 있다(그 판정은 operations.md 리뷰 파이프라인 3). 봇의 둘째 회차부터는 Critical·Major만 고치고 나머지는 보류 이유를 PR 코멘트에 남긴다. 첫 회차에서 응답 헤더 값이 DEBUG 로그에 남는다는 Critical은 받아들인 한계로 두었다(일지 "둔 Critical"). PR 코멘트로 이유를 남기지는 않았다. 이 커밋은 PR의 범위를 넓히지 않아 PR 본문은 그대로 둔다. 남은 단계는 푸시와 봇 회차, 병합(merge.md "워크트리에서 병합할 때"), 병합 뒤 next-session 2다. 병합 뒤 다음 작업은 일지 "다음"대로 명세 검토(spec-reviewer)와 티켓 나누기이고, 승인받은 ADR 0057 이력 둘의 결정을 바꾸는 반영은 사용자에게 다시 묻는다. 프로브를 다시 돌리려면 환경을 새로 만든다(프로브 README "돌리는 법". 앞 세션의 환경은 그 세션의 스크래치패드에 있다)
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

모델 줄은 `directive.md` 2의 잇는 지시문(`PR 반영·병합`이면 Sonnet 5.5 / high)을 따랐다. 이 세션은 막히지 않았다.

제목을 `docs/local-model-spec (인계함)`으로 바꿨다. 이 세션이 띄운 백그라운드 작업은 남아 있지 않았다(커밋 명령 하나가 끝났다). `git worktree unlock C:/project/agent/.claude/worktrees/local-model-spec`은 `is not locked`로 끝나 넘어갔다.

open-session을 부른다 2026-11-12T12:11:22Z

## 다섯째 세션 (2026-11-12 21:20)

위 "넷째 세션의 인계 (커밋 뒤)"의 지시문을 받은 새 세션이 이 절부터 쓴다. 모델은 Sonnet 5.5 / high다(받은 지시문의 모델 줄 그대로). 세션 제목을 `docs/local-model-spec`으로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다. 지시문의 첫 줄이 `to-spec`을 가리켜 그 스킬을 읽었으나, 다음 작업이 PR 반영·병합이라 `merge.md` 2(봇 회차)대로 했다.

> 사용자: `.claude/skills/to-spec/SKILL.md` 를 읽어 그대로 따른다. (…) 인자: 다음 작업: 기능 local-model. 명세 PR 547의 봇 회차 반영 커밋을 푸시하고 병합 (…) 이어받을 상태: 인계: 커밋 뒤. (…) 이번 요청 범위: PR과 병합까지

시작할 때 본 것: `git fetch origin` 뒤 `origin/dev`는 `fba36f78a` 그대로였고, 로컬 HEAD는 `b28b7cf57`(푸시하지 않은 커밋 하나), PR 547의 머리는 `0c26ca6e3`, `mergeStateStatus`는 `CLEAN`이었다(손으로 봤다). 커밋하지 않은 변경은 이 일지 하나였다.
