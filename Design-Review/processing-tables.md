# Server and client processing tables

The receiving pipeline and error precedence are defined in [error-catalog.md](error-catalog.md). All messages have both a server handler here and a client recovery path in [use-case-flows.md](use-case-flows.md). No handler has been implemented.

## 1. Transactions, concurrency and restart

Use one process-wide `domainLock` for shared domain state and a durable SQL transaction per mutation. All handlers, sweeper and worker state transitions use it; multi-query reads use the same lock for consistent snapshots. This deliberately simple model replaces the earlier per-flight/ledger lock mix, which left payment and cross-leg admin cancellation insufficiently synchronized.

Acquire domainLock → begin transaction → replay/ownership/quote/state checks → validate authoritative values → mutate → store ledger/jobs/notifications/idempotency result → serialize/size-check saved reply → commit → release domainLock. Perform socket writes, real email provider calls and other slow I/O **after** release. A per-connection queue/writeLock serializes the complete encoded reply/push with a short-write loop. Never hold writeLock while acquiring domainLock.

SQL constraints: unique normalized username, unique booking/ticket IDs, nonnegative balance, heldSeats/soldSeats ≥0 and sum ≤capacity, foreign keys, unique ledger movement for a cancellation, unique (user,type,key) idempotency record and unique delivery job ID. Keep admin audit old/new values with actor/reason. For the small dataset, an admin update can synchronously change all affected round-trip bookings in one transaction. Large batches are outside this proposal.

A 30-second sweeper releases each expired hold once; request handlers also expire relevant holds under the same rules before seat/payment checks. Payment converts held to sold. Startup reloads SQL state, expires overdue holds and resumes queued delivery jobs. Sessions/request IDs are connection-local and never restored after restart.

Persistent entities: users, flights, fares (class/price/capacity/counters), bookings (revision/status/hold expiry/cancellation reason/current fare/net paid/change fees), passengers, booking legs (accepted departure baseline and current itinerary), tickets, immutable balance ledger, change quotes, notifications, delivery jobs and idempotency results. Change quotes bind owner, replacement, revisions/versions, amounts, expiry and consumed state. Cancellation needs no stored quote. This is a logical data model; engine-specific DDL is a future implementation artifact.

## 2. Server handling by message

Checks in the table occur inside the transaction/lock when they depend on mutable domain state. Shared auth/shape checks run first. Applied mutations check their durable operation key before state eligibility. Cancellation dry runs only preview; change dry runs persist quotes without applying a booking/seat/money mutation.

| Message | Authoritative processing | Reply and durable effect |
|---|---|---|
| `PING` | Read server clock | serverTime; no domain effect |
| `REGISTER` | Validate BR-01/02, normalize username, hash password; enforce unique username | USER profile and seeded balance; stays ANON; no password in result/log |
| `LOGIN` | Verify stored hash and role; count own unread notifications | Bind identity; USER includes balance/currency/unread count; queue success before enabling this customer socket for pushes |
| `LOGOUT` | Queue success, stop accepting new requests; remove push registration | Flush success then close; no booking change |
| `GET_BALANCE` | Read own balance snapshot | balance/currency |
| `SEARCH_FLIGHTS` | Validate route/date/count/class; release stale relevant holds; filter eligible flights for each direction; sort value then ID | Priced offers; no reservation |
| `COMPARE_FLIGHTS` | Resolve all IDs, same route/date/class and live eligibility; compute totals, minima and deltas | Rows in request order; no reservation |
| `BOOK_FLIGHT` | Replay; resolve both legs and passenger data, route/time order, current price, eligibility and live inventory | All-leg hold or none; booking revision 1, total, expiry, replay result; no debit |
| `PAY_BOOKING` | Replay; owner; expire hold if due; special invalidated-hold errors; PENDING_PAYMENT; flight eligibility; balance | Atomic debit + ledger + held→sold + TICKETED/revision + tickets + delivery jobs + persisted QUEUED replay result |
| `RESEND_TICKET` | Owner and TICKETED; create one real-email job to saved contactEmail using existing codes; no channel/destination input | channel EMAIL and QUEUED/SENT/FAILED with masked email; no money/ticket issue |
| `LIST_BOOKINGS` | Own rows, status filter, bounded pagination | Newest-first summaries and nextOffset |
| `GET_BOOKING` | Own booking; expose current itinerary, delivery, status and revision | Full detail; cancelled tickets remain historical/invalid |
| `CANCEL_BOOKING` dry | Owner; live pending/ticketed; hold expiry and BR-31 eligibility | Advisory preview: fee 0, full current fare refund for eligible paid booking or zero for unpaid, bookingRevision and balanceIfApplied; no stored quote |
| `CANCEL_BOOKING` apply | Replay; owned booking; expire due hold; live state; paid departure cutoff/disruption rule | Whole-booking CANCELLED, all-leg release, full fare refund once (zero if unpaid), revision increment, save replay result; no cancellation quote or fee calculation |
| `CHANGE_BOOKING` dry | Owner; TICKETED; current/replacement departures ≥2h, same route/class, round-trip order, live seats; compute fee/difference | Persist 60-second quote binding booking/replacement/flight versions and amounts; no seats reserved |
| `CHANGE_BOOKING` apply | Replay; owned quote/booking; expiry/snapshots, eligibility, replacement inventory and balance | Atomic seat swap + ledger + fare/net-paid change + revision + baseline + ticket current itinerary + delivery jobs + consume quote + replay result; failure leaves original intact |
| `PRINT_TICKET` | Own TICKETED booking; render bounded current text snapshot | filename/mimeType/lines; printing or saving is local and changes no server state |
| `GET_NOTIFICATIONS` | Own persisted rows, unread filter, bounded pagination | Complete Notification objects + read + nextOffset |
| `ACK_NOTIFICATION` | Validate all IDs owned before marking any; already-read IDs allowed | Mark all read atomically; acknowledged = number of distinct supplied owned IDs, including already read |
| `ADMIN_LIST_FLIGHTS` | Apply filters and pagination; derive departed status and economy availability | Flight versions/current data + nextOffset |
| `ADMIN_UPDATE_FLIGHT` | Replay; lookup; active/future flight; expectedVersion; action-specific validation; affect only live bookings | Atomic flight/version + all affected bookings/legs/inventory/ledger/notifications/audit + replay snapshot; queue pushes after commit |

