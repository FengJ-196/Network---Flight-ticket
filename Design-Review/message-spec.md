# FBP message specification (v1)

Machine-readable twin: `message-catalog.json`. Examples: `wire-examples.md`. Behavior: `processing-tables.md`.

## 1. Transport and framing

- **TCP**, server listens on a configurable port (default `9090`). Reliable ordered stream is needed for payments (assumption A1; UDP rejected).
- **Framing: newline-delimited JSON (NDJSON)**. One message = one UTF-8 JSON object on one line ending with `\n` (`\r\n` tolerated). JSON text must not contain raw newlines (they are escaped as `\n`).
- Max frame 65,536 bytes. Longer → `E_FRAME_TOO_LARGE`, then server closes the connection (stream cannot be resynchronized).
- Idle timeout: server closes a connection with no traffic for 300 s. Clients should send `PING` every 60 s.
- Server serializes writes per connection (one writer lock) so frames never interleave.

The limit counts UTF-8 JSON **payload bytes**, excluding LF and an optional CR immediately before it. No BOM, blank lines, duplicate JSON keys, non-finite numbers or outer whitespace. Decode strict UTF-8 only after buffering a full line; retain an incomplete suffix and drain all complete lines in order. Enforce the byte limit while buffering (one pending CR byte is allowed). Use a write loop for short writes, through the same serialized queue for replies and pushes.

EOF mid-frame discards the unfinished frame, logs TRUNCATED_FRAME and closes without dispatch. Incomplete-frame deadline: 10 seconds from its first byte; close/log FRAME_TIMEOUT without a reply. Oversize replies with `ERROR_RESP` if possible, then closes. Idle is measured from **received** complete frames, so outgoing pushes do not keep abandoned clients alive. No server greeting is required.

## 2. Envelope

Request (client → server):
```json
{"v":1,"type":"LOGIN","id":"c-004","data":{ ... }}
```
Response (server → client):
```json
{"v":1,"type":"LOGIN_RESP","id":"c-004","ok":true,"code":"OK","data":{ ... }}
{"v":1,"type":"LOGIN_RESP","id":"c-004","ok":false,"code":"E_BAD_CREDENTIALS","message":"...","data":{ ... }}
```
Push (server → client, unsolicited):
```json
{"v":1,"type":"NOTIFY","id":null,"data":{ ... }}
```

| Field | Rules |
|---|---|
| `v` | integer 1; wrong type → `E_VALIDATION`; another integer → `E_UNSUPPORTED_VERSION` |
| `type` | 1–64 ASCII uppercase/underscore characters; reply = request type + `_RESP`; valid but unknown name → `E_UNKNOWN_TYPE` |
| `id` | client-chosen string, 1–64 ASCII `[A-Za-z0-9_-]`, unique per connection; echoed in reply. `null` for pushes and uncorrelatable `ERROR_RESP` |
| `ok`/`code` | `true`/`"OK"` or `false`/`E_*` (see `error-catalog.md`) |
| `message` | human-readable English text on errors only; clients must key on `code` |
| `data` | object; absent fields are not allowed to be `null` unless stated |

Rules: the client sends **one request at a time** (waits for its response, timeout 10 s). A `NOTIFY` may arrive *between* a request and its response; clients must dispatch by `type`/`id`, not by arrival order. Unknown extra fields in `data` are rejected with `E_VALIDATION` (strict, so typos are found early). Passwords are plaintext inside `data` on the wire (course environment); a production system would use TLS.

Common value types: `Money` integer VND; `Time` ISO-8601 with offset; `Date` `YYYY-MM-DD`; `SeatClass` `ECONOMY|PREMIUM_ECONOMY|BUSINESS`.

Request keys are exactly `v,type,id,data`, all required; `v` is integer 1 (booleans rejected), `type` a string and `data` an object. Responses require `v,type,id,ok,code,data`, plus `message` on failure only. Pushes use `v,type,id,data`. Reject wrong-direction types. Duplicate request IDs → `E_VALIDATION`; durable mutation keys are separate from request IDs.

