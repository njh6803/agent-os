// (2) Agent OS 출처의 iframe 안에서 그리는 정적 페이지(Vite). 같은 컴포넌트를 문서에 바로 그린다. 격리는 iframe 이
// 한다. CSS 는 element 와 같은 원본을 Vite 가 파일로 뽑는다.

import { createRoot } from "react-dom/client";
import { ChatWidget } from "./components/organisms/ChatWidget";
import { targetFromLocation } from "./lib/target";
import "./styles/widget.css";

const mount = document.getElementById("root");
if (mount === null) {
  throw new Error("#root 가 없다");
}
createRoot(mount).render(<ChatWidget target={targetFromLocation(location)} />);
