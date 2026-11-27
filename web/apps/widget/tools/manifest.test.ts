// 위젯의 응답 머리 목록(`.next/routes-manifest.json`)을 다루는 코드(widget-runtime-values 티켓 02). 빌드가 끝날 때 원본을
// 남기는 것, 서비스 시작이 원본에서 `frame-ancestors` 값 하나만 바꾼 사본을 쓰는 것, 바꿀 자리가 기대한 모양이 아닐 때 아무것도
// 쓰지 않고 까닭을 말하는 것을 본다. 실제 `next build` 는 돌리지 않는다. 실제 빌드가 낸 목록의 모양은 위젯 e2e 의 준비가 지난다.

import { spawnSync } from "node:child_process";
import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { afterEach, beforeEach, describe, expect, test } from "vitest";
import { builtManifest } from "../testing/manifest.ts";
import { canSymlink } from "../testing/symlink.ts";
import {
  fillAncestors,
  keepOriginal,
  manifestPaths,
  PLACEHOLDER,
  writeServedManifest,
} from "./manifest.ts";

const MANIFEST = join(import.meta.dirname, "manifest.ts");

/** 이 머리 규칙의 첫 머리 값을 바꾼 목록의 글. */
function withValueAt(rule: number, value: string): string {
  const manifest = builtManifest();
  const headers = manifest["headers"];
  if (!Array.isArray(headers)) {
    throw new Error("시험의 목록에 headers 가 없다");
  }
  const target: unknown = headers[rule];
  if (typeof target !== "object" || target === null || !("headers" in target)) {
    throw new Error("시험의 목록에 그 규칙이 없다");
  }
  const list: unknown = target.headers;
  if (!Array.isArray(list)) {
    throw new Error("시험의 규칙에 headers 가 없다");
  }
  list[0] = { key: "Content-Security-Policy", value };
  return JSON.stringify(manifest);
}

function filled(text: string, origins: readonly string[]): unknown {
  const result = fillAncestors(text, origins);
  if ("problem" in result) {
    throw new Error(`바꾸지 못했다: ${result.problem}`);
  }
  return JSON.parse(result.text);
}

function problemOf(text: string, origins: readonly string[] = ["https://a.example"]): string {
  const result = fillAncestors(text, origins);
  if (!("problem" in result)) {
    throw new Error("바꿀 자리를 받아들였다");
  }
  return result.problem;
}

