#!/usr/bin/env bash
# 관리 화면의 주 이음매(Vitest jsdom + MSW + openapi-fetch)가 SSE 응답을 조각으로 흘리는지 잰다.
# 쓰는 법: bash .scratch/web-admin/probes/jsdom_sse.sh <작업 디렉터리>
# npm 레지스트리에 닿는다. 재는 것은 넷이다.
#   1. MSW 가 ReadableStream 으로 낸 SSE 를 openapi-fetch 의 parseAs: "stream" 이 조각마다 받는가
#      (첫 프레임이 스트림이 닫히기 전에 도착하는가)
#   2. 같은 호출이 409 JSON 봉투를 받으면 error 에 무엇이 오는가
#   3. baseUrl 을 상대 경로("/api")로 주면 jsdom 에서 요청이 서는가
#   4. jsdom 의 sessionStorage 가 있는가
set -u
work="${1:?작업 디렉터리를 준다}"
mkdir -p "$work" && cd "$work" || exit 1
printf '{ "name": "jsdom-sse", "private": true, "type": "module" }\n' > package.json
cat > probe.test.ts <<'EOF'
// @vitest-environment jsdom
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import createClient from 'openapi-fetch';
import { afterAll, beforeAll, expect, test } from 'vitest';

type paths = {
  '/runs/{run_id}/approval': {
    post: {
      parameters: { path: { run_id: string } };
      requestBody: { content: { 'application/json': { decision: 'approve'; at: number } } };
      responses: {
        200: { content: { 'text/event-stream': unknown } };
        409: { content: { 'application/json': { code: string; message: string } } };
      };
    };
  };
};

const encoder = new TextEncoder();
const frames = ['approval_granted', 'run_resumed', 'tool_called', 'run_finished'];
let streamClosedAt = 0;

const server = setupServer(
  http.post('*/api/runs/:runId/approval', async ({ params, request }) => {
    const body = (await request.json()) as { at: number };
    if (params.runId === 'stale' || body.at !== 2) {
      return HttpResponse.json({ code: 'conflict', message: '자리가 다르다' }, { status: 409 });
    }
    const stream = new ReadableStream<Uint8Array>({
      async start(controller) {
        for (const type of frames) {
          controller.enqueue(encoder.encode(`data: {"type":"${type}"}\r\n\r\n`));
          await new Promise((r) => setTimeout(r, 100));
          controller.enqueue(encoder.encode(': ping\r\n\r\n'));
        }
        streamClosedAt = performance.now();
        controller.close();
      },
    });
    return new HttpResponse(stream, { headers: { 'Content-Type': 'text/event-stream' } });
  }),
);
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterAll(() => server.close());

test('sessionStorage 와 location', () => {
  sessionStorage.setItem('k', 'v');
  console.log('PROBE location.origin =', location.origin, 'sessionStorage =', sessionStorage.getItem('k'));
});

test('상대 baseUrl', async () => {
  const client = createClient<paths>({ baseUrl: '/api' });
  try {
    await client.POST('/runs/{run_id}/approval', {
      params: { path: { run_id: 'r1' } }, body: { decision: 'approve', at: 2 }, parseAs: 'stream',
    });
    console.log('PROBE relative baseUrl: ok');
  } catch (e) {
    console.log('PROBE relative baseUrl: threw', String(e));
  }
});

test('스트림이 조각으로 온다', async () => {
  const client = createClient<paths>({ baseUrl: new URL('/api', location.origin).href });
  const { data, error, response } = await client.POST('/runs/{run_id}/approval', {
    params: { path: { run_id: 'r1' } }, body: { decision: 'approve', at: 2 }, parseAs: 'stream',
  });
  console.log('PROBE status', response.status, 'content-type', response.headers.get('content-type'), 'error', error);
  const reader = (data as ReadableStream<Uint8Array>).getReader();
  const decoder = new TextDecoder();
  const arrivals: Array<[number, string]> = [];
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    arrivals.push([performance.now(), decoder.decode(value)]);
  }
  const firstData = arrivals.find(([, text]) => text.includes('data:'));
  console.log('PROBE chunks', arrivals.length, 'first data at', firstData?.[0], 'stream closed at', streamClosedAt);
  console.log('PROBE first data before close:', (firstData?.[0] ?? Infinity) < streamClosedAt);
  expect(firstData).toBeDefined();
});

test('409 봉투', async () => {
  const client = createClient<paths>({ baseUrl: new URL('/api', location.origin).href });
  const { data, error, response } = await client.POST('/runs/{run_id}/approval', {
    params: { path: { run_id: 'stale' } }, body: { decision: 'approve', at: 1 }, parseAs: 'stream',
  });
  console.log('PROBE 409 status', response.status, 'data', typeof data, 'error', JSON.stringify(error));
});
EOF
npm i -s --no-audit --no-fund vitest jsdom msw openapi-fetch typescript@5.9 >/dev/null 2>&1
echo "=== versions ==="
for p in vitest jsdom msw openapi-fetch typescript; do
  printf '%s ' "$p"; node -p "require('./node_modules/$p/package.json').version"
done
node --version
npx vitest run --reporter=verbose 2>&1 | grep -E "PROBE|✓|×|FAIL|Error|passed|failed"
