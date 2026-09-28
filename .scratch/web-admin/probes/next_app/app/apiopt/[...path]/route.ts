// (b) 길의 사본. OPTIONS도 내보내면 상류까지 가는지 재려고 둔다.
import { relay } from "../../../lib/relay";

export async function GET(request: Request): Promise<Response> {
  return relay(request, "/apiopt");
}

export async function POST(request: Request): Promise<Response> {
  return relay(request, "/apiopt");
}

export async function OPTIONS(request: Request): Promise<Response> {
  return relay(request, "/apiopt");
}
