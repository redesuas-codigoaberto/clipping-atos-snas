#!/usr/bin/env python3
"""Build the offline HTML report comparing the clipping rule with the manual clippings."""

import argparse
import base64
import datetime as dt
import gzip
import json
import re
import shutil
from pathlib import Path

import dates
from clipping import MDS, assess_day, clipping_text, excerpt, identifier

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / 'templates' / 'report.html'
# Fonts and the gov.br logo the pages load, copied next to them.
ASSETS = ROOT / 'assets'
RULES = ROOT / 'docs' / 'regras.md'
MANUAL_DATE = re.compile(r'DOU-\s*(\d{2})/(\d{2})/(\d{4})')
# A cited act: [title](https://www.in.gov.br/[en/]web/dou/-/slug-123456789) followed by its description.
MANUAL_ENTRY = re.compile(
    r'\[([^\]]+)\]\((https?://(?:www\.)?in\.gov\.br/(?:en/)?web/dou/-/[^)\s>]*?-(\d{9}))\)([^\n]*)'
)


def index_days(data_dir):
    """The edition days with an index in data_dir, in date order."""
    return sorted((path.stem for path in Path(data_dir).glob(f'{dates.GLOB}.json')), key=dates.parse)


def load_manual_clippings(examples_dir):
    """Map each edition date (DD-MM-AAAA) to its manual clipping files and the acts they cite.

    Each act is {'id', 'title', 'url', 'text'}, where text is the description the CGREGS wrote.
    """
    clippings = {}
    for path in sorted(Path(examples_dir).glob('*.md')):
        text = path.read_text(encoding='utf-8', errors='replace')
        match = MANUAL_DATE.search(text)
        if not match:
            continue
        entry = clippings.setdefault(f'{match[1]}-{match[2]}-{match[3]}', {'sources': [], 'acts': {}})
        entry['sources'].append(path.name)
        for title, url, act_id, description in MANUAL_ENTRY.findall(text):
            entry['acts'].setdefault(
                act_id,
                {
                    'id': act_id,
                    'title': re.sub(r'\s+', ' ', title).strip(),
                    'url': url,
                    'text': re.sub(r'^[\s*:]+', '', description).strip(),
                },
            )
    return clippings


def manual_email(examples_dir, source):
    """The body of a manual clipping email: the text after the metadata header."""
    return (Path(examples_dir) / source).read_text(encoding='utf-8', errors='replace').split('\n---\n', 1)[-1].strip()


def email_key(text):
    """Normalize an email body so that formatting-only differences do not count."""
    text = text.replace('**', '').replace('\\$', '$').replace('/en/web', '/web')
    return re.sub(r'\s+', ' ', text.replace('https://in.gov', 'https://www.in.gov')).strip()


def compare_emails(generated, manual_bodies, manual_ids):
    """'identical', 'same_acts' or 'different' when there is a manual clipping, else None."""
    if not manual_bodies:
        return None
    if {match[2] for match in MANUAL_ENTRY.findall(generated)} != set(manual_ids):
        return 'different'
    if len(manual_bodies) == 1 and email_key(generated) == email_key(manual_bodies[0]):
        return 'identical'
    return 'same_acts'


def short_org(hierarchy):
    """The unit right below the ministry, or the top body for outside acts."""
    if MDS in hierarchy:
        position = hierarchy.index(MDS)
        return hierarchy[position + 1] if position + 1 < len(hierarchy) else MDS
    return hierarchy[0] if hierarchy else ''


