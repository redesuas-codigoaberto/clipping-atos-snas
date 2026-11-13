# Nomes do ministério da SNAS no DOU (2004–2026)

A Secretaria Nacional de Assistência Social (SNAS) manteve o nome desde 2004, mas o ministério ao qual pertence mudou cinco vezes. O DOU classifica cada ato pelo órgão: o primeiro nível é o ministério e os seguintes são as unidades, como em `Ministério do Desenvolvimento Social e Combate à Fome/SECRETARIA NACIONAL DE ASSISTÊNCIA SOCIAL`. Para selecionar os atos de cada data, o scraper precisa saber o nome que o DOU usava naquele dia.

## Fontes por período

| Período | Fonte | Campo com o órgão |
|---|---|---|
| 01-01-2004 a 31-12-2017 | Arquivos XML mensais dos [dados abertos da Imprensa Nacional](https://www.in.gov.br/acesso-a-informacao/dados-abertos/base-de-dados), um por seção | `artCategory`, com os níveis separados por `/` |
| 01-01-2018 em diante | Página de leitura do jornal (`https://www.in.gov.br/leiturajornal`), a mesma do fluxo diário | `hierarchyList` |

Antes de 2018 a página de leitura não serve. Nas datas testadas de 2004 a 2012 ela não devolveu nenhum ato; nas de 2013 a novembro de 2017, devolveu só parte da edição ou nada. Em 01-11-2017, por exemplo, listou 237 atos nas seções 1 e 2; em 01-12-2017, 1.100.

## Nomes e datas de troca

As datas abaixo são a primeira e a última edição em que cada nome aparece como primeiro nível nas seções 1 e 2 do DOU. Elas foram medidas nos próprios arquivos e não coincidem com as datas das normas, porque a Imprensa Nacional demorou dias ou semanas para atualizar a classificação.

| Nome no DOU | Primeira edição | Última edição |
|---|---|---|
| Ministério da Assistência Social | antes de 2004 | 02-02-2004 |
| Ministério do Desenvolvimento Social e Combate à Fome | 04-02-2004 | 13-05-2016 |
| Ministério do Desenvolvimento Social e Agrário | 16-05-2016 | 13-07-2017 |
| Ministério do Desenvolvimento Social | 14-07-2017 | 02-01-2019 |
| Ministério da Cidadania | 03-01-2019 | 24-01-2023 |
| Ministério do Desenvolvimento e Assistência Social, Família e Combate à Fome | 03-01-2023 | em uso |

De 03-01-2023 a 24-01-2023 os dois últimos nomes convivem, e há atos novos classificados ainda no Ministério da Cidadania. Nesse intervalo o scraper precisa aceitar os dois.

As normas que mudaram o nome são, segundo busca na web e ainda sem conferência no texto de cada uma, a MP 163/2004 (Lei 10.869/2004), a MP 726/2016 (Lei 13.341/2016), a MP 782/2017 (Lei 13.502/2017), a MP 870/2019 (Lei 13.844/2019) e a MP 1.154/2023.

## Particularidades da classificação

- **Maiúsculas.** Até 2017, os níveis abaixo do ministério vêm em maiúsculas (`SECRETARIA NACIONAL DE ASSISTÊNCIA SOCIAL`); a partir de 2018, em caixa normal. A comparação com os órgãos de `DIRECT_ORGS` precisa ignorar a caixa.
- **SNAS um nível abaixo (2019–2022).** No Ministério da Cidadania, a SNAS ficava sob a Secretaria Especial do Desenvolvimento Social: `Ministério da Cidadania/Secretaria Especial do Desenvolvimento Social/Secretaria Nacional de Assistência Social`.
- **Atos fora do ministério.** Há atos da SNAS classificados em outro ministério, como `Ministério de Minas e Energia/SECRETARIA NACIONAL DE ASSISTÊNCIA SOCIAL` (junho de 2010), e atos com uma unidade da SNAS no primeiro nível, como `Departamento da Rede Socioassistencial Privada do Sistema Único de Assistência Social` (01-02-2018). O filtro pelo nome do ministério sozinho os perde; eles só entram se o scraper também aceitar atos em que qualquer nível nomeia uma unidade da SNAS.

## Lacunas do arquivo XML

O inventário de 2004 a 2017 encontrou todas as três seções em todos os meses, exceto:

| Falta | Meses |
|---|---|
| Seção 1 | março a julho de 2015 |
| Seção 3 | janeiro a dezembro de 2017 |

A seção 1 traz os atos normativos, como portarias e resoluções, então os clippings de março a julho de 2015 ficam incompletos até que se encontre outra fonte para esses meses. Na página de dados abertos, o mês de março só aparece com o nome codificado na URL (`mes=Mar%C3%A7o`).
