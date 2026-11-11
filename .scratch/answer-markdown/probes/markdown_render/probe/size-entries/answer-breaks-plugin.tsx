// 합친 시제품에서 한 줄 바꿈만 라이브러리(remark-breaks)에 맡긴 것. 직접 짠 줄바꿈 변환은 끈다(코드는 묶음에 남는다).
import remarkBreaks from "remark-breaks";
import remarkGfm from "remark-gfm";
import { createAnswerMarkdown } from "../../apps/widget/components/molecules/AnswerMarkdown";
import { remarkAnswer } from "../../apps/widget/lib/answer-markdown/index";

export const Answer = createAnswerMarkdown({
  remarkPlugins: [remarkGfm, [remarkAnswer, { recoverEmphasis: true, softBreaks: false }], remarkBreaks],
  tableBox: "region",
  codeBlock: "focusable",
}).Direct;
