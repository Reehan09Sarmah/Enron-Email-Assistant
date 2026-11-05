"""R8: do copies in a body group look like one message? Recipients, shifts, audit."""

import argparse
import statistics
from collections import Counter, defaultdict
from functools import partial
from typing import NamedTuple, Optional

from scripts.data_checks.common import fingerprint
from scripts.data_checks.raw_csv import DEFAULT_BLOCK_MB
from scripts.data_checks.report import info, run_check, share_row
from scripts.data_checks.same_message_audit import (
    AUDIT_PATH,
    pick_groups,
    write_audit_file,
)
from scripts.data_checks.shared_groups import (
    header_value,
    load_groups,
    parse_instant,
    parse_message,
    read_summaries,
)

NAME = "same_message_check"
SENT_WORD = "sent"
SECONDS_PER_HOUR = 3600
MAX_SHIFT_HOURS = 14
SHIFT_TOLERANCE_SECONDS = 60
TOP_OWNERS = 10
MIN_COPIES_PER_OWNER = 5
NOTHING_DIFFERS = "nothing differs"
DATE_ONLY = "date only"
OTHER_DIFFERENCE = "sender and/or subject differs"
GAP_BUCKETS = [
    "0 s",
    "under 1 minute",
    "whole hours 1-14",
    "other under 24 hours",
    "1 day or more",
]
REMAINDER_LIMITS = [
    ("0 s", 0),
    ("up to 10 s", 10),
    ("up to 1 minute", 60),
    ("up to 5 minutes", 300),
    ("up to 30 minutes", 1800),
]
REMAINDER_MORE = "more"


class Header(NamedTuple):
    instant: Optional[int]
    date_fp: bytes
    sender_fp: bytes
    subject_fp: bytes
    recipients_fp: bytes


def recipient_set(headers):
    text = ",".join([header_value(headers, "to"), header_value(headers, "cc")])
    addresses = {part.strip() for part in text.lower().split(",") if part.strip()}
    return ",".join(sorted(addresses))


def summarise_compact(message):
    headers, _ = parse_message(message)
    date_text = header_value(headers, "date")
    return Header(
        parse_instant(date_text),
        fingerprint(date_text),
        fingerprint(header_value(headers, "from").lower()),
        fingerprint(header_value(headers, "subject")),
        fingerprint(recipient_set(headers)),
    )


def gap_bucket(gap):
    if gap == 0:
        return GAP_BUCKETS[0]
    if gap < 60:
        return GAP_BUCKETS[1]
    if gap % SECONDS_PER_HOUR == 0 and gap <= MAX_SHIFT_HOURS * SECONDS_PER_HOUR:
        return GAP_BUCKETS[2]
    return GAP_BUCKETS[3] if gap < 24 * SECONDS_PER_HOUR else GAP_BUCKETS[4]


def classify_group(headers):
    if len({h.sender_fp for h in headers}) > 1:
        return OTHER_DIFFERENCE
    if len({h.subject_fp for h in headers}) > 1:
        return OTHER_DIFFERENCE
    date_differs = len({h.date_fp for h in headers}) > 1
    return DATE_ONLY if date_differs else NOTHING_DIFFERS


def find_reference(copies, headers):
    """Index of the reference copy: a sent-folder copy if any, else the earliest."""
    dated = [i for i, h in enumerate(headers) if h.instant is not None]
    sent = [i for i in dated if SENT_WORD in copies[i].folder.lower()]
    candidates = sent or dated
    return min(candidates, key=lambda i: (headers[i].instant, copies[i].row))


def copy_offsets(copies, headers):
    """(owner, signed seconds from the reference copy) for each other dated copy."""
    reference = find_reference(copies, headers)
    base = headers[reference].instant
    return [
        (copy.user, header.instant - base)
        for index, (copy, header) in enumerate(zip(copies, headers))
        if index != reference and header.instant is not None
    ]


def same_mailbox_holdings(copies, headers):
    """For each owner holding the body in 2+ different folders: all dates equal?"""
    by_owner = defaultdict(list)
    for copy, header in zip(copies, headers):
        by_owner[copy.user].append((copy.folder, header.date_fp))
    holdings = [items for items in by_owner.values() if len(items) > 1]
    return [
        len({date for _, date in items}) == 1
        for items in holdings
        if len({folder for folder, _ in items}) > 1
    ], len(holdings)


def describe_group(copies, headers):
    instants = [h.instant for h in headers if h.instant is not None]
    gap = max(instants) - min(instants) if len(instants) > 1 else None
    kind = classify_group(headers)
    identical_dates, holdings = same_mailbox_holdings(copies, headers)
    dated_only_date = kind == DATE_ONLY and bool(instants)
    return {
        "kind": kind,
        "bucket": None if gap is None else gap_bucket(gap),
        "same_recipients": len({h.recipients_fp for h in headers}) == 1,
        "offsets": copy_offsets(copies, headers) if dated_only_date else [],
        "identical_dates": identical_dates,
        "holdings": holdings,
        "copies": copies,
    }


