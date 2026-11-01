"""R2: how many raw messages are copies of one Message-ID."""

from scripts.data_checks.common import read_index_table
from scripts.data_checks.index_tables import count_buckets, message_id_groups
from scripts.data_checks.report import info, run_check

NAME = "raw_copies"
COLUMNS = ["row", "user", "message_id_fp", "body_fp", "body_collapsed_fp"]
LARGEST_GROUPS = 10


def bucket_rows(label, counts):
    return [
        info(f"{label}: {bucket}", number)
        for bucket, number in count_buckets(counts).items()
    ]


def count_groups_with_different_bodies(groups, copies, column):
    distinct_bodies = groups[column].to_pylist()
    return sum(1 for n, bodies in zip(copies, distinct_bodies) if n > 1 and bodies > 1)


def check():
    index = read_index_table(COLUMNS)
    groups = message_id_groups(index)
    copies = groups["row_count"].to_pylist()
    users = groups["user_count_distinct"].to_pylist()
    with_copies = sum(1 for n in copies if n > 1)
    largest = sorted(zip(copies, users), reverse=True)[:LARGEST_GROUPS]

    table = [
        info("rows", index.num_rows),
        info("distinct Message-IDs", groups.num_rows),
        (
            "Message-IDs that appear in more than one row",
            "many",
            f"{with_copies:,}",
            with_copies > 0,
        ),
    ]
    table += bucket_rows("copies per Message-ID", copies)
    table += bucket_rows("distinct users per Message-ID", users)
    table += [
        info(
            "copied Message-IDs whose body differs",
            count_groups_with_different_bodies(
                groups, copies, "body_fp_count_distinct"
            ),
        ),
        info(
            "copied Message-IDs whose body differs after collapsing whitespace",
            count_groups_with_different_bodies(
                groups, copies, "body_collapsed_fp_count_distinct"
            ),
        ),
    ]

    return {
        "expects": "Many Message-IDs appear in more than one row.",
        "found": f"{groups.num_rows:,} distinct Message-IDs in {index.num_rows:,} "
        f"rows; {with_copies:,} have copies.",
        "table": table,
        "sections": {
            "10 largest groups (group size, distinct users)": [
                f"({size}, {user_count})" for size, user_count in largest
            ]
            or ["none"]
        },
        "details": {"largest_groups": largest},
    }


if __name__ == "__main__":
    run_check(NAME, check)
