# Convenção de idioma

- Escreva a documentação do projeto (inclusive mensagens de commit) em português brasileiro.
- Escreva scripts e código em inglês, incluindo nomes de variáveis, funções e comentários no código.
- Crie branches Git somente quando o usuário pedir explicitamente.

# Desenvolvimento

Os comandos estão em `make help`, e o fluxo, na seção “Desenvolvimento” do `README.md`.

- Faça commit só com `make check` passando.
- Quando mudar uma regra de seleção ou de resumo (`scripts/clipping.py`), rode `make regenerate` e confira no diff de `clipping-novo/` cada clipping que mudou. Atualize `docs/regras.md`, que explica as regras na aba Regras do relatório. Se a concordância com `clipping-antigo/` melhorar, suba os mínimos em `tests/test_archive.py`.
- Os scripts de `scripts/` usam só a biblioteca padrão do Python e rodam com `python scripts/<nome>.py`, sem ambiente virtual. Só os testes e o ruff precisam de pacotes: ficam no grupo `dev` de `pyproject.toml` e são instalados pelo uv.
- Dê aos scripts de `scripts/` nomes diferentes dos módulos da biblioteca padrão: os scripts importam uns aos outros pelo nome, e um `site.py` encobria o módulo `site` do Python.
- Datas em nomes de arquivo, argumentos e links usam DD-MM-AAAA (`scripts/dates.py`). Ordene essas datas com `dates.parse`, porque o texto não segue a ordem cronológica.
- Rode os scripts a partir da raiz do repositório, porque os caminhos padrão (`data/`, `clipping-novo/`) são relativos a ela.
