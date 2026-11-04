# 2026-11-04 (04) skill-plugin 02: 스킬 문서를 읽어 sdk 값으로 돌려주는 read_skill (구현 세션, 인계 전)

세션 제목은 `feature/02-read-skill-document-into-sdk-value`이다. 이 일지는 인계(`handoff.md`)로 쓴 앞 절이고, 이어받은 세션이 이어 쓰고 커밋한다. 회고(`retro`)는 단계를 닫는 마지막 세션이 이 일지까지 읽고 돈다.

## 사용자 프롬프트

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다.
> 인자: .scratch/skill-plugin/issues/02-read-skill-document-into-sdk-value.md
> 다음 단계: 구현 / 어디서: 새 세션. 나란히 여는 2 중 2. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 02-read-skill-document-into-sdk-value)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 시작 프롬프트: /implement .scratch/skill-plugin/issues/02-read-skill-document-into-sdk-value.md / 브랜치: feature/02-read-skill-document-into-sdk-value / 모델: Sonnet 5.5 / high / 읽을 것: ticket 01, journal 2026-11-04-02 '다음' / 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. tidy-checkouts는 묶음의 첫 세션이 돈다. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 '워크트리에서 병합할 때'를 Read로 열어 따른다 / 이번 요청 범위: PR과 병합까지

(원문은 줄바꿈이 있는 열 줄 지시문이었다. 위는 그 값을 옮긴 것이다.)

## 한 것

- 워크트리 `02-read-skill-document-into-sdk-value`에서 티켓 02를 구현했다. 커밋 `17cfa1bb`(로컬, 아직 푸시하지 않았다).
- sdk: `Skill`(frozen dataclass)과 `parse_skill`(`sdk/skill.py`), `AgentContext.skills`. 포트 `PluginSource.read_skill`과 파일시스템 어댑터 구현. core 컨텍스트는 빈 열을 든다. pyyaml 직접 의존성과 import-linter 계약("only the sdk reads YAML", `allow_indirect_imports = true`).
- 문서: `sdk.md` 스킬 줄, `core.md` 포트 표 13행, `adapters.md`의 `read_skill` 항목, `tech.md`, 헌법 판 3.0.65에서 3.0.66.
- 빨강을 본 것: import-linter 계약(어댑터에 `import yaml`을 넣어 BROKEN, 되돌림), core의 `ctx.skills == ()` 시험(`self.skills` 대입을 지워 `run_failed(agent_code)`로 빨강, 되돌림).
- 검증: `ruff check`, `ruff format --check`, `tools/run_checks.py`(체크 열 개 전부 통과), 커밋의 pre-commit 통과.

## 셀프 리뷰(`/code-review`) 반영

두 축이 같은 Major 하나를 짚었다.

- **고친 것 (Major).** `parse_skill` 독스트링과 `sdk.md`가 "문구는 머리말의 값을 되울리지 않는다"고 적었으나, 두 칸 거부(`ValidationError`)의 `str(error)`는 틀린 값을 `input_value`로 싣는다. 독스트링은 "가르기와 YAML 읽기의 문구는 값을 싣지 않고, 두 칸의 `ValidationError` 문구는 틀린 값을 싣는다. 내보내는 쪽은 `str(error)`를 쓰지 않고 입력 없이 다시 만든다(어댑터의 `_describe`가 그 예)"로, `sdk.md`도 같은 뜻으로 고쳤다. 새로 쓴 사실 문장이므로 PR 직전 리뷰에 밀 주장이다.
- 고친 것 (Minor): `filesystem.py` 모듈 독스트링과 `adapters.md`에 `read_skill`을 더했다. 약한 시험(`test_두_칸의_거부_문구는_ValueError_계열이다`)을 `ReaderError`가 줄·칸 없이 종류만 든다는 시험(`test_위치가_없는_YAML_오류는_종류만_든다`)으로 바꿨다.
- **남긴 것.** (1) `AgentContext.skills` 독스트링이 "이 에이전트가 쓰는"으로 적는 것은 계약이 약속하는 것을 말하라는 티켓의 요구라 그대로 둔다(틈은 `sdk.md`가 적는다). (2) `core/run.py`와 `tests/core/test_run.py`의 "다음 티켓이다" 주석은 지금 참이고 티켓 03이 고친다. (3) "머리말 안 `---` 줄 세 자리" 시험은 `yaml.safe_load`만 부른다(프로브도 같다). (4) `_parse_skill`과 `_parse`, `read_skill`과 `read_manifest`의 이름 대조가 같은 모양이다. 원인을 잇지 않는 차이가 티켓이 정한 의도라 합치지 않았다.
- 다시 돌린 명령: ruff 둘은 통과. 고친 뒤 `tests/sdk/test_skill.py`와 `tests/adapters/test_filesystem.py`는 통과. 전체 러너는 고치기 전 판으로 통과했고, 고친 뒤는 커밋의 pre-commit이 돌려 통과했다.

## PR 직전 리뷰 (CodeRabbit CLI)

