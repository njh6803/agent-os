// (b) 길: 라우트 핸들러. OPTIONS는 내보내지 않는다(Next가 자동으로 답하는지 재려고).
// OPTIONS까지 내보내는 사본은 app/apiopt/[...path]/route.ts.
import { relay } from "../../../lib/relay";

export async function GET(request: Request): Promise<Response> {
  return relay(request, "/api");
}

export async function POST(request: Request): Promise<Response> {
  return relay(request, "/api");
}
