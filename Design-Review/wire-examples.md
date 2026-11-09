# Wire examples (generated)

Generated from [wire-examples.jsonl](wire-examples.jsonl) by [validate_examples.py](validate_examples.py); edit the JSONL and regenerate.
JSONL rows contain annotations. Only each code block's payload is transmitted, encoded as UTF-8 and followed by one LF byte (0A); headings/metadata are not sent.
Fixed synthetic clock: 2026-11-04, +07:00. Main purchase occurs 10:20–10:23, delay 10:40, cancellation 10:41; supporting exchanges run 10:45–10:48.
C1 = Alice, C2 = admin, C4 = anonymous, C5 = Bob. Connections start ANON. All credentials and contacts are synthetic. These are proposed exchanges, not captured traffic.
R7 uses real email only. SENT in an example means provider acceptance; these fixtures do not send email or prove inbox receipt.

### 1. C4 C->S — Not logged in

Payload: 151 UTF-8 bytes; then LF.

```json
{"v":1,"type":"SEARCH_FLIGHTS","id":"c-001","data":{"origin":"HAN","destination":"SGN","departDate":"2026-12-20","passengers":1,"seatClass":"ECONOMY"}}
```

### 2. C4 S->C

Payload: 130 UTF-8 bytes; then LF.

```json
{"v":1,"type":"SEARCH_FLIGHTS_RESP","id":"c-001","ok":false,"code":"E_NOT_AUTHENTICATED","message":"Please LOGIN first","data":{}}
```

### 3. C4 C->S — Malformed frame (not JSON)

Payload: 17 UTF-8 bytes; then LF.

```json
{this is not json
```

### 4. C4 S->C — Connection stays open

