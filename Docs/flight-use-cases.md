# Flight application — use cases, flows, and errors

Historical discussion draft. Current review deliverables and explicit differences are indexed in [README](../Design-Review/README.md) and [design-review.md](../Design-Review/design-review.md). Use the message/business specifications in `Design-Review` for the current proposed contract.

Current R7 scope is confirmed: real email only; SMS options and delivery simulation discussed below are historical alternatives, not the selected design.

Discussion draft. User requirements are established; business policies marked
“proposed” need review. This document precedes the provisional protocol design
in `flight-protocol-plan.md`. No implementation is authorized by this document.

## Design method

For each user goal, define actor, trigger, preconditions, main success flow,
successful alternatives, failure flows, and postconditions. Then derive server
operations, messages, state transitions, transaction boundaries, and test cases.

A UI action does not necessarily produce a network message. Opening a form,
sorting already-loaded results, and opening the print dialog are client actions.
Business authorization and authoritative validation belong on the server.

## Actors and system boundary

- Customer: registers, logs in, searches, compares, books, pays, receives tickets,
  manages bookings, and receives flight updates.
- Admin: logs in and changes schedules, assigns delays, or cancels flights.
- Delivery provider: external email/SMS delivery, if real delivery is selected.
- Time: triggers hold expiration and delivery retry processing.

The server owns SQL data, authentication, inventory, prices, balance, ticket codes,
and notifications. Payment is a simulation using application balance, not a real
bank charge. Seeded flight data and seeded admin accounts are setup activities.
There is no public “register as admin” flow.

## Use-case inventory

| ID | Goal | Primary actor | Requirement |
|---|---|---|---|
| UC01 | Register account | Customer | Registration/login |
| UC02 | Log in / log out | Customer, admin | Registration/login |
| UC03 | Search flights | Customer  | Search |
| UC04 | Compare flight options | Customer or  | Comparison |
| UC05 | Reserve selected flights | Customer | Booking |
| UC06 | Pay for reserved booking | Customer | Online mock payment |
| UC07 | Obtain electronic tickets | Customer | Ticket code via email/SMS |
| UC08 | View bookings and ticket details | Customer | Manage tickets |
| UC09 | Cancel booking | Customer | Manage tickets |
| UC10 | Change booking | Customer | Manage tickets |
| UC11 | Print ticket | Customer | Manage tickets |
| UC12 | Receive/review flight notifications | Customer | Notifications |
| UC13 | Change flight schedule / assign delay | Admin | Schedule/delay notifications |
| UC14 | Cancel flight | Admin | Cancellation notifications |

Connection management and message logging are supporting technical flows, not
separate customer goals. Hold expiration and delivery retries are background flows.

## UC01 — Register account

Actor/trigger: a guest submits registration. Preconditions: connection available.

Main flow:
1. Client collects email, password, and confirm password. Name and phone are not
   part of UC01; delivery contact setup will be discussed in its own use case.
2. Client submits registration; server validates required fields, email syntax,
   password policy, and password confirmation, then normalizes email.
3. Server creates a customer with hashed password and the configured initial balance.
4. Server returns success; client offers login.

Alternatives: the customer may abandon the form before submission without any
server change. Client-side validation may catch errors before sending a request;
the server repeats validation authoritatively.

Failures:
- Missing fields → REQUIRED_FIELD with field-specific details.
- Invalid email format → INVALID_EMAIL.
- Password violates the agreed policy → PASSWORD_INVALID.
- Password and confirm password differ → PASSWORD_MISMATCH.
- Existing normalized email → EMAIL_EXISTS; offer login or another email.
- Storage failure → INTERNAL_ERROR; no partially created account.
- Lost response → retry may report EMAIL_EXISTS; login can establish whether the
  original registration succeeded. Do not promise an exactly-once registration UI.

Postcondition: exactly one customer for the normalized email; session stays guest.
Confirm password is compared only; it is never stored or logged. Password policy
is pending review; proposed default is 8–64 characters, at least one letter and
one digit. Do not trim or silently modify either password value.

## UC02 — Log in / log out

Actor/trigger: guest submits credentials. Preconditions: existing account.

