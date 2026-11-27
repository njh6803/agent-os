/**
 * 주체 이름 `<발급자>|<sub>` 의 구분자. 서버의 `PRINCIPAL_SEPARATOR`(`agent_os.http.sites`)와 같은 글자이고 sdk 계약
 * 밖의 결합이다. 구분자를 바꾸는 결정은 이것을 함께 바꾼다(`.claude/rules/web-admin.md`).
 */
const PRINCIPAL_SEPARATOR = "|";

/**
 * 주체가 최종 사용자인지. 최종 사용자가 아닌 주체는 OS 사용자 이름이고, `serve`·`run`·`resume` 이 그 이름에 이 글자를
 * 금지한다(end-user-channel 티켓 01). 그래서 그 가드 뒤에 쓴 트레이스에서 이것이 든 주체는 최종 사용자다. 실행 하나는 그
 * 시작 이벤트의 주체로, 대화는 첫 실행의 주체로 본다(대화 목록의 `principal`).
 */
export function isEndUserPrincipal(principal: string): boolean {
  return principal.includes(PRINCIPAL_SEPARATOR);
}
