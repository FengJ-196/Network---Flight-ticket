# Error and reply-code catalog

Every failure reply has `ok:false`, a stable `code`, an English `message` (not for matching), and object `data` with safe context. Known rejections do not apply the requested mutation. Exceptions: stale holds may expire/release seats while handling a request, and `E_HOLD_EXPIRED` reports that transition. No partial debit/refund is permitted. The connection remains usable except oversize, incomplete-frame/idle timeout, EOF or socket failure.

"Retry" = may the client resend the *same* request unchanged and expect a different outcome.

| Code | Category | Trigger | `data` context | Client recovery | Retry |
|---|---|---|---|---|---|
| `E_BAD_JSON` | protocol | Invalid UTF-8/JSON, duplicate keys, nonfinite numbers, non-object/blank/BOM-prefixed payload or outer whitespace | `{}` | Fix encoder; `ERROR_RESP` with `id:null`; remain connected | no |
| `E_UNSUPPORTED_VERSION` | protocol | `v` ≠ 1 | `{supported:[1]}` | Upgrade/downgrade client | no |
| `E_UNKNOWN_TYPE` | protocol | `type` not in catalog | `{type}` | Fix client | no |
| `E_FRAME_TOO_LARGE` | protocol | JSON payload > 65,536 bytes, excluding LF/optional CR | `{maxBytes}` | `ERROR_RESP id:null` if possible; server closes | no |
| `E_VALIDATION` | validation | Missing/extra/ill-typed/out-of-range field | `{field, reason}` | Correct input and resend | no |
| `E_NOT_AUTHENTICATED` | auth | Non-anonymous message before `LOGIN` | — | `LOGIN`, then resend | after login |
| `E_FORBIDDEN` | auth | Role not allowed for the message | `{requiredRole}` | Show "not permitted" | no |
| `E_INTERNAL` | server | Unexpected fault before commit; transaction rolled back | `{}` (internals only in logs) | Retry later with same mutation key | yes |
| `E_USERNAME_TAKEN` | conflict | `REGISTER` with existing username | `{field:"username"}` | Choose another | no |
| `E_BAD_CREDENTIALS` | auth | Unknown user or wrong password (indistinguishable) | — | Re-enter | yes, with new input |
| `E_ALREADY_LOGGED_IN` | state | `LOGIN`/`REGISTER` on an authenticated connection | — | `LOGOUT` first | no |
| `E_NOT_FOUND` | lookup | Flight/booking/notification missing **or not owned by caller** | `{kind, id}` | Refresh list | no |
| `E_SEATS_UNAVAILABLE` | business | Fewer free seats than requested at hold/change time | `{flightId, requested, seatsLeft}` | Re-search, pick another flight | no |
| `E_FLIGHT_UNAVAILABLE` | business | Flight cancelled or departed (also at `PAY`) | `{flightId, status}` | Re-search | no |
| `E_HOLD_EXPIRED` | business | `PAY` after hold expired; booking now `EXPIRED` | `{bookingCode}` | New `BOOK_FLIGHT` | no |
| `E_INSUFFICIENT_BALANCE` | business | Balance < amount due (`PAY`, or net of `CHANGE`) | `{required, available}` | Choose affordable itinerary or seeded fixture; no top-up message exists | after balance change |
| `E_STATE_CONFLICT` | state | Operation invalid for current state (pay twice, cancel a cancelled booking, print unpaid, update cancelled flight) | `{currentStatus}` | `GET_BOOKING` to resync | no |
| `E_CANCEL_NOT_ALLOWED` | business | Paid booking <2 h to first departure unless disrupted; any paid booking already departed | `{hoursToDeparture}` | Keep/view booking; eligible cancellations refund the full fare | no |
| `E_CHANGE_NOT_ALLOWED` | business | Different route/class, < 2 h to old or new departure, or same flight | `{reason}` (`ROUTE_MISMATCH`, `TOO_LATE`, `SAME_FLIGHT`, `CLASS_MISMATCH`) | Pick eligible flight | no |
| `E_IDEMPOTENCY_CONFLICT` | conflict | `idempotencyKey` reused with different payload | `{idempotencyKey}` | Generate a new key | no |
| `E_QUOTE_EXPIRED` | business | Owned change quote has reached its expiry | `{quoteId}` | Obtain and review a new quote | no |
| `E_VERSION_CONFLICT` | conflict | Admin expected flight version differs; quote's booking/flight/policy/amount snapshot changed or was consumed by another key | `{kind,expected?,actual?}` | Refresh/requote and obtain user confirmation | no |

## Disclosure rules

- Never include stack traces, SQL, file paths or other users' data in `message`/`data`.
- Email provider failure is reported as delivery.email.status FAILED after payment success; keep provider credentials and raw provider errors out of responses/logs. Use safe job diagnostics for recovery.
- Login failures reveal nothing about which half was wrong.
- Recursively redact passwords, names, DOB, identity numbers and contacts in logs, including printable lines; do not log raw malformed input. Passwords never appear in replies.
- `E_NOT_FOUND` is used for other users' booking codes to avoid leaking existence.

## Evaluation order (so tests are deterministic)

1. Frame size → strict UTF-8/JSON object → envelope shape/version → known request type/direction → unused connection request ID. Envelope failures use `ERROR_RESP` as specified in message-spec §2.
2. Authentication → role. LOGIN/REGISTER on an authenticated connection return `E_ALREADY_LOGGED_IN` before payload business validation.
3. Payload shape/type/range and action-dependent fields; first failing field in catalog required-then-optional order. Conditional apply fields follow the declared conditional order.
4. Under `domainLock` and a SQL transaction, resolve `(user,type,key)` replay/conflict **before** checking current booking/quote/flight state. Identity scope prevents another user replaying an owner's result. Replay uses the new request ID and saved success data, and never repeats delivery/refund/delay.
5. Lookup/ownership of all referenced resources (`E_NOT_FOUND`). For CHANGE_BOOKING applies: quote expiry → consumed/snapshot checks → booking state/policy/flight eligibility/inventory → balance → commit. Thus an expired quote yields `E_QUOTE_EXPIRED`; a changed/consumed quote with a different operation key yields `E_VERSION_CONFLICT` even if the booking is now terminal. Matching quote parameters are validated before expiry; a mismatch is `E_VALIDATION`.
6. For PAY: EXPIRED → `E_HOLD_EXPIRED`; an admin-invalidated hold reason FLIGHT_UPDATED/FLIGHT_CANCELLED → `E_FLIGHT_UNAVAILABLE`; other invalid states → `E_STATE_CONFLICT`. Otherwise state → policy/flight eligibility → balance → commit. CANCEL checks live state then BR-31 and refunds the full fare (or zero for unpaid) without a quote; terminal bookings return `E_STATE_CONFLICT`. Admin update checks active/future state, then expectedVersion, then applies atomically. A due hold is expired/released under the same transaction before responding.

No response is guaranteed on EOF or a frame deadline. A failure after a successful commit must never be reported as a rolled-back `E_INTERNAL`; recover the saved success data or close so the client reconciles the uncertain operation. After a replay, fetch current state because its saved balance/status may now be historical. `E_IDEMPOTENCY_CONFLICT` recovery requires inspecting the original operation before deciding to create a distinct one; a fresh key must not be used to conceal a timeout.
