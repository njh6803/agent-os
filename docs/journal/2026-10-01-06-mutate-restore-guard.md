# 2026-10-01 (06) 변이 도구의 되돌림 가드와 root에서도 서는 되돌림 실패 테스트 — 대기열 77·80

web-admin 뒤 하네스 chore 배치의 다음 묶음이다. 지시문은 일지 2026-10-01-05의 "다음"이 가리킨 next-session 지시문에서
왔다. 브랜치는 `chore/mutate-restore-guard`다. 데스크톱 앱 세션이 주 체크아웃에서 시작해 `EnterWorktree`로 만든 워크트리에서
일했다. 세션 제목은 UserPromptSubmit 훅의 지시대로 브랜치 이름으로 바꿨고, 이 앱에서는 `self`가 통했다.

> 사용자: ".scratch/retro-queue.md의 77·80(변이 도구의 되돌림과 그 테스트)을 chore PR 하나로 반영한다"

앞 PR의 끝을 여기 남긴다(일지 05에 없다). PR #114는 3회차(`9766bba`, CI 초록) 뒤 `ca056df`로 병합됐다. 3회차
claude-review의 Nit 둘(`operations.md` 새 항목의 머리 문단을 하위 항목으로 떼기, retro 5단계를 6단계로 가르기)은 둘 다 후속
허용이라 반영하지 않았다. 지시문의 선행 조건 둘은 이 세션이 닫았다. 클라우드 세션이 남긴 원격 브랜치
`chore/skill-check-and-retro-section`을 지웠고, main이고 깨끗한 주 체크아웃을 `ca056df`까지 당겼다.

## 자리를 정한 것

- **77.** `_run_mutated`가 쓰기에 성공한 변이 바이트를 `written`에 적고, 되돌리는 `_restore`가 파일이 그 바이트와 다르면 덮지
  않고 `RestoreError`로 알린다. 나머지 파일은 되돌리고, `main`은 3을 낸다.
  - `restore`에 적은 파일은 보지 않는다. 명령이 고쳐 쓰는 파일이라 그 쓰기와 다른 쓰기를 가를 수 없다. 편집한 파일을
    `restore`에도 적으면 그 파일도 보지 않는다. 이 모양은 지금 저장소의 변이 파일에 없다(명세 축 서브에이전트가 읽어 셌다).
  - 변이 바이트를 쓰다 실패한 파일은 `written`에 들지 않아 보지 않고 되돌린다. 쓰다 만 앞부분이 남아도 도구가 마지막으로
    쓴 것이고, 다른 쓰기로 알리면 쓰지 못한 원인이 가려진다.
  - `main`의 안내는 변이된 채 남은 파일을 `git diff`로 보고 되돌리라고 했다. 이제 "남은 파일을 git diff 로 보고 변이만 걷어
    낸다"고 한다. 다른 쓰기가 든 파일을 `git checkout`으로 되돌리면 그 쓰기까지 사라진다.
  - 독스트링의 3단계, "제자리가 아닌 실행", "못 보는 것"(되돌릴 파일에 든 다른 쓰기, 읽어 본 뒤 다시 쓰기까지의 틈)을
    고쳤다. 프로브 README의 `retro_hook_mutations.toml` 행에 있던 "되돌림이 변이 전 바이트로 덮는다"도 새 동작으로 고쳤다.
- **80.** `_잠그는_러너`가 `chmod` 대신 `_쓰기를_막는다`로 그 파일의 `Path.write_bytes`만 막는다(monkeypatch). 권한을 건드리지
  않으므로 uid와 무관하고, 테스트 셋의 `finally`에 있던 권한 복구도 사라졌다.

## 잰 것

- **80의 사건을 root 컨테이너에서 재현하고, 고친 뒤 다시 쟀다(프로브 `.scratch/harness/probes/mutate_as_root.sh`).** 이
  기계의 Docker Desktop에 이웃 저장소가 남긴 파이썬 이미지(`agent-runtime-platform-api:latest`)가 있었다. pytest는 `.venv`에서
  순수 파이썬 패키지만 골라 붙였고 이미지는 내려받지 않았다. 고치기 전(`ca056df`의 테스트) root는 3 failed·83 passed로 일지
  05와 같은 셋이었고, 같은 컨테이너의 uid 10001은 86 passed였다. 고친 뒤에는 root와 uid 10001 모두 89 passed(파이썬 3.12.14,
  pydantic 2.13.5, pytest 9.1.1), 윈도우도 89 passed다.
