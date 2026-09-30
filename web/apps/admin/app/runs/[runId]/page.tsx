import { RunPage } from "../../../components/pages/RunPage";

interface RunRouteProps {
  readonly params: Promise<{ readonly runId: string }>;
}

export default async function Page({ params }: RunRouteProps) {
  const { runId } = await params;
  return <RunPage runId={runId} />;
}
