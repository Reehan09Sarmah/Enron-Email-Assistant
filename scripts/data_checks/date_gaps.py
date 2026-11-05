"""R7: how the copies of one body differ in date, sender and subject."""

import argparse
from collections import Counter, defaultdict
from functools import partial

from scripts.data_checks.raw_csv import DEFAULT_BLOCK_MB
from scripts.data_checks.report import info, run_check, share_row
from scripts.data_checks.shared_groups import (
    MAX_ROWS_PER_GROUP,
    header_value,
    load_groups,
    parse_instant,
    parse_message,
    read_summaries,
    zone_label,
)

NAME = "date_gaps"
EXPECTED_GROUPS = 17_236
EXAMPLES_PER_BUCKET = 10
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR
MAX_ZONE_HOURS = 14
RECIPIENT_HEADERS = ["to", "cc", "bcc", "x-to", "x-cc", "x-bcc"]

NOTHING = "nothing differs"
DATE_ONLY = "date only"
SENDER_SUBJECT_ONLY = "sender and/or subject only"
DATE_AND_OTHER = "date plus sender/subject"
KINDS = [NOTHING, DATE_ONLY, SENDER_SUBJECT_ONLY, DATE_AND_OTHER]

ZERO = "0 s"
UNDER_MINUTE = "under 1 minute"
HOURS_SAME_ZONE = "whole hours 1-14, same zone label"
HOURS_OTHER_ZONE = "whole hours 1-14, different zone labels"
OTHER_UNDER_DAY = "other under 24 hours"
DAY_OR_MORE = "1 day or more"
NOT_PARSED = "fewer than 2 dates parsed"
GAP_BUCKETS = [
    ZERO,
    UNDER_MINUTE,
    HOURS_SAME_ZONE,
    HOURS_OTHER_ZONE,
    OTHER_UNDER_DAY,
    DAY_OR_MORE,
    NOT_PARSED,
]


def summarise_headers(message):
    headers, body = parse_message(message)
    date_text = header_value(headers, "date")
    cc, bcc = header_value(headers, "cc"), header_value(headers, "bcc")
    both_present = "cc" in headers and "bcc" in headers
    filled = {name: bool(header_value(headers, name)) for name in RECIPIENT_HEADERS}
    return {
        "sender": header_value(headers, "from").lower(),
        "subject": header_value(headers, "subject"),
        "date_text": date_text,
        "instant": parse_instant(date_text),
        "zone": zone_label(date_text),
        "body_chars": len(body),
        "filled": filled,
        "bcc_equals_cc": (cc == bcc) if both_present else None,
    }


def classify_differences(records):
    date_differs = len({record["date_text"] for record in records}) > 1
    other_differs = (
        len({record["sender"] for record in records}) > 1
        or len({record["subject"] for record in records}) > 1
    )
    if date_differs and other_differs:
        return DATE_AND_OTHER
    if date_differs:
        return DATE_ONLY
    return SENDER_SUBJECT_ONLY if other_differs else NOTHING


def gap_bucket(records):
    instants = [r["instant"] for r in records if r["instant"] is not None]
    if len(instants) < 2:
        return NOT_PARSED
    gap = max(instants) - min(instants)
    whole_hours = gap % SECONDS_PER_HOUR == 0
    within_zone_range = SECONDS_PER_HOUR <= gap <= MAX_ZONE_HOURS * SECONDS_PER_HOUR

    if gap == 0:
        return ZERO
    if gap < 60:
        return UNDER_MINUTE
    if whole_hours and within_zone_range:
        same_zone = len({record["zone"] for record in records}) == 1
        return HOURS_SAME_ZONE if same_zone else HOURS_OTHER_ZONE
    return OTHER_UNDER_DAY if gap < SECONDS_PER_DAY else DAY_OR_MORE


def owner_holds_two_dates(members, records):
    dates_by_user = defaultdict(set)
    for copy, record in zip(members, records):
        dates_by_user[copy.user].add(record["date_text"])
    return any(len(dates) > 1 for dates in dates_by_user.values())


def describe_group(members, summaries):
    records = [summaries[copy.row] for copy in members]
    kind = classify_differences(records)
    is_date_only = kind == DATE_ONLY
    return {
        "kind": kind,
        "bucket": gap_bucket(records) if is_date_only else None,
        "resend": is_date_only and owner_holds_two_dates(members, records),
        "length_differs": len({record["body_chars"] for record in records}) > 1,
        "rows": [copy.row for copy in members],
    }


def difference_rows(described):
    kinds = Counter(item["kind"] for item in described)
    return [
        share_row(f"groups: {kind}", kinds[kind], len(described)) for kind in KINDS
    ]


def gap_rows(date_only):
    buckets = Counter(item["bucket"] for item in date_only)
    rows = [info("date-only groups", len(date_only))]
    rows += [info(f"largest date gap: {name}", buckets[name]) for name in GAP_BUCKETS]
    rows += [
        share_row(
            "date-only groups where one mailbox owner holds two dates",
            sum(item["resend"] for item in date_only),
            len(date_only),
        ),
        share_row(
            "date-only groups where the body length differs",
            sum(item["length_differs"] for item in date_only),
            len(date_only),
        ),
    ]
    return rows


def header_rows(records):
    rows = []
    for name in RECIPIENT_HEADERS:
        filled = sum(record["filled"][name] for record in records)
        rows.append(share_row(f"rows with a non-empty {name}", filled, len(records)))

    with_both = [r["bcc_equals_cc"] for r in records if r["bcc_equals_cc"] is not None]
    rule = "rows with both Bcc and Cc: Bcc equals Cc"
    rows.append(share_row(rule, sum(with_both), len(with_both)))
    failures = sum(record["instant"] is None for record in records)
    rows.append(share_row("rows whose Date failed to parse", failures, len(records)))
    return rows


def collect_examples(described):
    examples = {}
    for name in GAP_BUCKETS:
        rows = [item["rows"] for item in described if item["bucket"] == name]
        examples[name] = rows[:EXAMPLES_PER_BUCKET]
    return examples


def check(args):
    groups, capped = load_groups()
    wanted = {copy.row for members in groups for copy in members}
    summaries = read_summaries(wanted, args.block_mb, summarise_headers)
    if len(summaries) != len(wanted):
        raise SystemExit("The index does not match the CSV. Rerun raw_index.")

    described = [describe_group(members, summaries) for members in groups]
    date_only = [item for item in described if item["kind"] == DATE_ONLY]
    table = [
        (
            "groups held by 2 or more users",
            f"{EXPECTED_GROUPS:,} (from R5)",
            f"{len(groups):,}",
            len(groups) == EXPECTED_GROUPS,
        ),
        info(f"groups capped at {MAX_ROWS_PER_GROUP} rows", capped),
        info("rows read", len(summaries)),
    ]
    table += difference_rows(described) + gap_rows(date_only)
    table += header_rows(list(summaries.values()))

    return {
        "expects": f"{EXPECTED_GROUPS:,} groups; the date text differs in about 22%.",
        "found": f"{len(groups):,} groups; {len(date_only):,} differ in the date only.",
        "table": table,
        "details": {
            "block_mb": args.block_mb,
            "groups": len(groups),
            "capped_groups": capped,
            "example_rows": collect_examples(described),
        },
    }


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block-mb", type=int, default=DEFAULT_BLOCK_MB)
    return parser.parse_args()


if __name__ == "__main__":
    run_check(NAME, partial(check, parse_args()))
