import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "위젯",
};

// 문서 뿌리의 테마·모드·밀도는 iframe 페이지(components/pages/WidgetPage)가 질의를 읽어 단다. 위젯은 iframe 의 크기를
// 채우므로 html 과 body 가 그 높이를 잇는다.
export default function RootLayout({ children }: { readonly children: ReactNode }) {
  return (
    <html lang="ko" className="h-full">
      <body className="h-full">{children}</body>
    </html>
  );
}
