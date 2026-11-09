# Design review and revision record

Reviewed 2026-11-05. Scope: original topic/lecturer notes, requirement image, relevant lecture pages and every supplied root design/example/validator file. Outcome: a concrete **design-review package** with source traceability and explicit open decisions; no implementation acceptance is claimed.

## Findings and resulting changes

| ID | Finding / consequence in the supplied package | Revision / evidence | Status |
|---|---|---|---|
| RV01 | README claimed unavailable sources/no repository, incorrect artifact location, nonexistent examples/tools directories and prior validation | Replaced with real local sources, task matrix, root links and reproducible commands | Corrected |
| RV02 | Required architecture figure, per-feature communication diagrams and presentation organization absent | application-design.md; UC01–UC14 in use-case-flows.md; design-review-outline.md | Added |
| RV03 | Validator used parent.parent and examples/ paths; failed with FileNotFoundError in this repository; implicit Windows encoding | Resolve script parent and root JSONL; explicit UTF-8; read-only --check mode; validate before rendering | Corrected |
| RV04 | Validator skipped comparison deltas; example F1001 delta was 1,100,000 while 3,700,000−2,580,000 = **1,120,000** | Corrected example/AS-10; added delta/minimum/duration checks | Corrected |
| RV05 | LIST_BOOKINGS promised newest-first but returned the older round trip before the later one-way booking | Reordered example #30; validator tracks creation order | Corrected |
| RV06 | NDJSON framing lacked byte-unit delimiter boundaries, incremental parser/short-write/EOF/deadline behavior; session diagrams lacked guards | Message spec §§1–2; transition table and client pending submachine; AS-27/38 | Specified; runtime unproven |
| RV07 | PAY lacked shared flight serialization and admin cancellation could miss other legs' locks; process-memory options could not meet restart guarantees | One domainLock with durable SQL transactions, all-leg effects and ledger/idempotency constraints | Corrected design; runtime unproven |
| RV08 | CANCEL had no durable key; repeating admin DELAY after lost reply could add minutes twice | Durable keys for applied BOOK/PAY/CANCEL/CHANGE/ADMIN_UPDATE, scoped by user/type; replay before stale state; transcript replay examples | Corrected |
| RV09 | Change apply could silently charge different amounts after its preview | CHANGE_BOOKING retains an owned 60-second quote; cancellation is now direct with an optional advisory preview under the confirmed full-fare policy | Change protected; cancellation simplified by user feedback |
| RV10 | Schedule updates silently changed pending holds, allowing purchase of an unaccepted itinerary | Any admin update invalidates whole unpaid booking and releases both legs; paid bookings receive persisted change notifications | Corrected proposal |
| RV11 | Earlier delivery simulation was labelled SENT and lacked durable recovery | Current PAY persists one QUEUED real-email job; worker reports SENT on provider acceptance or FAILED, with retry/uncertain-send semantics | Corrected; R7 real-email-only scope confirmed by user |
| RV12 | Logging only masked password and printed malformed raw input; SEND before write conflated attempt/success | Recursive personal-data redaction, invalid-input metadata only, explicit send outcomes and client read acknowledgment semantics | Corrected design; runtime unproven |
| RV13 | Ticket/code regex, money meanings, disruption baseline, departure cutoffs, fare classes and admin counts were inconsistent/underspecified | Business invariants; [A-Z0-9] PNR; accepted-baseline net shift; pre-departure guards; class fixtures; version/count definitions | Cancellation/refund policy now confirmed; other marked proposals remain |
| RV14 | Existing examples omitted several request types and real admin reschedule/cancel/refund/replay paths; scenarios overstated offline evidence | 92 annotated frames cover all 19 request types; AS-01–40 distinguish planned runtime scenarios from example checks | Expanded |
| RV15 | User confirmed R7: real email sending, no SMS | Updated business/protocol/worker/diagram contracts, removed phone fields and channel selector, revised examples and AS-15/16/35 | Scope settled; provider sending/inbox receipt await implementation |
| RV16 | User requested simpler refund logic | Removed 10%/30% cancellation tiers and mandatory cancellation quotes; aligned full-fare/zero-unpaid outcomes across contracts, examples and acceptance cases | Cancellation rules confirmed; runtime implementation remains pending |

## Initial draft versus current proposal

The initial documents contain discussion choices, not evidence that every choice was agreed. The review preserves the expanded draft where it has a coherent alternative and records the difference rather than silently reverting it.

