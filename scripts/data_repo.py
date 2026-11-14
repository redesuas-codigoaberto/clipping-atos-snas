"""Paths of the sibling data repository (../atos-snas-data), which keeps the 2004-2025 backfill and its clippings.

Only the backfill scripts use it; the daily run, the pages and the tests read data/ in this repository,
so they work without the sibling directory. The paths are relative to the root of this repository,
where the scripts run from.
"""

from pathlib import Path

ROOT = Path('../atos-snas-data')
RAW_XML = ROOT / 'raw' / 'xml'
RAW_HTML = ROOT / 'raw' / 'html'
DAYS = ROOT / 'dados'
CLIPPINGS = ROOT / 'clippings'


def year_dir(days_dir, day):
    """The folder of the DD-MM-AAAA `day`: each year keeps its indexes and texts as data/ does."""
    return Path(days_dir) / day[-4:]
