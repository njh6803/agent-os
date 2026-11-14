# 디자인 시스템 올리기: React 18에서 그려지는 마크다운 카드 (harness ds-upload-markdown-react-18-fix)

브랜치 `chore/ds-upload-markdown-react-18-fix`. 티켓은 `.scratch/harness/issues/ds-upload-markdown-react-18-fix.md`. 세션 제목은 인계 전 디자인 시스템에 고친 Markdown 카드 올리기였다.

## 사용자 프롬프트(원문)

이 세션은 사용자가 직접 연 것이 아니라, answer-markdown 기능을 마친 앞 세션이 위임한 일이다. 위임문의 요지를 옮긴다(사용자의 말은 아니다).

> 위임 세션: "디자인 시스템 아티팩트(https://claude.ai/artifact/8ttLDZQqchfD2ao1XG56GH)에 PR 564(dev 병합 커밋 db2c888d1)가 고친 Markdown 부품을 올리고, 앱 안 브라우저로 Components 절의 Markdown 카드가 그려지는지 본다." 올리기는 `/sync-design-system 올리기` 절차대로, 확인 절차를 건너뛰지 않는다. 카드가 여전히 안 그려지면 오류 모양을 적고 멈춰 알린다.

## 한 일

- `origin/dev`(`dce80e588`, PR 566 병합) 분리 HEAD에서 올리기를 했다. 기록의 `commit`(`ad7dff584`)은 이 HEAD의 조상이다. `pnpm -C web install --frozen-lockfile` 뒤 확인 `clean`(웹 편집 없음), 결정 `upload`였다.
- 산출은 804개 파일과 카드 열 개다. 계획은 보낼 파일 7개(`_ds_bundle.css`·`_ds_bundle.js`, `components/bundle.css`·`bundle.js`, `components/Markdown/README.md`·`preview.html`, `guidelines/web-design.md`), 지울 경로 0개, 호출 하나였고, 기록과 색인(`design-system.json`)을 함께 보냈다. `project/README.md`가 보낼 파일에 없어 옮기기 절은 묻지 않았다.
- 보내기 직전 확인(두 번째)이 첫 확인과 `cmp`로 같았다. 판은 `1794621629-6da7`이었다.
- 첫 보내기가 "You haven't viewed the latest version of this artifact"로 거부됐다. 거부 전에는 확인을 두 번 했다(첫 확인에 `paths` 읽기 셋, 보내기 직전 확인에 하나). 절차대로 아무것도 보내지 않았고, 차례는 `url`만 준 `read` 하나, 확인을 처음부터 다시 한 번(세 번째, `paths` 읽기 하나. 판 `1794621629-6da7` 그대로, 받은 파일의 sha256이 앞 확인과 같았고 보고도 `cmp`로 같았다), 같은 내용을 `force` 없이 다시 보내기였다. 재전송이 받아들여졌다(판 43 `1794636666-d3b5`). 앞 티켓 `ds-upload-markdown-cards`가 적은 "확인이 깨끗한데도 도구가 최신 판을 보지 않았다고 거부하는" 갈래를 한 번 더 봤다. 이번에는 `url`만 준 읽기와 `paths`를 준 확인 읽기를 한 번씩 하고 보내자 받아들여졌다. `url`만 준 읽기가 거부를 푼 것인지는 한 번 본 것이라 가르지 못했다. 합치지 않았다.
- 보낸 뒤 확인(네 번째)이 `clean`이다. 받은 파일 가운데 `components/Markdown/README.md`(3,697에서 5,305바이트)와 `guidelines/web-design.md`(15,293에서 15,307바이트)와 색인·기록의 sha256만 바뀌었다.
- 지난 산출 목록: 이번 산출의 경로 목록(`output-paths.json`)이 `previous-output.json`과 `cmp`로 같아 갱신하지 않았다.

## 앱 안 브라우저로 본 것(손으로 봤다)

