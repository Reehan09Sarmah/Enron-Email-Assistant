"""Run a check, print its summary in a fixed order and save it as JSON."""

import json
import time
from datetime import date

from scripts.data_checks.common import DATA_COMMIT, REPORT_DIR, peak_memory_mb

RESULT_LABELS = {True: "ok", False: "FINDING", None: "info"}


def format_count(value):
    return f"{value:,}" if isinstance(value, int) else str(value)


def expect_zero(rule, found):
    return (rule, 0, format_count(found), found == 0)


def info(rule, found):
    return (rule, "info", format_count(found), None)


def share_row(rule, count, total):
    percent = 100 * count / total if total else 0
    return info(rule, f"{percent:.1f}% ({count:,} of {total:,})")


def run_check(name, check):
    """check() returns a dict: expects, found, table, sections, details."""
    started = time.perf_counter()
    result = check()
    seconds = time.perf_counter() - started
    memory_mb = peak_memory_mb()

    print_summary(name, result, memory_mb, seconds)
    save_json(name, result, memory_mb, seconds)


def print_summary(name, result, memory_mb, seconds):
    print(f"CHECK {name}")
    print(f"\nExpected: {result['expects']}")
    print(f"Found: {result['found']}")
    print_table(result["table"])
    for title, lines in result.get("sections", {}).items():
        print(f"\n{title}")
        for line in lines:
            print(f"  {line}")
    print(f"\nPeak memory: {memory_mb:.0f} MB. Time: {seconds:.1f} s.")


def print_table(table):
    rule_width = max(len(row[0]) for row in table)
    expected_width = max(len(str(row[1])) for row in table)
    found_width = max(len(str(row[2])) for row in table)

    print()
    for rule, expected, found, matches in table:
        print(
            f"{rule.ljust(rule_width)}  {str(expected).ljust(expected_width)}  "
            f"{str(found).ljust(found_width)}  {RESULT_LABELS[matches]}"
        )


def save_json(name, result, memory_mb, seconds):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    saved = {
        "check": name,
        "date": date.today().isoformat(),
        "data_commit": DATA_COMMIT,
        "peak_memory_mb": round(memory_mb),
        "seconds": round(seconds, 1),
        "expects": result["expects"],
        "found": result["found"],
        "table": [
            {"rule": rule, "expected": str(expected), "found": str(found),
             "result": RESULT_LABELS[matches]}
            for rule, expected, found, matches in result["table"]
        ],
        "sections": result.get("sections", {}),
        "details": result.get("details", {}),
    }
    path = REPORT_DIR / f"{name}.json"
    path.write_text(json.dumps(saved, indent=2), encoding="utf-8")


def load_details(name):
    path = REPORT_DIR / f"{name}.json"
    if not path.exists():
        raise SystemExit(f"Run the {name} check first: {path} is missing.")
    return json.loads(path.read_text(encoding="utf-8"))["details"]
