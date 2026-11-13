"""The helpers of the other scripts: download retries, article parsing, pages, report and daily run."""

import datetime as dt
import io
import urllib.error

import pytest

import daily
import dou_fetch
from add_manual import sanitize
from build_site import inline, to_html
from report import compare_emails, email_key, load_manual_clippings
from save_articles import ArticleParser

# --- dou_fetch ---


def test_retry_delay_prefers_the_server_value_within_a_cap():
    assert dou_fetch.retry_delay(0, '30') == 30
    assert dou_fetch.retry_delay(0, '9999') == dou_fetch.MAX_RETRY_AFTER
    assert dou_fetch.retry_delay(2) == 15
    assert dou_fetch.retry_delay(1, 'Wed, 21 Oct 2026 07:28:00 GMT') == 10


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def http_error(code):
    return urllib.error.HTTPError('https://example', code, 'error', {}, None)


def fake_urlopen(monkeypatch, outcomes):
    """Make urlopen raise or return each outcome in turn; returns the list of sleeps."""
    outcomes, sleeps = list(outcomes), []

    def urlopen(request, timeout):
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return FakeResponse(outcome.encode('utf-8'))

    monkeypatch.setattr(dou_fetch.urllib.request, 'urlopen', urlopen)
    return sleeps


def test_transient_failures_are_retried(monkeypatch):
    sleeps = fake_urlopen(monkeypatch, [http_error(503), TimeoutError(), 'página'])
    assert dou_fetch.get_html('https://example', sleep=sleeps.append) == 'página'
    assert sleeps == [5, 10]


def test_client_errors_are_not_retried(monkeypatch):
    sleeps = fake_urlopen(monkeypatch, [http_error(404)])
    with pytest.raises(urllib.error.HTTPError):
        dou_fetch.get_html('https://example', sleep=sleeps.append)
    assert sleeps == []


def test_gives_up_after_the_last_attempt(monkeypatch):
    sleeps = fake_urlopen(monkeypatch, [http_error(500)] * dou_fetch.ATTEMPTS)
    with pytest.raises(urllib.error.HTTPError):
        dou_fetch.get_html('https://example', sleep=sleeps.append)
    assert len(sleeps) == dou_fetch.ATTEMPTS - 1


# --- save_articles ---


def test_article_parser_keeps_only_the_dou_text():
    parser = ArticleParser()
    parser.feed(
        '<div class="menu"><p>Menu</p></div>'
        '<div class="texto-dou"><p class="identifica">PORTARIA Nº 1</p><p>Art. 1º Aprovar&nbsp;o plano.</p>'
        '<div><table><tr><td>Município</td><td>UF</td></tr></table></div><ul><li>item</li></ul></div>'
        '<p>Rodapé</p>'
    )
    parser.flush()
    assert parser.blocks == ['## PORTARIA Nº 1', 'Art. 1º Aprovar\xa0o plano.', 'Município | UF', '- item']


# --- site ---


def test_inline_renders_bold_and_links_and_escapes_html():
    assert inline('**Data** <b> [Ato](https://x/?a=1&b=2)') == (
        '<strong>Data</strong> &lt;b&gt; <a href="https://x/?a=1&amp;b=2">Ato</a>'
    )


def test_each_paragraph_becomes_a_p():
    assert to_html('um\n\n\ndois\n') == '<p>um</p>\n<p>dois</p>'


# --- add_manual ---


def test_sanitize_drops_the_email_header():
    exported = '# Clipping DOU-05/01/2026\n\nDe: alguém@exemplo\nPara: equipe\n\n---\n\nCorpo do email.\n'
    assert sanitize(exported) == '# Clipping DOU-05/01/2026\n\n---\n\nCorpo do email.\n'


def test_sanitize_rejects_other_files():
    with pytest.raises(ValueError):
        sanitize('# Outro assunto\n\nsem separador')


# --- report ---

ACT = '[PORTARIA Nº 1](https://www.in.gov.br/web/dou/-/portaria-n-1-123456789)'


def test_manual_clippings_are_keyed_by_edition_date(tmp_path):
    (tmp_path / 'a.md').write_text(f'# Clipping DOU- 05/01/2026\n\n---\n\n{ACT}: Aprova o plano.\n', encoding='utf-8')
    clippings = load_manual_clippings(tmp_path)
    assert list(clippings) == ['2026-01-05']
    assert clippings['2026-01-05']['acts']['123456789']['text'] == 'Aprova o plano.'


def test_email_key_ignores_formatting():
    assert email_key('**Data**\n\n[a](https://in.gov.br/en/web/x)') == email_key(
        'Data [a](https://www.in.gov.br/web/x)'
    )


def test_compare_emails():
    generated = f'{ACT}: Aprova o plano.'
    assert compare_emails(generated, [], {}) is None
    assert compare_emails(generated, [generated], {'123456789': {}}) == 'identical'
    assert compare_emails(generated, ['outro texto'], {'123456789': {}}) == 'same_acts'
    assert compare_emails(generated, ['outro texto'], {}) == 'different'


# --- daily ---


@pytest.mark.parametrize('day, warns', [(dt.date(2026, 11, 2), True), (dt.date(2026, 11, 7), False)])
def test_no_edition_warns_only_on_weekdays(day, warns):
    assert bool(daily.no_edition_warning(day)) is warns


def test_selected_count_counts_act_paragraphs(tmp_path):
    path = tmp_path / 'c.md'
    path.write_text(f'**Brasília - DF.**\n\n{ACT}: a\n\n{ACT}: b\n\nAssinatura\n', encoding='utf-8')
    assert daily.selected_count(path) == 2


def test_summary_is_written_only_on_github_actions(tmp_path, monkeypatch):
    monkeypatch.delenv('GITHUB_STEP_SUMMARY', raising=False)
    daily.write_summary(['ignored'])
    summary = tmp_path / 'summary.md'
    monkeypatch.setenv('GITHUB_STEP_SUMMARY', str(summary))
    daily.write_summary(['## Clipping', '- Atos: 1'])
    assert summary.read_text(encoding='utf-8') == '## Clipping\n- Atos: 1\n'


def test_output_is_written_only_on_github_actions(tmp_path, monkeypatch):
    monkeypatch.delenv('GITHUB_OUTPUT', raising=False)
    daily.write_output('ignored', 'x')
    output = tmp_path / 'output'
    monkeypatch.setenv('GITHUB_OUTPUT', str(output))
    daily.write_output('warning', 'sem atos')
    assert output.read_text(encoding='utf-8') == 'warning=sem atos\n'
