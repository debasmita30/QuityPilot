---
doc_id: product_ops_guide
title: Product Operations Guide and Known Issues
status: current
scope: general
effective_date: 2026-07-20
---

## Known Issue: Carrier Sync Delay (SwiftHaul)

Tracking updates from carrier partner SwiftHaul have been delayed by up to 6 hours
since 2026-07-05 due to an integration issue on SwiftHaul's side. Shipments show as
"in transit" without status updates during this window even though carrier operations
are proceeding normally. This is not carrier fault for service-credit purposes unless
the underlying pickup or delivery itself was late, not just the tracking display.
Root cause: unresolved, SwiftHaul engineering engaged.

## Known Issue: Duplicate Invoice Generation

Enterprise accounts on consolidated monthly billing may see a duplicate invoice line
for shipments booked in the last week of July 2026 due to a billing cycle overlap bug.
Support should note this on any related ticket rather than treating it as a new
billing dispute. Root cause: identified, fix scheduled, do not action a refund without
escalation.

## Known Issue: Address Validation False Positives

The address validation step has occasionally rejected valid addresses in Tier 2 cities
since 2026-06-01, requiring manual override by support. This can delay pickup
scheduling and, if it causes a late pickup, does count as a ParcelPilot-side fault for
service-credit purposes. Root cause: identified, fix in progress.

## General Operational Notes

Carrier partners currently integrated: SwiftHaul, RapidLane, CargoNorth, BlueArc.
Standard pickup windows are booked in 2-hour blocks. Shipment value is used as the
basis for all fee and credit percentage calculations referenced in policy and SOP
documents.