Payload: 123 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ERROR_RESP","id":null,"ok":false,"code":"E_BAD_JSON","message":"Frame is not a valid JSON object","data":{}}
```

### 5. C1 C->S — US-1 register

Payload: 143 UTF-8 bytes; then LF.

```json
{"v":1,"type":"REGISTER","id":"c-001","data":{"username":"alice","password":"secret123","fullName":"Alice Nguyen","email":"alice@example.com"}}
```

### 6. C1 S->C — Registered; NOT logged in yet

Payload: 160 UTF-8 bytes; then LF.

```json
{"v":1,"type":"REGISTER_RESP","id":"c-001","ok":true,"code":"OK","data":{"userId":"U-1001","username":"alice","role":"USER","balance":5000000,"currency":"VND"}}
```

### 7. C1 C->S — Duplicate username

Payload: 143 UTF-8 bytes; then LF.

```json
{"v":1,"type":"REGISTER","id":"c-002","data":{"username":"alice","password":"secret123","fullName":"Alice Nguyen","email":"alice@example.com"}}
```

### 8. C1 S->C

Payload: 144 UTF-8 bytes; then LF.

```json
{"v":1,"type":"REGISTER_RESP","id":"c-002","ok":false,"code":"E_USERNAME_TAKEN","message":"Username already exists","data":{"field":"username"}}
```

### 9. C1 C->S — Bad password

Payload: 87 UTF-8 bytes; then LF.

```json
{"v":1,"type":"LOGIN","id":"c-003","data":{"username":"alice","password":"wrong-pass"}}
```

### 10. C1 S->C

Payload: 129 UTF-8 bytes; then LF.

```json
{"v":1,"type":"LOGIN_RESP","id":"c-003","ok":false,"code":"E_BAD_CREDENTIALS","message":"Invalid username or password","data":{}}
```

### 11. C1 C->S — Login

Payload: 86 UTF-8 bytes; then LF.

```json
{"v":1,"type":"LOGIN","id":"c-004","data":{"username":"alice","password":"secret123"}}
```

### 12. C1 S->C

Payload: 181 UTF-8 bytes; then LF.

```json
{"v":1,"type":"LOGIN_RESP","id":"c-004","ok":true,"code":"OK","data":{"userId":"U-1001","username":"alice","role":"USER","balance":5000000,"currency":"VND","unreadNotifications":0}}
```

### 13. C1 C->S — Invalid passengers

Payload: 151 UTF-8 bytes; then LF.

```json
{"v":1,"type":"SEARCH_FLIGHTS","id":"c-005","data":{"origin":"HAN","destination":"SGN","departDate":"2026-12-20","passengers":0,"seatClass":"ECONOMY"}}
```

### 14. C1 S->C

Payload: 170 UTF-8 bytes; then LF.

```json
{"v":1,"type":"SEARCH_FLIGHTS_RESP","id":"c-005","ok":false,"code":"E_VALIDATION","message":"passengers must be 1-9","data":{"field":"passengers","reason":"must be 1-9"}}
```

### 15. C1 C->S — Round-trip search

Payload: 194 UTF-8 bytes; then LF.

```json
{"v":1,"type":"SEARCH_FLIGHTS","id":"c-006","data":{"origin":"HAN","destination":"SGN","departDate":"2026-12-20","returnDate":"2026-12-27","passengers":2,"seatClass":"ECONOMY","sortBy":"PRICE"}}
```

### 16. C1 S->C

Payload: 2151 UTF-8 bytes; then LF.

```json
{"v":1,"type":"SEARCH_FLIGHTS_RESP","id":"c-006","ok":true,"code":"OK","data":{"passengers":2,"seatClass":"ECONOMY","currency":"VND","outbound":[{"flightId":"F1002","airline":{"code":"VJ","name":"VietJet Air"},"flightNo":"VJ131","origin":"HAN","destination":"SGN","departAt":"2026-12-20T07:30:00+07:00","arriveAt":"2026-12-20T09:40:00+07:00","durationMin":130,"status":"SCHEDULED","seatClass":"ECONOMY","pricePerPax":1290000,"totalPrice":2580000,"seatsLeft":35,"version":1},{"flightId":"F1003","airline":{"code":"QH","name":"Bamboo Airways"},"flightNo":"QH201","origin":"HAN","destination":"SGN","departAt":"2026-12-20T09:15:00+07:00","arriveAt":"2026-12-20T11:20:00+07:00","durationMin":125,"status":"SCHEDULED","seatClass":"ECONOMY","pricePerPax":1590000,"totalPrice":3180000,"seatsLeft":28,"version":1},{"flightId":"F1004","airline":{"code":"VN","name":"Vietnam Airlines"},"flightNo":"VN215","origin":"HAN","destination":"SGN","departAt":"2026-12-20T14:00:00+07:00","arriveAt":"2026-12-20T16:10:00+07:00","durationMin":130,"status":"SCHEDULED","seatClass":"ECONOMY","pricePerPax":1750000,"totalPrice":3500000,"seatsLeft":22,"version":1},{"flightId":"F1001","airline":{"code":"VN","name":"Vietnam Airlines"},"flightNo":"VN213","origin":"HAN","destination":"SGN","departAt":"2026-12-20T06:00:00+07:00","arriveAt":"2026-12-20T08:10:00+07:00","durationMin":130,"status":"SCHEDULED","seatClass":"ECONOMY","pricePerPax":1850000,"totalPrice":3700000,"seatsLeft":40,"version":1}],"inbound":[{"flightId":"F2002","airline":{"code":"VJ","name":"VietJet Air"},"flightNo":"VJ136","origin":"SGN","destination":"HAN","departAt":"2026-12-27T19:30:00+07:00","arriveAt":"2026-12-27T21:35:00+07:00","durationMin":125,"status":"SCHEDULED","seatClass":"ECONOMY","pricePerPax":1350000,"totalPrice":2700000,"seatsLeft":18,"version":1},{"flightId":"F2001","airline":{"code":"VN","name":"Vietnam Airlines"},"flightNo":"VN220","origin":"SGN","destination":"HAN","departAt":"2026-12-27T18:00:00+07:00","arriveAt":"2026-12-27T20:10:00+07:00","durationMin":130,"status":"SCHEDULED","seatClass":"ECONOMY","pricePerPax":1950000,"totalPrice":3900000,"seatsLeft":30,"version":1}]}}
```

### 17. C1 C->S — Compare 3 airlines, same route

Payload: 129 UTF-8 bytes; then LF.

```json
{"v":1,"type":"COMPARE_FLIGHTS","id":"c-007","data":{"flightIds":["F1001","F1002","F1003"],"seatClass":"ECONOMY","passengers":2}}
```

### 18. C1 S->C

Payload: 1314 UTF-8 bytes; then LF.

```json
{"v":1,"type":"COMPARE_FLIGHTS_RESP","id":"c-007","ok":true,"code":"OK","data":{"rows":[{"flightId":"F1001","airline":{"code":"VN","name":"Vietnam Airlines"},"flightNo":"VN213","origin":"HAN","destination":"SGN","departAt":"2026-12-20T06:00:00+07:00","arriveAt":"2026-12-20T08:10:00+07:00","durationMin":130,"status":"SCHEDULED","seatClass":"ECONOMY","pricePerPax":1850000,"totalPrice":3700000,"seatsLeft":40,"priceDeltaVsCheapest":1120000,"durationDeltaVsFastestMin":5,"version":1},{"flightId":"F1002","airline":{"code":"VJ","name":"VietJet Air"},"flightNo":"VJ131","origin":"HAN","destination":"SGN","departAt":"2026-12-20T07:30:00+07:00","arriveAt":"2026-12-20T09:40:00+07:00","durationMin":130,"status":"SCHEDULED","seatClass":"ECONOMY","pricePerPax":1290000,"totalPrice":2580000,"seatsLeft":35,"priceDeltaVsCheapest":0,"durationDeltaVsFastestMin":5,"version":1},{"flightId":"F1003","airline":{"code":"QH","name":"Bamboo Airways"},"flightNo":"QH201","origin":"HAN","destination":"SGN","departAt":"2026-12-20T09:15:00+07:00","arriveAt":"2026-12-20T11:20:00+07:00","durationMin":125,"status":"SCHEDULED","seatClass":"ECONOMY","pricePerPax":1590000,"totalPrice":3180000,"seatsLeft":28,"priceDeltaVsCheapest":600000,"durationDeltaVsFastestMin":0,"version":1}],"cheapestFlightId":"F1002","fastestFlightId":"F1003"}}
```

### 19. C1 C->S — Round trip, 2 pax -> seats held

Payload: 345 UTF-8 bytes; then LF.

```json
{"v":1,"type":"BOOK_FLIGHT","id":"c-008","data":{"outboundFlightId":"F1002","returnFlightId":"F2002","seatClass":"ECONOMY","passengers":[{"fullName":"Nguyen Van An","dob":"1990-05-12","idNumber":"012345678"},{"fullName":"Tran Thi Binh","dob":"1992-08-30","idNumber":"023456789"}],"contactEmail":"alice@example.com","idempotencyKey":"idem-0001"}}
```

### 20. C1 S->C

Payload: 460 UTF-8 bytes; then LF.

```json
{"v":1,"type":"BOOK_FLIGHT_RESP","id":"c-008","ok":true,"code":"OK","data":{"bookingCode":"R7TQ2D","status":"PENDING_PAYMENT","totalAmount":5280000,"currency":"VND","holdExpiresAt":"2026-11-04T10:30:00+07:00","legs":[{"legType":"OUTBOUND","flightId":"F1002","flightNo":"VJ131","departAt":"2026-12-20T07:30:00+07:00","fare":2580000},{"legType":"RETURN","flightId":"F2002","flightNo":"VJ136","departAt":"2026-12-27T19:30:00+07:00","fare":2700000}],"revision":1}}
```

### 21. C1 C->S — Balance 5,000,000 < 5,280,000

Payload: 132 UTF-8 bytes; then LF.

```json
{"v":1,"type":"PAY_BOOKING","id":"c-009","data":{"bookingCode":"R7TQ2D","paymentMethod":"CREDIT_CARD","idempotencyKey":"idem-0002"}}
```

### 22. C1 S->C — Balance unchanged; booking stays PENDING_PAYMENT until hold expires

Payload: 176 UTF-8 bytes; then LF.

```json
{"v":1,"type":"PAY_BOOKING_RESP","id":"c-009","ok":false,"code":"E_INSUFFICIENT_BALANCE","message":"Account balance is too low","data":{"required":5280000,"available":5000000}}
```

### 23. C1 C->S — One-way, 1 pax

Payload: 249 UTF-8 bytes; then LF.

```json
{"v":1,"type":"BOOK_FLIGHT","id":"c-010","data":{"outboundFlightId":"F1003","seatClass":"ECONOMY","passengers":[{"fullName":"Nguyen Van An","dob":"1990-05-12","idNumber":"012345678"}],"contactEmail":"alice@example.com","idempotencyKey":"idem-0003"}}
```

### 24. C1 S->C

Payload: 347 UTF-8 bytes; then LF.

```json
{"v":1,"type":"BOOK_FLIGHT_RESP","id":"c-010","ok":true,"code":"OK","data":{"bookingCode":"X4K9PL","status":"PENDING_PAYMENT","totalAmount":1590000,"currency":"VND","holdExpiresAt":"2026-11-04T10:31:00+07:00","legs":[{"legType":"OUTBOUND","flightId":"F1003","flightNo":"QH201","departAt":"2026-12-20T09:15:00+07:00","fare":1590000}],"revision":1}}
```

### 25. C1 C->S — Pay from balance

Payload: 129 UTF-8 bytes; then LF.

```json
{"v":1,"type":"PAY_BOOKING","id":"c-011","data":{"bookingCode":"X4K9PL","paymentMethod":"E_WALLET","idempotencyKey":"idem-0004"}}
```

### 26. C1 S->C — Payment and delivery jobs committed; actual delivery not claimed

Payload: 351 UTF-8 bytes; then LF.

```json
{"v":1,"type":"PAY_BOOKING_RESP","id":"c-011","ok":true,"code":"OK","data":{"bookingCode":"X4K9PL","status":"TICKETED","paid":1590000,"balanceAfter":3410000,"currency":"VND","eTicketCode":"X4K9PL","tickets":[{"passengerName":"NGUYEN VAN AN","ticketNo":"738-4400000001"}],"delivery":{"email":{"to":"al***@example.com","status":"QUEUED"}},"revision":2}}
```

### 27. C1 C->S — Resend ticket code

Payload: 75 UTF-8 bytes; then LF.

```json
{"v":1,"type":"RESEND_TICKET","id":"c-012","data":{"bookingCode":"X4K9PL"}}
```

### 28. C1 S->C — Real email job queued; provider sends after commit

Payload: 140 UTF-8 bytes; then LF.

```json
{"v":1,"type":"RESEND_TICKET_RESP","id":"c-012","ok":true,"code":"OK","data":{"channel":"EMAIL","to":"al***@example.com","status":"QUEUED"}}
```

### 29. C1 C->S — List all

Payload: 53 UTF-8 bytes; then LF.

```json
{"v":1,"type":"LIST_BOOKINGS","id":"c-013","data":{}}
```

### 30. C1 S->C

Payload: 409 UTF-8 bytes; then LF.

```json
{"v":1,"type":"LIST_BOOKINGS_RESP","id":"c-013","ok":true,"code":"OK","data":{"bookings":[{"bookingCode":"X4K9PL","status":"TICKETED","route":"HAN-SGN","firstDepartAt":"2026-12-20T09:15:00+07:00","passengers":1,"totalAmount":1590000},{"bookingCode":"R7TQ2D","status":"PENDING_PAYMENT","route":"HAN-SGN-HAN","firstDepartAt":"2026-12-20T07:30:00+07:00","passengers":2,"totalAmount":5280000}],"nextOffset":null}}
```

### 31. C1 C->S — Ticket details

Payload: 73 UTF-8 bytes; then LF.

```json
{"v":1,"type":"GET_BOOKING","id":"c-014","data":{"bookingCode":"X4K9PL"}}
```

### 32. C1 S->C — Illustrative SENT status means real provider accepted email; not an executed inbox test

Payload: 736 UTF-8 bytes; then LF.

```json
{"v":1,"type":"GET_BOOKING_RESP","id":"c-014","ok":true,"code":"OK","data":{"bookingCode":"X4K9PL","status":"TICKETED","seatClass":"ECONOMY","passengers":[{"fullName":"Nguyen Van An","dob":"1990-05-12","idNumber":"012345678"}],"legs":[{"legType":"OUTBOUND","flightId":"F1003","flightNo":"QH201","origin":"HAN","destination":"SGN","departAt":"2026-12-20T09:15:00+07:00","arriveAt":"2026-12-20T11:20:00+07:00","flightStatus":"SCHEDULED","fare":1590000}],"tickets":[{"passengerName":"NGUYEN VAN AN","ticketNo":"738-4400000001"}],"totalPaid":1590000,"currency":"VND","disrupted":false,"createdAt":"2026-11-04T10:21:00+07:00","paidAt":"2026-11-04T10:22:00+07:00","revision":2,"delivery":{"email":{"to":"al***@example.com","status":"SENT"}}}}
```

### 33. C1 C->S — Printable text ticket

Payload: 74 UTF-8 bytes; then LF.

```json
{"v":1,"type":"PRINT_TICKET","id":"c-015","data":{"bookingCode":"X4K9PL"}}
```

### 34. C1 S->C

Payload: 381 UTF-8 bytes; then LF.

```json
{"v":1,"type":"PRINT_TICKET_RESP","id":"c-015","ok":true,"code":"OK","data":{"filename":"ticket-X4K9PL.txt","mimeType":"text/plain","lines":["=== E-TICKET ===","Booking code (PNR): X4K9PL","Passenger: NGUYEN VAN AN","Ticket no: 738-4400000001","Flight: QH201 HAN -> SGN","Depart: 2026-12-20 09:15 (+07:00)","Arrive: 2026-12-20 11:20 (+07:00)","Class: ECONOMY","Status: TICKETED"]}}
```

### 35. C1 C->S — Quote change

Payload: 133 UTF-8 bytes; then LF.

```json
{"v":1,"type":"CHANGE_BOOKING","id":"c-016","data":{"bookingCode":"X4K9PL","legType":"OUTBOUND","newFlightId":"F1004","dryRun":true}}
```

### 36. C1 S->C

Payload: 462 UTF-8 bytes; then LF.

```json
{"v":1,"type":"CHANGE_BOOKING_RESP","id":"c-016","ok":true,"code":"OK","data":{"dryRun":true,"bookingCode":"X4K9PL","legType":"OUTBOUND","newFlight":{"flightId":"F1004","flightNo":"VN215","departAt":"2026-12-20T14:00:00+07:00","arriveAt":"2026-12-20T16:10:00+07:00"},"changeFee":200000,"fareDifference":160000,"netAmount":360000,"balanceIfApplied":3050000,"currency":"VND","quoteId":"Q-CHANGE-1","quoteExpiresAt":"2026-11-04T10:24:00+07:00","bookingRevision":2}}
```

### 37. C1 C->S — Apply change

Payload: 186 UTF-8 bytes; then LF.

```json
{"v":1,"type":"CHANGE_BOOKING","id":"c-017","data":{"bookingCode":"X4K9PL","legType":"OUTBOUND","newFlightId":"F1004","dryRun":false,"idempotencyKey":"idem-0005","quoteId":"Q-CHANGE-1"}}
```

### 38. C1 S->C

Payload: 404 UTF-8 bytes; then LF.

```json
{"v":1,"type":"CHANGE_BOOKING_RESP","id":"c-017","ok":true,"code":"OK","data":{"dryRun":false,"bookingCode":"X4K9PL","status":"TICKETED","legType":"OUTBOUND","newFlight":{"flightId":"F1004","flightNo":"VN215","departAt":"2026-12-20T14:00:00+07:00","arriveAt":"2026-12-20T16:10:00+07:00"},"changeFee":200000,"fareDifference":160000,"netAmount":360000,"balanceAfter":3050000,"currency":"VND","revision":3}}
```

### 39. C1 C->S — User tries admin op

Payload: 203 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ADMIN_UPDATE_FLIGHT","id":"c-018","data":{"flightId":"F1004","action":"DELAY","delayMinutes":150,"reason":"Late inbound aircraft","expectedVersion":1,"idempotencyKey":"user-admin-denied"}}
```

