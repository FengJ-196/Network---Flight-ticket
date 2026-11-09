# Business flow — Flight search & booking (socket application)

Status: **draft for review**, revised 2026-11-05. Protocol: custom TCP application protocol "FBP" (see `message-spec.md`). Sources and proposed policy choices: [README](README.md). Initial discussions in `Docs` are historical where this package explicitly differs.

## 1. Scope and actors

| Actor | Description | How created |
|---|---|---|
| USER | Customer: searches, compares, books, pays, manages tickets, receives notifications | `REGISTER` (role is always USER) |
| ADMIN | Airline operator: changes flight status/time, which triggers notifications | Pre-seeded on the server (e.g. `admin`); cannot be self-registered |
| Server | Single process, owns all data and enforces every rule | — |
| Email provider | Real email service used by the server to send e-ticket codes to the booking contact email | Sender/service credentials configured on server |

Proposed scope excludes real payment gateways/card data, seat maps, baggage, infants/children pricing and multi-city trips. **R7 is confirmed by the user: send real email only; SMS is excluded.** The server queues actual e-ticket emails after payment/change and supports email resend. A local file does not satisfy this requirement.

## 2. Glossary

- **Flight**: one scheduled airline flight (`flightId`, e.g. `F1003`), with status and per-class price and seat count.
- **Booking**: a purchase for 1–9 passengers on 1 or 2 legs (OUTBOUND, optional RETURN), identified by a 6-char **booking code** (= PNR = e-ticket code).
- **Ticket**: one per passenger (`ticketNo`) covering the booking's current legs, issued when payment succeeds. This is a simplified course model, rather than one airline coupon per passenger/leg.
- **Hold**: seats reserved for 10 minutes while a booking is `PENDING_PAYMENT`.
- **Disrupted booking**: a TICKETED booking with an unaccepted flight shift of at least 120 minutes in either direction from a leg's accepted departure. Cancellation has its own terminal status and automatic refund.
- **Balance**: user's account money in VND (integer). The only payment instrument actually debited.

## 3. Field authority and formats

| Field | Authority | Format |
|---|---|---|
| Prices, seat counts, flight status/times | Server (flight table) | Money integer VND; times ISO-8601 with offset (`+07:00`) |
| Airport | Server | 3-letter IATA uppercase (`HAN`, `SGN`, `DAD`) |
| Dates in search | Client | `YYYY-MM-DD`, interpreted in `+07:00` |
| Total, fees, refunds | **Server only** — client never sends amounts | integer VND |
| Booking/ticket codes, timestamps | Server | PNR: 6 chars `[A-Z0-9]`; generated uniquely, never an authorization credential |
| Seat class | Client chooses | `ECONOMY`, `PREMIUM_ECONOMY`, `BUSINESS` |

## 4. Seed data (for demo/tests)

Users: `admin` / `admin123` (ADMIN, `U-0001`). New users start with **5,000,000 VND** (assumption A3).

| flightId | Flight | Route | Departs → Arrives (2026) | ECONOMY/pax | Eco seats |
|---|---|---|---|---|---|
| F1001 | VN213 Vietnam Airlines | HAN→SGN | 12-20 06:00 → 08:10 | 1,850,000 | 40 |
| F1002 | VJ131 VietJet Air | HAN→SGN | 12-20 07:30 → 09:40 | 1,290,000 | 35 |
| F1003 | QH201 Bamboo Airways | HAN→SGN | 12-20 09:15 → 11:20 | 1,590,000 | 28 |
| F1004 | VN215 Vietnam Airlines | HAN→SGN | 12-20 14:00 → 16:10 | 1,750,000 | 22 |
| F2001 | VN220 Vietnam Airlines | SGN→HAN | 12-27 18:00 → 20:10 | 1,950,000 | 30 |
| F2002 | VJ136 VietJet Air | SGN→HAN | 12-27 19:30 → 21:35 | 1,350,000 | 18 |

