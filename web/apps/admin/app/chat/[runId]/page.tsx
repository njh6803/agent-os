import { ConversationPage } from "../../../components/pages/ConversationPage";

interface ChatRouteProps {
  readonly params: Promise<{ readonly runId: string }>;
}

export default async function Page({ params }: ChatRouteProps) {
  const { runId } = await params;
  return <ConversationPage runId={runId} />;
}
