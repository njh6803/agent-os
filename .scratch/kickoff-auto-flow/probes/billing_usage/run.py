"""킥오프 준비가 비공개 저장소의 Actions 분량을 명령으로 읽는 길을 잰다(ADR 0028 "사람 몫").

GitHub REST 의 사용자 billing usage 두 길을 부른다. 하나는 항목 목록(`settings/billing/usage`), 다른
하나는 요약(`settings/billing/usage/summary`)이고, 둘 다 `year`·`month` 로 이번 달만 받는다. 찍는
것은 응답의 모양(항목의 열쇠, product·sku·unitType 의 값)과, Actions 분을 저장소와 sku 마다 더한
값과 그 저장소의 공개 여부다. 공개 여부는 `gh repo list <주인> --json name,visibility` 한 번으로
받은 목록과 맞추고, 목록에 없는 이름은 "알 수 없음"이다. 사용량이 있는 저장소만 이름을 찍는다.
금액은 찍지 않는다. 응답 헤더의 `X-Accepted-OAuth-Scopes` 도 찍는다. 이번 달은 UTC 날짜로 고른다.

거르기가 실제로 됐다는 표지는 길마다 하나다. 항목 길은 항목이 하나 이상 있고 모든 항목의 `date` 가
이번 달이라는 것이다. 요약 길은 항목이 하나 이상 있고 `timePeriod` 가 이번 달의 연·월이라는 것이다.
저장소 목록은 하나 이상이어야 한다. 표지가 없으면 측정이 아니라고 찍고 1로 끝난다. 어느 길의 응답이
오류여도 1이다.

못 보는 것: 조직 주인의 길(`organizations/<org>/settings/billing/usage`. 조직 관리자만 부른다고
GitHub REST 문서가 적는다, 원문을 받아 손으로 봤다), 기본 범위로 막 로그인한 토큰(`user` 범위가
없을 때의 응답), Billing 화면의 Included usage 와 같은 값인지, 비공개 저장소의 항목(이 계정은 이번
달에 비공개 저장소의 Actions 가 없었다), 다른 계정의 플랜.

돌리는 법: 저장소 루트에서 `uv run python .scratch/kickoff-auto-flow/probes/billing_usage/run.py`.
`gh` 로그인이 든다.
"""

from __future__ import annotations

import datetime
import json
import subprocess
from collections import defaultdict


def gh_json(path: str) -> object:
    result = subprocess.run(
        ["gh", "api", path], capture_output=True, text=True, encoding="utf-8", check=False
    )
    if result.returncode != 0:
        return {"오류": result.stderr.strip()[:300]}
    return json.loads(result.stdout)


def accepted_scopes(path: str) -> str:
    result = subprocess.run(
        ["gh", "api", "-i", path], capture_output=True, text=True, encoding="utf-8", check=False
    )
    for line in result.stdout.splitlines():
        if line.lower().startswith("x-accepted-oauth-scopes:"):
            return line.split(":", 1)[1].strip()
    return "(헤더 없음)"


def repository_visibilities(owner: str) -> dict[str, str]:
    """주인의 저장소 이름마다 공개 여부. 사용량 항목의 `repositoryName` 은 주인 없는 이름이다."""
    listed = gh_list(["gh", "repo", "list", owner, "--json", "name,visibility", "--limit", "1000"])
    return {
        text(entry.get("name")): text(entry.get("visibility"))
        for entry in listed
        if isinstance(entry, dict)
    }


def gh_list(command: list[str]) -> list[object]:
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
    if result.returncode != 0:
        return []
    parsed = json.loads(result.stdout)
    return parsed if isinstance(parsed, list) else []


def text(value: object) -> str:
    return value if isinstance(value, str) else ""


def number(value: object) -> float:
    return float(value) if isinstance(value, int | float) else 0.0


def items_of(payload: object, key: str) -> list[dict[str, object]]:
    if not isinstance(payload, dict):
        return []
    raw = payload.get(key)
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def main() -> int:
    user = gh_json("user")
    login = text(user.get("login")) if isinstance(user, dict) else ""
    plan = user.get("plan") if isinstance(user, dict) else None
    plan_name = text(plan.get("name")) if isinstance(plan, dict) else ""
    today = datetime.datetime.now(tz=datetime.UTC).date()
    query = f"year={today.year}&month={today.month}"
    print(f"login={login} plan={plan_name} 이번 달={today.year}-{today.month:02d}")

    usage_path = f"users/{login}/settings/billing/usage?{query}"
    print(f"usage 의 X-Accepted-OAuth-Scopes: {accepted_scopes(usage_path)}")
    usage = gh_json(usage_path)
    if isinstance(usage, dict) and "오류" in usage:
        print(f"usage 오류: {usage['오류']}")
        return 1
    items = items_of(usage, "usageItems")
    keys = sorted({key for item in items for key in item})
    print(f"usage 항목 {len(items)}개, 열쇠 {keys}")
    shapes = sorted(
        {(text(i.get("product")), text(i.get("sku")), text(i.get("unitType"))) for i in items}
    )
    for product, sku, unit in shapes:
        print(f"  product={product} sku={sku} unitType={unit}")
    dates = sorted({text(i.get("date"))[:10] for i in items})
    month_prefix = f"{today.year}-{today.month:02d}-"
    if not dates or not all(date.startswith(month_prefix) for date in dates):
        print(f"측정 아님: 항목이 없거나 이번 달 밖의 날짜가 있다 {dates[:1]} ~ {dates[-1:]}")
        return 1
    print(f"  date 범위 {dates[0]} ~ {dates[-1]} (모두 이번 달)")

    # sku 마다 따로 더한다. Windows·macOS 의 배수는 재지 않아 sku 끼리 더하지 않는다(명세 "준비").
    minutes: dict[tuple[str, str], float] = defaultdict(float)
    for item in items:
        if text(item.get("product")) == "actions" and text(item.get("unitType")) == "Minutes":
            key = (text(item.get("repositoryName")), text(item.get("sku")))
            minutes[key] += number(item.get("quantity"))
    visibilities = repository_visibilities(login)
    if not visibilities:
        print("측정 아님: gh repo list 가 저장소를 하나도 내지 않았다")
        return 1
    print(f"저장소 목록 {len(visibilities)}개(gh repo list 한 번)")
    print("이번 달 Actions 분(저장소와 sku 마다):")
    for (repository, sku), total in sorted(minutes.items()):
        visibility = visibilities.get(repository, "알 수 없음")
        print(f"  {repository or '(이름 없음)'} {sku}: {total:g}분, visibility={visibility}")

    summary_path = f"users/{login}/settings/billing/usage/summary?{query}&product=actions"
    summary = gh_json(summary_path)
    if not isinstance(summary, dict) or "오류" in summary:
        print(f"summary 오류: {summary}")
        return 1
    print(f"summary 의 최상위 열쇠 {sorted(summary.keys())}")
    period = summary.get("timePeriod")
    summary_items = items_of(summary, "usageItems")
    expected = {"year": today.year, "month": today.month}
    if not summary_items or not isinstance(period, dict) or period != expected:
        print(f"측정 아님: summary 항목이 없거나 timePeriod 가 이번 달이 아니다 {period}")
        return 1
    print(f"  summary timePeriod {period} (이번 달)")
    for item in summary_items:
        print(
            "  summary 항목 "
            f"product={text(item.get('product'))} sku={text(item.get('sku'))} "
            f"unitType={text(item.get('unitType'))} "
            f"grossQuantity={number(item.get('grossQuantity')):g} "
            f"netQuantity={number(item.get('netQuantity')):g}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
