#!/usr/bin/env python3
"""Save full DOU articles for the selected ministry as Markdown."""

import argparse
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path

from clipping import is_candidate
from dou_fetch import get_html


class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.block = None
        self.parts = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div' and 'texto-dou' in attrs.get('class', '').split():
            self.depth = 1
            return
        if not self.depth:
            return
        if tag == 'div':
            self.depth += 1
        if tag in ('p', 'h1', 'h2', 'h3', 'li', 'tr'):
            self.flush()
            self.block = (tag, attrs.get('class', ''))
        elif tag == 'br':
            self.parts.append('\n')
        elif tag in ('td', 'th') and self.parts:
            self.parts.append(' | ')

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag in ('p', 'h1', 'h2', 'h3', 'li', 'tr'):
            self.flush()
        if tag == 'div':
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.parts.append(data)

    def flush(self):
        value = html.unescape(''.join(self.parts))
        value = re.sub(r'[ \t]+', ' ', value).strip()
        if value:
            tag, cls = self.block or ('p', '')
            prefix = (
                '# '
                if tag == 'h1'
                else '## '
                if tag == 'h2' or 'identifica' in cls
                else '### '
                if tag == 'h3'
                else '- '
                if tag == 'li'
                else ''
            )
            self.blocks.append(prefix + value)
        self.parts = []
        self.block = None


class NoArticleBody(RuntimeError):
    """The act's page has no text; the DOU publishes some acts only as an image or PDF."""


def save_article(article, output_dir):
    """Download one act and write it as Markdown; returns the path, or None when it was already saved."""
    path = output_dir / (article['urlTitle'].rsplit('/', 1)[-1] + '.md')
    if path.is_file() and path.stat().st_size > 0:
        return None
    url = article['url']
    parser = ArticleParser()
    parser.feed(get_html(url))
    parser.flush()
    if not parser.blocks:
        raise NoArticleBody(f'No article body found: {url}')
    header = [
        f'# {article["title"]}',
        f'Source: {url}',
        f'Date: {article["pubDate"]}',
        f'Section: {article["pubName"]}',
        f'Organization: {article["hierarchyStr"]}',
    ]
    path.write_text('\n\n'.join([*header, *parser.blocks]) + '\n', encoding='utf-8')
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('index', type=Path, help='Day index written by scrape.py')
    ap.add_argument('--output-dir', type=Path, default=Path('data'))
    args = ap.parse_args()
    index_data = json.loads(args.index.read_text(encoding='utf-8'))
    output_dir = args.output_dir / index_data['date']
    matches = [a for a in index_data['articles'] if is_candidate(a)]
    output_dir.mkdir(parents=True, exist_ok=True)
    for article in matches:
        path = save_article(article, output_dir)
        if path:
            print(path)
    print(f'Saved {len(matches)} articles')


if __name__ == '__main__':
    main()
