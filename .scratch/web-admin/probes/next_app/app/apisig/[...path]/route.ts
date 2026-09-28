// (b) 길의 사본. request.signal을 fetch에 넘긴다(클라이언트 끊김이 상류로 가는지 재려고).
import { relay } from "../../../lib/relay";

export async function GET(request: Request): Promise<Response> {
  return relay(request, "/apisig", true);
}

export async function POST(request: Request): Promise<Response> {
  return relay(request, "/apisig", true);
}
