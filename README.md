# Clipping de atos da SNAS

Este repositório gera todo dia o clipping das publicações do Diário Oficial da União (DOU) de interesse da Secretaria Nacional de Assistência Social (SNAS) e o publica no GitHub Pages.

O clipping é gerado automaticamente. A regra procura nomes e expressões nos atos do Ministério do Desenvolvimento e Assistência Social, Família e Combate à Fome (MDS), sem interpretar o assunto de cada um. Confira o clipping antes de usar.

## Como funciona

O workflow `.github/workflows/clipping.yml` roda duas vezes por dia, no horário de Brasília:

- às 8h05, depois da edição regular do DOU;
- às 11h05, de reserva. Essa execução cobre quedas mais longas do site do DOU e execuções agendadas que o GitHub não fez, e inclui as edições extras publicadas de manhã. Ela só faz commit se os atos coletados ou o clipping mudaram. Por isso, o clipping de um dia pode mudar depois das 8h05.

O GitHub pode atrasar execuções agendadas em alguns minutos. Edições extras publicadas depois das 11h05 ficam fora do clipping. Para incluí-las, rode o workflow à mão (veja abaixo).

Cada execução, com os scripts de `scripts/`:

1. coleta o índice da edição do dia (`scrape.py`);
2. baixa o texto dos atos do MDS (`save_articles.py`);
3. grava o email do clipping em `clipping-novo/AAAA-MM-DD.md` (`clipping.py`);
4. faz commit dos atos coletados e do clipping;
5. roda os testes (veja “Desenvolvimento”); se algum falhar, os dados ficam salvos, mas nada é publicado;
6. gera as páginas do clipping (`build_site.py`) e o relatório (`report.py`) e publica tudo no GitHub Pages.

`daily.py` executa os três primeiros passos. Em datas sem edição, como fins de semana e feriados, ele não grava clipping, e a execução termina sem erro. Num dia útil sem edição, a execução também termina sem erro, mas abre a issue “Dia útil sem atos no DOU”, porque o mesmo resultado apareceria se o site do DOU mudasse e a coleta deixasse de achar os atos. Se foi feriado ou ponto facultativo, basta fechar a issue. O resumo da execução, na página do workflow, mostra quantos atos a edição teve, quantos são do MDS e quantos entraram no clipping.

Quando o site do DOU falha, cada download é repetido algumas vezes em cerca de 30 segundos. Se ainda assim a coleta falhar, o workflow espera 10 minutos e roda `daily.py` de novo, até três tentativas. Os atos já baixados não são baixados de novo. Se as três tentativas falharem, a execução falha.

Quando uma execução falha, o workflow abre a issue “Falha no clipping diário”, com o link da execução. Assim, toda a organização fica sabendo, e não só quem configurou o agendamento, que é a única pessoa que o GitHub avisa por email. Enquanto a issue estiver aberta, as novas falhas viram comentários nela. Depois de corrigir, rode o workflow à mão e feche a issue.

## Arquivos versionados

| Caminho | Conteúdo |
| --- | --- |
| `data/AAAA-MM-DD.json` | Atos do MDS da edição, com `count` igual ao total de atos publicados no DOU naquele dia. |
| `data/AAAA-MM-DD/*.md` | Texto de cada ato do MDS. |
| `data/located.json` | Data e órgão dos atos de fora do MDS citados nos clippings manuais de 2026, tirados dos índices completos do DOU. |
| `clipping-novo/AAAA-MM-DD.md` | Email do clipping gerado. |
| `clipping-antigo/*.md` | Clippings enviados pela equipe, sem o cabeçalho do email. |
| `docs/regras.md` | Explicação das regras, exibida na aba Regras do relatório. |
| `scripts/` | Os scripts do clipping, das páginas e do relatório. |
| `templates/report.html` | Modelo das páginas do relatório. |
| `tests/` | Testes automáticos (veja “Desenvolvimento”). |

O índice guarda só os atos do MDS, porque são os únicos avaliados. O índice completo de um dia tem cerca de 3 MB; o enxuto, poucos KB.

## As páginas

