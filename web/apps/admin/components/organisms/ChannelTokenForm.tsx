import { useTokens } from "../../stores/tokens";

const FIELD = "channelToken";

/**
 * 채널 토큰을 넣는 자리. 선택이다. 넣지 않아도 관리 화면의 나머지를 모두 쓰고, 넣으면 멈춘 실행에 결정 자리가 설 수
 * 있다(web-admin 스토리 4, 5. 서는 조건은 `RunDecision` 이 든다). 확인할 채널의 읽기 경로가 없어(ADR 0014) 넣을 때
 * 확인하지 않는다. 틀린 채널 토큰은 첫 결정의 401 로 드러나고, 그때 이 자리가 다시 선다.
 *
 * 토큰은 헤더에만 실린다(스토리 9). 관리 토큰을 넣는 자리처럼 가린 입력이고 값을 React 상태로 들지 않으며, 넣는
 * 즉시 칸을 비운다. 폼은 보내지 않고 가로채므로 토큰이 주소의 질의로 가지 않는다.
 */
export function ChannelTokenForm() {
  const channelToken = useTokens((state) => state.channelToken);
  const accept = useTokens((state) => state.acceptChannelToken);

  if (channelToken !== null) {
    return <span>채널 토큰을 넣었다</span>;
  }
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const token = new FormData(form).get(FIELD);
        form.reset();
        if (typeof token === "string" && token.trim() !== "") {
          accept(token);
        }
      }}
    >
      <label>
        채널 토큰 <input type="password" name={FIELD} autoComplete="off" required />
      </label>
      <button type="submit">채널 토큰 넣기</button>
      <small>
        선택이다. <code>AGENT_OS_CHANNEL_TOKEN</code> 의 값을 넣으면 멈춘 실행에 결정을 낼 수 있다.
      </small>
    </form>
  );
}
