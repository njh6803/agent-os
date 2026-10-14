# 2026-10-14 (06) design-refresh 티켓 05의 올리기: Claude Design 재동기화

## 계기

일지 2026-10-13-62의 "다음"이 티켓 05의 "올리기"였다. 사용자가 그 지시문을 주 체크아웃 세션에 붙여 넣었다. 지시문의 "이
워크트리"(무시된 `.ds-sync/` 2.1.286 사본이 있는 자리)를 따라 `EnterWorktree(path=…/05-claude-design-upload)`로 들어갔다. 그
워크트리의 브랜치는 이미 squash로 병합됐고 작업 트리가 깨끗해서 `origin/main`(`5f72cdb`)에서 `chore/design-sync-refresh`를
땄다. `git switch -c`가 붙인 upstream(`origin/main`)은 맨 `git push`가 main으로 가지 않게 풀었다. 주 체크아웃은 `origin/main`과
같아 당길 것이 없었다. 셀프 리뷰 전에 그사이 전진한 `origin/main`(`54eb5be`)으로 앞으로 감았다(이 브랜치에 커밋이 없었다).

> 사용자: "다음 작업: .scratch/design-refresh/issues/05-claude-design-upload.md의 "올리기". 사람이 /design-sync를 시작해 새 디자인 시스템을 Claude Design 프로젝트에 올리고 티켓 05를 닫는다 … 이번 요청 범위: PR과 병합까지"

`DesignSync` 도구는 사용자가 시작한 `/design-sync` 안에서만 쓴다. 그래서 준비만 하고 사용자에게 시작을 넘겼다. 그사이 사용자가
미룰 수 있는지와 화면이 아닌 기능 작업을 물었다.

> 사용자: "화면 관련된 작업은 나중에 해도 돼?"

> 사용자: "하네스 작업말고 기능 작업은?"

`plan.md`의 `todo`는 web-widget과 admin-style 둘이고 둘 다 화면을 든다고 답했다. 화면이 아닌 몫(최종 사용자 경로의 이어 가기
계약, 긴 고리의 거슬러 읽기가 `serve`를 막는 것, 타임아웃 뒤 MCP 서버 프로세스)은 web-widget에서 떼어 기능 행으로 세울 수
있다고 제안했다. 사용자는 답 대신 `/design-sync`를 시작했다. 이 제안은 "다음"에 남긴다.

## 어떻게 했나

- **변환기 판.** 풀린 스킬은 지시문이 예상한 2.1.296이 아니라 2.1.295였다. 덮어쓰기 전의 2.1.286 사본을 스크래치에 보관하고
  스킬 폴더와 `diff -rq`로 견줬다(`node_modules`·`package*.json` 제외). `lib/`는 다른 파일이 없어 `lib/emit.mjs`의
  `overrides.<Name>.skip`(`visibleStoryIds`)과 `cardByDir`, 포크의 원본 `preview-gen-storybook.mjs`가 그대로였다. 다른 것은
  셋이었다. 캡처 서버 `storybook/http-serve.mjs`의 `charset=utf-8`, 새 `package-capture.mjs`, `non-storybook/SKILL.md`다.
- **입력.** `pnpm -C web install --frozen-lockfile`, 패키지 `build`, 참조 Storybook을 다시 지었다(`iframe.html` 18KB).
  원격 `_ds_sync.json`을 받아 고정된 프로젝트(owner "지형", `canEdit`)로 원자 경로를 탔다.
- **첫 드라이버.** `ok: true`, 아홉 컴포넌트가 모두 `changed`, `deletePaths` 비었음, `[FONT_MISSING]` 없음. compare가 보여
  주기용 11개만 캡처했다. 경고 하나 `[GRID_OVERFLOW] wide`(Alert의 두 스토리)에 `cfg.overrides.Alert.cardMode: "column"`을
  주었다. 시트 아홉을 모두 보고 Button과 StatusBadge는 raw 쌍도 열어 11개를 `match`로 매겼다(틀만 다르다). 마지막 드라이버에서
  아홉 모두 `carried forward`였다.
- **첫 업로드.** 기초 카드와 목록 타일을 `ds-bundle/`에 복사하고 `node .design-sync/check-conventions.mjs`가 0으로 끝났다
  (클래스 50, 변수 54, 뺀 스토리 77, 카드 다섯의 변수 133). `report_validate`(9, bad 0, thin 0)를 보내고 기준점을 다시 받아
  움직이지 않은 것을 본 뒤 사용자가 `finalize_plan`을 승인했다. 울타리 → 829개(글꼴은 130개씩 여섯 묶음) → 울타리 →
  `_ds_sync.json` 순서로 올렸다. 원격 `list_files`에 `foundations/` 넷, `thumbnail.html`, Noto Sans Mono가 있었다.