Main flow:
1. Client submits email and password.
2. Server verifies credentials and reads the stored role.
3. Server associates that user and role with the current connection.
4. Server returns profile, role, and balance; client displays the appropriate menu.

Alternatives: customer logs out; server clears authentication but keeps the socket
open. Admin login uses the same flow with the role obtained from SQL.

Failures:
- Wrong email or password → INVALID_CREDENTIALS; remain guest.
- Excessive attempts → RATE_LIMITED with retry guidance.
- Socket disconnect → authentication on that connection ends; reconnect and log in.
- Already authenticated login attempt → INVALID_STATE; log out before switching users.

Postcondition: authenticated identity is controlled by server state, never by a
role/user ID supplied in later request bodies.

## UC03 — Search flights

Actor/trigger: user submits search criteria. Preconditions: connection available.

Main flow:
1. User chooses origin, destination, departure date, passenger count, and seat class.
2. Client submits criteria.
3. Server validates criteria and searches eligible generated flights/fares.
4. Server returns airline, times, elapsed duration, class, total for the requested
   passengers, available seats, and option identifiers.
5. User reviews results.

Alternatives:
- Round trip: user supplies return date; server returns outbound and return options.
- No matches: successful response containing empty results; user changes criteria.
- Sort/filter loaded results locally; request another page when needed.

Failures:
- Same airports, invalid dates/count/class → VALIDATION_ERROR.
- Database unavailable → INTERNAL_ERROR; keep entered criteria for retry.

Postcondition: no seats held and no price guarantee. Search is read-only.

## UC04 — Compare flight options

Actor/trigger: user selects at least two options from search results.
Preconditions: comparable search context and valid option identifiers.

Main flow:
1. User selects options for the same direction, passenger count, and class.
2. Client requests current comparison data for the selected identifiers.
3. Server returns common fields: airline, times, duration, current price, availability.
4. Client displays the comparison; user chooses an option or returns to search.

Alternatives: compare outbound and return options separately. If all data is
already current, a local comparison is possible; a server request provides refresh.

Failures:
- Too few/many selections or incompatible context → VALIDATION_ERROR.
- Option no longer eligible → return it as unavailable within an otherwise successful
  comparison; user chooses another. Do not reserve seats during comparison.

Postcondition: no mutation; selected prices must still be checked when reserving.

## UC05 — Reserve selected flights

Actor/trigger: logged-in customer continues with selected flight(s).
Preconditions: passenger details supplied; one outbound and optional return option.

Main flow:
1. Client submits options, passenger details, the prices/versions shown to the user,
   and a stable operation key.
2. Server validates identity, route/date consistency, and passenger data.
3. In one transaction, server rechecks current prices and available seats.
4. Server reserves seats for every leg, creates a HELD booking, and stores its total.
5. Server returns booking ID, itemized total, and hold expiration.
6. Client displays final review and checkout.

Alternatives:
- Round trip: both legs are reserved together, or neither is.
- Customer abandons checkout: hold expires after proposed 10 minutes.
- Price changed since selection: server returns PRICE_CHANGED and current pricing;
  user explicitly accepts and submits a new operation before creating a hold.

Failures:
- Unauthenticated → AUTH_REQUIRED; preserve selection and offer login.
- Insufficient seats → SOLD_OUT; no hold on either leg.
- Cancelled/departed flight → FLIGHT_UNAVAILABLE; return to search.
- Bad passenger data → VALIDATION_ERROR; correct indicated fields.
- Lost response → retry same operation key; recover the same booking.

Postcondition: seats held; no money deducted; no tickets issued.

## UC06 — Pay for reserved booking

Actor/trigger: customer submits mock checkout. Preconditions: owns unexpired HELD booking.

Main flow:
1. Client displays server-held total and collects synthetic mock card fields.
2. Client submits booking ID, payment form, and stable payment operation key.
3. Server validates the form, locks relevant rows, and rechecks booking/flight eligibility.
4. Server verifies balance covers the stored total.
5. In one transaction, server deducts balance, records payment, converts held seats
   to sold seats, confirms booking, creates ticket codes, and queues delivery.
6. After commit, server returns confirmed booking, tickets, and updated balance.

