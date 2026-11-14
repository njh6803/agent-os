// 이미지 안의 package.json 사본에서 빌드에 쓰이지 않는 개발 의존성을 뺀다(저장소의 파일은 그대로다). 위젯을 뜰 때 빌드하는
// 이미지가 어디까지 작아지는지 보는 갈래(widget-lean)만 쓴다. 남기는 개발 의존성은 빌드가 import 하는 것(vite, Tailwind 의
// 플러그인 둘, tailwindcss, typescript)과 타입 검사가 읽는 타입 패키지다.
//
// 사용: node prune-manifests.mjs   (작업 폴더가 web/ 의 사본)

import { readFileSync, writeFileSync } from "node:fs";

const KEEP = {
  // pnpm 은 --filter 로 앱을 골라도 워크스페이스 뿌리의 의존성을 함께 깐다(deps-widget-filter 에서 봤다). 뿌리의 개발
  // 의존성(vitest, storybook, eslint, playwright 등)은 빌드가 쓰지 않아 모두 뺀다.
  "package.json": [],
  "apps/widget/package.json": [
    "@tailwindcss/postcss",
    "@tailwindcss/vite",
    "tailwindcss",
    "typescript",
    "vite",
    "@types/node",
    "@types/react",
    "@types/react-dom",
  ],
  "packages/ui/package.json": ["@types/mdast", "@types/react", "@types/react-dom", "react", "react-dom"],
};

for (const [path, keep] of Object.entries(KEEP)) {
  const manifest = JSON.parse(readFileSync(path, "utf-8"));
  const before = Object.keys(manifest.devDependencies ?? {});
  manifest.devDependencies = Object.fromEntries(
    Object.entries(manifest.devDependencies ?? {}).filter(([name]) => keep.includes(name)),
  );
  writeFileSync(path, `${JSON.stringify(manifest, null, 2)}\n`);
  const dropped = before.filter((name) => !keep.includes(name));
  console.log(`RI_PROBE pruned ${path} dropped=${dropped.join(",")}`);
}
