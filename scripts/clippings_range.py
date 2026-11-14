#!/usr/bin/env python3
"""Write the SNAS clipping of every edition in a date range of the data repository, in one process.

The data repository keeps each year in its own folder (see data_repo.py), and the clippings are written there too,
in clippings/<year>/. 2026 is in data/ here and its clippings in clipping-novo/, so the default range stops at 2025.
"""

import argparse
import datetime as dt
import json
from pathlib import Path

import dates
from clipping import assess_day, clipping_text
from data_repo import CLIPPINGS, DAYS, year_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--start', type=dates.argument, default=dt.date(2004, 1, 1))
    parser.add_argument('--end', type=dates.argument, default=dt.date(2025, 12, 31))
    parser.add_argument('--data-dir', type=Path, default=DAYS)
    parser.add_argument('--output-dir', type=Path, default=CLIPPINGS)
    args = parser.parse_args()
    paths = [
        path for path in args.data_dir.glob(f'*/{dates.GLOB}.json') if args.start <= dates.parse(path.stem) <= args.end
    ]
    written = selected = 0
    for index_path in sorted(paths, key=lambda path: dates.parse(path.stem)):
        index = json.loads(index_path.read_text(encoding='utf-8'))
        if not index['count']:
            continue
        day = index_path.stem
        text, count = clipping_text(dates.parse(day), assess_day(day, index, index_path.parent))
        folder = year_dir(args.output_dir, day)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f'{day}.md').write_text(text, encoding='utf-8')
        written += 1
        selected += count
    print(f'{written} clippings, {selected} acts')


if __name__ == '__main__':
    main()
