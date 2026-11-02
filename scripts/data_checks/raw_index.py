"""Index the raw Enron CSV: one row of fingerprints per message, no text kept."""

import argparse
import hashlib
import re
from functools import partial

import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm

from scripts.data_checks.common import (
    INDEX_PATH,
    RAW_CSV_PATH,
    collapse_whitespace,
    fingerprint,
)
from scripts.data_checks.raw_csv import DEFAULT_BLOCK_MB, iter_raw_batches
from scripts.data_checks.report import info, run_check

NAME = "raw_index"
HEADER_END = re.compile(r"\r?\n\r?\n")
TRACKED_HEADERS = ["message-id", "date", "from", "to"]
HASH_CHUNK_BYTES = 1024 * 1024
INDEX_SCHEMA = pa.schema(
    [
        ("row", pa.int64()),
        ("user", pa.string()),
        ("folder", pa.string()),
        ("file_fp", pa.binary()),
        ("message_id_fp", pa.binary()),
        ("body_fp", pa.binary()),
        ("body_collapsed_fp", pa.binary()),
        ("message_chars", pa.int64()),
        ("has_message_id", pa.bool_()),
        ("has_date", pa.bool_()),
        ("has_from", pa.bool_()),
        ("has_to", pa.bool_()),
    ]
)


def split_message(message):
    match = HEADER_END.search(message)
    if match is None:
        return message, ""
    return message[: match.start()], message[match.end() :]


def read_headers(header_block):
    headers = {}
    for line in header_block.splitlines():
        name, separator, value = line.partition(":")
        name = name.lower()
        if separator and name in TRACKED_HEADERS:
            headers.setdefault(name, value.strip())
    return headers


def folder_of(file_value):
    return "/".join(file_value.split("/")[1:-1])


def summarise_message(row_number, file_value, message):
    header_block, body = split_message(message)
    headers = read_headers(header_block)
    message_id = headers.get("message-id")

    return {
        "row": row_number,
        "user": file_value.split("/", 1)[0],
        "folder": folder_of(file_value),
        "file_fp": fingerprint(file_value),
        "message_id_fp": None if message_id is None else fingerprint(message_id),
        "body_fp": fingerprint(body),
        "body_collapsed_fp": fingerprint(collapse_whitespace(body)),
        "message_chars": len(message),
        "has_message_id": message_id is not None,
        "has_date": "date" in headers,
        "has_from": "from" in headers,
        "has_to": "to" in headers,
    }


def index_batch(batch, first_row):
    files = batch.column("file").to_pylist()
    messages = batch.column("message").to_pylist()
    summaries = [
        summarise_message(first_row + offset, file_value or "", message or "")
        for offset, (file_value, message) in enumerate(zip(files, messages))
    ]
    return pa.RecordBatch.from_pylist(summaries, schema=INDEX_SCHEMA)


def index_batches(csv_path, block_mb, limit_rows):
    rows_done = 0

    for batch in iter_raw_batches(csv_path, block_mb):
        if limit_rows is not None:
            batch = batch.slice(0, limit_rows - rows_done)
        yield index_batch(batch, rows_done)
        rows_done += batch.num_rows
        if limit_rows is not None and rows_done >= limit_rows:
            return


def write_index(batches, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    rows = 0

    writer = pq.ParquetWriter(temporary, INDEX_SCHEMA)
    try:
        for batch in batches:
            writer.write_batch(batch)
            rows += batch.num_rows
    except BaseException:
        writer.close()
        temporary.unlink(missing_ok=True)
        raise

    writer.close()
    temporary.replace(destination)
    return rows


def sha256_of_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source, tqdm(
        total=path.stat().st_size, unit="B", unit_scale=True, desc="sha256"
    ) as progress:
        while chunk := source.read(HASH_CHUNK_BYTES):
            digest.update(chunk)
            progress.update(len(chunk))
    return digest.hexdigest()


def build_index(args):
    batches = index_batches(RAW_CSV_PATH, args.block_mb, args.limit_rows)
    try:
        return write_index(batches, INDEX_PATH)
    except pa.ArrowInvalid as error:
        if "straddling" not in str(error):
            raise
        raise SystemExit(
            "A message is bigger than the block size. "
            "Rerun with a larger block, for example --block-mb 32."
        )


def check(args):
    rows = build_index(args)
    trial = args.limit_rows is not None
    sha256 = "not computed in a trial run" if trial else sha256_of_file(RAW_CSV_PATH)
    note = " (trial run, rows limited)" if trial else ""

    return {
        "expects": "One index row for every message row in the CSV.",
        "found": f"{rows:,} rows indexed{note}.",
        "table": [
            info("rows read", rows),
            info("CSV size in bytes", RAW_CSV_PATH.stat().st_size),
            info("CSV SHA-256", sha256),
            info("index file", INDEX_PATH.name),
        ],
        "details": {"limit_rows": args.limit_rows, "block_mb": args.block_mb},
    }


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit-rows", type=int, default=None, help="stop after this many rows"
    )
    parser.add_argument("--block-mb", type=int, default=DEFAULT_BLOCK_MB)
    return parser.parse_args()


if __name__ == "__main__":
    run_check(NAME, partial(check, parse_args()))
