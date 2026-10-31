# 2026-11-01 (02) 모델 매니페스트 계약 티켓 01 구현

세션 제목: `feature/01-contract-model-manifest-fields`. 인계 때 `feature/01-contract-model-manifest-fields (인계함)`으로 바꾼다. 컨텍스트가 인계 문턱을 넘은 `셀프 리뷰 직전`에 넘긴다. 이 일지는 새 세션이 이어 쓰고 커밋한다.

## 사용자 프롬프트 원문

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. … 인자: `.scratch/model-plugin/issues/01-contract-model-manifest-fields.md` … 다음 단계: 구현 … 나란히 여는 2 중 1 … 이번 요청 범위: PR과 병합까지

조작 지시(워크트리 진입, `tidy-checkouts`)는 따랐고 그 밖의 결정 질문은 없었다.

## 한 것(커밋하지 않은 작업 트리)

- sdk: `ModelProvider`(`StrEnum`, `anthropic` 하나)와 `PluginManifest`의 다섯 칸(`model`, `provider`, `model_id`, `max_tokens`, `temperature`), 종류별 거부 검증자. `sdk/__init__.py`에 `ModelProvider`를 낸다.
- 시험: `tests/sdk/test_manifest.py`에 모델 칸 받기·거부(오류 `type` 단언), 종류별 거부, 직렬화 스키마의 `required`·`null`·`ModelProvider` 정의, 보호 이름 공간 경고 없음(서브프로세스 `-W error`)을 더했다. `tests/adapters/test_filesystem.py`는 `_KIND_EXTRA`의 모델 칸을 채우고 모델 읽기와 옛 모델 파일(표지 행, `PluginError`) 시험을 더했다. `tests/test_server.py`는 `SONNET`을 모델 매니페스트로 고치고 `PICKY`(에이전트가 `model`을 적음)와 두 시험을 더했다. `tests/channel/http/test_router.py`는 `EXISTING_COMPONENTS`에 `ModelProvider`를 더했다.
- 계약: `openapi.json` 다시 뽑음, `web/packages/api-client/src/generated/openapi.ts` 다시 만듦.
- 관리 화면: 리터럴 여섯 파일에 다섯 칸을 더했다. 모델 리터럴(`HomePage.test.tsx`의 `sonnet`)은 `provider: "anthropic"`, `model_id: "claude-sonnet-5-5"`다. `PluginPage.test.tsx`의 JSON 문자열 정답에도 다섯 줄을 더했다. e2e 스택의 `models/sonnet`은 `provider`·`model_id`를 적는다.
- 사진 정답 여덟 장을 `pnpm -C web visual:admin:update`로 다시 만들었다. 바뀐 것은 `organisms-plugindetail--{enabled,disabled}-{1280,320}-{light,dark}.png` 여덟 장뿐이고, 다른 사진은 그대로다. 매니페스트 JSON에 `conversation_limit` 뒤로 다섯 줄(`model`, `provider`, `model_id`, `max_tokens`, `temperature`, 모두 `null`)이 늘어 상세가 길어졌다(1280 라이트 한 장을 눈으로 봤다). PR 본문에 적는다.
- 문서: `.claude/rules/sdk.md`의 두 문장(종류별 칸, 모델 한 줄)을 고쳤다. `manifest.py`의 `PluginKind` 위 주석에서 "model"을 뺐다(`skill`만 예약이다).
- 티켓 `01-contract-model-manifest-fields.md`는 체크박스를 모두 채우고 `Status: done`으로 바꿨다. 코드 리뷰가 끝나기 전의 값이라 리뷰가 고칠 것이 있으면 되돌린다.

## 검증(이 세션이 본 것)

- `uv run ruff check . && uv run ruff format --check .`, `uv run pyright`: 초록.
- `uv run python tools/run_checks.py`: check-ticket·zizmor·lint-imports·check-instructions·check-type-escapes·pyright·run-hooks·pytest·web-verify 모두 Passed(web-verify 518초, pytest 329초).
- 관리 화면 e2e(`pnpm -C web/apps/admin exec playwright test`): 9 passed.
- 사진 비교(`pnpm -C web visual:admin`): 정답을 다시 만든 뒤 초록. 다시 만들기 전에는 위 여덟 장만 빨갰다(예측과 같다).
- 첫 빨강: `pnpm -C web/apps/admin exec tsc --noEmit`이 열두 리터럴에서 `missing the following properties`로 빨갰고, sdk 시험은 `ImportError: cannot import name 'ModelProvider'`로 빨갰다.

## 남은 단계

셀프 리뷰, 카나리아, 커밋은 끝났다. 커밋 `f9ff889a`(`feat: 모델 매니페스트의 제공사·모델 id·파라미터와 에이전트의 model 칸을 계약에 더한다`)가 pre-commit을 모두 통과했다(출력을 읽었다: parallel-checks 441초 Passed, commit message Passed, constitution version은 헌법 파일을 안 고쳐 Skipped). 이 일지의 "셀프 리뷰"·"반영 뒤 검증" 절은 그 커밋에 들었고, 이 "남은 단계" 갱신만 커밋하지 않았다.

