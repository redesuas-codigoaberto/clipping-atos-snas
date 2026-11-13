#!/usr/bin/env python3
"""Download Diário Oficial article indexes for a date (Brazil time)."""

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo

from clipping import MDS
from dou_fetch import get_html

BASE = 'https://www.in.gov.br/leiturajornal'
SECTIONS = ('do1', 'do2', 'do3', 'do1e', 'do2e', 'do3e', 'do1a', 'do1esp', 'do2esp')


def fetch(date, section):
    url = f'{BASE}?data={date:%d-%m-%Y}&secao={section}'
    html = get_html(url)
    match = re.search(r'<script id="params" type="application/json">\s*(.*?)\s*</script>', html, re.S)
    if not match:
        raise RuntimeError(f'No article data found at {url}')
    data = json.loads(match.group(1))
    if data['dateUrl'] != date.strftime('%d-%m-%Y'):
        raise RuntimeError(f'Unexpected date at {url}: {data["dateUrl"]}')
    return data['jsonArray']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--date', type=dt.date.fromisoformat, default=dt.datetime.now(ZoneInfo('America/Sao_Paulo')).date()
    )
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
    path = args.output_dir / f'{args.date.isoformat()}.json'
    # Only MDS acts are evaluated, so the index keeps just them; count is the size of the whole edition.
    mds = [article for article in articles if MDS in article['hierarchyList']]
    path.write_text(
        json.dumps(
            {'date': args.date.isoformat(), 'count': len(articles), 'articles': mds}, ensure_ascii=False, indent=2
        )
        + '\n',
        encoding='utf-8',
    )
    print(path)


if __name__ == '__main__':
    main()