def build_model(data_dir, examples_dir):
    manual = load_manual_clippings(examples_dir)
    cited = {act_id for entry in manual.values() for act_id in entry['acts']}
    # Acts outside the MDS that the manual clippings cite; the slim indexes keep only MDS acts.
    located_path = Path(data_dir) / 'located.json'
    located = json.loads(located_path.read_text(encoding='utf-8')) if located_path.exists() else {}
    days, texts = [], {}
    for day in index_days(data_dir):
        index = json.loads((Path(data_dir) / f'{day}.json').read_text(encoding='utf-8'))
        for article in index['articles']:
            act_id = identifier(article)
            if act_id in cited and act_id not in located:
                located[act_id] = {
                    'date': day,
                    'title': article.get('title', ''),
                    'organization': article.get('hierarchyStr', ''),
                }
        day_manual = manual.get(day, {'sources': [], 'acts': {}})
        candidates = []
        assessed = assess_day(day, index, data_dir)
        generated, _ = clipping_text(dates.parse(day), assessed)
        for item in assessed:
            article, full_text = item['article'], item['full_text']
            act_id = identifier(article)
            sent = act_id in day_manual['acts'] if day_manual['sources'] else None
            candidate = {
                'id': act_id,
                'title': article['title'],
                'url': article['url'],
                'org': article.get('hierarchyStr', ''),
                'unit': short_org(article.get('hierarchyList', [])),
                'section': article.get('pubName', ''),
                'page': article.get('numberPage', ''),
                'type': article.get('artType', ''),
                'suggestion': item['suggestion'],
                'reasons': item['reasons'],
                'manual': sent,
                'excerpt': excerpt(article, full_text),
                'full': bool(full_text),
            }
            if sent:
                candidate['manualText'] = day_manual['acts'][act_id]['text']
            candidates.append(candidate)
            texts[act_id] = full_text or re.sub(r'\s+', ' ', article.get('content', '')).strip()
        known = {candidate['id'] for candidate in candidates}
        bodies = [manual_email(examples_dir, source) for source in day_manual['sources']]
        days.append(
            {
                # The page script compares, sorts and splits dates as AAAA-MM-DD, and <input type="date">
                # works in that format, so the model keeps it; the page shows and links them as DD-MM-AAAA.
                'date': dates.parse(day).isoformat(),
                'total': index.get('count', len(index['articles'])),
                'candidates': candidates,
                'manualSources': day_manual['sources'],
                'clipping': generated,
                'manualEmail': '\n\n---\n\n'.join(bodies),
                'emailMatch': compare_emails(generated, bodies, day_manual['acts']),
                'manualMissing': [day_manual['acts'][act_id] for act_id in sorted(set(day_manual['acts']) - known)],
            }
        )
    # Acts published after the clipping that cites them are located only after the full scan.
    for day in days:
        for missing in day['manualMissing']:
            found = located.get(missing['id'])
            missing['located'] = found and {**found, 'date': dates.parse(found['date']).isoformat()}
    rules = RULES.read_text(encoding='utf-8') if RULES.exists() else ''
    return {
        'generated': dt.datetime.now().astimezone().isoformat(timespec='seconds'),
        'days': days,
        'texts': texts,
        'rules': rules,
    }


def clipping_model(model):
    """Keep only what the clipping-only page reads: the generated email of each day."""
    keep = ('date', 'total', 'manualSources', 'clipping')
    days = [
        {**{key: day[key] for key in keep if key in day}, 'candidates': [], 'manualMissing': []}
        for day in model['days']
    ]
    return {'generated': model['generated'], 'days': days, 'texts': {}, 'rules': ''}


def write_page(path, model, only=''):
    payload = base64.b64encode(gzip.compress(json.dumps(model, ensure_ascii=False).encode('utf-8'), 9))
    html = TEMPLATE.read_text(encoding='utf-8').replace('__MODEL__', payload.decode('ascii'), 1)
    html = html.replace('__ONLY__', only, 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding='utf-8')
    return path.stat().st_size / 1e6


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path('data'))
    parser.add_argument('--examples-dir', type=Path, default=Path('clipping-antigo'))
    parser.add_argument('-o', '--output', type=Path, default=Path('site/relatorio.html'))
    parser.add_argument(
        '--clipping-output',
        type=Path,
        default=Path('site/index.html'),
        help='copy of the report with only the Clipping tab',
    )
    args = parser.parse_args()
    model = build_model(args.data_dir, args.examples_dir)
    size = write_page(args.output, model)
    candidates = sum(len(day['candidates']) for day in model['days'])
    print(f'{args.output}: {len(model["days"])} days, {candidates} candidates, {size:.1f} MB')
    size = write_page(args.clipping_output, clipping_model(model), only='clipping')
    print(f'{args.clipping_output}: Clipping tab only, {size:.1f} MB')
    for page in {args.output.parent, args.clipping_output.parent}:
        shutil.copytree(ASSETS, page, dirs_exist_ok=True)


if __name__ == '__main__':
    main()