A página inicial (`index.html`) mostra só o email gerado pelo programa, com o botão **Copiar** e com setas e calendário para trocar de dia.

`relatorio.html` é o relatório completo, que compara a seleção da regra com os clippings enviados pela equipe em cinco abas: Análise ano, Regras, Clipping, Comparativo resumos e Análise dia. As duas páginas são recalculadas a cada execução.

`clipping.html` mostra só o clipping mais recente, para copiar sem abrir o relatório. Cada dia também tem sua própria página (`AAAA-MM-DD.html`), e as setas passam de um dia para outro. O botão **Copiar** copia o email com a formatação, pronto para colar.

As páginas do GitHub Pages são públicas.

## Acrescentar clippings manuais

O GitHub Actions não tem acesso ao Outlook. Para a comparação com a equipe avançar, exporte os emails do clipping em Markdown e copie-os para `clipping-antigo/`:

```bash
python scripts/add_manual.py "/caminho/20261112T150000 Clipping DOU-12_11_2026.md"
git add clipping-antigo && git commit -m "Add manual clippings" && git push
```

`add_manual.py` mantém só o título e o corpo do email. Remetente, destinatários e identificador da mensagem não são copiados. O relatório é atualizado na próxima execução do workflow, ou na hora, se você rodá-lo à mão.

Se um clipping manual citar um ato de fora do MDS publicado depois de 2026-11-12, o relatório mostra o ato como não encontrado nos índices, porque o índice enxuto não guarda os outros órgãos.

## Configuração no GitHub

1. Crie o repositório no GitHub e envie este conteúdo.
2. Em **Settings → Pages**, escolha **GitHub Actions** em **Source**.
3. Em **Actions → Clipping diário → Run workflow**, rode o workflow uma vez para testar. O campo de data aceita `AAAA-MM-DD`; vazio, usa a data de hoje.

O GitHub desativa execuções agendadas depois de 60 dias sem atividade no repositório. Os commits diários dos clippings mantêm o repositório ativo.

## Executar localmente

Requer Python 3.12 ou superior, sem pacotes externos.

```bash
python scripts/daily.py                    # edição de hoje
python scripts/daily.py --date 2026-11-05  # outra data
python scripts/build_site.py               # grava as páginas do clipping em site/
python scripts/report.py                   # grava site/relatorio.html e site/index.html (depois de build_site.py, que limpa site/)
```

Para ver no navegador o mesmo site que vai para o GitHub Pages:

```bash
make serve             # gera site/ e serve em http://localhost:8000/
make serve PORT=8080   # outra porta
```

## Desenvolvimento

As verificações usam o [ruff](https://docs.astral.sh/ruff/) e o [pytest](https://docs.pytest.org/), instalados pelo [uv](https://docs.astral.sh/uv/) nas versões de `uv.lock`. O clipping continua sem pacotes externos; só as verificações precisam do uv.

```bash
make             # lista as tarefas
make check       # o mesmo que o workflow de verificações: ruff e testes
make test        # só os testes
make lint        # só o ruff, sem alterar nada
make format      # corrige o que o ruff consegue e formata o código
make regenerate  # regrava clipping-novo/ a partir de data/ com as regras atuais
```

O workflow `.github/workflows/ci.yml` roda o ruff e os testes, no Python 3.12, a cada push e pull request. O Dependabot propõe todo mês a atualização das actions e das ferramentas.

Os testes comparam o resultado das regras com o arquivo de 2026:

- cada clipping de `clipping-novo/` tem de ser igual ao que as regras atuais geram a partir de `data/`;
- a concordância com os clippings da equipe (`clipping-antigo/`) não pode cair abaixo da medida em 12/11/2026: 60 emails idênticos, 101 com os mesmos atos e 305 dos 307 atos do MDS enviados pela equipe sugeridos pela regra.

Ao mudar uma regra de propósito, rode `make regenerate` e confira no diff quais clippings antigos mudaram. Se a concordância melhorar, atualize os números mínimos em `tests/test_archive.py`.

## Licença

Este projeto é distribuído sob a [GNU General Public License v3.0](LICENSE).
