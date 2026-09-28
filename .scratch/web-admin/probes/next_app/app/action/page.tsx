import { probeAction } from "./actions";

export default function ActionPage() {
  return (
    <form action={async () => { "use server"; await probeAction(); }}>
      <button type="submit">run</button>
    </form>
  );
}
