import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(__file__).parent / "data" / "quitypilot.db"
DATASET_SNAPSHOT = datetime(2026, 8, 20, 9, 0, 0)

SCHEMA = """
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    tier TEXT NOT NULL,
    agreement_doc_id TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    carrier TEXT NOT NULL,
    status TEXT NOT NULL,
    shipment_value REAL NOT NULL,
    pickup_scheduled_at TEXT NOT NULL,
    pickup_actual_at TEXT,
    delivery_scheduled_at TEXT NOT NULL,
    delivery_actual_at TEXT,
    delay_reason TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE TABLE tickets (
    ticket_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    order_id TEXT,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    subject TEXT NOT NULL,
    resolution_notes TEXT,
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
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


def iso(dt: datetime) -> str:
    return dt.isoformat()


def seed(conn: sqlite3.Connection) -> None:
    accounts = [
        ("ACC-NORTHSTAR", "Northstar Logistics", "enterprise", "northstar_agreement", iso(DATASET_SNAPSHOT - timedelta(days=400))),
        ("ACC-LUMENWORKS", "LumenWorks", "enterprise", "lumenworks_agreement", iso(DATASET_SNAPSHOT - timedelta(days=300))),
        ("ACC-BRIGHTFREIGHT", "Bright Freight Co", "standard", None, iso(DATASET_SNAPSHOT - timedelta(days=150))),
        ("ACC-MERIDIAN", "Meridian Cargo", "standard", None, iso(DATASET_SNAPSHOT - timedelta(days=90))),
    ]
    conn.executemany(
        "INSERT INTO accounts VALUES (?,?,?,?,?)", accounts
    )

    orders = [
        ("ORD-1001", "ACC-NORTHSTAR", "SwiftHaul", "booked", 185000, iso(DATASET_SNAPSHOT + timedelta(hours=4)), None, iso(DATASET_SNAPSHOT + timedelta(hours=30)), None, None, iso(DATASET_SNAPSHOT - timedelta(hours=20))),
        ("ORD-1002", "ACC-NORTHSTAR", "RapidLane", "delivered", 92000, iso(DATASET_SNAPSHOT - timedelta(days=3)), iso(DATASET_SNAPSHOT - timedelta(days=3, hours=-3)), iso(DATASET_SNAPSHOT - timedelta(days=2)), iso(DATASET_SNAPSHOT - timedelta(days=1, hours=20)), "carrier_fault", iso(DATASET_SNAPSHOT - timedelta(days=5))),
        ("ORD-1003", "ACC-NORTHSTAR", "CargoNorth", "in_transit", 41000, iso(DATASET_SNAPSHOT - timedelta(days=1)), iso(DATASET_SNAPSHOT - timedelta(days=1)), iso(DATASET_SNAPSHOT + timedelta(hours=10)), None, None, iso(DATASET_SNAPSHOT - timedelta(days=2))),
        ("ORD-1004", "ACC-LUMENWORKS", "SwiftHaul", "delivered", 67000, iso(DATASET_SNAPSHOT - timedelta(days=6)), iso(DATASET_SNAPSHOT - timedelta(days=6, hours=-5)), iso(DATASET_SNAPSHOT - timedelta(days=5)), iso(DATASET_SNAPSHOT - timedelta(days=4, hours=18)), "carrier_fault", iso(DATASET_SNAPSHOT - timedelta(days=8))),
        ("ORD-1005", "ACC-LUMENWORKS", "BlueArc", "booked", 53000, iso(DATASET_SNAPSHOT + timedelta(hours=20)), None, iso(DATASET_SNAPSHOT + timedelta(hours=44)), None, None, iso(DATASET_SNAPSHOT - timedelta(hours=6))),
        ("ORD-1006", "ACC-LUMENWORKS", "RapidLane", "cancelled", 28000, iso(DATASET_SNAPSHOT - timedelta(days=2)), None, iso(DATASET_SNAPSHOT - timedelta(days=1)), None, "shipper_requested", iso(DATASET_SNAPSHOT - timedelta(days=4))),
        ("ORD-1007", "ACC-BRIGHTFREIGHT", "SwiftHaul", "in_transit", 15000, iso(DATASET_SNAPSHOT - timedelta(days=1)), iso(DATASET_SNAPSHOT - timedelta(days=1)), iso(DATASET_SNAPSHOT + timedelta(hours=8)), None, "tracking_sync_delay", iso(DATASET_SNAPSHOT - timedelta(days=3))),
        ("ORD-1008", "ACC-BRIGHTFREIGHT", "CargoNorth", "booked", 9800, iso(DATASET_SNAPSHOT + timedelta(hours=2)), None, iso(DATASET_SNAPSHOT + timedelta(hours=26)), None, None, iso(DATASET_SNAPSHOT - timedelta(hours=10))),
        ("ORD-1009", "ACC-MERIDIAN", "BlueArc", "delivered", 34000, iso(DATASET_SNAPSHOT - timedelta(days=10)), iso(DATASET_SNAPSHOT - timedelta(days=10)), iso(DATASET_SNAPSHOT - timedelta(days=9)), iso(DATASET_SNAPSHOT - timedelta(days=8, hours=22)), "address_validation_error", iso(DATASET_SNAPSHOT - timedelta(days=12))),
        ("ORD-1010", "ACC-MERIDIAN", "SwiftHaul", "booked", 21000, iso(DATASET_SNAPSHOT + timedelta(hours=1)), None, iso(DATASET_SNAPSHOT + timedelta(hours=25)), None, None, iso(DATASET_SNAPSHOT - timedelta(hours=2))),
    ]
    conn.executemany(
        "INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?)", orders
    )

    tickets = [
        ("TCK-2001", "ACC-NORTHSTAR", "ORD-1002", "service_credit", "high", "resolved",
         "Delivery delayed 5 hours, carrier fault",
         "Approved credit at 5% standard rate per policy v2.",
         iso(DATASET_SNAPSHOT - timedelta(days=4, hours=20)), iso(DATASET_SNAPSHOT - timedelta(days=4, hours=10))),
        ("TCK-2002", "ACC-NORTHSTAR", "ORD-1003", "tracking", "standard", "open",
         "No tracking updates for 6 hours",
         None, iso(DATASET_SNAPSHOT - timedelta(hours=5)), None),
        ("TCK-2003", "ACC-LUMENWORKS", "ORD-1004", "service_credit", "standard", "resolved",
         "Requesting credit for late delivery",
         "Approved credit at 3% per LumenWorks agreement rate.",
         iso(DATASET_SNAPSHOT - timedelta(days=4, hours=15)), iso(DATASET_SNAPSHOT - timedelta(days=4, hours=2))),
        ("TCK-2004", "ACC-LUMENWORKS", "ORD-1006", "cancellation", "standard", "resolved",
         "Cancelled shipment, asking about fee",
         "Waived fee as goodwill gesture, no policy basis recorded.",
         iso(DATASET_SNAPSHOT - timedelta(days=4)), iso(DATASET_SNAPSHOT - timedelta(days=3, hours=20))),
        ("TCK-2005", "ACC-BRIGHTFREIGHT", "ORD-1007", "tracking", "standard", "open",
         "Shipment stuck at in-transit with no updates",
         None, iso(DATASET_SNAPSHOT - timedelta(hours=18)), None),
        ("TCK-2006", "ACC-BRIGHTFREIGHT", "ORD-1007", "tracking", "standard", "open",
         "Same shipment still shows no movement",
         None, iso(DATASET_SNAPSHOT - timedelta(hours=6)), None),
        ("TCK-2007", "ACC-MERIDIAN", "ORD-1009", "service_credit", "high", "open",
         "Address validation caused late pickup, requesting credit",
         None, iso(DATASET_SNAPSHOT - timedelta(hours=30)), None),
        ("TCK-2008", "ACC-MERIDIAN", None, "billing", "standard", "open",
         "Duplicate invoice line on monthly statement",
         None, iso(DATASET_SNAPSHOT - timedelta(hours=12)), None),
        ("TCK-2009", "ACC-NORTHSTAR", None, "billing", "standard", "open",
         "Duplicate invoice line on monthly statement",
         None, iso(DATASET_SNAPSHOT - timedelta(hours=9)), None),
        ("TCK-2010", "ACC-LUMENWORKS", None, "billing", "standard", "open",
         "Two charges for same shipment this month",
         None, iso(DATASET_SNAPSHOT - timedelta(hours=3)), None),
        ("TCK-2011", "ACC-BRIGHTFREIGHT", "ORD-1008", "cancellation", "critical", "open",
         "Need to cancel booked shipment urgently, damage risk flagged",
         None, iso(DATASET_SNAPSHOT - timedelta(hours=1)), None),
    ]
    conn.executemany(
        "INSERT INTO tickets VALUES (?,?,?,?,?,?,?,?,?,?)", tickets
    )


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    seed(conn)
    conn.commit()
    conn.close()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
