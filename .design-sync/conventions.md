# Agent OS 디자인 시스템으로 그리는 법

화면 문구는 한국어다. 운영자 화면(관리 화면)과 최종 사용자 위젯이 이 디자인 시스템 하나를 나눠 쓴다.

## 준비와 테마

- 프로바이더가 없다. `styles.css` 하나와 `_ds_bundle.js` 를 싣고 `window.AgentOsUi` 에서 컴포넌트를 꺼낸다.
- 테마는 `<html>` 의 `data-theme`(`muk` 기본, `cheongnok`, `gongmun`, `hwangto`, `jadu`)이고, 모드는 같은 요소의
  `data-mode`(`light`, `dark`)다. `data-mode` 가 없으면 시스템 설정을 따른다. 목록은 `AgentOsUi.THEMES`(`key`, `name`)와
  `AgentOsUi.DEFAULT_THEME`.
- 한 영역만 다른 테마·모드로 그리려면 그 요소에 `data-theme`(와 `data-mode`)를 단다. 쓰임새 토큰이 그 요소에서 다시
  풀린다. 그 영역의 바탕은 `background: var(--bg); color: var(--text)` 로 칠한다(`<html>` 은 이미 그렇게 칠한다).
- 다크 전용 색이나 테마 전용 색을 따로 두지 않는다. 쓰임새 토큰이 테마와 모드를 바꾼다.

## 스타일 관용

- 컴포넌트는 `className` 과 `style` 을 받지 않는다. 모양은 props(`variant`, `size`, `tone`, `elevation`, `padding`,
  `status`)로만 고른다. props 는 `components/<group>/<Name>/<Name>.d.ts`.
- 내 배치(감싸는 `div`, 줄과 칸)는 둘 가운데 하나로 짓는다.
  - 번들 CSS 에 이미 있는 유틸리티 클래스: `flex flex-col flex-wrap flex-1 items-center items-start justify-between
    justify-center gap-1 gap-2 gap-3 gap-4 p-3 p-4 px-2 px-3 px-4 py-2 py-3 w-full min-w-0 shrink-0 bg-bg bg-raised
    bg-tint text-text text-muted text-danger text-warning text-success text-info text-heading text-body text-small
    text-caption text-code font-sans font-mono font-medium font-strong border border-border border-divider rounded-m
    rounded-l rounded-full shadow-1 shadow-2 shadow-3 overflow-hidden`. 제목 글자(`text-title`)는 클래스가 없으니 아래
    변수로 쓴다.
  - 그 밖은 인라인 `style` 의 CSS 변수:
    - 색(쓰임새): `--bg --raised --tint --text --muted --border --divider --accent --on-accent --focus --danger
      --warning --success --info --danger-tint --warning-tint --success-tint --info-tint --disabled-surface
      --disabled-text`
    - 여백(px): `--spacing-1`(4) `-2`(8) `-3`(12) `-4`(16) `-6`(24) `-8`(32)
    - 글자: `--text-title --text-heading --text-body --text-small --text-caption --text-code`, 짝인
      `--text-<이름>--line-height`, 굵기 `--font-weight-regular --font-weight-medium --font-weight-strong`, 글꼴
      `--sans --mono`
    - 모서리: `--radius-s --radius-m --radius-l --radius-full`
- 배치에는 위 목록의 클래스만 쓴다. 번들 CSS 에는 컴포넌트가 안에서 쓰는 클래스도 있지만 배치용으로 보장하지 않고, 흔한
  Tailwind 이름 가운데 `text-base`, `p-6`, `gap-8`, `rounded-s`, `dark:` 는 CSS 가 없어 아무것도 그리지 않는다. 원색
  토큰(`--gray-500`, `--accent-600` 등)은 테마의 재료이니 쓰지 않는다.
- 길이는 모두 px 이다. 넓은 화면의 기준 폭은 768px 이다(`--breakpoint-wide`).

## 어디를 읽나

- `components/<group>/<Name>/<Name>.prompt.md`: 언제 쓰는지, 해도 되는 것과 하지 않는 것, props.
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
            run_7f3a
          </h2>
          <StatusBadge status="paused" />
        </div>
        <Switch label="calc" checked onChange={() => {}} />
        <div className="flex gap-2">
          <Button variant="secondary">거부</Button>
          <Button variant="primary">승인</Button>
        </div>
      </div>
    </Card>
  );
}
```
