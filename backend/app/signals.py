from datetime import datetime, timedelta
from collections import defaultdict
from .database import get_conn, DATASET_SNAPSHOT

STANDARD_SLA_HOURS = {"critical": 2, "high": 8, "standard": 24}
NORTHSTAR_SLA_HOURS = 4

KNOWN_ISSUE_KEYWORDS = {
    "carrier_sync_delay": ["tracking", "no updates", "no movement", "stuck"],
    "duplicate_invoice": ["duplicate invoice", "two charges", "duplicate"],
    "address_validation": ["address validation", "late pickup"],
}


def _sla_target_hours(account_id: str, severity: str) -> int:
    if account_id == "ACC-NORTHSTAR":
        return NORTHSTAR_SLA_HOURS
    return STANDARD_SLA_HOURS.get(severity, 24)


def _sla_signals(tickets: list[dict]) -> list[dict]:
    signals = []
    for t in tickets:
        if t["status"] != "open":
            continue
        created = datetime.fromisoformat(t["created_at"])
        elapsed_hours = (DATASET_SNAPSHOT - created).total_seconds() / 3600
        target = _sla_target_hours(t["account_id"], t["severity"])
        ratio = elapsed_hours / target if target else 0
        if ratio >= 1.0:
            level = "breached"
        elif ratio >= 0.7:
            level = "at_risk"
        else:
            continue
        signals.append(
            {
                "type": "sla_risk",
                "level": level,
                "ticket_id": t["ticket_id"],
                "account_id": t["account_id"],
                "severity": t["severity"],
                "elapsed_hours": round(elapsed_hours, 1),
                "target_hours": target,
                "subject": t["subject"],
            }
        )
    signals.sort(key=lambda s: (s["level"] != "breached", -s["elapsed_hours"]))
    return signals


def _spike_signals(tickets: list[dict]) -> list[dict]:
    window_start = DATASET_SNAPSHOT - timedelta(hours=24)
    by_category: dict[str, list[dict]] = defaultdict(list)
    for t in tickets:
        created = datetime.fromisoformat(t["created_at"])
        if created >= window_start:
            by_category[t["category"]].append(t)

    signals = []
    for category, items in by_category.items():
        accounts = {i["account_id"] for i in items}
        if len(items) >= 2:
            signals.append(
                {
                    "type": "complaint_spike",
                    "category": category,
                    "ticket_count_24h": len(items),
                    "accounts_affected": sorted(accounts),
                    "ticket_ids": [i["ticket_id"] for i in items],
                }
            )
    return signals


def _cross_account_signals(tickets: list[dict]) -> list[dict]:
    signals = []
    for issue_id, keywords in KNOWN_ISSUE_KEYWORDS.items():
        matches = [
            t for t in tickets
            if any(k in t["subject"].lower() for k in keywords) and t["status"] == "open"
        ]
        accounts = {m["account_id"] for m in matches}
        if len(accounts) >= 2 or len(matches) >= 2:
            signals.append(
                {
                    "type": "known_issue_cluster",
                    "known_issue": issue_id,
                    "accounts_affected": sorted(accounts),
                    "ticket_ids": [m["ticket_id"] for m in matches],
                }
            )
    return signals


def _account_activity_signals(tickets: list[dict]) -> list[dict]:
    open_by_account: dict[str, int] = defaultdict(int)
    for t in tickets:
        if t["status"] == "open":
            open_by_account[t["account_id"]] += 1
    signals = []
    for account_id, count in open_by_account.items():
        if count >= 2:
            signals.append(
                {
                    "type": "unusual_account_activity",
                    "account_id": account_id,
                    "open_ticket_count": count,
                }
            )
    return signals


def compute_signals() -> dict:
    conn = get_conn()
    tickets = [dict(r) for r in conn.execute("SELECT * FROM tickets").fetchall()]
    conn.close()

    return {
        "dataset_reference_time": DATASET_SNAPSHOT.isoformat(),
        "sla_risk": _sla_signals(tickets),
        "complaint_spikes": _spike_signals(tickets),
        "known_issue_clusters": _cross_account_signals(tickets),
        "unusual_account_activity": _account_activity_signals(tickets),
    }
