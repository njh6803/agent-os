"use server";

// Server Actions CSRF 측정용. 불리면 서버 기록에 한 줄 남기고 문자열을 돌려준다.
export async function probeAction(): Promise<string> {
  console.log("[probe] server action ran");
  return "action-ran";
}
