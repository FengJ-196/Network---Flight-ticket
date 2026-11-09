# Flight booking protocol — discussion draft

Historical discussion draft. The current proposal uses the expanded FBP names in `Design-Review` and NDJSON; see [README](../Design-Review/README.md) and [design-review.md](../Design-Review/design-review.md) for source precedence and differences. The workspace/exercise references below describe the earlier discussion context.

Current R7 scope is confirmed: real email only; SMS options and delivery simulation discussed below are historical alternatives, not the selected design.

## 1. Current design

The workspace contains C socket exercises, including `multiTCP/server_windows.c`
and `multiTCP/client_windows.c`. They relay bytes between two clients. There is
no flight application, structured message protocol, authentication, or SQL schema.
This document proposes a new application protocol; it does not change those exercises.

User requirements: customers and admins; generated flight data; SQL persistence;
search and comparison; booking and ticket management; flight updates; mock card
form with payment deducted from the customer's application balance.

All policies below are proposed defaults, not yet agreed requirements.

## 2. Proposed design

### Phase 1 — Message contract and connection

Use a persistent TCP socket per connected client. All messages use this frame:

```text
4-byte unsigned payload length in network byte order | UTF-8 JSON payload
```

Length counts JSON bytes only. Allow 1–65,536 bytes. Buffer partial frames and
process multiple frames in one read. Loop on partial writes. Serialize all writes
to a socket so responses and events cannot interleave inside a frame. Close on
invalid lengths or incomplete-frame timeout; return a structured error for a
complete but invalid JSON message when possible. Do not log raw invalid payloads.

Three message kinds:

```json
{"version":1,"kind":"request","request_id":"r-101","action":"FLIGHT.SEARCH","data":{"origin":"SGN","destination":"HAN","departure_date":"2026-11-10","return_date":null,"passengers":2,"seat_class":"ECONOMY","limit":20,"cursor":null}}
```

```json
{"version":1,"kind":"response","request_id":"r-101","action":"FLIGHT.SEARCH","ok":true,"data":{"outbound_options":[],"return_options":[],"next_cursor":null}}
```

```json
{"version":1,"kind":"response","request_id":"r-102","action":"BOOKING.PAY","ok":false,"error":{"code":"INSUFFICIENT_BALANCE","message":"Your balance is too low.","details":{"required_amount":2400000,"available_balance":2000000}}}
```

```json
{"version":1,"kind":"event","event_id":"evt-501","action":"FLIGHT.UPDATED","data":{"flight_id":"flt-17","flight_version":4,"change_type":"DELAY","previous_departure_at":"2026-11-10T01:00:00Z","departure_at":"2026-11-10T03:00:00Z","reason":"Weather"}}
```

Request IDs correlate responses; events may arrive between responses. Use one
request processor per connection for v1; different connections run concurrently.
The client keeps receiving even while the user is entering a form.

Money is an integer number of VND; never a floating-point value. Instants use UTC
ISO 8601. Search dates use the departure airport's local calendar date. IDs are
opaque strings. Every returned fare includes currency, total per passenger
including fees, departure/arrival instants, airline, duration, and available seats.
Bound strings, passenger count (proposed 1–9), and list sizes; paginate large lists.

### Phase 2 — Actions and authorization

