// (2) Agent OS 출처의 iframe 안에서 그리는 정적 페이지. 같은 컴포넌트를 문서에 바로 그린다. 격리는 iframe 이 한다.

import { createRoot } from "react-dom/client";
import { ChatWidget } from "./components/organisms/ChatWidget";
import { STYLES } from "./lib/styles";
import { targetFromLocation } from "./lib/target";

const mount = document.getElementById("root");
if (mount === null) {
  throw new Error("#root 가 없다");
}
const style = document.createElement("style");
style.textContent = STYLES;
document.head.append(style);
createRoot(mount).render(<ChatWidget target={targetFromLocation(location)} />);
