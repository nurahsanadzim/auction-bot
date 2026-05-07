from core.models import Item, Bid


def get_top_bid(item_id: str, bids: list[Bid]) -> Bid | None:
    active = [b for b in bids if b.item_id == item_id and not b.revoked]
    return max(active, key=lambda b: b.amount, default=None)


def resolve_big_auction(items: list[Item], bids: list[Bid]) -> dict[str, Bid | None]:
    """
    Each user can win at most one big item.
    Iteratively resolves conflicts: users winning multiple items keep only
    their highest bid; released items go to the next eligible bidder.
    """
    big_item_ids = [i.id for i in items if i.type == "big" and i.active]
    active_bids = [b for b in bids if not b.revoked]

    bids_by_item: dict[str, list[Bid]] = {
        iid: sorted(
            [b for b in active_bids if b.item_id == iid],
            key=lambda b: b.amount,
            reverse=True,
        )
        for iid in big_item_ids
    }

    # Initial assignment: top bid per item
    assignments: dict[str, Bid | None] = {
        iid: (bids_by_item[iid][0] if bids_by_item[iid] else None)
        for iid in big_item_ids
    }

    for _ in range(len(big_item_ids) + 1):
        # Build user → [item_ids] map
        user_wins: dict[int, list[str]] = {}
        for iid, bid in assignments.items():
            if bid:
                user_wins.setdefault(bid.telegram_id, []).append(iid)

        conflicted = {uid: iids for uid, iids in user_wins.items() if len(iids) > 1}
        if not conflicted:
            break

        for uid, iids in conflicted.items():
            # Keep the item where this user has the highest bid amount
            best_iid = max(
                iids,
                key=lambda iid: next(
                    (b.amount for b in bids_by_item[iid] if b.telegram_id == uid), 0
                ),
            )
            for iid in iids:
                if iid == best_iid:
                    continue
                # Find next eligible bidder (not already winning another item)
                taken = {
                    b.telegram_id
                    for i2, b in assignments.items()
                    if i2 != iid and b is not None
                }
                assignments[iid] = next(
                    (b for b in bids_by_item[iid] if b.telegram_id not in taken),
                    None,
                )

    return assignments
