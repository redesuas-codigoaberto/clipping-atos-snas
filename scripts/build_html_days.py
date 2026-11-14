#!/usr/bin/env python3
"""Build day indexes and article texts from the raw reading-page cache written by backfill_html.py.

For each date it merges the cached sections, keeps the candidate acts (see clipping.is_candidate), writes
<data-dir>/<year>/<DD-MM-AAAA>.json like scrape.py does and downloads each candidate's full text like save_articles.py.
Texts already saved are skipped, so a stopped run resumes. A date whose sections are not all cached yet is skipped.
"""

import argparse
import concurrent.futures
import datetime as dt
import gzip
import json
import sys
import urllib.error
from pathlib import Path

import dates
from backfill_html import path_for
from clipping import is_candidate
from data_repo import DAYS, RAW_HTML, year_dir
from save_articles import NoArticleBody, save_article
from scrape import SECTIONS


def read_day(cache_dir, date):
    """The articles of every section of `date`, or None when a section is not cached yet."""
    paths = [path_for(cache_dir, date, section) for section in SECTIONS]
    if not all(path.exists() for path in paths):
        return None
    articles = []
    for path in paths:
        with gzip.open(path, 'rt', encoding='utf-8') as file:
            for article in json.load(file):
                article['url'] = 'https://www.in.gov.br/web/dou/-/' + article['urlTitle']
                articles.append(article)
    return articles


def write_index(data_dir, date, articles):
    """Write the day index; returns its candidates."""
    candidates = [article for article in articles if is_candidate(article)]
    index = {'date': dates.name(date), 'count': len(articles), 'articles': candidates}
    (data_dir / f'{dates.name(date)}.json').write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    return candidates


def save_texts(data_dir, date, candidates):
    """Download the missing texts of the day; returns the failures as messages."""
    output_dir = data_dir / dates.name(date)
    if candidates:
        output_dir.mkdir(exist_ok=True)
    failures = []
    for article in candidates:
        try:
            save_article(article, output_dir)
        except NoArticleBody:
            # Not a failure: the clipping falls back to the index snippet, as it does for any act without a text.
            continue
        except urllib.error.HTTPError as exc:
            # The DOU no longer serves some old acts (404); retrying never helps, so the snippet is used as well.
            if exc.code != 404:
                failures.append(f'{article["urlTitle"]}: {exc}')
        except Exception as exc:  # noqa: BLE001 - a failed act is retried on the next run
            failures.append(f'{article["urlTitle"]}: {exc}')
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--start', type=dates.argument, required=True)
    parser.add_argument('--end', type=dates.argument, required=True)
    parser.add_argument('--cache-dir', type=Path, default=RAW_HTML)
    parser.add_argument('--data-dir', type=Path, default=DAYS)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    days = [args.start + dt.timedelta(days=i) for i in range((args.end - args.start).days + 1)]
    failed = skipped = 0
    with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
        futures = {}
        for date in days:
            articles = read_day(args.cache_dir, date)
            if articles is None:
                skipped += 1
            elif articles:
                folder = year_dir(args.data_dir, dates.name(date))
                folder.mkdir(parents=True, exist_ok=True)
                futures[pool.submit(save_texts, folder, date, write_index(folder, date, articles))] = date
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            failures = future.result()
            failed += bool(failures)
            status = f'FAILED {"; ".join(failures)}' if failures else 'ok'
            print(f'[{i}/{len(futures)}] {dates.name(futures[future])}: {status}', flush=True)
    print(f'{skipped} dates skipped because their sections are not all cached yet')
    if failed:
        print(f'{failed} dates had failures; run the same command again to retry them', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
