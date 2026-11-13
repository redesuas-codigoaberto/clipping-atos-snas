"""The date format of file names, command-line arguments and links: the Brazilian DD-MM-AAAA.

These names do not sort chronologically as text, so sort them with `parse` as the key.
"""

import argparse
import datetime as dt

FORMAT = '%d-%m-%Y'
# Glob for the files named after an edition, such as data/12-11-2026.json.
GLOB = '[0-3][0-9]-[01][0-9]-[0-9][0-9][0-9][0-9]'


def parse(text):
    """The date written as DD-MM-AAAA; raises ValueError for any other format."""
    return dt.datetime.strptime(text, FORMAT).date()


def name(date):
    """The date written as DD-MM-AAAA."""
    return date.strftime(FORMAT)


def argument(text):
    """`parse` for argparse, with an error message that shows the expected format."""
    try:
        return parse(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f'use a data no formato DD-MM-AAAA, como 12-11-2026, e não {text!r}') from None
