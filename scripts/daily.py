#!/usr/bin/env python3
"""Collect one DOU edition and write its SNAS clipping.

Runs scrape.py, save_articles.py and clipping.py in order. A date without any
published article (weekends, holidays) is not an error: no clipping is written.
A failed download is an error, so the scheduled run shows up as failed.
"""

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import dates

HERE = Path(__file__).resolve().parent


def run(*args):
    subprocess.run([sys.executable, str(HERE / args[0]), *args[1:]], check=True)


def no_edition_warning(day):
    """A warning when a weekday has no articles, or None.

    Weekday holidays (Carnaval, Tiradentes, 7 de Setembro...) are expected, so this does not fail the run;
    but the same result would show if the DOU site changed and the scraper found no articles at all.
    """
    if day.weekday() >= 5:
        return None
    return f'{dates.name(day)}: no DOU articles on a weekday; check whether it was a holiday or the site changed'


def selected_count(clipping_path):
    """Number of acts in a clipping written by clipping.py: each one is a paragraph starting with its link."""
    return sum(line.startswith('[') for line in clipping_path.read_text(encoding='utf-8').splitlines())


def write_output(name, value):
    """Set a step output, read by later workflow steps as steps.<id>.outputs.<name>, when running there."""
    path = os.environ.get('GITHUB_OUTPUT')
    if path:
        with open(path, 'a', encoding='utf-8') as output:
            output.write(f'{name}={value}\n')


def write_summary(lines):
    """Append Markdown to the GitHub Actions job summary, when running there."""
    path = os.environ.get('GITHUB_STEP_SUMMARY')
    if path:
        with open(path, 'a', encoding='utf-8') as summary:
            summary.write('\n'.join(lines) + '\n')


def main():
    today = dt.datetime.now(ZoneInfo('America/Sao_Paulo')).date()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date', type=dates.argument, default=today)
    parser.add_argument('--data-dir', type=Path, default=Path('data'))
    parser.add_argument('--output-dir', type=Path, default=Path('clipping-novo'))
    args = parser.parse_args()
    day = dates.name(args.date)
    run('scrape.py', '--date', day, '--output-dir', str(args.data_dir))
    index_path = args.data_dir / f'{day}.json'
    index = json.loads(index_path.read_text(encoding='utf-8'))
    summary = [f'## Clipping {day}', '', f'- Atos na edição: {index["count"]}']
    if index['count'] == 0:
        print(f'{day}: no DOU edition published; no clipping written')
        warning = no_edition_warning(args.date)
        if warning:
            # A workflow command: GitHub shows it as a warning annotation on the run page.
            print(f'::warning::{warning}')
            # The workflow opens an issue from it, so that the warning reaches someone.
            write_output('warning', warning)
        write_summary([*summary, '- Sem edição publicada; nenhum clipping gravado.'])
        return
    run('save_articles.py', str(index_path), '--output-dir', str(args.data_dir))
    run('clipping.py', day, '--data-dir', str(args.data_dir), '--output-dir', str(args.output_dir))
    selected = selected_count(args.output_dir / f'{day}.md')
    write_summary([*summary, f'- Atos do MDS: {len(index["articles"])}', f'- Atos no clipping: {selected}'])


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
