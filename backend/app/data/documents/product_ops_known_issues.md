---
doc_id: product_ops_guide
title: Product Operations Guide
status: current
scope: general
effective_date: 2026-08-14
---

## Plan Capabilities

- Bulk Upload: Available on Growth and Enterprise. Supported file size is up to 5,000
  rows per CSV.
- Standard: Bulk Upload is not included.
- Shipment status: BOOKED means the shipment is created but ParcelPilot has not yet
  received a pickup confirmation. PICKED_UP means carrier pickup has been confirmed.

## Current Known Issues

### KI-208 - Bulk Upload failures on large CSVs

Opened: 10 August 2026. Status: Investigating.

Some Growth and Enterprise customers experience intermittent failures on CSV uploads
above approximately 3,000 rows, even though the supported product limit remains 5,000
rows. Workaround: split the upload into files below 3,000 rows. Individual shipment
creation is unaffected.

### KI-211 - SwiftShip pickup webhook delay

Opened: 12 August 2026. Status: Monitoring.

SwiftShip pickup confirmation webhooks can arrive up to 20 minutes late. A parcel may
physically be collected while ParcelPilot still shows BOOKED. Before telling a
customer that a pickup did not occur, verify the carrier status or wait through the
known delay window.
