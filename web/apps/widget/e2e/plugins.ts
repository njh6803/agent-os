// 위젯 e2e 의 임시 플러그인 루트(web-widget 명세 Testing Decisions 4). 에이전트는 모델 없이 돈다. MCP 매니페스트가 이
// 기계의 파이썬 인터프리터 경로를 들어야 해서 커밋하지 않고 임시 디렉터리에 쓴다(관리 화면 e2e 의 stack.ts 와 같다).
//
// - `tools` 는 MCP 픽스처 서버의 add 를 `ctx.tool()` 로 직접 두 번 부른다. 둘째 앞에서 문 폴더에 요청과 같은 이름의
//   파일이 생기기를 기다린다. 그 사이에 첫 도구 줄이 화면에 서 있는지를 시험이 본다(도구 줄이 결말 전에 선다).
// - `html` 은 실행되면 흔적을 남기는 HTML 조각을 출력으로 낸다. 위젯이 그것을 글로 보이는지를 시험이 본다.
// - `echo` 는 받은 요청의 글자 수를 낸다. 서버에 직접 보내는 글자 수 상한의 사례가 쓴다.
//
// TOML 기본 문자열과 파이썬 문자열 리터럴은 JSON 문자열과 이스케이프가 같아 경로를 `JSON.stringify` 로 적는다(윈도우
// 경로의 역슬래시).

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

export const AGENTS = ["tools", "html", "echo"] as const;
/** `html` 에이전트의 출력. 실행되면 iframe 창의 `__widgetE2ePwned` 가 선다. */
export const HTML_OUTPUT =
  '<img src="x" onerror="window.__widgetE2ePwned = 1"><script>window.__widgetE2ePwned = 2</script>';

export function writeFixturePlugins(
  root: string,
  python: string,
  mcpServer: string,
  gates: string,
): void {
  const write = (path: string, text: string): void => {
    mkdirSync(dirname(join(root, path)), { recursive: true });
    writeFileSync(join(root, path), text);
  };
  const manifest = (kind: string, name: string, extra = ""): string =>
    `schema_version = "1"\nkind = "${kind}"\nname = "${name}"\nversion = "0.1.0"\n${extra}`;
  const agent = (
    name: string,
    extra: string,
    imports: readonly string[],
    body: readonly string[],
  ) => {
    write(
      `agents/${name}/plugin.toml`,
      manifest("agent", name, `entrypoint = "agent:Agent"\n${extra}`),
    );
    write(
      `agents/${name}/agent.py`,
      [
        ...imports,
        "from collections.abc import AsyncIterator",
        "",
        "from agent_os.sdk import AgentContext, Event, RunFinished",
        "",
        "",
        "class Agent:",
        "    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:",
        ...body.map((line) => `        ${line}`),
        "",
      ].join("\n"),
    );
  };

  agent(
    "tools",
    'mcp = ["fixture"]\n',
    ["import asyncio", "from pathlib import Path"],
    [
      'first = await ctx.tool("add", a=2, b=3)',
      `gate = Path(${JSON.stringify(gates)}) / Path(request).name`,
      "while not gate.exists():",
      "    await asyncio.sleep(0.1)",
      'second = await ctx.tool("add", a=4, b=5)',
      'yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=f"{first}/{second}")',
    ],
  );
  agent(
    "html",
    "",
    [],
    [`yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=${JSON.stringify(HTML_OUTPUT)})`],
  );
  agent(
    "echo",
    "",
    [],
    ['yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=f"chars:{len(request)}")'],
  );
  write(
    "mcp/fixture/plugin.toml",
    manifest(
      "mcp",
      "fixture",
      `[server]\ncommand = ${JSON.stringify(python)}\nargs = [${JSON.stringify(mcpServer)}]\n`,
    ),
  );
}