1. 이 일지의 갱신을 커밋에 얹는다(푸시 전이라 별도 커밋으로 한다).
2. 푸시하고 `/git-pr`로 PR을 연다. PR 본문에 사진 여덟 장(`organisms-plugindetail--{enabled,disabled}-{1280,320}-{light,dark}.png`, 매니페스트 JSON에 `conversation_limit` 뒤 다섯 줄이 늘어 상세가 길어졌다), 계약 영향(`openapi.json`·생성 타입·`schema_version` "1" 유지), 틈(런타임이 아직 모델 매니페스트를 읽지 않는다. 04가 닫는다)을 적는다. `Generated with` 줄도 넣는다.
3. 봇 회차와 병합은 `merge.md`를 Read로 열어 따른다. 병합은 이 워크트리에서 하므로 "워크트리에서 병합할 때"를 따른다. 티켓 02(`feature/02-manifest-errors-omit-input`, PR #445)가 `tests/adapters/test_filesystem.py`를 같이 고친다. 뒤에 병합되는 쪽이 앞의 것을 합친다.

## 셀프 리뷰(`/code-review origin/main`, base `bf6c1f26`, 미커밋 파일 26개·미추적 1개·커밋 0)

명세 축(Critical 없음, Major 1, Minor 3):

- Major: `GET /plugins`가 공통 넷만 적은 모델 파일을 그 행만 표지 행으로, 단건을 500으로 내는 시험이 HTTP 층에 없었다(어댑터 시험이 갈음). 고쳤다: `tests/test_server.py`에 `OLD_MODEL` 표지와 `test_공통_넷만_적은_모델_파일은_목록에서_그_행만_표지이고_단건으로는_500이다`를 더했다.
- Minor: `manifest.py`의 `model` 칸 주석("실행을 준비할 때 본다")과 모델 칸 주석("어댑터가 든다")이 04 전에는 거짓이다. 고쳤다: 계약이 약속하는 말("sdk가 보지 않는다", "sdk가 정하지 않는다")로 바꿨다. `sdk.md`의 "없으면 기본 모델이다"는 계약 문장이라 두었다.
- Minor: `ModelProvider` 독스트링 "값은 하나다"는 둘째 제공사에서 거짓이 되고 `openapi.json`에 박힌다. 고쳤다: "모델 플러그인의 제공사."로 줄이고 `openapi.json`과 생성 타입을 다시 만들었다(`PluginKind`의 "값은 넷이다"는 이 티켓 밖이라 두었다).
- Minor: 검증자 문구 "provider을"의 조사. 고쳤다: 기존 `conversation_limit 을`과 같이 공백을 두었고 시험의 `match`도 맞췄다.

표준 축(Critical·Major·문서화된 표준의 하드 위반 없음. 서브에이전트가 `parse_manifest`로 경계 입력을 손으로 대 본 결과다):

- Nit: 보호 이름 공간 시험의 독스트링이 `model`도 `model_` 접두에 걸린다고 썼다. 고쳤다: `model_id`만 걸릴 수 있고 `model`은 그 접두가 아니다.
- Nit: `model_id = "   "`(공백만)이 통과한다. 남겼다: 명세·프로브가 정한 경계는 "비지 않은 문자열"(`min_length=1`)이고 공백 걸러내기는 요구에 없다. 필요하면 04에서 모델을 만드는 쪽이 본다.
- Minor(판단): 에이전트 전용 칸 거부 연쇄가 네 번째로 늘었다(Repeated Switches). 남겼다: 이 티켓 밖의 정리이고 판단 항목이다.
- Nit(판단): 모델 네 칸의 이름이 `manifest.py`와 시험 두 곳에 따로 있다(Data Clumps). 남겼다. 시험이 sdk 상수를 읽으면 시험이 자기가 재는 코드와 같은 목록을 쓰게 된다.
- Nit: `sdk.md` 문단에 종류 `model`과 칸 `model`이 함께 나온다. 남겼다: 칸은 백틱과 "에이전트의 `model`"로 이미 구분했다.
- 오탐: README의 "skill과 model은 로더가 생길 때"(티켓 06 몫), `ModelProvider`의 닫힌 열거(ADR 0008·0040, 스토리 26).

## 반영 뒤 검증

- 카나리아: `uv run python tools/canary.py .scratch/end-user-continuation/probes/canary/sdk_rule_failure_cause.toml <출력>`과 `…/sdk_rule_shortcut_patterns.toml`을 이 워크트리에서 돌렸다(claude 2.1.312, 대조군은 둘 다 이 체크아웃의 커밋 `bf6c1f26`의 `README.md`). 둘 다 러너의 판정이 통과 4·실패 0·"없음" 섞임 0이다(러너 출력을 읽었다). 두 명세의 `# 최신 결과:` 줄을 갱신했다.
- 시험(반영 뒤 손으로 침): `tests/sdk/test_manifest.py`·`tests/adapters/test_filesystem.py`·`tests/channel/http/test_router.py` 238 passed, `tests/test_server.py -k "모델 or 표지 or openapi or 계약"` 22 passed. `ruff check`·`ruff format --check` 초록. 전체 러너는 pre-commit이 갈음한다.

## 인계(`커밋 뒤`)

컨텍스트가 인계 문턱을 두 번째로 넘은 `커밋 뒤`에 넘긴다. 이 세션의 제목은 `feature/01-contract-model-manifest-fields (인계함)`이다(바꾸기 전 제목은 `feature/01-contract-model-manifest-fields`). 이 세션의 사용자 프롬프트는 위 원문 그대로이고 결정 질문은 없었다. 이 세션이 번복한 것은 없고, 셀프 리뷰 지적은 위 절에 있다.

## 보류와 메모

- README의 "skill과 model은 로더가 생길 때" 문장은 티켓 06이 고친다. 이 티켓에서 걷지 않았다. 관리 화면 모델 행의 안내 줄도 06이다.
- 나란히 도는 티켓 02(`02-manifest-errors-omit-input`)도 `tests/adapters/test_filesystem.py`를 고친다. 뒤에 병합되는 쪽이 앞의 것을 합친다.
- 병합은 이 워크트리에서 하므로 `merge.md`의 "워크트리에서 병합할 때"를 따른다.

open-session을 부른다 2026-10-31T17:11:16Z
open-session을 부른다 2026-10-31T17:29:04Z