PAY's canonical success result is persisted in the payment transaction with one email job and status QUEUED. The worker sends real email after commit, but the payment reply and all replays use the persisted QUEUED snapshot. GET_BOOKING shows the latest email job status for the booking; RESEND_TICKET reports its new job's current QUEUED/SENT/FAILED status. No post-commit email failure is reported as payment rollback.

### Admin apply rules

| Action | Flight | Each TICKETED booking | Each live PENDING_PAYMENT booking |
|---|---|---|---|
| DELAY | Add delayMinutes to current departure/arrival; status DELAYED; version+1 | Update affected leg, revision+1; persist DELAY notification; waiver uses absolute net shift from that leg's accepted baseline | Cancel **entire** booking with reason FLIGHT_UPDATED; release all leg holds; zero refund |
| RESCHEDULE | Set future departure/arrival with arrival>departure; status RESCHEDULED; version+1 | Same, SCHEDULE_CHANGE notification; refresh if itinerary becomes inconvenient; no implicit rebooking | Same invalidation as DELAY |
| CANCEL | Set CANCELLED; version+1 | FLIGHT_CANCELLED; release all sold legs; void travel validity; refund outstanding net paid including change fees once; persist refund notification | CANCELLED reason FLIGHT_CANCELLED; release all leg holds; zero refund |

Ignore already terminal bookings when computing effects/refunds. Snapshot affectedBookings and notificationsCreated after mutation. pushedOnline counts eligible customer connections selected for queueing, not acknowledged delivery. Save counts in the same transaction; replay does not enqueue pushes again. A crash before queueing is recovered through GET_NOTIFICATIONS, not a second admin mutation.

Payment racing any admin update is serialized: payment first then DELAY/RESCHEDULE retains paid booking and notifies; update first invalidates hold and payment fails. Cancellation after payment refunds once; cancellation first prevents payment. Last-seat booking and cleanup races use the same serialization.

## 3. Delivery and notification processing

| Situation | Required processing |
|---|---|
| Payment/change commits | One real-email job already exists in SQL for saved contactEmail; worker checks TICKETED and job revision before claiming; obsolete jobs become nonretryable FAILED (SUPERSEDED). Send through configured provider, then record SENT on acceptance or FAILED on error/timeout |
| Provider failure or restart | Persist job ID, attempt count, safe failure reason, next retry time and provider reference when available. Resume queued/retryable jobs with bounded backoff; no ticket issue/charge is repeated. A crash/timeout after provider acceptance can cause duplicate email on retry; do not promise exactly-once receipt |
| Customer online | Persist notification first, then enqueue NOTIFY on every authenticated customer connection |
| Customer offline or push fails | Notification stays unread; pull after login recovers it |
| Duplicate/out-of-order event | Client deduplicates notificationId; refresh booking rather than replacing newer itinerary with old event fields |
| Read acknowledgment | ACK_NOTIFICATION is the user's read action; a successful socket write is not a read acknowledgment |

