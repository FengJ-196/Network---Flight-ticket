#!/usr/bin/env python3
"""Validate the local FBP design transcript, then render wire-examples.md.

Usage: python validate_examples.py [--check]
--check verifies the generated Markdown without changing files.
Uses only Python's standard library. This is structural/transcript validation,
not a running TCP parser, SQL transaction, provider, or two-PC test.
"""
import argparse
import copy
import json
from pathlib import Path
import re
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parent
MUTATIONS = {"BOOK_FLIGHT", "PAY_BOOKING", "CANCEL_BOOKING",
             "CHANGE_BOOKING", "ADMIN_UPDATE_FLIGHT"}
MONEY = {"balance", "balanceAfter", "balanceIfApplied", "totalAmount",
         "totalPaid", "paid", "fare", "pricePerPax", "totalPrice", "fee",
         "refundAmount", "required", "available", "changeFee",
         "fareDifference", "netAmount", "priceDeltaVsCheapest"}


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key {key}")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError(f"nonfinite JSON value {value}")
    return json.loads(text, object_pairs_hook=pairs, parse_constant=nonfinite)


def compact(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def render(entries):
    lines = [
        "# Wire examples (generated)", "",
        "Generated from [wire-examples.jsonl](wire-examples.jsonl) by "
        "[validate_examples.py](validate_examples.py); edit the JSONL and regenerate.",
        "JSONL rows contain annotations. Only each code block's payload is transmitted, "
        "encoded as UTF-8 and followed by one LF byte (0A); headings/metadata are not sent.",
        "Fixed synthetic clock: 2026-11-04, +07:00. Main purchase occurs 10:20–10:23, "
        "delay 10:40, cancellation 10:41; supporting exchanges run 10:45–10:48.",
        "C1 = Alice, C2 = admin, C4 = anonymous, C5 = Bob. Connections start ANON. "
        "All credentials and contacts are synthetic. These are proposed exchanges, not captured traffic.",
        "R7 uses real email only. SENT in an example means provider acceptance; these fixtures do not send email or prove inbox receipt.",
        "",
    ]
    for entry in entries:
        payload = entry.get("raw") if "raw" in entry else compact(entry["msg"])
        size = len(payload.encode("utf-8"))
        title = f"### {entry['n']}. {entry['conn']} {entry['dir']}"
        if entry.get("note"):
            title += " — " + entry["note"]
        lines += [title, "", f"Payload: {size} UTF-8 bytes; then LF.",
                  "", "```json", payload, "```", ""]
    return "\n".join(lines)


def validate(root=ROOT):
    cat = strict_json((root / "message-catalog.json").read_text(encoding="utf-8"))
    entries = [strict_json(line) for line in
               (root / "wire-examples.jsonl").read_text(encoding="utf-8").splitlines()
               if line.strip()]
    problems, conns, balances, books, applied = [], {}, {}, {}, {}
    used_types, used_errors = set(), set()

    def check(ok, message):
        if not ok:
            problems.append(message)

    cancel_spec = cat["messages"]["CANCEL_BOOKING"]
    check("quoteId" not in cancel_spec["required"] + cancel_spec["optional"],
          "catalog: cancellation must not require or accept quoteId")
    check(cat.get("cancellation_policy", {}).get("fee") == 0
          and cat.get("cancellation_policy", {}).get("quoteRequired") is False,
          "catalog: cancellation must have zero fee and no quote")
    check(cat.get("delivery_channels") == ["EMAIL"], "catalog: R7 must use EMAIL only")
    check(cat.get("delivery_statuses") == ["QUEUED", "SENT", "FAILED"],
          "catalog: real email delivery statuses must be QUEUED/SENT/FAILED")

    def email_delivery(data, context, required=False):
        if not isinstance(data, dict):
            check(False, f"{context}: delivery must be object")
            return
        check(set(data) == {"email"} if required else set(data) <= {"email"},
              f"{context}: delivery must contain only email")
        if "email" not in data:
            return
        job = data["email"]
        if not isinstance(job, dict):
            check(False, f"{context}: email delivery must be object")
            return
        check(all(k in job for k in cat["objects"]["EmailDelivery"]["required"]),
              f"{context}: incomplete email delivery")
        check(job.get("status") in cat["delivery_statuses"],
              f"{context}: invalid real email delivery status")
        check(isinstance(job.get("to"), str) and "@" in job["to"],
              f"{context}: email delivery requires masked email recipient")

    def integers(value, context):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in MONEY:
                    check(type(item) is int, f"{context}: {key} must be integer VND")
                    if type(item) is int:
                        check(abs(item) <= 9_000_000_000_000,
                              f"{context}: {key} exceeds money bound")
                        if key not in {"netAmount", "fareDifference", "balanceIfApplied"}:
                            check(item >= 0, f"{context}: negative {key}")
                integers(item, context)
        elif isinstance(value, list):
            for item in value:
                integers(item, context)

    def notification(data, context, listed=False):
        required = cat["push"]["NOTIFY"]["required"]
        check(all(k in data for k in required), f"{context}: incomplete Notification")
        extra = cat["objects"]["Notification"]["kind_fields"]
        kind = data.get("kind")
        check(kind in extra, f"{context}: invalid notification kind")
        check(all(k in data for k in extra.get(kind, [])),
              f"{context}: missing kind-specific notification fields")
        if listed:
            check(type(data.get("read")) is bool, f"{context}: list needs read flag")

    for index, entry in enumerate(entries, 1):
        n = entry.get("n")
        prefix = f"example #{n}"
        check(n == index, f"{prefix}: expected sequential number {index}")
        check(entry.get("dir") in {"C->S", "S->C"}, f"{prefix}: bad direction")
        c = conns.setdefault(entry["conn"],
                             {"role": "ANON", "user": None, "pending": None,
                              "ids": set(), "closed": False})
        check(not c["closed"], f"{prefix}: frame on closed connection")
        payload = entry["raw"] if "raw" in entry else compact(entry["msg"])
        wire = payload.encode("utf-8") + b"\n"
        check(len(wire) - 1 <= 65536, f"{prefix}: oversized UTF-8 payload")
        check(b"\n" not in wire[:-1] and b"\r" not in wire[:-1],
              f"{prefix}: raw newline breaks NDJSON")
        if "raw" in entry:
            check(entry["dir"] == "C->S", f"{prefix}: malformed fixture direction")
            check(c["pending"] is None, f"{prefix}: overlapping request")
            try:
                strict_json(payload)
                check(False, f"{prefix}: malformed fixture is valid JSON")
            except ValueError:
                pass
            c["pending"] = ("ERROR", None, {}, None)
            continue

        m = entry["msg"]
        check(type(m.get("v")) is int and m["v"] == 1, f"{prefix}: invalid version")
        check(isinstance(m.get("data"), dict), f"{prefix}: data must be object")
        d, t = m.get("data", {}), m.get("type")
        integers(d, prefix)
        if entry["dir"] == "C->S":
            used_types.add(t)
            check(set(m) == {"v", "type", "id", "data"}, f"{prefix}: request envelope")
            check(c["pending"] is None, f"{prefix}: overlapping request")
            rid = m.get("id")
            check(isinstance(rid, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", rid)
                  is not None, f"{prefix}: bad request ID")
            check(rid not in c["ids"], f"{prefix}: reused connection request ID")
            c["ids"].add(rid)
            spec = cat["messages"].get(t)
            if spec is None:
                check(False, f"{prefix}: unknown request type")
                continue
            issues = []
            for key in spec["required"]:
                if key not in d:
                    issues.append(f"missing {key}")
            for key, value in d.items():
                if key not in spec["required"] + spec["optional"]:
                    issues.append(f"unknown {key}")
                    continue
                kind = cat["field_types"][key]
                valid = {
                    "string": lambda x: isinstance(x, str) and bool(x),
                    "boolean": lambda x: type(x) is bool,
                    "integer": lambda x: type(x) is int,
                    "string_array": lambda x: isinstance(x, list) and all(isinstance(y, str) for y in x),
                    "integer_or_passenger_array": lambda x: type(x) is int if t != "BOOK_FLIGHT" else isinstance(x, list),
                }[kind](value)
                if not valid:
                    issues.append(f"wrong type for {key}")
                if key in cat["enums"] and value not in cat["enums"][key]:
                    issues.append(f"invalid enum {key}")
            if "conditional_required" in spec:
                conditional = spec["conditional_required"]
                if d.get("dryRun", False):
                    issues += [f"forbidden {k}" for k in conditional["forbidden_when_dryRun_true"] if k in d]
                else:
                    issues += [f"missing {k}" for k in conditional["when_dryRun_false_or_omitted"] if k not in d]
            if t == "ADMIN_UPDATE_FLIGHT" and d.get("action") in spec["action_fields"]:
                needed = spec["action_fields"][d["action"]]
                all_action = {"delayMinutes", "newDepartAt", "newArriveAt"}
                issues += [f"missing {k}" for k in needed if k not in d]
                issues += [f"forbidden {k}" for k in all_action - set(needed) if k in d]
            if t in {"SEARCH_FLIGHTS", "COMPARE_FLIGHTS"} and type(d.get("passengers")) is int:
                if not 1 <= d["passengers"] <= 9:
                    issues.append("passengers out of range")
            if t == "BOOK_FLIGHT":
                pax = d.get("passengers", [])
                if not isinstance(pax, list) or not 1 <= len(pax) <= 9:
                    issues.append("invalid passenger array")
                else:
                    for passenger in pax:
                        if not isinstance(passenger, dict) or set(passenger) != {"fullName", "dob", "idNumber"}:
                            issues.append("invalid Passenger fields")
            for key, low, high in [("limit", 1, 20), ("offset", 0, 10000),
                                   ("delayMinutes", 1, 1440), ("expectedVersion", 1, 2**31-1)]:
                if key in d and (type(d[key]) is not int or not low <= d[key] <= high):
                    issues.append(f"{key} out of range")
            for key, low, high in [("flightIds", 2, 5), ("notificationIds", 1, 50)]:
                if key in d and isinstance(d[key], list):
                    if not low <= len(d[key]) <= high or len(set(d[key])) != len(d[key]):
                        issues.append(f"invalid {key} count/duplicates")
            expected = entry.get("expectedRequestError")
            check(not issues or expected == "E_VALIDATION",
                  f"{prefix}: request constraints: {', '.join(issues)}")
            check(expected is None or bool(issues), f"{prefix}: expected-invalid annotation has no detected fault")
            c["pending"] = (t, rid, d, expected)
            continue

        if t == "NOTIFY":
            check(set(m) == {"v", "type", "id", "data"} and m.get("id") is None,
                  f"{prefix}: push envelope")
            check(c["role"] == "USER", f"{prefix}: push on noncustomer connection")
            notification(d, prefix)
            book = books.get(d.get("bookingCode"))
            if book:
                check(book["owner"] == c["user"], f"{prefix}: push to wrong owner")
            continue

        check(c["pending"] is not None, f"{prefix}: orphan response")
        if c["pending"] is None:
            continue
        req, rid, req_data, expected = c["pending"]
        c["pending"] = None
        check(type(m.get("ok")) is bool, f"{prefix}: ok must be boolean")
        check(m.get("id") == rid, f"{prefix}: response ID mismatch")
        check(t == ("ERROR_RESP" if req == "ERROR" else req + "_RESP"),
              f"{prefix}: response type mismatch")
        needed_envelope = {"v", "type", "id", "ok", "code", "data"}
        if m.get("ok") is False:
            needed_envelope.add("message")
        check(set(m) == needed_envelope, f"{prefix}: response envelope fields")
        if m.get("ok") is not True:
            code = m.get("code")
            used_errors.add(code)
            allowed = cat["common_errors"] + ([] if req == "ERROR" else cat["messages"][req]["errors"])
            check(code in cat["errors"] and code in allowed, f"{prefix}: disallowed error {code}")
            check(isinstance(m.get("message"), str) and bool(m["message"]), f"{prefix}: missing error message")
            if expected:
                check(code == expected, f"{prefix}: wrong expected rejection")
            continue

        check(expected is None, f"{prefix}: invalid request succeeded")
        check(req != "ERROR", f"{prefix}: malformed input succeeded")
        if req == "ERROR":
            continue
        spec = cat["messages"][req]
        check(m.get("code") == "OK", f"{prefix}: success code")
        check(c["role"] in spec["roles"], f"{prefix}: success for disallowed role")
        check(all(k in d for k in spec["success_required"]), f"{prefix}: missing success fields")
        if req in {"REGISTER", "LOGIN"}:
            check(d["role"] in {"USER", "ADMIN"}, f"{prefix}: invalid returned role")
            if req == "REGISTER":
                check(d["role"] == "USER", f"{prefix}: public admin registration")
            else:
                c["role"], c["user"] = d["role"], d["userId"]
                if d["role"] == "USER":
                    check(all(k in d for k in ["balance", "currency", "unreadNotifications"]),
                          f"{prefix}: incomplete customer login")
            if "balance" in d:
                balances[d["userId"]] = d["balance"]
        if req == "LOGOUT":
            check(d == {}, f"{prefix}: logout data must be empty")
            c["closed"] = True

        key = None
        if req in MUTATIONS and not req_data.get("dryRun", False):
            key = (c["user"], req, req_data["idempotencyKey"])
            canonical = copy.deepcopy(req_data)
            if req in {"CANCEL_BOOKING", "CHANGE_BOOKING"}:
                canonical.setdefault("dryRun", False)
            if key in applied:
                old_request, old_data = applied[key]
                check(canonical == old_request and d == old_data,
                      f"{prefix}: replay differs from committed request/result")
                continue
            applied[key] = (canonical, copy.deepcopy(d))

        user, balance = c["user"], balances.get(c["user"])
        code = d.get("bookingCode")
        book = books.get(code)
        if req == "BOOK_FLIGHT":
            check(d["totalAmount"] == sum(leg["fare"] for leg in d["legs"]),
                  f"{prefix}: booking total != sum of legs")
            books[code] = {"owner": user, "status": d["status"], "pax": len(req_data["passengers"]),
                           "fare": d["totalAmount"], "paid": 0, "fees": 0,
                           "legs": copy.deepcopy(d["legs"]), "revision": d["revision"],
                           "order": n}
        if req == "PAY_BOOKING":
            email_delivery(d["delivery"], prefix, required=True)
            check(book is not None and book["owner"] == user, f"{prefix}: payment unknown/unowned")
            if book:
                check(d["paid"] == book["fare"] and len(d["tickets"]) == book["pax"],
                      f"{prefix}: payment fare/ticket count")
                book.update(status="TICKETED", paid=d["paid"], revision=d["revision"])
            check(balance is not None and balance - d["paid"] == d["balanceAfter"],
                  f"{prefix}: payment balance arithmetic")
            balances[user] = d["balanceAfter"]
            check(all(job["status"] == "QUEUED" for job in d["delivery"].values()),
                  f"{prefix}: payment snapshot must be QUEUED")
        if req in {"CANCEL_BOOKING", "CHANGE_BOOKING"}:
            dry = req_data.get("dryRun", False)
            result_type = "AppliedQuoteResult"
            if dry:
                result_type = "CancellationPreviewResult" if req == "CANCEL_BOOKING" else "QuoteResult"
            fields = cat["objects"][result_type]["required"]
            check(d.get("dryRun") is dry and all(k in d for k in fields),
                  f"{prefix}: preview/quote/applied result fields")
            after = d["balanceIfApplied" if dry else "balanceAfter"]
            if req == "CHANGE_BOOKING":
                check(d["netAmount"] == d["changeFee"] + d["fareDifference"],
                      f"{prefix}: change net arithmetic")
                check(balance - d["netAmount"] == after, f"{prefix}: change balance arithmetic")
                if not dry and book:
                    book["fare"] += d["fareDifference"]
                    book["fees"] += d["changeFee"]
                    book["paid"] += d["netAmount"]
                    book["revision"] = d["revision"]
                    for leg in book["legs"]:
                        if leg["legType"] == req_data["legType"]:
                            leg.update(d["newFlight"])
                            leg["fare"] += d["fareDifference"]
            else:
                check(d["fee"] == 0, f"{prefix}: cancellation fee must be zero")
                check(not {"quoteId", "quoteExpiresAt"} & set(d),
                      f"{prefix}: cancellation must not create a quote")
                check(balance + d["refundAmount"] == after, f"{prefix}: cancel balance arithmetic")
                if book:
                    expected_refund = book["fare"] if book["status"] == "TICKETED" else 0
                    check(d["refundAmount"] == expected_refund, f"{prefix}: cancellation must refund full fare or zero if unpaid")
                    if not dry:
                        book.update(status="CANCELLED", revision=d["revision"],
                                    paid=book["paid"] - d["refundAmount"])
            if not dry:
                balances[user] = after
        if req == "ADMIN_UPDATE_FLIGHT":
            flight = d["flight"]
            affected = [b for b in books.values() if b["status"] in {"PENDING_PAYMENT", "TICKETED"}
                        and any(leg["flightId"] == flight["flightId"] for leg in b["legs"])]
            check(d["affectedBookings"] == len(affected), f"{prefix}: affected booking count")
            check(d["notificationsCreated"] == sum(b["status"] == "TICKETED" for b in affected),
                  f"{prefix}: notification count")
            for b in affected:
                b["revision"] += 1
                if req_data["action"] == "CANCEL":
                    balances[b["owner"]] += b["paid"]
                    b["paid"] = 0
                    b["status"] = "FLIGHT_CANCELLED" if b["status"] == "TICKETED" else "CANCELLED"
                elif b["status"] == "PENDING_PAYMENT":
                    b["status"] = "CANCELLED"
                else:
                    for leg in b["legs"]:
                        if leg["flightId"] == flight["flightId"]:
                            leg.update(departAt=flight["departAt"], arriveAt=flight["arriveAt"])
        if req == "GET_BALANCE":
            check(d["balance"] == balance, f"{prefix}: GET_BALANCE differs from ledger chain")
        if req == "GET_BOOKING":
            email_delivery(d["delivery"], prefix, required=d.get("status") == "TICKETED")
            if book:
                check(d["status"] == book["status"] and d["totalPaid"] == book["paid"]
                      and d["revision"] == book["revision"], f"{prefix}: booking snapshot inconsistent")
        if req == "LIST_BOOKINGS":
            known = [books[b["bookingCode"]]["order"] for b in d["bookings"] if b["bookingCode"] in books]
            check(known == sorted(known, reverse=True), f"{prefix}: bookings not newest first")
        if req == "GET_NOTIFICATIONS":
            for item in d["notifications"]:
                notification(item, prefix, listed=True)
        if req in {"SEARCH_FLIGHTS", "COMPARE_FLIGHTS"}:
            offers = d.get("outbound", []) + d.get("inbound", []) + d.get("rows", [])
            for offer in offers:
                check(all(k in offer for k in cat["objects"]["Offer"]["required"]),
                      f"{prefix}: incomplete Offer")
                check(offer["totalPrice"] == offer["pricePerPax"] * req_data["passengers"],
                      f"{prefix}: offer total arithmetic")
                duration = (datetime.fromisoformat(offer["arriveAt"]) -
                            datetime.fromisoformat(offer["departAt"])).total_seconds() / 60
                check(offer["durationMin"] == duration, f"{prefix}: elapsed duration")
            if req == "COMPARE_FLIGHTS" and offers:
                cheapest = min(offers, key=lambda o: (o["totalPrice"], o["flightId"]))
                fastest = min(offers, key=lambda o: (o["durationMin"], o["flightId"]))
                check(d["cheapestFlightId"] == cheapest["flightId"]
                      and d["fastestFlightId"] == fastest["flightId"], f"{prefix}: comparison markers")
                for offer in offers:
                    check(offer["priceDeltaVsCheapest"] == offer["totalPrice"] - cheapest["totalPrice"]
                          and offer["durationDeltaVsFastestMin"] == offer["durationMin"] - fastest["durationMin"],
                          f"{prefix}: comparison delta")
        if req == "RESEND_TICKET":
            check(d.get("channel") == "EMAIL", f"{prefix}: resend response must use EMAIL")
            check(isinstance(d.get("to"), str) and "@" in d["to"],
                  f"{prefix}: resend requires masked email recipient")
            check(d["status"] in cat["delivery_statuses"], f"{prefix}: delivery status")

    for name, c in conns.items():
        check(c["pending"] is None, f"{name}: unanswered request at end")
    for message in list(cat["messages"]) + list(cat["push"]):
        check(f"`{message}`" in (root / "message-spec.md").read_text(encoding="utf-8"),
              f"message-spec.md does not document {message}")
    error_doc = (root / "error-catalog.md").read_text(encoding="utf-8")
    for code in cat["errors"]:
        check(f"`{code}`" in error_doc, f"error-catalog.md does not document {code}")
    for name, spec in cat["messages"].items():
        check(set(spec["errors"]) <= set(cat["errors"]), f"{name}: undefined catalog errors")
        check(name in used_types, f"{name}: no complete request example")
    for path in root.glob("*.md"):
        for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", path.read_text(encoding="utf-8")):
            if re.match(r"^[a-zA-Z]+:", target) or target.startswith("#"):
                continue
            local = target.strip("<>").split("#", 1)[0]
            check((path.parent / local).exists(), f"{path.name}: broken link {target}")
    return problems, entries, used_types, used_errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        problems, entries, types, errors = validate()
        generated = render(entries)
        if args.check and (ROOT / "wire-examples.md").read_text(encoding="utf-8") != generated:
            problems.append("wire-examples.md is stale; run without --check")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"FAILED: invalid package input: {exc}")
        return 1
    if problems:
        print("FAILED:")
        for problem in problems:
            print(" -", problem)
        return 1
    if not args.check:
        (ROOT / "wire-examples.md").write_text(generated, encoding="utf-8", newline="\n")
    print(f"OK: {len(entries)} transcript frames; all {len(types)} request types; "
          f"{len(errors)} error codes demonstrated; local Markdown links resolve.")
    print("Validated envelopes, payload inventory/types, reply pairing, roles, replay snapshots, "
          "UTF-8 byte bounds and transcript money/booking arithmetic.")
    print("Structural/transcript checks only; no application, SQL, TCP or two-PC runtime proof.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