- **카드 확인.** 티켓은 사람이 카드를 확인한다고 적는다. 내장 브라우저가 claude.ai에 로그인되어 있지 않아 사용자에게 확인을
  부탁했고, 사용자는 내장 브라우저에 로그인했다. 그 뒤 세션이 같은 창(사용자도 보는 창)에서 셋을 봤다. 그래서 이 확인은
  사람이 아니라 세션이 본 것이다. (1) 디자인 시스템 창이 기초 카드 넷을 그룹 `Colors`·`Density`·`Spacing`·`Type` 아래에
  모았고 색 카드는 값까지 채웠다. 카드 이름은 파일 이름을 따라 `index`다. (2) 컴포넌트 카드가 다크 설정의 앱에서 본문
  글자(StatusBadge의 `run_7f3a` 등)를 흰 바탕 위에 거의 보이지 않게 그렸다. 탭의 색 설정을 라이트로 에뮬레이트하자 진하게
  보였다. 창의 목록에는 컴포넌트 아홉(atoms 여섯, molecules 셋)이 모두 있었다.
  (3) 목록 타일 이미지는 URL의 시각만 연 순간으로 바뀌고 그림은 첫 동기화의 옛 타일(띠 넷)이었다.
- **사용자가 고른 것.** 둘을 물었다. 첫째는 "다크 설정에서 컴포넌트 카드의 글자가 흐린 문제를 어떻게 할까요?"였고 선택지는
  "포크에서 라이트로 고정 (Recommended)"(globals 없는 스토리도 `data-mode="light"`와 기본 테마로 감싼다, 11개를 다시
  캡처·채점하고 컴포넌트 파일을 다시 올린다)과 "그대로 두고 기록"이었다. 사용자는 선택지 대신 물었다.

  > 사용자: "카드에는 data-mode(라이트·다크를 고르는 속성)을 추가하면 안되는거야?"

  둘째는 "목록 타일이 옛 그림 그대로입니다. 어떻게 할까요?"였고 선택지는 "기록만 하고 둔다 (Recommended)"와 ".thumbnail을
  지워 본다"(삭제 승인이 따로 필요하고 다시 생기지 않으면 타일이 빈 채로 남을 수 있다)였다. 사용자는 뒤의 것을 골랐다.

  > 사용자: ".thumbnail을 지워 본다"

  첫째 답은 `data-mode`를 다는 것이 첫 선택지와 같다고 읽었다. 카드 HTML은 빌드마다 새로 지어지므로 손이 아니라 포크에
  단다고 답하고 그렇게 했다. 포크가 globals 없는 스토리도
  `data-theme="nokcheong"`·`data-mode="light"`로 감싸고 글자색을 그 안에서 `var(--text)`로 다시 푼다(여백과 바탕은 없다).
  `cfg.libOverrides`의 설명 문장도 고쳤다(`sync-hashes.mjs`가 그 값을 채점 키에 넣지 않는 것을 읽었다). 포크가 채점
  계약이라 아홉을 다시 캡처해 다시 `match`로 매겼고, 첫 업로드가 올린 기준점으로 마지막 드라이버를 돌려 아홉 모두
  `carried forward`, `bundle`·`styling`·`aux`가 모두 `false`였다. 둘째 `finalize_plan`(쓰기는 같은 전체 목록, 지우기는
  `.thumbnail`)을 사용자가 승인했고, 컴포넌트 카드 45개를 올리고 `.thumbnail`을 지우고 울타리와 기준점을 올렸다.
- **둘째 확인.** 다크 설정의 앱에서 Button과 StatusBadge 카드의 글자가 진하게 보였다. 나머지 일곱은 다크에서 열어 보지
  않았다. 목록 화면을 다시 연 뒤 타일 이미지가
  새 그림(녹청 바탕의 "Agent OS", 띠 셋)이 됐다. 서버가 `.thumbnail`이 없을 때만 `thumbnail.html`을 그리는 것으로 본다.
- **기록.** `.design-sync/NOTES.md`에 재동기화, 채점이 빼는 목록을 따른다는 것, 기초 카드가 모인다는 것과 그 이름, 다크
  카드의 원인과 포크, 타일을 바꾸려면 `.thumbnail`을 지운다는 것, 원격에 남은 옛 고정폭 글꼴, Alert의 `cardMode`, 이번
  채점을 적었다. 티켓 05의 남은 상자 셋을 닫았고 `plan.md`의 admin-style·web-widget 행에 올렸다고 적었다.

## 정한 것

1. **다크 카드는 포크에서 라이트로 고정한다.** 카드에 `data-mode`를 추가하면 안 되느냐는 사용자의 물음을 첫 선택지로 읽은 길이다. 기초 카드와 목록 타일이 이미 `data-mode="light"`를 다는
   것과 같은 까닭이다. compare의 chromium은 라이트라 두 쪽이 같아 보여 이 차이를 잡지 못한다.
2. **원격의 옛 고정폭 글꼴 28개는 지우지 않았다.** 드라이버의 `deletePaths`가 `components/` 경로만 견주어 비었고, 스킬이
   재동기화의 삭제 목록을 손으로 짓지 말라고 한다. 새 `fonts/fonts.css`가 가리키지 않아 화면에는 영향이 없다. NOTES에 지우는
   길을 적었다.