| Action | Who | Input → result |
|---|---|---|
| AUTH.REGISTER | Guest | Email, password, name, optional phone → customer ID |
| AUTH.LOGIN | Guest | Email, password → user ID, server-assigned role, balance |
| AUTH.LOGOUT | Signed in | Empty → clear connection authentication |
| ACCOUNT.GET | Signed in | Empty → own profile and current balance |
| FLIGHT.SEARCH | Guest/customer | Route, dates, count, class, pagination → outbound/return options |
| FLIGHT.COMPARE | Guest/customer | 2–10 fare IDs and passenger count → common comparison fields and totals |
| BOOKING.CREATE | Customer | Fare IDs (one or two legs), passenger details, idempotency key → held booking, total, expiry |
| BOOKING.PAY | Customer | Booking ID, mock card form, idempotency key → paid booking, ticket codes, balance |
| BOOKING.LIST | Customer | Pagination → own bookings |
| BOOKING.GET | Customer | Booking ID → own booking, tickets, current flight details |
| BOOKING.CANCEL | Customer | Booking ID, idempotency key → cancelled booking, refund, balance |
| BOOKING.CHANGE_QUOTE | Customer | Booking ID, replacement fare IDs → expiring quote and signed price difference |
| BOOKING.CHANGE | Customer | Booking ID, quote ID, mock form if extra payment, idempotency key → replacement tickets, balance |
| TICKET.GET | Customer | Ticket ID → own printable ticket data |
| TICKET.SEND | Customer | Booking ID, EMAIL or SMS, idempotency key → delivery job ID |
| DELIVERY.GET | Customer | Delivery job ID → own delivery status |
| NOTIFICATION.LIST | Signed in | Pagination → own persisted notifications |
| NOTIFICATION.ACK | Signed in | Event IDs → mark own notifications read |
| ADMIN.FLIGHT.UPDATE | Admin | Flight ID, expected version, new departure/arrival times, change type, reason, idempotency key → updated flight |
| ADMIN.FLIGHT.CANCEL | Admin | Flight ID, expected version, reason, idempotency key → cancelled flight and affected booking count |
| PING | Any | Empty → server time |

The server derives user and role from connection authentication, never from a
client-supplied user ID or role. Registration always creates a customer; provision
admins separately. Require fresh login after reconnect in v1. Store password
hashes, never plaintext. Use synthetic credentials/card data in a local demo;
any real credentials would require encrypted transport.

Common error codes: INVALID_MESSAGE, UNSUPPORTED_VERSION, UNKNOWN_ACTION,
VALIDATION_ERROR, AUTH_REQUIRED, INVALID_CREDENTIALS, EMAIL_EXISTS, FORBIDDEN,
NOT_FOUND, INVALID_STATE, SOLD_OUT, HOLD_EXPIRED, QUOTE_EXPIRED, PRICE_CHANGED,
FLIGHT_UNAVAILABLE, INSUFFICIENT_BALANCE, INVALID_MOCK_CARD, VERSION_CONFLICT,
IDEMPOTENCY_CONFLICT, RATE_LIMITED, INTERNAL_ERROR. Return NOT_FOUND for another
customer's booking/ticket. Failed operations never partially change money or seats.

### Phase 3 — State machines

Connection authentication:

```text
DISCONNECTED --connect--> GUEST
GUEST --valid login--> CUSTOMER or ADMIN
CUSTOMER / ADMIN --logout--> GUEST
any connected state --disconnect--> DISCONNECTED
```

Registration leaves the connection in GUEST. Failed login leaves it unchanged.
Search and compare do not change connection state. UI pages are separate from
protocol states; the server validates each request independently.

Booking:

```text
HELD --successful payment--> CONFIRMED
HELD --expiry--> EXPIRED
HELD --customer cancellation / flight cancellation--> CANCELLED
CONFIRMED --customer cancellation / flight cancellation--> CANCELLED
CONFIRMED --successful change--> CONFIRMED (new revision and ticket codes)
```

Create reserves seats for a proposed 10 minutes; no deduction yet. Failed payment
leaves the hold intact until expiry. Payment must check expiry even if the cleanup
worker has not run. Terminal bookings cannot be paid, changed, or refunded again.
A confirmed booking remains confirmed during schedule changes and delays.

Flight:

```text
SCHEDULED --admin delay--> DELAYED
SCHEDULED / DELAYED --admin reschedule--> SCHEDULED or DELAYED
SCHEDULED / DELAYED --admin cancel--> CANCELLED
```

