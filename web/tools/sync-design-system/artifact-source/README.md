# Agent OS 디자인 시스템으로 그리는 법

화면 문구는 한국어다. 운영자 화면(관리 화면)과 최종 사용자 위젯이 이 디자인 시스템 하나를 나눠 쓴다.

## 준비, 테마, 밀도

- 프로바이더가 없다. 목업에는 파일 넷(`styles.css`, `fonts/fonts.css`, `_ds_bundle.css`, `_ds_bundle.js`)을 경로 그대로
  두고, 문서에는 `styles.css` 하나와 `_ds_bundle.js` 를 싣는다. `styles.css` 가 `fonts/fonts.css` 와 `_ds_bundle.css` 를
  차례로 가져온다. 컴포넌트는 `window.AgentOsUi` 에서 꺼낸다.
- 테마는 `<html>` 의 `data-theme`(`nokcheong` 기본, `guncheong`, `jacho`, `jjokbit`)이고 색만 바꾼다. 글꼴, 크기,
  모서리는 모든 테마가 같다. 모드는 같은 요소의 `data-mode`(`light`, `dark`)이고, 없으면 시스템 설정을 따른다. 목록은
  `AgentOsUi.THEMES`(`key`, `name`)와 `AgentOsUi.DEFAULT_THEME`.
- 밀도는 같은 요소의 `data-density`(`compact` 촘촘, `regular` 보통)다. 없으면 폭 768px 이상에서 촘촘, 미만에서 보통이다.
  관리 화면은 달지 않고, 위젯은 `regular` 를 단다. 밀도는 버튼과 입력의 높이, 표의 행 높이, 본문·표·고정폭 글자의 크기를
  바꾼다.
- 한 영역만 다른 테마·모드·밀도로 그리려면 그 요소에 `data-theme`(와 `data-mode`, `data-density`)를 단다. 쓰임새 토큰과
  밀도 변수가 그 요소에서 다시 풀린다. 테마나 모드를 단 영역의 바탕은 `background: var(--bg); color: var(--text)` 로
  칠한다(`<html>` 은 이미 그렇게 칠한다). `data-theme` 만 달고 `data-mode` 를 빼면 그 영역은 시스템 설정을 따른다.
- 다크 전용 색이나 테마 전용 색을 따로 두지 않는다. 쓰임새 토큰이 테마와 모드를 바꾼다.

## 스타일 관용

- 컴포넌트는 `className` 과 `style` 을 받지 않는다. 모양은 props(`variant`, `size`, `tone`, `padding`, `status`)로만
  고른다. 높이는 밀도가 정해 버튼에는 `size` 가 없다.
- 내 배치(감싸는 `div`, 줄과 칸)는 둘 가운데 하나로 짓는다.
  - 번들 CSS 에 이미 있는 유틸리티 클래스: `flex flex-col flex-wrap flex-1 items-center items-start justify-between
    justify-center gap-1 gap-2 gap-3 gap-4 p-3 p-4 px-3 px-4 py-2 py-3 w-full min-w-0 shrink-0 overflow-hidden bg-bg
    bg-bg-raised text-text text-text-muted text-danger text-warning text-success text-info text-body text-table text-mono
    text-small text-badge font-sans font-mono font-regular font-medium font-semibold border border-border
    border-border-control rounded-s rounded-m rounded-l rounded-full h-control h-row shadow-float`. `text-body`,
    `text-table`, `text-mono`, `h-control`, `h-row` 는 밀도를 따른다. `shadow-float` 은 떠 있는 것(위젯 창, 메뉴)에만
    쓴다. 제목 글자(`text-title`)는 클래스가 없으니 아래 변수로 쓴다.
  - 그 밖은 인라인 `style` 의 CSS 변수:
    - 색(쓰임새): `--bg --bg-raised --text --text-muted --border --border-control --accent --on-accent --focus-ring
      --danger --warning --success --info --primary --on-primary --primary-hover --primary-active --bg-hover
      --bg-active --bg-selected --text-disabled --bg-disabled --shadow-color`. `--bg-hover`, `--bg-active`,
      `--bg-selected` 는 반투명이라 놓인 바탕에 겹쳐 칠한다.
    - 여백(px): `--spacing-1`(4) `-2`(8) `-3`(12) `-4`(16) `-6`(24) `-8`(32)
    - 밀도(px, 밀도가 고른다): `--control-h --row-h --body-size --body-lh --table-size --table-lh --mono-size`. 고정폭
      글자의 줄 높이는 `--table-lh` 다.
    - 글자: `--text-title --text-small --text-badge`, 짝인 `--text-<이름>--line-height` 와
      `--text-<이름>--font-weight`, 굵기 `--font-weight-regular --font-weight-medium --font-weight-semibold`, 글꼴
      `--sans --mono`
    - 모서리: `--radius-s --radius-m --radius-l --radius-full`
    - 틀(px): `--spacing-nav`(옆 탐색의 폭) `--spacing-nav-item`(탐색 항목의 높이) `--spacing-top-bar`(768px 미만의 위
      막대)
- 배치에는 위 목록의 클래스만 쓴다. 번들 CSS 에는 컴포넌트가 안에서 쓰는 클래스도 있지만 배치용으로 보장하지 않고, 흔한
  Tailwind 이름 가운데 `text-base`, `p-5`, `gap-8`, `rounded-md`, `truncate`, `dark:` 는 CSS 가 없어 아무것도 그리지
  않는다. 원색 토큰(`--gray-500`, `--accent-600` 등)은 테마의 재료이니 쓰지 않는다.
- 길이는 모두 px 이다. 넓은 화면의 기준 폭은 768px 이다(`--breakpoint-wide`).

## 어디를 읽나

- `components/<이름>/README.md`(쓰임): 언제 쓰는지, 해도 되는 것과 하지 않는 것.
- Components 절의 컴포넌트 카드: 그 컴포넌트를 실제 자리(승인 묻기, 실행 목록, 플러그인 줄 등)에 놓은 모습이다.
- 기초 카드(Colors, Type, Spacing, Density): 색, 글자 단계, 간격과 모서리, 밀도 두 벌.
- `guidelines/web-design.md`: 상태를 색만으로 보이지 않기, 승인 묻기의 버튼 차례("거부" 보조가 먼저, "승인" 주가
  나중), 도구 이름과 인자는 고정폭 글자 그대로 같은 여러 컴포넌트에 걸친 기준.
- `styles.css` 가 가져오는 `_ds_bundle.css`: 위 토큰과 클래스의 원본.

## 예시

```jsx
const { Card, Switch, StatusBadge, Button } = window.AgentOsUi;

function PausedRun() {
  return (
    <Card padding="4">
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between gap-3">
          <h2
            style={{
              margin: 0,
              fontSize: "var(--text-title)",
              lineHeight: "var(--text-title--line-height)",
              fontWeight: "var(--text-title--font-weight)",
            }}
          >
            결제 환불
          </h2>
          <StatusBadge status="paused" />
        </div>
        <span className="font-mono text-mono text-text-muted">run_7f3a</span>
        <Switch label="payments.refund" checked onChange={() => {}} />
        <div className="flex gap-2">
          <Button variant="secondary">거부</Button>
          <Button variant="primary">승인</Button>
        </div>
      </div>
    </Card>
  );
}
```
