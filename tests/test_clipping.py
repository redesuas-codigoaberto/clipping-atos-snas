"""The selection rule and the summary rule, case by case as docs/regras.md describes them."""

import datetime as dt

import pytest

from clipping import NOTHING, SIGNATURE, SUMMARY_LIMIT, assess, clipping_text, excerpt, identifier, is_candidate
from conftest import make_article, make_full_text

PREAMBLE = 'O SECRETÁRIO NACIONAL DE ASSISTÊNCIA SOCIAL, no uso das atribuições que lhe confere o Decreto, resolve:'


def test_identifier_is_the_numeric_suffix(article):
    assert identifier(article) == '123456789'


def test_only_mds_acts_are_candidates(article):
    assert is_candidate(article)
    assert not is_candidate({**article, 'hierarchyList': ['Ministério da Saúde']})


# --- selection ---


@pytest.mark.parametrize(
    'unit',
    [
        'Secretaria Nacional de Assistência Social',
        'Conselho Nacional de Assistência Social',
        'Comissão Intergestores Tripartite do Sistema Único de Assistência Social',
    ],
)
def test_acts_of_the_snas_bodies_are_suggested(unit):
    suggestion, reasons = assess(make_article(units=(unit, 'Departamento')))
    assert suggestion == 'suggest'
    assert reasons == [f'organization: {unit}']


@pytest.mark.parametrize(
    'text, reason',
    [
        ('Repasse aos municípios do SUAS.', 'mentions SUAS'),
        ('Aprovado pelo CNAS.', 'mentions CNAS'),
        ('Ouvida a SNAS.', 'mentions SNAS'),
        ('O Secretario Nacional de Assistência Social designa', 'mentions the national secretariat'),
        ('no âmbito do Sistema Único de Assistência Social', 'mentions SUAS by name'),
        ('serviços de Proteção Social Especial', 'mentions social protection'),
    ],
)
def test_mds_acts_mentioning_a_term_are_suggested(article, text, reason):
    suggestion, reasons = assess(article, text)
    assert suggestion == 'suggest'
    assert reason in reasons


def test_acronyms_only_match_in_capitals(article):
    """'suas' is also a pronoun, so only 'SUAS' counts."""
    assert assess(article, 'no exercício de suas atribuições')[0] == 'review'


def test_ministry_name_does_not_count_as_a_mention(article):
    assert assess(article, article['hierarchyStr']) == ('review', ['no direct SNAS relevance signal'])


# --- summary ---


def test_ementa_is_the_summary(article):
    text = make_full_text(article, 'Altera a Resolução CIT nº 17.', PREAMBLE, 'Art. 1º A Resolução passa a vigorar.')
    assert excerpt(article, text) == 'Altera a Resolução CIT nº 17.'


def test_without_ementa_the_paragraph_after_resolve_is_the_summary(article):
    text = make_full_text(article, PREAMBLE, 'Art. 1º Aprovar o plano de ação.', 'Art. 2º Entra em vigor.')
    assert excerpt(article, text) == 'Art. 1º Aprovar o plano de ação.'


def test_amendment_announcement_takes_the_new_text(article):
    text = make_full_text(
        article,
        PREAMBLE,
        'Art. 1º O art. 2º da Portaria nº 5 passa a vigorar com a seguinte redação:',
        '"Art. 2º Fica instituído o comitê."',
        'Art. 2º Esta portaria entra em vigor.',
    )
    assert excerpt(article, text) == (
        'Art. 1º O art. 2º da Portaria nº 5 passa a vigorar com a seguinte redação: "Art. 2º Fica instituído o comitê."'
    )


def test_later_designation_is_added(article):
    text = make_full_text(article, PREAMBLE, 'Art. 1º Dispensar Fulana.', 'Art. 2º Designar Beltrana.')
    assert excerpt(article, text) == 'Art. 1º Dispensar Fulana. Art. 2º Designar Beltrana.'


@pytest.mark.parametrize(
    'block, expected',
    [
        ('Objeto: Aquisição de computadores. Vigência: 01/01/2026 a 31/12/2026.', 'Aquisição de computadores.'),
        (
            'Objeto da contratação: Serviço de limpeza. Valor Total: R$ 10,00.',
            'Objeto da contratação: Serviço de limpeza.',
        ),
    ],
)
def test_contract_extract_summary_is_its_object(block, expected):
    article = make_article(title='EXTRATO DE CONTRATO Nº 1/2026', artType='Extrato de Contrato')
    text = make_full_text(article, 'Espécie: Contrato nº 1/2026. Contratante: MDS.', block)
    assert excerpt(article, text) == expected


def test_without_preamble_the_first_long_paragraph_up_to_recursos(article):
    long_paragraph = 'Espécie: Termo de Fomento celebrado com a entidade para apoio a serviços socioassistenciais.'
    text = make_full_text(article, 'Processo nº 1.', f'{long_paragraph} RECURSOS: R$ 1.000,00.')
    assert excerpt(article, text) == long_paragraph


def test_title_is_not_repeated(article):
    content = f'{article["title"]} - Divulga a relação de municípios'
    assert excerpt({**article, 'content': content}) == 'Divulga a relação de municípios'


@pytest.mark.parametrize(
    'ending, expected',
    [('.', 'Aprova o plano de ação.'), (':', 'Aprova o plano de ação.'), ('', 'Aprova o plano de ação')],
)
def test_removing_the_title_keeps_the_final_punctuation(article, ending, expected):
    """Only the separator after the title is removed; a final colon still becomes a period."""
    content = f'{article["title"]} - Aprova o plano de ação{ending}'
    assert excerpt({**article, 'content': content}) == expected


def test_a_paragraph_introducing_a_list_ends_with_a_period(article):
    text = make_full_text(article, PREAMBLE, 'Art. 1º Habilitar os municípios abaixo:', '| Município | UF |')
    assert excerpt(article, text) == 'Art. 1º Habilitar os municípios abaixo.'


def test_long_summaries_are_cut_at_a_word(article):
    value = excerpt({**article, 'content': 'palavra ' * 400})
    assert len(value) <= SUMMARY_LIMIT
    assert value.endswith('palavra…')


def test_empty_act_points_to_the_dou(article):
    assert excerpt(article) == 'Consultar o texto integral no DOU.'


# --- email ---


def test_email_lists_suggested_acts_between_date_and_signature(article):
    assessed = [
        {'article': article, 'full_text': '', 'suggestion': 'suggest', 'reasons': []},
        {'article': make_article(title='OUTRA'), 'full_text': '', 'suggestion': 'review', 'reasons': []},
    ]
    text, count = clipping_text(dt.date(2026, 3, 5), assessed)
    paragraphs = text.rstrip('\n').split('\n\n')
    assert count == 1
    assert paragraphs[0] == '**Brasília - DF, 05 de Março de 2026.**'
    assert paragraphs[1].startswith(f'[{article["title"]}]({article["url"]}): ')
    assert paragraphs[2:] == list(SIGNATURE)


def test_email_without_acts_says_so():
    text, count = clipping_text(dt.date(2026, 3, 5), [])
    assert count == 0
    assert text.split('\n\n')[1] == NOTHING
