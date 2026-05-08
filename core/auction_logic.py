from core.models import Item, Bid


def get_leading_bid(item_id: str, bids: list[Bid]) -> Bid | None:
    """Highest non-revoked bid for an item. Tie-break: earliest timestamp wins."""
    active = [b for b in bids if b.item_id == item_id and not b.revoked]
    return min(
        (b for b in sorted(active, key=lambda b: -b.amount)[:1 or None]),
        key=lambda b: b.timestamp,
        default=None,
    ) if active else None


def _ranked_bids(item_id: str, bids: list[Bid]) -> list[Bid]:
    """Non-revoked bids for an item sorted by amount desc, then timestamp asc (earliest wins tie)."""
    active = [b for b in bids if b.item_id == item_id and not b.revoked]
    return sorted(active, key=lambda b: (-b.amount, b.timestamp))


def resolve_at_close(items: list[Item], bids: list[Bid]) -> dict[str, Bid | None]:
    """
    Apply 1-win-per-user constraint after auction closes.
    Items with the highest top bids are assigned first.
    For each item, try bidders in rank order; skip users already assigned a win.
    """
    active_items = [i for i in items if i.active]

    # Sort items: highest top bid first so valuable items get priority assignment
    def top_amount(item: Item) -> int:
        ranked = _ranked_bids(item.id, bids)
        return ranked[0].amount if ranked else 0

    sorted_items = sorted(active_items, key=top_amount, reverse=True)

    assigned_users: set[int] = set()
    result: dict[str, Bid | None] = {}

    for item in sorted_items:
        candidates = _ranked_bids(item.id, bids)
        winner = next((b for b in candidates if b.telegram_id not in assigned_users), None)
        if winner:
            assigned_users.add(winner.telegram_id)
        result[item.id] = winner

    return result