| Area | Initial discussion in Docs | Expanded/current review choice | Requirement implication |
|---|---|---|---|
| Framing and naming | 4-byte length prefix; version/kind/action/request_id | NDJSON; v/type/id; named _RESP replies | Either can meet custom-socket brief; do not mix parsers/envelopes |
| Accounts/session | Email login, confirmation password; logout to guest | Username login; required name/email; logout closes socket | Phone fields removed with email-only delivery; remaining account design is proposed |
| Payment | Synthetic card form discussed | Balance debit; method label only | Lecturer permits account balance; no real card charge is claimed |
| Cancellation/change | Proposed full pre-departure refund and whole-booking replacement | User confirmed full fare refund at ≥2 h or disrupted before departure, no cancellation fee/quote; one-leg change retains its separate quote/fee proposal | Cancellation scope settled by user on 2026-11-05; change policy still proposed |
| Tickets | One code per passenger/leg; void/reissue on change | One simplified ticket per passenger for all current legs; stable ID plus booking revision | Topic requires codes and management, not airline coupon modeling |
| Delivery | Real provider or simulation were discussed as alternatives | User confirmed real email only; durable email queue and actual provider send | Scope settled; verify real inbox receipt when implemented |
| Persistence | SQL discussed | Durable SQL carried forward; SQLite proposed | Engine is not specified by the supplied topic or lecture |
| Workspace | Historical C socket exercise paths | No client/server source files found in supplied file inventory | Do not claim those exercises are a flight implementation |

## Remaining decisions and evidence

1. **R7 implementation:** scope is confirmed as real email only. Select/configure provider, sender and controlled recipient mailbox; implement actual sending/retry handling and verify inbox receipt. No scope approval for simulation is pending.
2. Cancellation/refunds are confirmed by the user: no percentage tiers, full fare when eligible, unpaid holds released with zero refund; cancellation no longer requires a quote. Confirm the remaining change fees, change quotes, ten-minute hold, direct/adult-only scope, whole-booking admin refund and ticket simplification.
3. Select an allowed server language (PDF p.21 specifies C/C++/Java) and database engine. The PDF's sentence constrains the server language; no unsupported client-language mandate is added.
4. Execute implementation acceptance tests and two-PC demo; gather real logs and application evaluation for the later final report. The design review does not require pretending these have run.

## Verification performed

The source requirement image was inspected and lecture text on pages 10, 12–14 and 21–24 was extracted/checked against the local PDF. All supplied Markdown, catalog, JSONL and validator files were read. The original validator was run and its root-path failure reproduced before revision.

From this folder, run `python validate_examples.py` and `python validate_examples.py --check` for the updated structural/transcript verification. The generated transcript includes payload byte counts; the validator checks all request types, typed replies, conditional fields, roles, replay snapshots and the demonstrated money/booking chains. It also checks local package Markdown links. Full semantic/schema coverage, rendered Mermaid/PowerPoint, runtime TCP/database/concurrency/timers/printing/logging/restart tests and real delivery are **not** proven by these commands.

Executed successfully on Python 3.13: generation and read-only checks, plus six in-memory negative controls for mismatched response ID, missing apply quote, incorrect comparison delta, changed saved replay result, Unicode payload byte overflow and an unanswered request. Each negative control was rejected and the unchanged baseline passed again. No package dependency was needed by the validator.

After the R7 clarification, generation/read-only checks passed again for all 92 frames. Six email-scope negative controls rejected extra SMS delivery, simulated delivery status, resend channel input, registration phone, booking contactPhone and an SMS resend response. The baseline, source links, Markdown fences and 40 scenario IDs passed; no real email was sent during design validation.

Feedback log: on 2026-11-05 the user confirmed R7 as real email sending only, with SMS excluded, and simplified cancellation/refunds to full fare at ≥2 h or for disrupted bookings before departure, standard <2 h blocked, and live unpaid holds released without refund. Cancellation quote requirements were removed with this simplification. Other policy approvals and lecturer comments have not been supplied.

Cancellation revision verification: generation and read-only validation passed for 92 frames and all 19 request types (9 error codes now demonstrated). Four in-memory negative controls rejected cancellation fees, partial fare refunds, legacy cancellation quote input and stored preview quotes. Python syntax, Markdown fences and local links passed. These are design/transcript checks, not executed application refunds.
