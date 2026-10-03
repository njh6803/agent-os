// 위젯의 CSS. 후보 넷이 같은 글자를 쓴다. shadow root 안에서는 `:host` 가 호스트 요소를 가리키고, iframe 페이지의
// 문서에 그대로 넣으면 `:host` 규칙은 아무것도 맞추지 않는다.
//
// `:host { all: initial }` 은 사이트 문서에서 상속되는 속성(글꼴, 색)을 끊는다. 선택자는 shadow 경계를 넘지 않지만
// 상속은 넘기 때문이다. 사이트가 호스트 요소 자체를 겨냥한 규칙은 `:host` 보다 앞선다(shadow.mjs 가 잰다).

export const STYLES = `
:host {
  all: initial;
  display: block;
  font: 14px/1.4 system-ui, sans-serif;
  color: rgb(17, 24, 39);
}
.widget {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 320px;
  padding: 12px;
  border: 1px solid rgb(209, 213, 219);
  border-radius: 8px;
  background: rgb(255, 255, 255);
  color: rgb(17, 24, 39);
}
.messages {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 240px;
  overflow-y: auto;
}
li {
  padding: 4px 0;
}
li[data-role="user"] {
  font-weight: 600;
}
form {
  display: flex;
  gap: 4px;
}
input {
  flex: 1;
}
button {
  background: rgb(37, 99, 235);
  color: rgb(255, 255, 255);
  border: 0;
  border-radius: 4px;
  padding: 4px 12px;
}
`;
