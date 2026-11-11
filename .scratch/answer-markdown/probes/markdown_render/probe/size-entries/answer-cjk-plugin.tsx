// 합친 시제품에서 닫히지 않는 굵게만 라이브러리(remark-cjk-friendly)에 맡긴 것. 직접 짠 되살리기 변환은 끈다(코드는
// 묶음에 남는다).
import remarkCjkFriendly from "remark-cjk-friendly";
import remarkGfm from "remark-gfm";
import { createAnswerMarkdown } from "../../apps/widget/components/molecules/AnswerMarkdown";
import { remarkAnswer } from "../../apps/widget/lib/answer-markdown/index";

export const Answer = createAnswerMarkdown({
  remarkPlugins: [remarkGfm, remarkCjkFriendly, [remarkAnswer, { recoverEmphasis: false, softBreaks: true }]],
  tableBox: "region",
  codeBlock: "focusable",
}).Direct;
