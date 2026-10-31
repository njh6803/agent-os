# 032: `-I`로 돌리는 파이썬에 `-X utf8`을 함께 주는 줄을 환경 규약에 더한다

**What to build:** `docs/constitution/operations.md` 환경 규약 상세의 `PYTHONUTF8` 줄 바로 아래에 한 줄을 더한다. `python -I`는 `PYTHON*` 환경 변수를 모두 무시해 설정 `env`의 `PYTHONUTF8`이 닿지 않으니, 한글을 찍는 스크립트를 `-I`로 돌릴 때는 `-X utf8`을 함께 준다. 대기열 484(40의 2회차)가 세 번째 반복에서 문턱을 지났다. 세 번째는 model-plugin 설계 PR의 셀프 리뷰 반영을 확인하려고 앞 세션의 기록 파일을 `uv run python -I`로 읽은 스크립트의 한글 출력이 cp949로 나가 Bash 도구에서 깨져 보인 것이다. 면제 PR `docs/model-plugin`의 회고가 같은 PR에 싣는 티켓이다(retro 4단계, ADR 0037).

**대기열:** 484

**Status:** done

## 수용 기준

- [x] `docs/constitution/operations.md` 환경 규약 상세의 `PYTHONUTF8` 줄 바로 아래에 `-I`가 `PYTHON*` 환경 변수를 모두 무시하므로 `-X utf8`을 함께 준다는 줄이 있다
- [x] 회고 반영: 그 줄을 더하고 대기열 484를 이 티켓으로 닫았다, 일지 2026-10-31-06-model-plugin-design.md
- [x] 검증 명령이 모두 초록이다
