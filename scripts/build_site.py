#!/usr/bin/env python3
"""Build the clipping pages: one page per day, and clipping.html with the latest one."""

import argparse
import datetime as dt
import html
import re
import shutil
from pathlib import Path
from zoneinfo import ZoneInfo

MONTH_NAMES = (
    'janeiro',
    'fevereiro',
    'março',
    'abril',
    'maio',
    'junho',
    'julho',
    'agosto',
    'setembro',
    'outubro',
    'novembro',
    'dezembro',
)
WEEKDAYS = ('segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo')

PAGE = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Clipping DOU – {title}</title>
<style>
:root {{ color-scheme: light dark; --line: #8884; --muted: #888; }}
body {{ font: 15px/1.6 system-ui, sans-serif; max-width: 860px; margin: 0 auto; padding: 24px 18px 60px; }}
header {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
header h1 {{ font-size: 20px; margin: 0; flex: 1; }}
nav a, button {{ font: inherit; padding: 4px 12px; border: 1px solid var(--line); border-radius: 6px;
  background: none; color: inherit; text-decoration: none; cursor: pointer; }}
nav a.off {{ opacity: .35; pointer-events: none; }}
.note {{ color: var(--muted); font-size: 13px; margin: 8px 0 18px; }}
.email {{ border: 1px solid var(--line); border-radius: 8px; padding: 18px 22px; }}
.email p {{ margin: 0 0 12px; }}
#copied {{ color: var(--muted); font-size: 13px; }}
details {{ margin-top: 28px; }}
details ul {{ columns: 3 180px; padding-left: 18px; }}
</style>
</head>
<body>
<header>
  <h1>Clipping DOU – {title}</h1>
  <nav><a href="{prev}" class="{prev_class}" title="Dia anterior">‹</a>
    <a href="{next}" class="{next_class}" title="Próximo dia">›</a></nav>
  <button id="copy">Copiar</button><span id="copied"></span>
  <nav><a href="relatorio.html">Relatório</a></nav>
</header>
<p class="note">Gerado automaticamente a partir do Diário Oficial da União.
A seleção procura nomes e expressões, sem interpretar o assunto do ato: confira antes de usar.
Atualizado em {updated}.</p>
<div class="email" id="email">
{body}
</div>
<details>
  <summary>Clippings anteriores</summary>
  <ul>
{archive}
  </ul>
</details>
<script>
document.getElementById('copy').onclick = async () => {{
  const el = document.getElementById('email');
  try {{
    await navigator.clipboard.write([new ClipboardItem({{
      'text/html': new Blob([el.innerHTML], {{ type: 'text/html' }}),
      'text/plain': new Blob([el.innerText], {{ type: 'text/plain' }}),
    }})]);
  }} catch {{
    const range = document.createRange();
    range.selectNodeContents(el);
    getSelection().removeAllRanges(); getSelection().addRange(range);
    document.execCommand('copy');
    getSelection().removeAllRanges();
  }}
  const note = document.getElementById('copied');
  note.textContent = 'Copiado. Cole no email.';
  setTimeout(() => {{ note.textContent = ''; }}, 3000);
}};
</script>
</body>
</html>
"""


def link(match):
    # The URL was escaped with the rest of the text; only its quotes still need escaping inside the attribute.
    url = match.group(2).replace('"', '&quot;')
    return f'<a href="{url}">{match.group(1)}</a>'


def inline(text):
    """Render the only inline Markdown clipping.py writes: **bold** and [text](url)."""
    text = html.escape(text, quote=False)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', link, text)


def to_html(markdown):
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', markdown) if p.strip()]
    return '\n'.join(f'<p>{inline(p)}</p>' for p in paragraphs)


def long_date(day):
    return f'{WEEKDAYS[day.weekday()]}, {day.day} de {MONTH_NAMES[day.month - 1]} de {day.year}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clippings-dir', type=Path, default=Path('clipping-novo'))
    parser.add_argument('-o', '--output-dir', type=Path, default=Path('site'))
    args = parser.parse_args()
    days = sorted(dt.date.fromisoformat(path.stem) for path in args.clippings_dir.glob('????-??-??.md'))
    if args.output_dir.exists():
        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True)
    if not days:
        (args.output_dir / 'clipping.html').write_text(
            '<!doctype html><meta charset="utf-8"><title>Clipping DOU</title><p>Ainda não há clippings.</p>\n',
            encoding='utf-8',
        )
        print(f'{args.output_dir}: no clippings yet')
        return
    updated = dt.datetime.now(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
    archive = '\n'.join(f'    <li><a href="{day}.html">{day:%d/%m/%Y}</a></li>' for day in reversed(days))
    for i, day in enumerate(days):
        prev_day = days[i - 1] if i else None
        next_day = days[i + 1] if i + 1 < len(days) else None
        page = PAGE.format(
            title=long_date(day),
            updated=updated,
            archive=archive,
            body=to_html((args.clippings_dir / f'{day}.md').read_text(encoding='utf-8')),
            prev=f'{prev_day}.html' if prev_day else '#',
            prev_class='' if prev_day else 'off',
            next=f'{next_day}.html' if next_day else '#',
            next_class='' if next_day else 'off',
        )
        (args.output_dir / f'{day}.html').write_text(page, encoding='utf-8')
    shutil.copy(args.output_dir / f'{days[-1]}.html', args.output_dir / 'clipping.html')
    print(f'{args.output_dir}: {len(days)} clipping(s), latest {days[-1]}')


if __name__ == '__main__':
    main()
