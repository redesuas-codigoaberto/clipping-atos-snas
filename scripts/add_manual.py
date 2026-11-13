#!/usr/bin/env python3
"""Copy manual clipping emails (Markdown exported from Outlook) into clipping-antigo/, without the email header.

Only the title line ("# Clipping DOU-DD/MM/AAAA") and the body after the "---" separator are kept,
so the sender, the recipients and the message ID are never published.
"""

import argparse
from pathlib import Path


def sanitize(text):
    title = next((line for line in text.splitlines() if line.startswith('# ')), '')
    if '\n---\n' not in text or 'DOU' not in title:
        raise ValueError('not an exported clipping email (missing title or "---" separator)')
    body = text.split('\n---\n', 1)[1].strip()
    return f'{title}\n\n---\n\n{body}\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', type=Path, nargs='+', help='Exported .md emails')
    parser.add_argument('--output-dir', type=Path, default=Path('clipping-antigo'))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for path in args.files:
        try:
            text = sanitize(path.read_text(encoding='utf-8', errors='replace'))
        except ValueError as exc:
            print(f'Skipping {path}: {exc}')
            continue
        (args.output_dir / path.name).write_text(text, encoding='utf-8')
        print(args.output_dir / path.name)


if __name__ == '__main__':
    main()
