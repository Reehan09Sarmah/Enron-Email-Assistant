"""R1: the basic shape of the raw Enron CSV, read from the index."""

import statistics

import pyarrow as pa
import pyarrow.compute as pc

from scripts.data_checks.common import fingerprint, read_index_table
from scripts.data_checks.report import info, run_check, share_row

NAME = "raw_shape"
COLUMNS = [
    "row",
    "user",
    "message_chars",
    "body_collapsed_fp",
    "has_message_id",
    "has_date",
    "has_from",
    "has_to",
]
EXPECTED_ROWS = 517_401
NEARLY_ALL = 0.99


def count_true(column):
    return pc.sum(pc.cast(column, pa.int64())).as_py() or 0


def count_where_equal(column, value):
    return pc.sum(pc.cast(pc.equal(column, value), pa.int64())).as_py() or 0


def emails_per_user(index):
    counts = index.group_by("user").aggregate([("row", "count")])
    return counts["row_count"].to_pylist()


def check():
    index = read_index_table(COLUMNS)
    rows = index.num_rows
    per_user = emails_per_user(index)
    with_message_id = count_true(index["has_message_id"])
    empty_body = pa.scalar(fingerprint(""), pa.binary())

    table = [
        ("rows", f"about {EXPECTED_ROWS:,}", f"{rows:,}", rows == EXPECTED_ROWS),
        (
            "rows with a Message-ID header",
            "nearly all",
            f"{100 * with_message_id / rows:.1f}% ({with_message_id:,})",
            with_message_id / rows >= NEARLY_ALL,
        ),
        share_row("rows with a Date header", count_true(index["has_date"]), rows),
        share_row("rows with a From header", count_true(index["has_from"]), rows),
        share_row("rows with a To header", count_true(index["has_to"]), rows),
        info("distinct users", len(per_user)),
        info(
            "emails per user min / median / max",
            f"{min(per_user):,} / {statistics.median(per_user):,} / {max(per_user):,}",
        ),
        info("empty messages", count_where_equal(index["message_chars"], 0)),
        info(
            "messages with an empty body",
            count_where_equal(index["body_collapsed_fp"], empty_body),
        ),
    ]

    return {
        "expects": f"About {EXPECTED_ROWS:,} rows, nearly all with a Message-ID.",
        "found": f"{rows:,} rows from {len(per_user):,} users.",
        "table": table,
        "details": {"rows": rows, "with_message_id": with_message_id},
    }


if __name__ == "__main__":
    run_check(NAME, check)
