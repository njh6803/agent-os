import { ConversationPage } from "../../../components/pages/ConversationPage";

// `/chat/new` 는 `/chat/[runId]` 보다 먼저 맞는 고정 주소다. 끝 실행이 없는 새 대화다.
export default function Page() {
  return <ConversationPage runId={null} />;
}
