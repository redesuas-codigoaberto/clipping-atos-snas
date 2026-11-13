#!/usr/bin/env python3
"""Write the SNAS clipping email for one DOU edition from the local index."""

import argparse
import datetime as dt
import json
import re
from pathlib import Path

MDS = 'Ministério do Desenvolvimento e Assistência Social, Família e Combate à Fome'
DIRECT_ORGS = (
    'Secretaria Nacional de Assistência Social',
    'Conselho Nacional de Assistência Social',
    'Comissão Intergestores Tripartite do Sistema Único de Assistência Social',
    'Departamento da Rede Socioassistencial Privada do Sistema Único de Assistência Social',
)
TERMS = (
    (r'(?-i:\bSNAS\b)', 'mentions SNAS'),
    (r'(?-i:\bCNAS\b)', 'mentions CNAS'),
    (r'(?-i:\bSUAS\b)', 'mentions SUAS'),
    # Matches the body and its head's title (Secretária/Secretário), with or without the accent.
    (r'\bSecret[aá]ri[ao] Nacional de Assistência Social\b', 'mentions the national secretariat'),
    (r'\bSistema Único de Assistência Social\b', 'mentions SUAS by name'),
    (r'\bproteção social (?:básica|especial)\b', 'mentions social protection'),
)
SIGNATURE = (
    'Coordenação-Geral de Regulação do Acesso e Assuntos Normativos do SUAS – CGREGS',
    'Departamento de Gestão do Sistema Único de Assistência Social – DGSUAS',
    'Secretaria Nacional de Assistência Social – SNAS',
    'Ministério do Desenvolvimento e Assistência Social, Família e Combate à Fome – MDS',
)
NOTHING = 'Não há publicações de interesse da SNAS.'
# Safety cap for acts whose chosen paragraph is unusually long; manual summaries reach about 1,100 characters.
SUMMARY_LIMIT = 1500
MONTH_NAMES = (
    'Janeiro',
    'Fevereiro',
    'Março',
    'Abril',
    'Maio',
    'Junho',
    'Julho',
    'Agosto',
    'Setembro',
    'Outubro',
    'Novembro',
    'Dezembro',
)


def identifier(article):
    return article['urlTitle'].rsplit('-', 1)[-1]


def is_candidate(article):
    """Only acts published by the MDS are evaluated."""
    return MDS in article.get('hierarchyList', [])


def assess(article, full_text=''):
    """Return ('suggest' or 'review', reasons) for an MDS act."""
    hierarchy = article.get('hierarchyList', [])
    reasons = [f'organization: {org}' for org in DIRECT_ORGS if any(org in part for part in hierarchy)]
    if reasons:
        return 'suggest', reasons
    content = ' '.join(str(article.get(key, '')) for key in ('title', 'content')) + ' ' + full_text
    content = re.sub(re.escape(MDS), '', content, flags=re.I)
    reasons = [reason for pattern, reason in TERMS if re.search(pattern, content, re.I)]
    return ('suggest' if reasons else 'review'), reasons or ['no direct SNAS relevance signal']


CONTRACT_OBJECT_LABELED = re.compile(r'objeto da contrata[çc][ãa]o\s*:', re.I)
CONTRACT_OBJECT = re.compile(r'\bobjeto\s*:\s*', re.I)
CONTRACT_NEXT_FIELD = re.compile(
    r'\s+(?:N[úu]mero do Contrato|Vig[êe]ncia(?: do Contrato)?|Fundamento Legal|Valor(?: Total| do Contrato)?'
    r'|Data de Assinatura)\s*:',
    re.I,
)


def contract_object(blocks):
    """The object of an extrato de contrato, as the CGREGS copies it, or ''.

    "Objeto da contratação: ..." is copied with its label; a plain "Objeto: ..." without it.
    The text stops at the next contract field (number, term, legal basis, value or signature date).
    """
    for pattern, keep_label in ((CONTRACT_OBJECT_LABELED, True), (CONTRACT_OBJECT, False)):
        for block in blocks:
            match = pattern.search(block)
            if match:
                value = block[match.start() if keep_label else match.end() :]
                return CONTRACT_NEXT_FIELD.split(value, maxsplit=1)[0].strip()
    return ''


AMENDMENT_ANNOUNCEMENT = re.compile(r'seguinte reda[çc][ãa]o:?$')
DESIGNATION = re.compile(r'^(?:Art\.\s*\d+\S*\s+)?Designar\b')


