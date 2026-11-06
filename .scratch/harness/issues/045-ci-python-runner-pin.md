# 045: CI의 `python` 잡이 `ubuntu-latest`가 아니라 `ubuntu-24.04`에서 돌게 못 박는다

**What to build:** `.github/workflows/ci.yml`의 `python` 잡은 `ubuntu-latest`에서 돌고 `ripgrep`을 apt로 깐다(`ripgrep` 설치 단계, ADR 0038). `tests/tools/test_hook_env_read_rg.py`는 그 `rg`를 실제로 띄워 훅과 견주는데, 그 시험의 `_GREP_TOOL_STRICTER` 주석(117줄)은 "rg 14.1.1 은 겹친 묶음을 풀지 못해 오류로 끝나고 훅은 둘 다 푼다"고 적어 14.x의 동작을 가정한다. 2026-11-06에 `ubuntu-latest`가 `ubuntu-24.04`(이미지 `20261101.360.1`, ripgrep 14.1.0-1)에서 `ubuntu-26.04`(이미지 `20261101.186.1`, ripgrep 15.1.0-1ubuntu1)로 넘어갔고, 그 뒤의 `python` 잡이 `[{{.env}}]` 한 건으로 실패해(`1 failed, 6441 passed`) 모든 PR의 `verify`가 빨개졌다. main의 마지막 초록 실행(`42172283644`, 06:05 UTC)과 PR #479의 실패 실행(`42183052219`, 07:46 UTC)의 `python` 잡 로그가 근거다.

`python` 잡 하나의 `runs-on`을 `ubuntu-24.04`로 못 박고, 까닭을 그 줄 위에 한 줄 적는다. `rg`를 까는 잡은 이 하나뿐이고(`grep -n ripgrep .github/workflows/ci.yml`) 다른 잡은 26.04에서도 통과했으므로 건드리지 않는다. ripgrep 15에서 훅과 `rg`가 어떻게 다른지 재서 시험이 두 판을 모두 아는 쪽으로 고치는 일은 이 티켓의 밖이다. 새 harness 티켓으로 다룬다(경위는 일지 2026-11-06-08 "이어받은 세션(PR 반영·병합부터)", 남긴 일은 일지 2026-11-06-10 "다음").

**대기열:** 500

**Status:** done

## 수용 기준

- [x] `ci.yml`의 `python` 잡만 `runs-on: ubuntu-24.04`이고 까닭을 적었다(주석 두 줄). 다른 잡의 `runs-on`은 바뀌지 않았다
- [ ] 이 PR의 CI에서 `python` 잡의 로그에 `Image: ubuntu-24.04`와 `Setting up ripgrep (14.1.0-1)`이 보이고 `python`과 `verify`가 초록이다
- [x] 워크플로 감사(zizmor)와 지침 검사를 포함해 검증 명령이 모두 초록이다(손으로 치는 명령 전부와 `uv run python tools/run_checks.py`. 커밋 직전의 pre-commit이 갈음하는 것은 그 결과로 갈음한다)
