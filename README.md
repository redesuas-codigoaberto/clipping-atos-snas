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
3. grava o email do clipping em `clipping-novo/DD-MM-AAAA.md` (`clipping.py`);
4. faz commit dos atos coletados e do clipping;
5. roda os testes (veja “Desenvolvimento”); se algum falhar, os dados ficam salvos, mas nada é publicado;
6. gera as páginas (`report.py`) e as publica no GitHub Pages.

`daily.py` executa os três primeiros passos. Em datas sem edição, como fins de semana e feriados, ele não grava clipping, e a execução termina sem erro. Num dia útil sem edição, a execução também termina sem erro, mas abre a issue “Dia útil sem atos no DOU”, porque o mesmo resultado apareceria se o site do DOU mudasse e a coleta deixasse de achar os atos. Se foi feriado ou ponto facultativo, basta fechar a issue. O resumo da execução, na página do workflow, mostra quantos atos a edição teve, quantos são do MDS e quantos entraram no clipping.

Quando o site do DOU falha, cada download é repetido algumas vezes em cerca de 30 segundos. Se ainda assim a coleta falhar, o workflow espera 10 minutos e roda `daily.py` de novo, até três tentativas. Os atos já baixados não são baixados de novo. Se as três tentativas falharem, a execução falha.

Quando uma execução falha, o workflow abre a issue “Falha no clipping diário”, com o link da execução. Assim, toda a organização fica sabendo, e não só quem configurou o agendamento, que é a única pessoa que o GitHub avisa por email. Enquanto a issue estiver aberta, as novas falhas viram comentários nela. Depois de corrigir, rode o workflow à mão e feche a issue.

## Arquivos versionados

| Caminho | Conteúdo |
| --- | --- |
| `data/DD-MM-AAAA.json` | Atos do MDS da edição, com `count` igual ao total de atos publicados no DOU naquele dia. |
| `data/DD-MM-AAAA/*.md` | Texto de cada ato do MDS. |
| `data/located.json` | Data e órgão dos atos de fora do MDS citados nos clippings manuais de 2026, tirados dos índices completos do DOU. |
| `clipping-novo/DD-MM-AAAA.md` | Email do clipping gerado. |
| `clipping-antigo/*.md` | Clippings enviados pela equipe, sem o cabeçalho do email. |
| `docs/regras.md` | Explicação das regras, exibida na aba Regras do relatório. |
| `scripts/` | Os scripts do clipping, das páginas e do relatório. |
| `templates/report.html` | Modelo das páginas do relatório. |
| `assets/` | Fontes Rawline e logo do gov.br, copiadas para o site junto com as páginas. As fontes são distribuídas sob a SIL Open Font License 1.1 (`assets/fonts/OFL.txt`). |
| `tests/` | Testes automáticos (veja “Desenvolvimento”). |

Os nomes dos arquivos usam a data no formato DD-MM-AAAA. Por isso, a lista em ordem alfabética, como a do GitHub, não segue a ordem das datas.

O índice guarda só os atos do MDS, porque são os únicos avaliados. O índice completo de um dia tem cerca de 3 MB; o enxuto, poucos KB.

## As páginas

A página inicial (`index.html`) mostra só o email gerado pelo programa, com o botão **Copiar**, que copia o email com a formatação, pronto para colar, e com setas e calendário para trocar de dia.

`relatorio.html` é o relatório completo, que compara a seleção da regra com os clippings enviados pela equipe em cinco abas: Análise ano, Regras, Clipping, Comparativo resumos e Análise dia. As duas páginas são recalculadas a cada execução.

A aba Análise ano cobre só 2026, o ano da comparação com os clippings da equipe, e não será adaptada a outros anos. A partir de 2027, o calendário continua mostrando 2026, e os dias novos não aparecem nele.