- 앱 안 브라우저(이미 claude.ai에 로그인된 상태)로 아티팩트를 열고 Components 절(`#components`)을 봤다. 카드는 스크롤해 보일 때 늦게 그려져, 처음 한 번은 빈 칸이었고 5초쯤 기다리자 그려졌다.
- 열 개 카드가 모두 그려졌다. Button(토큰 지우기 버튼과 승인·거부), Card(`run_7f3a` 일시정지 카드), Icon(플러그인·실행·설정), IconButton(입력 칸과 보내기), Progress(3단계 중 2단계 막대), StatusBadge(네 상태), Alert(경고·정보·오류 셋), Markdown, Switch, TextField를 눈으로 확인했다.
- Markdown 칸은 이전의 "This preview could not run..." 문구 대신 장면을 그렸다. 본문 한 단락과 각주 1, 번호 목록 둘(굵은 글씨 포함), 링크("인사 시스템 도움말"), 구분선 아래 "출처" 제목과 그 아래 "1. 육아휴직 업무편람, 12쪽 (갱신일 2026-10-01)" 줄이다. 확대해서 보니 마지막 출처 줄이 칸 아래 경계에서 잘리지 않았고 줄 아래에 여백이 남았다. TextField 칸의 마지막 줄(도움말 문구)도 잘리지 않았다.
- 재지는 않았다. 칸 높이는 눈으로 봤고, 늦게 자라는 내용이 더 있는지는 한 번 본 화면 밖이다. 콘솔 오류는 읽지 않았다.

## 사용자에게 남은 판단

없다. 카드가 그려졌으므로 멈추지 않았다.

## 셀프 리뷰

범위: base `dce80e5882a070ee8c1e8bc05593646e122b5bad`, 수정 파일 1개, 커밋 0개, 미추적 2개(문서만). 표준 축(sonnet·high)과 명세 축을 병렬로 돌렸다. Critical·Major 없음, Minor 5와 Nit 4(두 축이 겹쳐 짚은 것을 합쳤다).

- **고친 것**: 티켓 기준 1의 문구를 거부 경위를 예외로 읽지 않게 바꿨다. 기준 4에 ruff를 손으로 쳤고 나머지는 이 커밋의 pre-commit으로 갈음한다고 적었다. 대기열 항목의 머리와 승인 줄이 4회차와 5회차를 한 줄에서 모순으로 읽히게 하던 것을 맞췄고, 확인 횟수와 `url` 읽기의 순서를 실제 기록대로 일지와 대기열에 같게 적었다. 대기열의 "곧 거부는 ... 상관이 없었다" 단정을 "이 세션 안에서 판이 그대로였다"로 낮췄다. 일지의 출처 줄 인용을 원문처럼 두 줄로 나눠 적었다.
- **남긴 것**: 위임문을 따옴표로 옮긴 부분은 "요지를 옮긴다"고 밝혀 두었고(위임문이 사용자 말이 아니다), 원문 글자 대조는 이 세션이 위임문 원본을 파일로 가지고 있지 않아 하지 않았다. 5회차 chore 조건에 결정표의 "그 기능의 마지막 티켓" 줄이 걸리는지는 그 결정표를 읽지 않아 가르지 못했다. 회고 절은 회차 5 이상이라는 retro 스킬의 문장을 따랐다.
- **다시 돌린 명령**: `uv run ruff check .`와 `uv run ruff format --check .`는 출력이 통과 문구였다(파이프로 쳐 종료 코드는 못 봤다). 나머지는 이 커밋의 pre-commit으로 갈음한다. 결과는 PR 본문에 적는다.

## pre-commit 첫 실행(커밋은 막혔다)

