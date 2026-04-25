# AGENTS.md — COBOL Modernization Working Standard

This repository is used as a modernization workspace. The codebase currently contains:

- `release/`: Python backend/service runtime and tests.
- `docs/`: documentation site (Next.js) and static export artifacts.
- `website/`: active web UI code (Next.js).
- `old_version/`: historical prototypes and legacy reference code.
- `screenshots/`: manually captured images.

## Purpose

Use this repository to plan and execute **safe, auditable COBOL modernization** from discovery through delivery. Every change should reduce migration risk and preserve business behavior.

---

## Non-negotiable principles

1. **Behavior first, technology second**
   - Modernize only when behavior is captured and testable.
   - A translated system that changes financial/business outcomes is a failure.

2. **Strangler over big-bang**
   - Prefer incremental extraction and coexistence patterns.
   - Every slice must be deployable and reversible.

3. **Evidence over assumptions**
   - Record source proof for copybooks, JCL steps, job schedules, file layouts, and business rules.
   - If unknown, mark as unknown and create a discovery task.

4. **Compatibility is explicit**
   - For each interface define: encoding, precision/scale, date rules, sign conventions, rounding, and nullability.

5. **Plan before build**
   - Implementation work must be driven by an approved ExecPlan in `.agent/PLANS.md` format.

---

## Required delivery artifacts per modernization slice

Each slice (program family, batch flow, or business capability) must produce:

- ExecPlan (approved)
- Source inventory and dependency map
- Data contract map (copybooks/files/tables/messages)
- Golden test cases (including edge cases and reconciliation totals)
- Cutover + rollback checklist
- Post-cutover validation report

---

## Definition of Done (DoD)

A modernization slice is done only when all are true:

- Functional parity proven against agreed golden datasets.
- Reconciliation totals match legacy within defined tolerance (prefer zero delta for financial data).
- Operational runbook exists (scheduling, restart, failure handling, observability).
- Rollback is tested, not just documented.
- Stakeholder sign-off is captured (engineering + business owner).

---

## Working conventions for this repo

- Put modernization planning standards and concrete plans in `.agent/PLANS.md`.
- Keep plans concrete: systems, files, jobs, KPIs, and dates.
- Prefer small, reviewable PRs that map to one ExecPlan phase.
- Never delete historical/legacy references in `old_version/` unless explicitly requested.
- Treat generated static outputs (`docs/output/`, `.next/`, binaries in `release/dist/`) as build artifacts, not source-of-truth logic.

---

## Quality gates (recommended defaults)

Before merging modernization-related work:

- Run relevant tests in `release/tests/` when backend behavior is touched.
- For UI/process transparency changes, verify affected docs/pages render.
- Confirm plan status updates in `.agent/PLANS.md` are included with code changes.

---

## Escalation triggers

Pause implementation and escalate when any occur:

- Unresolved data-format ambiguity (packed decimals, sign nibble, EBCDIC/ASCII conversion).
- Missing reconciliation path for financial outputs.
- Unknown job dependency that affects SLA/close window.
- Security/compliance impact discovered mid-slice.
