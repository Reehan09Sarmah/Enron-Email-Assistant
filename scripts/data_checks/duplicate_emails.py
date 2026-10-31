"""C3: how many emails are exact copies, with and without the File: line."""

from collections import Counter

from scripts.data_checks.common import (
    ALL_FILES,
    SPLIT_FILES,
    fingerprint,
    read_batches,
)
from scripts.data_checks.report import load_details, run_check

NAME = "duplicate_emails"
COLUMNS = ["user", "email"]
FILE_LINE_PREFIX = "File:"
LARGEST_GROUPS = 10


def files_to_scan():
    if load_details("file_relationship")["all_splits_hold_same_emails"]:
        return SPLIT_FILES["dev"], "dev only"
    return ALL_FILES, "all splits"


def remove_file_line(email):
    lines = email.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith(FILE_LINE_PREFIX):
            return "".join(lines[:index] + lines[index + 1 :])
    return email


def add_to_group(groups, group, user):
    groups["rows"][group] += 1
    groups["users"].setdefault(group, set()).add(user)


def new_groups():
    return {"rows": Counter(), "users": {}}


def scan_files(file_names):
    full = new_groups()
    without_file = new_groups()
    rows = 0

    for file_name in file_names:
        for _, batch in read_batches(file_name, COLUMNS):
            for user, email in zip(batch["user"], batch["email"]):
                rows += 1
                add_to_group(full, fingerprint(email), user)
                add_to_group(without_file, fingerprint(remove_file_line(email)), user)

    return rows, full, without_file


def summarise(groups):
    rows_by_group = groups["rows"]
    users_by_group = groups["users"]
    duplicates = [group for group, size in rows_by_group.items() if size > 1]
    several_users = sum(1 for group in duplicates if len(users_by_group[group]) > 1)
    largest = sorted(
        ((rows_by_group[group], len(users_by_group[group])) for group in duplicates),
        reverse=True,
    )[:LARGEST_GROUPS]
    return {
        "unique": len(rows_by_group),
        "duplicate_groups": len(duplicates),
        "groups_with_several_users": several_users,
        "groups_within_one_user": len(duplicates) - several_users,
        "largest_groups": largest,
    }


def table_rows(label, summary):
    counts = [
        ("unique fingerprints", summary["unique"]),
        ("duplicate groups", summary["duplicate_groups"]),
        ("groups with more than one user", summary["groups_with_several_users"]),
        ("groups within one user", summary["groups_within_one_user"]),
    ]
    return [(f"{label}: {name}", "info", f"{n:,}", None) for name, n in counts]


def check():
    file_names, scope = files_to_scan()
    rows, full, without_file = scan_files(file_names)
    summaries = {
        "full text": summarise(full),
        "without File: line": summarise(without_file),
    }

    table = []
    for label, summary in summaries.items():
        table += table_rows(label, summary)

    return {
        "expects": "No expectation; this check only reports duplicates "
        f"(scope: {scope}).",
        "found": f"{rows:,} rows scanned. Full text: "
        f"{summaries['full text']['duplicate_groups']:,} duplicate groups; "
        f"without File: line: "
        f"{summaries['without File: line']['duplicate_groups']:,}.",
        "table": table,
        "sections": {
            f"10 largest groups, {label} (group size, distinct users)": [
                f"({size}, {users})" for size, users in summary["largest_groups"]
            ]
            or ["none"]
            for label, summary in summaries.items()
        },
        "details": {"scope": scope, "rows": rows, "summaries": summaries},
    }


if __name__ == "__main__":
    run_check(NAME, check)
