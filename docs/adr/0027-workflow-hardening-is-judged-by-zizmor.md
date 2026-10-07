---
status: accepted
date: 2026-10-07
---

# 워크플로 하드닝은 zizmor가 판정하고, 판은 uv 개발 의존성이 고정한다

체크아웃의 `persist-credentials: false`는 `ci.yml` 머리 주석의 규약뿐이었다. PR #158이 새 `visual` 잡에서 빠뜨린 것은 CodeRabbit이 잡았고, `claude-code-review.yml`의 체크아웃은 그 뒤에도 기본값이어서 액션의 지우기가 checkout v7의 `includeIf`를 보지 못한 채 리뷰 내내 토큰이 남았다(일지 2026-10-07-11, 2026-10-07-14). 기계가 판정할 수 있는 규칙이 사람의 기억에 걸려 있었다(대기열 142, 2회차). **zizmor를 판정자로 둔다. uv의 dev 의존성으로 들여 `uv.lock`이 판(1.30.1)을 고정하고, pre-commit의 검사 러너와 CI의 `python` 잡이 같은 명령 `uv run zizmor --offline --strict-collection --config .github/zizmor.yml .`을 돈다.** 페르소나는 기본값(regular)이다.

**설정은 명시한다.** zizmor의 설정 자동 탐색은 위로 올라가며 `.git` 디렉터리를 찾고 그 자리의 설정을 읽는다. 워크트리의 `.git`은 파일이라, `.claude/worktrees/<이름>/`에서 돌린 zizmor가 바깥 주 체크아웃(`C:\project\agent`)을 루트로 잡고 그곳의 설정을 찾았다(`-v` 출력의 `root`, 손으로 봤다). 그대로 두면 워크트리의 설정 변경이 그 워크트리의 게이트에 걸리지 않는다. 그래서 `--config`로 가리킨다.

측정은 `.scratch/harness/probes/zizmor_gate.py`가 다시 낸다(zizmor 1.30.1, Windows 10).

**판정자가 잡는가.** 체크아웃 다섯(`ci.yml` 넷, `claude-code-review.yml` 하나)에서 `persist-credentials: false`를 하나씩 지운 사본마다 artipacked가 그 단계를 가리켰다(어긋남 0/5). 지우지 않은 사본은 종료 0이다. 등급은 checkout의 판을 따랐다. 체크아웃 하나만 둔 워크플로에서 v4·v5는 medium, v6·v7은 low였고, 같은 잡에서 체크아웃 전체(`path: .`)를 upload-artifact로 올리면 한 단계씩 올랐다(프로브의 severity). 그래서 v4인 `ci.yml`의 사본은 종료 13, v7인 `claude-code-review.yml`의 사본은 종료 12였다. 하위 디렉터리만 올리는 `visual` 잡도 13이었다. low 하나도 게이트를 빨갛게 하므로 `--min-severity`를 두지 않는다.

**`--strict-collection`.** zizmor는 기본값으로 YAML이 깨진 입력을 경고만 하고 건너뛴다. 깨진 파일과 멀쩡한 워크플로를 함께 둔 트리에서 이 옵션이 없으면 종료 0, 있으면 1이었다. 건너뛴 파일은 판정을 지난 것이 아니다. GitHub가 들인 새 문법을 zizmor의 스키마가 아직 모르면 이 옵션이 멀쩡한 워크플로를 막을 수 있고, 그때는 zizmor를 올리는 것이 먼저다.

**오프라인.** 온라인 감사(알려진 취약 액션, 저장소 밖의 커밋, 참조 혼동 등)는 GitHub 토큰과 네트워크를 쓴다. 토큰을 준 실행도 오프라인과 같은 26건(auditor)이었다(2026-10-07, 손으로 봤다). 온라인 결과는 코드가 그대로여도 바깥의 공지에 따라 바뀌고, 로컬에는 토큰이 없을 수 있어 두 자리의 판정이 갈린다. 그래서 둘 다 `--offline`이다.

