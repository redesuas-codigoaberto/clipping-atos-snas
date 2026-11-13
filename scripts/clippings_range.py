#!/usr/bin/env python3
"""Write the SNAS clipping of every edition in a data directory, in one process (for the 2004-2025 backfill)."""

import argparse
import json
from pathlib import Path

import dates
from clipping import assess_day, clipping_text


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--data-dir', type=Path, default=Path('cache/historico/data'))
    parser.add_argument('--output-dir', type=Path, default=Path('clipping-historico'))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    written = selected = 0
    for index_path in sorted(args.data_dir.glob(f'{dates.GLOB}.json'), key=lambda path: dates.parse(path.stem)):
        index = json.loads(index_path.read_text(encoding='utf-8'))
        if not index['count']:
            continue
        day = index_path.stem
        text, count = clipping_text(dates.parse(day), assess_day(day, index, args.data_dir))
        (args.output_dir / f'{day}.md').write_text(text, encoding='utf-8')
        written += 1
        selected += count
    print(f'{written} clippings, {selected} acts')


if __name__ == '__main__':
    main()