### 40. C1 S->C

Payload: 150 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ADMIN_UPDATE_FLIGHT_RESP","id":"c-018","ok":false,"code":"E_FORBIDDEN","message":"Requires ADMIN role","data":{"requiredRole":"ADMIN"}}
```

### 41. C2 C->S — Seeded admin (second connection)

Payload: 85 UTF-8 bytes; then LF.

```json
{"v":1,"type":"LOGIN","id":"c-001","data":{"username":"admin","password":"admin123"}}
```

### 42. C2 S->C

Payload: 123 UTF-8 bytes; then LF.

```json
{"v":1,"type":"LOGIN_RESP","id":"c-001","ok":true,"code":"OK","data":{"userId":"U-0001","username":"admin","role":"ADMIN"}}
```

### 43. C2 C->S — Admin delays flight

Payload: 199 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ADMIN_UPDATE_FLIGHT","id":"c-002","data":{"flightId":"F1004","action":"DELAY","delayMinutes":150,"reason":"Late inbound aircraft","expectedVersion":1,"idempotencyKey":"admin-delay-1"}}
```

### 44. C2 S->C

Payload: 325 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ADMIN_UPDATE_FLIGHT_RESP","id":"c-002","ok":true,"code":"OK","data":{"flight":{"flightId":"F1004","flightNo":"VN215","status":"DELAYED","departAt":"2026-12-20T16:30:00+07:00","arriveAt":"2026-12-20T18:40:00+07:00","delayMinutes":150,"version":2},"affectedBookings":1,"notificationsCreated":1,"pushedOnline":1}}
```

### 45. C1 S->C — Server push to Alice's live connection

Payload: 475 UTF-8 bytes; then LF.

```json
{"v":1,"type":"NOTIFY","id":null,"data":{"notificationId":"N-0001","kind":"DELAY","bookingCode":"X4K9PL","flightId":"F1004","flightNo":"VN215","oldDepartAt":"2026-12-20T14:00:00+07:00","newDepartAt":"2026-12-20T16:30:00+07:00","newArriveAt":"2026-12-20T18:40:00+07:00","delayMinutes":150,"freeCancellation":true,"message":"Flight VN215 is delayed by 150 minutes. New departure 16:30. You may cancel free of charge.","createdAt":"2026-11-04T10:40:00+07:00","flightVersion":2}}
```

### 46. C1 C->S — Pull unread

Payload: 74 UTF-8 bytes; then LF.

```json
{"v":1,"type":"GET_NOTIFICATIONS","id":"c-019","data":{"unreadOnly":true}}
```

### 47. C1 S->C

Payload: 567 UTF-8 bytes; then LF.

```json
{"v":1,"type":"GET_NOTIFICATIONS_RESP","id":"c-019","ok":true,"code":"OK","data":{"notifications":[{"notificationId":"N-0001","kind":"DELAY","bookingCode":"X4K9PL","flightId":"F1004","flightNo":"VN215","oldDepartAt":"2026-12-20T14:00:00+07:00","newDepartAt":"2026-12-20T16:30:00+07:00","newArriveAt":"2026-12-20T18:40:00+07:00","delayMinutes":150,"freeCancellation":true,"message":"Flight VN215 is delayed by 150 minutes. New departure 16:30. You may cancel free of charge.","createdAt":"2026-11-04T10:40:00+07:00","flightVersion":2,"read":false}],"nextOffset":null}}
```

### 48. C1 C->S — Mark read

Payload: 84 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ACK_NOTIFICATION","id":"c-020","data":{"notificationIds":["N-0001"]}}
```