Alternatives:
- Mock wallet checkout can use the same balance transaction if wallet is in scope.
- Repeated request with the same operation key returns the saved outcome.
- Email/SMS fails later: booking/payment remain successful; follow UC07 recovery.

Failures:
- Invalid mock form → INVALID_MOCK_PAYMENT with safe field errors; no deduction.
- Low balance → INSUFFICIENT_BALANCE; hold stays valid until its original expiry.
- Expired hold → HOLD_EXPIRED; release reservation once; require a new booking.
- Flight changed/cancelled → FLIGHT_UNAVAILABLE; release invalid hold; search again.
- Booking already confirmed using a different operation key → INVALID_STATE;
  retrieve booking rather than charging again.
- Timeout/disconnect → outcome unknown to client, not “payment failed.” Reconnect,
  log in and retry same key or retrieve booking before offering another attempt.

Postcondition: success commits all payment/booking/ticket changes once. Failure
never leaves a deducted balance without the corresponding confirmed booking.

## UC07 — Obtain electronic tickets

Actor/trigger: successful payment/change queues delivery, or customer requests resend.
Preconditions: confirmed booking with active ticket codes; valid destination channel.

Main flow:
1. Server exposes codes immediately in the booking response/details.
2. Server queues email/SMS delivery to the customer's selected contact.
3. Worker sends the ticket information and records provider acceptance/status.
4. Customer can inspect delivery status and retrieve tickets through the app.

Alternatives: choose email or SMS; resend existing codes without issuing new tickets.
A simulated inbox is possible only if accepted for the assignment and labelled
SIMULATED; it does not establish actual email/SMS delivery.

Failures:
- Missing/invalid selected contact → VALIDATION_ERROR for send; booking stays confirmed.
- Provider unavailable → job FAILED/retry scheduled; no second charge or new codes.
- Excessive resends → RATE_LIMITED.
- Cancelled booking → INVALID_STATE; do not send an active-ticket confirmation.

Postcondition: delivery state is independent of payment state. Provider acceptance
does not prove the recipient read the message.

## UC08 — View bookings and ticket details

Actor/trigger: customer opens booking list or selects a booking.
Preconditions: authenticated customer.

Main flow: request own paginated bookings → select booking → server checks ownership
→ return passengers, issued/current itinerary, status, price, and ticket codes.

Alternatives: no bookings is a successful empty list; expired/cancelled bookings
remain visible with their status and void ticket information.

Failures: unknown or another customer's ID → NOT_FOUND; disconnected → reconnect/login.

Postcondition: no mutation; customer sees authoritative current state.

## UC09 — Cancel booking

Actor/trigger: customer confirms a cancellation summary.
Preconditions: owns HELD or CONFIRMED booking and policy permits cancellation.

Main flow:
1. Client displays booking and refund policy/amount.
2. Customer confirms; client sends booking ID, expected revision, and operation key.
3. Server locks and rechecks booking, eligibility and revision.
4. In one transaction, server cancels booking, releases seats, voids tickets,
   refunds any paid amount once, and records notification/ledger entries.
5. Server returns cancellation, refund amount, and updated balance.

Alternatives: cancelling a HELD booking releases seats with zero refund. Repeating
an already completed cancellation returns its current result without another refund.

Failures: booking departed → CANCELLATION_NOT_ALLOWED; changed booking revision →
VERSION_CONFLICT and refresh summary; expired booking → INVALID_STATE. Lost response
uses the same retry/recovery rule as payment.

Postcondition: proposed full refund before departure; entire booking cancelled.
Partial passenger/leg cancellation is outside proposed v1 scope.

## UC10 — Change booking

Actor/trigger: customer selects replacement itinerary. Preconditions: owns a
CONFIRMED booking before its earliest current departure.

Main flow:
1. Customer searches replacement flights and requests a change quote.
2. Server returns replacement details, old paid value, new total, price difference,
   quote ID and expiry. Quote does not reserve seats.
3. Customer confirms; supplies mock payment form if the difference is positive.
4. Server locks relevant records and rechecks booking revision, quote, inventory,
   flight versions, and balance.
5. Atomically reserve replacement seats, release old seats, settle difference,
   update booking revision, void old tickets, issue replacements and queue delivery.
