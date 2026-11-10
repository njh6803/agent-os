// 준비가 시험에 값을 넘기는 길. 준비(globalSetup)는 러너 프로세스에서 돌고 시험은 그 뒤에 띄워진 워커에서 돈다. 워커는
// 러너의 환경을 물려받으므로 준비가 환경 변수에 적은 값을 시험이 읽는다. 변수 이름은 패키지가 박지 않는다. 앱이 이름을
// 정해 두 쪽에 같은 글자로 준다.

/** 준비가 `name` 에 값을 적는다. 시험(워커)이 뜨기 전에 불러야 한다. */
export function publish(name: string, value: string): void {
  process.env[name] = value;
}

/** 시험이 준비가 `name` 에 적은 값을 읽는다. 준비가 돌지 않았으면 던진다. */
export function received(name: string): string {
  const value = process.env[name];
  if (value === undefined) {
    throw new Error(
      `e2e 의 준비(globalSetup)가 ${name} 을 넘기지 않았다. 앱의 playwright.config.ts 로 띄운다`,
    );
  }
  return value;
}