### 49. C1 S->C

Payload: 99 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ACK_NOTIFICATION_RESP","id":"c-020","ok":true,"code":"OK","data":{"acknowledged":1}}
```

### 50. C1 C->S — Optional full-fare cancellation preview for disrupted booking

Payload: 90 UTF-8 bytes; then LF.

```json
{"v":1,"type":"CANCEL_BOOKING","id":"c-021","data":{"bookingCode":"X4K9PL","dryRun":true}}
```

### 51. C1 S->C

Payload: 245 UTF-8 bytes; then LF.

```json
{"v":1,"type":"CANCEL_BOOKING_RESP","id":"c-021","ok":true,"code":"OK","data":{"dryRun":true,"bookingCode":"X4K9PL","fee":0,"feeReason":"INVOLUNTARY_CHANGE","refundAmount":1750000,"balanceIfApplied":4800000,"currency":"VND","bookingRevision":4}}
```

### 52. C1 C->S — Apply cancellation with booking code/key; no quote

Payload: 124 UTF-8 bytes; then LF.

```json
{"v":1,"type":"CANCEL_BOOKING","id":"c-022","data":{"bookingCode":"X4K9PL","dryRun":false,"idempotencyKey":"idem-cancel-1"}}
```

### 53. C1 S->C — Change fee 200,000 is non-refundable

Payload: 256 UTF-8 bytes; then LF.

```json
{"v":1,"type":"CANCEL_BOOKING_RESP","id":"c-022","ok":true,"code":"OK","data":{"dryRun":false,"bookingCode":"X4K9PL","status":"CANCELLED","fee":0,"feeReason":"INVOLUNTARY_CHANGE","refundAmount":1750000,"balanceAfter":4800000,"currency":"VND","revision":5}}
```

### 54. C1 C->S — Exact successful-key replay after cancellation returns historical result, without a debit

Payload: 129 UTF-8 bytes; then LF.

```json
{"v":1,"type":"PAY_BOOKING","id":"c-023","data":{"bookingCode":"X4K9PL","paymentMethod":"E_WALLET","idempotencyKey":"idem-0004"}}
```

### 55. C1 S->C

Payload: 351 UTF-8 bytes; then LF.

```json
{"v":1,"type":"PAY_BOOKING_RESP","id":"c-023","ok":true,"code":"OK","data":{"bookingCode":"X4K9PL","status":"TICKETED","paid":1590000,"balanceAfter":3410000,"currency":"VND","eTicketCode":"X4K9PL","tickets":[{"passengerName":"NGUYEN VAN AN","ticketNo":"738-4400000001"}],"delivery":{"email":{"to":"al***@example.com","status":"QUEUED"}},"revision":2}}
```

### 56. C1 C->S — Refresh current balance after historical replay

Payload: 51 UTF-8 bytes; then LF.

```json
{"v":1,"type":"GET_BALANCE","id":"c-024","data":{}}
```

### 57. C1 S->C

Payload: 112 UTF-8 bytes; then LF.

```json
{"v":1,"type":"GET_BALANCE_RESP","id":"c-024","ok":true,"code":"OK","data":{"balance":4800000,"currency":"VND"}}
```

### 58. C4 C->S

Payload: 44 UTF-8 bytes; then LF.

```json
{"v":1,"type":"PING","id":"c-002","data":{}}
```

### 59. C4 S->C

Payload: 111 UTF-8 bytes; then LF.

```json
{"v":1,"type":"PING_RESP","id":"c-002","ok":true,"code":"OK","data":{"serverTime":"2026-11-04T10:45:00+07:00"}}
```

### 60. C2 C->S — Same admin key: replay original delay result, no second delay or push

Payload: 199 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ADMIN_UPDATE_FLIGHT","id":"c-003","data":{"flightId":"F1004","action":"DELAY","delayMinutes":150,"reason":"Late inbound aircraft","expectedVersion":1,"idempotencyKey":"admin-delay-1"}}
```