describe("바꿀 자리를 찾는 규칙", () => {
  test("자리가 하나이고 값이 'none' 이면 그 값만 허용 출처를 공백으로 이은 값으로 바뀐다", () => {
    const expected = builtManifest(`frame-ancestors https://a.example https://b.example:8443`);

    const result = filled(JSON.stringify(builtManifest()), [
      "https://a.example",
      "https://b.example:8443",
    ]);

    // 다른 머리 규칙(글꼴, 페이지 안 번들, 값 파일)과 머리 밖의 키는 글자 그대로다.
    expect(result).toEqual(expected);
  });

  test("허용 출처가 비면 값은 그대로 'none' 이다", () => {
    expect(filled(JSON.stringify(builtManifest()), [])).toEqual(builtManifest());
  });

  test("머리의 이름은 대소문자를 가리지 않고 견준다", () => {
    for (const key of ["content-security-policy", "CONTENT-SECURITY-POLICY"]) {
      const manifest = builtManifest();
      const headers = manifest["headers"];
      if (!Array.isArray(headers)) {
        throw new Error("시험의 목록에 headers 가 없다");
      }
      headers[0] = {
        source: "/widget/:path*",
        headers: [{ key, value: PLACEHOLDER }],
        regex: "^/widget(?:/((?:[^/]+?)(?:/(?:[^/]+?))*))?(?:/)?$",
      };

      const result = fillAncestors(JSON.stringify(manifest), ["https://a.example"]);

      if ("problem" in result) {
        throw new Error(`${key} 를 받아들이지 않았다: ${result.problem}`);
      }
      expect(result.text).toContain("frame-ancestors https://a.example");
    }
  });

  test("값이 frame-ancestors 로 시작하지 않는 Content-Security-Policy 머리는 자리로 세지 않는다", () => {
    const manifest = builtManifest();
    const headers = manifest["headers"];
    if (!Array.isArray(headers)) {
      throw new Error("시험의 목록에 headers 가 없다");
    }
    headers.push({
      source: "/widget/other",
      headers: [{ key: "Content-Security-Policy", value: "default-src 'self'" }],
      regex: "^/widget/other(?:/)?$",
    });

    const result = filled(JSON.stringify(manifest), ["https://a.example"]);

    expect(JSON.stringify(result)).toContain("default-src 'self'");
    expect(JSON.stringify(result)).toContain("frame-ancestors https://a.example");
  });

  describe("자리가 기대와 다르면 바꾸지 않고, 사이트 파일이 아니라 산출물의 문제라고 말한다", () => {
    test("자리가 없다", () => {
      const manifest = builtManifest();
      manifest["headers"] = [];

      const problem = problemOf(JSON.stringify(manifest));

      expect(problem).toContain("frame-ancestors 를 정하는 자리가 없다");
      expect(problem).toContain("사이트 파일의 문제가 아니다");
      expect(problem).toContain("위젯을 다시 띄워도 풀리지 않는다");
    });

    test("자리가 둘이다", () => {
      const manifest = builtManifest();
      const headers = manifest["headers"];
      if (!Array.isArray(headers)) {
        throw new Error("시험의 목록에 headers 가 없다");
      }
      headers.push({
        source: "/widget/second",
        headers: [{ key: "Content-Security-Policy", value: PLACEHOLDER }],
        regex: "^/widget/second(?:/)?$",
      });

      const problem = problemOf(JSON.stringify(manifest));

      expect(problem).toContain("frame-ancestors 를 정하는 자리가 둘이다");
      expect(problem).toContain("사이트 파일의 문제가 아니다");
    });

    test("값이 'none' 이 아니다. 빌드가 사이트 파일을 읽어 값을 굳힌 산출물이다", () => {
      const problem = problemOf(withValueAt(0, "frame-ancestors https://decoy.example"), [
        "https://a.example",
      ]);

      expect(problem).toContain("frame-ancestors https://decoy.example");
      expect(problem).toContain(PLACEHOLDER);
      expect(problem).toContain("사이트 파일의 문제가 아니다");
    });

    test("목록이 JSON 이 아니다", () => {
      const problem = problemOf("{ 깨진 글");

      expect(problem).toContain("JSON 으로 읽지 못했다");
      expect(problem).toContain("사이트 파일의 문제가 아니다");
    });

    test("목록에 headers 배열이 없다", () => {
      const problem = problemOf(JSON.stringify({ version: 3 }));

      expect(problem).toContain("frame-ancestors 를 정하는 자리가 없다");
    });
  });
});