A recognized request with valid envelope uses its typed `_RESP` for auth/domain failures. Invalid JSON, UTF-8, duplicate keys, non-object JSON, blank/BOM-prefixed payload or outer whitespace → `ERROR_RESP`, `id:null`, `E_BAD_JSON`. Unsupported version, unknown type or invalid envelope → `ERROR_RESP`, echoing a valid ID if available, otherwise null. Invalid envelope uses `E_VALIDATION`. These complete-line rejections keep the connection open. EOF/frame timeout has no guaranteed reply.

## 3. Shared objects

**Offer**: `{flightId, version, airline:{code,name}, flightNo, origin, destination, departAt, arriveAt, durationMin, status, seatClass, pricePerPax, totalPrice, seatsLeft}` (`totalPrice = pricePerPax × passengers`).

**Passenger**: `{fullName, dob:Date, idNumber}`.

**Leg** (in bookings): `{legType:"OUTBOUND"|"RETURN", flightId, flightNo, origin, destination, departAt, arriveAt, flightStatus, fare}`.

`fare` covers all passengers on that leg. BOOK returns its explicitly listed compact Leg subset. Ticket is `{passengerName,ticketNo}`; one ticket covers that passenger's current booking legs under the simplified demo model. Identifiers remain stable after a change; revision invalidates older printable data.

**BookingStatus**: `PENDING_PAYMENT|TICKETED|EXPIRED|CANCELLED|FLIGHT_CANCELLED`. **FlightStatus**: `SCHEDULED|DELAYED|RESCHEDULED|CANCELLED|DEPARTED`.

## 4. Message catalog

Roles: A = anonymous, U = USER, M = ADMIN. "Common errors" (`E_BAD_JSON`, `E_UNSUPPORTED_VERSION`, `E_UNKNOWN_TYPE`, `E_FRAME_TOO_LARGE`, `E_VALIDATION`, `E_NOT_AUTHENTICATED`, `E_FORBIDDEN`, `E_INTERNAL`) can follow any request and are not repeated below.

### 4.1 Session and account

| Type | Roles | Request `data` | Success `data` | Specific errors |
|---|---|---|---|---|
| `PING` | A U M | — | `{serverTime}` | — |
| `REGISTER` | A | `username, password, fullName, email` | `{userId, username, role:"USER", balance, currency}` | `E_USERNAME_TAKEN`, `E_ALREADY_LOGGED_IN` |
| `LOGIN` | A | `username, password` | `{userId, username, role, balance?, currency?, unreadNotifications?}` (balance/unread only for USER) | `E_BAD_CREDENTIALS`, `E_ALREADY_LOGGED_IN` |
| `LOGOUT` | U M | — | `{}`; server then closes the connection | — |
| `GET_BALANCE` | U | — | `{balance, currency}` | — |

Validation: `email` contains one `@` and a dot in the domain. No phone field is accepted.

### 4.2 Search and compare

| Type | Roles | Request `data` | Success `data` | Specific errors |
|---|---|---|---|---|
| `SEARCH_FLIGHTS` | U | `origin, destination, departDate, passengers (1-9), seatClass`, optional `returnDate`, `sortBy` (`PRICE` default, `DEPARTURE`, `DURATION`) | `{passengers, seatClass, currency, outbound:[Offer], inbound:[Offer]}` (`inbound` is `[]` when no `returnDate`) | — |
| `COMPARE_FLIGHTS` | U | `flightIds` (2–5 distinct, same route/date), `seatClass, passengers` | `{rows:[Offer + priceDeltaVsCheapest + durationDeltaVsFastestMin], cheapestFlightId, fastestFlightId}` | `E_NOT_FOUND`, `E_FLIGHT_UNAVAILABLE`, `E_SEATS_UNAVAILABLE` |

Mixed routes/dates, duplicates or missing class → `E_VALIDATION` (`field:"flightIds"`). Cancelled/departed → `E_FLIGHT_UNAVAILABLE`; too few seats → `E_SEATS_UNAVAILABLE`. Rows retain request order; cheapest/fastest ties use ascending flightId.