- **새 테스트가 가드의 규칙을 하나씩 잰다(프로브 `.scratch/harness/probes/mutate_restore_mutations.toml`).** 빨강 기대 여섯과
  초록 기대 하나가 모두 기대대로였고, 빨간 여섯은 저마다 테스트 하나만 빨갰다. 셀프 리뷰 전의 첫 판(변이 다섯)도 모두
  기대대로 빨갰다. 리뷰 반영으로 `_restore`를 떼자 원문 셋이 들여쓰기 네 칸만큼 옮겨 갔고 `--check`가 그것을 알렸다.
- **실제 하위 프로세스가 변이 중에 대상을 고쳐도 덮지 않는다(손으로 봤다).** 워크트리에 임시 대상 파일과, 변이를 보면 그
  파일에 한 줄을 덧붙이는 pytest 테스트를 두고 도구를 돌렸다. 종료 코드 3과 "변이가 든 동안 다른 쓰기가 들어와 덮지
  않았다"가 나왔고, 파일에는 변이와 덧붙인 줄이 함께 남았다. 임시 파일은 지웠다.

## 셀프 리뷰

`/code-review`, base `ca056df`, 수정 파일 4, 커밋 0, 미추적 2. 두 축 모두 기본 모델이다(`tools/`와 `tests/`의 파이썬이
바뀌었다). 명세는 대기열 77·80 행이다.

- **명세 축.** 범위 초과는 없다. 틀린 것: 프로브 README의 "저마다 다른 테스트 하나만 빨갰다"(앞의 셋은 같은 테스트였다),
  `docker run`의 기본값이 `--pull=missing`이라 "내려받지 않는다"가 거짓일 수 있다. 부분적인 것: 변이를 쓰지 못한 파일의
  테스트는 그 파일이 바뀐 적이 없어 되돌린다는 것을 관찰하지 못한다. Nit: "제자리가 아닌 실행"의 보편형(되돌릴 파일
  예외), 테스트 독스트링의 따옴표가 실제 문구가 아니다, 되돌림 실패 테스트의 `match`가 가드 경로와 갈리지 않는다. 테스트가
  없는 경로 둘(`repeat` 2 이상, 파일이 지워짐)도 짚었다.
