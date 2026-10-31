"""C4: ids are unique and every email starts with the expected header block."""

import statistics
from collections import Counter

from scripts.data_checks.common import SPLIT_FILES, read_batches
from scripts.data_checks.report import run_check

NAME = "ids_and_headers"
COLUMNS = ["user", "path", "email"]
SPLITS = list(SPLIT_FILES)
HEADER_LABELS = ["Subject:", "Sender:", "Recipients:", "File:"]
EXPECTED_USERS = 150
EXPECTED_PER_USER = (5, 244, 5485)


def parse_header(email):
    """Return {label: value} for the four header lines, or None if malformed."""
    lines = email.split("\n", 5)[:5]
    if len(lines) < 5:
        return None

    labelled = all(line.startswith(label) for line, label in zip(lines, HEADER_LABELS))
    ruler = lines[4].strip()
    if not labelled or not ruler or set(ruler) != {"="}:
        return None
    return {
        label: line[len(label) :].strip()
        for line, label in zip(lines, HEADER_LABELS)
    }


def scan_split(split):
    paths = set()
    keys = set()
    emails_per_user = Counter()
    counts = Counter()

    for file_name in SPLIT_FILES[split]:
        for _, batch in read_batches(file_name, COLUMNS):
            for user, path, email in zip(batch["user"], batch["path"], batch["email"]):
                counts["rows"] += 1
                paths.add(path)
                keys.add((user, path))
                emails_per_user[user] += 1
                count_header(counts, parse_header(email), path)

    return {
        "paths": paths,
        "keys": keys,
        "emails_per_user": emails_per_user,
        "counts": counts,
    }


def count_header(counts, header, path):
    if header is None:
        counts["bad_header"] += 1
        return
    counts["good_header"] += 1
    counts["file_contains_path"] += path in header["File:"]
    counts["empty_recipients"] += header["Recipients:"] == ""
    counts["recipients_with_at"] += "@" in header["Recipients:"]


def per_user_summary(emails_per_user):
    sizes = list(emails_per_user.values())
    return (len(sizes), min(sizes), statistics.median(sizes), max(sizes))


def expect_zero(rule, found):
    return (rule, 0, f"{found:,}", found == 0)


def share_row(rule, count, total):
    return (rule, "info", f"{100 * count / total:.1f}% ({count:,} of {total:,})", None)


def check():
    scans = {split: scan_split(split) for split in SPLITS}
    total_rows = sum(scan["counts"]["rows"] for scan in scans.values())
    all_paths = set().union(*(scan["paths"] for scan in scans.values()))
    all_keys = set().union(*(scan["keys"] for scan in scans.values()))
    counts = sum((scan["counts"] for scan in scans.values()), Counter())

    table = [
        expect_zero("repeated paths, all rows", total_rows - len(all_paths)),
        expect_zero("repeated (user, path), all rows", total_rows - len(all_keys)),
    ]
    for split, scan in scans.items():
        rows = scan["counts"]["rows"]
        table.append(expect_zero(f"{split}: repeated paths", rows - len(scan["paths"])))
        table.append(
            expect_zero(f"{split}: repeated (user, path)", rows - len(scan["keys"]))
        )
        found = per_user_summary(scan["emails_per_user"])
        table.append(
            (
                f"{split}: users / emails per user min / median / max",
                " / ".join(f"{n:,}" for n in (EXPECTED_USERS, *EXPECTED_PER_USER)),
                " / ".join(f"{n:,}" for n in found),
                found == (EXPECTED_USERS, *EXPECTED_PER_USER),
            )
        )

    good = counts["good_header"]
    table += [
        expect_zero("emails without the expected header block", counts["bad_header"]),
        share_row("File: value contains path", counts["file_contains_path"], good),
        share_row("Recipients value is empty", counts["empty_recipients"], good),
        share_row("Recipients value contains @", counts["recipients_with_at"], good),
    ]

    return {
        "expects": "Unique paths and (user, path), 150 users with 5 / 244 / 5,485 "
        "emails (min / median / max), and the same four-line header on every email.",
        "found": f"{total_rows:,} rows read; {counts['bad_header']:,} without the "
        "expected header block.",
        "table": table,
        "details": {"counts": dict(counts), "rows": total_rows},
    }


if __name__ == "__main__":
    run_check(NAME, check)
