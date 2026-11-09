# Presenter guide: Flight Ticket Booking

Main presentation: slides **1–19**, followed by the final thank-you slide **20**, approximately **24:00**.

The deck uses the supplied HUST template with an English presenter label. The editable LaTeX contains hidden speaker notes. The original sample remains in `../11-05-progress-report/`.

## Slide order and speaking plan

### Slide 1: Flight Ticket Booking

Suggested time: 0:30. Sources: Docs/Requirement.png; Docs/topic.md

Present this as a design review. The talk covers the application, architecture, functionality and especially protocol messages, state machines and processing. The implementation and two-PC demo are later work.

### Slide 2: Application problem and scope

Suggested time: 1:00. Sources: application-design.md; Docs/topic.md

Introduce the two actors. Customers manage their own bookings. Admins change flight times or cancel flights. Balance payment and mocked flights come from the lecturer's notes. Real email comes from the user's R7 clarification. No bank integration is required for the selected scope.

### Slide 3: Required functionality and grading coverage

Suggested time: 1:00. Sources: Docs/topic.md; README.md traceability

Briefly establish complete coverage. The original topic allows email or text messages. Our confirmed implementation uses email only. The point weights are from the assignment and do not represent marks already earned.

### Slide 4: Client--server architecture

Suggested time: 1:30. Sources: application-design.md; processing-tables.md

Explain why this is client-server rather than P2P. Only the server owns authoritative prices, inventory, identity and balances. SQLite is a proposed storage engine, not a course requirement. The client and server must later run on separate PCs. The email worker sends only after the domain transaction commits.

### Slide 5: Customer and admin procedures

Suggested time: 1:00. Sources: application-design.md UC01-14; use-case-flows.md

Map these groups to UC01 through UC14. Server-side authorization is mandatory even if the client hides admin controls. REGISTER does not log in automatically. LOGOUT closes the connection. Individual operation checks are available in the appendix.

### Slide 6: Search and comparison example

Suggested time: 1:00. Sources: business-flow.md fixtures; message-spec.md search/compare

Use the fixed mocked fixtures. The table shows an illustrative subset, not the full search response. For one passenger F1003 costs 300,000 more than F1002 and saves five minutes. Prices multiply by passenger count. Payment checks balance and seats because neither search nor booking holds inventory.

### Slide 7: TCP framing and transport rules

Suggested time: 1:30. Sources: message-spec.md sections 1-2

TCP supplies an ordered byte stream, not message boundaries. The displayed backslash-n illustrates the final LF byte. CRLF is tolerated. Decode strict UTF-8 after receiving a complete bounded line. An oversized frame closes that connection. Client PING every 60 seconds keeps an idle connection active.

### Slide 8: Request, response and push envelopes

Suggested time: 1:30. Sources: message-spec.md envelope

These are complete illustrative PING and login-failure frames. Error text is for people, while code drives client behavior. Responses echo the request ID and append _RESP to the request type. Unknown request fields are rejected. Clients ignore unknown response fields for compatible additions.

### Slide 9: Protocol operation inventory

Suggested time: 1:00. Sources: message-catalog.json; message-spec.md

Explain the grouped inventory: 18 request types. BOOK_AND_PAY combines booking and payment into a single direct operation. Focus on state, purchase, cancellation refund, and admin-notification flows. PING is allowed before login. Other business operations require the appropriate bound role.

### Slide 10: Session and client request states

Suggested time: 1:30. Sources: state-machines.md sections 1,2,7

This diagram highlights successful login and close paths. Any connected state also closes on framing faults or idle timeout. A second login on an authenticated socket returns E_ALREADY_LOGGED_IN. A USER issuing an admin operation receives E_FORBIDDEN. A known error response completes the pending request without changing authentication state.

### Slide 11: Booking state machine

Suggested time: 1:30. Sources: state-machines.md booking lifecycle

The booking lifecycle has no pending payment state. Booking and payment occur in a single step: user clicks book and pay. The server checks ticket status (available seats) and user account balance. If valid, the server deducts the balance, allocates seats, and creates the booking directly in the PAID state. If checks fail, an error is returned without creating a booking. Later, if the customer cancels at least 2 hours before departure (or if the flight is disrupted or cancelled by admin), the server releases the seats and refunds 100% of the fare back to the user's account balance.

