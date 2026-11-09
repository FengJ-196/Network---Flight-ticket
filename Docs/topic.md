### Topic Requirement
The application allows users to search, compare, and book flight tickets online from various airlines. The application also enables users to manage their booked tickets, cancel, change, and receive notifications about flights. The required features include:


- User account registration and login.
- Search for flights based on departure and destination points, departure date, return date, number of passengers, and seat class.
- Compare ticket prices and flight times from different airlines.
- Book flight tickets and make online payments using credit cards or electronic wallets.
- Receive electronic ticket codes (via email or text message).
- Manage booked tickets: view ticket details, cancel tickets, change tickets, and print tickets.
- Receive flight notifications: schedule changes, flight cancellations, delays.

### Requirements:

- Establish a client-server connection using sockets (2 points).
- Log received and sent messages on the server (1 point).
- User account registration and login (2 points).
- Search for flights based on various criteria (2 points).
- Compare ticket prices and flight times from different airlines (2 points).
- Book flight tickets and make online payments (3 points).
- Receive electronic ticket codes (via email or text message) (2 points).
- Manage booked tickets: view ticket details, cancel tickets, change tickets, and print tickets (3 points).
- Receive flight notifications: schedule changes, flight cancellations, delays (3 points).


### Note when working with professor about the project: 

- Payment can be perform by having balance in user account, user account will be check for sufficient amount and deduction payment complete.
- Data for the flights will be all mocked data.
- Admin role is require to perform the flight notifications triggers.

### Confirmed R7 implementation scope (user, 2026-11-05)

- Send real e-ticket emails to the booking contact email.
- Email is the only delivery channel; SMS is excluded.
- Demonstrate actual receipt in a recipient mailbox. A simulated email/outbox file does not complete R7.

### Confirmed cancellation/refund scope (user, 2026-11-05)

- Paid booking at least 2 hours before departure: cancellation allowed, refund 100% of fare with no cancellation fee.
- Standard paid booking less than 2 hours before departure: `E_CANCEL_NOT_ALLOWED`.
- Disrupted booking before departure: full fare refund, including within 2 hours.
- Live `PENDING_PAYMENT`: release the hold, refund nothing.
- Keep cancellation simple: direct apply with the booking code and retry key; an optional preview needs no stored quote. Change-flight fees and quotes remain separate proposed rules.