### 61. C2 S->C

Payload: 325 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ADMIN_UPDATE_FLIGHT_RESP","id":"c-003","ok":true,"code":"OK","data":{"flight":{"flightId":"F1004","flightNo":"VN215","status":"DELAYED","departAt":"2026-12-20T16:30:00+07:00","arriveAt":"2026-12-20T18:40:00+07:00","delayMinutes":150,"version":2},"affectedBookings":1,"notificationsCreated":1,"pushedOnline":1}}
```

### 62. C2 C->S

Payload: 76 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ADMIN_LIST_FLIGHTS","id":"c-004","data":{"flightNo":"VN213"}}
```

### 63. C2 S->C

Payload: 315 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ADMIN_LIST_FLIGHTS_RESP","id":"c-004","ok":true,"code":"OK","data":{"flights":[{"flightId":"F1001","version":1,"flightNo":"VN213","origin":"HAN","destination":"SGN","departAt":"2026-12-20T06:00:00+07:00","arriveAt":"2026-12-20T08:10:00+07:00","status":"SCHEDULED","seatsLeft":40}],"nextOffset":null}}
```

### 64. C2 C->S

Payload: 275 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ADMIN_UPDATE_FLIGHT","id":"c-005","data":{"flightId":"F1001","action":"RESCHEDULE","newDepartAt":"2026-12-20T06:30:00+07:00","newArriveAt":"2026-12-20T08:40:00+07:00","reason":"Demo schedule revision","expectedVersion":1,"idempotencyKey":"admin-reschedule-1"}}
```