- **표준 축.** 같은 README 문장과 보편형, 프로브가 다시 내지 못하는 판(파이썬, pydantic), `RestoreError` 독스트링이 원인을
  둘로 닫는다(읽기 실패도 그리 간다), `finally` 안에 로직이 쌓였다(`CODING_STANDARDS.md`의 "에러 처리와 정상 흐름을
  분리한다"), `rewritable`을 집합으로 돌아 알림 순서가 실행마다 달라질 수 있다, 프로브 주석의 "tmp_path 밖에 쓰지 않는다"가
  지나치다. 판단 사항: Data Clumps(`held`·`written`·`rewritable`), `rewritable`이라는 이름, 테스트의 인라인 러너 중복.
- **고친 것.** README 문장, 보편형, `RestoreError` 독스트링, `_restore`로 떼기(실패는 반환값이 아니라 예외로 낸다, CQS),
  `rewritable`을 목록으로, `--pull never`, 프로브가 판을 찍게, 프로브 주석, `_쓰기를_막는다`에 `남는_앞부분`을 더해 쓰다 만
  파일을 되돌리는지 관찰하기, 따옴표 인용 걷기, `match`에 "쓰기를 막았다". 강화한 테스트가 새로 잡는 변이(쓰기에 성공한
  파일만 쥔다)와, 그 변이가 옛 테스트로는 지나간다는 초록 기대를 변이 파일에 더했다.
- **남긴 것.** Data Clumps와 이름은 판단 사항이고, 인라인 러너는 이 파일이 써 온 모양이다. `repeat` 2 이상은 반복이 끝난 뒤
  `finally`가 한 번 보는 구조이고, 지워진 파일은 기존 `OSError` 경로가 맡는다. 둘 다 테스트를 더하지 않았다.

## 검사

- 리뷰 반영 뒤: `uv run pytest -q` 1147 passed(경고 3은 `tests/test_conftest.py`의 pytest-asyncio 설정 경고로 이번 변경과
  무관하다), `uv run ruff check .`·`uv run ruff format --check .` 통과, `uv run pyright` 0 errors, `uv run lint-imports` 5 kept,
  `pnpm -C web verify` 초록(테스트 263, web은 바꾸지 않았다). `src/`를 바꾸지 않아 `-m llm`은 돌리지 않았다.

## PR 리뷰

PR #115. PR 직전 CodeRabbit CLI는 돌리지 않았다. 열기 전 `coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`였다.

- **CI**(`7eeb132`). `verify` 13분 40초, `claude-review` 1분 9초, 둘 다 초록. `verify`가 앞 PR(3분 남짓)보다 길었던 것은
  `uv sync --frozen` 한 단계가 10분 21초였기 때문이다(아래 회고).
- **CodeRabbit**(`@coderabbitai review`). 지적 없음. 요약의 범위가 `ca056df`부터 `7eeb132`까지라 HEAD까지 봤다.
- **claude-review.** Minor 하나: `_restore`의 `try` 안에 판정과 쓰기가 함께 있다(`CODING_STANDARDS.md`의 "에러 처리와 정상
  흐름을 분리한다"). 셀프 리뷰의 같은 지적에 `finally`에서 `_restore`로 떼었지만, 그 안의 `try`가 같은 모양을 다시 가졌다.
  파일 하나를 되돌리는 `_restore_file`로 떼고 다른 쓰기는 `_WrittenMeanwhile` 예외로 내, `try`에는 호출 하나만 남겼다. 리뷰가
  제안한 질의 함수(`-> bool`)는 읽다가 `OSError`를 낼 수 있어 `try` 안에 판정이 남는다. Nit 하나: "제자리가 아닌 실행"의 새
  문장이 "그래서"의 앞 문장을 바꿔 인과가 어긋났다. 단락 끝으로 옮겼다. 변이 셋의 원문을 새 구조에 맞췄고("알리고도
  덮는다"는 판정을 쓰기 뒤로 옮기는 변이가 됐다) 일곱 모두 다시 기대대로였다.

## 회고

후보 셋을 냈고 하나가 승인됐다.

> 사용자(질문에 답): "새 항목 (Recommended)", "기록만 (Recommended)", "기록만 (Recommended)"

- **82(새로).** `tools/hook_bash_python_stub.py`가 컨테이너 안의 python을 부르는 `docker run … -c "id -u; python --version"`을
  막아, 스크립트 파일로 우회했다. 같은 모양의 페이로드를 훅에 넣어 보니(스크래치 스크립트로 손으로 봤다) `echo "a; python x"`도
  막았고, `echo "python x"`와 `docker run … python --version`은 지나갔다. 독스트링이 문자열 안의 python은 명령어 자리가
  아니라고 적은 것은 문자열 머리의 python에만 맞는다.
- 기각한 것(일지에만): 리뷰 반영이 같은 규칙 위반을 한 층 아래로 옮겼다. 셀프 리뷰가 짚은 "`try` 안에 로직을 쌓지 않는다"를
  `_restore`로 떼어 고쳤는데 그 안의 `try`가 같은 모양이었고, claude-review가 다시 잡았다. 한 번이다. CI의 `uv sync`가 10분
  21초였다. setup-uv 캐시는 적중했지만 크기가 약 0MB(99328 B)였고, 같은 휠의 내려받기가 세 번씩 다시 시작됐다(로그를 읽었다).
  `prune-cache` 기본값(true)이 미리 빌드된 휠을 캐시에서 뺀 탓으로 본다(어림, setup-uv 문서는 읽지 않았다). 한 번이고 외부
  네트워크 사정이다.
- 일지에만: 프로브 README에 변이마다 서로 다른 테스트가 빨갰다고 로그를 다시 보지 않고 적었고 두 축이 모두 잡았다. 대기열
  20의 주장 검증이 이번에도 셋(그 문장, `docker run`의 기본 pull, 프로브가 다시 내지 못하는 판)을 잡았다. 세션 제목 훅의
  `self`는 이 데스크톱 앱 세션에서 통했다. 81의 거부는 클라우드 세션의 도구에서만 났다.

## 다음

- 대기열 77·80이 닫혔다. 이 PR의 2회차 CI와 병합은 다음 일지에 한 줄 남긴다.
- 다음 chore는 훅 셋인 79·81·82다. 셋 다 `tools/hook_payloads.toml`에 사례를 더한다. 81의 `self` 거부는 클라우드 세션에서만
  났다. 그 뒤 60(주장 검증 목록의 항목 하나)이다. web-widget은 설계 인터뷰가 먼저다.
