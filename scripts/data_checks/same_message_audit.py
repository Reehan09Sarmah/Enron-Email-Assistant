"""Write the hand-audit CSV: real header values for sampled groups, local file only."""

import csv
import random

from scripts.data_checks.common import ROOT
from scripts.data_checks.shared_groups import (
    header_value,
    parse_message,
    read_summaries,
)

AUDIT_PATH = ROOT / "data" / "audit" / "same_message_audit.csv"
AUDIT_SEED = 11
AUDIT_QUOTAS = {
    "whole hours 1-14": 30,
    "other under 24 hours": 30,
    "1 day or more": 20,
}
AUDIT_COLUMNS = [
    "audit_group",
    "gap_bucket",
    "owner",
    "folder",
    "sender",
    "subject",
    "date",
    "to",
    "cc",
    "rex_label",
]
FORMULA_STARTS = ("=", "+", "-", "@")


def pick_groups(described):
    """(bucket, copies) pairs: a seeded sample of groups for each quota."""
    chooser = random.Random(AUDIT_SEED)
    picked = []
    for bucket, quota in AUDIT_QUOTAS.items():
        candidates = [item for item in described if item["bucket"] == bucket]
        for item in chooser.sample(candidates, min(quota, len(candidates))):
            picked.append((bucket, item["copies"]))
    return picked


def summarise_audit_fields(message):
    headers, _ = parse_message(message)
    names = ["from", "subject", "date", "to", "cc"]
    return [header_value(headers, name) for name in names]


def safe_cell(value):
    return " " + value if value.startswith(FORMULA_STARTS) else value


def write_audit_file(picked, block_mb):
    """Write one row per copy; return the number of rows written."""
    wanted = {copy.row for _, copies in picked for copy in copies}
    fields = read_summaries(wanted, block_mb, summarise_audit_fields)

    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = 0
    with open(AUDIT_PATH, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(AUDIT_COLUMNS)
        for number, (bucket, copies) in enumerate(picked, start=1):
            for copy in copies:
                values = [safe_cell(value) for value in fields[copy.row]]
                writer.writerow([number, bucket, copy.user, copy.folder, *values, ""])
                rows += 1
    return rows
