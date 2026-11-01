"""R4: where the questions shared by several splits sit (follow-up to C2)."""

from collections import Counter

from scripts.data_checks.common import SPLIT_FILES, fingerprint, read_batches
from scripts.data_checks.index_tables import count_buckets
from scripts.data_checks.report import info, run_check

NAME = "question_overlap"
EXPECTED_SHARED = 3106
SPLIT_BITS = {"train": 1, "dev": 2, "test": 4}
EXAMPLES_PER_CATEGORY = 10
REFS_PER_EXAMPLE = 4
SAME_KEY = "same email key in two splits"
OTHER_KEYS = "only different email keys"


def find_shared_questions():
    split_bits = {}
    for split, file_names in SPLIT_FILES.items():
        for file_name in file_names:
            for _, batch in read_batches(file_name, ["questions"]):
                for questions in batch["questions"]:
                    for question in questions:
                        key = fingerprint(question)
                        split_bits[key] = split_bits.get(key, 0) | SPLIT_BITS[split]
    return {key for key, bits in split_bits.items() if bits & (bits - 1)}


def collect_occurrences(shared):
    occurrences = {}
    columns = ["user", "path", "questions", "gold_answers"]
    for split, file_names in SPLIT_FILES.items():
        for file_name in file_names:
            for first_row, batch in read_batches(file_name, columns):
                for offset, questions in enumerate(batch["questions"]):
                    email_key = (batch["user"][offset], batch["path"][offset])
                    reference = f"({file_name}, {first_row + offset})"
                    for position, question in enumerate(questions):
                        question_key = fingerprint(question)
                        if question_key in shared:
                            gold = fingerprint(batch["gold_answers"][offset][position])
                            occurrences.setdefault(question_key, []).append(
                                (split, email_key, gold, reference)
                            )
    return occurrences


def describe_question(occurrences):
    splits_by_email = {}
    golds_by_email = {}
    for split, email_key, gold, _ in occurrences:
        splits_by_email.setdefault(email_key, set()).add(split)
        golds_by_email.setdefault(email_key, set()).add(gold)

    same_key_emails = [
        key for key, splits in splits_by_email.items() if len(splits) > 1
    ]
    return {
        "category": SAME_KEY if same_key_emails else OTHER_KEYS,
        "emails": len(splits_by_email),
        "same_key_pairs": len(same_key_emails),
        "same_key_identical_gold": sum(
            1 for key in same_key_emails if len(golds_by_email[key]) == 1
        ),
        "references": [item[3] for item in occurrences][:REFS_PER_EXAMPLE],
    }


def check():
    shared = find_shared_questions()
    described = [
        describe_question(occurrences)
        for occurrences in collect_occurrences(shared).values()
    ]
    categories = Counter(item["category"] for item in described)
    pairs = sum(item["same_key_pairs"] for item in described)
    identical = sum(item["same_key_identical_gold"] for item in described)
    examples = {
        category: [
            item["references"]
            for item in described
            if item["category"] == category
        ][:EXAMPLES_PER_CATEGORY]
        for category in (SAME_KEY, OTHER_KEYS)
    }

    table = [
        (
            "questions shared by several splits",
            f"{EXPECTED_SHARED:,} (from C2)",
            f"{len(shared):,}",
            len(shared) == EXPECTED_SHARED,
        ),
        info(f"shared questions: {SAME_KEY}", categories[SAME_KEY]),
        info(f"shared questions: {OTHER_KEYS}", categories[OTHER_KEYS]),
        info("same-key cases (question, email) in two splits", pairs),
        info("... with an identical gold answer", identical),
        info("... with a different gold answer", pairs - identical),
    ]
    for bucket, number in count_buckets(item["emails"] for item in described).items():
        table.append(info(f"distinct emails per shared question: {bucket}", number))

    return {
        "expects": f"{EXPECTED_SHARED:,} shared questions, as found by C2.",
        "found": f"{len(shared):,} shared questions; {categories[SAME_KEY]:,} sit on "
        "the same email key in two splits.",
        "table": table,
        "sections": {
            f"Example row references, {category} (file name, row index)": [
                "; ".join(references) for references in category_examples
            ]
            or ["none"]
            for category, category_examples in examples.items()
        },
        "details": {"examples": examples},
    }


if __name__ == "__main__":
    run_check(NAME, check)