- `coderabbit auth status`는 Plan Free, `Seat: not assigned`였다. 그래도 `coderabbit-review` 서브에이전트가 `coderabbit review --agent --include-untracked --base origin/main`을 돌려 `review_completed`, 지적 0건, 검토 24개 파일로 끝났다(서브에이전트 보고를 옮긴 것이다). 한도나 인증 거절은 없었다. 좌석이 없는 Free 플랜이라 분석이 얕을 수 있다는 단서가 보고에 붙었다.
- 서브에이전트가 보안 축을 코드로 직접 따라갔다고 보고했다. `read_skill`의 경로는 인자 이름으로만 조립되고, 예외 문구와 사슬은 머리말의 값을 싣지 않으며, YAML은 `safe_load`다. 서브에이전트가 `tests/sdk/test_skill.py`와 `tests/adapters/test_filesystem.py` 129개 통과, pyright와 lint-imports(6 kept)도 쳤다고 적었다. 비밀 값을 넣은 즉석 탐침은 못 돌렸다고 적었다.
- 판정: 고칠 것 없음. 남기는 관찰 둘은 티켓 03의 몫이다. (1) 어댑터의 `read_skill`은 `name`을 스스로 검증하지 않는다. `read_manifest`와 같은 규약이라 호출부(03)가 `is_plugin_name`으로 거른 값만 넘기는지 03이 본다. (2) 새 호출부가 `parse_skill`의 `ValidationError`에 `str(error)`를 쓰지 않는지도 03이 본다. 둘 다 받는 쪽인 `.scratch/skill-plugin/issues/03-runtime-prepares-skills-per-run.md`의 수용 기준 한 줄로 옮겼다.

## 근거의 종류

- 검사 통과(`ruff`, `run_checks.py`의 열 개, 커밋의 pre-commit)는 명령의 출력과 종료 코드 0으로 본 것이다(러너 출력은 스크래치의 `checks.txt`, 커밋은 백그라운드 명령의 종료 코드 0).
- 두 빨강은 손으로 본 것이다. `core/run.py`의 `self.skills` 대입을 지우고 `uv run pytest tests/core/test_run.py -k 스킬_멤버는`을 쳐 `AttributeError`가 `run_failed(agent_code)`로 바뀐 출력을 읽었다. import-linter 계약은 어댑터에 `import yaml`을 넣어 BROKEN을 본 것이다. 둘 다 되돌렸다.
- 셀프 리뷰의 지적(Major 하나, Minor 여섯)은 서브에이전트 둘의 보고를 옮긴 것이다. 두 칸 거부의 문구가 값을 싣는다는 것은 두 보고가 각자 `uv run python`으로 대 봤다고 적었고, `tests/sdk/test_skill.py`의 양성 대조 주석이 같은 사실을 적는다. 이 세션이 그 입력을 직접 부르지는 않았다.
- 카나리아 사전 확인은 `uv run python tools/canary.py --preflight`에 명세 여덟을 넣어 종료 코드 0을 본 것이다. 사전 확인은 원천이 실리는지 재지 않는다(그 도구의 독스트링).

## 확인하지 못한 것

- 카나리아: `uv run python tools/sibling_overlap.py`가 바뀐 규칙 파일(`adapters.md`, `core.md`, `sdk.md`)을 원천으로 든 명세 여덟을 새 `claude -p`로 돌리라고 알린다. 계정 한도 때문이 아니라 비용 판단으로 사전 확인(`--preflight`)만 돌렸고 여덟 모두 통과했다. 본 회차는 돌리지 않았다. 바꾼 줄은 그 명세들이 묻는 줄이 아니다. 그 알림이 남은 채 커밋했다.
- `sibling_overlap.py`의 종료 코드 1은 위 카나리아 알림이다. 번호 겹침은 없고 헌법 판은 3.0.66으로 올렸다.

## 인계

제목을 `feature/02-read-skill-document-into-sdk-value (인계함)`으로 바꿨고 워크트리 잠금을 풀었다. 실행 중이던 백그라운드 작업은 없었다.

open-session을 부른다 2026-11-04T14:03:23Z

인계 못함 커밋 뒤: `tools/open_session.ps1`(앱 창을 조작하는 스크립트)의 실행을 자동 모드 분류기가 설명 없이 거부했다(PowerShell 도구의 거부 메시지). 새 세션은 열리지 않았다. 제목을 `feature/02-read-skill-document-into-sdk-value`로 되돌렸고 이 세션이 푸시부터 잇는다. 워크트리 잠금은 풀린 채로 둔다.

## 남은 일

푸시, PR(`git-pr`), PR 본문에 위 "남긴 것"과 카나리아 사전 확인만 했다는 것, ccd_pr 바인딩, 봇 회차, 병합(이 워크트리 사본의 `merge.md` "워크트리에서 병합할 때"). 병합 전에 티켓 01이 먼저 병합되었는지 보고, 겹치는 파일(`.claude/rules/sdk.md`, `tests/test_server.py`, `tests/adapters/test_filesystem.py`)은 뒤에 병합되는 쪽이 합친다.
