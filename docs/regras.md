# Regras do clipping automático

O clipping automático monta, para cada edição do Diário Oficial da União (DOU), o texto do email do clipping no formato que a Coordenação-Geral de Regulação do Acesso e Assuntos Normativos do SUAS (CGREGS) envia. O email traz a data, os atos selecionados e a assinatura. Cada ato aparece com o título, o link oficial e um resumo copiado do próprio ato. Quando nenhum ato é selecionado, o email diz: “Não há publicações de interesse da SNAS.”

**Confira o clipping antes de usar.** O programa procura nomes e expressões no texto dos atos, mas não entende o assunto. Em 2026, nos dias em que a equipe enviou clipping, quase metade dos atos selecionados pelo programa não constava do email enviado (veja “Resultados em 2026”).

## Quais atos entram

O programa examina somente os atos do Ministério do Desenvolvimento e Assistência Social, Família e Combate à Fome (MDS). Entram no clipping:

1. todos os atos publicados pela Secretaria Nacional de Assistência Social (SNAS), pelo Conselho Nacional de Assistência Social (CNAS), pela Comissão Intergestores Tripartite (CIT) do Sistema Único de Assistência Social (SUAS) ou pelo Departamento da Rede Socioassistencial Privada do SUAS;
2. os outros atos do MDS que mencionam, no título ou no texto, qualquer destas expressões:
   - SNAS, CNAS ou SUAS;
   - “Sistema Único de Assistência Social”;
   - “Secretaria Nacional de Assistência Social”, também nas formas “Secretária” e “Secretário”, com ou sem acento;
   - “proteção social básica” ou “proteção social especial”.

As siglas só são reconhecidas em letras maiúsculas, porque “suas” também é pronome. Quando um ato escreve “Suas”, em geral o nome por extenso aparece no mesmo texto.

Atos de outros órgãos não entram, mesmo quando citam a SNAS, o CNAS ou o SUAS. Em 2026 houve 9 casos assim, quase todos contratos e licitações de prefeituras, e nenhum interessava ao clipping.

## Como o resumo é escolhido

O programa não redige resumos. Ele copia, sem alterar, o trecho do ato que diz o que o ato faz, como a equipe faz no clipping manual. Para achar esse trecho, o programa olha o tipo de ato e como ele começa e segue o primeiro dos quatro casos abaixo que se aplica. Nos exemplos, o trecho destacado é o que vai para o resumo.

### 1. O ato tem ementa: o resumo é a ementa

A ementa é a frase que resume o ato. Ela vem logo depois do título e antes do preâmbulo, o parágrafo que apresenta a autoridade e termina em “resolve:”. Como o próprio ato já se resume na ementa, o programa a usa.

Exemplo: Resolução CIT nº 36, de 11 de fevereiro de 2026.

> **Altera a Resolução CIT nº 17, de 13 de dezembro de 2024.**
>
> A COMISSÃO INTERGESTORES TRIPARTITE - CIT, no uso das competências estabelecidas no Decreto nº 10.009, de 5 de setembro de 2019, […] resolve:
>
> Art. 1º A Resolução CIT nº 17, de 13 de dezembro de 2024, passa a vigorar com as seguintes alterações: […]

O artigo 1º diz o mesmo que a ementa, mas termina numa lista de alterações que não cabe no email.

### 2. O ato tem preâmbulo, mas não tem ementa: o resumo é o parágrafo depois de “resolve:”

É o caso comum de nomeações, designações e dispensas. Sem ementa, o que o ato decide está no parágrafo logo depois de “resolve:”. O programa copia esse parágrafo inteiro.

Em duas situações, a escolha da equipe varia, e o programa acrescenta mais um parágrafo. O resumo fica um pouco maior, mas passa a conter o trecho que a equipe costuma escolher, e o revisor só precisa cortar o que sobra:

- se o parágrafo anuncia uma alteração (“… passa a vigorar com a seguinte redação:”), entra também o parágrafo seguinte, com a nova redação;
- se o parágrafo traz outra decisão e um artigo seguinte começa com “Designar”, essa designação também entra.

Exemplo: Portaria/SAA/SE/MDS nº 661, de 4 de novembro de 2026.

> O SUBSECRETÁRIO DE ASSUNTOS ADMINISTRATIVOS SUBSTITUTO DA SECRETARIA-EXECUTIVA […], resolve:
>
> **Nomear a servidora MARIANA REIS DE SOUZA LIMA para exercer o Cargo Comissionado Executivo de Assistente Técnico, código CCE 2.03, da Coordenação-Geral de Proteção Social Especial de Média Complexidade, do Departamento de Proteção Social Especial, da Secretaria Nacional de Assistência Social, deste Ministério.**

### 3. Extrato de contrato: o resumo é o objeto do contrato

Nos extratos de contrato, a equipe copia o objeto, que diz o que está sendo contratado. Os demais campos (processo, pregão, contratante, contratado) ficam de fora. O programa procura o campo do objeto e para no campo seguinte (número do contrato, vigência, fundamento legal, valor ou data de assinatura). A forma do rótulo decide se ele entra no resumo, como faz a equipe:

- “OBJETO DA CONTRATAÇÃO:” entra no resumo;
- “Objeto:” sai, e o resumo começa no texto do objeto.

Exemplo com “Objeto:”: Extrato de Contrato nº 21/2026, de 27 de agosto de 2026.

