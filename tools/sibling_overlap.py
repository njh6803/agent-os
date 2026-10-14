"""이 브랜치가 새로 매긴 번호와 고친 파일을 형제와 대조하고 다음 빈 번호를 낸다.

커밋 직전에 대조하고(대기열 48·115), 일지를 쓰기 전에 그 이름의 날짜와 순번을 받는다(대기열 182).

형제는 셋이다. 이미 병합된 `origin/main`, 아직 병합되지 않은 열린 PR의 head,
아직 커밋되지 않은 같은 저장소의 다른 워크트리다. `origin/main`과 워크트리만 보던 손 대조는
아직 열린 PR이 먼저 가져간 번호와 다섯 번 부딪혔다(대기열 115). 클라우드 세션에서는 형제가
워크트리가 아니라 다른 세션의 열린 PR이라 손 대조가 보는 것이 main뿐이다(일지 2026-10-07-09).

번호는 넷이고, 형제가 새로 매긴 번호를 이 브랜치도 새로 매겼으면 겹침이다.

- 일지 순번: `docs/journal/YYYY-MM-DD-NN-*.md`의 `YYYY-MM-DD-NN`.
  같은 순번에 다른 파일이면 겹침이다.
- ADR 번호: `docs/adr/NNNN-*.md`의 `NNNN`. 같은 번호에 다른 파일이면 겹침이다.
- 대기열 행: `.scratch/retro-queue.md`의 `| N |`로 시작하는 행.
  같은 번호에 다른 행이면 겹침이다.
- 헌법 판: `docs/constitution/README.md`의 `**Version**: X.Y.Z`.
  둘이 같은 판으로 올렸으면 겹침이다.

"새로"는 이 브랜치와 `origin/main`의 merge-base에 없다는 뜻이다. 열린 PR과 워크트리는
그 merge-base와 `origin/main` 어디에도 없는 번호만 그 형제의 것으로 본다. 그래서 main이
이미 가진 번호는 main 줄에만 한 번 나온다. 이 브랜치의 새 번호에서는 main에 같은 번호·같은
파일(행)로 이미 든 것도 뺀다. 쌓아 올린 아래 PR이 squash로 병합된 뒤 main을 들이지 않은
브랜치에서 그 번호는 공유한 이력인데, 새 일지로 세면 이름순 판정이 거짓 1을 내고 main에 있는
일지를 옮기라고 한다. 헌법 판은 내용을 가를 수 없어 빼지 않는다. 이 브랜치는 작업 트리(커밋하지
않은 변경과 미추적 파일)를 읽는다. merge-base에서 네 자리 가운데 하나라도 비면 경로가 어긋난 것으로
보고 2로 끝난다(조용히 겹침 없음이 되지 않게).

열린 PR은 GitHub REST(`gh api repos/<owner>/<repo>/pulls?state=open`)로 읽는다. `origin`이
github.com이 아니거나 `gh`가 없거나 실패하면 `refs/pull/N/merge`가 있는 PR을 열린 것으로 본다.
2026-10-07에 이 클라우드 컨테이너에서 손으로 봤다. `gh pr list`는 GraphQL이 막혀 HTTP 403이었고
`gh api`의 REST는 열렸다. `git ls-remote origin 'refs/pull/*'`에는 PR 160개의 head ref와 merge
ref 하나(열린 #158)가 있었고, #158은 main과 충돌한 뒤에도(`mergeable_state: dirty`) 옛 base의
merge ref가 남아 있었다. 로컬 Windows에서는 아직 돌리지 않았다. head가 이 브랜치의 HEAD에 이미
들었거나 원격의 같은 이름 브랜치와 같은 PR은 이 브랜치 자신의 PR이라 형제가 아니다(앞의 것은
푸시 전의 새 커밋, 뒤의 것은 amend·rebase 뒤 아직 밀지 않은 때).

함께 고친 파일도 알린다. 이 브랜치가 merge-base 뒤에 고친 파일과 형제가 자기 merge-base
뒤에 고친 파일이 겹치면, 나중에 병합하는 쪽에서 글자 충돌이 날 수 있다. 이것은 종료
코드를 바꾸지 않는다. 형제와 main의 merge-base가 이 클론에 없으면(얕은 클론) 그 형제의 고친
파일만 "알 수 없다"로 두고 번호는 그대로 대조한다.

이 브랜치가 고친 파일(함께 고친 파일, 헌법 판, 카나리아, `--move` 가 쓰는 것)은 merge-base 뒤에
고친 파일 가운데 main 과 내용이 다른 것과 미추적 파일이다. main 을 합치다 충돌을 풀고 커밋하기
전에는 merge-base 가 옛 자리에 머물러, merge-base 와의 차이만 세면 main 이 들여온 파일이 모두
섞인다. 그 상태에서 친 대조가 main 의 규칙과 스킬을 카나리아 누락으로 알리고 1로 끝났다(일지
2026-10-14-04).

HEAD가 닫힌 PR의 head와 같은 형제 워크트리는 커밋하지 않은 변경(그 HEAD 뒤의 변경과 미추적
파일)만 고친 파일로 견주고, 형제 줄에서는 그 수만 접어 찍는다(대기열 194). 함께 고친 파일 서른여덟
줄 가운데 서른다섯 줄이 형제 워크트리의 것이라 열린 PR의 줄이 묻혔다(일지 2026-10-13-18). 이 판을
들일 때 같은 꼴로 다시 친 대조에서는 형제 워크트리의 줄 서른일곱 가운데 서른여섯이 PR이 닫힌
워크트리의 것이었다(손으로 봤다, 일지 2026-10-13-30). 그 커밋은 이미 병합됐거나, 병합 없이 닫혀
앞으로도 병합되지 않아 충돌 후보가 아니다. 그래서 병합과 닫힘을 가리지 않는다. 닫힌 PR은 열린
PR을 읽으려고 이미 치는 `ls-remote`의 `refs/pull/*/head` 가운데 열린 PR이 아닌 것이다. 병합 여부를
따로 물으면 `gh api …/pulls?state=closed --paginate`가 2.2~3.5초, `gh pr list --state merged`가
1.6~2.0초를 더 썼고, 그 `ls-remote`는 0.6~0.7초였다(2026-10-13 이 저장소의 PR 217개에서 세 번씩,
`.scratch/harness/probes/sibling_overlap_merge_cost.sh`). 병합 없이 닫힌 PR은 그때 0개였다.
번호는 접지 않고 그대로 대조한다.

다음 빈 번호를 늘 찍는다(대기열 157·182). 일지를 쓰기 전에는 이 브랜치에 새 번호가 없어
겹침 대조가 아무것도 알리지 못하고, 먼저 쓴 번호는 겹친 뒤에야 옮겨져 그 번호를 든 인용도
함께 고쳐야 했다. 일지는 오늘 날짜(main에 더 늦은 날짜의 일지가 있으면 그 날짜)의 순번,
대기열은 행 번호이고, 이 브랜치와 merge-base·main·형제 전체가 쓴 가장 큰 번호의 다음이다. 빈
사이 번호는 고르지 않는다. 새 일지는 이름순으로 맨 뒤여야 한다(아래). 이 브랜치에 새 일지가
없으면 그 번호로 바로 머리 한 줄 일지 파일을 만들라는 안내를 붙인다(대기열 220). 형제의 이
대조는 디스크의 일지 파일로 찬 번호를 보므로, 받은 번호를 파일 없이 두는 동안 형제가 같은 번호를
받아 갔다(대기열 205). 그 안내가 `next-session` 1단계에만 있었는데, 그 스킬은 보통 PR을 열거나
병합한 뒤에 실려 번호를 받는 때에 읽히지 않을 수 있다.

형제가 쓴 가장 높은 헌법 판도 늘 찍는다(대기열 199). 판을 올리기 전의 대조는 겹침을 알리지
못해, 올린 뒤 다시 친 대조가 형제가 먼저 매긴 같은 판을 알렸다. main은 가진 판, 다른 형제는
새로 매긴 판이 후보이고, 판은 글자가 아니라 수로 견준다. 다음 판은 고르지 않는다(아래).

헌법 파일(`principles.md`·`tech.md`·`operations.md`)을 merge-base 뒤에 고쳤는데 이 브랜치가
판을 새로 매기지 않았으면 알린다(대기열 224). `principles.md` 거버넌스는 원칙 변경을 major, 절
추가를 minor, 문구 수정을 patch로 올리고, 판을 올리지 않은 변경은 뒤에 소급했다. 2.4.0과 2.5.1이
그런 PR 열셋을 묶었고(`docs/constitution/README.md`), `operations.md`를 고치고 올리지 않은 것을 셀프
리뷰가 잡았다(일지 2026-10-13-18).

일지의 이름순 차례도 본다(대기열 175). 다음 세션은 이름순 최신 일지의 "다음"을 읽는다. 이
브랜치의 새 일지 가운데 이름순 최신 것이 main의 최신 일지보다 앞이면, 지금 병합해도 그 일지는
최신이 아니라 다음 세션이 그 "다음"을 지나친다. 날짜를 넘긴 세션이 시작한 날짜로 쓴 일지가
그랬다(일지 2026-10-12-05). 이것은 겹침처럼 1로 끝난다. 열린 PR·워크트리의 일지보다 앞인 것은
그쪽이 먼저 병합될 때만 문제이고, 그때는 main과의 대조가 잡으므로 알리기만 한다. 그것까지 1로
끝내면 다음 빈 번호를 받은 형제끼리 서로를 앞질러 옮기기를 되풀이한다.

바꾼 하네스 파일의 카나리아도 본다(대기열 235). 이 브랜치가 merge-base 뒤에 고친 스킬 본문
(`.claude/skills/*/SKILL.md`), 규칙(`.claude/rules/*.md`), 서브에이전트(`.claude/agents/*.md`)
가운데 지금 있는 것마다, 그 경로를 `source` 로 든 카나리아
명세(`.scratch/**/probes/canary/*.toml`)를 이 브랜치가 하나도 고치지 않았으면 알린다. 바꾼 하네스는
새 `claude -p` 세션에서 불러 보고 그 명세의 `# 최신 결과:` 줄을
고친다(`docs/constitution/operations.md` 환경 규약 상세). `next-session` 1단계를 바꾸고 카나리아를
돌리지 않은 채 셀프 리뷰 두 축과 PR 직전 리뷰를 지났고, 회고에서 그 절을 다시 읽다 찾았다(일지
2026-10-13-38). 헌법 판처럼 커밋 전에 고칠 누락이라 이것도 1로 끝난다. 다만 계정 한도로 카나리아를
돌리지 못하면 결과 줄을 고칠 수 없다. 그 갈래는 같은 절의 계정 한도 항목대로 사전 확인만 돌리고 이
알림이 남은 채 커밋한다고 출력이 함께 말한다(셀프 리뷰 명세 축, 일지 2026-10-14-04).

`--move` 는 "옮길 번호" 를 실제로 옮긴다(대기열 249). 형제가 더 높은 번호를 들고 먼저 병합해, 한
세션에서 받은 번호를 두 번 옮기고 그때마다 그 번호의 인용(다섯에서 아홉)을 손으로 고쳤다(일지
2026-10-13-59·2026-10-13-61). 일지와 ADR 은 파일 이름을 바꾸고, 이 브랜치의 변경과 미추적 파일 안의
인용을 바꾼다. 인용의 꼴은 일지 순번(`YYYY-MM-DD-NN`)과 일지 머리 줄(`# YYYY-MM-DD (NN)`), `ADR
NNNN` 과 목록 속 `·NNNN`, ADR 의 파일 이름(`NNNN-…`)과 색인의 `[NNNN]`, `대기열 N` 과 목록 속 `·N`,
대기열 파일의 행 머리(`| N |`)다. ADR 의 꼴은 `.claude/rules/adr.md` 의 번호 항목과 같다. 모든 꼴을
한 번에 바꿔, 차례대로 옮기는 사슬(03→05, 05→07)의 03 이 07 까지 가지 않는다. 인용 블록(`>` 로
시작하는 줄)은 옮기지 않는다. 일지는 사용자 프롬프트를 원문으로 인용하는데(`> 사용자:`), 이
브랜치의 일지를 옮긴 첫 실행이 그 원문의 일지 번호까지 바꿨다(일지 2026-10-14-04). merge-base 나
main 의 판에 글자 그대로 있는 줄도 옮기지 않는다. 그 줄의 같은 번호는 상대를 가리킨다
(`.claude/rules/adr.md`). main 을 합치다 같은 번호의 대기열 행 둘을 남긴 채 옮기면 main 의 행
머리까지 바뀌었다(PR 직전 버그 축). BOM 으로 시작하는 파일은 BOM 을 떼고 바꾼 뒤 다시 붙인다. UTF-8
로 읽지 못하는 파일은 두고, 옮길 자리에 무엇이 있으면 아무것도 고치지 않고 2로 끝난다. 고치다 멈추면
고친 것을 거꾸로 되돌리고 2로 끝난다. 되돌리지 못한 것이 있으면 그것을 들고 `--move` 를 다시 치지
말라고 한다(다시 치면 이미 옮긴 인용이 사슬을 따라 한 번 더 옮겨진다). 글을 먼저 고치고 이름을
바꾸며 인덱스는 건드리지 않는다. 그래서 출력은 이름을 바꾼 파일을 `옛 → 새` 로 따로 찍고, 옛 이름의
지움까지 스테이지하라고(`git add -A`) 말한다. 옮기지 못한 꼴(아래 못 보는 것)도 함께 말한다. 옮긴
뒤에는 다시 대조해 찍고 그 종료 코드로 끝난다.

`-h`·`--help` 는 쓰임과 종료 코드를 찍는다. 2로 끝나면 stderr 에 할 일(번호를 손으로 고르지
않는다)을 함께 싣는다(대기열 251). 시작 경로만 받던 때 `--help` 를 경로로 읽어 2로 끝났고, 2일 때
할 일은 번호를 받는 두 스킬 가운데 `code-review` 에만 있었다(일지 2026-10-12-32·2026-10-13-61).

쓰임: `uv run python tools/sibling_overlap.py [저장소 안의 경로] [--move]`. 먼저 `origin`의 main과
열린 PR의 head를 fetch한다(`origin/main`이 움직인다). 종료 코드는 번호 겹침도, main보다 앞선
새 일지도, 판을 올리지 않고 고친 헌법 파일도, 카나리아 명세를 고치지 않고 바꾼 하네스 파일도
없으면 0, 있으면 1, 대조나 옮기기를 끝내지 못하면(git 실패, 원격을 읽지 못함, 번호의 자리가 빔,
옮길 자리에 무엇이 있음, 인자가 틀림) 2다. 1이면 출력대로 고친다. 겹쳤거나 앞섰으면 이 브랜치가
비켜 간다. 출력의 "옮길 번호"는 겹친 종류(일지는 날짜마다)의 이 브랜치 새 번호 전부를 차례를
지켜 형제들의 최대값 뒤로 붙인 것이다(일지 2026-10-07-09가 03~07을 05~09로 옮긴 모양). main보다
앞선 새 일지가 있으면 일지는 날짜마다가 아니라 새 일지 전부를 다음 빈 일지 번호부터 차례대로
붙인다. 헌법 판은 고르지 않는다. 올림의 종류(major·minor·patch)는 바뀐 내용이 정하고, 형제가 쓴
가장 높은 판보다 높으면 된다.

못 보는 것:
- merge ref로 가릴 때(`gh`를 쓰지 못할 때), 열 때부터 main과 충돌한 PR. 웹 검색 요약이
  그런 PR에는 merge ref가 없고 merge ref는 GitHub이 문서로 약속하지 않은 기능이라고 했다
  (drone 포럼 글, 원문은 이 컨테이너의 egress가 막아 열지 못했다). 재지 않았다. 재려면 이
  저장소에 충돌하는 PR을 하나 열어야 한다. 그 PR의 head에 있는 워크트리는 닫힌 PR의 것으로 접혀
  커밋한 변경을 견주지 않는다.
- PR이 닫힌 워크트리 가운데 HEAD가 그 head와 다른 것. head 뒤에 커밋을 더한 워크트리는 새 일이라
  접지 않는 것이 맞지만, head까지 따라가지 않은(head의 조상에 남은) 워크트리도 접지 않아 이미
  병합된 커밋이 함께 고친 파일에 나온다.
- 헌법 판을 merge-base의 판에서 바꿨는지만 본다. 그보다 낮게 고쳐도, 올림의 종류가 바뀐 내용에
  맞지 않아도(원칙을 바꾸고 patch로 올려도) 지나간다. 헌법 README의 판 줄 밖 문장(색인)과 세 파일
  밖의 새 헌법 파일은 고쳐도 알리지 않는다.
- 푸시했지만 PR을 열지 않은 브랜치, 다른 기계·다른 클라우드 세션의 커밋하지 않은 변경.
- main을 이미 들여 작업 트리 안에서 같은 번호가 둘이 된 것. 둘 다 merge-base에 있거나 merge-base에
  든 번호와 같아 "새로"가 아니다. 일지는 `tests/test_journal_names.py`, ADR은
  `tools/check_adr_pointers.py`가 본다.
- `--move` 가 옮기지 못하는 인용. 줄인 꼴("일지 03"), 꼴의 낱말 없이 든 번호("새로 연 것은
  250·251"), 커밋 메시지와 PR 본문, 번호 뒤의 조사(받침에 따라 갈리는 을·를), 심볼릭 링크인
  파일(따라가 쓰지 않는다)은 그대로다. 인용 블록에서 `>` 없이 이어지는 줄은 옮긴다. 거꾸로 같은
  꼴이면 뜻을 가리지 않고 이 브랜치의 번호로 읽어 옮긴다. 이 브랜치가 더하거나 고친 줄에서 형제의
  같은 번호를 가리킨 인용도 옮긴다. 거꾸로 이 브랜치의 번호를 가리켰어도 merge-base 나 main 의 판에
  같은 글자의 줄이 있으면 둔다.
- 인덱스. 대조는 작업 트리를 읽으므로, `--move` 뒤 옛 이름의 지움을 스테이지하지 않고 커밋해 옛
  일지가 커밋에 남아도 0으로 끝난다.
- 카나리아 명세가 고친 단락을 묻는지. 그 하네스 파일을 원천으로 든 명세 하나를 이 브랜치가
  고쳤으면 지나가고, 명세를 고친 뒤 하네스를 다시 고친 것도 지나간다. `CLAUDE.md`, 스킬 폴더의
  `SKILL.md` 밖 파일, 훅 설정(`.claude/settings.json`)은 보지 않는다. 읽지 못한 명세(TOML 오류,
  글자가 아닌 `source`)는 원천이 없는 것으로 보아, 그 명세만 고친 하네스 파일도 알린다.
- 함께 고친 파일의 어느 줄이 겹치는지. 파일 이름만 견준다.
- 이 브랜치가 고쳤어도 main 과 내용이 같아진 파일(main 의 같은 변경을 손으로 옮긴 것). 이 브랜치가
  고친 파일로 세지 않는다.
- 다음 빈 번호나 가장 높은 헌법 판을 받은 뒤에 다른 세션이 같은 번호를 쓰는 것. 그 순간의
  형제만 본다. 그 뒤의 겹침은 커밋 직전의 대조가 잡는다. 이 브랜치의 판이 형제가 쓴 판보다 낮은
  것은 그 줄에 찍히기만 하고 종료 코드를 바꾸지 않는다. 그 형제가 판을 새로 올렸으면 둘이 같은 판
  줄을 고쳐, 나중에 병합하는 쪽에서 글자 충돌로 드러난다.
- 다른 시간대의 세션과 갈리는 "오늘". 오늘은 이 기계의 지역 날짜다. 더 늦은 날짜로 쓴 형제의
  일지가 먼저 병합되면 main과의 이름순 대조가 잡는다.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path, PurePosixPath
from typing import NoReturn, Protocol

REMOTE = "origin"
BRANCH = "main"
MAIN = f"{REMOTE}/{BRANCH}"
JOURNAL_DIR = "docs/journal"
ADR_DIR = "docs/adr"
QUEUE = ".scratch/retro-queue.md"
CONSTITUTION = "docs/constitution/README.md"
# 판을 올려야 하는 헌법 파일. 어느 변경이든 판을 올린다(`principles.md` 거버넌스의 semver)
CONSTITUTION_TEXTS = frozenset(
    f"docs/constitution/{name}.md" for name in ("principles", "tech", "operations")
)

JOURNAL_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2}-\d{2})-.+\.md$")
ADR_NAME = re.compile(r"^(\d{4})-.+\.md$")
QUEUE_ROW = re.compile(r"^\| (\d+) \|")
VERSION = re.compile(r"\*\*Version\*\*: (\d+\.\d+\.\d+)")
PULL_REF = re.compile(r"^refs/pull/(\d+)/(head|merge)$")
GITHUB_URL = re.compile(r"github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$")
GH_PULL = re.compile(r"^(\d+) ([0-9a-f]{40})$")
GH_JQ = r'.[] | "\(.number) \(.head.sha)"'

CANARY_SPECS = ".scratch/**/probes/canary/*.toml"
# 새 `claude -p` 세션에서 불러 보는 하네스 파일(`docs/constitution/operations.md` 환경 규약 상세)
HARNESS = re.compile(r"^\.claude/(?:skills/[^/]+/SKILL|rules/[^/]+|agents/[^/]+)\.md$")

# `--move` 가 옮기는 인용의 꼴. 갈래 하나로 묶어 한 번에 바꾼다(차례대로 옮기는 사슬이 두 번 가지
# 않게). 같은 자리에서는 앞 갈래가 이긴다(일지 순번이 ADR 파일 이름 꼴보다 먼저다). 맨 앞 갈래는
# 인용 블록의 줄을 통째로 먹어, 그 안의 번호가 다른 갈래에 걸리지 않고 `rewrite` 의 마지막 줄에서
# 그대로 돌아간다
_CITATIONS = (
    r"^(?P<quote>>[^\n]*)"
    r"|(?<!\d)(?P<journal>\d{4}-\d{2}-\d{2}-\d{2})(?!\d)"
    r"|^# (?P<day>\d{4}-\d{2}-\d{2}) \((?P<seq>\d{2})\)"
    r"|(?<=ADR )(?P<adrs>\d{4}(?:·\d{4})*)(?!\d)"
    r"|(?<![\w.])(?P<adr>\d{4})(?=-[a-z0-9]|\])"
    r"|(?<=대기열 )(?P<rows>\d+(?:·\d+)*)(?!\d)"
)
CITATION = re.compile(_CITATIONS, re.MULTILINE)
# 대기열 행의 머리. 일지의 다른 표에도 같은 꼴이 있어 대기열 파일에서만 바꾼다
QUEUE_CITATION = re.compile(_CITATIONS + r"|^\| (?P<row>\d+) \|", re.MULTILINE)
BOM = chr(0xFEFF)

NETWORK_TIMEOUT = 120
LOCAL_TIMEOUT = 30
ROW_WIDTH = 40
SHALLOW_HINT = "얕은 클론이면 `git fetch --unshallow origin` 뒤 다시 친다"

USAGE = (
    "이 브랜치가 새로 매긴 번호(일지 순번, ADR, 대기열 행, 헌법 판)와 고친 파일을 형제(origin/main,"
    " 열린 PR, 형제 워크트리)와 대조하고 다음 빈 번호를 낸다. 바꾼 하네스 파일의 카나리아 명세를"
    " 고치지 않았으면 알린다. 먼저 origin 의 main 과 열린 PR 의 head 를 fetch 한다. 판정의 근거와"
    " 못 보는 것은 이 파일의 독스트링에 있다."
)
EXITS = (
    "종료 코드: 0 고칠 것이 없다(함께 고친 파일과 앞서는 형제는 알리기만 한다). 1 출력대로"
    " 고친다(번호 겹침, main 보다 앞선 새 일지, 판을 올리지 않고 고친 헌법 파일, 카나리아 명세를"
    " 고치지 않고 바꾼 하네스 파일). 2 대조하거나 옮기지 못했거나 인자가 틀렸다(stderr 의 할 일을"
    " 따른다)."
)
# 2로 끝날 때 stderr 에 함께 싣는 할 일(대기열 251)
ON_FAILURE = (
    "할 일: 번호(일지 순번, ADR, 대기열 행, 헌법 판)를 손으로 고르지 않는다. 형제를 넘은"
    " 번호인지 알 수 없다. 원인을 고쳐 다시 친다. 일지 파일이 아직 없으면 그동안 일지에 옮길 것은"
    " 스크래치 파일에 적어 두고, 번호를 받은 뒤 일지로 옮긴다"
)
# 옮기다 멈추고 다 되돌리지 못했을 때의 할 일. 다시 치면 이미 옮긴 인용이 한 번 더 옮겨진다
ON_STUCK = (
    "할 일: `--move` 를 다시 치지 않는다. 이미 옮긴 인용이 한 번 더 옮겨진다. 위에 든 것을 손으로"
    " 되돌리거나 마저 옮긴 뒤 `--move` 없이 다시 대조한다"
)


class SurveyError(Exception):
    """대조를 끝내지 못했다. git 이 실패했거나, 원격을 읽지 못했거나, 번호의 자리가 비었다."""


class MoveError(Exception):
    """번호를 옮기지 못했고 디스크는 옮기기 전 그대로다. 원인을 고쳐 다시 치면 된다."""


class StuckMoveError(MoveError):
    """번호를 옮기다 멈췄고 고친 것을 다 되돌리지 못했다. 메시지가 남은 것을 든다."""


@dataclass(frozen=True)
class Numbers:
    journals: dict[str, str]  # 순번 → 파일 이름
    adrs: dict[str, str]  # 번호 → 파일 이름
    rows: dict[int, str]  # 행 번호 → 행
    version: str | None


@dataclass(frozen=True)
class Clash:
    kind: str
    key: str
    ours: str
    theirs: str


@dataclass(frozen=True)
class Move:
    kind: str
    old: str
    new: str


@dataclass(frozen=True)
class Sibling:
    label: str
    commit: str
    numbers: Numbers  # 이 형제만 새로 매긴 번호
    changed: frozenset[str] | None  # None 이면 merge-base 가 없어 알 수 없다
    # 이름순 최신 일지 순번. main 은 가진 일지 전체에서(main 을 이미 들인 브랜치에는 main 의 새
    # 번호가 없다), 다른 형제는 새로 매긴 일지에서 고른다(main 의 일지를 그 형제의 것으로 되풀이하지
    # 않게)
    latest: str | None
    # 가장 높은 헌법 판의 후보. `latest` 와 같은 까닭으로 main 은 가진 판, 다른 형제는 새로 매긴 판
    version: str | None
    # HEAD 가 닫힌 PR 의 head 인 워크트리면 그 PR 번호. `changed` 는 커밋하지 않은 변경뿐이다
    closed: int | None = None


@dataclass(frozen=True)
class Survey:
    ours: Numbers  # 이 브랜치가 새로 매긴 번호
    changed: frozenset[str]
    main: Sibling
    others: list[Sibling]  # 열린 PR 과 형제 워크트리
    taken: list[Numbers]  # 이 브랜치 밖의 모든 자리(merge-base, main, 형제)의 번호 전체
    pulls_from: str  # 열린 PR 을 읽은 길(FROM_GH 또는 FROM_MERGE_REF)
    harness: list[str]  # 이 브랜치가 고친 하네스 파일 가운데 지금 있는 것
    specs: dict[str, str | None]  # 카나리아 명세 → 그 `source`

    @property
    def siblings(self) -> list[Sibling]:
        return [self.main, *self.others]


def read_numbers(
    journal_names: list[str], adr_names: list[str], queue: str, constitution: str
) -> Numbers:
    journals = {m.group(1): name for name in journal_names if (m := JOURNAL_NAME.match(name))}
    adrs = {m.group(1): name for name in adr_names if (m := ADR_NAME.match(name))}
    rows = {int(m.group(1)): line for line in queue.splitlines() if (m := QUEUE_ROW.match(line))}
    version = VERSION.search(constitution)
    return Numbers(journals, adrs, rows, version.group(1) if version else None)


def fresh(numbers: Numbers, *known: Numbers) -> Numbers:
    """`known` 어디에도 없는 번호만 남긴다."""
    version = numbers.version
    if version is not None and any(version == other.version for other in known):
        version = None
    journals = {
        k: v for k, v in numbers.journals.items() if all(k not in n.journals for n in known)
    }
    adrs = {k: v for k, v in numbers.adrs.items() if all(k not in n.adrs for n in known)}
    rows = {k: v for k, v in numbers.rows.items() if all(k not in n.rows for n in known)}
    return Numbers(journals, adrs, rows, version)


def unshared(numbers: Numbers, other: Numbers) -> Numbers:
    """`other` 와 같은 번호에 같은 파일·같은 행인 것(공유한 이력)을 뺀다.

    헌법 판은 내용을 가를 수 없어 둔다. 같은 판이 공유한 이력인지 따로 올린 겹침인지 모른다.
    """
    journals = {k: v for k, v in numbers.journals.items() if other.journals.get(k) != v}
    adrs = {k: v for k, v in numbers.adrs.items() if other.adrs.get(k) != v}
    rows = {k: v for k, v in numbers.rows.items() if other.rows.get(k) != v}
    return Numbers(journals, adrs, rows, numbers.version)


def clashes(ours: Numbers, theirs: Numbers) -> list[Clash]:
    """둘 다 새로 매긴 번호 가운데 같은 번호를 다른 것에 쓴 것.

    같은 파일·같은 행은 겹침이 아니라 공유한 이력이다(쌓아 올린 브랜치).
    """
    found: list[Clash] = []
    named = (("일지", ours.journals, theirs.journals), ("ADR", ours.adrs, theirs.adrs))
    for kind, mine, other in named:
        for key in sorted(mine.keys() & other.keys()):
            if mine[key] != other[key]:
                found.append(Clash(kind, key, mine[key], other[key]))
    for row in sorted(ours.rows.keys() & theirs.rows.keys()):
        if ours.rows[row] != theirs.rows[row]:
            found.append(Clash("대기열", str(row), ours.rows[row], theirs.rows[row]))
    if ours.version is not None and ours.version == theirs.version:
        found.append(Clash("헌법", ours.version, ours.version, ours.version))
    return found


def latest_journal(numbers: Numbers) -> str | None:
    """이름순 최신 일지 순번. 순번은 자리 수가 고정이라 문자열 차례가 이름순이다."""
    return max(numbers.journals, default=None)


def is_behind(ours: Numbers, latest: str | None) -> bool:
    """이 브랜치의 새 일지 가운데 이름순 최신 것이 `latest` 보다 앞이다.

    같은 순번은 앞이 아니다. 그것은 겹침이다.
    """
    mine = latest_journal(ours)
    return mine is not None and latest is not None and mine < latest


def journal_day(today: str, main_latest: str | None) -> str:
    """새 일지의 날짜. 오늘이되, main 에 더 늦은 날짜의 일지가 있으면 그 날짜다.

    오늘로 쓰면 main 의 최신 일지보다 이름순으로 앞이 된다.
    """
    return max(today, main_latest[:10]) if main_latest else today


def _top_journal(numbers: list[Numbers], day: str) -> int:
    return max((int(k[11:]) for n in numbers for k in n.journals if k[:10] == day), default=0)


def next_numbers(numbers: list[Numbers], day: str) -> tuple[str, int]:
    """`numbers` 어디에도 없는 다음 일지 순번(`day` 의 가장 큰 순번 다음)과 다음 대기열 행."""
    row = max((k for n in numbers for k in n.rows), default=0)
    return f"{day}-{_top_journal(numbers, day) + 1:02d}", row + 1


def _shift(olds: list[int], top: int) -> list[tuple[int, int]]:
    """`olds` 를 차례대로 `top` 뒤에 붙인다. 자리가 그대로인 것은 뺀다."""
    pairs = [(old, top + 1 + i) for i, old in enumerate(sorted(olds))]
    return [(old, new) for old, new in pairs if old != new]


def moves(ours: Numbers, taken: list[Numbers], found: list[Clash]) -> list[Move]:
    """겹친 종류(일지는 날짜마다)의 이 브랜치 새 번호 전부를 형제들의 최대값 뒤로 옮긴다.

    겹친 번호만 옮기면 이 브랜치의 다른 새 번호와 부딪히거나 일지의 차례가 뒤집힌다.
    헌법 판은 고르지 않는다.
    """
    kinds = {clash.kind for clash in found}
    result: list[Move] = []
    for day in sorted({clash.key[:10] for clash in found if clash.kind == "일지"}):
        olds = [int(key[11:]) for key in ours.journals if key[:10] == day]
        top = _top_journal(taken, day)
        result += [Move("일지", f"{day}-{a:02d}", f"{day}-{b:02d}") for a, b in _shift(olds, top)]
    if "ADR" in kinds:
        top = max((int(k) for n in taken for k in n.adrs), default=0)
        olds = [int(key) for key in ours.adrs]
        result += [Move("ADR", f"{a:04d}", f"{b:04d}") for a, b in _shift(olds, top)]
    if "대기열" in kinds:
        top = max((k for n in taken for k in n.rows), default=0)
        result += [Move("대기열", str(a), str(b)) for a, b in _shift(list(ours.rows), top)]
    return result


def behind_moves(ours: Numbers, taken: list[Numbers], day: str) -> list[Move]:
    """새 일지 전부를 차례대로 `day` 의 형제들의 최대값 뒤로 옮긴다.

    새 일지가 main 의 최신 일지보다 이름순으로 앞일 때의 이동이다. 이때 일지는 날짜 안의 겹침
    이동(`moves`)을 따로 내지 않는다. 내면 같은 일지를 두 자리로 옮기라고 한다.
    """
    top = _top_journal(taken, day)
    return [
        Move("일지", old, f"{day}-{top + 1 + i:02d}") for i, old in enumerate(sorted(ours.journals))
    ]


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def highest_version(held: Sequence[tuple[str, str | None]]) -> tuple[str, list[str]] | None:
    """(자리, 판) 가운데 가장 높은 판과 그 판을 쓴 자리 전부. 판은 글자가 아니라 수로 견준다."""
    versions = [version for _, version in held if version is not None]
    if not versions:
        return None
    top = max(versions, key=_version_key)
    return top, [label for label, version in held if version == top]


def unbumped(changed: frozenset[str], ours: Numbers) -> list[str]:
    """이 브랜치가 판을 새로 매기지 않았는데 고친 헌법 파일."""
    return [] if ours.version is not None else sorted(changed & CONSTITUTION_TEXTS)


def harness_files(paths: Iterable[str]) -> list[str]:
    """`paths` 가운데 카나리아로 불러 보는 하네스 파일(스킬 본문, 규칙, 서브에이전트)."""
    return sorted(path for path in paths if HARNESS.match(path))


def uncanaried(
    harness: Iterable[str], changed: frozenset[str], specs: Mapping[str, str | None]
) -> list[tuple[str, list[str]]]:
    """`harness` 가운데 그 파일을 원천으로 든 카나리아 명세를 이 브랜치가 하나도 고치지 않은 것.

    짝의 뒤는 그 파일을 원천으로 든 명세 전부다(없으면 빈 목록).
    """
    found: list[tuple[str, list[str]]] = []
    for path in harness:
        held = sorted(spec for spec, source in specs.items() if source == path)
        if not any(spec in changed for spec in held):
            found.append((path, held))
    return found


@dataclass(frozen=True)
class Renumber:
    """옮길 번호를 종류마다 옛 번호 → 새 번호로 든다. 대기열 행 번호도 글자다."""

    journals: dict[str, str]
    adrs: dict[str, str]
    rows: dict[str, str]


def renumber(shifted: Iterable[Move]) -> Renumber:
    by_kind: dict[str, dict[str, str]] = {"일지": {}, "ADR": {}, "대기열": {}}
    for move in shifted:
        by_kind[move.kind][move.old] = move.new
    return Renumber(by_kind["일지"], by_kind["ADR"], by_kind["대기열"])


def rewrite(text: str, plan: Renumber, path: str, kept: frozenset[str] = frozenset()) -> str:
    """`plan` 의 옛 번호를 든 인용을 한 번에 새 번호로 바꾼다. `path` 가 대기열 파일이면 행의
    머리도 바꾼다. 인용 블록(`>` 로 시작하는 줄)은 다른 데서 옮겨 온 원문이라 둔다.

    `kept` 와 글자가 같은 줄(줄 끝의 CR 은 빼고 견준다)도 둔다. merge-base 나 main 의 판에 있던
    줄의 같은 번호는 상대를 가리킨다(`.claude/rules/adr.md`). BOM 은 떼고 바꾼 뒤 다시 붙인다.
    BOM 이 `^` 를 막아 일지 머리 줄만 옛 번호에 남았다(PR 직전 버그 축).
    """

    def swap(match: re.Match[str]) -> str:
        found = match.groupdict()
        if (key := found["journal"]) is not None:
            return plan.journals.get(key, key)
        if (day := found["day"]) is not None:
            new = plan.journals.get(f"{day}-{found['seq']}")
            return match[0] if new is None else f"# {new[:10]} ({new[11:]})"
        if (adrs := found["adrs"]) is not None:
            return "·".join(plan.adrs.get(number, number) for number in adrs.split("·"))
        if (adr := found["adr"]) is not None:
            return plan.adrs.get(adr, adr)
        if (rows := found["rows"]) is not None:
            return "·".join(plan.rows.get(number, number) for number in rows.split("·"))
        row = found.get("row")
        return f"| {plan.rows[row]} |" if row is not None and row in plan.rows else match[0]

    pattern = QUEUE_CITATION if path == QUEUE else CITATION
    bom = BOM if text.startswith(BOM) else ""
    lines = text[len(bom) :].split("\n")
    return bom + "\n".join(
        line if line.rstrip("\r") in kept else pattern.sub(swap, line) for line in lines
    )


@dataclass(frozen=True)
class MovePlan:
    renames: list[tuple[str, str]]  # 저장소 기준 옛 경로 → 새 경로
    texts: dict[str, str]  # 고칠 파일(옛 경로) → 고친 글
    originals: dict[str, bytes]  # 고칠 파일(옛 경로) → 고치기 전 바이트. 멈추면 되돌린다


def plan_moves(
    root: Path,
    ours: Numbers,
    shifted: Sequence[Move],
    changed: Iterable[str],
    kept: Mapping[str, frozenset[str]] | None = None,
) -> MovePlan:
    """옮길 번호대로 바꿀 파일 이름과, `changed` 가운데 인용을 고칠 파일의 글을 짓는다.

    디스크는 읽기만 한다. 옮길 자리에 무엇이 있거나 파일을 읽지 못하면 MoveError 다. 옮길 자리가
    이 브랜치의 다른 옮길 파일이면(같은 슬러그의 사슬) 그 파일을 먼저 옮기는 차례로 둔다. 심볼릭
    링크는 따라가 쓰지 않는다. 반박 검증에서 저장소 밖을 가리키는 링크를 따라가 밖의 파일을
    고쳤다(일지 2026-10-14-04). `kept` 는 파일마다 두는 줄이다(`rewrite`).
    """
    plan = renumber(shifted)
    renames: list[tuple[str, str]] = []
    named = ((JOURNAL_DIR, ours.journals, plan.journals), (ADR_DIR, ours.adrs, plan.adrs))
    for directory, names, mapping in named:
        for old, new in mapping.items():
            name = names[old]
            renames.append((f"{directory}/{name}", f"{directory}/{new}{name[len(old) :]}"))
    sources = {source for source, _ in renames}
    for _, target in renames:
        if target not in sources and (root / target).exists():
            raise MoveError(f"옮길 자리 {target} 에 이미 무엇이 있다. 아무것도 고치지 않았다")
    texts: dict[str, str] = {}
    originals: dict[str, bytes] = {}
    for path in sorted(changed):
        file = root / path
        if file.is_symlink() or not file.is_file():
            continue
        try:
            raw = file.read_bytes()
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue  # 글이 아니다
        except OSError as error:
            raise MoveError(f"{path} 를 읽지 못했다({error}). 아무것도 고치지 않았다") from error
        lines = (kept or {}).get(path, frozenset())
        if (changed_text := rewrite(text, plan, path, lines)) != text:
            texts[path] = changed_text
            originals[path] = raw
    return MovePlan(vacating_first(renames), texts, originals)


def vacating_first(renames: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """옮길 자리를 비켜 줄 이름 바꾸기를 먼저 둔다.

    옮김은 정렬한 옛 번호를 차례대로 붙인 것이라 서로 자리를 맞바꾸는 순환이 없다. 그래서 자리가
    빈 것부터 고르면 끝난다. 순환이 들어오면 끝나지 않는 대신 MoveError 다.
    """
    pending = list(renames)
    ordered: list[tuple[str, str]] = []
    while pending:
        sources = {source for source, _ in pending}
        ready = [pair for pair in pending if pair[1] not in sources]
        if not ready:
            raise MoveError(
                f"서로 자리를 맞바꾸는 이름 바꾸기가 있다: {pending}. 아무것도 고치지 않았다"
            )
        ordered += ready
        pending = [pair for pair in pending if pair not in ready]
    return ordered


def apply_moves(root: Path, plan: MovePlan) -> None:
    """글을 먼저 고치고 이름을 바꾼다. 인덱스는 건드리지 않는다.

    도중에 멈추면 바꾼 이름과 쓴 글을 거꾸로 되돌린다. 되돌리지 않고 다시 치면 이미 옮긴 인용이
    차례대로 옮기는 사슬(03→05, 05→06)을 따라 한 번 더 옮겨진다(셀프 리뷰 표준 축, 일지
    2026-10-14-04). 다 되돌렸으면 MoveError, 되돌리지 못한 것이 있으면 StuckMoveError 다.
    """
    written: list[str] = []
    renamed: list[tuple[str, str]] = []
    try:
        for path, text in plan.texts.items():
            # 쓰기 전에 올린다. `write_bytes` 는 먼저 비우고 써서, 쓰다 멈춘 파일도 되돌릴 것이다
            written.append(path)
            (root / path).write_bytes(text.encode("utf-8"))
        for source, target in plan.renames:
            (root / source).rename(root / target)
            renamed.append((source, target))
    except OSError as error:
        left = _undo(root, plan, written, renamed)
        if left:
            raise StuckMoveError(
                f"옮기다 멈췄고({error}) 되돌리지 못한 것이 있다: {', '.join(left)}"
            ) from error
        raise MoveError(f"옮기다 멈춰({error}) 고친 것을 모두 되돌렸다") from error


def _undo(
    root: Path, plan: MovePlan, written: list[str], renamed: list[tuple[str, str]]
) -> list[str]:
    """바꾼 이름을 거꾸로 되돌리고 쓴 글을 옛 바이트로 되쓴다. 되돌리지 못한 것을 돌려준다.

    이미 옛 바이트인 파일(열지도 못하고 멈춘 파일)은 되쓰지 않는다. 되쓰다 또 실패해 되돌리지 못한
    것으로 들면 `--move` 를 다시 치지 말라는 거짓 할 일이 나간다.
    """
    left: list[str] = []
    stuck: set[str] = set()
    for source, target in reversed(renamed):
        try:
            (root / target).rename(root / source)
        except OSError:
            left.append(f"{target} → {source}")
            stuck.add(source)
    for path in written:
        if path in stuck:
            left.append(path)  # 옛 이름으로 돌아오지 않아 그 자리에 쓰면 사본이 생긴다
            continue
        try:
            if (root / path).read_bytes() != plan.originals[path]:
                (root / path).write_bytes(plan.originals[path])
        except OSError:
            left.append(path)
    return left


def github_repo(url: str) -> tuple[str, str] | None:
    """원격 URL 이 github.com 의 것이면 (owner, repo)."""
    match = GITHUB_URL.search(url.strip())
    return (match.group(1), match.group(2)) if match else None


def gh_pulls(text: str) -> dict[int, str]:
    """`gh api … --jq` 가 낸 "번호 head" 줄에서 열린 PR 의 번호 → head 커밋."""
    found: dict[int, str] = {}
    for line in text.splitlines():
        match = GH_PULL.match(line.strip())
        if match:
            found[int(match.group(1))] = match.group(2)
    return dict(sorted(found.items()))


def open_pulls(listing: str) -> dict[int, str]:
    """`git ls-remote` 의 `refs/pull/*` 줄에서 merge ref 가 있는 PR 의 번호 → head 커밋."""
    heads: dict[int, str] = {}
    merges: set[int] = set()
    for line in listing.splitlines():
        sha, _, ref = line.partition("\t")
        match = PULL_REF.match(ref.strip())
        if match is None:
            continue
        number = int(match.group(1))
        if match.group(2) == "head":
            heads[number] = sha.strip()
        else:
            merges.add(number)
    return {number: heads[number] for number in sorted(merges) if number in heads}


def closed_heads(listing: str, pulls: dict[int, str]) -> dict[str, int]:
    """`git ls-remote` 의 `refs/pull/*/head` 줄에서 열린 PR(`pulls`)이 아닌 PR 의 head → 번호.

    열린 PR 의 head 와 같은 커밋은 뺀다. 한 커밋을 head 로 든 닫힌 PR 이 여럿이면 큰 번호다.
    """
    opened = set(pulls.values())
    found: dict[str, int] = {}
    for line in listing.splitlines():
        sha, _, ref = line.partition("\t")
        match = PULL_REF.match(ref.strip())
        if match is None or match.group(2) != "head":
            continue
        number, sha = int(match.group(1)), sha.strip()
        if number not in pulls and sha not in opened:
            found[sha] = max(number, found.get(sha, 0))
    return found


def remote_head(listing: str, branch: str) -> str | None:
    """`git ls-remote` 줄에서 원격 브랜치 `branch` 의 커밋."""
    for line in listing.splitlines():
        sha, _, ref = line.partition("\t")
        if ref.strip() == f"refs/heads/{branch}":
            return sha.strip()
    return None


def worktrees(porcelain: str) -> list[tuple[str, str]]:
    """`git worktree list --porcelain` 에서 (경로, HEAD). bare 와 사라진(prunable) 것은 뺀다."""
    found: list[tuple[str, str]] = []
    for block in re.split(r"\n\s*\n", porcelain.strip()):
        fields: dict[str, str] = {}
        for line in block.splitlines():
            name, _, value = line.partition(" ")
            fields[name] = value
        if "bare" in fields or "prunable" in fields:
            continue
        if "worktree" in fields and "HEAD" in fields:
            found.append((fields["worktree"], fields["HEAD"]))
    return found


def _run(command: list[str], cwd: Path, timeout: float) -> subprocess.CompletedProcess[str] | None:
    """명령을 띄운다. 띄우지 못하거나 시간을 넘기면 None."""
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _git_result(
    cwd: Path, args: tuple[str, ...], timeout: float
) -> subprocess.CompletedProcess[str]:
    result = _run(["git", "-c", "core.quotepath=false", *args], cwd, timeout)
    if result is None:
        raise SurveyError(f"git {args[0]} 을 띄우지 못했거나 {timeout}초를 넘겼다")
    return result


def git(cwd: Path, *args: str, timeout: float = LOCAL_TIMEOUT) -> str:
    result = _git_result(cwd, args, timeout)
    if result.returncode != 0:
        raise SurveyError(f"git {args[0]} (종료 {result.returncode}): {result.stderr.strip()}")
    return result.stdout


def is_ancestor(root: Path, commit: str, of: str) -> bool:
    result = _git_result(root, ("merge-base", "--is-ancestor", commit, of), LOCAL_TIMEOUT)
    if result.returncode > 1:
        raise SurveyError(f"git merge-base --is-ancestor: {result.stderr.strip()}")
    return result.returncode == 0


def merge_base(root: Path, one: str, other: str) -> str | None:
    """두 커밋의 merge-base. 이 클론에 공통 조상이 없으면(얕은 클론) None."""
    result = _git_result(root, ("merge-base", one, other), LOCAL_TIMEOUT)
    if result.returncode == 1:
        return None
    if result.returncode != 0:
        raise SurveyError(f"git merge-base: {result.stderr.strip()}")
    return result.stdout.strip()


def current_branch(root: Path) -> str | None:
    """지금 브랜치의 이름. detached HEAD 면 None."""
    result = _git_result(root, ("symbolic-ref", "--quiet", "--short", "HEAD"), LOCAL_TIMEOUT)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def gh_listing(root: Path, owner: str, repo: str) -> str | None:
    """`gh api` 로 읽은 열린 PR 의 "번호 head" 줄. gh 가 없거나 실패하면 None."""
    gh = shutil.which("gh")
    if gh is None:
        return None
    endpoint = f"repos/{owner}/{repo}/pulls?state=open&per_page=100"
    result = _run([gh, "api", endpoint, "--paginate", "--jq", GH_JQ], root, NETWORK_TIMEOUT)
    return result.stdout if result is not None and result.returncode == 0 else None


class Snapshot(Protocol):
    def names(self, directory: str) -> list[str]: ...

    def text(self, path: str) -> str: ...


@dataclass(frozen=True)
class Tree:
    """커밋 하나의 트리."""

    root: Path
    commit: str

    def names(self, directory: str) -> list[str]:
        listing = git(self.root, "ls-tree", "--name-only", self.commit, "--", f"{directory}/")
        return [PurePosixPath(line).name for line in listing.splitlines()]

    def text(self, path: str) -> str:
        if not git(self.root, "ls-tree", "--name-only", self.commit, "--", path).strip():
            return ""  # 그 커밋에 파일이 없다
        return git(self.root, "show", f"{self.commit}:{path}")


@dataclass(frozen=True)
class Disk:
    """작업 트리. 커밋하지 않은 변경과 미추적 파일까지 든다."""

    root: Path

    def names(self, directory: str) -> list[str]:
        folder = self.root / directory
        if not folder.is_dir():
            return []
        return sorted(path.name for path in folder.iterdir() if path.is_file())

    def text(self, path: str) -> str:
        file = self.root / path
        return file.read_text(encoding="utf-8", errors="replace") if file.is_file() else ""


def numbers_of(snapshot: Snapshot) -> Numbers:
    return read_numbers(
        snapshot.names(JOURNAL_DIR),
        snapshot.names(ADR_DIR),
        snapshot.text(QUEUE),
        snapshot.text(CONSTITUTION),
    )


def canary_sources(root: Path) -> dict[str, str | None]:
    """디스크의 카나리아 명세(저장소 기준 경로) → 그 `source`. 읽지 못했거나 글자가 아니면 None."""
    found: dict[str, str | None] = {}
    for file in sorted(root.glob(CANARY_SPECS)):
        try:
            source: object = tomllib.loads(file.read_text(encoding="utf-8")).get("source")
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
            source = None
        found[file.relative_to(root).as_posix()] = source if isinstance(source, str) else None
    return found


def empty_places(numbers: Numbers) -> list[str]:
    places = (
        (JOURNAL_DIR, not numbers.journals),
        (ADR_DIR, not numbers.adrs),
        (QUEUE, not numbers.rows),
        (CONSTITUTION, numbers.version is None),
    )
    return [place for place, empty in places if empty]


def _lines(text: str) -> frozenset[str]:
    return frozenset(line for line in text.splitlines() if line)


def _worktree_changes(path: Path, since: str) -> frozenset[str]:
    """작업 트리가 `since` 뒤에 고친 파일. 미추적 파일을 더한다."""
    tracked = git(path, "diff", "--name-only", since)
    untracked = git(path, "ls-files", "--others", "--exclude-standard")
    return _lines(tracked) | _lines(untracked)


def _own_changes(root: Path, base: str, main_sha: str) -> frozenset[str]:
    """이 작업 트리가 merge-base 뒤에 고친 파일 가운데 main 과 내용이 다른 것. 미추적 파일을 더한다.

    main 과 같은 파일은 main 이 들여온 것이다. 합치기를 커밋하기 전에는 merge-base 가 옛 자리에
    머물러 main 이 고친 파일이 모두 섞였고, 카나리아 누락이 main 의 규칙과 스킬을 알렸다(일지
    2026-10-14-04).
    """
    since_base = _lines(git(root, "diff", "--name-only", base))
    unlike_main = _lines(git(root, "diff", "--name-only", main_sha))
    untracked = _lines(git(root, "ls-files", "--others", "--exclude-standard"))
    return (since_base & unlike_main) | untracked


FROM_GH = "gh api"
FROM_MERGE_REF = "merge ref"


@dataclass(frozen=True)
class Remote:
    """원격에서 읽은 것. 열린 PR(번호 → head), 그것을 읽은 길, 이 브랜치의 원격 커밋, 닫힌 PR."""

    pulls: dict[int, str]
    pulls_from: str  # FROM_GH 또는 FROM_MERGE_REF
    own_head: str | None
    closed: dict[str, int]  # 닫힌 PR 의 head → 번호


def read_remote(root: Path) -> Remote:
    """열린 PR, 이 브랜치의 원격 커밋, 닫힌 PR 의 head 를 읽는다. 로컬의 ref 는 움직이지 않는다."""
    branch = current_branch(root)
    patterns = ["refs/pull/*/head", "refs/pull/*/merge"]
    patterns += [f"refs/heads/{branch}"] if branch else []
    listing = git(root, "ls-remote", REMOTE, *patterns, timeout=NETWORK_TIMEOUT)
    repo = github_repo(git(root, "remote", "get-url", REMOTE))
    from_gh = gh_listing(root, *repo) if repo else None
    if from_gh is not None:
        pulls, pulls_from = gh_pulls(from_gh), FROM_GH
    else:
        pulls, pulls_from = open_pulls(listing), FROM_MERGE_REF
    own = remote_head(listing, branch) if branch else None
    return Remote(pulls, pulls_from, own, closed_heads(listing, pulls))


def fetch(root: Path, pulls: dict[int, str]) -> None:
    """main 을 `origin/main` 으로 당기고, 열린 PR 의 head 를 ref 없이 받는다."""
    git(
        root,
        "fetch",
        "--quiet",
        "--no-tags",
        "--no-write-fetch-head",
        REMOTE,
        f"+refs/heads/{BRANCH}:refs/remotes/{MAIN}",
        *(f"refs/pull/{number}/head" for number in pulls),
        timeout=NETWORK_TIMEOUT,
    )


def survey(root: Path, remote: Remote) -> Survey:
    """fetch 가 끝난 클론에서 이 브랜치와 형제의 번호와 고친 파일을 읽는다."""
    main_sha = git(root, "rev-parse", MAIN).strip()
    base = merge_base(root, "HEAD", main_sha)
    if base is None:
        raise SurveyError(f"이 브랜치와 {MAIN} 의 merge-base 가 이 클론에 없다. {SHALLOW_HINT}")
    base_numbers = numbers_of(Tree(root, base))
    if missing := empty_places(base_numbers):
        raise SurveyError(f"merge-base 에서 번호의 자리가 비었다: {', '.join(missing)}")
    main_numbers = numbers_of(Tree(root, main_sha))
    main_changed = _lines(git(root, "diff", "--name-only", base, main_sha))
    main_new = fresh(main_numbers, base_numbers)
    main_sibling = Sibling(
        label=MAIN,
        commit=main_sha,
        numbers=main_new,
        changed=main_changed,
        latest=latest_journal(main_numbers),
        version=main_numbers.version,
    )
    others: list[Sibling] = []
    taken = [base_numbers, main_numbers]

    def add(
        label: str,
        head: str,
        numbers: Numbers,
        changed: frozenset[str] | None,
        closed: int | None = None,
    ) -> None:
        new = fresh(numbers, base_numbers, main_numbers)
        others.append(
            Sibling(
                label=label,
                commit=head,
                numbers=new,
                changed=changed,
                latest=latest_journal(new),
                version=new.version,
                closed=closed,
            )
        )
        taken.append(numbers)

    for number, head in remote.pulls.items():
        if head == remote.own_head or is_ancestor(root, head, "HEAD"):
            continue
        since = merge_base(root, head, main_sha)
        changed = _lines(git(root, "diff", "--name-only", since, head)) if since else None
        add(f"PR #{number}", head, numbers_of(Tree(root, head)), changed)
    for location, head in worktrees(git(root, "worktree", "list", "--porcelain")):
        path = Path(location).resolve()
        if path == root or not path.is_dir():
            continue
        numbers = numbers_of(Disk(path))
        if (closed := remote.closed.get(head)) is not None:
            # 커밋한 변경은 병합됐거나 앞으로 병합되지 않아 충돌 후보가 아니다(대기열 194)
            label = f"워크트리 {path}(PR #{closed} 닫힘)"
            add(label, head, numbers, _worktree_changes(path, head), closed)
            continue
        since = merge_base(root, head, main_sha)
        changed = _worktree_changes(path, since) if since else None
        add(f"워크트리 {path}", head, numbers, changed)
    ours = unshared(fresh(numbers_of(Disk(root)), base_numbers), main_numbers)
    changed = _own_changes(root, base, main_sha)
    harness = [path for path in harness_files(changed) if (root / path).is_file()]
    return Survey(
        ours,
        changed,
        main_sibling,
        others,
        taken,
        remote.pulls_from,
        harness,
        canary_sources(root),
    )


def findings(result: Survey) -> list[tuple[Sibling, Clash]]:
    return [
        (sibling, clash)
        for sibling in result.siblings
        for clash in clashes(result.ours, sibling.numbers)
    ]


def _short(text: str) -> str:
    return text if len(text) <= ROW_WIDTH else text[: ROW_WIDTH - 1] + "…"


def _describe(clash: Clash) -> str:
    if clash.kind == "헌법":
        return "이 브랜치와 그쪽이 같은 판으로 올렸다"
    if clash.kind == "대기열":
        return f"이 브랜치 `{_short(clash.ours)}`, 그쪽 `{_short(clash.theirs)}`"
    return f"이 브랜치 {clash.ours}, 그쪽 {clash.theirs}"


_PULLS_FROM = {FROM_GH: "gh api", FROM_MERGE_REF: "merge ref(gh api 를 쓰지 못했다)"}


def _ours_line(ours: Numbers) -> str:
    keys = [f"일지 {key}" for key in sorted(ours.journals)]
    keys += [f"ADR {key}" for key in sorted(ours.adrs)]
    keys += [f"대기열 {key}" for key in sorted(ours.rows)]
    keys += [f"헌법 {ours.version}"] if ours.version else []
    return f"이 브랜치의 새 번호: {', '.join(keys)}" if keys else "이 브랜치의 새 번호 없음"


@dataclass(frozen=True)
class Verdict:
    """출력과 종료 코드가 함께 읽는 판정. 한 번만 지어 둘이 어긋나지 않게 한다."""

    found: list[tuple[Sibling, Clash]]
    next_journal: str
    next_row: int
    behind: bool  # 이 브랜치의 새 일지가 main 의 최신 일지보다 이름순으로 앞이다
    shifted: list[Move]
    later: list[Sibling]  # 이 브랜치의 새 일지보다 이름순으로 뒤인 일지를 새로 매긴 다른 형제
    top_version: tuple[str, list[str]] | None  # 형제가 쓴 가장 높은 헌법 판과 그 자리
    unbumped: list[str]  # 판을 올리지 않고 고친 헌법 파일
    # 카나리아 명세를 고치지 않고 바꾼 하네스 파일과 그 파일을 원천으로 든 명세
    uncanaried: list[tuple[str, list[str]]]

    @property
    def code(self) -> int:
        return 1 if self.found or self.behind or self.unbumped or self.uncanaried else 0


def judge(result: Survey, today: str) -> Verdict:
    found = findings(result)
    day = journal_day(today, result.main.latest)
    journal, row = next_numbers([*result.taken, result.ours], day)
    behind = is_behind(result.ours, result.main.latest)
    clashed = [clash for _, clash in found]
    if behind:
        shifted = behind_moves(result.ours, result.taken, day)
        shifted += moves(result.ours, result.taken, [c for c in clashed if c.kind != "일지"])
    else:
        shifted = moves(result.ours, result.taken, clashed)
    later = [s for s in result.others if is_behind(result.ours, s.latest)]
    top = highest_version([(s.label, s.version) for s in result.siblings])
    return Verdict(
        found,
        journal,
        row,
        behind,
        shifted,
        later,
        top,
        unbumped(result.changed, result.ours),
        uncanaried(result.harness, result.changed, result.specs),
    )


def _siblings_line(siblings: list[Sibling]) -> str:
    shown = [f"{s.label} {s.commit[:7]}" for s in siblings if s.closed is None]
    if folded := sum(1 for s in siblings if s.closed is not None):
        shown.append(f"PR 이 닫힌 워크트리 {folded}곳(커밋하지 않은 변경만 견준다)")
    return "형제: " + ", ".join(shown)


def _reserve_line(journal: str) -> str:
    """받은 일지 번호로 바로 파일을 만들라는 안내(대기열 205·220)."""
    return (
        f"일지를 쓸 세션이면 다른 일보다 먼저 {JOURNAL_DIR}/{journal}-<슬러그>.md 를 머리 한 줄"
        f"(# {journal[:10]} ({journal[11:]}) <제목>)로 만든다. 형제의 이 대조는 디스크의 일지"
        " 파일로 찬 번호를 본다. 이 대조가 2로 끝난 동안 스크래치 파일에 적어 둔 것이 있으면 만든"
        " 일지로 옮긴다"
    )


def render(result: Survey, verdict: Verdict) -> str:
    mine = latest_journal(result.ours)
    lines = [
        _siblings_line(result.siblings),
        f"열린 PR 을 읽은 길: {_PULLS_FROM[result.pulls_from]}",
        f"다음 빈 번호(형제 포함): 일지 {verdict.next_journal}, 대기열 {verdict.next_row}",
    ]
    if not result.ours.journals:
        lines.append(_reserve_line(verdict.next_journal))
    if verdict.top_version:
        version, labels = verdict.top_version
        lines.append(
            f"형제가 쓴 가장 높은 헌법 판: {version}({', '.join(labels)})."
            " 판을 올리면 이보다 높게 고른다"
        )
    lines.append(_ours_line(result.ours))
    if verdict.found:
        lines.append(f"번호 겹침 {len(verdict.found)}:")
        lines += [f"- {s.label} {c.kind} {c.key}: {_describe(c)}" for s, c in verdict.found]
    else:
        lines.append("번호 겹침 없음")
    if verdict.unbumped:
        lines.append(
            f"헌법 파일을 고치고 판을 올리지 않았다: {', '.join(verdict.unbumped)}."
            " 위의 가장 높은 판보다 높게 올린다(원칙 변경은 major, 절 추가는 minor,"
            " 문구 수정은 patch)"
        )
    if verdict.uncanaried:
        lines.append(
            "카나리아 명세를 이 브랜치에서 고치지 않고 바꾼 하네스 파일. 새 `claude -p` 세션에서"
            " 불러 보고(`tools/canary.py`) 그 명세의 `# 최신 결과:` 줄을 고친다. 그 파일을 원천으로"
            " 든 명세가 없으면 새로 쓴다(docs/constitution/operations.md 환경 규약 상세). 계정"
            " 한도로 돌리지 못하면 그 절의 계정 한도 항목대로 사전 확인만 돌리고 이 알림이 남은 채"
            " 커밋한다:"
        )
        for path, specs in verdict.uncanaried:
            names = ", ".join(PurePosixPath(spec).name for spec in specs) or "명세 없음"
            lines.append(f"- {path}: {names}")
    if verdict.behind:
        lines.append(
            f"이 브랜치의 새 일지 {mine} 이 {MAIN} 의 최신 일지 {result.main.latest} 보다"
            ' 이름순으로 앞이다. 다음 세션이 이름순 최신 일지의 "다음" 을 읽어 이 일지를 지나친다'
        )
    if verdict.shifted:
        moved = ", ".join(f"{m.kind} {m.old} → {m.new}" for m in verdict.shifted)
        lines.append(f"옮길 번호: {moved}")
        lines.append(
            "`--move` 를 붙여 다시 치면 이 번호대로 일지·ADR 의 파일 이름과 일지 머리 줄, 이"
            " 브랜치의 변경과 미추적 파일 안의 인용을 옮긴다"
        )
    if verdict.later:
        lines.append(
            f"이 브랜치의 새 일지 {mine} 를 이름순으로 앞서는 형제"
            "(그쪽이 먼저 병합되면 옮긴다, 종료 코드와 무관):"
        )
        lines += [f"- {s.label}: {s.latest}" for s in verdict.later]
    shared: list[str] = []
    for sibling in result.siblings:
        if sibling.changed is None:
            shared.append(f"- {sibling.label}: 알 수 없다(merge-base 가 없다. {SHALLOW_HINT})")
        elif paths := sorted(result.changed & sibling.changed):
            shared.append(f"- {sibling.label}: {', '.join(paths)}")
    if shared:
        lines.append("함께 고친 파일(나중에 병합하는 쪽에서 글자 충돌 후보, 종료 코드와 무관):")
        lines += shared
    else:
        lines.append("함께 고친 파일 없음")
    return "\n".join(lines)


def _moved_line(shifted: Sequence[Move], plan: MovePlan) -> str:
    renamed = dict(plan.renames)
    moved = ", ".join(f"{m.kind} {m.old} → {m.new}" for m in shifted)
    names = ", ".join(f"{old} → {new}" for old, new in plan.renames) or "없음"
    texts = ", ".join(sorted(renamed.get(path, path) for path in plan.texts)) or "없음"
    return (
        f"옮겼다: {moved}. 이름을 바꾼 파일: {names}. 인용을 고친 파일: {texts}. 스테이지하지"
        ' 않았으니 옛 이름의 지움까지 함께 스테이지한다(`git add -A`). 줄인 꼴("일지 03"), 낱말'
        " 없이 든 번호, 번호 뒤의 조사는 옮기지 않았으니 손으로 본다"
    )


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        """인자가 틀려 2로 끝날 때도 할 일을 싣는다."""
        self.print_usage(sys.stderr)
        self.exit(2, f"인자가 틀렸다: {message}\n{ON_FAILURE}\n")


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="uv run python tools/sibling_overlap.py", description=USAGE, epilog=EXITS)
    parser.add_argument("path", nargs="?", help="저장소 안의 경로. 없으면 지금 폴더")
    parser.add_argument(
        "--move",
        action="store_true",
        help="옮길 번호대로 일지·ADR 의 파일 이름과 일지 머리 줄, 이 브랜치의 변경과 미추적 파일"
        " 안의 인용을 옮기고 다시 대조한다",
    )
    return parser


def main(argv: list[str] | None = None, today: date | None = None) -> int:
    """`today` 는 시험이 날짜를 고정하는 자리다. 없으면 이 기계의 지역 날짜다."""
    args = _parser().parse_args(argv)
    where: str | None = args.path
    move: bool = args.move
    start = Path(where) if where else Path.cwd()
    day = (today or datetime.now().astimezone().date()).isoformat()  # 이 기계의 시간대
    check = _move_and_check if move else _check
    try:
        result, verdict = check(start, day)
    except SurveyError as error:
        print(f"형제를 대조하지 못했다. {error}", file=sys.stderr)
        print(ON_FAILURE, file=sys.stderr)
        return 2
    except StuckMoveError as error:
        print(f"번호를 옮기지 못했다. {error}", file=sys.stderr)
        print(ON_STUCK, file=sys.stderr)
        return 2
    except MoveError as error:
        print(f"번호를 옮기지 못했다. {error}", file=sys.stderr)
        print(ON_FAILURE, file=sys.stderr)
        return 2
    print(render(result, verdict))
    return verdict.code


def _prepare(start: Path) -> tuple[Path, Remote]:
    """저장소 루트를 찾고 원격을 읽어 fetch 한다."""
    root = Path(git(start, "rev-parse", "--show-toplevel").strip()).resolve()
    remote = read_remote(root)
    fetch(root, remote.pulls)
    return root, remote


def _check(start: Path, day: str) -> tuple[Survey, Verdict]:
    """대조한다."""
    root, remote = _prepare(start)
    result = survey(root, remote)
    return result, judge(result, day)


def _kept_lines(root: Path, main_sha: str, paths: Iterable[str]) -> dict[str, frozenset[str]]:
    """파일마다 merge-base 와 main 의 판에 있는 줄(줄 끝의 CR 은 뺀다). 그 판에 없으면 빈 집합."""
    base = merge_base(root, "HEAD", main_sha)
    trees = [Tree(root, commit) for commit in (base, main_sha) if commit is not None]
    return {
        path: frozenset(line.rstrip("\r") for tree in trees for line in tree.text(path).split("\n"))
        for path in paths
    }


def _move_and_check(start: Path, day: str) -> tuple[Survey, Verdict]:
    """대조하고, 옮길 번호가 있으면 옮긴 뒤 다시 대조한다."""
    root, remote = _prepare(start)
    result = survey(root, remote)
    verdict = judge(result, day)
    if not verdict.shifted:
        print("옮길 번호가 없어 옮기지 않았다")
        return result, verdict
    kept = _kept_lines(root, result.main.commit, result.changed)
    plan = plan_moves(root, result.ours, verdict.shifted, result.changed, kept)
    apply_moves(root, plan)
    print(_moved_line(verdict.shifted, plan))
    result = survey(root, remote)
    return result, judge(result, day)


if __name__ == "__main__":
    sys.exit(main())
