# 2026-11-14 01:26 위젯이 모든 에이전트의 출력을 마크다운 부품으로 그린다 (answer-markdown 03)

브랜치 `feature/03-widget-renders-answers-as-markdown`. 티켓 `.scratch/answer-markdown/issues/03-widget-renders-answers-as-markdown.md`. 이 일지는 인계로 만든 중간 기록이고, 새 세션이 이어 쓰고 커밋한다. 회고와 "다음" 절은 단계를 닫는 마지막 세션이 쓴다.

## 사용자 프롬프트

> 사용자: `.claude/skills/implement/SKILL.md`를 읽고 그대로 따른다. 인자는 `.scratch/answer-markdown/issues/03-widget-renders-answers-as-markdown.md`. 위젯이 모든 에이전트의 출력을 01·02의 마크다운 부품으로 그린다. 다음 단계는 구현, 새 세션에서 `tidy-checkouts`를 먼저 돌고 새 워크트리에 들어가 브랜치 `feature/03-widget-renders-answers-as-markdown`로 바꾼다. 모델은 Sonnet 5.5 / high. 이번 요청 범위는 "PR과 병합까지"다.

이 세션이 받은 사용자 메시지는 이 지시문 하나다. 그 뒤의 알림은 모두 앱과 훅이 보냈다.

## 한 일

구현과 검증은 끝났고 커밋하지 않았다(작업 트리에 남아 있다).

- 위젯 출력: `web/apps/widget/components/organisms/Conversation.tsx`가 숨긴 "출력: "과 `Markdown`을 `<div>` 하나에 둔다. 읽기 영역(`WidgetScreen.tsx`)은 알림 항목에 종류(`output`·`note`)를 두고 출력만 `MarkdownText`로 문단 안에 그린다(`lib/conversation.ts`의 `Announcement`).
- 테스트: `WidgetMarkdown.test.tsx`(새 파일, 6건)와 `WidgetConversation.test.tsx`의 HTML 조각 사례 하나를 새 틀로 고쳤다.
- 준비 패키지: 고정된 마크다운 출력을 내는 `markdown` 픽스처 에이전트(`e2e-stack/src/plugins.ts`)와 그 시험.
- 위젯 e2e: 이미지 요청 0(양성 대조는 `Image` 로드. 전역 `fetch`는 ESLint가 막는다), 링크 새 탭, iframe 방식과 페이지 안 방식의 같은 모양과 사이트 CSS 불침투(`element.e2e.ts`). 페이지 전체에서 `5/9`를 찾던 두 곳을 대화 영역 안으로 좁혔다.
- 실제 모델 시험: 비교 규칙을 `tests/screen_text.py`의 함수 하나로 두고(`tests/test_screen_text.py` 8건) 두 래퍼(`tests/test_widget_llm.py`, `tests/test_portal_llm.py`)가 함께 부른다. 두 e2e 로케이터(`llm-ask.ts`, `calc.llm.ts`)는 숨긴 "출력: "의 부모 요소를 찾아 접두까지 그대로 싣고, 떼는 것은 함수가 한다.
- 문서: `EMBED.md`에 "에이전트의 답이 그려지는 모양" 절을 더했다. 대화 스토리의 긴 낱말 주석을 새 틀로 고쳤고, `MarkdownOutput` 스토리와 그 사진 둘(`organisms-conversation--markdown-output-{light,dark}.png`)을 더했다.
- 하네스 쪽 고침 하나: `web/apps/widget/tools/element.ts`의 `buildElement`가 빌드 동안 `NODE_ENV`를 `production`으로 고정한다. vitest(`NODE_ENV=test`)에서 빌드하면 micromark의 개발용 진입점이 `debug` 패키지와 그 `process.env`를 번들에 실어 `element.test.ts`가 빨개졌다(production에서는 0건이었다).

## 확인한 것

- `uv run ruff check . && uv run ruff format --check .`, `uv run pyright`: 초록.
- `uv run python tools/run_checks.py`: 열 단계 모두 통과(pytest 333.8초, web-verify 543.8초). 이 실행은 마크다운 스토리와 `element.ts` 고침이 든 상태에서 돌았다.
- 위젯 e2e 전체와 위젯 미리보기 페이지 e2e 전체: 초록(`element.e2e.ts`의 `h1` 로케이터를 고친 뒤).
- `uv run --env-file ../../../.env pytest -m llm_widget`: 1 passed(토큰 17,047, 모델 호출 4건). `-m llm_portal`: 1 passed(토큰 6,997, 모델 호출 2건).
- `pnpm -C web visual:widget`: 기존 사진 43장 모두 정답과 같다. 글자만 든 출력의 사진이 같다는 명세와 맞다. `visual:widget:update`로 새 사진 둘만 늘었다.
- `visual`·`visual:admin`: 돌리지 않았다. `web/packages/ui`와 관리 앱을 건드리지 않았다(CI의 `visual` 잡이 본다).
- element 번들 크기(손으로 쟀다. 임시 스크립트가 `buildElement`로 지은 `element.js`를 `node:zlib`의 `gzipSync`로 눌러 찍었고, 커밋하지 않고 지웠다. 명령은 `node web/apps/widget/tools/size-probe.ts`): 적용 전 raw 406,954 B, gzip 122,030 B. 적용 후 raw 587,963 B, gzip 176,003 B. gzip이 53,973 B(약 52.7 KiB) 늘었다. 두 파일(`Conversation.tsx`, `WidgetScreen.tsx`)만 적용 전으로 되돌려 잰 값이다. PR 본문에 적는다.

