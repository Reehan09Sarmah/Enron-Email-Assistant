"""R6: compare EnronQA bodies with raw bodies for a fixed sample of dev keys."""

import argparse
import os
import random
import statistics
from collections import Counter
from difflib import SequenceMatcher
from functools import partial

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from tqdm import tqdm

from scripts.data_checks.common import (
    RAW_CSV_PATH,
    RAW_DIR,
    SPLIT_FILES,
    collapse_whitespace,
    read_batches,
)
from scripts.data_checks.join_to_enronqa import body_after_ruler
from scripts.data_checks.raw_csv import DEFAULT_BLOCK_MB, iter_raw_batches
from scripts.data_checks.raw_index import split_message
from scripts.data_checks.report import expect_zero, info, run_check

NAME = "body_diff"
DEV_FILE = SPLIT_FILES["dev"][0]
SEED = 42
SAMPLE_SIZE = 200
SIMILARITY_CHARS = 20_000
EXAMPLES_PER_GROUP = 10
QA_IN_RAW = "EnronQA contained in raw"
RAW_IN_QA = "raw contained in EnronQA"
NEITHER = "neither"
GROUPS = [QA_IN_RAW, RAW_IN_QA, NEITHER]
QA_LONGER = "EnronQA longer"
RAW_LONGER = "raw longer"
SAME_LENGTH = "same length"
LONGER_LABELS = [QA_LONGER, RAW_LONGER, SAME_LENGTH]


def choose_positions():
    with pq.ParquetFile(RAW_DIR / DEV_FILE) as parquet_file:
        total = parquet_file.metadata.num_rows
    chosen = random.Random(SEED).sample(range(total), min(SAMPLE_SIZE, total))
    return set(chosen)


def read_enronqa_sample(positions):
    sample = {}
    for first_row, batch in read_batches(DEV_FILE, ["user", "path", "email"]):
        rows = zip(batch["user"], batch["path"], batch["email"])
        for offset, (user, path, email) in enumerate(rows):
            if first_row + offset in positions:
                sample[path] = (user, body_after_ruler(email))
    return sample


def read_raw_bodies(wanted_paths, block_mb):
    wanted = pa.array(sorted(wanted_paths), pa.string())
    bodies = {}
    for batch in iter_raw_batches(RAW_CSV_PATH, block_mb):
        hits = batch.filter(pc.is_in(batch.column("file"), value_set=wanted))
        files = hits.column("file").to_pylist()
        messages = hits.column("message").to_pylist()
        for file_value, message in zip(files, messages):
            bodies[file_value] = split_message(message or "")[1]
    return bodies


def common_prefix_length(first, second):
    return len(os.path.commonprefix([first, second]))


def containment_group(qa_text, raw_text):
    if qa_text in raw_text:
        return QA_IN_RAW
    if raw_text in qa_text:
        return RAW_IN_QA
    return NEITHER


def longer_side(qa_chars, raw_chars):
    if qa_chars == raw_chars:
        return SAME_LENGTH
    return QA_LONGER if qa_chars > raw_chars else RAW_LONGER


def compare_bodies(qa_body, raw_body):
    qa_text = collapse_whitespace(qa_body)
    raw_text = collapse_whitespace(raw_body)
    matcher = SequenceMatcher(
        None, qa_text[:SIMILARITY_CHARS], raw_text[:SIMILARITY_CHARS], autojunk=False
    )

    return {
        "qa_chars": len(qa_body),
        "raw_chars": len(raw_body),
        "longer": longer_side(len(qa_body), len(raw_body)),
        "length_ratio": len(qa_body) / len(raw_body),
        "common_prefix": common_prefix_length(qa_text, raw_text),
        "common_suffix": common_prefix_length(qa_text[::-1], raw_text[::-1]),
        "similarity": matcher.ratio(),
        "group": containment_group(qa_text, raw_text),
    }


def compare_sample(sample, raw_bodies):
    pairs = []
    for path, (user, qa_body) in tqdm(sample.items(), desc="comparing"):
        if path in raw_bodies:
            comparison = compare_bodies(qa_body, raw_bodies[path])
            pairs.append({"user": user, "path": path, **comparison})
    return pairs


def spread(pairs, field, decimals):
    values = [pair[field] for pair in pairs]
    low, middle, high = min(values), statistics.median(values), max(values)
    return f"{low:,.{decimals}f} / {middle:,.{decimals}f} / {high:,.{decimals}f}"


def spread_row(label, pairs, field, decimals):
    return info(f"{label}, min / median / max", spread(pairs, field, decimals))


def summary_rows(sample, pairs):
    groups = Counter(pair["group"] for pair in pairs)
    longer = Counter(pair["longer"] for pair in pairs)
    missing = len(sample) - len(pairs)
    rows = [
        info("sampled EnronQA dev keys", len(sample)),
        expect_zero("sampled keys not found in the raw CSV", missing),
        spread_row("length ratio EnronQA / raw", pairs, "length_ratio", 3),
        spread_row("similarity ratio", pairs, "similarity", 3),
        spread_row("common prefix chars", pairs, "common_prefix", 1),
        spread_row("common suffix chars", pairs, "common_suffix", 1),
    ]
    rows += [info(label, longer[label]) for label in LONGER_LABELS]
    rows += [info(label, groups[label]) for label in GROUPS]
    return rows


def example_keys(pairs):
    return {
        f"Example keys (user, path), {label}": [
            f"({pair['user']}, {pair['path']})"
            for pair in pairs
            if pair["group"] == label
        ][:EXAMPLES_PER_GROUP]
        or ["none"]
        for label in GROUPS
    }


def check(args):
    sample = read_enronqa_sample(choose_positions())
    raw_bodies = read_raw_bodies(set(sample), args.block_mb)
    pairs = compare_sample(sample, raw_bodies)
    if not pairs:
        raise SystemExit("No sampled key was found in the raw CSV.")

    counts = Counter(pair["group"] for pair in pairs)
    return {
        "expects": "For most pairs the EnronQA body sits inside the raw body.",
        "found": "; ".join(f"{label}: {counts[label]}" for label in GROUPS),
        "table": summary_rows(sample, pairs),
        "sections": example_keys(pairs),
        "details": {"seed": SEED, "block_mb": args.block_mb, "pairs": pairs},
    }


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block-mb", type=int, default=DEFAULT_BLOCK_MB)
    return parser.parse_args()


if __name__ == "__main__":
    run_check(NAME, partial(check, parse_args()))
