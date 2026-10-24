# 위젯 임베드 안내

사이트 개발자가 Agent OS의 위젯을 자기 페이지에 넣을 때 읽는 문서다. 서버 코드를 읽지 않고 이 문서만으로 붙일 수 있게 쓴다. 아래에서 `https://widget.example`은 운영자가 알려 준 위젯 출처를 뜻한다. 위젯 페이지와 최종 사용자 경로(`/end-user`)가 그 출처 하나 아래에 있다.

## 목차

1. [두 방식](#두-방식)
2. [페이지 안 방식](#페이지-안-방식)
3. [iframe 방식](#iframe-방식)
4. [속성](#속성)
5. [서명 토큰](#서명-토큰)
6. [운영자에게 넘길 것](#운영자에게-넘길-것)
7. [허용 출처의 표기](#허용-출처의-표기)
8. [사이트의 CSP](#사이트의-csp)
9. [지킬 것](#지킬-것)

## 두 방식

|                     | 페이지 안 방식                                                                  | iframe 방식                                    |
| ------------------- | ------------------------------------------------------------------------------- | ---------------------------------------------- |
| 넣는 것             | `<script>` 한 줄과 `<agent-os-widget>` 요소 하나                                | `<iframe>` 하나                                |
| 그리는 자리         | 사이트 문서 안의 shadow root                                                    | 위젯 출처의 별도 문서                          |
| 토큰을 주는 길      | 요소의 속성(property) `tokenProvider`에 함수를 준다                             | 위젯이 postMessage로 묻고 사이트가 답한다      |
| 품을 수 있는 페이지 | 어느 페이지든 번들을 실을 수 있다. 요청은 허용 출처의 페이지에서만 읽힌다(CORS) | 허용 출처의 페이지만 품는다(`frame-ancestors`) |

두 방식의 화면과 속성은 같다. 사이트의 CSS와 위젯의 CSS가 서로를 건드리지 않는 것도 같다.

## 페이지 안 방식

```html
<agent-os-widget
  agent="order-helper"
  heading="주문 도우미"
  intro="주문을 찾아 드립니다."
></agent-os-widget>
<script src="https://widget.example/widget/element.js"></script>
<script>
  document.querySelector("agent-os-widget").tokenProvider = async () => {
    // 사이트 백엔드가 그 사용자에게 새로 서명한 토큰을 받는다(아래 "서명 토큰").
    const response = await fetch("/my-backend/agent-os-token");
    return response.text();
  };
</script>
```

- **번들은 위젯 출처의 `<script src>`로 싣는다.** 번들은 처음 실행될 때 자기 `<script>`의 `src`에서 위젯 출처를 읽어 요청을 그 아래 `/end-user`로 보낸다. 번들 파일을 사이트의 서버로 옮겨 내면 요청이 사이트 출처로 간다. `type="module"`로 싣거나 내용을 인라인으로 붙여도 출처를 읽지 못한다. HTML 표준은 `async`·`defer`를 붙이거나 스크립트로 만든 classic `<script>`에도 실행하는 동안 `document.currentScript`를 세우므로 그렇게 실어도 된다(위젯 e2e는 페이지에 바로 적은 `<script>`만 잰다). 다만 번들의 `<script>`를 사이트의 shadow root 안에 넣으면 표준이 `document.currentScript`를 null로 두어 위젯이 서지 않는다. 문서에 바로 넣는다.
- **`crossorigin="anonymous"`를 붙여도 된다.** 번들 응답에는 `Access-Control-Allow-Origin: *`가 붙는다. 무결성 검사(`integrity`)도 그 위에서 쓸 수 있지만, 번들은 운영자의 사이트 파일 값(요청 글자 수 상한)을 담아 빌드되므로 운영자가 위젯을 다시 빌드할 때마다 해시를 새로 받아 바꿔야 한다. 바꾸지 않으면 번들이 실리지 않는다.
- **`tokenProvider`는 번들이 실리기 전에 줘도, 뒤에 줘도 된다.** 위젯은 요청을 보낼 때마다 이 함수를 부른다. 함수의 꼴은 `() => Promise<string>`이다. 함수가 없거나, 던지거나, 거부되거나, 문자열이 아닌 값을 주거나, 10초 안에 답하지 않으면 위젯은 요청을 보내지 않고 "로그인 정보를 받지 못했습니다." 알림을 보인다.
- **크기는 사이트가 정한다.** 요소는 `display: block`이고 위젯은 요소의 자리를 채운다. 폭과 높이를 CSS로 준다. 지원하는 가장 좁은 폭은 320px이고, 높이는 560px쯤이 화면 디자인의 예시다.
- **위젯은 `open` 모드의 shadow root에 그린다.** 사이트의 선택자는 위젯 안에 닿지 않는다. 글자 크기·글자 간격처럼 물려지는 속성은 위젯이 다시 정하고, 위젯은 길이를 `rem`으로 쓰지 않아 사이트의 `html { font-size }`와 무관하게 크기가 같다.
- **글꼴은 위젯 출처의 `/widget/fonts/`에서 받는다.** 위젯만 쓰는 family 이름(`agent-os-widget-sans`, `agent-os-widget-mono`)으로 사이트 문서에 등록하므로 사이트의 글꼴 이름을 덮지 않는다.
- **번들의 `<script>`보다 앞에 `name="currentScript"`인 요소(`img`, `form`, `iframe`, `embed`, `object`처럼 이름으로 `document`에 드러나는 요소)가 있으면 위젯은 서지 않는다.** `document`의 이름 있는 속성이 `document.currentScript`를 가려 번들이 자기 `<script>`를 찾지 못한다(DOM clobbering). 그런 요소의 `src`를 위젯 출처로 쓰면 토큰이 남의 출처로 가므로, 위젯은 토큰 함수를 부르지도 요청을 보내지도 않고 "위젯 설정이 올바르지 않습니다." 알림과 `document.currentScript`를 든 `console.error`를 남긴다. 사용자 글을 `name` 속성을 남기는 새니타이저로 그리는 페이지라면 그 속성을 걸러 낸다.

## iframe 방식

```html
<iframe
  id="agent-os-widget"
  title="주문 도우미"
  src="https://widget.example/widget?agent=order-helper&heading=%EC%A3%BC%EB%AC%B8%20%EB%8F%84%EC%9A%B0%EB%AF%B8"
  style="width: 400px; height: 560px; border: 0"
></iframe>
<script>
  const WIDGET_ORIGIN = "https://widget.example";
  const frame = document.getElementById("agent-os-widget");
  window.addEventListener("message", async (event) => {
    const data = event.data;
    if (
      event.source !== frame.contentWindow ||
      event.origin !== WIDGET_ORIGIN ||
      !data ||
      data.type !== "agent-os/token-request"
    ) {
      return;
    }
    const token = await (await fetch("/my-backend/agent-os-token")).text();
    frame.contentWindow.postMessage({ type: "agent-os/token", id: data.id, token }, WIDGET_ORIGIN);
  });
</script>
```

- **질의의 이름과 뜻은 [속성](#속성)과 같다.** 값은 URL 인코딩한다.
- **postMessage의 약속은 둘이다.** 위젯은 토큰이 필요할 때마다 부모 창에 `{type: "agent-os/token-request", id}`를 보낸다. `id`는 요청마다 새 무작위 문자열이다. 이 메시지에는 비밀이 없어 위젯은 대상 출처를 `"*"`로 둔다. 사이트는 `{type: "agent-os/token", id, token}`으로 답한다.
- **사이트가 지킬 것.** 답은 그 iframe의 창(`frame.contentWindow`)에만, 대상 출처를 위젯 출처로 적어 보낸다. `"*"`로 보내면 그 사이에 iframe이 다른 페이지로 옮겨졌을 때 토큰이 그 페이지로 간다. `id`는 받은 그대로 돌려준다. 묻는 메시지도 보낸 창이 그 iframe인지 먼저 본다.
- **토큰을 줄 수 없으면 `token`에 `null`을 담아 답한다.** 위젯이 곧바로 "로그인 정보를 받지 못했습니다." 알림을 보인다. 답하지 않아도 10초 뒤 같은 알림이 선다.
- **위젯은 부모 창이 보내고 출처가 허용 출처이며 `id`가 맞는 답만 받는다.** 나머지는 버린다. 허용 출처가 아닌 페이지는 애초에 iframe을 품지 못한다. 위젯 페이지의 `frame-ancestors`가 허용 출처만 적는다.

## 속성

페이지 안 방식은 요소의 속성(attribute), iframe 방식은 질의로 준다. 이름과 뜻이 같다.

| 이름      | 뜻                                                                               | 없거나 잘못 주면                                                                                        |
| --------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `agent`   | 에이전트 이름. 필수. `^[a-z][a-z0-9-]{1,62}$`를 지나야 한다                      | "위젯 설정이 올바르지 않습니다." 알림을 보이고 입력창을 막는다. 속성 이름을 든 `console.error`를 남긴다 |
| `heading` | 위쪽 띠에 보일 이름                                                              | 없으면 `agent` 값이다                                                                                   |
| `intro`   | 첫 화면에 보일 할 수 있는 일 한 줄                                               | 없으면 그 줄을 그리지 않는다                                                                            |
| `theme`   | `guncheong`(군청), `nokcheong`(녹청), `jacho`(자초), `jjokbit`(쪽빛) 가운데 하나 | 없으면 `nokcheong`이다. 목록 밖이면 `nokcheong`으로 그리고 `console.error`를 남긴다                     |
| `mode`    | `light` 또는 `dark`                                                              | 없으면 시스템 설정을 따른다. 목록 밖이면 시스템 설정으로 그리고 `console.error`를 남긴다                |

HTML 전역 속성 `title`은 요소 전체에 말풍선을 띄우므로 쓰지 않는다. 이름은 `heading`이다.

## 서명 토큰

토큰은 사이트 백엔드가 RS256으로 서명한 JWT다. 개인 키는 사이트 백엔드에만 두고 브라우저에 내리지 않는다. 서버는 공개 키만 들어 토큰을 만들 수 없다.

```json
{ "alg": "RS256", "typ": "JWT", "kid": "2026-10" }
```

```json
{
  "iss": "https://shop.example",
  "sub": "user-8f3a2c",
  "aud": "agent-os",
  "iat": 1792800000,
  "exp": 1792800300
}
```

- **알고리즘은 RS256 하나다.** 다른 알고리즘(`none`, HS256 등)은 받지 않는다.
- **클레임 다섯이 모두 있어야 한다.** `iss`는 운영자에게 알린 발급자이고 `|` 글자가 들 수 없다. `aud`는 운영자와 정한 대상이다. `sub`는 사용자 식별자다(아래). `iat`와 `exp`는 초 단위 시각(NumericDate)이다. `nbf`는 넣지 않아도 되고, 넣으면 서버가 본다.
- **수명(`exp - iat`)은 600초 이하다.** 서버는 시계 차이를 30초까지 봐준다. 요청마다 `tokenProvider`나 postMessage로 새 토큰을 받으므로 짧게 둔다. 이미 열린 응답 스트림은 토큰이 만료돼도 끊기지 않는다.
- **`sub`는 사이트가 인증한, 오래 가는 사용자 식별자여야 한다.** 이것은 사이트의 의무다. 서버는 `발급자|sub`를 그 사용자로 보고 실행의 주인과 사용자별 상한을 가른다. 로그인하지 않은 방문자에게 페이지마다 새 `sub`를 주면 사용자별 상한이 묶지 못한다. 그때도 사이트별 합계와 전역 상한은 걸린다.
- **`kid`로 키를 고른다.** 운영자가 사이트에 키를 여럿 올리면 토큰 헤더의 `kid`가 그 가운데 하나를 고른다. 헤더에 `kid`가 없으면 서버는 그 사이트의 키를 차례로 시도한다. `kid` 없는 키는 사이트마다 하나까지다. 키를 바꿀 때는 새 공개 키를 새 `kid`로 먼저 올리고, 새 키로 서명하기 시작한 뒤, 옛 키로 마지막 토큰에 서명하고 11분이 지나면 옛 키를 내린다. 서버는 `exp`가 지난 뒤에도 30초를 더 받고 30초 앞선 `iat`도 받으므로, 수명 600초에 시계 여유 두 몫을 더한 값이다.
- **실패하면 401이고 까닭은 말하지 않는다.** 만료인지 서명인지 밖에 말하면 토큰을 다듬어 가며 검증 단계를 알아낼 수 있어서다. 까닭은 운영자의 서버 기록에 남는다. 위젯은 "로그인 정보를 받지 못했습니다." 알림을 보인다.

키 쌍과 토큰을 짓는 예는 위젯 e2e의 `e2e/token.ts`다. Node의 `node:crypto`만 쓴다.

## 운영자에게 넘길 것

운영자는 아래 값을 서버의 사이트 파일에 적는다. 위젯도 같은 파일로 빌드된다.

- 발급자(`iss`에 넣을 값). `|`가 들지 않는다.
- 대상(`aud`에 넣을 값). 운영자와 정한다.
- 공개 키. SubjectPublicKeyInfo PEM이고, 키마다 `kid`를 함께 준다.
- 허용 출처. 위젯을 넣을 페이지의 출처 목록이다. 표기는 아래 절을 따른다.
- 열 에이전트의 이름 목록.

## 허용 출처의 표기

허용 출처는 브라우저가 `Origin` 헤더에 싣는 글자 그대로 적는다. 다른 표기는 CORS와 `frame-ancestors`에서 아무 페이지와도 맞지 않는다.

- 스킴은 `http`나 `https`다.
- 호스트는 소문자 ASCII다. 국제화 도메인은 퓨니코드(`xn--`)로 적는다.
- 기본 포트(`http`의 80, `https`의 443)는 적지 않는다. 다른 포트는 앞에 0 없이 65535 이하의 십진수로 적는다.
- 경로, 끝 슬래시, 질의, 조각, 사용자 정보, `*`, `null`이 없다.

맞는 표기는 `https://shop.example`, `https://shop.example:8443`이다. `https://Shop.example`, `https://shop.example/`, `https://shop.example:443`, `https://shop.example:08443`, `https://*.shop.example`은 서버가 받지 않는다.

**호스트는 영문자·숫자·하이픈으로 된 이름을 쓴다.** IP 주소인 호스트(`http://192.168.0.10:8080`, 대괄호로 적는 IPv6)와 CSP의 문법 밖인 호스트(밑줄, `$`, 빈 라벨이 든 것)의 출처는 서버가 받아도 iframe 방식에서 맞지 않을 수 있다. CSP3(2026-09-16 Working Draft)의 문법은 호스트 글자를 그 셋으로 두고, `frame-ancestors`의 호스트 대조는 호스트가 도메인이 아니면 맞지 않는다고 적는다. IP 주소 가운데 실제로 맞는 것은 `127.0.0.1`뿐이라고 같은 원문의 노트가 적는다. `;`나 `,`가 든 호스트는 그 출처 하나로 그치지 않는다. CSP 헤더가 그 글자에서 지시문이나 정책을 갈라, 헤더에서 그 글자 뒤에 오는 출처까지 모두 `frame-ancestors`에서 빠진다. 규칙 전체와 근거는 저장소의 `tests/fixtures/site_file/README.md`에 있다.

## 사이트의 CSP

사이트 페이지에 CSP가 있으면 위젯 출처를 아래 자리에 연다.

| 방식      | 자리          | 왜                                                                               |
| --------- | ------------- | -------------------------------------------------------------------------------- |
| 페이지 안 | `script-src`  | 번들(`/widget/element.js`)을 싣는다                                              |
| 페이지 안 | `connect-src` | 위젯이 최종 사용자 경로(`/end-user`)를 부른다                                    |
| 페이지 안 | `font-src`    | 위젯의 글꼴(`/widget/fonts/`)을 받는다                                           |
| iframe    | `frame-src`   | 위젯 페이지(`/widget`)를 품는다. iframe 안의 요청은 사이트의 CSP를 따르지 않는다 |

```
Content-Security-Policy: script-src 'self' https://widget.example; connect-src 'self' https://widget.example; font-src https://widget.example
```

- **위 예처럼 `tokenProvider`를 인라인 `<script>`로 주면 그 script도 `script-src`에 막힌다.** 사이트의 파일로 옮기거나 nonce·해시로 연다. 막히면 위젯은 토큰을 받지 못해 "로그인 정보를 받지 못했습니다." 알림을 보인다.
- **Chromium에서는 `style-src`에 더할 것이 없었다.** 위젯의 스타일은 shadow root에 붙인 구성 스타일시트이고, 사이트의 `style-src 'self'`가 그것을 막지 않았다. 위젯 e2e가 `default-src 'none'`에 위의 세 자리와 `style-src 'self'`, `img-src 'self'`(브라우저가 스스로 받는 파비콘)만 연 페이지에서 위젯이 디자인 토큰으로 칠해지고 CSP 위반이 하나도 없는 것을 본다. Firefox·Safari는 재지 않았다.
- **CSP가 글꼴을 막으면 시스템 글꼴로 그린다.** 위젯은 그대로 쓸 수 있다.

## 지킬 것

- **같은 에이전트의 위젯을 한 페이지에 둘 두지 않는다.** 지원하지 않는 배치다. 위젯이 대화를 브라우저에 남기면 저장의 키가 에이전트로 갈려 둘이 한 저장을 나눠 쓰게 된다(지금 판은 아직 대화를 남기지 않는다). 다른 에이전트의 위젯은 함께 둘 수 있다.
- **사이트가 코드에 적거나 읽는 이름과 경로가 공개 표면이다.** 속성 다섯(`agent`, `heading`, `intro`, `theme`, `mode`), postMessage의 `type` 둘(`agent-os/token-request`, `agent-os/token`)과 그 메시지의 `id`·`token`, 페이지 안 방식의 요소 이름(`agent-os-widget`)과 `tokenProvider`, 번들 경로(`/widget/element.js`)가 그 예다. 이것을 바꿀 때 위젯은 옛 이름을 한동안 함께 받는다. 사이트가 한꺼번에 고치지 않아도 위젯이 멈추지 않게 하기 위해서다.
