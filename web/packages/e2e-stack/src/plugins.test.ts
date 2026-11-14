import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, beforeEach, expect, test } from "vitest";
import {
  copyRepoPlugins,
  markdownOutput,
  pointDocSearchAt,
  writeFixturePlugins,
} from "./plugins.ts";
import { REPO } from "./serve.ts";

const REPO_URL = "http://rag-engine:8000/mcp";
const TEST_URL = "http://127.0.0.1:43210/mcp";

let root: string;

beforeEach(() => {
  root = mkdtempSync(join(tmpdir(), "agent-os-e2e-plugins-test-"));
});

afterEach(() => {
  rmSync(root, { recursive: true, force: true, maxRetries: 5 });
});

function docSearchManifest(): string {
  return readFileSync(join(root, "mcp", "doc-search", "plugin.toml"), "utf-8");
}

/** 규칙 파일에서 `[agents.<이름>]` 표 하나의 글(머리 줄부터 다음 빈 줄 앞까지). */
function agentTable(text: string, name: string): string {
  const lines = text.split(/\r?\n/);
  const start = lines.indexOf(`[agents.${name}]`);
  if (start === -1) {
    throw new Error(`규칙 파일에 [agents.${name}] 표가 없다`);
  }
  const rest = lines.slice(start);
  const end = rest.findIndex((line) => line.trim() === "");
  return (end === -1 ? rest : rest.slice(0, end)).join("\n");
}

test("문서 검색 연결의 주소만 시험이 띄운 서버의 것으로 바뀐다", () => {
  copyRepoPlugins(REPO, root);
  const before = docSearchManifest();

  pointDocSearchAt(root, TEST_URL);

  const after = docSearchManifest();
  expect(after).toContain(`url = "${TEST_URL}"`);
  expect(after.replace(TEST_URL, REPO_URL)).toBe(before);
});

function writeDocSearchManifest(text: string): void {
  mkdirSync(join(root, "mcp", "doc-search"), { recursive: true });
  writeFileSync(join(root, "mcp", "doc-search", "plugin.toml"), text);
}

test("문서 검색 연결에서 주소 줄을 찾지 못하면 바꾸지 못하고 알린다", () => {
  writeDocSearchManifest('name = "doc-search"\n');

  expect(() => {
    pointDocSearchAt(root, TEST_URL);
  }).toThrow("주소 줄 하나를 찾지 못했다");
});

test("문서 검색 연결에 주소 줄이 둘이면 어느 쪽인지 몰라 바꾸지 못하고 알린다", () => {
  const text = `url = "${REPO_URL}"\nurl = "${REPO_URL}"\n`;
  writeDocSearchManifest(text);

  expect(() => {
    pointDocSearchAt(root, TEST_URL);
  }).toThrow("주소 줄 하나를 찾지 못했다");
  expect(docSearchManifest()).toBe(text);
});

test("픽스처의 규칙 파일은 저장소 규칙 파일의 assistant 표를 글자 그대로 든다", () => {
  writeFixturePlugins(root, "python", "server.py", join(root, "gates"));

  const fixture = readFileSync(join(root, "rules.toml"), "utf-8");
  const repo = readFileSync(join(REPO, "plugins", "rules.toml"), "utf-8");
  expect(agentTable(fixture, "assistant")).toBe(agentTable(repo, "assistant"));
});

test("마크다운 에이전트는 시험이 준 이미지 주소가 든 고정 출력을 낸다", () => {
  const url = "http://site.test/pixel.png";
  writeFixturePlugins(root, "python", "server.py", join(root, "gates"), url);

  const agent = readFileSync(join(root, "agents", "markdown", "agent.py"), "utf-8");
  expect(agent).toContain(JSON.stringify(markdownOutput(url)));
  expect(markdownOutput(url)).toContain(`](${url})`);
});
