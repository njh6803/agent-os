// 두 명령(`start`, `make-key`)이 같이 쓰는 인자 도우미. pnpm 은 `pnpm start -- --config …` 의 구분자 두 줄표를 스크립트에
// 그대로 넘길 수 있어, 앞에 붙은 구분자는 건너뛴다. `parseArgs` 는 구분자 뒤를 위치 인자로 읽어 거부한다.

export function withoutSeparator(argv: readonly string[]): readonly string[] {
  return argv[0] === "--" ? argv.slice(1) : argv;
}
