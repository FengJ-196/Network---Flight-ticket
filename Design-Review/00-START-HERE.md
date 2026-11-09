# Start here — deliverables and reading order

This folder contains all 15 files from the reviewed design package, together with this reading guide. The original assignment and initial drafts remain in [../Docs](../Docs/topic.md).

## First review these four files

| Order | File | What to review |
|---|---|---|
| 1 | [application-design.md](application-design.md) | Application problem, scope, actors, architecture figure, functionality and two-PC plan |
| 2 | [business-flow.md](business-flow.md) | Business rules: booking, payment, cancellation/refunds, change fees, notifications and permissions |
| 3 | [design-review.md](design-review.md) | What was corrected, differences from the initial drafts and decisions still needing feedback |
| 4 | [design-review-outline.md](design-review-outline.md) | Suggested content and order for presenting the required design |

Focus your feedback on whether the scope and policies match your intention. Cancellation refunds are confirmed: 100% of fare when ≥2 h away or disrupted before departure, zero for live unpaid holds; standard <2 h is blocked. Cancellation has no required quote. Change fees/quotes and hold duration remain proposals. **R7 is confirmed: real email sending only; SMS is excluded.** Implementation must demonstrate actual receipt of the e-ticket email in a recipient inbox.

## Then review the detailed deliverables

These documents provide the protocol evidence behind the presentation.

| Order | File | Deliverable / review focus |
|---|---|---|
| 5 | [use-case-flows.md](use-case-flows.md) | All 14 use-case procedures, client/server behavior, communication diagrams and failure recovery |
| 6 | [message-spec.md](message-spec.md) | Message formats, framing, fields, request/reply contracts and server push |
| 7 | [state-machines.md](state-machines.md) | Client/server states, transitions, booking/flight lifecycles and reconnect behavior |
| 8 | [processing-tables.md](processing-tables.md) | What both sides do for each message, transactions, concurrency, logging and delivery |
| 9 | [error-catalog.md](error-catalog.md) | Error codes, causes, client recovery and error precedence |
| 10 | [wire-examples.md](wire-examples.md) | Complete readable message exchanges for all 19 request types |
| 11 | [acceptance-scenarios.md](acceptance-scenarios.md) | 40 planned scenarios describing how the eventual application should behave |

The [package README](README.md) maps these deliverables to the original requirements and records decisions and validation. The presentation file is an **outline**, not a PowerPoint deck. No running application or completed two-PC demo is included.

## Supporting files — optional manual reading

| File | Purpose |
|---|---|
| [message-catalog.json](message-catalog.json) | Machine-readable message inventory used by the validator |
| [wire-examples.jsonl](wire-examples.jsonl) | Source data for the readable wire-examples.md; edit this when changing examples |
| [validate_examples.py](validate_examples.py) | Checks the design examples and generates wire-examples.md |

From the repository root, run:

```text
python Design-Review/validate_examples.py --check
```

From inside this folder, run:

```text
python validate_examples.py --check
```

Omit `--check` to regenerate wire-examples.md after editing the JSONL. These are design/transcript checks; they do not execute the planned application scenarios.