As páginas seguem a identidade visual do gov.br: a fonte Rawline, as cores e os componentes do [Padrão Digital de Governo](https://www.gov.br/ds/), a barra do gov.br no topo e o rodapé em azul-escuro. O botão ◐ alterna entre o tema claro e o escuro.

As páginas do GitHub Pages são públicas.

## Acrescentar clippings manuais

O GitHub Actions não tem acesso ao Outlook. Para a comparação com a equipe avançar, exporte os emails do clipping em Markdown e copie-os para `clipping-antigo/`:

```bash
python scripts/add_manual.py "/caminho/20261112T150000 Clipping DOU-12_11_2026.md"
git add clipping-antigo && git commit -m "Add manual clippings" && git push
```

`add_manual.py` mantém só o título e o corpo do email. Remetente, destinatários e identificador da mensagem não são copiados. O relatório é atualizado na próxima execução do workflow, ou na hora, se você rodá-lo à mão.

Se um clipping manual citar um ato de fora do MDS publicado depois de 12/11/2026, o relatório mostra o ato como não encontrado nos índices, porque o índice enxuto não guarda os outros órgãos.

## Configuração no GitHub

1. Crie o repositório no GitHub e envie este conteúdo.
2. Em **Settings → Pages**, escolha **GitHub Actions** em **Source**.
3. Em **Actions → Clipping diário → Run workflow**, rode o workflow uma vez para testar. O campo de data aceita `DD-MM-AAAA`; vazio, usa a data de hoje.

O GitHub desativa execuções agendadas depois de 60 dias sem atividade no repositório. Os commits diários dos clippings mantêm o repositório ativo.

## Executar localmente

Requer Python 3.12 ou superior, sem pacotes externos.

```bash
python scripts/daily.py                    # edição de hoje
python scripts/daily.py --date 05-11-2026  # outra data
python scripts/report.py                   # grava site/index.html e site/relatorio.html
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
make dispatch    # roda agora o workflow diário no GitHub (DATE=DD-MM-AAAA para outra edição)
```

O workflow `.github/workflows/ci.yml` roda o ruff e os testes, no Python 3.12, a cada push e pull request. O Dependabot propõe todo mês a atualização das actions e das ferramentas.

Os testes comparam o resultado das regras com o arquivo de 2026:

- cada clipping de `clipping-novo/` tem de ser igual ao que as regras atuais geram a partir de `data/`;
- a concordância com os clippings da equipe (`clipping-antigo/`) não pode cair abaixo da medida em 12/11/2026: 60 emails idênticos, 101 com os mesmos atos e 305 dos 307 atos do MDS enviados pela equipe sugeridos pela regra.

Os testes também abrem as páginas geradas no Chrome (ou Chromium) instalado, em largura de celular e de desktop. Eles falham se houver erro de JavaScript, arquivo que não carrega ou conteúdo mais largo que a tela, e também conferem a janela de comparação num iPhone emulado. Sem navegador instalado, esses testes são pulados; nos workflows, que definem `REQUIRE_BROWSER`, eles falham. No workflow diário, os testes rodam antes da publicação, então uma página quebrada não vai ao ar.

Ao mudar uma regra de propósito, rode `make regenerate` e confira no diff quais clippings antigos mudaram. Se a concordância melhorar, atualize os números mínimos em `tests/test_archive.py`.

## Histórico de 2004 a 2025

O clipping de 2004 a 2025 sai de duas fontes, e o ministério da SNAS teve seis nomes nesse período (veja `docs/ministerios.md`, que também lista as lacunas das fontes). Os dados ficam no repositório vizinho `../atos-snas-data`, que os scripts abaixo usam por padrão (`scripts/data_repo.py`): os arquivos baixados em `raw/`, que o git ignora, e os índices e textos em `dados/<ano>/`, no mesmo formato de `data/`. Cada etapa retoma de onde parou ao ser executada de novo com os mesmos argumentos. Para parar, use Ctrl+C. Rode os comandos a partir da raiz do repositório.

```bash
# 2004 a 2017: arquivos XML mensais dos dados abertos da Imprensa Nacional (cerca de 10 GB de zips)
python scripts/dou_xml.py --start 01-01-2004 --end 29-11-2017

# 2018 em diante (e 30-11-2017 a 31-12-2017): página de leitura, sem filtrar, e depois índices e textos
python scripts/backfill_html.py --start 30-11-2017 --end 31-12-2025
python scripts/build_html_days.py --start 30-11-2017 --end 31-12-2025

make regenerate-historico   # grava ../atos-snas-data/clippings/<ano>/ a partir de dados/
```

Com um processo só, a página de leitura é lenta (cerca de 3 datas por minuto). Divida o período em faixas de dois anos e rode uma faixa em cada processo, em segundo plano. Na primeira execução, de 2018 a 2025, isso levou cerca de três horas. `build_html_days.py` ignora as datas que `backfill_html.py` ainda não terminou; rode-o de novo ao fim para pegar essas datas.

Este repositório não depende do vizinho: o fluxo diário, as páginas, o CI e os testes leem só `data/`. Só o histórico precisa de `../atos-snas-data`, que guarda também os clippings de 2004 a 2025 (`clippings/<ano>/`, gerados pelas regras atuais e ainda sem comparação com clippings da equipe), uma cópia de 2026 e o próprio README com o formato dos dados. Depois de mudar uma regra de seleção, rode `make regenerate-historico` para atualizar esses clippings.

## Licença

Este projeto é distribuído sob a [GNU General Public License v3.0](LICENSE).