Email states: QUEUED → SENT or FAILED; retryable FAILED → QUEUED. SENT means provider acceptance, not proof of arrival/read. R7 runtime evidence must include the actual email in a controlled recipient inbox. Contacts are masked in responses and removed from logs. The persisted SQL queue stores work to perform; merely writing a local queue/log file does not fulfill email delivery.

Server configuration supplies the real provider/sender and credentials; do not accept credentials, sender overrides or arbitrary recipients from FBP messages. Use a protected provider connection. Proposed retry policy: at most three attempts per job, with backoff before automatic retries; permanent rejection and SUPERSEDED do not retry automatically. After exhaustion, preserve FAILED and allow an explicit RESEND_TICKET. One worker claims a job at a time; a stable job/message identifier helps correlate attempts but does not guarantee provider deduplication. Email includes booking code, ticket numbers, passenger display names, itinerary/class and booking revision, with guidance to check current app details because a cancellation can race sending.

## 4. Server logging — R2

Write to console and append-only `logs/server-YYYYMMDD.log`. Record timestamp (+07:00), event, direction (RECV/SEND where applicable), connection ID, peer, authenticated user ID, request/event ID/type, **original payload UTF-8 byte count**, safe redacted object, code and duration. Byte count describes the transmitted payload, not the redacted serialization.

- Lifecycle: CONNECT, DISCONNECT with LOGOUT/IDLE/ERROR/OVERSIZE/TRUNCATED_FRAME/FRAME_TIMEOUT.
- Receipt: RECV even for rejected frames. Parse safely before rendering a redacted object.
- Sending: SEND_ATTEMPT before writing; SEND_SUCCESS only after every byte and LF has been written; SEND_FAILURE if incomplete. These describe local socket writes only.
- Redact recursively: password, fullName/passengerName, dob, idNumber, email/contactEmail/to and contact-like embedded strings. Never log provider credentials or email bodies; log job/attempt IDs and safe outcomes. For PRINT_TICKET log filename/line count in place of lines; for notification message log kind/ID instead of free text.
- Invalid JSON/UTF-8/oversize: length and reason only, no raw input, to prevent malformed credentials leaking.
- Domain events: hold expiration, delivery job transition and admin audit identity/result. Never put passwords, personal data or SQL internals into user-facing errors.

Illustrative metadata (length omitted because this is not an actual captured frame):

```text
2026-11-04T10:22:03.114+07:00 event=RECV conn=7 user=U-1001 type=PAY_BOOKING id=c-011 code=-
2026-11-04T10:22:03.116+07:00 event=SEND_SUCCESS dir=SEND conn=7 type=PAY_BOOKING_RESP id=c-011 code=OK
```

Actual log records must include peer, original byte count and redacted content per the field list. Example protocol credentials are synthetic wire fixtures, not acceptable production log content.

## 5. Client handling and recovery

| Received / local trigger | Client action and next state |
|---|---|
| Success matching pending ID/type | Resolve pending call; display authoritative result; return to READY unless logout closes |
| Known error | Dispatch by stable code; validation highlights safe field, auth offers login, ownership hides record, state/version/expiry refreshes/requotes; no automatic mutation with a fresh key |
| NOTIFY while waiting for reply | Persist/deduplicate event ID locally; show banner/refresh booking; keep waiting for the original ID |
| Unknown response ID/type or invalid server frame | Protocol diagnostic, close, reconcile pending mutation after login |
| Ten-second request timeout / socket loss | Outcome UNKNOWN; retain mutation payload/key; close, reconnect/backoff 2/4/8 seconds, login again, retry same key or fetch current state |
| Successful old-key replay | Show saved result as operation outcome, then GET_BOOKING/GET_BALANCE/notification list for current data |
| Quote expired or version changed | Obtain new quote, show new amount/itinerary and obtain new user acceptance before applying |
| Local print failure/cancel | Show local error or close dialog; server booking unchanged |

Read-only requests may be repeated. REGISTER recovery uses LOGIN; ACK_NOTIFICATION is idempotent; RESEND_TICKET may duplicate only delivery. LOGOUT connection loss means logged out locally. All applied BOOK/PAY/CANCEL/CHANGE/ADMIN_UPDATE requests use their original durable key across reconnect and restart.
