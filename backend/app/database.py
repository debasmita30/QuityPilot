import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "data" / "quitypilot.db"
DATASET_SNAPSHOT = datetime(2026, 8, 16, 11, 0, 0)
DATASET_SNAPSHOT_TZ = "Asia/Kolkata"
CURRENCY = "INR"

SCHEMA = """
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    account_name TEXT NOT NULL,
    plan TEXT NOT NULL,
    status TEXT NOT NULL,
    csm TEXT,
    contract_file TEXT,
    premium_support INTEGER NOT NULL,
    notes TEXT
);

CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    carrier TEXT NOT NULL,
    status TEXT NOT NULL,
    booked_at TEXT NOT NULL,
    pickup_window_start TEXT NOT NULL,
    pickup_window_end TEXT NOT NULL,
    pickup_actual_at TEXT,
    shipment_fee_inr REAL NOT NULL,
    carrier_fault INTEGER NOT NULL,
    customer_fault INTEGER NOT NULL,
    cancellation_requested_at TEXT,
    notes TEXT,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE TABLE tickets (
    ticket_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,
    subject TEXT NOT NULL,
    description TEXT NOT NULL,
    channel TEXT,
    assigned_to TEXT,
    last_customer_message_at TEXT,
    historical_resolution TEXT,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE TABLE escalations (
    escalation_id TEXT PRIMARY KEY,
    ticket_id TEXT,
    order_id TEXT,
    account_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _accounts() -> list[tuple]:
    return [
        ("ACCT-001", "Northstar Logistics", "Enterprise", "active", "Priya Mehta",
         "05_Northstar_Logistics_Enterprise_Agreement.pdf", 1,
         "Strategic account. Contract contains custom SLA and cancellation terms."),
        ("ACCT-002", "LumenWorks", "Growth", "active", "Arjun Rao",
         "06_LumenWorks_Service_Agreement.pdf", 0,
         "Growth customer with contract-specific service credit terms."),
        ("ACCT-003", "Beacon Retail", "Standard", "active", "Neha Kapoor",
         None, 0,
         "No custom agreement in the supplied pack; standard policies apply."),
        ("ACCT-004", "Axis Labs", "Enterprise", "active", "Priya Mehta",
         None, 0,
         "Enterprise plan; standard Enterprise support policy applies."),
    ]


def _orders() -> list[tuple]:
    return [
        ("ORD-1001", "ACCT-001", "SwiftShip", "BOOKED",
         "2026-08-16 09:00", "2026-08-16 10:30", "2026-08-16 11:30", None,
         4200.0, 0, 0, "2026-08-16 11:00",
         "Customer asks to cancel. Shipment has not been picked up."),
        ("ORD-1002", "ACCT-001", "BlueDart Pro", "PICKED_UP",
         "2026-08-16 08:10", "2026-08-16 09:00", "2026-08-16 10:00", "2026-08-16 09:35",
         5100.0, 0, 0, "2026-08-16 10:20",
         "Customer later asked to cancel after pickup."),
        ("ORD-2001", "ACCT-002", "SwiftShip", "BOOKED",
         "2026-08-16 09:00", "2026-08-16 11:00", "2026-08-16 12:00", None,
         1800.0, 0, 0, "2026-08-16 10:15",
         "Cancellation requested 75 minutes after booking; not yet picked up."),
        ("ORD-2002", "ACCT-002", "RoadRunner", "BOOKED",
         "2026-08-16 04:30", "2026-08-16 05:30", "2026-08-16 06:30", None,
         2400.0, 1, 0, None,
         "Pickup missed. Carrier accepted fault. Still not picked up at dataset snapshot."),
        ("ORD-3001", "ACCT-003", "RoadRunner", "BOOKED",
         "2026-08-16 10:25", "2026-08-16 12:00", "2026-08-16 13:00", None,
         1200.0, 0, 0, "2026-08-16 10:40",
         "Cancellation requested within 30 minutes of booking."),
        ("ORD-4001", "ACCT-004", "SwiftShip", "DELIVERED",
         "2026-08-14 14:00", "2026-08-15 09:00", "2026-08-15 10:00", "2026-08-15 09:20",
         3600.0, 0, 0, None,
         "Completed delivery."),
    ]


def _tickets() -> list[tuple]:
    return [
        ("TKT-501", "ACCT-001", "2026-08-16 10:30", "open",
         "All shipment creation is failing",
         "Every user at Northstar gets HTTP 500 when creating any shipment. Existing shipments can still be viewed.",
         "email", "Rohit", "2026-08-16 10:52", None),
        ("TKT-502", "ACCT-002", "2026-08-16 09:45", "open",
         "Bulk upload fails for 4,200-row CSV",
         "The CSV reaches roughly 70% and fails. Creating shipments one-by-one still works.",
         "chat", "Maya", "2026-08-16 10:40", None),
        ("TKT-503", "ACCT-003", "2026-08-16 10:05", "open",
         "How do we change the billing contact?",
         "Customer wants to replace the billing-contact email on their account.",
         "email", "Rohit", "2026-08-16 10:05", None),
        ("TKT-504", "ACCT-001", "2026-08-16 10:50", "open",
         "SwiftShip order still shows BOOKED after driver pickup",
         "Driver collected the parcel around 10 minutes ago, but ParcelPilot still shows BOOKED.",
         "chat", "Maya", "2026-08-16 10:58", None),
        ("TKT-505", "ACCT-004", "2026-08-16 08:30", "open",
         "Possible API key exposure",
         "An employee accidentally posted a screenshot containing a production API key in a public channel. They are asking what to do.",
         "email", "Rohit", "2026-08-16 09:10", None),
        ("TKT-450", "ACCT-001", "2026-07-12 14:10", "closed",
         "Cancellation fee after 30 minutes",
         "Northstar asked whether a BOOKED shipment could be cancelled 90 minutes after booking before pickup.",
         "email", "Maya", "2026-07-12 15:00",
         "Agent told customer a INR 250 cancellation fee applied after 30 minutes."),
        ("TKT-451", "ACCT-002", "2026-08-11 11:20", "closed",
         "Bulk upload fails for large CSV",
         "LumenWorks reported failures when uploading 3,500-row CSV files.",
         "chat", "Rohit", "2026-08-11 12:10",
         "Agent told customer Growth plan only supports 3,000 rows."),
    ]


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?)", _accounts())
    conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", _orders())
    conn.executemany("INSERT INTO tickets VALUES (?,?,?,?,?,?,?,?,?,?)", _tickets())
    conn.commit()
    conn.close()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