- 러너 출력을 읽었다. check-ticket·zizmor·lint-imports·check-instructions·check-type-escapes·pyright 둘·run-hooks·web-verify(1012초)는 Passed, pytest(807초)는 7306 passed, 3 failed였다. 실패는 `tests/tools/test_hook_push_behind_main.py::test_dev의_유무를_조회하다_시간을_넘기면_재지_않는다`, `tests/tools/test_probe_kit.py::test_배출은_줄이_계속_와도_제한_시간에_끝난다`, `tests/tools/test_rerun_runner.py::test_동시에_둘까지_돌고_셋째는_자리가_빌_때_연다`다. 모두 시간이나 부하에 민감한 시험이고, 이 브랜치는 문서 셋만 바꿔 이어지는 경로가 없다.
- 세 시험 파일을 단독으로(`-p no:xdist`) 쳐 보았다(손으로 쳤다). 158건 가운데 157건이 통과했고, 첫 실행에서 빨갛지 않던 `test_rerun_runner.py::test_다른_판의_확인을_쥐고_돌던_동안에도_첫_인계에서_멈춘다` 하나가 빨갰다. 첫 실행에서 빨간 셋은 단독에서 모두 통과했다. 이 PC에는 다른 세션이 함께 돌아 부하가 높았다.
- 대기열 0306이 이 종류(부하에서만 빨간 시간 시험)를 받아들여 닫았고, 새 사례는 일지에만 적고 커밋을 다시 친다고 정했으므로(그 항목 상태 줄) 사례를 고치지 않고 위 넷을 여기 남긴다. 같은 시험 `test_probe_kit.py::test_배출은_줄이_계속_와도_제한_시간에_끝난다`는 앞 일지(`2026-11-14-0041-04-markdown-card-renders-on-react-18.md`)도 한 번 빨갛다고 적었다. 두 번째 사례지만 사이에 초록 실행이 끼어 있어 연속 실패는 아니다.
- 같은 커밋을 다시 쳤을 때(두 번째 실행, 러너 출력을 읽었다) pytest(1012초)는 7308 passed, 1 failed였다. 빨간 것은 앞의 넷과 다른 `tests/channel/cli/test_interrupt.py::test_서버를_닫기_시작한_뒤에_한_번_누르면_닫기를_마치고_중단으로_끝난다`("Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다")였고, 나머지 검사는 모두 Passed였다. 실행마다 빨간 시험이 달라 같은 시험이 연속으로 빨간 것이 아니다(`CLAUDE.md` 작업 규약 6의 조건 밖). 위 0306의 받아들인 종류로 보아 사례만 적고 다시 친다. 원인은 가르지 못했다.
- 일지 인용 경고 1건(`check-quotes`, 막지 않는다)은 세션 제목을 따옴표로 감싼 줄이었다. 따옴표를 뗐다.

## 회고

후보 1개. 판정은 승인 1, 기각 0, 넘김 0이다.

- **보내기가 "You haven't viewed the latest version of this artifact"로 거부됐다(아티팩트 판은 그대로였다).** 판정은 승인이다. 사건은 위 "한 일"의 첫 보내기 거부이고, 층은 스킬의 틀린 사실을 고치는 고침(`.claude/skills/sync-design-system/SKILL.md` "보내기"가 그 거부를 사람이 바꾼 파일을 보낸 때로만 적는다)이며, 되돌림은 PR 하나다. 대기열 `ds-send-stale-view-rejected`에 5회차로 더했다(`queue_open_rows.py`로 찾은 열린 항목. 앞서 닫힌 0529와 이어진다). 이번 사건이 새로 보탠 사실은 판도 파일 내용도 안 바뀐 채 거부됐다는 것이다. 회차 5이므로 `next-session` 결정표의 chore 배치 조건에 닿았고, 고침 반영은 이 PR(티켓이 올리기 하나)에 싣지 않고 그 chore에 맡긴다.
- 일지에만 남기는 것: 카드는 스크롤해 보일 때 늦게 그려져 첫 화면이 빈 칸이다(5초 기다리면 그려진다). `upload.md` 6의 6 "카드"에 이 대기 한 줄이 없는 점은 사례 하나라 지금 적지 않는다. 앱 안 브라우저의 `find`는 카드(iframe) 안의 글을 못 찾는다(손으로 `find Markdown`을 쳐 "No matches"를 봤다).

## 다음

- 이 PR이 병합되면 이 일은 끝이다. 디자인 시스템 아티팩트에는 판 43이 올라가 있고 Markdown 카드가 그려진다.
- 대기열 `ds-send-stale-view-rejected`가 5회차에 닿았다(위 "회고"). 올리기 중 그 거부를 푸는 길을 스킬에 적는 고침이 chore로 남는다.
