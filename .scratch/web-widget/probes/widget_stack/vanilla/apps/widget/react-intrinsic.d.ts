// Next 페이지(React 19 JSX)에서 커스텀 요소 이름을 쓰기 위한 보강. 판정자의 no-namespace 는 .d.ts 의 선언을 허용하고
// .ts·.tsx 에 두면 빨갛다(judge.mjs 의 intrinsic-ts·intrinsic-dts).

import type { DetailedHTMLProps, HTMLAttributes } from "react";

declare module "react" {
  namespace JSX {
    interface IntrinsicElements {
      "agent-os-widget": DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement> & {
        readonly "api-base"?: string;
        readonly agent?: string;
        readonly token?: string;
      };
    }
  }
}
