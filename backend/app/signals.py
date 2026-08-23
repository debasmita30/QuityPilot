from datetime import datetime, timedelta
from collections import defaultdict
from .database import get_conn, DATASET_SNAPSHOT

PLAN_SLA_MINUTES = {
    "Enterprise": {"P1": 30, "P2": 120, "P3": 1440},
    "Growth": {"P1": 120, "P2": 240, "P3": 2880},
    "Standard": {"P1": 240, "P2": 1440, "P3": 2880},
}

ACCOUNT_SLA_OVERRIDE_MINUTES = {
    "ACCT-001": {"P1": 15, "P2": 60, "P3": 480},
    "ACCT-002": {"P1": 120, "P2": 240, "P3": 2880},
}

KNOWN_ISSUE_KEYWORDS = {
    "KI-208_bulk_upload_failures": ["bulk upload", "csv"],
    "KI-211_swiftship_webhook_delay": ["still shows booked", "webhook", "shows booked after"],
}


def classify_severity(subject: str, description: str) -> str:
    text = f"{subject} {description}".lower()
    p1_terms = [
        "all shipment creation", "complete outage", "cannot create any shipment",
        "api key", "credential", "security incident", "exposure",
    ]
    if any(t in text for t in p1_terms):
        return "P1"
    p2_terms = ["bulk upload fails", "major feature", "materially degraded"]
    if any(t in text for t in p2_terms):
        return "P2"
    return "P3"


def _categorize(subject: str, description: str) -> str:
    text = f"{subject} {description}".lower()
    if any(t in text for t in ["api key", "credential", "security incident", "exposure"]):
        return "security"
    if any(t in text for t in ["all shipment creation", "outage", "http 500"]):
        return "platform_outage"
    if any(t in text for t in ["bulk upload", "csv"]):
        return "bulk_upload"
    if any(t in text for t in ["still shows booked", "webhook", "tracking"]):
        return "tracking_status"
    if "billing" in text:
        return "billing"
    return "other"


def _sla_target_minutes(account_id: str, plan: str, severity: str) -> int:
    if account_id in ACCOUNT_SLA_OVERRIDE_MINUTES:
        return ACCOUNT_SLA_OVERRIDE_MINUTES[account_id][severity]
    return PLAN_SLA_MINUTES.get(plan, PLAN_SLA_MINUTES["Standard"])[severity]


def _sla_signals(tickets: list[dict], accounts_by_id: dict[str, dict]) -> list[dict]:
    signals = []
    for t in tickets:
        if t["status"] != "open":
            continue
        severity = classify_severity(t["subject"], t["description"])
        created = datetime.fromisoformat(t["created_at"])
        elapsed_minutes = (DATASET_SNAPSHOT - created).total_seconds() / 60
        account = accounts_by_id.get(t["account_id"], {})
        target = _sla_target_minutes(t["account_id"], account.get("plan", "Standard"), severity)
        ratio = elapsed_minutes / target if target else 0
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
                "classified_severity": severity,
                "elapsed_minutes": round(elapsed_minutes, 1),
                "target_minutes": target,
                "subject": t["subject"],
            }
        )
    signals.sort(key=lambda s: (s["level"] != "breached", -s["elapsed_minutes"]))
    return signals


def _spike_signals(tickets: list[dict]) -> list[dict]:
    window_start = DATASET_SNAPSHOT - timedelta(hours=24)
    by_category: dict[str, list[dict]] = defaultdict(list)
    for t in tickets:
        created = datetime.fromisoformat(t["created_at"])
        if created >= window_start:
            by_category[_categorize(t["subject"], t["description"])].append(t)

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


def _known_issue_clusters(tickets: list[dict]) -> list[dict]:
    signals = []
    for issue_id, keywords in KNOWN_ISSUE_KEYWORDS.items():
        matches = [
            t for t in tickets
            if any(k in f"{t['subject']} {t['description']}".lower() for k in keywords)
        ]
        accounts = {m["account_id"] for m in matches}
        if len(matches) >= 2:
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
    accounts = [dict(r) for r in conn.execute("SELECT * FROM accounts").fetchall()]
    conn.close()
    accounts_by_id = {a["account_id"]: a for a in accounts}

    return {
        "dataset_reference_time": DATASET_SNAPSHOT.isoformat(),
        "sla_risk": _sla_signals(tickets, accounts_by_id),
        "complaint_spikes": _spike_signals(tickets),
        "known_issue_clusters": _known_issue_clusters(tickets),
        "unusual_account_activity": _account_activity_signals(tickets),
    }