### 65. C2 S->C

Payload: 310 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ADMIN_UPDATE_FLIGHT_RESP","id":"c-005","ok":true,"code":"OK","data":{"flight":{"flightId":"F1001","version":2,"flightNo":"VN213","departAt":"2026-12-20T06:30:00+07:00","arriveAt":"2026-12-20T08:40:00+07:00","status":"RESCHEDULED"},"affectedBookings":0,"notificationsCreated":0,"pushedOnline":0}}
```

### 66. C2 C->S — Fresh key with stale version is rejected

Payload: 276 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ADMIN_UPDATE_FLIGHT","id":"c-006","data":{"flightId":"F1001","action":"RESCHEDULE","newDepartAt":"2026-12-20T06:30:00+07:00","newArriveAt":"2026-12-20T08:40:00+07:00","reason":"Demo schedule revision","expectedVersion":1,"idempotencyKey":"stale-admin-version"}}
```

### 67. C2 S->C

Payload: 171 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ADMIN_UPDATE_FLIGHT_RESP","id":"c-006","ok":false,"code":"E_VERSION_CONFLICT","data":{"kind":"flight","expected":1,"actual":2},"message":"Version conflict"}
```

### 68. C5 C->S

Payload: 135 UTF-8 bytes; then LF.

```json
{"v":1,"type":"REGISTER","id":"b-001","data":{"username":"bob","password":"secret123","fullName":"Bob Tran","email":"bob@example.com"}}
```

### 69. C5 S->C

Payload: 158 UTF-8 bytes; then LF.

```json
{"v":1,"type":"REGISTER_RESP","id":"b-001","ok":true,"code":"OK","data":{"userId":"U-1002","username":"bob","role":"USER","balance":5000000,"currency":"VND"}}
```

### 70. C5 C->S

Payload: 84 UTF-8 bytes; then LF.

```json
{"v":1,"type":"LOGIN","id":"b-002","data":{"username":"bob","password":"secret123"}}
```

### 71. C5 S->C

Payload: 179 UTF-8 bytes; then LF.

```json
{"v":1,"type":"LOGIN_RESP","id":"b-002","ok":true,"code":"OK","data":{"userId":"U-1002","username":"bob","role":"USER","balance":5000000,"currency":"VND","unreadNotifications":0}}
```

### 72. C5 C->S

Payload: 243 UTF-8 bytes; then LF.

```json
{"v":1,"type":"BOOK_FLIGHT","id":"b-003","data":{"outboundFlightId":"F1001","seatClass":"ECONOMY","passengers":[{"fullName":"Bob Tran","dob":"1990-01-01","idNumber":"111222333"}],"contactEmail":"bob@example.com","idempotencyKey":"bob-book-1"}}
```

### 73. C5 S->C

Payload: 347 UTF-8 bytes; then LF.

```json
{"v":1,"type":"BOOK_FLIGHT_RESP","id":"b-003","ok":true,"code":"OK","data":{"bookingCode":"BOB001","revision":1,"status":"PENDING_PAYMENT","totalAmount":1850000,"currency":"VND","holdExpiresAt":"2026-11-04T10:56:00+07:00","legs":[{"legType":"OUTBOUND","flightId":"F1001","flightNo":"VN213","departAt":"2026-12-20T06:30:00+07:00","fare":1850000}]}}
```

### 74. C5 C->S — Optional unpaid cancellation preview; no refund or stored quote

Payload: 90 UTF-8 bytes; then LF.

```json
{"v":1,"type":"CANCEL_BOOKING","id":"b-004","data":{"bookingCode":"BOB001","dryRun":true}}
```

### 75. C5 S->C

Payload: 233 UTF-8 bytes; then LF.

```json
{"v":1,"type":"CANCEL_BOOKING_RESP","id":"b-004","ok":true,"code":"OK","data":{"dryRun":true,"bookingCode":"BOB001","fee":0,"feeReason":"PENDING_HOLD","refundAmount":0,"currency":"VND","bookingRevision":1,"balanceIfApplied":5000000}}
```

### 76. C5 C->S — Repeat preview at 10:47; no quote expiry and the hold remains live

Payload: 90 UTF-8 bytes; then LF.

```json
{"v":1,"type":"CANCEL_BOOKING","id":"b-005","data":{"bookingCode":"BOB001","dryRun":true}}
```

### 77. C5 S->C — Preview still succeeds; no booking, balance or seat changes

Payload: 233 UTF-8 bytes; then LF.

```json
{"v":1,"type":"CANCEL_BOOKING_RESP","id":"b-005","ok":true,"code":"OK","data":{"dryRun":true,"bookingCode":"BOB001","fee":0,"feeReason":"PENDING_HOLD","refundAmount":0,"currency":"VND","bookingRevision":1,"balanceIfApplied":5000000}}
```

### 78. C5 C->S

Payload: 132 UTF-8 bytes; then LF.

```json
{"v":1,"type":"PAY_BOOKING","id":"b-006","data":{"bookingCode":"BOB001","paymentMethod":"CREDIT_CARD","idempotencyKey":"bob-pay-1"}}
```

### 79. C5 S->C

Payload: 346 UTF-8 bytes; then LF.

```json
{"v":1,"type":"PAY_BOOKING_RESP","id":"b-006","ok":true,"code":"OK","data":{"bookingCode":"BOB001","revision":2,"status":"TICKETED","paid":1850000,"balanceAfter":3150000,"currency":"VND","eTicketCode":"BOB001","tickets":[{"passengerName":"BOB TRAN","ticketNo":"738-4400000002"}],"delivery":{"email":{"to":"bo***@example.com","status":"QUEUED"}}}}
```

### 80. C2 C->S

Payload: 178 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ADMIN_UPDATE_FLIGHT","id":"c-007","data":{"flightId":"F1001","action":"CANCEL","reason":"Demo cancellation","expectedVersion":2,"idempotencyKey":"admin-cancel-1"}}
```