### 4.3 Booking and payment

| Type | Roles | Request `data` | Success `data` | Specific errors |
|---|---|---|---|---|
| `BOOK_FLIGHT` | U | `outboundFlightId`, optional `returnFlightId`, `seatClass, passengers:[Passenger] (1-9), contactEmail, idempotencyKey` | `{bookingCode, status:"PENDING_PAYMENT", totalAmount, currency, holdExpiresAt, legs:[{legType,flightId,flightNo,departAt,fare}]}` | `E_NOT_FOUND`, `E_FLIGHT_UNAVAILABLE`, `E_SEATS_UNAVAILABLE`, `E_IDEMPOTENCY_CONFLICT` |
| `PAY_BOOKING` | U | `bookingCode, paymentMethod (`CREDIT_CARD` or `E_WALLET`), idempotencyKey` | `{bookingCode, status:"TICKETED", paid, balanceAfter, currency, eTicketCode, tickets:[{passengerName,ticketNo}], delivery:{email:{to,status}}}` (`to` masked) | `E_NOT_FOUND`, `E_STATE_CONFLICT`, `E_HOLD_EXPIRED`, `E_FLIGHT_UNAVAILABLE`, `E_INSUFFICIENT_BALANCE`, `E_IDEMPOTENCY_CONFLICT` |
| `RESEND_TICKET` | U | `bookingCode` | `{channel:"EMAIL", to, status}` | `E_NOT_FOUND`, `E_STATE_CONFLICT` (not TICKETED) |

BOOK and PAY success also include `revision` (integer ≥1). **Email is the only delivery channel.** `delivery` contains only `email:{to,status}` once a delivery job exists; `to` is the masked booking contact email. `status` is `QUEUED`, `SENT` (real email provider accepted it), or `FAILED`. PAY always returns its persisted QUEUED snapshot, including on replay; GET_BOOKING returns the latest job status for the booking. SENT is provider acceptance, not mailbox receipt/read confirmation. Failed delivery does not roll back payment. RESEND_TICKET always uses saved contactEmail; it accepts neither a channel selector nor a destination override. Its reply may be QUEUED, SENT or FAILED. A retry may duplicate an email, never payment/tickets. Provider credentials stay on the server and are never wire fields.

### 4.4 Manage bookings

| Type | Roles | Request `data` | Success `data` | Specific errors |
|---|---|---|---|---|
| `LIST_BOOKINGS` | U | optional `status,limit,offset` | `{bookings:[{bookingCode,status,route,firstDepartAt,passengers,totalAmount}],nextOffset}` newest first | — |
| `GET_BOOKING` | U | `bookingCode` | `{bookingCode,revision,status,seatClass,passengers:[Passenger],legs:[Leg],tickets,totalPaid,currency,disrupted,createdAt,paidAt,delivery}` | `E_NOT_FOUND` |
| `CANCEL_BOOKING` | U | `bookingCode`, optional `dryRun` (default false); apply requires `idempotencyKey` | `{dryRun,bookingCode,fee:0,feeReason,refundAmount,currency}` plus optional preview `{bookingRevision,balanceIfApplied}` or applied `{status,revision,balanceAfter}` | `E_NOT_FOUND`, `E_STATE_CONFLICT`, `E_CANCEL_NOT_ALLOWED`, `E_IDEMPOTENCY_CONFLICT` |
| `CHANGE_BOOKING` | U | `bookingCode,legType,newFlightId`, optional `dryRun`; apply requires `quoteId,idempotencyKey` | `{dryRun,bookingCode,legType,newFlight:{flightId,flightNo,departAt,arriveAt},changeFee,fareDifference,netAmount,currency}` plus quote `{quoteId,quoteExpiresAt,bookingRevision,balanceIfApplied}` or applied `{status,revision,balanceAfter}` | `E_NOT_FOUND`, `E_STATE_CONFLICT`, `E_CHANGE_NOT_ALLOWED`, `E_FLIGHT_UNAVAILABLE`, `E_SEATS_UNAVAILABLE`, `E_INSUFFICIENT_BALANCE`, `E_IDEMPOTENCY_CONFLICT`, `E_QUOTE_EXPIRED`, `E_VERSION_CONFLICT` |
| `PRINT_TICKET` | U | `bookingCode` | `{filename, mimeType:"text/plain", lines:[string]}` | `E_NOT_FOUND`, `E_STATE_CONFLICT` (not TICKETED) |