def decision_paragraphs(blocks, first):
    """The paragraphs that state what an act without ementa decides, starting at `first`.

    The summaries are reviewed, so when the team's choice varies they err on the side of including it:
    - an amendment announcement ("... passa a vigorar com a seguinte redação:") also takes the new text;
    - when a designation ("Designar ...") comes after another decision, it is added too.
    """
    chosen = [blocks[first]]
    if AMENDMENT_ANNOUNCEMENT.search(blocks[first]) and first + 1 < len(blocks):
        chosen.append(blocks[first + 1])
    if not DESIGNATION.match(blocks[first]):
        later = next((block for block in blocks[first + 1 :] if DESIGNATION.match(block)), None)
        if later and later not in chosen:
            chosen.append(later)
    return chosen


def excerpt(article, full_text=''):
    """The act's description in the clipping, copied from the act the way the CGREGS does.

    - Acts with an ementa (the summary paragraph before the "... resolve:" preamble): the ementa.
    - Other acts with a preamble: the whole paragraph right after "resolve:" (see decision_paragraphs).
    - Extratos de contrato: the contract object (see contract_object).
    - Acts without a preamble, such as other extratos: the first long paragraph, up to the "RECURSOS:" field.
    """
    if full_text:
        body = full_text.split('Organization:', 1)[-1].split('\n\n', 1)[-1]
        blocks = [re.sub(r'\s+', ' ', block).strip() for block in re.split(r'\n\s*\n', body)]
        blocks = [block for block in blocks if block and not block.startswith('#')]
        resolution = next((i for i, block in enumerate(blocks) if block.rstrip().endswith('resolve:')), None)
        contract = contract_object(blocks) if article.get('artType', '').startswith('Extrato de Contrato') else ''
        if contract:
            value = contract
        elif resolution is not None and resolution > 0:
            value = blocks[0]
        elif resolution is not None and resolution + 1 < len(blocks):
            value = ' '.join(decision_paragraphs(blocks, resolution + 1))
        else:
            value = next((block for block in blocks if len(block) >= 80), blocks[0] if blocks else '')
    else:
        value = re.sub(r'\s+', ' ', article.get('content', '')).strip()
    title = article.get('title', '').strip()
    if value.casefold().startswith(title.casefold()):
        value = value[len(title) :].lstrip(' .:;–-')
    value = re.split(r'\s+RECURSOS\s*:', value, maxsplit=1)[0].strip()
    # A paragraph that introduces a list or table ends with a colon; the clipping ends it with a period.
    value = re.sub(r'\s*:$', '.', value)
    if len(value) > SUMMARY_LIMIT:
        value = value[: SUMMARY_LIMIT - 1].rsplit(' ', 1)[0] + '…'
    return value or 'Consultar o texto integral no DOU.'


def assess_day(day, index, data_dir):
    """Assess every candidate of one edition.

    Returns a list of dicts with the article, its local full text (or ''), the suggestion and the reasons.
    """
    results = []
    for article in index['articles']:
        if not is_candidate(article):
            continue
        markdown_path = Path(data_dir) / day / (article['urlTitle'].rsplit('/', 1)[-1] + '.md')
        full_text = markdown_path.read_text(encoding='utf-8') if markdown_path.exists() else ''
        suggestion, reasons = assess(article, full_text)
        results.append({'article': article, 'full_text': full_text, 'suggestion': suggestion, 'reasons': reasons})
    return results


def clipping_text(date, assessed):
    """The clipping email body, in the format the CGREGS sends."""
    lines = [f'**Brasília - DF, {date.day:02d} de {MONTH_NAMES[date.month - 1]} de {date.year}.**', '']
    selected = [item for item in assessed if item['suggestion'] == 'suggest']
    for item in selected:
        article = item['article']
        lines.extend([f'[{article["title"]}]({article["url"]}): {excerpt(article, item["full_text"])}', ''])
    if not selected:
        lines.extend([NOTHING, ''])
    for line in SIGNATURE:
        lines.extend([line, ''])
    return '\n'.join(lines).rstrip('\n') + '\n', len(selected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('date', type=dt.date.fromisoformat, help='DOU edition date (YYYY-MM-DD)')
    parser.add_argument('--data-dir', type=Path, default=Path('data'))
    parser.add_argument('--output-dir', type=Path, default=Path('clipping-novo'))
    args = parser.parse_args()
    day = args.date.isoformat()
    index_path = args.data_dir / f'{day}.json'
    index = json.loads(index_path.read_text(encoding='utf-8'))
    if index.get('date') != day:
        parser.error(f'Index date differs from requested date: {index_path}')
    text, count = clipping_text(args.date, assess_day(day, index, args.data_dir))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / f'{day}.md'
    output.write_text(text, encoding='utf-8')
    print(f'{output}: {count} ato(s)')


if __name__ == '__main__':
    main()
