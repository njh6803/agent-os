// 코드 칸(admin-style 명세 "앱 부품"). 고정폭 글자의 `<pre>` 이고 줄을 바꿔 흘러 가로로 밀지 않는다. 긴 낱말(식별자,
// 경로)도 아무 곳에서나 줄을 바꾼다. 바탕과 안쪽은 카드 밖에 홀로 선 코드 칸의 것이다(바탕 `bg-raised`, 안쪽 좁은 폭 3,
// 넓은 폭 4, 그림 mk-plugin, mk-plugin-m). 카드 안의 코드 칸은 그림에서 바탕 `bg`, 안쪽 3이라 그 갈래는 07·08이 든다.

/** JSON 값을 코드 칸의 글자로 옮긴다. 두 칸 들여 쓴다. */
export function formatJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

export function CodeBlock({ children }: { readonly children: string }) {
  return (
    <pre className="rounded-m border border-border bg-bg-raised p-3 font-mono text-mono whitespace-pre-wrap wrap-anywhere wide:p-4">
      {children}
    </pre>
  );
}