3. **기초 카드의 이름 `index`는 이번에 고치지 않았다.** 파일 이름을 바꾸면 고쳐질 것으로 보지만 재지 않았고, 카드를 다시
   올려 창에서 봐야 한다. `index.html`을 든 티켓 05의 "정한 것" 3과 프로브 `checker_mutations.mjs`를 함께 고칠 일이라
   "다음"의 후보로 남긴다. 검사기는 파일 이름을 가리지 않는다.
4. **`.thumbnail`은 손으로 지울 목록에 넣었다.** 스킬은 재동기화의 삭제 목록을 `upload.deletePaths`에서 그대로 옮기라고
   하지만, 그 파일은 변환기가 짓지 않고 서버가 만들어 diff에 보이지 않는다. 사용자가 지우기를 골랐다. 옛 고정폭 글꼴은
   변환기가 지은 것이라 같은 예외로 보지 않고 2대로 두었다.

## 검사

- 드라이버 넷의 판정: 첫 실행 `ok`·채점 대기 아홉, 채점 뒤 `carried forward` 아홉, 포크를 고친 뒤 채점 대기 아홉, 마지막
  `carried forward` 아홉·`pendingGrade` 비었음.
- 규약 검사기 두 번 0으로 끝났다.
- 원격 `list_files`, 내장 브라우저에서 디자인 시스템 창의 카드(다크와 라이트)와 타일 이미지 URL을 손으로 봤다.

## 셀프 리뷰

`/code-review`(base `54eb5be`, 바뀐 파일 다섯, 미추적 하나, 커밋 0)의 두 축. 파이썬 소스가 없어 표준 축은 sonnet이었다.
표준 축은 Major 1·Minor 5·Nit 3, 명세 축은 Major 1·Minor 4·Nit 3이었고 Major는 둘 다 같은 것이었다.

- **고친 것.**
  - `plan.md`의 design-refresh 행(done)이 미래형으로 남았다(두 축의 Major). "사람이 시작하는 첫 `/design-sync`가 본다"와
    "시작하는 것으로 닫는다"를 지난 일로 고쳤다.
  - NOTES의 낡은 문장 셋. 포크가 "globals 감싸기만 더했다", 첫 동기화의 채점 경고, 기초 카드의 이름 문제를 지난 관찰로만
    적은 것이다. 지금의 포크(감싸는 요소 하나, 두 갈래)와 지금의 채점 근거, 열린 문제와 고칠 자리로 고쳤다. 고치며 쓴
    "검사기가 `index.html`을 전제한다"는 `check-conventions.mjs`를 열어 보니 틀려(폴더마다 HTML이 하나인지만 본다) 바로잡았다.
  - `.thumbnail`을 손으로 지운 것이 스킬의 삭제 규칙과 어긋나 보인다는 지적. 서버가 만든 파일이라 diff에 보이지 않는다는
    까닭을 NOTES와 "정한 것" 4에 적었다.
  - 근거의 종류. 2.1.286과의 `diff -rq`가 스크래치 사본으로 한 것이라 다시 볼 수 없다고 적었다. 다른 파일 셋을 정확히
    적었다(일지가 "스킬 문서"로 뭉뚱그렸다). 빼는 목록을 채점이 따른다는 근거를 드라이버 로그의 `[COMPARE]` 줄로 적었다.
    라이트 시트가 앞의 판과 같다는 것은 눈으로 본 것이고 바이트 비교는 하지 않았다고 적었다. 다크에서 열어 본 카드는
    둘뿐이라고 좁혔다. 확인 방법의 말을 "탭의 색 설정을 에뮬레이트"로 맞췄다.
  - 카드 확인을 사람이 아니라 세션이 했다는 것, 질문 둘과 선택지, 첫 답을 첫 선택지로 읽은 해석, `origin/main`으로 앞으로
    감은 것을 일지에 적었다. 조작 응답 인용 하나를 뺐고, NOTES의 "첫 업로드"를 "재동기화의 첫 업로드"로 갈랐다.
- **남긴 것.**
  - 포크 `COMPOSE`의 두 갈래가 같은 `createElement` 모양을 되풀이한다(Duplicated Code, 판단 항목). 포크 주석의 "so the
    layout is the same"이 눈으로 본 단정이다(Nit). 포크의 바이트는 채점 계약이라 고치면 아홉을 다시 캡처·채점하고 다시
    올려야 한다. 다음에 포크를 고칠 때 함께 고친다(NOTES의 포크 항목이 라이트 고정의 짝이 `themes.ts`에 없다고 적는다).
  - 런북 `kickoff/prompting.md`의 목록 타일 교훈에 `.thumbnail` 지우기를 더할지(Nit)는 회고 후보로 넘긴다.

## 검증

(검증 뒤에 채운다)

## PR 직전 리뷰

(PR 직전 리뷰 뒤에 채운다)

## 회고

(회고 뒤에 채운다)

## 다음

(next-session 이 채운다)