> Nº Processo: 71000.051830/2026-91.
>
> Pregão Nº 90011/2025. Contratante: MINISTÉRIO DO DESENVOLVIMENTO E ASSISTÊNCIA SOCIAL FAMÍLIA E COMBATE À FOME.
>
> Contratado: 53.641.615/0001-63 - BRANDÃO VEICULOS LTDA. Objeto: **Aquisição de veículos tipo utilitário - caminhonete, para cargas acima de uma tonelada, destinados aos entes federativos por meio de doação, […]**
>
> Fundamento Legal: LEI 14.133/2021. Vigência: 25/08/2026 a 25/08/2027. […]

Exemplo com “OBJETO DA CONTRATAÇÃO:”: Extrato de Contrato de 11 de agosto de 2026, do projeto de cooperação com a UNESCO.

> MINISTÉRIO DO DESENVOLVIMENTO E ASSISTÊNCIA SOCIAL, FAMÍLIA E COMBATE À FOME Projeto UNESCO - 914BRZ3051.
>
> **OBJETO DA CONTRATAÇÃO: “Realizar a avaliação e proposição de melhorias nos processos de regulação do Sistema Único de Assistência Social (SUAS), […]”.**
>
> NÚMERO DO CONTRATO: SA-1461/2026

### 4. Outros atos sem preâmbulo: o resumo é o primeiro parágrafo com 80 caracteres ou mais, até “RECURSOS:”

Os demais extratos (de doação, de convênio, de termo aditivo e outros) não têm preâmbulo: são uma sequência de campos. O programa pula as linhas curtas, com menos de 80 caracteres, como “Nº Processo: …”, e usa o primeiro parágrafo mais longo. Quando esse parágrafo tem o campo “RECURSOS:”, o resumo para antes dele: ficam o processo, as partes e o objeto; saem o valor, o doador, o donatário e a data de assinatura.

Exemplo: Extrato de Doação nº 161/2026, de 20 de maio de 2026.

> **PROCESSO: 71000.013915/2026-71. Termo de Doação celebrado entre a União, por meio do Ministério do Desenvolvimento e Assistência Social, Família e Combate à Fome - MDS […] e o Município de Castelo do Piauí/PI, […]. OBJETO: Doação de 1 (um) veículo tipo Van com acessibilidade, Modelo Ducato Multi, com a finalidade de transportar equipes multidisciplinares e usuários referenciados à Rede Proteção Social Básica e Especial, integrante do Sistema Único de Assistência Social - SUAS.** RECURSOS: Valor Global R$ 283.990,00 (duzentos e oitenta e três mil novecentos e noventa reais). DOADOR: UNIÃO, […]

### Ajustes no trecho escolhido

- Se o trecho começa repetindo o título do ato, o título sai, porque ele já aparece no link do email.
- Se o trecho termina em dois-pontos, porque apresentava uma lista ou tabela que não entra no email, os dois-pontos viram ponto.
- Trechos com mais de 1.500 caracteres são cortados. Isso acontece em poucas atas e extratos de parceria.

### Quando conferir o resumo com mais atenção

- **Resumos com dois trechos.** Nas duas situações descritas no caso 2, o resumo traz o anúncio da alteração e a nova redação, ou a decisão principal e a designação. Corte o que não interessar. Na Portaria MDS nº 71/2026, por exemplo, o resumo traz o anúncio e a nova redação, e a equipe usou só o começo da nova redação.
- **Resumos que não trazem o trecho de interesse.** Em 2026, isso aconteceu em 15 dos 305 atos enviados que o programa também selecionou: a equipe preferiu o artigo 1º à ementa, copiou o preâmbulo, montou o texto à mão ou copiou uma lista inteira. Nesses casos, consulte o ato.

## Resultados em 2026

Para avaliar as regras, comparamos o clipping automático com os clippings enviados pela equipe nos 151 dias de 2026 em que houve envio:

| Comparação | Resultado |
|---|---|
| Dias em que o clipping automático traria os mesmos atos do clipping enviado | 101 de 151 |
| Dias em que o email automático seria idêntico ao enviado | 60 de 151 |
| Atos enviados que o programa também selecionou | 305 de 307 |
| Atos selecionados pelo programa que não foram enviados | 259 de 564 |
| Resumos idênticos aos do clipping enviado, entre os 305 atos | 260 (85%) |
| Resumos que contêm o trecho escolhido pela equipe, entre os 305 atos (basta cortar o que sobra) | 290 (95%) |

Os clippings enviados citaram 310 atos. Três deles tinham sido publicados em outra data e não entram na comparação, que por isso conta 307.

Dos 259 atos selecionados e não enviados, 203 são extratos do Gabinete do Ministro, em geral de termos de doação.

Os resumos diferentes vêm, em geral, de janeiro, quando a equipe resumia os extratos só pelo objeto, ou de escolhas pontuais, como copiar o preâmbulo em vez do artigo.

Dois atos enviados ficam de fora do clipping automático, porque não mencionam a SNAS nem o SUAS:

- a Portaria MDS nº 1.206/2026, que institui a Política de Gestão de Riscos do MDS;
- a Portaria MDS nº 109/2026, que nomeia o Chefe de Gabinete da Secretaria-Executiva.

Não criamos regra para esses casos. Nos mesmos dias, outras 14 portarias normativas do Gabinete do Ministro e outras 7 nomeações de chefe de gabinete não foram enviadas. Uma regra para pegar os dois atos selecionaria mais atos indevidos do que corretos.

O relatório do clipping automático mostra essa comparação ato por ato, nas abas Análise ano e Análise dia. Este texto também aparece lá, na aba Regras.