Additional proposed class fixtures (independent inventory): F1001 PREMIUM_ECONOMY 2,200,000 VND / 8 seats and BUSINESS 2,800,000 / 4; F2001 PREMIUM_ECONOMY 2,300,000 / 8 and BUSINESS 2,900,000 / 4. Other listed flights have ECONOMY only. This supports class-filter tests without changing the economy transcript. Initialize flight and booking revisions at 1; fare prices are fixed seed values in v1 (admin only edits times/status).

## 5. Business rules

**Accounts**
- BR-01 Username 3–20 ASCII chars `[a-z0-9_]`, normalize ASCII case before lookup and uniqueness checks. Password 6–64 Unicode characters, stored salted-hashed, never logged in clear; do not trim passwords. These are proposed demo policies.
- BR-02 Registration requires email. Booking requires `contactEmail`, defaulted by the client from the account email and explicitly confirmed by the customer. It is the saved e-ticket recipient; no phone/contactPhone field is collected in this protocol.
- BR-03 `REGISTER` does not log the user in. A connection authenticates once; a second `LOGIN` on it → `E_ALREADY_LOGGED_IN`. One user may hold several connections.
- BR-04 Bad username and bad password return the same error (no account enumeration).
- BR-05 Role is checked on the server for every request; admin messages from a USER → `E_FORBIDDEN`.

**Search / compare**
- BR-10 `origin ≠ destination`; `departDate ≥ today`; `returnDate ≥ departDate` if present; passengers 1–9.
- BR-11 Results exclude CANCELLED and already-departed flights and flights with fewer free seats than `passengers` in the chosen class. No results is a **success** with empty arrays.
- BR-12 Each offer shows airline, flight no., times, duration, price per passenger and total for the request, seats left. Default sort: price ascending; `sortBy` ∈ `PRICE|DEPARTURE|DURATION`.
- BR-13 Compare takes 2–5 distinct flights on the **same route and local departure date**, same passenger count/class; all must be currently eligible under BR-11. An unavailable flight returns `E_FLIGHT_UNAVAILABLE`; insufficient seats returns `E_SEATS_UNAVAILABLE`. Return rows in request order, cheapest/fastest markers and deltas; ties use ascending `flightId`.

**Booking and payment**
- BR-20 `BOOK_FLIGHT` creates a `PENDING_PAYMENT` booking and **holds** seats for 10 minutes. Both legs reserve atomically; a return reverses the route and departs after outbound arrival. Price is fixed at hold time and explicitly confirmed before payment. Expire stale holds before checking free seats, even if the sweeper has not run.
- BR-21 Passengers: `fullName`, `dob`, `idNumber` each; unique identity numbers within a booking, age at least 18 at outbound departure. Preserve original names; printable names use Unicode uppercase (do not silently remove Vietnamese letters).
- BR-22 `PAY_BOOKING` debits the balance atomically with ticket issue. Payment method is a label (`CREDIT_CARD` | `E_WALLET`); no card data is collected or stored.
- BR-23 Insufficient balance → no deduction; hold remains valid until original expiry. No top-up message exists; choose an affordable itinerary or use another seeded fixture.
- BR-24 Expired hold → booking `EXPIRED`, seats released, `PAY` → `E_HOLD_EXPIRED`.
- BR-25 Applied BOOK, PAY, CANCEL, CHANGE and ADMIN_UPDATE operations require a stable `idempotencyKey`. Uniqueness scope is `(userId, type, key)`. Store normalized payload fingerprint and success data durably in the same transaction as the mutation; replay with the new request ID before current state/quote-expiry checks. Same key/different payload → `E_IDEMPOTENCY_CONFLICT`. Rejections and dry runs are not cached. Keys/results are retained for the lifetime of the demo data, including across restarts. Never issue a fresh key solely because of a timeout.
- BR-26 Payment atomically issues ticket numbers/code and one durable email job addressed to saved `contactEmail`. After commit a worker sends a real e-ticket email through the configured provider. Jobs are QUEUED, SENT when the provider accepts the email, or FAILED on an unsuccessful/uncertain attempt. SENT alone does not prove mailbox receipt or reading; R7 acceptance requires inspecting a real recipient inbox. `RESEND_TICKET` takes only bookingCode and sends existing codes to that saved email, with no new charge/ticket. Retain job/attempt IDs across restart; provider timeouts or a crash after acceptance can cause duplicate emails on retry, never duplicate payment/tickets. Payment success is independent of email failure.