### Slide 12: Booking, payment and cancellation sequence

Suggested time: 2:00. Sources: use-case-flows.md UC05-06; processing-tables.md

The simplified booking process has no pending payment step. The customer sends BOOK_AND_PAY: the server checks ticket status and account balance. On success, it deducts balance, allocates seats, creates ticket codes, and queues the email in one atomic transaction. If balance is insufficient or seats are full, it returns an error with zero deduction. Later, if the customer cancels at least 2 hours before departure, CANCEL_BOOKING releases the seats and refunds 100% of the fare directly to the user's account balance.

### Slide 13: Real e-ticket email delivery

Suggested time: 1:15. Sources: business-flow.md BR26; processing-tables.md delivery

Distinguish provider acceptance from receipt or reading. SENT does not prove a mailbox received the email. Book and pay always returns its persisted QUEUED snapshot, including a retry. GET_BOOKING shows the latest email status. No provider has been selected or email sent by this design review.

### Slide 14: Cancellation and simple refund rules

Suggested time: 1:00. Sources: business-flow.md BR31,33; user refund clarification

Since all bookings are paid directly at booking, every cancellation operates on an existing paid ticket. If the customer cancels at least 2 hours before departure, the server releases the seats and refunds 100% of the fare directly to the user's account balance with zero fees. Cancellations within 2 hours are rejected unless the flight is disrupted (delay >= 120 minutes or rescheduled), which waives the cutoff and grants a full 100% refund. Admin flight cancellation triggers an automatic 100% refund to all booked customers. Departed flights cannot be cancelled.

### Slide 15: Viewing, changing and printing tickets

Suggested time: 1:00. Sources: use-case-flows.md UC08,10,11; business-flow.md BR32

Cancellation has no quote. Change retains one because the passenger accepts a replacement and a variable signed amount. Example from the transcript: change F1003 to F1004, fare difference 160,000 plus fee 200,000, total debit 360,000 VND. The change policy remains proposed. Printing occurs on the client and does not modify the booking.

### Slide 16: Admin updates and customer notifications

Suggested time: 1:45. Sources: use-case-flows.md UC12-14; message-spec.md notifications

Admins list flights before updating. DELAY adds minutes, RESCHEDULE supplies absolute times and CANCEL cancels the flight. expectedVersion rejects an update based on stale flight data. Each affected ticketed booking receives a saved notification. Live push is best effort. ACK marks a notification read, while successful socket write does not.

### Slide 17: Message processing on both ends

Suggested time: 1:30. Sources: processing-tables.md; error-catalog.md precedence

Explain both ends, as the lecture requires message processing rather than just an opcode list. A domain mutation either commits all effects or rolls back. The single-lock design is a proposed simple choice for this course dataset. It avoids two customers acquiring the last seat and prevents conflicting payment/admin changes.

### Slide 18: Logging and failure handling

Suggested time: 1:00. Sources: processing-tables.md logging; error-catalog.md

Logging fulfills R2 across success and failure. The actual transmitted payload byte count remains useful even when the object is redacted. Unknown booking codes and another user's booking both return E_NOT_FOUND. No captured application logs exist yet, so do not present a synthetic record as runtime evidence.

### Slide 19: Recovery after a lost reply

Suggested time: 1:15. Sources: state-machines.md recovery; business-flow.md BR25

The key scope is user, operation type and key. The server stores normalized payload and result in the mutation transaction. Same key with another payload yields E_IDEMPOTENCY_CONFLICT. BOOK, PAY, CANCEL, CHANGE and ADMIN_UPDATE use durable keys. Read-only calls can simply repeat. This guarantee does not promise exactly-once email delivery.

### Slide 20: Thank you and questions

Suggested time: 0:15. Final slide

Invite questions. This concludes the presentation.

## Presentation boundaries

State that the work is a design review. Synthetic transcript checks do not prove runtime TCP, database, email or two-PC behavior. Keep the confirmed full-fare cancellation explanation short. The booking flow uses direct balance debit on payment without seat holding. The separate change-flight fee and quote remain proposed.
