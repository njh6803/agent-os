// 비밀번호 규칙 목록(admin-login 명세 "계정 화면과 내 비밀번호", 그림 mk-set-password-states). 처음부터 보이고 규칙 넷마다
// 맞음과 맞지 않음을 글자로 적는다. 색만으로 가르지 않고 아이콘 모양과 글자를 함께 쓴다. 눌러 보내기 전에는 맞지 않는 규칙을
// 흐린 색으로 두고(아직 틀린 것이 아니다), 눌러 본 뒤에야 위험 색으로 바꾼다.
import { Icon } from "@agent-os/ui";
import type { PasswordCheck } from "./passwordRules";

const RULES = [
  { key: "length", text: "8자 이상" },
  { key: "upper", text: "영문 대문자 1자 이상" },
  { key: "digit", text: "숫자 1자 이상" },
  { key: "special", text: "특수문자 1자 이상" },
] as const satisfies readonly { key: "length" | "upper" | "digit" | "special"; text: string }[];

interface PasswordRuleListProps {
  readonly check: PasswordCheck;
  /** 보내 본 적이 있다. 참이면 맞지 않는 규칙이 위험 색으로 보인다. */
  readonly submitted: boolean;
}

export function PasswordRuleList({ check, submitted }: PasswordRuleListProps) {
  return (
    <ul aria-label="비밀번호 규칙" className="m-0 flex list-none flex-col gap-1 p-0">
      {RULES.map(({ key, text }) => {
        const met = check[key];
        const tone = met ? "text-success" : submitted ? "text-danger" : "text-text-muted";
        return (
          <li key={key} className="flex items-center gap-2 text-small">
            <span className={`flex items-center ${tone}`}>
              <Icon name={met ? "circle-check" : submitted ? "circle-x" : "circle"} size="16" />
            </span>
            <span className={met || !submitted ? "" : "text-danger"}>{text}</span>
            <span className={`ml-auto ${met || !submitted ? "text-text-muted" : "text-danger"}`}>
              {met ? "맞음" : "맞지 않음"}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
