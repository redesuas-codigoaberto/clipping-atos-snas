#!/usr/bin/env python3
"""Cache the raw, unfiltered DOU reading-page indexes for a date range, so that a long backfill can resume.

Each date and section becomes ../atos-snas-data/raw/html/<year>/<DD-MM-AAAA>_<section>.json.gz. A file is written only
after its download succeeds, so stopping the run (Ctrl+C) loses at most the files in progress, and running
the same command again skips every file already cached. Nothing is filtered here: the ministry changed
its name over the years, and the selection is done later from the cache.
"""

import argparse
import concurrent.futures
import datetime as dt
import gzip
import json
import os
import sys
from pathlib import Path

import dates
from data_repo import RAW_HTML
from scrape import SECTIONS, fetch


def path_for(cache_dir, date, section):
    return cache_dir / str(date.year) / f'{dates.name(date)}_{section}.json.gz'


def write_atomic(path, articles):
    """Write through a temporary file, so an interrupted run never leaves a truncated file behind."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.part')
    with gzip.open(tmp, 'wt', encoding='utf-8') as file:
        json.dump(articles, file, ensure_ascii=False)
    os.replace(tmp, path)


def cache_date(cache_dir, date):
    """Download the missing sections of `date`; return (sections downloaded, articles, failures)."""
    done = count = 0
    failures = []
    for section in SECTIONS:
        path = path_for(cache_dir, date, section)
        if path.exists():
            continue
        try:
            articles = fetch(date, section)
        except Exception as exc:  # noqa: BLE001 - a failed section is retried on the next run
            failures.append(f'{section}: {exc}')
            continue
        write_atomic(path, articles)
        done += 1
        count += len(articles)
    return done, count, failures


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--start', type=dates.argument, required=True)
    parser.add_argument('--end', type=dates.argument, required=True)
    parser.add_argument('--cache-dir', type=Path, default=RAW_HTML)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    days = [args.start + dt.timedelta(days=i) for i in range((args.end - args.start).days + 1)]
    pending = [d for d in days if not all(path_for(args.cache_dir, d, s).exists() for s in SECTIONS)]
    print(f'{len(days)} dates, {len(pending)} with sections to download', flush=True)
    failed = 0
    with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
        futures = {pool.submit(cache_date, args.cache_dir, d): d for d in pending}
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            date = futures[future]
            done, count, failures = future.result()
            failed += bool(failures)
            status = f'FAILED {"; ".join(failures)}' if failures else 'ok'
            progress = f'[{i}/{len(pending)}] {dates.name(date)}'
            print(f'{progress}: {done} sections, {count} articles, {status}', flush=True)
    if failed:
        print(f'{failed} dates had failures; run the same command again to retry them', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
