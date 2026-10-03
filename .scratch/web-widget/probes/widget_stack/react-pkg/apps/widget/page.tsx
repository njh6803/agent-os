// (2) iframe 용 정적 페이지(Vite, Next 를 쓰지 않을 때의 견줌). 공유 컴포넌트는 packages/widget-ui 에서 온다.

import { ChatWidget, STYLES, targetFromLocation } from "@agent-os/widget-ui";
import { createRoot } from "react-dom/client";

const mount = document.getElementById("root");
if (mount === null) {
  throw new Error("#root 가 없다");
}
const style = document.createElement("style");
style.textContent = STYLES;
document.head.append(style);
createRoot(mount).render(<ChatWidget target={targetFromLocation(location)} />);
