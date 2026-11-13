#!/usr/bin/env python3
"""Download Diário Oficial article indexes for a date (Brazil time)."""

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo

import dates
from clipping import is_candidate
from dou_fetch import get_html

BASE = 'https://www.in.gov.br/leiturajornal'
SECTIONS = ('do1', 'do2', 'do3', 'do1e', 'do2e', 'do3e', 'do1a', 'do1esp', 'do2esp')


# The reading page embeds its article list as JSON in this script element.
PARAMS = re.compile(r'<script id="params" type="application/json">\s*(.*?)\s*</script>', re.S)


def parse_index(html, date, url=''):
    """The articles listed in a DOU reading page for `date`.

    Raises RuntimeError when the page has no article data or shows another date than requested,
    so that a change in the site fails the run instead of producing an empty or wrong index.
    """
    match = PARAMS.search(html)
    if not match:
        raise RuntimeError(f'No article data found at {url}')
    data = json.loads(match.group(1))
    if data['dateUrl'] != date.strftime('%d-%m-%Y'):
        raise RuntimeError(f'Unexpected date at {url}: {data["dateUrl"]}')
    return data['jsonArray']


def fetch(date, section):
    url = f'{BASE}?data={date:%d-%m-%Y}&secao={section}'
    return parse_index(get_html(url), date, url)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=dates.argument, default=dt.datetime.now(ZoneInfo('America/Sao_Paulo')).date())
    parser.add_argument('--output-dir', type=Path, default=Path('data'))
    args = parser.parse_args()
    articles = []
    for section in SECTIONS:
        found = fetch(args.date, section)
        print(f'{section}: {len(found)} articles')
        for article in found:
            article['url'] = 'https://www.in.gov.br/web/dou/-/' + article['urlTitle']
        articles.extend(found)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / f'{dates.name(args.date)}.json'
    # Only candidates are evaluated, so the index keeps just them; count is the size of the whole edition.
    mds = [article for article in articles if is_candidate(article)]
    path.write_text(
        json.dumps(
            {'date': dates.name(args.date), 'count': len(articles), 'articles': mds}, ensure_ascii=False, indent=2
        )
        + '\n',
        encoding='utf-8',
    )
    print(path)


if __name__ == '__main__':
    main()
