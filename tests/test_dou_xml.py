"""The reader of the DOU open-data XML (2004 to 2017): fields, markup left in old files, and the written day."""

import json
import zipfile

import dou_xml

XML = """<xml>
  <article numberPage="48" pubName="DO2" name="PORTARIAS" artType="RETIFICAÇÃO&lt;/Identifica&gt;" \
pubDate="15/06/2016" artCategory="Ministério do Desenvolvimento Social e Agrário/SECRETARIA NACIONAL DE \
ASSISTÊNCIA SOCIAL" pdfPage="http://pesquisa.in.gov.br/imprensa/jsp/visualiza/index.jsp?jornal=2&amp;data=15/06/2016" \
editionNumber="113">
    <body>
      <Identifica><![CDATA[PORTARIA Nº 1, DE 14 DE JUNHO DE 2016]]></Identifica>
      <Data />
      <Ementa />
      <Texto><![CDATA[<p class='identifica pdf-CENTER'>PORTARIA Nº 1, DE 14 DE JUNHO DE 2016</p>
<p class='corpo pdf-JUSTIFY'>O SECRETÁRIO NACIONAL, resolve:</p>]]></Texto>
    </body>
  </article>
</xml>"""


def other_ministry_xml(date='15/06/2016'):
    return XML.replace(
        'Ministério do Desenvolvimento Social e Agrário/SECRETARIA NACIONAL DE ASSISTÊNCIA SOCIAL',
        'Ministério da Saúde',
    ).replace('15/06/2016', date)


def test_parse_article_reads_fields_and_cleans_markup():
    article, blocks = dou_xml.parse_article('220160615438.xml', XML)
    assert article['urlTitle'] == '220160615438'
    assert article['title'] == 'PORTARIA Nº 1, DE 14 DE JUNHO DE 2016'
    assert article['artType'] == 'RETIFICAÇÃO'
    assert article['hierarchyList'] == [
        'Ministério do Desenvolvimento Social e Agrário',
        'SECRETARIA NACIONAL DE ASSISTÊNCIA SOCIAL',
    ]
    assert article['url'].endswith('data=15/06/2016')
    assert blocks[-1] == 'O SECRETÁRIO NACIONAL, resolve:'


def test_write_day_keeps_candidates_and_records_the_gaps(tmp_path):
    entries = [dou_xml.parse_article('1.xml', XML), dou_xml.parse_article('2.xml', other_ministry_xml())]
    assert dou_xml.write_day(tmp_path, '15-06-2016', entries, absent=[1]) == 1
    index = json.loads((tmp_path / '15-06-2016.json').read_text(encoding='utf-8'))
    assert (index['count'], len(index['articles']), index['missingSections']) == (2, 1, ['DO1'])
    text = (tmp_path / '15-06-2016' / '1.md').read_text(encoding='utf-8')
    assert text.startswith('# PORTARIA Nº 1, DE 14 DE JUNHO DE 2016\n\nSource: ')
    assert 'Organization: Ministério do Desenvolvimento Social e Agrário/SECRETARIA' in text
    assert not (tmp_path / '15-06-2016' / '2.md').exists()


def test_month_articles_groups_the_zips_by_date(tmp_path):
    path = tmp_path / 'S02062016.zip'
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('1.xml', XML)
        archive.writestr('2.xml', other_ministry_xml('16/06/2016'))
        archive.writestr('S02062016/1_APL_18_001.jpg', b'not xml')
    days = dou_xml.month_articles({2: path})
    assert {date: len(entries) for date, entries in days.items()} == {'15/06/2016': 1, '16/06/2016': 1}


def test_months_covers_the_range_across_years():
    import datetime as dt

    assert list(dou_xml.months(dt.date(2016, 11, 5), dt.date(2017, 2, 1))) == [
        (2016, 11),
        (2016, 12),
        (2017, 1),
        (2017, 2),
    ]