### 81. C2 S->C

Payload: 308 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ADMIN_UPDATE_FLIGHT_RESP","id":"c-007","ok":true,"code":"OK","data":{"flight":{"flightId":"F1001","version":3,"flightNo":"VN213","departAt":"2026-12-20T06:30:00+07:00","arriveAt":"2026-12-20T08:40:00+07:00","status":"CANCELLED"},"affectedBookings":1,"notificationsCreated":1,"pushedOnline":1}}
```

### 82. C5 S->C — Cancellation refund notification; delivery is not a read acknowledgment

Payload: 356 UTF-8 bytes; then LF.

```json
{"v":1,"type":"NOTIFY","id":null,"data":{"notificationId":"N-0002","kind":"FLIGHT_CANCELLED","bookingCode":"BOB001","flightId":"F1001","flightVersion":3,"flightNo":"VN213","oldDepartAt":"2026-12-20T06:30:00+07:00","freeCancellation":true,"refundAmount":1850000,"message":"Flight VN213 cancelled. Booking refunded.","createdAt":"2026-11-04T10:48:00+07:00"}}
```

### 83. C2 C->S — Replay cancellation: no second refund/push

Payload: 178 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ADMIN_UPDATE_FLIGHT","id":"c-008","data":{"flightId":"F1001","action":"CANCEL","reason":"Demo cancellation","expectedVersion":2,"idempotencyKey":"admin-cancel-1"}}
```

