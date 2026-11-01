"""Count copies of each Message-ID in the raw index, and bucket the counts."""

from collections import Counter

import pyarrow.compute as pc

BUCKETS = [
    ("1", 1, 1),
    ("2", 2, 2),
    ("3-5", 3, 5),
    ("6-10", 6, 10),
    ("over 10", 11, None),
]


def bucket_label(count):
    for label, low, high in BUCKETS:
        if count >= low and (high is None or count <= high):
            return label
    raise ValueError(f"No bucket for {count}")


def count_buckets(counts):
    tally = Counter(bucket_label(count) for count in counts)
    return {label: tally.get(label, 0) for label, _, _ in BUCKETS}


def message_id_groups(index):
    """One row per Message-ID: copies, distinct users and distinct bodies."""
    with_id = index.filter(pc.is_valid(index["message_id_fp"]))
    return with_id.group_by("message_id_fp").aggregate(
        [
            ("row", "count"),
            ("user", "count_distinct"),
            ("body_fp", "count_distinct"),
            ("body_collapsed_fp", "count_distinct"),
        ]
    )
