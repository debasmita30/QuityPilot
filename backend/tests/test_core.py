import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from app.database import init_db
from app.auth import SessionContext
from app import tools
from app.retrieval import get_index
from app.signals import compute_signals


@pytest.fixture(autouse=True)
def fresh_db():
    init_db()
    yield


def northstar_session():
    return SessionContext(persona="customer", account_id="ACC-NORTHSTAR", role="customer", display_name="Northstar User")


def lumenworks_session():
    return SessionContext(persona="customer", account_id="ACC-LUMENWORKS", role="customer", display_name="Lumen User")


def internal_session(role="ops_manager"):
    return SessionContext(persona="internal", account_id=None, role=role, display_name="Ops")


def test_customer_cannot_read_other_account_order():
    result = tools.get_order(lumenworks_session(), "ORD-1001")
    assert result == {"error": "access_denied"}


def test_customer_can_read_own_order():
    result = tools.get_order(northstar_session(), "ORD-1001")
    assert "order" in result
    assert result["order"]["account_id"] == "ACC-NORTHSTAR"


def test_customer_list_orders_is_scoped():
    result = tools.list_orders(northstar_session())
    assert all(o["account_id"] == "ACC-NORTHSTAR" for o in result["orders"])


def test_internal_can_scope_to_requested_account():
    result = tools.list_orders(internal_session(), account_id="ACC-LUMENWORKS")
    assert all(o["account_id"] == "ACC-LUMENWORKS" for o in result["orders"])


def test_internal_rejects_unknown_account():
    with pytest.raises(Exception):
        tools.list_orders(internal_session(), account_id="ACC-DOES-NOT-EXIST")


def test_customer_session_denied_operational_signals():
    result = tools.get_operational_signals(northstar_session())
    assert result == {"error": "access_denied"}


def test_internal_session_gets_operational_signals():
    result = tools.get_operational_signals(internal_session())
    assert "sla_risk" in result


def test_retrieval_boosts_account_agreement_over_general_policy():
    index = get_index()
    results = index.search("cancellation fee", account_scope="northstar")
    assert results[0]["doc_id"] == "northstar_agreement"


def test_retrieval_excludes_deprecated_by_default():
    index = get_index()
    results = index.search("cancellation fee")
    assert all(r["status"] != "deprecated" for r in results)


def test_retrieval_includes_deprecated_when_requested():
    index = get_index()
    results = index.search("cancellation fee", include_deprecated=True)
    assert any(r["status"] == "deprecated" for r in results)


def test_propose_escalation_does_not_write_to_db():
    session = northstar_session()
    result = tools.propose_escalation(session, reason="test", priority="standard", ticket_id="TCK-2002")
    assert result["pending_action"]["status"] == "pending_confirmation"
    tickets = tools.list_tickets(session)
    assert "escalation_id" not in str(tickets)


def test_confirm_action_creates_escalation():
    session = northstar_session()
    proposal = tools.propose_escalation(session, reason="test", priority="standard", ticket_id="TCK-2002")
    action_id = proposal["pending_action"]["action_id"]
    confirmed = tools.confirm_action(session, action_id)
    assert confirmed["escalation"]["status"] == "confirmed"
    with pytest.raises(Exception):
        tools.confirm_action(session, action_id)


def test_other_account_cannot_confirm_someone_elses_action():
    proposal = tools.propose_escalation(northstar_session(), reason="test", priority="standard", ticket_id="TCK-2002")
    action_id = proposal["pending_action"]["action_id"]
    with pytest.raises(Exception):
        tools.confirm_action(lumenworks_session(), action_id)


def test_signals_flag_known_sla_breach():
    signals = compute_signals()
    ticket_ids = {s["ticket_id"] for s in signals["sla_risk"]}
    assert "TCK-2007" in ticket_ids


def test_signals_detect_cross_account_billing_cluster():
    signals = compute_signals()
    billing = [c for c in signals["known_issue_clusters"] if c["known_issue"] == "duplicate_invoice"]
    assert billing
    assert len(billing[0]["accounts_affected"]) >= 2
