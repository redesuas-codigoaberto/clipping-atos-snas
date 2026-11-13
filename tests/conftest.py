"""Builders for DOU articles shaped like the ones scrape.py and save_articles.py write."""

import pytest

from clipping import MDS


def make_article(title='PORTARIA Nº 1, DE 2 DE JANEIRO DE 2026', units=('Gabinete do Ministro',), **fields):
    """An index entry for an MDS act."""
    hierarchy = [MDS, *units]
    slug = title.lower().replace(' ', '-') + '-123456789'
    return {
        'title': title,
        'urlTitle': slug,
        'url': f'https://www.in.gov.br/web/dou/-/{slug}',
        'hierarchyList': hierarchy,
        'hierarchyStr': '/'.join(hierarchy),
        'artType': 'Portaria',
        'pubName': 'DO1',
        'pubDate': '02/01/2026',
        'content': '',
        **fields,
    }


def make_full_text(article, *blocks):
    """The Markdown file save_articles.py writes for `article`, with the body made of `blocks`."""
    header = [
        f'# {article["title"]}',
        f'Source: {article["url"]}',
        f'Date: {article["pubDate"]}',
        f'Section: {article["pubName"]}',
        f'Organization: {article["hierarchyStr"]}',
        f'## {article["title"]}',
    ]
    return '\n\n'.join([*header, *blocks]) + '\n'


@pytest.fixture
def article():
    return make_article()
