# Note on data

This submission uses the real ParcelPilot candidate data pack:

- `01_Support_Policy_v3_CURRENT.pdf`
- `02_Support_Policy_v2_DEPRECATED.pdf`
- `03_Cancellation_and_Service_Credit_SOP_v4.pdf`
- `04_Product_Operations_Guide_and_Known_Issues.pdf`
- `05_Northstar_Logistics_Enterprise_Agreement.pdf`
- `06_LumenWorks_Service_Agreement.pdf`
- `ParcelPilot_Assessment_Data.xlsx`

The six PDFs are transcribed into `backend/app/data/documents/*.md` with YAML
frontmatter (`doc_id`, `status`, `scope`, `effective_date`) that `retrieval.py` uses
for source-precedence filtering. The workbook's `accounts`, `orders`, and `tickets`
sheets are seeded directly into SQLite in `backend/app/database.py`, using the
workbook's stated dataset snapshot time (2026-08-16 11:00 Asia/Kolkata) as
`DATASET_SNAPSHOT` — the fixed "now" every date/time comparison in the system is
anchored to, per the README sheet's instruction to use it as the reference time for
all time-based questions.

## Deliberate traps in this dataset, and how the system is meant to handle them

- **Northstar's cancellation override is unconditional**, not time-windowed: any
  BOOKED shipment can be cancelled fee-free regardless of how long ago it was booked,
  which is a stronger override than the SOP's default 30-minute grace period. ORD-1001
  (Northstar, BOOKED, not picked up) tests whether the agent applies the agreement
  correctly instead of defaulting to the SOP's INR 250 fee.
- **`TKT-450`'s historical resolution is wrong for a checkable reason**: it applied
  the SOP's default INR 250 cancellation fee to a Northstar ticket, but Northstar's
  agreement waives that fee entirely — the past agent apparently didn't check the
  account-specific override. The system should flag this rather than repeat it.
- **`TKT-451`'s historical resolution is also wrong**: it told a customer the Growth
  plan supports only 3,000-row CSVs, but the Product Operations Guide states the
  actual supported limit is 5,000 rows (3,000 is only where intermittent *failures*
  become more likely under known issue KI-208, not the documented limit).
- **Ticket severity is not a stored field.** The workbook's `tickets` sheet has no
  severity column — `signals.py: classify_severity()` and the agent's system prompt
  both derive P1/P2/P3 from the ticket's subject/description against Support Policy
  v3's definitions, matching how a human agent would actually triage.
- **KI-211 (SwiftShip webhook delay) can explain a symptom without it being a new
  incident** — `TKT-504`'s "still shows BOOKED after pickup" was raised only ~10
  minutes after pickup, within the known delay window, so it shouldn't be treated as
  a fresh incident requiring escalation.
- **LumenWorks' agreement mostly restates rather than overrides** — its SLA targets
  happen to equal the Growth plan defaults, and its failed-pickup credit clause
  replaces the SOP's default threshold and amount with a fixed INR 300 / 4-hour rule.
  This tests whether the system still checks the agreement first even when the
  numbers turn out to match the default, rather than skipping the check because "it's
  probably the same as the default anyway."
