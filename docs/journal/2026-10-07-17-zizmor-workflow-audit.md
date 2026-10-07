# 2026-10-07 (17) 워크플로 하드닝을 zizmor로 판정한다

대기열 142의 일이다. PR #162를 연 세션의 next-session 지시문으로 연 새 세션이고, 주 체크아웃에서 브랜치를 따지 않고
`EnterWorktree`로 새 워크트리 `zizmor-workflow-audit`에 들어가 `origin/main`(`61884df`)에서 `chore/zizmor-workflow-audit`로
바꿨다. 순번은 17이다. 16은 형제 워크트리 `review-axis-and-failure-reason`의 미커밋 일지가 쓴다.

## 계기

> 사용자: "대기열 142(워크플로 하드닝을 zizmor로 판정)를 반영한다. 새 도구라 docs/constitution/tech.md와 docs/adr/의 ADR 초안을 먼저 보여 주고 승인받은 뒤 CI 잡이나 pre-commit에 둔다"

지시문의 선행 조건은 둘이었다. 설치 길과 판 고정(uv 개발 의존성, pre-commit 훅, GitHub Action), 그리고 이 저장소의 워크플로
둘에 첫 실행이 무엇을 내는지다. 형제 세션이 `operations.md`를 고치는 중이라 가드레일 절과 겹칠 수 있다는 것도 적혀 있었다.

ADR 초안을 보여 주고 `unpinned-uses` 정책을 물었더니 쉬운 설명을 먼저 청했다.

> 사용자: "쉽게 설명해줘"

태그가 옮겨질 수 있다는 것, 해시 고정의 비용, 세 선택지를 풀어 다시 물었다.

> 사용자: (고른 것) "① 서드파티만 해시 (Recommended)"

## 확인한 것

측정은 `.scratch/harness/probes/zizmor_gate.py`가 다시 낸다(zizmor 1.30.1). 숫자와 결론은 ADR 0027에 있고, 여기는 경위만 적는다.