**Manage tickets**
- BR-30 Users see only their own bookings; others' codes look like `E_NOT_FOUND`.
- BR-31 **Cancellation/refund policy confirmed by the user (2026-11-05):** allowed cancellations have no cancellation fee and refund 100% of the current fare. Use time until the earliest current departure:

| Time to departure | Fee | Result |
|---|---|---|
| TICKETED, ≥ 2 h | 0% | full fare refunded (100%) |
| TICKETED, < 2 h, not disrupted | — | `E_CANCEL_NOT_ALLOWED` |
| Disrupted TICKETED booking, before departure | 0% | full fare refunded, including within 2 h |
| Live `PENDING_PAYMENT` | 0% | hold released, nothing refunded |

Exactly 2 h is allowed. The existing no-cancellation-after-departure guard still applies. A live unpaid hold uses the unpaid rule. Prior change fees remain separate from the fare; this revision changes cancellation deductions, not the change-price calculation in BR-32.

- BR-32 Change (re-book one leg): same route and seat class; new flight must be bookable (BR-11 rules), **all current booking legs** and the replacement must depart ≥ 2 h away, and round-trip time order remains valid. No change after any leg has departed, even when disrupted. Change fee 200,000 VND per passenger (0 if disrupted). `fareDifference = newFare − oldLegFare`; net = fee + difference. Positive net requires balance; negative net is credited. Keep booking/ticket identifiers, increment booking revision and invalidate cached printable data; the ticket always represents current legs. Accepting a replacement resets that leg's accepted departure baseline. Queue revised e-ticket delivery.
- BR-33 Cancellation applies directly with `bookingCode` and `idempotencyKey`; no cancellation quote or expiry is needed. Optional `dryRun=true` returns a read-only refund preview, without storing a quote or reserving an amount. Apply checks current state and BR-31 again, then refunds once. For **CHANGE_BOOKING only**, a dry run creates a 60-second quote binding owner, replacement, amounts, booking revision and flight versions. Change apply requires `quoteId` and `idempotencyKey`; expiry → `E_QUOTE_EXPIRED`, changed snapshot → `E_VERSION_CONFLICT`. Exact successful-key replay takes precedence over current-state checks.
- BR-34 Print returns a plain-text ticket (`lines[]`) for TICKETED bookings; the client prints or saves it. Server does not print.

**Notifications (admin → users)**
- BR-40 ADMIN may DELAY (minutes), RESCHEDULE (new times), or CANCEL a flight that is not departed/cancelled.
- BR-41 DELAY/RESCHEDULE updates flight times and increments flight version. DELAY adds minutes to current times; RESCHEDULE sets absolute future times. TICKETED legs update, booking revision increments, and notification persists; absolute net shift ≥ 120 min from the accepted departure baseline grants disruption waiver. Corrections use net shift, not the sum of absolute changes. Invalidate **whole** PENDING_PAYMENT bookings on the flight to CANCELLED with reason FLIGHT_UPDATED and release all legs; a customer must accept a new hold for the changed itinerary.
- BR-42 CANCEL sets flight `CANCELLED`; each TICKETED booking on it becomes `FLIGHT_CANCELLED` and the **full amount paid (incl. change fees)** is refunded to balance automatically (assumption A6: a round trip is cancelled as a whole).
- BR-43 PENDING_PAYMENT bookings on a cancelled flight become CANCELLED with reason FLIGHT_CANCELLED, and every leg's hold is released. TICKETED cancellations release every leg's sold seats, void the booking's ticket validity and refund the outstanding net amount paid (current fare plus cumulative change fees), exactly once. Never undo refunds already paid on terminal bookings.
- BR-44 Notifications are stored (never lost). Online users get a live `NOTIFY` push; others get them via `LOGIN.unreadNotifications` + `GET_NOTIFICATIONS`. `ACK_NOTIFICATION` marks read.

