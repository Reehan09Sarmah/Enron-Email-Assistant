"""R7: how the copies of one body differ in date, sender and subject."""

import argparse
import re
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import timezone
from email.parser import HeaderParser
from email.utils import parsedate_to_datetime
from functools import partial

import pyarrow as pa
import pyarrow.compute as pc

from scripts.data_checks.common import (
    RAW_CSV_PATH,
    collapse_whitespace,
    read_index_table,
)
from scripts.data_checks.raw_csv import DEFAULT_BLOCK_MB, iter_raw_batches
from scripts.data_checks.raw_index import split_message
from scripts.data_checks.report import info, run_check, share_row

NAME = "date_gaps"
COLUMNS = ["row", "user", "body_collapsed_fp"]
EXPECTED_GROUPS = 17_236
MAX_ROWS_PER_GROUP = 20
EXAMPLES_PER_BUCKET = 10
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR
MAX_ZONE_HOURS = 14
RECIPIENT_HEADERS = ["to", "cc", "bcc", "x-to", "x-cc", "x-bcc"]
ZONE_AFTER_TIME = re.compile(r"\d{1,2}:\d{2}(?::\d{2})?\s*(.*)$")

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


def find_shared_rows(index):
    """Index rows whose body is held by 2 or more users."""
    per_body = index.group_by("body_collapsed_fp").aggregate(
        [("user", "count_distinct")]
    )
    shared = per_body.filter(pc.greater_equal(per_body["user_count_distinct"], 2))
    return index.join(
        shared.select(["body_collapsed_fp"]),
        keys="body_collapsed_fp",
        join_type="left semi",
    )


def group_rows(shared_rows):
    """One list of (row, user) per body, first rows kept; also the capped count."""
    by_body = defaultdict(list)
    columns = ["body_collapsed_fp", "row", "user"]
    for body, row, user in zip(*(shared_rows[name].to_pylist() for name in columns)):
        by_body[body].append((row, user))

    groups = [sorted(members) for members in by_body.values()]
    capped = sum(1 for members in groups if len(members) > MAX_ROWS_PER_GROUP)
    return [members[:MAX_ROWS_PER_GROUP] for members in groups], capped


def parse_instant(date_text):
    try:
        moment = parsedate_to_datetime(date_text)
    except (TypeError, ValueError):
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return int(moment.timestamp())


def zone_label(date_text):
    match = ZONE_AFTER_TIME.search(date_text)
    return match.group(1) if match else ""


def summarise_headers(message):
    header_block, body = split_message(message)
    headers = HeaderParser().parsestr(header_block, headersonly=True)

    def value(name):
        return collapse_whitespace(str(headers.get(name, "")))

    date_text = value("date")
    cc, bcc = value("cc"), value("bcc")
    both_present = "cc" in headers and "bcc" in headers
    return {
        "sender": value("from").lower(),
        "subject": value("subject"),
        "date_text": date_text,
        "instant": parse_instant(date_text),
        "zone": zone_label(date_text),
        "body_chars": len(body),
        "filled": {name: bool(value(name)) for name in RECIPIENT_HEADERS},
        "bcc_equals_cc": (cc == bcc) if both_present else None,
    }


def read_summaries(wanted_rows, block_mb):
    ordered = sorted(wanted_rows)
    summaries = {}
    first_row = 0

    for batch in iter_raw_batches(RAW_CSV_PATH, block_mb):
        start = bisect_left(ordered, first_row)
        stop = bisect_left(ordered, first_row + batch.num_rows)
        rows = ordered[start:stop]
        if rows:
            offsets = pa.array([row - first_row for row in rows])
            messages = batch.column("message").take(offsets).to_pylist()
            for row, message in zip(rows, messages):
                summaries[row] = summarise_headers(message or "")
        first_row += batch.num_rows
    return summaries


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
    for (_, user), record in zip(members, records):
        dates_by_user[user].add(record["date_text"])
    return any(len(dates) > 1 for dates in dates_by_user.values())


def describe_group(members, summaries):
    records = [summaries[row] for row, _ in members]
    kind = classify_differences(records)
    is_date_only = kind == DATE_ONLY
    return {
        "kind": kind,
        "bucket": gap_bucket(records) if is_date_only else None,
        "resend": is_date_only and owner_holds_two_dates(members, records),
        "length_differs": len({record["body_chars"] for record in records}) > 1,
        "rows": [row for row, _ in members],
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
    groups, capped = group_rows(find_shared_rows(read_index_table(COLUMNS)))
    wanted = {row for members in groups for row, _ in members}
    summaries = read_summaries(wanted, args.block_mb)
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