`feeReason`: `STANDARD`, `INVOLUNTARY_CHANGE`, `PENDING_HOLD`; all successful cancellations have `fee:0`. Paid bookings refund 100% of current fare when ≥2 h away or disrupted before departure; other paid bookings <2 h return `E_CANCEL_NOT_ALLOWED`. Live unpaid bookings release holds and refund zero.

Cancellation preview is optional and advisory: it creates no quote, needs no key and has no quote expiry. Cancellation apply needs only the booking code and key, rechecks current eligibility and returns the actual refund. `quoteId` is not a cancellation field. A dry-run cancellation rejects `idempotencyKey`.

For CHANGE_BOOKING, dry runs reject `quoteId`/`idempotencyKey`. Apply must match the owned quote's booking, leg and replacement; mismatch → `E_VALIDATION`, unowned quote → `E_NOT_FOUND`. Change quotes expire after 60 seconds; hold no seats; consume only on committed apply. Changed revision, flight version or amount → `E_VERSION_CONFLICT`; obtain another quote and user confirmation. Exact successful-key replay precedes expiry/stale-state checks. Unpaid GET returns `paidAt:null`, `tickets:[]`, `delivery:{}`. Terminal bookings retain ticket history but cannot print/resend active tickets.

### 4.5 Notifications

| Type | Roles | Request `data` | Success `data` | Specific errors |
|---|---|---|---|---|
| `GET_NOTIFICATIONS` | U | optional `unreadOnly` (default false), `limit,offset` | `{notifications:[Notification + read],nextOffset}` | — |
| `ACK_NOTIFICATION` | U | `notificationIds:[string]` | `{acknowledged}` | `E_NOT_FOUND` (id not owned) |
| `ADMIN_LIST_FLIGHTS` | M | optional `date,flightNo,status,limit,offset` | `{flights:[{flightId,version,flightNo,origin,destination,departAt,arriveAt,status,seatsLeft}],nextOffset}`; seatsLeft means ECONOMY availability in v1 | — |
| `ADMIN_UPDATE_FLIGHT` | M | `flightId,action,reason,expectedVersion,idempotencyKey`; action DELAY requires `delayMinutes` (1–1440); RESCHEDULE requires `newDepartAt,newArriveAt`; CANCEL requires none of these action fields | `{flight:{flightId,version,flightNo,status,departAt,arriveAt,delayMinutes?},affectedBookings,notificationsCreated,pushedOnline}` | `E_NOT_FOUND`, `E_STATE_CONFLICT`, `E_VERSION_CONFLICT`, `E_IDEMPOTENCY_CONFLICT` |

### 4.6 Server push

| Type | Direction | `data` |
|---|---|---|
| `NOTIFY` | S→C, `id:null`, no `ok` | `{notificationId,kind: DELAY / SCHEDULE_CHANGE / FLIGHT_CANCELLED,bookingCode,flightId,flightVersion,flightNo,oldDepartAt,newDepartAt?,newArriveAt?,delayMinutes?,freeCancellation,refundAmount? (cancelled only),message,createdAt}` |

Clients do not reply to `NOTIFY`; they confirm reading with `ACK_NOTIFICATION`. Pushes are best-effort live; the stored notification is the source of truth.

Notification lists contain the **same full** object as push, plus `read:boolean`. DELAY/SCHEDULE_CHANGE require new departure/arrival; DELAY also requires delayMinutes. FLIGHT_CANCELLED requires refundAmount and omits new times/delayMinutes. Deduplicate by notificationId; refresh current booking instead of applying old events over newer versions.