CANCELLED is terminal in v1. RESCHEDULE and DELAY are change types; the current
departure and arrival times are explicit values, not accumulated delay increments.
Reject departure in the past, arrival before departure, and edits after departure.
Keep the original scheduled times separately. Derive DELAYED when current departure
is later than original departure. Block customer cancellation/change after the
earliest current departure of the booking; check inside the transaction.

Payment: each successful money movement is an immutable ledger record. A rejected
payment is an error, not a booking state. Refunds reference the original payment.

Tickets: ACTIVE → VOID when cancelled or replaced. Issue one code per passenger
per flight leg after payment. Ticket printing is a client operation using TICKET.GET.
The ticket includes both issued itinerary and current flight information.

Delivery: QUEUED → SENT, or QUEUED → FAILED; failed jobs can be retried. Payment
success does not depend on email/SMS success. A simulation must be labelled
SIMULATED in the result and must not claim actual email/SMS delivery.

### Phase 4 — Message processing and transactions

General server pipeline:

```text
receive bytes → assemble frame → parse/validate envelope → log redacted receipt
→ check authentication/role → validate action payload → check ownership
→ dispatch handler → SQL transaction if needed → commit
→ enqueue response → log redacted send result
```

Malformed, rejected, and failed messages are also logged with a safe reason.
After commit, a separate delivery worker processes persisted outbox entries.
Push events only to the relevant authenticated user's connections. The client
deduplicates by event ID and refreshes affected records; events can be replayed.
After reconnect/login, fetch notification and booking lists to recover missed updates.

Booking creation transaction:

1. Resolve fare IDs and validate route, date order, class, passenger data, and availability.
2. Lock inventory in stable ID order; expire stale holds for those rows.
3. Compute total on the server. Reserve every requested leg or none.
4. Insert HELD booking, passenger/leg records, price snapshot and expiry.
5. Persist idempotent result and commit; return the server's total for confirmation.

Payment transaction:

1. Check ownership and idempotency result before re-executing anything.
2. Validate mock-only form: cardholder, synthetic card number, expiry and CVV.
3. Lock booking, account and inventory using a consistent global lock order;
   recheck HELD state, expiry and flight availability under those locks.
4. Deduct the exact held total only if balance is sufficient; insert payment ledger.
5. Convert held inventory to sold inventory, confirm booking, issue unique codes,
   and insert ticket delivery/outbox jobs in the same transaction.
6. Store response for the idempotency key, commit, then send it.

Client mutations carry a stable idempotency key retained across reconnects and
timeouts. Store uniqueness on (user, action, key), a canonical request fingerprint,
and the result in SQL. Concurrent duplicates execute once; exact retries return
the saved result; different payloads with the same key return IDEMPOTENCY_CONFLICT.
Do not retain full card numbers/CVV in fingerprints, responses, DB or logs; for
mock validation derive only a non-sensitive validated payment descriptor.
Return current booking/account state through GET after replaying an old result.

Proposed simplified commercial policies:

- Full refund for customer cancellation before departure.
- Whole-booking operations only: no partial passenger/leg cancellation or change.
- A round trip holds and pays for both legs atomically.
- Changing creates a short-lived price quote without holding replacement seats.
  Confirmation rechecks quote expiry, booking revision, flight versions and seats;
  reject stale quotes and request a new quote. Replace inventory/tickets, charge
  positive difference or refund negative difference atomically. Keep old tickets
  valid if the change fails. Notify the customer of the replacement codes.
- Cancelling any leg by admin cancels the entire affected booking and refunds its
  paid total. Lock affected rows, release holds/sold seats, void tickets, write
  refunds and notifications atomically. For the generated-data course project,
  perform this bounded operation synchronously; large production batches need
  a separate workflow. Repeated cancellation cannot create a second refund.
- Rescheduling/delay increments flight version, records history, and persists one
  notification per affected customer in the same transaction. Invalidate HELD
  bookings on that flight so customers must confirm the revised itinerary again.
- Seed balances as test data; no customer-controlled balance top-up in v1.

