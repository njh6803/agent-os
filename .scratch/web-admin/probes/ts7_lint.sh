#!/usr/bin/env bash
# typescript-eslint 의 타입 기반 규칙(원칙 III 의 TS 판정자)이 TS 5.9 와 7.0 에서 도는지 잰다.
# 쓰는 법: bash .scratch/web-admin/probes/ts7_lint.sh <작업 디렉터리>
# npm 레지스트리에 닿는다. 2026-09-28 결과: 5.9.3 은 5건을 잡고 종료 1, 7.0.2 는
# "typescript-eslint does not support TS 7.0" 으로 종료 2.
set -u
work="${1:?작업 디렉터리를 준다}"
mkdir -p "$work/src" && cd "$work" || exit 1
printf '{ "name": "ts7lint", "private": true, "type": "module" }\n' > package.json
cat > tsconfig.json <<'EOF'
{ "compilerOptions": { "strict": true, "target": "ES2022", "module": "ESNext", "moduleResolution": "Bundler", "noEmit": true }, "include": ["src"] }
EOF
cat > src/a.ts <<'EOF'
const raw: string = '{"a":1}';
const x = JSON.parse(raw);
export const y: number = x.a;
export const z = raw as unknown as number;
EOF
cat > eslint.config.mjs <<'EOF'
import tseslint from 'typescript-eslint';
export default tseslint.config(
  ...tseslint.configs.strictTypeChecked,
  { languageOptions: { parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname } },
    rules: { '@typescript-eslint/consistent-type-assertions': ['error', { assertionStyle: 'never' }] } },
);
EOF
for v in 5.9.3 7.0.2; do
  npm i -s --no-audit --no-fund --legacy-peer-deps "typescript@$v" typescript-eslint@8.70.1 eslint@10.11.0 >/dev/null 2>&1
  echo "=== typescript $v ==="
  npx tsc -v
  npx eslint src
  echo "eslint exit: $?"
done