6. Return updated booking, ticket codes and balance.

Alternatives: cheaper itinerary refunds the difference; equal price changes without
money movement; abandoning/expiring a quote leaves the original booking unchanged.

Failures: QUOTE_EXPIRED, PRICE_CHANGED, SOLD_OUT, VERSION_CONFLICT,
INSUFFICIENT_BALANCE, INVALID_MOCK_PAYMENT, or CHANGE_NOT_ALLOWED. Refresh/requote
as appropriate. Every failed change preserves the original tickets and booking.

Postcondition: one valid itinerary with its matching ledger/tickets; no intermediate
state where the original booking is lost because replacement failed.

## UC11 — Print ticket

Actor/trigger: customer selects Print. Preconditions: owns an issued ticket.

Main flow: retrieve current ticket data → check status → render printable view →
customer chooses printer/PDF → local print operation.

Alternatives: user cancels print dialog without server change. Historical void
tickets may be shown only with an explicit VOID label.

Failures: NOT_FOUND or disconnected when retrieving; local printer failure is a
client error, not a server transaction failure.

Postcondition: server booking state unchanged; no network PRINT command is required.

## UC12 — Receive/review flight notifications

Actor/trigger: flight update/cancellation affects customer's booking.
Preconditions: update committed; notification persisted for that customer.

Main flow:
1. Server persists event ID, affected flight/booking, reason, before/after values.
2. Server pushes event to customer's authenticated connections.
3. Client displays update and refreshes affected booking.
4. Customer opens notification; client marks it read.

Alternatives: offline customer retrieves notification list after next login.
Duplicate delivery is deduplicated by event ID. Out-of-order events trigger refresh;
client does not overwrite newer flight details with an older version.

Failures: push disconnect leaves persisted notification unread; retry/list recovers.
Unknown or another customer's notification ID → NOT_FOUND.

Postcondition: notification remains recoverable independently of live socket delivery.

## UC13 — Change schedule / assign delay

Actor/trigger: admin selects a flight and submits new times/reason.
Preconditions: admin authenticated; flight active and not yet departed.

Main flow:
1. Admin retrieves current flight and version.
2. Admin supplies new departure/arrival instants, change type, reason and expected version.
3. Server validates role, times and version.
4. Transaction updates flight/version, saves audit history, invalidates unpaid holds,
   and persists affected-customer notifications.
5. Commit, return updated flight; deliver notifications afterward.

Alternatives: correcting an existing delay is another versioned update. Confirmed
bookings stay confirmed; customers may later use normal cancellation/change rules.

Failures: customer attempts action → FORBIDDEN; stale edit → VERSION_CONFLICT;
invalid time → VALIDATION_ERROR; cancelled/departed flight → INVALID_STATE.

Postcondition: one auditable update and recoverable notifications. Automatic
rebooking and connection protection are outside proposed direct-flight scope.

## UC14 — Cancel flight

Actor/trigger: admin confirms flight cancellation with reason.
Preconditions: admin authenticated; active future flight.

Main flow:
1. Admin reviews flight and affected booking count.
2. Admin submits cancellation, expected version and stable operation key.
3. Server locks flight/inventory and affected bookings/accounts.
4. In one transaction, server cancels flight and affected bookings, releases seats,
   voids tickets, refunds paid totals once, writes audit and notifications.
5. Server commits and returns summary; notifications are delivered afterward.

Alternatives: HELD bookings cancel without refund. Proposed round-trip policy:
cancellation of either leg cancels/refunds the whole booking. Already cancelled
flight returns current result; no repeated refund.

Failures: FORBIDDEN, NOT_FOUND, VERSION_CONFLICT, INVALID_STATE, or INTERNAL_ERROR.
Rollback leaves no partly refunded/cancelled set. Synchronous processing is proposed
for bounded generated data; large datasets would need a separate batch workflow.

Postcondition: no active ticket remains on the cancelled flight; refunds reconcile.

## Cross-cutting error design

Distinguish three outcomes:

1. Success, including empty search results or a queued delivery.
2. Known rejection: a structured server error; documented state/side effects.
3. Unknown outcome: timeout/disconnect before response; reconcile before retrying
   a mutation. A transport failure does not prove transaction failure.

