# 0003: Progress bars with tqdm

- **Status:** accepted
- **Date:** 2026-11-02
- **Phase / component:** data checks / reading the raw Enron CSV
- **Builds on:** 0002 (pyarrow reader)
- **Unblocks:** `scripts/data_checks/raw_csv.py` and the raw-data probe scripts that Rex runs himself
- **Design doc sections updated:** none (a tool, not a design choice)

## The decision needed
Whether the data scripts should show live progress while they scan large files, and with what.

## Context
Rex now runs every long scan himself. A scan of the 1.4 GB raw CSV takes minutes, and without any output he cannot tell a slow scan from a hung one. The laptop has 7.7 GB RAM, so he also needs to see that a run is moving and be able to stop it safely.

## What was studied first
No study card. tqdm 4.70.1 was installed in `.venv` and imported on Python 3.14.7 (checked, 2026-11-02).

## Options considered
### Option A: no progress output
- What it is: the scripts print their summary at the end only.
- Makes easy: nothing to add.
- Makes hard later: a long scan looks the same as a frozen one.
- How it fails: Rex kills a healthy run, or waits on a hung one.

### Option B: print a line every N batches, standard library only
- What it is: a `print` in the reading loop.
- Makes easy: no new library.
- Makes hard later: no speed or time-left figure unless we write that code ourselves; the line format and N are ours to maintain.
- How it fails: N is wrong for some file sizes, so output is either too quiet or floods the screen.

### Option C: tqdm
- What it is: a small, widely used progress-bar library.
- Makes easy: one bar shows bytes read, speed and time left, with a few lines of code.
- Makes hard later: one more library to keep up to date.
- How it fails: the bar shows a wrong number if we feed it the wrong position (we use the file position of the open CSV), but it never changes the data.

## How we would know it was wrong
A tqdm release breaks on a newer Python, or the bar slows a scan by a measurable amount (then compare a run with `show_progress=False`).

## Claude's recommendation
Option C is reasonable. Risk stated once: tqdm adds a dependency for something that only changes the display, so a bug in it can only mislead Rex about progress, not change results. Claude does not object.

## Decision (Rex)
Option C, tqdm. Followed recommendation: yes (Claude had no objection).

## Why
Rex, original: "I would love to run the files myself from now on and check their workings."

In simple words: Rex wants to run the scans on his own laptop and see that they are alive. tqdm only changes what is displayed (bytes read, speed, time left). It does not touch the data. The cost is one more library to maintain.

## Dissent, if any
None.

## Consequences
Adds `tqdm==4.70.1` to `requirements.txt`. The CSV reader and the file-hash step show a progress bar on the error stream. Rex runs the scans, not Claude.

## Revisit when
tqdm stops working on the Python version in `.venv`, or a bar is shown to slow a scan.

## 30-second defence (Rex's voice)
_To be drafted by Claude at the next phase gate._