## 사용자가 봐야 할 것

- 새 사진 `web/apps/widget/visual/snapshots/organisms-conversation--markdown-output-light.png`와 `-dark.png`를 화면 파일(`.scratch/answer-markdown/design/`의 완성 화면 열)과 사람이 견준다. 라이트 사진을 직접 열어 보니 제목, 굵게, 위첨자 번호, 목록, 표, 링크, 출처 덩이가 기호 없이 보였다. 디자인과의 견줌은 사람의 몫이라 하지 않았다.

## 남은 일

1. `/code-review`로 셀프 리뷰(기준은 `origin/dev`)를 하고 Critical·Major를 고친다. 이 세션은 리뷰 직전에 인계했다.
2. 티켓 03의 체크박스를 채우고 `Status:`를 `done`으로 바꾼다. 티켓 04가 열려 있으니 `**끝:**` 줄은 쓰지 않는다. `uv run python tools/plan_table.py`가 계획표를 바꾸면 같은 커밋에 싣는다.
3. 루트 `README.md`의 트리와 원천 표를 점검한다. `tests/screen_text.py` 같은 파일이 표에 들어갈 자리인지 본다(`test_widget_llm.py`와 `fake_doc_search.py`는 `README.md`에 없었다).
4. 커밋 전 `git branch --show-current`, `uv run python tools/sibling_overlap.py`(직전에 쳤을 때 겹침 없음).
5. PR을 열고 봇 회차와 병합(`merge.md`, 워크트리 병합 절)을 마친다. PR 본문에 번들 크기와 "사람이 사진을 견줘야 한다"를 적는다.

## 인계

open-session을 부른다 2026-11-13T16:27:16Z

인계 못함 셀프 리뷰 직전: open-session의 send 스크립트(tools/open_session.ps1)가 자동 모드 분류기에 거부되어 새 세션을 열지 못했다. 제목을 되돌리고 이 세션에서 셀프 리뷰부터 잇는다.

## 셀프 리뷰 (기준 SHA 6cb9bf3bb, 파일 18개, 미추적 6개, 커밋 0개)

표준 축과 명세 축 서브에이전트를 병렬로 돌렸다. 둘 다 Critical·Major는 없었다.

고친 것(지적마다 근거를 코드와 파일에서 확인하고 고쳤다):
- `EMBED.md` 186행의 대화를 아직 남기지 않는다는 문장은 낡은 것이었다. `web/apps/widget/lib/storage.ts`가 같은 탭의 `sessionStorage`에 남긴다(코드를 읽어 확인). 이 문장과 새 절이 모순이라 함께 고쳤고, 새 절의 한 항목에 섞인 다시 불러온 대화와 읽기 영역을 둘로 갈랐다.
- `tests/screen_text.py` 독스트링의 "틀린 실패를 내지 않는다"를 좁혔다. 서브에이전트가 `screen_matches_output("이미지", "이미지")`가 False임을 직접 불러 보였고, 원문이 숨김 문구뿐인 출력은 지운 뒤 화면 글이 비어 걸린다. 그 경계를 `test_원문이_지우는_말뿐이면_지운_뒤_화면_글이_비어_걸린다`로 고정했다.
- `HIDDEN_PHRASES`가 상수를 자기 복사본과 견주던 시험을, 부품의 쓰임 문서(`Markdown.md`)가 적은 두 문구(`"(새 탭에서 열림)"`, `"이미지: "`)를 읽어 대는 시험으로 바꿨다.
- 주석 잔존: `llm-ask.ts`, 위젯과 포털의 `calc.llm.ts`가 "출력: "을 떼고 싣는다고 적던 것(코드는 접두까지 그대로 싣고 떼는 것은 `tests/screen_text.py`다), "출력 문단"(틀은 문단이 아니라 `div`다) 네 곳, `assistant.llm.ts`의 낡은 시제, `test_screen_text.py`의 "화면 파일 입력"을 고쳤다.
- `element.ts`의 `buildElement` JSDoc을 `NODE_ENV` 고정에 맞게 고쳤다.

남긴 것과 이유:
- `NODE_ENV` 고정을 지켜 주는 시험이 없다는 지적(표준 축 Minor)은 맞지 않다. 기존 번들 시험이 vitest의 `NODE_ENV=test`에서 돌아 `process.env` 단언이 이 고정 없이는 빨개진다(이 변경 직후 실제로 빨개졌고, 고친 뒤 7건 통과). 손으로 본 것이다.
- 두 파이썬 래퍼의 조건 복사와 두 TS 로케이터의 복사(Duplicated Code, Minor): 포털 래퍼 독스트링이 같은 코드를 따로 둔다고 밝힌 구조다.
- 티켓 "페이지 시험"의 "실패 안내" 사례(명세 축 경미): 실패 안내는 고정 문구고 `FailureAlert`가 `message`를 그리지 않아 별표를 넣을 입력이 없다(주석을 읽었다). 질문, 인사말, 승인 카드 인자, 알림은 시험이 있다.
- 사진 견줌과 번들 크기는 PR 본문과 사용자 보고로 넘긴다.

다시 돌린 명령: 이 반영(주석, 독스트링, 문서, 시험 한 건)은 `uv run pytest -q tests/test_screen_text.py`(9 passed), `uv run ruff check tests`·`ruff format --check tests`, `pnpm -C web exec prettier --check`까지 돌렸다. 나머지 검증 명령은 커밋의 pre-commit 결과로 갈음한다(커밋 뒤에 적는다).
