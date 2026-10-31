"""Shared helpers for the data checks: parquet reader, fingerprints, memory use."""

import ctypes
import hashlib
from ctypes import wintypes
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "enron_qa_0922"
REPORT_DIR = ROOT / "data" / "reports"
DATA_COMMIT = "c0b3a9190fd970e83cfbe7d399a08860e43e221e"
BATCH_SIZE = 1000
BYTES_PER_MB = 1024 * 1024

SPLIT_FILES = {
    "train": [
        "train-00000-of-00002.parquet",
        "train-00001-of-00002.parquet",
    ],
    "dev": ["dev-00000-of-00001.parquet"],
    "test": ["test-00000-of-00001.parquet"],
}
ALL_FILES = [name for names in SPLIT_FILES.values() for name in names]


def read_batches(file_name, columns):
    """Yield (index of the batch's first row, {column: values}) for one file."""
    first_row = 0
    with pq.ParquetFile(RAW_DIR / file_name) as parquet_file:
        for batch in parquet_file.iter_batches(batch_size=BATCH_SIZE, columns=columns):
            yield first_row, batch.to_pydict()
            first_row += batch.num_rows


def fingerprint(text):
    return hashlib.blake2b(text.encode("utf-8"), digest_size=16).digest()


class _MemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("page_fault_count", wintypes.DWORD),
        ("peak_working_set", ctypes.c_size_t),
        ("working_set", ctypes.c_size_t),
        ("quota_peak_paged_pool", ctypes.c_size_t),
        ("quota_paged_pool", ctypes.c_size_t),
        ("quota_peak_non_paged_pool", ctypes.c_size_t),
        ("quota_non_paged_pool", ctypes.c_size_t),
        ("pagefile_usage", ctypes.c_size_t),
        ("peak_pagefile_usage", ctypes.c_size_t),
    ]


def peak_memory_mb():
    """Peak working set of this process in MB (Windows only)."""
    kernel32 = ctypes.WinDLL("kernel32")
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL("psapi")
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_MemoryCounters),
        wintypes.DWORD,
    ]

    counters = _MemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    psapi.GetProcessMemoryInfo(
        kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb
    )
    return counters.peak_working_set / BYTES_PER_MB
