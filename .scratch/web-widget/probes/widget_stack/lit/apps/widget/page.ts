// (2) Agent OS 출처의 iframe 안에서 그리는 정적 페이지. 같은 커스텀 요소를 문서에 둔다(그 안은 shadow root 다).

import "./element";
import { targetFromLocation } from "./lib/target";

const target = targetFromLocation(location);
const widget = document.createElement("agent-os-widget");
widget.setAttribute("api-base", target.baseUrl);
widget.setAttribute("agent", target.agent);
widget.setAttribute("token", target.token);
document.body.append(widget);
