# Flight Search and Booking — design-review deliverables

**Status: ready for design review, with confirmed real-email delivery (R7) and simple full-fare cancellation rules (R8); other proposed policies are marked below.**
Revised 2026-11-05 against the actual files in `Docs`. This package specifies FBP v1 over direct TCP sockets. It contains no client/server implementation, runtime results or completed two-PC demo.

Start with **[00-START-HERE.md](00-START-HERE.md)** for the reading order and the distinction between deliverables and supporting files. The [presentation outline](design-review-outline.md) organizes the required introduction, architecture, functionality and protocol material. [design-review.md](design-review.md) records findings and source differences. All current package files are together in this `Design-Review` folder; original sources remain in `../Docs`.

## Required hand-in coverage

| Task / source | Required outcome | Earlier material / gap | Deliverable | Completion evidence |
|---|---|---|---|---|
| Requirement image; PDF pp.22/24 | Introduce application/problem | Features existed; no consolidated introduction | [Application design](application-design.md) | Problem, scope, actors and invariants |
| Image; PDF pp.21/22/24 | Architecture with figure | No topology or two-PC setup | Application design | PC A server / PC B clients figure, component ownership, transport and demo plan |
| Image; PDF pp.13/14/24 | Functionality and procedure for each use case | Business/processing tables, no individual communication diagrams | [Use-case flows](use-case-flows.md) | UC01–UC14, each with client/server steps, replies, failure recovery and sequence diagram |
| Image; PDF p.24 | Detailed message formats | Catalog existed; missing bounds/conditional fields and some examples | [Message spec](message-spec.md), [catalog](message-catalog.json), [wire transcript](wire-examples.md) | All 19 request types, replies, NOTIFY, framing, limits and errors |
| Image; PDF pp.10/22/24 | State machines | Diagrams lacked guarded transition tables and pending-request behavior | [State machines](state-machines.md) | Server transitions, client request/reconnect, booking/flight/quote/delivery models |
| Image; PDF pp.13/14/24 | Message processing on both ends | Payment/admin locking and retry gaps | [Processing tables](processing-tables.md), use-case flows | Handler table, atomicity, recipient delivery, logging and client dispatch |
| PDF p.22 | Present design, collect feedback and revise | No presentation organization or review record | [Presentation outline](design-review-outline.md), [review report](design-review.md) | Suggested slides and explicit open decisions; no lecturer feedback invented |
| PDF pp.21/23, later milestone | Working sockets on two PCs, final demo/evaluation report | No implementation exists | Application design validation plan; [scenarios](acceptance-scenarios.md) | Planned only; not marked complete |

The review outline is Markdown presentation content, not a PowerPoint deck. The lecture's later hard-copy report requires actual application evaluation and cannot be truthfully completed by this design-only review.

## Artifact index

| Artifact | Purpose |
|---|---|
| [business-flow.md](business-flow.md) | Business rules BR-01–50, permissions, seed fixtures, money/time invariants |
| [message-spec.md](message-spec.md) | Authoritative FBP wire/envelope/field/response contract |
| [message-catalog.json](message-catalog.json) | Machine-readable inventory, roles, fields/types, conditional requirements and errors; not a full JSON Schema |
| [error-catalog.md](error-catalog.md) | Stable error codes, disclosure, state effects, deterministic precedence and recovery |
| [state-machines.md](state-machines.md) | Session, request, booking, flight, quote and delivery transitions |
| [processing-tables.md](processing-tables.md) | Server/client processing, transaction/restart model and redacted logging |
| [use-case-flows.md](use-case-flows.md) | Procedure and sequence diagram for every feature |
| [wire-examples.jsonl](wire-examples.jsonl) / [wire-examples.md](wire-examples.md) | Annotated synthetic transcript and generated payloads/UTF-8 byte counts |
| [acceptance-scenarios.md](acceptance-scenarios.md) | AS-01–40: proposed observable acceptance cases, not executed tests |
| [validate_examples.py](validate_examples.py) | Standard-library validator and transcript renderer, runnable from any working directory |
| [application-design.md](application-design.md) | Introduction, architecture, use cases and two-PC deployment plan |
| [design-review-outline.md](design-review-outline.md) / [design-review.md](design-review.md) | Presentation content, review findings and unresolved decisions |

## Source inventory and precedence

