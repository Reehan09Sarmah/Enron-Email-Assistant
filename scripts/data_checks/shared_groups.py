"""Find the body groups held by 2+ users and read their headers from the CSV."""

import re
import sys
from bisect import bisect_left
from collections import defaultdict
from datetime import timezone
from email.parser import HeaderParser
from email.utils import parsedate_to_datetime
from typing import NamedTuple

import pyarrow as pa
import pyarrow.compute as pc

from scripts.data_checks.common import (
    RAW_CSV_PATH,
    collapse_whitespace,
    read_index_table,
)
from scripts.data_checks.raw_csv import iter_raw_batches
from scripts.data_checks.raw_index import split_message

INDEX_COLUMNS = ["row", "user", "folder", "body_collapsed_fp"]
MAX_ROWS_PER_GROUP = 20
ZONE_AFTER_TIME = re.compile(r"\d{1,2}:\d{2}(?::\d{2})?\s*(.*)$")


class Copy(NamedTuple):
    row: int
    user: str
    folder: str


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
    """One list of copies per body, first rows kept; also the capped count."""
    by_body = defaultdict(list)
    columns = ["body_collapsed_fp", "row", "user", "folder"]
    for body, row, user, folder in zip(
        *(shared_rows[name].to_pylist() for name in columns)
    ):
        by_body[body].append(Copy(row, sys.intern(user), sys.intern(folder)))

    groups = sorted(sorted(members) for members in by_body.values())
    capped = sum(1 for members in groups if len(members) > MAX_ROWS_PER_GROUP)
    return [members[:MAX_ROWS_PER_GROUP] for members in groups], capped


def load_groups():
    """Read the index, build the groups, and give the index memory back."""
    index = read_index_table(INDEX_COLUMNS)
    groups = group_rows(find_shared_rows(index))
    pa.default_memory_pool().release_unused()
    return groups


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


def parse_message(message):
    header_block, body = split_message(message)
    headers = HeaderParser().parsestr(header_block, headersonly=True)
    return headers, body


def header_value(headers, name):
    return collapse_whitespace(str(headers.get(name, "")))


def read_summaries(wanted_rows, block_mb, summarise):
    """Stream the CSV once and summarise only the wanted rows."""
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
                summaries[row] = summarise(message or "")
        first_row += batch.num_rows
    return summaries