**Observability**
- BR-50 Log every received/sent/rejected frame by metadata and recursively redacted structured content. Remove passwords, contacts, full names, DOB and identity numbers. Invalid JSON/UTF-8 logs only byte count and reason, never raw bytes. Separate SEND_ATTEMPT, SEND_SUCCESS and SEND_FAILURE; none proves recipient reading. Log connect/disconnect/timeouts and admin audit changes.

## 6. State models (summary; diagrams in `state-machines.md`)

- Booking: `PENDING_PAYMENT → TICKETED | EXPIRED | CANCELLED`; `TICKETED → CANCELLED | FLIGHT_CANCELLED`; change keeps `TICKETED`.
- Flight: `SCHEDULED → DELAYED | RESCHEDULED → (more updates) → CANCELLED | DEPARTED`.

## 7. Business transactions vs. messages

| Business transaction | Messages | Atomic unit on server |
|---|---|---|
| Book & pay | `BOOK_FLIGHT` then `PAY_BOOKING` | each message atomic; hold links them |
| Change ticket | `CHANGE_BOOKING(dryRun)` → apply with quote/key | seat swap + ledger + revision + delivery jobs + replay result in one SQL transaction |
| Cancel | `CANCEL_BOOKING` with bookingCode/key; optional preview | status + all-leg seat release + full fare refund (zero if unpaid) + replay result in one SQL transaction |
| Flight disruption | `ADMIN_UPDATE_FLIGHT` (+ pushes) | flight + all affected bookings/legs + notifications + refunds + replay result in one SQL transaction; pushes after commit |

## 8. Permission matrix

| Message | Anon | USER | ADMIN |
|---|---|---|---|
| PING | ✔ | ✔ | ✔ |
| REGISTER, LOGIN | ✔ | ✘ (`E_ALREADY_LOGGED_IN`) | ✘ |
| LOGOUT | ✘ | ✔ | ✔ |
| GET_BALANCE, SEARCH_FLIGHTS, COMPARE_FLIGHTS, BOOK/PAY, RESEND/LIST/GET/CANCEL/CHANGE/PRINT, GET_NOTIFICATIONS, ACK_NOTIFICATION | ✘ | ✔ (own data) | ✘ |
| ADMIN_LIST_FLIGHTS, ADMIN_UPDATE_FLIGHT | ✘ | ✘ | ✔ |

## 9. Alternate and failure paths

- Payment short of funds → `E_INSUFFICIENT_BALANCE`, booking stays pending until hold expires.
- Seats taken between search and booking → `E_SEATS_UNAVAILABLE` (client re-searches).
- Client crashes after `PAY` sent → reconnect, `LOGIN`, `GET_BOOKING`/retry `PAY` with the same key.
- User offline during disruption → notification stored, retrieved after login.
- Malformed/oversized frame → error reply (and close for oversize); server never crashes on bad input.

## 10. Monetary and time invariants

`totalAmount` is current sum of leg fares, each already multiplied by passenger count. `totalPaid` is net historical debits minus credits for this booking: after a paid change it equals current fare plus cumulative change fees. An allowed customer cancellation refunds the full current fare with `fee=0`; historical change fees are retained. An unpaid cancellation refunds zero. Admin cancellation refunds the entire outstanding `totalPaid`. Every debit/credit has an immutable ledger entry and cancellation/refund uniqueness prevents repetition.

Cancellation of a paid booking is forbidden at or after its earliest current departure, including disrupted bookings. Before departure, disruption waives the two-hour cancellation cutoff. The two-hour change cutoff still applies. PENDING_PAYMENT cancellation refunds zero and first checks hold expiration. `now >= holdExpiresAt` and `now >= quoteExpiresAt` mean expired; the latter applies only to change quotes. Capture server time inside the transaction.

For each fare: `capacity >= heldSeats + soldSeats >= 0`; free seats exclude only live holds and sold seats. Payment converts held to sold without changing free seats. Every failed change preserves original legs, seats, balance and valid tickets. Schedule updates never revive a terminal booking. Booking and flight revisions start at 1 and increment on each corresponding mutation; read calls and quote creation do not increment them.