| Source | Evidence / authority |
|---|---|
| [Docs/topic.md](../Docs/topic.md) | Nine graded features R1–R9; lecturer notes confirm balance payment, mocked flights and admin notification triggers |
| User confirmation of R7, recorded in topic.md | Real email sending only; SMS excluded; actual inbox receipt required for implementation acceptance |
| [Docs/Requirement.png](../Docs/Requirement.png) | Required review topics: introduction, architecture, functionality, protocol messages/states/processing |
| [Lecture PDF](<../Docs/06-Application protocoldesign.pdf>) | Text checked on pp.10, 12–14, 21–24: custom/direct sockets, C/C++/Java **server**, two separate PCs, design presentation and later final demo/report |
| [Initial use cases](../Docs/flight-use-cases.md) | Historical UC01–UC14 reasoning and draft policies, including possible real delivery |
| [Initial protocol plan](../Docs/flight-protocol-plan.md) | Historical length-prefixed/action-based proposal; references to C exercises describe a former workspace, not files present here |
| Expanded draft (formerly in repository root) | Starting point supplied for this review; retained names and NDJSON, USER/ADMIN and fee policy, with the corrections documented in design-review.md |

Confirmed topic/lecturer constraints and the user's R7 clarification take priority. Current contracts in this folder specify the proposed implementation. Historical drafts explain alternatives and do not override explicit current decisions. Commercial policies remain proposals; the real-email-only R7 scope is confirmed by the user.

## Graded requirement traceability

| Requirement (points) | Rules / design | Messages / use cases | Scenarios | Evidence limits |
|---|---|---|---|---|
| R1 Sockets (2) | Framing; architecture; state machines | PING and all exchanges | AS-01–03,26–29,38–39 | Direct sockets/two-PC runtime still required |
| R2 Server logging (1) | BR-50; processing §4 | All received/sent/rejected frames | AS-04,36 | Format/redaction specified, no captured server log |
| R3 Register/login (2) | BR-01–05 | REGISTER/LOGIN/LOGOUT; UC01–02 | AS-05–07,33,38 | Design and synthetic examples |
| R4 Search (2) | BR-10–12; fixture classes | SEARCH_FLIGHTS; UC03 | AS-08–09,34,37,40 | Calendar/class and seat rules specified |
| R5 Compare (2) | BR-13 | COMPARE_FLIGHTS; UC04 | AS-10 | Corrected cheapest-price delta to 1,120,000 VND |
| R6 Book/pay (3) | BR-20–25; lecturer balance note | BOOK_FLIGHT/PAY_BOOKING/GET_BALANCE; UC05–06 | AS-11–14,26,28–31,35,37,40 | No external bank/payment integration required by balance note |
| R7 E-ticket via real email (2) | BR-02/26; user confirmation | PAY/GET_BOOKING/RESEND_TICKET; UC07 | AS-15–16,35 | Confirmed scope: real email only; implement provider sending and verify actual recipient inbox receipt |
| R8 Manage tickets (3) | BR-30–34 | LIST/GET/CANCEL/CHANGE/PRINT; UC08–11 | AS-17–20,23,30–31,34,37 | Printing is client-local after server renders data |
| R9 Flight notifications (3) | BR-40–44; lecturer admin note | ADMIN_LIST/UPDATE, NOTIFY, GET/ACK_NOTIFICATIONS; UC12–14 | AS-21–25,28–29,31–32,35,39 | Delay, reschedule and cancel specified; pushes are best effort with durable inbox |

Total topic weights: **20 points**. This is traceability to required behavior, not a prediction of marks.

## Decision log — proposed unless explicitly sourced