**첫 실행과 `unpinned-uses`.** 도입 전 main(`61884df`)의 워크플로 둘과 `.pre-commit-config.yaml`에서 regular는 16건이고 모두 `unpinned-uses`(high)다. 1.30.1의 기본 정책은 모든 액션을 커밋 해시로 고정하라고 한다. artipacked는 0건이다(PR #162·#164가 이미 고쳤다). **GitHub의 `actions/` 조직 액션(`actions/*`)은 ref 고정을 허용하고 나머지는 해시로 고정한다.** 정책 이름은 `ref-pin`이고 태그만이 아니라 브랜치(`@main`)도 받는다. `github/*`처럼 GitHub의 다른 조직은 이 정책 밖이라 해시를 요구받는다(`actions/setup-python@main`은 종료 0, `github/codeql-action/init@v3`은 14였다. 손으로 봤다). `actions/` 조직은 러너를 돌리는 쪽과 신뢰 경계가 같고, 서드파티의 태그는 그 저장소의 권한만으로 옮겨진다(공개 사고 CVE-2025-30066에서 `tj-actions/changed-files`의 태그가 옮겨져 시크릿이 실행 로그에 찍혔다). 이 정책에서 남는 6건(`astral-sh/setup-uv` 2, `pnpm/action-setup` 3, `anthropics/claude-code-action` 1)을 해시와 판 주석으로 고정한다. 해시와 주석은 zizmor의 고침(`--fix=all`, 온라인)이 썼고, 셋 모두 그날 major 태그(`v5`·`v6`·`v1`)와 판 태그(`v5.4.2`·`v6.0.10`·`v1.0.244`)가 가리킨 커밋과 같았다(`gh api repos/<액션>/commits/<태그>`, 손으로 봤다). 그래서 고정이 도는 코드를 바꾸지 않는다. 해시로 고정한 액션은 패치 판을 저절로 받지 않는다. 갱신 도구(Dependabot 등)는 들이지 않고 손으로 올린다.

## Considered Options

- **머리 주석의 규약을 그대로 둔다.** 비용이 0이다. 그러나 두 번 빠졌고, 한 번은 CodeRabbit이, 한 번은 사람이 찾았다. 거부했다.
- **자체 검사.** YAML을 읽어 체크아웃마다 값을 본다. `.scratch/harness/probes/review_workflow.py`가 한 파일에서 하는 일이고, 새 도구 없이 이미 전이 의존성으로 있는 PyYAML로 된다. 그러나 규칙 하나뿐이다. 같은 도구가 보는 과한 권한, 템플릿 주입, `pull_request_target`, 캐시 오염을 하나씩 다시 짜야 한다. 거부했다.
- **actionlint.** 문법·표현식·셸 스크립트를 보는 린터이고 하드닝 감사(artipacked 같은 것)가 없다. 다른 축이라 이 결정의 대안이 아니다.
- **CodeQL의 actions 언어.** GitHub의 code scanning으로 돌리면 결과가 보안 탭에 쌓이고, 로컬에서 돌리려면 CodeQL CLI 번들을 uv 밖에서 따로 받아야 해 판의 원천이 `uv.lock` 하나로 모이지 않는다. 거부했다.
- **zizmor-action(`zizmorcore/zizmor-action`).** CI에서만 돌고 판이 액션 입력이라 로컬과 판의 원천이 둘이 된다. 기본값은 SARIF를 올려 `security-events: write`가 든다. 거부했다.
- **pre-commit 원격 훅(`zizmorcore/zizmor-pre-commit`).** 이 저장소의 훅은 모두 `repo: local`이고 CI는 pre-commit을 돌지 않는다. 판의 원천이 훅의 `rev`와 CI 둘이 된다. 거부했다.
- **`uvx zizmor@<판>`.** 설치 없이 판을 고정한다. 그러나 이 PC에서 프로브의 한 번과 손으로 친 다섯 번이 모두 설치에 실패했다. 여섯 중 다섯은 다른 프로세스가 휠에서 풀린 실행 파일을 잡고 있어 uv가 임시 디렉터리를 지우지 못한 것(os error 32)이고, 그때 떠 있던 것은 Windows Defender(`MsMpEng`)였다(원인으로 잰 것은 아니다). 나머지 하나(`UV_LINK_MODE=copy`)는 앞선 실패가 캐시에 남긴 임시 디렉터리를 휠의 잘못된 항목으로 읽었다. 같은 판을 dev 의존성으로 둔 임시 프로젝트의 `uv sync`는 프로브에서 네 번 모두(마지막은 `--no-cache`) 실행 파일을 남겼고, 이 워크트리의 `uv add --dev zizmor`도 지나갔다. 거부했다.
- **`unpinned-uses`를 모두 해시로 고정한다(zizmor 기본값, 16건).** 가장 엄하다. `actions/*`까지 고정하면 GitHub가 고친 패치도 손으로 올려야 받는데, 그 액션의 신뢰 경계는 러너와 같아 얻는 것이 적다. 거부했다.
- **`unpinned-uses`를 끈다.** 0건이 되지만, 비밀(`CLAUDE_CODE_OAUTH_TOKEN`)과 쓰기 토큰을 쥔 서드파티 액션이 태그에 남는다. 거부했다.
- **auditor 페르소나.** 10건을 더 낸다(이름 없는 정의 6, 설명 없는 권한 2, `claude-code-review.yml`에 워크플로 단위 `permissions`가 없음 1, 환경 밖의 시크릿 1). 거짓 양성을 감수하는 페르소나라 하드 게이트에 두지 않는다(`CLAUDE.md` 교정 루프).

## Consequences

- **게이트가 열둘에서 열셋이 된다.** 손으로 치는 검증 명령 다섯은 그대로이고, 지침 검사처럼 pre-commit(러너 `tools/run_checks.py`의 `CHECKS`)과 CI에만 있다. zizmor 실행 파일은 한 번에 0.2초 남짓이고(프로브의 timing), `uv run`을 거친 게이트 명령은 0.3초 남짓이었다(손으로 봤다). 그래서 `always_run`이다. 회귀 테스트 15개는 pytest에 1.5~6.7초를 더한다(세 번, 첫 회가 가장 느렸다. 손으로 봤다). 그래서 워크플로가 바뀌지 않은 커밋에서도 돌고, `uv.lock`으로 zizmor를 올린 커밋이 새 감사의 결과를 바로 본다.
- **판정자가 잡는지를 테스트가 본다(`tests/tools/test_zizmor_gate.py`).** 게이트의 인자를 저장소 워크플로와 설정의 사본에 돌린다. 체크아웃마다 `persist-credentials: false`를 지우면 artipacked 하나가 그 단계를, 서드파티 액션마다 해시를 태그로 바꾸면 unpinned-uses 하나가 그 줄을 가리키고 종료 코드가 0이 아님을 단언한다(실패의 까닭까지, 대기열 144). 깨진 YAML이 실패하는 것, 무시 주석을 단 체크아웃이 지나는 것, 러너와 CI의 명령이 같은 것도 본다. 그 밖의 감사가 꺼지는 것과 `actions/*`의 정책이 넓어지는 것은 보지 않는다. 설정에서 감사를 끄거나 정책을 넓히거나 명령에서 옵션을 빼는 변이 다섯이 모두 빨갛다(`.scratch/harness/probes/zizmor_gate_mutations.toml`).
- **예외는 그 자리의 주석이다.** 자격 증명이 필요한 잡이 생기면 그 체크아웃의 `uses:` 줄에 `# zizmor: ignore[artipacked]`와 까닭을 함께 둔다. 이 길은 위 테스트가 밟는다. `ci.yml` 머리 주석의 규약은 artipacked가 판정한다는 문장으로 바뀐다.
- **`claude-code-review.yml`의 액션을 고정하는 PR은 그 파일을 바꾸므로 claude-review가 건너뛴다**(ADR 0006, `operations.md` 리뷰 파이프라인). 그 PR은 CodeRabbit 코멘트와 셀프 리뷰로 손으로 본다.
- **`.pre-commit-config.yaml`도 감사 대상이다.** 1.30.1이 저장소 루트에서 거둔다. 지금은 0건이다. `node_modules`와 `.claude/worktrees/`는 `.gitignore`를 따라 거두지 않았다(주 체크아웃에서 손으로 봤다).
- **못 보는 것은 온라인 감사다.** 해시로 고정한 판에 취약점 공지가 나도 게이트는 모른다. 고정한 액션을 올릴 때 `GH_TOKEN`을 주고 `uv run zizmor --config .github/zizmor.yml .`을 손으로 돌린다.
- `operations.md` 가드레일, `tech.md`의 새 행(워크플로 감사), `CLAUDE.md` 검증 명령 절의 게이트 수가 바뀐다. 헌법 버전은 patch다.
