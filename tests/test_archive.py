"""Regression tests over the 2026 archive in data/, clipping-novo/ and clipping-antigo/.

When a rule changes on purpose, `make regenerate` rewrites clipping-novo/ and the diff shows every past clipping
that changed. The baseline numbers below may then go up; they should never have to go down.
"""

import collections
import datetime as dt
import json
from pathlib import Path

import pytest

from clipping import assess_day, clipping_text
from report import build_model

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
GENERATED = ROOT / 'clipping-novo'
MANUAL = ROOT / 'clipping-antigo'

# Agreement with the clippings the team sent, measured on 2026-11-12.
MIN_IDENTICAL_EMAILS = 60
MIN_SAME_ACTS_EMAILS = 101  # identical + same acts with other wording
MIN_SENT_ACTS_SUGGESTED = 305  # of the 307 MDS acts the team sent


def edition_days():
    days = []
    for path in sorted(DATA.glob('????-??-??.json')):
        if json.loads(path.read_text(encoding='utf-8'))['count']:
            days.append(path.stem)
    return days


def saved_text_path(day, article):
    """Where save_articles.py writes the full text of `article`."""
    return DATA / day / (article['urlTitle'].rsplit('/', 1)[-1] + '.md')


@pytest.mark.parametrize('day', edition_days())
def test_every_indexed_act_has_its_full_text(day):
    """Without its full text an act falls back to the short index summary, so a gap would go unnoticed."""
    index = json.loads((DATA / f'{day}.json').read_text(encoding='utf-8'))
    for article in index['articles']:
        path = saved_text_path(day, article)
        assert path.is_file(), f'missing full text: {path}'
        # The summary rules read only what follows the header that ends with the Organization line.
        body = path.read_text(encoding='utf-8').split('\nOrganization:', 1)[-1].split('\n\n', 1)[-1]
        assert body.strip(), f'full text without body: {path}'


def test_no_full_text_is_left_without_its_index():
    indexed = {
        saved_text_path(path.stem, article)
        for path in DATA.glob('????-??-??.json')
        for article in json.loads(path.read_text(encoding='utf-8'))['articles']
    }
    assert sorted(set(DATA.glob('????-??-??/*.md')) - indexed) == []


def test_every_edition_has_a_clipping_and_nothing_else_does():
    assert sorted(path.stem for path in GENERATED.glob('*.md')) == edition_days()


@pytest.mark.parametrize('day', edition_days())
def test_clipping_matches_the_current_rules(day):
    index = json.loads((DATA / f'{day}.json').read_text(encoding='utf-8'))
    text, _ = clipping_text(dt.date.fromisoformat(day), assess_day(day, index, DATA))
    assert text == (GENERATED / f'{day}.md').read_text(encoding='utf-8'), 'run `make regenerate` if the rule changed'


@pytest.fixture(scope='module')
def model():
    return build_model(DATA, MANUAL)


def test_agreement_with_the_team_does_not_regress(model):
    matches = collections.Counter(day['emailMatch'] for day in model['days'])
    assert matches['identical'] >= MIN_IDENTICAL_EMAILS
    assert matches['identical'] + matches['same_acts'] >= MIN_SAME_ACTS_EMAILS
    sent = [c for day in model['days'] for c in day['candidates'] if c['manual']]
    assert sum(c['suggestion'] == 'suggest' for c in sent) >= MIN_SENT_ACTS_SUGGESTED
