"""C1: every row of every file has the expected shape."""

from collections import Counter

from scripts.data_checks.common import ALL_FILES, read_batches
from scripts.data_checks.report import run_check

NAME = "rows_well_formed"
LENGTH_COLUMNS = [
    "questions",
    "rephrased_questions",
    "gold_answers",
    "alternate_answers",
    "incorrect_answers",
    "gold_rationales",
    "alternate_rationales",
    "include_email",
]
COLUMNS = ["email", "path", "user", "questions_count"] + LENGTH_COLUMNS
EXAMPLES_PER_RULE = 5


def is_blank(value):
    return value is None or (isinstance(value, str) and not value.strip())


def broken_rules(row):
    broken = []

    for column in LENGTH_COLUMNS:
        values = row[column]
        if values is None or len(values) != row["questions_count"]:
            broken.append(f"len({column}) == questions_count")

    for column in ["email", "path", "user"]:
        if is_blank(row[column]):
            broken.append(f"{column} is empty")
    if any(is_blank(question) for question in row["questions"] or []):
        broken.append("a question is empty")
    if any(is_blank(answer) for answer in row["gold_answers"] or []):
        broken.append("a gold answer is empty")

    if not (row["email"] or "").startswith("Subject:"):
        broken.append("email starts with Subject:")
    if not (row["path"] or "").startswith(f"{row['user']}/"):
        broken.append("path starts with user/")
    return broken


def all_rule_names():
    names = [f"len({column}) == questions_count" for column in LENGTH_COLUMNS]
    names += [f"{column} is empty" for column in ["email", "path", "user"]]
    names += ["a question is empty", "a gold answer is empty"]
    names += ["email starts with Subject:", "path starts with user/"]
    return names


def scan_files():
    violations = Counter()
    examples = {name: [] for name in all_rule_names()}
    rows_per_file = {}

    for file_name in ALL_FILES:
        rows_per_file[file_name] = 0
        for first_row, batch in read_batches(file_name, COLUMNS):
            for offset in range(len(batch["path"])):
                row = {column: batch[column][offset] for column in COLUMNS}
                rows_per_file[file_name] += 1
                for rule in broken_rules(row):
                    violations[rule] += 1
                    if len(examples[rule]) < EXAMPLES_PER_RULE:
                        examples[rule].append(f"({file_name}, {first_row + offset})")
    return violations, examples, rows_per_file


def check():
    violations, examples, rows_per_file = scan_files()

    table = [
        (rule, "0 rows break it", f"{violations[rule]} rows", violations[rule] == 0)
        for rule in all_rule_names()
    ]
    broken_count = sum(1 for rule in all_rule_names() if violations[rule])
    total_rows = sum(rows_per_file.values())
    return {
        "expects": "No row breaks any of the 15 rules below.",
        "found": f"{total_rows:,} rows read; {broken_count} of 15 rules are broken.",
        "table": table,
        "sections": {
            "Example rows (file name, row index), up to 5 per rule": [
                f"{rule}: {', '.join(rows)}"
                for rule, rows in examples.items()
                if rows
            ]
            or ["none, no rule is broken"]
        },
        "details": {"rows_per_file": rows_per_file, "examples": examples},
    }


if __name__ == "__main__":
    run_check(NAME, check)
