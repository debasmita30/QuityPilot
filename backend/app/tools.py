import uuid
from datetime import datetime
from fastapi import HTTPException
from .auth import SessionContext, VALID_ACCOUNTS
from .database import get_conn, DATASET_SNAPSHOT
from .retrieval import get_index

PENDING_ACTIONS: dict[str, dict] = {}


def _resolve_account_scope(session: SessionContext, requested_account_id: str | None) -> str | None:
    if session.persona == "customer":
        return session.account_id
    if requested_account_id:
        if requested_account_id not in VALID_ACCOUNTS:
            raise HTTPException(400, "unknown account_id")
        return requested_account_id
    return None


def search_documents(session: SessionContext, query: str, include_deprecated: bool = False) -> dict:
    account_scope = session.account_id.replace("ACC-", "").lower() if session.account_id else None
    index = get_index()
    results = index.search(query, account_scope=account_scope, include_deprecated=include_deprecated)
    return {"results": results}


def get_order(session: SessionContext, order_id: str) -> dict:
    conn = get_conn()
    row = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
    conn.close()
    if row is None:
        return {"error": "not_found"}
    order = dict(row)
    if session.persona == "customer" and order["account_id"] != session.account_id:
        return {"error": "access_denied"}
    now = DATASET_SNAPSHOT
    pickup = datetime.fromisoformat(order["pickup_scheduled_at"])
    order["hours_until_pickup"] = round((pickup - now).total_seconds() / 3600, 2)
    order["dataset_reference_time"] = now.isoformat()
    return {"order": order}


def list_orders(session: SessionContext, account_id: str | None = None, status: str | None = None) -> dict:
    scope = _resolve_account_scope(session, account_id)
    conn = get_conn()
    query = "SELECT * FROM orders WHERE 1=1"
    params: list = []
    if scope:
        query += " AND account_id = ?"
        params.append(scope)
    if status:
        query += " AND status = ?"
        params.append(status)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return {"orders": [dict(r) for r in rows]}


def get_ticket(session: SessionContext, ticket_id: str) -> dict:
    conn = get_conn()
    row = conn.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
    conn.close()
    if row is None:
        return {"error": "not_found"}
    ticket = dict(row)
    if session.persona == "customer" and ticket["account_id"] != session.account_id:
        return {"error": "access_denied"}
    created = datetime.fromisoformat(ticket["created_at"])
    ticket["hours_since_created"] = round((DATASET_SNAPSHOT - created).total_seconds() / 3600, 2)
    ticket["dataset_reference_time"] = DATASET_SNAPSHOT.isoformat()
    return {"ticket": ticket}


def list_tickets(
    session: SessionContext,
    account_id: str | None = None,
    status: str | None = None,
    category: str | None = None,
    severity: str | None = None,
) -> dict:
    scope = _resolve_account_scope(session, account_id)
    conn = get_conn()
    query = "SELECT * FROM tickets WHERE 1=1"
    params: list = []
    if scope:
        query += " AND account_id = ?"
        params.append(scope)
    if status:
        query += " AND status = ?"
        params.append(status)
    if category:
        query += " AND category = ?"
        params.append(category)
    if severity:
        query += " AND severity = ?"
        params.append(severity)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return {"tickets": [dict(r) for r in rows]}


def get_account(session: SessionContext, account_id: str | None = None) -> dict:
    scope = _resolve_account_scope(session, account_id)
    if scope is None:
        return {"error": "account_id_required"}
    conn = get_conn()
    row = conn.execute("SELECT * FROM accounts WHERE account_id = ?", (scope,)).fetchone()
    conn.close()
    if row is None:
        return {"error": "not_found"}
    return {"account": dict(row)}


def get_operational_signals(session: SessionContext) -> dict:
    if not session.is_internal:
        return {"error": "access_denied"}
    from .signals import compute_signals

    return compute_signals()


def propose_escalation(
    session: SessionContext,
    reason: str,
    priority: str,
    ticket_id: str | None = None,
    order_id: str | None = None,
) -> dict:
    account_id = session.account_id
    if session.persona == "customer" and ticket_id:
        ticket = get_ticket(session, ticket_id)
        if "error" in ticket:
            return ticket
    action_id = str(uuid.uuid4())
    action = {
        "action_id": action_id,
        "type": "create_escalation",
        "ticket_id": ticket_id,
        "order_id": order_id,
        "account_id": account_id,
        "reason": reason,
        "priority": priority,
        "requested_by": session.display_name,
        "status": "pending_confirmation",
    }
    PENDING_ACTIONS[action_id] = action
    return {"pending_action": action}


def confirm_action(session: SessionContext, action_id: str) -> dict:
    action = PENDING_ACTIONS.get(action_id)
    if action is None:
        raise HTTPException(404, "action not found or already resolved")
    if session.persona == "customer" and action["account_id"] != session.account_id:
        raise HTTPException(403, "not authorized to confirm this action")
    conn = get_conn()
    conn.execute(
        "INSERT INTO escalations VALUES (?,?,?,?,?,?,?,?,?)",
        (
            action["action_id"],
            action["ticket_id"],
            action["order_id"],
            action["account_id"],
            action["reason"],
            action["priority"],
            "open",
            action["requested_by"],
            DATASET_SNAPSHOT.isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    action["status"] = "confirmed"
    del PENDING_ACTIONS[action_id]
    return {"escalation": action}


def cancel_action(session: SessionContext, action_id: str) -> dict:
    action = PENDING_ACTIONS.pop(action_id, None)
    if action is None:
        raise HTTPException(404, "action not found or already resolved")
    return {"cancelled": action_id}
