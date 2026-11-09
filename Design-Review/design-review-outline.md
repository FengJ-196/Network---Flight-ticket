# Design presentation outline

Prepared from [Requirement.png](../Docs/Requirement.png) and the lecture PDF pages 22 and 24. Suggested sequence; the lecture does not prescribe this slide count or a presentation duration. This is presentation content and speaker guidance, not a generated PowerPoint file.

| Slide | Present | Figure / supporting evidence | Point to explain |
|---|---|---|---|
| 1. Application and problem | Flight Search and Booking; customer and admin goals | [Application design](application-design.md) | One booking must reconcile seats, money and tickets |
| 2. Requirements and scope | R1–R9; balance payment, mock flights, admin triggers | [Topic](../Docs/topic.md), README coverage matrix | Distinguish lecturer notes from proposed policies |
| 3. Architecture | PC B clients → TCP → PC A server → SQL/worker/logs | Architecture figure in application design | Direct sockets, allowed server languages, two separate PCs |
| 4. Functionality | UC01–UC14 grouped by account, shopping, checkout, management, updates | Use-case inventory in application design | Show what each actor can do and server role enforcement |
| 5. Wire format | NDJSON bytes, LF boundary, `v/type/id/data`, reply and push | [Message spec](message-spec.md) §§1–3 | One socket read may contain part of a frame or several frames |
| 6. Messages and replies | Account/search/checkout/manage/admin catalog; `OK` and stable `E_*` codes | Message spec §4; [error catalog](error-catalog.md) | Correlation ID differs from durable mutation key; pushes have no request ID |
| 7. Protocol state machines | Server ANON/USER/ADMIN/CLOSED; client pending request and reconnect | [State machines](state-machines.md) | Invalid login does not authenticate; reconnect always starts ANON |
| 8. Search and purchase | UC03–UC06 sequence; hold then pay | [Use-case flows](use-case-flows.md); wire examples #15–26 | Price comparison holds no seats; charge/tickets/ledger commit together |
| 9. Manage and print | View, direct cancellation/full fare refund, change quote/apply, printable data | UC08–UC11; wire examples #31–38 and #50–53 | Cancellation needs no quote; change quote binds the accepted amount |
| 10. Admin and multi-client delivery | Delay/reschedule/cancel → commit → response + customer push | UC12–UC14; examples #43–49 | Saved notification survives offline users; write success is not proof of reading |
| 11. Processing and failures | Handler pipeline, transaction boundary, lost response, logging | [Processing tables](processing-tables.md); AS-26 onward | Same key prevents duplicate debit/delay/refund; logs omit secrets |
| 12. Validation and feedback | Structural checks actually run; future two-PC demo; proposed policies; confirmed R7 real email only | [Review report](design-review.md), README validation | Demonstrate real inbox receipt during implementation; no runtime pass is claimed |

Keep exact field tables and the full UC diagrams in an appendix or linked package. For each displayed message, explain the receiving side's checks, reply and resulting state. Do not reduce the protocol explanation to a list of opcodes.

The walkthrough assumes the transcript's fixed 2026-11-04 clock, not today's wall clock. Rebase fixtures deliberately when implementing the demo. Show the account starting at 5,000,000 VND, paying 1,590,000, changing for 360,000, then receiving a 1,750,000 disruption refund: the final 4,800,000 includes a non-refundable 200,000 change fee under the separate proposed change-fee policy. Allowed cancellations now always refund 100% of fare, with no 48-hour tiers or cancellation quote.

Record lecturer feedback against decision IDs in README after presentation. R7 is confirmed by the user as real email only; the user also confirmed the simple full-fare cancellation policy. Presentation date, team/topic ID and language/provider selection have not been supplied; do not invent them.
