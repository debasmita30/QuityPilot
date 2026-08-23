# Note on data

This submission was built before the real ParcelPilot candidate data pack (the six
PDFs and `ParcelPilot_Assessment_Data.xlsx`) was available in this environment, so it
ships with an equivalent hand-built mock pack that mirrors the real one's structure and
deliberately reproduces the same traps described in the assessment brief:

- `support_policy_v3.md` — current general policy
- `support_policy_v2_deprecated.md` — deprecated, must never be cited as current
- `cancellation_service_credit_sop_v4.md` — procedural rules and escalation criteria
- `product_ops_known_issues.md` — known issues, some of which affect fault
  determination for service credits
- `northstar_enterprise_agreement.md` — overrides cancellation window, credit rate,
  SLA, and approval threshold for Northstar
- `lumenworks_service_agreement.md` — overrides only the credit rate for LumenWorks,
  explicitly confirms no override on cancellation/SLA (a "quiet" agreement, to test
  that the system doesn't invent overrides that aren't there)

Structured data (`database.py`) seeds four accounts, ten orders, and eleven tickets
designed to exercise: an SLA breach under an account-specific SLA override, a same-order
recurring ticket pair, a cross-account known-issue cluster (duplicate invoicing hitting
three different accounts within hours of each other), and at least one ticket whose
`resolution_notes` field cites the deprecated policy's numbers — to verify the agent
doesn't repeat it as current guidance.

**To use the real data pack:** replace the files in `backend/app/data/documents/` with
the real policy/agreement documents (keep the YAML frontmatter convention — `doc_id`,
`title`, `status`, `scope`, `effective_date` — since `retrieval.py` depends on it for
precedence filtering), and replace the seed data in `database.py` with a loader over
the real `ParcelPilot_Assessment_Data.xlsx` (a `pandas.read_excel` → `INSERT` pass is
a small, contained change; the SQL schema should map closely to the workbook's
account/order/ticket sheets). Update `DATASET_SNAPSHOT` in `database.py` to the
reference time stated in the workbook's README sheet.
