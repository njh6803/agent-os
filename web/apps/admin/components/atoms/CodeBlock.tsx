// 코드 칸(admin-style 명세 "앱 부품"). 고정폭 글자의 `<pre>` 이고 줄을 바꿔 흘러 가로로 밀지 않는다. 긴 낱말(식별자,
// 경로)도 아무 곳에서나 줄을 바꾼다. 놓인 자리가 둘이다. 카드 밖에 홀로 선 코드 칸은 바탕 `bg-raised`, 안쪽 좁은 폭 3,
// 넓은 폭 4다(그림 mk-plugin, mk-plugin-m). 카드 안의 코드 칸은 카드의 바탕(`bg-raised`)과 갈리게 바탕 `bg`, 안쪽 3이다
// (그림 mk-decision, mk-run 의 결정 카드).

/** JSON 값을 코드 칸의 글자로 옮긴다. 두 칸 들여 쓴다. */
export function formatJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

export type CodeBlockSurface = "page" | "card";

const SURFACE_CLASS = {
  page: "bg-bg-raised p-3 wide:p-4",
  card: "bg-bg p-3",
} satisfies Record<CodeBlockSurface, string>;

interface CodeBlockProps {
  readonly children: string;
  /** 놓인 자리. 기본은 카드 밖(`page`)이다. */
  readonly surface?: CodeBlockSurface;
}

export function CodeBlock({ children, surface = "page" }: CodeBlockProps) {
  return (
    <pre
      className={`rounded-m border border-border font-mono text-mono whitespace-pre-wrap wrap-anywhere ${SURFACE_CLASS[surface]}`}
    >
      {children}
    </pre>
  );
}
