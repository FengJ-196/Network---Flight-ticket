# Presenter guide: Flight Ticket Booking

Main presentation: slides **1–20**, then the final thank-you slide **30**, about **25:15**. The Questions link on slide 20 jumps directly to slide 30. Appendix pages **21–29** are optional.

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

Use the fixed mocked fixtures. The table shows an illustrative subset, not the full search response. For one passenger F1003 costs 300,000 more than F1002 and saves five minutes. Prices multiply by passenger count. A later booking must check seats again because search does not reserve inventory.

### Slide 7: TCP framing and transport rules

Suggested time: 1:30. Sources: message-spec.md sections 1-2

TCP supplies an ordered byte stream, not message boundaries. The displayed backslash-n illustrates the final LF byte. CRLF is tolerated. Decode strict UTF-8 after receiving a complete bounded line. An oversized frame closes that connection. Client PING every 60 seconds keeps an idle connection active.

### Slide 8: Request, response and push envelopes

Suggested time: 1:30. Sources: message-spec.md envelope

These are complete illustrative PING and login-failure frames. Error text is for people, while code drives client behavior. Responses echo the request ID and append _RESP to the request type. Unknown request fields are rejected. Clients ignore unknown response fields for compatible additions. A full push example is in the appendix.

### Slide 9: Protocol operation inventory

Suggested time: 1:00. Sources: message-catalog.json; message-spec.md

Do not read every name aloud. Explain the grouped inventory and then focus on state, purchase and admin-notification flows. Each message has documented role, payload, success result and errors in the source specification. PING is allowed before login. Other business operations require the appropriate bound role.

### Slide 10: Session and client request states

Suggested time: 1:30. Sources: state-machines.md sections 1,2,7

This diagram highlights successful login and close paths. Any connected state also closes on framing faults or idle timeout. A second login on an authenticated socket returns E_ALREADY_LOGGED_IN. A USER issuing an admin operation receives E_FORBIDDEN. A known error response completes the pending request without changing authentication state.

### Slide 11: Booking state machine

Suggested time: 1:30. Sources: state-machines.md booking lifecycle

A booking begins at BOOK_FLIGHT with held seats. PAY converts held seats to sold seats. Expiry or unpaid cancellation releases all holds. A paid customer cancellation follows the confirmed simple refund rules. Admin flight cancellation refunds the outstanding net amount paid once. Booking revisions make old print data detectable.

### Slide 12: Booking and payment message sequence

Suggested time: 2:00. Sources: use-case-flows.md UC05-06; processing-tables.md

Use the illustrative one-passenger F1003 purchase: starting balance 5,000,000 VND, fare 1,590,000 and remaining balance 3,410,000. The server computes amounts. Credit card and e-wallet are method labels, while the selected implementation debits balance. Both booking legs succeed together. Payment stores its success result and queued email job in the same transaction.

### Slide 13: Real e-ticket email delivery

Suggested time: 1:15. Sources: business-flow.md BR26; processing-tables.md delivery

Distinguish provider acceptance from receipt or reading. SENT does not prove a mailbox received the email. PAY always returns its persisted QUEUED snapshot, including a retry. GET_BOOKING shows the latest email status. No provider has been selected or email sent by this design review.

### Slide 14: Cancellation and simple refund rules

Suggested time: 1:00. Sources: business-flow.md BR31,33; user refund clarification

This is the user's confirmed simplified policy. Exactly two hours is allowed. Existing disruption means a net departure shift of at least 120 minutes from the accepted baseline. Previously charged change fees remain separate from the current fare. Avoid expanding the talk into complex refund tiers or calculations.

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

### Slide 20: Validation and implementation acceptance

Suggested time: 1:15. Sources: README.md validation; acceptance-scenarios.md; lecture pp21-24

Do not claim the structural validator runs the application. No client/server implementation or two-PC demo was found in the reviewed package. Our current deliverable is the protocol design. The later final report must evaluate the actual application. Confirm remaining proposed hold/change rules with the professor. Click Questions to jump to the final thank-you slide, skipping the optional appendix.

### Slide 21: Appendix: account, search and comparison processing

Optional reference. Sources: message-spec.md; processing-tables.md

Backup for UC01 to UC04 and balance. All operations enforce session roles. Unknown fields and incompatible input types return E_VALIDATION. Search/compare neither reserve seats nor move money.

### Slide 22: Appendix: purchase and email processing

Optional reference. Sources: message-spec.md; processing-tables.md

Backup for UC05 to UC07. A return trip must reverse the route and depart after outbound arrival. The contract uses one ticket number per passenger for all current booking legs. This is a proposed course simplification.

### Slide 23: Appendix: ticket-management processing

Optional reference. Sources: use-case-flows.md UC08-11; message-spec.md

Backup for UC08 to UC11. Cancellation preview is advisory. Change quotes expire at 60 seconds and do not hold replacement seats. Apply never silently substitutes a new change amount.

### Slide 24: Appendix: admin and notification processing

Optional reference. Sources: use-case-flows.md UC12-14; message-spec.md

Backup for UC12 to UC14. A push count describes selected connections, not acknowledged delivery or reading. If the server crashes after commit but before push, customers recover the saved notification through GET_NOTIFICATIONS. Admin-key replay must not apply another delay or another refund.

### Slide 25: Appendix: complete cancellation exchange

Optional reference. Sources: wire-examples.jsonl #52-53; message-spec.md

This complete exchange comes from the current wire transcript. Balance had been 3,050,000 after a flight change, so the 1,750,000 current-fare refund gives 4,800,000. The prior 200,000 change fee remains separate. No cancellation deduction is applied.

### Slide 26: Appendix: full server push example

Optional reference. Sources: wire-examples.jsonl NOTIFY; message-spec.md

This is a complete synthetic illustration of the specified push schema. The notification ID is illustrative. Arrival remains later than departure. The original F1004 arrival was 16:10 and a 150-minute delay gives 18:40. Server push can arrive between a request and its reply.

### Slide 27: Appendix: field bounds and important errors

Optional reference. Sources: message-spec.md bounds; error-catalog.md

Quote expiry applies only to changes. Version conflict also protects admin flight updates. The full error catalog defines safe context and recovery for 22 codes. The JSON catalog is a structural inventory, not a complete JSON Schema. Adult-only and list limits are proposed demo choices.

### Slide 28: Appendix: flight states and admin effects

Optional reference. Sources: state-machines.md flight lifecycle

Disruption is a property of the ticketed booking's accepted itinerary. Corrections use net time movement, not accumulated absolute changes. A successful customer replacement resets the accepted baseline for that leg. Admin cancellation has a separate full-outstanding-payment refund rule, including prior change fees.

### Slide 29: Appendix: source documents and review coverage

Optional reference. Sources: original assignment and current package

The current confirmed user decisions override conflicting initial drafts: real email only and simple full-fare cancellation. The initial Docs drafts remain historical references. All slide claims about application behavior describe the design, not an implemented service.

### Slide 30: Thank you and questions

Suggested time: 0:15. Final slide after all appendix material

Invite questions. This is the final page of the deck. Optional appendix slides 21--29 provide operation-level processing, full example messages, field bounds, flight states and sources. The main presentation reaches this page through the Questions link on slide 20.

## Presentation boundaries

State that the work is a design review. Synthetic transcript checks do not prove runtime TCP, database, email or two-PC behavior. Keep the confirmed full-fare cancellation explanation short. The separate change-flight fee and quote remain proposed.

After slide 20, click Questions to display slide 30. Open appendix slides 21–29 only when a question calls for their detail. The thank-you slide remains the final page in the exported PDF.