| ID | Current decision and rationale | Source / impact |
|---|---|---|
| D1 | TCP NDJSON, v/type/id/data; simple readable custom socket format | Expanded draft retained; supersedes initial 4-byte length prefix and action names |
| D2 | USER/ADMIN; username login; server-bound connection identity; logout closes | Expanded draft retained; supersedes initial email login/logout-to-guest |
| D3 | Account balance is the only debited instrument; CREDIT_CARD/E_WALLET are labels | Balance allowance confirmed in topic lecturer note; no real card form |
| D4 | All-leg ten-minute hold, then atomic payment | Proposed; confirmed policies not supplied |
| D5 | Allowed customer cancellations refund 100% of current fare, no fee: ≥2 h or disrupted before departure; standard <2 h blocked; unpaid releases holds/refunds zero. Change fee remains 200,000/pax as a separate proposal | **Cancellation policy confirmed by user, 2026-11-05**; removes the earlier 10%/30% tiers |
| D6 | Cancellation applies directly with bookingCode/key; optional read-only preview, no stored quote. CHANGE_BOOKING alone uses an owned 60-second quote | Simplified cancellation following user feedback; change apply still needs quoteId/key |
| D7 | Durable keys for applied BOOK/PAY/CANCEL/CHANGE/ADMIN_UPDATE; saved outcomes precede state checks | Review correction; prevents repeated payment/refund/delay across lost replies/restart |
| D8 | SQL persistence and one short domain transaction/lock; SQLite proposed | Durable behavior requires persistence; engine not confirmed by lecture/topic |
| D9 | Admin update invalidates unpaid whole bookings; confirmed bookings retain identity and receive persisted notifications | Review correction; customer must accept altered itinerary again |
| D10 | Admin cancellation of any leg cancels/refunds the whole live booking, including change fees | Expanded proposal retained; transaction also releases other leg's seats |
| D11 | Real email only, durable QUEUED email jobs, SENT on provider acceptance, FAILED on error | **Confirmed by user**; SMS excluded; real inbox receipt still requires runtime evidence |
| D12 | One ticket number per passenger covering current booking legs; identifiers retained after change, revision changes | Expanded simplification retained; differs from initial per-leg replacement-ticket proposal |
| D13 | Direct domestic flights, 1–9 adults, VND/+07:00, initial balance 5,000,000; no top-up | Expanded demo assumptions; additional premium/business fare fixtures defined in business-flow.md |

No external consumer or implementation was found. Contract additions are corrections to a draft; they require client/server adoption together and are not claimed to be backward compatible with the prior draft.

## Decisions for lecturer/team feedback

- **Email implementation:** R7 scope is settled. Select/configure a real email provider, sender credentials and a controlled test mailbox during implementation; demonstrate actual inbox receipt. Provider choice and retry tuning remain implementation decisions.
- **Policies:** cancellation/refund rules are confirmed by the user. Confirm remaining change-fee/change-quote, hold-duration, whole-booking admin rules, adult-only scope and simplified ticket model.
- **Implementation:** select C, C++ or Java for the server and a SQL engine. Client language/interface and actual LAN/firewall setup remain team choices.
- **Review logistics:** topic/team ID, presentation duration and lecturer feedback were not supplied. The week labels in the PDF are not treated as a current calendar deadline.

These choices do not prevent review of the concrete design. They must be settled before claiming implementation acceptance.

## Validation

From the repository root:

```text
python Design-Review/validate_examples.py
python Design-Review/validate_examples.py --check
```

The first command validates before rewriting generated Markdown; the second is read-only. Paths resolve relative to the script, with explicit UTF-8, including on Windows and from another working directory.

The revised transcript has **92 frames**, covers **all 19 request types** plus NOTIFY and protocol-error replies, and demonstrates 9 error codes. Checks cover envelopes, required/unknown fields and basic types/conditional fields, one pending request/correlation, roles, UTF-8 byte bounds, saved-key replay snapshots, comparison/duration/price arithmetic, balance/refund chains and local Markdown links. Every catalog message/error is cross-checked against its specification. The main balance chain is 5,000,000 → 3,410,000 → 3,050,000 → 4,800,000; a replay does not change it. Bob's admin-cancel example restores 5,000,000 after a 1,850,000 debit/refund.

R7 validation enforces email-only delivery with QUEUED/SENT/FAILED states and bookingCode-only resend input. Six additional negative checks rejected legacy SMS delivery, simulated status, a resend channel selector, registration/booking phone fields and an SMS resend response. The unchanged 92-frame baseline passed again. These checks do not contact an email provider.

Limits: this is a purpose-built structural/transcript check, **not** complete schema validation or execution of AS-01–40. It does not run a TCP parser, concurrency/deadlock tests, database constraints, hold/quote timers, real printing, log redaction, restart recovery, provider delivery, or two-PC interoperability. Those remain planned runtime checks. The presentation outline and Mermaid sources are Markdown; no rendered slide deck is claimed.

After the cancellation simplification, all 92 frames passed again. Four in-memory negative checks rejected a cancellation fee, a partial fare refund, a cancellation quote input and a stored preview quote. Cancellation boundary and real balance/seat effects remain planned application checks in AS-20/23/37.