describe("원본과 사본을 쓰는 자리", () => {
  let app: string;

  beforeEach(() => {
    app = mkdtempSync(join(tmpdir(), "widget-manifest-"));
    mkdirSync(join(app, ".next"));
  });

  afterEach(() => {
    rmSync(app, { recursive: true, force: true, maxRetries: 5 });
  });

  function paths() {
    return manifestPaths(app);
  }

  function seedOriginal(text = JSON.stringify(builtManifest())): void {
    writeFileSync(paths().original, text);
  }

  test("원본과 사본은 앱 폴더의 .next 안에 있고 이름이 다르다", () => {
    expect(paths().served).toBe(join(app, ".next", "routes-manifest.json"));
    expect(paths().original).not.toBe(paths().served);
    expect(paths().original.startsWith(join(app, ".next"))).toBe(true);
  });

  test("사본은 원본에서 값 하나만 바꾼 목록이고, 원본은 고치지 않는다", () => {
    const text = JSON.stringify(builtManifest());
    seedOriginal(text);

    writeServedManifest(app, { allowedOrigins: ["https://a.example"] });

    expect(JSON.parse(readFileSync(paths().served, "utf-8"))).toEqual(
      builtManifest("frame-ancestors https://a.example"),
    );
    expect(readFileSync(paths().original, "utf-8")).toBe(text);
  });

  test("다시 띄우면 앞 사본이 아니라 원본에서 새로 바꾼다", () => {
    seedOriginal();

    writeServedManifest(app, { allowedOrigins: ["https://a.example"] });
    writeServedManifest(app, { allowedOrigins: ["https://b.example"] });
    writeServedManifest(app, { allowedOrigins: [] });

    expect(JSON.parse(readFileSync(paths().served, "utf-8"))).toEqual(builtManifest());
  });

  test("원본이 없으면 아무것도 쓰지 않고 산출물에 원본이 없다고 말한다", () => {
    expect(() => {
      writeServedManifest(app, { allowedOrigins: ["https://a.example"] });
    }).toThrow("routes-manifest.original.json 이 없다");
    expect(existsSync(paths().served)).toBe(false);
  });

  test("바꿀 자리가 기대와 다르면 이미 있던 사본도 건드리지 않고 던진다", () => {
    seedOriginal(withValueAt(0, "frame-ancestors https://decoy.example"));
    writeFileSync(paths().served, "앞 사본");

    expect(() => {
      writeServedManifest(app, { allowedOrigins: ["https://a.example"] });
    }).toThrow("frame-ancestors https://decoy.example");

    expect(readFileSync(paths().served, "utf-8")).toBe("앞 사본");
  });

  // 윈도에서 링크를 만들 권한이 없으면 건너뛴 것으로 보인다(초록으로 지나가지 않는다). 리눅스의 CI 가 본다.
  test.skipIf(!canSymlink())(
    "사본의 자리가 다른 폴더 안을 가리키는 링크여도 링크를 따라가 그 폴더에 쓴다",
    () => {
      // 이미지가 읽기 전용 루트에서 쓸 자리를 `/run/agent-os-widget` 안으로 둔다(티켓 03). 이름 바꾸기로 덮으면 링크가 보통
      // 파일로 바뀌어 거기서 실패하므로, 쓰는 코드는 그 자리를 열어 바로 써야 한다.
      seedOriginal();
      const target = join(app, "run");
      mkdirSync(target);
      writeFileSync(join(target, "routes-manifest.json"), "{}");
      symlinkSync(join(target, "routes-manifest.json"), paths().served, "file");

      writeServedManifest(app, { allowedOrigins: ["https://a.example"] });

      expect(JSON.parse(readFileSync(join(target, "routes-manifest.json"), "utf-8"))).toEqual(
        builtManifest("frame-ancestors https://a.example"),
      );
    },
  );

  describe("빌드가 끝나면 원본을 남긴다", () => {
    test("빌드가 낸 목록을 원본으로 복사한다", () => {
      const text = JSON.stringify(builtManifest());
      writeFileSync(paths().served, text);

      keepOriginal(app);

      expect(readFileSync(paths().original, "utf-8")).toBe(text);
    });

    test("빌드가 목록을 남기지 않았으면 던지고 원본을 만들지 않는다", () => {
      expect(() => {
        keepOriginal(app);
      }).toThrow("응답 머리 목록을 남기지 않았다");
      expect(existsSync(paths().original)).toBe(false);
    });
  });

  // `next build` 는 `program.parse` 가 돌아온 뒤에 기다리지 않고 빌드를 마치면 `process.exit(0)` 으로 끝난다. 그래서 래퍼는
  // Next 를 부른 줄 뒤가 아니라 프로세스가 끝날 때 복사한다. 아래는 그 모양을 작은 자식 프로세스로 흉내 낸다.
  describe("프로세스가 끝날 때 원본을 남긴다", () => {
    /** 처리기를 등록한 뒤 `body` 를 돌리고 끝나는 자식 프로세스. 끝낸 종료 코드와 stderr 를 돌려준다. */
    function runChild(body: string): { status: number | null; stderr: string } {
      const script = [
        `import { keepOriginalOnExit } from ${JSON.stringify(pathToFileURL(MANIFEST).href)};`,
        `import { writeFileSync } from "node:fs";`,
        `keepOriginalOnExit(${JSON.stringify(app)});`,
        body,
      ].join("\n");
      const run = spawnSync(process.execPath, ["--input-type=module", "-e", script], {
        encoding: "utf-8",
        timeout: 30_000,
      });
      return { status: run.status, stderr: run.stderr };
    }

    const served = () => JSON.stringify(paths().served);

    test("종료 코드 0 으로 끝날 때, 등록한 뒤에 빌드가 쓴 목록을 원본으로 남긴다", () => {
      // 등록할 때는 목록이 없고, 끝나기 직전에야 쓰인다. 앞 빌드의 낡은 목록을 남기지 않는다는 뜻이다.
      writeFileSync(paths().served, "낡은 목록");

      const run = runChild(`writeFileSync(${served()}, "새 목록"); process.exit(0);`);

      expect(run.status).toBe(0);
      expect(readFileSync(paths().original, "utf-8")).toBe("새 목록");
    });

    test("실패 종료 코드로 끝나면 원본을 남기지 않는다", () => {
      writeFileSync(paths().served, "목록");

      const run = runChild("process.exit(1);");

      expect(run.status).toBe(1);
      expect(existsSync(paths().original)).toBe(false);
    });

    test("목록이 없으면 종료 코드를 1 로 바꾸고 까닭을 말한다", () => {
      const run = runChild("process.exit(0);");

      expect(run.status).toBe(1);
      expect(run.stderr).toContain("응답 머리 목록을 남기지 않았다");
      expect(existsSync(paths().original)).toBe(false);
    });
  });
});
