"""The day builder over the raw reading-page cache: merging sections, filtering candidates, resuming."""

import datetime as dt
import json
import urllib.error

import backfill_html
import build_html_days
from conftest import make_article

DATE = dt.date(2019, 3, 15)


def cache_section(cache_dir, section, articles):
    backfill_html.write_atomic(backfill_html.path_for(cache_dir, DATE, section), articles)


def cache_day(cache_dir, articles):
    """Cache every section of DATE; the articles go in DO1 and the other sections are empty."""
    for section in build_html_days.SECTIONS:
        cache_section(cache_dir, section, articles if section == 'do1' else [])


def test_a_day_with_a_missing_section_is_not_read(tmp_path):
    cache_section(tmp_path, 'do1', [])
    assert build_html_days.read_day(tmp_path, DATE) is None


def test_read_day_adds_the_article_links(tmp_path):
    cache_day(tmp_path, [make_article()])
    (article,) = build_html_days.read_day(tmp_path, DATE)
    assert article['url'] == 'https://www.in.gov.br/web/dou/-/' + article['urlTitle']


def test_write_index_keeps_candidates_and_counts_the_edition(tmp_path):
    inside = make_article()
    outside = {**make_article(title='PORTARIA Nº 2'), 'hierarchyList': ['Ministério da Saúde']}
    candidates = build_html_days.write_index(tmp_path, DATE, [inside, outside])
    index = json.loads((tmp_path / '15-03-2019.json').read_text(encoding='utf-8'))
    assert candidates == [inside]
    assert (index['date'], index['count'], len(index['articles'])) == ('15-03-2019', 2, 1)


def test_save_texts_reports_failures_and_skips_saved_acts(tmp_path, monkeypatch):
    article = make_article()
    saved = []
    monkeypatch.setattr(build_html_days, 'save_article', lambda art, out: saved.append(art['urlTitle']))
    assert build_html_days.save_texts(tmp_path, DATE, [article]) == []
    assert saved == [article['urlTitle']]

    def broken(art, out):
        raise RuntimeError('boom')

    monkeypatch.setattr(build_html_days, 'save_article', broken)
    assert build_html_days.save_texts(tmp_path, DATE, [article]) == [f'{article["urlTitle"]}: boom']


def test_an_act_without_text_is_not_a_failure(tmp_path, monkeypatch):
    def no_text(art, out):
        raise build_html_days.NoArticleBody('no body')

    monkeypatch.setattr(build_html_days, 'save_article', no_text)
    assert build_html_days.save_texts(tmp_path, DATE, [make_article()]) == []


def test_a_page_the_dou_no_longer_serves_is_not_a_failure_but_other_errors_are(tmp_path, monkeypatch):
    def http_error(code):
        def fail(art, out):
            raise urllib.error.HTTPError('https://example', code, 'error', {}, None)

        return fail

    article = make_article()
    monkeypatch.setattr(build_html_days, 'save_article', http_error(404))
    assert build_html_days.save_texts(tmp_path, DATE, [article]) == []
    monkeypatch.setattr(build_html_days, 'save_article', http_error(500))
    assert len(build_html_days.save_texts(tmp_path, DATE, [article])) == 1
