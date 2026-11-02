"""R5: how many raw bodies are held by several users or sit in sent folders."""

from collections import Counter

import pyarrow as pa
import pyarrow.compute as pc

from scripts.data_checks.common import (
    SPLIT_FILES,
    fingerprint,
    read_batches,
    read_index_table,
)
from scripts.data_checks.index_tables import BUCKETS, bucket_label
from scripts.data_checks.raw_copies import LARGEST_GROUPS, bucket_rows
from scripts.data_checks.report import info, run_check

NAME = "body_copies"
COLUMNS = ["row", "user", "file_fp", "folder", "body_collapsed_fp"]
SENT_WORD = "sent"


def read_dev_path_fingerprints():
    fingerprints = set()
    for file_name in SPLIT_FILES["dev"]:
        for _, batch in read_batches(file_name, ["path"]):
            fingerprints.update(fingerprint(path) for path in batch["path"])
    return fingerprints


def add_sent_flag(index):
    lowered = pc.utf8_lower(index["folder"])
    is_sent = pc.cast(pc.match_substring(lowered, SENT_WORD), pa.int8())
    return index.append_column("is_sent", is_sent)


def body_groups(index):
    """One row per distinct body: copies, distinct users, sent-folder flags."""
    return index.group_by("body_collapsed_fp").aggregate(
        [
            ("row", "count"),
            ("user", "count_distinct"),
            ("is_sent", "min"),
            ("is_sent", "max"),
        ]
    )


def count_mixed_groups(groups):
    rows = zip(
        groups["row_count"].to_pylist(),
        groups["is_sent_min"].to_pylist(),
        groups["is_sent_max"].to_pylist(),
    )
    return sum(1 for copies, low, high in rows if copies > 1 and low == 0 and high == 1)


def count_sent_folders(index):
    sent_rows = index.filter(pc.equal(index["is_sent"], 1))
    return sent_rows.num_rows, len(pc.unique(sent_rows["folder"]))


def count_dev_other_users(index, groups):
    dev_set = pa.array(sorted(read_dev_path_fingerprints()), pa.binary())
    dev_rows = index.filter(pc.is_in(index["file_fp"], value_set=dev_set))
    user_counts = groups.select(["body_collapsed_fp", "user_count_distinct"])
    joined = dev_rows.select(["body_collapsed_fp"]).join(
        user_counts, keys="body_collapsed_fp"
    )

    others = [users - 1 for users in joined["user_count_distinct"].to_pylist()]
    tally = Counter("0" if n == 0 else bucket_label(n) for n in others)
    return dev_rows.num_rows, tally


def sent_rows(index, groups):
    sent_row_count, sent_folder_count = count_sent_folders(index)
    return [
        info(f"distinct folder names containing '{SENT_WORD}'", sent_folder_count),
        info("rows in those folders", sent_row_count),
        info(
            "bodies in several rows that mix a sent folder with other folders",
            count_mixed_groups(groups),
        ),
    ]


def dev_rows(index, groups):
    matched, tally = count_dev_other_users(index, groups)
    rows = [info("EnronQA dev keys found in the index", matched)]
    for bucket in ["0"] + [label for label, _, _ in BUCKETS]:
        rule = f"dev emails, other users holding a copy: {bucket}"
        rows.append(info(rule, tally[bucket]))
    return rows


def check():
    index = add_sent_flag(read_index_table(COLUMNS))
    groups = body_groups(index)
    copies = groups["row_count"].to_pylist()
    users = groups["user_count_distinct"].to_pylist()
    held_by_several = sum(1 for count in users if count > 1)
    largest = sorted(zip(copies, users), reverse=True)[:LARGEST_GROUPS]

    table = [
        info("rows", index.num_rows),
        info("distinct bodies (whitespace collapsed)", groups.num_rows),
        (
            "bodies held by more than one user",
            "many",
            f"{held_by_several:,}",
            held_by_several > 0,
        ),
    ]
    table += bucket_rows("copies per body", copies)
    table += bucket_rows("distinct users per body", users)
    table += sent_rows(index, groups)
    table += dev_rows(index, groups)

    return {
        "expects": "Many bodies are held by more than one user.",
        "found": f"{held_by_several:,} of {groups.num_rows:,} distinct bodies are "
        "held by more than one user.",
        "table": table,
        "sections": {
            "10 largest groups (group size, distinct users)": [
                f"({size}, {user_count})" for size, user_count in largest
            ]
        },
        "details": {"largest_groups": largest},
    }


if __name__ == "__main__":
    run_check(NAME, check)