Admin action-specific fields not belonging to that action are rejected. One notification is persisted per affected ticketed booking. `affectedBookings` counts newly changed pending plus ticketed bookings; `notificationsCreated` counts saved ticketed-booking notifications. `pushedOnline` counts customer connections queued for best-effort push, not successful writes or recipients. These counts are saved operation snapshots; admin-key replay does not push again. Pull recovers missed notifications.

### 4.7 Field types, bounds and collections

| Fields | Type / constraints |
|---|---|
| Resource IDs, `quoteId` | Nonempty ASCII strings, max 64 chars; opaque except bookingCode |
| `idempotencyKey` | 1–64 ASCII `[A-Za-z0-9_-]`; persists through reconnect |
| `bookingCode`, `eTicketCode` | String matching `[A-Z0-9]{6}` |
| `revision`, `bookingRevision`, `version`, `flightVersion`, `expectedVersion` | Integers ≥1; booleans rejected |
| `username`, `password` | BR-01; username 3–20 normalized ASCII characters, password 6–64 Unicode characters |
| `fullName`, `passengerName`, `idNumber` | Nonempty strings; original name ≤120 characters, uppercase printable name ≤240; identity number ≤32 ASCII alphanumerics; no raw controls |
| `email`, `contactEmail`, delivery `to` | Email ≤254 chars with one @ and dotted domain; delivery `to` is masked in responses |
| Airport, airline code, flightNo | Known 3-letter uppercase airport; airline code 2–3 uppercase alphanumerics; flightNo 2–10 uppercase alphanumerics |
| Dates, DOB | Real `YYYY-MM-DD` calendar dates; business age/order checks in BR-10/21 |
| Timestamps | `YYYY-MM-DDTHH:MM:SS[.sss]+07:00`; real instants; arrival later than departure |
| Money fields | Integers VND 0..9,000,000,000,000; fareDifference/netAmount/balanceIfApplied may be signed within that magnitude; no floating money |
| `passengers` | Search/compare: integer 1–9; BOOK/GET: 1–9 Passenger objects; list: integer count |
| ID arrays | Distinct flightIds 2–5; notificationIds 1–50 |
| Flags | `dryRun,unreadOnly,read,freeCancellation,disrupted`: booleans; optional request flags default false |
| `delayMinutes`, `durationMin`, `seatsLeft` | Integers: request delay 1–1440, duration ≥1, seats ≥0 |
| `reason`, error/notification `message` | Nonempty strings ≤500 characters; clients match codes |
| `limit`, `offset`, `nextOffset` | limit 1–20 default 20; offset 0–10000 default 0; nextOffset integer or null at end |
| Enums | Exact values for role, class, status, method, action, legType, feeReason and sortBy from tables; resend response channel is always EMAIL; no other values/null |

Sort bookings by `(createdAt DESC,bookingCode ASC)`, notifications by `(createdAt DESC,notificationId ASC)`, admin flights by `(departAt ASC,flightId ASC)`. nextOffset is offset+returnedCount only if more rows exist. Concurrent changes may shift pages; deduplicate IDs and restart at 0 after mutations. Search sorts requested value ascending then flightId and returns all matching fixture flights (proposed fixture limit 10 flights per route/date). Empty arrays are success. Printable output: ≤200 lines, ≤240 characters each; encoder must still enforce the total byte bound. Other strings such as airline names, route and filenames have maximum 120 characters; ticketNo is 1–32 ASCII printable characters. Serialize/check the mutation's saved response against the byte bound **before commit**; unexpected oversize rolls back and yields logged `E_INTERNAL`, never partial JSON. A post-commit send fault closes/reconciles rather than reporting rollback. All scalar values are required unless the message table marks them optional or explicitly allows null.

## 5. Versioning

`v` is bumped only for incompatible changes. New optional response fields may be added in v1; clients ignore unknown **response** fields (servers reject unknown **request** fields).