- **첫 실행.** 도입 전 main에서 regular 16건이 모두 `unpinned-uses`였다. 1.30.1의 기본 정책은 GitHub 소유 액션까지 해시
  고정을 요구한다. artipacked는 0건이었다(PR #162·#164가 이미 고쳤다).
- **판정자가 잡는지.** 체크아웃 다섯에서 `persist-credentials: false`를 하나씩 지운 사본마다 artipacked가 그 단계를
  가리켰다. 등급이 checkout의 판에 따라 medium(v4)과 low(v7)로 갈려 `--min-severity`를 두지 않았다. 처음에는 등급을
  아티팩트 업로드 탓으로 적었는데 두 리뷰 축이 반례를 냈다(아래 셀프 리뷰).
- **`--strict-collection`.** 기본값은 깨진 YAML을 경고만 하고 건너뛰어, 멀쩡한 워크플로 옆에서 종료 0이었다.
- **설치 길.** `uvx`는 이 PC에서 여섯 번 모두 설치에 실패했다(다섯은 os error 32, 그때 Defender가 떠 있었다). 같은 판을
  dev 의존성으로 둔 `uv sync`는 지나갔다. 처음 두 번의 실패 뒤에는 휠을 PyPI에서 받아 해시를 대조하고 실행 파일만 꺼내
  첫 실행을 쟀다.
- **설정의 자동 탐색이 워크트리에서 주 체크아웃을 읽는다.** 구현 뒤 저장소 테스트가 `actions/*`까지 `unpinned-uses`로
  내서 알았다. `-v` 출력의 `root`가 `C:\project\agent`였다. zizmor는 위로 올라가며 `.git` 디렉터리를 찾는데 워크트리의
  `.git`은 파일이다. 그래서 게이트가 `--config .github/zizmor.yml`을 명시한다. 초안에는 없던 것이라 ADR에 문단을 더했다.
- **고정한 해시.** zizmor의 고침(`--fix=all`, 온라인)이 해시와 판 주석을 썼다. 세 액션 모두 major 태그와 판 태그가 같은
  커밋을 가리키는지 `gh api repos/<액션>/commits/<태그>`로 따로 봤다. `claude-code-action`의 `5898584`는 일지 2026-10-07-14가
  읽은 v1.0.244와 같다.

## 바꾼 것

- `pyproject.toml`·`uv.lock`: dev 의존성 `zizmor>=1.30.1`(락은 1.30.1).
- `.github/zizmor.yml`: `unpinned-uses` 정책(`actions/*`는 태그 허용, 나머지는 해시).
- `tools/run_checks.py`: `CHECKS`에 `zizmor`(`web-verify` 앞). 독스트링의 "일곱"은 잰 때의 수로 두고 여덟이 됐다고 적었다.
- `.github/workflows/ci.yml`: `python` 잡의 마지막 단계로 같은 명령. 머리 주석의 규약을 판정자 문장과 무시 주석의 모양으로
  바꿨다. 서드파티 액션 다섯을 해시로 고정했다.
- `.github/workflows/claude-code-review.yml`: `claude-code-action`을 해시로 고정하고 머리 주석에 한 줄. 이 파일을 바꾼 PR은
  claude-review가 건너뛰므로 별도 PR로 먼저 병합한다(`operations.md` 리뷰 파이프라인).
- `tests/tools/test_zizmor_gate.py`: 게이트 명령의 옵션과 CI의 같은 명령, 저장소가 지나고 워크플로를 모두 거두는 것,
  artipacked 다섯, unpinned-uses 여섯, 깨진 YAML, 무시 주석. 테스트를 먼저 써서 빨강을 본 뒤 구현했다(무시 주석
  한 건은 셀프 리뷰 뒤에 더했다).
- `.scratch/harness/probes/zizmor_gate.py`·`zizmor_gate_mutations.toml`과 README 두 행.
- 문서: ADR 0027과 색인, `tech.md`의 워크플로 감사 행, `operations.md` 가드레일의 문장 둘, `CLAUDE.md`의 게이트 수
  (열셋, pre-commit 여섯), 헌법 3.0.19, 루트 `README.md`의 검사 수, 대기열 142 닫힘.

`operations.md`는 가드레일 절(9행)만 고쳤다. 형제가 고치는 리뷰 파이프라인 절(25~38행)과는 떨어져 있다.

## 검사

- 테스트의 빨강: 구현 전 8 실패와 1 건너뜀(해시 고정 사례 0). 구현 뒤 `test_zizmor_gate.py` 15 통과(셀프 리뷰 뒤).
- 변이(`zizmor_gate_mutations.toml`): 서드파티 태그 허용, artipacked 끄기, `--strict-collection` 빼기, `--config` 빼기,
  CI 명령 어긋남. 다섯 모두 기대대로 빨강.
- 검증 명령: ruff 둘(import 정렬 하나를 고친 뒤), pyright 0 errors, lint-imports, pytest 1860 통과, 지침 검사, 타입 우회 검사,
  훅 러너, zizmor 0건, `pnpm -C web verify`. 셀프 리뷰를 반영한 뒤 다시 돌려 모두 초록이었고 pytest는 1861 통과, 변이
  다섯도 다시 기대대로 빨강이었다.

## 셀프 리뷰

`/code-review`, base `61884df`, 수정 13, 미추적 6, 커밋 0. `tools/`와 `tests/`의 소스가 있어 표준 축도 기본 모델이다.
명세는 대기열 142행, 사용자 지시문, 승인된 ADR 0027이고, PR 분할 계획과 형제와의 겹침은 리뷰어 참고로 갈랐다. 명세
축은 빠진 요구와 범위 넘침 없이 Minor 셋·Nit 넷, 표준 축은 Minor 다섯·판단 항목 하나·Nit 넷이었다. 겹친 것은 다섯이다.

- **고쳤다, 두 축 Minor(artipacked 등급의 원인).** ADR이 등급을 "아티팩트를 올리는 잡" 탓으로 적었는데, 두 축 모두
  업로드를 지워도 13이고 checkout만 `@v7`로 바꾸면 12라는 반례를 냈다. 손으로 다시 재 보니 v4·v5는 medium, v6·v7은
  low였고 체크아웃 전체를 올리는 업로드가 한 단계를 올렸다. 프로브에 severity 절을 더하고 ADR을 그 측정으로 고쳤다.
  잰 것은 종료 코드뿐인데 원인을 측정처럼 적은 것이다.
- **고쳤다, 두 축 Minor(ADR 안의 모순).** "두 번 모두 사람이 찾았다"가 같은 ADR의 "CodeRabbit이 잡았고"와 어긋났다.
- **고쳤다, 명세 Minor(`ref-pin`의 범위).** 태그만이 아니라 브랜치도 받고, `github/*`는 `actions/*`가 아니다. 손으로
  확인한 뒤 ADR·`tech.md`·설정 주석을 "`actions/` 조직, ref 고정"으로 좁혔다.
- **고쳤다, 표준 Minor(같은 사실이 두 곳).** `operations.md` 가드레일과 `tech.md`가 `--config`와 자동 탐색을 함께
  적었다. `operations.md`는 무엇을 판정하고 어디서 도는지만, `tech.md`는 판과 옵션만 들게 나눴다.
- **고쳤다, 표준 Minor(보편 주장).** 설정 주석과 테스트 독스트링의 "감사를 끄면 빨갛다"를 artipacked와 서드파티 정책으로
  좁히고, 못 보는 것(그 밖의 감사, `actions/*` 정책)을 적었다.
- **고쳤다, 표준 Minor(시간의 어림).** 러너 독스트링이 0.2초만 보고 회귀 테스트가 pytest에 더하는 몫을 빠뜨렸다. 세 번
  재서 1.5~6.7초, 게이트 명령은 `uv run`을 거쳐 0.3초 남짓이었다. ADR의 timing도 실행 파일의 값이라고 밝혔다.
- **고쳤다, 명세 Nit(부르는 쪽의 길).** 무시 주석의 길을 테스트가 밟지 않아 한 건을 더했다. `GH_TOKEN`으로 손으로 돌리는
  길은 남겼다. 그 길이 깨지면 손으로 돌리는 사람이 바로 본다.
- **고쳤다, 두 축 Nit.** CodeQL을 "GitHub에서만 돈다"고 적은 것(CLI가 로컬에서 돈다)을 판의 원천 문제로 고쳤다. ADR의
  "의존성이 0", 설정 주석의 "주 체크아웃의 설정을 읽었다"(찾지 못해 기본값으로 돌았다), 루트 `README.md`에서 "넷"의
  셈을 흐린 문장의 자리, 러너 `Check` 독스트링의 "예전 훅 id"도 고쳤다.
- **판단 항목을 따른다, 두 축(PR 분할).** `claude-code-review.yml`의 변경은 별도 PR로 먼저 병합한다. 그 PR에 들어갈 주석이
  "zizmor가 판정한다(ADR 0027)"를 적어 둘째 PR 전까지 main에서 거짓이었으므로 대기열 번호만 남겼다.
- **남겼다, 표준 Nit(헌법 버전).** 2.4.0은 새 규칙 문장과 스택 행을 minor로 올렸지만, 그 뒤 게이트와 스택 행을 더한
  3.0.2·3.0.8·3.0.17은 patch였다. 절을 더하지 않았으니 patch를 따른다.
- **남겼다, 표준 Nit(프로브와 테스트의 같은 함수).** 프로브는 `tests/`를 import하지 않는 단독 스크립트이고, 이웃
  프로브도 같다. 프로브의 `gate_args`는 설정이 없던 도입 전 트리도 재야 해서 `CHECKS`를 읽지 않는다.