Admin update and customer payment must lock shared flight/inventory rows so a
payment racing cancellation either commits before cancellation and gets refunded,
or observes cancellation and fails. Retry deadlock/serialization failures within
a bounded policy. Cleanup and request handlers use the same lock/state rules.

### Phase 5 — SQL and logging

Minimal relational entities:

- users: unique normalized email, password hash, role, balance, contact details.
- airports: code and time zone; airlines: ID and display name.
- flights: airline, route, original/current times, status, version.
- flight_fares: flight, class, price, capacity, held seats, sold seats, version.
- bookings: owner, status, total, currency, expiry, revision.
- booking_passengers and booking_legs: passenger details, selected fares and prices.
- tickets: unique code, booking/passenger/leg, revision, ACTIVE/VOID.
- balance_ledger: user, booking, charge/refund, amount, original payment reference.
- change_quotes: owner, booking revision, replacement fares/versions, total, expiry.
- flight_changes: actor, old/new values, reason, timestamp.
- notifications: user, event ID, type, payload, created/read timestamps.
- delivery_jobs/outbox: destination, channel, payload, status, attempts, next retry.
- idempotency_records: user/action/key, fingerprint, saved result.

Enforce foreign keys, unique ticket codes, nonnegative balances and inventory,
held + sold <= capacity, and unique refund references. Availability is capacity
minus live held/sold seats. Use transactions; do not trust client totals. Exact
locking syntax and schema DDL depend on the selected SQL engine.

Server logs: timestamp, direction, connection ID, authenticated user ID if any,
request/event ID, action, byte count, redacted data, result/error and duration.
Record SEND_ATTEMPT/SEND_SUCCESS/SEND_FAILURE separately; a successful local socket
write does not mean the customer read it. Redact passwords, mock card fields,
contact addresses and passenger personal data. Keep admin audit history in SQL.

## 3. Test specification

Proposed cases for review; none have been agreed or executed yet:

| Case | Expected assertion |
|---|---|
| Fragmented frame; two coalesced frames; partial writes | Exactly the original messages, parsed once each |
| Bad length, JSON, version, action, timeout | Defined error/close; no handler side effects |
| Registration/login/logout | Duplicate email rejected; hash stored; role cannot be selected by client |
| Permission and ownership | Customer cannot invoke admin action or access another customer's records |
| Search one-way/return, class, count, airport dates | Correct options, totals, pagination and available seats |
| Compare two airlines | Same passenger count/currency basis; accurate elapsed durations and prices |
| Two customers contend for last seat | At most one hold succeeds; inventory constraints remain true |
| Pay a hold with 5,000,000 VND balance and 2,400,000 VND total | Balance 2,600,000; one charge; confirmed booking and unique codes |
| Bad mock card, low balance, expired hold | No deduction/tickets; expired inventory released once |
| Response lost after payment commit; repeat on new connection | Same saved outcome; no duplicate charge or tickets |
| Cancel twice / concurrent cancel | Exactly one refund; tickets void; inventory released once |
| Change to higher/lower fare, stale quote or sold-out replacement | Correct difference; failure preserves original booking |
| Admin delay/reschedule/cancel races payment | Valid serial outcome; cancellation refund once; version checks work |
| Customer offline during admin update | Persisted notifications available after login |
| Delivery failure / server restart after commit | Booking remains paid; pending delivery resumes without charging again |
| Print ticket / replaced code | Current ticket renders; void ticket clearly identified |
| Log inspection | Received/sent/rejected actions traceable; sensitive fields absent |

Unresolved decisions for discussion:

1. Keep C/Winsock or choose another implementation language? Which SQL engine?
2. Real test email/SMS delivery or a clearly labelled simulated delivery inbox?
3. Approve the proposed hold, refund, change and whole-booking cancellation policies?
4. Are direct flights sufficient, with one outbound and optional return leg?
5. Is the wallet an alternate mock form, or is mock card checkout the only required flow?

Next review: settle these defaults, then specify each action's exact payload and
error precedence before implementing server handlers.
