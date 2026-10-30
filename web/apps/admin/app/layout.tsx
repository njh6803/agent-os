import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "관리 화면",
};

// 운영자가 고른 테마를 첫 그림 전에 다는 스크립트(public/theme.js)를 막는 `<script src>` 로 싣는다(admin-style 명세 "그리기
// 전 스크립트"). `async`·`defer` 를 달지 않는다. 클라이언트 컴포넌트의 효과와 `next/script` 의 `beforeInteractive` 는 첫
// 그림 뒤에 달았다(.scratch/admin-style/probes/prepaint_theme.mjs). 그 스크립트가 서버가 그린 `<html>` 에 속성을 더하므로
// `suppressHydrationWarning` 을 단다. 그 속성은 `<html>` 하나의 경고만 끈다.
export default function RootLayout({ children }: { readonly children: ReactNode }) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <head>
        <script src="/theme.js" />
      </head>
      <body>{children}</body>
    </html>
  );
}
