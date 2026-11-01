"""Stream the raw Enron CSV in fixed-size blocks, with a progress bar."""

from pathlib import Path
from typing import Iterator

import pyarrow as pa
from pyarrow import csv
from tqdm import tqdm

DEFAULT_BLOCK_MB = 16


def iter_raw_batches(
    path: Path,
    block_mb: int = DEFAULT_BLOCK_MB,
    show_progress: bool = True,
) -> Iterator[pa.RecordBatch]:
    read_options = csv.ReadOptions(block_size=block_mb * 1024 * 1024)
    parse_options = csv.ParseOptions(newlines_in_values=True)
    convert_options = csv.ConvertOptions(
        column_types={"file": pa.string(), "message": pa.string()}
    )

    with open(path, "rb") as source:
        reader = csv.open_csv(
            source,
            read_options=read_options,
            parse_options=parse_options,
            convert_options=convert_options,
        )

        with tqdm(
            total=path.stat().st_size,
            unit="B",
            unit_scale=True,
            desc=path.name,
            disable=not show_progress,
        ) as progress:
            for batch in reader:
                progress.n = source.tell()
                progress.refresh()
                yield batch

            progress.n = progress.total
            progress.refresh()
