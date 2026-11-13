"""The published pages open in a browser: no script errors, no missing files, nothing wider than the screen.

The other tests check the data and the rules; these check the page script and the CSS, which run only in a
browser. They build the site from data/ and open it in the installed Chrome or Chromium. Without a browser
they are skipped, unless REQUIRE_BROWSER is set, as in the workflows, where a skip would hide a broken page.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BROWSERS = ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser')
# A phone (the width of a common iPhone) and a desktop.
WIDTHS = (390, 1400)
REPORT_VIEWS = ('ano', 'regras', 'clipping', 'resumos', 'dia')


def browser_path():
    found = os.environ.get('CHROME_PATH') or next(filter(None, map(shutil.which, BROWSERS)), None)
    if not found:
        if os.environ.get('REQUIRE_BROWSER'):
            pytest.fail('no Chrome or Chromium found; set CHROME_PATH')
        pytest.skip('no Chrome or Chromium found')
    return found


@pytest.fixture(scope='module')
def site(tmp_path_factory):
    """The site built by report.py, as the workflow builds it."""
    out = tmp_path_factory.mktemp('site')
    subprocess.run(
        [
            sys.executable,
            str(ROOT / 'scripts' / 'report.py'),
            '-o',
            str(out / 'relatorio.html'),
            '--clipping-output',
            str(out / 'index.html'),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return out


@pytest.fixture(scope='module')
def browser():
    sync_api = pytest.importorskip('playwright.sync_api')
    path = browser_path()
    with sync_api.sync_playwright() as playwright:
        chrome = playwright.chromium.launch(executable_path=path)
        yield playwright, chrome
        chrome.close()


def open_page(context, url):
    """Open `url` and wait for the view to render; returns the page and the problems it reported."""
    page = context.new_page()
    problems = []
    page.on('pageerror', lambda error: problems.append(f'script error: {error}'))
    page.on('console', lambda msg: msg.type == 'error' and problems.append(f'console: {msg.text}'))
    page.on('requestfailed', lambda request: problems.append(f'not loaded: {request.url}'))
    page.goto(url)
    try:
        # Done when the loading message is gone, or replaced by the page's error message.
        page.wait_for_function(
            "!document.querySelector('#app .loading') || document.querySelector('#app .loading.error')", timeout=15000
        )
    except Exception:
        # A script error usually stops the view from rendering; report it rather than the timeout.
        pytest.fail('the view did not render: ' + ('; '.join(problems) or 'no error reported'))
    page.wait_for_load_state('load')
    if page.locator('#app .loading.error').count():
        pytest.fail('the view did not render: ' + '; '.join(problems))
    return page, problems


def overflow(page):
    """How many pixels the page is wider than the screen."""
    return page.evaluate('document.documentElement.scrollWidth - window.innerWidth')


@pytest.mark.parametrize('width', WIDTHS)
@pytest.mark.parametrize(
    'name, view',
    [('index.html', 'clipping'), *(('relatorio.html', view) for view in REPORT_VIEWS)],
)
def test_view_renders_and_fits_the_screen(site, browser, name, view, width):
    _, chrome = browser
    context = chrome.new_context(viewport={'width': width, 'height': 900})
    page, problems = open_page(context, (site / name).as_uri() + f'#{view}')
    assert problems == []
    assert page.locator('#app').inner_text().strip(), 'the view rendered nothing'
    assert overflow(page) <= 0, f'{overflow(page)} px wider than a {width} px screen'
    context.close()


def test_comparison_window_on_a_phone(site, browser):
    """The window that compares a summary with the team's, opened on an emulated iPhone."""
    playwright, chrome = browser
    context = chrome.new_context(**playwright.devices['iPhone 13'])
    page, problems = open_page(context, (site / 'relatorio.html').as_uri() + '#resumos')
    # Tap the card body, not the title link, which leads to the day view.
    page.locator('.pair[data-i] .cols, .pair[data-i] .one').first.tap()
    page.wait_for_selector('.amodal')
    assert problems == []
    assert overflow(page) <= 0
    columns = page.evaluate("getComputedStyle(document.querySelector('.acols')).gridTemplateColumns.split(' ').length")
    assert columns == 1, 'the two texts should be stacked on a phone'
    box = page.locator('.abox').bounding_box()
    assert box['width'] <= page.viewport_size['width']
    context.close()