def recipient_rows(described):
    rows = []
    for bucket in GAP_BUCKETS:
        members = [item for item in described if item["bucket"] == bucket]
        same = sum(item["same_recipients"] for item in members)
        rows.append(info(f"gap {bucket}: groups", len(members)))
        rule = f"gap {bucket}: same recipient set in all copies"
        rows.append(share_row(rule, same, len(members)))

    nothing = [item for item in described if item["kind"] == NOTHING_DIFFERS]
    same = sum(item["same_recipients"] for item in nothing)
    rows.append(share_row("nothing differs: same recipient set", same, len(nothing)))
    return rows


def remainder_label(seconds):
    for label, limit in REMAINDER_LIMITS:
        if seconds <= limit:
            return label
    return REMAINDER_MORE


def nearest_hours(seconds):
    return (seconds + SECONDS_PER_HOUR // 2) // SECONDS_PER_HOUR


def remainder_rows(described):
    gaps = [abs(seconds) for item in described for _, seconds in item["offsets"]]
    within = [gap for gap in gaps if nearest_hours(gap) <= MAX_SHIFT_HOURS]
    rows = [
        info("date-only groups: copies compared with their reference", len(gaps)),
        info("... gap beyond 14 hours, left out below", len(gaps) - len(within)),
    ]
    selections = [
        ("gaps up to 14 hours", within),
        ("gaps under 1 hour", [gap for gap in within if gap < SECONDS_PER_HOUR]),
    ]
    labels = [name for name, _ in REMAINDER_LIMITS] + [REMAINDER_MORE]
    for title, selected in selections:
        tally = Counter(
            remainder_label(abs(gap - SECONDS_PER_HOUR * nearest_hours(gap)))
            for gap in selected
        )
        rows += [
            info(f"distance to a whole hour, {title}: {label}", tally[label])
            for label in labels
        ]
    return rows


def shifted_copies(described):
    """Owner -> Counter of whole-hour shifts (within 1 minute) of date-only copies."""
    shifts = defaultdict(Counter)
    for item in described:
        for owner, seconds in item["offsets"]:
            hours = nearest_hours(abs(seconds))
            off_by = abs(abs(seconds) - SECONDS_PER_HOUR * hours)
            if 1 <= hours <= MAX_SHIFT_HOURS and off_by <= SHIFT_TOLERANCE_SECONDS:
                shifts[owner][hours if seconds > 0 else -hours] += 1
    return shifts


def spread(values):
    if not values:
        return "n/a"
    middle = statistics.median(values)
    return f"{min(values):.3f} / {middle:.3f} / {max(values):.3f}"


def shift_rows(described):
    shifts = shifted_copies(described)
    totals = {owner: sum(counter.values()) for owner, counter in shifts.items()}
    shares = {o: max(shifts[o].values()) / totals[o] for o in shifts}
    busy = [o for o in shifts if totals[o] >= MIN_COPIES_PER_OWNER]
    top = sorted(totals.values(), reverse=True)[:TOP_OWNERS]
    return [
        info("copies shifted by whole hours (within 1 minute)", sum(totals.values())),
        info("owners with shifted copies", len(shifts)),
        info(
            "owners' share on their most common shift, min / median / max",
            spread(list(shares.values())),
        ),
        info(f"owners with {MIN_COPIES_PER_OWNER}+ shifted copies", len(busy)),
        info(
            "... their share on the most common shift, min / median / max",
            spread([shares[o] for o in busy]),
        ),
        share_row(
            f"shifted copies held by the {TOP_OWNERS} owners with the most",
            sum(top),
            sum(totals.values()),
        ),
    ]


def mailbox_rows(described):
    flags = [flag for item in described for flag in item["identical_dates"]]
    holdings = sum(item["holdings"] for item in described)
    return [
        info("owner holds the body twice or more", holdings),
        info("... in 2 or more different folders", len(flags)),
        share_row("... with identical Date text in all copies", sum(flags), len(flags)),
    ]


def check(args):
    groups, capped = load_groups()
    wanted = {copy.row for copies in groups for copy in copies}
    summaries = read_summaries(wanted, args.block_mb, summarise_compact)
    if len(summaries) != len(wanted):
        raise SystemExit("The index does not match the CSV. Rerun raw_index.")

    described = [
        describe_group(copies, [summaries[copy.row] for copy in copies])
        for copies in groups
    ]
    del summaries
    undated = sum(item["bucket"] is None for item in described)
    table = [
        info("groups held by 2 or more users", len(groups)),
        info("groups capped at 20 rows", capped),
        info("groups with fewer than 2 dated copies", undated),
    ]
    table += recipient_rows(described) + remainder_rows(described)
    table += shift_rows(described) + mailbox_rows(described)
    written = write_audit_file(pick_groups(described), args.block_mb)
    table += [
        info("audit file rows written", written),
        info("audit file (local only)", f"data/audit/{AUDIT_PATH.name}"),
    ]

    return {
        "expects": "Groups with whole-hour gaps show one owner's clock, not a re-send.",
        "found": f"{len(groups):,} groups; {written:,} audit rows written.",
        "table": table,
        "details": {"block_mb": args.block_mb, "groups": len(groups)},
    }


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block-mb", type=int, default=DEFAULT_BLOCK_MB)
    return parser.parse_args()


if __name__ == "__main__":
    run_check(NAME, partial(check, parse_args()))
