#!/usr/bin/env python3
"""Turn the monthly XML files of the DOU open data into day indexes and article texts, for 2004 to 2017.

The Imprensa Nacional publishes one zip per section and month. This script downloads them to the data repository
(skipping zips already there, so a stopped run resumes) and writes, for each date with an edition, the same
files the daily run writes from the reading page, in the folder of its year: <year>/<DD-MM-AAAA>.json with the
candidate acts and <year>/<DD-MM-AAAA>/<id>.md with each act's full text. The old XML is not well formed
(some attributes hold markup), so the fields are read with regular expressions instead of an XML parser.
"""

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.parse
import zipfile
from pathlib import Path

import dates
from clipping import is_candidate
from data_repo import DAYS, RAW_XML, year_dir
from dou_fetch import get_bytes, get_html
from save_articles import ArticleParser

PAGE = 'https://www.in.gov.br/acesso-a-informacao/dados-abertos/base-de-dados?ano={year}&mes={month}'
MONTHS = (
    'Janeiro',
    'Fevereiro',
    'Março',
    'Abril',
    'Maio',
    'Junho',
    'Julho',
    'Agosto',
    'Setembro',
    'Outubro',
    'Novembro',
    'Dezembro',
)
SECTIONS = (1, 2, 3)
ATTRIBUTE = re.compile(r'(\w+)="([^"]*)"')
TAG = re.compile(r'<[^>]*>')


def zip_name(year, month, section):
    return f'S{section:02d}{month:02d}{year}.zip'


def month_links(year, month):
    """The download URL of each section the open-data page lists for the month."""
    # The page needs the month name percent-encoded: "Março" unencoded returns no files.
    page = get_html(PAGE.format(year=year, month=urllib.parse.quote(MONTHS[month - 1])))
    links = {}
    for section in SECTIONS:
        match = re.search(rf'documents/49035712/[^"]*/{zip_name(year, month, section)}[^"]*', page)
        if match:
            links[section] = 'https://www.in.gov.br/' + html.unescape(match.group(0))
    return links


def cached_zips(cache_dir, year, month):
    """The month's zips, downloading the missing ones; returns ({section: path}, [sections not published])."""
    paths = {section: cache_dir / zip_name(year, month, section) for section in SECTIONS}
    missing = [section for section, path in paths.items() if not path.exists()]
    absent = []
    if missing:
        links = month_links(year, month)
        for section in missing:
            if section not in links:
                absent.append(section)
                continue
            data = get_bytes(links[section])
            tmp = paths[section].with_name(paths[section].name + '.part')
            cache_dir.mkdir(parents=True, exist_ok=True)
            tmp.write_bytes(data)
            if not zipfile.is_zipfile(tmp):
                tmp.unlink()
                raise RuntimeError(f'Not a zip file: {links[section]}')
            os.replace(tmp, paths[section])
    return {section: path for section, path in paths.items() if section not in absent}, absent


def cdata(text, tag):
    match = re.search(rf'<{tag}>\s*<!\[CDATA\[(.*?)\]\]>', text, re.S)
    return match.group(1) if match else ''


def clean(value):
    """An attribute or title without the markup some old files leave in it (`RETIFICAÇÃO</Identifica>`)."""
    return re.sub(r'\s+', ' ', TAG.sub(' ', html.unescape(value))).strip()


def parse_article(name, text):
    """The index entry (the reading page's fields) and the body blocks of one XML article."""
    head = text[: text.find('<body')]
    attributes = {key: html.unescape(value) for key, value in ATTRIBUTE.findall(head)}
    body = re.sub(r'\s+', ' ', cdata(text, 'Texto'))
    parser = ArticleParser()
    parser.feed(f'<div class="texto-dou">{body}</div>')
    parser.flush()
    category = attributes.get('artCategory', '')
    title = clean(cdata(text, 'Identifica')) or clean(attributes.get('name', ''))
    plain = ' '.join(block.lstrip('#- ') for block in parser.blocks)
    article = {
        'pubName': attributes.get('pubName', ''),
        'urlTitle': Path(name).stem,
        'numberPage': attributes.get('numberPage', ''),
        'title': title,
        'pubDate': attributes.get('pubDate', ''),
        'content': plain[:400] + (' ...' if len(plain) > 400 else ''),
        'editionNumber': attributes.get('editionNumber', ''),
        'artType': clean(attributes.get('artType', '')),
        'hierarchyStr': category,
        'hierarchyList': [part.strip() for part in category.split('/') if part.strip()],
        # Acts before 2018 have no page of their own; the link opens the DOU page where the act is printed.
        'url': attributes.get('pdfPage', ''),
    }
    return article, parser.blocks


def markdown(article, blocks):
    header = [
        f'# {article["title"]}',
        f'Source: {article["url"]}',
        f'Date: {article["pubDate"]}',
        f'Section: {article["pubName"]}',
        f'Organization: {article["hierarchyStr"]}',
    ]
    return '\n\n'.join([*header, *blocks]) + '\n'


def month_articles(zips):
    """{pubDate: [(article, blocks)]} for every act in the month's zips."""
    days = {}
    for path in zips.values():
        with zipfile.ZipFile(path) as archive:
            for name in sorted(archive.namelist()):
                if not name.endswith('.xml'):
                    continue
                article, blocks = parse_article(name, archive.read(name).decode('utf-8', 'replace'))
                days.setdefault(article['pubDate'], []).append((article, blocks))
    return days


def write_day(data_dir, day, entries, absent):
    """Write the day index with the candidates and their texts; returns the number of candidates."""
    candidates = [(article, blocks) for article, blocks in entries if is_candidate(article)]
    index = {
        'date': day,
        'count': len(entries),
        'articles': [article for article, _ in candidates],
        'source': 'xml',
        # Sections the open data lacks for this month (docs/ministerios.md); their acts are not in the index.
        'missingSections': [f'DO{section}' for section in absent],
    }
    (data_dir / f'{day}.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if candidates:
        (data_dir / day).mkdir(exist_ok=True)
    for article, blocks in candidates:
        (data_dir / day / f'{article["urlTitle"]}.md').write_text(markdown(article, blocks), encoding='utf-8')
    return len(candidates)


def months(start, end):
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        yield year, month
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--start', type=dates.argument, required=True)
    parser.add_argument('--end', type=dates.argument, required=True)
    parser.add_argument('--cache-dir', type=Path, default=RAW_XML)
    parser.add_argument('--data-dir', type=Path, default=DAYS)
    args = parser.parse_args()
    for year, month in months(args.start, args.end):
        zips, absent = cached_zips(args.cache_dir, year, month)
        written = candidates = 0
        for pub_date, entries in month_articles(zips).items():
            try:
                date = dt.datetime.strptime(pub_date, '%d/%m/%Y').date()
            except ValueError:
                print(f'{month:02d}-{year}: {len(entries)} acts without a valid date ({pub_date!r})', file=sys.stderr)
                continue
            if args.start <= date <= args.end:
                folder = year_dir(args.data_dir, dates.name(date))
                folder.mkdir(parents=True, exist_ok=True)
                candidates += write_day(folder, dates.name(date), entries, absent)
                written += 1
        gaps = f', missing sections {absent}' if absent else ''
        print(f'{month:02d}-{year}: {written} editions, {candidates} candidates{gaps}', flush=True)


if __name__ == '__main__':
    main()
