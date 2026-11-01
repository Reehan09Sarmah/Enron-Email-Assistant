"""R3: match EnronQA dev emails to the raw CSV rows through the file path."""

from collections import Counter

import pyarrow as pa
import pyarrow.compute as pc

from scripts.data_checks.common import (
    SPLIT_FILES,
    collapse_whitespace,
    fingerprint,
    read_batches,
    read_index_table,
)
from scripts.data_checks.index_tables import (
    BUCKETS,
    bucket_label,
    message_id_groups,
)
from scripts.data_checks.report import expect_zero, info, run_check, share_row

NAME = "join_to_enronqa"
DEV_COLUMNS = ["user", "path", "email"]
INDEX_COLUMNS = [
    "user",
    "file_fp",
    "message_id_fp",
    "body_fp",
    "body_collapsed_fp",
    "row",
]
PATH_FIXES = {
    "raw path has a trailing dot": lambda path: path + ".",
    "EnronQA path has a trailing dot": lambda path: path.removesuffix("."),
    "EnronQA path starts with maildir/": lambda path: path.removeprefix("maildir/"),
    "raw path starts with maildir/": lambda path: "maildir/" + path,
    "backslashes instead of slashes": lambda path: path.replace("\\", "/"),
    "different letter case": lambda path: path.lower(),
}
NO_PATTERN = "no pattern found"
UNKNOWN_USER = "user folder not in the raw data"


def body_after_ruler(email):
    parts = email.split("\n", 5)
    return parts[5] if len(parts) > 5 else ""


def read_dev_table():
    columns = {
        "path_fp": [],
        "qa_user": [],
        "qa_path": [],
        "qa_body_fp": [],
        "qa_body_collapsed_fp": [],
    }
    for file_name in SPLIT_FILES["dev"]:
        for _, batch in read_batches(file_name, DEV_COLUMNS):
            for user, path, email in zip(batch["user"], batch["path"], batch["email"]):
                body = body_after_ruler(email)
                columns["path_fp"].append(fingerprint(path))
                columns["qa_user"].append(user)
                columns["qa_path"].append(path)
                columns["qa_body_fp"].append(fingerprint(body))
                columns["qa_body_collapsed_fp"].append(
                    fingerprint(collapse_whitespace(body))
                )
    return pa.table(columns)


def count_true(mask):
    return pc.sum(pc.cast(mask, pa.int64())).as_py() or 0


def classify_unmatched(path, raw_files, raw_users):
    for name, fix in PATH_FIXES.items():
        fixed = fix(path)
        if fixed != path and fingerprint(fixed) in raw_files:
            return name
    if path.split("/", 1)[0] not in raw_users:
        return UNKNOWN_USER
    return NO_PATTERN


def count_difference_patterns(unmatched, raw):
    raw_files = set(raw["file_fp"].to_pylist())
    raw_users = set(raw["user"].to_pylist())
    return Counter(
        classify_unmatched(path, raw_files, raw_users)
        for path in unmatched["qa_path"].to_pylist()
    )


def count_other_user_copies(matched, raw):
    with_id = matched.filter(pc.is_valid(matched["message_id_fp"]))
    groups = message_id_groups(raw).select(["message_id_fp", "user_count_distinct"])
    joined = with_id.join(groups, keys="message_id_fp")

    others = [users - 1 for users in joined["user_count_distinct"].to_pylist()]
    tally = Counter("0" if n == 0 else bucket_label(n) for n in others)
    return with_id.num_rows, tally


def count_raw_not_in_enronqa(raw, dev):
    users = pa.array(sorted(set(dev["qa_user"].to_pylist())))
    in_users = pc.is_in(raw["user"], value_set=users)
    in_enronqa = pc.is_in(raw["file_fp"], value_set=dev["path_fp"].combine_chunks())

    from_users = count_true(in_users)
    both = count_true(pc.and_(in_users, in_enronqa))
    return from_users, from_users - both


def join_dev_to_raw(dev, raw):
    raw_columns = raw.select(
        ["file_fp", "message_id_fp", "body_fp", "body_collapsed_fp"]
    )
    joined = dev.join(
        raw_columns, keys="path_fp", right_keys="file_fp", join_type="left outer"
    )
    matched = joined.filter(pc.is_valid(joined["body_fp"]))
    unmatched = joined.filter(pc.is_null(joined["body_fp"]))
    return matched, unmatched


def match_rows(dev, raw, matched, unmatched):
    duplicate_files = raw.num_rows - pc.count_distinct(raw["file_fp"]).as_py()
    rows = [
        expect_zero("raw rows sharing a file value with another row", duplicate_files),
        info("EnronQA dev keys", dev.num_rows),
        share_row("keys matching a raw file value", matched.num_rows, dev.num_rows),
    ]
    for pattern, number in count_difference_patterns(unmatched, raw).most_common():
        rows.append(info(f"unmatched: {pattern}", number))
    return rows


def body_rows(matched):
    same = pc.equal(matched["qa_body_fp"], matched["body_fp"])
    same_collapsed = pc.equal(
        matched["qa_body_collapsed_fp"], matched["body_collapsed_fp"]
    )
    return [
        share_row("matched, identical body", count_true(same), matched.num_rows),
        share_row(
            "matched, identical body after collapsing whitespace",
            count_true(same_collapsed),
            matched.num_rows,
        ),
    ]


def copy_rows(matched, raw):
    with_id, other_users = count_other_user_copies(matched, raw)
    rows = [
        info("matched with a Message-ID", with_id),
        info("matched with no Message-ID", matched.num_rows - with_id),
    ]
    for bucket in ["0"] + [label for label, _, _ in BUCKETS]:
        rows.append(info(f"other users holding a copy: {bucket}", other_users[bucket]))
    return rows


def check():
    dev = read_dev_table()
    raw = read_index_table(INDEX_COLUMNS)
    matched, unmatched = join_dev_to_raw(dev, raw)
    from_users, not_in_enronqa = count_raw_not_in_enronqa(raw, dev)

    table = match_rows(dev, raw, matched, unmatched)
    table += body_rows(matched)
    table += copy_rows(matched, raw)
    table += [
        info("raw messages from the EnronQA users", from_users),
        info("... of which not in EnronQA dev", not_in_enronqa),
    ]

    return {
        "expects": "Every EnronQA dev key matches a raw file value with the same body.",
        "found": f"{matched.num_rows:,} of {dev.num_rows:,} keys match a raw row.",
        "table": table,
        "details": {"matched": matched.num_rows, "dev_keys": dev.num_rows},
    }


if __name__ == "__main__":
    run_check(NAME, check)
