// (b) 길의 중계 함수. 라우트 핸들러가 fetch로 상류를 부르고 본문 스트림을 그대로 돌려준다.
const upstream = process.env.PROBE_UPSTREAM ?? "http://127.0.0.1:8765";

// withSignal: request.signal을 fetch에 넘긴다(app/apisig/). 넘기지 않는 것이 기본(app/api/, app/apiopt/)
export async function relay(request: Request, prefix: string, withSignal = false): Promise<Response> {
  const incoming = new URL(request.url);
  const target = upstream + incoming.pathname.slice(prefix.length) + incoming.search;
  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  // 요청 헤더를 손대지 않고 넘긴다. 상류가 무엇을 받는지는 상류의 /echo가 되돌려 준다.
  const init: RequestInit & { duplex?: "half" } = {
    method: request.method,
    headers: request.headers,
    body: hasBody ? request.body : undefined,
    redirect: "manual",
    cache: "no-store",
  };
  if (hasBody) init.duplex = "half";
  if (withSignal) init.signal = request.signal;
  const res = await fetch(target, init);
  return new Response(res.body, { status: res.status, headers: res.headers });
}