Proposed error envelope (message action/ID are in the surrounding protocol envelope):

```json
{
  "code": "INSUFFICIENT_BALANCE",
  "message": "Your balance is too low.",
  "retryable": false,
  "details": {
    "required_amount": 2400000,
    "available_balance": 2000000,
    "currency": "VND"
  }
}
```

`retryable` means retrying unchanged input may succeed after a transient condition;
it is not permission to repeat a mutation with a fresh operation key. UI behavior
is driven by stable codes, not by parsing human-readable messages.

| Category | Codes | Client recovery | State guarantee |
|---|---|---|---|
| Framing/protocol | INVALID_MESSAGE, UNSUPPORTED_VERSION, UNKNOWN_ACTION | Correct client; close on unsafe framing | No business handler execution |
| Field validation | VALIDATION_ERROR, INVALID_MOCK_PAYMENT | Highlight safe field errors | No payment/booking mutation |
| Authentication | AUTH_REQUIRED, INVALID_CREDENTIALS | Log in/correct credentials | No unauthorized action |
| Authorization/ownership | FORBIDDEN, NOT_FOUND | Hide action or refresh list | No cross-account disclosure |
| Changed business data | PRICE_CHANGED, SOLD_OUT, FLIGHT_UNAVAILABLE | Refresh/reselect and confirm | No partial reservation/purchase |
| Expiration/state | HOLD_EXPIRED, QUOTE_EXPIRED, INVALID_STATE | Retrieve state; create new hold/quote if needed | Expired hold may be released |
| Policy | CANCELLATION_NOT_ALLOWED, CHANGE_NOT_ALLOWED | Explain policy; keep current booking | No mutation |
| Balance | INSUFFICIENT_BALANCE | Keep hold until expiry; no automatic retry | No deduction |
| Concurrency | VERSION_CONFLICT, IDEMPOTENCY_CONFLICT | Refresh or correct key usage | Existing committed result preserved |
| Temporary/server | RATE_LIMITED, TEMPORARILY_UNAVAILABLE, INTERNAL_ERROR | Back off; reuse operation key | Rollback or recover stored outcome |
| Delivery | DELIVERY_FAILED | Inspect/retry delivery job | Confirmed booking unaffected |
| Transport | Local timeout/disconnect, no server code | Reconnect/login/reconcile | Outcome may already be committed |

Validation order: safe frame/envelope → known action → authentication/role → payload
shape → ownership → idempotency lookup → locked state/policy checks → mutation.
For idempotent retries, return stored results before re-running state-dependent
checks. Do not expose account-specific business details before ownership checks.
Never expose SQL errors, passwords, full card fields or internal stack traces.

Server logs record received/sent/rejected message metadata with redacted payloads;
admin business audit records are persisted in SQL. Log attempted sends separately
from completed socket writes. Never equate a socket write with user acknowledgement.

## Deriving the protocol and tests

Each use-case step that crosses the client/server boundary becomes an operation.
UC05 creates a hold; UC06 confirms payment; UC07 queues/checks delivery. They must
not be compressed into a single success/failure state. UC13 and UC14 produce events
consumed by UC12. UC11 requires data retrieval, not a server print operation.

Required supporting invariants:
- Inventory never exceeds capacity, including concurrent holds.
- Balance never becomes negative; every deduction/refund has a ledger record.
- Stable operation keys prevent duplicate mutations after lost responses.
- All legs of a booking succeed/fail together.
- Admin cancellation racing payment produces either rejection or payment followed
  by one refund; no paid ticket survives cancellation.
- Delivery failures cannot change successful payment into failure.

For each use case, test main flow, each alternative, every listed rejection,
ownership checks, and relevant retry/concurrency races. Cases remain proposed,
not executed or agreed. No implementation should start until scope/policy review.

## Decisions to resolve during review

1. Direct flights with optional round trip only?
2. Ten-minute holds, full pre-departure refunds, entire-booking changes/cancellations?
3. Whole-booking refund when admin cancels one leg of a round trip?
4. Mock card only, or also a mock wallet option?
5. Real test email/SMS or explicitly accepted simulation?
6. Implementation language and SQL engine, after behavior is settled.
