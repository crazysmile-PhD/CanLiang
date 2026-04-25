# PLANS.md — ExecPlan Standard for COBOL Modernization

Use this file for all modernization execution plans. Keep entries short, concrete, and auditable.

---

## ExecPlan Skeleton (keep this structure)

```md
## ExecPlan: <Short Capability Name>

### 1) Objective
- Business outcome:
- In scope:
- Out of scope:
- Success metrics:

### 2) Legacy Baseline
- COBOL programs / JCL jobs:
- Input files / copybooks:
- Output files / downstream consumers:
- Current SLA / run window:

### 3) Modern Target Design
- Target service/module(s):
- Data mappings and compatibility rules:
- Error handling + restart semantics:
- Observability (logs, metrics, tracing):

### 4) Migration Strategy
- Phase 1 (discovery + golden tests):
- Phase 2 (dual-run / shadow):
- Phase 3 (cutover):
- Phase 4 (decommission):

### 5) Validation Plan
- Golden dataset coverage:
- Reconciliation checks:
- Non-functional tests (perf, resiliency):
- Sign-off owners:

### 6) Risks & Mitigations
- Risk:
- Mitigation:
- Trigger/owner:

### 7) Rollback Plan
- Rollback trigger:
- Rollback steps:
- Data repair/replay approach:

### 8) Execution Tracker
- Status: [Not Started | In Progress | Blocked | Done]
- Target dates:
- Decisions log:
```

---

## Opinionated guidance (how to fill the skeleton)

- Use business capability names, not technical nicknames.
- Success metrics must include at least one **business KPI** and one **technical KPI**.
- Validation must always include reconciliation totals and edge-case records.
- Dual-run period should be long enough to cover month-end or equivalent peak complexity.
- If a section is unknown, write `UNKNOWN` plus discovery owner/date.

---

## Example 1 — Batch Billing Modernization

## ExecPlan: Monthly Billing Batch

### 1) Objective
- Business outcome: Produce monthly customer invoices without changing billed totals.
- In scope: Legacy rating + invoice generation batch flow.
- Out of scope: Customer portal UI and payment gateway.
- Success metrics: 0 material invoice variance; batch completes within 90 minutes.

### 2) Legacy Baseline
- COBOL programs / JCL jobs: `BILLRATE`, `BILLPRNT`, JCL chain `JOBBILLM`.
- Input files / copybooks: `CUSMAST`, `USAGEDET`, copybooks `CB-CUST`, `CB-USAGE`.
- Output files / downstream consumers: `INVOICE.OUT`, AR import process.
- Current SLA / run window: Complete by 04:00 UTC on day 1 monthly.

### 3) Modern Target Design
- Target service/module(s): Python batch service in `release/app/` with staged pipeline.
- Data mappings and compatibility rules: Preserve COBOL packed-decimal precision and legacy rounding order.
- Error handling + restart semantics: Checkpoint per customer-account range with idempotent replay.
- Observability (logs, metrics, tracing): Metrics for records processed, variance count, and run duration.

### 4) Migration Strategy
- Phase 1 (discovery + golden tests): Capture 12 months of representative legacy outputs.
- Phase 2 (dual-run / shadow): Run modern path in shadow for two monthly cycles.
- Phase 3 (cutover): Switch AR feed to modern output with one-click rollback.
- Phase 4 (decommission): Freeze legacy job after two clean cycles post-cutover.

### 5) Validation Plan
- Golden dataset coverage: Normal, zero-usage, high-volume, negative adjustment accounts.
- Reconciliation checks: Total billed amount and invoice count by region/product.
- Non-functional tests (perf, resiliency): Simulate job restart after mid-run failure.
- Sign-off owners: Billing operations lead + modernization tech lead.

### 6) Risks & Mitigations
- Risk: Packed-decimal sign handling mismatch causes cent-level variance.
- Mitigation: Byte-level parsing tests for signed numeric fields.
- Trigger/owner: Any variance > $0.01/account, owned by data migration lead.

### 7) Rollback Plan
- Rollback trigger: Variance threshold breach or missed SLA.
- Rollback steps: Re-enable `JOBBILLM`; route AR feed back to legacy output.
- Data repair/replay approach: Re-run modern job in shadow for root-cause comparison.

### 8) Execution Tracker
- Status: In Progress
- Target dates: Discovery complete by 2026-05-20; cutover candidate 2026-07-01.
- Decisions log: 2026-04-25 — dual-run period set to two full monthly cycles.

---

## Example 2 — Claims Adjudication Service Extraction

## ExecPlan: Claims Eligibility Rules Extraction

### 1) Objective
- Business outcome: Externalize eligibility rules while preserving claim approval outcomes.
- In scope: Rule-evaluation logic currently embedded in COBOL module.
- Out of scope: Provider portal and payment remittance.
- Success metrics: >=99.95% decision parity, p95 latency < 250ms.

### 2) Legacy Baseline
- COBOL programs / JCL jobs: `CLMELIG`, called by nightly claims pipeline.
- Input files / copybooks: Claim record copybook `CB-CLAIM`, member coverage file.
- Output files / downstream consumers: Eligibility decision code consumed by adjudication step.
- Current SLA / run window: Nightly completion by 06:00 UTC.

### 3) Modern Target Design
- Target service/module(s): Rules microservice + compatibility adapter.
- Data mappings and compatibility rules: Canonical model with strict code-set translation table.
- Error handling + restart semantics: Deterministic fallback to legacy code path on adapter failure.
- Observability (logs, metrics, tracing): Decision-parity dashboard and failure reason tags.

### 4) Migration Strategy
- Phase 1 (discovery + golden tests): Mine top 200 rule paths from production history.
- Phase 2 (dual-run / shadow): Evaluate modern decision in parallel for 30 consecutive days.
- Phase 3 (cutover): Route 10% traffic, then 50%, then 100% with gates.
- Phase 4 (decommission): Retire COBOL module after 60 days stable at 100%.

### 5) Validation Plan
- Golden dataset coverage: Boundary ages, lapsed coverage, exception code scenarios.
- Reconciliation checks: Daily parity by decision code and line-of-business.
- Non-functional tests (perf, resiliency): Chaos test for rules-engine dependency outage.
- Sign-off owners: Claims product owner + platform engineering manager.

### 6) Risks & Mitigations
- Risk: Ambiguous legacy rule precedence.
- Mitigation: Rule precedence matrix signed by business SMEs before coding.
- Trigger/owner: Parity drift >0.05% in any decision class, owned by claims domain lead.

### 7) Rollback Plan
- Rollback trigger: Sustained parity drift for two consecutive processing windows.
- Rollback steps: Shift traffic to legacy adjudication call; disable modern decision writes.
- Data repair/replay approach: Replay impacted claims through legacy-only path and reconcile.

### 8) Execution Tracker
- Status: Not Started
- Target dates: Discovery start 2026-06-01; pilot cutover target 2026-08-15.
- Decisions log: 2026-04-25 — chose incremental traffic ramps over single cutover.