### 84. C2 S->C

Payload: 308 UTF-8 bytes; then LF.

```json
{"v":1,"type":"ADMIN_UPDATE_FLIGHT_RESP","id":"c-008","ok":true,"code":"OK","data":{"flight":{"flightId":"F1001","version":3,"flightNo":"VN213","departAt":"2026-12-20T06:30:00+07:00","arriveAt":"2026-12-20T08:40:00+07:00","status":"CANCELLED"},"affectedBookings":1,"notificationsCreated":1,"pushedOnline":1}}
```

### 85. C5 C->S

Payload: 51 UTF-8 bytes; then LF.

```json
{"v":1,"type":"GET_BALANCE","id":"b-007","data":{}}
```

### 86. C5 S->C

Payload: 112 UTF-8 bytes; then LF.

```json
{"v":1,"type":"GET_BALANCE_RESP","id":"b-007","ok":true,"code":"OK","data":{"balance":5000000,"currency":"VND"}}
```

### 87. C1 C->S — Reused successful BOOK key with another flight

Payload: 249 UTF-8 bytes; then LF.

```json
{"v":1,"type":"BOOK_FLIGHT","id":"c-025","data":{"outboundFlightId":"F1004","seatClass":"ECONOMY","passengers":[{"fullName":"Nguyen Van An","dob":"1990-05-12","idNumber":"012345678"}],"contactEmail":"alice@example.com","idempotencyKey":"idem-0003"}}
```

### 88. C1 S->C

Payload: 160 UTF-8 bytes; then LF.

```json
{"v":1,"type":"BOOK_FLIGHT_RESP","id":"c-025","ok":false,"code":"E_IDEMPOTENCY_CONFLICT","data":{"idempotencyKey":"idem-0003"},"message":"Idempotency conflict"}
```

### 89. C5 C->S

Payload: 46 UTF-8 bytes; then LF.

```json
{"v":1,"type":"LOGOUT","id":"b-008","data":{}}
```

### 90. C5 S->C

Payload: 73 UTF-8 bytes; then LF.

```json
{"v":1,"type":"LOGOUT_RESP","id":"b-008","ok":true,"code":"OK","data":{}}
```

### 91. C1 C->S

Payload: 46 UTF-8 bytes; then LF.

```json
{"v":1,"type":"LOGOUT","id":"c-026","data":{}}
```

### 92. C1 S->C

Payload: 73 UTF-8 bytes; then LF.

```json
{"v":1,"type":"LOGOUT_RESP","id":"c-026","ok":true,"code":"OK","data":{}}
```
