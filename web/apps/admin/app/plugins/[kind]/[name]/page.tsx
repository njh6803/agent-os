import { PluginPage } from "../../../../components/pages/PluginPage";

interface PluginRouteProps {
  readonly params: Promise<{ readonly kind: string; readonly name: string }>;
}

export default async function Page({ params }: PluginRouteProps) {
  const { kind, name } = await params;
  return <PluginPage kind={kind} name={name} />;
}
