"""C2: how train, dev and test relate to each other."""

from scripts.data_checks.common import SPLIT_FILES, fingerprint, read_batches
from scripts.data_checks.report import run_check

NAME = "file_relationship"
COLUMNS = ["user", "path", "email", "questions"]
SPLITS = list(SPLIT_FILES)


def scan_split(split):
    email_by_key = {}
    question_fingerprints = set()
    rows = 0
    repeated_keys = 0
    repeated_keys_with_other_email = 0

    for file_name in SPLIT_FILES[split]:
        for _, batch in read_batches(file_name, COLUMNS):
            for offset in range(len(batch["path"])):
                key = (batch["user"][offset], batch["path"][offset])
                email_fingerprint = fingerprint(batch["email"][offset])
                rows += 1
                if key in email_by_key:
                    repeated_keys += 1
                    if email_by_key[key] != email_fingerprint:
                        repeated_keys_with_other_email += 1
                else:
                    email_by_key[key] = email_fingerprint
                for question in batch["questions"][offset]:
                    question_fingerprints.add(fingerprint(question))

    return {
        "rows": rows,
        "email_by_key": email_by_key,
        "questions": question_fingerprints,
        "repeated_keys": repeated_keys,
        "repeated_keys_with_other_email": repeated_keys_with_other_email,
    }


def count_emails_that_differ(scans):
    key_sets = [set(scan["email_by_key"]) for scan in scans.values()]
    shared_keys = set.intersection(*key_sets)
    return sum(
        1
        for key in shared_keys
        if len({scan["email_by_key"][key] for scan in scans.values()}) > 1
    )


def count_questions_in_several_splits(scans):
    train, dev, test = (scans[split]["questions"] for split in SPLITS)
    return len((train & dev) | (train & test) | (dev & test))


def expect_zero(rule, found):
    return (rule, 0, f"{found:,}", found == 0)


def info(rule, found):
    return (rule, "info", f"{found:,}", None)


def split_rows(split, scan):
    return [
        info(f"{split}: rows", scan["rows"]),
        info(f"{split}: unique keys", len(scan["email_by_key"])),
        expect_zero(f"{split}: keys repeated", scan["repeated_keys"]),
        expect_zero(
            f"{split}: repeated keys with another email",
            scan["repeated_keys_with_other_email"],
        ),
        info(f"{split}: unique question fingerprints", len(scan["questions"])),
    ]


def check():
    scans = {split: scan_split(split) for split in SPLITS}
    key_sets = [set(scans[split]["email_by_key"]) for split in SPLITS]

    identical_keys = key_sets[0] == key_sets[1] == key_sets[2]
    keys_in_some_splits_only = len(set.union(*key_sets)) - len(
        set.intersection(*key_sets)
    )
    emails_that_differ = count_emails_that_differ(scans)
    same_emails = identical_keys and emails_that_differ == 0

    table = [
        (
            "key sets of train, dev, test identical",
            "yes",
            "yes" if identical_keys else "no",
            identical_keys,
        ),
        expect_zero("keys not in all three splits", keys_in_some_splits_only),
        expect_zero("keys whose email differs between splits", emails_that_differ),
        expect_zero(
            "question fingerprints in more than one split",
            count_questions_in_several_splits(scans),
        ),
    ]
    for split in SPLITS:
        table += split_rows(split, scans[split])

    return {
        "expects": "All three splits hold the same (user, path) keys and emails, "
        "each key once per split, and no question appears in two splits.",
        "found": f"All splits hold the same emails: {'yes' if same_emails else 'no'}.",
        "table": table,
        "details": {
            "all_splits_hold_same_emails": same_emails,
            "rows": {split: scans[split]["rows"] for split in SPLITS},
        },
    }


if __name__ == "__main__":
    run_check(NAME, check)
